#!/usr/bin/env python3
"""Offline runner for the human-flavor-pipeline Golden A/B evaluation.

The runner deliberately does not call a model API. ``prepare`` combines two
already-generated result sets into blinded judge packets, and ``report`` joins
human or model-judge decisions with a separate answer key.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import secrets
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = 1
DEFAULT_CASES_PATH = Path(__file__).with_name("cases.jsonl")
SIDE_NAMES = ("A", "B")
SYSTEM_NAMES = ("baseline", "candidate")
CASE_ID_RE = re.compile(r"^G[1-9][0-9]*$")

CASE_KEYS = {"schema_version", "id", "title", "context", "before", "rubric"}
CONTEXT_KEYS = {"carrier", "audience", "register", "voice"}
RUBRIC_KEYS = {
    "must_change",
    "must_keep",
    "acceptable",
    "hard_fail",
    "judge_notes",
}


class EvalError(ValueError):
    """Raised for malformed input or an incomplete evaluation bundle."""


def _read_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    records: list[tuple[int, dict[str, Any]]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                if not raw_line.strip():
                    continue
                try:
                    value = json.loads(raw_line)
                except json.JSONDecodeError as exc:
                    raise EvalError(
                        f"{path}:{line_number}: invalid JSON: {exc.msg}"
                    ) from exc
                if not isinstance(value, dict):
                    raise EvalError(
                        f"{path}:{line_number}: each JSONL record must be an object"
                    )
                records.append((line_number, value))
    except OSError as exc:
        raise EvalError(f"cannot read {path}: {exc}") from exc
    return records


def _write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=False))
                handle.write("\n")
        os.replace(temporary_name, path)
    except OSError as exc:
        if temporary_name:
            try:
                Path(temporary_name).unlink(missing_ok=True)
            except OSError:
                pass
        raise EvalError(f"cannot write {path}: {exc}") from exc


def _require_exact_keys(
    value: Mapping[str, Any], expected: set[str], location: str
) -> None:
    actual = set(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    details: list[str] = []
    if missing:
        details.append(f"missing {', '.join(missing)}")
    if extra:
        details.append(f"unexpected {', '.join(extra)}")
    if details:
        raise EvalError(f"{location}: {'; '.join(details)}")


def _require_nonempty_string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvalError(f"{location}: expected a non-empty string")
    return value


def _require_string_list(
    value: Any, location: str, *, allow_empty: bool = False
) -> list[str]:
    if not isinstance(value, list):
        raise EvalError(f"{location}: expected a list of strings")
    if not value and not allow_empty:
        raise EvalError(f"{location}: list must not be empty")
    seen: set[str] = set()
    for index, item in enumerate(value):
        text = _require_nonempty_string(item, f"{location}[{index}]")
        if text in seen:
            raise EvalError(f"{location}[{index}]: duplicate item {text!r}")
        seen.add(text)
    return value


def validate_case(case: Mapping[str, Any], location: str = "case") -> None:
    _require_exact_keys(case, CASE_KEYS, location)
    if case["schema_version"] != SCHEMA_VERSION:
        raise EvalError(
            f"{location}.schema_version: expected {SCHEMA_VERSION}, "
            f"got {case['schema_version']!r}"
        )

    case_id = _require_nonempty_string(case["id"], f"{location}.id")
    if not CASE_ID_RE.fullmatch(case_id):
        raise EvalError(f"{location}.id: expected G followed by a positive integer")
    _require_nonempty_string(case["title"], f"{location}.title")
    _require_nonempty_string(case["before"], f"{location}.before")

    context = case["context"]
    if not isinstance(context, dict):
        raise EvalError(f"{location}.context: expected an object")
    _require_exact_keys(context, CONTEXT_KEYS, f"{location}.context")
    for key in sorted(CONTEXT_KEYS):
        _require_nonempty_string(context[key], f"{location}.context.{key}")

    rubric = case["rubric"]
    if not isinstance(rubric, dict):
        raise EvalError(f"{location}.rubric: expected an object")
    _require_exact_keys(rubric, RUBRIC_KEYS, f"{location}.rubric")
    for key in sorted(RUBRIC_KEYS):
        _require_string_list(
            rubric[key],
            f"{location}.rubric.{key}",
            allow_empty=(key == "must_change"),
        )


def load_cases(path: Path = DEFAULT_CASES_PATH) -> list[dict[str, Any]]:
    records = _read_jsonl(path)
    if not records:
        raise EvalError(f"{path}: no cases found")

    cases: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for line_number, case in records:
        location = f"{path}:{line_number}"
        validate_case(case, location)
        case_id = case["id"]
        if case_id in seen_ids:
            raise EvalError(f"{location}.id: duplicate case id {case_id}")
        seen_ids.add(case_id)
        cases.append(case)
    return cases


def load_outputs(
    path: Path, system_name: str, expected_case_ids: set[str]
) -> dict[str, str]:
    outputs: dict[str, str] = {}
    for line_number, record in _read_jsonl(path):
        location = f"{path}:{line_number}"
        _require_exact_keys(record, {"case_id", "output"}, location)
        case_id = _require_nonempty_string(record["case_id"], f"{location}.case_id")
        output = _require_nonempty_string(record["output"], f"{location}.output")
        if case_id in outputs:
            raise EvalError(f"{location}.case_id: duplicate case id {case_id}")
        outputs[case_id] = output

    actual_case_ids = set(outputs)
    missing = sorted(expected_case_ids - actual_case_ids)
    extra = sorted(actual_case_ids - expected_case_ids)
    if missing or extra:
        details: list[str] = []
        if missing:
            details.append(f"missing cases {', '.join(missing)}")
        if extra:
            details.append(f"unknown cases {', '.join(extra)}")
        raise EvalError(f"{system_name} outputs {path}: {'; '.join(details)}")
    return outputs


def _packet_id(seed: int, case_id: str) -> str:
    digest = hashlib.sha256(f"{seed}\0{case_id}".encode("utf-8")).hexdigest()
    return f"p-{digest[:16]}"


def prepare_packets(
    cases: Sequence[Mapping[str, Any]],
    baseline_outputs: Mapping[str, str],
    candidate_outputs: Mapping[str, str],
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return blinded packets and a separate answer key.

    Candidate placement is balanced: for an even case count it appears on each
    side equally often; for an odd count the imbalance is at most one.
    """

    expected_ids = {str(case["id"]) for case in cases}
    for name, outputs in (
        ("baseline", baseline_outputs),
        ("candidate", candidate_outputs),
    ):
        actual_ids = set(outputs)
        if actual_ids != expected_ids:
            missing = sorted(expected_ids - actual_ids)
            extra = sorted(actual_ids - expected_ids)
            raise EvalError(
                f"{name} output coverage mismatch: missing={missing}, extra={extra}"
            )

    rng = random.Random(seed)
    shuffled_cases = list(cases)
    rng.shuffle(shuffled_cases)

    candidate_on_a = [True] * (len(cases) // 2)
    candidate_on_a.extend([False] * (len(cases) // 2))
    if len(cases) % 2:
        candidate_on_a.append(bool(rng.getrandbits(1)))
    rng.shuffle(candidate_on_a)

    packets: list[dict[str, Any]] = []
    answer_key: list[dict[str, Any]] = []
    for case, is_candidate_a in zip(shuffled_cases, candidate_on_a):
        case_id = str(case["id"])
        packet_id = _packet_id(seed, case_id)
        sides = (
            {"A": "candidate", "B": "baseline"}
            if is_candidate_a
            else {"A": "baseline", "B": "candidate"}
        )
        responses = {
            side: (
                candidate_outputs[case_id]
                if system_name == "candidate"
                else baseline_outputs[case_id]
            )
            for side, system_name in sides.items()
        }
        packets.append(
            {
                "schema_version": SCHEMA_VERSION,
                "packet_id": packet_id,
                "case_id": case_id,
                "title": case["title"],
                "context": case["context"],
                "before": case["before"],
                "rubric": case["rubric"],
                "responses": responses,
                "judge_instructions": {
                    "task": "Compare A and B against the rubric. Judge quality, not wording overlap.",
                    "hard_fail_rule": (
                        "Mark every side that hits any rubric.hard_fail item. "
                        "A sole hard-failing side cannot win or tie."
                    ),
                    "output": {
                        "packet_id": packet_id,
                        "winner": "A | B | tie",
                        "hard_fail": ["A and/or B; use an empty list if neither"],
                        "reason": "brief evidence-based rationale",
                    },
                },
            }
        )
        answer_key.append(
            {
                "schema_version": SCHEMA_VERSION,
                "packet_id": packet_id,
                "case_id": case_id,
                "sides": sides,
            }
        )
    return packets, answer_key


def load_answer_key(path: Path) -> list[dict[str, Any]]:
    keys: list[dict[str, Any]] = []
    seen_packet_ids: set[str] = set()
    seen_case_ids: set[str] = set()
    for line_number, record in _read_jsonl(path):
        location = f"{path}:{line_number}"
        _require_exact_keys(
            record, {"schema_version", "packet_id", "case_id", "sides"}, location
        )
        if record["schema_version"] != SCHEMA_VERSION:
            raise EvalError(f"{location}.schema_version: unsupported version")
        packet_id = _require_nonempty_string(
            record["packet_id"], f"{location}.packet_id"
        )
        case_id = _require_nonempty_string(record["case_id"], f"{location}.case_id")
        sides = record["sides"]
        if not isinstance(sides, dict):
            raise EvalError(f"{location}.sides: expected an object")
        _require_exact_keys(sides, set(SIDE_NAMES), f"{location}.sides")
        if set(sides.values()) != set(SYSTEM_NAMES):
            raise EvalError(
                f"{location}.sides: A and B must map once each to baseline and candidate"
            )
        if packet_id in seen_packet_ids:
            raise EvalError(f"{location}.packet_id: duplicate {packet_id}")
        if case_id in seen_case_ids:
            raise EvalError(f"{location}.case_id: duplicate {case_id}")
        seen_packet_ids.add(packet_id)
        seen_case_ids.add(case_id)
        keys.append(record)
    if not keys:
        raise EvalError(f"{path}: no answer-key records found")
    return keys


def load_judgments(
    path: Path, expected_packet_ids: set[str]
) -> dict[str, dict[str, Any]]:
    judgments: dict[str, dict[str, Any]] = {}
    allowed_keys = {"packet_id", "winner", "hard_fail", "reason"}
    for line_number, record in _read_jsonl(path):
        location = f"{path}:{line_number}"
        actual_keys = set(record)
        required_keys = {"packet_id", "winner", "hard_fail"}
        missing = sorted(required_keys - actual_keys)
        extra = sorted(actual_keys - allowed_keys)
        if missing or extra:
            details: list[str] = []
            if missing:
                details.append(f"missing {', '.join(missing)}")
            if extra:
                details.append(f"unexpected {', '.join(extra)}")
            raise EvalError(f"{location}: {'; '.join(details)}")

        packet_id = _require_nonempty_string(
            record["packet_id"], f"{location}.packet_id"
        )
        if packet_id not in expected_packet_ids:
            raise EvalError(f"{location}.packet_id: unknown packet {packet_id}")
        if packet_id in judgments:
            raise EvalError(f"{location}.packet_id: duplicate packet {packet_id}")

        winner = record["winner"]
        if winner not in ("A", "B", "tie"):
            raise EvalError(f"{location}.winner: expected A, B, or tie")
        hard_fail = record["hard_fail"]
        if not isinstance(hard_fail, list):
            raise EvalError(f"{location}.hard_fail: expected a list")
        if any(side not in SIDE_NAMES for side in hard_fail):
            raise EvalError(f"{location}.hard_fail: entries must be A or B")
        if len(hard_fail) != len(set(hard_fail)):
            raise EvalError(f"{location}.hard_fail: duplicate side")
        if "reason" in record:
            _require_nonempty_string(record["reason"], f"{location}.reason")
        judgments[packet_id] = record
    return judgments


def _ratio(count: int, denominator: int) -> float:
    return round(count / denominator, 4) if denominator else 0.0


def summarize_results(
    answer_key: Sequence[Mapping[str, Any]],
    judgments: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    wins = ties = losses = 0
    candidate_hard_fails = baseline_hard_fails = 0
    either_hard_fails = both_hard_fails = 0
    conflicts: list[str] = []
    missing: list[str] = []
    cases: list[dict[str, Any]] = []

    for key in answer_key:
        packet_id = str(key["packet_id"])
        case_id = str(key["case_id"])
        judgment = judgments.get(packet_id)
        if judgment is None:
            missing.append(packet_id)
            continue

        sides = key["sides"]
        candidate_side = "A" if sides["A"] == "candidate" else "B"
        baseline_side = "B" if candidate_side == "A" else "A"
        winner = judgment["winner"]
        if winner == "tie":
            outcome = "tie"
            ties += 1
        elif winner == candidate_side:
            outcome = "win"
            wins += 1
        else:
            outcome = "loss"
            losses += 1

        hard_fail_sides = set(judgment["hard_fail"])
        candidate_failed = candidate_side in hard_fail_sides
        baseline_failed = baseline_side in hard_fail_sides
        candidate_hard_fails += int(candidate_failed)
        baseline_hard_fails += int(baseline_failed)
        either_hard_fails += int(candidate_failed or baseline_failed)
        both_hard_fails += int(candidate_failed and baseline_failed)

        if candidate_failed != baseline_failed:
            non_failed_side = baseline_side if candidate_failed else candidate_side
            if winner != non_failed_side:
                conflicts.append(packet_id)

        cases.append(
            {
                "packet_id": packet_id,
                "case_id": case_id,
                "candidate_side": candidate_side,
                "outcome": outcome,
                "candidate_hard_fail": candidate_failed,
                "baseline_hard_fail": baseline_failed,
            }
        )

    judged = len(cases)
    expected = len(answer_key)
    return {
        "schema_version": SCHEMA_VERSION,
        "expected": expected,
        "judged": judged,
        "missing": missing,
        "coverage_rate": _ratio(judged, expected),
        "candidate_outcome": {
            "win": wins,
            "tie": ties,
            "loss": losses,
            "win_rate": _ratio(wins, judged),
            "tie_rate": _ratio(ties, judged),
            "loss_rate": _ratio(losses, judged),
        },
        "hard_failure": {
            "candidate": {
                "count": candidate_hard_fails,
                "rate": _ratio(candidate_hard_fails, judged),
            },
            "baseline": {
                "count": baseline_hard_fails,
                "rate": _ratio(baseline_hard_fails, judged),
            },
            "either_response": {
                "count": either_hard_fails,
                "rate": _ratio(either_hard_fails, judged),
            },
            "both_responses": {
                "count": both_hard_fails,
                "rate": _ratio(both_hard_fails, judged),
            },
        },
        "hard_fail_verdict_conflicts": conflicts,
        "cases": cases,
    }


def _format_percent(rate: float) -> str:
    return f"{rate * 100:.1f}%"


def format_report(summary: Mapping[str, Any]) -> str:
    outcome = summary["candidate_outcome"]
    hard_failure = summary["hard_failure"]
    lines = [
        f"Coverage: {summary['judged']}/{summary['expected']} "
        f"({_format_percent(summary['coverage_rate'])})",
        (
            "Candidate W/T/L: "
            f"{outcome['win']}/{outcome['tie']}/{outcome['loss']} "
            f"({_format_percent(outcome['win_rate'])}/"
            f"{_format_percent(outcome['tie_rate'])}/"
            f"{_format_percent(outcome['loss_rate'])})"
        ),
        (
            "Hard failures: candidate "
            f"{hard_failure['candidate']['count']}/{summary['judged']} "
            f"({_format_percent(hard_failure['candidate']['rate'])}); baseline "
            f"{hard_failure['baseline']['count']}/{summary['judged']} "
            f"({_format_percent(hard_failure['baseline']['rate'])})"
        ),
    ]
    if summary["missing"]:
        lines.append(f"Missing packets: {', '.join(summary['missing'])}")
    if summary["hard_fail_verdict_conflicts"]:
        lines.append(
            "WARNING hard-fail/verdict conflicts: "
            + ", ".join(summary["hard_fail_verdict_conflicts"])
        )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate, blind, and report Golden A/B evaluations offline."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate case JSONL")
    validate_parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)

    prepare_parser = subparsers.add_parser(
        "prepare", help="create blinded judge packets and a separate answer key"
    )
    prepare_parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    prepare_parser.add_argument("--baseline", type=Path, required=True)
    prepare_parser.add_argument("--candidate", type=Path, required=True)
    prepare_parser.add_argument("--packets", type=Path, required=True)
    prepare_parser.add_argument("--key", type=Path, required=True)
    prepare_parser.add_argument(
        "--seed", type=int, help="integer seed; omitted means a fresh random seed"
    )

    report_parser = subparsers.add_parser(
        "report", help="summarize judge JSONL from the candidate perspective"
    )
    report_parser.add_argument("--judgments", type=Path, required=True)
    report_parser.add_argument("--key", type=Path, required=True)
    report_parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="report available judgments instead of failing on missing packets",
    )
    report_parser.add_argument(
        "--json", action="store_true", help="emit machine-readable JSON"
    )
    return parser


def _ensure_distinct_paths(named_paths: Mapping[str, Path]) -> None:
    resolved: dict[Path, str] = {}
    for name, path in named_paths.items():
        normalized = path.expanduser().resolve()
        if normalized in resolved:
            raise EvalError(
                f"{name} and {resolved[normalized]} must use different paths: {path}"
            )
        resolved[normalized] = name


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            cases = load_cases(args.cases)
            print(f"OK: validated {len(cases)} cases from {args.cases}")
            return 0

        if args.command == "prepare":
            _ensure_distinct_paths(
                {
                    "cases": args.cases,
                    "baseline": args.baseline,
                    "candidate": args.candidate,
                    "packets": args.packets,
                    "key": args.key,
                }
            )
            cases = load_cases(args.cases)
            expected_ids = {case["id"] for case in cases}
            baseline = load_outputs(args.baseline, "baseline", expected_ids)
            candidate = load_outputs(args.candidate, "candidate", expected_ids)
            seed = args.seed if args.seed is not None else secrets.randbits(64)
            packets, answer_key = prepare_packets(cases, baseline, candidate, seed)
            _write_jsonl(args.packets, packets)
            _write_jsonl(args.key, answer_key)
            print(
                f"OK: prepared {len(packets)} blinded packets; seed={seed}; "
                f"packets={args.packets}; key={args.key}"
            )
            return 0

        if args.command == "report":
            _ensure_distinct_paths({"judgments": args.judgments, "key": args.key})
            answer_key = load_answer_key(args.key)
            expected_packet_ids = {record["packet_id"] for record in answer_key}
            judgments = load_judgments(args.judgments, expected_packet_ids)
            summary = summarize_results(answer_key, judgments)
            if summary["missing"] and not args.allow_partial:
                raise EvalError(
                    "missing judgments for packets: " + ", ".join(summary["missing"])
                )
            if args.json:
                print(json.dumps(summary, ensure_ascii=False, indent=2))
            else:
                print(format_report(summary))
            return 0

        raise AssertionError(f"unhandled command {args.command}")
    except EvalError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

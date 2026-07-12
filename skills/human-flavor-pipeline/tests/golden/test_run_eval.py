#!/usr/bin/env python3

from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


GOLDEN_DIR = Path(__file__).resolve().parent
if str(GOLDEN_DIR) not in sys.path:
    sys.path.insert(0, str(GOLDEN_DIR))

import run_eval  # noqa: E402


class CaseSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = run_eval.load_cases(GOLDEN_DIR / "cases.jsonl")

    def test_builtin_cases_validate_and_cover_g1_to_g10(self) -> None:
        self.assertEqual([case["id"] for case in self.cases], [f"G{i}" for i in range(1, 11)])

    def test_g7_rejects_every_new_fact_even_when_marked(self) -> None:
        g7 = next(case for case in self.cases if case["id"] == "G7")
        hard_fail = "\n".join(g7["rubric"]["hard_fail"])
        self.assertIn("新增任何", hard_fail)
        self.assertIn("仍判硬失败", hard_fail)

    def test_g9_allows_sourced_opening_but_rejects_invented_experience(self) -> None:
        g9 = next(case for case in self.cases if case["id"] == "G9")
        acceptable = "\n".join(g9["rubric"]["acceptable"])
        hard_fail = "\n".join(g9["rubric"]["hard_fail"])
        self.assertIn("有来源", acceptable)
        self.assertIn("判断起手", acceptable)
        self.assertIn("亲历现场", hard_fail)

    def test_schema_rejects_missing_and_unknown_fields(self) -> None:
        missing = copy.deepcopy(self.cases[0])
        del missing["before"]
        with self.assertRaisesRegex(run_eval.EvalError, "missing before"):
            run_eval.validate_case(missing)

        unknown = copy.deepcopy(self.cases[0])
        unknown["rubric"]["score"] = 5
        with self.assertRaisesRegex(run_eval.EvalError, "unexpected score"):
            run_eval.validate_case(unknown)

    def test_schema_rejects_duplicate_case_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicates.jsonl"
            with path.open("w", encoding="utf-8") as handle:
                for case in (self.cases[0], self.cases[0]):
                    handle.write(json.dumps(case, ensure_ascii=False) + "\n")
            with self.assertRaisesRegex(run_eval.EvalError, "duplicate case id G1"):
                run_eval.load_cases(path)

    def test_validate_cli_reports_case_count(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            status = run_eval.main(
                ["validate", "--cases", str(GOLDEN_DIR / "cases.jsonl")]
            )
        self.assertEqual(status, 0)
        self.assertIn("validated 10 cases", output.getvalue())


class BlindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = run_eval.load_cases(GOLDEN_DIR / "cases.jsonl")
        cls.baseline = {case["id"]: f"old::{case['id']}" for case in cls.cases}
        cls.candidate = {case["id"]: f"new::{case['id']}" for case in cls.cases}

    def test_prepare_is_deterministic_balanced_and_blinded(self) -> None:
        packets, answer_key = run_eval.prepare_packets(
            self.cases, self.baseline, self.candidate, seed=20260713
        )
        packets_again, key_again = run_eval.prepare_packets(
            self.cases, self.baseline, self.candidate, seed=20260713
        )
        self.assertEqual(packets, packets_again)
        self.assertEqual(answer_key, key_again)
        self.assertEqual(len(packets), 10)
        self.assertEqual(
            sum(key["sides"]["A"] == "candidate" for key in answer_key), 5
        )

        packet_by_id = {packet["packet_id"]: packet for packet in packets}
        for key in answer_key:
            packet = packet_by_id[key["packet_id"]]
            self.assertNotIn("sides", packet)
            self.assertNotIn("baseline", packet)
            self.assertNotIn("candidate", packet)
            for side in ("A", "B"):
                system_name = key["sides"][side]
                expected = (
                    self.candidate[key["case_id"]]
                    if system_name == "candidate"
                    else self.baseline[key["case_id"]]
                )
                self.assertEqual(packet["responses"][side], expected)

    def test_prepare_rejects_incomplete_outputs(self) -> None:
        incomplete = dict(self.candidate)
        incomplete.pop("G10")
        with self.assertRaisesRegex(run_eval.EvalError, "coverage mismatch"):
            run_eval.prepare_packets(
                self.cases, self.baseline, incomplete, seed=1
            )

    def test_prepare_and_report_cli_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline_path = root / "baseline.jsonl"
            candidate_path = root / "candidate.jsonl"
            packets_path = root / "packets.jsonl"
            key_path = root / "key.jsonl"
            judgments_path = root / "judgments.jsonl"

            for path, outputs in (
                (baseline_path, self.baseline),
                (candidate_path, self.candidate),
            ):
                with path.open("w", encoding="utf-8") as handle:
                    for case_id, output in outputs.items():
                        handle.write(
                            json.dumps(
                                {"case_id": case_id, "output": output},
                                ensure_ascii=False,
                            )
                            + "\n"
                        )

            with redirect_stdout(io.StringIO()):
                prepare_status = run_eval.main(
                    [
                        "prepare",
                        "--cases",
                        str(GOLDEN_DIR / "cases.jsonl"),
                        "--baseline",
                        str(baseline_path),
                        "--candidate",
                        str(candidate_path),
                        "--packets",
                        str(packets_path),
                        "--key",
                        str(key_path),
                        "--seed",
                        "9",
                    ]
                )
            self.assertEqual(prepare_status, 0)
            answer_key = run_eval.load_answer_key(key_path)

            with judgments_path.open("w", encoding="utf-8") as handle:
                for key in answer_key:
                    candidate_side = (
                        "A" if key["sides"]["A"] == "candidate" else "B"
                    )
                    handle.write(
                        json.dumps(
                            {
                                "packet_id": key["packet_id"],
                                "winner": candidate_side,
                                "hard_fail": [],
                                "reason": "candidate is better",
                            }
                        )
                        + "\n"
                    )

            output = io.StringIO()
            with redirect_stdout(output):
                report_status = run_eval.main(
                    [
                        "report",
                        "--judgments",
                        str(judgments_path),
                        "--key",
                        str(key_path),
                        "--json",
                    ]
                )
            self.assertEqual(report_status, 0)
            report = json.loads(output.getvalue())
            self.assertEqual(report["candidate_outcome"]["win"], 10)
            self.assertEqual(report["hard_failure"]["candidate"]["count"], 0)


class StatisticsTests(unittest.TestCase):
    def test_candidate_win_tie_loss_and_hard_failure_rates(self) -> None:
        answer_key = [
            {
                "packet_id": "p1",
                "case_id": "G1",
                "sides": {"A": "candidate", "B": "baseline"},
            },
            {
                "packet_id": "p2",
                "case_id": "G2",
                "sides": {"A": "baseline", "B": "candidate"},
            },
            {
                "packet_id": "p3",
                "case_id": "G3",
                "sides": {"A": "baseline", "B": "candidate"},
            },
        ]
        judgments = {
            "p1": {"winner": "A", "hard_fail": []},
            "p2": {"winner": "A", "hard_fail": ["B"]},
            "p3": {"winner": "tie", "hard_fail": ["A", "B"]},
        }

        summary = run_eval.summarize_results(answer_key, judgments)

        self.assertEqual(
            summary["candidate_outcome"],
            {
                "win": 1,
                "tie": 1,
                "loss": 1,
                "win_rate": 0.3333,
                "tie_rate": 0.3333,
                "loss_rate": 0.3333,
            },
        )
        self.assertEqual(
            summary["hard_failure"]["candidate"],
            {"count": 2, "rate": 0.6667},
        )
        self.assertEqual(
            summary["hard_failure"]["baseline"],
            {"count": 1, "rate": 0.3333},
        )
        self.assertEqual(summary["hard_fail_verdict_conflicts"], [])

    def test_summary_tracks_missing_packets(self) -> None:
        answer_key = [
            {
                "packet_id": "p1",
                "case_id": "G1",
                "sides": {"A": "candidate", "B": "baseline"},
            },
            {
                "packet_id": "p2",
                "case_id": "G2",
                "sides": {"A": "baseline", "B": "candidate"},
            },
        ]
        summary = run_eval.summarize_results(
            answer_key, {"p1": {"winner": "A", "hard_fail": []}}
        )
        self.assertEqual(summary["judged"], 1)
        self.assertEqual(summary["coverage_rate"], 0.5)
        self.assertEqual(summary["missing"], ["p2"])


if __name__ == "__main__":
    unittest.main()

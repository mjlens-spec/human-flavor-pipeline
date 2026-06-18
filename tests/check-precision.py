#!/usr/bin/env python3
"""Executable precision contract backed by production pattern data."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "tests" / "fixtures" / "18-precision-cases.jsonl"
RULES = ROOT / "patterns" / "precision-rules.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def context_allows(rule: dict[str, Any], context: str) -> bool:
    if "contexts" in rule and context not in rule["contexts"]:
        return False
    return context not in rule.get("excluded_contexts", [])


def regex_matches(rule: dict[str, Any], text: str) -> bool:
    if not re.search(rule["regex"], text):
        return False
    excluded = rule.get("excluded_regex")
    return not excluded or not re.search(excluded, text)


def short_sentence_run(rule: dict[str, Any], text: str) -> bool:
    run = 0
    for sentence in (part.strip() for part in re.split(r"[。！？]", text)):
        if not sentence:
            continue
        run = run + 1 if len(sentence) <= rule["max_chars"] else 0
        if run >= rule["min_count"]:
            return True
    return False


def title_restatement(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or not lines[0].startswith("#") or len(lines) < 2:
        return False
    title = lines[0].lstrip("# ")
    title_core = re.sub(r"^(为什么|如何|怎么)", "", title)
    return title in lines[1] or bool(title_core and title_core in lines[1])


def rule_matches(rule: dict[str, Any], text: str, context: str) -> bool:
    if not context_allows(rule, context):
        return False
    required = rule.get("required_regex")
    if required and not re.search(required, text):
        return False

    kind = rule["kind"]
    if kind == "regex":
        return regex_matches(rule, text)
    if kind == "regex_count":
        return len(re.findall(rule["regex"], text)) >= rule["min_count"]
    if kind == "term_count":
        count = sum(text.count(term) for term in rule["terms"])
        return count >= rule["min_count"]
    if kind == "short_sentence_run":
        return short_sentence_run(rule, text)
    if kind == "title_restatement":
        return title_restatement(text)
    raise ValueError(f"unsupported matcher kind: {kind}")


def classify(
    text: str, context: str, rules: list[dict[str, Any]]
) -> tuple[set[str], set[str]]:
    patterns: set[str] = set()
    risks: set[str] = set()
    for rule in rules:
        if not rule_matches(rule, text, context):
            continue
        target = patterns if rule["axis"] == "pattern" else risks
        target.add(rule["id"])
    return patterns, risks


def validate_production_docs(config: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for document in config["documentation"]:
        path = ROOT / document["path"]
        content = path.read_text(encoding="utf-8")
        for marker in document["required_markers"]:
            if marker not in content:
                failures.append(f"{document['path']}: missing production marker {marker!r}")
    return failures


def validate_rule_registry(rules: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    rule_ids = [rule["id"] for rule in rules]
    if len(rule_ids) != len(set(rule_ids)):
        failures.append("patterns/precision-rules.json: duplicate rule id")
    for rule in rules:
        if rule["axis"] not in {"pattern", "risk"}:
            failures.append(f"{rule['id']}: invalid axis {rule['axis']!r}")
        if rule["kind"] not in {
            "regex",
            "regex_count",
            "term_count",
            "short_sentence_run",
            "title_restatement",
        }:
            failures.append(f"{rule['id']}: unsupported matcher kind {rule['kind']!r}")
    return failures


def main() -> int:
    config = load_json(RULES)
    rules = config["rules"]
    failures = validate_production_docs(config) + validate_rule_registry(rules)
    cases = [
        json.loads(line)
        for line in CASES.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for case in cases:
        patterns, risks = classify(case["text"], case["context"], rules)
        expected_patterns = set(case["expected_patterns"])
        expected_risks = set(case["expected_risks"])
        if patterns != expected_patterns or risks != expected_risks:
            failures.append(
                f"{case['id']}: patterns={sorted(patterns)} "
                f"expected={sorted(expected_patterns)}; risks={sorted(risks)} "
                f"expected={sorted(expected_risks)}"
            )

    covered_rule_ids = {
        rule_id
        for case in cases
        for rule_id in case["expected_patterns"] + case["expected_risks"]
    }
    uncovered_rule_ids = {rule["id"] for rule in rules} - covered_rule_ids
    if uncovered_rule_ids:
        failures.append(
            "production rules without a positive control: "
            + ", ".join(sorted(uncovered_rule_ids))
        )

    required_negatives = {
        rule["id"] for rule in rules if rule.get("requires_adjacent_negative")
    }
    guarded_rule_ids = {
        rule_id for case in cases for rule_id in case.get("guards", [])
    }
    unknown_guards = guarded_rule_ids - {rule["id"] for rule in rules}
    if unknown_guards:
        failures.append("unknown guard rule ids: " + ", ".join(sorted(unknown_guards)))
    for case in cases:
        overlap = set(case.get("guards", [])) & set(case["expected_patterns"])
        if overlap:
            failures.append(
                f"{case['id']}: adjacent negative also expects guarded rule(s) "
                + ", ".join(sorted(overlap))
            )
    missing_negatives = required_negatives - guarded_rule_ids
    if missing_negatives:
        failures.append(
            "production slop rules without an adjacent negative: "
            + ", ".join(sorted(missing_negatives))
        )

    if failures:
        print("precision contract failed", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        return 1

    anti_false_positive = sum(not case["expected_patterns"] for case in cases)
    positive_controls = len(cases) - anti_false_positive
    print(
        f"precision contract ok: {len(cases)} cases, "
        f"{anti_false_positive} anti-false-positive cases, "
        f"{positive_controls} positive controls, production rules loaded"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

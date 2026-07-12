#!/usr/bin/env python3
"""Deterministic fact-integrity gate for before/after Chinese text.

The gate protects literal facts that a polishing pass must not silently remove,
change, or invent.  It uses only Python's standard library and intentionally
does not attempt semantic fact checking.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURES = ROOT / "tests" / "fixtures" / "20-fact-integrity-cases.jsonl"

KIND_ORDER = {
    "date": 0,
    "version": 1,
    "percentage": 2,
    "money": 3,
    "number": 4,
    "quote": 5,
    "code": 6,
    "placeholder": 7,
}

ARABIC_NUMBER = r"[+-]?(?:\d{1,3}(?:[,，]\d{3})+|\d+)(?:\.\d+)?"
CHINESE_NUMBER = r"(?:[零〇一二两三四五六七八九十百千万亿兆俩几半]+(?:点[零〇一二三四五六七八九]+)?)"

FENCED_CODE_RE = re.compile(
    r"(?ms)^ {0,3}(?P<fence>`{3,}|~{3,})[^\n]*\n.*?^ {0,3}(?P=fence)\s*$"
)
DOUBLE_INLINE_CODE_RE = re.compile(r"(?<!`)``([^`\n]|`(?!`))+``(?!`)")
INLINE_CODE_RE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")

QUOTE_PATTERNS = [
    re.compile(r"「(?:[^「」]|『[^『』]*』)*」", re.DOTALL),
    re.compile(r"『[^『』]*』", re.DOTALL),
    re.compile(r"“[^”]*”", re.DOTALL),
    re.compile(r"‘[^’]*’", re.DOTALL),
    re.compile(r'"[^"\n]+"'),
]

PLACEHOLDER_PATTERNS = [
    re.compile(r"\{\{[^{}\n]+\}\}"),
    re.compile(r"\{%[^%\n]+%\}"),
    re.compile(r"\$\{[^{}\n]+\}"),
    re.compile(r"<%[^%\n]+%>"),
    re.compile(r"<<[^<>\n]+>>"),
    re.compile(r"\[\[[^\[\]\n]+\]\]"),
    re.compile(r"\{[A-Za-z_][A-Za-z0-9_.-]*\}"),
    re.compile(
        r"\[(?:(?:待填|待补|待填写|填写|填入|请输入|此处填写)[^\[\]\n]{0,20}"
        r"|[^\[\]\n]{0,20}(?:名|名称|姓名|日期|时间|金额|预算|编号|ID|链接|地址|电话|邮箱|版本)"
        r"|[A-Za-z_][A-Za-z0-9_.-]{1,30}|X{2,})\](?!\s*\()"
    ),
    re.compile(
        r"<(?:(?:待填|待补)?[\u4e00-\u9fff]{1,16}"
        r"|[A-Z][A-Z0-9_-]{1,30})>"
    ),
    re.compile(r"\b(?:YYYY|XXXX)[-/.](?:MM|XX)[-/.](?:DD|XX)\b", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9_])(?:XXX+|TBD|TODO)(?![A-Za-z0-9_])"),
    re.compile(r"(?<![A-Za-z0-9_])#[0-9]+[A-Za-z](?![A-Za-z0-9_])"),
]

# Markdown 的列表序号和标题编号是排版结构,不是正文事实。只屏蔽行首编号,
# 句子里的数量仍照常保护。
STRUCTURAL_NUMBER_RE = re.compile(
    r"(?m)^[ \t]*(?:#{1,6}[ \t]+|\*{1,2})?(\d+)(?=[.)、．][ \t]+)"
)

ATOMIC_PATTERNS = [
    (
        "date",
        re.compile(
            r"(?<!\d)(?:"
            r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*[日号]"
            r"|\d{4}\s*年\s*\d{1,2}\s*月"
            r"|\d{1,2}\s*月\s*\d{1,2}\s*[日号]"
            r"|\d{4}[-/.]\d{1,2}[-/.]\d{1,2}"
            r"|\d{4}[-/.]\d{1,2}"
            r"|\d{4}\s*年"
            r")(?!\d)"
        ),
    ),
    (
        "version",
        re.compile(
            r"(?<![A-Za-z0-9_])(?:"
            r"(?:(?:v(?:er(?:sion)?)?|版本)\s*)\d+(?:\.\d+){1,3}(?:[-+][A-Za-z0-9_.-]+)?"
            r"|(?:[A-Za-z][A-Za-z0-9_.-]*\s+)?\d+\.\d+\.\d+(?:[-+][A-Za-z0-9_.-]+)?"
            r"|[A-Za-z][A-Za-z0-9_.-]*\s+\d+\.\d+"
            r")(?![A-Za-z0-9_])",
            re.IGNORECASE,
        ),
    ),
    (
        "percentage",
        re.compile(
            rf"(?<![A-Za-z0-9_])(?:"
            rf"{ARABIC_NUMBER}\s*[%％]"
            rf"|百分之\s*(?:{ARABIC_NUMBER}|{CHINESE_NUMBER})"
            rf"|(?:{ARABIC_NUMBER}|{CHINESE_NUMBER})\s*(?:成|折)(?:多|左右)?"
            rf"|一半"
            rf")(?![A-Za-z0-9_])"
        ),
    ),
    (
        "money",
        re.compile(
            rf"(?<![A-Za-z0-9_])(?:"
            rf"(?:人民币|RMB|CNY|USD|US\$|HKD|EUR|GBP|NT\$|新台币|台币|￥|¥|\$|€|£)\s*"
            rf"(?:{ARABIC_NUMBER}|{CHINESE_NUMBER})(?:\s*[万亿kK])?(?:\s*(?:元|美元|港元|欧元|英镑))?"
            rf"|(?:{ARABIC_NUMBER}|{CHINESE_NUMBER})\s*(?:多|余|左右)?\s*(?:亿元|万元|元|块钱|美元|港元|欧元|英镑|新台币|台币)"
            rf")(?![A-Za-z0-9_])",
            re.IGNORECASE,
        ),
    ),
    (
        "number",
        re.compile(
            rf"(?<![A-Za-z0-9_])(?:"
            rf"{ARABIC_NUMBER}"
            rf"|第?{CHINESE_NUMBER}(?:来|多|余)?(?:个百分点|个人|个月|季度|星期|小时|分钟|公里|公斤|个|人|次|年|月|日|天|周|季|秒|期|篇|条|件|家|台|套|项|组|份|位|名|层|轮|倍|岁|米|斤)"
            rf")(?![A-Za-z0-9_])"
        ),
    ),
]


@dataclass(frozen=True)
class Fact:
    kind: str
    raw: str
    normalized: str
    start: int
    end: int


@dataclass
class Report:
    missing: list[dict[str, str]]
    changed: list[dict[str, str]]
    added: list[dict[str, str]]

    def ok(self, allow_added: bool = False) -> bool:
        return not self.missing and not self.changed and (allow_added or not self.added)

    def as_dict(self, allow_added: bool = False) -> dict[str, Any]:
        return {
            "ok": self.ok(allow_added),
            "missing": self.missing,
            "changed": self.changed,
            "added": self.added,
        }


def overlaps(span: tuple[int, int], blocked: Iterable[tuple[int, int]]) -> bool:
    start, end = span
    return any(start < blocked_end and blocked_start < end for blocked_start, blocked_end in blocked)


def normalize(kind: str, raw: str) -> str:
    value = raw.replace("\r\n", "\n").replace("\r", "\n")
    if kind == "number":
        return re.sub(r"[\s,，]", "", value).lstrip("+")
    if kind == "percentage":
        return re.sub(r"\s+", "", value.replace("％", "%")).lstrip("+")
    if kind == "money":
        aliases = {
            "￥": "CNY",
            "¥": "CNY",
            "人民币": "CNY",
            "RMB": "CNY",
            "$": "USD",
            "US$": "USD",
            "美元": "USD",
            "HKD": "HKD",
            "港元": "HKD",
            "EUR": "EUR",
            "€": "EUR",
            "欧元": "EUR",
            "GBP": "GBP",
            "£": "GBP",
            "英镑": "GBP",
            "NT$": "TWD",
            "新台币": "TWD",
            "台币": "TWD",
        }
        compact = re.sub(r"[\s,，]", "", value).upper()
        for source in sorted(aliases, key=len, reverse=True):
            compact = compact.replace(source, aliases[source])
        return compact.lstrip("+")
    if kind == "date":
        compact = re.sub(r"\s+", "", value).replace("号", "日")
        match = re.fullmatch(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", compact)
        if match:
            return f"{int(match[1]):04d}-{int(match[2]):02d}-{int(match[3]):02d}"
        match = re.fullmatch(r"(\d{4})年(\d{1,2})月(\d{1,2})日", compact)
        if match:
            return f"{int(match[1]):04d}-{int(match[2]):02d}-{int(match[3]):02d}"
        match = re.fullmatch(r"(\d{4})[-/.](\d{1,2})", compact)
        if match:
            return f"{int(match[1]):04d}-{int(match[2]):02d}"
        match = re.fullmatch(r"(\d{4})年(\d{1,2})月", compact)
        if match:
            return f"{int(match[1]):04d}-{int(match[2]):02d}"
        match = re.fullmatch(r"(\d{1,2})月(\d{1,2})日", compact)
        if match:
            return f"--{int(match[1]):02d}-{int(match[2]):02d}"
        return compact
    if kind == "version":
        match = re.search(r"\d+(?:\.\d+)+(?:[-+][A-Za-z0-9_.-]+)?", value)
        return match.group(0).lower() if match else re.sub(r"\s+", "", value).lower()
    if kind == "quote":
        return value[1:-1] if len(value) >= 2 else value
    if kind == "code":
        lines = value.splitlines()
        if lines and re.match(r"^ {0,3}(?:`{3,}|~{3,})", lines[0]):
            body = lines[1:]
            if body and re.match(r"^ {0,3}(?:`{3,}|~{3,})\s*$", body[-1]):
                body = body[:-1]
            return "\n".join(body).strip()
        ticks = re.match(r"^(`+)", value)
        if ticks and value.endswith(ticks.group(1)):
            width = len(ticks.group(1))
            return value[width:-width]
        return value
    if kind == "placeholder":
        return re.sub(r"\s+", "", value)
    return value


def make_fact(kind: str, match: re.Match[str]) -> Fact:
    raw = match.group(0)
    return Fact(kind, raw, normalize(kind, raw), match.start(), match.end())


def collect_pattern_facts(
    text: str,
    kind: str,
    patterns: Sequence[re.Pattern[str]],
    blocked: Sequence[tuple[int, int]] = (),
) -> list[Fact]:
    facts: list[Fact] = []
    local_spans: list[tuple[int, int]] = list(blocked)
    for pattern in patterns:
        for match in pattern.finditer(text):
            if overlaps(match.span(), local_spans):
                continue
            fact = make_fact(kind, match)
            facts.append(fact)
            local_spans.append((fact.start, fact.end))
    return facts


def extract_facts(text: str) -> list[Fact]:
    code = collect_pattern_facts(text, "code", [FENCED_CODE_RE])
    code_spans = [(fact.start, fact.end) for fact in code]
    code += collect_pattern_facts(
        text, "code", [DOUBLE_INLINE_CODE_RE, INLINE_CODE_RE], code_spans
    )
    code_spans = [(fact.start, fact.end) for fact in code]

    quotes = collect_pattern_facts(text, "quote", QUOTE_PATTERNS, code_spans)
    protected_spans = code_spans + [(fact.start, fact.end) for fact in quotes]
    placeholders = collect_pattern_facts(
        text, "placeholder", PLACEHOLDER_PATTERNS, protected_spans
    )

    facts = code + quotes + placeholders
    structural_spans = [match.span(1) for match in STRUCTURAL_NUMBER_RE.finditer(text)]
    blocked = (
        protected_spans
        + [(fact.start, fact.end) for fact in placeholders]
        + structural_spans
    )
    for kind, pattern in ATOMIC_PATTERNS:
        new_facts = collect_pattern_facts(text, kind, [pattern], blocked)
        facts.extend(new_facts)
        blocked.extend((fact.start, fact.end) for fact in new_facts)

    return sorted(facts, key=lambda fact: (fact.start, KIND_ORDER[fact.kind], fact.end))


def unmatched_facts(left: Sequence[Fact], right: Sequence[Fact]) -> list[Fact]:
    common = Counter((fact.kind, fact.normalized) for fact in left) & Counter(
        (fact.kind, fact.normalized) for fact in right
    )
    remaining = common.copy()
    unmatched: list[Fact] = []
    for fact in left:
        key = (fact.kind, fact.normalized)
        if remaining[key]:
            remaining[key] -= 1
        else:
            unmatched.append(fact)
    return unmatched


def compare(before: str, after: str) -> Report:
    before_facts = extract_facts(before)
    after_facts = extract_facts(after)
    removed = unmatched_facts(before_facts, after_facts)
    added = unmatched_facts(after_facts, before_facts)

    removed_by_kind: dict[str, list[Fact]] = defaultdict(list)
    added_by_kind: dict[str, list[Fact]] = defaultdict(list)
    for fact in removed:
        removed_by_kind[fact.kind].append(fact)
    for fact in added:
        added_by_kind[fact.kind].append(fact)

    changed: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    additions: list[dict[str, str]] = []
    for kind in KIND_ORDER:
        old = removed_by_kind[kind]
        new = added_by_kind[kind]
        pair_count = min(len(old), len(new))
        changed.extend(
            {"kind": kind, "before": old[index].raw, "after": new[index].raw}
            for index in range(pair_count)
        )
        missing.extend({"kind": kind, "value": fact.raw} for fact in old[pair_count:])
        additions.extend({"kind": kind, "value": fact.raw} for fact in new[pair_count:])

    return Report(missing=missing, changed=changed, added=additions)


def format_report(report: Report, allow_added: bool) -> str:
    status = "ok" if report.ok(allow_added) else "failed"
    lines = [f"fact integrity {status}"]
    for label, records in (
        ("missing", report.missing),
        ("changed", report.changed),
        ("added", report.added),
    ):
        lines.append(f"{label}: {len(records)}")
        for record in records:
            if label == "changed":
                lines.append(
                    f"  [{record['kind']}] {record['before']!r} -> {record['after']!r}"
                )
            else:
                lines.append(f"  [{record['kind']}] {record['value']!r}")
    if allow_added and report.added:
        lines.append("added facts allowed by explicit --allow-added")
    return "\n".join(lines)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def select_markdown_section(text: str, title: str | None) -> str:
    """Return one Markdown section body, or the full text when title is omitted."""
    if not title:
        return text
    lines = text.splitlines(keepends=True)
    heading_re = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*\n?$")
    start: int | None = None
    level: int | None = None
    for index, line in enumerate(lines):
        match = heading_re.match(line)
        if not match:
            continue
        heading = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(2)).strip()
        if start is None and heading == title:
            start = index + 1
            level = len(match.group(1))
            continue
        if start is not None and len(match.group(1)) <= (level or 6):
            return "".join(lines[start:index])
    if start is None:
        raise ValueError(f"Markdown section not found: {title!r}")
    return "".join(lines[start:])


def load_fixture_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for line_number, line in enumerate(read_text(path).splitlines(), start=1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {error}") from error
        missing_keys = {"id", "before", "after", "expected"} - set(case)
        if missing_keys:
            raise ValueError(
                f"{path}:{line_number}: missing keys: {', '.join(sorted(missing_keys))}"
            )
        if case["id"] in seen_ids:
            raise ValueError(f"{path}:{line_number}: duplicate id {case['id']!r}")
        if not isinstance(case["before"], str) or not isinstance(case["after"], str):
            raise ValueError(f"{path}:{line_number}: before/after must be strings")
        required_expected = {"ok", "missing", "changed", "added"}
        if not isinstance(case["expected"], dict) or set(case["expected"]) != required_expected:
            raise ValueError(
                f"{path}:{line_number}: expected must contain exactly "
                "ok, missing, changed, added"
            )
        seen_ids.add(case["id"])
        cases.append(case)
    if not cases:
        raise ValueError(f"{path}: no fixture cases")
    return cases


def run_fixtures(path: Path, json_output: bool) -> int:
    cases = load_fixture_cases(path)
    failures: list[dict[str, Any]] = []
    for case in cases:
        allow_added = bool(case.get("allow_added", False))
        actual = compare(case["before"], case["after"]).as_dict(allow_added)
        expected = case["expected"]
        differences = {
            key: {"expected": expected[key], "actual": actual.get(key)}
            for key in expected
            if actual.get(key) != expected[key]
        }
        if differences:
            failures.append({"id": case["id"], "differences": differences})

    result = {
        "ok": not failures,
        "fixture": str(path),
        "cases": len(cases),
        "failures": failures,
    }
    if json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif failures:
        print(f"fact-integrity fixtures failed: {len(failures)}/{len(cases)}", file=sys.stderr)
        for failure in failures:
            print(f"- {failure['id']}: {json.dumps(failure['differences'], ensure_ascii=False)}", file=sys.stderr)
    else:
        print(f"fact-integrity fixtures ok: {len(cases)} cases")
    return 0 if not failures else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fail when protected facts are missing, changed, or newly added."
    )
    parser.add_argument("before", nargs="?", type=Path, help="source text file")
    parser.add_argument("after", nargs="?", type=Path, help="rewritten text file")
    parser.add_argument(
        "--fixtures",
        nargs="?",
        const=DEFAULT_FIXTURES,
        type=Path,
        metavar="JSONL",
        help="run JSONL self-tests (defaults to tests/fixtures/20-fact-integrity-cases.jsonl)",
    )
    parser.add_argument(
        "--allow-added",
        action="store_true",
        help="allow added facts; intended only for independent research mode",
    )
    parser.add_argument(
        "--before-section",
        metavar="HEADING",
        help="compare only this Markdown section in the before file",
    )
    parser.add_argument(
        "--after-section",
        metavar="HEADING",
        help="compare only this Markdown section in the after file",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.fixtures is not None:
            if args.before is not None or args.after is not None:
                parser.error("--fixtures cannot be combined with before/after files")
            if args.allow_added:
                parser.error("fixture cases declare allow_added individually")
            if args.before_section or args.after_section:
                parser.error("section selectors cannot be combined with --fixtures")
            return run_fixtures(args.fixtures, args.json)

        if args.before is None or args.after is None:
            parser.error("provide both before and after files, or use --fixtures")
        before_text = select_markdown_section(read_text(args.before), args.before_section)
        after_text = select_markdown_section(read_text(args.after), args.after_section)
        report = compare(before_text, after_text)
        if args.json:
            print(json.dumps(report.as_dict(args.allow_added), ensure_ascii=False, indent=2))
        else:
            print(format_report(report, args.allow_added))
        return 0 if report.ok(args.allow_added) else 1
    except (OSError, ValueError) as error:
        print(f"fact integrity error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

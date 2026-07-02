#!/usr/bin/env python3
"""Compressors for test-runner output (pytest, npm test/jest).

Strategy: the FAILURES section (and everything after it) is preserved
VERBATIM — we only drop the progress/collection section above it. For
all-green runs, only the final summary line survives. This guarantees
spec success criterion 3 (zero information loss on failures) structurally
rather than by pattern-matching individual failure lines.
"""
import re

PARSER_VERSION = "1.0.0"

_PYTEST_SECTION_RE = re.compile(r"^=+ (FAILURES|ERRORS) =+$")
_PYTEST_SUMMARY_RE = re.compile(r"^=+ .*(passed|failed|error|no tests ran).* =+$")
_NPM_MARKER_RE = re.compile(r"(Tests:|Test Suites:|✓|✕|√|passing|failing)")
_NPM_PASS_LINE_RE = re.compile(r"^\s*(✓|√)|^\s*PASS\s")


def compress_pytest(raw: str) -> str | None:
    if "test session starts" not in raw:
        return None
    lines = raw.splitlines()
    fail_idx = next((i for i, l in enumerate(lines)
                     if _PYTEST_SECTION_RE.match(l.strip())), None)
    if fail_idx is not None:
        # FAILURES → end, verbatim. Savings come from dropping everything above.
        return "\n".join(lines[fail_idx:])
    summary = [l for l in lines if _PYTEST_SUMMARY_RE.match(l.strip())]
    return "\n".join(summary) if summary else None


def compress_npm_test(raw: str) -> str | None:
    if not _NPM_MARKER_RE.search(raw):
        return None
    kept, passed = [], 0
    for line in raw.splitlines():
        s = line.rstrip()
        if _NPM_PASS_LINE_RE.match(s):
            passed += 1
            continue
        if not s:
            continue
        kept.append(s)  # everything not provably a pass-line is kept
    if passed:
        kept.append(f"[{passed} passing checks omitted]")
    return "\n".join(kept)

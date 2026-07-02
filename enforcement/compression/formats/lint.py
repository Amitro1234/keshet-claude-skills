#!/usr/bin/env python3
"""Compressors for linter output (eslint stylish format, ruff check).

Both formats are already fairly dense; the win here is dropping blank
lines, deprecation banners, and fix-hint footers while keeping every
violation line (anything carrying a file:line reference) verbatim.
"""
import re

PARSER_VERSION = "1.0.0"

_ESLINT_LOC_RE = re.compile(r"^\s+\d+:\d+\s+(error|warning)")
_RUFF_VIOLATION_RE = re.compile(r"^\S+:\d+:\d+: \w+")
_RUFF_SUMMARY_RE = re.compile(r"^Found \d+ error")


def compress_eslint(raw: str) -> str | None:
    lines = raw.splitlines()
    if not any(_ESLINT_LOC_RE.match(l) for l in lines):
        return None
    return "\n".join(l.rstrip() for l in lines if l.strip())


def compress_ruff(raw: str) -> str | None:
    lines = raw.splitlines()
    violations = [l for l in lines if _RUFF_VIOLATION_RE.match(l)]
    summary = [l for l in lines if _RUFF_SUMMARY_RE.match(l)]
    if not violations and not summary:
        return None
    return "\n".join(violations + summary)

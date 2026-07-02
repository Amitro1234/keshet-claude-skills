#!/usr/bin/env python3
"""Compressors for linter output (eslint stylish format, ruff check).

Both formats are already fairly dense; the win here is dropping blank
lines, deprecation banners, and fix-hint footers while keeping every
violation line (anything carrying a file:line reference) verbatim.
"""
import re

PARSER_VERSION = "1.0.0"

_ESLINT_LOC_RE = re.compile(r"^\s+\d+:\d+\s+(error|warning)")
_RUFF_VIOLATION_RE = re.compile(r"^.+?:\d+:\d+: \w+")
_RUFF_SUMMARY_RE = re.compile(r"^Found \d+ error")
_RUFF_NOISE_RE = re.compile(r"^warning: |^\[\*\] ")


def compress_eslint(raw: str) -> str | None:
    lines = raw.splitlines()
    if not any(_ESLINT_LOC_RE.match(l) for l in lines):
        return None
    return "\n".join(l.rstrip() for l in lines if l.strip())


def compress_ruff(raw: str) -> str | None:
    lines = raw.splitlines()
    has_violation = any(_RUFF_VIOLATION_RE.match(l) for l in lines)
    has_summary = any(_RUFF_SUMMARY_RE.match(l) for l in lines)
    if not has_violation and not has_summary:
        return None
    # Conservative: drop only proven noise (deprecation banners, fix hints,
    # blank lines); keep everything else — incl. multi-line parse-error
    # context blocks, which are diagnostic payload, not decoration.
    kept = [l.rstrip() for l in lines if l.strip() and not _RUFF_NOISE_RE.match(l)]
    return "\n".join(kept)

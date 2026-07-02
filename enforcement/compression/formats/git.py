#!/usr/bin/env python3
"""Compressors for git command output.

Contract (same for every parser in formats/): pure function, takes the raw
output string, returns the compressed string — or None when the input
doesn't match the expected shape. None ALWAYS means untouched passthrough;
a parser must never guess.

Safety rule for diff (spec success criterion 3, absolute): every changed
line, hunk header, and file header is preserved verbatim. Only proven
metadata noise ('index abc..def 100644' lines) is dropped.
"""
import re

PARSER_VERSION = "1.0.0"

_STATUS_NOISE_PREFIXES = (
    '  (use "git',
    '  (commit or discard',
    '  (all conflicts fixed',
    'no changes added to commit',
    'nothing added to commit',
)

_COMMIT_RE = re.compile(r"^commit ([0-9a-f]{40})\b")


def compress_git_status(raw: str) -> str | None:
    lines = raw.splitlines()
    if not lines:
        return None
    first = lines[0]
    if not (first.startswith("On branch") or first.startswith("HEAD detached")):
        return None
    kept = []
    for line in lines:
        s = line.rstrip()
        if not s:
            continue
        if any(s.startswith(p) for p in _STATUS_NOISE_PREFIXES):
            continue
        kept.append(s)
    return "\n".join(kept)


def compress_git_log(raw: str) -> str | None:
    if not _COMMIT_RE.search(raw):
        return None  # already --oneline or a custom format; don't touch
    out = []
    sha = author = date = msg = None

    def flush():
        if sha:
            out.append(f"{sha[:8]} {msg or '(no message)'} ({author or '?'}, {date or '?'})")

    for line in raw.splitlines():
        m = _COMMIT_RE.match(line)
        if m:
            flush()
            sha, author, date, msg = m.group(1), None, None, None
        elif line.startswith("Author:"):
            author = line[len("Author:"):].strip().split("<")[0].strip()
        elif line.startswith("Date:"):
            date = line[len("Date:"):].strip()
        elif line.startswith("    ") and msg is None and line.strip():
            msg = line.strip()  # first subject line only; body dropped
    flush()
    return "\n".join(out) if out else None


def compress_git_diff(raw: str) -> str | None:
    if "diff --git" not in raw:
        return None
    # Conservative by design: drop ONLY 'index ...' metadata lines.
    kept = [l for l in raw.splitlines() if not l.startswith("index ")]
    return "\n".join(kept)

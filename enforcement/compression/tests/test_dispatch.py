#!/usr/bin/env python3
"""Routing tests: command string -> (kind, parser, version) or None."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from compression import dispatch  # noqa: E402

CASES = [
    # (tool_name, command, expected_kind_or_None)
    ("Bash", "git status", "git-status"),
    ("Bash", "git status --short", "git-status"),
    ("Bash", "git diff HEAD~1", "git-diff"),
    ("Bash", "git log -n 20", "git-log"),
    ("Bash", "pytest -v tests/", "pytest"),
    ("Bash", "python -m pytest enforcement/tests/", "pytest"),
    ("Bash", "npm test", "npm-test"),
    ("Bash", "npm run test -- --coverage", "npm-test"),
    ("Bash", "npx eslint src/", "eslint"),
    ("Bash", "ruff check .", "ruff"),
    ("Bash", "git push origin main", None),          # git, but not a covered subcommand
    ("Bash", "cat file.py", None),                    # no parser
    ("Bash", "echo pytest is great", None),           # 'pytest' not as a command word...
    ("Read", "git status", None),                     # wrong tool
    ("PowerShell", "git status", None),               # MVP is Bash-matcher only
]


def test_routing_table():
    for tool, cmd, expected in CASES:
        entry = dispatch.route(tool, cmd)
        actual = entry[0] if entry else None
        assert actual == expected, f"{tool}:{cmd!r} -> {actual}, expected {expected}"


def test_route_returns_callable_and_version():
    kind, fn, version = dispatch.route("Bash", "git status")
    assert callable(fn)
    assert isinstance(version, str) and version


if __name__ == "__main__":
    test_routing_table()
    print("PASS: test_routing_table")
    test_route_returns_callable_and_version()
    print("PASS: test_route_returns_callable_and_version")
    print("all dispatch tests passed")

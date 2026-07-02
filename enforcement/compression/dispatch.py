#!/usr/bin/env python3
"""Routes (tool_name, command) to a format parser.

MVP covers Bash only — the settings.json matcher is 'Bash' too, so this
module double-checks what the matcher already enforces (defense in depth,
and unit-testable without a live hook).

To add a parser later: write compress_<x>() in formats/, add one row to
_ROUTES. Nothing else changes — the hook and stats are parser-agnostic.
"""
import re

from .formats import git, lint, test_runners

# A "command position" is: start of string, or right after && / ; / |
_CMD_START = r"(?:^|&&\s*|;\s*|\|\s*)"

_ROUTES = [
    ("git-status", re.compile(_CMD_START + r"git\s+status\b"), git.compress_git_status, git.PARSER_VERSION),
    ("git-diff",   re.compile(_CMD_START + r"git\s+diff\b"),   git.compress_git_diff,   git.PARSER_VERSION),
    ("git-log",    re.compile(_CMD_START + r"git\s+log\b"),    git.compress_git_log,    git.PARSER_VERSION),
    ("pytest",     re.compile(_CMD_START + r"(?:python\d?\s+-m\s+)?pytest\b"),
     test_runners.compress_pytest, test_runners.PARSER_VERSION),
    ("npm-test",   re.compile(_CMD_START + r"(?:npm\s+(?:run\s+)?test|yarn\s+test)\b"),
     test_runners.compress_npm_test, test_runners.PARSER_VERSION),
    ("eslint",     re.compile(_CMD_START + r"(?:npx\s+)?eslint\b"), lint.compress_eslint, lint.PARSER_VERSION),
    ("ruff",       re.compile(_CMD_START + r"(?:npx\s+)?ruff\s+check\b"), lint.compress_ruff, lint.PARSER_VERSION),
]


def route(tool_name: str, command: str):
    if tool_name != "Bash":
        return None
    cmd = command.strip()
    for kind, pattern, fn, version in _ROUTES:
        if pattern.search(cmd):
            return kind, fn, version
    return None

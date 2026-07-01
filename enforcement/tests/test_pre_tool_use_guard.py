#!/usr/bin/env python3
"""
Repeatable automated tests for enforcement/hooks/pre_tool_use_guard.py.

Run with: python3 -m pytest enforcement/tests/test_pre_tool_use_guard.py -v
(or just: python3 enforcement/tests/test_pre_tool_use_guard.py -- it also
runs standalone without pytest installed, see __main__ block).

These are REAL tests -- they invoke the actual hook script as a subprocess
with crafted stdin, exactly as Claude Code would, and check the real exit
code. Unlike the SKILL.md behavioral scenarios (see enforcement/tests/
skill-scenarios.md), this file tests executable code, so it's fully
deterministic and safe to run in CI on every change to the hook.

Run this after ANY edit to pre_tool_use_guard.py or to
docs/approved-mcp-connectors.md (the allowlist is currently hand-duplicated
into the hook -- see enforcement/README.md open item #1 -- so a connector
added to the doc but not the hook will silently fail these tests, which is
exactly the drift-detection purpose of this suite).
"""

import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "pre_tool_use_guard.py"

CASES = [
    # (name, payload_dict_or_None_for_malformed, expected "allow"/"block")
    ("cat .env (secret content)",
     {"tool_name": "Bash", "tool_input": {"command": "cat .env"}}, "block"),
    ("cat .env.production (dotted variant)",
     {"tool_name": "Bash", "tool_input": {"command": "cat .env.production"}}, "block"),
    ("grep for API_KEY",
     {"tool_name": "Bash", "tool_input": {"command": "grep -r API_KEY ."}}, "block"),
    ("printenv",
     {"tool_name": "Bash", "tool_input": {"command": "printenv"}}, "block"),
    ("rm -rf / (root wipe)",
     {"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}, "block"),
    ("fork bomb",
     {"tool_name": "Bash", "tool_input": {"command": ":(){ :|:& };:"}}, "block"),
    ("history -c",
     {"tool_name": "Bash", "tool_input": {"command": "history -c"}}, "block"),
    ("mkfs on a device",
     {"tool_name": "Bash", "tool_input": {"command": "mkfs.ext4 /dev/sdb1"}}, "block"),
    ("dd raw disk write",
     {"tool_name": "Bash", "tool_input": {"command": "dd if=/dev/zero of=/dev/sda"}}, "block"),
    ("approved MCP server (slack)",
     {"tool_name": "mcp__slack__send_message", "tool_input": {"channel": "general", "text": "hi"}}, "allow"),
    ("unapproved MCP server (openai)",
     {"tool_name": "mcp__openai__chat_completion", "tool_input": {"prompt": "hi"}}, "block"),
    ("unapproved MCP server (random-scraper)",
     {"tool_name": "mcp__random-scraper__fetch", "tool_input": {"url": "http://example.com"}}, "block"),
    ("normal safe git command",
     {"tool_name": "Bash", "tool_input": {"command": "git status"}}, "allow"),
    ("normal file read",
     {"tool_name": "Read", "tool_input": {"file_path": "src/app.py"}}, "allow"),
    ("npm install (not this hook's job -- settings.json ask-tier handles it)",
     {"tool_name": "Bash", "tool_input": {"command": "npm install express"}}, "allow"),
    ("rm -rf ./node_modules (safe, scoped delete)",
     {"tool_name": "Bash", "tool_input": {"command": "rm -rf ./node_modules"}}, "allow"),
    ("cat env_config.py (must NOT false-positive on filename containing 'env')",
     {"tool_name": "Bash", "tool_input": {"command": "cat env_config.py"}}, "allow"),
    ("malformed/empty stdin (fail-open by design -- see docstring in the hook)",
     None, "allow"),
    # --- Known, documented gaps -- these are EXPECTED to currently fail. ---
    # They exist so nobody re-discovers the gap by accident and thinks it's
    # a regression; they document a real limitation instead. If one of these
    # ever starts passing, update enforcement/README.md's "partially hard"
    # section -- the gap you closed is worth writing down.
    ("KNOWN GAP: python inline read of .env bypasses content-pattern check",
     {"tool_name": "Bash", "tool_input": {
         "command": "python3 -c \"print(open('.env').read())\""
     }}, "allow", True),  # 5th element: xfail=True
]


def run_hook(payload) -> int:
    stdin_data = "" if payload is None else json.dumps(payload)
    proc = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=stdin_data,
        capture_output=True,
        text=True,
    )
    return proc.returncode


def _check(name, payload, expected, xfail=False):
    code = run_hook(payload)
    actual = "allow" if code == 0 else "block"
    passed = actual == expected
    if xfail:
        # An xfail case is expected to NOT match -- i.e. we expect the gap.
        # If it suddenly DOES match "block", that's good news, report it as such.
        if actual == "block":
            return True, f"XPASS (gap appears closed now): {name}"
        return True, f"XFAIL (known gap, as expected): {name}"
    return passed, f"{'PASS' if passed else 'FAIL'}: {name} (expected={expected}, got={actual})"


def test_all_cases():
    """Single pytest entry point iterating all CASES (also runnable standalone)."""
    failures = []
    for case in CASES:
        name, payload, expected = case[0], case[1], case[2]
        xfail = case[3] if len(case) > 3 else False
        ok, msg = _check(name, payload, expected, xfail)
        print(msg)
        if not ok:
            failures.append(msg)
    assert not failures, f"{len(failures)} hook test(s) failed:\n" + "\n".join(failures)


if __name__ == "__main__":
    failures = []
    for case in CASES:
        name, payload, expected = case[0], case[1], case[2]
        xfail = case[3] if len(case) > 3 else False
        ok, msg = _check(name, payload, expected, xfail)
        print(msg)
        if not ok:
            failures.append(msg)
    print(f"\n{len(CASES) - len(failures)}/{len(CASES)} passed.")
    sys.exit(1 if failures else 0)

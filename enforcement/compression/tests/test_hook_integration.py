#!/usr/bin/env python3
"""Integration tests: invoke the hook as a subprocess with crafted stdin,
exactly as Claude Code would — same harness style as
enforcement/tests/test_pre_tool_use_guard.py.

Contract under test:
  - compression   -> stdout JSON with hookSpecificOutput.updatedToolOutput, exit 0
  - passthrough   -> empty stdout, exit 0
  - ANY failure   -> empty stdout, exit 0 (fail-open; never non-zero)
Every case must also append exactly one stats event.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# tests/ -> compression/ -> enforcement/ ; hook lives at enforcement/hooks/
HOOK = Path(__file__).resolve().parents[2] / "hooks" / "post_tool_use_compressor.py"
FIXTURES = Path(__file__).parent / "fixtures"
PYTEST_GOLDEN = (FIXTURES / "pytest_failure_raw.txt").read_text(encoding="utf-8")


def run_hook(payload, env_extra=None):
    """Returns (exit_code, stdout, stats_events)."""
    with tempfile.TemporaryDirectory() as td:
        stats_path = os.path.join(td, "stats.jsonl")
        env = dict(os.environ, KESHET_COMPRESSION_STATS_PATH=stats_path)
        if env_extra:
            env.update(env_extra)
        stdin = payload if isinstance(payload, str) else json.dumps(payload)
        proc = subprocess.run([sys.executable, str(HOOK)], input=stdin,
                              capture_output=True, text=True, env=env,
                              encoding="utf-8")
        events = []
        if os.path.exists(stats_path):
            for line in Path(stats_path).read_text(encoding="utf-8").splitlines():
                events.append(json.loads(line))
        return proc.returncode, proc.stdout.strip(), events


def bash_event(command, stdout_text):
    return {"tool_name": "Bash",
            "tool_input": {"command": command},
            "tool_response": {"stdout": stdout_text, "stderr": "", "interrupted": False}}


def test_pytest_output_gets_compressed():
    code, out, events = run_hook(bash_event("pytest -v tests/", PYTEST_GOLDEN))
    assert code == 0
    body = json.loads(out)
    compressed = body["hookSpecificOutput"]["updatedToolOutput"]
    assert body["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert "FAILED tests/test_events.py::test_event_dedup_by_external_id" in compressed
    assert len(compressed) < len(PYTEST_GOLDEN) * 0.9
    assert len(events) == 1 and events[0]["kind"] == "pytest" and events[0]["error"] is None


def test_uncovered_command_passthrough():
    code, out, events = run_hook(bash_event("cat README.md", "file contents here"))
    assert code == 0 and out == ""
    assert events[0]["skipped"] == "no_parser"


def test_nocompress_flag_in_command():
    code, out, events = run_hook(bash_event("NOCOMPRESS=1 pytest -v", PYTEST_GOLDEN))
    assert code == 0 and out == ""
    assert events[0]["skipped"] == "nocompress_flag"


def test_env_kill_switch():
    code, out, events = run_hook(bash_event("pytest -v", PYTEST_GOLDEN),
                                 env_extra={"KESHET_NOCOMPRESS": "1"})
    assert code == 0 and out == ""
    assert events[0]["skipped"] == "env_disabled"


def test_size_ceiling_passthrough():
    huge = "x" * 2_000_001
    code, out, events = run_hook(bash_event("git status", huge))
    assert code == 0 and out == ""
    assert events[0]["skipped"] == "size_ceiling"


def test_no_gain_passthrough():
    # 'On branch main' alone: parser succeeds but result isn't >=10% smaller
    code, out, events = run_hook(bash_event("git status", "On branch main"))
    assert code == 0 and out == ""
    assert events[0]["skipped"] in ("no_gain", "parser_declined")


def test_malformed_stdin_fails_open():
    code, out, _ = run_hook("this is not json {{{")
    assert code == 0 and out == ""


def test_string_tool_response_also_works():
    payload = {"tool_name": "Bash", "tool_input": {"command": "pytest -v"},
               "tool_response": PYTEST_GOLDEN}  # some tool shapes are plain strings
    code, out, events = run_hook(payload)
    assert code == 0
    assert json.loads(out)["hookSpecificOutput"]["updatedToolOutput"]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS: {name}")
    print("all hook integration tests passed")

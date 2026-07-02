#!/usr/bin/env python3
"""Keshet PostToolUse compressor hook.

Purpose
-------
Companion to pre_tool_use_guard.py (which blocks dangerous calls BEFORE
they run). This hook runs AFTER a tool call and compresses known-verbose
output (git/pytest/npm-test/lint) before it enters Claude's context.
Design doc: docs/superpowers/specs/2026-07-02-command-output-compressor-design.md

Contract (verify against https://code.claude.com/docs/en/hooks before
production rollout — same caveat as pre_tool_use_guard.py):
  - stdin: JSON {"tool_name", "tool_input", "tool_response", ...}
  - to REPLACE output: print {"hookSpecificOutput": {"hookEventName":
    "PostToolUse", "updatedToolOutput": "<text>"}} to stdout, exit 0
  - to PASS THROUGH: print nothing, exit 0
  - this hook NEVER exits non-zero. Fail-open is absolute: worst case is
    "no savings this call", never "Claude saw wrong/missing output".

Deployment layout must mirror the repo: hook in <root>/hooks/, package in
<root>/compression/ (works for both enforcement/ and .claude/).
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from compression import dispatch, stats  # noqa: E402

SIZE_CEILING = 2_000_000          # chars; above this, don't even try (latency guard)
MIN_GAIN_RATIO = 0.90             # emit only if compressed < 90% of raw
NOCOMPRESS_RE = re.compile(r"\bNOCOMPRESS\b")
ENV_KILL_SWITCH = "KESHET_NOCOMPRESS"


def extract_output_text(tool_response):
    """tool_response shape varies by tool; handle dict-with-stdout and plain str."""
    if isinstance(tool_response, str):
        return tool_response
    if isinstance(tool_response, dict):
        for key in ("stdout", "output", "content", "text"):
            v = tool_response.get(key)
            if isinstance(v, str) and v:
                return v
    return None


def main() -> None:
    start = time.perf_counter()
    sink = stats.LocalFileSink()

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Fail open, but still leave one observability event (the sink's
        # write is itself fail-open, so this cannot raise).
        sink.write(stats.make_event(
            "", None, None, 0, 0,
            round((time.perf_counter() - start) * 1000, 2),
            skipped="malformed_stdin"))
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command", ""))
    raw = extract_output_text(payload.get("tool_response"))

    def log(kind=None, version=None, compressed_chars=None, skipped=None, error=None):
        raw_chars = len(raw) if raw is not None else 0
        sink.write(stats.make_event(
            tool_name, kind, version, raw_chars,
            compressed_chars if compressed_chars is not None else raw_chars,
            round((time.perf_counter() - start) * 1000, 2),
            skipped=skipped, error=error))

    if raw is None:
        log(skipped="no_text_output")
        sys.exit(0)
    if os.environ.get(ENV_KILL_SWITCH):
        log(skipped="env_disabled")
        sys.exit(0)
    if NOCOMPRESS_RE.search(command):
        log(skipped="nocompress_flag")
        sys.exit(0)
    if len(raw) > SIZE_CEILING:
        log(skipped="size_ceiling")
        sys.exit(0)

    entry = dispatch.route(tool_name, command)
    if entry is None:
        log(skipped="no_parser")
        sys.exit(0)
    kind, parser_fn, version = entry

    try:
        compressed = parser_fn(raw)
    except Exception as e:  # noqa: BLE001 — fail-open IS the contract here
        log(kind=kind, version=version, error=f"{type(e).__name__}: {e}")
        sys.exit(0)

    if compressed is None:
        log(kind=kind, version=version, skipped="parser_declined")
        sys.exit(0)
    if len(compressed) >= len(raw) * MIN_GAIN_RATIO:
        log(kind=kind, version=version, skipped="no_gain")
        sys.exit(0)

    out_json = json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "updatedToolOutput": compressed,
        }
    }, ensure_ascii=True)  # ASCII-only JSON: valid on ANY console/pipe encoding
    try:
        print(out_json)
    except Exception as e:
        log(kind=kind, version=version, error=f"emit_failed: {type(e).__name__}")
        sys.exit(0)
    log(kind=kind, version=version, compressed_chars=len(compressed))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException:
        # Absolute fail-open: NO failure of this hook may ever block or
        # alter the tool call it observes.
        sys.exit(0)

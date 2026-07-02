#!/usr/bin/env python3
"""Stats sink for the command-output compressor.

Every hook invocation logs exactly one event here — compressed, skipped,
or errored — so report.py can show the denominator (total invocations),
not just wins. See docs/superpowers/specs/2026-07-02-command-output-
compressor-design.md, "Statistics and reporting".

The sink abstraction exists so a Phase 2 centralized sink (App Insights /
Blob upload) can be added without touching parser code. MVP ships
LocalFileSink only.
"""
import json
import os
import time
from pathlib import Path

DEFAULT_PATH = ".claude/compression-stats.jsonl"
ENV_PATH_OVERRIDE = "KESHET_COMPRESSION_STATS_PATH"


class StatsSink:
    def write(self, event: dict) -> None:
        raise NotImplementedError


class LocalFileSink(StatsSink):
    """MVP sink: appends JSON lines to a per-machine, gitignored file."""

    def __init__(self, path: str | None = None):
        self.path = Path(path or os.environ.get(ENV_PATH_OVERRIDE) or DEFAULT_PATH)

    def write(self, event: dict) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception:
            # Stats writes are fully fail-open. Losing one event is always better
            # than breaking the hook — including TypeError from non-serializable values.
            pass


def make_event(tool, kind, parser_version, raw_chars, compressed_chars,
               duration_ms, skipped=None, error=None) -> dict:
    return {
        "ts": round(time.time(), 3),
        "tool": tool,
        "kind": kind,
        "parser_version": parser_version,
        "raw_chars": raw_chars,
        "compressed_chars": compressed_chars,
        # English-biased rough heuristic (chars/4) — for trend reporting
        # only, never presented as an exact count or used for billing.
        "raw_tokens_est": raw_chars // 4,
        "compressed_tokens_est": compressed_chars // 4,
        "duration_ms": duration_ms,
        "skipped": skipped,
        "error": error,
    }

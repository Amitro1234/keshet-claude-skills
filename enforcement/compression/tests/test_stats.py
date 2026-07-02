#!/usr/bin/env python3
"""Unit tests for enforcement/compression/stats.py. Stdlib only.
Run: python -m pytest enforcement/compression/tests/test_stats.py -v
(or standalone: python enforcement/compression/tests/test_stats.py)"""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from compression import stats  # noqa: E402


def test_make_event_fields():
    e = stats.make_event("Bash", "pytest", "1.0.0", 8000, 800, 12.5)
    assert e["tool"] == "Bash"
    assert e["kind"] == "pytest"
    assert e["parser_version"] == "1.0.0"
    assert e["raw_chars"] == 8000
    assert e["compressed_chars"] == 800
    assert e["raw_tokens_est"] == 2000       # chars // 4
    assert e["compressed_tokens_est"] == 200
    assert e["duration_ms"] == 12.5
    assert e["skipped"] is None
    assert e["error"] is None
    assert isinstance(e["ts"], float)


def test_make_event_skipped_and_error():
    e = stats.make_event("Bash", None, None, 100, 100, 1.0,
                         skipped="no_parser", error=None)
    assert e["kind"] is None
    assert e["skipped"] == "no_parser"


def test_local_file_sink_appends_jsonl():
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "sub", "stats.jsonl")  # parent dir must be auto-created
        sink = stats.LocalFileSink(path)
        sink.write({"a": 1})
        sink.write({"b": "עברית"})  # ensure_ascii=False must hold non-ASCII
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        assert json.loads(lines[0]) == {"a": 1}
        assert json.loads(lines[1]) == {"b": "עברית"}


def test_local_file_sink_env_override():
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "env-stats.jsonl")
        os.environ["KESHET_COMPRESSION_STATS_PATH"] = path
        try:
            sink = stats.LocalFileSink()
            assert str(sink.path) == path
        finally:
            del os.environ["KESHET_COMPRESSION_STATS_PATH"]


def test_sink_write_never_raises_on_bad_path():
    # Fail-open: an unwritable path must not raise (stats must never break the hook)
    sink = stats.LocalFileSink("Z:\\nonexistent-drive-hopefully\\stats.jsonl"
                               if os.name == "nt" else "/proc/definitely/not/writable.jsonl")
    sink.write({"a": 1})  # must not raise


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS: {name}")
    print("all stats tests passed")

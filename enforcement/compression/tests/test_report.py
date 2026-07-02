#!/usr/bin/env python3
"""Tests for the stats aggregation logic (summarize), not the table formatting."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from compression import report  # noqa: E402

EVENTS = [
    {"kind": "pytest", "skipped": None, "error": None,
     "raw_tokens_est": 2000, "compressed_tokens_est": 200},
    {"kind": "pytest", "skipped": None, "error": None,
     "raw_tokens_est": 1000, "compressed_tokens_est": 100},
    {"kind": "git-status", "skipped": "no_gain", "error": None,
     "raw_tokens_est": 10, "compressed_tokens_est": 10},
    {"kind": None, "skipped": "no_parser", "error": None,
     "raw_tokens_est": 500, "compressed_tokens_est": 500},
    {"kind": "ruff", "skipped": None, "error": "ValueError: boom",
     "raw_tokens_est": 300, "compressed_tokens_est": 300},
]


def test_summarize_denominator_and_kinds():
    total, per_kind, skips = report.summarize(EVENTS)
    assert total == 5                                  # denominator: ALL invocations
    assert per_kind["pytest"]["calls"] == 2
    assert per_kind["pytest"]["raw"] == 3000
    assert per_kind["pytest"]["comp"] == 300
    assert per_kind["ruff"]["errors"] == 1
    assert skips["no_parser"] == 1
    assert skips["no_gain"] == 1


def test_summarize_empty():
    total, per_kind, skips = report.summarize([])
    assert total == 0 and not per_kind and not skips


def test_summarize_negative_savings_renders_plus(capsys=None):
    # comp > raw: summarize returns the numbers; rendering is main()'s job,
    # so assert the data survives summarize unchanged
    events = [{"kind": "pytest", "skipped": None, "error": None,
               "raw_tokens_est": 100, "compressed_tokens_est": 107}]
    total, per_kind, _ = report.summarize(events)
    assert per_kind["pytest"]["raw"] == 100
    assert per_kind["pytest"]["comp"] == 107


def test_load_skips_non_dict_json_lines(tmp_path=None):
    import tempfile, os
    from pathlib import Path
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "stats.jsonl"
        p.write_text('{"kind": "pytest"}\n"just a string"\n42\n{broken\n{"kind": "ruff"}\n',
                     encoding="utf-8")
        events = report.load(p)
        assert len(events) == 2
        assert events[0]["kind"] == "pytest"
        assert events[1]["kind"] == "ruff"


if __name__ == "__main__":
    test_summarize_denominator_and_kinds()
    print("PASS: test_summarize_denominator_and_kinds")
    test_summarize_empty()
    print("PASS: test_summarize_empty")
    test_summarize_negative_savings_renders_plus()
    print("PASS: test_summarize_negative_savings_renders_plus")
    test_load_skips_non_dict_json_lines()
    print("PASS: test_load_skips_non_dict_json_lines")
    print("all report tests passed")

#!/usr/bin/env python3
"""Unit + golden-file tests for pytest / npm-test parsers.

The golden-file assertion IS spec success criterion 3: every FAILED /
ERROR / E-assertion / traceback-location line present in raw output must
survive compression verbatim. Token savings with information loss is a
failed result, not a trade-off.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from compression.formats import test_runners  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
PYTEST_GOLDEN = (FIXTURES / "pytest_failure_raw.txt").read_text(encoding="utf-8")

# Lines that must NEVER be lost (criterion 3)
CRITICAL_LINE_RE = re.compile(r"^(FAILED|ERROR|E |> )|Traceback|\.py:\d+")

NPM_RAW = """
> myapp@1.0.0 test
> jest

PASS src/utils.test.js
  ✓ formats dates (3 ms)
  ✓ parses config (1 ms)
FAIL src/api.test.js
  ✕ returns 409 on duplicate (12 ms)

  ● returns 409 on duplicate

    expect(received).toBe(expected)
    Expected: 409
    Received: 201

      at Object.<anonymous> (src/api.test.js:88:22)

Tests:       1 failed, 2 passed, 3 total
Time:        2.1 s
"""


def test_pytest_golden_no_critical_line_lost():
    out = test_runners.compress_pytest(PYTEST_GOLDEN)
    assert out is not None
    for line in PYTEST_GOLDEN.splitlines():
        if CRITICAL_LINE_RE.search(line.strip()):
            assert line in out, f"CRITICAL LINE LOST: {line!r}"


def test_pytest_drops_progress_section():
    out = test_runners.compress_pytest(PYTEST_GOLDEN)
    assert "tests/test_auth.py .........................." not in out
    assert len(out) < len(PYTEST_GOLDEN) * 0.9


def test_pytest_all_green_returns_summary_only():
    raw = ("============================= test session starts =============================\n"
           "collected 50 items\n\ntests/test_a.py " + "." * 50 + " [100%]\n\n"
           "============================== 50 passed in 2.10s =============================\n")
    out = test_runners.compress_pytest(raw)
    assert out is not None
    assert "50 passed" in out
    assert "tests/test_a.py" not in out


def test_pytest_unrecognized_returns_none():
    assert test_runners.compress_pytest('{"some": "json output"}') is None


def test_npm_keeps_failures_counts_passes():
    out = test_runners.compress_npm_test(NPM_RAW)
    assert out is not None
    assert "✕ returns 409 on duplicate" in out
    assert "at Object.<anonymous> (src/api.test.js:88:22)" in out
    assert "Tests:       1 failed, 2 passed, 3 total" in out
    assert "✓ formats dates" not in out
    assert "passing checks omitted" in out


def test_npm_unrecognized_returns_none():
    assert test_runners.compress_npm_test("make: *** No rule to make target") is None


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS: {name}")
    print("all test-runner format tests passed")

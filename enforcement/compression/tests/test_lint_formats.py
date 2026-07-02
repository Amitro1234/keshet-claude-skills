#!/usr/bin/env python3
"""Unit tests for eslint/ruff parsers. Every violation line (file:line:col)
must survive verbatim — only decoration (blank lines, fix hints) is dropped."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from compression.formats import lint  # noqa: E402

ESLINT_RAW = """
C:\\repo\\src\\api.js
  12:5   error    'resp' is assigned a value but never used   no-unused-vars
  88:22  warning  Unexpected console statement                no-console

C:\\repo\\src\\utils.js
  3:1    error    Parsing error: Unexpected token

✖ 3 problems (2 errors, 1 warning)
"""

RUFF_RAW = """warning: The top-level linter settings are deprecated.
src/api.py:12:5: F841 Local variable `resp` is assigned to but never used
src/api.py:88:22: E501 Line too long (120 > 88)
Found 2 errors.
[*] 1 fixable with the `--fix` option.
"""


def test_eslint_keeps_every_violation():
    out = lint.compress_eslint(ESLINT_RAW)
    assert out is not None
    assert "12:5   error    'resp' is assigned a value but never used   no-unused-vars" in out
    assert "88:22  warning  Unexpected console statement                no-console" in out
    assert "C:\\repo\\src\\api.js" in out
    assert "✖ 3 problems (2 errors, 1 warning)" in out


def test_eslint_unrecognized_returns_none():
    assert lint.compress_eslint("all good, no output format here") is None


def test_ruff_keeps_violations_drops_deprecation_noise():
    out = lint.compress_ruff(RUFF_RAW)
    assert out is not None
    assert "src/api.py:12:5: F841" in out
    assert "src/api.py:88:22: E501" in out
    assert "Found 2 errors." in out
    assert "top-level linter settings are deprecated" not in out


def test_ruff_unrecognized_returns_none():
    assert lint.compress_ruff("bash: ruff: command not found") is None


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS: {name}")
    print("all lint format tests passed")

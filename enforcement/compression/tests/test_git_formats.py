#!/usr/bin/env python3
"""Unit tests for the git output parsers. Parsers are pure functions:
str -> compressed str, or None meaning 'not confident, pass through'."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from compression.formats import git  # noqa: E402

STATUS_RAW = """On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
\tmodified:   enforcement/hooks/pre_tool_use_guard.py
\tmodified:   CHANGELOG.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
\tenforcement/compression/

no changes added to commit (use "git add" and/or "git commit -a")
"""

LOG_RAW = """commit 9056ffdaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
Author: Amit Rosen <amit.rosen@keshet-tv.com>
Date:   Wed Jul 1 17:35:00 2026 +0300

    refactor: align skills with Superpowers standards

    Longer body line that should not appear in compact output.

commit 76b6906bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
Author: Amit Rosen <amit.rosen@keshet-tv.com>
Date:   Wed Jul 1 15:00:00 2026 +0300

    fix: close PowerShell blind spot in enforcement hook
"""

DIFF_RAW = """diff --git a/CHANGELOG.md b/CHANGELOG.md
index 1a2b3c4..5d6e7f8 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -10,3 +10,4 @@ header context line
 unchanged line
-old line
+new line
+added line
"""


def test_status_keeps_files_drops_hints():
    out = git.compress_git_status(STATUS_RAW)
    assert out is not None
    assert "modified:   enforcement/hooks/pre_tool_use_guard.py" in out
    assert "enforcement/compression/" in out
    assert "On branch main" in out
    assert '(use "git add' not in out
    assert "no changes added to commit" not in out
    assert len(out) < len(STATUS_RAW)


def test_status_unrecognized_returns_none():
    assert git.compress_git_status("some random text") is None


def test_log_one_line_per_commit():
    out = git.compress_git_log(LOG_RAW)
    assert out is not None
    lines = out.splitlines()
    assert len(lines) == 2
    assert lines[0].startswith("9056ffda ")
    assert "refactor: align skills with Superpowers standards" in lines[0]
    assert "Amit Rosen" in lines[0]
    assert "Longer body line" not in out


def test_log_already_oneline_returns_none():
    assert git.compress_git_log("9056ffd refactor: align skills\n76b6906 fix: hook\n") is None


def test_diff_preserves_all_change_lines():
    out = git.compress_git_diff(DIFF_RAW)
    assert out is not None
    for required in ("diff --git a/CHANGELOG.md b/CHANGELOG.md", "--- a/CHANGELOG.md",
                     "+++ b/CHANGELOG.md", "@@ -10,3 +10,4 @@", "-old line",
                     "+new line", "+added line", " unchanged line"):
        assert required in out, f"missing: {required}"
    assert "index 1a2b3c4" not in out


def test_diff_not_a_diff_returns_none():
    assert git.compress_git_diff("nothing to see") is None


GOLDEN_DIFF = (Path(__file__).parent / "fixtures" / "git_diff_multifile_raw.txt").read_text(encoding="utf-8")


def test_diff_golden_multifile_no_content_line_lost():
    out = git.compress_git_diff(GOLDEN_DIFF)
    assert out is not None
    out_lines = set(out.splitlines())
    for line in GOLDEN_DIFF.splitlines():
        if re.match(r"^index [0-9a-f]+\.\.[0-9a-f]+", line):
            continue  # the ONLY thing the parser may drop
        assert line in out_lines, f"CONTENT LINE LOST: {line!r}"


def test_diff_context_line_starting_with_index_is_preserved():
    raw = """diff --git a/calc.py b/calc.py
index 1a2b3c4..5d6e7f8 100644
--- a/calc.py
+++ b/calc.py
@@ -1,3 +1,3 @@
index = compute_index(rows)
-total = index + 1
+total = index + 2
"""
    out = git.compress_git_diff(raw)
    assert "index = compute_index(rows)" in out      # context line must survive
    assert "index 1a2b3c4..5d6e7f8 100644" not in out  # real metadata still dropped


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS: {name}")
    print("all git format tests passed")

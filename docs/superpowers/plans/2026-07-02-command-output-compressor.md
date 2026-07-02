# Command-Output Compressor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A PostToolUse hook that compresses verbose Bash command output (git/pytest/npm-test/lint) before it enters Claude's context, with per-event stats logging and an aggregation report.

**Architecture:** A thin hook script (`enforcement/hooks/post_tool_use_compressor.py`) reads the PostToolUse JSON from stdin, routes the command through `enforcement/compression/dispatch.py` to a format-specific parser (`formats/git.py`, `formats/test_runners.py`, `formats/lint.py`), and emits `updatedToolOutput` JSON only when compression succeeded and gained ≥10%. Every invocation — compressed, skipped, or errored — is logged via `stats.py` to `.claude/compression-stats.jsonl`. Fail-open is absolute: any exception results in unchanged passthrough.

**Tech Stack:** Python 3 stdlib only (`json`, `re`, `sys`, `os`, `time`, `pathlib`, `collections`). No pip dependencies. Tests follow the existing subprocess-harness pattern in `enforcement/tests/test_pre_tool_use_guard.py`.

**Spec:** `docs/superpowers/specs/2026-07-02-command-output-compressor-design.md` (approved).

## Global Constraints

- Python stdlib only — no external dependencies, in the hook or the tests.
- Fail-open always: no exception may alter or block the tool's original output beyond "compression didn't happen".
- Parsers are pure functions `(raw: str) -> str | None`; `None` always means untouched passthrough, never a guess.
- Input size ceiling: output > 2,000,000 chars → immediate passthrough (`skipped: "size_ceiling"`).
- Minimum gain: emit compressed output only if `len(compressed) < len(raw) * 0.90`, else passthrough (`skipped: "no_gain"`).
- Every stats event includes `parser_version`; every invocation (including `no_parser`) is logged — the denominator matters.
- NOCOMPRESS escape hatch: the literal word `NOCOMPRESS` anywhere in the command string → passthrough; env var `KESHET_NOCOMPRESS` set → all compression disabled.
- Hook matcher in settings.json is `Bash` only for MVP (all parsers are Bash-command parsers; narrower matcher = fewer Python startups).
- Never compress away a FAILED/ERROR/traceback line or a changed diff line — golden tests enforce this (spec success criterion 3, absolute).
- Repo conventions: file paths/tests styled after `enforcement/hooks/pre_tool_use_guard.py` and `enforcement/tests/test_pre_tool_use_guard.py`. Windows dev machine — run tests with `python`, not `python3`.
- The deployed layout mirrors the repo layout: hook at `.claude/hooks/`, package at `.claude/compression/` — the hook resolves the package via `parent-of-parent` path insertion, which works identically in both layouts.

---

### Task 1: Package skeleton + stats module

**Files:**
- Create: `enforcement/compression/__init__.py` (empty)
- Create: `enforcement/compression/formats/__init__.py` (empty)
- Create: `enforcement/compression/stats.py`
- Create: `enforcement/compression/tests/__init__.py` (empty)
- Test: `enforcement/compression/tests/test_stats.py`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: `stats.StatsSink` (abstract, `.write(event: dict) -> None`), `stats.LocalFileSink(path: str | None = None)` (default path `.claude/compression-stats.jsonl`, overridable via env `KESHET_COMPRESSION_STATS_PATH`), `stats.make_event(tool, kind, parser_version, raw_chars, compressed_chars, duration_ms, skipped=None, error=None) -> dict`. Task 6 (hook) and Task 7 (report) depend on these exact names.

- [ ] **Step 1: Write the failing test**

```python
# enforcement/compression/tests/test_stats.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest enforcement/compression/tests/test_stats.py -v`
Expected: FAIL / collection error with `ModuleNotFoundError: No module named 'compression'`

- [ ] **Step 3: Create the package files and minimal implementation**

Create empty files: `enforcement/compression/__init__.py`, `enforcement/compression/formats/__init__.py`, `enforcement/compression/tests/__init__.py`.

```python
# enforcement/compression/stats.py
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
        except OSError:
            # Stats must never break the hook. Losing one event is fine.
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest enforcement/compression/tests/test_stats.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add enforcement/compression/
git commit -m "feat(compression): package skeleton + stats sink with fail-open writes"
```

---

### Task 2: Git parsers (`formats/git.py`)

**Files:**
- Create: `enforcement/compression/formats/git.py`
- Test: `enforcement/compression/tests/test_git_formats.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `git.PARSER_VERSION: str` ("1.0.0"), `git.compress_git_status(raw: str) -> str | None`, `git.compress_git_log(raw: str) -> str | None`, `git.compress_git_diff(raw: str) -> str | None`. Task 5 (dispatch) imports all four names.

- [ ] **Step 1: Write the failing test**

```python
# enforcement/compression/tests/test_git_formats.py
#!/usr/bin/env python3
"""Unit tests for the git output parsers. Parsers are pure functions:
str -> compressed str, or None meaning 'not confident, pass through'."""
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


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS: {name}")
    print("all git format tests passed")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest enforcement/compression/tests/test_git_formats.py -v`
Expected: FAIL with `ModuleNotFoundError`/`ImportError` (git module doesn't exist)

- [ ] **Step 3: Write minimal implementation**

```python
# enforcement/compression/formats/git.py
#!/usr/bin/env python3
"""Compressors for git command output.

Contract (same for every parser in formats/): pure function, takes the raw
output string, returns the compressed string — or None when the input
doesn't match the expected shape. None ALWAYS means untouched passthrough;
a parser must never guess.

Safety rule for diff (spec success criterion 3, absolute): every changed
line, hunk header, and file header is preserved verbatim. Only proven
metadata noise ('index abc..def 100644' lines) is dropped.
"""
import re

PARSER_VERSION = "1.0.0"

_STATUS_NOISE_PREFIXES = (
    '  (use "git',
    '  (commit or discard',
    '  (all conflicts fixed',
    'no changes added to commit',
    'nothing added to commit',
)

_COMMIT_RE = re.compile(r"^commit ([0-9a-f]{40})\b")


def compress_git_status(raw: str) -> str | None:
    lines = raw.splitlines()
    if not lines:
        return None
    first = lines[0]
    if not (first.startswith("On branch") or first.startswith("HEAD detached")):
        return None
    kept = []
    for line in lines:
        s = line.rstrip()
        if not s:
            continue
        if any(s.startswith(p) for p in _STATUS_NOISE_PREFIXES):
            continue
        kept.append(s)
    return "\n".join(kept)


def compress_git_log(raw: str) -> str | None:
    if not _COMMIT_RE.search(raw):
        return None  # already --oneline or a custom format; don't touch
    out = []
    sha = author = date = msg = None

    def flush():
        if sha:
            out.append(f"{sha[:8]} {msg or '(no message)'} ({author or '?'}, {date or '?'})")

    for line in raw.splitlines():
        m = _COMMIT_RE.match(line)
        if m:
            flush()
            sha, author, date, msg = m.group(1), None, None, None
        elif line.startswith("Author:"):
            author = line[len("Author:"):].strip().split("<")[0].strip()
        elif line.startswith("Date:"):
            date = line[len("Date:"):].strip()
        elif line.startswith("    ") and msg is None and line.strip():
            msg = line.strip()  # first subject line only; body dropped
    flush()
    return "\n".join(out) if out else None


def compress_git_diff(raw: str) -> str | None:
    if "diff --git" not in raw:
        return None
    # Conservative by design: drop ONLY 'index ...' metadata lines.
    kept = [l for l in raw.splitlines() if not l.startswith("index ")]
    return "\n".join(kept)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest enforcement/compression/tests/test_git_formats.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add enforcement/compression/formats/git.py enforcement/compression/tests/test_git_formats.py
git commit -m "feat(compression): git status/log/diff parsers"
```

---

### Task 3: Test-runner parsers (`formats/test_runners.py`) + pytest golden file

**Files:**
- Create: `enforcement/compression/formats/test_runners.py`
- Create: `enforcement/compression/tests/fixtures/pytest_failure_raw.txt` (golden file)
- Test: `enforcement/compression/tests/test_test_runner_formats.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `test_runners.PARSER_VERSION: str` ("1.0.0"), `test_runners.compress_pytest(raw: str) -> str | None`, `test_runners.compress_npm_test(raw: str) -> str | None`. Task 5 (dispatch) imports all three names.

- [ ] **Step 1: Create the golden fixture (real-shaped pytest failure output)**

```text
# enforcement/compression/tests/fixtures/pytest_failure_raw.txt
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-9.0.3, pluggy-1.5.0
rootdir: C:\repo
collected 52 items

tests/test_auth.py ..........................                            [ 50%]
tests/test_events.py .................F.                                 [ 86%]
tests/test_api.py ......F                                                [100%]

================================== FAILURES ===================================
_______________________ test_event_dedup_by_external_id _______________________

    def test_event_dedup_by_external_id():
        first = create_event(external_id="X1")
>       assert create_event(external_id="X1") is None
E       AssertionError: assert <Event id=2> is None

tests/test_events.py:41: AssertionError
______________________________ test_api_409_dup _______________________________

    def test_api_409_dup():
>       assert resp.status_code == 409
E       assert 201 == 409

tests/test_api.py:88: assert
=========================== short test summary info ===========================
FAILED tests/test_events.py::test_event_dedup_by_external_id - AssertionError
FAILED tests/test_api.py::test_api_409_dup - assert 201 == 409
========================= 2 failed, 50 passed in 4.12s ========================
```

- [ ] **Step 2: Write the failing test**

```python
# enforcement/compression/tests/test_test_runner_formats.py
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
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest enforcement/compression/tests/test_test_runner_formats.py -v`
Expected: FAIL with ImportError (test_runners doesn't exist)

- [ ] **Step 4: Write minimal implementation**

```python
# enforcement/compression/formats/test_runners.py
#!/usr/bin/env python3
"""Compressors for test-runner output (pytest, npm test/jest).

Strategy: the FAILURES section (and everything after it) is preserved
VERBATIM — we only drop the progress/collection section above it. For
all-green runs, only the final summary line survives. This guarantees
spec success criterion 3 (zero information loss on failures) structurally
rather than by pattern-matching individual failure lines.
"""
import re

PARSER_VERSION = "1.0.0"

_PYTEST_SECTION_RE = re.compile(r"^=+ (FAILURES|ERRORS) =+$")
_PYTEST_SUMMARY_RE = re.compile(r"^=+ .*(passed|failed|error|no tests ran).* =+$")
_NPM_MARKER_RE = re.compile(r"(Tests:|Test Suites:|✓|✕|√|passing|failing)")
_NPM_PASS_LINE_RE = re.compile(r"^\s*(✓|√)|^\s*PASS\s")


def compress_pytest(raw: str) -> str | None:
    if "test session starts" not in raw:
        return None
    lines = raw.splitlines()
    fail_idx = next((i for i, l in enumerate(lines)
                     if _PYTEST_SECTION_RE.match(l.strip())), None)
    if fail_idx is not None:
        # FAILURES → end, verbatim. Savings come from dropping everything above.
        return "\n".join(lines[fail_idx:])
    summary = [l for l in lines if _PYTEST_SUMMARY_RE.match(l.strip())]
    return "\n".join(summary) if summary else None


def compress_npm_test(raw: str) -> str | None:
    if not _NPM_MARKER_RE.search(raw):
        return None
    kept, passed = [], 0
    for line in raw.splitlines():
        s = line.rstrip()
        if _NPM_PASS_LINE_RE.match(s):
            passed += 1
            continue
        if not s:
            continue
        kept.append(s)  # everything not provably a pass-line is kept
    if passed:
        kept.append(f"[{passed} passing checks omitted]")
    return "\n".join(kept)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest enforcement/compression/tests/test_test_runner_formats.py -v`
Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add enforcement/compression/formats/test_runners.py enforcement/compression/tests/
git commit -m "feat(compression): pytest/npm-test parsers with golden-file no-loss test"
```

---

### Task 4: Lint parsers (`formats/lint.py`)

**Files:**
- Create: `enforcement/compression/formats/lint.py`
- Test: `enforcement/compression/tests/test_lint_formats.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `lint.PARSER_VERSION: str` ("1.0.0"), `lint.compress_eslint(raw: str) -> str | None`, `lint.compress_ruff(raw: str) -> str | None`. Task 5 (dispatch) imports all three names.

- [ ] **Step 1: Write the failing test**

```python
# enforcement/compression/tests/test_lint_formats.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest enforcement/compression/tests/test_lint_formats.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write minimal implementation**

```python
# enforcement/compression/formats/lint.py
#!/usr/bin/env python3
"""Compressors for linter output (eslint stylish format, ruff check).

Both formats are already fairly dense; the win here is dropping blank
lines, deprecation banners, and fix-hint footers while keeping every
violation line (anything carrying a file:line reference) verbatim.
"""
import re

PARSER_VERSION = "1.0.0"

_ESLINT_LOC_RE = re.compile(r"^\s+\d+:\d+\s+(error|warning)")
_RUFF_VIOLATION_RE = re.compile(r"^\S+:\d+:\d+: \w+")
_RUFF_SUMMARY_RE = re.compile(r"^Found \d+ error")


def compress_eslint(raw: str) -> str | None:
    lines = raw.splitlines()
    if not any(_ESLINT_LOC_RE.match(l) for l in lines):
        return None
    return "\n".join(l.rstrip() for l in lines if l.strip())


def compress_ruff(raw: str) -> str | None:
    lines = raw.splitlines()
    violations = [l for l in lines if _RUFF_VIOLATION_RE.match(l)]
    summary = [l for l in lines if _RUFF_SUMMARY_RE.match(l)]
    if not violations and not summary:
        return None
    return "\n".join(violations + summary)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest enforcement/compression/tests/test_lint_formats.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add enforcement/compression/formats/lint.py enforcement/compression/tests/test_lint_formats.py
git commit -m "feat(compression): eslint/ruff parsers"
```

---

### Task 5: Dispatch routing (`dispatch.py`)

**Files:**
- Create: `enforcement/compression/dispatch.py`
- Test: `enforcement/compression/tests/test_dispatch.py`

**Interfaces:**
- Consumes: `git.compress_git_status/log/diff` + `git.PARSER_VERSION` (Task 2), `test_runners.compress_pytest/compress_npm_test` + version (Task 3), `lint.compress_eslint/compress_ruff` + version (Task 4).
- Produces: `dispatch.route(tool_name: str, command: str) -> tuple[str, Callable[[str], str | None], str] | None` — returns `(kind, parser_fn, parser_version)` or `None`. Task 6 (hook) calls exactly this.

- [ ] **Step 1: Write the failing test**

```python
# enforcement/compression/tests/test_dispatch.py
#!/usr/bin/env python3
"""Routing tests: command string -> (kind, parser, version) or None."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from compression import dispatch  # noqa: E402

CASES = [
    # (tool_name, command, expected_kind_or_None)
    ("Bash", "git status", "git-status"),
    ("Bash", "git status --short", "git-status"),
    ("Bash", "git diff HEAD~1", "git-diff"),
    ("Bash", "git log -n 20", "git-log"),
    ("Bash", "pytest -v tests/", "pytest"),
    ("Bash", "python -m pytest enforcement/tests/", "pytest"),
    ("Bash", "npm test", "npm-test"),
    ("Bash", "npm run test -- --coverage", "npm-test"),
    ("Bash", "npx eslint src/", "eslint"),
    ("Bash", "ruff check .", "ruff"),
    ("Bash", "git push origin main", None),          # git, but not a covered subcommand
    ("Bash", "cat file.py", None),                    # no parser
    ("Bash", "echo pytest is great", None),           # 'pytest' not as a command word... 
    ("Read", "git status", None),                     # wrong tool
    ("PowerShell", "git status", None),               # MVP is Bash-matcher only
]


def test_routing_table():
    for tool, cmd, expected in CASES:
        entry = dispatch.route(tool, cmd)
        actual = entry[0] if entry else None
        assert actual == expected, f"{tool}:{cmd!r} -> {actual}, expected {expected}"


def test_route_returns_callable_and_version():
    kind, fn, version = dispatch.route("Bash", "git status")
    assert callable(fn)
    assert isinstance(version, str) and version


if __name__ == "__main__":
    test_routing_table()
    print("PASS: test_routing_table")
    test_route_returns_callable_and_version()
    print("PASS: test_route_returns_callable_and_version")
    print("all dispatch tests passed")
```

Note on the `echo pytest is great` case: routing is prefix/word-boundary based; `pytest` must match as a command position (start of command or after `python -m` / `&&` / `;`), not as a mere argument to `echo`. The regexes below implement that; if this proves too strict/loose in real use, adjust the regex and add the real-world command to CASES.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest enforcement/compression/tests/test_dispatch.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write minimal implementation**

```python
# enforcement/compression/dispatch.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest enforcement/compression/tests/test_dispatch.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add enforcement/compression/dispatch.py enforcement/compression/tests/test_dispatch.py
git commit -m "feat(compression): command-to-parser dispatch table"
```

---

### Task 6: The PostToolUse hook (`post_tool_use_compressor.py`)

**Files:**
- Create: `enforcement/hooks/post_tool_use_compressor.py`
- Create: `enforcement/compression/tests/fixtures/sample_pytest_event.json` (used by both tests and the Task 8 latency bench)
- Test: `enforcement/compression/tests/test_hook_integration.py`

**Interfaces:**
- Consumes: `dispatch.route()` (Task 5), `stats.LocalFileSink` / `stats.make_event` (Task 1).
- Produces: the executable hook. Contract with Claude Code: reads PostToolUse JSON on stdin (`{"tool_name", "tool_input", "tool_response"}`); on compression prints `{"hookSpecificOutput": {"hookEventName": "PostToolUse", "updatedToolOutput": "<compressed>"}}` to stdout and exits 0; on passthrough prints nothing and exits 0. **Never** exits non-zero.

- [ ] **Step 1: Create the sample event fixture**

```json
{
  "tool_name": "Bash",
  "tool_input": {"command": "pytest -v tests/"},
  "tool_response": {"stdout": "PLACEHOLDER_REPLACED_IN_TEST", "stderr": "", "interrupted": false}
}
```

Save as `enforcement/compression/tests/fixtures/sample_pytest_event.json`. The integration test injects the golden pytest output into the `stdout` field at runtime (single source of truth: `pytest_failure_raw.txt` from Task 3).

- [ ] **Step 2: Write the failing test**

```python
# enforcement/compression/tests/test_hook_integration.py
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
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest enforcement/compression/tests/test_hook_integration.py -v`
Expected: FAIL — hook file does not exist (subprocess returns non-zero / FileNotFoundError)

- [ ] **Step 4: Write the hook**

```python
# enforcement/hooks/post_tool_use_compressor.py
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
        sys.exit(0)  # fail open; nothing sane to log

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

    log(kind=kind, version=version, compressed_chars=len(compressed))
    sys.stdout.reconfigure(encoding="utf-8")  # Windows console safety for ✓/✕/Hebrew
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "updatedToolOutput": compressed,
        }
    }, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest enforcement/compression/tests/test_hook_integration.py -v`
Expected: 8 passed

- [ ] **Step 6: Run the full compression test suite together**

Run: `python -m pytest enforcement/compression/tests/ -v`
Expected: all tests pass (5 + 6 + 6 + 4 + 2 + 8 = 31 tests across the five files)

- [ ] **Step 7: Commit**

```bash
git add enforcement/hooks/post_tool_use_compressor.py enforcement/compression/tests/
git commit -m "feat(compression): PostToolUse hook with fail-open, kill switches, stats"
```

---

### Task 7: Report script (`report.py`)

**Files:**
- Create: `enforcement/compression/report.py`
- Test: `enforcement/compression/tests/test_report.py`

**Interfaces:**
- Consumes: the stats event dict shape from Task 1 (`kind`, `skipped`, `error`, `raw_tokens_est`, `compressed_tokens_est`).
- Produces: CLI script `python enforcement/compression/report.py [path]` (default path `.claude/compression-stats.jsonl`) printing a summary table; `report.summarize(events: list[dict]) -> tuple[int, dict, dict]` for tests — returns `(total_invocations, per_kind, skip_counts)`.
- Spec open-item resolution: no `--since` flag in MVP (YAGNI) — to reset measurement, delete or rotate the stats file; the whole-file read is trivially fast at MVP volumes.

- [ ] **Step 1: Write the failing test**

```python
# enforcement/compression/tests/test_report.py
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


if __name__ == "__main__":
    test_summarize_denominator_and_kinds()
    print("PASS: test_summarize_denominator_and_kinds")
    test_summarize_empty()
    print("PASS: test_summarize_empty")
    print("all report tests passed")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest enforcement/compression/tests/test_report.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Write minimal implementation**

```python
# enforcement/compression/report.py
#!/usr/bin/env python3
"""Aggregate .claude/compression-stats.jsonl into a summary table.

Usage: python enforcement/compression/report.py [path-to-stats.jsonl]

The 'TOTAL INVOCATIONS' line is the denominator — how many tool calls the
hook saw at all, compressed or not. Savings % without that number is
marketing, not measurement.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

DEFAULT_PATH = ".claude/compression-stats.jsonl"


def load(path):
    events = []
    p = Path(path)
    if not p.exists():
        return events
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # a torn/corrupt line shouldn't kill the report
    return events


def summarize(events):
    total = len(events)
    per_kind = defaultdict(lambda: {"calls": 0, "raw": 0, "comp": 0, "errors": 0})
    skips = defaultdict(int)
    for e in events:
        if e.get("skipped"):
            skips[e["skipped"]] += 1
        kind = e.get("kind")
        if kind is None:
            continue
        row = per_kind[kind]
        row["calls"] += 1
        row["raw"] += e.get("raw_tokens_est") or 0
        row["comp"] += e.get("compressed_tokens_est") or 0
        if e.get("error"):
            row["errors"] += 1
    return total, dict(per_kind), dict(skips)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    events = load(path)
    total, per_kind, skips = summarize(events)
    print("=== Compression Report ===")
    print(f"Stats file        : {path}")
    print(f"TOTAL INVOCATIONS : {total}")
    if not per_kind:
        print("No parser-matched events yet.")
        return
    print(f"\n{'Kind':<12}{'Calls':>7}{'Raw tok':>10}{'Comp tok':>10}{'Saved':>8}{'Errors':>8}")
    t_raw = t_comp = 0
    for kind in sorted(per_kind):
        r = per_kind[kind]
        saved = f"-{100 * (1 - r['comp'] / r['raw']):.0f}%" if r["raw"] else "n/a"
        print(f"{kind:<12}{r['calls']:>7}{r['raw']:>10}{r['comp']:>10}{saved:>8}{r['errors']:>8}")
        t_raw += r["raw"]
        t_comp += r["comp"]
    total_saved = f"-{100 * (1 - t_comp / t_raw):.0f}%" if t_raw else "n/a"
    print(f"{'TOTAL':<12}{'':>7}{t_raw:>10}{t_comp:>10}{total_saved:>8}")
    if skips:
        print("\nSkip reasons: " + ", ".join(f"{k}={v}" for k, v in sorted(skips.items())))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest enforcement/compression/tests/test_report.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add enforcement/compression/report.py enforcement/compression/tests/test_report.py
git commit -m "feat(compression): stats aggregation report (rtk-gain-style)"
```

---

### Task 8: Wiring, docs, latency bench

**Files:**
- Modify: `enforcement/project-settings.example.json` (add PostToolUse hook entry + comment)
- Modify: `enforcement/README.md` (add compressor to "Files here" + open items)
- Modify: `CHANGELOG.md` (Unreleased section)
- Modify: `.gitignore` (ensure `.claude/compression-stats.jsonl` is ignored)

**Interfaces:**
- Consumes: everything above, as a deployed whole.
- Produces: deployable configuration + documentation. No code.

- [ ] **Step 1: Add the PostToolUse hook to `enforcement/project-settings.example.json`**

Add to the `"hooks"` object (alongside the existing `PreToolUse` entry):

```json
"PostToolUse": [
  {
    "matcher": "Bash",
    "hooks": [
      {
        "type": "command",
        "command": "python3 .claude/hooks/post_tool_use_compressor.py"
      }
    ]
  }
]
```

And add this comment key at the bottom of the file:

```json
"_comment_6": "The PostToolUse compressor (post_tool_use_compressor.py + the .claude/compression/ package, both copied from enforcement/) is OPT-IN per project: shipping this settings block IS the opt-in. Matcher is 'Bash' only by design — all MVP parsers are Bash-command parsers, and a narrower matcher means fewer Python startups (latency). Same python3-on-Windows caveat as _comment_5 applies. To disable per-command: include the word NOCOMPRESS in the command. To disable machine-wide: set KESHET_NOCOMPRESS=1."
```

- [ ] **Step 2: Verify the JSON is still valid**

Run: `python -c "import json; json.load(open('enforcement/project-settings.example.json', encoding='utf-8')); print('valid')"`
Expected: `valid`

- [ ] **Step 3: Add `.gitignore` entry**

Append to `.gitignore` (check it isn't already covered by a `.claude/` pattern first — run `git check-ignore -v .claude/compression-stats.jsonl` and skip this step if it already matches):

```
# per-machine compression stats (see enforcement/compression/stats.py)
.claude/compression-stats.jsonl
```

- [ ] **Step 4: Update `enforcement/README.md`**

In the "Files here" section, add two rows after the existing hook bullet:

```markdown
- `hooks/post_tool_use_compressor.py` — PostToolUse hook that compresses verbose Bash output (git status/diff/log, pytest, npm test, eslint, ruff) before it enters Claude's context. Fail-open: any parser error means untouched passthrough, never altered output. Opt-in per project via the PostToolUse block in `project-settings.example.json`. Design: `docs/superpowers/specs/2026-07-02-command-output-compressor-design.md`.
- `compression/` — the parser package behind the hook above (`dispatch.py` routing, `formats/` parsers, `stats.py` local JSONL logging, `report.py` savings report, `tests/` incl. golden-file no-information-loss tests). Deploy alongside the hook: copy to `.claude/compression/`.
```

And add to "Open items before this is production-ready":

```markdown
4. **Compressor Phase 1 gates not yet measured on a real machine:** the spec defines four success criteria (≥60% savings on covered commands, ≤100ms p95 hook overhead including Python startup, zero information loss, <1% parser error rate). The golden-file tests cover criterion 3 structurally; criteria 1, 2, and 4 need a week of real Builder-session stats (`python enforcement/compression/report.py`) before org-wide rollout.
```

- [ ] **Step 5: Measure hook latency (Phase 1 criterion 2, first data point)**

Build a real stdin sample and time 20 runs (PowerShell on the dev machine):

```powershell
# from the repo root
python - <<'EOF'
import json, pathlib
raw = pathlib.Path("enforcement/compression/tests/fixtures/pytest_failure_raw.txt").read_text(encoding="utf-8")
evt = {"tool_name": "Bash", "tool_input": {"command": "pytest -v tests/"},
       "tool_response": {"stdout": raw, "stderr": "", "interrupted": False}}
pathlib.Path("bench_event.json").write_text(json.dumps(evt), encoding="utf-8")
EOF

$times = 1..20 | ForEach-Object {
  (Measure-Command {
    Get-Content bench_event.json -Raw | python enforcement/hooks/post_tool_use_compressor.py | Out-Null
  }).TotalMilliseconds
}
$sorted = $times | Sort-Object
"p50: {0:N0}ms  p95(~19th of 20): {1:N0}ms" -f $sorted[9], $sorted[18]
Remove-Item bench_event.json
```

Expected: prints p50/p95. Record the numbers in the commit message. If p95 > 100ms, note it in `enforcement/README.md` open item 4 — per the spec, the first mitigation to evaluate is the matcher scope, not parser micro-optimization. (The heredoc form above is for Git Bash; if running the Python part in PowerShell, write the JSON-builder as a small temp .py file instead.)

- [ ] **Step 6: Add CHANGELOG entry**

Add under `## [Unreleased] — July 2026` a new `### Added` block (create the block if absent):

```markdown
### Added

- `enforcement/hooks/post_tool_use_compressor.py` + `enforcement/compression/` —
  opt-in PostToolUse hook that compresses verbose Bash output (git
  status/diff/log, pytest, npm test, eslint, ruff) before it enters
  Claude's context. Python stdlib only, absolute fail-open, per-event
  stats to `.claude/compression-stats.jsonl` (with parser_version and a
  full-invocation denominator), `report.py` savings summary,
  NOCOMPRESS/`KESHET_NOCOMPRESS` escape hatches, 2MB input ceiling, and
  golden-file tests asserting zero information loss on failure output.
  Design + Phase 1 success gates:
  `docs/superpowers/specs/2026-07-02-command-output-compressor-design.md`.
```

- [ ] **Step 7: Run the entire repo test suite (old + new) one last time**

Run: `python -m pytest enforcement/ -v`
Expected: all tests pass — the 33 existing guard tests AND all new compression tests. Zero failures.

- [ ] **Step 8: Commit**

```bash
git add enforcement/project-settings.example.json enforcement/README.md CHANGELOG.md .gitignore
git commit -m "feat(compression): wire PostToolUse hook into example settings + docs + latency baseline"
```

---

## Post-plan verification (manual, before calling Phase 1 done)

Not tasks for the implementing engineer — gates for the reviewer (see spec "Phase 1 success criteria"):

1. **Dry run on a real machine:** deploy hook + package to one project's `.claude/`, run a normal session (some git/pytest/lint activity), then `python enforcement/compression/report.py` — confirm events flow and savings are real.
2. **Task-outcome parity check (criterion 3):** give a fresh Claude session the compressed golden pytest output and ask it to "fix the failing test" — confirm it identifies both failures exactly as it would from raw output.
3. **Week-long measurement** before any org-wide rollout recommendation.

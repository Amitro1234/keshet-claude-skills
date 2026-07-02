# Command-Output Compressor — Design

Status: Approved for implementation planning
Date: 2026-07-02
Owner: Amit Rosen, AI Architecture

## Context

Third-party tools like [RTK](https://github.com/rtk-ai/rtk) and
[headroom](https://github.com/headroomlabs-ai/headroom) claim 60-95% token
savings by compressing tool output before it reaches the model. Both are
young projects (created ~5 months prior to this writing) with growth curves
suspicious enough (near-identical star counts acquired in near-identical
timeframes) to treat as inspiration only, not as vendored dependencies —
adopting either directly would mean trusting an unreviewed, unaudited
release pipeline with full visibility into everything Claude Code sees on
every Builder machine.

This spec defines an in-house, narrow-scope equivalent: a `PostToolUse`
hook that compresses known-verbose command output, built and owned inside
this repo's existing `enforcement/` layer, using the same design
philosophy as `enforcement/hooks/pre_tool_use_guard.py` (Python stdlib
only, fail-open, unit-tested with crafted stdin).

This is a distinct mechanism from `claude-enterprise-skills/prompt-caching`
(which reduces the *price* of repeated, stable content) and from
`context-hygiene` / `output-discipline` (which are advisory — they rely on
Claude choosing to comply). This mechanism is deterministic: it runs on
every matching tool call regardless of which model tier is active or what
Claude decides.

## Scope (MVP)

**In scope:** six command types split across two categories that
routinely produce token-heavy output for Keshet Builders:

| Category | Commands |
|---|---|
| Git | `git status`, `git diff`, `git log` |
| Test / lint | `pytest`, `npm test`, `eslint` / `ruff check` |

**Explicitly out of scope for this pass** (deferred, not rejected):
- MCP connector output compression (Jira, Monday, SharePoint, etc.)
- Document/prose compression (Google Docs, PDFs) — fundamentally different
  problem: CLI tool output has a clear noise/signal split (progress bars vs.
  a failing test); prose in a document is close to 100% signal, so the same
  "strip proven-noise" strategy does not apply safely. Revisit only with a
  distinct retrieval/relevance-based approach, not as an extension of this
  design.
- Hebrew-specific tokenization handling — out of scope per explicit
  direction; git/test/lint output is expected to be predominantly
  English regardless of Builder's spoken language.
- Admin-level cross-machine aggregation — see Phase 2 below.

## Architecture

```
enforcement/
├── hooks/
│   ├── pre_tool_use_guard.py           (existing — blocking)
│   └── post_tool_use_compressor.py     (new — compression)
└── compression/
    ├── __init__.py
    ├── dispatch.py                     — routes tool_name/command → parser
    ├── stats.py                        — StatsSink abstraction + LocalFileSink
    ├── formats/
    │   ├── git.py
    │   ├── test_runners.py
    │   └── lint.py
    └── tests/
        └── test_compression.py         — same harness style as
                                           test_pre_tool_use_guard.py
```

### Why PostToolUse, not PreToolUse (RTK's approach)

Verified against current Claude Code hooks documentation: `PreToolUse` can
rewrite `tool_input` (`updatedInput`) before a command runs; `PostToolUse`
can rewrite the result (`updatedToolOutput`) after it runs. PostToolUse was
chosen because:

1. It fires on **any** tool call — Bash, MCP, Read — not just Bash. This
   keeps the framework extensible to MCP connector output later (Phase 2)
   without a second mechanism.
2. The command a Builder or Claude sees is never rewritten — reduces
   confusion, especially for non-developer Builders using Cowork-adjacent
   workflows.
3. No added latency to the command's own execution — only a small
   post-processing step on already-returned output.

### Data flow

```
Tool runs (Bash / MCP / Read)
        │
        ▼
Claude Code fires PostToolUse → post_tool_use_compressor.py
        │
        ▼
dispatch.py: is there a registered parser for this tool_name/command?
        │
        ├─ no  ──────────────────────────► passthrough, stats.log_event(raw, raw)
        │
        └─ yes
             │
             ▼
        formats/*.py attempts compression
             │
             ├─ success ──► updatedToolOutput = compressed; stats.log_event(raw, compressed)
             │
             └─ exception ──► fail-open: passthrough unchanged; stats.log_event(raw, raw, error=str(e))
```

Fail-open is absolute: a bug in a parser must never corrupt, hide, or
alter what Claude receives beyond "compression didn't happen this time."
This mirrors `pre_tool_use_guard.py`'s own fail-open philosophy for
malformed hook input.

## Compression strategy

Each parser is a pure function: `(raw_output: str) -> str | None`. Returns
`None` when it isn't confident it understood the shape of the output —
`None` always means untouched passthrough, never a guess.

**Guiding rule:** compress only content that is provably non-informational
(progress bars, timestamps, repeated boilerplate, PASS lines once counted).
Never touch content that could change a downstream decision:

| Output type | Always preserved in full | Safe to compress |
|---|---|---|
| `pytest` / `npm test` | Every FAILED/ERROR line, tracebacks, file:line | PASSED lines → count only |
| `eslint` / `ruff` | Every warning/error, file+line+rule | Banners, repeated headers |
| `git status` / `log` | Changed file names, commit messages | ASCII framing, extra whitespace |
| `git diff` | Every changed code line, unmodified | Only repeated metadata headers |

### Example parser (pytest)

```python
def compress_pytest(raw: str) -> str | None:
    lines = raw.splitlines()
    failures = [l for l in lines if l.startswith(("FAILED", "ERROR")) or "Traceback" in l]
    passed_count = sum(1 for l in lines if " PASSED" in l or l.strip().startswith("."))
    if not failures and passed_count == 0:
        return None  # unrecognized shape -> passthrough
    summary = f"{passed_count} passed" if not failures else ""
    return "\n".join(failures) + (f"\n{summary}" if summary else "")
```

## Statistics and reporting

Every compression attempt (success, no-op, or error) is logged — not just
"wins" — for full transparency into whether the mechanism is actually
working.

```python
class StatsSink:
    def write(self, event: dict) -> None: ...

class LocalFileSink(StatsSink):
    """MVP: writes to .claude/compression-stats.jsonl (gitignored, per-machine)."""
```

The sink is an abstraction specifically so a future centralized sink
(Phase 2) can be added without touching parser code.

Logged fields per event: timestamp, tool name, raw/compressed char counts,
a rough token estimate (`len(text) // 4` — an English-biased heuristic,
explicitly not presented as exact), a `parser_version` string (so Phase 2
dashboards can distinguish "old parser failed" from "fixed parser works" —
retrofitting this later would leave all historical data unattributable),
and an `error` field when a parser threw.

The hook also logs every invocation — including tool calls with no
registered parser — so the report can answer "out of N total tool calls,
how many were even candidates for compression?" Without that denominator,
an admin sees only wins, never misses, and can't judge whether the
mechanism is actually pulling its weight.

`enforcement/compression/report.py` aggregates the local log into a
per-session summary table (tool, calls, raw tokens, compressed tokens,
% saved) — analogous to `rtk gain`, run manually after a test session.

## Error handling

- A parser exception is caught at the dispatch layer, logged with the
  error message, and treated as a `None` result (passthrough).
- Malformed/unparseable hook stdin (mirroring `pre_tool_use_guard.py`)
  fails open — the tool's original output is never blocked or altered.
- No exception from this hook should ever propagate up and interrupt the
  underlying tool call.

## Testing

1. **Unit tests per parser** — crafted input/expected-output pairs, run as
   a subprocess against the hook exactly as Claude Code would invoke it
   (same pattern as `enforcement/tests/test_pre_tool_use_guard.py`).
2. **Golden-file tests** — real captured output (an actual failing pytest
   run, an actual multi-file git diff) checked to confirm the compressed
   version still contains every FAILED/ERROR/traceback line and every
   changed code line from the original.
3. **Success-criterion test** — not just "% tokens saved": a parser is not
   shipped unless a task performed against its compressed output (e.g.,
   "fix the failing test") produces the same outcome as the same task
   against raw output. Token savings without preserved task success is a
   failing result, not a partial win.

## Performance

- Python stdlib only (`json`, `re`, `time`) — no external dependencies,
  matching `pre_tool_use_guard.py`. This hook runs on every matching tool
  call, so added weight compounds across a session.
- Token estimation uses `len(text) // 4`, not a real tokenizer — avoids
  importing a tokenizer library for a rough estimate that's only used for
  the local stats/report, not for any pricing or budget decision.
- Stats logging is a single `jsonl` append per event — no blocking I/O
  beyond that.
- **Input size ceiling:** output larger than 2MB goes straight to
  passthrough without attempting any parser — closes the one scenario
  where the hook itself could meaningfully slow a tool call (regex over a
  giant log).
- **Known cost to measure honestly:** Python interpreter startup itself
  (tens of ms per invocation, worse on Windows) is likely the dominant
  overhead, not the parsing. If measured overhead breaks the latency
  budget below, the first mitigation is narrowing the hook's `matcher` in
  settings.json (fire on `Bash` only instead of all tools), not
  micro-optimizing parser code.

## Relationship to existing mechanisms

- **`model-router-skill`** decides which model reasons about a task, and
  operates before/independent of any tool call. This hook operates after a
  tool call, regardless of which model is active. They do not interact —
  compression behaves identically on Haiku, Sonnet, or Opus.
- **`prompt-caching`**: reduces the price of stable, repeated content
  (CLAUDE.md, memory files). This hook reduces the token *volume* of
  dynamic, non-repeating content (a git diff is different every time, so
  it isn't cacheable to begin with). Complementary, not overlapping.
- **`context-hygiene` / `output-discipline`**: advisory skills that rely on
  Claude choosing to comply. This hook is deterministic — it runs whether
  or not Claude "remembers" to be economical.

## Rollout

- Opt-in per project via a flag in `.claude/settings.json` (project tier),
  not forced org-wide on day one — consistent with how
  `enforcement/project-settings.example.json` is already deployed. If a
  parser turns out to hurt a specific Builder's workflow, it can be
  disabled per-project without affecting others.
- `NOCOMPRESS` escape hatch (env var or command prefix, exact mechanism
  TBD in implementation plan) for cases where a Builder explicitly wants
  full raw output (e.g., compiling a complete test report).

## Phase 1 success criteria

Measured over at least one week of real Builder sessions (not synthetic
tests), using the local stats log. Phase 2 investment is justified only if
Phase 1 passes all four:

| # | Criterion | Target | How measured |
|---|---|---|---|
| 1 | **Real savings** | ≥60% average char reduction on covered commands, AND covered commands account for a meaningful share of session tool-call volume (report shows the denominator) | `report.py` over a real week's `compression-stats.jsonl` |
| 2 | **Latency** | Hook overhead ≤100ms p95 per invocation, end-to-end (including Python startup) | Timing wrapper in the hook itself, logged per event |
| 3 | **Quality — zero information loss** | Zero observed cases where compressed output omitted a FAILED/ERROR/traceback line or a changed diff line; task-outcome parity on the golden-file benchmark tasks ("fix the failing test" gives the same result on raw vs. compressed) | Golden-file tests pre-ship + any real-usage incident counts as an automatic fail |
| 4 | **Reliability** | Parser error rate <1% of invocations, and 100% of errors fail open (zero broken tool calls attributable to the hook) | `error` field counts in stats log |

Criterion 3 is absolute: token savings with any information loss is a
failed phase, not a trade-off. Criteria 1–2 are targets — if savings land
at 50% or latency at 120ms, that's a judgment call, not an automatic kill.

## Phase 2 (roadmap only — not built in this pass)

**Goal:** let an admin (AI Architecture) see, in aggregate, whether the
compression mechanism is working across Builder machines and where parsers
need improvement — without collecting what any individual Builder is
actually doing on their machine.

Not designed or built now. **Direction decided (2026-07-02, Amit):
option 1 — Azure Application Insights — is the selected approach**,
conditional on Phase 1 passing its gates. No self-hosted service is
required: an App Insights resource (created once by the Azure subscription
admin), each Builder machine POSTs events to the ingestion endpoint via a
connection string (plain `urllib`, no SDK), dashboards via KQL/Workbooks
in the Azure portal. Event volume at fleet scale is a few MB/month —
ingestion cost is negligible. Option 2 kept below for the record only.

1. **Azure Application Insights custom events (SELECTED)** — lightweight
   `track_event` calls via the REST ingestion API (no SDK dependency
   required, a plain `urllib` POST is sufficient), aggregated centrally
   with existing KQL/dashboard tooling. Fits the org's existing Azure
   footprint (already referenced throughout
   `keshet-builder-skills/spec-pack/templates.md` and the approved
   connector list).
2. **Periodic Blob upload (not selected)** — each Builder machine uploads
   its local `compression-stats.jsonl` (or a rolled-up weekly summary) to
   an isolated path in Azure Blob Storage. Requires a scoped ingestion
   token per machine, not a shared write key, to avoid one leaked
   credential granting write access for the whole fleet.

Both require an explicit decision on data ownership, retention period, and
who has dashboard access — the same category of decision already gated by
`docs/rules-policy.md`, not a decision this spec makes unilaterally.

## Open items for the implementation plan

- Exact `NOCOMPRESS` mechanism (env var vs. command prefix)
- Where `.claude/settings.json`'s opt-in flag is documented for Builders
- ~~Whether `report.py` needs a `--since` / session-scoping option, or
  whether reading the whole local log file is sufficient for MVP~~ **RESOLVED:** no
  time filter in MVP; delete/rotate the stats file to reset measurement.

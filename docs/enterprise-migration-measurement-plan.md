# Enterprise Migration — Developer Usage Measurement Plan

Date: 2026-07-02 · Owner: Amit Rosen, AI Architecture
Status: ready to execute · Related open items: #2 (Team vs Enterprise), #10 (Business Case), #13 (migrating existing Team-tier work)

## Why now, and why developers

The first cohort receiving Enterprise access is the **developers** — which
is also the ideal measurement population: all six command types the
compressor covers (git status/diff/log, pytest, npm test, eslint/ruff) are
developer commands, so parser coverage is maximal exactly there. Developers
are also a forgiving pilot population for latency and can report issues
precisely.

**The primary goal is NOT "check whether compression pays off"** — it is
to produce the number the organization does not have today: **how many
tokens a real developer consumes per day/month**, which is the input to:
1. Calibrating programmatic Spend Limits (Enterprise-only)
2. The quantitative slide in the leadership Business Case (#10)
3. Sizing/structuring the Enterprise contract in negotiation

Compression is measured along the way, against the Phase 1 gates already
defined in the spec
(`docs/superpowers/specs/2026-07-02-command-output-compressor-design.md`).

## Population and duration

- **2-3 developers** from the first Enterprise cohort, each on at least one real work project
- **Two weeks** of normal (not synthetic) work — minimum one week before drawing conclusions
- Informed opt-in: each developer knows what is collected (see Privacy below) and how to turn it off (`KESHET_NOCOMPRESS=1`)

## What gets deployed on each machine

Per `enforcement/README.md` (deployment + runtime sections):
1. `.claude/hooks/post_tool_use_compressor.py` + `.claude/compression/` (from the repo, pinned tag)
2. The PostToolUse block from `project-settings.example.json` into the project's settings
3. Python: the machine's installed interpreter if present; otherwise the portable
   runtime per the documented recipe
   (⚠️ subject to the hardening rules — never combine a user-writable path with an EDR exclusion)
4. `.claude/compression-stats.jsonl` added to the target project's .gitignore

### Day-one verification checks (mandatory before trusting any data)

- [ ] Verify `updatedToolOutput` semantics on a real machine — specifically whether
      stderr output (jest!) is swallowed/preserved (Important finding #1 from the final review)
- [ ] `python`/`python3` actually resolves in the hook command (see `_comment_5`)
- [ ] Events are written to the stats file after real git/pytest commands
- [ ] Perceived latency: the developer runs 10 ordinary git commands and reports how it feels

## Required metrics

| # | Metric | Source | Serves |
|---|---|---|---|
| 1 | **Tool-input tokens per developer per day** (cumulative raw_tokens_est + invocation denominator) | `report.py` | Contract sizing, Spend Limits, leadership slide |
| 2 | Coverage rate: % of tool calls with a parser out of all calls | skip-counts in the report | Whether the compressor is relevant at all |
| 3 | Savings on covered commands (target ≥60%, criterion 1) | `report.py` | Compressor rollout decision |
| 4 | Actual p95 latency + user complaints (criterion 2 — currently known ~1-2s) | duration_ms + reports | Rollout decision + EDR/binary prioritization |
| 5 | Zero information-loss incidents (criterion 3 — absolute) | Developer reports + spot checks | Blocks rollout if failed |
| 6 | Parser error rate <1%, all fail-open (criterion 4) | error field in the report | Code health |

## Deliverables at the end of the period

1. **One numbers report** (cumulative report.py table per developer + average) —
   the input for the "cost per developer" slide in the leadership deck
2. **Go/no-go decision on the compressor** per the Phase 1 gates — including the
   legitimate option "shelve compression, keep the measurement infrastructure"
3. **Initial spend-cap recommendation** — proposed Spend Limits values per group based
   on measured consumption (replacing the current guesswork table in the
   agentic-loop-guard reference)
4. If continuing: Phase 2 plan (App Insights — direction selected 2026-07-02)

## The full data stack — what Enterprise unlocks (verified against official docs, 2026-07-02)

Three complementary layers, all landing in App Insights (the direction selected for Phase 2):

| Layer | Source | Answers | Availability |
|---|---|---|---|
| Cost per developer | **Claude Code Analytics API** (`/v1/organizations/usage_report/claude_code`) — tokens + estimated cost per user/day/model, sessions, lines of code, commits, suggestion acceptance rates. Free. | "Who consumes what" — the input for Spend Limits and the executive slide | For claude.ai orgs: via the Enterprise Analytics API (Analytics key) — unlocked by the migration |
| Real-time | **Claude Code's built-in OpenTelemetry** → OTLP → App Insights | Tokens per session, anomaly alerts | Available today; requires env-var configuration on developer machines |
| Command-level | **compression-stats** (this repo) | "Which commands inflate the context" — the resolution no Anthropic API provides | Available today |

**The Compliance API is deliberately NOT in the cost stack:** it is an audit
tool (activity feed + access to chat/file content) with no token/cost data —
using it for cost analysis would require reading content, exactly the
surveillance layer this program avoids. Costs are fully obtained from the
layers above without touching anyone's content. See the next section for the
Compliance API's actual, scoped role.

## The self-improvement loop (Compliance API's scoped role)

Goal as stated by the program owner: when the data shows a wasteful action —
e.g. Claude using a connector inefficiently, or a session pattern that burns
tokens — link that action to its cost, understand it, and feed the fix back
into the skills library and the enforcement tooling. Not surveillance of
people; continuous improvement of the system.

### Loop stages

1. **Detect** — the App Insights dashboard flags an expensive pattern:
   a per-user/day cost spike (Analytics API), a token-heavy session (OTel),
   or an outsized command kind (local stats).
2. **Explain** — the **Compliance API activity feed** supplies the missing
   *action* dimension: what kind of activity was happening in that window —
   which connector was invoked, which project/chat context. Join key:
   actor email × time window. **Metadata first**; content access only for a
   specific flagged pattern, under the governance boundary below.
3. **Attribute** — map the wasteful pattern to the control that should have
   prevented it: a missing parser? a `context-hygiene` rule? a
   `model-router` misroute? connector misuse covered by
   `docs/approved-mcp-connectors.md` or the guardrails skill?
4. **Remediate** — change the responsible artifact in this repo: update the
   skill text, add a parser + dispatch row, add a hook rule, adjust the
   routing table. The repo is the remediation surface.
5. **Verify** — re-run the relevant behavioral scenario
   (`enforcement/tests/behavioral-scenarios.md`) AND re-measure the same
   metric. A remediation without a measured delta does not count as done.

### Worked example

Detected: input-token spikes whenever a session touches the Jira connector
(OTel), matching activity-feed windows showing repeated full-board fetches
(Compliance metadata). Cost attributed: ~$X/week across the cohort.
Remediation: a `context-hygiene` rule ("fetch only the tickets relevant to
the task, never the full board") and, later, an MCP-output parser (Phase 2
scope). Verified: input tokens per Jira-touching session drop Y% the
following week — loop closed.

### Governance boundary (what keeps this from becoming Big Brother)

- Analysis operates on **aggregated patterns**, never individual report cards;
  outputs are skill/tooling changes, not conclusions about people.
- **Metadata before content**: the activity feed's event metadata is the
  default; reading underlying chat/file content requires a specific flagged
  pattern, a documented reason, and CISO sign-off — the same review path as
  any other 🔴-classified data access.
- The Compliance API key lives with the security function, not the FinOps
  function; FinOps consumes derived, aggregated views only.
- Participating developers are told this loop exists and what it reads.

## Privacy and classification

The stats file contains: timestamps, tool name, command kind, sizes, run
durations, error field. **No command content, no output, no code.**
Classification: 🟡 Internal. Before Phase 2 (centralized shipping to App
Insights) — formal approval against the data-classification table + notify
participating developers.

## Out of scope for this plan

- Org-wide rollout of any component — measurement on the cohort only
- Code changes to the compressor (beyond fixing bugs the measurement surfaces)
- The Enterprise decision itself — this plan feeds it, it does not make it

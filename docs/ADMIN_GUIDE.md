# keshet-claude-skills — Admin Guide

**For:** anyone who needs to operate, extend, or troubleshoot this repo — not just the original author.
**Owner:** AI Architecture (Amit Rosen) · **Repo:** `Amitro1234/keshet-claude-skills` · **Last updated:** 2026-07-01

If you're new to this repo, read this document top to bottom once. It explains what every file is, when it's used, and what to do (and not do) with it. Nothing here requires you to already know Claude Code internals — where a concept needs explaining, it's explained inline.

---

## 1. What this repo actually is, in 30 seconds

This repo is a library of **Skills** — markdown files that tell Claude how to behave in specific situations (e.g. "when writing SQL, follow these naming rules" or "before every task, pick the cheapest capable model"). It's split into three concerns that are easy to conflate but serve different purposes:

| Concern | Directory | Question it answers |
|---|---|---|
| **Cost control (FinOps)** | `claude-enterprise-skills/` | "Are we spending tokens efficiently?" |
| **Build quality gates** | `keshet-builder-skills/` | "Is this application safe/tested/documented enough to ship?" |
| **Real enforcement** | `enforcement/` | "What actually *stops* someone, versus what's just a suggestion Claude reads?" |

A skill file is **not code** — it's text Claude reads and (usually) follows. It does not, by itself, stop anyone from doing anything. `enforcement/` is the one directory in this repo that contains actual executable logic (a Python hook, JSON permission configs) — that's the only part of this repo that Claude Code itself enforces regardless of what any prompt says. Keep that distinction in mind throughout: most of this repo is *guidance*, a small part of it is *enforcement*, and `docs/rules-policy.md` is the document that tells you which is which, rule by rule.

---

## 2. Full directory map

```
keshet-claude-skills/
├── README.md, CHANGELOG.md, CLAUDE.md, .gitignore     ← repo-level docs (§3)
├── .github/workflows/validate-skills.yml               ← CI (§3)
├── tools/validate-skills.ps1                           ← structural validator (§3)
│
├── claude-enterprise-skills/        ← FinOps skills (§4)
│   ├── README.md
│   ├── _shared/model-tiers.md       ← single source of truth for model IDs/pricing
│   ├── model-router-skill/SKILL.md
│   ├── context-hygiene/SKILL.md
│   ├── output-discipline/SKILL.md
│   ├── prompt-caching/SKILL.md
│   ├── agentic-loop-guard/SKILL.md
│   └── batch-detector/SKILL.md
│
├── keshet-builder-skills/           ← Builder Flow quality gates (§5)
│   ├── README.md
│   ├── spec-pack/SKILL.md
│   ├── security/SKILL.md
│   ├── architecture/SKILL.md
│   ├── db-structure/SKILL.md
│   ├── code-review/SKILL.md
│   ├── documentation/SKILL.md
│   ├── unit-test/SKILL.md
│   ├── audit-logging/SKILL.md
│   ├── deployment/SKILL.md
│   ├── monitoring-alerting/SKILL.md
│   └── memory/SKILL.md
│
├── company-agent-guardrails/SKILL.md   ← app-agnostic safety guardrails (§6)
│
├── docs/                             ← policy documents, not skills (§7)
│   ├── approved-mcp-connectors.md
│   ├── incident-response.md
│   ├── rules-policy.md
│   └── skills-gap-fixes.md
│
├── templates/                        ← files you copy into other repos (§8)
│   ├── global.CLAUDE.md
│   ├── project.CLAUDE.md.template
│   └── .claudeignore.example
│
└── enforcement/                      ← real, executable enforcement (§9)
    ├── README.md
    ├── managed-settings.example.json
    ├── project-settings.example.json
    ├── hooks/pre_tool_use_guard.py
    └── tests/
        ├── test_pre_tool_use_guard.py
        └── behavioral-scenarios.md
```

---

## 3. Repo-level files

| File | What it is | When you touch it |
|---|---|---|
| `README.md` | The front door. Directory map, quick-start install steps, skill execution order, Builder Flow → skill mapping table, known gaps, estimated cost impact. | Whenever the directory structure changes, or a skill is added/removed — keep the tree diagram honest. |
| `CHANGELOG.md` | Version history, newest first. Each release documents what changed and why. | Every time you ship a batch of changes — add an entry before merging, don't just rely on git log. |
| `CLAUDE.md` (repo root) | A short "what is this repo" primer, meant to be read by Claude itself if someone points Claude at this repo directly (as opposed to installing it as a skill library on a Builder machine). | Rarely — keep in sync with README.md's directory tree if it drifts. |
| `.gitignore` | Standard git ignore rules for this repo's own housekeeping (not to be confused with `templates/.claudeignore.example`, which is a *different* file for a *different* purpose — see §8). | Rarely. |
| `.github/workflows/validate-skills.yml` | GitHub Actions CI. Runs `tools/validate-skills.ps1` on every PR touching a `SKILL.md`, and on every push to `main`. This is what makes "0 failures" claims in the CHANGELOG verifiable rather than just asserted. | Only if you change what CI validates, or which branches trigger it. |
| `tools/validate-skills.ps1` | PowerShell script. Checks every `SKILL.md` for required structure: frontmatter (`name:`, `description:`), required sections (`## Purpose`, `## Trigger Conditions`, `## What NOT to do`), and a `PASS`/`VERDICT` keyword in the output format. **Important limitation:** this validates *structure*, not *content accuracy*. It will pass a skill that has the right headings but a wrong price or a stale model name in the body — see `docs/skills-gap-fixes.md` and the audit this repo's `enforcement/` layer grew out of. Must be saved as UTF-8 **with BOM** — Windows PowerShell 5.1 (the Builder default) misreads it as ANSI otherwise and fails to parse the file's em-dashes/box-drawing characters. | When adding a new required section across all skills, or fixing a validator bug. Run it locally with `.\tools\validate-skills.ps1` from the repo root before opening a PR. |

---

## 4. `claude-enterprise-skills/` — FinOps (cost control)

These are the skills that keep token spend under control. They don't gate whether an app is safe to ship — they govern *how efficiently* Claude works while building it.

| File | What it does | Trigger | Platform reality |
|---|---|---|---|
| `_shared/model-tiers.md` | **The single source of truth for model IDs and pricing.** Every other skill that needs a model ID or a $/token figure links here instead of hardcoding it. Contains the pinned model IDs for Tier 1/2/3, the pricing table (input/output/cache read/cache write), and a documented quarterly update procedure. | N/A — this is reference data, not a behavioral skill. | N/A. |
| `model-router-skill/SKILL.md` | Forces Claude to classify every task into Tier 1 (Haiku)/2 (Sonnet)/3 (Opus) *before* starting, and announce it. Has upgrade/downgrade modifiers (production-critical paths, 🔴 Confidential data, user says "use the best model", etc.). | Before every task, without exception. | Claude Code CLI: `/model` flag. Cowork/Chat: select from the UI model picker — there is no slash command outside the CLI. |
| `context-hygiene/SKILL.md` | Pre-flight token budgeting: excludes junk (`node_modules`, lockfiles, binaries) via `.claudeignore`, caps single-file reads at 200 lines, compresses conversation history past 40K tokens. | Session running >20 min, >4 files about to be read, "analyze the whole codebase"-style requests. | Full support on CLI. On Cowork, treat the `.claudeignore`-respecting claim as *aspirational* until you've verified Cowork actually parses it the same way the CLI does — it wasn't confirmed against Cowork's actual connected-folder behavior as of this writing. |
| `output-discipline/SKILL.md` | Diffs over full-file rewrites, a response-length table by question type, no filler phrases, no unsolicited extras (tests/READMEs the user didn't ask for). | Always active. | Full support everywhere — pure behavioral rules, nothing CLI-specific. |
| `prompt-caching/SKILL.md` | API/SDK-only: when to mark content cacheable (>1,024 tokens, reused across requests), the actual `cache_control` JSON shape, the break-even cost formula, both the 5-minute (1.25x write premium) and 1-hour (2x) cache tiers. | Large static content (system prompts, Spec Packs) sent more than once. | **Not applicable to interactive Claude Code, Cowork, or Chat** — those manage caching automatically. This skill is for people writing pipelines against the raw API/SDK. |
| `agentic-loop-guard/SKILL.md` | Hard behavioral ceilings on autonomous sessions: checkpoint every 10 tool calls, hard stop at 50, max 3 retries on a failed op, loop detection, a 200K-token cost alert. Also documents the org's spend-cap reference table (Builder $150/mo, Safe Use $30/mo, Automation $200/mo). | Any session where Claude executes tool calls autonomously, especially >5 sequential calls or "just handle it"-style broad autonomy grants. | Full support on CLI and Cowork; partial on Chat (autonomous multi-step loops are rarer there, correctly downgraded). **The dollar figures in the spend-cap table are illustrative, not fetched from the real Admin Panel** — verify they match your actual Claude Enterprise Admin Panel configuration before treating them as fact. |
| `batch-detector/SKILL.md` | Detects batch-eligible workloads (N>10 items, can wait 24h) and forces a stop-and-flag before a synchronous API call proceeds, showing the real Batch API request shape. | Bulk operations, scheduled/nightly jobs, CI/CD steps, eval runs. | CLI/SDK pipeline builders only — explicitly not applicable to Cowork or Chat (those users don't write Batch API jobs). |

**Common mistake to avoid:** don't add a new model ID or price anywhere except `_shared/model-tiers.md`. If you find yourself typing `claude-opus-` or a dollar sign followed by a per-token rate in any *other* file in this directory, stop and add a pointer to `_shared/model-tiers.md` instead. This exact mistake (a hardcoded model string that went stale in 5 of 6 files after one release) is why the shared file exists — see `_shared/model-tiers.md`'s own header for the story.

---

## 5. `keshet-builder-skills/` — Builder Flow quality gates

These are the mandatory gates a Builder's project passes through on the way to Production. Each one maps to specific steps in the 11-step Builder Flow (defined in the master project doc, not in this repo). Every skill in this directory ends its review with a structured `VERDICT: PASS/FAIL`-style block — that's the contract every skill in this directory follows, so a human or a future automation can grep for it.

| File | Gate step(s) | What it checks | Verdict format |
|---|---|---|---|
| `spec-pack/SKILL.md` | Step 5 (before any code) | Generates PRD + Technical Spec + Acceptance Criteria from templates. Hard rule: no code until Champion/Owner approves at Step 6. Cross-checks external integrations against `docs/approved-mcp-connectors.md` by name. | `VERDICT: PASS — ready for Step 6 / FAIL — [blocking items]` |
| `security/SKILL.md` | Steps 7, 8, 10 | 7-point checklist: secrets, data classification, input validation, auth, logging, dependencies, deployment config. Links the MCP-connector check to `docs/approved-mcp-connectors.md` explicitly. | `VERDICT: PASS / BLOCK` |
| `architecture/SKILL.md` | Step 7→8 | App-size classification (Local Demo/Department Tool/Production), 4-layer structure rules, tech-selection guidance, an 8-item anti-pattern table. Links connector rules to `docs/approved-mcp-connectors.md`. | `VERDICT: PASS / NEEDS REVISION` |
| `db-structure/SKILL.md` | Step 7→8 | Naming conventions, required types (`NUMERIC` not `FLOAT` for money, `TIMESTAMPTZ` not `TIMESTAMP`), a "dangerous migrations" list requiring explicit approval (e.g. any migration on a table with >1M rows). | `VERDICT: PASS / NEEDS REVISION` |
| `code-review/SKILL.md` | Step 8, Step 10 | 5-dimension review (correctness, security, maintainability, performance, tests) using the org's severity model (🔴 BLOCKER / 🟡 MAJOR / 🟢 MINOR / 💡 SUGGESTION — defined once in `keshet-builder-skills/README.md`, reused by every skill in this directory). Explicitly defers to `security` and `unit-test` rather than duplicating their checks. | `VERDICT: PASS / CONDITIONAL PASS / FAIL` |
| `documentation/SKILL.md` | Step 7→8 | Five documentation layers: `CLAUDE.md` template, README, inline-comment rules, API docs, and a Production runbook. | `VERDICT: PASS / NEEDS REVISION` |
| `unit-test/SKILL.md` | Step 7→9 | Coverage thresholds by layer (business logic 80%, API routes 100%), AAA test structure, "never mock your own business logic" rule. | `VERDICT: PASS / NEEDS REVISION` |
| `audit-logging/SKILL.md` | Step 7→10 | Splits application logs (30-day retention) from the audit trail (1yr+, append-only), a JSON schema for audit entries, a PII/secrets denylist for what's allowed in logs. Escalates per the severity levels in `docs/incident-response.md`. | `VERDICT: PASS / NEEDS REVISION` |
| `deployment/SKILL.md` | Steps 9–11 | Pre-flight 6-item checklist, separate Stage and Production deployment sequences, a 60-minute post-deploy monitoring window, a 5-step rollback procedure. Bans Friday/broadcast-event/peak-hour deploys — the one genuinely Keshet-specific operational rule in this file. | Three separate blocks: Stage sign-off, Production sign-off, Rollback declare/complete |
| `monitoring-alerting/SKILL.md` | Step 10→11 | Three monitoring layers (health check, app metrics, log-based), an SLO table (99.5% availability, tightened to 99.9% for 🔴 data), 5 alert templates. Maps its own CRITICAL/HIGH/MEDIUM alert severity to `docs/incident-response.md`'s P1–P4 scale. | `VERDICT: PASS — ready for Production / NEEDS REVISION` |
| `memory/SKILL.md` | Every session | Three parallel protocols depending on platform: Claude Code CLI (git-committed `.claude/memory/` files), Cowork (same files, in the connected folder — with an explicit fallback if the folder isn't git-backed), and In-Conversation (Chat, or Cowork with no connected folder — chat-only structured summary blocks). Run a "Platform Detection" step first to pick the right protocol. | `VERDICT: PASS — session memory complete` |

**How these interlock:** `code-review` explicitly says "if `security` hasn't run yet, run it now" — that's the one skill-to-skill dependency written into the text. Everything else runs independently at its own trigger point; there's no other automatic chaining. If you're debugging "why didn't skill X catch this," check whether X's trigger conditions actually matched the situation — most gaps are trigger-condition misses, not logic bugs.

---

## 6. `company-agent-guardrails/SKILL.md`

This one is structurally different from everything else in the repo, and it's easy to misread it as "the security rules" when it's actually a **meta-skill for drafting guardrails** — most of its content is a workflow for producing *new* guardrail documents (a Deny/Ask/Monitor taxonomy, a rule-drafting workflow, a placement guide covering both Claude *and* Cursor). The one section that's an actual fixed policy, not a drafting process, is **"Recommended Default Stance"**:

- **Deny:** secret exfiltration, pipe-to-shell, disabling sandbox/permissions, destructive system commands, credential-store access.
- **Ask:** git push/force-push, deploys, package installs, schema changes, writes outside the project directory, any MCP call not on the approved list.
- **Monitor:** all shell execution, in-project file writes, external API calls (logged, not blocked).

This is the policy that `enforcement/` actually implements in code (see §9) — when you're trying to figure out *why* a given settings.json rule exists, trace it back to this Deny/Ask/Monitor table first.

---

## 7. `docs/` — policy documents (not skills)

Files here are referenced *by* skills, but aren't skills themselves — no frontmatter, no trigger conditions, they're just policy.

| File | What it is | Status |
|---|---|---|
| `approved-mcp-connectors.md` | The authoritative allowlist of MCP connectors Builders/agents may use, by data classification and scope (read/write/execute). Includes the request process for adding a new connector. Referenced by name from `spec-pack`, `security`, and `architecture` skills. | Live — but hand-maintained. See the duplication-risk note in §9. |
| `incident-response.md` | P1–P4 severity levels, containment procedures per incident type, notification rules, a post-incident review template. | **Escalation contacts (CISO, Legal, Builder's Manager, Champion/Owner) are still `[fill in]` placeholders.** This document is not actually usable in a real incident until those are filled in — that's the single highest-priority open item in this whole repo. |
| `rules-policy.md` | The organizational Rules document: takes every mandatory skill and states, per rule, exactly what mechanism enforces it and how strong that enforcement really is (🔒 Hard / 🔐 Hard-if-managed / ⚠️ Advisory-only). Split into Admin-tier rules (the FinOps skills), Builder-tier rules (the 11 Builder Flow skills), shared Guardrails, and a separate section on what's different for Safe Use (Cowork/Chat) users who have no hooks or settings.json at all. | Draft — not yet signed off by Security/CISO. Read this before assuming any rule in this repo is actually enforced rather than just written down. |
| `skills-gap-fixes.md` | A point-in-time gap-analysis document (dated 2026-06-28) listing structural fixes that were needed across the library (missing sections, stale model names, header mismatches). Most of what it describes has already been applied — check `CHANGELOG.md`'s 2.1.0/2.1.1 entries before assuming an item here is still outstanding. | Historical record — useful for understanding *why* the current structure looks the way it does, not a live task list. |

---

## 8. `templates/` — files you copy into *other* repos

These aren't read in place; they're meant to be copied elsewhere.

| File | Copy to | What it does |
|---|---|---|
| `global.CLAUDE.md` | `~/.claude/CLAUDE.md` on a Builder's machine (once, machine-wide) | Activates all the FinOps skills and Builder gates on every project that machine touches. Model IDs are deliberately *not* hardcoded here — it points to `claude-enterprise-skills/_shared/model-tiers.md` instead, specifically so this file never needs editing just because a model shipped. **This only works for Claude Code CLI** — Cowork and Chat don't read a home-directory config file, so this file has no effect there. |
| `project.CLAUDE.md.template` | `[new-project-root]/CLAUDE.md` | Per-project scaffold: data classification block, architecture layer diagram, active-skills-by-trigger-step list, Builder Flow status tracker, memory-file pointers. **This one *does* work in Cowork too** — Cowork reads a project-root `CLAUDE.md` from the connected folder automatically, the same mechanism Claude Code CLI uses for project-level context. |
| `.claudeignore.example` | `[project-root]/.claudeignore` | Standard exclusion list referenced by `context-hygiene/SKILL.md` — dependencies, build output, binaries, lockfiles, secrets, coverage output, editor noise. Copy and adjust per project (e.g. uncomment the migrations/generated-code sections if relevant). |

---

## 9. `enforcement/` — the part that's actually enforced

Everything above this section is text Claude reads. This directory is different: it's executable configuration and code that Claude Code itself checks, independent of what any prompt says. Read `enforcement/README.md` in full before touching anything here — it explains the three enforcement tiers (Instruction-level / Project settings / Managed settings) and exactly which rules are hard-enforceable today versus permanently advisory-only. The summary:

| File | What it is | Deploy to |
|---|---|---|
| `README.md` | The enforcement-layer explainer: which of the three tiers is un-bypassable (managed settings — and importantly, this does **not** require an Enterprise plan; the on-disk file mechanism works on Team too, pushed via ordinary IT tooling like Intune/GPO/Jamf), what's genuinely hard vs. "hard but the Builder owns the file" vs. permanently advisory. | Read, don't deploy. |
| `managed-settings.example.json` | The un-bypassable tier. Locks the MCP connector allowlist and denies the highest-risk actions (reading `.env`/credential files, `git push --force`, `sudo`, pipe-to-shell) org-wide. | Push via IT tooling (any plan) to the OS-standard managed-settings location, or via the claude.ai admin console (Team or Enterprise). |
| `project-settings.example.json` | The "Ask" tier from the Guardrails Recommended Default Stance — git push, deploys, package installs, migrations. Editable by the Builder, but changes show up in git history/PRs. Also wires in the hook below. | Ship as the default `.claude/settings.json` in the org's Builder repo template (Builder Flow Step 3: Provisioning). |
| `hooks/pre_tool_use_guard.py` | A `PreToolUse` hook — real Python, actually executed by Claude Code before a tool call runs. Catches things a settings.json glob can't: `cat .env` (a Bash call, not a `Read` tool call, so the file-glob deny rule alone misses it), calls to MCP tools whose *server* isn't in the hardcoded `APPROVED_MCP_SERVERS` set, and destructive commands with unusual syntax (fork bombs, `mkfs`, raw `dd` writes). **Known, deliberate gap:** it does not catch an obfuscated read like `python3 -c "open('.env').read()"` — that's documented, not hidden, in both this file's docstring and the test suite below. | Copy to `.claude/hooks/pre_tool_use_guard.py` in the org template repo. |
| `tests/test_pre_tool_use_guard.py` | Real, automated, repeatable tests for the hook above — 19 cases, runnable standalone (`python3 tests/test_pre_tool_use_guard.py`) or via pytest. Includes one intentional `xfail` documenting the known gap mentioned above, so nobody re-discovers it and mistakes it for a regression. **Run this after every edit to the hook, or to `docs/approved-mcp-connectors.md`** — the allowlist is currently hand-duplicated into this hook (see the open item below), so a connector added to the doc but not the hook will silently fail these tests, which is the point. | Run locally; wire into CI if you want this checked automatically (not yet done — see open items). |
| `tests/behavioral-scenarios.md` | The non-executable counterpart. Tests *advisory* skills (no hook/settings.json backing) the only way you can test text-based instructions: spawn a fresh Claude session with the skill text plus a realistic user message, grade the response against explicit pass criteria. 3 scenarios validated 2026-07-01 (security catching a live secret under social pressure, spec-pack resisting "let's just start coding," model-router + connector-allowlist blocking an unapproved integration without refusing the whole task — all 3 passed). 4 more scenarios are written but not yet run. | Re-run manually (spawn a fresh session, follow the file's instructions) after editing any advisory skill. |

### Open items in this directory (not yet resolved — don't assume otherwise)

1. **Allowlist duplication:** the approved-connector list is hand-maintained in three places (`docs/approved-mcp-connectors.md`, `managed-settings.example.json`, `hooks/pre_tool_use_guard.py`). If one is updated and the others aren't, they drift silently with no error. A script that generates the JSON/Python lists from the markdown table would close this — not built yet.
2. **Schema verification:** the hook's stdin JSON shape and the managed-settings key names were verified against Claude Code docs as of 2026-07-01 — this is an area Anthropic changes over time. Re-verify against `https://code.claude.com/docs/en/hooks` and `https://code.claude.com/docs/en/admin-setup` before deploying the managed tier to real machines; a mistyped key there could silently do nothing rather than throw an error.
3. **Not yet run inside a real Claude Code CLI session** — everything here has been tested via direct subprocess calls and simulated agent sessions, not an actual Builder machine. Do one dry run (project-tier settings.json only, no managed tier) before wider rollout.

---

## 10. How-to recipes

**Add a new mandatory skill:**
1. Create `[category]/[skill-name]/SKILL.md` with YAML frontmatter (`name:`, `description:`) and the four required sections (`## Purpose`, `## Trigger Conditions`, `## What NOT to do`, plus your own content).
2. Add it to the directory tree in `README.md` and the relevant sub-README (`claude-enterprise-skills/README.md` or `keshet-builder-skills/README.md`).
3. Add it to the Builder Flow mapping table if it gates a specific step.
4. Run `tools/validate-skills.ps1` locally before opening a PR — CI will run it again automatically.
5. If it's a Builder Flow gate, give it a `VERDICT: PASS/FAIL`-style output block to match every other skill in that directory.

**Update model pricing / add a new model:**
1. Edit only `claude-enterprise-skills/_shared/model-tiers.md` — update the table, and the "Last verified" / "Next review due" dates.
2. Grep the repo for the *old* model ID string to confirm nothing else still hardcodes it: `grep -rn "claude-sonnet-5" .` (substitute whatever string you're retiring).
3. This is also done automatically on a quarterly cadence via a scheduled reminder Amit set up — but if a new model ships off-cycle, don't wait for the reminder.

**Add a newly-approved MCP connector:**
1. Add it to the table in `docs/approved-mcp-connectors.md` with its data classification and scope.
2. Add it to `APPROVED_MCP_SERVERS` in `enforcement/hooks/pre_tool_use_guard.py`.
3. Add it to the `allowedMcpServers` array in `enforcement/managed-settings.example.json`.
4. Run `python3 enforcement/tests/test_pre_tool_use_guard.py` to confirm nothing broke.
(Steps 2–4 exist only because of the duplication problem noted in §9's open items — if that gets automated, this recipe shrinks to step 1.)

**Deploy the enforcement layer to a new Builder machine:**
1. Read `enforcement/README.md` in full first — it explains what each tier actually buys you.
2. Copy `project-settings.example.json` → `[project-root]/.claude/settings.json` (or bake it into the org's repo template so every new project gets it automatically).
3. Copy `hooks/pre_tool_use_guard.py` → `[project-root]/.claude/hooks/pre_tool_use_guard.py`.
4. For the managed tier: either push `managed-settings.example.json` to the OS-standard managed-settings location via your IT tooling, or configure the equivalent rules in the claude.ai admin console.

**Set up a new Builder machine from scratch:**
Follow `README.md`'s Quick Start section (§3 above already points you there) — clone the repo to `~/.claude/skills/keshet-claude-skills`, copy `templates/global.CLAUDE.md` to `~/.claude/CLAUDE.md`, and copy `templates/project.CLAUDE.md.template` into each new project.

---

## 11. Ownership and maintenance calendar

| What | Cadence | Owner |
|---|---|---|
| Model IDs/pricing (`_shared/model-tiers.md`) | Quarterly (Jan/Apr/Jul/Oct 1st) — automated reminder already scheduled | AI Architecture |
| Approved connector list + its 3-way duplication | On every new connector request (5 business days per `approved-mcp-connectors.md`'s own SLA) | AI Architecture |
| Incident response contacts (`docs/incident-response.md`) | As soon as the named people are confirmed — currently blocking, not scheduled | AI Architecture + CISO |
| `docs/rules-policy.md` sign-off | Once, before this repo's rules are presented as "the org's actual policy" rather than a draft | Security/CISO |
| Skill structural validation | Automatic, every PR (CI) | N/A (automated) |
| Skill *content* accuracy (pricing, cross-references, no truncation) | Not automated — this is exactly the gap the 2026-07-01 audit found. Manual review recommended each time a skill file is edited. | Whoever makes the edit, spot-checked by AI Architecture |

---

*If something in this repo doesn't match this guide, the guide is stale, not necessarily the repo — check `git log` for what changed since 2026-07-01 and update this file rather than assuming the mismatch means something is broken.*

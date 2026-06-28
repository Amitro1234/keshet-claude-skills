# keshet-claude-skills — Gap Fixes & Missing Sections
# Generated: 2026-06-28
# Purpose: Ready-to-paste content for all structural and content gaps found in the skills audit.
#
# HOW TO USE:
# For each skill below, copy the provided text and insert it into the SKILL.md
# at the location indicated. Then re-run tools/validate-skills.ps1 to verify.

---

## 1. GLOBAL FIX — Platform Compatibility Header

Add this block to the frontmatter description of every skill, or as a note under `## Purpose`:

```
> **Platform compatibility:**
> - Claude Code CLI: ✅ Full support
> - Cowork: ✅ / ⚠️ / ❌  (see per-skill notes below)
> - Claude.ai Chat: ✅ / ⚠️ / ❌  (see per-skill notes below)
```

---

## 2. model-router — Missing Sections + Model Update + Platform Fix

**File:** `claude-enterprise-skills/model-router-skill/SKILL.md`

### 2a. Update model name (Tier 3)

Find and replace:
```
Old: claude-opus-4-7
New: claude-opus-4-8
```

Applies to all occurrences in the routing table, decision logic, slash command examples, and quick reference.

### 2b. Add `## Trigger Conditions` section

Insert after the `## Purpose` section:

```markdown
## Trigger Conditions

This skill activates **before every task**, without exception.

Activate explicitly when:
- A new Claude Code session starts
- The user asks Claude to perform any task (read, write, fix, run, review, design)
- The scope of an in-progress task changes significantly
- A Builder Flow gate is being crossed (Steps 6, 8, 10)
- An agentic session begins (tool calls will be made autonomously)
```

### 2c. Add `## What NOT to do` section

Insert before `## Maintenance`:

```markdown
## What NOT to do

- Do not default to Tier 2 (Sonnet) for tasks that are clearly Tier 1 execution
- Do not use Tier 3 (Opus) for standard bug fixes or routine code writing
- Do not skip announcing the model and tier before starting work
- Do not silently escalate to a heavier model — always announce and confirm
- Do not apply Tier 3 to batch or pipeline jobs — use `batch-detector` skill instead
- Do not use `/model` in Cowork or Chat — select the model from the UI model picker instead
```

### 2d. Add platform note to Step 4 (Set the model)

In the "Step 4 — Announce and set the model" section, add after the slash command block:

```markdown
> **Platform note:**
> - **Claude Code CLI:** use `/model <model-string>` as shown above
> - **Cowork / Claude.ai Chat:** select the model from the model picker in the UI (Opus 4.8 = Tier 3, Sonnet 4.6 = Tier 2, Haiku 4.5 = Tier 1). The slash command is not available outside Claude Code CLI.
```

---

## 3. output-discipline — Missing `## What NOT to do`

**File:** `claude-enterprise-skills/output-discipline/SKILL.md`

The skill has a "What NOT to do" section but uses a different heading. The validator looks for the exact string `## What NOT to do`.

**Fix:** Rename the existing final section header from whatever it currently reads to:

```markdown
## What NOT to do
```

The content already exists — this is a header rename only.

---

## 4. prompt-caching — Missing `## Trigger Conditions` + Platform Note

**File:** `claude-enterprise-skills/prompt-caching/SKILL.md`

### 4a. Add `## Trigger Conditions` section

Insert after `## Purpose`:

```markdown
## Trigger Conditions

Activate this skill when ALL of the following are true:
- The session includes large static content (system prompt, Spec Pack, schema, SDK docs)
- That content exceeds **1,024 tokens**
- The same content will be sent to the model more than once (across turns or requests)

**This skill is for API/SDK integrations only.**
It does not apply to interactive Claude Code sessions, Cowork, or claude.ai Chat —
those environments manage caching automatically. Target audience: developers building
pipelines, automations, or multi-turn API applications using the Anthropic SDK.
```

### 4b. Add platform note under `## Purpose`

```markdown
> **Platform compatibility:**
> - Claude Code CLI (API integrations / pipelines): ✅ Full support
> - Interactive Claude Code sessions: ⚠️ Caching is managed by Claude Code automatically — no manual setup needed
> - Cowork: ❌ Not applicable — users do not control API parameters
> - Claude.ai Chat: ❌ Not applicable
```

---

## 5. company-agent-guardrails — Full Reformat

**File:** `company-agent-guardrails/SKILL.md`

This skill has a completely different structure from all other Keshet skills. It needs three sections added. Insert them at the top of the file body (after the frontmatter `---`):

### Add `## Purpose`

```markdown
## Purpose

Define and enforce practical safety guardrails for AI coding agents across Keshet.
These guardrails reduce accidental harm and improve visibility without blocking
developer productivity. They apply to all agents operating in Claude Code, Cowork,
and any pipeline or automation using Claude.

The goal is not sandbox-grade security — it is to make dangerous actions visible
and require explicit human confirmation before they execute.
```

### Add `## Trigger Conditions`

Insert after `## Purpose`:

```markdown
## Trigger Conditions

This skill is **always active** for any AI agent session. Activate explicitly when:
- A new Claude Code session starts on any Keshet project
- An agent is about to execute shell commands, git operations, or MCP tool calls
- A user grants broad autonomy ("just handle it", "do it automatically")
- A pipeline or automation is being designed or reviewed
- Any action would touch secrets, credentials, or files outside the project directory
```

### Add `## What NOT to do`

Insert before `## Safety Notes` (at the end of the file):

```markdown
## What NOT to do

- Do not install MCP servers, hooks, or persistent services without explicit user approval
- Do not read, display, or pass `.env` files or credential files to any context
- Do not execute destructive shell commands (rm -rf, DROP TABLE, format disk) without confirmation
- Do not push to git or deploy without the user seeing exactly what will be pushed
- Do not access file paths outside the current project directory
- Do not silently retry failed operations — always surface failures to the user
- Do not treat instruction-only guardrail files as enforcement — they guide behavior but do not enforce it at the OS level
```

---

## 6. keshet-builder-skills — Missing `## Trigger Conditions` (all affected skills)

The trigger information already exists in each skill's YAML frontmatter description.
For each skill below, extract that information into a `## Trigger Conditions` section
in the body. Insert it immediately after `## Purpose`.

### 6a. architecture/SKILL.md

```markdown
## Trigger Conditions

Activate this skill when any of the following applies:
- Designing a new service, module, or application from scratch
- Choosing a technology stack or database
- Designing an API or integration pattern
- Structuring an existing codebase that has no clear layers
- The user asks "how should I build this?" or "what architecture should I use?"
- Advancing from Step 7 (Build) to Step 8 (Validation Sandbox)
- Any deviation from standard org patterns is being considered
```

### 6b. audit-logging/SKILL.md

```markdown
## Trigger Conditions

Activate this skill when any of the following applies:
- Any code writes log statements of any kind
- A user action creates, updates, or deletes data
- An admin operation is performed (provisioning, config change, spend cap change)
- An authentication or authorization event occurs
- An MCP tool call is made by an AI agent
- An external API integration is added
- Advancing from Step 7 (Build) to Step 8 (Validation Sandbox)
- Advancing to Production (Step 10 gate)
```

### 6c. code-review/SKILL.md

```markdown
## Trigger Conditions

Activate this skill when any of the following applies:
- The user asks to "review", "check", or "validate" any code
- A git push or merge is about to happen
- The Builder asks "is this ready?" or "can I advance to the next step?"
- Advancing from Step 7 (Build) to Step 8 (Validation Sandbox)
- Advancing from Stage to Production (Step 10 gate)
```

### 6d. db-structure/SKILL.md

```markdown
## Trigger Conditions

Activate this skill when any of the following applies:
- A `CREATE TABLE` or schema definition is being written
- An ORM model (SQLAlchemy, Prisma, Django models, etc.) is being defined
- A migration file is being created or reviewed
- A database access pattern, index, or query is being designed
- The user asks any question about data storage design
- Advancing from Step 7 (Build) to Step 8 (Validation Sandbox)
```

### 6e. deployment/SKILL.md

```markdown
## Trigger Conditions

Activate this skill when any of the following applies:
- The user says "deploy", "push to staging", "go to prod", or "release"
- The Builder is advancing to Step 9 (Stage deployment)
- The Champion/Owner has signed off and the Builder is advancing to Step 10 (Stage→Prod gate)
- A rollback is being considered or executed
- A smoke test needs to be run after deployment
```

### 6f. documentation/SKILL.md

```markdown
## Trigger Conditions

Activate this skill when any of the following applies:
- A new project is being started (CLAUDE.md needs to be created)
- A feature or module is being completed
- The user asks to "write docs", "update the README", or "document this"
- Public functions or API endpoints are being added without docstrings
- Advancing from Step 7 (Build) to Step 8 (Validation Sandbox)
- A Production runbook is needed before Step 10
```

### 6g. memory/SKILL.md

```markdown
## Trigger Conditions

Activate this skill when any of the following applies:
- A Claude Code session starts on any Builder project (always — session start briefing)
- A significant architectural or technical decision is made during a session
- A Builder Flow gate is crossed
- The session has run for more than 15 minutes
- More than 10 tool calls have been made
- The user says "done", "wrap up", "end session", or "that's it for today"
```

### 6h. monitoring-alerting/SKILL.md

```markdown
## Trigger Conditions

Activate this skill when any of the following applies:
- An application is being prepared for Production deployment (Step 10 gate)
- The user asks about SLOs, alerts, dashboards, or on-call rotation
- A new Production service is going live
- An existing Production service has no monitoring configured
- Step 11 (Production Monitoring) begins — run the daily health check
```

### 6i. spec-pack/SKILL.md

```markdown
## Trigger Conditions

Activate this skill when any of the following applies:
- A new project or feature is being started
- The user says "let's write the spec", "what should we build", or "start the project"
- The Builder is at Step 5 in the Builder Flow
- Code is about to be written but no Spec Pack exists yet
- The Champion/Owner asks what will be built

**Hard rule:** No code is written until the Spec Pack is complete and approved at Step 6.
If the user tries to start coding without a Spec Pack, stop and run this skill first.
```

### 6j. unit-test/SKILL.md

```markdown
## Trigger Conditions

Activate this skill when any of the following applies:
- New functions, classes, or modules are being written
- A bug is being fixed (write a test that reproduces the bug first)
- The user asks to "write tests", "add coverage", or "check test coverage"
- The `code-review` skill flags insufficient test coverage
- Advancing from Step 7 (Build) to Step 8 (Validation Sandbox)
- Advancing to Stage deployment (Step 9)
```

---

## 7. Missing `## What NOT to do` — Builder Skills

### 7a. architecture/SKILL.md

Add before the closing of the file (after the Architecture Review Checklist):

```markdown
## What NOT to do

- Do not apply production-grade complexity (microservices, event sourcing) to a Department Tool
- Do not put business logic in API routes — it becomes untestable
- Do not access the database directly from the UI or presentation layer
- Do not use `print()` as logging in any environment — use a structured logger
- Do not choose a technology without a documented rationale (ADR or Spec Pack note)
- Do not deviate from the standard project folder structure without recording it in the Spec Pack
- Do not call external APIs inline in business logic — always through a dedicated client class
- Do not use SQLite in any shared or production environment
```

### 7b. audit-logging/SKILL.md

Add after the Audit & Logging Review Checklist:

```markdown
## What NOT to do

- Do not conflate application logs and audit trail entries — they serve different purposes and audiences
- Do not write audit entries to a standard CRUD table that can be updated or deleted
- Do not log PII (names, emails, phone numbers, IDs) in any log statement
- Do not log credentials, tokens, or API keys — even partially ("sk-...") 
- Do not use `print()` as the logging mechanism in any environment
- Do not disable DEBUG logging by commenting it out — use log level configuration
- Do not route audit entries only to local disk — use the org's centralized SIEM or audit store
- Do not omit the `trace_id` — without it, distributed request tracing is impossible
```

### 7c. db-structure/SKILL.md

Add after the DB Structure Review Checklist:

```markdown
## What NOT to do

- Do not use natural keys (email, phone, external ID) as primary keys — they change
- Do not use `FLOAT` for money or financial values — use `NUMERIC(19,4)`
- Do not use `TIMESTAMP` without timezone — always use `TIMESTAMPTZ`
- Do not use `VARCHAR(255)` — use `TEXT` (PostgreSQL has no performance difference)
- Do not use `ON DELETE CASCADE` unless child data is truly meaningless without the parent
- Do not add a `NOT NULL` column to a large existing table without a default value — it locks the table
- Do not rename columns without a migration plan — it breaks all queries using the old name
- Do not run schema changes directly in Production — always via a numbered migration file
- Do not store production data in Dev or Stage databases — use anonymized fixtures
```

### 7d. documentation/SKILL.md

Add after the Documentation Review Checklist:

```markdown
## What NOT to do

- Do not write CLAUDE.md and then never update it — it must reflect the current state of the project
- Do not write comments that describe what the code is obviously doing ("increment counter")
- Do not leave TODO comments without an owner and issue reference
- Do not write a README aimed at developers when the users are non-technical — know your audience
- Do not skip the runbook for Production apps — ops cannot respond to incidents without it
- Do not document the API only in your head — every endpoint needs a written contract
- Do not use "see the code" as documentation — the code shows what, documentation explains why
```

### 7e. unit-test/SKILL.md

Add after the Test Review Checklist:

```markdown
## What NOT to do

- Do not mock the database — test against a real test database with fixture setup and teardown
- Do not mock your own business logic — if you need to, the design is wrong
- Do not write tests that always pass regardless of the code's behavior (tautological tests)
- Do not share mutable state between tests — tests must be independent and runnable in any order
- Do not call real external APIs (email, SMS, payment, MCP tools) in tests — mock them
- Do not skip writing tests because "it's just a small change" — bugs hide in small changes
- Do not merge code with failing tests — fix the tests or the code, never skip
- Do not use `xfail` as a permanent state — it means "known broken" and must be resolved
```

---

## 8. memory/SKILL.md — Missing PASS/VERDICT output format

**File:** `keshet-builder-skills/memory/SKILL.md`

Add at the end of the Session End Protocol section, after Step 3:

```markdown
### Session End Output Format

```
=== SESSION END REVIEW — [Project Name] ===
Date: [date]
Duration: ~[N] minutes · Tool calls: [N]

Memory files updated:
✅ decisions.md — [N new decisions recorded / no new decisions]
✅ session-log.md — [session summary written]
✅ project-state.md — [updated to current state]

Committed to git: [YES / REMINDER: run git add .claude/memory/ && git commit]

VERDICT: PASS — session memory complete
```
```

---

## 9. spec-pack/SKILL.md — Missing PASS/VERDICT output format

**File:** `keshet-builder-skills/spec-pack/SKILL.md`

The Spec Pack Review Checklist at the end already produces output but does not use the exact `VERDICT: PASS / FAIL` format the validator expects. Update the output format block:

```markdown
```
=== SPEC PACK REVIEW — [Project Name] ===
PRD: [COMPLETE / MISSING: list items]
Technical Spec: [COMPLETE / MISSING: list items]
Acceptance Criteria: [COMPLETE / MISSING: list items]
Ready for Step 6 (Champion Approval): [YES / NO — list blocking items]

VERDICT: [PASS — ready for Step 6 / FAIL — list all blocking items]
```
```

---

## 10. batch-detector — Platform Scope Clarification

**File:** `claude-enterprise-skills/batch-detector/SKILL.md`

Add under `## Purpose`:

```markdown
> **Platform compatibility:**
> - Claude Code CLI (API/SDK development): ✅ Full support — target audience is developers building pipelines and automations using the Anthropic Python/TypeScript SDK
> - Interactive Claude Code sessions: ⚠️ Use only when the Builder is writing pipeline code; not applicable to interactive coding sessions
> - Cowork: ❌ Not applicable — Cowork users do not build Batch API jobs
> - Claude.ai Chat: ❌ Not applicable
```

---

## Summary — Changes by File

| File | Changes Required |
|---|---|
| `model-router/SKILL.md` | Update `opus-4-7` → `opus-4-8`; add `## Trigger Conditions`; add `## What NOT to do`; add platform note to Step 4 |
| `output-discipline/SKILL.md` | Rename final section header to `## What NOT to do` |
| `prompt-caching/SKILL.md` | Add `## Trigger Conditions` with platform scope note |
| `batch-detector/SKILL.md` | Add platform compatibility note under `## Purpose` |
| `company-agent-guardrails/SKILL.md` | Add `## Purpose`, `## Trigger Conditions`, `## What NOT to do` |
| `architecture/SKILL.md` | Add `## Trigger Conditions`; add `## What NOT to do` |
| `audit-logging/SKILL.md` | Add `## Trigger Conditions`; add `## What NOT to do` |
| `code-review/SKILL.md` | Add `## Trigger Conditions` |
| `db-structure/SKILL.md` | Add `## Trigger Conditions`; add `## What NOT to do` |
| `deployment/SKILL.md` | Add `## Trigger Conditions` |
| `documentation/SKILL.md` | Add `## Trigger Conditions`; add `## What NOT to do` |
| `memory/SKILL.md` | Add `## Trigger Conditions`; add PASS/VERDICT output block |
| `monitoring-alerting/SKILL.md` | Add `## Trigger Conditions` |
| `spec-pack/SKILL.md` | Add `## Trigger Conditions`; update output block to include VERDICT keyword |
| `unit-test/SKILL.md` | Add `## Trigger Conditions`; add `## What NOT to do` |

**After applying all changes:** re-run `tools/validate-skills.ps1` — expected result: ALL SKILLS PASS.

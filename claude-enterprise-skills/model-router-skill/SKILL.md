---
name: model-router
description: >
  Dynamic model router for Claude Code — automatically selects the most cost-effective
  Claude model for each task instead of always defaulting to the most expensive model.
  ALWAYS use this skill at the start of any Claude Code session, or whenever the user
  asks Claude to perform a task of any kind (read files, run tests, lint, write code,
  refactor, review architecture, debug, etc.) so the right model is chosen before work
  begins. Triggers on: any coding task, file operations, test runs, linting, code review,
  architecture planning, debugging, or any request where model selection matters for the
  cost/quality tradeoff. When in doubt — use this skill.
---

# Model Router — Keshet Enterprise Edition

## Purpose

Select the appropriate Claude model **before starting any work**, based on task complexity
and required reasoning depth.

Claude Code defaults to expensive models for everything — even trivial tasks like running
`ruff`, reading a file, or checking `git status`. This wastes budget on work that Haiku
handles just as well. The router fixes that by routing each task to the cheapest model
that can handle it well.

**Keshet cost context:** Sonnet costs several times more than Haiku per token (see
`_shared/model-tiers.md` for the current ratio). A team of 20 Builders
defaulting to Sonnet for every operation spends ~$130K/year on API. Consistent routing
reduces that to ~$95K — a saving of ~$35K without reducing quality.

---

## Trigger Conditions

This skill activates **before every task**, without exception.

Activate explicitly when:
- A new Claude Code session starts
- The user asks Claude to perform any task (read, write, fix, run, review, design)
- The scope of an in-progress task changes significantly
- A Builder Flow gate is being crossed (Steps 6, 8, 10)
- An agentic session begins (tool calls will be made autonomously)

---

## Routing Table

> Model IDs and prices are **not** hardcoded here — `claude-enterprise-skills/_shared/model-tiers.md`
> is the single source of truth. Check that file for the current pinned model ID and
> per-1M price before relying on any number in this section.

| Tier | Model | Cost (input/output per 1M) | Use When |
|---|---|---|---|
| **1 — Light** | see `_shared/model-tiers.md` | see `_shared/model-tiers.md` | File reads, grep, lint, tests, bash, config parsing |
| **2 — Standard** | see `_shared/model-tiers.md` | see `_shared/model-tiers.md` | Write code, fix bugs, refactor, test writing, debug, code review |
| **3 — Heavy** | see `_shared/model-tiers.md` | see `_shared/model-tiers.md` | Architecture, security audit, greenfield design, threat modeling |

> **Default when uncertain:** Tier 2 — see `_shared/model-tiers.md` for the current Tier 2 model ID

---

## Decision Logic

### Step 1 — Classify the task

**Tier 1 — Execution only (no reasoning)**
- Read / list / search files
- Run: `ruff`, `black`, `mypy`, `pytest`, `eslint`, `pre-commit`, `shellcheck`
- `grep`, `ripgrep`, `find`, `awk`, `jq`
- `git status`, `git log`, `git diff`, `git blame`
- Parse config, extract a value, count lines, diff two files
- Trivial docstring or one-liner comment
- Check file existence, verify environment variables
- Run smoke tests, verify a deployment succeeded

**Tier 2 — Reasoning required**
- Write a new function, class, or module
- Fix a bug — single file or multi-file
- Refactor — single module or cross-cutting
- Write or update unit / integration tests
- Explain what a code block does
- Debug across multiple files or services
- Code review with trade-off analysis
- Integrate a new library or connector (MCP, API)
- Feature implementation within existing architecture
- Build step in the Keshet Builder Flow (steps 2–8)
- Spec Pack generation (PRD, Technical Spec, Acceptance Criteria)

**Tier 3 — Deep reasoning (architectural, security, greenfield)**
- Greenfield service or system design
- Security audit and threat modeling
- Evaluating competing architectural approaches
- Diagnosing intermittent production issues with no clear root cause
- Cross-cutting concerns affecting the whole platform
- Data Classification decisions with legal/compliance impact
- Gate decisions: Stage→Production (Builder Flow Step 10)
- "I don't know where to start" — no clear path forward
- Strategic decisions with long-term consequences
- Any task where the CISO or Legal must be in the loop

---

### Step 2 — Apply modifiers

**Upgrade one tier if:**
- The task touches production-critical paths: auth, payments, data migrations, broadcast infrastructure
- The codebase is >10K LOC and the task is cross-cutting
- User says: "use the best model", "I need this solid", "don't rush"
- Data classification is 🔴 Confidential (employee data, contracts, customer data)
- The Builder Flow gate is Stage→Prod (step 10) — always upgrade to Tier 3 review

**Downgrade one tier if:**
- User says: "quick check", "just verify", "fast scan", "don't overthink"
- Output will be reviewed before any action is taken
- Change is purely additive with no risk of breaking existing behavior
- Data classification is 🟢 Public or 🟡 Internal only

---

### Step 3 — Agentic and tool-use routing

When Claude is running as an **agent** (executing tool calls autonomously), apply
these additional rules:

| Agent action | Tier | Model |
|---|---|---|
| File reads, shell commands, grep | 1 | Haiku |
| Generating code or documents | 2 | Sonnet |
| Planning the overall task strategy | 2 | Sonnet |
| Evaluating security / architectural risk | 3 | Opus |
| Final review before a Stage→Prod gate | 3 | Opus |

For pipelines and automation (CI/CD, nightly jobs):
- Always set model explicitly — do not rely on routing heuristics
- Default pipeline model: the Tier 1 model (see `_shared/model-tiers.md` for the current pinned ID)
- Escalate to Sonnet only for code generation steps
- Combine with `batch-detector` skill for jobs processing >10 items

---

### Step 4 — Announce and set the model

Always state the routing decision before starting work (model IDs below are examples —
see `_shared/model-tiers.md` for the current pinned values):

> "Task: run lint and show failures → **Tier 1**, using the Tier 1 model."
> "Task: implement SharePoint connector module → **Tier 2**, using the Tier 2 model."
> "Task: security audit of API gateway → **Tier 3**, using the Tier 3 model."

Set the model via slash command if needed (substitute the current pinned ID for
each tier from `_shared/model-tiers.md`):
```
/model <tier-1-model-id>   # Tier 1 — see _shared/model-tiers.md
/model <tier-2-model-id>   # Tier 2 — see _shared/model-tiers.md
/model <tier-3-model-id>   # Tier 3 — see _shared/model-tiers.md
```

> **Platform note:**
> - **Claude Code CLI:** use `/model <model-string>` as shown above
> - **Cowork / Claude.ai Chat:** select the model from the model picker in the UI, matching the current Tier 1/2/3 pins in `_shared/model-tiers.md`. The slash command is not available outside Claude Code CLI.

---

## Mid-Session Model Switch Protocol

Models cannot be switched automatically mid-task. When scope escalates during a session, follow this protocol by platform:

### Claude Code CLI

1. Stop work. Announce the escalation:
   ```
   ESCALATION: Task scope changed — this now requires Tier [N] (was Tier [N-1]).
   Reason: [what changed — e.g., "bug is in the auth layer, production-critical"]
   Action required: please run /model claude-[model] to switch, then type "continue".
   ```
2. Wait for the user to run the slash command.
3. Resume only after the model switch is confirmed.

### Cowork

1. Stop work. Announce:
   ```
   ESCALATION: This task needs a heavier model (Tier [N]).
   Action: click the model picker (top of the chat) → select [Opus 4.8 / Sonnet 5].
   Then start a new message to continue — I'll pick up from where we left off.
   ```
2. At the start of the next message, re-state the context and continue.

### Claude.ai Chat

Same as Cowork — model selection is in the UI picker. Announce the escalation, ask the user to switch, then continue in the next message.

### When NOT to escalate mid-session

If the escalation is minor (Tier 1 → Tier 2 only) and the remaining work is small (<5 tool calls), continue with the current model and note the cost difference:
```
Minor escalation: continuing with Sonnet instead of Haiku for this step.
Estimated additional cost: ~$0.002 — acceptable for this task size.
```

---

## Quick Reference

Model IDs intentionally omitted below — see `_shared/model-tiers.md` for current pins.
```
TIER 1 → read, run, find, lint, format, check, diff
TIER 2 → write, fix, test, explain, refactor, debug, review, spec
TIER 3 → design, architect, audit, investigate, gate-decision
```

---

## Keshet Builder Flow — Tier Mapping

| Builder Flow Step | Recommended Tier | Reason |
|---|---|---|
| Step 1: Access Request review | 2 | Needs judgment on scope and data classification |
| Step 2: Local environment setup | 1 | Tooling, file ops |
| Step 3: Repo provisioning | 1–2 | Mostly execution; Sonnet for template decisions |
| Step 4: Documentation / ticket | 2 | Writing quality matters |
| Step 5: Spec Pack generation | 2 | PRD, Technical Spec, Acceptance Criteria |
| Step 6: Spec approval review | 3 | Gate — careful review needed |
| Step 7: Build with Claude | 2 | Core coding work |
| Step 8: Agent Validation Sandbox | 2 | Code quality, tests, compliance |
| Step 9: Stage deployment | 1–2 | Mostly execution; Sonnet for issue diagnosis |
| Step 10: Gate Stage→Prod | 3 | Mandatory — 6-condition gate, high stakes |
| Step 11: Production monitoring | 1 | Log reading, alert parsing |

---

## Cost Examples

| Session type | Without routing | With routing | Saving |
|---|---|---|---|
| 30-min debug session (Tier 1→2 split) | ~$0.45 (all Sonnet) | ~$0.18 | −60% |
| Spec Pack generation (Tier 2) | ~$0.12 (same) | ~$0.12 | — |
| Stage→Prod gate review (Tier 3) | ~$0.30 (same) | ~$0.30 | — |
| Full Builder day (mixed) | ~$6.00 (all Sonnet) | ~$3.20 | −47% |

---

## Behavior Instructions

When this skill is active, Claude must:

1. **State the selected model and tier before starting work** — never skip this.

2. **Re-evaluate mid-task** if scope expands. If a "quick fix" reveals a deeper issue,
   stop, announce the escalation, confirm with the user before switching models.

3. **Never silently use a heavier model** than the task requires.

4. **When ambiguous between two tiers**, pick the lower one and state the assumption.

5. **For composite tasks**, split by sub-task:
   - "Run tests AND fix failures" → tests = Tier 1, diagnose = Tier 2, fix = Tier 2

6. **For agentic sessions**, checkpoint model choice at each phase, not just at start.

---

## What NOT to do

- Do not default to Tier 2 (Sonnet) for tasks that are clearly Tier 1 execution (file reads, lint, grep)
- Do not use Tier 3 (Opus) for standard bug fixes, routine code writing, or test generation
- Do not skip announcing the model and tier before starting work — always state it
- Do not silently escalate to a heavier model mid-task — always announce and confirm with the user
- Do not apply Tier 3 to batch or pipeline jobs — use the `batch-detector` skill instead
- Do not use `/model` in Cowork or Chat — select the model from the UI model picker instead
- Do not assume the most expensive model produces better results for simple tasks

---

## Maintenance

Owner: Amit Rosen, AI Architecture, CIO division
Review cycle: Quarterly, or after any Anthropic pricing update
Source: https://github.com/Amitro1234/Model-Router-Claude-Code
Last updated: June 2026

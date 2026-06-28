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

**Keshet cost context:** Sonnet costs 10× more than Haiku per token. A team of 20 Builders
defaulting to Sonnet for every operation spends ~$130K/year on API. Consistent routing
reduces that to ~$85K — a saving of ~$45K without reducing quality.

---

## Routing Table

| Tier | Model | Cost (input/output per 1M) | Use When |
|---|---|---|---|
| **1 — Light** | `claude-haiku-4-5-20251001` | $0.80 / $4 | File reads, grep, lint, tests, bash, config parsing |
| **2 — Standard** | `claude-sonnet-4-6` | $3 / $15 | Write code, fix bugs, refactor, test writing, debug, code review |
| **3 — Heavy** | `claude-opus-4-7` | $15 / $75 | Architecture, security audit, greenfield design, threat modeling |

> **Default when uncertain:** Tier 2 — `claude-sonnet-4-6`

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
- Default pipeline model: `claude-haiku-4-5-20251001`
- Escalate to Sonnet only for code generation steps
- Combine with `batch-detector` skill for jobs processing >10 items

---

### Step 4 — Announce and set the model

Always state the routing decision before starting work:

> "Task: run lint and show failures → **Tier 1**, using `claude-haiku-4-5-20251001`."
> "Task: implement SharePoint connector module → **Tier 2**, using `claude-sonnet-4-6`."
> "Task: security audit of API gateway → **Tier 3**, using `claude-opus-4-7`."

Set the model via slash command if needed:
```
/model claude-haiku-4-5-20251001   # Tier 1
/model claude-sonnet-4-6           # Tier 2
/model claude-opus-4-7             # Tier 3
```

---

## Quick Reference

```
TIER 1 — claude-haiku-4-5-20251001   → read, run, find, lint, format, check, diff
TIER 2 — claude-sonnet-4-6           → write, fix, test, explain, refactor, debug, review, spec
TIER 3 — claude-opus-4-7             → design, architect, audit, investigate, gate-decision
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

## Escalation Examples

| User Request | Initial Tier | Escalated? | Reason |
|---|---|---|---|
| "Run pytest and show failures" | 1 | No | Pure execution |
| "Fix this TypeError in utils.py" | 2 | No | Standard bug fix |
| "Fix TypeError — turns out it's in the auth layer" | 2→3 | Yes | Touched auth, production-critical |
| "Add docstring to this function" | 1 | No | Trivial |
| "Design our SharePoint connector" | 3 | No | Greenfield |
| "Deploy to staging" | 1 | No | Execution |
| "Something's wrong in prod — logs show 500s" | 2→3 | Yes | Production issue, unclear root cause |

---

## Integration with Other Org Skills

Stack this skill with the rest of the Keshet Enterprise Skills:

```
1. model-router        → pick the cheapest capable model
2. context-hygiene     → trim context before sending
3. prompt-caching      → mark stable prefix for 90% discount
4. output-discipline   → govern response format and length
5. batch-detector      → route async jobs to Batch API (50% off)
6. agentic-loop-guard  → enforce checkpoints and hard stops
```

---

## Overriding Per-Session

Override anytime with a slash command:
```
/model claude-haiku-4-5-20251001
/model claude-sonnet-4-6
/model claude-opus-4-7
```

Or instruct explicitly: "Use Haiku for this task" / "Switch to Opus for the architecture section."

---

## Maintenance

Owner: Amit Rosen, AI Architecture, CIO division
Review cycle: Quarterly, or after any Anthropic pricing update
Source: https://github.com/Amitro1234/Model-Router-Claude-Code
Last updated: June 2026

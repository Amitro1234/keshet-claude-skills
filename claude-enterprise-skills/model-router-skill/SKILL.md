---
name: model-router-skill
description: >
  Use when starting any Claude Code task or session, when task scope changes
  mid-session, or when a Builder Flow gate (Steps 6, 8, 10) is being crossed.
---

# Model Router — Keshet Enterprise Edition

## Purpose

Select the appropriate Claude model **before starting any work**, based on task
complexity and required reasoning depth. Claude Code defaults to expensive models
even for trivial tasks (running `ruff`, reading a file, `git status`) — this wastes
budget on work a cheaper tier handles just as well.

Full classification rules, agentic/pipeline routing, the mid-session escalation
protocol, and cost examples live in `reference.md` — load it when applying the
router in detail. This file covers the tier table and the non-negotiable rules.

---

## Trigger Conditions

Activates **before every task**, without exception:
- A new Claude Code session starts
- The user asks Claude to perform any task (read, write, fix, run, review, design)
- Task scope changes significantly mid-session
- A Builder Flow gate is being crossed (Steps 6, 8, 10)
- An agentic session begins (tool calls will be made autonomously)

---

## Routing Table

> Model IDs and prices are **not** hardcoded here — `claude-enterprise-skills/_shared/model-tiers.md`
> is the single source of truth.

| Tier | Use When |
|---|---|
| **1 — Light** | File reads, grep, lint, tests, bash, config parsing |
| **2 — Standard** | Write code, fix bugs, refactor, test writing, debug, code review |
| **3 — Heavy** | Architecture, security audit, greenfield design, threat modeling, Stage→Prod gate |

**Default when uncertain:** Tier 2. See `reference.md` for the full classification
table, upgrade/downgrade modifiers, and agentic/pipeline routing rules.

---

Announce like:
```
Task: implement SharePoint connector module → Tier 2, using the Tier 2 model.
```

## Non-negotiable rules

1. **State the selected model and tier before starting work** — never skip this.
2. **Re-evaluate mid-task** if scope expands — stop, announce, confirm with the user before switching (see `reference.md` for the escalation protocol per platform).
3. **Never silently use a heavier model** than the task requires.
4. **When ambiguous between two tiers**, pick the lower one and state the assumption.

---

## What NOT to do

- Do not default to Tier 2 for tasks that are clearly Tier 1 execution
- Do not use Tier 3 for standard bug fixes or routine code writing
- Do not skip announcing the model and tier before starting work
- Do not silently escalate to a heavier model mid-task
- Do not apply Tier 3 to batch or pipeline jobs — use `batch-detector` instead
- Do not use `/model` in Cowork or Chat — select the model from the UI picker instead

---

## Maintenance

Owner: Amit Rosen, AI Architecture, CIO division
Review cycle: Quarterly, or after any Anthropic pricing update
Source: https://github.com/Amitro1234/Model-Router-Claude-Code
Last updated: July 2026

---
name: agentic-loop-guard
description: >
  Use when Claude is about to execute tool calls autonomously without per-step
  approval — multi-step tasks, loop constructs ("keep trying until..."), broad
  autonomy grants, or webhook/cron-triggered pipeline sessions.
---

# agentic-loop-guard — Org-Level Runaway Agent Prevention Skill

## Purpose

Agentic loops — agents repeatedly calling tools, spawning sub-tasks, or
retrying failed operations without a human checkpoint — are the single
largest source of unexpected API spend in Claude Enterprise deployments.

Limits here scale against the session's own opening declaration, not fixed
constants — a live audit (`enforcement/tests/behavioral-scenarios.md`,
Scenario 8) showed fixed limits hurt legitimate plan-driven multi-agent
work. Templates and the spend-cap table: `reference.md`.

---

## Trigger Conditions

Always active for any session where Claude executes tool calls autonomously.
Activate explicitly when: a task involves >5 sequential tool calls, a loop
construct is implied, the user grants broad autonomy ("just handle it"), or
a pipeline is event-triggered (webhook, cron, file watch).

---

## Step 1 — Declare the work mode and budget (the declaration IS the limit)

Before autonomous work starts, state:

```
Agent session starting. Mode: [interactive-solo | orchestrated | unattended]
Task: [description]
Estimated: ~[N] tool calls, ~[M] subagents, ~[T]K tokens
Checkpoints: [every 10 calls | at each structural gate: <name them>]
```

- **interactive-solo** — user watching, no structured process. Default.
- **orchestrated** — plan-driven multi-agent work with its own structural
  gates (per-task reviews, approval steps). The gates must actually exist
  and be named — "I'm being systematic" doesn't qualify.
- **unattended** — cron/webhook/user away. Strictest limits.

## Limits by mode

| Rule | interactive-solo | orchestrated | unattended |
|---|---|---|---|
| Checkpoint | every 10 calls: report + **wait** | at each structural gate: report, **don't block** (user can interrupt) | every 10 calls: hard stop |
| Tool-call ceiling | 50, then ask | 2× declared estimate, then stop and ask | 50 absolute |
| Subagents | 5 without asking | declared estimate; alert + ask at 2× declared | 0 without pre-approval |
| Token alert | 200K | at declared budget, again at each further 50% | 200K, then stop |
| Retries per failed op | 3 | 3 | 3 |
| Identical-call loop | halt at 3rd repeat | halt at 3rd repeat | halt at 3rd repeat |

An undeclared session gets interactive-solo limits. Exceeding a declared
estimate is a signal, not a crime — say so out loud and recalibrate;
silently blowing past it is the failure mode this skill exists to catch.

---

## What NOT to do

- Do not claim "orchestrated" mode without naming the actual structural gates
- Do not run `git push`, `kubectl apply`, or any write-to-production command inside an autonomous loop without a checkpoint
- Do not spawn subagents beyond the declared estimate without announcing it
- Do not catch-and-retry silently — always surface failures to the user
- Do not use `while True` or equivalent without a defined exit condition checked every iteration
- Do not treat a passed token-alert threshold as "already alerted, keep going" — each threshold gets its own announcement

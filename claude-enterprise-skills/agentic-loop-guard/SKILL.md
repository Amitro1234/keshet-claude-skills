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
This skill enforces hard stops, checkpoints, and cost ceilings. Message
templates and the spend-cap table live in `reference.md`.

---

## Trigger Conditions

Always active for any session where Claude executes tool calls autonomously.
Activate explicitly when: a task involves >5 sequential tool calls, a loop
construct is implied, the user grants broad autonomy ("just handle it"), or
a pipeline is event-triggered (webhook, cron, file watch).

---

## Hard Limits

Non-negotiable — do not exceed without explicit user override.

| Limit | Default | Rationale |
|---|---|---|
| Max consecutive tool calls without checkpoint | 10 | Matches `output-discipline` |
| Max total tool calls per session | 50 | Budget ceiling |
| Max retries on a single failed operation | 3 | Prevents retry storms |
| Max sub-agents spawned per session | 5 | Prevents exponential fan-out |
| Max tokens before cost alert | 200K | ~$0.60 at Sonnet rates — see `_shared/model-tiers.md` |

## Required Actions

1. **Session opening** — state the task, estimated steps, and the hard-stop/checkpoint limits:
   ```
   Agent session starting. Task: [description]. Hard stop: 50 tool calls. Checkpoint: every 10.
   ```
2. **Checkpoint every 10 tool calls** — summarize what's done, next step, cost so far; wait for approval.
3. **Retry guard** — max 3 attempts on a failed operation, then stop and ask.
4. **Loop detection** — identical tool call + params 3 times in a session → halt immediately.
5. **Token budget alert** — surface a cost alert on crossing 200K tokens in one session.

See `reference.md` for the exact message format for each.

---

## What NOT to do

- Do not run `git push`, `kubectl apply`, or any write-to-production command inside an autonomous loop without a checkpoint
- Do not spawn sub-agents without counting them toward the session's tool call budget
- Do not catch-and-retry silently — always surface failures to the user
- Do not use `while True` or equivalent without a defined exit condition checked every iteration
- Do not continue past the 50-tool-call hard stop even if "almost done"

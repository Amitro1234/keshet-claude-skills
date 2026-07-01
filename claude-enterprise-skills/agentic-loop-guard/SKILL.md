---
name: agentic-loop-guard
description: >
  Org-level runaway agent prevention skill — always active for any session where
  Claude executes tool calls autonomously. Enforces 10-call checkpoints, 50-call
  hard stop, 3-retry limit, loop detection, and 200K-token cost alerts. Triggers on:
  any autonomous multi-step task, any loop construct, broad autonomy grants
  ("just handle it"), pipeline or webhook-triggered sessions, or tasks with >5
  sequential tool calls.
---

# agentic-loop-guard — Org-Level Runaway Agent Prevention Skill

## Purpose

Agentic loops — AI agents repeatedly calling tools, spawning sub-tasks, or retrying
failed operations without a human checkpoint — are the single largest source of
unexpected API spend in Claude Enterprise deployments.

This skill enforces hard stops, checkpoint intervals, and cost ceilings to prevent
any single agentic session from consuming disproportionate budget.

Applies to: all Claude Code users running multi-step agent workflows, all automated
pipelines, all MCP-connected agents.

> **Platform compatibility:**
> - Claude Code CLI: ✅ Full support — tool call counting is precise; hard stops and checkpoints apply exactly
> - Cowork: ✅ Applies when using agentic tasks or MCP tools; checkpoint and retry rules apply
> - Claude.ai Chat: ⚠️ Partial — fully autonomous multi-step loops are less common; retry guard and cost awareness still apply when Claude is performing multi-step reasoning

---

## Trigger Conditions

This skill is **always active** for any session where Claude will execute tool calls
autonomously (i.e., without the user approving each step).

Activate explicitly when:
- A task involves more than 5 sequential tool calls
- A loop construct is implied (e.g., "keep trying until it works", "process all files")
- The user grants broad autonomy ("just handle it", "do it automatically")
- A pipeline is triggered by an event (webhook, cron, file watch)

---

## Hard Limits

These limits are non-negotiable. Do not exceed them without explicit user override.

| Limit | Default | Rationale |
|---|---|---|
| Max consecutive tool calls without checkpoint | 10 | Matches `output-discipline` checkpoint rule |
| Max total tool calls per session | 50 | Budget ceiling for an agentic session |
| Max retries on a single failed operation | 3 | Prevents retry storms |
| Max sub-agents spawned per session | 5 | Prevents exponential fan-out |
| Max tokens consumed before cost alert | 200K | ~$0.60 at current Sonnet (Tier 2) rates — see `claude-enterprise-skills/_shared/model-tiers.md` — warrants attention |

---

## Required Actions

### Step 1: Session opening declaration

At the start of any agentic session, state:

```
Agent session starting.
Task: [description]
Estimated steps: ~[N] tool calls
Hard stop: 50 tool calls or user interrupt
Checkpoint: every 10 tool calls
```

### Step 2: Checkpoint every 10 tool calls

After every 10 consecutive tool calls, stop and produce:

```
=== Agent Checkpoint (tool calls: [N]/50) ===
Completed: [bullet list of what was done]
Next step: [single next action]
Estimated remaining: ~[M] more tool calls
Cost so far: ~[X]K tokens

Awaiting approval to continue. Type "continue" or provide new instructions.
```

Do not proceed until the user responds.

### Step 3: Retry guard

When a tool call fails, follow this protocol:

```
Attempt [1/3] failed: [error]
Retrying with [adjustment]...

[If attempt 3 fails:]
Operation failed after 3 attempts: [operation name]
Error: [last error message]
Stopping. Do not want to retry indefinitely and consume budget.
Please review and advise.
```

Never retry more than 3 times without a human decision.

### Step 4: Loop detection

If the same tool call is being made with the same parameters for the 3rd time
in a session, halt immediately:

```
LOOP DETECTED: [tool name] called with identical parameters [N] times.
Last result: [result]
This looks like a stuck loop. Stopping to prevent runaway spend.
```

### Step 5: Token budget alert

Monitor estimated token consumption. When crossing 200K tokens in a single session:

```
COST ALERT: This session has consumed ~200K tokens (~$0.60 at Sonnet rates — see claude-enterprise-skills/_shared/model-tiers.md for current pricing).
Task completion estimate: [X]% done.
Projected total: ~[Y]K tokens (~$[Z]).

Recommend: confirm this spend is expected before continuing.
Type "continue" to proceed, or "stop" to end the session.
```

---

## Spend Cap Reference (Keshet)

Group-level caps as configured in Claude Enterprise Admin Panel:

| Group | Monthly cap | Per-session alert threshold |
|---|---|---|
| Developers (Builder) | $150/user | 200K tokens |
| Business users (Safe Use) | $30/user | 50K tokens |
| Automation accounts | $200/account | 500K tokens |

If a session is projected to exceed the per-session alert threshold,
always surface the cost alert (Step 5) before continuing.

---

## What NOT to do

- Do not run `git push`, `kubectl apply`, or any write-to-production command inside
  an autonomous loop without a checkpoint
- Do not spawn sub-agents without counting them toward the session's tool call budget
- Do not catch-and-retry silently — always surface failures to the user
- Do not use `while True` or equivalent patterns without a defined exit condition
  checked after every iteration
- Do not continue after the 50-tool-call hard stop even if the task is "almost done"

---

## Cost Rationale

An unguarded agentic loop on a coding task can consume:
- 5M tokens in 20 minutes (tool call responses + code context)
- ~$15–25 on Sonnet (Tier 2) for a single session gone wrong — see `claude-enterprise-skills/_shared/model-tiers.md` for current Tier 2 pricing

A team of 20 Builders, one runaway session each per month:
- 20 × $20 = $400/month in preventable waste
- Annual cost: ~$4,800 — more than the seat cost for several users

The checkpoint and loop-detection rules prevent this at near-zero overhead.

# Agentic Loop Guard — Reference

Message templates, spend-cap table, and cost rationale for
`agentic-loop-guard/SKILL.md`. Load this file when producing the actual
checkpoint/alert/retry messages — the core SKILL.md states the limits and
required actions on their own.

---

## Message templates

### Session opening declaration (mode-based, per SKILL.md Step 1)

```
Agent session starting. Mode: [interactive-solo | orchestrated | unattended]
Task: [description]
Estimated: ~[N] tool calls, ~[M] subagents, ~[T]K tokens
Checkpoints: [every 10 calls | at each structural gate: <name them>]
Hard stop: [50 calls | 2x declared estimate] or user interrupt
```

For orchestrated mode, the named structural gates replace the fixed
10-call cadence — e.g. "checkpoint after each task's review completes."
A checkpoint in orchestrated mode reports and continues (the user can
interrupt); it does not block awaiting approval.

### Checkpoint (solo: every 10 tool calls, blocking / orchestrated: per gate, non-blocking)

```
=== Agent Checkpoint (tool calls: [N]/[ceiling]) ===
Completed: [bullet list of what was done]
Next step: [single next action]
Estimated remaining: ~[M] more tool calls
Cost so far: ~[X]K tokens

Awaiting approval to continue. Type "continue" or provide new instructions.
```

Do not proceed until the user responds.

### Retry guard

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

### Loop detection

If the same tool call is made with the same parameters for the 3rd time in a
session, halt immediately:

```
LOOP DETECTED: [tool name] called with identical parameters [N] times.
Last result: [result]
This looks like a stuck loop. Stopping to prevent runaway spend.
```

### Token budget alert (crossing 200K tokens)

```
COST ALERT: This session has consumed ~200K tokens (~$0.60 at Sonnet rates —
see claude-enterprise-skills/_shared/model-tiers.md for current pricing).
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

If a session is projected to exceed the per-session alert threshold, always
surface the token budget alert before continuing.

---

## Cost Rationale

An unguarded agentic loop on a coding task can consume:
- 5M tokens in 20 minutes (tool call responses + code context)
- ~$15–25 on Sonnet (Tier 2) for a single session gone wrong — see `_shared/model-tiers.md` for current pricing

A team of 20 Builders, one runaway session each per month:
- 20 × $20 = $400/month in preventable waste
- Annual cost: ~$4,800 — more than the seat cost for several users

The checkpoint and loop-detection rules prevent this at near-zero overhead.

## Platform compatibility

- Claude Code CLI: full support — tool call counting is precise
- Cowork: applies when using agentic tasks or MCP tools
- Claude.ai Chat: partial — fully autonomous multi-step loops are less common; retry guard and cost awareness still apply during multi-step reasoning

# Keshet — Model Tier Reference (single source of truth)

> **Last verified:** 2026-07-01 · **Next review due:** 2026-10-01 (quarterly)
> **Owner:** AI Architecture (Amit Rosen)
>
> This is the ONLY place model IDs and pricing should be hardcoded in this repo.
> Every skill that needs a model ID or price should link here instead of repeating
> the value inline. When a new Claude model ships, update this file once -- do not
> hunt through every skill file.

## Current pinned models (verify against https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions before updating)

| Tier | Model ID | Input $/1M | Output $/1M | Cache write (5-min / 1-hr) | Cache read |
|---|---|---|---|---|---|
| 1 — Light | `claude-haiku-4-5-20251001` | $1.00 | $5.00 | $1.25 / $2.00 | $0.10 |
| 2 — Standard | `claude-sonnet-5` | $3.00 | $15.00 | $3.75 / $6.00 | $0.30 |
| 3 — Heavy | `claude-opus-4-8` | $5.00 | $25.00 | $6.25 / $10.00 | $0.50 |

Note: Anthropic does not offer "-latest" style auto-updating aliases -- every model ID
above is a pinned snapshot that will NOT silently change. That's why this file needs a
human to update it on a cadence, not code that updates itself.

## Update procedure (quarterly, or whenever Anthropic ships a new model generation)

1. Check https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions for the current model lineup.
2. Update the table above with new model IDs / prices.
3. Update "Last verified" and "Next review due" dates.
4. Grep the repo for the OLD model ID strings you just replaced (e.g. `grep -rn "claude-sonnet-5" .` before you change it, to see every place that will need the same update if you ever move away from linking to this file) to make sure nothing still hardcodes the old value outside this file.
5. No other file in this repo should need editing for a routine model-version bump -- if you find one that does, that file has a hardcoded value that should be converted to a link to this file instead (see "How skills should reference this file" below).

## How skills should reference this file

Instead of writing `claude-sonnet-4-6` (or any other specific ID) inline, a skill should say something like:

> Tier 2 model — see `claude-enterprise-skills/_shared/model-tiers.md` for the current pinned model ID and price.

This means a routine model update touches exactly one file (this one) instead of every skill that mentions a model.

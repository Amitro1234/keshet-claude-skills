---
name: batch-detector
description: >
  Org-level Batch API routing skill — identifies tasks eligible for the 50% Batch API
  discount and routes them appropriately. Triggers on: any bulk operation over N>10
  items, scheduled/nightly jobs, CI/CD pipeline steps, evaluation runs, or any task
  where the user can wait up to 24 hours for results. Always flag before running
  synchronous API calls on batch-eligible workloads.
---

# batch-detector — Org-Level Batch API Routing Skill

## Purpose

Anthropic's Batch API provides a **50% discount** on all token costs for tasks that
do not require real-time responses. This skill identifies batch-eligible tasks and
prevents them from being processed as synchronous (full-price) requests.

Target users: developers and data engineers building pipelines, automations, and
bulk-processing workflows.

> **Platform compatibility:**
> - Claude Code CLI (API/SDK development): ✅ Full support — target audience is developers building pipelines and automations using the Anthropic Python/TypeScript SDK
> - Interactive Claude Code sessions: ⚠️ Use only when the Builder is writing pipeline code; not applicable to interactive coding sessions
> - Cowork: ❌ Not applicable — Cowork users do not build Batch API jobs
> - Claude.ai Chat: ❌ Not applicable

---

## Trigger Conditions

Activate this skill when the user's task involves ANY of the following:

1. **Bulk operations** — processing the same prompt over a list of inputs
   - Translating N documents
   - Classifying N tickets / records / events
   - Summarizing N articles or reports
   - Extracting structured data from N files
   - Evaluating N model outputs (LLM-as-judge)

2. **Scheduled / nightly jobs** — tasks that run on a cron or pipeline trigger,
   not in response to a live user action

3. **CI/CD pipeline steps** — code review, security scan, or test generation
   triggered by a git push or PR event (not a developer sitting at a terminal)

4. **Evaluation runs** — running a test suite against an LLM, benchmarking prompts,
   or comparing model outputs at scale

The rule of thumb: **if N > 10 and the user can wait up to 24 hours, it is batch-eligible.**

---

## Required Actions

### Step 1: Flag the task

When a batch-eligible task is detected, immediately output:

```
BATCH_CANDIDATE detected.
Reason: [why this qualifies — e.g., "processing 150 records with the same classification prompt"]
Estimated saving: 50% on API costs for this job.

Options:
  A) Run now via synchronous API (full price, results immediate)
  B) Route to Batch API (50% discount, results within 24h)

Recommendation: B — unless you need results in under 1 hour.
```

Wait for user confirmation before proceeding.

### Step 2: If user chooses Batch API

Structure the job correctly:

```python
# Batch API request format (Anthropic)
requests = [
    {
        "custom_id": f"item-{i}",
        "params": {
            "model": "claude-haiku-4-5-20251001",  # Tier 1 — see claude-enterprise-skills/_shared/model-tiers.md for the current pinned ID
            "max_tokens": 500,
            "messages": [{"role": "user", "content": prompt_for_item(item)}]
        }
    }
    for i, item in enumerate(items)
]
```

Key rules for batch jobs:
- Default to the Tier 1 model (see `claude-enterprise-skills/_shared/model-tiers.md` for the current pinned ID) unless the task requires reasoning (use Sonnet then)
- Set `max_tokens` as low as the task allows — do not use 4096 for a classification that needs 50 tokens
- Use `custom_id` that maps back to your source data for easy join on results

### Step 3: Estimate the saving

Before submitting, output a cost estimate:

```
Batch job estimate:
  Items: [N]
  Model: [Tier 1 — see claude-enterprise-skills/_shared/model-tiers.md]
  Est. input tokens per item: ~[X]
  Est. output tokens per item: ~[Y]
  Total tokens: ~[N × (X + Y)]
  Synchronous cost: ~$[A]
  Batch cost (50% off): ~$[B]
  Saving: ~$[A - B]
```

---

## Model selection for batch jobs

> Model IDs intentionally omitted below — `claude-enterprise-skills/_shared/model-tiers.md`
> is the source of truth for the current pinned ID per tier.

| Task type | Model |
|---|---|
| Classification, tagging, routing | Tier 1 |
| Extraction, summarization, translation | Tier 1 (upgrade to Tier 2 if output quality is insufficient) |
| Code review, security scan (CI/CD) | Tier 2 |
| Complex reasoning, multi-step analysis | Tier 2 |

## What NOT to do

- Do not route batch-eligible jobs through the synchronous API without flagging it first
- Do not use the Tier 3 model (see `_shared/model-tiers.md`) for batch jobs — never justified at scale
- Do not set `max_tokens` to the model maximum for jobs that need short outputs
- Do not submit a batch job without a `custom_id` strategy — results cannot be joined back to source data
- Do not run batch jobs on tasks that require real-time human responses
- Do not skip the cost estimate before submitting — always show projected saving first

---

## Cost Rationale

A pipeline classifying 500 support tickets per day (~300 input + 50 output tokens per
ticket → ~150K input / 25K output tokens/day). This example has two independent
savings levers — keep them separate, since only the second one is this skill's job:

1. **Model tier (a `model-router` decision):** ticket classification is Tier 1 (no
   reasoning needed), so it should never run on Sonnet in the first place.
   - Sonnet, synchronous: ~$0.83/day → ~$300/year
   - Haiku, synchronous: ~$0.28/day → ~$100/year
   - Saving from routing to the right model tier: ~$200/year — this is a
     `model-router` win, not a batch discount.

2. **Batch API (this skill's decision):** ticket classification can wait up to 24h,
   so the Haiku job qualifies for the flat 50% Batch API discount.
   - Haiku, Batch API (50% off the Haiku sync cost): ~$0.14/day → ~$50/year
   - Saving from batching alone: ~$50/year — exactly 50% off the Haiku sync cost above.

Combined (Sonnet-sync baseline → Haiku-batch): ~$300/year → ~$50/year. Do not
attribute the full combined saving to "the 50% Batch API discount" — only the
second step (Haiku sync → Haiku batch) is the 50% discount; the first step is a
separate model-downgrade decision.

At scale, batch routing of automations and pipelines can save thousands of dollars
per year on a 70-person team running multiple data workflows.

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
            "model": "claude-haiku-4-5-20251001",  # Use cheapest model that fits the task
            "max_tokens": 500,
            "messages": [{"role": "user", "content": prompt_for_item(item)}]
        }
    }
    for i, item in enumerate(items)
]
```

Key rules for batch jobs:
- Default to `claude-haiku-4-5-20251001` unless the task requires reasoning (use Sonnet then)
- Set `max_tokens` as low as the task allows — do not use 4096 for a classification that needs 50 tokens
- Use `custom_id` that maps back to your source data for easy join on results

### Step 3: Estimate the saving

Before submitting, output a cost estimate:

```
Batch job estimate:
  Items: [N]
  Model: claude-haiku-4-5-20251001
  Est. input tokens per item: ~[X]
  Est. output tokens per item: ~[Y]
  Total tokens: ~[N × (X + Y)]
  Synchronous cost: ~$[A]
  Batch cost (50% off): ~$[B]
  Saving: ~$[A - B]
```

---

## Model selection for batch jobs

| Task type | Model |
|---|---|
| Classification, tagging, routing | `claude-haiku-4-5-20251001` |
| Extraction, summarization, translation | `cla

## What NOT to do

- Do not route batch-eligible jobs through the synchronous API without flagging it first
- Do not use `claude-opus-4-8` for batch jobs — never justified at scale
- Do not set `max_tokens` to the model maximum for jobs that need short outputs
- Do not submit a batch job without a `custom_id` strategy — results cannot be joined back to source data
- Do not run batch jobs on tasks that require real-time human responses
- Do not skip the cost estimate before submitting — always show projected saving first

---

## Cost Rationale

A pipeline classifying 500 support tickets per day:
- Synchronous (Sonnet 4.6): ~$0.50/day → $180/year
- Batch (Haiku 4.5, 50% off): ~$0.015/day → $5.50/year

At scale, batch routing of automations and pipelines can save thousands of dollars
per year on a 70-person team running multiple data workflows.

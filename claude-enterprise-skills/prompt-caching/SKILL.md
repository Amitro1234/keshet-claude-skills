---
name: prompt-caching
description: >
  Org-level prompt caching skill — activates whenever stable content (CLAUDE.md,
  Spec Pack, DB schema, shared docs) will be passed to the model more than once.
  Provides 90% discount on cache hits ($0.30/M vs $3.00/M on Sonnet). Triggers on:
  session start when context includes a large system prompt, Spec Pack reference,
  shared schema, or SDK documentation exceeding 1,024 tokens.
---

# prompt-caching — Org-Level Prompt Cache Skill

## Purpose

Anthropic's prompt caching provides a **90% discount** on repeated input tokens
(cache hits cost $0.30/M vs. $3.00/M for Sonnet 4.6).
This skill ensures every session that can benefit from caching is structured correctly.

Applies to: all Claude Code users, all API integrations, all agentic workflows.

> **Platform compatibility:**
> - Claude Code CLI (API integrations / pipelines): ✅ Full support
> - Interactive Claude Code sessions: ⚠️ Caching is managed by Claude Code automatically — no manual setup needed
> - Cowork: ❌ Not applicable — users do not control API parameters
> - Claude.ai Chat: ❌ Not applicable

---

## Trigger Conditions

Activate this skill when ALL of the following are true:
- The session includes large static content (system prompt, Spec Pack, schema, SDK docs)
- That content exceeds **1,024 tokens**
- The same content will be sent to the model more than once (across turns or requests)

**This skill is for API/SDK integrations only.**
It does not apply to interactive Claude Code sessions, Cowork, or Claude.ai Chat —
those environments manage caching automatically. Target audience: developers building
pipelines, automations, or multi-turn API applications using the Anthropic SDK.

---

## When Caching Applies

Caching is available whenever the same prefix content appears across multiple requests.
The minimum cacheable block is **1,024 tokens**.

High-value cache candidates:

| Candidate | Typical size | Expected saving |
|---|---|---|
| Organizational CLAUDE.md / system prompt | 2K–10K tokens | Very high |
| Large codebase context passed repeatedly | 10K–100K tokens | Very high |
| Spec Pack (PRD, Technical Spec, Acceptance Criteria) | 5K–20K tokens | High |
| Shared library/SDK documentation | 10K–50K tokens | High |
| DB schema passed to multiple queries | 2K–15K tokens | Medium |

---

## Required Actions

### Step 1: Identify the cache candidate

Before starting any session that reads large static context, identify whether that
context will be reused across turns or requests.

Ask yourself:
- Does the system prompt / CLAUDE.md exceed 1,024 tokens? → Cache it.
- Is there a shared document (Spec, schema, SDK docs) that will be referenced repeatedly? → Cache it.
- Is this a one-off query with no repeated context? → Caching does not help.

### Step 2: Declare the cache block

When building API requests programmatically, mark the stable prefix with
`"cache_control": {"type": "ephemeral"}`:

```python
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": large_static_context,          # the stable part
                "cache_control": {"type": "ephemeral"} # mark for caching
            },
            {
                "type": "text",
                "text": dynamic_query                  # the changing part — not cached
            }
        ]
    }
]
```

Key rule: **the cached content must always come before the dynamic content**.
Changing the order breaks the cache.

### Step 3: Estimate the saving

Before enabling caching on a workflow, output:

```
Cache estimate:
  Static context: ~[X]K tokens
  Requests per day: ~[N]
  Cache write cost (first hit): [X] × $3.75/M = $[A]   ← 25% surcharge on write
  Cache read cost (subsequent hits): [X] × $0.30/M = $[B]
  Without caching (all N requests): [X × N] × $3.00/M = $[C]
  With caching (1 write + N-1 reads): $[A] + ([N-1] × $[B]) = $[D]
  Daily saving: ~$[C - D]
  Monthly saving (22 days): ~$[E]
```

### Step 4: Verify cache hits

In Claude Code, cache behavior is visible in API response metadata:
```json
"usage": {
  "input_tokens": 1200,
  "cache_creation_input_tokens": 8500,   ← cache written this request
  "cache_read_input_tokens": 0
}
```
On subsequent requests with the same prefix:
```json
"usage": {
  "input_tokens": 1200,
  "cache_creation_input_tokens": 0,
  "cache_read_input_tokens": 8500        ← cache hit — 90% cheaper
}
```

If `cache_read_input_tokens` is 0 on the second request, the prefix changed —
debug by checking whether the cached block is truly identical across requests.

---

## Cache lifetime

Ephemeral cache entries expire after **5 minutes of inactivity**.
For long-running sessions, ensure at least one request per 5 minutes
touches the cached prefix to keep it warm.

For nightly batch jobs, structure the job to write cache on the first item
and reuse across all subsequent items within the same run.

---

## Cost Rationale

Sonnet 4.6 pricing (per 1M tokens):
- Input (no cache): $3.00
- Cache write: $3.75 (25% premium — amortized after 2+ reads)
- Cache read: $0.30 (90% discount)

Scenario: 50K-token Spec Pack, read 200 times in one day by a Builder team:
- Without caching: 200 × 50K × $3.00/M = **$30.00/day**
- With caching: (1 × 50K × $3.75/M) + (199 × 50K × $0.30/M) = $0.19 + $2.99 = **$3.18/day**
- Daily saving: **$26.82** → Monthly saving: **~$590**

---

## What NOT to do

- Do not mark dynamic content (user queries, timestamps, per-request IDs) as cached
- Do not place the cache block after the dynamic content — cache invalidates immediately
- Do not cache content shorter than 1,024 tokens — no discount applies
- Do not assume caching is automatic — it must be explicitly declared in the API call
- Do not cache sensitive PII or credentials inside shared system prompts

---

## Integration with other org skills

Cache the organizational CLAUDE.md and Spec Pack at the start of every Builder session.
This stacks with `context-hygiene` (trimmed context = cheaper cache writes) and
`batch-detector` (batch jobs benefit most from caching large shared prompts).

Recommended session startup order:
```
1. model-router       → pick the cheapest capable model
2. context-hygiene    → trim before sending
3. prompt-caching     → mark stable prefix for caching
4. output-discipline  → govern response format
5. batch-detector     → flag if the whole job should be async
```

# Output Discipline — Reference

Examples and cost rationale for `output-discipline/SKILL.md`. Load this file
when you need the worked examples — the core SKILL.md states the 5 rules and
the agentic checkpoint format on their own.

---

## Rule 1: Diffs over full files — example

Bad output:
```python
# [entire 300-line file rewritten because 3 lines changed]
```

Good output:
```python
# ... (line 47)
def process_event(event: dict) -> None:
-    logger.info(event)          # changed: added structured logging
+    logger.info("event received", extra={"event_id": event.get("id")})
# ... (line 52)
```

**Exception:** the file is new (does not exist yet), or the user explicitly asks for the full file.

## Rule 2: No boilerplate comments — example

```python
# Bad — never write these:
# Import libraries
import pandas as pd

# Define main function
def main():
    pass

# Call main
main()
```

## Rule 3: Responses proportional to the question

| Question type | Max response length |
|---|---|
| Yes/No question | 1–3 sentences |
| Factual lookup | 1 paragraph |
| Code fix (single bug) | The fix + 1 sentence explanation |
| Architecture question | Up to 5 bullet points or 3 paragraphs |
| Full design document | Unlimited, but only when explicitly requested |

Do not pad responses with: "Great question!", summaries of what you just said,
"Let me know if you need anything else", or restatements of the user's request.

## Rule 4: Prefer references over repetition — example

Good: "Update the `process_event` function you wrote earlier to also log the timestamp."
Bad: [Repeat the entire function before suggesting changes]

## Rule 5: No unsolicited alternatives

Do not output 3 alternative implementations when 1 was requested.
Do not add "you could also consider..." unless the user asked for options.

---

## Cost Rationale

Output tokens cost **5× more** than input tokens (see `claude-enterprise-skills/_shared/model-tiers.md`
for current per-tier input/output pricing). Every unnecessary output token —
padding, full-file rewrites, unsolicited alternatives — is real money at team scale.

A team of 20 Builders, each generating 20% fewer output tokens through discipline:
- Baseline output spend: ~$6/day × 20 = $120/day → $30,000/year
- After output discipline: ~$96/day → $24,000/year
- Saving: ~$6,000/year from formatting rules alone — zero reduction in quality

## Platform compatibility

- Claude Code CLI: full support
- Cowork: full support
- Claude.ai Chat: full support

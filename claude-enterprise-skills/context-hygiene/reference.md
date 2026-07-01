# Context Hygiene — Reference

`.claudeignore` exclusion list, history-compression format, and cost rationale
for `context-hygiene/SKILL.md`.

---

## Default `.claudeignore` exclusions

Never include the following in any context window without explicit user instruction:

```
node_modules/
dist/
build/
.next/
.nuxt/
*.lock           (package-lock.json, yarn.lock, pnpm-lock.yaml)
*.min.js
*.min.css
*.map
*.bin
*.wasm
*.png *.jpg *.jpeg *.gif *.svg *.ico
*.mp4 *.mov *.avi
coverage/
__pycache__/
*.pyc
.env*            (never include env files in context)
```

If the project does not have a `.claudeignore`, suggest creating one at the end of the session.

## Compressed history format

When conversation history is compressed (context >40K tokens), keep verbatim
only the last 3 turns; compress earlier turns into:

```
=== Compressed History ===
[TASK] What was being done
[DECISIONS] Key decisions made
[FILES_CHANGED] path/to/file — what changed
[OPEN_ITEMS] What still needs to be done
=========================
```

Announce when compressing: "Compressing conversation history to stay within token budget."

## Cost Rationale

| Scenario | Estimated saving |
|---|---|
| .claudeignore + file limits | −15% to −25% on API costs |
| History compression on long sessions | Additional −10% to −15% |

Source: Anthropic Enterprise Pricing 2026 · internal FinOps analysis.

## Platform compatibility

- Claude Code CLI: full support — `.claudeignore` scoping, per-file limits, history compression all apply
- Cowork: applies via a connected folder for `.claudeignore`; history compression works in-conversation
- Claude.ai Chat: partial — file exclusions and per-file limits are advisory; paste only relevant sections and compress history manually

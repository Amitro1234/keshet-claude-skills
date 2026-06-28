---
name: context-hygiene
description: >
  Org-level token budget skill for Keshet Builders. Enforces context discipline to
  prevent token bloat and reduce API costs. ALWAYS activate when a session exceeds 20
  minutes, more than 4 files are in context, or a full codebase review is requested.
  Triggers on: long sessions, multi-file tasks, codebase analysis, or any new task
  following a long prior conversation.
---

# context-hygiene — Org-Level Token Budget Skill

## Purpose

Enforce context discipline across the organization to prevent token bloat.
This skill runs **before any long session or multi-file task** and must not be skipped.

> **Platform compatibility:**
> - Claude Code CLI: ✅ Full support — `.claudeignore` file scoping, per-file limits, and history compression all apply
> - Cowork: ✅ Applies — use a connected folder for `.claudeignore`; context discipline and history compression work in-conversation
> - Claude.ai Chat: ⚠️ Partial — steps 2 and 3 (file exclusions, per-file limits) are advisory; paste only relevant code sections and compress history manually

---

## Trigger Conditions

Activate this skill when ANY of the following is true:
- A session has been running for more than 20 minutes
- More than 4 files are about to be passed to the model
- The user asks to "analyze", "review", or "work on" an entire codebase or folder
- A new task begins after a long prior conversation

---

## Required Actions (in order)

### 1. Declare the estimated context size

Before sending any large prompt, estimate and state:

```
Context estimate: ~[X]K tokens (files: [N], history: [M] turns)
```

If the estimate exceeds **60K tokens**, stop and proceed to step 2.

### 2. Apply .claudeignore exclusions

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

### 3. Enforce per-file limits

- Maximum **200 lines** from any single file unless the user explicitly asks for more
- For config files (JSON, YAML, TOML): include only the relevant section, not the full file
- For large SQL schemas: include only the tables relevant to the current task

### 4. Compress conversation history when context exceeds 40K tokens

When the running context grows large, summarize older turns into a structured log.
Keep verbatim: the last 3 conversation turns only.
Compress earlier turns into this format:

```
=== Compressed History ===
[TASK] What was being done
[DECISIONS] Key decisions made
[FILES_CHANGED] path/to/file — what changed
[OPEN_ITEMS] What still needs to be done
=========================
```

Announce when compressing: "Compressing conversation history to stay within token budget."

---

## Cost Rationale

| Scenario | Estimated saving |
|---|---|
| .claudeignore + file limits | −15% to −25% on API costs |
| History compression on long sessions | Additional −10% to −15% |

Source: Anthropic Enterprise Pricing 2026 · internal FinOps analysis.

---

## What NOT to do

- Never pass `node_modules` to the model
- Never include unchanged files "for context" — reference them by name only
- Never repeat the user's full message back before answering
- Never include binary or media files in context
- Do not maintain verbatim history beyond the last 3 turns without compression

---

## End-of-session suggestion

If the session was long (>30 min) or touched many files, offer:

> "This session used an estimated [X]K tokens. Want me to generate a `.claudeignore` for this project to reduce costs on future sessions?"

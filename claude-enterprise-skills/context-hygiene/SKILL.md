---
name: context-hygiene
description: >
  Use when a session runs long, more than 4 files are about to enter context,
  a full codebase or folder review is requested, or a new task begins after a
  long prior conversation.
---

# context-hygiene — Org-Level Token Budget Skill

## Purpose

Enforce context discipline to prevent token bloat and reduce API costs. Runs
before any long session or multi-file task and must not be skipped. The
`.claudeignore` exclusion list, history-compression format, and cost rationale
live in `reference.md`.

---

## Trigger Conditions

Activate when ANY of: session running >20 minutes, >4 files about to enter
context, the user asks to analyze/review/work on an entire codebase or
folder, or a new task begins after a long prior conversation.

---

## Required Actions (in order)

1. **Declare estimated context size**:
   ```
   Context estimate: ~[X]K tokens (files: [N], history: [M] turns)
   ```
   If it exceeds 60K tokens, proceed to step 2.
2. **Apply `.claudeignore` exclusions** — never include `node_modules`, build output, lockfiles, binaries/media, or `.env*` without explicit instruction. See `reference.md` for the full list.
3. **Enforce per-file limits** — max 200 lines from any single file unless asked for more; include only the relevant section of large configs/schemas.
4. **Compress history when context exceeds 40K tokens** — keep the last 3 turns verbatim, compress the rest into the structured format in `reference.md`.

---

## What NOT to do

- Never pass `node_modules` to the model
- Never include unchanged files "for context" — reference them by name only
- Never repeat the user's full message back before answering
- Never include binary or media files in context
- Do not maintain verbatim history beyond the last 3 turns without compression

---

## End-of-session suggestion

If the session was long (>30 min) or touched many files, offer to generate a
`.claudeignore` for the project to reduce costs on future sessions.

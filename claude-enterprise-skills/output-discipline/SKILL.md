---
name: output-discipline
description: >
  Use whenever a file is being modified, a response is being composed, or an
  autonomous agent session is running — applies to every Keshet Claude Code,
  Cowork, or Chat session.
---

# output-discipline — Org-Level Output Token Reduction Skill

## Purpose

Output tokens cost 5x more than input tokens in the Anthropic pricing model.
This skill enforces output discipline to eliminate waste without reducing
quality. Worked examples and cost math live in `reference.md`.

---

## Trigger Conditions

Always active — not optional. Applies to any file modification, any response
composition, any autonomous agent session, any code change/review/explanation.

---

## Core Rules

1. **Diffs over full files** — output only changed blocks with ±5 lines of context, never a full-file rewrite, unless the file is new or the user asks for the full file.
2. **No boilerplate comments** — never describe what code obviously does.
3. **Responses proportional to the question** — a yes/no gets 1–3 sentences, not a report. See `reference.md` for the length table.
4. **Reference, don't repeat** — point back to code/text already shown this session instead of restating it.
5. **No unsolicited alternatives** — one implementation unless alternatives were requested.

## Agentic session limits

- After every **10 consecutive tool calls**, stop and produce a checkpoint:
  ```
  === Checkpoint (10 tool calls used) ===
  Done: [list]
  Next: [next step]
  Awaiting approval to continue.
  ```
- Do not `git commit` or `git push` without explicit user confirmation.
- Do not create files the user did not ask for (no auto-READMEs, no auto-test files).

---

## What NOT to do

- Do not rewrite a file that only needed a small change
- Do not repeat the user's question at the start of a response
- Do not add a closing summary that repeats what was just said
- Do not generate example usage or test cases unless asked
- Do not generate more than one implementation unless alternatives were requested
- Do not pad responses with "Great question!" or similar
- Do not output boilerplate comments

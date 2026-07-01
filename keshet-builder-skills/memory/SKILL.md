---
name: memory
description: >
  Use at the start of any Claude Code session on a Builder project, when a
  significant technical or architectural decision is made, or at session end
  (>15 minutes or >10 tool calls).
---

# Memory Skill — Keshet Builder Mandatory

## Purpose

Claude Code has no built-in memory between sessions. Without explicit memory
management, every new session starts blind — losing decisions made, context
accumulated, and open items tracked.

This skill enforces a structured memory system using three files in
`.claude/memory/` (or the platform equivalent — see Platform Detection
below), committed to the repo so memory is shared across machines and
survives session restarts. Full step-by-step protocols, decision-entry
format, and file templates live in `protocols.md`.

---

## Memory Files

```
.claude/
└── memory/
    ├── decisions.md      ← architectural and technical decisions (permanent record)
    ├── session-log.md    ← compressed history of recent sessions (rolling, last 10)
    └── project-state.md  ← current build status, open items, next step (always current)
```

These files are **part of the repo** — commit them. Do not put credentials,
PII, or sensitive data in memory files.

---

## Trigger Conditions

Activate when: a Claude Code session starts on any Builder project (always
— session start briefing), a significant architectural/technical decision
is made, a Builder Flow gate is crossed, the session runs >15 minutes or
>10 tool calls, or the user says "done" / "wrap up" / "end session".

---

## Platform Detection — Run First

Before applying any memory protocol, detect the environment, then follow
the matching protocol in `protocols.md`:

```
IF running in Claude Code CLI with a project directory:
  → Standard Protocol (.claude/memory/ files)

IF running in Cowork WITH a connected/mounted folder:
  → Cowork Protocol (memory files in the connected folder)

IF running in Cowork WITHOUT a connected folder, OR in Claude.ai Chat:
  → In-Conversation Protocol (no files — summary block only)
```

> **Platform compatibility:** Claude Code CLI (full — Standard Protocol),
> Cowork (supported — Cowork Protocol), Claude.ai Chat (supported —
> In-Conversation Protocol).

---

## What NOT to do

- Do not put credentials, API keys, or secrets in any memory file
- Do not put PII (names, emails, employee data) in memory files
- Do not skip the session start briefing — it prevents repeated work and lost context
- Do not let `session-log.md` grow unbounded — keep the last 10 sessions only
- Do not overwrite `decisions.md` — only append; decisions are a permanent record
- If the project is git-backed, do not skip committing memory files at session end — without a commit, the memory is lost
- Do not use the Standard Protocol in Cowork without a connected folder — use the In-Conversation Protocol instead

---

## Session End Output

```
=== SESSION END REVIEW — [Project Name] ===
Memory files updated: decisions.md / session-log.md / project-state.md
Committed to git: [YES / REMINDER: run git add .claude/memory/ && git commit]

VERDICT: PASS — session memory complete
```

Full session-end procedure (what goes in each file): `protocols.md`.

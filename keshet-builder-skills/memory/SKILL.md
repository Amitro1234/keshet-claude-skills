---
name: keshet-memory
description: >
  Session memory and decision tracking for Keshet Builders. Loads project context
  at session start, captures decisions during the session, and writes a structured
  summary at session end. Triggers on: start of any Claude Code session on a Builder
  project, any architectural or technical decision, and at session end (>15 minutes
  or >10 tool calls). Prevents context loss between sessions.
---

# Memory Skill — Keshet Builder Mandatory

## Purpose

Claude Code has no built-in memory between sessions. Without explicit memory management,
every new session starts blind — losing decisions made, context accumulated, and open
items tracked.

This skill enforces a structured memory system using three files in `.claude/memory/`.
These files are committed to the repo so memory is shared across machines and survives
session restarts.

---

## Memory Files

```
.claude/
└── memory/
    ├── decisions.md      ← architectural and technical decisions (permanent record)
    ├── session-log.md    ← compressed history of recent sessions (rolling, last 10)
    └── project-state.md  ← current build status, open items, next step (always current)
```

These files are **part of the repo** — commit them. They are not secrets.
Do not put credentials, PII, or sensitive data in memory files.

---

## Trigger Conditions

Activate this skill when any of the following applies:
- A Claude Code session starts on any Builder project (always — session start briefing)
- A significant architectural or technical decision is made during a session
- A Builder Flow gate is crossed
- The session has run for more than 15 minutes
- More than 10 tool calls have been made
- The user says "done", "wrap up", "end session", or "that's it for today"

---

## Session Start Protocol

**Run this at the start of every session on a Builder project.**

### Step 1: Check for memory files

```bash
ls .claude/memory/
```

If the folder does not exist:
```
Memory not initialized for this project.
Initializing now — creating .claude/memory/ with empty files.
```
Create the three empty files with headers (see templates below).

### Step 2: Load and summarize memory

Read all three files and produce a session briefing:

```
=== SESSION START — [Project Name] ===
Date: [today]

FROM PROJECT STATE:
  Builder Flow step: [current step]
  Last gate passed: [gate + date]
  Open items: [list from project-state.md]

FROM RECENT SESSIONS:
  Last session ([date]): [1-line summary]
  Key decisions since [date]: [bullet list from decisions.md]

READY TO CONTINUE.
Next suggested action: [derived from open items]
```

If memory files are empty (new project): state that and ask the Builder what step they are on.

### Step 3: Cache memory files

Mark all three memory files for prompt caching (they are small, stable, and read every session):
```python
# Apply cache_control to memory file content when building system prompt
"cache_control": {"type": "ephemeral"}
```

---

## During-Session Protocol: Capturing Decisions

Whenever a significant decision is made during a session, capture it immediately.

A "significant decision" is any of:
- Technology or framework selection
- Database schema design choice
- API design pattern choice
- Security approach choice
- Architectural pattern (layered, event-driven, etc.)
- "We decided not to do X" (negative decisions are equally important)
- Any deviation from org standards (with justification)

### Decision entry format

Append to `decisions.md`:

```markdown
## [YYYY-MM-DD] [short title]

**Decision:** [what was decided, in one sentence]
**Context:** [why this decision was needed]
**Alternatives considered:** [what else was on the table]
**Consequences:** [trade-offs accepted, what this makes easier/harder]
**Owner:** [who made/approved the decision]
```

Announce when writing: "Recording decision to memory: [title]."

---

## Session End Protocol

**Run when ANY of the following is true:**
- Session has run for >15 minutes
- More than 10 tool calls were made
- A Builder Flow gate was crossed
- The user says "done", "wrap up", "end session", "that's it for today"

### Step 1: Write session summary to session-log.md

Prepend a new entry (keep the last 10 entries, compress older ones):

```markdown
## [YYYY-MM-DD HH:MM] — Session Summary

**Duration:** ~[N] minutes
**Tool calls:** [N]
**Builder Flow step at end:** [N]

**What was done:**
- [bullet: completed task]
- [bullet: completed task]

**Decisions made:** (see decisions.md for full entries)
- [1-line per decision]

**Files changed:**
- `path/to/file.py` — [what changed]

**Open items carried forward:**
- [ ] [item]
```

### Step 2: Update project-state.md

Overwrite the file completely with the current state:

```markdown
# Project State — [Project Name]
Last updated: [YYYY-MM-DD HH:MM]

## Builder Flow
Current step: [N — step name]
Last gate passed: [step name] on [date]
Next gate: [step name]
Gate requirements remaining:
- [ ] [requirement]

## Open Items
- [ ] [item — who owns it]
- [ ] [item — who owns it]

## Current Focus
[One paragraph: what is being built right now, where it's headed]

## Known Blockers
- [blocker — what's needed to unblock]

## Recently Completed
- [date]: [what was completed]
```

### Step 3: Announce the summary

```
=== SESSION END REVIEW — [Project Name] ===
Date: [date]
Duration: ~[N] minutes · Tool calls: [N]

Memory files updated:
✅ decisions.md — [N new decisions recorded / no new decisions]
✅ session-log.md — [session summary written]
✅ project-state.md — [updated to current state]

Key things done this session:
- [bullet]

Open for next session:
- [bullet]

Committed to git: [YES / REMINDER: run git add .claude/memory/ && git commit]

VERDICT: PASS — session memory complete
```

---

## Memory File Templates (for initialization)

### decisions.md
```markdown
# Decisions Log — [Project Name]
Records architectural, technical, and product decisions.
Format: newest first.

---

<!-- decisions go here -->
```

### session-log.md
```markdown
# Session Log — [Project Name]
Compressed history of Builder sessions. Last 10 sessions kept in full.

---

<!-- sessions go here — newest first -->
```

### project-state.md
```markdown
# Project State — [Project Name]
Always-current snapshot. Overwritten at end of each session.

Last updated: [date]

## Builder Flow
Current step: 1 — Access Request
Last gate passed: none
Next gate: Step 6 — Spec Approval

## Open Items
- [ ] Complete Spec Pack

## Current Focus
Project just initialized. Spec Pack in progress.

## Known Blockers
None.

## Recently Completed
- [date]: Project initialized
```

---

## git Commit Reminder

Memory files must be committed to keep them shared and backed up.

At session end, if memory files were updated:
```
Reminder: commit memory files to preserve this session's context.

git add .claude/memory/
git commit -m "memory: session [date] — [1-line summary]"
```

---

## What NOT to do

- Do not put credentials, API keys, or secrets in any memory file
- Do not put PII (names, emails, employee data) in memory files
- Do not skip the session start briefing — it prevents repeated work
- Do not let session-log.md grow unbounded — keep last 10 sessions only
- Do not overwrite decisions.md — only append; decisions are a permanent record

---
name: keshet-documentation
description: >
  Documentation standards for Keshet Builders. Mandatory at Build (Step 7) and Spec
  Pack generation (Step 5). Triggers on: any request to write or review documentation,
  README, inline comments, API docs, or when completing a feature or module. Ensures
  documentation is complete enough for handoff without the original Builder.
---

# Documentation Skill — Keshet Builder Mandatory

## Purpose

Documentation is not optional. Every application built through the Keshet Vibe Coding
platform must be documented well enough that:

1. A new Builder can continue the work without asking the original author
2. Operations can run and troubleshoot the application in production
3. The Champion/Owner can verify that behavior matches the spec
4. Compliance can audit what the system does and what data it handles

**Rule of thumb:** If you left the company today, could another Builder pick this up
tomorrow? If not, the documentation is incomplete.

---

## Documentation Layers

Every application must have all applicable layers:

### Layer 1: CLAUDE.md (mandatory for every project)

Present at the project root. Loaded automatically by Claude Code on every session.

```markdown
# [Project Name] — CLAUDE.md

## Project overview
[1–3 sentences: what this app does, who uses it, what problem it solves]

## Data classification
[🟢 Public / 🟡 Internal / 🔴 Confidential]
[What data the app handles]

## Active org skills
The following Keshet skills are mandatory for this project:
- Security:      keshet-builder-skills/security/SKILL.md
- Architecture:  keshet-builder-skills/architecture/SKILL.md
- DB Structure:  keshet-builder-skills/db-structure/SKILL.md
- Code Review:   keshet-builder-skills/code-review/SKILL.md
- Documentation: keshet-builder-skills/documentation/SKILL.md
- Unit Test:     keshet-builder-skills/unit-test/SKILL.md
- Audit Logging: keshet-builder-skills/audit-logging/SKILL.md
- Model Router:  claude-enterprise-skills/model-router-skill/SKILL.md

## Architecture
[App category: Local Demo / Department Tool / Production]
[Key layers and how they communicate]
[Key technology choices with brief rationale]

## Key commands
[How to run locally, run tests, lint, build, deploy to Stage]

## Environment variables
[List each required env var, what it does, where to get it]

## External integrations
[List each external service/API/MCP connector, what it's used for]

## Known limitations
[Things that are intentionally not implemented, deferred scope]

## Contacts
Champion/Owner: [name]
Builder: [name]
Last updated: [date]
```

### Layer 2: README.md

User-facing. Concise. Written for the person who will use or maintain the app.

Required sections:
- **What it does** — one paragraph
- **How to get access** — who to ask, what's required
- **How to use it** — step-by-step for the primary use case
- **How to report a problem** — who to contact, what info to provide
- **Architecture diagram** — even a simple text diagram is sufficient

### Layer 3: Inline code documentation

Rules for inline documentation:

| Element | Documentation requirement |
|---|---|
| Public functions / methods | Docstring: what it does, params, return value, raises |
| Private functions | Comment if non-obvious; no comment if self-explanatory |
| Business logic | Comment WHY, not WHAT — code shows what; comments explain why |
| Magic numbers/strings | Extract to named constant with a comment explaining the value |
| Workarounds | Comment: what's being worked around, why, and when it can be removed |
| TODO items | Format: `# TODO(owner): description — issue #NNN` |

Bad inline documentation:
```python
# increment counter
counter += 1

# define function
def process_event(event):
    pass
```

Good inline documentation:
```python
# Retry limit set to 3 based on Keshet SLA: max 2-minute processing window.
# Increasing beyond 3 would breach the SLA on slow external APIs.
MAX_RETRIES = 3

def process_broadcast_event(event: dict) -> ProcessingResult:
    """
    Process an incoming broadcast event from the scheduling system.

    Args:
        event: Dict with keys: event_id (str), segment_id (str), scheduled_at (datetime)

    Returns:
        ProcessingResult with status and any error details

    Raises:
        ValidationError: if event is missing required fields
        IntegrationError: if the downstream scheduling API is unavailable
    """
```

### Layer 4: API Documentation

Required for any service that exposes HTTP endpoints or MCP tools.

For HTTP APIs — at minimum, for each endpoint:
```
GET /api/v1/segments/{id}
Description: Retrieve a broadcast segment by ID
Auth: Bearer token required (scope: segments:read)
Parameters: id (string, required) — segment UUID
Response 200: { id, name, duration_ms, status, created_at }
Response 404: { error: "segment not found" }
Response 401: { error: "unauthorized" }
```

For MCP tools — document each tool's:
- Name and description
- Input schema (each parameter: name, type, required, description)
- Output schema
- Side effects (what it writes, what it calls externally)
- Failure modes

### Layer 5: Runbook (required for Production apps)

Stored in `docs/runbook.md`. Required before Step 10 (Stage→Prod gate).

```markdown
# [App Name] Runbook

## How to deploy
[Step-by-step deploy instructions]

## How to roll back
[Exact steps to roll back to previous version]

## Key logs
[Where to find logs, what to look for]

## Common alerts and what to do
| Alert | Likely cause | Resolution |
|---|---|---|
| [alert name] | [cause] | [action] |

## How to restart the service
[Commands]

## Emergency contacts
[Who to call and when]
```

---

## Documentation Review Checklist

Before advancing from Step 7 (Build) to Step 8 (Validation):

- [ ] `CLAUDE.md` present and complete (all required sections filled)
- [ ] `README.md` present and written for the end user / maintainer
- [ ] All public functions have docstrings
- [ ] No unexplained magic numbers or constants
- [ ] All TODO items have owner and issue reference
- [ ] API / MCP tools documented
- [ ] Runbook present (Production apps only)

Output format:
```
=== DOCUMENTATION REVIEW — [App Name] ===
CLAUDE.md: [COMPLETE / MISSING SECTIONS: list]
README.md: [COMPLETE / MISSING SECTIONS: list]
Inline docs: [PASS / ISSUES: list]
API docs: [COMPLETE / MISSING: list]
Runbook: [COMPLETE / NOT REQUIRED / MISSING]
VERDICT: [PASS / NEEDS REVISION]
```

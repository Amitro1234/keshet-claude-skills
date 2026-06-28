---
name: keshet-spec-pack
description: >
  Spec Pack generation skill for Keshet Builders. Mandatory at Step 5 before any
  code is written. Produces three documents: PRD (Product Requirements Document),
  Technical Spec, and Acceptance Criteria. Triggers on: any request to start a new
  project, "let's write the spec", "what should we build", Step 5 in the Builder Flow,
  or any task that has not yet been specified in writing. Nothing gets built without a
  Spec Pack. This is the single highest-leverage quality gate.
---

# Spec Pack Skill — Keshet Builder Mandatory

## Purpose

A Spec Pack is the foundation of every Keshet Build. Writing code before a Spec Pack
is approved is the single most common cause of rework, miscommunication, and production
incidents on the platform.

This skill produces three documents that together define exactly what will be built,
how it will be built, and how anyone can verify it was built correctly.

**Rule:** No code is written until the Spec Pack is approved by the Champion/Owner (Step 6).

---

## Three Documents in a Spec Pack

| Document | Owner | Audience | Gate |
|---|---|---|---|
| **PRD** (Product Requirements Document) | Champion/Owner | Builder, Stakeholders | Step 6 |
| **Technical Spec** | Builder (with Claude) | Builder, AI Architecture | Step 6 |
| **Acceptance Criteria** | Champion/Owner + Builder | Builder, QA, Champion | Step 8 + Step 10 |

All three live in the Spec Pack ticket (Monday / Jira). They are linked from the
project's `CLAUDE.md` and committed to the repo under `docs/spec/`.

---

## Document 1: PRD (Product Requirements Document)

### Purpose
Defines the "what" and "why" — written from the user's perspective, not the technical
implementation's perspective.

### PRD Template

```markdown
# PRD — [Project Name]
Version: 1.0
Date: [date]
Champion/Owner: [name, role]
Builder: [name]
Status: [Draft / Under Review / Approved]

---

## Problem Statement
[1–3 sentences: what problem exists today, for whom, and what the impact is.
Be specific — not "we need a better process" but "the scheduling team manually
exports 150 rows from Monday every Monday morning, taking 2 hours, with frequent
copy-paste errors that delay the broadcast."]

## Proposed Solution
[1–2 sentences: what the system will do to solve the problem. No technical details yet.]

## Users and Use Cases

### Primary Users
| User type | Count | How they use it |
|---|---|---|
| [role] | [N] | [what they do with it] |

### Primary Use Cases
1. **[Use case name]:** [1 sentence description — who does what, with what outcome]
2. **[Use case name]:** [...]

### Out of Scope
[What this system explicitly will NOT do. Be specific — this prevents scope creep.]
- [item]
- [item]

## Success Metrics
How will we know this is working?
- [metric: e.g. "scheduling export takes <5 minutes instead of 2 hours"]
- [metric: e.g. "zero copy-paste errors on Monday uploads"]

## Data Classification
🟢 Public / 🟡 Internal / 🔴 Confidential
[What data will this system handle? Who can see it?]

## Constraints and Dependencies
- [constraint: timeline, budget, regulatory, existing system]
- [dependency: other system, team, approval needed]

## Open Questions
- [ ] [question — who needs to answer it, by when]
```

---

## Document 2: Technical Spec

### Purpose
Defines the "how" — the architecture, data model, integrations, and implementation
plan. Written by the Builder with Claude assistance. Reviewed by AI Architecture
for Production apps.

### Technical Spec Template

```markdown
# Technical Spec — [Project Name]
Version: 1.0
Date: [date]
Builder: [name]
Reviewed by: [AI Architecture reviewer, if applicable]
Status: [Draft / Under Review / Approved]

---

## Application Category
[Local Demo / Department Tool / Production]

## Architecture Overview

### Layer diagram
```
[Presentation]   ← [what's here: e.g., Python FastAPI routes, or MCP tool handlers]
[Business Logic] ← [what's here: e.g., scheduling logic, validation rules]
[Data Access]    ← [what's here: e.g., DB models, Monday API client]
[Infrastructure] ← [logging, secrets, config, monitoring]
```

### Technology Stack
| Layer | Technology | Justification |
|---|---|---|
| Language | [e.g. Python 3.12] | [reason — e.g., team familiarity, existing libs] |
| Framework | [e.g. FastAPI] | [reason] |
| Database | [e.g. PostgreSQL 15] | [reason] |
| Hosting | [e.g. Azure App Service] | [reason] |

Any deviation from org defaults (Python / TypeScript) requires an ADR.

### External Integrations
| Service | MCP Connector | Purpose | Data sent | Approved? |
|---|---|---|---|---|
| [e.g. Monday.com] | `monday` | Read task list | Internal task data | ✅ See approved-mcp-connectors.md |

### Data Model
[For each key entity, define the table/schema. Reference `db-structure` skill for
naming conventions.]

```sql
-- Example
CREATE TABLE broadcast_events (
    id          BIGSERIAL PRIMARY KEY,
    external_id TEXT NOT NULL,
    title       TEXT NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX uq_broadcast_events_external_id ON broadcast_events(external_id);
```

### API Design
[For each endpoint, define the contract.]

```
POST /api/v1/events
Description: Create a broadcast event
Auth: Bearer token (scope: events:write)
Request body: { external_id, title, scheduled_at }
Response 201: { id, external_id, title, scheduled_at, status }
Response 400: { error: "validation error", details: [...] }
Response 409: { error: "duplicate external_id" }
```

### Security Approach
- Authentication: [e.g., Azure AD token via MSAL]
- Authorization: [e.g., role check on every endpoint]
- Secret management: [e.g., Azure Key Vault via environment variables]
- Data classification handling: [specific controls for this project's data level]

### Error Handling Strategy
[How will errors be surfaced to users? What gets logged? What gets retried?]

### Deployment Plan
- Stage: [where, how, what CI/CD]
- Production: [where, how, what CI/CD]
- Rollback: [how to roll back if something goes wrong]

## Architectural Decision Records (ADRs)

### ADR-001: [Decision title]
**Date:** [date]
**Status:** Accepted
**Context:** [what problem]
**Decision:** [what was chosen]
**Alternatives:** [what else was considered]
**Consequences:** [trade-offs]

## Known Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| [risk] | High/Med/Low | High/Med/Low | [how we handle it] |

## Estimated Build Time
| Phase | Estimate | Owner |
|---|---|---|
| DB schema + migrations | [Xh] | Builder |
| API routes | [Xh] | Builder |
| Business logic | [Xh] | Builder |
| Tests | [Xh] | Builder |
| Documentation | [Xh] | Builder |
| **Total** | **[Xh]** | |
```

---

## Document 3: Acceptance Criteria

### Purpose
Defines exactly what "done" means. Written in plain language. Used by the Builder
to verify the build, by Claude to run the Validation Sandbox (Step 8), and by the
Champion/Owner to sign off at Step 10.

### Acceptance Criteria Template

```markdown
# Acceptance Criteria — [Project Name]
Version: 1.0
Date: [date]
Status: [Draft / Approved]

---

## Format: Given / When / Then

Each criterion follows this format:
- **Given** [initial state or precondition]
- **When** [action taken]
- **Then** [expected outcome — verifiable and specific]

---

## Functional Criteria

### [Use Case 1 name]

**AC-001:**
- Given: [precondition]
- When: [action]
- Then: [outcome — specific and measurable, e.g., "the event appears in the list with status 'scheduled'"]

**AC-002:**
- Given: [precondition]
- When: [action — edge case, e.g., duplicate entry]
- Then: [outcome — e.g., "a 409 error is returned with message 'duplicate external_id'"]

### [Use Case 2 name]

**AC-003:** ...

---

## Non-Functional Criteria

**AC-NF-001 — Performance:**
- Given: 100 concurrent users
- When: any user submits an event
- Then: the response time is under 500ms at the 95th percentile

**AC-NF-002 — Security:**
- Given: an unauthenticated request
- When: any protected endpoint is called
- Then: a 401 is returned — no data is exposed

**AC-NF-003 — Logging:**
- Given: any user action that writes data
- When: the action completes (success or failure)
- Then: an audit trail entry is written with actor, action, resource, result, and timestamp

---

## Out-of-Scope Confirmations

The following are explicitly NOT tested and NOT expected:
- [item]

---

## Sign-off

Champion/Owner: _____________________ Date: _______
Builder: _____________________ Date: _______
```

---

## Spec Pack Review Checklist

Before advancing from Step 5 to Step 6 (Spec Approval):

**PRD:**
- [ ] Problem statement is specific and quantified (not vague)
- [ ] Use cases are named and described from the user's perspective
- [ ] Out of scope is explicitly listed
- [ ] Success metrics are measurable
- [ ] Data classification is declared

**Technical Spec:**
- [ ] Application category declared (Local Demo / Department Tool / Production)
- [ ] Architecture diagram complete — all layers defined
- [ ] Technology choices made with rationale
- [ ] All external integrations listed and verified against `approved-mcp-connectors.md`
- [ ] Data model defined (if DB exists)
- [ ] API endpoints defined (if applicable)
- [ ] Security approach documented
- [ ] Deployment plan exists

**Acceptance Criteria:**
- [ ] At least one AC per use case
- [ ] At least one AC per error/edge case
- [ ] Non-functional AC covers performance, security, and logging
- [ ] Each AC is verifiable — "user sees a success message" is not verifiable; "HTTP 201 with `{ id, status }` is returned" is

**Output format:**

```
=== SPEC PACK REVIEW — [Project Name] ===
PRD: [COMPLETE / MISSING: list]
Technical Spec: [COMPLETE / MISSING: list]
Acceptance Criteria: [COMPLETE / MISSING: list]
Ready for Step 6 (Champion Approval): [YES / NO — list blocking items]
```

---

## What NOT to do

- Do not start writing code before the Spec Pack is approved at Step 6
- Do not write Acceptance Criteria that are not testable ("the app should be fast")
- Do not skip the Technical Spec for "small" projects — scope always grows
- Do not leave out Out of Scope — it is the most important section for preventing rework
- Do not write the Spec Pack alone — the PRD must be validated by the Champion/Owner before Step 6

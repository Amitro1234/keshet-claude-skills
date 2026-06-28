---
name: keshet-architecture
description: >
  Architecture standards for Keshet Builders. Enforces structural decisions during
  Build (Step 7) and validates them at the Agent Validation Sandbox (Step 8).
  Triggers on: new service design, API design, module structure, technology choices,
  integration patterns, database selection, or any "how should I build this" question.
---

# Architecture Skill — Keshet Builder Mandatory

## Purpose

Applications built on the Keshet Vibe Coding platform must follow organizational
architecture standards. This skill ensures Builders make sound structural decisions
from the start — not after code review in production.

**Default stance:** When in doubt, choose the simplest architecture that meets the
requirement. Do not over-engineer. A department tool does not need microservices.

---

## Trigger Conditions

Activate this skill when any of the following applies:
- Designing a new service, module, or application from scratch
- Choosing a technology stack or database
- Designing an API or integration pattern
- Structuring an existing codebase that has no clear layers
- The user asks "how should I build this?" or "what architecture should I use?"
- Advancing from Step 7 (Build) to Step 8 (Validation Sandbox)
- Any deviation from standard org patterns is being considered

---

## Application Categories and Architecture Fit

Before writing a single line of code, classify the application:

| Category | Definition | Recommended Architecture |
|---|---|---|
| **Local Demo** | Runs on Builder's machine only | Single script or simple app, no production concerns |
| **Department Tool** | Used by one department, <50 users | Monolith, simple REST API, managed DB service |
| **Production** | Broad exposure, sensitive data, or critical process | Layered architecture, proper separation of concerns, full Builder Flow |

**Never apply production-grade complexity to a Department Tool.** Conversely, never
deploy a Local Demo pattern to Production.

---

## Structural Standards

### Layered Architecture (required for all Production apps)

```
┌────────────────────────────────────────────┐
│  Presentation Layer                         │  ← UI, API routes, MCP tool handlers
├────────────────────────────────────────────┤
│  Business Logic Layer                       │  ← Domain logic, rules, workflows
├────────────────────────────────────────────┤
│  Data Access Layer                          │  ← DB queries, external API calls, caching
├────────────────────────────────────────────┤
│  Infrastructure Layer                       │  ← Config, logging, secrets, monitoring
└────────────────────────────────────────────┘
```

Rules:
- Presentation Layer must not contain business logic
- Business Logic Layer must not contain SQL or raw HTTP calls
- Data Access Layer must not contain routing or UI logic
- Infrastructure concerns (logging, config) must not be scattered across layers

### Module / File Structure

```
project/
├── src/
│   ├── api/         ← Routes and HTTP handlers
│   ├── services/    ← Business logic
│   ├── data/        ← DB models, repository pattern, external clients
│   ├── utils/       ← Pure utility functions, no side effects
│   └── config/      ← Config loading, environment variable handling
├── tests/
│   ├── unit/
│   └── integration/
├── CLAUDE.md        ← Org skills + project context for Claude
└── .env.example     ← Template — no real secrets
```

Do not deviate from this structure without documenting the reason in the Spec Pack.

---

## Technology Selection Rules

### Language and Runtime

- **Default:** Python 3.11+ (backend), TypeScript (frontend / Node scripts)
- Other languages require explicit justification in the Spec Pack
- No mixing of languages in the same service without a clear boundary

### API Design

- **REST** for standard CRUD operations and integrations
- **Async/event-driven** (via webhook or message queue) for long-running operations
- No GraphQL without explicit approval — adds complexity for most use cases
- API versioning: `/api/v1/` prefix from day one — not retrofitted later

### Database Selection

| Use Case | Recommended | Avoid |
|---|---|---|
| Structured business data | PostgreSQL | SQLite in production |
| Key-value store / cache | Redis | Rolling your own cache |
| Document store | MongoDB (if justified) | JSON blobs in a relational DB |
| Search | Elasticsearch (if justified) | Full-text LIKE queries at scale |

Refer to `db-structure` skill for schema standards.

### External Integrations

- All external API calls go through a dedicated client class in `src/data/`
- No direct `requests.get()` or `axios.get()` calls in business logic
- Rate limits, retries, and timeouts must be configured — not left at defaults
- Only connectors on the approved Keshet connector list are permitted without review

### MCP / AI Integration

- Only MCP tools from the org-approved list may be called
- Every MCP tool call must be logged (who, when, what was passed)
- AI-generated content must be labeled as such in any user-facing output

---

## Architecture Decision Record (ADR)

For any non-trivial architectural decision, include a brief ADR in the Spec Pack:

```markdown
## ADR: [Decision title]
**Date:** [date]
**Status:** Accepted

**Context:** [What problem are we solving?]
**Decision:** [What did we choose?]
**Alternatives considered:** [What else was on the table?]
**Consequences:** [Trade-offs accepted]
```

Decisions requiring an ADR:
- Database selection
- API design pattern
- Authentication mechanism
- External service dependency
- Any deviation from the standard project structure

---

## Anti-Patterns — Hard Prohibitions

| Anti-pattern | Why it's prohibited |
|---|---|
| Secrets in source code | Security — see `security` skill |
| Business logic in API routes | Untestable, unmaintainable |
| Direct DB access from UI layer | Couples presentation to data |
| God objects / god services | Impossible to test and maintain |
| `print()` as logging | No log levels, no structure, lost in production |
| Synchronous calls to slow external APIs in request path | Blocks the server |
| SQLite in a shared/production environment | Concurrency issues, no access control |
| Storing sessions in memory only | Lost on restart, broken in multi-instance |

---

## Architecture Review Checklist

Before advancing from Step 7 (Build) to Step 8 (Validation):

- [ ] Application category declared (Local Demo / Department Tool / Production)
- [ ] Layered architecture enforced — no cross-layer violations
- [ ] All technology choices match org standards or have an ADR
- [ ] No prohibited anti-patterns present
- [ ] External integrations go through a client class, not inline
- [ ] MCP tool calls are logged and limited to approved tools
- [ ] Project follows the standard folder structure
- [ ] `CLAUDE.md` present at project root with active skills listed

Output format:
```
=== ARCHITECTURE REVIEW — [App Name] ===
Category: [Local Demo / Department Tool / Production]
Layers: [PASS / VIOLATIONS: list]
Technology: [PASS / DEVIATIONS: list with ADR reference]
Anti-patterns: [NONE / FOUND: list]
VERDICT: [PASS / NEEDS REVISION]
```

---

## What NOT to do

- Do not apply production-grade complexity (microservices, event sourcing) to a Department Tool
- Do not put business logic in API routes — it becomes untestable
- Do not access the database directly from the UI or presentation layer
- Do not use `print()` as logging in any environment — use a structured logger
- Do not choose a technology without a documented rationale (ADR or Spec Pack note)
- Do not deviate from the standard project folder structure without recording it in the Spec Pack
- Do not call external APIs inline in business logic — always through a dedicated client class
- Do not use SQLite in any shared or production environment

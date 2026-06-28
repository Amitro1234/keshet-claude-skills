# Keshet Builder Skills — Mandatory Quality Gates

Skills and rules for the Keshet Vibe Coding Builder Flow.
Maintained by AI Architecture (Amit Rosen, CIO division).

---

## Overview

These skills are **mandatory** for every Builder working on a Production or Department Tool
application. They are enforced as Rules through Claude Code — not optional.

Each skill maps to one or more steps in the Keshet Builder Flow (11 steps with gates).

---

## Repository structure

```
keshet-builder-skills/
├── README.md                    ← this file
├── spec-pack/
│   └── SKILL.md                 ← PRD, Technical Spec, Acceptance Criteria (Step 5)
├── security/
│   └── SKILL.md                 ← secret exposure, input validation, auth, deps
├── architecture/
│   └── SKILL.md                 ← layered structure, tech selection, anti-patterns
├── db-structure/
│   └── SKILL.md                 ← schema standards, naming, migrations, indexing
├── code-review/
│   └── SKILL.md                 ← 5-dimension review: correctness, security, maintainability, perf, tests
├── documentation/
│   └── SKILL.md                 ← CLAUDE.md, README, inline docs, API docs, runbook
├── unit-test/
│   └── SKILL.md                 ← AAA pattern, coverage requirements, mocking rules
├── audit-logging/
│   └── SKILL.md                 ← structured logs, audit trail, PII rules, SIEM routing
├── deployment/
│   └── SKILL.md                 ← Stage + Prod deployment checklist, smoke tests, rollback (Steps 9, 10)
├── monitoring-alerting/
│   └── SKILL.md                 ← SLOs, health check, alerts, dashboard, on-call (Step 11)
└── memory/
    └── SKILL.md                 ← session memory, decision log, project state tracking
```

---

## Builder Flow — Skill Mapping

| Flow Step | Required Skills |
|---|---|
| Step 1: New project init | memory (initialize .claude/memory/) |
| Step 5: Spec Pack generation | spec-pack + documentation |
| Step 7: Build with Claude | security + architecture + db-structure + documentation + unit-test + audit-logging |
| Step 8: Agent Validation Sandbox | code-review + security + unit-test |
| Step 9: Stage deployment | deployment |
| Step 10: Stage→Prod Gate | code-review (all 5 dimensions) + security + audit-logging + deployment |
| Step 11: Production Monitoring | audit-logging + monitoring-alerting |
| Every session (start/end) | memory |

---

## How to activate (CLAUDE.md)

Add the following to your project's `CLAUDE.md`:

```markdown
## Mandatory Keshet Builder Skills

The following skills are active for this project and must run at the appropriate steps:

- Spec Pack:     ~/.claude/skills/keshet-claude-skills/keshet-builder-skills/spec-pack/SKILL.md
- Security:      ~/.claude/skills/keshet-claude-skills/keshet-builder-skills/security/SKILL.md
- Architecture:  ~/.claude/skills/keshet-claude-skills/keshet-builder-skills/architecture/SKILL.md
- DB Structure:  ~/.claude/skills/keshet-claude-skills/keshet-builder-skills/db-structure/SKILL.md
- Code Review:   ~/.claude/skills/keshet-claude-skills/keshet-builder-skills/code-review/SKILL.md
- Documentation: ~/.claude/skills/keshet-claude-skills/keshet-builder-skills/documentation/SKILL.md
- Unit Test:     ~/.claude/skills/keshet-claude-skills/keshet-builder-skills/unit-test/SKILL.md
- Audit Logging: ~/.claude/skills/keshet-claude-skills/keshet-builder-skills/audit-logging/SKILL.md
- Deployment:    ~/.claude/skills/keshet-claude-skills/keshet-builder-skills/deployment/SKILL.md
- Monitoring:    ~/.claude/skills/keshet-claude-skills/keshet-builder-skills/monitoring-alerting/SKILL.md
- Memory:        ~/.claude/skills/keshet-claude-skills/keshet-builder-skills/memory/SKILL.md
```

Also install the CLAUDE.md files:
- Global (per-machine, once): copy `templates/global.CLAUDE.md` → `~/.claude/CLAUDE.md`
- Per-project: copy `templates/project.CLAUDE.md.template` → `[project-root]/CLAUDE.md`

---

## Skill Summary

| Skill | Trigger | Output |
|---|---|---|
| **spec-pack** | Step 5 — before any code is written | Spec Pack Review with PRD + Technical Spec + AC completeness check |
| **security** | Any credential, auth, PII, or external integration code | Security Review with PASS/BLOCK verdict |
| **architecture** | New service design, tech choices, module structure | Architecture Review with PASS/NEEDS REVISION |
| **db-structure** | Schema creation, migrations, ORM models | DB Structure Review with PASS/NEEDS REVISION |
| **code-review** | Any code before gate crossing | 5-dimension review with severity-classified findings |
| **documentation** | Feature completion, Spec Pack generation | Documentation Review with PASS/NEEDS REVISION |
| **unit-test** | New functions, bug fixes, before gate crossings | Test Review with coverage report |
| **audit-logging** | Any user action, data write, admin op, MCP call | Audit & Logging Review with PASS/NEEDS REVISION |
| **deployment** | Steps 9 and 10 — deploying to Stage or Production | Deployment sign-off with pre-flight + smoke test results |
| **monitoring-alerting** | Step 10 gate + Step 11 production | Monitoring Review with SLOs, alerts, and on-call checklist |
| **memory** | Session start/end, any architectural decision | Session briefing + decision log + project state update |

---

## Severity Model

All reviews use a consistent severity model:

| Level | Meaning | Gate impact |
|---|---|---|
| 🔴 BLOCKER | Must fix before advancing — security, data loss, or spec mismatch | Stops the build |
| 🟡 MAJOR | Should fix; Champion sign-off required to advance with open item | Conditional advance |
| 🟢 MINOR | Encouraged fix; does not block | Can advance |
| 💡 SUGGESTION | Optional improvement | No impact |

---

## Relationship to Enterprise Skills

These Builder Skills work alongside the `claude-enterprise-skills` collection:

```
claude-enterprise-skills/   ← FinOps: cost, tokens, model routing, caching
keshet-builder-skills/      ← Quality Gates: security, architecture, testing, compliance
```

Recommended load order:
```
1. model-router        (enterprise) → model selection
2. context-hygiene     (enterprise) → trim context
3. prompt-caching      (enterprise) → cache stable prefixes
4. output-discipline   (enterprise) → response format
5. spec-pack           (builder)    → Step 5: before any code is written
6. security            (builder)    → always active on code that touches credentials/data
7. architecture        (builder)    → on new design decisions
8. db-structure        (builder)    → on any schema work
9. code-review         (builder)    → before gate crossings
10. documentation      (builder)    → on feature completion
11. unit-test          (builder)    → before gate crossings
12. audit-logging      (builder)    → on any user-facing or data-writing code
13. deployment         (builder)    → Steps 9 and 10: Stage and Production deployments
14. monitoring-alerting (builder)   → Step 10 gate and Step 11: Production monitoring
```

---

## Maintenance

Owner: Amit Rosen, AI Architecture, CIO division
Review cycle: Quarterly, or after any Builder Flow policy update
Last updated: June 2026

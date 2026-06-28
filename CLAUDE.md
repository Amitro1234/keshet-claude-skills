# keshet-claude-skills — CLAUDE.md

This repository contains the official Keshet AI skills library.
Maintained by Amit Rosen, AI Architecture, CIO division.

---

## What's in this repo

```
keshet-claude-skills/
├── claude-enterprise-skills/     ← FinOps: cost control, token optimization
│   ├── model-router-skill/       ← route tasks to cheapest capable model
│   ├── context-hygiene/          ← prevent context bloat
│   ├── output-discipline/        ← reduce output token waste
│   ├── prompt-caching/           ← 90% discount on repeated context
│   ├── agentic-loop-guard/       ← prevent runaway agent spend
│   └── batch-detector/           ← 50% discount via Batch API
│
├── keshet-builder-skills/        ← Quality gates for Builder Flow
│   ├── spec-pack/                ← mandatory: PRD, Technical Spec, Acceptance Criteria (Step 5)
│   ├── security/                 ← mandatory: secrets, auth, input validation
│   ├── architecture/             ← mandatory: layers, tech selection, anti-patterns
│   ├── db-structure/             ← mandatory: schema, naming, migrations
│   ├── code-review/              ← mandatory: 5-dimension review before gates
│   ├── documentation/            ← mandatory: CLAUDE.md, README, inline, runbook
│   ├── unit-test/                ← mandatory: coverage, AAA, mocking rules
│   ├── audit-logging/            ← mandatory: structured logs, audit trail, PII
│   ├── deployment/               ← mandatory: Stage + Prod deployment checklist (Steps 9, 10)
│   ├── monitoring-alerting/      ← mandatory: SLOs, alerts, dashboards (Step 11)
│   └── memory/                   ← mandatory: session memory, decision log
│
├── company-agent-guardrails/     ← Safety rules: secrets, destructive ops, MCP policy
│
├── docs/                         ← Org-level reference documents
│   ├── approved-mcp-connectors.md ← authoritative list of approved MCP connectors
│   └── incident-response.md      ← security incident response procedure (P1–P4)
│
└── templates/                    ← CLAUDE.md templates for global and per-project use
    ├── global.CLAUDE.md          ← copy to ~/.claude/CLAUDE.md on Builder machines
    ├── project.CLAUDE.md.template ← copy to each new Builder project root
    └── .claudeignore.example     ← copy to project root as .claudeignore
```

---

## How to update skills

1. Edit the relevant `SKILL.md` file
2. Open a PR — changes are picked up by Claude Code automatically on next session
3. No reinstall needed for existing users (skills are loaded from path on each session)

---

## Contacts

Owner: Amit Rosen · Amit.Rosen@keshet-tv.com · AI Architecture, CIO division
Review cycle: Quarterly
Last updated: June 2026

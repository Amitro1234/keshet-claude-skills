# keshet-claude-skills

Official Claude Code skills library for the Keshet Vibe Coding platform.  
Maintained by AI Architecture — Amit Rosen, CIO division.

---

## What's here

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
├── keshet-builder-skills/        ← Mandatory quality gates for Builder Flow
│   ├── spec-pack/                ← PRD, Technical Spec, Acceptance Criteria (Step 5)
│   ├── security/                 ← secrets, auth, input validation, dependencies
│   ├── architecture/             ← layered structure, tech selection, anti-patterns
│   ├── db-structure/             ← schema standards, naming, migrations
│   ├── code-review/              ← 5-dimension review before every gate
│   ├── documentation/            ← CLAUDE.md, README, inline docs, runbook
│   ├── unit-test/                ← coverage, AAA pattern, mocking rules
│   ├── audit-logging/            ← structured logs, audit trail, PII protection
│   ├── deployment/               ← Stage + Production deployment checklist (Steps 9, 10)
│   ├── monitoring-alerting/      ← SLOs, alerts, dashboards, on-call (Step 11)
│   └── memory/                   ← session memory, decision log, project state
│
├── company-agent-guardrails/     ← Safety rules for all AI coding agents
│
├── docs/
│   ├── approved-mcp-connectors.md ← authoritative list of approved MCP connectors
│   └── incident-response.md      ← security incident response procedure (P1–P4)
│
└── templates/
    ├── global.CLAUDE.md          ← install once: ~/.claude/CLAUDE.md
    ├── project.CLAUDE.md.template ← copy to each new Builder project root
    └── .claudeignore.example     ← copy to project root as .claudeignore
```

---

## Quick start (Builder setup)

### 1 — Clone this repo

```bash
git clone https://github.com/Amitro1234/keshet-claude-skills.git ~/.claude/skills/keshet-claude-skills
```

Or if installing globally on a Builder machine:

```
~/.claude/
└── skills/
    └── keshet-claude-skills/     ← this repo
```

### 2 — Install the global CLAUDE.md

```bash
cp ~/.claude/skills/keshet-claude-skills/templates/global.CLAUDE.md ~/.claude/CLAUDE.md
```

This activates all enterprise skills and builder gates on every project on your machine.

### 3 — Start a new project

```bash
cp ~/.claude/skills/keshet-claude-skills/templates/project.CLAUDE.md.template ./CLAUDE.md
# Edit CLAUDE.md — fill in all [PLACEHOLDERS]
```

That's it. Claude Code picks up the skills automatically on the next session.

---

## Skill execution order

```
1. model-router        → pick the cheapest capable model
2. context-hygiene     → trim context before sending
3. prompt-caching      → cache stable prefixes (Spec Pack, CLAUDE.md)
4. output-discipline   → govern response format
5. company-agent-guardrails → safety rules always active
--- Builder gates (trigger at relevant Build Flow steps) ---
6. spec-pack           → Step 5: Spec Pack generation (PRD, Technical Spec, AC)
7. security            → any credential, auth, or PII code
8. architecture        → any new design decision
9. db-structure        → any schema or migration work
10. code-review        → before every gate crossing
11. documentation      → feature completion and Spec Pack
12. unit-test          → before gate crossings
13. audit-logging      → any user action or data write
14. deployment         → Steps 9 and 10: Stage and Production deployment
15. monitoring-alerting → Step 10 gate and Step 11: Production
16. memory             → every session start and end
--- Async/bulk workloads ---
17. agentic-loop-guard → any autonomous multi-step agent session
18. batch-detector     → any job with N>10 items that can wait
```

---

## Builder Flow — skill mapping

| Flow Step | Skills required |
|---|---|
| Step 1: New project | memory (init) |
| Step 5: Spec Pack | spec-pack + documentation |
| Step 7: Build | security + architecture + db-structure + documentation + unit-test + audit-logging |
| Step 8: Validation Sandbox | code-review + security + unit-test |
| Step 9: Stage deployment | deployment |
| Step 10: Stage→Prod Gate | code-review (all 5 dimensions) + security + audit-logging + deployment |
| Step 11: Production | audit-logging + monitoring-alerting |
| Every session | memory (start + end) |

---

## Updating skills

1. Edit the relevant `SKILL.md`
2. Open a PR — changes are picked up by Claude Code automatically on next session
3. No reinstall needed (skills are loaded from path each session)

---

## Known gaps / future work

- **CI validation:** `tools/validate-skills.ps1` runs automatically on every PR via `.github/workflows/validate-skills.yml` (GitHub-hosted `pwsh`). It can also be run locally — on Windows PowerShell 5.1 the script must stay UTF-8-with-BOM (it contains non-ASCII characters that PS 5.1 misreads under a non-UTF-8 ANSI codepage otherwise), or run it under `pwsh`.
- **Incident response contacts:** `docs/incident-response.md` has placeholder `[fill in]` entries for CISO and Legal escalation contacts. These must be filled in before the document is useful in a real P1.
- **Pricing freshness:** model cost figures in `model-router/SKILL.md` and `global.CLAUDE.md` are hardcoded. Review them quarterly alongside the Anthropic pricing page.

---

## Cost impact (estimated, 20 Builders)

| Optimization | Mechanism | Saving |
|---|---|---|
| model-router | Haiku for light tasks | −35% on API |
| context-hygiene | Exclude junk, compress history | −15% to −25% |
| output-discipline | Diffs, no padding | −10% to −20% |
| prompt-caching | 90% off repeated context | −10% to −30% |
| batch-detector | 50% off async jobs | −5% to −15% |
| **Combined** | | **−50% to −65% vs. baseline** |

---

## Contacts

Owner: Amit Rosen · Amit.Rosen@keshet-tv.com · AI Architecture, CIO division  
Review cycle: Quarterly  
Last updated: June 2026

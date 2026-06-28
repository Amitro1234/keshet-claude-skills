# CHANGELOG — keshet-claude-skills

All notable changes to this skills library are recorded here.
Format: newest entry first. Review cycle: quarterly (or after any policy or pricing update).

Owner: AI Architecture (Amit Rosen, CIO division)

---

## [2.0.0] — June 2026

### Added

**New skills:**
- `keshet-builder-skills/spec-pack/` — Spec Pack generation skill (PRD, Technical Spec,
  Acceptance Criteria templates). Covers the previously unguarded Step 5 of the Builder Flow.
- `keshet-builder-skills/deployment/` — Deployment skill for Stage (Step 9) and Production
  (Step 10→11). Covers pre-flight checks, smoke tests, rollback procedure, and deployment
  sign-off format.
- `keshet-builder-skills/monitoring-alerting/` — Monitoring and alerting standards for
  Production applications. Covers SLOs, health check requirements, alert definitions,
  dashboard requirements, and on-call documentation.

**New documents:**
- `docs/approved-mcp-connectors.md` — Authoritative list of org-approved MCP connectors.
  Referenced by `architecture`, `security`, and `audit-logging` skills. Required to be
  updated when a new connector is approved.
- `docs/incident-response.md` — Security incident response procedure. Covers P1–P4
  severity levels, escalation contacts, containment steps, notification obligations,
  and post-incident review format.

**New templates:**
- `templates/.claudeignore.example` — Standard `.claudeignore` for Keshet projects.
  Referenced by `context-hygiene` skill. Copy to project root as `.claudeignore`.

### Fixed

- `templates/global.CLAUDE.md` — Corrected all skill paths. Previous paths were missing
  the `keshet-claude-skills/` subfolder, causing silent skill-load failures after the
  standard `git clone` install. All paths now match the README installation instructions.
- `templates/global.CLAUDE.md` — Added Windows path note (`%USERPROFILE%\.claude\`).
- `templates/project.CLAUDE.md.template` — Replaced all `[path]` placeholders with
  resolved paths matching the standard install location. Added Windows path comment.
  Added new skills (spec-pack, deployment, monitoring-alerting) to active skills section.
  Clarified Builder Flow status placeholders with examples.

### Changed

- `claude-enterprise-skills/context-hygiene/SKILL.md` — Added YAML frontmatter
  (`name`, `description`) to match the format of builder skills and enable reliable
  skill discovery.
- `claude-enterprise-skills/output-discipline/SKILL.md` — Added YAML frontmatter.
- `claude-enterprise-skills/prompt-caching/SKILL.md` — Added YAML frontmatter.
- `claude-enterprise-skills/agentic-loop-guard/SKILL.md` — Added YAML frontmatter.
- `claude-enterprise-skills/batch-detector/SKILL.md` — Added YAML frontmatter.
- `keshet-builder-skills/README.md` — Added new skills to flow mapping table and
  skill summary.
- `CLAUDE.md` (repo root) — Updated directory tree to reflect new skills.
- `README.md` — Updated directory tree, skill execution order, Builder Flow mapping
  table, and added `docs/` references.

### Removed

- Nothing removed in this release.

---

## [1.0.0] — June 2026 (initial release)

### Added

- `claude-enterprise-skills/` — 6 FinOps skills:
  - `model-router-skill/` — tier-based model routing (Haiku / Sonnet / Opus)
  - `context-hygiene/` — token budget enforcement and `.claudeignore` patterns
  - `output-discipline/` — diffs over full files, proportional responses
  - `prompt-caching/` — 90% discount via Anthropic prompt cache
  - `agentic-loop-guard/` — checkpoint and hard-stop rules for autonomous agents
  - `batch-detector/` — 50% discount via Batch API routing

- `keshet-builder-skills/` — 8 mandatory quality gate skills:
  - `security/` — secrets, auth, input validation, dependencies, deployment config
  - `architecture/` — layered structure, tech selection, anti-patterns
  - `db-structure/` — schema standards, naming conventions, migrations, indexing
  - `code-review/` — 5-dimension review (correctness, security, maintainability, performance, tests)
  - `documentation/` — CLAUDE.md, README, inline docs, API docs, runbook
  - `unit-test/` — AAA pattern, coverage requirements, mocking rules
  - `audit-logging/` — structured logs, audit trail, PII rules, SIEM routing
  - `memory/` — session memory, decision log, project state tracking

- `company-agent-guardrails/` — app-agnostic AI agent safety rules

- `templates/` — `global.CLAUDE.md` and `project.CLAUDE.md.template`

- Root: `CLAUDE.md`, `README.md`, `.gitignore`

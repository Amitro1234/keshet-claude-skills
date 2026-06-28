# CHANGELOG — keshet-claude-skills

All notable changes to this skills library are recorded here.
Format: newest entry first. Review cycle: quarterly (or after any policy or pricing update).

Owner: AI Architecture (Amit Rosen, CIO division)

---

## [2.1.1] — June 2026

### Fixed

- `tools/validate-skills.ps1` — re-saved as UTF-8 **with BOM**. Without it, Windows
  PowerShell 5.1 (the Builder default) read the file under a non-UTF-8 ANSI codepage and
  failed to parse on the em-dash / box-drawing characters, so the validator could not run
  at all. Now runs clean on PS 5.1 (18 skills, 119 checks, 0 failures).
- `company-agent-guardrails/SKILL.md` — completed the truncated "Recommended Default
  Stance" section (was cut off mid-word at "destructive system comm"); now lists full
  Deny / Ask / Monitor stances. Removed a duplicated Purpose paragraph.

### Added

- `.github/workflows/validate-skills.yml` — CI workflow running the validator on every PR
  and push to `main` via GitHub-hosted `pwsh`. Closes the "CI not wired in" known gap.

---

## [2.1.0] — June 2026

### Changed (structural quality pass — all 15 skills updated)

- All 15 `SKILL.md` files now have a `## Trigger Conditions` section in the body (was only in YAML frontmatter for many skills)
- All builder skills and `company-agent-guardrails` now have a `## What NOT to do` section
- `model-router`: updated Tier 3 model from `claude-opus-4-7` → `claude-opus-4-8` (5 occurrences); added platform note to Step 4 (CLI vs Cowork/Chat model picker)
- `prompt-caching`: added platform compatibility note (applies to API integrations only, not interactive sessions or Cowork)
- `batch-detector`: added platform compatibility note (CLI pipeline builders only)
- `company-agent-guardrails`: added `## Purpose` section and restructured to match standard skill format
- `memory`: updated Session End output block to include `VERDICT: PASS` for validator compliance
- `spec-pack`: updated review output block to include `VERDICT: PASS/FAIL` keyword
- `docs/skills-gap-fixes.md`: source gap analysis document added to `docs/`

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

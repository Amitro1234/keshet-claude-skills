# Keshet — Global Claude Code Configuration
# File: ~/.claude/CLAUDE.md
# Install (macOS/Linux): copy this file to ~/.claude/CLAUDE.md
# Install (Windows):     copy this file to %USERPROFILE%\.claude\CLAUDE.md
# Skills root (macOS/Linux): ~/.claude/skills/keshet-claude-skills/
# Skills root (Windows):     %USERPROFILE%\.claude\skills\keshet-claude-skills\
# Owner: AI Architecture (Amit Rosen)
# Last updated: June 2026

---

## Who you are working with

You are assisting a Keshet Builder — a developer or technical employee building
applications, automations, or AI agents on the Keshet Vibe Coding platform.

All builds must pass through the Keshet Builder Flow (11 steps with gates).
Do not skip steps. Do not advance past a gate without running the required skills.

---

## Model Selection (mandatory — run before every task)

Before starting ANY task, classify it and announce the tier and model:

| Tier | Model | When |
|---|---|---|
| 1 — Light | see `claude-enterprise-skills/_shared/model-tiers.md` | Read files, run tools, grep, lint, bash, git ops |
| 2 — Standard | see `claude-enterprise-skills/_shared/model-tiers.md` | Write code, fix bugs, refactor, tests, debug, review, specs |
| 3 — Heavy | see `claude-enterprise-skills/_shared/model-tiers.md` | Architecture, security audit, greenfield design, Stage→Prod gate |

Default when uncertain: **Tier 2** — current pinned model ID is in `claude-enterprise-skills/_shared/model-tiers.md`, not hardcoded here, so this file never goes stale when a model ships.

Extended routing rules: `~/.claude/skills/keshet-claude-skills/claude-enterprise-skills/model-router-skill/SKILL.md`

---

## Active Global Skills

The following skills are active on all projects on this machine.
Load and apply them at the relevant trigger points — do not wait to be asked.

### FinOps (always active)
- Model routing:     `~/.claude/skills/keshet-claude-skills/claude-enterprise-skills/model-router-skill/SKILL.md`
- Context hygiene:   `~/.claude/skills/keshet-claude-skills/claude-enterprise-skills/context-hygiene/SKILL.md`
- Output discipline: `~/.claude/skills/keshet-claude-skills/claude-enterprise-skills/output-discipline/SKILL.md`
- Agentic loop guard:`~/.claude/skills/keshet-claude-skills/claude-enterprise-skills/agentic-loop-guard/SKILL.md`

### FinOps (pipeline/automation builders only)
These skills apply when building API integrations, automations, or bulk-processing pipelines.
They do not apply to interactive coding sessions.
- Prompt caching:    `~/.claude/skills/keshet-claude-skills/claude-enterprise-skills/prompt-caching/SKILL.md`
- Batch detector:    `~/.claude/skills/keshet-claude-skills/claude-enterprise-skills/batch-detector/SKILL.md`

### Builder Gates (trigger at relevant Build Flow steps)
- Security:          `~/.claude/skills/keshet-claude-skills/keshet-builder-skills/security/SKILL.md`
- Architecture:      `~/.claude/skills/keshet-claude-skills/keshet-builder-skills/architecture/SKILL.md`
- DB Structure:      `~/.claude/skills/keshet-claude-skills/keshet-builder-skills/db-structure/SKILL.md`
- Code Review:       `~/.claude/skills/keshet-claude-skills/keshet-builder-skills/code-review/SKILL.md`
- Documentation:     `~/.claude/skills/keshet-claude-skills/keshet-builder-skills/documentation/SKILL.md`
- Unit Test:         `~/.claude/skills/keshet-claude-skills/keshet-builder-skills/unit-test/SKILL.md`
- Audit & Logging:   `~/.claude/skills/keshet-claude-skills/keshet-builder-skills/audit-logging/SKILL.md`
- Memory:            `~/.claude/skills/keshet-claude-skills/keshet-builder-skills/memory/SKILL.md`
- Spec Pack:         `~/.claude/skills/keshet-claude-skills/keshet-builder-skills/spec-pack/SKILL.md`
- Deployment:        `~/.claude/skills/keshet-claude-skills/keshet-builder-skills/deployment/SKILL.md`
- Monitoring:        `~/.claude/skills/keshet-claude-skills/keshet-builder-skills/monitoring-alerting/SKILL.md`

### Guardrails (always active)
- Agent guardrails:  `~/.claude/skills/keshet-claude-skills/company-agent-guardrails/SKILL.md`

---

## Security Rules (non-negotiable)

- Never read, display, or include `.env` files or any file containing credentials in context
- Never write secrets inline in code — always load from environment variables
- Never run `git push` without explicit user confirmation
- Never execute destructive shell commands (rm -rf, DROP TABLE, etc.) without confirmation
- Never access paths outside the current project directory
- Never install packages without the user seeing what is being installed
- If uncertain whether an action is safe: ask, do not proceed

---

## Builder Flow — Step Reference

When a Builder is working on a project, track which step they are on:

| Step | Gate condition before advancing |
|---|---|
| 1. Access Request | Manager approval |
| 2. Local environment | Tooling verified |
| 3. Repo provisioning | From org template, not blank |
| 4. Ticket & documentation | Spec Pack ticket created |
| 5. Spec Pack | PRD + Technical Spec + AC complete |
| 6. Spec approval | Champion/Owner signed off |
| **7. Build** | **All mandatory skills active** |
| **8. Validation Sandbox** | **Code review + security + unit tests PASS** |
| 9. Stage deployment | deployment skill + smoke tests + integration tests PASS |
| **10. Stage→Prod Gate** | **6-condition gate — Tier 3 model, Champion approval** |
| 11. Production monitoring | audit-logging + monitoring-alerting skills active |

---

## Cost Awareness

- Current per-model pricing lives in `claude-enterprise-skills/_shared/model-tiers.md` only — not repeated here, so this file can't drift out of sync with it (see the "Model Selection" section above for why)
- Haiku (Tier 1) — use for all execution tasks
- Sonnet (Tier 2) — use for all reasoning tasks
- Opus (Tier 3) — use only for architecture, security audit, Prod gate
- Prompt cache reads: ~90% cheaper than non-cached — mark Spec Pack and CLAUDE.md for caching
- Batch API: 50% cheaper — route all non-interactive jobs there

At end of every session over 30 minutes: offer to generate a `.claudeignore` and a session summary.

---

## Behavior

- State the model tier before every task
- Run mandatory skills at their trigger points without being asked
- Checkpoint every 10 tool calls in agentic sessions
- Never proceed past a Builder Flow gate without running the required gate skills
- Keep responses proportional — diffs over full files, no padding

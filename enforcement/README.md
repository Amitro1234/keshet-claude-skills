# Keshet Rules — Enforcement Layer

This folder is the technical half of `docs/rules-policy.md`. The policy doc says *what* is required; this folder is *how much of it can actually be enforced, and with what config* — verified against current Claude Code hooks/permissions documentation (2026-07-01).

## Why two documents, not one

A rule that's only written in `CLAUDE.md` is an instruction Claude reads and (almost always) follows — but nothing stops a Builder from deleting that line, or Claude from making a judgment call under pressure. A rule enforced here is checked by Claude Code itself, independent of what any prompt says. `docs/rules-policy.md` states the org's actual policy; this folder implements the subset of it that's genuinely enforceable, and is explicit about the subset that isn't.

## The three enforcement tiers (weakest to strongest)

| Tier | Where it lives | Who can change it | Can a Builder bypass it? |
|---|---|---|---|
| **Instruction-level** | `CLAUDE.md`, skill files, system prompt | Anyone who can edit those files | Yes — it's guidance, not enforcement |
| **Project settings** | `.claude/settings.json` + `.claude/hooks/` in each Builder repo (`project-settings.example.json` here) | The Builder, but changes are visible in git history / PRs | Technically yes (they own the file), but it's auditable |
| **Managed settings** | (a) `managed-settings.json` on disk, pushed via any IT tooling (Intune/GPO/Jamf) — **works on any Claude plan, including Team**; or (b) server-managed push from the claude.ai admin console — requires Team or Enterprise, Team already qualifies | Only whoever controls IT deployment or the admin console (Admin Panel Owner / CISO) | **No** — this is the one tier Claude Code itself will not let a Builder override |

Only the managed tier is "cannot be bypassed" in the strict sense. Project-tier settings.json rules are still real enforcement (Claude Code itself blocks the action, not just a suggestion) — they're just editable by the person they're meant to constrain, so use them for things where visibility/audit is the goal, and reserve the managed tier for anything that must hold even against a compromised or careless Builder machine.

## What's genuinely hard-enforceable today, and what isn't

Verified against Claude Code's hooks and permissions docs:

- **Hard, via `permissions.deny` + managed settings:** blocking specific file-read patterns (`.env`, `.ssh/**`, `.aws/**`), blocking specific Bash command patterns (`git push --force`, `sudo *`, `curl | sh`), enforcing an MCP server allowlist (`allowedMcpServers` / `deniedMcpServers`).
- **Hard, via a `PreToolUse` hook (`pre_tool_use_guard.py`):** semantic checks a glob can't express — e.g. `cat .env` isn't a `Read` tool call, it's a `Bash` call, so the file-glob deny rule doesn't catch it; the hook inspects the command string instead. Same for MCP-tool-level allowlisting (a server can be "approved" but a specific tool on it might still need review) and destructive commands with unusual syntax.
- **Partially hard:** anything syntactic can be worked around by a sufficiently motivated Claude finding an alternate syntax (Python's `os.remove` instead of `rm`, a different MCP server that does the same thing). Layering settings.json + hooks closes most, not all, of this gap. This is exactly the limitation `company-agent-guardrails/SKILL.md` already states in its own text ("guardrail files guide behavior but do not enforce it at the OS level") — the hooks/settings layer is what actually closes part of that gap, but not all of it.
- **Not enforceable at all today, anywhere:** "announce the model tier before starting work" (`model-router-skill`'s core behavior) — there's no hook that fires at "before Claude starts reasoning about a task," only before/after specific tool calls. This stays instruction-level no matter what. Same for most of the FinOps skills' actual guidance (context hygiene, output discipline) — they shape *how* Claude behaves, not *what tools* it's allowed to call, so hooks/permissions have nothing to grab onto.
- **Cowork and Claude.ai Chat have neither hooks nor settings.json.** Everything in this folder applies to Claude Code CLI on Builder machines only. For Cowork/Safe-Use users, the only real technical enforcement points are: which MCP connectors are enabled for their workspace (an admin-console setting, not a file here), and the sandboxed-VM isolation Cowork already provides by default. Everything else for that population is instruction-level (`CLAUDE.md`, skill guidance) — see `docs/rules-policy.md` §4 for what that means in practice.

## Files here

- `managed-settings.example.json` — deploy via IT tooling (any plan) or Claude admin console (Team+). Locks the MCP allowlist and the hard security denies org-wide.
- `project-settings.example.json` — ship this as the default `.claude/settings.json` in the org repo template (Builder Flow Step 3), covers the "Ask" tier (git push, deploys, installs, migrations) plus wires in the hook below.
- `hooks/pre_tool_use_guard.py` — the semantic hook referenced from `project-settings.example.json`. Copy to `.claude/hooks/pre_tool_use_guard.py` in the org template repo.
- `tests/test_pre_tool_use_guard.py` — real, automated, repeatable tests for the hook above (19 cases; run with `python3 tests/test_pre_tool_use_guard.py` or via pytest). Includes one intentional `xfail` documenting a known bypass (obfuscated `.env` reads via inline Python) rather than hiding it. **Run this after every edit to the hook or to `docs/approved-mcp-connectors.md`.**
- `tests/behavioral-scenarios.md` — the non-executable counterpart: scenario tests for skills that are advisory-only (no hook/settings.json backing). 3 scenarios validated 2026-07-01 (security-secret-catch, spec-pack-gate, model-router+connector-block — all passed), 4 more scaffolded for the next pass.

## Open items before this is production-ready

1. **MCP allowlist duplication risk:** the approved-connector list is now hand-maintained in three places — `docs/approved-mcp-connectors.md` (source of truth), `managed-settings.example.json`, and `pre_tool_use_guard.py`. If one is updated and the others aren't, they drift silently. Worth writing a small script that generates the JSON/Python list from the markdown table so there's one source of truth — flagging this rather than building it now, since it's a repo-tooling decision, not a policy one.
2. **Schema verification:** the exact hook stdin JSON shape and the managed-settings key names were verified against Claude Code docs as of 2026-07-01 but this is an area that changes; confirm against `https://code.claude.com/docs/en/hooks` and `https://code.claude.com/docs/en/admin-setup` before deploying to real Builder machines, and definitely before deploying the managed tier (a typo'd key there could silently do nothing rather than error).
3. **The hook itself is now unit-tested (`tests/test_pre_tool_use_guard.py`, 19/19 passing) and 3 of the advisory skills have been behaviorally validated (`tests/behavioral-scenarios.md`)** — but none of this has run inside a real Claude Code CLI session on an actual Builder machine yet, only via direct subprocess calls and simulated sessions. Recommend a dry run on one Builder machine (`.claude/settings.json` only, no managed tier yet) before wider rollout.

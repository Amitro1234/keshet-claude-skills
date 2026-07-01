# Company Agent Guardrails — Reference

Default policy categories and file-placement paths for
`company-agent-guardrails/SKILL.md`. Load this file when drafting or
auditing an actual guardrail set — the core SKILL.md covers the workflow and
default stance on their own.

---

## Default Policy Categories

Use these categories as the baseline:

- **Sensitive data:** `.env*`, tokens, API keys, private keys, SSH, cloud credentials, kubeconfigs, Docker credentials, CI/CD secrets.
- **Destructive shell:** recursive delete, disk formatting, permission recursion, mass overwrite, history deletion, process killing, service disabling.
- **Exfiltration:** file uploads, POST/PUT with local files, paste sites, pipe-to-shell, encoded payloads, reverse shells, metadata service access.
- **Workspace boundary:** reads/writes outside the active project, especially user home, OS config, credential stores, and other repos.
- **Persistence:** shell startup files, scheduled tasks, login items, registry run keys, git hooks, package manager scripts, agent hooks.
- **Agent configuration:** MCP server config, skills, plugins, slash commands, global instructions, sandbox or permission settings.
- **Git safety:** force push, hard reset, branch/tag deletion, protected branch pushes, credential changes in remotes.

## Placement Guide

Use the app's native mechanism, but keep the wording portable:

- Cursor personal skill: `~/.cursor/skills/company-agent-guardrails/SKILL.md`
- Cursor project rule: `.cursor/rules/company-agent-guardrails.mdc`
- Cursor project skill: `.cursor/skills/company-agent-guardrails/SKILL.md`
- Claude personal skill: `~/.claude/skills/company-agent-guardrails/SKILL.md`
- Claude project instructions: `CLAUDE.md`
- Generic project fallback: `AGENTS.md` or `docs/agent-guardrails.md`

For stronger enforcement, prefer the app's hook or permission system when
available — e.g. Claude Code hooks can block some tool calls before
execution, while instruction-only files are advisory.

## Platform compatibility

- Claude Code CLI: full support — guidance applies, and Claude Code's own hook/permission system can additionally enforce some of these rules at the shell level
- Cowork: full support — guidance applies the same way; Cowork cannot run shell-level enforcement, so these rules rely on the agent following them
- Claude.ai Chat: full support — same limitation as Cowork, no shell-level enforcement available

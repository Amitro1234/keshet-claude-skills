---
name: company-agent-guardrails
description: Draft, review, and refine app-agnostic company guardrails for AI coding agents. Use when the user asks for agent safety rules, Claude or Cursor skills, MCP policies, secret-handling policy, destructive-command policy, hooks, or Prempti-inspired controls.
---

# Company Agent Guardrails

## Purpose

Define and enforce practical safety guardrails for AI coding agents across Keshet.
These guardrails reduce accidental harm and improve visibility without blocking
developer productivity. They apply to all agents operating in Claude Code, Cowork,
and any pipeline or automation using Claude.

The goal is not sandbox-grade security — it is to make dangerous actions visible
and require explicit human confirmation before they execute.

---

## Trigger Conditions

This skill is **always active** for any AI agent session. Activate explicitly when:
- A new Claude Code session starts on any Keshet project
- An agent is about to execute shell commands, git operations, or MCP tool calls
- A user grants broad autonomy ("just handle it", "do it automatically")
- A pipeline or automation is being designed or reviewed
- Any action would touch secrets, credentials, or files outside the project directory

---

Use this skill to create practical guardrails for AI coding agents across desktop apps and CLIs. The goal is to reduce accidental harm and improve visibility, not to claim sandbox-grade security.

## First Principles

1. Identify the action surface: shell commands, file reads/writes, git operations, MCP calls, package installs, hooks, skills, or secrets.
2. Classify each control as `deny`, `ask`, `monitor`, or `guidance`.
3. Prefer small, explicit rules over broad vague rules.
4. Preserve developer productivity by asking on ambiguous actions and denying only clearly unsafe actions.
5. State limitations clearly: rules, skills, and instruction files guide agent behavior; hooks and endpoint tools can enforce more, but they still are not a full OS sandbox unless paired with real containment.

## Default Policy Categories

Use these categories as the baseline:

- Sensitive data: `.env*`, tokens, API keys, private keys, SSH, cloud credentials, kubeconfigs, Docker credentials, CI/CD secrets.
- Destructive shell: recursive delete, disk formatting, permission recursion, mass overwrite, history deletion, process killing, service disabling.
- Exfiltration: file uploads, POST/PUT with local files, paste sites, pipe-to-shell, encoded payloads, reverse shells, metadata service access.
- Workspace boundary: reads/writes outside the active project, especially user home, OS config, credential stores, and other repos.
- Persistence: shell startup files, scheduled tasks, login items, registry run keys, git hooks, package manager scripts, agent hooks.
- Agent configuration: MCP server config, skills, plugins, slash commands, global instructions, sandbox or permission settings.
- Git safety: force push, hard reset, branch/tag deletion, protected branch pushes, credential changes in remotes.

## Rule Drafting Workflow

When asked to create guardrails:

1. Ask where the rule should live: personal user config, project-shared config, or both.
2. Ask what should happen for each category: block, ask, monitor, or allow.
3. Draft the smallest useful rule set.
4. Include examples of actions that trigger the rule.
5. Include known limitations and what still requires sandboxing, endpoint controls, or least privilege.
6. If writing files, use the target app's native location and keep the policy content app-agnostic.

## Placement Guide

Use the app's native mechanism, but keep the wording portable:

- Cursor personal skill: `~/.cursor/skills/company-agent-guardrails/SKILL.md`
- Cursor project rule: `.cursor/rules/company-agent-guardrails.mdc`
- Cursor project skill: `.cursor/skills/company-agent-guardrails/SKILL.md`
- Claude personal skill: `~/.claude/skills/company-agent-guardrails/SKILL.md`
- Claude project instructions: `CLAUDE.md`
- Generic project fallback: `AGENTS.md` or `docs/agent-guardrails.md`

For stronger enforcement, prefer the app's hook or permission system when available. For example, Claude Code hooks can block some tool calls before execution, while instruction-only files are advisory.

## Recommended Default Stance

Use this unless the company provides a stricter policy:

- Deny: secret exfiltration, pipe-to-shell, sandbox disable, destructive system comm

## What NOT to do

- Do not install MCP servers, hooks, or persistent services without explicit user approval
- Do not read, display, or pass `.env` files or credential files into any context
- Do not execute destructive shell commands (`rm -rf`, `DROP TABLE`, disk format) without confirmation
- Do not push to git or deploy without the user seeing exactly what will be pushed
- Do not access file paths outside the current project directory
- Do not silently retry failed operations — always surface failures to the user
- Do not treat instruction-only guardrail files as OS-level enforcement — they guide behavior, they do not sandbox it
- Do not install third-party agent tools from unverified sources without a security review


---

## Output Template

When proposing a guardrail set, always respond with:

```markdown
## Guardrail Summary
<short summary of what is being protected>

## Policies
- Deny:    <actions that are blocked outright>
- Ask:     <actions that require explicit user confirmation>
- Monitor: <actions that are logged and visible but not blocked>

## Files To Create Or Update
- `<path>`: <purpose of this file>

## Limitations
<what these guardrails do NOT enforce — what requires additional sandboxing or endpoint controls>
```
## Safety Notes

Do not install endpoint agents, hooks, MCP servers, or persistent services without explicit user approval. For third-party tools like Prempti, cloning source for review is lower risk than installing release artifacts; installing should go through security review, checksum verification, and a pilot environment.

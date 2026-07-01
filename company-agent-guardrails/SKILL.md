---
name: company-agent-guardrails
description: >
  Use when drafting, reviewing, or refining AI agent safety rules — secret-handling,
  destructive-command, or MCP policy — for Claude, Cursor, or similar coding agents.
---

# Company Agent Guardrails

## Purpose

Define and enforce practical safety guardrails for AI coding agents across
Keshet — visible, human-confirmed control over dangerous actions, not
sandbox-grade security. Applies to all agents in Claude Code, Cowork, and
any pipeline or automation using Claude. Default policy categories and
per-app file placement paths live in `reference.md`.

---

## Trigger Conditions

Always active for any AI agent session. Activate explicitly when: a new
session starts on a Keshet project, an agent is about to run shell/git/MCP
calls, a user grants broad autonomy ("just handle it"), a pipeline is being
designed or reviewed, or an action would touch secrets or files outside the
project directory.

---

## First Principles

1. Identify the action surface: shell, file reads/writes, git, MCP calls, package installs, hooks, skills, secrets.
2. Classify each control as `deny`, `ask`, `monitor`, or `guidance`.
3. Prefer small, explicit rules over broad vague ones.
4. Preserve developer productivity — ask on ambiguous actions, deny only clearly unsafe ones.
5. State limitations clearly: instruction files guide behavior; hooks/endpoint tools enforce more, but neither is a full OS sandbox without real containment.

## Rule Drafting Workflow

1. Ask where the rule should live: personal config, project-shared config, or both.
2. Ask what should happen per category: block, ask, monitor, or allow.
3. Draft the smallest useful rule set.
4. Include examples of actions that trigger the rule.
5. Include known limitations — what still needs sandboxing or endpoint controls.
6. If writing files, use the target app's native location; keep policy wording app-agnostic.

## Recommended Default Stance

Use this unless the company provides a stricter policy:

- **Deny:** secret exfiltration, pipe-to-shell (`curl ... | sh`), sandbox/permission disable, destructive system commands (recursive delete, disk format, history wipe), credential-store access.
- **Ask:** git push/force-push, deploys, package installs, schema changes, writes outside the project directory, any MCP tool call not on the org-approved list.
- **Monitor:** all shell execution, in-project file writes, external API calls — logged and visible, not blocked.

## What NOT to do

- Do not install MCP servers, hooks, or persistent services without explicit user approval
- Do not read, display, or pass `.env` files or credential files into any context
- Do not execute destructive shell commands without confirmation
- Do not push to git or deploy without the user seeing exactly what will be pushed
- Do not access file paths outside the current project directory
- Do not silently retry failed operations — always surface failures
- Do not treat instruction-only guardrail files as OS-level enforcement
- Do not install third-party agent tools from unverified sources without a security review — prefer reviewing source over installing prebuilt release artifacts, and route installs through checksum verification and a pilot environment

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

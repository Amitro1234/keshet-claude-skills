# Keshet — Approved MCP Connectors

This is the authoritative list of MCP (Model Context Protocol) connectors approved for
use in Keshet Builder projects. Claude and AI agents must only invoke tools from
connectors on this list. Any connector not listed here requires a security review before
use in any Builder project.

**Owner:** AI Architecture (Amit Rosen, CIO division)
**Review cycle:** Quarterly, or after any new connector request
**Last updated:** June 2026

---

## How to Read This List

| Column | Meaning |
|---|---|
| Connector | MCP server name as configured in Claude Code |
| Purpose | What it does |
| Data Classification | Maximum data level it may handle |
| Scope | Read-only / Read-write / Execute |
| Approved for | Which project categories may use it |
| Notes | Restrictions or conditions |

---

## Approved Connectors

### Productivity & Communication

| Connector | Purpose | Data Class | Scope | Approved for | Notes |
|---|---|---|---|---|---|
| `slack` | Send messages, read channels | 🟡 Internal | Read-Write | Department Tool, Production | No DMs; only approved channels. Never send 🔴 Confidential data. |
| `microsoft-teams` | Send messages to Teams channels | 🟡 Internal | Write | Department Tool, Production | Same restrictions as Slack. |
| `sharepoint` | Read/write SharePoint documents and lists | 🟡 Internal | Read-Write | Department Tool, Production | Requires site-level permission review before use. |
| `outlook-calendar` | Read calendar availability | 🟡 Internal | Read | Department Tool | Read-only. No writes without Champion approval. |

### Project & Task Management

| Connector | Purpose | Data Class | Scope | Approved for | Notes |
|---|---|---|---|---|---|
| `monday` | Read/write Monday.com boards and items | 🟡 Internal | Read-Write | Department Tool, Production | Do not write 🔴 Confidential data to Monday items. |
| `jira` | Read issues, update status, create tickets | 🟡 Internal | Read-Write | Production | Production only — department tools use Monday. |
| `github` | Read repos, open PRs, comment on issues | 🟡 Internal | Read-Write | All | Force push, branch deletion: always ask user first. |

### Data & Storage

| Connector | Purpose | Data Class | Scope | Approved for | Notes |
|---|---|---|---|---|---|
| `postgresql` | Query and write Keshet internal databases | 🔴 Confidential | Read-Write | Production | Requires Champion approval per-project. DLP must be active. |
| `azure-blob-storage` | Read/write files in approved storage accounts | 🟡 Internal | Read-Write | Production | Only org-provisioned storage accounts. |
| `excel-sheets` | Read/write Excel/Sheets files | 🟡 Internal | Read-Write | Department Tool | No 🔴 Confidential data in spreadsheets. |

### AI & Search

| Connector | Purpose | Data Class | Scope | Approved for | Notes |
|---|---|---|---|---|---|
| `azure-ai-search` | Semantic search over internal content | 🟡 Internal | Read | All | Read-only. |
| `context7` | Fetch library and framework documentation | 🟢 Public | Read | All | Public docs only — do not pass internal data to Context7. |

### Development & Infrastructure

| Connector | Purpose | Data Class | Scope | Approved for | Notes |
|---|---|---|---|---|---|
| `filesystem` | Read/write files in the project directory | 🟡 Internal | Read-Write | All | Scoped to project root only. Never access paths outside the project. |
| `git` | Run git operations | 🟡 Internal | Execute | All | Force push and hard reset: always ask user. Never auto-push. |
| `azure-devops` | CI/CD pipeline status, build triggers | 🟡 Internal | Read-Write | Production | Triggering production deployments requires Champion approval. |

---

## Requesting a New Connector

To add a new MCP connector to this list:

1. Open a ticket on the AI Architecture Monday board: **"MCP Connector Review Request"**
2. Include:
   - Connector name and source (GitHub URL or registry)
   - What data it will access (classification level)
   - What scope it needs (read / write / execute)
   - Which projects need it
3. AI Architecture will review within **5 business days**
4. Security review is required for any connector that:
   - Accesses 🔴 Confidential data
   - Has Execute scope on production infrastructure
   - Is not from a major vendor (Microsoft, Atlassian, GitHub, etc.)

---

## Enforcement

Claude and AI agents must enforce this list at two points:

1. **`architecture/SKILL.md`** — checks that all connectors in the design are on this list
2. **`security/SKILL.md`** — checks that MCP tool calls are only to approved connectors
3. **`audit-logging/SKILL.md`** — every MCP tool call must be logged (who, when, what was passed)

If a task requires a connector not on this list, Claude must:

```
CONNECTOR NOT APPROVED: [connector name]
This connector is not on the Keshet approved connector list.
Required action: submit an MCP Connector Review Request before proceeding.
See: docs/approved-mcp-connectors.md
```

Do not proceed with an unapproved connector without explicit Champion and AI Architecture sign-off.

---

## Connector Security Rules (all connectors)

Regardless of which approved connector is used:

- Never pass 🔴 Confidential data to a connector without confirming DLP is active
- Never store credentials for a connector in code — use environment variables or Key Vault
- Never grant a connector more scope than the task requires
- Every connector call must be logged per the `audit-logging` skill
- If a connector call fails 3 times, stop and surface the failure to the user — do not retry silently

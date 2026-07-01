---
name: keshet-security
description: >
  Mandatory security checklist for Keshet Builders. Run at every Build session (Step 7)
  and before every gate crossing (Steps 8, 10). Triggers on: any code that handles
  credentials, API keys, user data, database access, external integrations, authentication,
  or deployment to Stage/Production. Non-negotiable — cannot be skipped.
---

# Security Skill — Keshet Builder Mandatory

## Purpose

Every application built through the Keshet Vibe Coding platform must pass a security
review before advancing in the Builder Flow. This skill enforces that review at build time,
catching issues before they reach the Agent Validation Sandbox (Step 8) or the
Stage→Production gate (Step 10).

This is a **mandatory skill** — it runs on every Builder session, not only when the
user requests it.

> **Platform compatibility:**
> - Claude Code CLI: ✅ Full support — can run `npm audit`, `pip-audit`, and grep for secrets directly
> - Cowork: ✅ Full support — review and checklist apply; run audit commands separately in terminal
> - Claude.ai Chat: ✅ Supported — paste code for review; run audit commands separately

---

## Trigger Conditions

Activate automatically when the code under review includes any of:

- Credentials, API keys, tokens, passwords, or secrets
- Database connections, queries, or ORM models
- HTTP requests to external services or internal APIs
- File system operations outside the project directory
- User authentication or authorization logic
- Logging of any kind (check for PII in log output)
- Environment variable handling
- Deployment configuration (docker-compose, k8s manifests, CI/CD)
- MCP server configuration or tool definitions
- Any data classified as 🔴 Confidential

---

## Mandatory Security Checks

Run ALL of the following before marking a build as ready for Step 8.

### Check 1: Secret Exposure

```
SECURITY CHECK — SECRETS
```

- [ ] No hardcoded credentials in any file (API keys, passwords, tokens, connection strings)
- [ ] All secrets loaded from environment variables or a secrets manager — never inline
- [ ] `.env` files are listed in `.gitignore` — confirmed present
- [ ] No secrets in comments, log statements, or error messages
- [ ] No secrets in test fixtures or mock data

**If any check fails:** STOP. Do not proceed. Flag as `SECURITY_BLOCK: SECRET_EXPOSURE`.

### Check 2: Data Classification Compliance

```
SECURITY CHECK — DATA CLASSIFICATION
```

Refer to the Keshet Data Classification policy:

| Level | What's in the code | Required controls |
|---|---|---|
| 🟢 Public | Public content, marketing data | None beyond standard |
| 🟡 Internal | Business data, internal processes | Logging review, access control |
| 🔴 Confidential | Employee data, contracts, customer PII, financial | DLP active, audit logging, CISO approval before Prod |

- [ ] Data classification level identified and documented in the Spec Pack
- [ ] Code handles data at or below the declared classification level
- [ ] 🔴 Confidential data: confirm DLP is active and CISO notified

### Check 3: Input Validation

```
SECURITY CHECK — INPUT VALIDATION
```

- [ ] All user inputs validated before use (type, length, format, range)
- [ ] No direct string interpolation into SQL queries — use parameterized queries or ORM
- [ ] No `eval()`, `exec()`, or dynamic code execution on user input
- [ ] File path inputs sanitized — no path traversal (`../`) possible
- [ ] Webhook payloads validated and authenticated before processing

### Check 4: Authentication & Authorization

```
SECURITY CHECK — AUTH
```

- [ ] Every endpoint / route has an explicit authorization check
- [ ] No "admin by default" or "open by default" endpoints
- [ ] Tokens expire — no eternal sessions
- [ ] Failed authentication attempts are logged (but not with the attempted password)
- [ ] MCP tools: only tools in the org-approved connector list are invoked (see `docs/approved-mcp-connectors.md`)

### Check 5: Logging Safety

```
SECURITY CHECK — LOGGING
```

- [ ] No PII in log output (names, emails, phone numbers, IDs, IP addresses without masking)
- [ ] No credentials or tokens in log output — even partial
- [ ] Log level is appropriate: DEBUG logs are not active in Production
- [ ] Logs route to the org's approved logging infrastructure — not to external services

### Check 6: Dependency Safety

```
SECURITY CHECK — DEPENDENCIES
```

- [ ] All packages installed from the org-approved package registry or public registries
- [ ] No unpinned wildcard versions in `package.json` or `requirements.txt`
- [ ] No `npm install <url>` or `pip install <git+url>` without security review
- [ ] Run `npm audit` / `pip-audit` — no HIGH or CRITICAL vulnerabilities unresolved

### Check 7: Deployment Config

```
SECURITY CHECK — DEPLOYMENT
```

- [ ] Secrets injected via environment variables — not baked into Docker image or CI config
- [ ] Least-privilege IAM / service account — only permissions the app actually needs
- [ ] No production credentials in Dev or Stage environments
- [ ] Health check endpoints do not expose internal system state or versions

---

## Output Format

After running all checks, produce:

```
=== SECURITY REVIEW — [App Name] ===
Date: [date]
Builder: [name]
Step: [7 / 8 / 10]
Data Classification: [🟢/🟡/🔴]

PASSED CHECKS:
✅ [check name]
...

FAILED CHECKS:
❌ [check name] — [specific issue found]
...

VERDICT: [PASS / BLOCK]
If BLOCK: [list of issues that must be resolved before proceeding]
```

A `BLOCK` verdict means the build **cannot advance to the next step** until all issues
are resolved and the security check is re-run.

---

## Escalation Path

| Issue Type | Who to notify | SLA |
|---|---|---|
| SECRET_EXPOSURE — found in code | Security/CISO | 1 hour |
| PII in logs | Security/CISO | 1 hour |
| 🔴 Confidential data without DLP | CISO + Pipeline Maintainer | 2 hours |
| HIGH/CRITICAL dependency vulnerability | Builder + Pipeline Maintainer | Next business day |

---

## What NOT to do

- Do not skip this skill because "it's just a demo" — demos reach production
- Do not mark checks as passing without actually verifying them
- Do not log errors that include the stack trace in Production (leaks internal structure)
- Do not add secrets to `.env.example` files as "placeholder values" — use `YOUR_KEY_HERE`
- Do not store secrets in Claude's context window or in Spec Pack documents

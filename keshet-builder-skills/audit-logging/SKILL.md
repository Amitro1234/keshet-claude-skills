---
name: audit-logging
description: >
  Audit trail and logging standards for Keshet Builders. Mandatory at Build (Step 7)
  for all Production applications. Triggers on: any code that writes logs, any user action
  that changes data, any admin operation, any authentication event, any MCP tool call,
  or any external API integration. Required before Stage→Prod gate (Step 10).
---

# Audit & Logging Skill — Keshet Builder Mandatory

## Purpose

Audit logs are Keshet's paper trail. They answer: who did what, to what, when, and
from where. They are required for security incident response, compliance review, and
operations troubleshooting.

This skill enforces two distinct concerns:

1. **Application logs** — operational visibility for developers and ops
2. **Audit trail** — immutable record of business-significant events for compliance and security

Both are mandatory. They serve different consumers and must not be conflated.

> **Platform compatibility:**
> - Claude Code CLI: ✅ Full support — Claude can inspect log configuration, write structured logger setup, and verify audit entries
> - Cowork: ✅ Full support — review and logging checklist apply with connected folder
> - Claude.ai Chat: ✅ Supported — paste log output or logging code for review and standards check

---

## Trigger Conditions

Activate this skill when any of the following applies:
- Any code writes log statements of any kind
- A user action creates, updates, or deletes data
- An admin operation is performed (provisioning, config change, spend cap change)
- An authentication or authorization event occurs
- An MCP tool call is made by an AI agent
- An external API integration is added
- Advancing from Step 7 (Build) to Step 8 (Validation Sandbox)
- Advancing to Production (Step 10 gate)

---

## Two Types of Logs

| Type | Purpose | Consumer | Retention | Mutability |
|---|---|---|---|---|
| **Application log** | Debug, monitor, alert on system behavior | Developers, Ops | 30 days | Can be pruned |
| **Audit trail** | Record business-significant user/system actions | Security, Compliance, Legal | 1 year minimum | Immutable |

**Critical rule:** Application logs can be verbose and purged. Audit trail entries must
never be deleted or modified — they are the legal record.

---

## Application Logging Standards

### Log Levels

Use the correct level — do not use INFO for everything:

| Level | When to use | Example |
|---|---|---|
| `DEBUG` | Detailed diagnostic info — off in production | Function entry/exit, variable values |
| `INFO` | Significant events in normal operation | Server started, job completed |
| `WARNING` | Something unexpected but not an error | Config missing, using fallback value |
| `ERROR` | An operation failed but the service continues | API call failed, DB write failed |
| `CRITICAL` | The service cannot continue — requires immediate attention | DB unreachable, fatal config error |

Production log level must be `INFO` or higher — `DEBUG` logs must be disabled in Production.

### Structured Logging (required)

All logs must be **structured JSON** — not plain text strings.

```python
# Bad — not searchable, not parseable
logger.info(f"Processing event {event_id} for user {user_id}")

# Good — structured, every field searchable
logger.info("event_processing_started", extra={
    "event_id": event_id,
    "user_id": user_id,
    "service": "broadcast-scheduler",
    "environment": settings.ENVIRONMENT
})
```

Required fields in every log entry:
```json
{
  "timestamp": "2026-06-28T10:30:00.000Z",
  "level": "INFO",
  "service": "broadcast-scheduler",
  "environment": "production",
  "message": "event_processing_started",
  "trace_id": "abc123"
}
```

The `trace_id` links all log entries from a single request — critical for debugging.
Generate a UUID at request entry and pass it through the call chain.

### What NOT to log (PII / Secrets)

The following must **never** appear in any log:

- Passwords, tokens, API keys, session IDs
- Full names, email addresses, phone numbers, national IDs
- Financial data, salary, payment card information
- Health or medical information
- IP addresses (log hashed IP if needed for rate limiting)

If an error message from an external service contains PII, sanitize it before logging:
```python
# Bad
logger.error(f"Auth failed: {response.body}")  # may contain user data

# Good
logger.error("auth_failed", extra={"status_code": response.status_code, "provider": "okta"})
```

---

## Audit Trail Standards

### Which Events Require an Audit Entry

The following events must always generate an audit trail entry:

| Category | Events |
|---|---|
| Authentication | Login success, login failure, logout, token refresh, MFA challenge |
| Authorization | Permission denied, role change, group membership change |
| Data write | Create, Update, Delete on any 🟡 Internal or 🔴 Confidential data |
| Admin operations | User provisioning, deprovisioning, config changes, spend cap changes |
| MCP tool calls | Every tool call made by an AI agent on behalf of a user |
| Deployment | Deploy to Stage, deploy to Production, rollback |
| Data export | Any download or export of business data |

### Audit Entry Schema

Every audit entry must include all of the following:

```json
{
  "audit_id":    "uuid-v4",                   // unique per event — immutable
  "timestamp":   "2026-06-28T10:30:00.000Z",  // UTC, full precision
  "actor_id":    "user-uuid",                 // who performed the action
  "actor_type":  "human | ai_agent | system", // type of actor
  "action":      "data.update",               // namespaced verb
  "resource":    "broadcast_segment",         // what was acted on
  "resource_id": "segment-uuid",              // specific instance
  "result":      "success | failure",         // outcome
  "ip_address":  "hashed",                    // hashed, not plain
  "app":         "broadcast-scheduler",       // which application
  "environment": "production",
  "metadata":    { }                          // action-specific extras (no PII)
}
```

### Audit Entry Implementation Pattern

```python
from audit import audit_log

def update_segment(segment_id: str, payload: dict, actor: User) -> Segment:
    segment = Segment.get_by_id(segment_id)

    # Business logic
    segment.update(payload)
    segment.save()

    # Audit trail — ALWAYS after the operation, includes result
    audit_log(
        actor_id=actor.id,
        actor_type="human",
        action="broadcast.segment.update",
        resource="broadcast_segment",
        resource_id=segment_id,
        result="success",
        metadata={"fields_changed": list(payload.keys())}  # keys only, not values
    )

    return segment
```

Note: `metadata` includes field names changed — **never the old or new values**
unless those values are non-sensitive and explicitly required for the audit.

### Audit Log Storage

- Audit entries must be written to a **separate, append-only store** — not the same DB
  table as application data
- Acceptable stores: dedicated audit DB table (immutable), SIEM via API, or a
  write-once log stream (e.g., Kinesis, Azure Event Hub)
- Audit entries must never be deleted by application code — only by a compliance-approved
  retention policy
- Retention: minimum 1 year for all events; 3 years for 🔴 Confidential data events

---

## Log Infrastructure Requirements

| Requirement | Implementation |
|---|---|
| Log aggregation | Logs must route to the org's centralized logging system |
| Alerting | ERROR and CRITICAL logs must trigger an alert (PagerDuty / Slack). Escalate per the severity levels and contacts in `docs/incident-response.md`. |
| Audit trail routing | Audit entries must route to the org's SIEM or compliance system |
| Log access | Production logs: only Ops/Security roles can access — not all developers |
| No local-only logs | Do not write to files on the server disk as the primary log — use structured output to stdout, collected by the infra |

---

## Audit & Logging Review Checklist

Before advancing from Step 7 (Build) to Step 8 (Validation):

- [ ] Structured JSON logging implemented throughout (`logger.info("event", extra={...})`)
- [ ] Log levels used correctly — DEBUG disabled in Production config
- [ ] No PII, passwords, or tokens in any log statement
- [ ] All required audit events have audit trail entries (see table above)
- [ ] Audit entries include all required fields (actor, action, resource, result, timestamp)
- [ ] Audit entries written to append-only store (not a standard CRUD table that can be updated or deleted)

## What NOT to do

- Do not conflate application logs and audit trail entries — they serve different purposes and audiences
- Do not write audit entries to a standard CRUD table that can be updated or deleted
- Do not log PII (names, emails, phone numbers, IDs) in any log statement
- Do not log credentials, tokens, or API keys — even partially
- Do not use `print()` as the logging mechanism in any environment
- Do not disable DEBUG logging by commenting it out — use log level configuration
- Do not route audit entries only to local disk — use the org's centralized SIEM or audit store
- Do not omit the `trace_id` — without it, distributed request tracing is impossible


---

## Review Output

```
=== AUDIT & LOGGING REVIEW — [App Name] ===
Structured logging: [PASS / ISSUES: list]
Log level discipline: [PASS / ISSUES: list]
PII in logs: [NONE FOUND / FOUND: locations]
Audit events covered: [N/N required events]
Audit schema: [COMPLETE / MISSING FIELDS: list]
Audit storage: [APPEND-ONLY / STANDARD TABLE — must fix]

VERDICT: [PASS / NEEDS REVISION]
```

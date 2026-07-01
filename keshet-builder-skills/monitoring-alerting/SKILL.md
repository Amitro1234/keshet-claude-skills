---
name: monitoring-alerting
description: >
  Monitoring and alerting standards for Keshet Builders. Mandatory before Production
  deployment (Step 10 gate) and active throughout Step 11 (Production Monitoring).
  Triggers on: any Production application going live, any question about SLOs, alerts,
  dashboards, on-call, or rollback plans. Ensures that Production problems are detected
  within minutes, not hours.
---

# Monitoring & Alerting Skill — Keshet Builder Mandatory

## Purpose

An application without monitoring is an application that fails silently. This skill
defines the minimum monitoring and alerting configuration required before any Keshet
application reaches Production.

**Two concerns:**
1. **Monitoring** — observing what the system is doing (metrics, dashboards, SLOs)
2. **Alerting** — being woken up when something is wrong (thresholds, routing, runbook)

Both are required. An app with monitoring but no alerts means humans check dashboards
manually. An app with alerts but no monitoring means alerts fire without context.

> **Platform compatibility:**
> - Claude Code CLI: ✅ Full support — Claude can inspect monitoring config, write health check code, and generate alert definitions
> - Cowork: ✅ Full support — monitoring review and SLO definitions apply with connected folder
> - Claude.ai Chat: ✅ Supported — describe your stack; Claude generates SLO definitions, alert configs, and the health check endpoint

---

## Trigger Conditions

Activate this skill when any of the following applies:
- An application is being prepared for Production deployment (Step 10 gate)
- The user asks about SLOs, alerts, dashboards, or on-call rotation
- A new Production service is going live
- An existing Production service has no monitoring configured
- Step 11 (Production Monitoring) begins — run the daily health check

---

## Required Monitoring Layers

Every Production application must implement all three layers before Step 10.

### Layer 1: Health Check Endpoint

Every application must expose a `/health` endpoint that returns its current status.

```python
# Minimum health check
@app.get("/health")
async def health():
    # Check DB connectivity — if DB is down, return 503
    try:
        db.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False

    status = "ok" if db_ok else "degraded"
    code = 200 if db_ok else 503

    return JSONResponse(
        status_code=code,
        content={
            "status": status,
            "version": settings.APP_VERSION,
            "checks": {
                "database": "ok" if db_ok else "unreachable"
            }
        }
    )
```

Rules:
- `/health` must **not** require authentication
- `/health` must **not** return internal system details (stack traces, connection strings)
- `/health` must return `200` only if the service is fully operational
- Response time for `/health` must be under **500ms** at all times

### Layer 2: Application Metrics

Instrument the application to emit the following metrics:

| Metric | Type | What to measure |
|---|---|---|
| `http_requests_total` | Counter | All HTTP requests, labelled by method, route, status code |
| `http_request_duration_seconds` | Histogram | Response time per route — measure p50, p95, p99 |
| `active_connections` | Gauge | Current open connections |
| `db_query_duration_seconds` | Histogram | Database query time per query type |
| `error_total` | Counter | Application errors by type and severity |
| `[domain]_events_processed` | Counter | Business metric — e.g., `broadcast_events_processed_total` |

Emit metrics to the org's centralized metrics store (Azure Monitor / Prometheus — confirm
with AI Architecture which is active for your project).

### Layer 3: Log-Based Monitoring

Ensure the centralized logging system (configured per `audit-logging` skill) is
set up to support log-based metric extraction:

- Error rate: count of `level = ERROR` per minute
- Critical errors: count of `level = CRITICAL` — should be zero in normal operation
- Slow requests: count of requests where `duration_ms > 1000`

---

## SLO Definitions

Define Service Level Objectives before going live. These are the targets for the
monitoring dashboard and the thresholds for alerts.

### Minimum required SLOs

| SLO | Target | Measurement window | Alert threshold |
|---|---|---|---|
| **Availability** | 99.5% | Rolling 30 days | Alert when 30-min availability drops below 99% |
| **Error rate** | <1% of requests | Rolling 5 minutes | Alert when error rate exceeds 2% for 3 consecutive minutes |
| **Latency (p95)** | <500ms | Rolling 5 minutes | Alert when p95 latency exceeds 1000ms for 5 consecutive minutes |
| **Health check** | Always 200 | Continuous | Alert on first failure |

For 🔴 Confidential data applications, tighten these thresholds:
- Availability: 99.9%
- Error rate: <0.5%

Document the SLOs in `docs/runbook.md` and in the project's `CLAUDE.md`.

---

## Alert Definitions

### Alert 1: Service Down

```
Name: [App Name] — Service Down
Condition: /health returns non-200 OR is unreachable for >1 minute
Severity: CRITICAL
Action: page on-call immediately
Channel: [Slack #ops-alerts + PagerDuty]
Runbook: docs/runbook.md — "How to restart the service"
```

### Alert 2: High Error Rate

```
Name: [App Name] — High Error Rate
Condition: error rate > 2% for 3 consecutive minutes
Severity: HIGH
Action: notify on-call within 5 minutes
Channel: [Slack #ops-alerts]
Runbook: docs/runbook.md — "High error rate"
```

### Alert 3: Slow Response Time

```
Name: [App Name] — Latency Degraded
Condition: p95 latency > 1000ms for 5 consecutive minutes
Severity: MEDIUM
Action: notify on-call within 15 minutes (business hours), page after-hours if production impact
Channel: [Slack #ops-alerts]
Runbook: docs/runbook.md — "Latency spike"
```

### Alert 4: CRITICAL Log Event

```
Name: [App Name] — Critical Error
Condition: any log entry with level = CRITICAL
Severity: CRITICAL
Action: page on-call immediately
Channel: [Slack #ops-alerts + PagerDuty]
```

### Alert 5: No Heartbeat (for scheduled jobs / pipelines)

If the application includes a scheduled job:

```
Name: [App Name] — Job Missed Schedule
Condition: [job name] has not run for > [expected_interval × 1.5]
Severity: HIGH
Action: notify on-call
Channel: [Slack #ops-alerts]
```

---

## Dashboard Requirements

Every Production application must have a monitoring dashboard with these panels:

| Panel | Metric | Visualization |
|---|---|---|
| Request rate | `http_requests_total` per minute | Time series |
| Error rate (%) | errors / total requests | Time series with threshold line at 1% |
| p95 Latency | `http_request_duration_seconds` p95 | Time series with threshold line at 500ms |
| Active connections | `active_connections` | Gauge |
| Health check status | `/health` response | Status badge (green/red) |
| DB query latency | `db_query_duration_seconds` | Time series |
| [Business metric] | e.g., `broadcast_events_processed_total` | Counter or time series |

Dashboard must be accessible to: Builder, Champion/Owner, Operations, AI Architecture.
Dashboard must **not** require editing access to view.

---

## On-Call and Escalation

Define before going live:

| Severity | Response time | Who responds | Escalation path |
|---|---|---|---|
| CRITICAL | 15 minutes (24/7) | [Primary on-call] | → [Secondary] → [Manager] |
| HIGH | 30 minutes (business hours), 1 hour (after hours) | [Primary on-call] | → [Manager] |
| MEDIUM | Next business day | [Builder] | — |

Mapping into the org incident process (see `docs/incident-response.md` for severity
definitions and escalation contacts): CRITICAL → treat as P1/P2, HIGH → P2/P3,
MEDIUM → P3/P4. A firing alert should always have a clear path into that process.

Write this table in `docs/runbook.md`.

---

## Monitoring Review Checklist

Before advancing to Production (Step 10 gate):

- [ ] `/health` endpoint implemented — returns 200/503 with DB check, no auth required
- [ ] Application metrics emitting to centralized store
- [ ] Log-based error monitoring configured
- [ ] SLOs defined for availability, error rate, and latency
- [ ] At minimum 4 alerts configured: Service Down, High Error Rate, Slow Latency, Critical Log
- [ ] Scheduled job heartbeat alert (if applicable)
- [ ] Monitoring dashboard created and shared
- [ ] On-call rotation documented in runbook
- [ ] Escalation path documented in runbook

Output format:
```
=== MONITORING REVIEW — [App Name] ===
Health check: [IMPLEMENTED / MISSING]
Metrics: [EMITTING / NOT CONFIGURED]
SLOs defined: [YES — availability: X%, error rate: Y%, latency: Zms / NOT DEFINED]
Alerts configured: [N/4 required alerts set up — missing: list]
Dashboard: [CREATED / MISSING]
On-call documented: [YES / MISSING]
VERDICT: [PASS — ready for Production / NEEDS REVISION — list blocking items]
```

---

## Post-Deployment Monitoring (Step 11)

Once in Production, run this check at the **start of every Builder session** on the project:

```
=== PRODUCTION HEALTH CHECK — [App Name] ===
Last checked: [date/time]
Availability (last 24h): [X%]
Error rate (last 1h): [X%]
p95 Latency (last 1h): [Xms]
Open alerts: [none / list]
Last deployment: [date, commit]
```

If any SLO is breached or an alert is open: address it before doing any new development work.

---

## What NOT to do

- Do not go live without at least a health check endpoint and a "service down" alert
- Do not configure alerts to only send to email — email is not fast enough for incidents
- Do not set alert thresholds so tight they fire constantly (alert fatigue = ignored alerts)
- Do not share Production dashboard edit access broadly — read-only for most users
- Do not write SLOs after going live — define them before, so the baseline is known
- Do not skip the post-deployment monitoring window (60 minutes) — this is when issues appear

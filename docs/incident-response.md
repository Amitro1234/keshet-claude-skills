# Keshet — Security Incident Response Procedure

This document defines what happens after a security incident is detected in a Keshet
Builder application. It complements the `security` skill's escalation table by providing
the step-by-step response procedure for each incident type.

**Owner:** AI Architecture + CISO (Amit Rosen, CIO division)
**Applies to:** All Production applications built through the Keshet Vibe Coding platform
**Last updated:** June 2026

---

## Incident Severity Levels

| Level | Definition | Examples | Response time |
|---|---|---|---|
| 🔴 P1 — Critical | Active breach, data exfiltration, service fully down | Credential leak confirmed in prod, customer PII exposed | 15 minutes (24/7) |
| 🟠 P2 — High | Suspected breach, security control failure, data loss risk | Hardcoded secret found in code, SQL injection vector found | 1 hour (business hours) |
| 🟡 P3 — Medium | Security weakness found, no confirmed impact | Dependency with HIGH vulnerability, missing auth check | Next business day |
| 🟢 P4 — Low | Best-practice gap, advisory | Weak logging, missing rate limiting | Within sprint |

---

## Escalation Contacts

| Role | Contact | When to notify |
|---|---|---|
| AI Architecture | Amit Rosen · Amit.Rosen@keshet-tv.com | All P1 and P2 incidents |
| CISO | [CISO name and contact — fill in] | All P1 incidents; P2 involving 🔴 Confidential data |
| Legal | [Legal contact — fill in] | P1 involving customer PII or contractual data |
| Builder's Manager | [fill in per project] | All P1 and P2 incidents |
| Champion/Owner | [fill in per project] | All incidents on their application |

---

## P1 / P2 Response Procedure

### Step 1: Detect and declare (within 15 minutes for P1, 1 hour for P2)

When a security issue is detected — by Claude, by a developer, by a monitoring alert,
or by an external report — declare the incident immediately:

```
SECURITY INCIDENT DECLARED
Severity: [P1 / P2]
Time: [UTC timestamp]
Application: [app name]
Detected by: [name / tool / alert]
Issue: [1–2 sentence description — what was found, what is at risk]
Data at risk: [classification level — 🟢/🟡/🔴, what type of data]
```

Send to: AI Architecture + CISO (for P1) or AI Architecture (for P2) via direct message.
Do **not** post details in public Slack channels.

### Step 2: Contain (P1 — within 30 minutes)

Containment depends on the incident type:

**Credential/secret leak:**
```
Containment actions:
1. Rotate the leaked credential immediately — even if unsure it was accessed
2. Revoke all active sessions/tokens for the affected service
3. If the secret is in git history: assume it is compromised — it cannot be safely removed retroactively
4. Remove the secret from code and redeploy with env variable approach
```

**Active breach / unauthorized access:**
```
Containment actions:
1. Disable the affected service or endpoint immediately
2. Revoke all authentication tokens for affected users
3. Preserve logs — do not rotate or truncate until forensics are complete
4. Notify AI Architecture before taking further action
```

**PII exposure:**
```
Containment actions:
1. Stop the data flow immediately (disable the endpoint, stop the job)
2. Identify the scope: how many records, which fields, how long exposed
3. Do NOT delete the data or logs — preserve for legal/compliance review
4. Notify CISO and Legal within 1 hour
```

**Dependency vulnerability:**
```
Containment actions:
1. Assess whether the vulnerability is reachable in the current codebase
2. If reachable in Production: treat as P1, take the affected feature offline if necessary
3. If not yet reachable: patch within next business day
```

### Step 3: Assess impact

Answer these questions within 2 hours of incident declaration:

- Was the security control actually exploited, or only potentially exploitable?
- What data was potentially accessed? (classification level, record count, time window)
- Were external parties (customers, partners) affected?
- Is the issue contained, or is the threat still active?

Document answers in the incident ticket.

### Step 4: Notify (P1 only — if data was accessed)

If there is evidence that data was actually accessed (not just potentially at risk):

- **Within 2 hours:** Notify CISO, Legal, and affected Champion/Owner
- **Within 24 hours:** CISO determines if regulatory notification is required
  (GDPR: 72-hour notification window to supervisory authority)
- AI Architecture assists with technical timeline and scope documentation

Do not self-assess whether notification is legally required — escalate to Legal.

### Step 5: Remediate

Fix the root cause:

- [ ] The immediate vulnerability is fixed (patched, secret rotated, endpoint secured)
- [ ] Fix has been code-reviewed (`code-review` skill, `security` skill)
- [ ] Tests added that would have caught this issue
- [ ] Fix deployed to Stage and validated
- [ ] Fix deployed to Production with monitoring window

### Step 6: Post-incident review (within 5 business days)

Write a post-incident review document (store in `docs/incidents/YYYY-MM-DD-[title].md`):

```markdown
# Post-Incident Review — [Title]
Date of incident: [date]
Date of review: [date]
Severity: [P1/P2]
Author: [name]
Reviewers: AI Architecture, CISO

## Summary
[2–3 sentences: what happened, what was affected, what was done]

## Timeline
| Time (UTC) | Event |
|---|---|
| [time] | [event] |

## Root Cause
[What was the fundamental cause — not the symptom but why it happened]

## Impact
- Data at risk: [classification, what, count, duration]
- Users affected: [count and type]
- Services affected: [list]
- External notifications required: [yes/no, to whom]

## What went well
[What detection or response steps worked correctly]

## What went poorly
[Where the process failed or was slower than it should be]

## Action Items
| Action | Owner | Due date |
|---|---|---|
| [preventive action] | [name] | [date] |

## Tests Added
[List any tests added to prevent regression]
```

---

## P3 / P4 Procedure (lower severity)

P3 and P4 incidents do not require emergency response but must be tracked and resolved:

1. Open a ticket in the project's task tracker with severity label
2. Assign to the Builder with a due date (P3: next sprint, P4: within 2 sprints)
3. Resolve before the next Stage→Prod gate if the app is in active development
4. Document in the `security` skill checklist for next review

---

## What Claude Does During an Incident

When a security incident is detected or suspected, Claude must:

1. **Stop the current task immediately** — do not continue building features during an active incident
2. **Declare the incident** using the format in Step 1
3. **Assist with containment** — suggest specific commands for rotating secrets, disabling endpoints, etc.
4. **Do not speculate publicly** — do not post incident details in general channels
5. **Preserve evidence** — remind the Builder not to delete logs, rotate credentials prematurely, or overwrite affected files before forensics

If Claude detects a hardcoded secret, exposed PII, or a critical vulnerability during a code review or build session:

```
SECURITY ISSUE DETECTED — [severity]
Type: [e.g., SECRET_EXPOSURE / PII_IN_LOGS / SQL_INJECTION]
Location: [file:line]
Issue: [what was found]

This must be addressed before any other work continues.
Required action: [specific fix]
Escalation: [who to notify per the incident response procedure]
```

---

## Quick Reference Card

```
P1 — Active breach or confirmed exposure
  → Declare immediately → Contain in 30 min → Notify CISO + Legal → Remediate → Post-incident review

P2 — Security control failure, no confirmed exposure
  → Declare within 1 hour → Assess → Notify AI Architecture → Fix before next gate

P3 — Weakness found, no immediate risk
  → Open ticket → Fix within sprint → Review at next security check

P4 — Best-practice gap
  → Open ticket → Fix within 2 sprints
```

Contacts: Amit Rosen (AI Architecture) · Amit.Rosen@keshet-tv.com

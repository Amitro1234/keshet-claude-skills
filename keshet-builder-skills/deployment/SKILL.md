---
name: keshet-deployment
description: >
  Deployment skill for Keshet Builders. Mandatory at Stage deployment (Step 9) and
  Stage→Prod gate (Step 10). Covers the full deployment sequence: pre-flight checks,
  environment validation, smoke test execution, rollback preparation, and deployment
  sign-off. Triggers on: any request to deploy to Stage or Production, "push to staging",
  "go to prod", "release", or whenever the Builder is advancing to Step 9 or 10.
---

# Deployment Skill — Keshet Builder Mandatory

## Purpose

Deployments fail for predictable reasons: missing environment variables, wrong secrets,
a migration that wasn't run, a smoke test that was skipped. This skill enforces a
repeatable deployment checklist that catches these issues before they become incidents.

**Two deployment targets covered by this skill:**
1. **Stage** — required before Validation Sandbox (Step 9)
2. **Production** — required after Stage→Prod gate approval (Step 10, Champion sign-off)

---

## Trigger Conditions

Activate this skill when any of the following applies:
- The user says "deploy", "push to staging", "go to prod", or "release"
- The Builder is advancing to Step 9 (Stage deployment)
- The Champion/Owner has signed off and the Builder is advancing to Step 10 (Stage→Prod gate)
- A rollback is being considered or executed
- A smoke test needs to be run after deployment

---

## Pre-Flight Checklist (run before every deployment)

### Check 1: Tests pass cleanly

```bash
# Must pass with zero failures and zero skipped tests
pytest -v
# or
npm test
```

- [ ] All tests pass — no failures, no unexplained skips
- [ ] Coverage threshold met (≥80% — see `unit-test` skill)
- [ ] No `xfail` tests that have been failing for >2 weeks

If tests are failing: **STOP. Do not deploy.**

### Check 2: Code review complete

- [ ] `code-review` skill has been run at the current step
- [ ] No unresolved 🔴 BLOCKER findings
- [ ] 🟡 MAJOR findings documented and Champion-acknowledged if advancing to Production

### Check 3: Security review complete

- [ ] `security` skill has been run
- [ ] No `SECURITY_BLOCK` findings outstanding
- [ ] Secrets confirmed: loaded from environment variables, not inline

### Check 4: Environment variables validated

Before deploying, verify every required environment variable is set in the target environment:

```bash
# Print all required vars from .env.example — check each is set in target env
cat .env.example
```

- [ ] Every variable in `.env.example` has a value in the target environment
- [ ] No variable is empty or set to a placeholder (`YOUR_KEY_HERE`, `TODO`, `CHANGE_ME`)
- [ ] No `.env` files are included in the deployment artifact (Docker image, zip, etc.)

### Check 5: Database migrations

- [ ] All pending migrations identified: `alembic current` / `prisma migrate status` / equivalent
- [ ] Migrations reviewed — no dangerous operations (see `db-structure` skill: NOT NULL without default, column renames, type changes)
- [ ] Rollback migration prepared for each new migration
- [ ] Migration will be run **before** the new application version starts (not after)

### Check 6: Rollback plan documented

Before every deployment, write down (or confirm in the runbook):

```
Rollback plan for this deployment:
1. How to detect that the deployment failed: [signal — e.g., error rate >1%, smoke test fails]
2. How to roll back the application: [command — e.g., `az webapp deployment slot swap --slot production --target-slot staging`]
3. How to roll back the migration (if any): [command or "no migration — no rollback needed"]
4. Who to notify: [names and channels]
5. Max acceptable time-to-rollback: [e.g., 15 minutes]
```

A deployment without a rollback plan is not permitted for Production.

---

## Stage Deployment (Step 9)

### Pre-deployment

Run the pre-flight checklist above. All checks must pass.

### Deployment sequence

```bash
# 1. Run migrations first
alembic upgrade head          # Python
# or
npx prisma migrate deploy     # Node

# 2. Deploy application
# [use org CI/CD pipeline — do not deploy manually to shared environments]

# 3. Verify deployment completed
# Check pipeline status — wait for green
```

### Smoke test (mandatory after Stage deployment)

A smoke test verifies that the deployed application is alive and responding.
Run immediately after deployment — before any manual testing.

```bash
# Minimum smoke test: health check endpoint
curl -f https://[stage-url]/health
# Expected: HTTP 200 with { "status": "ok" }
```

Required smoke tests for every deployment:

- [ ] Health check endpoint returns HTTP 200
- [ ] Authentication works: a test token returns a valid response (not 401/500)
- [ ] Primary use case works end-to-end (the most important thing the app does)
- [ ] Database connectivity confirmed (health check should include DB ping)

If any smoke test fails: **roll back immediately** — do not investigate in the live environment.

### Stage deployment sign-off

```
=== STAGE DEPLOYMENT — [App Name] ===
Date: [date]
Builder: [name]
Version/commit: [ref]
Migrations run: [list or "none"]

Pre-flight:
✅ Tests: [PASS]
✅ Code review: [PASS]
✅ Security: [PASS]
✅ Environment variables: [PASS]
✅ Migrations: [PASS / none]
✅ Rollback plan: [documented]

Smoke tests:
✅ Health check: [HTTP 200]
✅ Auth check: [PASS]
✅ Primary use case: [PASS]

VERDICT: DEPLOYED TO STAGE ✅
Ready for: Validation Sandbox (Step 8 activities)
```

---

## Production Deployment (Step 10 → 11)

Production deployments require Champion/Owner sign-off on the Stage→Prod gate
**before** the deployment begins. Do not deploy to Production without that sign-off.

### Additional Production-only checks

Beyond the pre-flight checklist:

- [ ] Champion/Owner has signed off on the Stage→Prod gate (Step 10)
  - Sign-off format: `"Stage→Prod gate approved — [name] — [date]"` on Spec Pack ticket
- [ ] Monitoring and alerting configured (see `monitoring-alerting` skill)
- [ ] Runbook present and reviewed (`docs/runbook.md`) — see `documentation` skill
- [ ] On-call contact confirmed: who is responsible for the first 24 hours post-deployment
- [ ] Deployment window confirmed: avoid Friday afternoons, broadcast events, peak hours

### Production deployment sequence

```bash
# 1. Final migration check against production DB
# (migrations should have been validated in Stage — confirm nothing new)

# 2. Run migrations
alembic upgrade head

# 3. Deploy via CI/CD pipeline — never manual in Production
# Monitor pipeline progress

# 4. Immediate post-deployment smoke tests (same as Stage)
curl -f https://[prod-url]/health
```

### Post-deployment monitoring window

For the first **60 minutes** after a Production deployment:

- Monitor error rate in the logging dashboard
- Monitor response time (p95 should be within 20% of pre-deployment baseline)
- Watch for any audit log anomalies
- Keep rollback ready — do not begin another deployment in this window

### Production deployment sign-off

```
=== PRODUCTION DEPLOYMENT — [App Name] ===
Date: [date]
Builder: [name]
Champion sign-off: [name] on [date] — [ticket link]
Version/commit: [ref]
Migrations run: [list or "none"]

Pre-flight: ✅ (all checks passed — see Stage sign-off)
Stage→Prod gate: ✅ [Champion name, date]
Monitoring configured: ✅
Runbook present: ✅
On-call contact: [name]

Smoke tests (Production):
✅ Health check: [HTTP 200]
✅ Auth check: [PASS]
✅ Primary use case: [PASS]

VERDICT: DEPLOYED TO PRODUCTION ✅
Monitoring window: 60 minutes — ends at [time]
Rollback contact: [name, channel]
```

---

## Rollback Procedure

If the deployment is failing (smoke tests fail, error rate spikes, Champion requests rollback):

### Step 1: Declare the rollback

```
ROLLBACK INITIATED — [App Name]
Reason: [what failed]
Time: [timestamp]
Executing rollback now.
```

### Step 2: Roll back the application

```bash
# Swap back to previous slot (Azure example)
az webapp deployment slot swap \
  --resource-group [rg] \
  --name [app-name] \
  --slot production \
  --target-slot staging

# Or re-deploy previous known-good commit via CI/CD
```

### Step 3: Roll back migrations (if applicable)

```bash
# Only if the migration is safe to reverse
alembic downgrade -1

# If migration is NOT safely reversible: do not run downgrade
# Instead: keep the old schema, re-deploy old code, and fix forward
```

### Step 4: Verify rollback

Run smoke tests against the rolled-back version. Confirm it passes.

### Step 5: Notify and document

```
ROLLBACK COMPLETE — [App Name]
Time: [timestamp]
Duration: [X minutes from deploy to rollback complete]
Root cause (initial): [what failed]
Action taken: [what was rolled back]
Next steps: [who is investigating, timeline for re-deploy]
```

Notify: Champion/Owner, AI Architecture, relevant on-call channel.

---

## What NOT to do

- Do not deploy to Production without Champion sign-off on the Stage→Prod gate
- Do not deploy on Fridays, during broadcast events, or during peak usage hours
- Do not skip migrations and "just deploy code" — schema mismatches cause runtime failures
- Do not investigate failures in the live Production environment — roll back first, investigate later
- Do not push hotfixes directly to Production without running at least a pre-flight check
- Do not deploy multiple changes in the same deployment window — one change at a time
- Do not mark a deployment as successful until smoke tests pass

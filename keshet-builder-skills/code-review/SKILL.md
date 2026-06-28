---
name: keshet-code-review
description: >
  Structured code review gate for Keshet Builders. Mandatory at Agent Validation Sandbox
  (Step 8) and before Stage→Prod gate (Step 10). Triggers on: any request to review,
  check, or validate code; before any git push or merge; or whenever the Builder asks
  "is this ready?". Covers correctness, maintainability, security, performance, and
  test coverage.
---

# Code Review Skill — Keshet Builder Mandatory

## Purpose

Code review is a gate, not a formality. This skill enforces a structured review of every
piece of code before it advances through the Builder Flow. It catches issues that
unit tests cannot: logic errors, security gaps, maintainability problems, and
violations of org standards.

**Who runs this review:** Claude runs the automated portion. A human Champion/Owner
performs the final approval before Stage→Prod (Step 10).

> **Platform compatibility:**
> - Claude Code CLI: ✅ Full support — Claude reads files directly and can run linting/analysis
> - Cowork: ✅ Full support — review applies with connected folder or pasted code
> - Claude.ai Chat: ✅ Supported — paste code or diffs into the conversation for a full 5-dimension review

---

## Trigger Conditions

Activate this skill when any of the following applies:
- The user asks to "review", "check", or "validate" any code
- A git push or merge is about to happen
- The Builder asks "is this ready?" or "can I advance to the next step?"
- Advancing from Step 7 (Build) to Step 8 (Validation Sandbox)
- Advancing from Stage to Production (Step 10 gate)

---

## Review Dimensions

Every code review covers all five dimensions. Missing any one means the review is incomplete.

### Dimension 1: Correctness

Does the code do what the Spec says it should?

- [ ] Code behavior matches the Acceptance Criteria in the Spec Pack
- [ ] Edge cases handled: empty input, null/None, zero, very large values, concurrent access
- [ ] No off-by-one errors in loops or index operations
- [ ] Error paths return meaningful errors — not silent failures
- [ ] Return values used by callers — no ignored error returns

### Dimension 2: Security

Does the code follow the `security` skill requirements?

- [ ] No hardcoded credentials or secrets
- [ ] All inputs validated before use
- [ ] No SQL injection vectors (parameterized queries only)
- [ ] Auth/authz checks present on every protected route
- [ ] PII not logged
- [ ] Dependencies free of HIGH/CRITICAL vulnerabilities

If the `security` skill has not been run, run it now before continuing.

### Dimension 3: Maintainability

Can another developer (or Claude) understand and modify this code in 6 months?

- [ ] Functions are short — single responsibility, <50 lines as a guideline
- [ ] Variable and function names are descriptive — no `x`, `tmp`, `data2`
- [ ] No magic numbers — constants defined and named
- [ ] No dead code (commented-out blocks, unused imports, unreachable branches)
- [ ] No deep nesting (>3 levels of if/for/try) — extract into functions
- [ ] Duplication: any block >5 lines repeated more than once is extracted
- [ ] TODO comments have an associated issue/ticket — not open-ended

### Dimension 4: Performance

Will this code behave acceptably at the scale the app will actually see?

- [ ] No N+1 query patterns — DB queries not inside loops over a result set
- [ ] No synchronous operations in async request handlers (blocking the event loop)
- [ ] Pagination used for any query that could return >100 rows
- [ ] No unbounded memory allocation (building huge lists/dicts in memory)
- [ ] External API calls have timeouts configured — not left at default/infinity
- [ ] Expensive operations are cached where appropriate (with TTL)

### Dimension 5: Test Coverage

Is there sufficient test coverage for the risk level of this code?

| Code type | Minimum coverage |
|---|---|
| Business logic | 80% unit test coverage |
| API routes | Integration test for each route |
| Data access layer | Tested against a real test DB (not mocked) |
| Utility functions | 100% unit test coverage |
| Error paths | At least one test per expected error condition |

See `unit-test` skill for test writing standards.

---

## Severity Levels

Each finding is classified:

| Level | Definition | Required action |
|---|---|---|
| 🔴 BLOCKER | Security issue, data loss risk, crashes in basic use, spec mismatch | Must fix before advancing |
| 🟡 MAJOR | Serious maintainability issue, performance risk at scale, missing required tests | Should fix before advancing; document if deferring |
| 🟢 MINOR | Style, naming, minor clarity issue | Fix encouraged; can advance with open item |
| 💡 SUGGESTION | Optional improvement, not a defect | Take or leave |

A review with any 🔴 BLOCKER is a `FAIL` — the build does not advance.
A review with unresolved 🟡 MAJOR issues requires Champion sign-off to advance.

---

## Review Output Format

```
=== CODE REVIEW — [App Name] ===
Date: [date]
Reviewer: Claude (automated) + [human if applicable]
Files reviewed: [list]
Builder Flow Step: [8 / 10]
Commit/branch: [ref]

DIMENSION RESULTS:
✅ Correctness — [PASS / ISSUES: list]
✅ Security    — [PASS / ISSUES: list]  (or: "Security skill run separately — [result]")
✅ Maintainability — [PASS / ISSUES: list]
✅ Performance — [PASS / ISSUES: list]
✅ Test Coverage — [PASS / ISSUES: list]

FINDINGS:
[🔴 BLOCKER | 🟡 MAJOR | 🟢 MINOR | 💡 SUGGESTION]
File: path/to/file.py, Line: 42
Issue: [description]
Fix: [specific recommendation]

...

SUMMARY:
Blockers: [N]
Majors: [N]
Minors: [N]
Suggestions: [N]

VERDICT: [PASS / CONDITIONAL PASS (list open majors) / FAIL (list blockers)]
```

---

## Human Review Requirements

Claude's automated review is necessary but not sufficient for Production advances.
The following require a human Champion/Owner review:

- Any code touching 🔴 Confidential data
- Any new external integration or MCP tool connection
- Any change to authentication or authorization logic
- Any database migration (refer to `db-structure` skill)
- Any Step 10 (Stage→Prod) gate crossing

The Champion signs off by commenting on the Spec Pack ticket:
`"Code review approved — [name] — [date]"`

---

## What NOT to do

- Do not skip the review because the code "looks fine" — every Build goes through review
- Do not mark a finding as MINOR if it's a security issue — always escalate to BLOCKER
- Do not approve code that deviates from the Spec without Champion sign-off
- Do not merge without resolving all BLOCKERs
- Do not run review on minified, compiled, or generated code — review source only

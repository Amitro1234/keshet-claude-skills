---
name: spec-pack
description: >
  Use when starting a new project or feature, when the user asks to "write
  the spec" or "what should we build," or when code is about to be written
  with no Spec Pack in place yet.
---

# Spec Pack Skill — Keshet Builder Mandatory

## Purpose

A Spec Pack is the foundation of every Keshet Build. Writing code before a
Spec Pack is approved is the single most common cause of rework,
miscommunication, and production incidents on the platform.

This skill produces three documents that together define exactly what will
be built, how it will be built, and how anyone can verify it was built
correctly — see `templates.md` for the full PRD / Technical Spec /
Acceptance Criteria templates.

**Rule:** No code is written until the Spec Pack is approved by the
Champion/Owner (Step 6).

> **Platform compatibility:**
> - Claude Code CLI: full support — Claude writes Spec Pack files directly into `docs/spec/`
> - Cowork: full support — spec generation works in conversation; save output to connected folder
> - Claude.ai Chat: supported — Claude generates all three documents in conversation; copy into your ticket system (Monday/Jira)

---

## Trigger Conditions

Activate when: a new project or feature is being started, the user says
"let's write the spec" / "what should we build" / "start the project", the
Builder is at Step 5, code is about to be written but no Spec Pack exists
yet, or the Champion/Owner asks what will be built.

**Hard rule:** No code is written until the Spec Pack is complete and
approved at Step 6. If the user tries to start coding without a Spec Pack,
stop and run this skill first.

---

## Three Documents in a Spec Pack

| Document | Owner | Audience | Gate |
|---|---|---|---|
| **PRD** (Product Requirements Document) | Champion/Owner | Builder, Stakeholders | Step 6 |
| **Technical Spec** | Builder (with Claude) | Builder, AI Architecture | Step 6 |
| **Acceptance Criteria** | Champion/Owner + Builder | Builder, QA, Champion | Step 8 + Step 10 |

All three live in the Spec Pack ticket (Monday / Jira). They are linked from
the project's `CLAUDE.md` and committed to the repo under `docs/spec/`. Full
templates for all three: `templates.md`.

---

## Spec Pack Review Checklist

Before advancing from Step 5 to Step 6 (Spec Approval):

**PRD:**
- [ ] Problem statement is specific and quantified (not vague)
- [ ] Use cases are named and described from the user's perspective
- [ ] Out of scope is explicitly listed
- [ ] Success metrics are measurable
- [ ] Data classification is declared

**Technical Spec:**
- [ ] Application category declared (Local Demo / Department Tool / Production)
- [ ] Architecture diagram complete — all layers defined
- [ ] Technology choices made with rationale
- [ ] All external integrations listed and verified against `approved-mcp-connectors.md`
- [ ] Data model defined (if DB exists)
- [ ] API endpoints defined (if applicable)
- [ ] Security approach documented
- [ ] Deployment plan exists

**Acceptance Criteria:**
- [ ] At least one AC per use case
- [ ] At least one AC per error/edge case
- [ ] Non-functional AC covers performance, security, and logging
- [ ] Each AC is verifiable — "user sees a success message" is not verifiable; "HTTP 201 with `{ id, status }` is returned" is

## What NOT to do

- Do not start writing code before the Spec Pack is approved at Step 6
- Do not write Acceptance Criteria that are not testable ("the app should be fast")
- Do not skip the Technical Spec for "small" projects — scope always grows
- Do not leave Out of Scope blank — it is the most important section for preventing rework
- Do not write the Spec Pack alone — the PRD must be validated by the Champion/Owner before Step 6
- Do not use vague problem statements ("we need a better process") — be specific and quantified

---

## Rationalizations — Excuse vs. Reality

| Excuse | Reality |
|---|---|
| "We already know what to build, the spec is just paperwork" | The spec is where scope creep and rework get caught — before code, not after. |
| "Let's code first and write the spec to match" | That's not a spec, it's a retroactive rationalization of whatever got built. |
| "It's a small feature, doesn't need all three documents" | Scope always grows. The Technical Spec you skipped is the one that would have caught the growth. |
| "The Champion is busy, I'll just start and get approval later" | Step 6 approval exists before Step 7 build for a reason — after-the-fact sign-off isn't a gate. |
| "The Acceptance Criteria are obvious, no need to write them down" | "Obvious" to the Builder often isn't obvious to the Champion signing off at Step 10 — write it down. |

## Red Flags — STOP and run this skill first

- You're about to write code and there's no Spec Pack ticket yet
- You're thinking "we'll formalize the spec after we see what we build"
- The PRD's "Out of Scope" section is blank
- An Acceptance Criterion reads like a vague feeling ("the app should be fast") instead of Given/When/Then
- The user says "let's just start coding, we'll figure out the details as we go"

**All of these mean: stop, produce all three documents, and get Champion/Owner sign-off before Step 7.**

---

## Review Output

```
=== SPEC PACK REVIEW — [Project Name] ===
PRD: [COMPLETE / MISSING: list]
Technical Spec: [COMPLETE / MISSING: list]
Acceptance Criteria: [COMPLETE / MISSING: list]
Ready for Step 6 (Champion Approval): [YES / NO — list blocking items]

VERDICT: [PASS — ready for Step 6 / FAIL — list blocking items]
```

---
name: keshet-db-structure
description: >
  Database design standards for Keshet Builders. Mandatory at Build (Step 7) whenever
  a schema, migration, or data model is created or modified. Triggers on: CREATE TABLE,
  schema changes, ORM model definitions, migration files, database access patterns,
  indexing decisions, or any question about data storage design.
---

# DB Structure Skill — Keshet Builder Mandatory

## Purpose

Database schemas outlive the applications built on them. A poorly designed schema
causes production incidents, data loss, and expensive migrations years later.
This skill enforces consistent, safe, and maintainable database design across all
Keshet Builder applications.

---

## Trigger Conditions

Activate this skill when any of the following applies:
- A `CREATE TABLE` or schema definition is being written
- An ORM model (SQLAlchemy, Prisma, Django models, etc.) is being defined
- A migration file is being created or reviewed
- A database access pattern, index, or query is being designed
- The user asks any question about data storage design
- Advancing from Step 7 (Build) to Step 8 (Validation Sandbox)

---

## Naming Conventions

All identifiers must follow these conventions — no exceptions:

| Object | Convention | Example |
|---|---|---|
| Tables | `snake_case`, plural | `user_events`, `broadcast_segments` |
| Columns | `snake_case` | `created_at`, `external_id` |
| Primary key | `id` (surrogate, always) | `id BIGSERIAL PRIMARY KEY` |
| Foreign keys | `<table_singular>_id` | `user_id`, `segment_id` |
| Boolean columns | `is_` or `has_` prefix | `is_active`, `has_been_processed` |
| Timestamp columns | `_at` suffix | `created_at`, `updated_at`, `deleted_at` |
| Junction tables | `<table1>_<table2>` alphabetical | `role_user`, not `user_role` |
| Indexes | `idx_<table>_<columns>` | `idx_user_events_user_id` |
| Unique constraints | `uq_<table>_<columns>` | `uq_users_email` |

---

## Required Columns

Every table must include:

```sql
id          BIGSERIAL PRIMARY KEY,           -- surrogate key, never expose externally
created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

If the table supports soft delete (preferred over hard delete for audit compliance):
```sql
deleted_at  TIMESTAMPTZ NULL                 -- NULL = not deleted, timestamp = soft-deleted
```

**Do not use natural keys as primary keys.** Email, phone, external ID — these change.
Always use a surrogate `id` and add a unique constraint on the natural key separately.

---

## Schema Design Rules

### Normalization
- Aim for 3NF (Third Normal Form) — no transitive dependencies
- Denormalize only with explicit justification in an ADR and a measured performance need
- No JSON blobs used to avoid normalization — use a proper column or child table

### Data Types
| Data | Type | Notes |
|---|---|---|
| Text (variable) | `TEXT` | Not `VARCHAR(255)` — unnecessary constraint |
| Short codes, enums | `TEXT` + CHECK constraint | Or a proper enum type |
| Money / prices | `NUMERIC(19,4)` | Never `FLOAT` — floating point is not precise |
| Timestamps | `TIMESTAMPTZ` | Always with timezone — never `TIMESTAMP` |
| Booleans | `BOOLEAN` | Never `TINYINT(1)` or `0/1` in TEXT |
| Large binary | `BYTEA` / object storage | >1MB: store in S3/blob, save URL in DB |
| UUIDs (external-facing) | `UUID` | When exposing IDs publicly — use UUID, not BIGINT |

### Constraints
- Every foreign key must have a corresponding index
- Every unique constraint must be declared explicitly — not enforced only in application code
- `NOT NULL` is the default — only use `NULL` when absence of value is a meaningful business state
- Avoid `ON DELETE CASCADE` unless the child data is truly meaningless without the parent

---

## Migrations

All schema changes must be delivered as **numbered migration files**, never as ad-hoc SQL:

```
migrations/
├── 001_initial_schema.sql
├── 002_add_users_table.sql
├── 003_add_broadcast_segments.sql
└── 004_add_index_user_events_user_id.sql
```

Migration rules:
- [ ] Migrations are **always additive** — never DROP without a separate deprecation migration
- [ ] Each migration is idempotent where possible (`CREATE TABLE IF NOT EXISTS`)
- [ ] Every migration has a corresponding **rollback migration** or a documented rollback plan
- [ ] Migrations are reviewed before applying to Stage and tested before Production
- [ ] No schema changes directly in Production — always via migration pipeline

**Dangerous migrations — require explicit approval:**
- Adding `NOT NULL` to an existing column without a default (locks table)
- Renaming a column (breaks all queries using the old name)
- Changing a column's data type (risk of data loss)
- Dropping any column or table
- Any migration on a table with >1M rows (lock time risk — use online migration tooling)

---

## Indexing Standards

Create indexes for:
- Every foreign key column
- Every column used in a `WHERE` clause in a common query
- Every column used in an `ORDER BY` on a large table
- Composite indexes when queries filter on multiple columns together

Do NOT create indexes on:
- Boolean columns (low cardinality — indexes don't help)
- Columns that are rarely queried
- Tables with <10K rows (sequential scan is faster)

Always measure query performance with `EXPLAIN ANALYZE` before declaring an index sufficient.

---

## Data Security in DB Design

- [ ] 🔴 Confidential columns (PII, financial data) noted in schema documentation
- [ ] Passwords are never stored — only bcrypt/argon2 hashes
- [ ] PII columns flagged for DLP review before Production
- [ ] Soft delete preferred over hard delete — data retained for audit trail
- [ ] No production data in Dev or Stage databases — use anonymized fixtures

---

## DB Structure Review Checklist

Before advancing from Step 7 (Build) to Step 8 (Validation):

- [ ] Naming conventions followed throughout
- [ ] Required columns present (`id`, `created_at`, `updated_at`)
- [ ] No natural keys used as primary keys
- [ ] Correct data types used (no FLOAT for money, no TIMESTAMP without TZ)
- [ ] All foreign keys indexed
- [ ] All schema changes delivered as numbered migration files
- [ ] Rollback plan documented for each migration
- [ ] No dangerous migrations without approval
- [ ] PII columns identified and flagged

Output format:
```
=== DB STRUCTURE REVIEW — [App Name] ===
Tables reviewed: [list]
Naming: [PASS / VIOLATIONS: list]
Data types: [PASS / ISSUES: list]
Indexes: [PASS / MISSING: list]
Migrations: [PASS / ISSUES: list]
Security: [PASS / FLAGS: list]
VERDICT: [PASS / NEEDS REVISION]
```

---

## What NOT to do

- Do not use natural keys (email, phone, external ID) as primary keys — they change
- Do not use `FLOAT` for money or financial values — use `NUMERIC(19,4)`
- Do not use `TIMESTAMP` without timezone — always use `TIMESTAMPTZ`
- Do not use `VARCHAR(255)` — use `TEXT` (PostgreSQL has no performance difference)
- Do not use `ON DELETE CASCADE` unless child data is truly meaningless without the parent
- Do not add a `NOT NULL` column to a large existing table without a default value — it locks the table
- Do not rename columns without a migration plan — it breaks all queries using the old name
- Do not run schema changes directly in Production — always via a numbered migration file
- Do not store production data in Dev or Stage databases — use anonymized fixtures

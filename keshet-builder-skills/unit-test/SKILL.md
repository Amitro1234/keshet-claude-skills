---
name: keshet-unit-test
description: >
  Unit and integration testing standards for Keshet Builders. Mandatory at Build (Step 7)
  and Agent Validation Sandbox (Step 8). Triggers on: any request to write, review, or
  run tests; when implementing new functions or classes; when fixing bugs; or when the
  code review skill flags insufficient test coverage.
---

# Unit Test Skill — Keshet Builder Mandatory

## Purpose

Tests are not optional. Code without tests cannot be safely changed, cannot be
confidently deployed, and cannot be maintained by anyone other than the original author.

Every Keshet Builder application must have a working test suite before it can
advance past Step 8 (Agent Validation Sandbox).

---

## Test Types and When to Write Them

| Test type | What it tests | When required |
|---|---|---|
| **Unit test** | A single function/method in isolation | All business logic functions |
| **Integration test** | Multiple components working together | API routes, DB access layer |
| **Contract test** | Interface between this app and an external service | Any external API or MCP integration |
| **Smoke test** | That the deployed app starts and responds | Every deployment to Stage and Prod |

---

## Coverage Requirements

| Code layer | Required coverage | Measured by |
|---|---|---|
| Business logic (`src/services/`) | ≥80% line coverage | pytest-cov / jest --coverage |
| API routes (`src/api/`) | 100% route coverage (integration test per route) | Explicit route list check |
| Data access layer (`src/data/`) | Tested against real test DB | Fixture + teardown |
| Utility functions (`src/utils/`) | 100% | pytest-cov |
| Error paths | At least 1 test per error condition | Manual check |
| Happy path | At least 1 test per public function | pytest-cov |

Meeting the coverage number is not sufficient — tests must be **meaningful**.
A test that passes always regardless of the code's behavior is not a test.

---

## Test Writing Standards

### Structure: Arrange, Act, Assert (AAA)

Every test follows this structure:

```python
def test_calculate_segment_duration_returns_ms():
    # Arrange
    start = datetime(2026, 1, 1, 10, 0, 0)
    end   = datetime(2026, 1, 1, 10, 0, 30)

    # Act
    result = calculate_segment_duration(start, end)

    # Assert
    assert result == 30_000  # 30 seconds in milliseconds
```

### Naming Convention

```
test_<function_name>_<condition>_<expected_outcome>

# Good:
test_process_event_with_missing_id_raises_validation_error
test_calculate_duration_with_equal_timestamps_returns_zero
test_create_user_with_duplicate_email_returns_409

# Bad:
test_1
test_process
test_it_works
```

### One assertion focus per test

Each test should verify one specific behavior. Multiple unrelated assertions in one
test make failures hard to diagnose.

```python
# Bad — two unrelated assertions
def test_user_creation():
    user = create_user("alice@keshet.tv")
    assert user.id is not None
    assert send_welcome_email.called  # testing two things

# Good — split into two tests
def test_create_user_assigns_id():
    user = create_user("alice@keshet.tv")
    assert user.id is not None

def test_create_user_sends_welcome_email():
    create_user("alice@keshet.tv")
    assert send_welcome_email.called
```

### Test isolation

- Tests must not depend on execution order
- Tests must not share mutable state
- Tests must clean up after themselves (use fixtures with teardown)
- Each test must be runnable in isolation: `pytest tests/test_events.py::test_name`

### Mocking rules

- Mock external services (APIs, MCP tools, email, SMS) — never call real external services in tests
- Do NOT mock the database — test against a real test DB (use a separate DB or transactions that roll back)
- Do NOT mock your own business logic — if you're mocking your own code, the design is wrong

```python
# Good — mock the external HTTP call, test the logic
@patch("src.data.clients.scheduling_api.get_segment")
def test_process_event_handles_404(mock_get):
    mock_get.side_effect = NotFoundException("segment not found")
    result = process_event({"segment_id": "nonexistent"})
    assert result.status == "failed"
    assert "not found" in result.error_message

# Bad — mock your own service
@patch("src.services.event_service.validate_event")
def test_process_event(...):  # you're now testing nothing
```

---

## Python Test Setup

```
project/
├── tests/
│   ├── conftest.py           ← fixtures, DB setup/teardown
│   ├── unit/
│   │   ├── test_services.py
│   │   └── test_utils.py
│   └── integration/
│       ├── test_api_routes.py
│       └── test_data_layer.py
├── pytest.ini                 ← pytest config
└── requirements-test.txt      ← test dependencies
```

`pytest.ini` minimum config:
```ini
[pytest]
testpaths = tests
addopts = --cov=src --cov-report=term-missing --cov-fail-under=80
```

Required test packages:
```
pytest
pytest-cov
pytest-asyncio      # if using async code
pytest-mock
factory_boy         # for test data factories
```

---

## JavaScript / TypeScript Test Setup

```
project/
├── src/
└── tests/
    ├── unit/
    └── integration/
```

`package.json` minimum:
```json
{
  "scripts": {
    "test": "jest",
    "test:coverage": "jest --coverage --coverageThreshold='{\"global\":{\"lines\":80}}'"
  }
}
```

Required test packages:
```
jest
@types/jest
jest-mock-extended
supertest        # for API route integration tests
```

---

## Running Tests Before Gate Crossings

Before advancing from Step 7 (Build) to Step 8 (Validation):
```bash
pytest --cov=src --cov-fail-under=80 -v
# All tests must pass. Coverage must be ≥80%.
```

Before Step 9 (Stage deployment):
```bash
pytest -v                    # full suite
pytest tests/integration/    # integration tests against real test DB
```

Before Step 10 (Stage→Prod gate):
```bash
pytest -v                    # full suite must pass clean
# No skipped tests without documented reason
# No xfail tests that have been failing for >2 weeks
```

---

## Test Review Checklist

```
=== TEST REVIEW — [App Name] ===
Unit test coverage: [N]% (required: ≥80%)
API routes covered: [N/N routes]
Error paths tested: [PASS / MISSING: list]
Mocking discipline: [PASS / ISSUES: list]
Test isolation: [PASS / ISSUES: list]
All tests passing: [YES / FAILURES: list]
VERDICT: [PASS / NEEDS REVISION]
```

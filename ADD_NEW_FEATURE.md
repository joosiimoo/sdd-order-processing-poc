# Adding a New Feature using Spec-Driven Development (SDD)

This repository uses **Spec-Driven Development (SDD)**.
All new features MUST follow the workflow defined in this document.

This process assumes **Cursor** is used as the implementation environment.

---

## 0. Prerequisites

Before starting a new feature, ensure:

- The repository is cloned
- Cursor is opened at the repository root
- Python dependencies are installed
- Baseline tests pass

Run:

```bash
PYTHONPATH=. pytest tests/ -v
```

You MUST start from a green baseline.

---

## 1. Write the Specification (Source of Truth)

Create a new specification file:

```text
openspec/features/<feature-name>.md
```

Rules:
- One feature = one file
- Declarative language only
- No implementation details
- No assumptions beyond what is written

Example:

```text
openspec/features/refund-processing.md
```

The specification is the **only authority** for behavior.

---

## 2. Generate Tests from the Spec (Cursor)

Open **Cursor** and select the specification file you just created.

Use the following prompt **exactly as written**.

### Cursor Prompt — Generate Tests

```text
You are implementing Spec-Driven Development.

Given the specification in this file:
openspec/features/<feature-name>.md

Create a comprehensive pytest test suite that fully enforces this specification.

Requirements:
- Tests must reflect ONLY what is explicitly stated in the spec
- Do not invent behavior
- Do not implement application code
- Tests must fail against the current codebase

Output:
- Create a new test file under tests/
- Name it test_<feature-name>_spec.py
- Organize tests by spec sections
- Use clear test names that reflect the behavior

Do not modify existing tests or application code.
```

Expected result:
- A new test file is created under `tests/`
- Existing code is untouched
- New tests fail

---

## 3. Run Tests (Contract Validation)

Run:

```bash
PYTHONPATH=. pytest tests/ -v
```

Expected outcome:
- New tests FAIL
- Existing tests still PASS

If:
- New tests pass → tests are invalid
- Existing tests fail → tests are invalid

Do NOT proceed until this step is correct.

---

## 4. Implement Incrementally (Cursor)

Implementation is done **only to satisfy failing tests**.

Open Cursor and use the following prompt.

### Cursor Prompt — Implement Feature

```text
Implement only the minimum code required to make the failing tests in
tests/test_<feature-name>_spec.py pass.

Constraints:
- Follow the specification exactly
- Do not refactor unrelated code
- Do not modify existing behavior
- Implement incrementally, one failing test at a time

Do not change the tests.
```

Loop:
1. Implement
2. Run tests
3. Observe fewer failures
4. Repeat until green

---

## 5. Definition of Done (DoD)

A feature is considered complete when:

- All tests pass
- No existing specs were modified
- No existing tests were modified
- No behavior exists without a test
- The implementation matches the spec exactly

Final verification:

```bash
PYTHONPATH=. pytest tests/ -v
```

---

## 6. Commit

Commit using a clear, SDD-oriented message:

```bash
git add .
git commit -m "Add <feature-name> feature (SDD)"
git push
```

---

## Summary

The SDD execution loop is:

```
Spec → Tests (Cursor) → Tests fail → Implementation (Cursor) → Tests pass
```

No step may be skipped.

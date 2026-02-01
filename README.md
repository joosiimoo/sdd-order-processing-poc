# Order Processing POC – Spec-Driven Development Reference

## 1. What is this repo?

A reference implementation of **Spec-Driven Development (SDD)**. It implements a simple Order Processing API (create, get, confirm, cancel orders) to demonstrate how specifications drive the development cycle. The specification is the single source of truth; tests and code follow from it.

## 2. SDD Workflow Used

1. **Specify** – Write or update the functional spec in `openspec/`
2. **Test** – Add or adjust tests that encode spec behavior (`tests/`)
3. **Implement** – Write code to satisfy tests and spec
4. **Verify** – Run tests to ensure implementation conforms

Specs are never written to match the code. Code and tests are written to match the specs.

## 3. Project Structure

```
openspec/           # Specifications (source of truth)
├── domain.md       # Domain concepts
└── features/
    └── order-processing.md   # API, validation, errors

app/                # Implementation
└── main.py         # FastAPI app, in-memory storage

tests/              # Spec-derived tests
├── conftest.py     # Pytest fixtures (client, base_path)
└── test_order_processing_spec.py
```

## 4. How to Run Tests

```bash
pip install -r requirements-dev.txt
pytest
```

For verbose output: `pytest -v`

## 5. How to Extend with a New Feature

1. **Update the spec** – Add the feature to `openspec/features/order-processing.md` (or a new feature file). Define request/response shapes, validation rules, and error cases.
2. **Add tests** – Add tests in `tests/test_order_processing_spec.py` that assert the spec behavior. Reference the spec section in docstrings.
3. **Implement** – Implement the feature in `app/main.py` until tests pass.
4. **Verify** – Run `pytest` and ensure no existing tests fail.

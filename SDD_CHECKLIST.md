# SDD Checklist

Use this checklist when adding or changing features.

---

- [ ] **1. Define the spec**
  - Add or update the specification in `openspec/` (e.g. `features/order-processing.md`)
  - Include: request/response shapes, validation rules, error codes, state transitions

- [ ] **2. Generate tests from the spec**
  - Add tests in `tests/` that assert spec behavior
  - Map each test to a spec section (docstring or comment)
  - Cover success paths and error cases

- [ ] **3. Ensure tests fail**
  - Run `pytest` — tests should fail (feature not implemented or behavior incorrect)

- [ ] **4. Implement incrementally**
  - Implement only what is needed to make the next failing test pass
  - Do not add behavior not specified

- [ ] **5. Verify against the spec**
  - Run `pytest` — all tests pass
  - Review: implementation matches spec, no spec violations

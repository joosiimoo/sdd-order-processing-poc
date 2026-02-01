# SDD Playbook

## 1. What is Spec-Driven Development?

SDD is a workflow where you write the specification first, then derive tests from it, then implement until tests pass. The spec is the source of truth. Code and tests exist only to satisfy the spec.

## 2. Core Principles

- **Spec first** — No implementation without a written spec. No spec changes to justify existing code.
- **Tests from spec** — Tests encode spec behavior. They are not derived from the implementation.
- **Implementation last** — Code exists only to satisfy tests and spec. No extra features.
- **Traceability** — Each test references a spec section. Each requirement is testable.

## 3. The SDD Workflow

1. **Define the spec** — Document the feature: endpoints, request/response shapes, validation rules, error codes, state transitions.
2. **Add tests** — Write tests that assert spec behavior. Link each test to a spec section (docstring).
3. **Run tests** — They should fail. If they pass before implementation, the tests are wrong.
4. **Implement incrementally** — Make one failing test pass at a time. Add no behavior beyond the spec.
5. **Verify** — All tests pass. Manually confirm implementation matches spec.

## 4. Role of the Specification

- Lives in `openspec/` (e.g. `features/order-processing.md`).
- Defines: domain concepts, API contracts, validation rules, error formats, state machines.
- Is the single source of truth. Disputes are resolved by the spec.
- Must be explicit enough that tests can be derived from it.

## 5. Role of Tests

- Encode spec behavior in executable form.
- Map to spec sections via docstrings or comments.
- Cover success paths and error cases.
- Run before and during implementation to guide work.
- Should fail when behavior diverges from spec.

## 6. Role of Implementation

- Exists only to satisfy the spec and tests.
- Should be minimal: no speculative features, no “nice to have”.
- If something is unclear, clarify in the spec first, then implement.

## 7. When to Introduce Infrastructure

- **Docker** — When you need consistent environments (DB, app) or to run the app in a container. Add after core behavior works locally.
- **Database** — When the spec requires persistence. Start with in-memory storage; add DB when the spec demands it.
- **CI** — Once tests are stable. Run `pytest` on every commit.

Introduce only when the spec or team workflow requires it. Avoid adding infra “for later”.

## 8. Common Mistakes to Avoid

- **Spec written to match code** — Spec must come first. Refactor spec if wrong; don’t bend it to fit implementation.
- **Tests that pass before implementation** — Tests should fail until the feature exists. Otherwise they don’t guard behavior.
- **Implementing beyond the spec** — No “while we’re here” features. Add to spec first.
- **Skipping the spec** — “We know what we want” leads to drift. Write it down.

## 9. When SDD Fits / When It Doesn’t

**Good fit:** APIs, services with clear contracts, regulated domains, projects where correctness and traceability matter more than speed. Teams that value alignment over rapid iteration.

**Poor fit:** Prototypes with fluid requirements, pure experimentation, very small one-off scripts. Situations where writing a spec adds little value.

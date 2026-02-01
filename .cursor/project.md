You are working on a Spec-Driven Development (SDD) proof of concept.

Core principles:
- Specifications are the source of truth.
- Code must conform strictly to written specs.
- Tests are derived from specs, not from code.
- Implementation exists only to satisfy specs and tests.
- No feature should be implemented without an explicit spec.

Project context:
- This is a Proof of Concept for Spec-Driven Development.
- The domain is Order Processing.
- The goal is clarity, correctness, and traceability — not speed or shortcuts.

Rules:
- Do not invent requirements.
- Do not add features not present in the spec.
- If something is unclear, ask for clarification in comments.
- Prefer explicitness over cleverness.
- Keep the implementation minimal and readable.

Tech stack:
- Backend: FastAPI (Python)
- Database: PostgreSQL
- ORM: SQLAlchemy / SQLModel
- Tests: Pytest
- Infra: Docker Compose

Everything must align with the specs located under /openspec.


# Backend Staff Engineer Brief

## Key Decisions
- FastAPI + SQLAlchemy + Postgres.
- Celery + Redis for background jobs (phase 2 for heavy exports).
- JWT auth for MVP.

## Risks
- Data correctness → unit tests for calculation engine.

## Deliverables
- MVP API + deterministic calc engine.

## Acceptance Criteria
- API can generate Excel packs deterministically.

# DevOps/SRE Brief

## Key Decisions
- Docker Compose for local dev and single VPS.
- Makefile scripts for common workflows.

## Risks
- Secrets management → use env vars and avoid committing secrets.

## Deliverables
- MVP: compose file + runbooks.

## Acceptance Criteria
- `make dev` boots the stack reliably.

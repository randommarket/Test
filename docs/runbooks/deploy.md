# Deploy Runbook

1. Provision a VPS with Docker and Docker Compose.
2. Clone the repo.
3. Set environment variables (DATABASE_URL, REDIS_URL, SECRET_KEY).
4. (Optional) Override alert thresholds: `RUNWAY_RISK_THRESHOLD`, `REVENUE_DROP_THRESHOLD`, `MARGIN_DROP_THRESHOLD`.
5. Run `make dev` for local or use `docker compose up -d` for production.
6. Validate `/health` returns `{"status":"ok"}` and check logs via `docker compose logs -f backend`.

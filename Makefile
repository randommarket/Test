.PHONY: dev migrate seed test lint verify-backup

dev:
	docker compose up --build

migrate:
	docker compose run --rm backend alembic upgrade head

seed:
	docker compose run --rm backend python -m app.services.seed

test:
	docker compose run --rm backend pytest

lint:
	docker compose run --rm backend ruff check app tests

verify-backup:
	./scripts/verify_backup.sh backup.sql

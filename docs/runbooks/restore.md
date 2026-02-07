# Restore Runbook

1. Copy backup file to the server.
2. Run:
   ```bash
   docker compose exec -T db psql -U prs prs < backup.sql
   ```
3. Validate application health and sample queries after restore.

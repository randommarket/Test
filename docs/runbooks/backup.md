# Backup Runbook

1. Execute a Postgres dump:
   ```bash
   docker compose exec db pg_dump -U prs prs > backup.sql
   ```
2. Store the backup in secure storage.
3. Verify backup integrity by checking file size and running a sample restore in a staging environment.
4. Run automated verification:
   ```bash
   make verify-backup
   ```

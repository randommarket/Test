# Risks & Mitigations

- **Data quality issues**: enforce CSV validation and canonical mapping. Provide templates.
- **Incorrect KPI definitions**: publish finance conventions and test with fixtures.
- **Scalability**: design data model with org scoping and indexes; use background jobs for heavy tasks.
- **Security**: use JWT auth, RBAC roles, and audit logs.
- **Operational reliability**: provide runbooks for backups and restores.

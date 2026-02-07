# API Spec

Base URL: `/`

## Auth
- `POST /auth/register` (org_name, email, password)
- `POST /auth/login` (email, password)

## Companies
- `POST /companies`
- `GET /companies`

## Users (org_admin only)
- `GET /users`
- `POST /users`
- `PATCH /users/{user_id}` (role update)

## Actuals
- `POST /companies/{company_id}/actuals` (CSV upload)

## Mappings
- `GET /companies/{company_id}/mappings/suggest`
- `GET /companies/{company_id}/mappings/status`
- `GET /companies/{company_id}/mappings/export`
- `POST /companies/{company_id}/mappings/import`

## Scenarios
- `POST /companies/{company_id}/scenarios`

## Packs
- `GET /companies/{company_id}/pack` (streams an .xlsx download)

## Dashboard
- `GET /portfolio/dashboard`

## Audit Logs
- `GET /audit/logs`

## Organization Settings (org_admin only)
- `GET /org/settings`
- `PUT /org/settings`

## Templates
- `GET /templates/actuals.csv`

## UI
- `GET /` (operator UI)

OpenAPI: available at `/docs` once running.

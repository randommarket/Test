# Product Requirements Document (PRD)

## Goal
Deliver a production-ready MVP for managing monthly reporting across 50–75 startups with deterministic calculations, scenario modeling, and Excel exports.

## Users
- Portfolio manager (primary)
- Analyst (data prep, scenario runs)
- Viewer (read-only)

## MVP Features
1. Multi-tenant organizations with roles.
2. Company CRUD.
3. CSV upload of monthly actuals (P&L + cash balance).
4. Canonical schema mapping and validations.
5. KPI computation: revenue, gross profit, gross margin, EBITDA, burn, runway.
6. Forecasts (12 months) and scenarios (Base/Upside/Downside).
7. Sensitivity grid across two drivers.
8. Excel reporting pack export.
9. Portfolio dashboard and risk list.
10. Audit logs for uploads, mapping changes, scenario edits, and pack generation.

## Success Criteria
- All KPI math is deterministic and tested.
- Excel pack generation is reproducible and validated with golden-file checks.
- MVP can be deployed locally via Docker Compose in under 10 minutes.

## Out of Scope (Phase 2)
- PDF export
- External connectors (QuickBooks, Stripe)
- SSO
- Complex cash flow modeling

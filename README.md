# Portfolio Reporting Studio

## What it is
Portfolio Reporting Studio is a multi-tenant reporting system for portfolio managers overseeing 50–75 startups. It standardizes monthly financials, computes deterministic KPIs, runs forecast scenarios, and exports Excel reporting packs.

## How it works
1. Upload monthly actuals using the canonical CSV template.
2. Map accounts into the canonical chart.
3. Generate KPI trends, forecasts, and scenario outputs.
4. Export Excel packs for company reporting.
5. Review portfolio dashboard and risk list.

## Run Instructions
```bash
make dev
make migrate
make seed
```

Access API docs at http://localhost:8000/docs

## Operator UI
Open http://localhost:8000/ for a minimal operator workflow (login, upload actuals, mappings, pack download).

## Demo
See `examples/demo_walkthrough.md`.

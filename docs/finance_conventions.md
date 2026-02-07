# Finance Conventions

## Sign Conventions
- Revenue and gross profit are positive.
- Operating expenses are positive (entered as positive values).
- EBITDA = Gross Profit - OpEx.
- Burn = max(0, -EBITDA).

## Runway
- `runway_months = cash_balance / max(1, average_monthly_burn_last_3m)`
- Cash balance is a canonical line item. If unavailable, set to 0 and runway is 0.

## Periods
- Monthly period dates should use the first day of the month (`YYYY-MM-01`).

## Rounding
- Calculations are performed in full precision; formatting/rounding is applied in reports.

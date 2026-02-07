from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

import pandas as pd

CANONICAL_CATEGORIES = [
    "Revenue",
    "COGS",
    "Sales & Marketing",
    "R&D",
    "G&A",
    "Other OpEx",
    "Cash",
]


@dataclass(frozen=True)
class ActualRecord:
    period: date
    category: str
    amount: float


@dataclass(frozen=True)
class KPIResult:
    period: date
    revenue: float
    gross_profit: float
    gross_margin: float
    opex: float
    ebitda: float
    burn: float
    cash_balance: float
    runway_months: float


def _safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def compute_kpis(actuals: Iterable[ActualRecord]) -> list[KPIResult]:
    df = pd.DataFrame([a.__dict__ for a in actuals])
    if df.empty:
        return []
    grouped = df.pivot_table(index="period", columns="category", values="amount", aggfunc="sum").fillna(0)
    results: list[KPIResult] = []
    for period, row in grouped.iterrows():
        revenue = float(row.get("Revenue", 0))
        cogs = float(row.get("COGS", 0))
        gross_profit = revenue - cogs
        gross_margin = _safe_divide(gross_profit, revenue)
        opex = float(row.get("Sales & Marketing", 0)) + float(row.get("R&D", 0)) + float(
            row.get("G&A", 0)
        ) + float(row.get("Other OpEx", 0))
        ebitda = gross_profit - opex
        cash_balance = float(row.get("Cash", 0))
        burn = max(0.0, -ebitda)
        results.append(
            KPIResult(
                period=period,
                revenue=revenue,
                gross_profit=gross_profit,
                gross_margin=gross_margin,
                opex=opex,
                ebitda=ebitda,
                burn=burn,
                cash_balance=cash_balance,
                runway_months=0.0,
            )
        )
    results.sort(key=lambda r: r.period)
    for idx, result in enumerate(results):
        recent = results[max(0, idx - 2) : idx + 1]
        avg_burn = sum(r.burn for r in recent) / max(1, len(recent))
        runway = result.cash_balance / max(1.0, avg_burn)
        results[idx] = KPIResult(
            period=result.period,
            revenue=result.revenue,
            gross_profit=result.gross_profit,
            gross_margin=result.gross_margin,
            opex=result.opex,
            ebitda=result.ebitda,
            burn=result.burn,
            cash_balance=result.cash_balance,
            runway_months=runway,
        )
    return results


def forecast(base_kpis: list[KPIResult], months: int, revenue_growth: float, gross_margin: float, opex_growth: float) -> list[KPIResult]:
    if not base_kpis:
        return []
    last = base_kpis[-1]
    period = last.period
    results: list[KPIResult] = []
    revenue = last.revenue
    opex = last.opex
    cash = last.cash_balance
    for _ in range(months):
        period = (period.replace(day=1) + pd.DateOffset(months=1)).date()
        revenue *= 1 + revenue_growth
        gross_profit = revenue * gross_margin
        opex *= 1 + opex_growth
        ebitda = gross_profit - opex
        burn = max(0.0, -ebitda)
        cash = max(0.0, cash - burn)
        runway = cash / max(1.0, burn)
        results.append(
            KPIResult(
                period=period,
                revenue=revenue,
                gross_profit=gross_profit,
                gross_margin=gross_margin,
                opex=opex,
                ebitda=ebitda,
                burn=burn,
                cash_balance=cash,
                runway_months=runway,
            )
        )
    return results


def sensitivity_grid(
    base_kpis: list[KPIResult],
    revenue_growth_range: list[float],
    gross_margin_range: list[float],
    opex_growth: float,
    months: int = 12,
) -> list[dict[str, float]]:
    grid: list[dict[str, float]] = []
    for rg in revenue_growth_range:
        for gm in gross_margin_range:
            forecasted = forecast(base_kpis, months, rg, gm, opex_growth)
            runway = forecasted[-1].runway_months if forecasted else 0.0
            grid.append({"revenue_growth": rg, "gross_margin": gm, "runway_months": runway})
    return grid

from datetime import date

from app.services.finance import ActualRecord, compute_kpis, forecast


def test_compute_kpis_runway():
    actuals = [
        ActualRecord(date(2024, 1, 1), "Revenue", 1000),
        ActualRecord(date(2024, 1, 1), "COGS", 200),
        ActualRecord(date(2024, 1, 1), "Sales & Marketing", 500),
        ActualRecord(date(2024, 1, 1), "Cash", 3000),
    ]
    kpis = compute_kpis(actuals)
    assert kpis[0].gross_profit == 800
    assert kpis[0].ebitda == 300
    assert kpis[0].runway_months >= 0


def test_forecast_length():
    actuals = [
        ActualRecord(date(2024, 1, 1), "Revenue", 1000),
        ActualRecord(date(2024, 1, 1), "COGS", 200),
        ActualRecord(date(2024, 1, 1), "Sales & Marketing", 300),
        ActualRecord(date(2024, 1, 1), "Cash", 5000),
    ]
    kpis = compute_kpis(actuals)
    forecasted = forecast(kpis, 12, 0.05, 0.6, 0.03)
    assert len(forecasted) == 12

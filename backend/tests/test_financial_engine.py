import pytest

from app.models import FinancialSnapshot
from app.services.financial_engine import compute_financial_metrics


def make_snapshot(**overrides) -> FinancialSnapshot:
    defaults = dict(
        monthly_revenue=50_000,
        monthly_cogs=15_000,
        monthly_operating_expenses=60_000,
        cash_balance=500_000,
        new_customers_this_month=10,
        total_customers=100,
        churned_customers_this_month=2,
        sales_marketing_spend=20_000,
        avg_revenue_per_account=500,
        avg_price_per_unit=100,
        avg_variable_cost_per_unit=30,
        fixed_costs_monthly=25_000,
    )
    defaults.update(overrides)
    return FinancialSnapshot(**defaults)


def test_gross_margin():
    fs = make_snapshot(monthly_revenue=100_000, monthly_cogs=30_000)
    metrics = compute_financial_metrics(fs)
    # (100000 - 30000) / 100000 = 70%
    assert metrics["gross_margin_pct"] == 70.0


def test_net_burn_and_runway():
    fs = make_snapshot(
        monthly_revenue=50_000,
        monthly_cogs=15_000,
        monthly_operating_expenses=60_000,
        cash_balance=350_000,
    )
    metrics = compute_financial_metrics(fs)
    # net burn = 60000 + 15000 - 50000 = 25000
    assert metrics["net_burn_monthly"] == 25_000
    # runway = 350000 / 25000 = 14 months
    assert metrics["runway_months"] == 14.0


def test_runway_is_none_when_profitable():
    fs = make_snapshot(monthly_revenue=200_000, monthly_cogs=20_000, monthly_operating_expenses=50_000)
    metrics = compute_financial_metrics(fs)
    assert metrics["net_burn_monthly"] < 0
    assert metrics["runway_months"] is None


def test_cac():
    fs = make_snapshot(sales_marketing_spend=20_000, new_customers_this_month=10)
    metrics = compute_financial_metrics(fs)
    assert metrics["cac"] == 2_000


def test_cac_none_when_no_new_customers():
    fs = make_snapshot(new_customers_this_month=0)
    metrics = compute_financial_metrics(fs)
    assert metrics["cac"] is None


def test_ltv_and_ltv_to_cac():
    # gross margin = (50000-15000)/50000 = 70%
    # churn = 2/100 = 2% monthly -> avg lifetime = 50 months
    # ltv = arpa(500) * 0.70 * 50 = 17500
    fs = make_snapshot()
    metrics = compute_financial_metrics(fs)
    assert metrics["ltv"] == 17_500.0
    # cac = 20000/10 = 2000; ltv/cac = 17500/2000 = 8.75
    assert metrics["ltv_to_cac"] == 8.75


def test_break_even():
    # contribution margin = 100 - 30 = 70; break-even units = 25000/70 = 357.1
    fs = make_snapshot(avg_price_per_unit=100, avg_variable_cost_per_unit=30, fixed_costs_monthly=25_000)
    metrics = compute_financial_metrics(fs)
    assert metrics["break_even_units"] == pytest.approx(357.1, rel=1e-2)
    # break-even revenue = fixed_costs / (contribution_margin/price) = 25000 / 0.7 = 35714.3
    assert metrics["break_even_revenue"] == pytest.approx(35714.29, rel=1e-2)


def test_annualized_revenue_run_rate():
    fs = make_snapshot(monthly_revenue=80_000)
    metrics = compute_financial_metrics(fs)
    assert metrics["annualized_revenue_run_rate"] == 960_000

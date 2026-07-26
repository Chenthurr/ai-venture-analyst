"""
Financial analysis engine.

Every metric here is a standard, correctly-implemented VC/startup finance
formula. No placeholders -- each function is independently testable
(see backend/tests/test_financial_engine.py).
"""
from __future__ import annotations

from typing import Optional

from app.models import FinancialSnapshot


def safe_div(numerator: float, denominator: float) -> Optional[float]:
    if denominator == 0:
        return None
    return numerator / denominator


def compute_financial_metrics(fs: FinancialSnapshot) -> dict:
    revenue = fs.monthly_revenue
    cogs = fs.monthly_cogs
    opex = fs.monthly_operating_expenses

    gross_profit = revenue - cogs
    gross_margin_pct = (safe_div(gross_profit, revenue) or 0.0) * 100

    # Net income (simplified: no separate interest/tax/D&A lines collected in v1,
    # so operating income doubles as net income here; EBITDA below adds back
    # nothing extra since D&A isn't separately captured yet).
    net_income = gross_profit - opex
    net_margin_pct = (safe_div(net_income, revenue) or 0.0) * 100

    # Net burn: cash consumed per month. Positive = burning cash.
    net_burn_monthly = opex + cogs - revenue

    runway_months = None
    if net_burn_monthly > 0:
        runway_months = safe_div(fs.cash_balance, net_burn_monthly)

    # CAC: total S&M spend / new customers acquired this period
    cac = safe_div(fs.sales_marketing_spend, fs.new_customers_this_month)

    # Monthly churn rate = churned / total customers at start of period
    # (approximated here using total_customers as the base).
    monthly_churn_rate = safe_div(fs.churned_customers_this_month, fs.total_customers)
    monthly_churn_rate_pct = (monthly_churn_rate or 0.0) * 100 if monthly_churn_rate is not None else None

    # LTV = ARPA * gross margin % * average customer lifetime (1 / churn rate)
    ltv = None
    if fs.avg_revenue_per_account and monthly_churn_rate and monthly_churn_rate > 0:
        avg_lifetime_months = 1 / monthly_churn_rate
        ltv = fs.avg_revenue_per_account * (gross_margin_pct / 100) * avg_lifetime_months

    ltv_to_cac = None
    if ltv is not None and cac:
        ltv_to_cac = safe_div(ltv, cac)

    # CAC payback period (months) = CAC / (ARPA * gross margin %)
    cac_payback_months = None
    if cac is not None and fs.avg_revenue_per_account:
        monthly_gross_profit_per_account = fs.avg_revenue_per_account * (gross_margin_pct / 100)
        cac_payback_months = safe_div(cac, monthly_gross_profit_per_account)

    # EBITDA (monthly) -- v1 has no separate D&A input, so EBITDA == operating income.
    ebitda_monthly = net_income

    # Break-even analysis (unit economics based)
    contribution_margin = fs.avg_price_per_unit - fs.avg_variable_cost_per_unit
    contribution_margin_pct = None
    break_even_units = None
    break_even_revenue = None
    if fs.avg_price_per_unit > 0:
        contribution_margin_pct = safe_div(contribution_margin, fs.avg_price_per_unit)
        if contribution_margin_pct and contribution_margin_pct != 0:
            contribution_margin_pct *= 100
            break_even_units = safe_div(fs.fixed_costs_monthly, contribution_margin)
            break_even_revenue = safe_div(fs.fixed_costs_monthly, contribution_margin / fs.avg_price_per_unit)

    annualized_revenue_run_rate = revenue * 12

    return {
        "gross_margin_pct": round(gross_margin_pct, 2),
        "net_margin_pct": round(net_margin_pct, 2),
        "net_burn_monthly": round(net_burn_monthly, 2),
        "runway_months": round(runway_months, 1) if runway_months is not None else None,
        "cac": round(cac, 2) if cac is not None else None,
        "ltv": round(ltv, 2) if ltv is not None else None,
        "ltv_to_cac": round(ltv_to_cac, 2) if ltv_to_cac is not None else None,
        "cac_payback_months": round(cac_payback_months, 1) if cac_payback_months is not None else None,
        "ebitda_monthly": round(ebitda_monthly, 2),
        "break_even_units": round(break_even_units, 1) if break_even_units is not None else None,
        "break_even_revenue": round(break_even_revenue, 2) if break_even_revenue is not None else None,
        "contribution_margin_pct": round(contribution_margin_pct, 2) if contribution_margin_pct is not None else None,
        "monthly_churn_rate_pct": round(monthly_churn_rate_pct, 2) if monthly_churn_rate_pct is not None else None,
        "annualized_revenue_run_rate": round(annualized_revenue_run_rate, 2),
    }

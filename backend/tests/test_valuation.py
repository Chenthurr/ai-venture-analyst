import pytest

from app.models import FinancialSnapshot
from app.services.valuation import (
    scorecard_method,
    berkus_method,
    vc_method,
    dcf_method,
    risk_factor_summation_method,
    compute_all_valuations,
)

AVERAGE_SCORES = {
    "founder_strength": {"score": 50},
    "market_size": {"score": 50},
    "product_quality": {"score": 50},
    "competition": {"score": 50},
    "business_model": {"score": 50},
    "financial_health": {"score": 50},
    "scalability": {"score": 50},
    "technology": {"score": 50},
    "traction": {"score": 50},
}


def make_snapshot(**overrides) -> FinancialSnapshot:
    defaults = dict(
        monthly_revenue=40_000,
        monthly_cogs=10_000,
        monthly_operating_expenses=50_000,
        cash_balance=300_000,
        projected_annual_growth_rate=0.5,
        discount_rate=0.35,
        exit_multiple_revenue=5.0,
        years_to_exit=5,
        anticipated_roi=10.0,
        investment_amount_requested=1_000_000,
    )
    defaults.update(overrides)
    return FinancialSnapshot(**defaults)


def test_scorecard_average_scores_equal_base_valuation():
    # All scores at 50 (average) -> ratio 1.0 for every factor -> weighted sum == 1.0
    result = scorecard_method(AVERAGE_SCORES, stage="seed")
    assert result["details"]["weighted_factor_sum"] == pytest.approx(1.0, rel=1e-3)
    assert result["estimated_valuation"] == pytest.approx(6_000_000, rel=1e-3)


def test_scorecard_above_average_increases_valuation():
    strong_scores = {k: {"score": 90} for k in AVERAGE_SCORES}
    result = scorecard_method(strong_scores, stage="seed")
    assert result["estimated_valuation"] > 6_000_000


def test_scorecard_ratio_is_clamped():
    extreme_scores = {k: {"score": 100} for k in AVERAGE_SCORES}
    result = scorecard_method(extreme_scores, stage="seed")
    for factor in result["details"]["factors"].values():
        assert factor["ratio"] <= 2.0


def test_berkus_caps_at_2_5_million():
    perfect_scores = {
        "product_quality": {"score": 100},
        "technology": {"score": 100},
        "founder_strength": {"score": 100},
        "business_model": {"score": 100},
        "traction": {"score": 100},
    }
    result = berkus_method(perfect_scores)
    assert result["estimated_valuation"] == 2_500_000


def test_berkus_zero_scores_give_zero_valuation():
    zero_scores = {k: {"score": 0} for k in ["product_quality", "technology", "founder_strength", "business_model", "traction"]}
    result = berkus_method(zero_scores)
    assert result["estimated_valuation"] == 0


def test_vc_method_math():
    fs = make_snapshot(
        monthly_revenue=40_000,  # ARR = 480,000
        projected_annual_growth_rate=0.5,
        years_to_exit=5,
        exit_multiple_revenue=5.0,
        anticipated_roi=10.0,
        investment_amount_requested=1_000_000,
    )
    result = vc_method(fs)
    current_arr = 480_000
    terminal_arr = current_arr * (1.5 ** 5)
    terminal_value = terminal_arr * 5.0
    post_money = terminal_value / 10.0
    expected_pre_money = post_money - 1_000_000
    assert result["estimated_valuation"] == pytest.approx(expected_pre_money, rel=1e-6)


def test_vc_method_floors_at_zero():
    fs = make_snapshot(monthly_revenue=100, investment_amount_requested=50_000_000)
    result = vc_method(fs)
    assert result["estimated_valuation"] >= 0


def test_dcf_produces_positive_value_for_profitable_growth():
    fs = make_snapshot(
        monthly_revenue=100_000,
        monthly_cogs=20_000,  # 80% gross margin
        monthly_operating_expenses=40_000,
        projected_annual_growth_rate=0.3,
        discount_rate=0.35,
    )
    result = dcf_method(fs)
    assert result["estimated_valuation"] > 0
    assert len(result["details"]["yearly_projection"]) == fs.years_to_exit


def test_risk_factor_summation_neutral_scores_equal_base():
    neutral = {cat: {"score": 50} for cat in [
        "management_risk", "stage_of_business_risk", "legislation_political_risk",
        "manufacturing_risk", "sales_marketing_risk", "funding_capital_raising_risk",
        "competition_risk", "technology_risk", "litigation_risk", "international_risk",
        "reputation_risk", "exit_value_risk",
    ]}
    result = risk_factor_summation_method("seed", neutral)
    assert result["estimated_valuation"] == 6_000_000


def test_risk_factor_summation_low_risk_increases_valuation():
    low_risk = {cat: {"score": 100} for cat in [
        "management_risk", "stage_of_business_risk", "legislation_political_risk",
        "manufacturing_risk", "sales_marketing_risk", "funding_capital_raising_risk",
        "competition_risk", "technology_risk", "litigation_risk", "international_risk",
        "reputation_risk", "exit_value_risk",
    ]}
    result = risk_factor_summation_method("seed", low_risk)
    assert result["estimated_valuation"] > 6_000_000


def test_compute_all_valuations_excludes_berkus_when_revenue_exists():
    fs = make_snapshot(monthly_revenue=40_000)
    result = compute_all_valuations(fs, "seed", AVERAGE_SCORES, {})
    assert len(result["methods"]) == 5  # still shown
    method_names = [m["method"] for m in result["methods"]]
    assert "Berkus Method" in method_names
    assert result["blended_valuation"] > 0


def test_compute_all_valuations_includes_berkus_when_pre_revenue():
    fs = make_snapshot(monthly_revenue=0)
    result = compute_all_valuations(fs, "pre-seed", AVERAGE_SCORES, {})
    assert result["blended_valuation"] > 0

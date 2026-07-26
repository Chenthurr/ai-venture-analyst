"""
Valuation engine.

Implements five real, standard early-stage valuation methodologies:
  1. Scorecard Method
  2. Berkus Method
  3. VC Method
  4. Discounted Cash Flow (DCF)
  5. Risk Factor Summation Method

Each returns its own estimate + a full breakdown of the calculation so the
frontend (and the user) can see exactly how the number was produced --
nothing is a black box.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from app.models import FinancialSnapshot

# Typical U.S. median pre-money valuation for a comparable-stage company.
# This is an editable assumption, not a hidden constant -- it is surfaced
# in every method's `details` so the user can see and challenge it.
STAGE_BASE_VALUATIONS = {
    "pre-seed": 3_000_000,
    "seed": 6_000_000,
    "series-a": 18_000_000,
    "series-b": 45_000_000,
    "growth": 100_000_000,
}


def _base_valuation_for_stage(stage: Optional[str]) -> float:
    if not stage:
        return STAGE_BASE_VALUATIONS["seed"]
    return STAGE_BASE_VALUATIONS.get(stage.lower().strip(), STAGE_BASE_VALUATIONS["seed"])


# ---------------------------------------------------------------------------
# 1. Scorecard Method
# ---------------------------------------------------------------------------
# Standard Bill Payne weightings across comparison categories.
SCORECARD_WEIGHTS = {
    "founder_strength": 0.30,      # "Management" in the classic method
    "market_size": 0.25,
    "product_quality": 0.15,       # "Product/Technology"
    "competition": 0.10,
    "business_model": 0.10,        # "Marketing/Sales channels"
    "financial_health": 0.05,      # "Need for additional investment"
    "scalability": 0.05,           # "Other"
}


def scorecard_method(scores: Dict[str, dict], stage: Optional[str]) -> dict:
    """
    scores: {category: {"score": 0-100, "reasoning": str}, ...} from the AI
    scoring module. A score of 50 == "average" comparable startup (ratio 1.0).
    Ratios are clamped to [0.4, 2.0] which mirrors the standard method's
    practical range (extreme multipliers rarely reflect real comparables).
    """
    base = _base_valuation_for_stage(stage)
    weighted_sum = 0.0
    factor_breakdown = {}
    for category, weight in SCORECARD_WEIGHTS.items():
        raw_score = (scores.get(category) or {}).get("score", 50)
        ratio = raw_score / 50.0
        ratio = max(0.4, min(ratio, 2.0))
        weighted_sum += weight * ratio
        factor_breakdown[category] = {"score": raw_score, "ratio": ratio, "weight": weight}

    valuation = base * weighted_sum
    return {
        "method": "Scorecard Method",
        "estimated_valuation": round(valuation, 2),
        "details": {
            "base_stage_valuation": base,
            "weighted_factor_sum": round(weighted_sum, 3),
            "factors": factor_breakdown,
        },
        "notes": (
            "Base valuation is a comparable median for the company's funding stage, "
            "adjusted by weighted factor ratios (1.0 = average comparable startup)."
        ),
    }


# ---------------------------------------------------------------------------
# 2. Berkus Method
# ---------------------------------------------------------------------------
BERKUS_MAX_PER_FACTOR = 500_000

BERKUS_FACTORS = [
    ("sound_idea", "Sound idea (basic value, product risk)"),
    ("prototype", "Prototype/technology (reduces technology risk)"),
    ("quality_team", "Quality management team (reduces execution risk)"),
    ("strategic_relationships", "Strategic relationships (reduces market risk)"),
    ("product_rollout", "Product rollout or early sales (reduces production risk)"),
]


def berkus_method(scores: Dict[str, dict]) -> dict:
    """
    Classic Berkus Method for pre-revenue / early-revenue startups: up to
    $500k assigned per qualitative factor, capped at $2.5M total.
    We derive each factor's fraction of $500k from the 0-100 AI score for the
    closest matching category.
    """
    mapping = {
        "sound_idea": "product_quality",
        "prototype": "technology",
        "quality_team": "founder_strength",
        "strategic_relationships": "business_model",
        "product_rollout": "traction",
    }
    breakdown = {}
    total = 0.0
    for factor_key, description in BERKUS_FACTORS:
        score_key = mapping[factor_key]
        raw_score = (scores.get(score_key) or {}).get("score", 50)
        value = BERKUS_MAX_PER_FACTOR * (raw_score / 100.0)
        breakdown[factor_key] = {
            "description": description,
            "score": raw_score,
            "value": round(value, 2),
        }
        total += value

    return {
        "method": "Berkus Method",
        "estimated_valuation": round(total, 2),
        "details": {"factors": breakdown, "max_possible": BERKUS_MAX_PER_FACTOR * 5},
        "notes": (
            "Assigns up to $500k per qualitative risk-reduction factor; "
            "intended for pre-revenue or very early revenue startups."
        ),
    }


# ---------------------------------------------------------------------------
# 3. VC Method
# ---------------------------------------------------------------------------

def vc_method(fs: FinancialSnapshot) -> dict:
    """
    Terminal Value = current ARR grown at the projected annual growth rate for
    `years_to_exit`, multiplied by an exit revenue multiple.
    Post-money = Terminal Value / Anticipated ROI (the multiple investors require).
    Pre-money = Post-money - investment requested.
    """
    current_arr = fs.monthly_revenue * 12
    terminal_arr = current_arr * ((1 + fs.projected_annual_growth_rate) ** fs.years_to_exit)
    terminal_value = terminal_arr * fs.exit_multiple_revenue

    roi = fs.anticipated_roi if fs.anticipated_roi > 0 else 10.0
    post_money = terminal_value / roi
    pre_money = post_money - fs.investment_amount_requested

    return {
        "method": "VC Method",
        "estimated_valuation": round(max(pre_money, 0), 2),
        "details": {
            "current_arr": round(current_arr, 2),
            "years_to_exit": fs.years_to_exit,
            "projected_annual_growth_rate": fs.projected_annual_growth_rate,
            "terminal_arr": round(terminal_arr, 2),
            "exit_multiple_revenue": fs.exit_multiple_revenue,
            "terminal_value": round(terminal_value, 2),
            "anticipated_roi": roi,
            "post_money_valuation": round(post_money, 2),
            "investment_amount_requested": fs.investment_amount_requested,
        },
        "notes": (
            "Pre-money = (Terminal Value / Anticipated ROI) - Investment Requested. "
            "Terminal Value = projected exit-year ARR x exit revenue multiple."
        ),
    }


# ---------------------------------------------------------------------------
# 4. Discounted Cash Flow (simplified, revenue-driven)
# ---------------------------------------------------------------------------

def dcf_method(fs: FinancialSnapshot) -> dict:
    """
    Projects monthly net cash flow (using current gross margin & opex ratios)
    forward at the given annual growth rate for `years_to_exit`, discounts
    each year's cash flow at `discount_rate`, and adds a terminal value using
    the Gordon Growth (perpetuity) formula with a conservative 3% terminal
    growth rate.
    """
    current_arr = fs.monthly_revenue * 12
    gross_margin = 1 - (fs.monthly_cogs / fs.monthly_revenue) if fs.monthly_revenue else 0.0
    opex_annual = fs.monthly_operating_expenses * 12

    discount_rate = fs.discount_rate if fs.discount_rate > 0 else 0.35
    growth = fs.projected_annual_growth_rate
    terminal_growth = 0.03

    yearly_cash_flows = []
    revenue = current_arr
    pv_sum = 0.0
    for year in range(1, fs.years_to_exit + 1):
        revenue = revenue * (1 + growth)
        gross_profit = revenue * gross_margin
        # Opex scales at half the revenue growth rate (operating leverage assumption)
        year_opex = opex_annual * ((1 + growth / 2) ** year)
        free_cash_flow = gross_profit - year_opex
        discount_factor = (1 + discount_rate) ** year
        pv = free_cash_flow / discount_factor
        pv_sum += pv
        yearly_cash_flows.append({
            "year": year,
            "revenue": round(revenue, 2),
            "free_cash_flow": round(free_cash_flow, 2),
            "present_value": round(pv, 2),
        })

    terminal_fcf = yearly_cash_flows[-1]["free_cash_flow"] * (1 + terminal_growth) if yearly_cash_flows else 0
    terminal_value = (
        terminal_fcf / (discount_rate - terminal_growth)
        if discount_rate > terminal_growth else 0
    )
    pv_terminal_value = terminal_value / ((1 + discount_rate) ** fs.years_to_exit)

    enterprise_value = pv_sum + pv_terminal_value

    return {
        "method": "Discounted Cash Flow",
        "estimated_valuation": round(max(enterprise_value, 0), 2),
        "details": {
            "gross_margin_used": round(gross_margin, 3),
            "discount_rate": discount_rate,
            "terminal_growth_rate": terminal_growth,
            "yearly_projection": yearly_cash_flows,
            "pv_of_projected_cash_flows": round(pv_sum, 2),
            "terminal_value": round(terminal_value, 2),
            "pv_of_terminal_value": round(pv_terminal_value, 2),
        },
        "notes": (
            "Free cash flow projected off current gross margin and an operating-leverage "
            "opex assumption, discounted at the given rate; terminal value via Gordon Growth."
        ),
    }


# ---------------------------------------------------------------------------
# 5. Risk Factor Summation Method
# ---------------------------------------------------------------------------
RISK_FACTOR_STEP = 250_000  # standard $250k per risk-factor step

RISK_CATEGORIES = [
    "management_risk",
    "stage_of_business_risk",
    "legislation_political_risk",
    "manufacturing_risk",
    "sales_marketing_risk",
    "funding_capital_raising_risk",
    "competition_risk",
    "technology_risk",
    "litigation_risk",
    "international_risk",
    "reputation_risk",
    "exit_value_risk",
]


def risk_factor_summation_method(stage: Optional[str], risk_scores: Dict[str, dict]) -> dict:
    """
    risk_scores: {category: {"score": 0-100}} where 100 = very low risk
    (very favorable) and 0 = very high risk. Each category is converted to a
    standard -2..+2 rating (in $250k increments) added to the stage base
    valuation, mirroring the classic Risk Factor Summation Method.
    """
    base = _base_valuation_for_stage(stage)
    breakdown = {}
    total_adjustment = 0.0
    for category in RISK_CATEGORIES:
        raw_score = (risk_scores.get(category) or {}).get("score", 50)
        # Map 0-100 -> -2..+2 rating
        rating = round((raw_score - 50) / 25, 1)
        rating = max(-2.0, min(rating, 2.0))
        adjustment = rating * RISK_FACTOR_STEP
        breakdown[category] = {"score": raw_score, "rating": rating, "adjustment": adjustment}
        total_adjustment += adjustment

    valuation = base + total_adjustment
    return {
        "method": "Risk Factor Summation",
        "estimated_valuation": round(max(valuation, 0), 2),
        "details": {
            "base_stage_valuation": base,
            "total_adjustment": round(total_adjustment, 2),
            "risk_factors": breakdown,
        },
        "notes": (
            "Stage base valuation adjusted +/- $250k per risk category, rated -2 to +2 "
            "(higher AI risk score = lower risk = more positive adjustment)."
        ),
    }


def compute_all_valuations(
    fs: FinancialSnapshot,
    stage: Optional[str],
    scores: Dict[str, dict],
    risk_scores: Dict[str, dict],
) -> dict:
    methods: List[dict] = [
        scorecard_method(scores, stage),
        berkus_method(scores),
        vc_method(fs),
        dcf_method(fs),
        risk_factor_summation_method(stage, risk_scores),
    ]
    # Berkus is only meaningful pre-revenue/early-revenue; still shown for
    # transparency but excluded from the blended average once there's real ARR,
    # since VC Method / DCF become more reliable at that point.
    has_revenue = fs.monthly_revenue > 0
    blend_pool = [m for m in methods if not (has_revenue and m["method"] == "Berkus Method")]
    blended = sum(m["estimated_valuation"] for m in blend_pool) / len(blend_pool)

    return {"methods": methods, "blended_valuation": round(blended, 2)}

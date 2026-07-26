from app.models import Project, AnalysisReport
from app.services import report_generator


def make_project(**overrides) -> Project:
    defaults = dict(
        id="proj-1",
        owner_id="user-1",
        company_name="Acme AI",
        industry="DevTools",
        country="US",
        stage="seed",
        founders="Jane Doe",
        one_liner="AI for devs",
    )
    defaults.update(overrides)
    return Project(**defaults)


def make_analysis(**overrides) -> AnalysisReport:
    defaults = dict(
        id="analysis-1",
        project_id="proj-1",
        executive_summary="Acme AI is a promising devtools startup with strong early traction.",
        swot={
            "strengths": ["Strong technical team"],
            "weaknesses": ["Limited sales experience"],
            "opportunities": ["Expanding TAM"],
            "threats": ["Well-funded competitors"],
        },
        scores={
            "founder_strength": {"score": 80, "reasoning": "Experienced team [1]"},
            "market_size": {"score": 65, "reasoning": "Large addressable market [2]"},
        },
        risk_scores={
            "management_risk": {"score": 70, "reasoning": "Low risk"},
            "competition_risk": {"score": 40, "reasoning": "Crowded space"},
        },
        investment_memo="## Overview\n\nAcme AI builds developer tools.\n\n## Recommendation\n\nInvest.",
        citations=[{"claim": "Strong technical team", "filename": "deck.pdf", "chunk_index": 2}],
        financial_metrics={
            "gross_margin_pct": 70.0,
            "net_margin_pct": -10.0,
            "net_burn_monthly": 25000.0,
            "runway_months": 20.0,
            "cac": 2000.0,
            "ltv": 17500.0,
            "ltv_to_cac": 8.75,
            "cac_payback_months": 5.7,
            "ebitda_monthly": -5000.0,
            "break_even_revenue": 35714.29,
            "monthly_churn_rate_pct": 2.0,
            "annualized_revenue_run_rate": 600000.0,
        },
        valuation={
            "methods": [
                {"method": "Scorecard Method", "estimated_valuation": 6_000_000, "details": {}, "notes": "n/a"},
                {"method": "VC Method", "estimated_valuation": 1_278_125, "details": {}, "notes": "n/a"},
            ],
            "blended_valuation": 3_500_000,
        },
        model_used="gpt-4.1",
    )
    defaults.update(overrides)
    return AnalysisReport(**defaults)


def test_investment_memo_pdf_is_valid_pdf():
    project = make_project()
    analysis = make_analysis()
    pdf_bytes = report_generator.generate_investment_memo_pdf(
        project, analysis, analysis.financial_metrics, analysis.valuation
    )
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000


def test_investment_memo_pdf_handles_missing_analysis():
    project = make_project()
    pdf_bytes = report_generator.generate_investment_memo_pdf(project, None, None, None)
    assert pdf_bytes.startswith(b"%PDF")


def test_board_report_pdf_is_valid_pdf():
    project = make_project()
    analysis = make_analysis()
    pdf_bytes = report_generator.generate_board_report_pdf(
        project, analysis, analysis.financial_metrics, analysis.valuation
    )
    assert pdf_bytes.startswith(b"%PDF")


def test_investor_report_pdf_is_valid_pdf():
    project = make_project()
    analysis = make_analysis()
    pdf_bytes = report_generator.generate_investor_report_pdf(
        project, analysis, analysis.financial_metrics, analysis.valuation
    )
    assert pdf_bytes.startswith(b"%PDF")


def test_due_diligence_checklist_pdf_requires_no_analysis():
    project = make_project()
    pdf_bytes = report_generator.generate_due_diligence_checklist_pdf(project)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000

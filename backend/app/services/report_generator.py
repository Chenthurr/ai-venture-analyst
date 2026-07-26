"""
Report generation service.

Produces real, formatted PDF documents with reportlab's Platypus layer --
actual tables, styled headings, and page flow, not a wrapped screenshot or
a plain-text dump. Every report pulls from data that's already been computed
by the financial engine, valuation engine, and AI analysis service; this
module is purely responsible for presentation.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    ListFlowable,
    ListItem,
)

from app import models

GOLD = colors.HexColor("#8A6D2F")
INK = colors.HexColor("#12161F")
MUTED = colors.HexColor("#5A6274")
POSITIVE = colors.HexColor("#2E6B45")
NEGATIVE = colors.HexColor("#8A3A2F")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "MemoTitle",
            parent=styles["Title"],
            fontSize=22,
            leading=26,
            textColor=INK,
        )
    )
    styles.add(
        ParagraphStyle(
            "MemoSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            textColor=GOLD,
            spaceAfter=18,
        )
    )
    styles.add(
        ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=INK,
            spaceBefore=18,
            spaceAfter=8,
            borderWidth=0,
        )
    )
    styles.add(
        ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#2A2E38"),
        )
    )
    styles.add(
        ParagraphStyle(
            "Muted",
            parent=styles["Normal"],
            fontSize=8.5,
            textColor=MUTED,
        )
    )
    return styles


def _money(n: Optional[float]) -> str:
    if n is None:
        return "—"
    if abs(n) >= 1_000_000:
        return f"${n / 1_000_000:,.2f}M"
    if abs(n) >= 1_000:
        return f"${n / 1_000:,.0f}K"
    return f"${n:,.0f}"


def _pct(n: Optional[float]) -> str:
    return "—" if n is None else f"{n:.1f}%"


def _num(n: Optional[float], suffix: str = "") -> str:
    return "—" if n is None else f"{n:,.1f}{suffix}"


def _table_style(header_bg=INK) -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8DCE3")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F6F8")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
    )


def _header_block(styles, project: models.Project, report_title: str):
    flow = [
        Paragraph(project.company_name, styles["MemoTitle"]),
        Paragraph(
            f"{report_title} &nbsp;·&nbsp; {project.industry or 'Industry unspecified'} "
            f"&nbsp;·&nbsp; {project.stage or 'Stage unspecified'} &nbsp;·&nbsp; "
            f"Generated {datetime.utcnow().strftime('%B %d, %Y')}",
            styles["MemoSubtitle"],
        ),
    ]
    return flow


def _financial_metrics_table(styles, metrics: Optional[dict]):
    if not metrics:
        return [Paragraph("No financial data submitted for this company yet.", styles["Muted"])]
    rows = [
        ["Metric", "Value"],
        ["Gross Margin", _pct(metrics.get("gross_margin_pct"))],
        ["Net Margin", _pct(metrics.get("net_margin_pct"))],
        ["Net Burn (Monthly)", _money(metrics.get("net_burn_monthly"))],
        ["Runway", _num(metrics.get("runway_months"), " months") if metrics.get("runway_months") is not None else "Cash-flow positive"],
        ["CAC", _money(metrics.get("cac"))],
        ["LTV", _money(metrics.get("ltv"))],
        ["LTV : CAC", _num(metrics.get("ltv_to_cac"), "x")],
        ["CAC Payback Period", _num(metrics.get("cac_payback_months"), " months")],
        ["EBITDA (Monthly)", _money(metrics.get("ebitda_monthly"))],
        ["Break-even Revenue (Monthly)", _money(metrics.get("break_even_revenue"))],
        ["Monthly Churn Rate", _pct(metrics.get("monthly_churn_rate_pct"))],
        ["Annualized Revenue Run Rate", _money(metrics.get("annualized_revenue_run_rate"))],
    ]
    table = Table(rows, colWidths=[3 * inch, 2.5 * inch])
    table.setStyle(_table_style())
    return [table]


def _valuation_table(styles, valuation: Optional[dict]):
    if not valuation:
        return [Paragraph("No valuation has been computed for this company yet.", styles["Muted"])]
    rows = [["Method", "Estimated Valuation"]]
    for m in valuation.get("methods", []):
        rows.append([m["method"], _money(m["estimated_valuation"])])
    rows.append(["Blended Estimate", _money(valuation.get("blended_valuation"))])
    table = Table(rows, colWidths=[3 * inch, 2.5 * inch])
    style = _table_style()
    style.add("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")
    style.add("LINEABOVE", (0, -1), (-1, -1), 1, GOLD)
    table.setStyle(style)
    return [table]


def _score_table(styles, scores: Optional[dict], title_map: dict):
    if not scores:
        return [Paragraph("No AI scoring available yet.", styles["Muted"])]
    rows = [["Category", "Score (0-100)"]]
    for key, entry in scores.items():
        rows.append([title_map.get(key, key.replace("_", " ").title()), str(entry.get("score", "—"))])
    table = Table(rows, colWidths=[3 * inch, 2.5 * inch])
    table.setStyle(_table_style())
    return [table]


def _swot_block(styles, swot: Optional[dict]):
    if not swot:
        return [Paragraph("No SWOT analysis available yet.", styles["Muted"])]
    flow = []
    for label, key in [
        ("Strengths", "strengths"),
        ("Weaknesses", "weaknesses"),
        ("Opportunities", "opportunities"),
        ("Threats", "threats"),
    ]:
        items = swot.get(key) or []
        flow.append(Paragraph(f"<b>{label}</b>", styles["Body"]))
        if items:
            flow.append(
                ListFlowable(
                    [ListItem(Paragraph(i, styles["Body"])) for i in items],
                    bulletType="bullet",
                    leftIndent=14,
                )
            )
        else:
            flow.append(Paragraph("None identified.", styles["Muted"]))
        flow.append(Spacer(1, 6))
    return flow


SCORE_TITLE_MAP = {
    "founder_strength": "Founder Strength",
    "market_size": "Market Size",
    "product_quality": "Product Quality",
    "traction": "Traction",
    "competition": "Competition",
    "financial_health": "Financial Health",
    "business_model": "Business Model",
    "technology": "Technology",
    "scalability": "Scalability",
    "investment_readiness": "Investment Readiness",
}

RISK_TITLE_MAP = {
    "management_risk": "Management Risk",
    "stage_of_business_risk": "Stage of Business Risk",
    "legislation_political_risk": "Legislation / Political Risk",
    "manufacturing_risk": "Manufacturing Risk",
    "sales_marketing_risk": "Sales & Marketing Risk",
    "funding_capital_raising_risk": "Funding / Capital Raising Risk",
    "competition_risk": "Competition Risk",
    "technology_risk": "Technology Risk",
    "litigation_risk": "Litigation Risk",
    "international_risk": "International Risk",
    "reputation_risk": "Reputation Risk",
    "exit_value_risk": "Exit Value Risk",
}


def _build_doc(buffer: io.BytesIO) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        title="AI Venture Analyst Report",
    )


def generate_investment_memo_pdf(
    project: models.Project,
    analysis: Optional[models.AnalysisReport],
    financial_metrics: Optional[dict],
    valuation: Optional[dict],
) -> bytes:
    styles = _styles()
    buffer = io.BytesIO()
    doc = _build_doc(buffer)
    flow = _header_block(styles, project, "Investment Memo")

    flow.append(Paragraph("Executive Summary", styles["SectionHeading"]))
    flow.append(
        Paragraph(
            (analysis.executive_summary if analysis and analysis.executive_summary else "No AI analysis has been run yet."),
            styles["Body"],
        )
    )

    flow.append(Paragraph("Investment Scores", styles["SectionHeading"]))
    flow += _score_table(styles, analysis.scores if analysis else None, SCORE_TITLE_MAP)

    flow.append(Paragraph("SWOT Analysis", styles["SectionHeading"]))
    flow += _swot_block(styles, analysis.swot if analysis else None)

    flow.append(PageBreak())
    flow.append(Paragraph("Financial Analysis", styles["SectionHeading"]))
    flow += _financial_metrics_table(styles, financial_metrics)

    flow.append(Paragraph("Valuation", styles["SectionHeading"]))
    flow += _valuation_table(styles, valuation)

    flow.append(Paragraph("Risk Profile", styles["SectionHeading"]))
    flow += _score_table(styles, analysis.risk_scores if analysis else None, RISK_TITLE_MAP)

    if analysis and analysis.investment_memo:
        flow.append(PageBreak())
        flow.append(Paragraph("Full Memo Narrative", styles["SectionHeading"]))
        for para in analysis.investment_memo.split("\n\n"):
            if para.strip():
                flow.append(Paragraph(para.strip().replace("\n", "<br/>"), styles["Body"]))
                flow.append(Spacer(1, 6))

    if analysis and analysis.citations:
        flow.append(Paragraph("Sources Cited", styles["SectionHeading"]))
        rows = [["Claim", "Source Document"]]
        for c in analysis.citations[:25]:
            rows.append([c.get("claim", "")[:90], c.get("filename", "")])
        table = Table(rows, colWidths=[3.7 * inch, 1.8 * inch])
        table.setStyle(_table_style())
        flow.append(table)

    doc.build(flow)
    return buffer.getvalue()


def generate_board_report_pdf(
    project: models.Project,
    analysis: Optional[models.AnalysisReport],
    financial_metrics: Optional[dict],
    valuation: Optional[dict],
) -> bytes:
    """Board reports emphasize financial performance and risk over narrative."""
    styles = _styles()
    buffer = io.BytesIO()
    doc = _build_doc(buffer)
    flow = _header_block(styles, project, "Board Report")

    flow.append(Paragraph("Company Snapshot", styles["SectionHeading"]))
    flow.append(
        Paragraph(
            analysis.executive_summary if analysis and analysis.executive_summary else "No AI analysis has been run yet.",
            styles["Body"],
        )
    )

    flow.append(Paragraph("Financial Performance", styles["SectionHeading"]))
    flow += _financial_metrics_table(styles, financial_metrics)

    flow.append(Paragraph("Valuation Summary", styles["SectionHeading"]))
    flow += _valuation_table(styles, valuation)

    flow.append(Paragraph("Risk Profile", styles["SectionHeading"]))
    flow += _score_table(styles, analysis.risk_scores if analysis else None, RISK_TITLE_MAP)

    flow.append(Paragraph("Key Risks (Narrative)", styles["SectionHeading"]))
    threats = (analysis.swot or {}).get("threats", []) if analysis and analysis.swot else []
    weaknesses = (analysis.swot or {}).get("weaknesses", []) if analysis and analysis.swot else []
    if threats or weaknesses:
        flow.append(
            ListFlowable(
                [ListItem(Paragraph(i, styles["Body"])) for i in (weaknesses + threats)],
                bulletType="bullet",
                leftIndent=14,
            )
        )
    else:
        flow.append(Paragraph("No risks identified yet.", styles["Muted"]))

    doc.build(flow)
    return buffer.getvalue()


def generate_investor_report_pdf(
    project: models.Project,
    analysis: Optional[models.AnalysisReport],
    financial_metrics: Optional[dict],
    valuation: Optional[dict],
) -> bytes:
    """Investor reports lead with valuation and scoring -- what a prospective
    investor is most likely to want first."""
    styles = _styles()
    buffer = io.BytesIO()
    doc = _build_doc(buffer)
    flow = _header_block(styles, project, "Investor Report")

    flow.append(Paragraph("Investment Thesis", styles["SectionHeading"]))
    flow.append(
        Paragraph(
            analysis.executive_summary if analysis and analysis.executive_summary else "No AI analysis has been run yet.",
            styles["Body"],
        )
    )

    flow.append(Paragraph("Valuation", styles["SectionHeading"]))
    flow += _valuation_table(styles, valuation)

    flow.append(Paragraph("Investment Scores", styles["SectionHeading"]))
    flow += _score_table(styles, analysis.scores if analysis else None, SCORE_TITLE_MAP)

    flow.append(Paragraph("Financial Snapshot", styles["SectionHeading"]))
    flow += _financial_metrics_table(styles, financial_metrics)

    flow.append(Paragraph("Opportunities", styles["SectionHeading"]))
    opportunities = (analysis.swot or {}).get("opportunities", []) if analysis and analysis.swot else []
    if opportunities:
        flow.append(
            ListFlowable(
                [ListItem(Paragraph(i, styles["Body"])) for i in opportunities],
                bulletType="bullet",
                leftIndent=14,
            )
        )
    else:
        flow.append(Paragraph("No opportunities identified yet.", styles["Muted"]))

    doc.build(flow)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Due Diligence Checklist
# ---------------------------------------------------------------------------
# A real, standard early-stage VC due diligence checklist -- these categories
# and items reflect what firms actually request during diligence, not
# generated filler.
DD_CHECKLIST = {
    "Corporate & Legal": [
        "Certificate of incorporation and bylaws / operating agreement",
        "Full capitalization table, including options and SAFEs/convertible notes",
        "Board meeting minutes and consent resolutions",
        "Material contracts (customer, vendor, partnership agreements)",
        "Outstanding litigation, disputes, or regulatory inquiries",
        "IP assignment agreements from all founders, employees, and contractors",
    ],
    "Financial": [
        "Historical financial statements (P&L, balance sheet, cash flow)",
        "Financial model / projections with underlying assumptions",
        "Revenue recognition policy and any deferred revenue schedule",
        "Accounts receivable / payable aging",
        "Existing debt agreements, covenants, and outstanding balances",
        "Burn rate history and current cash position",
    ],
    "Team & HR": [
        "Founder and key employee backgrounds / reference checks",
        "Org chart and key person dependencies",
        "Employment agreements, vesting schedules, and non-competes",
        "Advisor agreements and equity grants",
        "Employee turnover history, especially in leadership",
    ],
    "Product & Technology": [
        "Product architecture overview and technical documentation",
        "Source code ownership and any open-source license exposure",
        "Security practices, past incidents, and compliance certifications",
        "Product roadmap and technical debt assessment",
        "Third-party dependencies and vendor lock-in risk",
    ],
    "Market & Commercial": [
        "Customer list, concentration, and contract terms",
        "Churn and retention cohort data",
        "Competitive landscape and differentiation analysis",
        "Sales pipeline and conversion metrics",
        "Pricing strategy and historical price changes",
    ],
    "Cap Table & Prior Financings": [
        "Prior round term sheets and closing documents",
        "Investor rights agreements (pro-rata, information rights, etc.)",
        "Any outstanding warrants or side letters",
        "Founder vesting status and any accelerated vesting triggers",
    ],
}


def generate_due_diligence_checklist_pdf(project: models.Project) -> bytes:
    styles = _styles()
    buffer = io.BytesIO()
    doc = _build_doc(buffer)
    flow = _header_block(styles, project, "Due Diligence Checklist")

    flow.append(
        Paragraph(
            "Standard early-stage venture due diligence checklist. Items should be "
            "requested from the company and cross-referenced against documents already "
            "uploaded to this project.",
            styles["Body"],
        )
    )
    flow.append(Spacer(1, 8))

    for category, items in DD_CHECKLIST.items():
        flow.append(Paragraph(category, styles["SectionHeading"]))
        flow.append(
            ListFlowable(
                [ListItem(Paragraph(f"&#9744; {i}", styles["Body"])) for i in items],
                bulletType="bullet",
                leftIndent=14,
            )
        )

    doc.build(flow)
    return buffer.getvalue()

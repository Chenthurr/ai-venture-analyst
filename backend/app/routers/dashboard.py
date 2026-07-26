from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user
from app.services.financial_engine import compute_financial_metrics

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _latest(query_model, project_id: str, db: Session):
    return (
        db.query(query_model)
        .filter(query_model.project_id == project_id)
        .order_by(query_model.created_at.desc())
        .first()
    )


@router.get("/summary", response_model=schemas.DashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    projects = db.query(models.Project).filter(models.Project.owner_id == user.id).all()

    stage_breakdown: dict = {}
    project_summaries = []
    risk_heatmap = []
    scores_for_avg = []
    valuations_for_total = []
    burns_for_total = []

    for project in projects:
        stage_key = project.stage or "unspecified"
        stage_breakdown[stage_key] = stage_breakdown.get(stage_key, 0) + 1

        analysis = _latest(models.AnalysisReport, project.id, db)
        snapshot = _latest(models.FinancialSnapshot, project.id, db)

        overall_score = None
        if analysis and analysis.scores:
            score_values = [s.get("score", 0) for s in analysis.scores.values()]
            if score_values:
                overall_score = sum(score_values) / len(score_values)
                scores_for_avg.append(overall_score)

        blended_valuation = None
        if analysis and analysis.valuation:
            blended_valuation = analysis.valuation.get("blended_valuation")
            if blended_valuation:
                valuations_for_total.append(blended_valuation)

        net_burn_monthly = None
        runway_months = None
        if snapshot:
            metrics = compute_financial_metrics(snapshot)
            net_burn_monthly = metrics["net_burn_monthly"]
            runway_months = metrics["runway_months"]
            burns_for_total.append(net_burn_monthly)

        project_summaries.append(
            schemas.ProjectSummary(
                id=project.id,
                company_name=project.company_name,
                industry=project.industry,
                stage=project.stage,
                overall_score=round(overall_score, 1) if overall_score is not None else None,
                blended_valuation=blended_valuation,
                net_burn_monthly=net_burn_monthly,
                runway_months=runway_months,
                has_analysis=analysis is not None,
                has_financials=snapshot is not None,
            )
        )

        if analysis and analysis.risk_scores:
            risk_heatmap.append(
                schemas.RiskHeatmapEntry(
                    project_id=project.id,
                    company_name=project.company_name,
                    risk_scores={k: v.get("score", 50) for k, v in analysis.risk_scores.items()},
                )
            )

    return schemas.DashboardSummary(
        total_projects=len(projects),
        stage_breakdown=stage_breakdown,
        avg_overall_score=round(sum(scores_for_avg) / len(scores_for_avg), 1) if scores_for_avg else None,
        total_blended_valuation=round(sum(valuations_for_total), 2),
        total_monthly_burn=round(sum(burns_for_total), 2),
        projects=project_summaries,
        risk_heatmap=risk_heatmap,
    )

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user, get_project_or_404
from app.services.ai_analysis import run_full_analysis, answer_question
from app.services.financial_engine import compute_financial_metrics
from app.services.valuation import compute_all_valuations

router = APIRouter(prefix="/api/projects/{project_id}/analysis", tags=["analysis"])


@router.post("", response_model=schemas.AnalysisOut, status_code=201)
def trigger_analysis(
    project_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    project = get_project_or_404(project_id, db, user)

    snapshot = (
        db.query(models.FinancialSnapshot)
        .filter(models.FinancialSnapshot.project_id == project_id)
        .order_by(models.FinancialSnapshot.created_at.desc())
        .first()
    )
    financial_metrics = compute_financial_metrics(snapshot) if snapshot else {}

    try:
        result = run_full_analysis(db, project, financial_metrics)
    except RuntimeError as e:
        # e.g. missing OPENAI_API_KEY
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {e}")

    valuation = None
    if snapshot:
        valuation = compute_all_valuations(
            snapshot, project.stage, result.get("scores") or {}, result.get("risk_scores") or {}
        )

    report = models.AnalysisReport(
        project_id=project_id,
        executive_summary=result.get("executive_summary"),
        swot=result.get("swot"),
        scores=result.get("scores"),
        risk_scores=result.get("risk_scores"),
        investment_memo=result.get("investment_memo"),
        citations=result.get("citations"),
        financial_metrics=financial_metrics,
        valuation=valuation,
        model_used=result.get("model_used"),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/latest", response_model=schemas.AnalysisOut)
def get_latest_analysis(
    project_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    get_project_or_404(project_id, db, user)
    report = (
        db.query(models.AnalysisReport)
        .filter(models.AnalysisReport.project_id == project_id)
        .order_by(models.AnalysisReport.created_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="No analysis has been run yet")
    return report


@router.post("/chat", response_model=schemas.ChatResponse)
def chat(
    project_id: str,
    payload: schemas.ChatRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    project = get_project_or_404(project_id, db, user)
    try:
        result = answer_question(db, project, payload.question)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"AI chat failed: {e}")
    return result

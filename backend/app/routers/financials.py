from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user, get_project_or_404
from app.services.financial_engine import compute_financial_metrics
from app.services.valuation import compute_all_valuations

router = APIRouter(prefix="/api/projects/{project_id}/financials", tags=["financials"])


def _latest_snapshot(db: Session, project_id: str) -> models.FinancialSnapshot | None:
    return (
        db.query(models.FinancialSnapshot)
        .filter(models.FinancialSnapshot.project_id == project_id)
        .order_by(models.FinancialSnapshot.created_at.desc())
        .first()
    )


@router.post("", response_model=schemas.FinancialSnapshotOut, status_code=201)
def create_snapshot(
    project_id: str,
    payload: schemas.FinancialSnapshotIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    get_project_or_404(project_id, db, user)
    snapshot = models.FinancialSnapshot(project_id=project_id, **payload.model_dump())
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


@router.get("/latest", response_model=schemas.FinancialSnapshotOut)
def get_latest_snapshot(
    project_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    get_project_or_404(project_id, db, user)
    snapshot = _latest_snapshot(db, project_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="No financial data submitted yet")
    return snapshot


@router.get("/metrics", response_model=schemas.FinancialMetricsOut)
def get_metrics(
    project_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    get_project_or_404(project_id, db, user)
    snapshot = _latest_snapshot(db, project_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="No financial data submitted yet")
    return compute_financial_metrics(snapshot)


@router.get("/valuation", response_model=schemas.ValuationOut)
def get_valuation(
    project_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    project = get_project_or_404(project_id, db, user)
    snapshot = _latest_snapshot(db, project_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="No financial data submitted yet")

    # Valuation methods that use qualitative scores fall back to a neutral
    # 50/100 for every category if no AI analysis has been run yet.
    latest_report = (
        db.query(models.AnalysisReport)
        .filter(models.AnalysisReport.project_id == project_id)
        .order_by(models.AnalysisReport.created_at.desc())
        .first()
    )
    scores = (latest_report.scores if latest_report and latest_report.scores else {})
    risk_scores = (latest_report.risk_scores if latest_report and latest_report.risk_scores else {})

    return compute_all_valuations(snapshot, project.stage, scores, risk_scores)

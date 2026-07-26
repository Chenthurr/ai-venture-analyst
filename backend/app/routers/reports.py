from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.deps import get_current_user, get_project_or_404
from app.services import report_generator

router = APIRouter(prefix="/api/projects/{project_id}/reports", tags=["reports"])


def _latest_analysis(db: Session, project_id: str):
    return (
        db.query(models.AnalysisReport)
        .filter(models.AnalysisReport.project_id == project_id)
        .order_by(models.AnalysisReport.created_at.desc())
        .first()
    )


def _pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/investment-memo")
def download_investment_memo(
    project_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    project = get_project_or_404(project_id, db, user)
    analysis = _latest_analysis(db, project_id)
    if not analysis:
        raise HTTPException(
            status_code=400,
            detail="No AI analysis has been run yet. Run analysis before generating a memo.",
        )
    pdf_bytes = report_generator.generate_investment_memo_pdf(
        project, analysis, analysis.financial_metrics, analysis.valuation
    )
    filename = f"{project.company_name.replace(' ', '_')}_Investment_Memo.pdf"
    return _pdf_response(pdf_bytes, filename)


@router.get("/board-report")
def download_board_report(
    project_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    project = get_project_or_404(project_id, db, user)
    analysis = _latest_analysis(db, project_id)
    if not analysis:
        raise HTTPException(status_code=400, detail="No AI analysis has been run yet.")
    pdf_bytes = report_generator.generate_board_report_pdf(
        project, analysis, analysis.financial_metrics, analysis.valuation
    )
    filename = f"{project.company_name.replace(' ', '_')}_Board_Report.pdf"
    return _pdf_response(pdf_bytes, filename)


@router.get("/investor-report")
def download_investor_report(
    project_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    project = get_project_or_404(project_id, db, user)
    analysis = _latest_analysis(db, project_id)
    if not analysis:
        raise HTTPException(status_code=400, detail="No AI analysis has been run yet.")
    pdf_bytes = report_generator.generate_investor_report_pdf(
        project, analysis, analysis.financial_metrics, analysis.valuation
    )
    filename = f"{project.company_name.replace(' ', '_')}_Investor_Report.pdf"
    return _pdf_response(pdf_bytes, filename)


@router.get("/due-diligence-checklist")
def download_due_diligence_checklist(
    project_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    project = get_project_or_404(project_id, db, user)
    pdf_bytes = report_generator.generate_due_diligence_checklist_pdf(project)
    filename = f"{project.company_name.replace(' ', '_')}_DD_Checklist.pdf"
    return _pdf_response(pdf_bytes, filename)

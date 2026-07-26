import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.database import get_db
from app.deps import get_current_user, get_project_or_404
from app.services.document_parser import (
    SUPPORTED_EXTENSIONS,
    detect_file_type,
    parse_document,
    chunk_text,
)
from app.services.embeddings import embed_texts

router = APIRouter(prefix="/api/projects/{project_id}/documents", tags=["documents"])


@router.post("", response_model=schemas.DocumentOut, status_code=201)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    doc_category: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    project = get_project_or_404(project_id, db, user)

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.max_upload_mb:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.max_upload_mb}MB limit")

    project_dir = os.path.join(settings.upload_dir, project_id)
    os.makedirs(project_dir, exist_ok=True)
    stored_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(project_dir, stored_name)
    with open(file_path, "wb") as f:
        f.write(contents)

    file_type = detect_file_type(file.filename)
    document = models.Document(
        project_id=project_id,
        filename=file.filename,
        file_path=file_path,
        file_type=file_type,
        doc_category=doc_category,
        status="uploaded",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # --- Parse synchronously (v1: no Celery worker yet -- see README roadmap) ---
    try:
        text, tables = parse_document(file_path, file_type)
        document.extracted_text = text
        document.extracted_tables = tables
        document.status = "parsed"
        db.commit()
    except Exception as e:  # noqa: BLE001
        document.status = "failed"
        document.error_message = f"Parsing failed: {e}"
        db.commit()
        db.refresh(document)
        return document

    # --- Chunk + embed (requires OPENAI_API_KEY; if missing, leave as 'parsed') ---
    if settings.openai_api_key:
        try:
            chunks = chunk_text(text)
            if chunks:
                embeddings = embed_texts(chunks)
                for i, (content, embedding) in enumerate(zip(chunks, embeddings)):
                    db.add(models.DocumentChunk(
                        document_id=document.id,
                        project_id=project_id,
                        chunk_index=i,
                        content=content,
                        embedding=embedding,
                    ))
            document.status = "embedded"
            db.commit()
        except Exception as e:  # noqa: BLE001
            document.status = "failed"
            document.error_message = f"Embedding failed: {e}"
            db.commit()

    db.refresh(document)
    return document


@router.get("", response_model=List[schemas.DocumentOut])
def list_documents(
    project_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    get_project_or_404(project_id, db, user)
    return (
        db.query(models.Document)
        .filter(models.Document.project_id == project_id)
        .order_by(models.Document.created_at.desc())
        .all()
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    get_project_or_404(project_id, db, user)
    doc = (
        db.query(models.Document)
        .filter(models.Document.id == document_id, models.Document.project_id == project_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc)
    db.commit()
    return None

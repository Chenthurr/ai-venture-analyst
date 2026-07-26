from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth, projects, documents, financials, analysis, reports, dashboard

# Create tables on startup (v1: no Alembic migrations wired up yet, see README).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Venture Analyst API",
    description="AI-powered startup investment analysis platform.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(documents.router)
app.include_router(financials.router)
app.include_router(analysis.router)
app.include_router(reports.router)
app.include_router(dashboard.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "openai_configured": bool(settings.openai_api_key)}

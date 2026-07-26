import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Float, Integer, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")


class Project(Base):
    """A single startup being analyzed."""
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    owner_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)

    company_name = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    country = Column(String, nullable=True)
    stage = Column(String, nullable=True)  # pre-seed, seed, series-a, ...
    founders = Column(String, nullable=True)  # comma separated names for v1
    one_liner = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="projects")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    financials = relationship("FinancialSnapshot", back_populates="project", cascade="all, delete-orphan")
    reports = relationship("AnalysisReport", back_populates="project", cascade="all, delete-orphan")


class Document(Base):
    """An uploaded file (pitch deck, financials, etc.) and its extracted content."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False)

    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, pptx, xlsx, csv, docx, image
    doc_category = Column(String, nullable=True)  # pitch_deck, financials, market_report, other

    extracted_text = Column(Text, nullable=True)
    extracted_tables = Column(JSON, nullable=True)  # list of tables as list-of-lists
    summary = Column(Text, nullable=True)

    status = Column(String, default="uploaded")  # uploaded -> parsed -> embedded -> failed
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """A chunk of a document's text with its embedding vector, for RAG retrieval."""
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    document_id = Column(UUID(as_uuid=False), ForeignKey("documents.id"), nullable=False)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False)

    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # list[float], stored as JSON (no pgvector dependency)

    document = relationship("Document", back_populates="chunks")


class FinancialSnapshot(Base):
    """
    Raw financial inputs for a project at a point in time.
    These are the inputs to the financial engine / valuation engine.
    """
    __tablename__ = "financial_snapshots"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False)

    label = Column(String, default="Current")  # e.g. "Q1 2026"

    # Core P&L inputs (monthly, in USD, unless noted)
    monthly_revenue = Column(Float, default=0.0)
    monthly_cogs = Column(Float, default=0.0)
    monthly_operating_expenses = Column(Float, default=0.0)
    cash_balance = Column(Float, default=0.0)

    # Growth / customer inputs
    new_customers_this_month = Column(Integer, default=0)
    total_customers = Column(Integer, default=0)
    churned_customers_this_month = Column(Integer, default=0)
    sales_marketing_spend = Column(Float, default=0.0)
    avg_revenue_per_account = Column(Float, default=0.0)  # ARPA, monthly

    # For break-even
    avg_price_per_unit = Column(Float, default=0.0)
    avg_variable_cost_per_unit = Column(Float, default=0.0)
    fixed_costs_monthly = Column(Float, default=0.0)

    # For DCF / comparables / VC method
    projected_annual_growth_rate = Column(Float, default=0.20)  # 20% default
    discount_rate = Column(Float, default=0.35)  # startup-appropriate WACC/discount
    exit_multiple_revenue = Column(Float, default=5.0)
    years_to_exit = Column(Integer, default=5)
    anticipated_roi = Column(Float, default=10.0)  # for VC method (10x)
    investment_amount_requested = Column(Float, default=0.0)
    industry_revenue_multiple = Column(Float, default=6.0)  # comparables method

    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="financials")


class AnalysisReport(Base):
    """
    A generated AI analysis report (executive summary, SWOT, scores, memo).
    Stored as structured JSON so the frontend can render it richly.
    """
    __tablename__ = "analysis_reports"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False)

    executive_summary = Column(Text, nullable=True)
    swot = Column(JSON, nullable=True)  # {strengths: [], weaknesses: [], opportunities: [], threats: []}
    scores = Column(JSON, nullable=True)  # {founder_strength: {score, reasoning}, ...}
    risk_scores = Column(JSON, nullable=True)  # {management_risk: {score, reasoning}, ...}
    investment_memo = Column(Text, nullable=True)
    citations = Column(JSON, nullable=True)  # [{claim, document_id, filename, chunk_index}]

    financial_metrics = Column(JSON, nullable=True)  # computed by financial engine
    valuation = Column(JSON, nullable=True)  # computed by valuation engine

    model_used = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="reports")

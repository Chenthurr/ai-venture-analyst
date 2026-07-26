from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Projects ----------

class ProjectCreate(BaseModel):
    company_name: str
    industry: Optional[str] = None
    country: Optional[str] = None
    stage: Optional[str] = None
    founders: Optional[str] = None
    one_liner: Optional[str] = None


class ProjectUpdate(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    stage: Optional[str] = None
    founders: Optional[str] = None
    one_liner: Optional[str] = None


class ProjectOut(BaseModel):
    id: str
    company_name: str
    industry: Optional[str]
    country: Optional[str]
    stage: Optional[str]
    founders: Optional[str]
    one_liner: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Documents ----------

class DocumentOut(BaseModel):
    id: str
    filename: str
    file_type: str
    doc_category: Optional[str]
    status: str
    summary: Optional[str]
    error_message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Financials ----------

class FinancialSnapshotIn(BaseModel):
    label: Optional[str] = "Current"
    monthly_revenue: float = 0
    monthly_cogs: float = 0
    monthly_operating_expenses: float = 0
    cash_balance: float = 0
    new_customers_this_month: int = 0
    total_customers: int = 0
    churned_customers_this_month: int = 0
    sales_marketing_spend: float = 0
    avg_revenue_per_account: float = 0
    avg_price_per_unit: float = 0
    avg_variable_cost_per_unit: float = 0
    fixed_costs_monthly: float = 0
    projected_annual_growth_rate: float = 0.20
    discount_rate: float = 0.35
    exit_multiple_revenue: float = 5.0
    years_to_exit: int = 5
    anticipated_roi: float = 10.0
    investment_amount_requested: float = 0
    industry_revenue_multiple: float = 6.0


class FinancialSnapshotOut(FinancialSnapshotIn):
    id: str
    project_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FinancialMetricsOut(BaseModel):
    gross_margin_pct: float
    net_margin_pct: float
    net_burn_monthly: float
    runway_months: Optional[float]
    cac: Optional[float]
    ltv: Optional[float]
    ltv_to_cac: Optional[float]
    cac_payback_months: Optional[float]
    ebitda_monthly: float
    break_even_units: Optional[float]
    break_even_revenue: Optional[float]
    contribution_margin_pct: Optional[float]
    monthly_churn_rate_pct: Optional[float]
    annualized_revenue_run_rate: float


class ValuationMethodResult(BaseModel):
    method: str
    estimated_valuation: float
    details: Dict[str, Any]
    notes: str


class ValuationOut(BaseModel):
    methods: List[ValuationMethodResult]
    blended_valuation: float


# ---------- Analysis ----------

class AnalysisRequest(BaseModel):
    force_refresh: bool = False


class AnalysisOut(BaseModel):
    id: str
    project_id: str
    executive_summary: Optional[str]
    swot: Optional[Dict[str, Any]]
    scores: Optional[Dict[str, Any]]
    investment_memo: Optional[str]
    citations: Optional[List[Dict[str, Any]]]
    financial_metrics: Optional[Dict[str, Any]]
    valuation: Optional[Dict[str, Any]]
    model_used: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]


# ---------- Dashboard ----------

class ProjectSummary(BaseModel):
    id: str
    company_name: str
    industry: Optional[str]
    stage: Optional[str]
    overall_score: Optional[float]
    blended_valuation: Optional[float]
    net_burn_monthly: Optional[float]
    runway_months: Optional[float]
    has_analysis: bool
    has_financials: bool


class RiskHeatmapEntry(BaseModel):
    project_id: str
    company_name: str
    risk_scores: Dict[str, int]  # category -> 0-100 (100 = low risk)


class DashboardSummary(BaseModel):
    total_projects: int
    stage_breakdown: Dict[str, int]
    avg_overall_score: Optional[float]
    total_blended_valuation: float
    total_monthly_burn: float
    projects: List[ProjectSummary]
    risk_heatmap: List[RiskHeatmapEntry]

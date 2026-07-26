export interface Project {
  id: string;
  company_name: string;
  industry: string | null;
  country: string | null;
  stage: string | null;
  founders: string | null;
  one_liner: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentOut {
  id: string;
  filename: string;
  file_type: string;
  doc_category: string | null;
  status: "uploaded" | "parsed" | "embedded" | "failed";
  summary: string | null;
  error_message: string | null;
  created_at: string;
}

export interface FinancialMetrics {
  gross_margin_pct: number;
  net_margin_pct: number;
  net_burn_monthly: number;
  runway_months: number | null;
  cac: number | null;
  ltv: number | null;
  ltv_to_cac: number | null;
  cac_payback_months: number | null;
  ebitda_monthly: number;
  break_even_units: number | null;
  break_even_revenue: number | null;
  contribution_margin_pct: number | null;
  monthly_churn_rate_pct: number | null;
  annualized_revenue_run_rate: number;
}

export interface ValuationMethodResult {
  method: string;
  estimated_valuation: number;
  details: Record<string, any>;
  notes: string;
}

export interface Valuation {
  methods: ValuationMethodResult[];
  blended_valuation: number;
}

export interface ScoreEntry {
  score: number;
  reasoning: string;
}

export interface SwotData {
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}

export interface Citation {
  claim?: string;
  filename: string;
  document_id: string;
  chunk_index: number;
  relevance_score: number;
}

export interface ProjectSummary {
  id: string;
  company_name: string;
  industry: string | null;
  stage: string | null;
  overall_score: number | null;
  blended_valuation: number | null;
  net_burn_monthly: number | null;
  runway_months: number | null;
  has_analysis: boolean;
  has_financials: boolean;
}

export interface RiskHeatmapEntry {
  project_id: string;
  company_name: string;
  risk_scores: Record<string, number>;
}

export interface DashboardSummary {
  total_projects: number;
  stage_breakdown: Record<string, number>;
  avg_overall_score: number | null;
  total_blended_valuation: number;
  total_monthly_burn: number;
  projects: ProjectSummary[];
  risk_heatmap: RiskHeatmapEntry[];
}

export interface AnalysisReport {
  id: string;
  project_id: string;
  executive_summary: string | null;
  swot: SwotData | null;
  scores: Record<string, ScoreEntry> | null;
  investment_memo: string | null;
  citations: Citation[] | null;
  financial_metrics: FinancialMetrics | null;
  valuation: Valuation | null;
  model_used: string | null;
  created_at: string;
}

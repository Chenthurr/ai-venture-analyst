import { FinancialMetrics } from "@/types";
import { Stat } from "@/components/ui";

function fmtMoney(n: number | null) {
  if (n === null || n === undefined) return "—";
  return `$${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function fmtRatio(n: number | null, suffix = "x") {
  if (n === null || n === undefined) return "—";
  return `${n.toFixed(2)}${suffix}`;
}

export function FinancialMetricsPanel({ metrics }: { metrics: FinancialMetrics }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <Stat label="Gross Margin" value={metrics.gross_margin_pct.toFixed(1)} suffix="%" />
      <Stat
        label="Net Margin"
        value={metrics.net_margin_pct.toFixed(1)}
        suffix="%"
        tone={metrics.net_margin_pct >= 0 ? "positive" : "negative"}
      />
      <Stat
        label="Net Burn / mo"
        value={fmtMoney(metrics.net_burn_monthly)}
        tone={metrics.net_burn_monthly > 0 ? "negative" : "positive"}
      />
      <Stat
        label="Runway"
        value={metrics.runway_months !== null ? metrics.runway_months.toFixed(1) : "∞"}
        suffix={metrics.runway_months !== null ? "months" : ""}
        tone={
          metrics.runway_months !== null && metrics.runway_months < 6
            ? "negative"
            : "neutral"
        }
      />
      <Stat label="CAC" value={fmtMoney(metrics.cac)} />
      <Stat label="LTV" value={fmtMoney(metrics.ltv)} />
      <Stat
        label="LTV : CAC"
        value={fmtRatio(metrics.ltv_to_cac)}
        tone={
          metrics.ltv_to_cac !== null
            ? metrics.ltv_to_cac >= 3
              ? "positive"
              : "negative"
            : "neutral"
        }
      />
      <Stat
        label="CAC Payback"
        value={
          metrics.cac_payback_months !== null
            ? metrics.cac_payback_months.toFixed(1)
            : "—"
        }
        suffix="months"
      />
      <Stat label="EBITDA / mo" value={fmtMoney(metrics.ebitda_monthly)} tone={metrics.ebitda_monthly >= 0 ? "positive" : "negative"} />
      <Stat label="Break-even Revenue" value={fmtMoney(metrics.break_even_revenue)} />
      <Stat
        label="Monthly Churn"
        value={
          metrics.monthly_churn_rate_pct !== null
            ? metrics.monthly_churn_rate_pct.toFixed(1)
            : "—"
        }
        suffix="%"
        tone={
          metrics.monthly_churn_rate_pct !== null && metrics.monthly_churn_rate_pct > 5
            ? "negative"
            : "neutral"
        }
      />
      <Stat label="Annualized Run Rate" value={fmtMoney(metrics.annualized_revenue_run_rate)} />
    </div>
  );
}

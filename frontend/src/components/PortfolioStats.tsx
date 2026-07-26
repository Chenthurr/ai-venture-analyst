import { DashboardSummary } from "@/types";
import { Card, Stat, Tag } from "@/components/ui";

const RISK_LABELS: Record<string, string> = {
  management_risk: "Mgmt",
  stage_of_business_risk: "Stage",
  legislation_political_risk: "Legal",
  manufacturing_risk: "Mfg",
  sales_marketing_risk: "S&M",
  funding_capital_raising_risk: "Funding",
  competition_risk: "Comp",
  technology_risk: "Tech",
  litigation_risk: "Litig",
  international_risk: "Intl",
  reputation_risk: "Rep",
  exit_value_risk: "Exit",
};

function fmtUsd(n: number) {
  if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
}

function heatColor(score: number) {
  // score = risk LEVEL here (0 = safe, 100 = high risk)
  if (score >= 66) return "bg-signal-negative/70";
  if (score >= 33) return "bg-gold/60";
  return "bg-signal-positive/60";
}

export function PortfolioStats({ summary }: { summary: DashboardSummary }) {
  return (
    <div className="space-y-6 mb-10">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat label="Portfolio Companies" value={summary.total_projects} />
        <Stat
          label="Avg Conviction Score"
          value={summary.avg_overall_score !== null ? summary.avg_overall_score.toFixed(0) : "—"}
        />
        <Stat label="Total Blended Valuation" value={fmtUsd(summary.total_blended_valuation)} />
        <Stat
          label="Total Monthly Burn"
          value={fmtUsd(summary.total_monthly_burn)}
          tone={summary.total_monthly_burn > 0 ? "negative" : "positive"}
        />
      </div>

      {Object.keys(summary.stage_breakdown).length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs uppercase tracking-wider text-paper-faint">By stage:</span>
          {Object.entries(summary.stage_breakdown).map(([stage, count]) => (
            <Tag key={stage} tone="neutral">
              {stage} · {count}
            </Tag>
          ))}
        </div>
      )}

      {summary.risk_heatmap.length > 0 && (
        <Card className="p-4 overflow-x-auto">
          <div className="text-xs uppercase tracking-wider text-paper-faint mb-3">
            Portfolio Risk Heatmap
          </div>
          <table className="w-full text-xs">
            <thead>
              <tr>
                <th className="text-left text-paper-faint font-normal pb-2 pr-3">Company</th>
                {Object.values(RISK_LABELS).map((label) => (
                  <th key={label} className="text-paper-faint font-normal pb-2 px-1 text-center">
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {summary.risk_heatmap.map((row) => (
                <tr key={row.project_id}>
                  <td className="text-paper pr-3 py-1 whitespace-nowrap">{row.company_name}</td>
                  {Object.keys(RISK_LABELS).map((key) => {
                    const safeScore = row.risk_scores[key] ?? 50;
                    const riskLevel = 100 - safeScore; // invert: stored score is "safety"
                    return (
                      <td key={key} className="px-1 py-1">
                        <div
                          className={`h-5 w-6 rounded-sm mx-auto ${heatColor(riskLevel)}`}
                          title={`${RISK_LABELS[key]}: ${riskLevel.toFixed(0)} risk`}
                        />
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

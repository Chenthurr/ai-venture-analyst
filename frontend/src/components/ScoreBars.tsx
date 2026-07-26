import { ScoreEntry } from "@/types";

const LABELS: Record<string, string> = {
  founder_strength: "Founder Strength",
  market_size: "Market Size",
  product_quality: "Product Quality",
  traction: "Traction",
  competition: "Competition",
  financial_health: "Financial Health",
  business_model: "Business Model",
  technology: "Technology",
  scalability: "Scalability",
  investment_readiness: "Investment Readiness",
};

function barColor(score: number) {
  if (score >= 70) return "bg-signal-positive";
  if (score >= 40) return "bg-gold";
  return "bg-signal-negative";
}

export function ScoreBars({ scores }: { scores: Record<string, ScoreEntry> }) {
  return (
    <div className="space-y-3">
      {Object.entries(scores).map(([key, entry]) => (
        <div key={key} className="group relative">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-paper-muted">{LABELS[key] || key}</span>
            <span className="font-mono text-sm text-paper tabular-nums">{entry.score}</span>
          </div>
          <div className="h-1.5 bg-ink rounded-full overflow-hidden border border-ink-border">
            <div
              className={`h-full ${barColor(entry.score)} transition-all`}
              style={{ width: `${entry.score}%` }}
            />
          </div>
          <p className="text-xs text-paper-faint mt-1 leading-snug opacity-0 group-hover:opacity-100 transition-opacity absolute z-10 bg-ink-raised border border-ink-border rounded p-2 max-w-sm">
            {entry.reasoning}
          </p>
        </div>
      ))}
    </div>
  );
}

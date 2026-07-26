"use client";

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import { ScoreEntry } from "@/types";

const LABELS: Record<string, string> = {
  management_risk: "Management",
  stage_of_business_risk: "Stage",
  legislation_political_risk: "Legal/Political",
  manufacturing_risk: "Manufacturing",
  sales_marketing_risk: "Sales & Marketing",
  funding_capital_raising_risk: "Funding",
  competition_risk: "Competition",
  technology_risk: "Technology",
  litigation_risk: "Litigation",
  international_risk: "International",
  reputation_risk: "Reputation",
  exit_value_risk: "Exit Value",
};

export function RiskRadar({ riskScores }: { riskScores: Record<string, ScoreEntry> }) {
  // Chart shows risk LEVEL (inverse of the "low risk = high score" convention
  // used by the valuation engine), so a bigger spike on this chart = more risk.
  const data = Object.entries(riskScores).map(([key, entry]) => ({
    category: LABELS[key] || key,
    risk: 100 - entry.score,
  }));

  if (data.length === 0) {
    return <p className="text-sm text-paper-faint italic">No risk analysis available yet.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <RadarChart data={data} outerRadius="75%">
        <PolarGrid stroke="#232837" />
        <PolarAngleAxis dataKey="category" tick={{ fill: "#8890A0", fontSize: 11 }} />
        <PolarRadiusAxis domain={[0, 100]} tick={{ fill: "#5A6274", fontSize: 10 }} axisLine={false} />
        <Radar dataKey="risk" stroke="#C1554A" fill="#C1554A" fillOpacity={0.25} />
      </RadarChart>
    </ResponsiveContainer>
  );
}

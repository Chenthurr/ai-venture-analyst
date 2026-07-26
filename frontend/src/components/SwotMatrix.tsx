import { SwotData } from "@/types";
import { Card } from "@/components/ui";

const QUADRANTS: { key: keyof SwotData; label: string; tone: string }[] = [
  { key: "strengths", label: "Strengths", tone: "border-signal-positive/30" },
  { key: "weaknesses", label: "Weaknesses", tone: "border-signal-negative/30" },
  { key: "opportunities", label: "Opportunities", tone: "border-gold/30" },
  { key: "threats", label: "Threats", tone: "border-signal-neutral/30" },
];

export function SwotMatrix({ swot }: { swot: SwotData }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {QUADRANTS.map((q) => (
        <Card key={q.key} className={`p-4 border-t-2 ${q.tone}`}>
          <div className="text-xs uppercase tracking-wider text-paper-faint mb-2">
            {q.label}
          </div>
          <ul className="space-y-1.5">
            {(swot[q.key] || []).map((item, i) => (
              <li key={i} className="text-sm text-paper-muted leading-snug flex gap-2">
                <span className="text-paper-faint">—</span>
                <span>{item}</span>
              </li>
            ))}
            {(!swot[q.key] || swot[q.key].length === 0) && (
              <li className="text-sm text-paper-faint italic">No items identified.</li>
            )}
          </ul>
        </Card>
      ))}
    </div>
  );
}

"use client";

import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from "recharts";
import { Valuation } from "@/types";
import { Card } from "@/components/ui";

function formatUsd(n: number) {
  if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
}

export function ValuationPanel({ valuation }: { valuation: Valuation }) {
  const chartData = valuation.methods.map((m) => ({
    method: m.method.replace(" Method", ""),
    value: m.estimated_valuation,
  }));

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#232837" horizontal={false} />
            <XAxis type="number" tickFormatter={formatUsd} tick={{ fill: "#8890A0", fontSize: 11 }} />
            <YAxis dataKey="method" type="category" width={110} tick={{ fill: "#8890A0", fontSize: 11 }} />
            <Tooltip
              formatter={(v: number) => formatUsd(v)}
              contentStyle={{ background: "#171C27", border: "1px solid #232837", fontSize: 12 }}
            />
            <Bar dataKey="value" fill="#C9A24B" radius={[0, 3, 3, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <div className="flex items-center justify-between px-4 py-3 border border-gold/30 bg-gold/5 rounded">
        <span className="text-sm text-paper-muted">Blended Valuation Estimate</span>
        <span className="font-mono text-xl text-gold tabular-nums">
          {formatUsd(valuation.blended_valuation)}
        </span>
      </div>

      <div className="space-y-2">
        {valuation.methods.map((m) => (
          <details key={m.method} className="border border-ink-border rounded group">
            <summary className="cursor-pointer px-4 py-3 flex items-center justify-between text-sm">
              <span className="text-paper">{m.method}</span>
              <span className="font-mono text-paper-muted tabular-nums">
                {formatUsd(m.estimated_valuation)}
              </span>
            </summary>
            <div className="px-4 pb-4 pt-1 text-xs text-paper-faint leading-relaxed border-t border-ink-border">
              <p className="mb-2">{m.notes}</p>
              <pre className="whitespace-pre-wrap font-mono text-[11px] text-paper-muted bg-ink p-2 rounded overflow-x-auto">
                {JSON.stringify(m.details, null, 2)}
              </pre>
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}

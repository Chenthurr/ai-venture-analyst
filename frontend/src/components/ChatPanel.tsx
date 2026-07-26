"use client";

import { useState } from "react";
import { Button, Input, SectionLabel, Card } from "@/components/ui";
import { Citation } from "@/types";

interface ChatTurn {
  question: string;
  answer: string;
  citations: Citation[];
}

const SUGGESTIONS = [
  "Should I invest?",
  "What are the biggest risks?",
  "How can valuation increase?",
  "How can CAC improve?",
  "Generate a due diligence checklist",
  "Suggest KPIs to track",
];

export function ChatPanel({
  onAsk,
}: {
  onAsk: (question: string) => Promise<{ answer: string; citations: Citation[] }>;
}) {
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask(q: string) {
    if (!q.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      const res = await onAsk(q);
      setTurns((t) => [...t, { question: q, answer: res.answer, citations: res.citations }]);
      setQuestion("");
    } catch (e: any) {
      setError(e.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <SectionLabel number="06" title="Ask the Analyst" />

      <div className="flex flex-wrap gap-2 mb-4">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => ask(s)}
            className="text-xs px-2.5 py-1 rounded border border-ink-border text-paper-faint hover:text-gold hover:border-gold/40"
          >
            {s}
          </button>
        ))}
      </div>

      <div className="space-y-4 mb-4 max-h-[420px] overflow-y-auto">
        {turns.map((t, i) => (
          <div key={i}>
            <div className="text-sm text-paper-muted mb-1.5">
              <span className="text-gold">You —</span> {t.question}
            </div>
            <Card className="p-3">
              <p className="text-sm text-paper leading-relaxed whitespace-pre-wrap">{t.answer}</p>
              {t.citations.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2 pt-2 border-t border-ink-border">
                  {t.citations.map((c, ci) => (
                    <span
                      key={ci}
                      className="text-[11px] font-mono px-1.5 py-0.5 bg-ink-raised text-paper-faint rounded"
                    >
                      {c.filename}#{c.chunk_index}
                    </span>
                  ))}
                </div>
              )}
            </Card>
          </div>
        ))}
      </div>

      {error && <p className="text-sm text-signal-negative mb-2">{error}</p>}

      <div className="flex gap-2">
        <Input
          placeholder="Ask about this startup…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && ask(question)}
          className="flex-1"
        />
        <Button onClick={() => ask(question)} disabled={loading}>
          {loading ? "Thinking…" : "Ask"}
        </Button>
      </div>
    </div>
  );
}

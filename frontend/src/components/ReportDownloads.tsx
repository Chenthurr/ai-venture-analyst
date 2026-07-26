"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Button, SectionLabel } from "@/components/ui";

const REPORTS: {
  type: "investment-memo" | "board-report" | "investor-report" | "due-diligence-checklist";
  label: string;
  requiresAnalysis: boolean;
}[] = [
  { type: "investment-memo", label: "Investment Memo", requiresAnalysis: true },
  { type: "board-report", label: "Board Report", requiresAnalysis: true },
  { type: "investor-report", label: "Investor Report", requiresAnalysis: true },
  { type: "due-diligence-checklist", label: "Due Diligence Checklist", requiresAnalysis: false },
];

export function ReportDownloads({
  projectId,
  companyName,
  hasAnalysis,
}: {
  projectId: string;
  companyName: string;
  hasAnalysis: boolean;
}) {
  const [downloading, setDownloading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleDownload(reportType: (typeof REPORTS)[number]["type"], label: string) {
    setError(null);
    setDownloading(reportType);
    try {
      const filename = `${companyName.replace(/\s+/g, "_")}_${label.replace(/\s+/g, "_")}.pdf`;
      await api.downloadReport(projectId, reportType, filename);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to generate report.");
    } finally {
      setDownloading(null);
    }
  }

  return (
    <div>
      <SectionLabel number="07" title="Reports" />
      <div className="flex flex-wrap gap-3">
        {REPORTS.map((r) => {
          const disabled = (r.requiresAnalysis && !hasAnalysis) || downloading !== null;
          return (
            <Button
              key={r.type}
              variant="ghost"
              disabled={disabled}
              onClick={() => handleDownload(r.type, r.label)}
              title={r.requiresAnalysis && !hasAnalysis ? "Run AI analysis first" : undefined}
            >
              {downloading === r.type ? "Generating…" : `⬇ ${r.label}`}
            </Button>
          );
        })}
      </div>
      {error && <p className="text-sm text-signal-negative mt-2">{error}</p>}
    </div>
  );
}

"use client";

import { useParams } from "next/navigation";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { Navbar } from "@/components/Navbar";
import { Button, Card, SectionLabel, Tag } from "@/components/ui";
import { ConvictionGauge } from "@/components/ConvictionGauge";
import { SwotMatrix } from "@/components/SwotMatrix";
import { ScoreBars } from "@/components/ScoreBars";
import { RiskRadar } from "@/components/RiskRadar";
import { FinancialForm } from "@/components/FinancialForm";
import { FinancialMetricsPanel } from "@/components/FinancialMetricsPanel";
import { ValuationPanel } from "@/components/ValuationPanel";
import { DocumentUploader } from "@/components/DocumentUploader";
import { ChatPanel } from "@/components/ChatPanel";
import { ReportDownloads } from "@/components/ReportDownloads";
import { useState } from "react";

export default function ProjectDetailPage() {
  const { ready } = useRequireAuth();
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const invalidateProject = () =>
    queryClient.invalidateQueries({ queryKey: ["project", projectId] });

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId),
    enabled: ready,
  });

  const { data: documents = [] } = useQuery({
    queryKey: ["documents", projectId],
    queryFn: () => api.listDocuments(projectId),
    enabled: ready,
  });

  const { data: financials } = useQuery({
    queryKey: ["financials", projectId],
    queryFn: () => api.getLatestFinancials(projectId),
    enabled: ready,
    retry: false,
  });

  const { data: metrics } = useQuery({
    queryKey: ["metrics", projectId],
    queryFn: () => api.getFinancialMetrics(projectId),
    enabled: ready && !!financials,
    retry: false,
  });

  const { data: valuation } = useQuery({
    queryKey: ["valuation", projectId],
    queryFn: () => api.getValuation(projectId),
    enabled: ready && !!financials,
    retry: false,
  });

  const { data: analysis } = useQuery({
    queryKey: ["analysis", projectId],
    queryFn: () => api.getLatestAnalysis(projectId),
    enabled: ready,
    retry: false,
  });

  const uploadMutation = useMutation({
    mutationFn: ({ file, category }: { file: File; category: string }) =>
      api.uploadDocument(projectId, file, category),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents", projectId] }),
  });

  const deleteDocMutation = useMutation({
    mutationFn: (documentId: string) => api.deleteDocument(projectId, documentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents", projectId] }),
  });

  const financialsMutation = useMutation({
    mutationFn: (values: Record<string, number>) => api.submitFinancials(projectId, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["financials", projectId] });
      queryClient.invalidateQueries({ queryKey: ["metrics", projectId] });
      queryClient.invalidateQueries({ queryKey: ["valuation", projectId] });
    },
  });

  const analysisMutation = useMutation({
    mutationFn: () => api.runAnalysis(projectId),
    onSuccess: () => {
      setAnalysisError(null);
      queryClient.invalidateQueries({ queryKey: ["analysis", projectId] });
      queryClient.invalidateQueries({ queryKey: ["valuation", projectId] });
    },
    onError: (e) => setAnalysisError(e instanceof ApiError ? e.message : "Analysis failed."),
  });

  if (!ready || !project) return null;

  const overallScore = analysis?.scores
    ? Math.round(
        Object.values(analysis.scores as Record<string, { score: number }>).reduce(
          (sum, s) => sum + s.score,
          0
        ) / Object.keys(analysis.scores).length
      )
    : null;

  return (
    <div className="min-h-screen">
      <Navbar title={project.company_name} />
      <main className="max-w-6xl mx-auto px-6 py-10 space-y-12">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="font-display text-3xl text-paper">{project.company_name}</h1>
              <Tag tone="gold">{project.stage || "stage unset"}</Tag>
            </div>
            <p className="text-paper-muted mt-2 max-w-xl">{project.one_liner}</p>
            <div className="flex gap-4 mt-3 text-xs text-paper-faint">
              <span>{project.industry || "Industry unspecified"}</span>
              <span>·</span>
              <span>{project.country || "Country unspecified"}</span>
              <span>·</span>
              <span>{project.founders || "Founders unspecified"}</span>
            </div>
          </div>
          <div className="flex flex-col items-center gap-3">
            {overallScore !== null && <ConvictionGauge score={overallScore} />}
            <Button onClick={() => analysisMutation.mutate()} disabled={analysisMutation.isPending}>
              {analysisMutation.isPending ? "Analyzing…" : analysis ? "Re-run Analysis" : "Run AI Analysis"}
            </Button>
          </div>
        </div>

        {analysisError && (
          <Card className="p-4 border-signal-negative/40">
            <p className="text-sm text-signal-negative">{analysisError}</p>
          </Card>
        )}

        {/* 01 Executive Summary + SWOT + Scores */}
        <section>
          <SectionLabel number="01" title="Executive Summary" />
          {analysis?.executive_summary ? (
            <p className="text-paper-muted leading-relaxed mb-6">{analysis.executive_summary}</p>
          ) : (
            <p className="text-sm text-paper-faint italic mb-6">
              No analysis yet. Upload documents and financials, then run AI analysis.
            </p>
          )}

          {analysis?.swot && (
            <div className="mb-6">
              <SwotMatrix swot={analysis.swot} />
            </div>
          )}

          {analysis?.scores && (
            <Card className="p-5">
              <h3 className="text-sm uppercase tracking-wider text-paper-faint mb-4">
                Investment Scores
              </h3>
              <ScoreBars scores={analysis.scores} />
            </Card>
          )}
        </section>

        {/* 02 Financials input */}
        <section>
          <FinancialForm
            initial={financials || undefined}
            submitting={financialsMutation.isPending}
            onSubmit={(values) => financialsMutation.mutate(values)}
          />
        </section>

        {/* 03 Documents */}
        <section>
          <DocumentUploader
            documents={documents}
            uploading={uploadMutation.isPending}
            onUpload={(file, category) => uploadMutation.mutate({ file, category })}
            onDelete={(id) => deleteDocMutation.mutate(id)}
          />
        </section>

        {/* 04 Financial Metrics */}
        {metrics && (
          <section>
            <SectionLabel number="04" title="Financial Analysis" />
            <FinancialMetricsPanel metrics={metrics} />
          </section>
        )}

        {/* 05 Valuation */}
        {valuation && (
          <section>
            <SectionLabel number="05" title="Valuation Engine" />
            <ValuationPanel valuation={valuation} />
          </section>
        )}

        {/* Risk radar */}
        {analysis?.risk_scores && Object.keys(analysis.risk_scores).length > 0 && (
          <section>
            <SectionLabel number="—" title="Risk Radar" />
            <Card className="p-5">
              <RiskRadar riskScores={analysis.risk_scores} />
            </Card>
          </section>
        )}

        {/* Investment memo */}
        {analysis?.investment_memo && (
          <section>
            <SectionLabel number="—" title="Full Investment Memo" />
            <Card className="p-6 prose-invert">
              <pre className="whitespace-pre-wrap font-body text-sm text-paper-muted leading-relaxed">
                {analysis.investment_memo}
              </pre>
            </Card>
          </section>
        )}

        {/* 06 Chat */}
        <section>
          <ChatPanel onAsk={(q) => api.chat(projectId, q)} />
        </section>

        {/* 07 Reports */}
        <section>
          <ReportDownloads
            projectId={projectId}
            companyName={project.company_name}
            hasAnalysis={!!analysis}
          />
        </section>
      </main>
    </div>
  );
}

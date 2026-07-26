"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { Navbar } from "@/components/Navbar";
import { Button, Card, Input, Select, SectionLabel } from "@/components/ui";
import { PortfolioStats } from "@/components/PortfolioStats";
import { Project } from "@/types";

const STAGES = ["pre-seed", "seed", "series-a", "series-b", "growth"];

export default function DashboardPage() {
  const { ready } = useRequireAuth();
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    company_name: "",
    industry: "",
    country: "",
    stage: "seed",
    founders: "",
    one_liner: "",
  });

  const { data: projects, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: api.listProjects,
    enabled: ready,
  });

  const { data: summary } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: api.getDashboardSummary,
    enabled: ready,
  });

  const createMutation = useMutation({
    mutationFn: (payload: typeof form) => api.createProject(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setShowForm(false);
      setForm({ company_name: "", industry: "", country: "", stage: "seed", founders: "", one_liner: "" });
    },
  });

  if (!ready) return null;

  return (
    <div className="min-h-screen">
      <Navbar title="Portfolio" />
      <main className="max-w-6xl mx-auto px-6 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="font-display text-2xl text-paper">Portfolio Overview</h1>
            <p className="text-sm text-paper-muted mt-1">
              {projects?.length || 0} companies under review
            </p>
          </div>
          <Button onClick={() => setShowForm((s) => !s)}>
            {showForm ? "Cancel" : "+ New Startup"}
          </Button>
        </div>

        {showForm && (
          <Card className="p-6 mb-8">
            <SectionLabel number="—" title="New Startup Profile" />
            <form
              onSubmit={(e) => {
                e.preventDefault();
                createMutation.mutate(form);
              }}
              className="grid grid-cols-1 md:grid-cols-2 gap-4"
            >
              <Input
                label="Company Name"
                required
                value={form.company_name}
                onChange={(e) => setForm((f) => ({ ...f, company_name: e.target.value }))}
              />
              <Input
                label="Industry"
                value={form.industry}
                onChange={(e) => setForm((f) => ({ ...f, industry: e.target.value }))}
              />
              <Input
                label="Country"
                value={form.country}
                onChange={(e) => setForm((f) => ({ ...f, country: e.target.value }))}
              />
              <Select
                label="Stage"
                value={form.stage}
                onChange={(e) => setForm((f) => ({ ...f, stage: e.target.value }))}
              >
                {STAGES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </Select>
              <Input
                label="Founders"
                placeholder="Jane Doe, John Smith"
                value={form.founders}
                onChange={(e) => setForm((f) => ({ ...f, founders: e.target.value }))}
              />
              <Input
                label="One-liner"
                value={form.one_liner}
                onChange={(e) => setForm((f) => ({ ...f, one_liner: e.target.value }))}
              />
              <div className="md:col-span-2">
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? "Creating…" : "Create Startup Profile"}
                </Button>
              </div>
            </form>
          </Card>
        )}

        {summary && summary.total_projects > 0 && <PortfolioStats summary={summary} />}

        {isLoading && <p className="text-sm text-paper-faint">Loading portfolio…</p>}

        {!isLoading && projects?.length === 0 && !showForm && (
          <Card className="p-10 text-center">
            <p className="text-paper-muted">No startups yet.</p>
            <p className="text-sm text-paper-faint mt-1">
              Add a company to begin building an investment memo.
            </p>
          </Card>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects?.map((p: Project) => (
            <Link key={p.id} href={`/dashboard/${p.id}`}>
              <Card className="p-5 h-full hover:border-gold/40 transition-colors">
                <div className="flex items-start justify-between">
                  <h3 className="font-display text-lg text-paper">{p.company_name}</h3>
                  <span className="font-mono text-[10px] uppercase text-gold border border-gold/30 px-1.5 py-0.5 rounded">
                    {p.stage || "—"}
                  </span>
                </div>
                <p className="text-sm text-paper-muted mt-2 line-clamp-2">
                  {p.one_liner || "No description yet."}
                </p>
                <div className="text-xs text-paper-faint mt-4 flex gap-3">
                  <span>{p.industry || "Unspecified industry"}</span>
                  <span>·</span>
                  <span>{p.country || "Unspecified"}</span>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}

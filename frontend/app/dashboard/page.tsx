"use client";
import { useQuery } from "@tanstack/react-query";
import { Shell } from "@/components/layout/shell";
import { RevenueChart } from "@/components/charts/revenue-chart";
import { FunnelChart } from "@/components/charts/funnel-chart";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChartSkeleton, Skeleton } from "@/components/ui/skeleton";
import { api } from "@/services/api";
import { QUERY_KEYS } from "@/constants";
import { formatPercent } from "@/lib/utils";
import { MessageSquareText, Sparkles, ArrowRight, Cpu } from "lucide-react";
import type { KPIs } from "@/types";
import Link from "next/link";

// ── helpers ──────────────────────────────────────────────────────────────────
const num = (v: unknown) => Number(String(v ?? 0).replace(/[^0-9.-]/g, "")) || 0;
const compactUSD = (v: number) =>
  v >= 1e6 ? `$${(v / 1e6).toFixed(2)}M` : v >= 1e3 ? `$${(v / 1e3).toFixed(0)}K` : `$${v.toFixed(0)}`;

const ACTION_STYLE: Record<string, { badge: "success" | "warning" | "danger" | "info"; ring: string }> = {
  LAUNCH: { badge: "success", ring: "border-emerald-500/30 from-emerald-600/10" },
  ITERATE: { badge: "warning", ring: "border-amber-500/30 from-amber-600/10" },
  ROLLBACK: { badge: "danger", ring: "border-red-500/30 from-red-600/10" },
  INVESTIGATE: { badge: "info", ring: "border-sky-500/30 from-sky-600/10" },
};

const AGENT_LABEL: Record<string, string> = {
  metrics_agent: "Metrics",
  experiment_agent: "Experiments",
  customer_voice_agent: "Customer Voice",
  release_incident_agent: "Release & Incidents",
};

// ── small building blocks ────────────────────────────────────────────────────
function SectionLabel({ title, discipline }: { title: string; discipline: string }) {
  return (
    <div className="flex items-baseline gap-2.5 mb-3">
      <h2 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">{title}</h2>
      <span className="text-[10px] text-zinc-600">{discipline}</span>
    </div>
  );
}

function MetricTile({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
      <p className="text-[11px] text-zinc-500 font-medium">{label}</p>
      <p className="text-2xl font-bold text-zinc-100 tracking-tight mt-1.5">{value}</p>
      {sub && <p className="text-[11px] text-zinc-600 mt-1">{sub}</p>}
    </div>
  );
}

function ModelTile({ method, color, value, label, href }: { method: string; color: string; value: string; label: string; href: string }) {
  return (
    <Link href={href} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 hover:border-zinc-700 transition-colors group">
      <span className={`inline-block text-[9px] font-semibold px-1.5 py-0.5 rounded ${color}`}>{method}</span>
      <p className="text-xl font-bold text-zinc-100 tracking-tight mt-2">{value}</p>
      <p className="text-[11px] text-zinc-500 mt-0.5 flex items-center gap-1">
        {label}
        <ArrowRight className="w-2.5 h-2.5 opacity-0 group-hover:opacity-100 transition-opacity" />
      </p>
    </Link>
  );
}

// ── hero: the AI decision (LLM + Decision Science) ──────────────────────────
function DecisionHero({ run }: { run: Record<string, unknown> | undefined }) {
  if (!run) return <Skeleton className="h-44 w-full rounded-xl" />;
  const rec = (run.recommendation ?? {}) as {
    action?: string; rationale?: string; confidence?: number;
    findings?: { agent: string; finding: string; confidence: number }[];
  };
  const llm = (run.llm ?? {}) as { model?: string; used_remote_llm?: boolean };
  const vdb = (run.vector_db ?? {}) as { documents_indexed?: number };
  const action = (rec.action ?? "—").toUpperCase();
  const style = ACTION_STYLE[action] ?? { badge: "info" as const, ring: "border-indigo-500/30 from-indigo-600/10" };

  return (
    <div className={`rounded-xl border bg-gradient-to-br to-zinc-900/60 p-6 ${style.ring}`}>
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="w-4 h-4 text-indigo-400" />
        <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">AI Decision</span>
        <span className="ml-auto flex items-center gap-1 text-[10px] text-zinc-500">
          <Cpu className="w-3 h-3" />
          {llm.model?.split("/").pop() ?? "LLM"} · LangGraph · {vdb.documents_indexed ?? 0} evidence docs
        </span>
      </div>

      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2.5 mb-2.5">
            <Badge variant={style.badge} className="text-sm px-3 py-1">{action}</Badge>
            {rec.confidence != null && (
              <span className="text-xs text-zinc-500">Confidence {Math.round((rec.confidence ?? 0) * 100)}%</span>
            )}
            {llm.used_remote_llm && (
              <span className="text-[10px] bg-indigo-500/15 text-indigo-400 px-1.5 py-0.5 rounded">🧠 LLM-synthesized</span>
            )}
          </div>
          <p className="text-sm text-zinc-300 leading-relaxed max-w-2xl">{rec.rationale ?? "Loading decision context..."}</p>
        </div>
        <Link
          href="/ai-assistant"
          className="flex items-center gap-1.5 text-xs font-medium text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/15 border border-indigo-500/20 px-3 py-2 rounded-lg transition-colors shrink-0"
        >
          <MessageSquareText className="w-3.5 h-3.5" /> Ask AI
        </Link>
      </div>

      {/* agent findings */}
      {rec.findings && rec.findings.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-5 pt-5 border-t border-zinc-800/80">
          {rec.findings.map((f) => (
            <div key={f.agent} className="flex items-start gap-2.5">
              <span className="text-[10px] font-semibold text-zinc-500 bg-zinc-800/70 px-1.5 py-0.5 rounded shrink-0 mt-0.5 min-w-[92px] text-center">
                {AGENT_LABEL[f.agent] ?? f.agent}
              </span>
              <p className="text-[11px] text-zinc-400 leading-snug">{f.finding}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── explainability: Decision Confidence + evidence attribution ──────────────
type Attribution = { agent: string; label: string; weight: number; direction: string; confidence: number };

const DIR_STYLE: Record<string, { bar: string; dot: string; tag: string }> = {
  risk: { bar: "bg-red-500/70", dot: "bg-red-400", tag: "text-red-400" },
  opportunity: { bar: "bg-emerald-500/70", dot: "bg-emerald-400", tag: "text-emerald-400" },
  informational: { bar: "bg-zinc-500/70", dot: "bg-zinc-400", tag: "text-zinc-400" },
};

function ConfidenceBreakdown({ run }: { run: Record<string, unknown> | undefined }) {
  if (!run) return <Skeleton className="h-56 w-full rounded-xl" />;
  const rec = (run.recommendation ?? {}) as { confidence?: number; attribution?: Attribution[] };
  const attribution = rec.attribution ?? [];
  const confidencePct = Math.round((rec.confidence ?? 0) * 100);
  if (attribution.length === 0) return null;

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
      <div className="flex items-start justify-between gap-4 mb-5">
        <div>
          <h3 className="text-sm font-semibold text-zinc-200">Decision Confidence</h3>
          <p className="text-[11px] text-zinc-500 mt-0.5">How each evidence stream contributed to the recommendation</p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-3xl font-bold text-zinc-100 tracking-tight leading-none">{confidencePct}%</p>
          <p className="text-[10px] text-zinc-500 mt-1 uppercase tracking-wider">confidence</p>
        </div>
      </div>

      <div className="space-y-3">
        {attribution.map((a) => {
          const s = DIR_STYLE[a.direction] ?? DIR_STYLE.informational;
          return (
            <div key={a.agent}>
              <div className="flex items-center justify-between text-[11px] mb-1">
                <span className="flex items-center gap-1.5 text-zinc-300">
                  <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
                  {a.label}
                  <span className={`text-[10px] ${s.tag}`}>· {a.direction}</span>
                </span>
                <span className="font-semibold text-zinc-200 tabular-nums">{a.weight}%</span>
              </div>
              <div className="h-2 rounded-full bg-zinc-800 overflow-hidden">
                <div className={`h-full rounded-full ${s.bar}`} style={{ width: `${a.weight}%` }} />
              </div>
            </div>
          );
        })}
      </div>

      <p className="text-[10px] text-zinc-600 mt-4 pt-4 border-t border-zinc-800/80">
        Weights are derived from each agent&apos;s evidence strength and direction, normalized to 100% — an explainable trace of the confidence score.
      </p>
    </div>
  );
}

export default function DashboardPage() {
  const { data: kpis } = useQuery({ queryKey: QUERY_KEYS.kpis, queryFn: api.kpis });
  const { data: revenue, isLoading: revLoading } = useQuery({ queryKey: QUERY_KEYS.monthlyRevenue, queryFn: api.monthlyRevenue });
  const { data: funnel, isLoading: funnelLoading } = useQuery({ queryKey: QUERY_KEYS.funnel, queryFn: api.funnel });
  const { data: run } = useQuery({ queryKey: QUERY_KEYS.decisionRun, queryFn: api.decisionRun });
  const { data: reviews } = useQuery({ queryKey: QUERY_KEYS.reviews, queryFn: () => api.reviews(500) });
  const { data: forecast } = useQuery({ queryKey: QUERY_KEYS.forecast, queryFn: api.forecast });
  const { data: anomalies } = useQuery({ queryKey: QUERY_KEYS.anomalies, queryFn: api.anomalies });
  const { data: segments } = useQuery({ queryKey: QUERY_KEYS.segments, queryFn: api.segments });
  const { data: modelEval } = useQuery({ queryKey: ["modelEval"], queryFn: api.modelEvaluation });

  const k = kpis as KPIs | undefined;

  // ── ML signal aggregates (from real outputs) ──
  const totalReviews = reviews?.reduce((s, r) => s + num(r.reviews), 0) ?? 0;
  const posReviews = reviews?.filter((r) => r.sentiment === "positive").reduce((s, r) => s + num(r.reviews), 0) ?? 0;
  const posPct = totalReviews ? Math.round((posReviews / totalReviews) * 100) : 0;
  const topicCount = reviews ? new Set(reviews.map((r) => r.topic)).size : 0;
  const forecastTotal = forecast?.reduce((s, r) => s + num(r.forecast_revenue), 0) ?? 0;
  const anomalyCount = anomalies?.filter((r) => String(r.is_anomaly).toLowerCase() === "true").length ?? 0;
  const segmentCount = segments?.length ?? 0;

  return (
    <Shell>
      <div className="space-y-8 max-w-6xl">
        <div>
          <h1 className="text-lg font-bold text-zinc-100">Decision Intelligence</h1>
          <p className="text-sm text-zinc-500 mt-0.5">Evidence-grounded product decisions from LLM agents, ML, and analytics.</p>
        </div>

        {/* 1 — AI DECISION (LLM + Decision Science) */}
        <section>
          <SectionLabel title="The Decision" discipline="LLM · Decision Science · Explainable AI" />
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
            <div className="lg:col-span-3">
              <DecisionHero run={run as Record<string, unknown> | undefined} />
            </div>
            <div className="lg:col-span-2">
              <ConfidenceBreakdown run={run as Record<string, unknown> | undefined} />
            </div>
          </div>
        </section>

        {/* 2 — BUSINESS METRICS (Analytics) */}
        <section>
          <SectionLabel title="Business Metrics" discipline="Warehouse · SQL" />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {k ? (
              <>
                <MetricTile label="Completed Revenue" value={compactUSD(k.completed_revenue)} sub={`${k.completed_orders.toLocaleString()} completed orders`} />
                <MetricTile label="Purchase Conversion" value={formatPercent(k.purchase_conversion)} sub={`${k.total_users.toLocaleString()} users`} />
                <MetricTile label="Avg Order Value" value={compactUSD(k.average_order_value)} sub={`${k.total_orders.toLocaleString()} total orders`} />
                <MetricTile label="Avg Review Rating" value={`${k.avg_review_rating} / 5`} sub={`cancellation ${formatPercent(k.cancellation_rate)}`} />
              </>
            ) : (
              [0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-24 rounded-xl" />)
            )}
          </div>
        </section>

        {/* 3 — ML SIGNALS (Data Science) */}
        <section>
          <SectionLabel title="ML Signals" discipline="Data Science · scikit-learn · XGBoost · Hugging Face" />
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <ModelTile method="DistilBERT" color="bg-emerald-500/15 text-emerald-400" value={`${posPct}%`} label="positive sentiment" href="/reviews" />
            <ModelTile method="BERTopic" color="bg-purple-500/15 text-purple-400" value={String(topicCount)} label="complaint topics" href="/reviews" />
            <ModelTile method="Holt-Winters" color="bg-blue-500/15 text-blue-400" value={compactUSD(forecastTotal)} label="14-day forecast" href="/analytics" />
            <ModelTile method="Isolation Forest" color="bg-amber-500/15 text-amber-400" value={String(anomalyCount)} label="anomalous days" href="/analytics" />
            <ModelTile method="KMeans" color="bg-cyan-500/15 text-cyan-400" value={String(segmentCount)} label="user segments" href="/analytics" />
            <ModelTile method="XGBoost + 4" color="bg-indigo-500/15 text-indigo-400" value={modelEval ? (modelEval as { best_metrics?: { roc_auc?: number } }).best_metrics?.roc_auc?.toFixed(3) ?? "—" : "—"} label="revenue-risk AUC" href="/risk-model" />
          </div>
        </section>

        {/* 4 — CHARTS */}
        <section>
          <SectionLabel title="Trends" discipline="Analytics" />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card className="lg:col-span-2">
              <CardHeader><CardTitle>Monthly Revenue</CardTitle></CardHeader>
              <CardContent>{revLoading ? <ChartSkeleton /> : revenue && <RevenueChart data={revenue} />}</CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Conversion Funnel</CardTitle></CardHeader>
              <CardContent>{funnelLoading ? <ChartSkeleton height="h-52" /> : funnel && <FunnelChart data={funnel} />}</CardContent>
            </Card>
          </div>
        </section>
      </div>
    </Shell>
  );
}

"use client";
import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Shell } from "@/components/layout/shell";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TableSkeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/states";
import { api } from "@/services/api";
import { QUERY_KEYS } from "@/constants";
import { FlaskConical, TrendingUp, TrendingDown } from "lucide-react";

const REC_VARIANT: Record<string, "success" | "warning" | "danger"> = {
  ship_or_expand: "success",
  continue_test_or_segment: "warning",
  rollback_or_redesign: "danger",
};

const REC_LABEL: Record<string, string> = {
  ship_or_expand: "Ship",
  continue_test_or_segment: "Continue",
  rollback_or_redesign: "Rollback",
};

export default function ExperimentsPage() {
  const [filter, setFilter] = useState<string>("all");
  const { data: experiments, isLoading } = useQuery({ queryKey: QUERY_KEYS.experiments, queryFn: api.experiments });

  const filtered = useMemo(() => {
    if (filter === "all") return experiments ?? [];
    return (experiments ?? []).filter(e => e.rollout_recommendation === filter);
  }, [experiments, filter]);

  const stats = useMemo(() => ({
    ship: (experiments ?? []).filter(e => e.rollout_recommendation === "ship_or_expand").length,
    continue: (experiments ?? []).filter(e => e.rollout_recommendation === "continue_test_or_segment").length,
    rollback: (experiments ?? []).filter(e => e.rollout_recommendation === "rollback_or_redesign").length,
  }), [experiments]);

  return (
    <Shell>
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-bold text-zinc-100">Experiments</h1>
          <p className="text-sm text-zinc-500 mt-0.5">A/B test results, statistical significance, and rollout decisions</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Ship or Expand", count: stats.ship, variant: "success" as const, icon: <TrendingUp className="w-4 h-4 text-emerald-400" /> },
            { label: "Continue / Segment", count: stats.continue, variant: "warning" as const, icon: <FlaskConical className="w-4 h-4 text-amber-400" /> },
            { label: "Rollback / Redesign", count: stats.rollback, variant: "danger" as const, icon: <TrendingDown className="w-4 h-4 text-red-400" /> },
          ].map(item => (
            <div key={item.label} className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 flex items-center gap-4">
              <div className="p-2 rounded-lg bg-zinc-800">{item.icon}</div>
              <div>
                <p className="text-2xl font-bold text-zinc-100">{item.count}</p>
                <p className="text-xs text-zinc-500">{item.label}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Filter */}
        <div className="flex gap-1 bg-zinc-900 border border-zinc-800 rounded-lg p-1 w-fit">
          {[["all", "All"], ["ship_or_expand", "Ship"], ["continue_test_or_segment", "Continue"], ["rollback_or_redesign", "Rollback"]].map(([val, label]) => (
            <button key={val} onClick={() => setFilter(val)}
              className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${filter === val ? "bg-zinc-800 text-zinc-100" : "text-zinc-500 hover:text-zinc-300"}`}>
              {label}
            </button>
          ))}
        </div>

        <Card>
          <CardContent className="pt-5">
            {isLoading ? <TableSkeleton rows={8} /> : filtered.length ? (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-zinc-800">
                      {["Experiment", "Feature Area", "Metric", "Lift", "P-Value", "Significant", "Decision"].map(h => (
                        <th key={h} className="text-left py-2 px-3 text-zinc-500 font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((r, i) => {
                      const lift = Number(r.lift_pct);
                      const pValue = Number(r.p_value);
                      const significant = pValue < 0.05;
                      return (
                        <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors">
                          <td className="py-2 px-3 text-zinc-300 font-medium">{r.experiment_id}</td>
                          <td className="py-2 px-3 text-zinc-400">{r.feature_area}</td>
                          <td className="py-2 px-3 text-zinc-400">{r.primary_metric}</td>
                          <td className={`py-2 px-3 font-medium ${lift > 0 ? "text-emerald-400" : "text-red-400"}`}>
                            {lift > 0 ? "+" : ""}{lift.toFixed(1)}%
                          </td>
                          <td className="py-2 px-3 text-zinc-400">{pValue.toFixed(3)}</td>
                          <td className="py-2 px-3">
                            <Badge variant={significant ? "success" : "default"}>{significant ? "Yes" : "No"}</Badge>
                          </td>
                          <td className="py-2 px-3">
                            <Badge variant={REC_VARIANT[r.rollout_recommendation] ?? "default"}>
                              {REC_LABEL[r.rollout_recommendation] ?? r.rollout_recommendation}
                            </Badge>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : <EmptyState />}
          </CardContent>
        </Card>
      </div>
    </Shell>
  );
}

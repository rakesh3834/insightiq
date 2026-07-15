"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Shell } from "@/components/layout/shell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { RevenueChart } from "@/components/charts/revenue-chart";
import { ForecastChart } from "@/components/charts/forecast-chart";
import { Badge } from "@/components/ui/badge";
import { ChartSkeleton, TableSkeleton } from "@/components/ui/skeleton";
import { ErrorState, EmptyState } from "@/components/ui/states";
import { Button } from "@/components/ui/button";
import { api } from "@/services/api";
import { QUERY_KEYS } from "@/constants";
import { Download, Filter } from "lucide-react";

const TABS = ["Revenue", "Anomalies", "Forecast", "Segments", "Tableau"] as const;
type Tab = typeof TABS[number];

export default function AnalyticsPage() {
  const [tab, setTab] = useState<Tab>("Revenue");

  const { data: revenue, isLoading: revLoading } = useQuery({ queryKey: QUERY_KEYS.monthlyRevenue, queryFn: api.monthlyRevenue });
  const { data: anomalies, isLoading: anomLoading, error: anomError, refetch: refetchAnom } = useQuery({ queryKey: QUERY_KEYS.anomalies, queryFn: api.anomalies });
  const { data: forecast, isLoading: foreLoading } = useQuery({ queryKey: QUERY_KEYS.forecast, queryFn: api.forecast });
  const { data: segments, isLoading: segLoading } = useQuery({ queryKey: QUERY_KEYS.segments, queryFn: api.segments });
  const { data: tableau, isLoading: tabLoading } = useQuery({ queryKey: QUERY_KEYS.tableau, queryFn: api.tableau });

  const exportCSV = (data: Record<string, string>[], name: string) => {
    if (!data?.length) return;
    const csv = [Object.keys(data[0]).join(","), ...data.map(r => Object.values(r).join(","))].join("\n");
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([csv])); a.download = `${name}.csv`; a.click();
  };

  return (
    <Shell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-zinc-100">Analytics</h1>
            <p className="text-sm text-zinc-500 mt-0.5">Interactive charts and data exploration</p>
          </div>
          <Button variant="outline" size="sm"><Filter className="w-3.5 h-3.5" /> Filter</Button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-zinc-900 border border-zinc-800 rounded-lg p-1 w-fit">
          {TABS.map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${tab === t ? "bg-zinc-800 text-zinc-100" : "text-zinc-500 hover:text-zinc-300"}`}>
              {t}
            </button>
          ))}
        </div>

        {tab === "Revenue" && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Monthly Revenue Trend</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => revenue && exportCSV(revenue as Record<string, string>[], "monthly_revenue")}>
                <Download className="w-3.5 h-3.5" /> Export
              </Button>
            </CardHeader>
            <CardContent>
              {revLoading ? <ChartSkeleton /> : revenue ? <RevenueChart data={revenue} /> : <EmptyState />}
              {revenue && (
                <div className="mt-4 overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead><tr className="border-b border-zinc-800">{["Month", "Revenue", "Orders", "AOV"].map(h => <th key={h} className="text-left py-2 px-3 text-zinc-500 font-medium">{h}</th>)}</tr></thead>
                    <tbody>{revenue.slice(-6).map((r, i) => (
                      <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors">
                        <td className="py-2 px-3 text-zinc-300">{r.month}</td>
                        <td className="py-2 px-3 text-zinc-300">${Number(r.revenue).toLocaleString()}</td>
                        <td className="py-2 px-3 text-zinc-400">{r.orders}</td>
                        <td className="py-2 px-3 text-zinc-400">${Number(r.average_order_value).toFixed(0)}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {tab === "Anomalies" && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Anomaly Detection</CardTitle>
              <div className="flex items-center gap-2">
                <Badge variant="danger">{anomalies?.filter(a => a.is_anomaly === "True").length ?? 0} anomalies</Badge>
                <Button variant="ghost" size="sm" onClick={() => anomalies && exportCSV(anomalies, "anomalies")}><Download className="w-3.5 h-3.5" /></Button>
              </div>
            </CardHeader>
            <CardContent>
              {anomLoading ? <TableSkeleton /> : anomError ? <ErrorState onRetry={refetchAnom} /> : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead><tr className="border-b border-zinc-800">{["Date", "Orders", "Revenue", "Cancel Rate", "Status"].map(h => <th key={h} className="text-left py-2 px-3 text-zinc-500 font-medium">{h}</th>)}</tr></thead>
                    <tbody>{anomalies?.filter(a => a.is_anomaly === "True").slice(0, 20).map((r, i) => (
                      <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors">
                        <td className="py-2 px-3 text-zinc-300">{r.order_day}</td>
                        <td className="py-2 px-3 text-zinc-400">{r.orders}</td>
                        <td className="py-2 px-3 text-zinc-400">${Number(r.revenue).toLocaleString()}</td>
                        <td className="py-2 px-3 text-zinc-400">{(Number(r.cancellation_rate) * 100).toFixed(1)}%</td>
                        <td className="py-2 px-3"><Badge variant="danger">Anomaly</Badge></td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {tab === "Forecast" && (
          <Card>
            <CardHeader><CardTitle>14-Day Revenue Forecast</CardTitle></CardHeader>
            <CardContent>
              {foreLoading ? <ChartSkeleton /> : forecast ? <ForecastChart data={forecast} /> : <EmptyState />}
              {forecast && (
                <div className="mt-4 overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead><tr className="border-b border-zinc-800">{["Day", "Forecast Revenue", "Method"].map(h => <th key={h} className="text-left py-2 px-3 text-zinc-500 font-medium">{h}</th>)}</tr></thead>
                    <tbody>{forecast.map((r, i) => (
                      <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors">
                        <td className="py-2 px-3 text-zinc-300">{r.forecast_day}</td>
                        <td className="py-2 px-3 text-zinc-300">${Number(r.forecast_revenue).toLocaleString()}</td>
                        <td className="py-2 px-3 text-zinc-500">{r.method}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {tab === "Segments" && (
          <Card>
            <CardHeader><CardTitle>User Segments</CardTitle></CardHeader>
            <CardContent>
              {segLoading ? <TableSkeleton /> : segments?.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead><tr className="border-b border-zinc-800">{["Segment", "Users", "Avg Orders", "Avg Spend", "Avg Events", "Cancel Rate"].map(h => <th key={h} className="text-left py-2 px-3 text-zinc-500 font-medium">{h}</th>)}</tr></thead>
                    <tbody>{segments.map((r, i) => (
                      <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors">
                        <td className="py-2 px-3"><Badge variant="info">Segment {r.segment}</Badge></td>
                        <td className="py-2 px-3 text-zinc-300">{Number(r.users).toLocaleString()}</td>
                        <td className="py-2 px-3 text-zinc-400">{Number(r.avg_orders).toFixed(1)}</td>
                        <td className="py-2 px-3 text-zinc-400">${Number(r.avg_spend).toFixed(0)}</td>
                        <td className="py-2 px-3 text-zinc-400">{Number(r.avg_events).toFixed(1)}</td>
                        <td className="py-2 px-3 text-zinc-400">{(Number(r.avg_cancellation_rate) * 100).toFixed(1)}%</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              ) : <EmptyState />}
            </CardContent>
          </Card>
        )}

        {tab === "Tableau" && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Revenue by Category & Brand</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => tableau && exportCSV(tableau, "tableau_extract")}><Download className="w-3.5 h-3.5" /> Export</Button>
            </CardHeader>
            <CardContent>
              {tabLoading ? <TableSkeleton /> : tableau?.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead><tr className="border-b border-zinc-800">{["Category", "Brand", "Orders", "Revenue", "Avg Price", "Avg Rating"].map(h => <th key={h} className="text-left py-2 px-3 text-zinc-500 font-medium">{h}</th>)}</tr></thead>
                    <tbody>{tableau.slice(0, 30).map((r, i) => (
                      <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors">
                        <td className="py-2 px-3 text-zinc-300">{r.category}</td>
                        <td className="py-2 px-3 text-zinc-400">{r.brand}</td>
                        <td className="py-2 px-3 text-zinc-400">{r.orders}</td>
                        <td className="py-2 px-3 text-zinc-300">${Number(r.gross_item_revenue).toLocaleString()}</td>
                        <td className="py-2 px-3 text-zinc-400">${Number(r.avg_item_price).toFixed(0)}</td>
                        <td className="py-2 px-3 text-zinc-400">⭐ {Number(r.avg_review_rating).toFixed(1)}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              ) : <EmptyState />}
            </CardContent>
          </Card>
        )}
      </div>
    </Shell>
  );
}

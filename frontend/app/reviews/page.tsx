"use client";
import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Shell } from "@/components/layout/shell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { SentimentChart } from "@/components/charts/sentiment-chart";
import { Badge } from "@/components/ui/badge";
import { TableSkeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/states";
import { api } from "@/services/api";
import { QUERY_KEYS, SENTIMENT_COLORS } from "@/constants";

const SENTIMENTS = ["positive", "neutral", "negative"] as const;

export default function ReviewsPage() {
  const [sentiment, setSentiment] = useState<string[]>(["negative"]);
  const [category, setCategory] = useState("");

  const { data: reviews, isLoading } = useQuery({ queryKey: QUERY_KEYS.reviews, queryFn: () => api.reviews(500) });

  const categories = useMemo(() => [...new Set(reviews?.map(r => r.category) ?? [])].sort(), [reviews]);

  const filtered = useMemo(() => {
    let d = reviews ?? [];
    if (sentiment.length) d = d.filter(r => sentiment.includes(r.sentiment));
    if (category) d = d.filter(r => r.category === category);
    return d;
  }, [reviews, sentiment, category]);

  const sentimentCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    (reviews ?? []).forEach(r => { counts[r.sentiment] = (counts[r.sentiment] ?? 0) + Number(r.reviews); });
    return Object.entries(counts).map(([sentiment, count]) => ({ sentiment, count }));
  }, [reviews]);

  const topTopics = useMemo(() => {
    const counts: Record<string, number> = {};
    (reviews ?? []).forEach(r => { counts[r.topic] = (counts[r.topic] ?? 0) + Number(r.reviews); });
    return Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 10);
  }, [reviews]);

  return (
    <Shell>
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-bold text-zinc-100">Review Intelligence</h1>
          <p className="text-sm text-zinc-500 mt-0.5">Sentiment analysis, topic clusters, and customer voice</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Sentiment chart */}
          <Card>
            <CardHeader><CardTitle>Sentiment Distribution</CardTitle></CardHeader>
            <CardContent>
              <SentimentChart data={sentimentCounts} />
            </CardContent>
          </Card>

          {/* Topic clusters */}
          <Card className="lg:col-span-2">
            <CardHeader><CardTitle>Top Topics</CardTitle></CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {topTopics.map(([topic, count]) => (
                  <div key={topic} className="flex items-center gap-1.5 bg-zinc-800/60 border border-zinc-700 rounded-lg px-3 py-1.5">
                    <span className="text-xs text-zinc-300">{topic}</span>
                    <span className="text-[10px] text-zinc-500">{count}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex gap-1">
            {SENTIMENTS.map(s => (
              <button key={s} onClick={() => setSentiment(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s])}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${sentiment.includes(s) ? "border-transparent text-white" : "bg-transparent border-zinc-700 text-zinc-500 hover:text-zinc-300"}`}
                style={sentiment.includes(s) ? { background: SENTIMENT_COLORS[s] + "33", borderColor: SENTIMENT_COLORS[s] + "66", color: SENTIMENT_COLORS[s] } : {}}>
                {s}
              </button>
            ))}
          </div>
          <select value={category} onChange={e => setCategory(e.target.value)}
            className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-300 outline-none focus:border-indigo-500/50">
            <option value="">All categories</option>
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <span className="text-xs text-zinc-600 ml-auto">{filtered.length} results</span>
        </div>

        {/* Table */}
        <Card>
          <CardContent className="pt-5">
            {isLoading ? <TableSkeleton rows={8} /> : filtered.length ? (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead><tr className="border-b border-zinc-800">{["Category", "Brand", "Topic", "Sentiment", "Reviews", "Avg Rating"].map(h => <th key={h} className="text-left py-2 px-3 text-zinc-500 font-medium">{h}</th>)}</tr></thead>
                  <tbody>{filtered.slice(0, 50).map((r, i) => (
                    <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors">
                      <td className="py-2 px-3 text-zinc-300">{r.category}</td>
                      <td className="py-2 px-3 text-zinc-400">{r.brand}</td>
                      <td className="py-2 px-3 text-zinc-400">{r.topic}</td>
                      <td className="py-2 px-3">
                        <Badge variant={r.sentiment === "positive" ? "success" : r.sentiment === "negative" ? "danger" : "default"}>{r.sentiment}</Badge>
                      </td>
                      <td className="py-2 px-3 text-zinc-400">{r.reviews}</td>
                      <td className="py-2 px-3 text-zinc-400">⭐ {Number(r.avg_rating).toFixed(1)}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            ) : <EmptyState message="No reviews match the selected filters." />}
          </CardContent>
        </Card>
      </div>
    </Shell>
  );
}

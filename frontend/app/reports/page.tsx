"use client";
import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Shell } from "@/components/layout/shell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/services/api";
import { QUERY_KEYS } from "@/constants";
import { Download, CheckCircle, XCircle, Sparkles, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const TABS = ["Decision Memo", "Presentation", "PRD Compliance"] as const;
type Tab = typeof TABS[number];

const SUGGESTED = [
  "Should we launch the new checkout?",
  "Should we roll back the search experiment?",
  "Why is purchase conversion dropping?",
  "What should we do about negative reviews?",
];

const PROSE = "prose prose-invert prose-sm max-w-none text-zinc-300 [&_h1]:text-zinc-100 [&_h2]:text-zinc-200 [&_h3]:text-zinc-300 [&_strong]:text-zinc-200 [&_code]:bg-zinc-800 [&_code]:px-1 [&_code]:rounded [&_blockquote]:border-l-indigo-500 [&_blockquote]:text-zinc-400";

type Generated = { question: string; memo: string; presentation: string; used_remote_llm: boolean; decision: { action?: string; confidence?: number } };

export default function ReportsPage() {
  const [tab, setTab] = useState<Tab>("Decision Memo");
  const [question, setQuestion] = useState("");
  const [generated, setGenerated] = useState<Generated | null>(null);
  const [generating, setGenerating] = useState(false);

  const { data: memo, isLoading: memoLoading } = useQuery({ queryKey: QUERY_KEYS.decisionMemo, queryFn: api.decisionMemo });
  const { data: presentation, isLoading: presLoading } = useQuery({ queryKey: QUERY_KEYS.presentation, queryFn: api.presentation });
  const { data: prd, isLoading: prdLoading } = useQuery({ queryKey: QUERY_KEYS.prdCompliance, queryFn: api.prdCompliance });

  const generate = async (q: string) => {
    if (!q.trim() || generating) return;
    setGenerating(true);
    try {
      const res = await api.generateReport(q);
      setGenerated(res);
      if (tab === "PRD Compliance") setTab("Decision Memo");
    } catch {
      setGenerated({ question: q, memo: `> Could not generate the report. Is the API running on \`localhost:8000\`?`, presentation: "", used_remote_llm: false, decision: {} });
    } finally {
      setGenerating(false);
    }
  };

  // Deep-link support: ?tab=PRD+Compliance opens a tab; ?q=... auto-generates a report.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const t = params.get("tab");
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (t && (TABS as readonly string[]).includes(t)) setTab(t as Tab);
    const q = params.get("q");
    if (q) { setQuestion(q); generate(q); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Generated report (question-specific) takes precedence over the default pipeline report.
  const memoMd = generated?.memo ?? memo?.memo ?? "";
  const presMd = generated?.presentation ?? presentation?.presentation ?? "";

  const download = (content: string, filename: string) => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([content], { type: "text/markdown" }));
    a.download = filename; a.click();
  };

  return (
    <Shell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-zinc-100">Reports</h1>
            <p className="text-sm text-zinc-500 mt-0.5">Decision memos, executive presentations, and compliance</p>
          </div>
        </div>

        {/* Question box — regenerate the memo + presentation for a specific question */}
        <div className="rounded-xl border border-indigo-500/20 bg-gradient-to-br from-indigo-600/10 to-zinc-900/40 p-4">
          <div className="flex items-center gap-2 mb-2.5">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">Generate a report for a question</span>
          </div>
          <div className="flex gap-2">
            <input
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => e.key === "Enter" && generate(question)}
              placeholder="e.g. Should we roll back the new search ranking experiment?"
              className="flex-1 bg-zinc-900 border border-zinc-800 focus:border-indigo-500/50 rounded-lg px-3.5 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 outline-none"
            />
            <Button variant="primary" size="md" onClick={() => generate(question)} disabled={!question.trim() || generating}>
              {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              {generating ? "Generating..." : "Generate"}
            </Button>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-2.5">
            {SUGGESTED.map(q => (
              <button key={q} onClick={() => { setQuestion(q); generate(q); }}
                className="text-[11px] bg-zinc-900 border border-zinc-800 hover:border-indigo-500/40 hover:text-indigo-400 text-zinc-500 px-2.5 py-1 rounded-full transition-all">
                {q}
              </button>
            ))}
          </div>
          {generated && (
            <p className="text-[11px] text-zinc-500 mt-2.5">
              Showing report for: <span className="text-zinc-300">“{generated.question}”</span>
              {generated.decision.action && <> — decision <span className="text-indigo-400 font-medium">{generated.decision.action.toUpperCase()}</span></>}
              {" · "}{generated.used_remote_llm ? "LLM-generated" : "deterministic"}
              {" · "}<button onClick={() => setGenerated(null)} className="text-zinc-500 hover:text-zinc-300 underline">reset to default</button>
            </p>
          )}
        </div>

        <div className="flex gap-1 bg-zinc-900 border border-zinc-800 rounded-lg p-1 w-fit">
          {TABS.map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${tab === t ? "bg-zinc-800 text-zinc-100" : "text-zinc-500 hover:text-zinc-300"}`}>
              {t}
            </button>
          ))}
        </div>

        {tab === "Decision Memo" && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>{generated ? "Decision Memo (generated)" : "Decision Memo"}</CardTitle>
              <Button variant="outline" size="sm" onClick={() => memoMd && download(memoMd, "decision_memo.md")}>
                <Download className="w-3.5 h-3.5" /> Download MD
              </Button>
            </CardHeader>
            <CardContent>
              {(memoLoading && !generated) || generating ? <Skeleton className="h-64 w-full" /> : (
                <div className={PROSE}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{memoMd}</ReactMarkdown>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {tab === "Presentation" && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>{generated ? "Executive Presentation (generated)" : "Executive Presentation"}</CardTitle>
              <Button variant="outline" size="sm" onClick={() => presMd && download(presMd, "presentation.md")}>
                <Download className="w-3.5 h-3.5" /> Download MD
              </Button>
            </CardHeader>
            <CardContent>
              {(presLoading && !generated) || generating ? <Skeleton className="h-64 w-full" /> : (
                <div className={PROSE}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{presMd}</ReactMarkdown>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {tab === "PRD Compliance" && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>PRD Compliance Matrix</CardTitle>
              {prd && <Badge variant="success">{prd.filter(r => r.status === "complete").length}/{prd.length} Complete</Badge>}
            </CardHeader>
            <CardContent>
              {prdLoading ? <Skeleton className="h-64 w-full" /> : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead><tr className="border-b border-zinc-800">{["Requirement", "Status", "Artifact"].map(h => <th key={h} className="text-left py-2 px-3 text-zinc-500 font-medium">{h}</th>)}</tr></thead>
                    <tbody>{prd?.map((r, i) => (
                      <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors">
                        <td className="py-2 px-3 text-zinc-300">{r.prd_requirement}</td>
                        <td className="py-2 px-3">
                          <div className="flex items-center gap-1.5">
                            {r.status === "complete"
                              ? <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                              : <XCircle className="w-3.5 h-3.5 text-red-400" />}
                            <Badge variant={r.status === "complete" ? "success" : "danger"}>{r.status}</Badge>
                          </div>
                        </td>
                        <td className="py-2 px-3 text-zinc-500 font-mono text-[11px]">{r.artifact}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </Shell>
  );
}

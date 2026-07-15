"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Shell } from "@/components/layout/shell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { api, type ModelEvaluation, type FeatureSelection } from "@/services/api";
import { Brain, Loader2, Play, Check, Minus } from "lucide-react";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine,
  ScatterChart, Scatter, Legend,
} from "recharts";

const TT = { background: "#18181b", border: "1px solid #3f3f46", borderRadius: 8, fontSize: 12 };

function MetricTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
      <p className="text-[11px] text-zinc-500 font-medium">{label}</p>
      <p className="text-2xl font-bold text-zinc-100 tracking-tight mt-1">{value}</p>
    </div>
  );
}

function PredictionPlayground() {
  const [f, setF] = useState({ order_value: 1200, total_qty: 8, n_items: 4, avg_item_price: 150, n_events: 3, account_age_days: 5, order_hour: 2, is_weekend: 1, gender: "male" });
  const [result, setResult] = useState<{ cancellation_probability: number; risk_band: string; model: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try { setResult(await api.modelPredict(f)); } catch { setResult(null); } finally { setLoading(false); }
  };

  const fields: [keyof typeof f, string][] = [
    ["order_value", "Order value ($)"], ["total_qty", "Total quantity"], ["n_events", "User events"],
    ["account_age_days", "Account age (days)"], ["order_hour", "Order hour (0-23)"], ["is_weekend", "Weekend (0/1)"],
  ];
  const bandColor: Record<string, string> = { high: "text-red-400", medium: "text-amber-400", low: "text-emerald-400" };

  return (
    <Card>
      <CardHeader><CardTitle>Prediction Playground</CardTitle></CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {fields.map(([k, label]) => (
            <div key={k}>
              <label className="text-[11px] text-zinc-500">{label}</label>
              <input type="number" value={f[k] as number}
                onChange={e => setF({ ...f, [k]: Number(e.target.value) })}
                className="w-full mt-1 bg-zinc-900 border border-zinc-800 focus:border-indigo-500/50 rounded-lg px-3 py-1.5 text-sm text-zinc-200 outline-none" />
            </div>
          ))}
        </div>
        <div className="flex items-center gap-4 mt-4">
          <Button variant="primary" size="md" onClick={run} disabled={loading}>
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Predict risk
          </Button>
          {result && (
            <div className="flex items-center gap-3">
              <span className={`text-2xl font-bold ${bandColor[result.risk_band] ?? "text-zinc-200"}`}>
                {(result.cancellation_probability * 100).toFixed(1)}%
              </span>
              <Badge variant={result.risk_band === "high" ? "danger" : result.risk_band === "medium" ? "warning" : "success"}>
                {result.risk_band} risk
              </Badge>
              <span className="text-[11px] text-zinc-600">via {result.model}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function BusinessCasePanel({ m }: { m: ModelEvaluation }) {
  const b = m.business_case;
  const tw = b.test_window;
  const usd = (n: number) => `$${Math.round(n).toLocaleString()}`;
  const qa: [string, string][] = [
    ["Why this model?", b.why_this_model],
    ["What problem does it solve?", b.problem],
    ["What decision does it drive?", b.decision_enabled],
    ["Which business metric does it move?", `${b.primary_metric}. The threshold is the lever — ${b.lever.replace(/^The threshold is the business lever: /, "")}`],
  ];
  return (
    <section>
      <div className="flex items-baseline gap-2.5 mb-3">
        <h2 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">Model Card — Business Case</h2>
        <span className="text-[10px] text-zinc-600">why it exists · what it moves · what it&apos;s worth</span>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Why this model, and what it solves</CardTitle></CardHeader>
          <CardContent>
            <dl className="space-y-3">
              {qa.map(([q, a]) => (
                <div key={q}>
                  <dt className="text-[11px] font-semibold text-indigo-300">{q}</dt>
                  <dd className="text-[13px] text-zinc-400 leading-relaxed mt-0.5">{a}</dd>
                </div>
              ))}
            </dl>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>What it&apos;s worth</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
                <p className="text-[11px] text-emerald-300/80 font-medium">Recovered GMV / test window</p>
                <p className="text-2xl font-bold text-emerald-300 tracking-tight mt-1">{usd(b.recovered_gmv)}</p>
                <p className="text-[10px] text-zinc-500 mt-1">{tw.caught_cancellations.toLocaleString()} caught × {usd(b.avg_order_value)} AOV × {(b.assumed_save_rate * 100).toFixed(0)}% save rate</p>
              </div>
              <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
                <p className="text-[11px] text-red-300/80 font-medium">Still leaking if no action</p>
                <p className="text-2xl font-bold text-red-300 tracking-tight mt-1">{usd(b.leaked_gmv_if_no_action)}</p>
                <p className="text-[10px] text-zinc-500 mt-1">{tw.missed_cancellations.toLocaleString()} missed cancellations × AOV</p>
              </div>
              <p className="text-[11px] text-zinc-500">
                At threshold <span className="text-zinc-300 font-medium">{b.operating_threshold}</span>: flags {(tw.review_rate * 100).toFixed(0)}% of orders
                ({tw.flagged_for_review.toLocaleString()}) for review, catching <span className="text-emerald-400">{(tw.recall * 100).toFixed(0)}%</span> of cancellations at {(tw.precision * 100).toFixed(0)}% precision.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
      <p className="text-[10px] text-zinc-600 mt-2">Figures scoped to the held-out test window ({tw.orders.toLocaleString()} orders); save rate is a documented assumption — replace with a measured rate once intervention A/B data exists.</p>
    </section>
  );
}

function CalibrationPanel({ m }: { m: ModelEvaluation }) {
  const c = m.calibration;
  const rt = m.recommended_threshold;
  const brierDrop = c.brier_uncalibrated > 0 ? ((1 - c.brier_calibrated / c.brier_uncalibrated) * 100) : 0;
  return (
    <section>
      <div className="flex items-baseline gap-2.5 mb-3">
        <h2 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">Calibration &amp; Operating Threshold</h2>
        <span className="text-[10px] text-zinc-600">Isotonic calibration · Brier score · max-F1 threshold on held-out test</span>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader><CardTitle>Reliability curve (are the probabilities honest?)</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={230}>
              <ScatterChart margin={{ left: 4, right: 12, top: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis type="number" dataKey="mean_predicted" domain={[0, 1]} tick={{ fontSize: 10, fill: "#71717a" }}
                  label={{ value: "Mean predicted", position: "insideBottom", offset: -2, fontSize: 10, fill: "#71717a" }} />
                <YAxis type="number" dataKey="observed_frequency" domain={[0, 1]} tick={{ fontSize: 10, fill: "#71717a" }} />
                <Tooltip contentStyle={TT} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="#3f3f46" strokeDasharray="4 4" />
                <Scatter name="Uncalibrated" data={c.reliability_uncalibrated} fill="#f59e0b" line={{ stroke: "#f59e0b" }} isAnimationActive={false} />
                <Scatter name="Calibrated" data={c.reliability_calibrated} fill="#6366f1" line={{ stroke: "#6366f1" }} isAnimationActive={false} />
              </ScatterChart>
            </ResponsiveContainer>
            <div className="grid grid-cols-2 gap-3 mt-3">
              <MetricTile label="Brier — uncalibrated" value={c.brier_uncalibrated.toFixed(3)} />
              <MetricTile label={`Brier — ${c.method} calibrated`} value={c.brier_calibrated.toFixed(3)} />
            </div>
            <p className="text-[11px] text-zinc-500 mt-2">
              Isotonic calibration pulls the curve onto the diagonal — a <span className="text-emerald-400 font-medium">{brierDrop.toFixed(0)}% lower Brier score</span>, so predicted probabilities can be trusted as real cancellation rates.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Threshold sweep — picking the operating point</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={230}>
              <LineChart data={m.threshold_sweep} margin={{ left: 4, right: 12, top: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="threshold" type="number" domain={[0.1, 0.9]} tick={{ fontSize: 10, fill: "#71717a" }}
                  label={{ value: "Decision threshold", position: "insideBottom", offset: -2, fontSize: 10, fill: "#71717a" }} />
                <YAxis type="number" domain={[0, 1]} tick={{ fontSize: 10, fill: "#71717a" }} />
                <Tooltip contentStyle={TT} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <ReferenceLine x={rt.threshold} stroke="#10b981" strokeDasharray="4 4"
                  label={{ value: `F1-optimal ${rt.threshold}`, position: "top", fontSize: 10, fill: "#10b981" }} />
                <Line type="monotone" dataKey="precision" stroke="#f59e0b" strokeWidth={2} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="recall" stroke="#38bdf8" strokeWidth={2} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="f1" stroke="#6366f1" strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
            <p className="text-[11px] text-zinc-500 mt-2">
              Because cancellations are the minority class, the naive 0.5 cut is wrong. Max-F1 lands at
              <span className="text-emerald-400 font-medium"> {rt.threshold}</span> — precision {rt.precision.toFixed(2)}, recall {rt.recall.toFixed(2)}, flagging {(rt.flagged_rate * 100).toFixed(0)}% of orders for intervention.
            </p>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

function FeatureSelectionPanel() {
  const { data } = useQuery({ queryKey: ["featureSelection"], queryFn: api.modelFeatureSelection });
  const fs = data as FeatureSelection | undefined;
  if (!fs) return null;
  const Yes = () => <Check className="w-3.5 h-3.5 text-emerald-400 mx-auto" />;
  const No = () => <Minus className="w-3 h-3 text-zinc-700 mx-auto" />;
  const cols: [string, keyof FeatureSelection["selection"][number]][] = [
    ["MI", "mutual_information"], ["L1", "l1"], ["RFECV", "rfecv"], ["SFS", "sfs"], ["SBS", "sbs"],
  ];
  return (
    <section>
      <div className="flex items-baseline gap-2.5 mb-3">
        <h2 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">Feature Selection</h2>
        <span className="text-[10px] text-zinc-600">Filter (MI) · Embedded (L1) · Wrapper (RFECV, forward SFS, backward SBS) · {fs.cv_folds}-fold CV</span>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader><CardTitle>Which method keeps which feature</CardTitle></CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead><tr className="border-b border-zinc-800 text-zinc-500">
                  <th className="text-left py-2 px-2 font-medium">Feature</th>
                  {cols.map(([h]) => <th key={h} className="py-2 px-2 font-medium text-center">{h}</th>)}
                  <th className="py-2 px-2 font-medium text-center">Votes</th>
                </tr></thead>
                <tbody>
                  {fs.selection.map((s) => (
                    <tr key={s.feature} className="border-b border-zinc-800/50">
                      <td className="py-1.5 px-2 text-zinc-300">{s.feature}</td>
                      {cols.map(([h, key]) => <td key={h} className="py-1.5 px-2">{s[key] ? <Yes /> : <No />}</td>)}
                      <td className="py-1.5 px-2 text-center">
                        <Badge variant={s.votes >= 3 ? "success" : s.votes >= 1 ? "warning" : "default"}>{s.votes}/5</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-[11px] text-zinc-500 mt-3">
              <span className="text-emerald-400 font-medium">Consensus (≥3 votes):</span> {fs.consensus_features.join(", ")}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Model AUC per selected subset</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={230}>
              <BarChart data={fs.subset_auc} layout="vertical" margin={{ left: 20, right: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
                <XAxis type="number" domain={[0.6, 0.8]} tick={{ fontSize: 10, fill: "#71717a" }} />
                <YAxis type="category" dataKey="method" width={110} tick={{ fontSize: 10, fill: "#a1a1aa" }} />
                <Tooltip contentStyle={TT} />
                <Bar dataKey="roc_auc" radius={[0, 4, 4, 0]} isAnimationActive={false} label={{ position: "right", fontSize: 10, fill: "#71717a" }}>
                  {fs.subset_auc.map((r, i) => <Cell key={i} fill={r.method === "Full feature set" ? "#3f3f46" : "#6366f1"} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <p className="text-[11px] text-zinc-500 mt-1">Wrapper methods match the full-set AUC with far fewer features; the univariate MI filter underperforms (misses multivariate signal).</p>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

export default function RiskModelPage() {
  const { data, isLoading } = useQuery({ queryKey: ["modelEval"], queryFn: api.modelEvaluation });
  const m = data as ModelEvaluation | undefined;

  return (
    <Shell>
      <div className="space-y-8 max-w-6xl">
        <div>
          <h1 className="text-lg font-bold text-zinc-100 flex items-center gap-2"><Brain className="w-5 h-5 text-indigo-400" /> Cancellation Risk Model</h1>
          <p className="text-sm text-zinc-500 mt-0.5">Supervised ML — trained, evaluated, and served from a persisted model. Predicts which orders are likely to cancel.</p>
        </div>

        {isLoading || !m ? <Skeleton className="h-40 w-full rounded-xl" /> : (
          <>
            <BusinessCasePanel m={m} />

            {/* Best model metrics */}
            <section>
              <div className="flex items-baseline gap-2.5 mb-3">
                <h2 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">Best Model</h2>
                <Badge variant="info">{m.best_model}</Badge>
                <span className="text-[10px] text-zinc-600">selected by {m.cv_folds}-fold CV ROC-AUC ({m.best_metrics.cv_auc_mean.toFixed(3)} ± {m.best_metrics.cv_auc_std.toFixed(3)}) · {m.n_train.toLocaleString()} train / {m.n_test.toLocaleString()} test · base rate {(m.base_rate * 100).toFixed(1)}%</span>
              </div>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <MetricTile label="ROC-AUC" value={m.best_metrics.roc_auc.toFixed(3)} />
                <MetricTile label="Precision" value={m.best_metrics.precision.toFixed(3)} />
                <MetricTile label="Recall" value={m.best_metrics.recall.toFixed(3)} />
                <MetricTile label="F1 Score" value={m.best_metrics.f1.toFixed(3)} />
              </div>
            </section>

            {/* Leaderboard + ROC */}
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader><CardTitle>Model Leaderboard ({m.cv_folds}-fold CV ROC-AUC)</CardTitle></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={m.models} layout="vertical" margin={{ left: 20, right: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
                      <XAxis type="number" domain={[0.5, 0.8]} tick={{ fontSize: 10, fill: "#71717a" }} />
                      <YAxis type="category" dataKey="model" width={130} tick={{ fontSize: 10, fill: "#a1a1aa" }} />
                      <Tooltip contentStyle={TT} formatter={(v, _n, p) => [`${Number(v).toFixed(4)} ± ${Number(p?.payload?.cv_auc_std ?? 0).toFixed(4)}`, "CV ROC-AUC"]} />
                      <Bar dataKey="cv_auc_mean" radius={[0, 4, 4, 0]} isAnimationActive={false}>
                        {m.models.map((r, i) => <Cell key={i} fill={r.model === m.best_model ? "#6366f1" : "#3f3f46"} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <p className="text-[11px] text-zinc-500 mt-1">Ranked by mean cross-validated AUC (error bars = fold std) rather than a single split — robust to split luck.</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>ROC Curve — {m.best_model}</CardTitle></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={m.roc_curve.fpr.map((x, i) => ({ fpr: x, tpr: m.roc_curve.tpr[i] }))}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="fpr" type="number" domain={[0, 1]} tick={{ fontSize: 10, fill: "#71717a" }} label={{ value: "FPR", position: "insideBottom", offset: -2, fontSize: 10, fill: "#71717a" }} />
                      <YAxis type="number" domain={[0, 1]} tick={{ fontSize: 10, fill: "#71717a" }} />
                      <Tooltip contentStyle={TT} />
                      <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="#3f3f46" strokeDasharray="4 4" />
                      <Line type="monotone" dataKey="tpr" stroke="#6366f1" strokeWidth={2} dot={false} isAnimationActive={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </section>

            {/* Feature importance + confusion matrix */}
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader><CardTitle>Feature Importance (permutation)</CardTitle></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={230}>
                    <BarChart data={[...m.feature_importance].reverse()} layout="vertical" margin={{ left: 20, right: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
                      <XAxis type="number" tick={{ fontSize: 10, fill: "#71717a" }} />
                      <YAxis type="category" dataKey="feature" width={110} tick={{ fontSize: 10, fill: "#a1a1aa" }} />
                      <Tooltip contentStyle={TT} />
                      <Bar dataKey="importance" fill="#10b981" radius={[0, 4, 4, 0]} isAnimationActive={false} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Confusion Matrix (test set)</CardTitle></CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-2 max-w-sm mx-auto mt-4">
                    {([["True Negative", m.confusion_matrix[0][0], "bg-emerald-500/5 border-emerald-500/20"],
                      ["False Positive", m.confusion_matrix[0][1], "bg-amber-500/5 border-amber-500/20"],
                      ["False Negative", m.confusion_matrix[1][0], "bg-red-500/5 border-red-500/20"],
                      ["True Positive", m.confusion_matrix[1][1], "bg-emerald-500/5 border-emerald-500/20"]] as [string, number, string][]).map(([label, val, cls], i) => (
                      <div key={i} className={`rounded-lg border p-4 text-center ${cls}`}>
                        <p className="text-2xl font-bold text-zinc-100">{val.toLocaleString()}</p>
                        <p className="text-[11px] text-zinc-500 mt-1">{label}</p>
                      </div>
                    ))}
                  </div>
                  <p className="text-[11px] text-zinc-600 text-center mt-3">Rows = actual, columns = predicted at the F1-optimal threshold ({m.recommended_threshold.threshold})</p>
                </CardContent>
              </Card>
            </section>

            <CalibrationPanel m={m} />

            <FeatureSelectionPanel />

            <PredictionPlayground />

            <p className="text-[11px] text-zinc-600">{m.note}</p>
          </>
        )}
      </div>
    </Shell>
  );
}

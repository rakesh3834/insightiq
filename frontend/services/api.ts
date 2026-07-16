const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

export const api = {
  health: () => get<{ status: string }>("/health"),
  ask: (question: string) => post<Record<string, unknown>>("/ask", { question }),
  generateReport: (question: string) =>
    post<{ question: string; memo: string; presentation: string; used_remote_llm: boolean; decision: { action?: string; confidence?: number }; scope: Record<string, unknown> }>("/reports/generate", { question }),
  kpis: () => get<Record<string, number>>("/metrics/summary"),
  funnel: () => get<{ step: string; users: string }[]>("/metrics/funnel"),
  monthlyRevenue: () => get<{ month: string; revenue: string; orders: string; average_order_value: string }[]>("/metrics/monthly-revenue"),
  tableau: () => get<Record<string, string>[]>("/metrics/tableau"),
  reviews: (limit = 200) => get<Record<string, string>[]>(`/reviews/intelligence?limit=${limit}`),
  experiments: () => get<Record<string, string>[]>("/experiments/decisions"),
  anomalies: () => get<Record<string, string>[]>("/anomalies"),
  forecast: () => get<{ forecast_day: string; forecast_revenue: string; method: string }[]>("/forecast"),
  segments: () => get<Record<string, string>[]>("/segments/profiles"),
  releaseImpact: () => get<Record<string, string>[]>("/release/impact"),
  rootCause: () => get<Record<string, string>[]>("/root-cause/hypotheses"),
  decisionRun: () => get<Record<string, unknown>>("/decision-intelligence/run"),
  prdCompliance: () => get<Record<string, string>[]>("/prd/compliance"),
  decisionMemo: () => get<{ memo: string }>("/recommendations/decision"),
  presentation: () => get<{ presentation: string }>("/reports/presentation"),
  costOptimization: () => get<Record<string, unknown>>("/cost/optimization"),
  modelEvaluation: () => get<ModelEvaluation>("/model/evaluation"),
  modelFeatureSelection: () => get<FeatureSelection>("/model/feature-selection"),
  modelPredict: (features: Record<string, number | string>) =>
    post<{ cancellation_probability: number; risk_band: string; model: string }>("/model/predict", features),
};

export interface FeatureSelection {
  n_samples: number;
  cv_folds: number;
  methods: string[];
  selection: { feature: string; mi_score: number; mutual_information: boolean; l1: boolean; rfecv: boolean; sfs: boolean; sbs: boolean; votes: number }[];
  subset_auc: { method: string; n_features: number; roc_auc: number }[];
  consensus_features: string[];
  note: string;
}

export interface AttributionItem {
  agent: string;
  label: string;
  weight: number;
  direction: "risk" | "opportunity" | "informational";
  confidence: number;
}

export interface ModelEvaluation {
  model_name?: string;
  target_short?: string;
  target: string;
  n_samples: number;
  n_train: number;
  n_test: number;
  base_rate: number;
  cv_folds: number;
  selection_metric: string;
  features: string[];
  models: { model: string; cv_auc_mean: number; cv_auc_std: number; roc_auc: number; precision: number; recall: number; f1: number; accuracy: number }[];
  best_model: string;
  best_metrics: { model: string; cv_auc_mean: number; cv_auc_std: number; roc_auc: number; precision: number; recall: number; f1: number; accuracy: number };
  feature_importance: { feature: string; importance: number }[];
  roc_curve: { fpr: number[]; tpr: number[] };
  confusion_matrix: number[][];
  calibration: {
    method: string;
    brier_uncalibrated: number;
    brier_calibrated: number;
    reliability_uncalibrated: { mean_predicted: number; observed_frequency: number }[];
    reliability_calibrated: { mean_predicted: number; observed_frequency: number }[];
  };
  threshold_sweep: { threshold: number; precision: number; recall: number; f1: number; flagged_rate: number }[];
  recommended_threshold: { threshold: number; precision: number; recall: number; f1: number; flagged_rate: number; criterion: string };
  business_case: {
    problem: string;
    why_this_model: string;
    decision_enabled: string;
    primary_metric: string;
    operating_threshold: number;
    avg_order_value: number;
    assumed_save_rate: number;
    test_window: {
      orders: number; caught_cancellations: number; missed_cancellations: number;
      false_alarms: number; flagged_for_review: number; review_rate: number; precision: number; recall: number;
    };
    recovered_gmv: number;
    leaked_gmv_if_no_action: number;
    lever: string;
    recovered_gmv_formula: string;
  };
  note: string;
}

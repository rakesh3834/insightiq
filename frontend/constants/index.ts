export const NAV_ITEMS = [
  { label: "Dashboard", href: "/dashboard", icon: "LayoutDashboard" },
  { label: "AI Assistant", href: "/ai-assistant", icon: "Bot" },
  { label: "Analytics", href: "/analytics", icon: "BarChart3" },
  { label: "Reviews", href: "/reviews", icon: "Star" },
  { label: "Experiments", href: "/experiments", icon: "FlaskConical" },
  { label: "Reports", href: "/reports", icon: "FileText" },
  { label: "Settings", href: "/settings", icon: "Settings" },
] as const;

export const QUERY_KEYS = {
  kpis: ["kpis"],
  funnel: ["funnel"],
  monthlyRevenue: ["monthlyRevenue"],
  tableau: ["tableau"],
  reviews: ["reviews"],
  experiments: ["experiments"],
  anomalies: ["anomalies"],
  forecast: ["forecast"],
  segments: ["segments"],
  releaseImpact: ["releaseImpact"],
  rootCause: ["rootCause"],
  decisionRun: ["decisionRun"],
  prdCompliance: ["prdCompliance"],
  decisionMemo: ["decisionMemo"],
  presentation: ["presentation"],
} as const;

export const CHART_COLORS = {
  primary: "#6366f1",
  secondary: "#8b5cf6",
  success: "#10b981",
  warning: "#f59e0b",
  danger: "#ef4444",
  muted: "#6b7280",
  blue: "#3b82f6",
  cyan: "#06b6d4",
};

export const SENTIMENT_COLORS: Record<string, string> = {
  positive: "#10b981",
  neutral: "#6b7280",
  negative: "#ef4444",
};

export const RECOMMENDATION_COLORS: Record<string, string> = {
  ship_or_expand: "#10b981",
  continue_test_or_segment: "#f59e0b",
  rollback_or_redesign: "#ef4444",
};

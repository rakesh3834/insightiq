export interface KPIs {
  total_users: number;
  total_orders: number;
  completed_orders: number;
  completed_revenue: number;
  average_order_value: number;
  purchase_conversion: number;
  cancellation_rate: number;
  cart_rate: number;
  avg_review_rating: number;
  total_products: number;
  total_events: number;
}

export interface FunnelStep {
  step: string;
  users: string;
}

export interface MonthlyRevenue {
  month: string;
  revenue: string;
  orders: string;
  average_order_value: string;
}

export interface ReviewRow {
  category: string;
  brand: string;
  topic: string;
  sentiment: string;
  reviews: string;
  avg_rating: string;
}

export interface ExperimentRow {
  experiment_id: string;
  experiment_name: string;
  variant: string;
  metric: string;
  control_value: string;
  variant_value: string;
  lift: string;
  p_value: string;
  significant: string;
  rollout_recommendation: string;
}

export interface AnomalyRow {
  order_day: string;
  orders: string;
  revenue: string;
  cancellation_rate: string;
  anomaly_score: string;
  is_anomaly: string;
}

export interface ForecastRow {
  forecast_day: string;
  forecast_revenue: string;
  method: string;
}

export interface SegmentRow {
  segment: string;
  users: string;
  avg_orders: string;
  avg_spend: string;
  avg_events: string;
  avg_cancellation_rate: string;
}

export interface RootCauseRow {
  rank: string;
  hypothesis: string;
  confidence: string;
  evidence: string;
  recommended_action: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  thinking?: string[];
}

export type NavItem = {
  label: string;
  href: string;
  icon: string;
};

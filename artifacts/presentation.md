# InsightIQ Executive Presentation

## Slide 1: Decision
- Recommendation: INVESTIGATE
- Workflow: Mixpanel -> Tableau -> SQL -> Data Scientist -> Reviews -> Release Notes -> Presentation -> Decision

## Slide 2: Product Health
- Completed revenue: USD 2,419,712.58
- Purchase conversion: 33.3%
- Cancellation rate: 19.6%
- Average review rating: 3.54

## Slide 3: Customer Evidence
- Review intelligence is exported by category, brand, topic, and sentiment.
- Customer language is treated as supporting evidence, not a replacement for warehouse metrics.

## Slide 4: Data Science Evidence
- Anomaly detection flags unusual revenue/order/cancellation days.
- Segmentation identifies high-value, high-friction, and low-engagement user groups.
- Forecasting projects short-term revenue from recent completed-order trends.

## Slide 5: Recommendation Evidence
- 21 release areas have nearby anomalies or incidents.

## Slide 6: Decision Intelligence Workflow
- Question: Why should the product team investigate purchase conversion and rollout risk before expanding the latest ecommerce experience?
- Orchestrated action: INVESTIGATE
- Evidence coverage: 1.0
- Agents: 4
- Rationale: Multiple evidence streams show risk; the safest decision is to investigate before expanding rollout.

## Slide 7: Next Actions
- Review the highest-risk release areas.
- Validate event instrumentation for funnel drops.
- Prioritize review themes that overlap with high-revenue categories.
- Re-run the pipeline after the next release or incident window.
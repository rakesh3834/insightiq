# InsightIQ Decision Memo

Decision: INVESTIGATE

## Evidence
- 21 release areas have nearby anomalies or incidents.

## KPI Snapshot
- Completed revenue: USD 2,419,712.58
- Average order value: USD 595.93
- Cart rate: 70.2%
- Purchase conversion: 33.3%
- Cancellation rate: 19.6%
- Average review rating: 3.54

## Release Risk
- REL-013 Clothing: investigate (2 nearby anomalies, 2 related incidents).
- REL-017 Electronics: investigate (2 nearby anomalies, 1 related incidents).
- REL-020 Automotive: investigate (1 nearby anomalies, 3 related incidents).
- REL-021 Search: investigate (1 nearby anomalies, 3 related incidents).
- REL-001 Clothing: investigate (1 nearby anomalies, 2 related incidents).

## AI Decision Intelligence
- Decision question: Why should the product team investigate purchase conversion and rollout risk before expanding the latest ecommerce experience?
- Orchestrated action: INVESTIGATE
- Orchestrated confidence: 0.92
- Evidence coverage: 1.0
- Agent count: 4
- Evidence item count: 13

## Cancellation-Risk Model — Business Case
- Why this model: Cancellation is a pre-fulfilment decision: a calibrated per-order risk score lets ops intervene (verify payment, prioritise support, hold shipment) before the revenue is lost. Logistic Regression wins on cross-validated AUC, scores in <1ms, and yields calibrated probabilities ops can act on.
- Problem solved: Orders cancel after checkout, leaking revenue and burning fulfilment cost on orders that never complete.
- Decision enabled: Flag high-risk orders for a proactive save-intervention at the F1-optimal threshold.
- Primary metric: Cancellation rate → recovered GMV
- Operating point: threshold 0.25 → flags 40% of orders (2,017), catching 65% of cancellations at 42% precision.
- Value (test window of 5,000 orders): recovers ~USD 176,664 (847 caught × USD 596 AOV × 35% save rate); USD 274,129 still leaks with no action.
- Lever: The threshold is the business lever: lower it to recover more revenue (higher recall, more manual reviews); raise it to cut ops cost (higher precision, fewer flags).

## Trade-Offs
- Launch maximizes speed but risks compounding hidden quality issues.
- Iterate reduces product risk while preserving learning velocity.
- Rollback is reserved for clear customer or revenue harm.
- Investigate is appropriate when signals conflict or tracking quality is uncertain.
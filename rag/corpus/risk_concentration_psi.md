---
id: RISK-CONC-010
track: risk
topics: [concentration, institution, anomaly-score, psi]
asset_classes: [LOAN, DEPOSIT, SECURITY]
jurisdictions: [US, GB, DE, FR]
---

# Risk note — concentration and score drift

Elevated anomaly scores clustered in a small set of institutions can indicate
concentration risk rather than isolated typos. Monitor the share of flagged
value by institution and asset class.

Population Stability Index (PSI) on predicted categories or anomaly-score
bins above 0.2 warrants model re-check; above 0.25 is a major shift. Combine
PSI alerts with faithfulness checks on LLM explanations before changing
thresholds.

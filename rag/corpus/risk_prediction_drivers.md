---
id: RISK-PRED-011
track: risk
topics: [risk-prediction, drivers, embeddings, red-flags]
asset_classes: [LOAN, DEPOSIT, FX, SECURITY, DERIVATIVE]
jurisdictions: [US, GB, DE, JP, CH, SG, FR, IN]
---

# Risk-prediction assist — driver narrative (not a black-box forecast)

Risk scores in this simulation come from embedding distance to category
centroids plus optional amount extremity. An LLM risk narrative should explain
*drivers*: purpose–asset mismatch, red-flag vocabulary, and magnitude — and
must cite retrieved policy or typology chunks.

Do not invent forward-looking market forecasts. Prefer: “score elevated because
purpose contains structuring language and amount exceeds peer range.”

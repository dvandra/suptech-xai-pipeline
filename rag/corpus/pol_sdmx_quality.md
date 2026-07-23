---
id: POL-SDMX-003
track: supervisory
topics: [sdmx, validation, data-quality, fmr]
asset_classes: [LOAN, DEPOSIT, SECURITY, DERIVATIVE, FX]
jurisdictions: [US, GB, DE, JP, CH, SG, FR, IN]
---

# SDMX data-quality expectations for high-frequency banking returns

Observations must include mandatory dimensions (reporting area, institution,
asset class, time period), a numeric measure, and coded attributes from the
published codelists. Duplicate series keys are rejected.

Semantic AI analysis runs only after structural validation succeeds. Invalid
codes, missing dimensions, or non-numeric measures never enter the anomaly
model — they are governance failures, not model failures.

# SupTech-XAI Anomaly Report

Dataflow: `DEMO:BANKING_FLOWS_FLOW(1.0)`  
Prompt version: `v2`  
Explain model: `llama3` (fallback: rule-based)  
Flagged observations: **29**

Each explanation uses a four-step Chain-of-Thought contract (purpose vs asset class → amount → red flags → rating/action).

## GB.BANK033.LOAN.2024-08 - GB / LOAN
**Amount:** 436,835,930.11 GBP  
**Stated purpose:** Urgent offshore transfer to unregistered shell entity no questions  
**Anomaly score:** 1.0801 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `LOAN`; its wording sits far from typical LOAN activity (anomaly score 1.0801, above the alert threshold).
STEP2: The amount is 436,835,930 GBP, which is unusually large for this activity type.
STEP3: Red-flag language detected (shell, unregistered, offshore): transfer to an opaque shell entity; dealing with an unregistered entity; unexplained offshore routing.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## CH.BANK038.FX.2025-01 - CH / FX
**Amount:** 254,653,712.48 INR  
**Stated purpose:** Urgent offshore transfer to unregistered shell entity no questions  
**Anomaly score:** 1.0801 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `LOAN`; its wording sits far from typical FX activity (anomaly score 1.0801, above the alert threshold).
STEP2: The amount is 254,653,712 INR, which is unusually large for this activity type.
STEP3: Red-flag language detected (shell, unregistered, offshore): transfer to an opaque shell entity; dealing with an unregistered entity; unexplained offshore routing.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## CH.BANK012.FX.2025-06 - CH / FX
**Amount:** 75,160,401.87 JPY  
**Stated purpose:** Structuring cash below reporting threshold across multiple accounts  
**Anomaly score:** 1.0803 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `DEPOSIT`; its wording sits far from typical FX activity (anomaly score 1.0803, above the alert threshold).
STEP2: The amount is 75,160,402 JPY, which is unusually large for this activity type.
STEP3: Red-flag language detected (structuring, threshold): structuring to evade reporting thresholds; activity engineered around reporting thresholds.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## DE.BANK039.LOAN.2024-01 - DE / LOAN
**Amount:** 460,181,947.12 EUR  
**Stated purpose:** Layering funds through rapid round-trip cross-border wires  
**Anomaly score:** 1.0801 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `FX`; its wording sits far from typical LOAN activity (anomaly score 1.0801, above the alert threshold).
STEP2: The amount is 460,181,947 EUR, which is unusually large for this activity type.
STEP3: Red-flag language detected (layering, round-trip): layering consistent with money-laundering typologies; round-tripping of funds across jurisdictions.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## US.BANK036.DEPOSIT.2024-07 - US / DEPOSIT
**Amount:** 277,409,879.65 SGD  
**Stated purpose:** Structuring cash below reporting threshold across multiple accounts  
**Anomaly score:** 1.0803 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `DEPOSIT`; its wording sits far from typical DEPOSIT activity (anomaly score 1.0803, above the alert threshold).
STEP2: The amount is 277,409,880 SGD, which is unusually large for this activity type.
STEP3: Red-flag language detected (structuring, threshold): structuring to evade reporting thresholds; activity engineered around reporting thresholds.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## US.BANK004.FX.2025-05 - US / FX
**Amount:** 386,589,002.17 CHF  
**Stated purpose:** Urgent offshore transfer to unregistered shell entity no questions  
**Anomaly score:** 1.0801 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `LOAN`; its wording sits far from typical FX activity (anomaly score 1.0801, above the alert threshold).
STEP2: The amount is 386,589,002 CHF, which is unusually large for this activity type.
STEP3: Red-flag language detected (shell, unregistered, offshore): transfer to an opaque shell entity; dealing with an unregistered entity; unexplained offshore routing.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## GB.BANK031.DERIVATIVE.2025-04 - GB / DERIVATIVE
**Amount:** 101,142,188.05 INR  
**Stated purpose:** Trade mis-invoicing to move value across jurisdictions  
**Anomaly score:** 1.0936 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `SECURITY`; its wording sits far from typical DERIVATIVE activity (anomaly score 1.0936, above the alert threshold).
STEP2: The amount is 101,142,188 INR, which is unusually large for this activity type.
STEP3: Red-flag language detected (mis-invoic): trade mis-invoicing to move value.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## FR.BANK028.LOAN.2025-02 - FR / LOAN
**Amount:** 277,974,771.92 USD  
**Stated purpose:** Layering funds through rapid round-trip cross-border wires  
**Anomaly score:** 1.0801 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `FX`; its wording sits far from typical LOAN activity (anomaly score 1.0801, above the alert threshold).
STEP2: The amount is 277,974,772 USD, which is unusually large for this activity type.
STEP3: Red-flag language detected (layering, round-trip): layering consistent with money-laundering typologies; round-tripping of funds across jurisdictions.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## CH.BANK011.DERIVATIVE.2025-01 - CH / DERIVATIVE
**Amount:** 285,352,413.23 EUR  
**Stated purpose:** Payment to sanctioned counterparty routed via intermediary  
**Anomaly score:** 1.0626 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `DERIVATIVE`; its wording sits far from typical DERIVATIVE activity (anomaly score 1.0626, above the alert threshold).
STEP2: The amount is 285,352,413 EUR, which is unusually large for this activity type.
STEP3: Red-flag language detected (sanction): counterparty linked to sanctions.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## US.BANK022.FX.2024-01 - US / FX
**Amount:** 336,173,827.78 INR  
**Stated purpose:** Payment to sanctioned counterparty routed via intermediary  
**Anomaly score:** 1.0626 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `DERIVATIVE`; its wording sits far from typical FX activity (anomaly score 1.0626, above the alert threshold).
STEP2: The amount is 336,173,828 INR, which is unusually large for this activity type.
STEP3: Red-flag language detected (sanction): counterparty linked to sanctions.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## FR.BANK006.DERIVATIVE.2024-10 - FR / DERIVATIVE
**Amount:** 106,171,773.28 INR  
**Stated purpose:** Trade mis-invoicing to move value across jurisdictions  
**Anomaly score:** 1.0936 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `SECURITY`; its wording sits far from typical DERIVATIVE activity (anomaly score 1.0936, above the alert threshold).
STEP2: The amount is 106,171,773 INR, which is unusually large for this activity type.
STEP3: Red-flag language detected (mis-invoic): trade mis-invoicing to move value.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## CH.BANK033.DEPOSIT.2025-02 - CH / DEPOSIT
**Amount:** 192,018,119.02 INR  
**Stated purpose:** Urgent offshore transfer to unregistered shell entity no questions  
**Anomaly score:** 1.0801 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `LOAN`; its wording sits far from typical DEPOSIT activity (anomaly score 1.0801, above the alert threshold).
STEP2: The amount is 192,018,119 INR, which is unusually large for this activity type.
STEP3: Red-flag language detected (shell, unregistered, offshore): transfer to an opaque shell entity; dealing with an unregistered entity; unexplained offshore routing.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## CH.BANK005.DERIVATIVE.2025-02 - CH / DERIVATIVE
**Amount:** 247,304,729.44 SGD  
**Stated purpose:** Structuring cash below reporting threshold across multiple accounts  
**Anomaly score:** 1.0803 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `DEPOSIT`; its wording sits far from typical DERIVATIVE activity (anomaly score 1.0803, above the alert threshold).
STEP2: The amount is 247,304,729 SGD, which is unusually large for this activity type.
STEP3: Red-flag language detected (structuring, threshold): structuring to evade reporting thresholds; activity engineered around reporting thresholds.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## FR.BANK003.SECURITY.2025-02 - FR / SECURITY
**Amount:** 114,733,701.78 GBP  
**Stated purpose:** Layering funds through rapid round-trip cross-border wires  
**Anomaly score:** 1.0801 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `FX`; its wording sits far from typical SECURITY activity (anomaly score 1.0801, above the alert threshold).
STEP2: The amount is 114,733,702 GBP, which is unusually large for this activity type.
STEP3: Red-flag language detected (layering, round-trip): layering consistent with money-laundering typologies; round-tripping of funds across jurisdictions.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## US.BANK022.DERIVATIVE.2024-11 - US / DERIVATIVE
**Amount:** 453,664,112.97 GBP  
**Stated purpose:** Payment to sanctioned counterparty routed via intermediary  
**Anomaly score:** 1.0626 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `DERIVATIVE`; its wording sits far from typical DERIVATIVE activity (anomaly score 1.0626, above the alert threshold).
STEP2: The amount is 453,664,113 GBP, which is unusually large for this activity type.
STEP3: Red-flag language detected (sanction): counterparty linked to sanctions.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## SG.BANK008.LOAN.2024-10 - SG / LOAN
**Amount:** 387,895,009.82 JPY  
**Stated purpose:** Trade mis-invoicing to move value across jurisdictions  
**Anomaly score:** 1.0936 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `SECURITY`; its wording sits far from typical LOAN activity (anomaly score 1.0936, above the alert threshold).
STEP2: The amount is 387,895,010 JPY, which is unusually large for this activity type.
STEP3: Red-flag language detected (mis-invoic): trade mis-invoicing to move value.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## GB.BANK032.DERIVATIVE.2025-03 - GB / DERIVATIVE
**Amount:** 241,823,128.68 USD  
**Stated purpose:** Layering funds through rapid round-trip cross-border wires  
**Anomaly score:** 1.0801 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `FX`; its wording sits far from typical DERIVATIVE activity (anomaly score 1.0801, above the alert threshold).
STEP2: The amount is 241,823,129 USD, which is unusually large for this activity type.
STEP3: Red-flag language detected (layering, round-trip): layering consistent with money-laundering typologies; round-tripping of funds across jurisdictions.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## CH.BANK014.LOAN.2025-03 - CH / LOAN
**Amount:** 70,457,811.48 CHF  
**Stated purpose:** Urgent offshore transfer to unregistered shell entity no questions  
**Anomaly score:** 1.0801 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `LOAN`; its wording sits far from typical LOAN activity (anomaly score 1.0801, above the alert threshold).
STEP2: The amount is 70,457,811 CHF, which is unusually large for this activity type.
STEP3: Red-flag language detected (shell, unregistered, offshore): transfer to an opaque shell entity; dealing with an unregistered entity; unexplained offshore routing.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## US.BANK004.LOAN.2024-04 - US / LOAN
**Amount:** 344,105,428.28 JPY  
**Stated purpose:** Urgent offshore transfer to unregistered shell entity no questions  
**Anomaly score:** 1.0801 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `LOAN`; its wording sits far from typical LOAN activity (anomaly score 1.0801, above the alert threshold).
STEP2: The amount is 344,105,428 JPY, which is unusually large for this activity type.
STEP3: Red-flag language detected (shell, unregistered, offshore): transfer to an opaque shell entity; dealing with an unregistered entity; unexplained offshore routing.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## US.BANK006.DERIVATIVE.2024-11 - US / DERIVATIVE
**Amount:** 66,124,369.58 CHF  
**Stated purpose:** Layering funds through rapid round-trip cross-border wires  
**Anomaly score:** 1.0801 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `FX`; its wording sits far from typical DERIVATIVE activity (anomaly score 1.0801, above the alert threshold).
STEP2: The amount is 66,124,370 CHF, which is unusually large for this activity type.
STEP3: Red-flag language detected (layering, round-trip): layering consistent with money-laundering typologies; round-tripping of funds across jurisdictions.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## US.BANK040.LOAN.2024-06 - US / LOAN
**Amount:** 139,712,307.06 EUR  
**Stated purpose:** Structuring cash below reporting threshold across multiple accounts  
**Anomaly score:** 1.0803 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `DEPOSIT`; its wording sits far from typical LOAN activity (anomaly score 1.0803, above the alert threshold).
STEP2: The amount is 139,712,307 EUR, which is unusually large for this activity type.
STEP3: Red-flag language detected (structuring, threshold): structuring to evade reporting thresholds; activity engineered around reporting thresholds.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## DE.BANK021.DERIVATIVE.2024-11 - DE / DERIVATIVE
**Amount:** 238,160,634.50 EUR  
**Stated purpose:** Trade mis-invoicing to move value across jurisdictions  
**Anomaly score:** 1.0936 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `SECURITY`; its wording sits far from typical DERIVATIVE activity (anomaly score 1.0936, above the alert threshold).
STEP2: The amount is 238,160,634 EUR, which is unusually large for this activity type.
STEP3: Red-flag language detected (mis-invoic): trade mis-invoicing to move value.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## IN.BANK010.DEPOSIT.2025-06 - IN / DEPOSIT
**Amount:** 411,784,634.84 EUR  
**Stated purpose:** Payment to sanctioned counterparty routed via intermediary  
**Anomaly score:** 1.0626 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `DERIVATIVE`; its wording sits far from typical DEPOSIT activity (anomaly score 1.0626, above the alert threshold).
STEP2: The amount is 411,784,635 EUR, which is unusually large for this activity type.
STEP3: Red-flag language detected (sanction): counterparty linked to sanctions.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## IN.BANK031.FX.2024-07 - IN / FX
**Amount:** 233,108,353.20 INR  
**Stated purpose:** Structuring cash below reporting threshold across multiple accounts  
**Anomaly score:** 1.0803 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `DEPOSIT`; its wording sits far from typical FX activity (anomaly score 1.0803, above the alert threshold).
STEP2: The amount is 233,108,353 INR, which is unusually large for this activity type.
STEP3: Red-flag language detected (structuring, threshold): structuring to evade reporting thresholds; activity engineered around reporting thresholds.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## JP.BANK009.DERIVATIVE.2024-12 - JP / DERIVATIVE
**Amount:** 199,280,297.11 SGD  
**Stated purpose:** Urgent offshore transfer to unregistered shell entity no questions  
**Anomaly score:** 1.0801 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `LOAN`; its wording sits far from typical DERIVATIVE activity (anomaly score 1.0801, above the alert threshold).
STEP2: The amount is 199,280,297 SGD, which is unusually large for this activity type.
STEP3: Red-flag language detected (shell, unregistered, offshore): transfer to an opaque shell entity; dealing with an unregistered entity; unexplained offshore routing.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## DE.BANK019.LOAN.2024-09 - DE / LOAN
**Amount:** 170,140,221.25 EUR  
**Stated purpose:** Structuring cash below reporting threshold across multiple accounts  
**Anomaly score:** 1.0803 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `DEPOSIT`; its wording sits far from typical LOAN activity (anomaly score 1.0803, above the alert threshold).
STEP2: The amount is 170,140,221 EUR, which is unusually large for this activity type.
STEP3: Red-flag language detected (structuring, threshold): structuring to evade reporting thresholds; activity engineered around reporting thresholds.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## GB.BANK029.SECURITY.2024-04 - GB / SECURITY
**Amount:** 437,989,831.47 INR  
**Stated purpose:** Payment to sanctioned counterparty routed via intermediary  
**Anomaly score:** 1.0626 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `DERIVATIVE`; its wording sits far from typical SECURITY activity (anomaly score 1.0626, above the alert threshold).
STEP2: The amount is 437,989,831 INR, which is unusually large for this activity type.
STEP3: Red-flag language detected (sanction): counterparty linked to sanctions.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## GB.BANK020.SECURITY.2025-06 - GB / SECURITY
**Amount:** 392,882,989.57 CHF  
**Stated purpose:** Trade mis-invoicing to move value across jurisdictions  
**Anomaly score:** 1.0936 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `SECURITY`; its wording sits far from typical SECURITY activity (anomaly score 1.0936, above the alert threshold).
STEP2: The amount is 392,882,990 CHF, which is unusually large for this activity type.
STEP3: Red-flag language detected (mis-invoic): trade mis-invoicing to move value.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

## FR.BANK007.DERIVATIVE.2024-09 - FR / DERIVATIVE
**Amount:** 148,343,870.75 GBP  
**Stated purpose:** Trade mis-invoicing to move value across jurisdictions  
**Anomaly score:** 1.0936 | **Risk rating:** HIGH  
**Step validation:** PASS

STEP1: The stated purpose is categorised as `SECURITY`; its wording sits far from typical DERIVATIVE activity (anomaly score 1.0936, above the alert threshold).
STEP2: The amount is 148,343,871 GBP, which is unusually large for this activity type.
STEP3: Red-flag language detected (mis-invoic): trade mis-invoicing to move value.
STEP4: Risk rating: HIGH. Recommended action: Escalate to the AML/financial-crime unit and file for review.

---

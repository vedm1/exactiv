# PRD-A — Exaktiv Claims (health-claim file extraction, India first)

Version 1.0 · 4 November 2026 · Status: draft for the build-phase kit · Written in ASD-STE100
Depends on: PRD-00 Exaktiv Core Engine. This PRD does not repeat the core requirements.

## 1. Summary

Exaktiv Claims reads a health-insurance reimbursement claim file. A file can hold scanned PDFs, phone photos and handwritten pages, in English and Indian languages. Exaktiv Claims classifies each page, extracts the fields that a claims processor needs, checks the documents against each other, raises flags, and gives the processor a case summary in which each value links to its source page. A human makes every claim decision. Exaktiv Claims sells per claim file to mid-size Indian health insurers and TPAs.

Exaktiv Underwrite (life underwriting medical reports and death claims) uses the same extractors. It comes after Claims v1 (section 12).

## 2. Problem

- India settled about 32.6 million health claims in FY25 (+21% on FY24). About 69% went through TPAs.
- Reimbursement files are paper-heavy: claim form, discharge summary, itemised bills, lab reports, prescriptions, ID. Many pages are handwritten or photographed. About half of the reimbursement claims at the largest TPA arrive electronically, but "electronic" means a scan or a PDF, not structured data.
- The best model reads handwritten fields at about 75% accuracy. Indian medical records mix English with Hindi, Kannada and other languages.
- Claims processors re-key values, check bills against discharge summaries by hand, and look for missing documents. This is slow and costly.
- Regulators want control and audit: IRDAI requires policy and claim records in India, its April 2026 cyber rules keep logs in India, and its AI working group (June 2026) targets claims and fraud. The RBI draft model-risk rules (2026) say that "outsourcing a model does not outsource the risk", and this view is spreading across financial regulators.

## 3. Goals and non-goals

### Goals (v1)

1. Process one reimbursement claim file from upload to a draft case summary in under 2 minutes, before human review.
2. Beat a frontier baseline (Gemini Flash, India region) by 5 or more points of field accuracy on handwritten fields.
3. Link every value in the case summary to its source page and location.
4. Raise cross-document flags that a processor can act on.
5. Give an evidence pack per claim file (Exaktiv Proof) mapped to IRDAI, DPDP and FREE-AI expectations.
6. Keep all data and model calls in India.

### Non-goals (v1)

- No automatic claim approval or rejection. A human decides every claim.
- No cashless pre-authorisation in real time (v2).
- No fraud score. Flags only state facts (for example, "bill date is after discharge date").
- No integration with NHCX in v1 (read NHCX documents as files only).
- No life underwriting (Exaktiv Underwrite, after v1).
- No EU or US tenants for this product in v1.
- No ICD-10 coding as an authoritative output. The product suggests a code, and a human confirms it.

## 4. Users and buyers

| Role | Need |
|---|---|
| Claims processor (TPA or insurer) | Fewer values to type. See conflicts across documents fast. |
| Medical adjudicator (doctor on the claims team) | See diagnosis, procedures, history and lab values in one view, with sources. |
| Claims manager | Throughput, backlog, turnaround time, accuracy. |
| CIO / CISO / compliance | Data stays in India. Audit trail. Access control. DPDP compliance. |
| Buyer | Head of claims operations at a mid-size health insurer or TPA. Not the top 3 TPAs (Medi Assist sells its own platform). |

## 5. Scope: case type and documents

**Case type in v1:** health-insurance reimbursement claim (in-patient hospitalisation).

**Document types to classify (v1):**

| Code | Document type |
|---|---|
| CF-A | Claim form Part A (insured), IRDAI standard format |
| CF-B | Claim form Part B (hospital), IRDAI standard format |
| DS | Discharge summary |
| BILL-F | Final hospital bill (summary) |
| BILL-I | Itemised bill / bill break-up |
| PHARM | Pharmacy bills |
| LAB | Laboratory and investigation reports |
| RX | Prescriptions and doctor notes |
| ID | ID document (masked on ingest) |
| POL | Policy copy or e-card |
| BANK | Cancelled cheque / bank details (masked on ingest) |
| OTHER | Any other page |

**Languages (v1):** English, Hindi, Kannada. Add Tamil, Telugu and Marathi in v1.1.

**Input quality:** scans at 150–300 dpi, phone photos with angle, shadow and folds, handwritten forms and notes.

## 6. Functional requirements

### 6.1 Fields to extract (v1)

| Group | Fields |
|---|---|
| Patient and policy | Patient name, age, gender, policy number, member ID, insurer, TPA, relation to proposer |
| Hospital | Hospital name, city, hospital registration / ROHINI ID if present, treating doctor, doctor registration number |
| Stay | Admission date and time, discharge date and time, length of stay, room category, ICU days |
| Clinical | Provisional and final diagnosis (text), suggested ICD-10 code (needs human confirmation), procedures (text), history of present illness, past history and duration of known conditions, key findings, key lab values with units and dates |
| Bills | Bill number, bill date, line items (description, category, quantity, unit price, amount), room rent per day, total billed, discounts, amount paid by patient, pharmacy totals, implant details and invoices |
| Claim | Total amount claimed, claim type, date of first consultation, pre- and post-hospitalisation expenses claimed |
| Bank | Account holder name, IFSC (account number masked; only last 4 digits shown) |

Each value follows the core value record (PRD-00 FR-EXT-3).

### 6.2 Cross-document checks (v1)

Rules live in code or versioned configuration (G3). Each check gives pass, fail or "cannot check", with the source values.

| ID | Check |
|---|---|
| X1 | Admission and discharge dates agree across claim form, discharge summary and final bill |
| X2 | Length of stay matches the number of room-rent days on the bill |
| X3 | Line items sum to the bill total (within ₹1) |
| X4 | Bill dates fall inside the stay, or inside the allowed pre- and post-hospitalisation window (window from policy configuration) |
| X5 | Patient name and age agree across documents (fuzzy match with a score) |
| X6 | Diagnosis on the discharge summary is consistent with the procedures billed (rule table plus model check; model result is advisory) |
| X7 | Items that match the IRDAI standard list of non-medical (non-payable) items are marked (list version recorded; confirm the current IRDAI list before build) |
| X8 | Room rent per day compared with the policy's room-rent limit (limit from policy configuration, not from the model) |
| X9 | Missing-document check against a checklist per claim type |
| X10 | Duplicate bill check: same bill number or same total and date in another file of the same tenant |

### 6.3 Flags

- A flag states a fact and its sources. Example: "X2 failed: length of stay 4 days; room-rent days billed 6 (BILL-I page 3)".
- Flags never state "fraud". The product does not give a fraud score in v1.

### 6.4 Case summary

- One screen and one PDF per claim file.
- Sections: patient and policy, stay, diagnosis and procedures, bills summary, checks and flags, missing documents, values still open for review.
- Each value has a link to its source crop.
- A "draft" watermark stays until a human marks the case "reviewed".

### 6.5 Reviewer screens (on top of the core queue)

- Case view: all pages as thumbnails, classified, with the case summary next to them.
- Field view: the core review queue, filtered to this case.
- Keyboard-first. A processor can finish a case without the mouse.

### 6.6 Evidence pack (Exaktiv Proof for Claims)

- Core evidence pack (PRD-00 FR-PRF) plus a mapping page:
  - IRDAI: data stored in India; access log; retention period per tenant policy.
  - DPDP Act: purpose of processing, data minimised, masked identifiers, retention and deletion record.
  - RBI FREE-AI and the RBI draft model-risk rules (as reference for financial regulators): model inventory entry, model version, validation results, human-in-the-loop record, documentation access for the customer.
- The mapping is a template. The customer's compliance team confirms it.

### 6.7 Benchmark page (sales tool)

- Run the pipeline and Gemini Flash (India region) on the same test set.
- Show field accuracy overall, for printed fields, and for handwritten fields separately.
- Show cost per claim file and time per claim file.

## 7. Product guardrails (in addition to core G1–G13)

| ID | Guardrail | How to check |
|---|---|---|
| A-G1 | **No claim decision by the system.** The product never approves, rejects or sets a payable amount. | No API or UI path writes a decision. |
| A-G2 | **India only.** All claim data, page images, model calls and logs stay in the India region. | Region test (core G7) with India tenants. |
| A-G3 | **Policy rules come from configuration.** Room-rent limits, waiting periods, co-pay and windows come from the tenant's policy configuration, never from a model. | Code review; tests for X4 and X8 use configuration only. |
| A-G4 | **Identifiers masked on ingest.** Aadhaar numbers, PAN, bank account numbers and phone numbers are masked in page images and text for all users except a role that needs them. Aadhaar is never stored unmasked. | Ingest test with synthetic identifiers. |
| A-G5 | **No real medical records before a signed pilot.** The PoC uses synthetic and public documents only. No data from any past employer. | Fixture source notes; data bucket policy. |
| A-G6 | **ICD codes are suggestions.** A suggested code is labelled "suggested" until a human confirms it. | UI and API show the status. |

## 8. Data for the PoC and the tests

| Source | Use | Note |
|---|---|---|
| IRDAI standard claim form Parts A and B (public) | Templates for synthetic cases | Fill with fake data |
| Synthetic discharge summaries, bills, lab reports, prescriptions | Test set | Built from common Indian hospital formats; fake data only |
| Hand-filled forms by 15–20 paid volunteers, in English, Hindi and Kannada | Handwriting test set | Photograph in poor light, at angles, with folds |
| Public datasets (for example FUNSD for forms, IAM for handwriting, IIIT Hyderabad Indic handwriting sets) | Training help | Check each licence; some are research-only (G12) |

Target test set for the PoC: 300–500 documents in 40–60 synthetic claim files, with a labelled answer key.

## 9. Metrics and pass rules

### Demo pass rule (before showing the PoC to insurers)

- 5 or more points better than Gemini Flash on handwritten fields.
- One full claim file processed in under 2 minutes before review.
- 100% of values in the case summary link to a source.

### 30-day market test (after the PoC)

- 15 calls with claims, underwriting or CIO leads at mid-size health and life insurers and TPAs.
- Get 200 anonymised real documents under NDA.
- **Pass (all):** 3 or more firms share documents; 1 or more signs a paid-pilot letter of ₹5 lakh or more; the pipeline is 5 or more points better on handwritten fields (or 5 times cheaper at equal accuracy); half of the buyers say in-India or self-hosted processing is mandatory.
- **Fail:** buyers say "we use Gemini or Azure" or "Perfios / Superclaims / MAtrix does this", or the gain is under 3 points.

### Pilot metrics

| Metric | Target |
|---|---|
| Processor time per claim file | 40% or less of the current time |
| Field accuracy after review | 99% or more |
| Share of values auto-accepted (after calibration) | 60% or more on printed fields |
| Turnaround time | Measured before and after; target set with the customer |

## 10. Pricing (Proposed)

- Per claim file processed and reviewed: ₹25–30 (base ₹30). Volume tiers above 20,000 files per month.
- Pilot: fixed fee ₹5 lakh or more for 8–12 weeks, credited against the first contract.
- Revenue maths: about 28,000 claim files per month gives about US$9.5k per month (₹8 lakh). A realistic customer sends 10,000–12,000 files per month, so ₹8 lakh needs about 3 customers.

## 11. Market and competition (desk research, 2–3 November 2026)

- India reachable market (SAM): about US$4–7.5M per year (base US$5.5M).
- Competitors: Medi Assist (MAtrix platform, MAven IDP; live at Star Health and SBI General), Superclaims (bought by ekincare, July 2026; more than 100,000 claims per month), Vitraya, ClaimSetu, Perfios (claims digitisation), Coforge Nexa, LTIMindtree. Large insurers use Gemini and Azure OpenAI in Indian regions.
- Position: higher accuracy on handwritten and regional-language pages, a source link for every value, and an evidence pack. Do not compete on "sovereign AI" or "own your model".

## 12. Exaktiv Underwrite (after Claims v1)

- Same engine and extractors. New document types: medical examination reports, lab panels, attending doctor statements, past treatment records, death certificates and claimant statements.
- Outputs: medical summary for the underwriter, with sources; a disclosure-check list (conditions in records against the proposal form).
- Buyer: mid-size private life insurers.
- Price: about ₹200 per case.

## 13. Proposed phases

| Phase | Objective | Gate |
|---|---|---|
| EXC1 | Claims schema, document types and field definitions as versioned configuration | Gates all Claims extraction |
| EXC2 | Synthetic and handwritten test set with answer key (300–500 documents) | Gates EXC7 |
| EXC3 | Page classification for the 12 document types | Accuracy 95% or more on the test set |
| EXC4 | Field extraction per document type, with identifier masking (A-G4) | Gates EXC5 |
| EXC5 | Cross-document checks X1–X10 and flags, with policy configuration (A-G3) | Gates the case summary |
| EXC6 | Case summary screen and PDF, case view in the reviewer UI (EXC6-ui) | Gates demos |
| EXC7 | Benchmark against Gemini Flash; handwriting fine-tune (LoRA) | Demo pass rule (section 9) |
| EXC8 | Claims evidence pack with the regulation mapping | Gates the first pilot on real data |
| EXC9 | Pilot hardening: tenant set-up, India-region deployment, access roles, retention and deletion | ISO 27001 work started |

## 14. Risks

| Risk | Effect | Mitigation |
|---|---|---|
| Handwriting gain is under 5 points | Weak sales story | Pitch reviewer speed to TPAs; collect real handwritten data in the pilot; fine-tune per tenant |
| Medi Assist, Superclaims or Perfios win on price | Low price per file | Target mid-size insurers and TPAs not on MAtrix; win on accuracy and evidence |
| Long sales cycle (90–240 days) and security reviews | Late revenue | Start calls in month 0; start ISO 27001 in month 4; offer an offline pilot on anonymised data |
| NHCX makes claims more structured | Less paper over time | Attachments stay scanned for 2–4 more years [E]; move up to checks and summaries, not only extraction |
| Health data incident | Severe trust and legal damage | A-G2, A-G4, G11; no real data before a signed pilot; DPDP controls |
| SOC 2 / ISO cost (₹15–40 lakh) | Cash pressure | Start ISO 27001 first; use Product Data revenue to pay for it |

## 15. Open questions

1. Which mid-size insurers and TPAs in the founders' network can join the 30-day test?
2. Which policy-rule fields does a first customer need in configuration (room rent, co-pay, sub-limits)?
3. Self-hosted open model in India, or a managed endpoint in the Mumbai region?
4. Which Indian languages after Hindi and Kannada, based on the first customer's mix?

## Sources

- India health claims FY25: https://indiamedtoday.com/record-health-insurance-claims-settled-in-fy25-average-payout-per-claim-declines/
- Medi Assist investor presentation (Aug 2026): https://nsearchives.nseindia.com/corporate/MEDIASSIST_09082026195837_MAHSInvestorPresentationAug26.pdf
- ekincare buys Superclaims: https://www.digitalhealthnews.com/ekincare-acquires-superclaims-to-expand-ai-powered-insurance-claims-operations
- IDP leaderboard (handwriting accuracy): https://trailhq.com/blog/idp-leaderboard-1-5
- IRDAI data localisation: https://www.mondaq.com/article/1858412/data-localisation-in-the-indian-insurance-sector
- IRDAI AI working group: https://insurancebusinessmag.com/asia/news/technology/indias-insurance-regulator-steps-in-to-govern-ai-adoption-579846.aspx
- RBI draft model-risk rules 2026: https://vinodkothari.com/2026/06/rbi-draft-model-risk-management-guidelines-2026/
- ICICI Lombard and Gemini: https://cloud.google.com/customers/icicilombard
- LLM data residency in India: https://www.techplained.com/llm-api-data-residency-india
- NHCX status: https://nirmitee.io/blog/is-nhcx-mandatory-hospitals-hmis-2026/
- Perfios insurance: https://perfios.ai/insurance
- SOC 2 cost in India: https://www.cybersigmacs.com/blog/soc-2-audit-cost-timeline-india/

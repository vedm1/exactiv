# PRD-B1 — Exaktiv Product Data (ETIM feature fill that passes data-pool checks, EU first)

Version 1.0 · 4 November 2026 · Status: draft for the build-phase kit · Written in ASD-STE100
Depends on: PRD-00 Exaktiv Core Engine. This PRD does not repeat the core requirements.

## 1. Summary

Exaktiv Product Data fills ETIM product data for technical products (electrical first, then HVAC and plumbing). It reads the supplier's datasheets, manuals and existing product lists. It assigns the ETIM class, fills each ETIM feature with a value from the allowed list or a number with an allowed unit, and links each value to its datasheet page. A human reviewer approves low-confidence values. The output is a file that the supplier uploads to a data pool (2BA in the Netherlands and Belgium, Open Datacheck in Germany). The promise: **each delivered SKU passes the data-pool check at the agreed quality level**. Exaktiv Product Data sells per accepted SKU, plus a yearly upkeep fee for new ETIM versions.

## 2. Problem

- Wholesalers in electrical and HVAC/plumbing import product data from data pools. More than 80% of German electrical wholesalers get master data through Open Datacheck. In the Netherlands and Belgium, 2BA is the central pool.
- **Manufacturers, importers and agents supply the data and pay for it.** 2BA grades supplier data with a data label and asks suppliers to reach its 2025 label level "as soon as possible".
- 75% of manufacturers have difficulty filling data-steward roles. Before AI, publishing to a data pool could cost about US$50k in consulting.
- Each new release (ETIM 10, ECLASS 16) adds or changes classes and features, so suppliers must remap data again and again.
- Long-tail suppliers (small and mid-size manufacturers, importers, agents, and exporters from India, Turkey, Poland and Asia) have the biggest gap: few staff, datasheets in several languages, and low data labels.

## 3. Goals and non-goals

### Goals (v1)

1. Assign the correct ETIM class for each SKU of a supplier batch (electrical, ETIM 10).
2. Fill ETIM features with 95% or more accuracy against the datasheets, after review.
3. Make every delivered SKU pass the pool validation at the agreed level (2BA label or Open Datacheck check).
4. Link every feature value to its datasheet page and location.
5. Export upload-ready files (ETIM xChange and BMEcat with ETIM features; 2BA and Open Datacheck formats as required).
6. Re-map a supplier's catalogue when a new ETIM version comes out (upkeep service).

### Non-goals (v1)

- No B2C marketplace enrichment (product titles, marketing text, SEO). The challenge found no market for it in this channel.
- No wholesaler-side product (wholesalers are a referral source only).
- No ECLASS in v1. Add ECLASS in v1.1, because the same engine fits.
- No GPSR or Digital Product Passport fields in v1. Add them when the delegated acts for these product groups have dates.
- No direct upload to a data pool without the supplier's approval (core G13).
- No translation of marketing text. ETIM feature values are coded, so they do not need translation.

## 4. Users and buyers

| Role | Need |
|---|---|
| Product data manager at a manufacturer, importer or agent | Upload datasheets, get a clean ETIM file, pass the pool check, with little work |
| Export manager at a non-EU manufacturer selling into NL, BE or DE | Meet the data requirements of EU wholesalers in English |
| Exaktiv reviewer (team or contractor) | Review low-confidence features fast, next to the datasheet page |
| Buyer | Owner, sales director or product-data lead of a supplier with 2,000–20,000 SKUs and a low data label |
| Referral source | Wholesaler category managers who want better data from their weak suppliers |

## 5. Inputs and outputs

### Inputs

- Datasheets and manuals (PDF, scanned or digital) in English, German, Dutch or French.
- Existing product lists (CSV, XLSX, BMEcat) with article numbers, GTIN/EAN, descriptions.
- Optional: the supplier's current pool export and its current label or check report.

### Outputs

- Per SKU: ETIM class, all features of the class with values (coded values, numbers with units, ranges, yes/no), and "not applicable" or "not found" where true.
- Export formats: ETIM xChange (JSON) and BMEcat 2005 with ETIM features. Confirm the exact upload format each pool accepts before EXP5.
- A quality report per batch: share of features filled, pool check result per SKU, open items.
- An evidence pack per batch (Exaktiv Proof): each value with its datasheet crop and the approver.

## 6. Functional requirements

### 6.1 ETIM model

- B-ETIM-1: Load the official ETIM model (classes, features, value lists, units) for the supported version. Store the version. Confirm the licence and download terms with ETIM International before build (G12).
- B-ETIM-2: Value lists and units come only from the ETIM model (core G3). The model never makes a new value code.
- B-ETIM-3: Support ETIM 10 for electrical (EC) classes in v1. Add HVAC/plumbing classes in v1.1.

### 6.2 Classification

- B-CLS-1: Propose an ETIM class per SKU from the description, datasheet and existing data. Give the top 3 classes with confidence.
- B-CLS-2: A class below the threshold goes to review. A class change after review re-runs feature extraction for that SKU.

### 6.3 Feature extraction

- B-FEA-1: For each feature of the class, extract the value from the datasheet tables, text and drawings.
- B-FEA-2: Convert units to the ETIM unit for the feature (for example mm to the required unit). Store the original value and unit too.
- B-FEA-3: Map text values to the allowed value code. If no code fits, mark the feature for review. Never make a new code.
- B-FEA-4: Mark "not applicable" only when the datasheet shows it. Otherwise mark "not found" and send it to review.
- B-FEA-5: For product families (one datasheet, many variants), split values per variant by article number.

### 6.4 Pool validation

- B-VAL-1: Run the same checks as the target pool before delivery (required features per class, value formats, units, label rules). Record the check version.
- B-VAL-2: If the pool gives a validation service or a test upload, use it in the delivery step (to confirm with 2BA and ITEK).
- B-VAL-3: A SKU counts as "accepted" (billable, core G5) only when it passes the pool check at the agreed level and all its required features are accepted.

### 6.5 Reviewer screens (on top of the core queue)

- SKU view: features of the class in a table, each value next to the datasheet crop.
- Family view: all variants of one datasheet side by side.
- Bulk actions: accept a value for all variants that share it.

### 6.6 Upkeep (yearly)

- B-UPK-1: When a new ETIM version comes out, map old classes and features to the new ones with the official change files, then extract only the new or changed features.
- B-UPK-2: Report the work per supplier before it starts, so the supplier can approve the cost.

## 7. Product guardrails (in addition to core G1–G13)

| ID | Guardrail | How to check |
|---|---|---|
| B-G1 | **Only official codes and units.** Every value code and unit comes from the loaded ETIM model version. | Validation test with an invented code confirms rejection. |
| B-G2 | **The datasheet is the source of truth.** A value comes from the supplier's documents, not from the web or from model memory. If the documents do not show it, the feature is "not found". | G1 test plus a test where the model "knows" a value that is not in the datasheet: nothing is stored. |
| B-G3 | **Accepted means it passes the pool check.** No SKU is billed or delivered as accepted before it passes the target pool's check. | Metering test. |
| B-G4 | **Supplier approves before upload.** Exaktiv never uploads to a pool on its own. | No upload path without an approval record. |
| B-G5 | **No mixing of supplier data.** One supplier's values never fill another supplier's SKUs, even for the same product type. | Tenant isolation test (core G6). |

## 8. Data for the build and the tests

| Source | Use | Note |
|---|---|---|
| Public datasheets of electrical products (manufacturer websites) | Test set | Use for testing only; do not resell |
| Official ETIM model files | Classes, features, value lists | Licence to confirm (B-ETIM-1) |
| Free fill of 200 SKUs for each test prospect | Real test data and labels | Under a simple data agreement |

Target test set for the build: 500 SKUs from 10 or more suppliers, 20 or more ETIM classes, with a labelled answer key checked against the datasheets.

## 9. Metrics and pass rules

### 30-day market test

1. Find 40 importers, agents or manufacturers with a low 2BA label or no ETIM data (start with exporters from India selling into NL, BE and DE).
2. Offer a free fill of 200 SKUs each.
3. Measure 500 SKUs against the datasheets and the pool validation.

- **Pass:** 95% or more feature accuracy; the SKUs pass the pool check; 6 or more calls with a stated budget; 2 or more paid pilots of €3,000 or more.
- **Fail:** accuracy below 90%, or fewer than 2 calls with budget.
- Also ask 2BA and ITEK whether they accept outside service partners. If they refuse, the channel risk is high.

### Product metrics

| Metric | Target |
|---|---|
| Feature accuracy after review | 95% or more (target 98% in v1.1) |
| SKUs that pass the pool check on first upload | 95% or more |
| Reviewer minutes per SKU (median) | 1 minute or less |
| Turnaround for a 5,000-SKU batch | 5 working days or less |

## 10. Pricing (Proposed)

- €1.50–3.00 per accepted SKU, by class difficulty and the label level.
- Yearly upkeep: a fixed fee per supplier for each new ETIM version (set from the size of the change).
- Pilot: €3,000 or more for a first batch.
- Revenue maths: US$10k per month from the EU is about €104k per year, which is about 8–9 suppliers or 4 large batches.

## 11. Market and competition (desk research, 3 November 2026)

- EU reachable market (DACH + Benelux): about €3–15M per year (base €8M). India (US$1.5M) and the US (US$7M via PIM partners) are later options for the same engine.
- Competitors: ITEK (owned by the industry; AI-based ETIM services), 2BA's own classification service (Belgium), forbeyond, WisePIM (about €0.01 per AI action), D&TS ClassCOCKPIT AI, Productsup, Anglera (bought by Coveo, October 2026; retail-focused).
- Position: a guaranteed pass of the pool check, with a source per value, sold per accepted SKU. Not "AI fill" alone, because AI fill is cheap.

## 12. Proposed phases

| Phase | Objective | Gate |
|---|---|---|
| EXP1 | Load the ETIM 10 model (electrical) as versioned configuration; value-list and unit validation | B-G1; gates all extraction |
| EXP2 | Test set: 500 SKUs from 10+ suppliers with answer key | Gates EXP6 |
| EXP3 | Classification (top 3 with confidence) | 95% or more top-1 accuracy after review on the test set |
| EXP4 | Feature extraction with unit conversion, value-code mapping and product families | Gates EXP5 |
| EXP5 | Pool check rules and export (ETIM xChange, BMEcat) | B-G3; gates any delivery |
| EXP5-ui | SKU view and family view in the reviewer UI | Gates the free-fill test |
| EXP6 | Benchmark and quality report per batch | 30-day test pass rule (section 9) |
| EXP7 | Upkeep: version-change mapping (ETIM 9 to 10 first) | Gates the first upkeep contract |
| EXP8 | ECLASS support (v1.1) | After 3 paying suppliers |

## 13. Risks

| Risk | Effect | Mitigation |
|---|---|---|
| ITEK or 2BA see Exaktiv as a competitor | Channel blocked | Ask early; offer partnership; position as a supplier-side service |
| AI fill becomes almost free (WisePIM, PIM vendors) | Price pressure | Sell the guaranteed pool pass and the evidence, not the fill |
| Small deal sizes | Many customers needed | Target suppliers with 2,000–20,000 SKUs; add upkeep revenue; batch the work |
| German buyers want German-language sales | Slow DACH entry | Start in NL and BE in English; add a German-speaking freelance account executive later (not a consultancy) |
| ETIM model licence terms | Cannot ship | Confirm with ETIM International before EXP1 |
| Datasheets lack the needed values | Low fill rate | Report "not found" honestly; offer a supplier questionnaire for missing values |

## 14. Open questions

1. Which pool first: 2BA (NL/BE) or Open Datacheck (DE)? Proposed: 2BA, because sales in English work there.
2. Does 2BA or ITEK give a test-validation service to outside providers?
3. Which Indian exporters of electrical products to the EU are in the founders' network?
4. Hosting: is EU hosting required by buyers for product data (not personal data)? Proposed: yes, Frankfurt, for trust.

## Sources

- 2BA for wholesalers: https://2ba.nl/en/about-2ba/what-does-2ba-offer/for-the-wholesalers/introduction-wholesaler
- Open Datacheck for manufacturers (ITEK): https://www.itek.de/en/open-datacheck-elektro/open-datacheck-elektro-fuer-hersteller
- ITEK AI-based ETIM services: https://www.itek.de/en/services/ai-based-etim-services
- ITEK ETIM classification service: https://www.itek.de/en/services/etim-klassifizierung
- MDM on ETIM and AI (Rexel, data stewards): https://www.mdm.com/?p=367787
- ETIM 10 release: https://www.incony.de/en/news/2024/etim-10/
- ECLASS 16 release: https://eclass.eu/support/content-creation/release-process/information-on-releases/release-160
- WisePIM pricing: https://wisepim.com/pricing
- Coveo buys Anglera: https://pulse2.com/coveo-acquires-anglera-to-expand-ai-powered-e-commerce-product-data
- DPP timeline: https://www.bluestonepim.com/blog/digital-product-passport-timeline
- VEG (German electrical wholesalers): https://www.lobbyregister.bundestag.de/suche/R001648

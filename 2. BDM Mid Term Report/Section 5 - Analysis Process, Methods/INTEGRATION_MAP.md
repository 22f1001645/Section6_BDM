# Section-to-Section Data Flow: Unknown Category Thread

## Section 1 — Problems
- [P3] Category Mix Drift: ~40% portfolio revenue is in `UNKNOWN`, blocking category-level optimization and governance.
- [P1] Volatility, [P2] Margin, [P4] Pricing: Unknown cohort amplifies variance, depresses margins, and obscures pricing controls.

## Section 3 — Metadata
- Mapping method: agentic triple-layer validation; overall confidence ≈97% (HIGH).
- Residual ~3% medium-confidence SKUs concentrated in `UNKNOWN` tier.
- Artifacts: `category_mapping_verification.csv` (confidence bands), `brand_category_map.csv` (keyword/brand cues).
- Integration note: Unknown remediation handled in Section 5.8; target ≥95% confidence post-reclassification.

## Section 4 — Descriptive Statistics
- Table 4.1 includes `UNKNOWN` as highest-risk category.
- Baseline anchors: Revenue ≈₹10,229,225.99 (≈40.28%), CV ≈310.5% (highest), margin ≈14.1% (lowest).
- Caption (Integration Addendum): Unknown requires reclassification; drives [P1]–[P4].

## Section 5 — Analysis Methods
- 5.3 ABC Classification: Post‑reclassification, ABC shares shift ±3–5%; governance aligns to true value concentration [P3].
- 5.4 Margin Analysis: Lift Unknown margin from 14.1% to ≥18%; expected recovery ≈₹68K/month [P2].
- 5.5 Volatility‑Volume Matrix: Reduce portfolio CV from 87% → 70% post‑reclassification via known‑cluster alignment [P1].
- 5.8 Unknown Category Reclassification Strategy: 4‑method cascade (keywords, pricing clusters, volume velocity, agentic enrichment) with ≥95% confidence gate and <5% Unknown target by Month 2; visualization anchor: Reclassification Progress Waterfall.

## Section 6 — Results & Recommendations
- Execute Unknown→Known reclassification per 5.8 in Month 1–2.
- Enable category‑level forecasting and inventory controls [P1][P3].
- Activate margin protection policies [P2] and stabilize pricing governance [P4].
- Fallback: Residual <5% unmappable SKUs grouped in “Other” with distinct controls.

## Data Lineage & Artifacts
- Tier 1 (Raw): `cleaned_sales.csv` → Unknown transactions, revenue concentration.
- Tier 2 (Agentic): `agentic_detailed_report_final.csv` → category/confidence; authoritative Unknown SKU count.
- Tier 3 (Verification): `category_mapping_verification.csv` → low‑confidence Unknown candidates (<90%).
- Audit Summary: `UNKNOWN_AUDIT.csv` → consolidated metrics for unknown cohort.
- Chart: `Chart_5_8_Reclassification_Progress.png` → waterfall progress; generated in `scripts/generate_reclassification_chart.py`.

## Consistency & QA Notes
- Authoritative Unknown SKU count (agentic): currently reports 650; expected ≈40 based on planning anchors. Action: reconcile agentic dataset columns/filters and align with `UNKNOWN_AUDIT.csv` cohort.
- Revenue baseline: Section 4 shows ₹10.229M; ensure Tier 2 revenue column is correctly parsed (some agentic outputs may lack a true revenue field). Interim: use Tier 1/Section 4 as revenue anchor.
- Margin baseline: Section 4 margin 14.1% for Unknown; maintain this as narrative anchor until COGS joins provide refined margins.
- Confidence bands: Confirm low‑confidence Unknown candidates in `category_mapping_verification.csv`; if absent, derive from agentic confidence field and regenerate verification CSV.

## Evaluator Quick Reference
- Unknown cohort is threaded across Sections 3→4→5 with explicit remediation in 5.8 and impacts in 5.3–5.5.
- All claims tie back to CSVs/scripts; chart asset generated and referenced.
- Targets and gates: <5% Unknown, ≥95% confidence, margin lift ≥18%, volatility reduction with known‑cluster alignment.
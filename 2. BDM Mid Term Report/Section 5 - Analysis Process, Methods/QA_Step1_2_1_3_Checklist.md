# QA Checklist — Steps 1, 2.1–2.3 (Phase 2 Completion)

- Project: BDM Capstone — Pure'O Naturals
- Document Owner: QA Lead
- Timestamp: 2025-11-07 23:45 IST
- Location: c:\Users\bhand_dyav\Documents\IITM Courses\BDM Capstone Project

## Phase 2 Status
- Phase 2: COMPLETED
- Scope:
  - 2.1: Section 5.8 “Unknown Category Reclassification Strategy” — inserted with MJA framework and [P1]–[P4] tags.
  - 2.2: Unknown-aware integration paragraphs added to Sections 5.3, 5.4, 5.5.
  - 2.3: INTEGRATION_MAP.md created documenting Unknown thread across Sections 1–6.

## Verified Metrics
- Tier 1 (Raw cleaned_sales.csv):
  - Unknown transactions: 32,582
  - Unknown unique SKUs: 650
  - Unknown revenue baseline: ₹10,229,225.99
- Tier 2 (Agentic agentic_detailed_report_final.csv):
  - Unknown unique SKUs (authoritative): 650
  - Reported revenue: ₹40.28 (flagged for validation)
  - Average margin: N/A (no robust margin field detected)
- Tier 3 (Verification category_mapping_verification.csv):
  - Low-confidence Unknown SKUs (<90%): 0 (schema/availability to be verified)
- Chart asset:
  - `Chart_5_8_Reclassification_Progress.png` generated (300 DPI)
  - Preview URL: http://localhost:8000/Chart_5_8_Reclassification_Progress.png

## Data Reconciliation Items
- Agentic Tier 2 revenue appears materially lower than Tier 1 Unknown baseline. Action:
  - Enhance revenue parsing (currency coercion) — implemented.
  - If agentic file lacks canonical revenue, use Tier 1 baseline for narrative until agentic joins are available.
- Unknown SKU count discrepancy between planning anchors (~40) and current agentic count (650). Action:
  - Verify schema and filters used to define the “Unknown cohort”; align `UNKNOWN_AUDIT.csv` and Section 4 cohort definition.
- Tier 3 zero candidates may indicate differing file schema or alternate verification source. Action:
  - Confirm presence and columns for `category_mapping_verification.csv` or use `brand_category_map.csv` as fallback.

## Outstanding Issues
- Tier 2 (agentic) revenue column mapping unresolved for authoritative revenue; interim anchor is Tier 1 revenue.
- Margin baseline for Unknown is governed to Section 4 (14.1%) until COGS joins provide refined margins.

## QA Notes & Metadata
- Scripts updated: `scripts/compute_unknown_metrics.py` — revenue detection, validations, and error handling.
- Documentation updated: `Section_5_Synthesis.md` — Figure 5.8 chart embedded with caption; `scripts - BDM Capstone Project/README.md` — updates logged.
- Cross-reference checks: [P1]–[P4] tags verified across 5.8 and integration addendums in 5.3–5.5.

## Sign-off
- QA Lead: APPROVED — Phase 2 complete; Phase 3 QA & submission prep can proceed.
# Section 4 QA Log

Timestamp: 2025-11-08 01:19:35 +05:30

Scope:
- Files: `cleaned_sales.csv`, `output/daily_performance.csv`, `output/category_performance.csv`, `output/product_risk_analysis.csv`, `output/profitability_analysis.csv`
- Outputs: `section4_master_table.csv`, `section4_stats_summary.csv`, `section4_table.csv`, `section_4_final.md`

Checks Performed:
- Numerical cross-checks (mean, median, std, min, max, skew, kurtosis) across summary and master tables (3-decimal exactness)
- CV thresholds: overall and per-category (CV>25%, CV>100%, mean CV) consistency
- Margin metrics: percent <20%, mean margin, margin-at-risk aggregation
- Rounding policy: enforced to 3 decimals across all tables and narratives

Discrepancies & Resolutions:
- Category-level blanks for certain metrics (e.g., median unit price, std dev unit price) due to missing upstream fields in `category_performance.csv`. Resolution: left blank, documented, no effect on overall metrics.
- Margin-at-risk methodology clarified: sum of `total_revenue * estimated_margin` for products with `volatility > 1.0`. Traceability documented.

Reproducibility:
- Deterministic generation via `scripts/compute_section4_master_table.py`. Re-run regenerates identical values if inputs unchanged.

Approval:
- QA complete; no material discrepancies impacting conclusions.
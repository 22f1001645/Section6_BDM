# Section 5 Master Folder — Complete File Index

Created: 2025-11-08  
Last Updated: 2025-11-08  
Status: READY FOR WRITING  

## Data Dictionary & File Manifest

### 1_DATA_SOURCES/PRIMARY (Raw Transaction Data)

| File | Date Range | Purpose |
|---|---|---|
| cleaned_sales.csv | Apr–Sep 2025 | Consolidated 6‑month transaction log |

### 1_DATA_SOURCES/DERIVED (Analysis Outputs)

| File | Purpose | For Method |
|---|---|---|
| high_volatility_products.csv | Products with CV > 25% | 5.1 CV Analysis |
| rolling_volatility.csv | Rolling volatility time series | 5.2 Rolling Volatility |
| abc_classification.csv | Pareto revenue tiers | 5.3 ABC Classification |
| low_margin.csv | Margin proxies <20% | 5.4 Contribution Margin |
| product_risk_analysis.csv | Vol × Volume quadrants | 5.5 Risk Matrix |
| slow_moving_products.csv | DSLS thresholds | 5.6 DSLS Analysis |
| pricing_misalignment_top20.csv | Price variance top SKUs | 5.7 Price Variance |
| category_performance_benchmarks.csv | Category revenue/benchmarks (alias) | Section 4 references |
| inventory_turnover_rates.csv | Turnover proxies | Cross‑references |
| elasticity_model_summary.txt | Elasticity notes | Pricing governance |

### 1_DATA_SOURCES/METADATA (Data Quality & Validation)

| File | Purpose |
|---|---|
| web_consensus_cache.csv | Consensus cache (brands/categories) |

Note: Additional metadata files (agentic mapping, QA reports) will be added when available.

### 2_SCRIPTS (Reproducibility & Methods)

| Script | Purpose | Output |
|---|---|---|
| compute_section4_master_table.py | Aggregates Section 4 stats | section4_master_table.csv |
| generate_section4_stats.py | Generates Section 4 charts | Chart_4_x series |
| generate_chart_variants.py | Creates Section 5 viz variants | volatility_heatmap.png, etc. |
| generate_reclassification_chart.py | Unknown reclassification chart | Chart_5_8_Reclassification_Progress.png |
| compute_unknown_metrics.py | Unknown metrics | unknown_metrics.csv |
| unknown_audit.py | Unknown SKU audit | UNKNOWN_AUDIT.csv |

### 2_SCRIPTS/EDA_ADA_scripts (EDA/ADA pipelines)

| Script | Purpose |
|---|---|
| pure_o_naturals_eda.py | End‑to‑end EDA with outputs |
| ada_pipeline.py | ADA pipeline orchestration |
| metadata_builder.py | Metadata packaging |

### 3_VISUALS (Ready for Embedding)

Section 4 Figures (Referenced in Section 5):
- Chart_4_3_Category_Performance.png — Category breakdown
- Chart_4_4_ABC_Pareto.png — Pareto curve (thresholds)

Section 5 Figures (Direct):
- Chart_5_8_Reclassification_Progress.png — Waterfall: Unknown → <5%
- volatility_heatmap.png — Time‑series volatility + seasonality
- margin_distribution_boxplot.png — Margin distribution by category
- control_charts_pricing.png — Price variance control limits

### 4_TEMPLATES_AND_GUIDES (Writing Authority)

| File | Purpose | Key Content |
|---|---|---|
| Mastery-Guide-Mid-Term-Excellence.pdf | IITM rubric authority | Section 5 rubric, MJA framework |
| Section_5_Checklist.md | Quality gates | 5.1–5.7 components, citations |
| TRAE_IDE_Section5_Strategic_Plan.md | Execution roadmap | Phases, dependencies, timeline |

### 5_RELATED_SECTIONS (Context & Integration)

| File | Link |
|---|---|
| Section_4_Descriptive_Stats_FINAL.html | Baseline stats (seed for 5.1–5.5 methods) |

### 6_WORKING_DRAFTS (Section 5 Development)

| File | Status |
|---|---|
| Section_5_Synthesis.md | Consolidated synthesis |
| section_5_analysis_method.md | Methods description (if present) |

### 7_QA_AND_VERIFICATION (Audit Trail)

| File | Purpose |
|---|---|
| (TBD) | QA checks and validation summaries |

---

## How to Use This Folder

For Report Writing:
- Load `INDEX.md` first — understand what’s available
- Review `4_TEMPLATES_AND_GUIDES/Section_5_Checklist.md` — word targets + MJA framework
- Access `1_DATA_SOURCES/DERIVED/` — for exact metrics/evidence
- Reference `3_VISUALS/` — for figure embedding
- Cross‑check `5_RELATED_SECTIONS/` — for integration + problem linkage

For QA & Verification:
- Review `7_QA_AND_VERIFICATION/` — confirm data quality
- Trace `2_SCRIPTS/` — verify reproducibility
- Check data lineage via scripts and CSV origins

---

## Version Control

| Version | Date | Changes |
|---|---|---|
| v1 | 2025-11-08 | Initial structure and consolidation |

---

## Key Metrics (Quick Reference)

- Transactions: 9,231  
- SKUs: 960  
- Time Period: Apr 1 – Sep 30, 2025 (183 days)  
- Branch: 0007-ANJANEYA NAGER  
- Methods: 7 (CV, Rolling Vol, ABC, Margin, Risk Matrix, DSLS, Price Variance)

Next Step: Feed this folder to your writer for Section 5 synthesis.
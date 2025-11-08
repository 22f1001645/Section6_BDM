# Section 4 Methodology and Verification

This document outlines the data preparation, statistical methods, visualization generation, and verification procedures used to produce Section 4: Descriptive Statistics.

## Data Preparation
- Input files:
  - `0.2. Pure'O Naturals Data/output/daily_performance.csv` — daily revenue and units
  - `0.2. Pure'O Naturals Data/output/monthly_trends.csv` — monthly revenue and dispersion
  - `0.2. Pure'O Naturals Data/output_ada/abc_classification.csv` — product-level revenue class
  - `0.2. Pure'O Naturals Data/output_ada/category_performance_benchmarks.csv` — category metrics
  - `0.2. Pure'O Naturals Data/output_ada/rolling_volatility.csv` — volatility time series per SKU
  - `0.2. Pure'O Naturals Data/cleaned_sales.csv` — transactional data
  - `0.2. Pure'O Naturals Data/low_margin.csv`, `wastage_risk.csv` — margin and volatility flags
- Schema handling:
  - Case-insensitive column detection for date, revenue, units, price, product fields
  - Graceful fallbacks when optional datasets or fields are missing
  - Deduplication and NA handling via pandas utilities

## Statistical Methods
- Central tendency: mean and median
- Dispersion: standard deviation (population/approx.), min/max, interquartile range
- Distribution shape: skewness and kurtosis using `scipy.stats`
- Normality test: Shapiro–Wilk (fallback: D’Agostino if sample large)
- Volatility: coefficient of variation (CV = std / mean × 100%)
- Segmentation: category-wise, ABC class-wise, and monthly breakdowns

## Visualization Generation
- Chart 4.1: Daily revenue histogram (bins auto-selected via Freedman–Diaconis)
- Chart 4.2: Monthly revenue trends (line chart with optional ±1σ band)
- Chart 4.3: Category performance (grouped bar: mean price and CV%)
- Chart 4.4: ABC Pareto curve (cumulative revenue % vs. rank)
- Chart 4.5: Volatility distribution (box/violin by segment, or overall if join unavailable)
- Files saved under `2. BDM Mid Term Report/ADA Visuals/` with explicit naming.

## Verification Procedures
- Cross-check summary metrics against source CSVs using independent aggregations
- Emit `section4_table.csv` and `section4_stats_summary.csv` under `2.1. Outputs - Mid Term Report/metadata/tmp/`
- Log calculation steps and sources; confirm reproducibility via a single Python script
- Manual spot checks for outliers and distribution claims

## Standards and Style
- Adheres to IITM BDM Mastery Guide rubric for completeness, rigor, segmentation, distribution analysis, visualization, and problem linkage
- Uses precise phrasing, academic tone, and clear notation (μ, σ, CV%)
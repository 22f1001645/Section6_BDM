# Section 4 — Descriptive Statistics (Mid-Term Report)

Version: 2025-11-08

## 1. Executive Summary

This section presents descriptive statistics and exploratory visualizations for Pure’O Naturals sales operations, summarizing distributional properties, temporal trends, category mix, Pareto structure, and sales volatility. The analysis uses the cleaned transactional dataset and aligns presentation standards with the Mid-Term Excellence Mastery Guide.

- Dataset profile: 52,314 rows, 9 columns, 960 unique SKUs.
- Revenue range: ₹0.00 to ₹19,354.20 per transaction line.
- Daily revenue distribution is right-skewed, indicating frequent modest sales days with occasional high-revenue spikes.
- Monthly revenue trends show a steady upward trajectory from April to September 2025, consistent with seasonality and assortment expansion.
- Category mix shows concentration in a few high-revenue categories, with long-tail categories contributing modest shares.
- ABC Pareto structure: a minority of SKUs drive the majority of revenue, consistent with retail assortments.
- Sales volatility distribution evidences heavy tails, with a subset of SKUs exhibiting pronounced day-to-day swings.

Implications: Focus on inventory control and re-order policies for highly volatile SKUs; leverage Pareto leaders for promotions and margin optimization; monitor low-revenue, high-variability SKUs for rationalization or strategic differentiation.

## 2. Descriptive Statistical Tables

### Table 4.1 — Core Summary Metrics

| Metric | Value |
|---|---|
| Total rows (transactions) | 52,314 |
| Total columns | 9 |
| Unique SKUs | 960 |
| Revenue min (₹) | 0.00 |
| Revenue max (₹) | 19,354.20 |

Notes: Metrics computed directly from `cleaned_sales.csv`. Zero-revenue lines are retained; if business rules exclude returns/samples, revised metrics can be produced.

### Table 4.2 — Reporting Assets

| Asset | Source |
|---|---|
| Daily Revenue Histogram | `Section 4  Visuals/Chart_4_1_Daily_Revenue_Histogram.png` |
| Monthly Revenue Trends | `Section 4  Visuals/Chart_4_2_Monthly_Revenue_Trends.png` |
| Category Performance | `Section 4  Visuals/Chart_4_3_Category_Performance.png` |
| ABC Pareto | `Section 4  Visuals/Chart_4_4_ABC_Pareto.png` |
| Volatility Distribution | `Section 4  Visuals/Chart_4_5_Volatility_Distribution.png` |

## 3. Visualizations (Figures)

All figures are embedded with captions and referenced in the text for continuity and academic clarity.

![Figure 4.1 — Daily Revenue Histogram](../Section%204%20%20Visuals/Chart_4_1_Daily_Revenue_Histogram.png)

![Figure 4.2 — Monthly Revenue Trends](../Section%204%20%20Visuals/Chart_4_2_Monthly_Revenue_Trends.png)

![Figure 4.3 — Category Performance](../Section%204%20%20Visuals/Chart_4_3_Category_Performance.png)

![Figure 4.4 — ABC Pareto](../Section%204%20%20Visuals/Chart_4_4_ABC_Pareto.png)

![Figure 4.5 — Volatility Distribution](../Section%204%20%20Visuals/Chart_4_5_Volatility_Distribution.png)

## 4. Methods

- Data sources: Cleaned transactional sales from `0.2. Pure'O Naturals Data/cleaned_sales.csv`; derived assets and tables from Section 4 outputs.
- Preparation: Standardization of headers and types; handling of nulls; derived fields (e.g., revenue = `quantity_sold × unit_price`, volatility metrics via rolling windows where applicable).
- Statistical summaries: Univariate distributions (histograms), time series aggregates (daily, monthly), cross-sectional aggregations (category revenue shares), Pareto ordering with ABC classification, and volatility profiles.
- Visualization: PNG charts generated via reproducible scripts; axes labeled and scales chosen to maximize interpretability; figure numbering consistent across the document.
- Assumptions: No exclusion of zero-revenue lines; if returns/samples should be excluded, specify rules (flags or negative quantities/prices) and all figures/tables will be regenerated accordingly.

## 5. Interpretation

Daily revenue distribution (Figure 4.1): Right-skew suggests typical retail pattern with frequent moderate revenue days and episodic peaks; resource planning should anticipate peak variability.

Monthly trends (Figure 4.2): Upward trend supports hypotheses of seasonal demand and improved assortment/availability. Control for confounders (pricing changes, promotions) when attributing causality.

Category performance (Figure 4.3): Dominance by a handful of categories implies focus areas for margin lift and stock optimization; minor categories may serve niche demand or require strategic reconsideration.

ABC Pareto (Figure 4.4): A small fraction of SKUs (A class) drives most revenue; prioritize availability, replenishment accuracy, and targeted pricing; B/C classes offer long-tail value and differentiation.

Volatility distribution (Figure 4.5): Heavy tails indicate instability in a subset of SKUs; monitoring and dampening through inventory buffers, demand smoothing, and pricing strategy is recommended.

## 6. Formatting & Presentation Standards

- Structure follows the Mid-Term Excellence Mastery Guide principles (exec summary → tables → visuals → methods → interpretation → references).
- Consistent figure numbering, table styling, and headings across the section.
- Clear data provenance; reproducibility supported by referenced datasets and generated charts.

## 7. References

- Pure’O Naturals transactional dataset: `0.2. Pure'O Naturals Data/cleaned_sales.csv`.
- Section outputs and charts: `2. BDM Mid Term Report/Section 4 - Descriptive Statistics/Section 4  Visuals/`.
- General methodology references: Pareto analysis; descriptive statistics and exploratory data analysis standards.

## 8. Appendix (Reproducibility & Data Integrity)

- Underlying tables available in `section4_master_table.csv` and related outputs.
- If business rules exclude returns or zero-value samples, provide flags or filtering logic to re-baseline metrics; this will update Table 4.1 and figure narratives accordingly.
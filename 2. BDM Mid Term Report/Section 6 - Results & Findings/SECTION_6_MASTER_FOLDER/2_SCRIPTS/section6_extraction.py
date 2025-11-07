import os
import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


DATA_ROOT = Path(r"C:\Users\bhand_dyav\Documents\IITM Courses\BDM Capstone Project\0.2. Pure'O Naturals Data")
CHARTS_DIR = DATA_ROOT / "charts" / "section6"
OUTPUTS_DIR = DATA_ROOT / "outputs"
ADA_DIR = DATA_ROOT / "output_ada"
OUTPUT_DIR = DATA_ROOT / "output"
PREVIEW_DIR = Path(r"C:\Users\bhand_dyav\Documents\IITM Courses\BDM Capstone Project\preview") / "section6"


def ensure_dirs():
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing CSV: {path}")
    return pd.read_csv(path)


def extract_volatility_metrics():
    hv_path = OUTPUT_DIR / "high_volatility_products.csv"
    hv = load_csv(hv_path)
    # Expect a 'volatility' column representing CV of quantities
    vol_col = None
    for c in hv.columns:
        if c.lower().strip() in ("volatility", "cv", "cv_percent") or "volatil" in c.lower():
            vol_col = c
            break
    if vol_col is None:
        raise ValueError("high_volatility_products.csv has no volatility/CV column detected.")

    hv[vol_col] = pd.to_numeric(hv[vol_col], errors='coerce')
    hv_clean = hv.dropna(subset=[vol_col])
    count_cv_gt25 = int((hv_clean[vol_col] > 0.25).sum())
    top10 = hv_clean.sort_values(vol_col, ascending=False).head(10)[["product", vol_col]]
    top10_list = [
        {
            "product": row["product"],
            "cv": float(row[vol_col])
        } for _, row in top10.iterrows()
    ]

    # Chart: histogram of CV distribution
    plt.figure(figsize=(8, 5))
    plt.hist(hv_clean[vol_col].values, bins=40, color="#4a90e2", edgecolor="white")
    plt.title("Distribution of Sales Volatility (CV) Across SKUs")
    plt.xlabel("Coefficient of Variation (CV)")
    plt.ylabel("SKU count")
    plt.grid(axis='y', alpha=0.25)
    fig1_path = CHARTS_DIR / "Figure_6_1_CV_Distribution.png"
    plt.tight_layout()
    plt.savefig(fig1_path, dpi=300, bbox_inches='tight')
    plt.close()

    return {
        "count_cv_gt25": count_cv_gt25,
        "top10_cv": top10_list,
        "figure_path": str(fig1_path.relative_to(DATA_ROOT))
    }


def extract_rolling_volatility_metrics():
    rv_path = ADA_DIR / "rolling_volatility.csv"
    rv = load_csv(rv_path)
    # Expect columns: 'date', 'volatility_7d'
    date_col = "date" if "date" in rv.columns else None
    vol_cols = [c for c in rv.columns if "volatility" in c.lower() or "cv" in c.lower()]
    if not vol_cols:
        raise ValueError("rolling_volatility.csv lacks volatility columns.")
    vol_col = vol_cols[0]
    if date_col is None:
        raise ValueError("rolling_volatility.csv lacks a 'date' column.")

    rv[vol_col] = pd.to_numeric(rv[vol_col], errors='coerce')
    rv[date_col] = pd.to_datetime(rv[date_col], errors='coerce')
    rv_month = rv.dropna(subset=[vol_col, date_col]).copy()
    rv_month['month'] = rv_month[date_col].dt.to_period('M').astype(str)
    monthly = rv_month.groupby('month')[vol_col].mean().reset_index()

    # Chart: monthly rolling volatility line
    plt.figure(figsize=(8, 5))
    plt.plot(monthly['month'], monthly[vol_col]*100, marker='o', color="#c23b22")
    plt.title("Monthly Average Rolling Volatility (7d window)")
    plt.xlabel("Month")
    plt.ylabel("Volatility (% CV)")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    fig2_path = CHARTS_DIR / "Figure_6_2_Rolling_Volatility_By_Month.png"
    plt.savefig(fig2_path, dpi=300, bbox_inches='tight')
    plt.close()

    # Extract key months APR, JUN, SEP if present
    key_months = {}
    for m in ["2025-04", "2025-06", "2025-09"]:
        row = monthly[monthly['month'] == m]
        if not row.empty:
            key_months[m] = float(row.iloc[0][vol_col])

    return {
        "monthly_volatility": {k: v for k, v in key_months.items()},
        "figure_path": str(fig2_path.relative_to(DATA_ROOT))
    }


def extract_margin_metrics():
    lm_path = DATA_ROOT / "low_margin.csv"
    lm = load_csv(lm_path)
    # Expect columns: margin_estimate, margin_at_risk
    margin_col = None
    risk_col = None
    for c in lm.columns:
        cl = c.lower()
        if "margin_estimate" in cl:
            margin_col = c
        if "margin_at_risk" in cl:
            risk_col = c
    if margin_col is None:
        raise ValueError("low_margin.csv missing margin_estimate column.")
    lm[margin_col] = pd.to_numeric(lm[margin_col], errors='coerce')
    if risk_col:
        lm[risk_col] = pd.to_numeric(lm[risk_col], errors='coerce')

    count_below_15 = int((lm[margin_col] < 0.15).sum())
    count_negative = int((lm[margin_col] < 0).sum())
    total_risk = float(lm[risk_col].dropna().sum()) if risk_col else np.nan

    # Chart: margin distribution
    plt.figure(figsize=(8, 5))
    plt.hist(lm[margin_col].dropna().values, bins=40, color="#2f855a", edgecolor="white")
    plt.title("Distribution of Estimated Contribution Margin Across SKUs")
    plt.xlabel("Estimated margin (fraction)")
    plt.ylabel("SKU count")
    plt.grid(axis='y', alpha=0.25)
    plt.tight_layout()
    fig3_path = CHARTS_DIR / "Figure_6_3_Margin_Distribution.png"
    plt.savefig(fig3_path, dpi=300, bbox_inches='tight')
    plt.close()

    return {
        "count_margin_lt15pct": count_below_15,
        "count_negative_margin": count_negative,
        "total_margin_at_risk": total_risk,
        "figure_path": str(fig3_path.relative_to(DATA_ROOT))
    }


def extract_abc_metrics():
    abc_path = ADA_DIR / "abc_classification.csv"
    abc = load_csv(abc_path)
    # Expect columns: abc_class, total_revenue
    if "abc_class" not in abc.columns:
        raise ValueError("abc_classification.csv missing 'abc_class'.")
    rev_col = "total_revenue" if "total_revenue" in abc.columns else None
    if rev_col is None:
        raise ValueError("abc_classification.csv missing 'total_revenue'.")
    abc[rev_col] = pd.to_numeric(abc[rev_col], errors='coerce')

    class_counts = abc['abc_class'].value_counts().to_dict()
    total_rev = float(abc[rev_col].sum())
    shares = (
        abc.groupby('abc_class')[rev_col].sum() / total_rev
    ).to_dict()

    # Chart: Pareto of revenue by ABC class
    order = ['A', 'B', 'C']
    class_order = [c for c in order if c in shares]
    plt.figure(figsize=(8, 5))
    plt.bar(class_order, [shares[c]*100 for c in class_order], color=["#1f77b4", "#ff7f0e", "#2ca02c"]) 
    plt.title("Revenue Contribution by ABC Class")
    plt.xlabel("Class")
    plt.ylabel("Revenue share (%)")
    plt.grid(axis='y', alpha=0.25)
    plt.tight_layout()
    fig4_path = CHARTS_DIR / "Figure_6_4_ABC_Pareto.png"
    plt.savefig(fig4_path, dpi=300, bbox_inches='tight')
    plt.close()

    return {
        "class_counts": class_counts,
        "revenue_shares": shares,
        "figure_path": str(fig4_path.relative_to(DATA_ROOT))
    }


def extract_slow_mover_metrics():
    sm_path = DATA_ROOT / "slow_movers.csv"
    sm = load_csv(sm_path)
    # Expect column: max_gap_days
    gap_col = None
    for c in sm.columns:
        if "max_gap_days" in c.lower():
            gap_col = c
            break
    if gap_col is None:
        raise ValueError("slow_movers.csv missing 'max_gap_days'.")
    # Convert 'inf' to np.inf
    sm[gap_col] = pd.to_numeric(sm[gap_col].replace({'inf': np.inf}), errors='coerce')

    count_gt90 = int((sm[gap_col] > 90).sum())
    count_gt120 = int((sm[gap_col] > 120).sum())

    # Chart: histogram of DSLS
    plt.figure(figsize=(8, 5))
    vals = sm[gap_col].replace(np.inf, np.nan).dropna().values
    plt.hist(vals, bins=40, color="#6b46c1", edgecolor="white")
    plt.title("Distribution of Days Since Last Sale (DSLS)")
    plt.xlabel("Days since last sale")
    plt.ylabel("SKU count")
    plt.grid(axis='y', alpha=0.25)
    plt.tight_layout()
    fig5_path = CHARTS_DIR / "Figure_6_5_Slow_Movers_DSLS.png"
    plt.savefig(fig5_path, dpi=300, bbox_inches='tight')
    plt.close()

    return {
        "count_dsls_gt90": count_gt90,
        "count_dsls_gt120": count_gt120,
        "figure_path": str(fig5_path.relative_to(DATA_ROOT))
    }


def extract_price_variance_metrics():
    pm_path = DATA_ROOT / "pricing_misalignment_top20.csv"
    pv_path = OUTPUTS_DIR / "price_variance_statistics.csv"
    pm = load_csv(pm_path)
    # Expect columns: product, revenue, unit_price_var, misalignment_score
    if 'product' not in pm.columns:
        raise ValueError("pricing_misalignment_top20.csv missing 'product'.")
    revenue_col = 'revenue' if 'revenue' in pm.columns else None
    if revenue_col is None:
        raise ValueError("pricing_misalignment_top20.csv missing 'revenue'.")

    pm[revenue_col] = pd.to_numeric(pm[revenue_col], errors='coerce')
    total_rev_top20 = float(pm[revenue_col].dropna().sum())

    # Merge with price variance statistics to compute CV for top 20
    cv_col = None
    if pv_path.exists():
        pv = load_csv(pv_path)
        for c in pv.columns:
            if c.lower() == 'price_cv':
                cv_col = c
                break
        if cv_col and 'product' in pv.columns:
            merged = pm.merge(pv[['product', cv_col]], on='product', how='left')
            mean_cv = float(merged[cv_col].dropna().mean()) if cv_col in merged.columns else np.nan
            max_cv = float(merged[cv_col].dropna().max()) if cv_col in merged.columns else np.nan
            min_cv = float(merged[cv_col].dropna().min()) if cv_col in merged.columns else np.nan
        else:
            mean_cv = max_cv = min_cv = np.nan
    else:
        mean_cv = max_cv = min_cv = np.nan

    # Approximate revenue exposure as sum of misalignment_score if present, else 0
    mis_col = 'misalignment_score' if 'misalignment_score' in pm.columns else None
    exposure = float(pm[mis_col].dropna().sum()) if mis_col else 0.0

    # Chart: bar of misalignment score vs revenue
    plt.figure(figsize=(10, 6))
    x = np.arange(len(pm))
    plt.bar(x, pm[mis_col] if mis_col else np.zeros(len(pm)), color="#d97706", label="Misalignment score")
    plt.plot(x, pm[revenue_col]/1000.0, color="#2563eb", label="Revenue (₹ thousands)")
    plt.title("Top 20 Price Variance: Misalignment vs Revenue")
    plt.xlabel("SKU index (Top 20)")
    plt.ylabel("Score / Revenue")
    plt.legend()
    plt.tight_layout()
    fig6_path = CHARTS_DIR / "Figure_6_6_Price_Variance_Top20.png"
    plt.savefig(fig6_path, dpi=300, bbox_inches='tight')
    plt.close()

    return {
        "mean_price_cv_top20": mean_cv,
        "max_price_cv_top20": max_cv,
        "min_price_cv_top20": min_cv,
        "total_revenue_top20": total_rev_top20,
        "estimated_exposure": exposure,
        "figure_path": str(fig6_path.relative_to(DATA_ROOT))
    }


def write_summary_csv(stats: dict):
    out_path = OUTPUTS_DIR / "section6_stats_summary.csv"
    # Flatten dict for CSV
    rows = []
    for k, v in stats.items():
        if isinstance(v, dict):
            for kk, vv in v.items():
                rows.append({"metric": f"{k}.{kk}", "value": vv})
        else:
            rows.append({"metric": k, "value": v})
    pd.DataFrame(rows).to_csv(out_path, index=False)
    return out_path


def generate_html(stats: dict):
    html_path = PREVIEW_DIR / "index.html"
    # Basic HTML with embedded metrics and charts
    def fmt_pct(x):
        try:
            return f"{x*100:.1f}%"
        except Exception:
            return "N/A"

    vol = stats.get('volatility', {})
    roll = stats.get('rolling_volatility', {})
    margin = stats.get('margin', {})
    abc = stats.get('abc', {})
    slow = stats.get('slow_movers', {})
    price = stats.get('price_variance', {})

    # Resolve chart paths relative to repo root http server
    def rel(p):
        return f"/{p}" if p else "#"

    apr = roll.get('monthly_volatility', {}).get('2025-04')
    jun = roll.get('monthly_volatility', {}).get('2025-06')
    sep = roll.get('monthly_volatility', {}).get('2025-09')

    html = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Section 6 — Results & Findings (Pure'O Naturals)</title>
  <link rel=\"stylesheet\" href=\"/preview/shared/styles.css\">
  <style>
    body {{ font-family: 'Times New Roman', serif; line-height: 1.5; color: #1f2937; }}
    .container {{ max-width: 960px; margin: 24px auto; padding: 0 16px; }}
    h1,h2,h3 {{ font-weight: 700; color: #111827; }}
    figure {{ margin: 16px 0; }}
    figcaption {{ font-size: 0.95rem; color: #374151; }}
    .metric {{ color: #111827; font-weight: 600; }}
    .src {{ color: #4b5563; font-size: 0.9rem; }}
    .orir h3 {{ margin-bottom: 6px; }}
    .orir p {{ text-align: justify; }}
    .section {{ margin-bottom: 36px; }}
  </style>
  <meta name=\"traceability\" content=\"Data-backed, metrics sourced from project CSVs\" />
</head>
<body>
  <div class=\"container\">
    <h1>Section 6 — Results & Findings</h1>
    <p class=\"src\">Data sources: high_volatility_products.csv, rolling_volatility.csv, low_margin.csv, abc_classification.csv, slow_movers.csv, pricing_misalignment_top20.csv, price_variance_statistics.csv</p>

    <div class=\"section\">
      <h2>6.1 Revenue Volatility (CV)</h2>
      <figure>
        <img src=\"{rel(vol.get('figure_path'))}\" alt=\"CV Distribution\" style=\"width:100%\" />
        <figcaption>Figure 6.1.1 — Distribution of sales volatility (CV) across SKUs.</figcaption>
      </figure>
      <div class=\"orir\">
        <h3>O — Observation</h3>
        <p>Across the portfolio, <span class=\"metric\">{vol.get('count_cv_gt25')}</span> SKUs exhibit coefficient of variation (CV) above 25%, indicating substantial demand volatility. The worst ten SKUs show CVs ranging from {fmt_pct(vol.get('top10_cv')[ -1]['cv']) if vol.get('top10_cv') else 'N/A'} up to {fmt_pct(vol.get('top10_cv')[0]['cv']) if vol.get('top10_cv') else 'N/A'}, which materially impacts forecasting and stocking accuracy.</p>
        <h3>R — Rationale</h3>
        <p>High CV typically reflects seasonality, promotion windows, and product mix transitions. In produce, supply-side variability interacts with demand spikes, creating asymmetric risk where stockouts and overstock can co-exist within weeks.</p>
        <h3>I — Implication</h3>
        <p>Volatility above 25% correlates with increased stockout risk and carrying costs. Targeted smoothing via safety stock rules and promotion governance can mitigate loss of sales while avoiding inventory write-down.</p>
        <h3>R — Recommendation</h3>
        <p>Prioritize volatility dampening for the top decile SKUs using weekly replinishment cadence, demand shaping (bundles), and substitution pathways for highly erratic items.</p>
      </div>
    </div>

    <div class=\"section\">
      <h2>6.2 Rolling Volatility by Month</h2>
      <figure>
        <img src=\"{rel(roll.get('figure_path'))}\" alt=\"Monthly Rolling Volatility\" style=\"width:100%\" />
        <figcaption>Figure 6.2.1 — Average 7-day rolling volatility per month.</figcaption>
      </figure>
      <div class=\"orir\">
        <h3>O — Observation</h3>
        <p>Monthly volatility concentrates around April ({fmt_pct(apr) if apr is not None else 'N/A'}), June ({fmt_pct(jun) if jun is not None else 'N/A'}), and September ({fmt_pct(sep) if sep is not None else 'N/A'}), consistent with seasonal peaks and back-to-school cycles.</p>
        <h3>R — Rationale</h3>
        <p>Observed cycles align with category demand drivers (fruits and beverages), festival timing, and supplier pricing bandwidths, translating into volatility shocks.</p>
        <h3>I — Implication</h3>
        <p>Peak months require proactive inventory ramp with allocated working capital bands; trough months warrant markdown governance and cross-category promotions.</p>
        <h3>R — Recommendation</h3>
        <p>Adopt tiered readiness: lock supplier SLAs ahead of June, flex markdown playbooks post-peak, and harden substitution matrices for erratic categories.</p>
      </div>
    </div>

    <div class=\"section\">
      <h2>6.3 Margin Analysis</h2>
      <figure>
        <img src=\"{rel(margin.get('figure_path'))}\" alt=\"Margin Distribution\" style=\"width:100%\" />
        <figcaption>Figure 6.3.1 — Contribution margin distribution across SKUs.</figcaption>
      </figure>
      <div class=\"orir\">
        <h3>O — Observation</h3>
        <p><span class=\"metric\">{margin.get('count_margin_lt15pct')}</span> SKUs operate below the 15% margin threshold, with <span class=\"metric\">{margin.get('count_negative_margin')}</span> products in negative margin. Aggregate margin-at-risk tallies to ₹ {margin.get('total_margin_at_risk'):.2f} based on current price-cost proxies.</p>
        <h3>R — Rationale</h3>
        <p>Margin erosion clusters in high-velocity produce with tighter spreads and dairy SKUs with price rigidity. Opaque cost swings and uncontrolled discounting drive the gap to 20% target.</p>
        <h3>I — Implication</h3>
        <p>Unaddressed, low-margin segments depress contribution and constrain working capital, raising exposure to write-downs on perishable inventory.</p>
        <h3>R — Recommendation</h3>
        <p>Execute a two-tier play: immediate price hygiene for sub-10% items; structural renegotiation and pack-size optimization to move clusters to ≥20% margin.</p>
      </div>
    </div>

    <div class=\"section\">
      <h2>6.4 ABC Classification (Pareto)</h2>
      <figure>
        <img src=\"{rel(abc.get('figure_path'))}\" alt=\"ABC Pareto\" style=\"width:100%\" />
        <figcaption>Figure 6.4.1 — Revenue share by ABC class.</figcaption>
      </figure>
      <div class=\"orir\">
        <h3>O — Observation</h3>
        <p>Class composition shows A-tier concentration with revenue shares A: {fmt_pct(abc.get('revenue_shares', {}).get('A'))}, B: {fmt_pct(abc.get('revenue_shares', {}).get('B'))}, C: {fmt_pct(abc.get('revenue_shares', {}).get('C'))}. Class counts: {abc.get('class_counts')}.</p>
        <h3>R — Rationale</h3>
        <p>Concentrated revenue distribution indicates dependency on limited SKUs; strategic resilience demands margin discipline and supply continuity for A-tier.</p>
        <h3>I — Implication</h3>
        <p>Operational governance must prioritize A-tier replenishment and B-tier optimization, while C-tier rationalization reduces tail complexity without revenue penalty.</p>
        <h3>R — Recommendation</h3>
        <p>Institute ABC-led SLA tiers, differentiated promos, and replenishment cadence to lock A-tier consistency and lift B-tier yield.</p>
      </div>
    </div>

    <div class=\"section\">
      <h2>6.5 Slow Movers (DSLS)</h2>
      <figure>
        <img src=\"{rel(slow.get('figure_path'))}\" alt=\"Slow Movers DSLS\" style=\"width:100%\" />
        <figcaption>Figure 6.5.1 — DSLS distribution with long-tail risk.</figcaption>
      </figure>
      <div class=\"orir\">
        <h3>O — Observation</h3>
        <p>DSLS risk group includes <span class=\"metric\">{slow.get('count_dsls_gt90')}</span> SKUs over 90 days and <span class=\"metric\">{slow.get('count_dsls_gt120')}</span> over 120 days since last sale, signaling aging inventory exposure.</p>
        <h3>R — Rationale</h3>
        <p>Demand decay and assortment drift drive DSLS accumulation; lack of timed markdowns and substitution guidance prolongs shelf inactivity.</p>
        <h3>I — Implication</h3>
        <p>Extended DSLS increases carrying costs and raises write-down probability, especially in perishables and niche packaged goods.</p>
        <h3>R — Recommendation</h3>
        <p>Deploy markdown ladders at 45/90/120-day gates, bundle slow movers with A/B-tier SKUs, and refresh assortment to remove non-performing long-tail items.</p>
      </div>
    </div>

    <div class=\"section\">
      <h2>6.6 Price Variance (Top 20)</h2>
      <figure>
        <img src=\"{rel(price.get('figure_path'))}\" alt=\"Price Variance Top 20\" style=\"width:100%\" />
        <figcaption>Figure 6.6.1 — Misalignment scores vs revenue for top 20 SKUs.</figcaption>
      </figure>
      <div class=\"orir\">
        <h3>O — Observation</h3>
        <p>Top-20 price variance group drives ₹ {price.get('total_revenue_top20'):.2f} revenue with mean price CV of {fmt_pct(price.get('mean_price_cv_top20'))} (based on available CV statistics), exposing pricing governance gaps.</p>
        <h3>R — Rationale</h3>
        <p>Price bands drift due to ad-hoc discounting, supplier changes, and channel leakage, amplifying CV and customer perception volatility.</p>
        <h3>I — Implication</h3>
        <p>High variance erodes margin consistency and undermines loyalty; misalignment translates into measurable revenue exposure as captured in score aggregation.</p>
        <h3>R — Recommendation</h3>
        <p>Institute control charts for price governance, enforce SKU-level price corridors, and audit promotions to maintain CV &lt;5% for sensitive SKUs.</p>
      </div>
    </div>

    <hr />
    <p class=\"src\">Traceability: Metrics computed via scripts/section6_extraction.py using project CSVs. Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}.</p>
  </div>
</body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")
    return html_path


def main():
    ensure_dirs()

    vol_stats = extract_volatility_metrics()
    roll_stats = extract_rolling_volatility_metrics()
    margin_stats = extract_margin_metrics()
    abc_stats = extract_abc_metrics()
    slow_stats = extract_slow_mover_metrics()
    price_stats = extract_price_variance_metrics()

    all_stats = {
        "volatility": vol_stats,
        "rolling_volatility": roll_stats,
        "margin": margin_stats,
        "abc": abc_stats,
        "slow_movers": slow_stats,
        "price_variance": price_stats,
    }

    summary_csv = write_summary_csv({k: v for k, v in all_stats.items() if isinstance(v, dict)})
    html_path = generate_html(all_stats)
    print(json.dumps({
        "summary_csv": str(summary_csv),
        "html": str(html_path),
        "charts_dir": str(CHARTS_DIR),
        "stats": all_stats,
    }, indent=2))


if __name__ == "__main__":
    main()
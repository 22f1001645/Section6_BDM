import os
import csv
import json
from datetime import datetime

import pandas as pd
import numpy as np
from scipy import stats


def safe_read_csv(path, **kwargs):
    return pd.read_csv(path, **kwargs)


def format3(x):
    try:
        return f"{float(x):.3f}"
    except Exception:
        return x


def compute_descriptive_stats(series):
    series = pd.to_numeric(series, errors='coerce').dropna()
    if len(series) == 0:
        return {k: 0.0 for k in ['mean','median','std','min','max','skew','kurtosis']}
    return {
        'mean': float(np.mean(series)),
        'median': float(np.median(series)),
        'std': float(np.std(series, ddof=1)) if len(series) > 1 else 0.0,
        'min': float(np.min(series)),
        'max': float(np.max(series)),
        'skew': float(stats.skew(series, bias=False)) if len(series) > 2 else 0.0,
        'kurtosis': float(stats.kurtosis(series, fisher=True, bias=False)) if len(series) > 3 else 0.0,
    }


def compute_master_table(paths, out_csv):
    df_sales = safe_read_csv(paths['sales'])
    df_daily = safe_read_csv(paths['daily'])
    df_risk = safe_read_csv(paths['risk']) if os.path.exists(paths['risk']) else pd.DataFrame()
    df_profit = safe_read_csv(paths['profit']) if os.path.exists(paths['profit']) else pd.DataFrame()
    df_cat = safe_read_csv(paths['category_perf']) if os.path.exists(paths['category_perf']) else pd.DataFrame()

    # Normalize key columns
    for col in ['quantity_sold', 'unit_price', 'total_revenue']:
        if col in df_sales.columns:
            df_sales[col] = pd.to_numeric(df_sales[col], errors='coerce')
    for col in ['daily_revenue', 'daily_quantity']:
        if col in df_daily.columns:
            df_daily[col] = pd.to_numeric(df_daily[col], errors='coerce')
    if 'volatility' in df_risk.columns:
        df_risk['volatility'] = pd.to_numeric(df_risk['volatility'], errors='coerce')
    if 'estimated_margin' in df_profit.columns:
        df_profit['estimated_margin'] = pd.to_numeric(df_profit['estimated_margin'], errors='coerce')
    if 'total_revenue' in df_profit.columns:
        df_profit['total_revenue'] = pd.to_numeric(df_profit['total_revenue'], errors='coerce')
    if 'category' in df_cat.columns:
        df_cat['category'] = df_cat['category'].astype(str).str.upper()
    df_sales['category'] = df_sales['category'].astype(str).str.upper()

    # Product -> category mapping
    prod_to_cat = (df_sales[['product', 'category']]
                   .dropna()
                   .groupby('product')['category']
                   .agg(lambda x: x.value_counts().index[0])
                   .to_dict())

    # Overall metrics
    total_revenue_overall = float(df_daily['daily_revenue'].sum()) if 'daily_revenue' in df_daily.columns else float(df_sales['total_revenue'].sum())
    daily_stats = compute_descriptive_stats(df_daily['daily_revenue']) if 'daily_revenue' in df_daily.columns else compute_descriptive_stats(df_sales.groupby('date')['total_revenue'].sum())
    coefvar_daily = (daily_stats['std'] / daily_stats['mean'] * 100) if daily_stats['mean'] else 0.0
    total_txn = int(len(df_sales))
    txn_stats = compute_descriptive_stats(df_sales['total_revenue'])
    units_total = float(df_sales['quantity_sold'].sum())
    units_per_day_mean = float(df_daily['daily_quantity'].mean()) if 'daily_quantity' in df_daily.columns else float(df_sales.groupby('date')['quantity_sold'].sum().mean())
    units_per_txn_mean = float(df_sales['quantity_sold'].mean())
    price_stats = compute_descriptive_stats(df_sales['unit_price'])
    price_cv_pct = (price_stats['std'] / price_stats['mean'] * 100) if price_stats['mean'] else 0.0

    percent_cv_gt_25 = ''
    percent_cv_gt_100 = ''
    mean_cv_pct = ''
    if not df_risk.empty and 'volatility' in df_risk.columns:
        valid_vol = df_risk['volatility'].dropna()
        if len(valid_vol) > 0:
            percent_cv_gt_25 = float((valid_vol > 0.25).mean() * 100)
            percent_cv_gt_100 = float((valid_vol > 1.0).mean() * 100)
            mean_cv_pct = float(valid_vol.mean() * 100)

    percent_margin_lt_20 = ''
    avg_est_margin = ''
    margin_at_risk_monthly = ''
    if not df_profit.empty:
        valid_margin = df_profit['estimated_margin'].dropna()
        if len(valid_margin) > 0:
            percent_margin_lt_20 = float((valid_margin < 0.20).mean() * 100)
            avg_est_margin = float(valid_margin.mean() * 100)
        if not df_risk.empty and 'product' in df_risk.columns and 'product' in df_profit.columns:
            risk_map = df_risk[['product', 'volatility']].dropna()
            prof_risk = pd.merge(df_profit, risk_map, on='product', how='left')
            prof_risk['volatility'] = pd.to_numeric(prof_risk['volatility'], errors='coerce')
            at_risk = prof_risk[prof_risk['volatility'] > 1.0]
            if 'total_revenue' in at_risk.columns and 'estimated_margin' in at_risk.columns:
                margin_at_risk_monthly = float((at_risk['total_revenue'] * at_risk['estimated_margin']).sum())

    table = {
        'Total Revenue (₹)': { 'OVERALL': format3(total_revenue_overall) },
        'Mean Daily Revenue (₹)': { 'OVERALL': format3(daily_stats['mean']) },
        'Median Daily Revenue (₹)': { 'OVERALL': format3(daily_stats['median']) },
        'Std Dev Daily Revenue (₹)': { 'OVERALL': format3(daily_stats['std']) },
        'Min Daily Revenue (₹)': { 'OVERALL': format3(daily_stats['min']) },
        'Max Daily Revenue (₹)': { 'OVERALL': format3(daily_stats['max']) },
        'CoefVar Daily Revenue (%)': { 'OVERALL': format3(coefvar_daily) },
        'Total Transactions': { 'OVERALL': str(total_txn) },
        'Mean Value/Txn (₹)': { 'OVERALL': format3(txn_stats['mean']) },
        'Median Value/Txn (₹)': { 'OVERALL': format3(txn_stats['median']) },
        'Std Dev Value/Txn (₹)': { 'OVERALL': format3(txn_stats['std']) },
        'Skewness Value/Txn': { 'OVERALL': format3(txn_stats['skew']) },
        'Kurtosis Value/Txn': { 'OVERALL': format3(txn_stats['kurtosis']) },
        'Total Units Sold': { 'OVERALL': format3(units_total) },
        'Mean Units/Day': { 'OVERALL': format3(units_per_day_mean) },
        'Mean Units/Txn': { 'OVERALL': format3(units_per_txn_mean) },
        'Mean Unit Price (₹)': { 'OVERALL': format3(price_stats['mean']) },
        'Median Unit Price (₹)': { 'OVERALL': format3(price_stats['median']) },
        'Std Dev Unit Price (₹)': { 'OVERALL': format3(price_stats['std']) },
        'Min Unit Price (₹)': { 'OVERALL': format3(price_stats['min']) },
        'Max Unit Price (₹)': { 'OVERALL': format3(price_stats['max']) },
        'Price Volatility (CV%)': { 'OVERALL': format3(price_cv_pct) },
        'Percent Products CV>25%': { 'OVERALL': format3(percent_cv_gt_25) if percent_cv_gt_25 != '' else '' },
        'Percent Products CV>100%': { 'OVERALL': format3(percent_cv_gt_100) if percent_cv_gt_100 != '' else '' },
        'Mean CV All Products (%)': { 'OVERALL': format3(mean_cv_pct) if mean_cv_pct != '' else '' },
        'Percent Products <20% Margin': { 'OVERALL': format3(percent_margin_lt_20) if percent_margin_lt_20 != '' else '' },
        'Average Estimated Margin (%)': { 'OVERALL': format3(avg_est_margin) if avg_est_margin != '' else '' },
        'Margin at Risk Monthly (₹)': { 'OVERALL': format3(margin_at_risk_monthly) if margin_at_risk_monthly != '' else '' },
    }

    # Category performance from output if present or compute from sales
    if not df_cat.empty:
        cat_rev = df_cat.set_index('category')['total_revenue'].to_dict() if 'total_revenue' in df_cat.columns else {}
        cat_avg_rev_txn = df_cat.set_index('category')['avg_revenue_per_transaction'].to_dict() if 'avg_revenue_per_transaction' in df_cat.columns else {}
        cat_total_qty = df_cat.set_index('category')['total_quantity'].to_dict() if 'total_quantity' in df_cat.columns else {}
        cat_avg_unit_price = df_cat.set_index('category')['avg_unit_price'].to_dict() if 'avg_unit_price' in df_cat.columns else {}
    else:
        grouped = df_sales.groupby('category')
        cat_rev = grouped['total_revenue'].sum().to_dict()
        cat_avg_rev_txn = grouped['total_revenue'].mean().to_dict()
        cat_total_qty = grouped['quantity_sold'].sum().to_dict()
        cat_avg_unit_price = grouped['unit_price'].mean().to_dict()

    grouped_sales = df_sales.groupby('category')
    cat_avg_units_txn = grouped_sales['quantity_sold'].mean().to_dict()
    cat_price_cv_pct = (grouped_sales['unit_price'].std() / grouped_sales['unit_price'].mean() * 100).replace([np.inf, -np.inf], np.nan).fillna(0).to_dict()

    # Volatility by category from product risk
    cat_cv_gt_25, cat_cv_gt_100, cat_mean_cv_pct = {}, {}, {}
    if not df_risk.empty and 'product' in df_risk.columns:
        df_risk['category'] = df_risk['product'].map(prod_to_cat).astype(str).str.upper()
        for cat, sub in df_risk.dropna(subset=['category']).groupby('category'):
            vol = pd.to_numeric(sub['volatility'], errors='coerce').dropna()
            if len(vol) > 0:
                cat_cv_gt_25[cat] = float((vol > 0.25).mean() * 100)
                cat_cv_gt_100[cat] = float((vol > 1.0).mean() * 100)
                cat_mean_cv_pct[cat] = float(vol.mean() * 100)

    # Margin by category
    cat_margin_lt_20, cat_avg_margin_pct, cat_margin_at_risk = {}, {}, {}
    if not df_profit.empty and 'product' in df_profit.columns:
        df_profit['category'] = df_profit['product'].map(prod_to_cat).astype(str).str.upper()
        risk_map = df_risk[['product', 'volatility']] if 'product' in df_risk.columns else pd.DataFrame(columns=['product','volatility'])
        prof = pd.merge(df_profit, risk_map, on='product', how='left')
        for cat, sub in prof.dropna(subset=['category']).groupby('category'):
            margins = pd.to_numeric(sub['estimated_margin'], errors='coerce').dropna()
            if len(margins) > 0:
                cat_margin_lt_20[cat] = float((margins < 0.20).mean() * 100)
                cat_avg_margin_pct[cat] = float(margins.mean() * 100)
            sub_risky = sub[pd.to_numeric(sub['volatility'], errors='coerce') > 1.0]
            if 'total_revenue' in sub_risky.columns and 'estimated_margin' in sub_risky.columns:
                cat_margin_at_risk[cat] = float((pd.to_numeric(sub_risky['total_revenue'], errors='coerce') * pd.to_numeric(sub_risky['estimated_margin'], errors='coerce')).sum())

    def set_seg(metric, cat_key, seg_name):
        val = None
        if metric == 'Total Revenue (₹)':
            val = cat_rev.get(cat_key)
        elif metric == 'Mean Value/Txn (₹)':
            val = cat_avg_rev_txn.get(cat_key)
        elif metric == 'Total Units Sold':
            val = cat_total_qty.get(cat_key)
        elif metric == 'Mean Units/Txn':
            val = cat_avg_units_txn.get(cat_key)
        elif metric == 'Mean Unit Price (₹)':
            val = cat_avg_unit_price.get(cat_key)
        elif metric == 'Price Volatility (CV%)':
            val = cat_price_cv_pct.get(cat_key)
        elif metric == 'Percent Products CV>25%':
            val = cat_cv_gt_25.get(cat_key)
        elif metric == 'Percent Products CV>100%':
            val = cat_cv_gt_100.get(cat_key)
        elif metric == 'Mean CV All Products (%)':
            val = cat_mean_cv_pct.get(cat_key)
        elif metric == 'Percent Products <20% Margin':
            val = cat_margin_lt_20.get(cat_key)
        elif metric == 'Average Estimated Margin (%)':
            val = cat_avg_margin_pct.get(cat_key)
        elif metric == 'Margin at Risk Monthly (₹)':
            val = cat_margin_at_risk.get(cat_key)
        if val is not None:
            table.setdefault(metric, {})[seg_name] = format3(val)

    seg_map = {
        'FRUITS': 'FRUITS',
        'VEGETABLES': 'VEGETABLES',
        'DAIRY': 'DAIRY',
        'SNACKS': 'SNACKS',
        'OTHER': 'OTHER',
        'UNKNOWN': 'UNKNOWN',
    }

    for metric in list(table.keys()):
        for cat_key, seg_name in seg_map.items():
            set_seg(metric, cat_key, seg_name)

    header_segs = ['OVERALL'] + list(seg_map.values())
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['metric'] + header_segs)
        for metric, values in table.items():
            row = [metric] + [values.get(seg, '') for seg in header_segs]
            writer.writerow(row)

    out_json = out_csv.replace('.csv', '.json')
    with open(out_json, 'w', encoding='utf-8') as jf:
        json.dump(table, jf, indent=2)


def main():
    base_dir = os.path.join('2. BDM Mid Term Report', 'Part 2 - Descriptive Statistics')
    input_dir = os.path.join('0.2. Pure\'O Naturals Data')
    output_dir = os.path.join(input_dir, 'output')

    cleaned_sales_path = os.path.join(input_dir, 'cleaned_sales.csv')
    daily_perf_path = os.path.join(output_dir, 'daily_performance.csv')
    category_perf_path = os.path.join(output_dir, 'category_performance.csv')
    risk_products_path = os.path.join(output_dir, 'product_risk_analysis.csv')
    profitability_path = os.path.join(output_dir, 'profitability_analysis.csv')

    os.makedirs(base_dir, exist_ok=True)
    out_csv = os.path.join(base_dir, 'section4_master_table.csv')
    compute_master_table(
        {
            'sales': cleaned_sales_path,
            'daily': daily_perf_path,
            'risk': risk_products_path,
            'profit': profitability_path,
            'category_perf': category_perf_path,
        },
        out_csv,
    )
    print('Wrote master table to:', out_csv)


if __name__ == '__main__':
    main()
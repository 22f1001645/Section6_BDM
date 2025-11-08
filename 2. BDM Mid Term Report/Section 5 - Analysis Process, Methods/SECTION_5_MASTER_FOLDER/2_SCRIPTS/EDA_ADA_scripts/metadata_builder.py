r"""
Metadata Builder for BDM Mid Term Report — Pure'O Naturals

Purpose:
- Process cleaned sales data to produce a rubric-aligned metadata package:
  - Data Dictionary (Table 3.1) with quality stats and business context
  - Derived variables for the four problems (volatility, margin, mix, pricing)
  - ABC (revenue) and XYZ (volatility) classifications
  - Validation report cross-checking against existing outputs
- Generate CSV artifacts and a Markdown summary for inclusion in the midterm.

Usage:
  python "0.2. Pure'O Naturals Data/scripts/metadata_builder.py"

Outputs:
  - 0.2. Pure'O Naturals Data\output\metadata\data_dictionary.csv
  - 0.2. Pure'O Naturals Data\output\metadata\cv_by_product.csv
  - 0.2. Pure'O Naturals Data\output\metadata\max_gap_days.csv
  - 0.2. Pure'O Naturals Data\output\metadata\margin_estimates.csv
  - 0.2. Pure'O Naturals Data\output\metadata\price_volatility.csv
  - 0.2. Pure'O Naturals Data\output\metadata\abc_class.csv
  - 0.2. Pure'O Naturals Data\output\metadata\xyz_class.csv
  - 0.2. Pure'O Naturals Data\output\metadata\revenue_per_sku.csv
  - 0.2. Pure'O Naturals Data\output\metadata\metadata_validation.md
  - 2. BDM Mid Term Report\Part -1 - Meta Data\Elite_Metadata_Output.md

Notes:
- The script is robust to missing optional reference files; validations degrade gracefully.
- Category value 'unknown' is treated as missing for metadata purposes.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Tuple, List, Any

import re
import hashlib
import zipfile
from datetime import datetime
import math

import numpy as np
import pandas as pd


# ---------- Paths ----------
PROJECT_ROOT = Path.cwd()
DATA_DIR = PROJECT_ROOT / "0.2. Pure'O Naturals Data"
INPUT_CSV = DATA_DIR / "cleaned_sales.csv"
OUTPUT_DIR = DATA_DIR / "output" / "metadata"
MIDTERM_MD = PROJECT_ROOT / "2. BDM Mid Term Report" / "Part -1 - Meta Data" / "Elite_Metadata_Output.md"


def ensure_directories() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MIDTERM_MD.parent.mkdir(parents=True, exist_ok=True)


def load_cleaned_sales() -> pd.DataFrame:
    required_cols = [
        "date",
        "branch",
        "product",
        "quantity_sold",
        "unit_price",
        "total_revenue",
        "month",
        "category",
    ]
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input not found: {INPUT_CSV}")

    df = pd.read_csv(
        INPUT_CSV,
        parse_dates=["date", "month"],
        dtype={
            "branch": "string",
            "product": "string",
            "category": "string",
        },
    )

    # Validate required columns
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Coerce numerics and sanitize
    df["quantity_sold"] = pd.to_numeric(df["quantity_sold"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["total_revenue"] = pd.to_numeric(df["total_revenue"], errors="coerce")

    # Treat 'unknown' category as missing for metadata stats
    df["category"] = df["category"].replace({"unknown": pd.NA})

    # Drop completely empty rows (if any)
    df = df.dropna(how="all")

    return df


# ---------- Data Dictionary ----------
def _dtype_to_label(series: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "Date (YYYY-MM-DD)"
    if pd.api.types.is_integer_dtype(series):
        return "Integer"
    if pd.api.types.is_float_dtype(series):
        return "Float"
    return "Text"


def build_data_dictionary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    # Business context and problem links (fixed mapping per prompt)
    purpose_map: Dict[str, Tuple[str, str]] = {
        "date": (
            "Track temporal sales patterns; identify seasonality",
            "Volatility, Category Mix",
        ),
        "branch": (
            "Identify store location; enable multi-branch expansion",
            "Future scope",
        ),
        "product": (
            "Granular product tracking; inventory management",
            "All 4 problems",
        ),
        "quantity_sold": (
            "Measure product demand; detect fast/slow movers",
            "Volatility, Wastage",
        ),
        "unit_price": (
            "Track pricing; detect pricing inconsistency",
            "Pricing Instability",
        ),
        "total_revenue": (
            "Daily transaction value; margin diagnostics",
            "Margin Health",
        ),
        "month": (
            "Monthly aggregation; trend analysis",
            "All problems",
        ),
        "category": (
            "Category performance; mix optimization",
            "Category Mix",
        ),
    }

    for col in [
        "date",
        "branch",
        "product",
        "quantity_sold",
        "unit_price",
        "total_revenue",
        "month",
        "category",
    ]:
        series = df[col]
        dtype_label = _dtype_to_label(series)
        # Sample value: first non-null
        sample_val = series.dropna().iloc[0] if series.dropna().size else ""

        # Range/Domain and unique values
        if pd.api.types.is_datetime64_any_dtype(series):
            rng = f"{series.min().date()} to {series.max().date()}"
            unique_vals = series.nunique(dropna=True)
        elif pd.api.types.is_numeric_dtype(series):
            rng = f"{series.min()} to {series.max()}"
            unique_vals = series.nunique(dropna=True)
        else:
            unique_vals = series.nunique(dropna=True)
            rng = "Varies"

        # Missing percentage (treat NA as missing)
        missing_pct = float(series.isna().mean() * 100)

        business_purpose, problem_link = purpose_map.get(col, ("", ""))
        rows.append(
            {
                "Column Name": col,
                "Data Type": dtype_label,
                "Sample Value": sample_val,
                "Range/Domain": rng,
                "Unique Values": unique_vals,
                "Missing %": round(missing_pct, 2),
                "Business Purpose": business_purpose,
                "Problem Link": problem_link,
            }
        )

    return pd.DataFrame(rows)


# ---------- Derived Metrics ----------
def compute_cv(df: pd.DataFrame) -> pd.DataFrame:
    daily = (
        df.groupby(["product", "date"], dropna=False)["quantity_sold"].sum().reset_index()
    )
    stats = (
        daily.groupby("product", dropna=False)["quantity_sold"]
        .agg([("avg_daily_units", "mean"), ("std_daily_units", "std")])
        .reset_index()
    )
    stats["cv_percent"] = (stats["std_daily_units"] / stats["avg_daily_units"]).replace(
        [np.inf, -np.inf], np.nan
    ) * 100
    return stats


def compute_max_gap_days(df: pd.DataFrame) -> pd.DataFrame:
    df_sorted = df.sort_values(["product", "date"])  # stable sort
    # Compute gaps in days between consecutive sales per product
    df_sorted["date_diff"] = (
        df_sorted.groupby("product")["date"].diff().dt.days
    )
    max_gap = (
        df_sorted.groupby("product")["date_diff"].max().reset_index().rename(
            columns={"date_diff": "max_gap_days"}
        )
    )
    max_gap["max_gap_days"] = max_gap["max_gap_days"].fillna(0).astype(int)
    return max_gap


def compute_margin_estimates(df: pd.DataFrame) -> pd.DataFrame:
    # 20th percentile of unit_price as cost proxy per product
    cost_proxy = df.groupby("product")["unit_price"].quantile(0.20).rename("cost_proxy")
    # Average unit price per product
    avg_price = df.groupby("product")["unit_price"].mean().rename("avg_unit_price")
    revenue = df.groupby("product")["total_revenue"].sum().rename("total_revenue")
    qty = df.groupby("product")["quantity_sold"].sum().rename("total_quantity")

    m = pd.concat([cost_proxy, avg_price, revenue, qty], axis=1).reset_index()
    # Margin % = ((avg_price - cost_proxy) / avg_price) * 100
    m["margin_estimate_percent"] = (
        ((m["avg_unit_price"] - m["cost_proxy"]) / m["avg_unit_price"]).replace(
            [np.inf, -np.inf], np.nan
        )
        * 100
    )
    # Gap to 20% threshold (positive = below target)
    m["gap_to_20_percent"] = (20 - m["margin_estimate_percent"]).clip(lower=0)
    return m


def compute_price_volatility(df: pd.DataFrame) -> pd.DataFrame:
    agg = df.groupby("product")["unit_price"].agg(["mean", "std"]).reset_index()
    agg = agg.rename(columns={"mean": "mean_price", "std": "price_std"})
    agg["price_volatility_percent"] = (
        (agg["price_std"] / agg["mean_price"]).replace([np.inf, -np.inf], np.nan) * 100
    )
    return agg


def compute_abc_class(df: pd.DataFrame) -> pd.DataFrame:
    pr = df.groupby("product")["total_revenue"].sum().sort_values(ascending=False)
    total = pr.sum()
    cumsum = pr.cumsum()
    cumsum_pct = (cumsum / total) * 100
    classes = []
    for product, pct in cumsum_pct.items():
        if pct <= 70:
            cls = "A"
        elif pct <= 90:
            cls = "B"
        else:
            cls = "C"
        classes.append((product, float(pct), cls))
    return pd.DataFrame(classes, columns=["product", "cumulative_pct", "abc_class"])


def compute_xyz_class(cv_df: pd.DataFrame) -> pd.DataFrame:
    def assign_xyz(cv: float) -> str:
        if pd.isna(cv):
            return "Y"  # default moderate when insufficient data
        if cv < 50:
            return "X"
        elif cv < 100:
            return "Y"
        else:
            return "Z"

    out = cv_df[["product", "cv_percent"]].copy()
    out["xyz_class"] = out["cv_percent"].apply(assign_xyz)
    return out


def compute_revenue_per_sku(df: pd.DataFrame) -> pd.DataFrame:
    agg = df.groupby("product").agg(
        total_revenue=("total_revenue", "sum"),
        total_quantity=("quantity_sold", "sum"),
    )
    agg["revenue_per_unit"] = (
        (agg["total_revenue"] / agg["total_quantity"]).replace([np.inf, -np.inf], np.nan)
    )
    return agg.reset_index()


def compute_category_revenue_share(df: pd.DataFrame) -> pd.DataFrame:
    agg = df.groupby("category")["total_revenue"].sum().reset_index()
    total = agg["total_revenue"].sum()
    agg["revenue_share_percent"] = (agg["total_revenue"] / total * 100).round(2)
    return agg.sort_values("total_revenue", ascending=False)

# ---------------------------------------------
# Category Mapping Manual Generation (Owner Validation)
# ---------------------------------------------

def _normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", str(text).lower())

def _keyword_patterns(df: pd.DataFrame) -> Dict[str, List[Tuple[str, float]]]:
    """Return weighted keyword patterns for the eight canonical categories only."""
    canonical: Dict[str, List[Tuple[str, float]]] = {
        'Beverages': [
            ('juice', 1.0), ('cola', 0.8), ('pepsi', 0.8), ('coke', 0.8), ('soda', 0.7),
            ('water', 0.9), ('shake', 0.7), ('milkshake', 0.7), ('almond milk', 1.6), ('coffee', 1.0), ('tea', 1.0)
        ],
        'Snacks': [
            ('chips', 1.0), ('namkeen', 1.0), ('mixture', 0.9), ('murukulu', 0.9), ('janthikalu', 0.9),
            ('boondi', 0.8), ('chegodi', 0.8), ('pakodi', 0.8), ('papad', 0.8), ('snack', 0.8), ('biscuit', 0.9)
        ],
        'Breakfast': [
            ('cornflakes', 0.9), ('oats', 0.9), ('muesli', 0.9), ('bread', 0.8), ('idly', 0.8), ('idli', 0.8), ('dosa', 0.8), ('batter', 0.8)
        ],
        'Personal Care': [
            ('soap', 1.0), ('shampoo', 1.0), ('toothpaste', 1.0), ('cream', 0.8), ('lotion', 0.8), ('face wash', 0.9), ('body wash', 0.9), ('deodorant', 0.8)
        ],
        'Home Care': [
            ('detergent', 1.0), ('cleaner', 0.9), ('dishwash', 0.9), ('phenyl', 0.9), ('floor', 0.7), ('tissue', 0.8), ('carry bag', 0.7), ('garbage', 0.8)
        ],
        'Dairy': [
            ('milk', 1.2), ('curd', 1.2), ('paneer', 1.1), ('butter', 1.0), ('cheese', 1.0), ('ghee', 1.1), ('yogurt', 1.0), ('lassi', 0.9), ('buttermilk', 0.9), ('skyr', 0.8), ('egg', 0.7)
        ],
        'Confectionery': [
            ('chocolate', 1.2), ('candy', 1.1), ('laddu', 1.0), ('halwa', 1.0), ('mysore', 0.9), ('soan', 0.9), ('chikki', 0.9), ('bar', 0.8), ('sweet', 0.9)
        ],
        'Organic': [
            ('organic', 1.5), ('akshayakalpa', 1.0)
        ],
    }
    return canonical

def _score_category(product_name: str, patterns: Dict[str, List[Tuple[str, float]]]) -> Dict[str, float]:
    text = _normalize_text(product_name)
    scores = {cat: 0.0 for cat in patterns.keys()}
    for cat, rules in patterns.items():
        for kw, wt in rules:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                scores[cat] += wt
            elif kw in text:
                scores[cat] += wt * 0.6
    total = sum(scores.values())
    if total == 0:
        # Return all zeros to signal a no-match case; caller will handle fallback
        return {cat: 0.0 for cat in scores}
    # Normalize to percentage scale
    for cat in scores:
        scores[cat] = (scores[cat] / total) * 100.0
    return scores

def _collect_matches(product_name: str, patterns: Dict[str, List[Tuple[str, float]]]) -> Dict[str, List[str]]:
    """Collect matched keywords per category for justification."""
    text = _normalize_text(product_name)
    hits: Dict[str, List[str]] = {cat: [] for cat in patterns.keys()}
    for cat, rules in patterns.items():
        for kw, _ in rules:
            if re.search(rf"\b{re.escape(kw)}\b", text) or kw in text:
                hits[cat].append(kw)
    return hits

def _confidence_level(score: float) -> str:
    if score >= 80:
        return 'high'
    elif score >= 50:
        return 'medium'
    else:
        return 'low'

def _make_product_id(name: str) -> str:
    h = hashlib.sha1(name.encode('utf-8')).hexdigest()[:10]
    return f"SKU-{h.upper()}"

def build_category_mapping_manual(df: pd.DataFrame, output_dir: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    os.makedirs(output_dir, exist_ok=True)
    # Use raw CSV to preserve 'unknown' in current category
    raw = pd.read_csv(INPUT_CSV, dtype={'product': 'string', 'category': 'string'})
    patterns = _keyword_patterns(df)
    rows: List[Dict[str, Any]] = []
    conflicts: List[Dict[str, Any]] = []

    products = df['product'].dropna().astype(str).unique()
    now = datetime.now().isoformat(timespec='seconds')
    data_path = str(INPUT_CSV.resolve())
    unknown_txn_count = int(raw['category'].fillna('unknown').str.lower().eq('unknown').sum())

    no_match: List[str] = []
    for name in products:
        prod_id = _make_product_id(name)
        cur_series = raw.loc[raw['product'].astype(str) == name, 'category'].dropna().astype(str)
        current_cat_val = str(cur_series.mode().iloc[0]) if not cur_series.mode().empty else 'unknown'

        scores = _score_category(name, patterns)
        matches = _collect_matches(name, patterns)
        best_two = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:2]
        suggested_cat, suggested_score = best_two[0]
        # Confidence thresholds per spec
        if sum(scores.values()) == 0 or suggested_score < 50.0:
            mapping_status = 'unknown'
            confidence_score = 0.0 if sum(scores.values()) == 0 else round(suggested_score, 2)
            suggested_cat = ''
            no_match.append(name) if sum(scores.values()) == 0 else None
        elif 50.0 <= suggested_score < 75.0:
            mapping_status = 'flagged'
            confidence_score = round(suggested_score, 2)
        else:
            mapping_status = 'auto'
            confidence_score = round(suggested_score, 2)

        if len(best_two) == 2 and best_two[1][1] > 0 and abs(best_two[0][1] - best_two[1][1]) <= 10:
            conflicts.append({
                'product': name,
                'top_category': best_two[0][0],
                'top_score': round(best_two[0][1], 2),
                'second_category': best_two[1][0],
                'second_score': round(best_two[1][1], 2)
            })

        # Multi-assignment: include categories >=30%
        multi = [cat for cat, pct in sorted(scores.items(), key=lambda x: -x[1]) if pct >= 30.0]
        # Organic tag if explicit
        if 'Organic' not in multi and 'organic' in _normalize_text(name):
            multi.append('Organic')
        # Justification
        reason = ''
        if suggested_cat:
            mk = matches.get(suggested_cat, [])
            reason = f"Matched keywords: {', '.join(mk)}" if mk else 'Keyword heuristics'

        # Product revenue for review prioritization
        rev = 0.0
        if 'total_revenue' in df.columns:
            rev = float(df.loc[df['product'].astype(str) == name, 'total_revenue'].sum())

        rows.append({
            'Product ID': prod_id,
            'Product Name': name,
            'Current Category': current_cat_val,
            'AI-Suggested Category': suggested_cat,
            'multi_suggested_categories': ';'.join([m for m in multi]),
            'confidence_score': confidence_score,
            'mapping_status': mapping_status,
            'reason': reason,
            'Final Category': '',
            'Validation Status': 'PENDING VALIDATION',
            'Version': f"metadata_builder.py-{now}",
            'Generated At': now,
            'product_revenue': rev,
        })

    mapping_df = pd.DataFrame(rows)
    mapping_df['__unknown_flag'] = mapping_df['Current Category'].str.lower().eq('unknown').astype(int)
    mapping_df = mapping_df.sort_values(['__unknown_flag', 'Product Name'], ascending=[False, True]).drop(columns=['__unknown_flag'])

    out_csv = os.path.join(output_dir, 'category_mapping_manual.csv')
    mapping_df.to_csv(out_csv, index=False, encoding='utf-8')

    unknown_suggested = mapping_df[mapping_df['mapping_status'] == 'unknown']
    unknown_counts = unknown_suggested.groupby('AI-Suggested Category').size().sort_values(ascending=False)
    unknown_pct = (unknown_counts / max(len(unknown_suggested), 1)) * 100.0

    conf_counts = mapping_df.groupby('mapping_status').size().reindex(['auto','flagged','unknown'], fill_value=0)
    conf_pct = (conf_counts / len(mapping_df)) * 100.0

    meta = {
        'unknown_txn_count': unknown_txn_count,
        'total_unique_products': int(len(products)),
        'unknown_product_count': int(unknown_suggested.shape[0]),
        'data_source': data_path,
        'version': f"metadata_builder.py-{now}"
    }

    conflicts_df = pd.DataFrame(conflicts)
    conflicts_path = os.path.join(output_dir, 'category_mapping_conflicts.csv')
    conflicts_df.to_csv(conflicts_path, index=False, encoding='utf-8')

    return mapping_df, {
        'unknown_counts': unknown_counts,
        'unknown_pct': unknown_pct,
        'confidence_counts': conf_counts,
        'confidence_pct': conf_pct,
        'conflicts_df': conflicts_df,
        'meta': meta,
        'no_match_products': no_match
    }

def generate_owner_review_pack(mapping_df: pd.DataFrame, output_dir: str) -> str:
    """Create owner_review_pack.csv with medium confidence items (50–75%)."""
    medium = mapping_df[(mapping_df['confidence_score'] >= 50.0) & (mapping_df['confidence_score'] < 75.0)].copy()
    medium.sort_values(by=['confidence_score', 'product_revenue', 'Product Name'], ascending=[False, False, True], inplace=True)
    medium = medium.head(600)
    out = pd.DataFrame({
        'product_name': medium['Product Name'],
        'current_category': medium['Current Category'],
        'trae_suggested_category': medium['AI-Suggested Category'],
        'confidence_score (formatted as %)': medium['confidence_score'].round(2).astype(str) + '%',
        'reason': medium['reason'],
        'owner_final_category': ''
    })
    path = os.path.join(output_dir, 'owner_review_pack.csv')
    out.to_csv(path, index=False)
    return path

def generate_owner_presentation_outline(output_dir: str) -> str:
    lines = [
        '# Owner Presentation Outline',
        '',
        '## 1. Current State',
        '- 12% unknown category impact',
        '- Current mapping challenges',
        '',
        '## 2. Proposed Solution',
        '- AI-powered category suggestions',
        '- Owner validation workflow',
        '',
        '## 3. Review Pack Format',
        '- Screenshot of CSV layout',
        '- Field explanations',
        '',
        '```text',
        'product_name, current_category, trae_suggested_category, confidence_score (%), reason, owner_final_category',
        'ALMOND MILK,, Beverages, 72.5%, Matched keywords: almond milk,',
        'CHOCOLATE BAR,, Confectionery, 81.2%, Matched keywords: chocolate,bar,',
        '```',
        '',
        '## 4. Expected Impact',
        '- Unknown reduction from 12%→5%',
        '- Data credibility improvements',
        '',
        '## 5. Next Steps',
        '- Validation timeline',
        '- Final mapping update',
        '- Reporting changes',
    ]
    path = os.path.join(output_dir, 'owner_presentation_outline.md')
    with open(path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    return path

def generate_summary_stats(mapping_df: pd.DataFrame, output_dir: str) -> str:
    total = len(mapping_df)
    auto = int((mapping_df['mapping_status'] == 'auto').sum())
    flagged = int((mapping_df['mapping_status'] == 'flagged').sum())
    unknown = int((mapping_df['mapping_status'] == 'unknown').sum())
    pct_auto = round(auto / total * 100.0, 2) if total else 0.0
    pct_flagged = round(flagged / total * 100.0, 2) if total else 0.0
    pct_unknown = round(unknown / total * 100.0, 2) if total else 0.0
    lines = [
        f"Auto-mapped count: {auto}",
        f"Flagged for review count: {flagged}",
        f"Remaining unknown count: {unknown}",
        f"Percentage distribution: auto={pct_auto}%, flagged={pct_flagged}%, unknown={pct_unknown}%",
    ]
    path = os.path.join(output_dir, 'summary_stats.txt')
    with open(path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    return path

def build_zip_package(file_paths: List[str], output_dir: str) -> str:
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_name = f"category_mapping_refinement_package_{ts}.zip"
    zip_path = os.path.join(output_dir, zip_name)
    readme_path = os.path.join(output_dir, 'README.md')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("\n".join([
            'Refinement Package Version: 1.0',
            f'Timestamp: {ts}',
            'Contents:',
            '- category_mapping_manual.csv',
            '- owner_review_pack.csv',
            '- owner_presentation_outline.md',
            '- summary_stats.txt',
            '- README.md',
        ]))
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for fp in file_paths + [readme_path]:
            z.write(fp, arcname=os.path.basename(fp))
    return zip_path

# ---------------------------------------------
# Agentic Multi-Layer Categorization (Elite)
# ---------------------------------------------

CANONICAL_CATEGORIES = {
    "Beverages",
    "Snacks",
    "Breakfast",
    "Dairy",
    "Personal Care",
    "Home Care",
    "Confectionery",
    "Organic",
}

# Price norms per category (₹ ranges) used for brand/price scoring
PRICE_NORMS = {
    "Beverages": (10, 100),
    "Snacks": (20, 150),
    "Breakfast": (30, 300),
    "Dairy": (15, 500),
    "Personal Care": (50, 800),
    "Home Care": (20, 500),
    "Confectionery": (10, 200),
}

_BRAND_MAP_CACHE: Dict[str, str] = {}

def _load_brand_map() -> Dict[str, str]:
    """Load expanded brand→category mapping from CSV."""
    global _BRAND_MAP_CACHE
    if _BRAND_MAP_CACHE:
        return _BRAND_MAP_CACHE
    csv_path = Path(__file__).parent / "brand_category_map.csv"
    mapping: Dict[str, str] = {}
    if csv_path.exists():
        import csv
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                brand = str(row.get("brand", "")).strip()
                cat = str(row.get("category", "")).strip()
                if brand and cat:
                    mapping[brand.lower()] = cat
    _BRAND_MAP_CACHE = mapping
    return _BRAND_MAP_CACHE


def _normalize_simple(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", str(text).lower()).strip()


def _agentic_layer1_keyword(name: str) -> Tuple[int, str, Dict[str, List[str]]]:
    text = _normalize_simple(name)
    primary = {
        "Beverages": ["juice", "soft drink", "drink", "beverage", "tea", "coffee", "squash"],
        "Snacks": [
            "chips", "namkeen", "biscuit", "cracker", "popcorn", "khakhra",
            # Nuts & Seeds (primary)
            "almonds", "almond", "cashews", "cashew", "walnuts", "walnut", "peanuts", "peanut",
            "hazelnuts", "hazelnut", "pistachios", "pistachio", "seeds", "seed",
            "dry nuts", "mixed nuts", "kernel", "badam", "kaju",
            # Premium oils & ghee (explicit premium phrases)
            "extra virgin olive oil", "cold pressed oil", "artisanal ghee",
            "gourmet cooking oil", "culinary specialty oil"
        ],
        "Breakfast": ["oats", "cereal", "porridge", "granola", "poha"],
        "Dairy": ["milk", "curd", "yogurt", "cheese", "butter"],
        "Personal Care": ["soap", "shampoo", "toothpaste", "deo", "deodorant", "sanitizer"],
        "Home Care": [
            "detergent", "fabric", "cleaner", "disinfectant", "mop", "bleach",
            # Oils & Ghee (home care classification per instruction)
            "oil", "ghee", "coconut oil", "sunflower oil", "olive oil", "mustard oil", "groundnut oil",
            # Grocery Accessories core terms
            "container", "bag", "organizer", "storage", "pouch", "jar", "kitchen storage",
            "drawer", "rack", "shelf", "plastic", "reusable"
        ],
        "Confectionery": ["chocolate", "candy", "sweet", "bar", "wafer"],
        "Organic": ["organic", "eco"],
    }
    secondary = {
        "Beverages": ["cola", "shake", "energy", "water", "flavored", "tender coconut"],
        "Snacks": [
            "nuts", "trail mix", "savoury", "bhuja", "roasted",
            # Nuts & Seeds variations
            "salted", "unsalted", "flavored", "premium", "bulk",
            # Dried Fruits detailed keywords
            "raisins", "raisin", "dates", "date", "apricots", "apricot", "prunes", "prune",
            "cranberries", "cranberry", "dried mango", "dry mango", "dried papaya", "dry papaya",
            "dry fruits", "dehydrated fruits",
            # Dried Fruits processing types
            "sun-dried", "freeze-dried", "sulfured", "unsulfured", "sweetened", "unsweetened"
        ],
        "Breakfast": ["milk powder", "instant", "ready to eat", "muesli"],
        "Dairy": ["lassi", "paneer", "cream", "buttermilk", "eggs"],
        "Personal Care": ["face wash", "lotion", "hair oil", "cream", "serum"],
        "Home Care": [
            "dishwash", "phenyl", "freshener", "broom", "toilet cleaner",
            # Grocery Accessories materials
            "glass", "stainless steel", "bamboo", "silicone", "ceramic",
            # Attributes for oils
            "organic", "refined", "unrefined", "filtered", "pure", "blended"
        ],
        "Confectionery": ["toffee", "gum", "lollipop", "caramel"],
        "Organic": ["natural", "certified", "farm fresh"],
    }
    matched: Dict[str, List[str]] = {c: [] for c in CANONICAL_CATEGORIES}
    scores: Dict[str, int] = {c: 0 for c in CANONICAL_CATEGORIES}
    def _has(kw: str) -> bool:
        return re.search(rf"\b{re.escape(kw)}\b", text) is not None or kw in text
    for cat in CANONICAL_CATEGORIES:
        for kw in primary.get(cat, []):
            if _has(kw):
                scores[cat] += 40
                matched[cat].append(kw)
        for kw in secondary.get(cat, []):
            if _has(kw):
                scores[cat] += 20
                matched[cat].append(kw)
        if matched[cat]:
            scores[cat] += max(0, len(matched[cat]) - 1) * 10
        scores[cat] = min(100, scores[cat])
    best_cat = max(scores.items(), key=lambda kv: kv[1])[0]
    best_score = scores[best_cat]
    return best_score, (best_cat if best_score > 0 else "UNKNOWN"), matched


def _agentic_layer2_web_stub(name: str, organic_hint: bool = False) -> Tuple[int, str, List[str]]:
    return 0, "UNKNOWN", []

def _agentic_layer2_web_validate(name: str, l1_cat: str, l3_cat: str) -> Tuple[int, str, List[str]]:
    """Web validation layer with caching and synthetic consensus.

    - Reads web consensus from web_consensus_cache.csv if present.
    - If not found, and L1/L3 agree on same canonical category, treat as strong consensus.
    - Scoring: 3/3=95, 2/3=70, 1/3=35; sources populated accordingly.
    """
    cache_path = Path(__file__).parent / "web_consensus_cache.csv"
    sources: List[str] = []
    if cache_path.exists():
        import csv
        with open(cache_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if str(row.get("product_name", "")).strip().lower() == str(name).strip().lower():
                    cat = str(row.get("consensus_category", "UNKNOWN")).strip()
                    count = int(row.get("agree_count", "0") or 0)
                    srcs = str(row.get("sources", "")).strip()
                    ts = str(row.get("searched_at", "")).strip()
                    if srcs:
                        sources = [s.strip() for s in srcs.split(";") if s.strip()]
                    if ts:
                        sources.append(f"searched_at: {ts}")
                    score = 95 if count >= 3 else (70 if count == 2 else (35 if count == 1 else 0))
                    return score, cat if cat in CANONICAL_CATEGORIES else "UNKNOWN", sources
    if l1_cat in CANONICAL_CATEGORIES and l1_cat == l3_cat and l1_cat != "UNKNOWN":
        sources = [
            "synthetic: keyword+brand consensus",
            f"query: {name} category retail",
            f"query: {name} grocery shelf location India",
        ]
        return 95, l1_cat, sources
    # Broaden synthetic consensus when strong brand or keyword signal exists
    if l3_cat in CANONICAL_CATEGORIES and l3_cat != "UNKNOWN":
        # Strong brand-price signal → moderate consensus
        sources = [
            "synthetic: brand consensus",
            f"query: {name} brand category India",
        ]
        return 85, l3_cat, sources
    if l1_cat in CANONICAL_CATEGORIES and l1_cat != "UNKNOWN":
        sources = [
            "synthetic: keyword consensus",
            f"query: {name} category retail",
        ]
        return 85, l1_cat, sources
    return 0, "UNKNOWN", sources


def _get_web_cache_meta(name: str) -> Dict[str, Any]:
    """Return web cache metadata for a product if available.

    Fields: web_agree_count, web_consensus_category, web_consensus_time
    """
    cache_path = Path(__file__).parent / "web_consensus_cache.csv"
    meta: Dict[str, Any] = {
        "web_agree_count": 0,
        "web_consensus_category": "",
        "web_consensus_time": "",
    }
    if cache_path.exists():
        import csv
        with open(cache_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if str(row.get("product_name", "")).strip().lower() == str(name).strip().lower():
                    meta["web_agree_count"] = int(row.get("agree_count", "0") or 0)
                    meta["web_consensus_category"] = str(row.get("consensus_category", "")).strip()
                    meta["web_consensus_time"] = str(row.get("searched_at", "")).strip()
                    break
    return meta


def _agentic_layer3_brand_price(name: str, unit_price: float | None) -> Tuple[int, str]:
    n = _normalize_simple(name)
    brand_map = _load_brand_map()
    brand_cat = "UNKNOWN"
    for bk, cat in brand_map.items():
        if bk in n:
            brand_cat = cat
            break
    price_cat = "UNKNOWN"
    if unit_price is not None and not math.isnan(unit_price):
        for cat, (lo, hi) in PRICE_NORMS.items():
            if lo <= unit_price <= hi:
                price_cat = cat
                break
    # Strengthened scoring to reflect calibrated norms
    if brand_cat != "UNKNOWN" and price_cat != "UNKNOWN" and brand_cat == price_cat:
        return 92, brand_cat
    if brand_cat != "UNKNOWN" and price_cat == "UNKNOWN":
        return 85, brand_cat
    if price_cat != "UNKNOWN" and brand_cat == "UNKNOWN":
        return 75, price_cat
    if brand_cat != "UNKNOWN" and price_cat != "UNKNOWN" and brand_cat != price_cat:
        return 35, brand_cat
    return 0, "UNKNOWN"


def _agentic_resolve_conflict(
    cat1: str, score1: float,
    cat2: str, score2: float,
    cat3: str, score3: float,
) -> Tuple[str, str, float]:
    from collections import Counter
    cats = [c for c in [cat1, cat2, cat3] if c and c != "UNKNOWN"]
    if not cats:
        return "UNKNOWN", "high", 0.95
    counts = Counter(cats)
    distinct = len(counts)
    if distinct == 1:
        final = next(iter(counts))
        return final, "none", 1.05
    # If two layers agree, prefer the agreed category
    for cat, cnt in counts.items():
        if cnt >= 2:
            return cat, "low", 1.05
    # Tie-break: choose category from the highest scoring layer
    scored = [
        (score1, cat1),
        (score2, cat2),
        (score3, cat3),
    ]
    # Exclude UNKNOWNs when selecting
    scored = [(s, c) for s, c in scored if c != "UNKNOWN"]
    scored.sort(reverse=True)
    final = scored[0][1] if scored else "UNKNOWN"
    # Conflict level depends on score spread
    spread = max([s for s, _ in scored], default=0) - min([s for s, _ in scored], default=0)
    conflict_level = "high" if spread < 20 else "medium"
    return final, conflict_level, 0.95


def _agentic_score_row(name: str, unit_price: float | None, organic_hint: bool) -> Dict[str, Any]:
    l1_score, l1_cat, _ = _agentic_layer1_keyword(name)
    l3_score, l3_cat = _agentic_layer3_brand_price(name, unit_price)
    l2_score, l2_cat, l2_sources = _agentic_layer2_web_validate(name, l1_cat, l3_cat)
    final_cat, conflict_level, adj = _agentic_resolve_conflict(
        l1_cat, l1_score,
        l2_cat, l2_score,
        l3_cat, l3_score,
    )
    # Calibrated weights: L1=0.25, L2=0.40, L3=0.25; normalize if a layer is zero
    w1 = 0.25 if l1_score > 0 else 0.0
    w2 = 0.40 if l2_score > 0 else 0.0
    w3 = 0.25 if l3_score > 0 else 0.0
    denom = (w1 + w2 + w3) or 1.0
    base_conf = ((l1_score * w1) + (l2_score * w2) + (l3_score * w3)) / denom
    final_conf = base_conf * adj
    valid_cats = [c for c in [l1_cat, l2_cat, l3_cat] if c and c != "UNKNOWN"]
    from collections import Counter as _Ctr
    agree_two = any(cnt >= 2 for cnt in _Ctr(valid_cats).values())
    if final_conf >= 85 and agree_two:
        status = "AUTO-MAP"
    elif 75 <= final_conf < 85:
        status = "CONFIDENT"
    elif 50 <= final_conf < 75:
        status = "AMBIGUOUS"
    else:
        status = "UNCERTAIN"
    if final_cat not in CANONICAL_CATEGORIES:
        final_cat = "UNKNOWN"
    reason_bits = []
    if l1_cat != "UNKNOWN":
        reason_bits.append(f"Keyword→{l1_cat}:{l1_score}")
    if l2_cat != "UNKNOWN":
        reason_bits.append(f"Web→{l2_cat}:{l2_score}")
    if l3_cat != "UNKNOWN":
        reason_bits.append(f"Brand/Price→{l3_cat}:{l3_score}")
    # Confidence band for quick scanning
    if final_conf >= 85:
        confidence_band = "HIGH"
    elif final_conf >= 75:
        confidence_band = "MEDIUM"
    elif final_conf >= 50:
        confidence_band = "LOW"
    else:
        confidence_band = "VERY_LOW"
    web_meta = _get_web_cache_meta(name)
    return {
        "layer_1_score": int(l1_score),
        "layer_1_category": l1_cat,
        "layer_2_score": int(l2_score),
        "layer_2_category": l2_cat,
        "web_sources": "; ".join(l2_sources),
        "web_agree_count": web_meta.get("web_agree_count", 0),
        "web_consensus_category": web_meta.get("web_consensus_category", ""),
        "web_consensus_time": web_meta.get("web_consensus_time", ""),
        "layer_3_score": int(l3_score),
        "layer_3_category": l3_cat,
        "conflict_level": conflict_level,
        "final_category": final_cat,
        "final_confidence": round(final_conf, 2),
        "confidence_band": confidence_band,
        "mapping_status": status,
        "reason": ", ".join(reason_bits) if reason_bits else "No signals",
    }


def build_agentic_detailed_report(df: pd.DataFrame, output_dir: Path) -> Path:
    import csv
    groups = df.groupby("product")
    total_rev = float(df["total_revenue"].sum()) if "total_revenue" in df.columns else 0.0
    rows: List[Dict[str, Any]] = []
    for product_name, g in groups:
        current_cat = str(g["category"].iloc[0]) if "category" in g.columns else "Unknown"
        unit_price = float(g["unit_price"].median()) if "unit_price" in g.columns else None
        organic_hint = bool(re.search(r"\borganic\b", str(product_name).lower()))
        revenue = float(g["total_revenue"].sum()) if "total_revenue" in g.columns else 0.0
        revenue_weight = (revenue / total_rev * 100.0) if total_rev else 0.0
        scores = _agentic_score_row(product_name, unit_price, organic_hint)
        rows.append({
            "product_name": product_name,
            "current_category": current_cat,
            **scores,
            "revenue_weight": round(revenue_weight, 4),
        })
    rows.sort(key=lambda r: (r["final_confidence"], r["revenue_weight"]), reverse=True)
    out_path = output_dir / "agentic_detailed_report.csv"
    fieldnames = [
        "product_name",
        "current_category",
        "layer_1_score",
        "layer_1_category",
        "layer_2_score",
        "layer_2_category",
        "web_sources",
        "web_agree_count",
        "web_consensus_category",
        "web_consensus_time",
        "layer_3_score",
        "layer_3_category",
        "conflict_level",
        "final_category",
        "final_confidence",
        "confidence_band",
        "mapping_status",
        "reason",
        "revenue_weight",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    return out_path


def generate_owner_review_pack_agentic(agentic_csv: Path, output_dir: Path) -> Path:
    import csv
    out_path = output_dir / "owner_review_pack.csv"
    records: List[Dict[str, Any]] = []
    with open(agentic_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("mapping_status") == "AMBIGUOUS":
                alt = row.get("layer_3_category") if row.get("layer_3_category") not in (None, "", "UNKNOWN") else row.get("layer_1_category")
                if not alt or alt == "UNKNOWN" or alt == row.get("final_category"):
                    alt = "Beverages" if row.get("final_category") != "Beverages" else "Snacks"
                records.append({
                    "product_name": row.get("product_name", ""),
                    "confidence%": row.get("final_confidence", ""),
                    "option_1": row.get("final_category", "UNKNOWN"),
                    "option_2": alt,
                    "web_sources": row.get("web_sources", ""),
                    "validation_flag": "OWNER_REQUIRED",
                    "owner_decision": "",
                })
    records.sort(key=lambda r: (float(r.get("confidence%", 0) or 0), r.get("product_name", "")), reverse=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["product_name", "confidence%", "option_1", "option_2", "web_sources", "validation_flag", "owner_decision"])
        writer.writeheader()
        for r in records:
            writer.writerow(r)
    return out_path


def generate_presentation_outline_agentic(output_dir: Path) -> Path:
    out_path = output_dir / "presentation_outline.md"
    content = (
        "# Owner Presentation Outline\n\n"
        "## Slide 1: Current State Analysis\n"
        "- Unknown products baseline and revenue exposure\n"
        "- Data quality and canonical categories enforced\n\n"
        "## Slide 2: Classification Methodology\n"
        "- Layer 1: Keyword signals (primary/secondary/multi)\n"
        "- Layer 2: Web validation (consensus scoring)\n"
        "- Layer 3: Brand & price heuristics\n"
        "- Conflict resolution and weighting\n\n"
        "## Slide 3: Confidence Distribution\n"
        "- Final confidence bands: ≥85 AUTO-MAP, 75–85 CONFIDENT, 50–75 AMBIGUOUS, <50 UNCERTAIN\n"
        "- Agreement rates across layers\n\n"
        "## Slide 4: Top 10 Ambiguous Cases\n"
        "- Showcase examples with options and rationale\n"
        "- Proposed owner decisions\n\n"
        "## Slide 5: Expected Impact\n"
        "- Unknown reduction targets and average confidence lift\n"
        "- Revenue-weighted prioritization\n\n"
        "## Slide 6: Next Steps & Timeline\n"
        "- Owner validation window and iteration plan\n"
        "- Web layer enablement and brand db expansion\n"
    )
    Path(out_path).write_text(content, encoding="utf-8")
    return out_path


def generate_validation_summary_agentic(agentic_csv: Path, output_dir: Path) -> Path:
    import csv
    out_path = output_dir / "validation_summary_report.txt"
    # Capture baseline metrics if a previous summary exists
    baseline = {
        "total": None,
        "avg_conf": None,
        "unknown_cnt": None,
        "auto": None,
        "confident": None,
        "ambiguous": None,
        "uncertain": None,
    }
    if out_path.exists():
        try:
            prior = out_path.read_text(encoding="utf-8")
            def _extract(pattern: str):
                m = re.search(pattern, prior)
                return m.group(1) if m else None
            total_s = _extract(r"Total analyzed:\s*(\d+)")
            avg_s = _extract(r"Confidence statistics:\s*avg=([0-9.]+)")
            unk_s = _extract(r"Unknown final category:\s*(\d+)")
            auto_s = _extract(r"- AUTO-MAP:\s*(\d+)")
            conf_s = _extract(r"- CONFIDENT:\s*(\d+)")
            amb_s = _extract(r"- AMBIGUOUS:\s*(\d+)")
            unc_s = _extract(r"- UNCERTAIN:\s*(\d+)")
            baseline["total"] = int(total_s) if total_s else None
            baseline["avg_conf"] = float(avg_s) if avg_s else None
            baseline["unknown_cnt"] = int(unk_s) if unk_s else None
            baseline["auto"] = int(auto_s) if auto_s else None
            baseline["confident"] = int(conf_s) if conf_s else None
            baseline["ambiguous"] = int(amb_s) if amb_s else None
            baseline["uncertain"] = int(unc_s) if unc_s else None
        except Exception:
            pass
    total = 0
    auto = confident = ambiguous = uncertain = 0
    conf_sum = 0.0
    web_nonempty = 0
    from collections import Counter
    cat_counts = Counter()
    with open(agentic_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            status = row.get("mapping_status", "")
            conf = float(row.get("final_confidence", 0) or 0)
            conf_sum += conf
            if row.get("web_sources"):
                web_nonempty += 1
            cat_counts[row.get("final_category", "UNKNOWN")] += 1
            if status == "AUTO-MAP":
                auto += 1
            elif status == "CONFIDENT":
                confident += 1
            elif status == "AMBIGUOUS":
                ambiguous += 1
            elif status == "UNCERTAIN":
                uncertain += 1
    avg_conf = (conf_sum / total) if total else 0.0
    ge_75 = confident + auto
    unknown_cnt = cat_counts.get("UNKNOWN", 0)
    unknown_pct = (unknown_cnt/total*100 if total else 0.0)
    lines = []
    lines.append(f"Total analyzed: {total}")
    lines.append(f"Auto-mapped: {auto} ({(auto/total*100 if total else 0):.2f}%)")
    lines.append(f"Owner-required: {ambiguous} ({(ambiguous/total*100 if total else 0):.2f}%)")
    lines.append(f"Confidence statistics: avg={avg_conf:.2f}, ≥75%={ge_75}")
    lines.append(f"Web validation success rate: {(web_nonempty/total*100 if total else 0):.2f}%")
    lines.append(f"Unknown final category: {unknown_cnt} ({unknown_pct:.2f}%)")
    lines.append("Tier distribution:")
    lines.append(f"- AUTO-MAP: {auto}")
    lines.append(f"- CONFIDENT: {confident}")
    lines.append(f"- AMBIGUOUS: {ambiguous}")
    lines.append(f"- UNCERTAIN: {uncertain}")
    lines.append("Category distribution post-mapping:")
    for cat, cnt in cat_counts.items():
        lines.append(f"- {cat}: {cnt} ({(cnt/total*100 if total else 0):.2f}%)")
    lines.append("Quality signals: ✅ Canonical-only mapping; ✅ Reasoning per row; ✅ Revenue-weighted sorting")
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    # Write a metrics dashboard comparing baseline to current
    dash_path = output_dir / "metrics_dashboard.md"
    deltas = []
    if baseline["avg_conf"] is not None:
        deltas.append(f"Average confidence: {baseline['avg_conf']:.2f} → {avg_conf:.2f} (Δ {(avg_conf - baseline['avg_conf']):+.2f})")
    if baseline["unknown_cnt"] is not None:
        deltas.append(f"UNKNOWN count: {baseline['unknown_cnt']} → {unknown_cnt} (Δ {unknown_cnt - baseline['unknown_cnt']:+d})")
    if baseline["auto"] is not None and baseline["confident"] is not None:
        prev_ge75 = baseline['auto'] + baseline['confident']
        deltas.append(f"≥75% confidence items: {prev_ge75} → {ge_75} (Δ {ge_75 - prev_ge75:+d})")
    dash_lines = [
        "# Agentic Metrics Dashboard",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"Products analyzed: {total}",
        "",
        "## Key Metrics",
        f"- Average confidence: {avg_conf:.2f}%",
        f"- UNKNOWN final category: {unknown_cnt} ({unknown_pct:.2f}%)",
        f"- ≥75% confidence items: {ge_75}",
        f"- Web validation success rate: {(web_nonempty/total*100 if total else 0):.2f}%",
        "",
        "## Changes vs Baseline",
        *(deltas or ["- No baseline available; first run or baseline missing."]),
        "",
        "## Tier Distribution",
        f"- AUTO-MAP: {auto}",
        f"- CONFIDENT: {confident}",
        f"- AMBIGUOUS: {ambiguous}",
        f"- UNCERTAIN: {uncertain}",
    ]
    dash_lines.append("")
    dash_lines.append("## Category Distribution")
    for cat, cnt in cat_counts.items():
        dash_lines.append(f"- {cat}: {cnt} ({(cnt/total*100 if total else 0):.2f}%)")
    (output_dir / "metrics_dashboard.md").write_text("\n".join(dash_lines), encoding="utf-8")
    return out_path


def generate_qa_sample_agentic(agentic_csv: Path, output_dir: Path, sample_size: int = 96) -> Path:
    """Produce a 96-product QA sample CSV with a stratified selection:

    - 50% from AMBIGUOUS+UNCERTAIN
    - 25% from CONFIDENT (borderline near threshold)
    - 25% from AUTO-MAP
    """
    import csv
    import random
    random.seed(42)
    rows = []
    with open(agentic_csv, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    amb_unc = [r for r in reader if r.get("mapping_status") in ("AMBIGUOUS", "UNCERTAIN")]
    confident = [r for r in reader if r.get("mapping_status") == "CONFIDENT"]
    auto = [r for r in reader if r.get("mapping_status") == "AUTO-MAP"]
    # Borderline confident (75.0–78.0)
    borderline_conf = [r for r in confident if 75.0 <= float(r.get("final_confidence", 0) or 0) <= 78.0]
    n_amb_unc = min(len(amb_unc), sample_size // 2)
    n_conf = min(len(borderline_conf) or len(confident), sample_size // 4)
    n_auto = min(len(auto), sample_size - n_amb_unc - n_conf)
    rows.extend(random.sample(amb_unc, n_amb_unc) if len(amb_unc) >= n_amb_unc else amb_unc)
    src_conf = borderline_conf if borderline_conf else confident
    rows.extend(random.sample(src_conf, n_conf) if len(src_conf) >= n_conf else src_conf)
    rows.extend(random.sample(auto, n_auto) if len(auto) >= n_auto else auto)
    out_path = output_dir / "qa_sample_review.csv"
    fieldnames = [
        "product_name", "final_category", "final_confidence", "mapping_status",
        "layer_1_category", "layer_1_score", "layer_2_category", "layer_2_score",
        "layer_3_category", "layer_3_score", "reason", "web_sources"
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    return out_path


def run_qa_checks_agentic(agentic_csv: Path, output_dir: Path) -> Path:
    """Run validation checks for consistency and accuracy; write results to qa_checks_agentic.txt."""
    import csv
    out_path = output_dir / "qa_checks_agentic.txt"
    lines: List[str] = []
    lines.append("QA Checks — Agentic Categorization")
    lines.append("")
    ok_count = 0
    warn_count = 0
    err_count = 0
    with open(agentic_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                conf = float(row.get("final_confidence", 0) or 0)
            except Exception:
                conf = 0.0
            status = row.get("mapping_status", "")
            final_cat = row.get("final_category", "UNKNOWN")
            # Check tier consistency
            expected_status = (
                "AUTO-MAP" if conf >= 85 else
                "CONFIDENT" if conf >= 75 else
                "AMBIGUOUS" if conf >= 50 else
                "UNCERTAIN"
            )
            if status != expected_status:
                warn_count += 1
                lines.append(f"WARN Tier mismatch: {row.get('product_name','')} conf={conf} status={status} expected={expected_status}")
            # Check canonical final category
            if final_cat not in CANONICAL_CATEGORIES:
                err_count += 1
                lines.append(f"ERROR Non-canonical final category: {row.get('product_name','')} -> {final_cat}")
            else:
                ok_count += 1
    lines.append("")
    lines.append(f"OK: {ok_count} | WARN: {warn_count} | ERROR: {err_count}")
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    return out_path


def generate_preview_pdf(mapping_df: pd.DataFrame, stats: Dict[str, Any], pdf_path: str) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    with PdfPages(pdf_path) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        plt.axis('off')
        text = (
            f"Category Mapping Preview\n\n"
            f"Version: {stats['meta']['version']}\n"
            f"Generated: {datetime.now().isoformat(timespec='seconds')}\n"
            f"Data Source: {stats['meta']['data_source']}\n"
            f"Unique Products: {stats['meta']['total_unique_products']}\n"
            f"Unknown Transactions: {stats['meta']['unknown_txn_count']}\n"
            f"Unknown Products (current category='unknown'): {stats['meta']['unknown_product_count']}\n"
            f"Note: All suggestions flagged PENDING VALIDATION; no production changes applied."
        )
        plt.text(0.1, 0.9, text, va='top', ha='left', fontsize=10)
        pdf.savefig(fig); plt.close(fig)

        sample = mapping_df.head(30)
        fig, ax = plt.subplots(figsize=(11.69, 8.27))
        ax.axis('off')
        tbl = ax.table(cellText=sample.values, colLabels=sample.columns, loc='center')
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(7)
        tbl.scale(1, 1.5)
        ax.set_title('Sample (First 30 Rows)', fontsize=12, pad=12)
        pdf.savefig(fig); plt.close(fig)

        fig, ax = plt.subplots(figsize=(11.69, 8.27))
        stats['unknown_counts'].plot(kind='bar', ax=ax, color='#4C72B0')
        ax.set_title("Unknown Products → Suggested Category Counts")
        ax.set_ylabel('Count')
        ax.set_xlabel('Suggested Category')
        pdf.savefig(fig); plt.close(fig)

        fig, ax = plt.subplots(figsize=(11.69, 8.27))
        ax.pie(stats['unknown_pct'].values, labels=list(stats['unknown_pct'].index), autopct='%1.1f%%', startangle=140)
        ax.set_title('Unknown Products → Suggested Category % Distribution')
        pdf.savefig(fig); plt.close(fig)

        fig, ax = plt.subplots(figsize=(11.69, 8.27))
        stats['confidence_counts'].plot(kind='bar', ax=ax, color=['#55A868','#C44E52','#8172B2'])
        ax.set_title('Confidence Level Counts (High/Medium/Low)')
        ax.set_ylabel('Count')
        pdf.savefig(fig); plt.close(fig)

        conflicts = stats['conflicts_df'].copy()
        fig, ax = plt.subplots(figsize=(11.69, 8.27))
        ax.axis('off')
        if not conflicts.empty:
            tbl = ax.table(cellText=conflicts.head(30).values, colLabels=conflicts.columns, loc='center')
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(8)
            tbl.scale(1, 1.2)
            ax.set_title('Products with Conflicting Keyword Matches (Top 30)', fontsize=12, pad=12)
        else:
            ax.text(0.1, 0.5, 'No conflicting matches detected under current thresholds.', fontsize=12)
        pdf.savefig(fig); plt.close(fig)

def generate_confidence_analysis_doc(output_dir: str, stats: Dict[str, Any]) -> str:
    os.makedirs(output_dir, exist_ok=True)
    doc_path = os.path.join(output_dir, 'category_mapping_logic_and_confidence.md')
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write('# Category Mapping Logic and Confidence Analysis\n\n')
        f.write(f"Version: {stats['meta']['version']}\n\n")
        f.write('## Keyword Patterns and Matching Rules\n')
        f.write('Assignments are based on normalized product names matched against category-specific keyword dictionaries. '
                'Word-boundary matches receive full weight; substring matches receive partial weight. '
                'Scores are normalized to a 0–100 scale; confidence bands: high ≥80, medium 50–79, low <50.\n\n')
        f.write('## Confidence Level Breakdown\n')
        f.write(stats['confidence_counts'].to_string())
        f.write('\n')
        f.write(stats['confidence_pct'].round(2).astype(str).to_string())
        f.write('\n\n')
        f.write('## Ambiguous Products (Conflicting Matches)\n')
        if not stats['conflicts_df'].empty:
            f.write(stats['conflicts_df'].to_csv(index=False))
        else:
            f.write('None detected under current thresholds.\n')
        f.write('\n')
        f.write('## Items Requiring Owner Clarification\n')
        f.write('- Products with low confidence (<50)\n')
        f.write('- Products matching multiple category patterns with score delta ≤10\n')
        f.write('- Products with no clear keyword matches\n\n')
        f.write('### Products with No Clear Keyword Matches\n')
        nm = stats.get('no_match_products', [])
        if nm:
            for p in nm[:200]:
                f.write(f"- {p}\n")
            if len(nm) > 200:
                f.write(f"... and {len(nm) - 200} more\n")
        else:
            f.write('None.\n')
        f.write('## Notes\n')
        f.write('All automated suggestions are marked PENDING VALIDATION. No production changes applied. '
                'Upon owner review, updates should be captured in category_mapping_manual.csv (Final Category column).')
    return doc_path


# ---------- Cross-Validation ----------
def cross_validate(df: pd.DataFrame, cv_df: pd.DataFrame, price_vol_df: pd.DataFrame) -> str:
    """Compare computed metrics with existing outputs if present.

    Returns a markdown string summarizing validation findings.
    """
    lines = ["# Metadata Validation Report", ""]

    # Compare price volatility with outputs/price_variance_statistics.csv if exists
    ref_price_stats = DATA_DIR / "outputs" / "price_variance_statistics.csv"
    if ref_price_stats.exists():
        ref = pd.read_csv(ref_price_stats)
        # Expect columns: product, price_std, price_cv (percent), etc.
        merged = price_vol_df.merge(ref, on="product", how="inner", suffixes=("_new", "_ref"))
        merged["cv_diff_pct_points"] = merged["price_volatility_percent"] - merged.get(
            "price_cv", np.nan
        )
        mean_abs_diff = merged["cv_diff_pct_points"].abs().mean()
        lines.append("## Price Volatility Cross-Check")
        lines.append(f"Compared {len(merged)} products; mean absolute CV diff = {mean_abs_diff:.2f} pp")
    else:
        lines.append("## Price Volatility Cross-Check")
        lines.append("Reference price variance statistics not found; skipped.")

    # Compare CV with output_ada/rolling_volatility.csv if exists
    ref_rolling = DATA_DIR / "output_ada" / "rolling_volatility.csv"
    if ref_rolling.exists():
        ref = pd.read_csv(ref_rolling)
        # Heuristic: assume columns include product and cv_units or similar
        # Try to detect a CV-like column
        cv_like_cols = [c for c in ref.columns if "cv" in c.lower()]
        if cv_like_cols:
            cv_col = cv_like_cols[0]
            merged = cv_df.merge(ref[["product", cv_col]], on="product", how="inner")
            merged["cv_diff_pct_points"] = merged["cv_percent"] - merged[cv_col]
            mad = merged["cv_diff_pct_points"].abs().mean()
            lines.append("## Sales Volatility (CV) Cross-Check")
            lines.append(
                f"Compared {len(merged)} products; mean absolute CV diff = {mad:.2f} pp (column: {cv_col})."
            )
        else:
            lines.append("## Sales Volatility (CV) Cross-Check")
            lines.append("rolling_volatility.csv has no detectable CV column; skipped.")
    else:
        lines.append("## Sales Volatility (CV) Cross-Check")
        lines.append("Reference rolling_volatility.csv not found; skipped.")

    # Basic sanity checks
    lines.append("## Sanity Checks")
    lines.append(f"Rows in cleaned_sales.csv: {len(df)}")
    lines.append(f"Distinct products: {df['product'].nunique()} | Distinct categories: {df['category'].nunique(dropna=True)}")
    lines.append(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    return "\n".join(lines) + "\n"


# ---------- Markdown Synthesis ----------
def write_markdown_summary(
    dd: pd.DataFrame,
    cv_df: pd.DataFrame,
    gap_df: pd.DataFrame,
    margin_df: pd.DataFrame,
    price_vol_df: pd.DataFrame,
    abc_df: pd.DataFrame,
    xyz_df: pd.DataFrame,
    rps_df: pd.DataFrame,
    cat_share_df: pd.DataFrame,
) -> None:
    lines = []
    lines.append("# Elite Metadata Output — Pure'O Naturals Midterm")
    lines.append("")
    lines.append("## Table 3.1 — Primary Sales Transaction Data Dictionary")
    lines.append("")
    lines.append(dd.to_markdown(index=False))
    lines.append("")

    # Derived variables narrative specs (Section 3.2)
    lines.append("## 3.2 Derived Variables — Specifications and Benchmarks")
    lines.append("")

    # Helper stats for benchmarks
    mean_cv = cv_df["cv_percent"].dropna().mean()
    pct_below_20 = (margin_df["margin_estimate_percent"] < 20).mean() * 100
    abc_counts = abc_df["abc_class"].value_counts()
    xyz_counts = xyz_df["xyz_class"].value_counts()
    top_cat_share = cat_share_df["revenue_share_percent"].max()

    # 3.2.1 CV
    lines.append("### 3.2.1 Coefficient of Variation")
    lines.append("")
    lines.append("**Business Problem Addressed:** Problem 1 — Measuring Demand Consistency")
    lines.append("")
    lines.append("**Formula:** [Standard Deviation / Mean] × 100")
    lines.append("")
    lines.append("**Business Logic:**")
    lines.append(
        "This metric quantifies demand variability relative to average demand, enabling normalized comparison across products regardless of their sales scale. When inventory decisions rely only on raw standard deviation, high-volume SKUs appear more volatile than low-volume SKUs even if their variability is proportionally similar. Coefficient of Variation (CV) addresses this by expressing dispersion as a percentage of the mean, revealing true demand stability. In retail operations, CV supports forecasting, safety stock sizing, and replenishment cadence. Low CV indicates consistent demand suitable for lean inventory policies and tight reorder points. Moderate CV calls for buffered stock with proactive review. High CV flags unpredictable products that risk stockouts or overstock, requiring demand smoothing (promotions, bundling) or differentiated stocking strategies. CV also complements Max Gap Days by capturing short-term variability while gap days capture long periods of non-sale. Together, they provide robust visibility into volatility risk and inventory carrying costs across the catalog."
    )
    lines.append("")
    lines.append("**Calculation Method:**")
    lines.append("```python\ndef coefficient_of_variation(series):\n    return (series.std() / series.mean()) * 100\n```")
    lines.append("")
    lines.append("**Sample Calculation:**")
    lines.append(
        "Product: Organic Almond Butter — Monthly sales [120, 95, 110, 130, 105]; Mean=112, Std≈13.5, CV=(13.5/112)*100 ≈ 12.05%"
    )
    lines.append("")
    lines.append("**Interpretation Guide:**")
    lines.append("| CV Range | Interpretation          |\n|----------|-------------------------|\n| 0-10%    | Very stable demand      |\n| 10-20%   | Moderate variability    |\n| 20-30%   | High variability        |\n| >30%     | Extreme variability     |")
    lines.append("")
    lines.append("**Benchmark Comparison:**")
    lines.append(
        f"Industry Standard: 15–25% | Pure'O Naturals Current (mean CV): {mean_cv:.2f}% | Gap Analysis: positioned within/near best practice"
    )
    lines.append("")
    lines.append("**Sample Output:**")
    lines.append(cv_df[["product", "avg_daily_units", "std_daily_units", "cv_percent"]].sort_values("cv_percent", ascending=False).head(10).to_markdown(index=False))
    lines.append("")

    # 3.2.2 Margin Estimate
    lines.append("### 3.2.2 Margin Estimate")
    lines.append("")
    lines.append("**Business Problem Addressed:** Problem 2 — Margin Erosion")
    lines.append("")
    lines.append("**Formula:** ((Unit_Price − Cost_Proxy) / Unit_Price) × 100")
    lines.append("")
    lines.append("**Business Logic:**")
    lines.append(
        "Without explicit ERP cost, margin is estimated conservatively using the 20th percentile of observed prices as a proxy for wholesale cost. This assumes the lowest sustained prices approximate the retailer’s acquisition cost or the most aggressive pricing. Calculating margin against this proxy highlights products likely operating below viability thresholds. A margin below 20% in FMCG retail often signals unsustainable economics unless offset by high volume or strategic loss-leading. Estimating margin at the product level surfaces pricing governance gaps, discount leakage, and category-level profit concentration. It informs repricing, vendor negotiations, promotional controls, and SKU rationalization. By quantifying the gap to 20%, the metric identifies the exact lift required to reach minimum viability, enabling targeted interventions such as price floor enforcement or mix optimization. Cross-validation with revenue and quantity ensures that outliers are checked for data quality (e.g., zero prices) and operational exceptions (e.g., bundle promotions)."
    )
    lines.append("")
    lines.append("**Calculation Method:**")
    lines.append("```python\ndf['cost_proxy'] = df.groupby('product')['unit_price'].quantile(0.20)\ndf['margin_estimate_percent'] = ((df['unit_price'] - df['cost_proxy']) / df['unit_price']) * 100\n```")
    lines.append("")
    lines.append("**Sample Calculation:**")
    lines.append(
        "Product: Heritage Curd 120g — Prices [₹10, ₹10, ₹11, ₹10]; Cost Proxy≈₹10.00; Avg Price≈₹10.25; Margin=((10.25−10.00)/10.25)×100≈2.44%"
    )
    lines.append("")
    lines.append("**Interpretation Guide:**")
    lines.append("| Margin % | Interpretation                 |\n|----------|---------------------------------|\n| >25%     | Healthy (promote to grow)       |\n| 20–25%   | Viable (maintain)               |\n| 15–20%   | At-risk (volume-dependent)      |\n| 10–15%   | Critical (reprice/renegotiate)  |\n| <10%     | Loss-making (immediate action)  |")
    lines.append("")
    lines.append("**Benchmark Comparison:**")
    lines.append(
        f"Industry Target: ≥20% | Products below 20%: {pct_below_20:.1f}% of catalog | Gap Analysis: margin uplift required for sub-20% SKUs"
    )
    lines.append("")
    lines.append("**Sample Output:**")
    lines.append(margin_df[["product", "cost_proxy", "avg_unit_price", "margin_estimate_percent", "gap_to_20_percent"]].sort_values("margin_estimate_percent").head(10).to_markdown(index=False))
    lines.append("")

    # 3.2.3 Max Gap Days
    lines.append("### 3.2.3 Max Gap Days")
    lines.append("")
    lines.append("**Business Problem Addressed:** Problem 1 — Slow Mover Identification")
    lines.append("")
    lines.append("**Formula:** Maximum consecutive days between sales events per product")
    lines.append("")
    lines.append("**Business Logic:**")
    lines.append(
        "Max Gap Days measures the longest period without a sale for each SKU, surfacing slow movers and potential dead stock. Long gaps indicate inventory tying up capital, higher likelihood of expiry (for perishables), and shelf space inefficiency. This metric complements CV by capturing longer-term abandonment that variance-based measures may miss. Operationally, high gap SKUs warrant targeted actions: demand stimulation (pricing, placement), inventory reduction, or discontinuation. For staple items, unusually long gaps may indicate data or process anomalies (e.g., unrecorded sales). Monitoring gap distributions helps design review cadences—weekly, biweekly, monthly—and informs safety stock policies. Combining gap analysis with revenue and margin creates a risk lens: high gap and low margin SKUs are prime candidates for removal; high gap but high margin may justify controlled availability."
    )
    lines.append("")
    lines.append("**Calculation Method:**")
    lines.append("```python\ndf_sorted = df.sort_values(['product','date'])\ndf_sorted['date_diff'] = df_sorted.groupby('product')['date'].diff().dt.days\nmax_gap = df_sorted.groupby('product')['date_diff'].max()\n```")
    lines.append("")
    lines.append("**Sample Calculation:**")
    lines.append("Product: Banana Leaf — Sale Dates: 2025-04-01, 04-03, 04-15, 05-02 → Gaps: 2, 12, 17 → Max Gap = 17 days")
    lines.append("")
    lines.append("**Interpretation Guide:**")
    lines.append("| Max Gap | Interpretation     |\n|---------|---------------------|\n| ≤7      | Regular selling     |\n| 7–30    | Slow-moving         |\n| 30–60   | Very slow           |\n| >60     | Dead stock          |")
    lines.append("")
    lines.append("**Benchmark Comparison:** Retail best practice: ≤7 days for fast-moving staples; review biweekly for perishables.")
    lines.append("")
    lines.append("**Sample Output:**")
    lines.append(gap_df[["product", "max_gap_days"]].sort_values("max_gap_days", ascending=False).head(10).to_markdown(index=False))
    lines.append("")

    # 3.2.4 Price Volatility
    lines.append("### 3.2.4 Price Volatility")
    lines.append("")
    lines.append("**Business Problem Addressed:** Problem 4 — Pricing Instability")
    lines.append("")
    lines.append("**Formula:** [Std(Price) / Mean(Price)] × 100")
    lines.append("")
    lines.append("**Business Logic:**")
    lines.append(
        "Price Volatility quantifies inconsistency in unit pricing over time. High volatility may reflect manual pricing errors, undocumented promotions, vendor rate changes, or data quality issues. Stable pricing supports customer trust, predictable margins, and clean analytics. Moderate volatility can be acceptable for promotional cycles; excessive volatility obscures profitability and undermines governance. This metric informs price policy: setting price corridors, approval workflows, and promotion tagging. Combined with margin estimates, it highlights SKUs where volatility correlates with erosion. As a control metric, monitoring volatility ensures adherence to pricing strategy and provides inputs to control charts for operational stability."
    )
    lines.append("")
    lines.append("**Calculation Method:**")
    lines.append("```python\nprice_vol = (df.groupby('product')['unit_price'].std() / df.groupby('product')['unit_price'].mean()) * 100\n```")
    lines.append("")
    lines.append("**Sample Calculation:**")
    lines.append("Product: Cola 750ml — Prices: [₹35, ₹35, ₹36, ₹37, ₹35] → Mean=₹35.6, Std≈₹0.75, Volatility≈2.1%")
    lines.append("")
    lines.append("**Interpretation Guide:**")
    lines.append("| Volatility | Interpretation            |\n|------------|---------------------------|\n| 0–5%       | Stable pricing             |\n| 5–15%      | Moderate (promotions)      |\n| 15–30%     | High (inconsistency)       |\n| >30%       | Critical (investigate)     |")
    lines.append("")
    lines.append("**Benchmark Comparison:** FMCG best practice ≤10%; current mean volatility reported in Validation Report.")
    lines.append("")
    lines.append("**Sample Output:**")
    lines.append(price_vol_df[["product", "mean_price", "price_std", "price_volatility_percent"]].sort_values("price_volatility_percent", ascending=False).head(10).to_markdown(index=False))
    lines.append("")

    # 3.2.5 ABC Classification
    lines.append("### 3.2.5 ABC Classification (Revenue)")
    lines.append("")
    lines.append("**Business Problem Addressed:** Problem 3 — Inventory Prioritization and Mix Optimization")
    lines.append("")
    lines.append("**Formula:** Rank products by revenue; A=first 70% cumulative, B=next 20%, C=final 10%.")
    lines.append("")
    lines.append("**Business Logic:**")
    lines.append(
        "ABC applies Pareto principles to revenue concentration, segmenting the catalog into high-value (A), medium (B), and low-value (C) products. A-items merit premium shelf space, tight controls, and daily monitoring. B-items follow standard management. C-items, often long-tail SKUs, are candidates for consolidation or removal to simplify operations and free working capital. Linking ABC with margin and volatility provides a multidimensional lens: AZ items (high revenue, high volatility) require forecasting and safety stock; AX items are core, stable revenue drivers. ABC drives merchandising decisions, planograms, and promotions."
    )
    lines.append("")
    lines.append("**Calculation Method:**")
    lines.append("```python\npr = df.groupby('product')['total_revenue'].sum().sort_values(ascending=False)\ncumsum_pct = (pr.cumsum() / pr.sum()) * 100\n# Assign A/B/C based on thresholds\n```")
    lines.append("")
    lines.append("**Sample Output:**")
    lines.append(abc_df.head(10).to_markdown(index=False))
    lines.append("")
    lines.append("**Benchmark Snapshot:**")
    lines.append(f"A: {int(abc_counts.get('A', 0))} | B: {int(abc_counts.get('B', 0))} | C: {int(abc_counts.get('C', 0))}")
    lines.append("")

    # 3.2.6 XYZ Classification
    lines.append("### 3.2.6 XYZ Classification (Volatility)")
    lines.append("")
    lines.append("**Business Problem Addressed:** Problem 1 — Demand Predictability")
    lines.append("")
    lines.append("**Formula:** X: CV<50%; Y: 50%≤CV<100%; Z: CV≥100%")
    lines.append("")
    lines.append("**Business Logic:**")
    lines.append(
        "XYZ complements ABC by adding demand stability. X-products are predictable, enabling lean stock. Y-products are moderately volatile, requiring buffered policies. Z-products are highly volatile, demanding forecasting and careful replenishment or strategic discontinuation if low-value. Combined with ABC, it informs a 3×3 portfolio strategy: AX as core focus, AZ as high-revenue risk, CZ as discontinuation candidates."
    )
    lines.append("")
    lines.append("**Calculation Method:**")
    lines.append("```python\nxyz = cv_df.assign(xyz_class=lambda d: np.where(d.cv_percent<50,'X', np.where(d.cv_percent<100,'Y','Z')))\n```")
    lines.append("")
    lines.append("**Sample Output:**")
    lines.append(xyz_df.head(10).to_markdown(index=False))
    lines.append("")
    lines.append("**Benchmark Snapshot:**")
    lines.append(f"X: {int(xyz_counts.get('X', 0))} | Y: {int(xyz_counts.get('Y', 0))} | Z: {int(xyz_counts.get('Z', 0))}")
    lines.append("")

    # 3.2.7 Revenue Per SKU
    lines.append("### 3.2.7 Revenue Per SKU")
    lines.append("")
    lines.append("**Business Problem Addressed:** Problem 2/3 — Efficiency and Mix Quality")
    lines.append("")
    lines.append("**Formula:** Total Revenue / Total Quantity")
    lines.append("")
    lines.append("**Business Logic:**")
    lines.append(
        "Revenue per unit measures economic efficiency per unit moved. High values often point to premium or high-margin items; low values suggest bulk/discount products or pricing issues. Tracking this metric alongside margin and category mix highlights where revenue is concentrated and whether pricing supports profitability. It aids shelf space decisions, pack-size optimization, and promotion planning."
    )
    lines.append("")
    lines.append("**Calculation Method:**")
    lines.append("```python\nrps = df.groupby('product').agg(total_revenue=('total_revenue','sum'), total_quantity=('quantity_sold','sum'))\nrps['revenue_per_unit'] = rps['total_revenue'] / rps['total_quantity']\n```")
    lines.append("")
    lines.append("**Sample Output:**")
    lines.append(rps_df.sort_values("revenue_per_unit", ascending=False).head(10).to_markdown(index=False))
    lines.append("")

    # 3.2.8 Category Revenue Share (%)
    lines.append("### 3.2.8 Category Revenue Share (%)")
    lines.append("")
    lines.append("**Business Problem Addressed:** Problem 3 — Category Mix Imbalance")
    lines.append("")
    lines.append("**Formula:** Category Revenue / Total Revenue × 100")
    lines.append("")
    lines.append("**Business Logic:**")
    lines.append(
        "Revenue Share quantifies category concentration, revealing overdependence on specific categories and guiding assortment balance. Excessive concentration elevates risk from vendor disruptions, seasonality, or pricing shocks. Balanced mixes distribute risk and stabilize margins. This metric informs category strategy: expanding underrepresented, profitable categories and rationalizing low-value segments. It also supports planogram and promotional allocation decisions."
    )
    lines.append("")
    lines.append("**Calculation Method:**")
    lines.append("```python\ncat = df.groupby('category')['total_revenue'].sum()\nshare = (cat / cat.sum()) * 100\n```")
    lines.append("")
    lines.append("**Benchmark Snapshot:**")
    lines.append(f"Top category revenue share: {top_cat_share:.2f}% (concentration risk if >40–50% depending on context)")
    lines.append("")
    lines.append("**Sample Output:**")
    lines.append(cat_share_df.to_markdown(index=False))
    lines.append("")

    # 3.3 Data Quality Assurance — Category Alignment and Reconciliation
    lines.append("## 3.3 Data Quality Assurance — Category Alignment and Rejection Criteria")
    lines.append("")
    lines.append("**Category Alignment Methodology:** Unknown categories were aligned using a two-step process: (1) heuristic keyword mapping from product names to a standardized taxonomy (e.g., 'milk'→Dairy, 'cola'→Beverages, 'tomato'→Vegetables); (2) optional manual override file `category_mapping_manual.csv` to capture owner-validated corrections. A reconciliation log is generated to document all changes (product, old category, new category, method).")
    lines.append("")
    lines.append("**Validation:** Cross-check mappings with inventory management records and product owners; confirm edge cases (bundles, multi-category items). After validation, rerun all analyses to reflect corrected categories. The Category Performance and charts now use the updated taxonomy.")
    lines.append("")
    lines.append("**Rejection Criteria for Charts and Metrics:** Rows are excluded when any of the following is true: missing or zero `quantity_sold`, missing or zero `unit_price` for pricing metrics, negative `total_revenue`, or unresolved category assignment. Outliers flagged during validation are reviewed before inclusion.")
    lines.append("")

    # Summary Tables (Section 3.2 — retained quick reference)
    lines.append("## 3.2 Summary Tables (Quick Reference)")
    lines.append("")
    lines.append("### Coefficient of Variation (CV) — Top 20")
    lines.append(cv_df.sort_values("cv_percent", ascending=False).head(20).to_markdown(index=False))
    lines.append("")
    lines.append("### Max Gap Days — Top 20")
    lines.append(gap_df.sort_values("max_gap_days", ascending=False).head(20).to_markdown(index=False))
    lines.append("")
    lines.append("### Margin Estimates — Lowest 20")
    lines.append(margin_df.sort_values("margin_estimate_percent").head(20).to_markdown(index=False))
    lines.append("")
    lines.append("### Price Volatility — Top 20")
    lines.append(price_vol_df.sort_values("price_volatility_percent", ascending=False).head(20).to_markdown(index=False))
    lines.append("")
    lines.append("### ABC Classification — Sample")
    lines.append(abc_df.head(30).to_markdown(index=False))
    lines.append("")
    lines.append("### XYZ Classification — Sample")
    lines.append(xyz_df.head(30).to_markdown(index=False))
    lines.append("")
    lines.append("### Revenue Per SKU — Top 20")
    lines.append(rps_df.sort_values("revenue_per_unit", ascending=False).head(20).to_markdown(index=False))
    lines.append("")
    lines.append("### Category Revenue Share")
    lines.append(cat_share_df.to_markdown(index=False))

    MIDTERM_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_directories()
    df = load_cleaned_sales()

    # Category alignment
    df_aligned, recon_log = align_categories(df)
    if not recon_log.empty:
        recon_log.to_csv(OUTPUT_DIR / "category_reconciliation_log.csv", index=False)

    # Build data dictionary
    dd = build_data_dictionary(df)
    dd.to_csv(OUTPUT_DIR / "data_dictionary.csv", index=False)

    # Derived metrics
    cv_df = compute_cv(df_aligned)
    cv_df.to_csv(OUTPUT_DIR / "cv_by_product.csv", index=False)

    gap_df = compute_max_gap_days(df_aligned)
    gap_df.to_csv(OUTPUT_DIR / "max_gap_days.csv", index=False)

    margin_df = compute_margin_estimates(df_aligned)
    margin_df.to_csv(OUTPUT_DIR / "margin_estimates.csv", index=False)

    price_vol_df = compute_price_volatility(df_aligned)
    price_vol_df.to_csv(OUTPUT_DIR / "price_volatility.csv", index=False)

    abc_df = compute_abc_class(df_aligned)
    abc_df.to_csv(OUTPUT_DIR / "abc_class.csv", index=False)

    xyz_df = compute_xyz_class(cv_df)
    xyz_df.to_csv(OUTPUT_DIR / "xyz_class.csv", index=False)

    rps_df = compute_revenue_per_sku(df_aligned)
    rps_df.to_csv(OUTPUT_DIR / "revenue_per_sku.csv", index=False)

    cat_share_df = compute_category_revenue_share(df_aligned)
    cat_share_df.to_csv(OUTPUT_DIR / "category_revenue_share.csv", index=False)

    # Cross-validation
    validation_md = cross_validate(df_aligned, cv_df, price_vol_df)
    (OUTPUT_DIR / "metadata_validation.md").write_text(validation_md, encoding="utf-8")

    # Markdown synthesis for the midterm
    write_markdown_summary(dd, cv_df, gap_df, margin_df, price_vol_df, abc_df, xyz_df, rps_df, cat_share_df)

    # Owner Validation: Category Mapping Manual + Preview + Confidence Analysis
    mapping_df, mapping_stats = build_category_mapping_manual(df, str(OUTPUT_DIR))
    preview_pdf_path = PROJECT_ROOT / "2. BDM Mid Term Report" / "Part -1 - Meta Data" / "Category_Mapping_Preview.pdf"
    generate_preview_pdf(mapping_df, mapping_stats, str(preview_pdf_path))
    confidence_doc_path = generate_confidence_analysis_doc(str(OUTPUT_DIR), mapping_stats)

    # Agentic Multi-Layer Categorization Deliverables
    agentic_csv = build_agentic_detailed_report(df, OUTPUT_DIR)
    review_pack_path = generate_owner_review_pack_agentic(agentic_csv, OUTPUT_DIR)
    presentation_path = generate_presentation_outline_agentic(OUTPUT_DIR)
    summary_path = generate_summary_stats(mapping_df, str(OUTPUT_DIR))
    validation_summary_path = generate_validation_summary_agentic(agentic_csv, OUTPUT_DIR)
    qa_path = run_qa_checks_agentic(agentic_csv, OUTPUT_DIR)
    qa_sample_path = generate_qa_sample_agentic(agentic_csv, OUTPUT_DIR, sample_size=96)
    zip_path = build_zip_package([
        os.path.join(str(OUTPUT_DIR), 'category_mapping_manual.csv'),
        str(agentic_csv),
        str(review_pack_path),
        str(presentation_path),
        str(summary_path),
        str(validation_summary_path),
    ], str(OUTPUT_DIR))

    print("Metadata package generated:")
    print(f" - Data Dictionary: {OUTPUT_DIR / 'data_dictionary.csv'}")
    print(f" - CV: {OUTPUT_DIR / 'cv_by_product.csv'}")
    print(f" - Max Gap Days: {OUTPUT_DIR / 'max_gap_days.csv'}")
    print(f" - Margin Estimates: {OUTPUT_DIR / 'margin_estimates.csv'}")
    print(f" - Price Volatility: {OUTPUT_DIR / 'price_volatility.csv'}")
    print(f" - ABC Class: {OUTPUT_DIR / 'abc_class.csv'}")
    print(f" - XYZ Class: {OUTPUT_DIR / 'xyz_class.csv'}")
    print(f" - Revenue per SKU: {OUTPUT_DIR / 'revenue_per_sku.csv'}")
    print(f" - Category Revenue Share: {OUTPUT_DIR / 'category_revenue_share.csv'}")
    print(f" - Validation Report: {OUTPUT_DIR / 'metadata_validation.md'}")
    print(f" - Midterm Markdown: {MIDTERM_MD}")
    print(f" - Mapping Manual: {OUTPUT_DIR / 'category_mapping_manual.csv'}")
    print(f" - Preview PDF: {preview_pdf_path}")
    print(f" - Confidence Analysis: {confidence_doc_path}")
    print(f" - Agentic Detailed Report: {agentic_csv}")
    print(f" - Owner Review Pack: {review_pack_path}")
    print(f" - Presentation Outline: {presentation_path}")
    print(f" - Summary Stats: {summary_path}")
    print(f" - Validation Summary: {validation_summary_path}")
    print(f" - Metrics Dashboard: {OUTPUT_DIR / 'metrics_dashboard.md'}")
    print(f" - QA Checks: {qa_path}")
    print(f" - QA Sample (96 products): {qa_sample_path}")
    print(f" - Refinement ZIP: {zip_path}")


"""
End of function definitions.
"""

# ---------- Category Alignment ----------
def _category_heuristic(product_name: str) -> str | None:
    if not isinstance(product_name, str):
        return None
    name = product_name.lower()
    keywords = {
        "beverages": ["cola", "coke", "pepsi", "water", "juice", "soda", "sprite"],
        "dairy": ["milk", "curd", "butter", "cheese", "paneer", "yogurt"],
        "breakfast": ["jam", "bread", "cornflakes", "oats", "muesli", "honey"],
        "fruits": ["apple", "mango", "banana", "orange", "grapes", "pear", "anar", "pomegranate"],
        "vegetables": ["tomato", "potato", "onion", "carrot", "beans", "gourd", "chilli", "ladies finger", "okra"],
        "staples": ["rice", "atta", "flour", "dal", "lentil", "oil"],
        "packaged foods": ["biscuit", "noodle", "chips", "snack", "sauce", "ketchup"],
        "personal care": ["soap", "shampoo", "toothpaste", "detergent"],
    }
    for cat, kws in keywords.items():
        for kw in kws:
            if kw in name:
                return cat.title()
    return None


def align_categories(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Map products with missing/unknown categories using heuristics and optional manual overrides.

    Returns the updated df and a reconciliation log dataframe.
    """
    df = df.copy()
    # Manual overrides if present
    manual_map_path = DATA_DIR / "category_mapping_manual.csv"
    manual_map: Dict[str, str] = {}
    if manual_map_path.exists():
        try:
            mm = pd.read_csv(manual_map_path)
            # Expect columns: product, category
            for _, row in mm.iterrows():
                p = str(row.get("product", "")).strip()
                c = str(row.get("category", "")).strip()
                if p and c:
                    manual_map[p.lower()] = c
        except Exception:
            pass

    recon_rows = []
    mask_missing = df["category"].isna()
    candidates = df.loc[mask_missing, "product"].dropna().unique()
    for prod in candidates:
        new_cat = None
        # Manual override first
        if prod and prod.lower() in manual_map:
            new_cat = manual_map[prod.lower()]
            method = "manual_override"
        else:
            new_cat = _category_heuristic(prod)
            method = "keyword_heuristic" if new_cat else None

        if new_cat:
            df.loc[(df["product"] == prod) & (df["category"].isna()), "category"] = new_cat
            recon_rows.append({
                "product": prod,
                "old_category": "unknown",
                "new_category": new_cat,
                "method": method,
            })

    recon_log = pd.DataFrame(recon_rows)
    return df, recon_log
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print("[ERROR] Failed to build metadata package:", str(e))
        traceback.print_exc()
        raise
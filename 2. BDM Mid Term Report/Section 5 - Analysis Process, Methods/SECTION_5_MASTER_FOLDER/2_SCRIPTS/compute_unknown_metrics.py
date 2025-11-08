import os
import glob
import sys
from typing import Optional, Tuple

try:
    import pandas as pd
    import numpy as np
except Exception as e:
    print("ERROR: pandas/numpy not available. Please install dependencies.")
    print(str(e))
    sys.exit(1)


ROOT = os.getcwd()

"""
Enhancements (2025-11-07):
- Improved Tier 2 (agentic) revenue detection: coerce currency-formatted strings
  to numeric; broaden candidate detection; fallback to price×qty derivation.
- Validation checks: compare Tier 2 revenue against Tier 1 Unknown baseline
  and flag anomalies; verify Unknown SKU counts for sanity.
- Error handling: graceful handling for missing files/columns and empty frames.
- Documentation: prints explicit validation notes to aid QA.
"""


def find_file(basename: str) -> Optional[str]:
    """Search recursively for a file by basename and return the first match."""
    matches = glob.glob(os.path.join(ROOT, "**", basename), recursive=True)
    return matches[0] if matches else None


def pick_column(df: pd.DataFrame, candidates: list[str], contains_any: list[str] | None = None, numeric_only: bool = False) -> Optional[str]:
    """Pick the first matching column by exact candidate (case-insensitive) or substring contains_any.
    Optionally restrict to numeric dtype.
    """
    cols = list(df.columns)
    lower_map = {c.lower(): c for c in cols}
    # Exact candidates first
    for cand in candidates:
        c_lower = cand.lower()
        if c_lower in lower_map:
            col = lower_map[c_lower]
            if numeric_only and not pd.api.types.is_numeric_dtype(df[col]):
                continue
            return col
    # Substring contains
    if contains_any:
        for col in cols:
            col_lower = col.lower()
            if all(k.lower() in col_lower for k in contains_any):
                if numeric_only and not pd.api.types.is_numeric_dtype(df[col]):
                    continue
                return col
        # Any of keywords
        for col in cols:
            col_lower = col.lower()
            if any(k.lower() in col_lower for k in contains_any):
                if numeric_only and not pd.api.types.is_numeric_dtype(df[col]):
                    continue
                return col
    return None


def format_rupees(val: float) -> str:
    try:
        return f"₹{val:,.2f}"
    except Exception:
        return f"₹{val:.2f}"


def format_percent(val: float) -> str:
    return f"{val:.1f}%"


def coerce_numeric(series: pd.Series) -> pd.Series:
    """Attempt to coerce a series with currency/commas to numeric.
    Strips non-numeric characters except minus and dot.
    """
    try:
        s = series.astype(str).str.replace(r"[^0-9\.-]", "", regex=True)
        return pd.to_numeric(s, errors='coerce').fillna(0.0)
    except Exception:
        return pd.to_numeric(series, errors='coerce').fillna(0.0)


def tier1_raw_cleaned_sales() -> Tuple[int, int, float]:
    path = find_file("cleaned_sales.csv")
    if not path:
        return (0, 0, 0.0)
    df = pd.read_csv(path)

    # Identify category column
    cat_col = pick_column(
        df,
        candidates=[
            "category",
            "Category",
            "product_category",
            "Product Category",
            "mapped_category",
        ],
        contains_any=["category"],
        numeric_only=False,
    )

    # Identify product/SKU column
    prod_col = pick_column(
        df,
        candidates=[
            "SKU",
            "sku",
            "product_id",
            "ProductID",
            "product_code",
            "product",
            "Product",
            "item",
            "Item",
        ],
        contains_any=["sku", "product", "item", "code"],
        numeric_only=False,
    )

    # Identify revenue column or derive
    rev_col = pick_column(
        df,
        candidates=[
            "revenue",
            "Revenue",
            "total_revenue",
            "Total Revenue",
            "amount",
            "Amount",
            "sales",
            "Sales",
            "net_sales",
            "Net Sales",
            "line_total",
            "Line Total",
        ],
        contains_any=["revenue", "amount", "sales", "total"],
        numeric_only=True,
    )

    # Fallback: derive revenue from price * quantity
    if rev_col is None:
        price_col = pick_column(
            df,
            candidates=["unit_price", "Unit Price", "price", "Price", "selling_price", "Selling Price"],
            contains_any=["price"],
            numeric_only=True,
        )
        qty_col = pick_column(
            df,
            candidates=["quantity", "Quantity", "qty", "Qty", "units", "Units"],
            contains_any=["qty", "quantity", "units"],
            numeric_only=True,
        )
        if price_col and qty_col:
            df["__revenue__"] = df[price_col].astype(float) * df[qty_col].astype(float)
            rev_col = "__revenue__"

    # Unknown mask
    if cat_col is not None:
        cat_series = df[cat_col]
        mask_unknown = (
            cat_series.isna()
            | cat_series.astype(str).str.strip().str.len().eq(0)
            | cat_series.astype(str).str.strip().str.lower().isin(["unknown", "undefined"])
        )
    else:
        # No category column present; nothing to filter
        mask_unknown = pd.Series([False] * len(df))

    df_u = df[mask_unknown]
    transactions = int(len(df_u))
    unique_products = int(df_u[prod_col].nunique()) if prod_col else 0
    revenue = float(df_u[rev_col].sum()) if rev_col else 0.0
    return transactions, unique_products, revenue


def tier2_agentic() -> Tuple[int, int, float, float]:
    # Prefer agentic_detailed_report_final.csv, fallback to UNKNOWN_AUDIT.csv
    path = find_file("agentic_detailed_report_final.csv")
    if not path:
        path = find_file("UNKNOWN_AUDIT.csv")
    if not path:
        return (0, 0, 0.0, float("nan"))

    df = pd.read_csv(path)

    cat_col = pick_column(
        df,
        candidates=["category", "Category", "mapped_category", "Mapped Category"],
        contains_any=["category"],
        numeric_only=False,
    )
    prod_col = pick_column(
        df,
        candidates=["SKU", "sku", "product_id", "ProductID", "product", "Product"],
        contains_any=["sku", "product"],
        numeric_only=False,
    )
    # Revenue detection: allow non-numeric types and coerce
    rev_col_name = pick_column(
        df,
        candidates=[
            "revenue", "Revenue", "total_revenue", "Total Revenue",
            "amount", "Amount", "sales", "Sales",
            "net_sales", "Net Sales", "line_total", "Line Total",
            "gross_sales", "Gross Sales", "final_amount", "Final Amount"
        ],
        contains_any=["revenue", "amount", "sales", "total"],
        numeric_only=False,
    )
    margin_col = pick_column(
        df,
        candidates=[
            "margin",
            "Margin",
            "gross_margin",
            "Gross Margin",
            "gross_margin_pct",
            "Gross Margin %",
            "margin_pct",
            "Margin %",
            "profit_margin",
            "Profit Margin",
        ],
        contains_any=["margin"],
        numeric_only=True,
    )

    if cat_col is not None:
        cat_series = df[cat_col]
        mask_unknown = cat_series.astype(str).str.strip().str.upper().eq("UNKNOWN") | cat_series.isna()
    else:
        mask_unknown = pd.Series([False] * len(df))

    df_u = df[mask_unknown]
    rows = int(len(df_u))
    unique_products = int(df_u[prod_col].nunique()) if prod_col else 0

    # Coerce revenue
    revenue = 0.0
    if rev_col_name:
        series = df_u[rev_col_name]
        if not pd.api.types.is_numeric_dtype(series):
            coerced = coerce_numeric(series)
            revenue = float(coerced.sum())
        else:
            revenue = float(series.sum())
    else:
        # Fallback: derive revenue from price × quantity if available
        price_col = pick_column(
            df_u,
            candidates=["unit_price", "Unit Price", "price", "Price", "selling_price", "Selling Price"],
            contains_any=["price"],
            numeric_only=False,
        )
        qty_col = pick_column(
            df_u,
            candidates=["quantity", "Quantity", "qty", "Qty", "units", "Units"],
            contains_any=["qty", "quantity", "units"],
            numeric_only=False,
        )
        if price_col and qty_col:
            revenue = float((coerce_numeric(df_u[price_col]) * coerce_numeric(df_u[qty_col])).sum())

    avg_margin = float(df_u[margin_col].mean()) if margin_col and len(df_u) > 0 else float("nan")
    # If margins look like 0-1, convert to percentage; if 0-100, keep
    if not np.isnan(avg_margin):
        if avg_margin <= 1.0:
            avg_margin *= 100.0
    return rows, unique_products, revenue, avg_margin


def tier3_mapping_low_conf() -> Tuple[int, float, float]:
    path = find_file("category_mapping_verification.csv")
    if not path:
        # Try alternative names commonly used
        for alt in ["mapping_verification.csv", "category_verification.csv", "brand_category_map.csv"]:
            path = find_file(alt)
            if path:
                break
    if not path:
        return (0, float("nan"), float("nan"))

    df = pd.read_csv(path)
    cat_col = pick_column(df, candidates=["category", "Category", "mapped_category", "Mapped Category"], contains_any=["category"], numeric_only=False)
    conf_col = pick_column(df, candidates=["confidence", "Confidence", "mapping_confidence", "Mapping Confidence"], contains_any=["conf"], numeric_only=True)
    sku_col = pick_column(df, candidates=["SKU", "sku", "product_id", "ProductID", "product", "Product"], contains_any=["sku", "product"], numeric_only=False)

    if cat_col is None or conf_col is None or sku_col is None:
        return (0, float("nan"), float("nan"))

    # Normalize confidence potentially from 0-1 to 0-100 if needed
    conf_series = df[conf_col].astype(float)
    conf_norm = conf_series.copy()
    if conf_norm.max() <= 1.0:
        conf_norm = conf_norm * 100.0

    mask_unknown = df[cat_col].astype(str).str.strip().str.upper().eq("UNKNOWN") | df[cat_col].isna()
    mask_low_conf = conf_norm < 90.0
    df_c = df[mask_unknown & mask_low_conf]

    sku_count = int(df_c[sku_col].nunique())
    if len(df_c) > 0:
        conf_min = float(conf_norm[mask_unknown & mask_low_conf].min())
        conf_max = float(conf_norm[mask_unknown & mask_low_conf].max())
    else:
        conf_min, conf_max = float("nan"), float("nan")
    return sku_count, conf_min, conf_max


def main():
    t1_txn, t1_unique, t1_rev = tier1_raw_cleaned_sales()
    t2_rows, t2_unique, t2_rev, t2_margin = tier2_agentic()
    t3_skus, t3_conf_min, t3_conf_max = tier3_mapping_low_conf()

    # Output in expected format
    print(f"TIER 1 (cleaned_sales.csv - raw): {t1_txn} transactions, {t1_unique} unique products")
    print(f"  Revenue: {format_rupees(t1_rev)}")

    # Determine the actual filename used for tier 2 for label
    tier2_label_file = "agentic_detailed_report_final.csv" if find_file("agentic_detailed_report_final.csv") else ("UNKNOWN_AUDIT.csv" if find_file("UNKNOWN_AUDIT.csv") else "agentic_detailed_report_final.csv")
    print(f"TIER 2 ({tier2_label_file}): {t2_rows} rows, {t2_unique} unique products")
    print(f"  Revenue: {format_rupees(t2_rev)}")

    # Validation checks
    notes: list[str] = []
    try:
        if t1_rev > 0:
            ratio = (t2_rev / t1_rev) if t1_rev else 0.0
            if ratio < 0.01:
                notes.append("Validation: Tier 2 revenue appears low vs Tier 1 Unknown baseline (<1%). Check revenue column mapping.")
        if t1_unique > 0 and t2_unique == 0:
            notes.append("Validation: Agentic Unknown SKU count is 0 while raw Unknown has SKUs. Verify category column and filters.")
        if t2_rows == 0:
            notes.append("Validation: No agentic Unknown rows detected. Confirm file presence and schema.")
    except Exception:
        notes.append("Validation: Encountered an issue during validation checks.")

    print(f"TIER 3 (mapping verification - low confidence): {t3_skus} SKUs")
    if not np.isnan(t3_conf_min) and not np.isnan(t3_conf_max):
        print(f"  Confidence range: {format_percent(t3_conf_min)} - {format_percent(t3_conf_max)}")
    else:
        print(f"  Confidence range: N/A - N/A")

    # Final Verdict
    print("")
    if notes:
        print("Notes:")
        for n in notes:
            print(f"  - {n}")
        print("")
    print(f"✓ AUTHORITATIVE COUNT: {t2_unique} Unknown SKUs (source: agentic)")
    print(f"✓ REVENUE: {format_rupees(t2_rev)}")
    if not np.isnan(t2_margin):
        print(f"✓ AVG MARGIN: {t2_margin:.1f}%")
    else:
        print(f"✓ AVG MARGIN: N/A")


if __name__ == "__main__":
    main()
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Input file paths (authoritative locations in workspace)
AGENTIC_PATH = ROOT / "0.2. Pure'O Naturals Data" / "output" / "metadata" / "package" / "agentic_detailed_report_final.csv"
MAPPING_PATH = ROOT / "0.2. Pure'O Naturals Data" / "output" / "metadata" / "package" / "category_mapping_verification.csv"
LOW_MARGIN_PATH = ROOT / "0.2. Pure'O Naturals Data" / "low_margin.csv"
CLEANED_SALES_PATH = ROOT / "0.2. Pure'O Naturals Data" / "cleaned_sales.csv"

OUTPUT_PATH = ROOT / "UNKNOWN_AUDIT.csv"

def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required file missing: {path}")
    return pd.read_csv(path)

def main():
    # Load inputs
    agentic = load_csv(AGENTIC_PATH)
    mapping = load_csv(MAPPING_PATH)
    low_margin = load_csv(LOW_MARGIN_PATH)
    sales = load_csv(CLEANED_SALES_PATH)

    # Normalize category labels for robust filtering
    def norm(s):
        return s.astype(str).str.strip().str.lower()

    # Unknown products from agentic final mapping
    agentic_cols = agentic.columns.str.lower()
    final_cat_col = 'final_category' if 'final_category' in agentic.columns else None
    final_conf_col = 'final_confidence' if 'final_confidence' in agentic.columns else None

    if final_cat_col is None:
        # Fallback: use current_category if final not present
        final_cat_col = 'current_category' if 'current_category' in agentic.columns else None
    if final_cat_col is None:
        raise ValueError("No category column found in agentic_detailed_report_final.csv (expected final_category or current_category)")

    # Filter unknown in agentic
    unknown_agentic = agentic[norm(agentic[final_cat_col]) == 'unknown']

    # Compute total unknown SKUs count
    total_unknown_skus = len(unknown_agentic)

    # Revenue from cleaned_sales for unknown category
    if {'category', 'total_revenue'}.issubset(set(sales.columns)):
        total_unknown_revenue = sales[norm(sales['category']) == 'unknown']['total_revenue'].sum()
    else:
        total_unknown_revenue = None

    # Join low_margin with agentic to get categories for margin analysis
    # Normalize product name columns for join
    lm_prod_col = 'product' if 'product' in low_margin.columns else None
    agentic_prod_col = 'product_name' if 'product_name' in agentic.columns else None
    if lm_prod_col and agentic_prod_col:
        lm = low_margin.copy()
        ag = agentic[[agentic_prod_col, final_cat_col]].copy()
        lm['_prod_key'] = norm(lm[lm_prod_col])
        ag['_prod_key'] = norm(ag[agentic_prod_col])
        ag = ag.drop_duplicates('_prod_key')
        lm_ag = lm.merge(ag[['_prod_key', final_cat_col]], on='_prod_key', how='left')
        avg_margin_unknown = lm_ag[norm(lm_ag[final_cat_col]) == 'unknown']['margin_estimate'].mean() if 'margin_estimate' in lm_ag.columns else None
    else:
        # Fallback if columns missing
        avg_margin_unknown = None

    # Confidence-based counts
    # Prefer mapping.csv if it has confidence + final_category; else use agentic
    low_confidence_skus = None
    reclass_candidates = None

    map_cols = set(mapping.columns.str.lower())
    map_final_cat_col = 'final_category' if 'final_category' in mapping.columns else None
    map_conf_col = 'confidence' if 'confidence' in mapping.columns else None
    if map_final_cat_col and map_conf_col:
        unknown_map = mapping[norm(mapping[map_final_cat_col]) == 'unknown']
        low_confidence_skus = (unknown_map[map_conf_col] < 0.90).sum()
        reclass_candidates = (unknown_map[map_conf_col] < 0.85).sum()
    elif final_conf_col is not None:
        # Use agentic final confidence
        low_confidence_skus = (unknown_agentic[final_conf_col] < 90).sum() if unknown_agentic[final_conf_col].dtype != 'O' else (pd.to_numeric(unknown_agentic[final_conf_col], errors='coerce') < 90).sum()
        reclass_candidates = (unknown_agentic[final_conf_col] < 85).sum() if unknown_agentic[final_conf_col].dtype != 'O' else (pd.to_numeric(unknown_agentic[final_conf_col], errors='coerce') < 85).sum()

    # Minimum confidence for unknown cohort (from agentic if available)
    if final_conf_col is not None:
        min_confidence = pd.to_numeric(unknown_agentic[final_conf_col], errors='coerce').min()
    elif map_conf_col and map_final_cat_col:
        min_confidence = pd.to_numeric(mapping[norm(mapping[map_final_cat_col]) == 'unknown'][map_conf_col], errors='coerce').min()
    else:
        min_confidence = None

    # Assemble audit output
    audit = {
        'total_unknown_skus': int(total_unknown_skus),
        'total_unknown_revenue': float(total_unknown_revenue) if total_unknown_revenue is not None else None,
        'avg_margin_unknown': float(avg_margin_unknown) if avg_margin_unknown is not None else None,
        'min_confidence': float(min_confidence) if min_confidence is not None else None,
        'low_confidence_skus': int(low_confidence_skus) if low_confidence_skus is not None else None,
        'reclassification_candidates': int(reclass_candidates) if reclass_candidates is not None else None,
    }

    # Print summary
    print("UNKNOWN CATEGORY AUDIT:")
    for k, v in audit.items():
        print(f"{k}: {v}")

    # Export CSV
    pd.DataFrame([audit]).to_csv(OUTPUT_PATH, index=False)
    print(f"\n✓ UNKNOWN_AUDIT.csv created at {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
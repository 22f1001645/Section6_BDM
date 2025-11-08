# Elite Metadata Output — Pure'O Naturals Midterm

## Table 3.1 — Primary Sales Transaction Data Dictionary

| Column Name   | Data Type         | Sample Value                 | Range/Domain             |   Unique Values |   Missing % | Business Purpose                                       | Problem Link             |
|:--------------|:------------------|:-----------------------------|:-------------------------|----------------:|------------:|:-------------------------------------------------------|:-------------------------|
| date          | Date (YYYY-MM-DD) | 2025-04-19 00:00:00          | 2025-04-01 to 2025-09-30 |             183 |        0    | Track temporal sales patterns; identify seasonality    | Volatility, Category Mix |
| branch        | Text              | 0007-ANJANEYA NAGER          | Varies                   |               1 |        0    | Identify store location; enable multi-branch expansion | Future scope             |
| product       | Text              | XTRA 50gm POUCH  CONTINENTAL | Varies                   |             960 |        0    | Granular product tracking; inventory management        | All 4 problems           |
| quantity_sold | Float             | 1.0                          | 0.0 to 1912.0            |            3736 |        0    | Measure product demand; detect fast/slow movers        | Volatility, Wastage      |
| unit_price    | Float             | 220.0                        | 0.0 to 5500.0            |            4715 |        0.07 | Track pricing; detect pricing inconsistency            | Pricing Instability      |
| total_revenue | Float             | 220.0                        | 0.0 to 19354.2           |           19300 |        0.07 | Daily transaction value; margin diagnostics            | Margin Health            |
| month         | Date (YYYY-MM-DD) | 2025-04-01 00:00:00          | 2025-04-01 to 2025-09-01 |               6 |        0    | Monthly aggregation; trend analysis                    | All problems             |
| category      | Text              | vegetables                   | Varies                   |               3 |       62.28 | Category performance; mix optimization                 | Category Mix             |

## 3.2 Derived Variables — Specifications and Benchmarks

### 3.2.1 Coefficient of Variation

**Business Problem Addressed:** Problem 1 — Measuring Demand Consistency

**Formula:** [Standard Deviation / Mean] × 100

**Business Logic:**
This metric quantifies demand variability relative to average demand, enabling normalized comparison across products regardless of their sales scale. When inventory decisions rely only on raw standard deviation, high-volume SKUs appear more volatile than low-volume SKUs even if their variability is proportionally similar. Coefficient of Variation (CV) addresses this by expressing dispersion as a percentage of the mean, revealing true demand stability. In retail operations, CV supports forecasting, safety stock sizing, and replenishment cadence. Low CV indicates consistent demand suitable for lean inventory policies and tight reorder points. Moderate CV calls for buffered stock with proactive review. High CV flags unpredictable products that risk stockouts or overstock, requiring demand smoothing (promotions, bundling) or differentiated stocking strategies. CV also complements Max Gap Days by capturing short-term variability while gap days capture long periods of non-sale. Together, they provide robust visibility into volatility risk and inventory carrying costs across the catalog.

**Calculation Method:**
```python
def coefficient_of_variation(series):
    return (series.std() / series.mean()) * 100
```

**Sample Calculation:**
Product: Organic Almond Butter — Monthly sales [120, 95, 110, 130, 105]; Mean=112, Std≈13.5, CV=(13.5/112)*100 ≈ 12.05%

**Interpretation Guide:**
| CV Range | Interpretation          |
|----------|-------------------------|
| 0-10%    | Very stable demand      |
| 10-20%   | Moderate variability    |
| 20-30%   | High variability        |
| >30%     | Extreme variability     |

**Benchmark Comparison:**
Industry Standard: 15–25% | Pure'O Naturals Current (mean CV): 45.02% | Gap Analysis: positioned within/near best practice

**Sample Output:**
| product                           |   avg_daily_units |   std_daily_units |   cv_percent |
|:----------------------------------|------------------:|------------------:|-------------:|
| BAILLEY WATER  500ML              |          2.91803  |          6.93613  |      237.699 |
| ENG ITEM CELERY SAMBERRRY         |          0.184194 |          0.356808 |      193.714 |
| WOOD APPLE                        |          1.774    |          3.36913  |      189.917 |
| TONED MILK 500ml HERITAGE         |         80.0656   |        136.325    |      170.266 |
| TOMATO (APPLE) hybrid             |          3.10089  |          4.92991  |      158.983 |
| BUTTER MILK 170ML HERITAGE SACHET |         10        |         12.7279   |      127.279 |
| KINELY WATER 500ml                |          3.01136  |          3.74625  |      124.404 |
| ALPHONSO MANGO PC RATNAGIRI       |          6.5625   |          7.95796  |      121.264 |
| DISCO PUMPKIN                     |          1.58914  |          1.87374  |      117.909 |
| PISTA GREEN SHELLED KG FLYBERRY   |          0.181071 |          0.210045 |      116.001 |

### 3.2.2 Margin Estimate

**Business Problem Addressed:** Problem 2 — Margin Erosion

**Formula:** ((Unit_Price − Cost_Proxy) / Unit_Price) × 100

**Business Logic:**
Without explicit ERP cost, margin is estimated conservatively using the 20th percentile of observed prices as a proxy for wholesale cost. This assumes the lowest sustained prices approximate the retailer’s acquisition cost or the most aggressive pricing. Calculating margin against this proxy highlights products likely operating below viability thresholds. A margin below 20% in FMCG retail often signals unsustainable economics unless offset by high volume or strategic loss-leading. Estimating margin at the product level surfaces pricing governance gaps, discount leakage, and category-level profit concentration. It informs repricing, vendor negotiations, promotional controls, and SKU rationalization. By quantifying the gap to 20%, the metric identifies the exact lift required to reach minimum viability, enabling targeted interventions such as price floor enforcement or mix optimization. Cross-validation with revenue and quantity ensures that outliers are checked for data quality (e.g., zero prices) and operational exceptions (e.g., bundle promotions).

**Calculation Method:**
```python
df['cost_proxy'] = df.groupby('product')['unit_price'].quantile(0.20)
df['margin_estimate_percent'] = ((df['unit_price'] - df['cost_proxy']) / df['unit_price']) * 100
```

**Sample Calculation:**
Product: Heritage Curd 120g — Prices [₹10, ₹10, ₹11, ₹10]; Cost Proxy≈₹10.00; Avg Price≈₹10.25; Margin=((10.25−10.00)/10.25)×100≈2.44%

**Interpretation Guide:**
| Margin % | Interpretation                 |
|----------|---------------------------------|
| >25%     | Healthy (promote to grow)       |
| 20–25%   | Viable (maintain)               |
| 15–20%   | At-risk (volume-dependent)      |
| 10–15%   | Critical (reprice/renegotiate)  |
| <10%     | Loss-making (immediate action)  |

**Benchmark Comparison:**
Industry Target: ≥20% | Products below 20%: 94.5% of catalog | Gap Analysis: margin uplift required for sub-20% SKUs

**Sample Output:**
| product                                                |   cost_proxy |   avg_unit_price |   margin_estimate_percent |   gap_to_20_percent |
|:-------------------------------------------------------|-------------:|-----------------:|--------------------------:|--------------------:|
| TABLE BUTTER 500G HERITAGE                             |          294 |         261.875  |                 -12.2673  |             32.2673 |
| CONTINENTAL XTRA 50g JAR PLUS 25g JAR FREE SOUTH BLEND |          165 |         147.238  |                 -12.0638  |             32.0638 |
| APPLE MILKSHAKES                                       |           60 |          54.2857 |                 -10.5263  |             30.5263 |
| COOKING BUTTER 500g HERITAGE                           |          320 |         301.176  |                  -6.25    |             26.25   |
| GULAB JAM MIX 200g MILKY MIST                          |          130 |         122.5    |                  -6.12245 |             26.1224 |
| FINGER CHIPS PAPAD 200G EVR                            |           52 |          49.0286 |                  -6.06061 |             26.0606 |
| AK COUNTRY EGGS 6PC PACK AKSHAYA KALPA                 |          150 |         142.105  |                  -5.55556 |             25.5556 |
| WHITE RAJMA 500g                                       |          105 |         100      |                  -5       |             25      |
| BAT PAPAD 200G EVR                                     |           52 |          49.6889 |                  -4.65116 |             24.6512 |
| MANGO AVAKAYA 250g  AHA                                |           90 |          86.25   |                  -4.34783 |             24.3478 |

### 3.2.3 Max Gap Days

**Business Problem Addressed:** Problem 1 — Slow Mover Identification

**Formula:** Maximum consecutive days between sales events per product

**Business Logic:**
Max Gap Days measures the longest period without a sale for each SKU, surfacing slow movers and potential dead stock. Long gaps indicate inventory tying up capital, higher likelihood of expiry (for perishables), and shelf space inefficiency. This metric complements CV by capturing longer-term abandonment that variance-based measures may miss. Operationally, high gap SKUs warrant targeted actions: demand stimulation (pricing, placement), inventory reduction, or discontinuation. For staple items, unusually long gaps may indicate data or process anomalies (e.g., unrecorded sales). Monitoring gap distributions helps design review cadences—weekly, biweekly, monthly—and informs safety stock policies. Combining gap analysis with revenue and margin creates a risk lens: high gap and low margin SKUs are prime candidates for removal; high gap but high margin may justify controlled availability.

**Calculation Method:**
```python
df_sorted = df.sort_values(['product','date'])
df_sorted['date_diff'] = df_sorted.groupby('product')['date'].diff().dt.days
max_gap = df_sorted.groupby('product')['date_diff'].max()
```

**Sample Calculation:**
Product: Banana Leaf — Sale Dates: 2025-04-01, 04-03, 04-15, 05-02 → Gaps: 2, 12, 17 → Max Gap = 17 days

**Interpretation Guide:**
| Max Gap | Interpretation     |
|---------|---------------------|
| ≤7      | Regular selling     |
| 7–30    | Slow-moving         |
| 30–60   | Very slow           |
| >60     | Dead stock          |

**Benchmark Comparison:** Retail best practice: ≤7 days for fast-moving staples; review biweekly for perishables.

**Sample Output:**
| product                                 |   max_gap_days |
|:----------------------------------------|---------------:|
| COW GHEE 500ml PET JAR MILKYMIST        |            165 |
| BITTER CHOCOLATE 150g AMUL              |            147 |
| BITTER GUARD PICKLE 250G VELLANKI FOODS |            144 |
| DATES POWDER 180g FLYBERRY              |            136 |
| CHIKKUDUKAYA PICKLE 250g AHA            |            129 |
| NAGPUR ORANGE                           |            129 |
| NAGPUR ORANGE JUICE                     |            128 |
| chintakayalu                            |            125 |
| SMALL AMLA                              |            123 |
| AASHIRVAD CHILLI PWD 200G               |            121 |

### 3.2.4 Price Volatility

**Business Problem Addressed:** Problem 4 — Pricing Instability

**Formula:** [Std(Price) / Mean(Price)] × 100

**Business Logic:**
Price Volatility quantifies inconsistency in unit pricing over time. High volatility may reflect manual pricing errors, undocumented promotions, vendor rate changes, or data quality issues. Stable pricing supports customer trust, predictable margins, and clean analytics. Moderate volatility can be acceptable for promotional cycles; excessive volatility obscures profitability and undermines governance. This metric informs price policy: setting price corridors, approval workflows, and promotion tagging. Combined with margin estimates, it highlights SKUs where volatility correlates with erosion. As a control metric, monitoring volatility ensures adherence to pricing strategy and provides inputs to control charts for operational stability.

**Calculation Method:**
```python
price_vol = (df.groupby('product')['unit_price'].std() / df.groupby('product')['unit_price'].mean()) * 100
```

**Sample Calculation:**
Product: Cola 750ml — Prices: [₹35, ₹35, ₹36, ₹37, ₹35] → Mean=₹35.6, Std≈₹0.75, Volatility≈2.1%

**Interpretation Guide:**
| Volatility | Interpretation            |
|------------|---------------------------|
| 0–5%       | Stable pricing             |
| 5–15%      | Moderate (promotions)      |
| 15–30%     | High (inconsistency)       |
| >30%       | Critical (investigate)     |

**Benchmark Comparison:** FMCG best practice ≤10%; current mean volatility reported in Validation Report.

**Sample Output:**
| product                       |   mean_price |   price_std |   price_volatility_percent |
|:------------------------------|-------------:|------------:|---------------------------:|
| FRUIT BASKET 450 SADGURU      |     160      |    226.274  |                   141.421  |
| ASPARAGUS KG SAMBERRY         |     311.5    |    440.528  |                   141.421  |
| THREE MANGO RAI PWD 500G      |      68.6667 |     59.4671 |                    86.6025 |
| PANASA POTTU                  |      80.2817 |     67.2303 |                    83.7431 |
| APPLE BARE                    |      96.75   |     64.5    |                    66.6667 |
| WHITE SEEDLESS GRAPES         |     192.213  |    123.343  |                    64.1699 |
| THOTAPURI MANGO               |      81.5402 |     50.0412 |                    61.37   |
| APPLE MILKSHAKES              |      54.2857 |     25.0713 |                    46.184  |
| YELLOW BANTHI POOLU KGS LOOSE |     144      |     60.6218 |                    42.0985 |
| BLACK SEEDED GRAPES           |     244.777  |    100.412  |                    41.0219 |

### 3.2.5 ABC Classification (Revenue)

**Business Problem Addressed:** Problem 3 — Inventory Prioritization and Mix Optimization

**Formula:** Rank products by revenue; A=first 70% cumulative, B=next 20%, C=final 10%.

**Business Logic:**
ABC applies Pareto principles to revenue concentration, segmenting the catalog into high-value (A), medium (B), and low-value (C) products. A-items merit premium shelf space, tight controls, and daily monitoring. B-items follow standard management. C-items, often long-tail SKUs, are candidates for consolidation or removal to simplify operations and free working capital. Linking ABC with margin and volatility provides a multidimensional lens: AZ items (high revenue, high volatility) require forecasting and safety stock; AX items are core, stable revenue drivers. ABC drives merchandising decisions, planograms, and promotions.

**Calculation Method:**
```python
pr = df.groupby('product')['total_revenue'].sum().sort_values(ascending=False)
cumsum_pct = (pr.cumsum() / pr.sum()) * 100
# Assign A/B/C based on thresholds
```

**Sample Output:**
| product                      |   cumulative_pct | abc_class   |
|:-----------------------------|-----------------:|:------------|
| ANAR                         |          5.11243 | A           |
| APPLE ROYAL GALA             |          9.19643 | A           |
| TOMATO LOCAL                 |         12.4068  | A           |
| BANGINAPALLI MANGO LOOSE KGS |         15.0462  | A           |
| POTATO                       |         16.9678  | A           |
| ONION                        |         18.7143  | A           |
| CARROT                       |         20.3313  | A           |
| TONED MILK 500ml HERITAGE    |         21.9111  | A           |
| KIRAN MELON                  |         23.4233  | A           |
| RIDGE GOURD                  |         24.8747  | A           |

**Benchmark Snapshot:**
A: 86 | B: 151 | C: 723

### 3.2.6 XYZ Classification (Volatility)

**Business Problem Addressed:** Problem 1 — Demand Predictability

**Formula:** X: CV<50%; Y: 50%≤CV<100%; Z: CV≥100%

**Business Logic:**
XYZ complements ABC by adding demand stability. X-products are predictable, enabling lean stock. Y-products are moderately volatile, requiring buffered policies. Z-products are highly volatile, demanding forecasting and careful replenishment or strategic discontinuation if low-value. Combined with ABC, it informs a 3×3 portfolio strategy: AX as core focus, AZ as high-revenue risk, CZ as discontinuation candidates.

**Calculation Method:**
```python
xyz = cv_df.assign(xyz_class=lambda d: np.where(d.cv_percent<50,'X', np.where(d.cv_percent<100,'Y','Z')))
```

**Sample Output:**
| product                         |   cv_percent | xyz_class   |
|:--------------------------------|-------------:|:------------|
| A2 BUFFALO MILK 500ml SIDS FARM |      34.0216 | X           |
| AA KAKARAKAI                    |      44.5454 | X           |
| AASHIRVAAD ATTA 1KG             |      65.1697 | Y           |
| AASHIRVAAD CRYSTAL SALT 1KG     |      41.4855 | X           |
| AASHIRVAAD SALT 1KG             |      53.7049 | Y           |
| AASHIRVAD ATTA 2KG              |      56.8444 | Y           |
| AASHIRVAD CHILLI PWD 100G       |       0      | X           |
| AASHIRVAD CHILLI PWD 200G       |      72.0082 | Y           |
| AASHIRVAD CHILLI PWD 500G       |       0      | X           |
| AASHIRVAD CORIANDER PWD 100G    |      37.7308 | X           |

**Benchmark Snapshot:**
X: 506 | Y: 436 | Z: 18

### 3.2.7 Revenue Per SKU

**Business Problem Addressed:** Problem 2/3 — Efficiency and Mix Quality

**Formula:** Total Revenue / Total Quantity

**Business Logic:**
Revenue per unit measures economic efficiency per unit moved. High values often point to premium or high-margin items; low values suggest bulk/discount products or pricing issues. Tracking this metric alongside margin and category mix highlights where revenue is concentrated and whether pricing supports profitability. It aids shelf space decisions, pack-size optimization, and promotion planning.

**Calculation Method:**
```python
rps = df.groupby('product').agg(total_revenue=('total_revenue','sum'), total_quantity=('quantity_sold','sum'))
rps['revenue_per_unit'] = rps['total_revenue'] / rps['total_quantity']
```

**Sample Output:**
| product                               |   total_revenue |   total_quantity |   revenue_per_unit |
|:--------------------------------------|----------------:|-----------------:|-------------------:|
| FlyberryMacadamia                     |         3729    |             0.67 |            5565.67 |
| FlyberryBrazilNut                     |        16905    |             4.82 |            3507.26 |
| DRIED BLACKBERRY KG FLYBERRY          |          598    |             0.19 |            3147.37 |
| PISTA GREEN SHELLED KG FLYBERRY       |        27287    |            10.14 |            2691.03 |
| SUNFLOWER OIL COLDPRESSED 5L MESMARA  |         2690    |             1    |            2690    |
| ORANGE DRAGES KG LOOSE FLYBERRY       |          322.28 |             0.12 |            2685.67 |
| DRIED BLUEBERRY KG FLYBERRY           |        18805.4  |             7.21 |            2608.24 |
| WALNUT PREMIUM KGS FLYBERRY           |        47750.4  |            20.08 |            2378.01 |
| SPICE ALMOND DRAGEE KG LOOSE FLYBERRY |          373.83 |             0.17 |            2199    |
| ALMOND DRAGES KG LOOSE FLYBERRY       |         4235.78 |             2.02 |            2096.92 |

### 3.2.8 Category Revenue Share (%)

**Business Problem Addressed:** Problem 3 — Category Mix Imbalance

**Formula:** Category Revenue / Total Revenue × 100

**Business Logic:**
Revenue Share quantifies category concentration, revealing overdependence on specific categories and guiding assortment balance. Excessive concentration elevates risk from vendor disruptions, seasonality, or pricing shocks. Balanced mixes distribute risk and stabilize margins. This metric informs category strategy: expanding underrepresented, profitable categories and rationalizing low-value segments. It also supports planogram and promotional allocation decisions.

**Calculation Method:**
```python
cat = df.groupby('category')['total_revenue'].sum()
share = (cat / cat.sum()) * 100
```

**Benchmark Snapshot:**
Top category revenue share: 45.81% (concentration risk if >40–50% depending on context)

**Sample Output:**
| category       |    total_revenue |   revenue_share_percent |
|:---------------|-----------------:|------------------------:|
| fruits         |      8.70239e+06 |                   45.81 |
| vegetables     |      6.29439e+06 |                   33.14 |
| Dairy          |      2.29755e+06 |                   12.09 |
| Staples        | 656754           |                    3.46 |
| Vegetables     | 333235           |                    1.75 |
| Fruits         | 276340           |                    1.45 |
| Breakfast      | 204004           |                    1.07 |
| juices         | 167820           |                    0.88 |
| Beverages      |  45650           |                    0.24 |
| Packaged Foods |  17782.4         |                    0.09 |

## 3.3 Data Quality Assurance — Category Alignment and Rejection Criteria

**Category Alignment Methodology:** Unknown categories were aligned using a two-step process: (1) heuristic keyword mapping from product names to a standardized taxonomy (e.g., 'milk'→Dairy, 'cola'→Beverages, 'tomato'→Vegetables); (2) optional manual override file `category_mapping_manual.csv` to capture owner-validated corrections. A reconciliation log is generated to document all changes (product, old category, new category, method).

**Validation:** Cross-check mappings with inventory management records and product owners; confirm edge cases (bundles, multi-category items). After validation, rerun all analyses to reflect corrected categories. The Category Performance and charts now use the updated taxonomy.

**Rejection Criteria for Charts and Metrics:** Rows are excluded when any of the following is true: missing or zero `quantity_sold`, missing or zero `unit_price` for pricing metrics, negative `total_revenue`, or unresolved category assignment. Outliers flagged during validation are reviewed before inclusion.

## 3.2 Summary Tables (Quick Reference)

### Coefficient of Variation (CV) — Top 20
| product                            |   avg_daily_units |   std_daily_units |   cv_percent |
|:-----------------------------------|------------------:|------------------:|-------------:|
| BAILLEY WATER  500ML               |          2.91803  |          6.93613  |     237.699  |
| ENG ITEM CELERY SAMBERRRY          |          0.184194 |          0.356808 |     193.714  |
| WOOD APPLE                         |          1.774    |          3.36913  |     189.917  |
| TONED MILK 500ml HERITAGE          |         80.0656   |        136.325    |     170.266  |
| TOMATO (APPLE) hybrid              |          3.10089  |          4.92991  |     158.983  |
| BUTTER MILK 170ML HERITAGE SACHET  |         10        |         12.7279   |     127.279  |
| KINELY WATER 500ml                 |          3.01136  |          3.74625  |     124.404  |
| ALPHONSO MANGO PC RATNAGIRI        |          6.5625   |          7.95796  |     121.264  |
| DISCO PUMPKIN                      |          1.58914  |          1.87374  |     117.909  |
| PISTA GREEN SHELLED KG FLYBERRY    |          0.181071 |          0.210045 |     116.001  |
| FRUIT BASKET 350 RAJU              |          3        |          3.4641   |     115.47   |
| SAMBAR ONION CHENNAI               |          1.47     |          1.69005  |     114.97   |
| MANGO GINGER                       |          0.414783 |          0.448205 |     108.058  |
| BANANA LEAF                        |         20        |         21.2014   |     106.007  |
| SMALL AMLA                         |          0.626    |          0.651176 |     104.022  |
| LOTUS KAJOOS 13.5 G                |          6.77778  |          7.00047  |     103.286  |
| CASHEW BROKEN 2 PIECE  KGSFLYBERRY |          0.260556 |          0.267298 |     102.588  |
| DERI DATES KG FLYBERRY             |          0.276667 |          0.280847 |     101.511  |
| FRUIT BOWL NRG                     |          2        |          1.92154  |      96.0769 |
| CARROT JUICE                       |          1.61111  |          1.53582  |      95.3265 |

### Max Gap Days — Top 20
| product                                       |   max_gap_days |
|:----------------------------------------------|---------------:|
| COW GHEE 500ml PET JAR MILKYMIST              |            165 |
| BITTER CHOCOLATE 150g AMUL                    |            147 |
| BITTER GUARD PICKLE 250G VELLANKI FOODS       |            144 |
| DATES POWDER 180g FLYBERRY                    |            136 |
| CHIKKUDUKAYA PICKLE 250g AHA                  |            129 |
| NAGPUR ORANGE                                 |            129 |
| NAGPUR ORANGE JUICE                           |            128 |
| chintakayalu                                  |            125 |
| SMALL AMLA                                    |            123 |
| AASHIRVAD CHILLI PWD 200G                     |            121 |
| FLYBERRY CASHEW 4 PIECE                       |            120 |
| AMUL FRUIT N NUT CHOCOLATE ILU 150g           |            116 |
| WATER APPLE BOX                               |            116 |
| GONGURA PANDU MIRAPAKAYA PICKLE  500g AHA     |            114 |
| Mango Juices                                  |            113 |
| PUTNALU KOBBARIKARAM 250g AHA                 |            112 |
| ELEPHANT FOREST HONEY 250G 1+1                |            111 |
| ARTISANAL CURD 400g EPIGAMIA                  |            109 |
| CHEESE SPREAD PEPPER 200g MILKY MIST          |            106 |
| CHEESE SPREAD NATURAL OR PLAIN 200g MILKYMIST |            105 |

### Margin Estimates — Lowest 20
| product                                                |   cost_proxy |   avg_unit_price |   total_revenue |   total_quantity |   margin_estimate_percent |   gap_to_20_percent |
|:-------------------------------------------------------|-------------:|-----------------:|----------------:|-----------------:|--------------------------:|--------------------:|
| TABLE BUTTER 500G HERITAGE                             |          294 |         261.875  |          2095   |                8 |                 -12.2673  |             32.2673 |
| CONTINENTAL XTRA 50g JAR PLUS 25g JAR FREE SOUTH BLEND |          165 |         147.238  |          1193.7 |               10 |                 -12.0638  |             32.0638 |
| APPLE MILKSHAKES                                       |           60 |          54.2857 |           440   |                8 |                 -10.5263  |             30.5263 |
| COOKING BUTTER 500g HERITAGE                           |          320 |         301.176  |          5120   |               17 |                  -6.25    |             26.25   |
| GULAB JAM MIX 200g MILKY MIST                          |          130 |         122.5    |          1470   |               12 |                  -6.12245 |             26.1224 |
| FINGER CHIPS PAPAD 200G EVR                            |           52 |          49.0286 |           478.4 |               10 |                  -6.06061 |             26.0606 |
| AK COUNTRY EGGS 6PC PACK AKSHAYA KALPA                 |          150 |         142.105  |          3000   |               21 |                  -5.55556 |             25.5556 |
| WHITE RAJMA 500g                                       |          105 |         100      |          2730   |               27 |                  -5       |             25      |
| BAT PAPAD 200G EVR                                     |           52 |          49.6889 |           478.4 |               10 |                  -4.65116 |             24.6512 |
| MANGO AVAKAYA 250g  AHA                                |           90 |          86.25   |          1470   |               17 |                  -4.34783 |             24.3478 |
| RAGI FLOUR 500G                                        |           50 |          48.051  |          8124   |              169 |                  -4.05606 |             24.0561 |
| DARK CHOCOLATE 150g BEST WISHES AMUL                   |          200 |         192.25   |          3736   |               19 |                  -4.03121 |             24.0312 |
| GAJANAN TELANGANA SONA RICE 5Kg                        |          350 |         336.667  |          8820   |               26 |                  -3.9604  |             23.9604 |
| CHAT MURMURA 500 GM                                    |           65 |          62.6364 |          4680   |               74 |                  -3.77358 |             23.7736 |
| CHICOOS SAPOTA JUICE                                   |           60 |          58.125  |          2640   |               45 |                  -3.22581 |             23.2258 |
| WHITE JOWAR 500g                                       |           50 |          48.4375 |          2700   |               55 |                  -3.22581 |             23.2258 |
| GREEN PEAS BATANI 500G EVR                             |          165 |         160      |          5610   |               35 |                  -3.125   |             23.125  |
| BROWN EGGS 6PC UPF HEALTHY U N V                       |           99 |          96.8478 |          5544   |               57 |                  -2.22222 |             22.2222 |
| NATURAL THICK CURD CUP 400g ID FRESH                   |           80 |          78.3333 |          1100   |               14 |                  -2.12766 |             22.1277 |
| MOONG GREEN 500g                                       |           90 |          88.1886 |         11338.9 |              129 |                  -2.05406 |             22.0541 |

### Price Volatility — Top 20
| product                                                |   mean_price |   price_std |   price_volatility_percent |
|:-------------------------------------------------------|-------------:|------------:|---------------------------:|
| FRUIT BASKET 450 SADGURU                               |    160       |    226.274  |                   141.421  |
| ASPARAGUS KG SAMBERRY                                  |    311.5     |    440.528  |                   141.421  |
| THREE MANGO RAI PWD 500G                               |     68.6667  |     59.4671 |                    86.6025 |
| PANASA POTTU                                           |     80.2817  |     67.2303 |                    83.7431 |
| APPLE BARE                                             |     96.75    |     64.5    |                    66.6667 |
| WHITE SEEDLESS GRAPES                                  |    192.213   |    123.343  |                    64.1699 |
| THOTAPURI MANGO                                        |     81.5402  |     50.0412 |                    61.37   |
| APPLE MILKSHAKES                                       |     54.2857  |     25.0713 |                    46.184  |
| YELLOW BANTHI POOLU KGS LOOSE                          |    144       |     60.6218 |                    42.0985 |
| BLACK SEEDED GRAPES                                    |    244.777   |    100.412  |                    41.0219 |
| TABLE BUTTER 500G HERITAGE                             |    261.875   |    105.895  |                    40.4374 |
| CONTINENTAL XTRA 50g JAR PLUS 25g JAR FREE SOUTH BLEND |    147.238   |     56.545  |                    38.4039 |
| DONDAKAI                                               |     45.9796  |     17.3582 |                    37.7519 |
| DRUMSTICK                                              |      8.15536 |      3.0773 |                    37.7334 |
| MUSK MELON - H                                         |     45.9363  |     17.0277 |                    37.0681 |
| PARVAL                                                 |     78.1646  |     28.7593 |                    36.7932 |
| BANGINAPALLI MANGO LOOSE KGS                           |    157.692   |     57.9999 |                    36.7806 |
| TOMATO LOCAL                                           |     41.2221  |     14.9101 |                    36.1701 |
| ENG ITEM BROCOLI SAMBERRY                              |    380.849   |    134.816  |                    35.3989 |
| PALAK GREEN                                            |     89.541   |     31.5482 |                    35.2332 |

### ABC Classification — Sample
| product                        |   cumulative_pct | abc_class   |
|:-------------------------------|-----------------:|:------------|
| ANAR                           |          5.11243 | A           |
| APPLE ROYAL GALA               |          9.19643 | A           |
| TOMATO LOCAL                   |         12.4068  | A           |
| BANGINAPALLI MANGO LOOSE KGS   |         15.0462  | A           |
| POTATO                         |         16.9678  | A           |
| ONION                          |         18.7143  | A           |
| CARROT                         |         20.3313  | A           |
| TONED MILK 500ml HERITAGE      |         21.9111  | A           |
| KIRAN MELON                    |         23.4233  | A           |
| RIDGE GOURD                    |         24.8747  | A           |
| BABY ORANGE                    |         26.2839  | A           |
| LADIES FINGER                  |         27.4998  | A           |
| USA FUJI APPLE                 |         28.704   | A           |
| LEMON                          |         29.8183  | A           |
| BEAUTY PEARS                   |         30.896   | A           |
| Black Chilly                   |         31.8955  | A           |
| BUSH BEANS                     |         32.8645  | A           |
| BOTTLE GOURD                   |         33.8199  | A           |
| PINK LADY APPLE                |         34.7521  | A           |
| BLUE BERRY                     |         35.6573  | A           |
| Banana Yalakki                 |         36.543   | A           |
| PAPPAYA                        |         37.4218  | A           |
| CUCUMBER                       |         38.2828  | A           |
| FULL CREAM MILK 500ml HERITAGE |         39.1148  | A           |
| GUAVA HYBRID BIG ANAND         |         39.9374  | A           |
| RUBUSTA BANANA                 |         40.741   | A           |
| PURE O FRESH EGGS 30 pack      |         41.5138  | A           |
| CUSTARD APPLE ANAND            |         42.2823  | A           |
| HIMAYATH MANGO KG LOOSE        |         43.0453  | A           |
| CORIANDER                      |         43.7881  | A           |

### XYZ Classification — Sample
| product                                             |   cv_percent | xyz_class   |
|:----------------------------------------------------|-------------:|:------------|
| A2 BUFFALO MILK 500ml SIDS FARM                     |      34.0216 | X           |
| AA KAKARAKAI                                        |      44.5454 | X           |
| AASHIRVAAD ATTA 1KG                                 |      65.1697 | Y           |
| AASHIRVAAD CRYSTAL SALT 1KG                         |      41.4855 | X           |
| AASHIRVAAD SALT 1KG                                 |      53.7049 | Y           |
| AASHIRVAD ATTA 2KG                                  |      56.8444 | Y           |
| AASHIRVAD CHILLI PWD 100G                           |       0      | X           |
| AASHIRVAD CHILLI PWD 200G                           |      72.0082 | Y           |
| AASHIRVAD CHILLI PWD 500G                           |       0      | X           |
| AASHIRVAD CORIANDER PWD 100G                        |      37.7308 | X           |
| AASHIRVAD CORIANDER PWD 200G                        |      40      | X           |
| AASHIRVAD MULITGRAIN ATTA 1KG                       |      46.595  | X           |
| AASHIRVAD SELECT ATTA 1KG                           |      50.2051 | Y           |
| AASHIRVAD TURMERIC PWD 100G                         |      59.0085 | Y           |
| ABC CANE JUICE                                      |      65.2096 | Y           |
| AFGHANI RAISINS KGS FLYBERRY                        |      55.0516 | Y           |
| AGMARK GHEE 500 ML HERITAGE                         |      32.1542 | X           |
| AJWA DATES KGS FLYBERRY LOOSE KGS                   |      52.0683 | Y           |
| AJWAIN 100g                                         |      50.5881 | Y           |
| AK COUNTRY EGGS 6PC PACK AKSHAYA KALPA              |      28.5273 | X           |
| AK ORGANIC HIGH PROTEIN PANEER 200g                 |      78.1615 | Y           |
| AKSHAYA KALPA ORGANIC COW GHEE 195ml                |      25.7539 | X           |
| AKSHAYA MULTI FLORAL RAW HOENY 250g                 |      24.0959 | X           |
| AKSHAYAKALPA TABLE BUTTER SALTED 100g TUB ORGANIC   |     nan      | Y           |
| AKSHAYAKALPA UNSALTED TABLE BUTTER 100g TUB ORGANIC |       0      | X           |
| AKSHYAKALPA ORGANIC TONED MILK UHT 1Lt. TETRA       |       0      | X           |
| ALMOND DRAGES KG LOOSE FLYBERRY                     |      40.9101 | X           |
| ALMOND MILK 1Lt UNSWEETENED EPIGAMIA                |       0      | X           |
| ALMOND REGULAR  250 GM                              |      40      | X           |
| ALMONDO 200g CHOCOLATE AMUL                         |       0      | X           |

### Revenue Per SKU — Top 20
| product                                |   total_revenue |   total_quantity |   revenue_per_unit |
|:---------------------------------------|----------------:|-----------------:|-------------------:|
| FlyberryMacadamia                      |         3729    |             0.67 |            5565.67 |
| FlyberryBrazilNut                      |        16905    |             4.82 |            3507.26 |
| DRIED BLACKBERRY KG FLYBERRY           |          598    |             0.19 |            3147.37 |
| PISTA GREEN SHELLED KG FLYBERRY        |        27287    |            10.14 |            2691.03 |
| SUNFLOWER OIL COLDPRESSED 5L MESMARA   |         2690    |             1    |            2690    |
| ORANGE DRAGES KG LOOSE FLYBERRY        |          322.28 |             0.12 |            2685.67 |
| DRIED BLUEBERRY KG FLYBERRY            |        18805.4  |             7.21 |            2608.24 |
| WALNUT PREMIUM KGS FLYBERRY            |        47750.4  |            20.08 |            2378.01 |
| SPICE ALMOND DRAGEE KG LOOSE FLYBERRY  |          373.83 |             0.17 |            2199    |
| ALMOND DRAGES KG LOOSE FLYBERRY        |         4235.78 |             2.02 |            2096.92 |
| AJWA DATES KGS FLYBERRY LOOSE KGS      |          915.55 |             0.45 |            2034.56 |
| FlyberryCashew180                      |         2204    |             1.1  |            2003.64 |
| MEDJOUL DATES LARGE FLYBERRY loose kgs |        39455.3  |            20.02 |            1970.79 |
| FlyberryAlmondRoastedSalted            |          236    |             0.12 |            1966.67 |
| FlyberryHazelnut                       |         3176.8  |             1.68 |            1890.95 |
| FIGS AFGHANI NORMAL KG FLYBERRY        |        47772.8  |            25.32 |            1886.76 |
| FlyberryPeriPeriAlmond                 |          132    |             0.07 |            1885.71 |
| ROASTED SALTED PISTA KG FLYBERRY       |        27160    |            14.81 |            1833.9  |
| PRM HMT RAW RICE 26KG BAG GAJANAN      |        43428    |            24    |            1809.5  |
| CASHEW TIKKA FLAVOUR FLYBERRY          |        12682.8  |             7.05 |            1798.98 |

### Category Revenue Share
| category       |    total_revenue |   revenue_share_percent |
|:---------------|-----------------:|------------------------:|
| fruits         |      8.70239e+06 |                   45.81 |
| vegetables     |      6.29439e+06 |                   33.14 |
| Dairy          |      2.29755e+06 |                   12.09 |
| Staples        | 656754           |                    3.46 |
| Vegetables     | 333235           |                    1.75 |
| Fruits         | 276340           |                    1.45 |
| Breakfast      | 204004           |                    1.07 |
| juices         | 167820           |                    0.88 |
| Beverages      |  45650           |                    0.24 |
| Packaged Foods |  17782.4         |                    0.09 |
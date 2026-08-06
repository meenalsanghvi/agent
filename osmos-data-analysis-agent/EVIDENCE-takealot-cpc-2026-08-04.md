# Evidence dossier — takealot CPC increase, 4 August 2026

**Ticket:** "There's an increase in CPC for product and category pages, please check."
**Marketplace:** takealot-marketplace · agency **105** · marketplace_client_id **100002** ·
**ZAR** · Africa/Johannesburg · **PLA** (`channel = 'os_product_ads'`)
**USD→ZAR conversion factor:** 15.735642
**Worked:** 2026-08-05/06 · **Narrative log:** `ticket-investigations-2026-08-06.md`

This file is the **proof**, not the story. Every claim carries the query that produced it,
the raw output, and a verdict of **PROVEN / REFUTED / UNPROVEN**. Nothing is asserted here
without the data beneath it.

---

## 1. Claim register

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| C1 | CPC increased on the product page | **PARTLY PROVEN** — WoW *fell* 1.9%; Aug 4 alone is a 15-day high | §4.1, §4.2 |
| C2 | CPC increased on the category page | **REFUTED** — WoW fell 4.9% | §4.1 |
| C3 | Aug 4 PRODUCT CPC is the highest in 15 days | **PROVEN** — ZAR 2.8147 vs prior max 2.7729 | §4.2 |
| C4 | Aug 4 survives a like-for-like intraday test | **PROVEN** — hours 0–8: 3.0685 vs max 2.9367 | §4.3 |
| C5 | Aug 3 is part of the spike | **REFUTED** — inside the prior band | §4.2, §4.3 |
| C6 | Aug 5 continued an acceleration | **UNPROVEN, WITHDRAWN** — partial day, early hours run hot | §4.3 |
| C7 | The rise is only a denominator artifact | **PROVEN at page level, INSUFFICIENT as explanation** | §4.4, §5 |
| C8 | Five non-remarketing category caches rose 13–20% | **PROVEN** | §5.1 |
| C9 | Remarketing variants + brand cache did *not* rise | **PROVEN** | §5.1 |
| C10 | A category floor raise caused it | **REFUTED** — distribution bottom unchanged | §6.1, §6.2 |
| C11 | The ZAR 1.50 floor changed | **REFUTED** — identical both days | §6.2 |
| C12 | Advertiser bid changes caused it | **REFUTED** — zero manual bids, 4,289 campaigns | §7.1 |
| C13 | Category-mix shift caused it | **REFUTED** — survives holding category fixed | §8 |
| C14 | Merchant or campaign churn caused it | **REFUTED** — survives paired-entity test | §8 |
| C15 | A real price rise occurred on unchanged cells | **PROVEN** — +11.2%, 879 cells | §8 |
| C16 | Cache migration completed Aug 3 ~14:00 SAST | **PROVEN** — 233→0 in one hour | §9 |
| C17 | The migration *caused* the re-pricing | **UNPROVEN** — timing + ramp shape only | §9, §13 |
| C18 | `raw_bid` is the pre-adjustment input | **UNVERIFIED ASSUMPTION** — no documentation exists | §13 |
| C19 | Financial impact ≈ ZAR 5,273/day (0.57%) | **PROVEN** — arithmetic in §10 | §10 |
| C20 | Marketplace CPC is spiking | **REFUTED** — Aug 4 below 30-day average | §10 |
| C21 | Marketplace CTR is declining 8–10% | **PROVEN** on matched weekdays | §10 |
| C22 | EcoFlow is a clean platform-effect case | **REFUTED** — continuing SKUs' CPC fell 5.3% | §12 |
| C23 | v3 bid multiplier 6.19 caused EcoFlow's SKU rise | **UNPROVEN** — snapshot overwritten post-incident | §12.4 |

**Net:** 11 proven, 8 refuted, 4 unproven. The mechanism is established; the *cause* of the
mechanism is not.

---

## 2. Reproducibility

### Two independent data paths were used

| Path | Auth | Used for |
|---|---|---|
| KAM reports via MCP (`osmos-performance-local`) | kamService service account | page/merchant/budget/audit reports |
| **BigQuery via `bq`** | `meenal.sanghvi@onlinesales.ai` | everything cache-, bid-, SKU- and floor-level |

**Why BQ was necessary, not preferred:** `RESPONDED_SKUS_REPORT` — the only cache-aware
report — hardcodes `page_type = 'SEARCH'` in its frozen SQL. It cannot answer a PRODUCT-page
cache question at any time, under any parameters.

**Billing project matters.** `bigquery.jobs.create` is **denied** on
`prj-onlinesales-vertexai` (the gcloud default), `prj-onlinesales-bq-kam` and
`prj-onlinesales-reporting-prod`. It is **granted** on `prj-onlinesales-prod-01`, which is
where every query in this dossier was billed. `bigquery.tables.list` is denied on the
`reporting` dataset, so table names had to be lifted from the report configs rather than
listed.

### Source tables

| Table | Role |
|---|---|
| `prj-onlinesales-prod-01.reporting.os_product_ads_response_to_clicks_mapping` | clicks, bids, cache_type, page_type, sku, categories |
| `prj-onlinesales-prod-01.reporting.clients` | agency/marketplace/currency join |
| `prj-onlinesales-prod-01.reporting.static_currency_conversion` | USD→ZAR |
| `prj-onlinesales-prod-01.reporting.os_product_ads_product_selection_100002` | bid config, ROI optimiser multipliers |

### Spend definition — identical to the report layer

Spend is the **bid on valid clicks, converted to ZAR** — the bid value multiplied by the
USD→ZAR conversion factor, counted only where the click is flagged valid. This definition was
taken from `INTERNAL_PERF_RESPONDED_SKUS.json` rather than invented, so BQ figures and report
figures are directly comparable. **It is not impression-based.** The reconciliation in §3
confirms the two agree to within 0.1%.

### Date handling

Two timestamps matter and they are not interchangeable. **`click_timestamp_utc` is the
partition key**; **`response_timestamp_utc`, converted to Africa/Johannesburg, is the
semantic date** used for every "Jul 28" / "Aug 4" attribution in this file. Every query
bounded *both* — the semantic date for correctness, the partition key for cost. Bounding only
the semantic date scans the entire table (~277 GB vs ~38 GB pruned).

All dates in this dossier are **Africa/Johannesburg**, not UTC.

---

## 3. Validation — why the derived numbers can be trusted

Three independent reconciliations were run **before** any conclusion was drawn.

| Check | Derived | Measured | Delta |
|---|---|---|---|
| CATEGORY weekly spend, current | 166,747.47 | 166,747.47 | **0.00** |
| CATEGORY weekly clicks, current | 40,710 | 40,710 | **0** |
| CATEGORY weekly spend, baseline | 188,102.68 | 188,102.68 | **0.00** |
| Cache-sum CPC, Jul 28 (BQ) vs page report | 2.6282 | 2.6283 | **0.004%** |
| Cache-sum CPC, Aug 4 (BQ) vs page report | 2.7229 | 2.7257 | **0.103%** |
| Cache rows' share of page-report clicks, Jul 28 | 41,790 / 42,644 | — | **98.0%** |
| Cache rows' share of page-report clicks, Aug 4 | 35,615 / 36,302 | — | **98.1%** |

The ~2% gap is clicks with no `cache_type` mapping. It is **stable across both days**, so it
cannot bias a two-day comparison.

---

## 4. Page level

### 4.1 Week over week — `PAGE_PERFORMANCE_PLA_REPORT`

Jul 29–Aug 4 vs Jul 22–28. Two calls (single-period report).

| Page | Base CPC | Cur CPC | Δ | Base spend | Cur spend | Base share | Cur share | Contrib to Δ |
|---|---|---|---|---|---|---|---|---|
| SEARCH | 6.1430 | 5.7746 | −6.0% | 6,323,854.55 | 5,381,972.87 | 86.21% | 84.58% | 96.84% |
| PRODUCT | 2.6507 | 2.5993 | **−1.9%** | 736,160.22 | 665,005.56 | 10.03% | 10.45% | 7.32% |
| CATEGORY | 4.3080 | 4.0960 | **−4.9%** | 188,102.68 | 166,747.47 | 2.56% | 2.62% | 2.20% |
| CUSTOM | 5.3457 | 5.0159 | −6.2% | 35,966.06 | 102,485.34 | 0.49% | 1.61% | −6.84% |
| HOME | 3.2000 | 3.1132 | −2.7% | 51,439.47 | 46,673.69 | 0.70% | 0.73% | 0.49% |
| **Total** | **5.3402** | **5.0339** | **−5.7%** | **7,335,523.0** | **6,362,885.1** | 100% | 100% | 100% |

**→ C2 REFUTED.** CATEGORY CPC fell. **→ C1 partly refuted** at week granularity.

Raw impressions/clicks behind the above are in §10 (30-day series).

### 4.2 PRODUCT daily CPC, Jul 20 – Aug 4 (15 complete days)

| Date | Day | Spend | Clicks | Impressions | **CPC** |
|---|---|---|---|---|---|
| Jul 20 | Mon | 87,663.39 | 34,328 | 4,592,475 | 2.5537 |
| Jul 21 | Tue | 94,043.18 | 35,964 | 4,828,976 | 2.6153 |
| Jul 22 | Wed | 93,582.84 | 36,802 | 4,991,448 | 2.5429 |
| Jul 23 | Thu | 105,232.11 | 40,019 | 5,389,232 | 2.6296 |
| Jul 24 | Fri | 109,372.33 | 39,447 | 5,270,008 | **2.7729** ← prior max |
| Jul 25 | Sat | 101,639.06 | 37,196 | 4,437,547 | 2.7329 |
| Jul 26 | Sun | 100,827.05 | 38,459 | 4,821,860 | 2.6217 |
| Jul 27 | Mon | 111,683.75 | 43,157 | 6,248,972 | 2.5878 |
| Jul 28 | Tue | 113,823.09 | 42,644 | 6,074,028 | 2.6691 |
| Jul 29 | Wed | 108,046.13 | 41,643 | 5,586,979 | 2.5946 |
| Jul 30 | Thu | 102,745.56 | 39,598 | 5,479,373 | 2.5947 |
| Jul 31 | Fri | 91,791.43 | 35,653 | 5,015,641 | 2.5750 |
| Aug 1 | Sat | 81,457.85 | 32,890 | 4,186,195 | 2.4767 |
| Aug 2 | Sun | 85,208.11 | 34,237 | 4,520,893 | 2.4890 |
| Aug 3 | Mon | 93,575.10 | 35,516 | 5,489,433 | 2.6350 |
| **Aug 4** | **Tue** | **102,183.04** | **36,303** | **5,468,261** | **2.8147** |

**→ C3 PROVEN.** 2.8147 > 2.7729. **→ C5 REFUTED**: Aug 3 at 2.6350 sits inside the
14-day band (2.4767–2.7729).

### 4.3 Partial-day control — full day vs hours 0–8

Same-hours comparison to remove partial-day bias.

| Date | Last hour with clicks | Clicks (full) | **CPC full** | Clicks h0–8 | **CPC h0–8** |
|---|---|---|---|---|---|
| Jul 28 | 23 | 41,790 | 2.6661 | 10,648 | 2.9367 |
| Jul 29 | 23 | 40,803 | 2.5960 | 9,492 | 2.8605 |
| Jul 30 | 23 | 38,795 | 2.5932 | 9,487 | 2.8060 |
| Jul 31 | 23 | 34,939 | 2.5751 | 9,694 | 2.7571 |
| Aug 1 | 23 | 32,181 | 2.4787 | 8,731 | 2.7374 |
| Aug 2 | 23 | 33,462 | 2.4856 | 8,110 | 2.8904 |
| Aug 3 | 23 | 34,847 | 2.6328 | 7,558 | 2.8412 |
| **Aug 4** | 23 | 35,615 | **2.8124** | 8,653 | **3.0685** |
| Aug 5 | **12** ⚠ | 13,296 | 3.0363 | 7,765 | 3.0541 |

**→ C4 PROVEN.** Aug 4's h0–8 CPC of 3.0685 is **+4.5%** above the highest prior day
(2.9367). **→ C6 WITHDRAWN**: hours 0–8 CPC exceeds full-day CPC on *every* day
(2.74–2.94 vs 2.48–2.67), so a quarter-complete day structurally overstates the level.
Aug 5 is excluded from all conclusions.

### 4.4 The aggregate two-day read

Aug 3–4 vs Jul 27–28 (Mon–Tue vs Mon–Tue):

| Metric | Jul 27–28 | Aug 3–4 | Δ |
|---|---|---|---|
| **CPC** | 2.6283 | 2.7257 | **+3.71%** |
| Spend | 225,506.84 | 195,756.48 | −13.19% |
| Clicks | 85,801 | 71,818 | −16.30% |
| Impressions | 12,323,000 | 10,957,694 | −11.08% |
| CTR | 0.6963% | 0.6552% | −5.91% |

Arithmetic check: 0.8681 ÷ 0.8370 = **1.0372** ✓ — the ratio rise is fully explained by the
denominator falling faster.

**→ C7: PROVEN at this level, and this is where a shallower investigation would have
stopped and been wrong.** §5 shows what it concealed.

---

## 5. Cache level — the decisive drill

### 5.1 All caches, PRODUCT page, Tue Jul 28 → Tue Aug 4

Full daily series Jul 28–Aug 4 was pulled; endpoints
shown.

| Cache type | Clk J28 | Spend J28 | CPC J28 | Clk A4 | Spend A4 | CPC A4 | **CPC Δ** | Clk Δ |
|---|---|---|---|---|---|---|---|---|
| GRANULAR_SOLR_CATEGORY | 5,841 | 16,057.30 | 2.7491 | 5,503 | 18,098.38 | 3.2888 | **+19.6%** | −5.8% |
| CATEGORY_PRICE_DISCOUNT_BUCKET_TOP_SELLING_L3 | 3,746 | 8,218.70 | 2.1940 | 1,668 | 4,342.35 | 2.6033 | **+18.7%** | −55.5% |
| CATEGORY_TOP_POPULAR_PRODUCTS | 1,540 | 3,769.44 | 2.4477 | 1,217 | 3,446.23 | 2.8317 | **+15.7%** | −21.0% |
| BRAND_GRANULAR_CATEGORY | 3,636 | 10,778.64 | 2.9644 | 3,475 | 11,869.65 | 3.4157 | **+15.2%** | −4.4% |
| SOLR_CATEGORY | 2,632 | 6,639.18 | 2.5225 | 2,117 | 6,036.11 | 2.8513 | **+13.0%** | −19.6% |
| UA_MERCHANT_CACHE | 922 | 2,131.47 | 2.3118 | 669 | 1,603.21 | 2.3964 | +3.7% | −27.4% |
| SOLR_CATEGORY_REMARKETING | 6,475 | 14,732.06 | 2.2752 | 5,888 | 12,954.75 | 2.2002 | **−3.3%** | −9.1% |
| UA_BRAND_CACHE *(control)* | 6,352 | 18,976.80 | 2.9875 | 4,591 | 13,070.84 | 2.8471 | **−4.7%** | −27.7% |
| GRANULAR_SOLR_CATEGORY_REMARKETING | 130 | 306.77 | 2.3598 | 38 | 81.59 | 2.1472 | **−9.0%** | −70.8% |
| NOVELTY_CATEGORY_CACHE | 1,764 | 7,400.53 | 4.1953 | 1,641 | 5,347.34 | 3.2586 | **−22.3%** | −7.0% |
| SIMILAR_SKU_CACHE | 8,752 | 22,404.67 | 2.5599 | **0** | 0 | — | *retired* | −100% |
| SIMILAR_ITEM_GROUP_CACHE | 0 | 0 | — | 8,808 | 23,311.88 | 2.6467 | *new* | — |
| **Blended** | **41,790** | | **2.6661** | **35,615** | | **2.8123** | **+5.5%** | −14.8% |

**→ C8 PROVEN** (five caches, all ≥13%). **→ C9 PROVEN**: both remarketing variants and the
brand cache fell.

**The structural fact that constrains any explanation:** every riser is a *non-remarketing
category* cache. A cause that hits category-relevancy pricing but spares its own remarketing
variants, and pushes one sibling **down 22.3%** on the same day, is narrow and structured —
not marketplace-wide auction competition.

### 5.2 Full daily cache series (5 tracked caches, Jul 22 – Aug 4)

Clicks / spend per day, showing the migration ramp:

| Date | SIMILAR_SKU clk | SIMILAR_ITEM_GROUP clk | GRAN_SOLR_CAT clk | BRAND_GRAN_CAT clk | UA_BRAND clk |
|---|---|---|---|---|---|
| Jul 22 | 7,261 | — | 5,498 | 2,698 | 6,435 |
| Jul 23 | 7,304 | — | 5,501 | 3,495 | 6,703 |
| Jul 24 | 7,859 | — | 5,376 | 3,352 | 6,302 |
| Jul 25 | 6,815 | — | 5,220 | 3,105 | 6,104 |
| Jul 26 | 7,113 | — | 5,401 | 3,036 | 5,910 |
| Jul 27 | 8,926 | — | 5,969 | 3,689 | 6,343 |
| Jul 28 | 8,752 | — | 5,841 | 3,636 | 6,352 |
| Jul 29 | 9,049 | — | 5,449 | 3,521 | 6,229 |
| Jul 30 | 8,202 | — | 5,512 | 3,447 | 5,609 |
| **Jul 31** | 7,046 | **162** ← canary | 5,074 | 3,279 | 5,029 |
| Aug 1 | 5,718 | 366 | 4,681 | 2,871 | 4,867 |
| Aug 2 | 5,975 | 384 | 5,211 | 3,087 | 4,270 |
| **Aug 3** | 3,248 | **4,613** | 5,527 | 3,511 | 4,317 |
| **Aug 4** | **0** | **8,808** | 5,503 | 3,475 | 4,591 |

CPC on the two risers, daily: GRANULAR_SOLR_CATEGORY 2.7491 → 2.8051 → 2.7895 → 2.8239 →
2.6825 → 2.5878 → **3.0345** → **3.2888**. BRAND_GRANULAR_CATEGORY 2.9644 → 2.9156 →
3.0116 → 3.0009 → 2.7981 → 2.8158 → **3.2400** → **3.4157**.

Both step up on Aug 3 **and again** on Aug 4 from a common Aug 1–2 weekend trough — a
two-stage ramp, not a single jump.

---

## 6. Refuting the floor hypothesis

### 6.1 Bid distribution

`raw_bid` percentiles (USD), GRANULAR_SOLR_CATEGORY + BRAND_GRANULAR_CATEGORY:

| Day | Cache | n | **raw_min** | **raw_p01** | raw_p05 | raw_p25 | raw_p50 | raw_p90 |
|---|---|---|---|---|---|---|---|---|
| Jul 28 | BRAND_GRANULAR_CATEGORY | 3,636 | **0.014** | **0.02** | 0.04 | 0.08 | 0.13 | 0.23 |
| Aug 4 | BRAND_GRANULAR_CATEGORY | 3,475 | **0.014** | **0.02** | 0.04 | 0.09 | 0.15 | 0.27 |
| Jul 28 | GRANULAR_SOLR_CATEGORY | 5,841 | **0.014** | **0.02** | 0.04 | 0.08 | 0.13 | 0.23 |
| Aug 4 | GRANULAR_SOLR_CATEGORY | 5,503 | **0.014** | **0.02** | 0.04385 | 0.09 | 0.15 | 0.27 |

Charged `bid` on the same rows: `bid_min` **0.0** and `bid_p05` **0.09532** on *all four*
rows; `bid_p50` 0.10532 → 0.11444 (BGC) and 0.10532 → 0.10532 (GSC).

Upper tail, GRANULAR_SOLR_CATEGORY ():

| Day | n | bid mean | bid p75 | bid p90 | bid p99 | **bid max** | raw mean | raw p99 | raw max |
|---|---|---|---|---|---|---|---|---|---|
| Jul 28 | 5,841 | 0.17470 | 0.18912 | 0.32362 | 0.91908 | **3.1775** | 0.13498 | 0.33 | 0.53 |
| Aug 4 | 5,503 | 0.20900 | 0.23623 | 0.44186 | 1.12368 | **3.1775** | 0.15459 | 0.34 | 0.93658 |

**→ C10 REFUTED.** A floor raise truncates the distribution from below and creates a mass
point at the new floor. Here **min, p01 and p05 are unchanged** while p25/p50/p90 rose
12–17%. That is the opposite shape. `bid_max` is identical (3.1775) — an unchanged hard cap.

### 6.2 Floor share

| Metric | Aug 2 | Aug 4 | Δ |
|---|---|---|---|
| Total clicks | 33,462 | 35,615 | +6.4% |
| Clicks at **exactly ZAR 1.50** | 19,401 | 19,329 | **−0.4%** |
| **Share at floor** | **57.98%** | **54.27%** | −3.71pp |
| `min_click_price_zar` | 0.0 | 0.0 | — |
| Derived: above-floor clicks | 14,061 | 16,286 | **+15.8%** |
| Derived: above-floor CPC | **3.8455** | **4.3699** | **+13.6%** |

**→ C11 REFUTED.** ZAR 1.50 = USD 0.09532 × 15.735642, matching the `bid_p05` value that is
identical on both days.

**Mechanism exposed:** the floor-priced click count is *flat*. **Every additional click
arrived above the floor**, and above-floor clicks got 13.6% more expensive. Two compounding
effects, neither involving a floor change.

---

## 7. Refuting advertiser action

### 7.1 Bid diagnostics

Raw output, USD, PRODUCT page:

| Day | Cache | bid_type | clicks | **avg bid** | **avg original_bid** | **avg raw_bid** |
|---|---|---|---|---|---|---|
| Jul 28 | BRAND_GRANULAR_CATEGORY | AUTO_CPC | 3,166 | 0.19237 | 0.22763 | 0.13364 |
| Aug 4 | BRAND_GRANULAR_CATEGORY | AUTO_CPC | 3,076 | **0.22071** | **0.26545** | **0.15276** |
| Jul 28 | BRAND_GRANULAR_CATEGORY | ROI | 470 | 0.16157 | 0.19066 | 0.12606 |
| Aug 4 | BRAND_GRANULAR_CATEGORY | ROI | 399 | 0.18900 | 0.24055 | 0.14865 |
| Jul 28 | GRANULAR_SOLR_CATEGORY | AUTO_CPC | 5,118 | 0.17881 | 0.25613 | 0.13573 |
| Aug 4 | GRANULAR_SOLR_CATEGORY | AUTO_CPC | 4,832 | **0.21111** | **0.30872** | **0.15493** |
| Jul 28 | GRANULAR_SOLR_CATEGORY | ROI | 723 | 0.14563 | 0.20087 | 0.12969 |
| Aug 4 | GRANULAR_SOLR_CATEGORY | ROI | 671 | **0.19388** | **0.30873** | 0.15219 |
| Jul 28 | **UA_BRAND_CACHE** | AUTO_CPC | 5,489 | 0.19779 | 0.25128 | 0.10939 |
| Aug 4 | **UA_BRAND_CACHE** | AUTO_CPC | 3,988 | **0.18755** | **0.24025** | **0.11257** |
| Jul 28 | **UA_BRAND_CACHE** | ROI | 863 | 0.13939 | 0.16170 | 0.12531 |
| Aug 4 | **UA_BRAND_CACHE** | ROI | 603 | 0.13718 | 0.16373 | 0.13626 |

Percent changes:

| Cache | bid_type | bid Δ | original_bid Δ | **raw_bid Δ** |
|---|---|---|---|---|
| GRANULAR_SOLR_CATEGORY | AUTO_CPC | +18.1% | +20.5% | **+14.1%** |
| GRANULAR_SOLR_CATEGORY | ROI | +33.1% | +53.7% | +17.3% |
| BRAND_GRANULAR_CATEGORY | AUTO_CPC | +14.7% | +16.6% | **+14.3%** |
| BRAND_GRANULAR_CATEGORY | ROI | +17.0% | +26.2% | +17.9% |
| **UA_BRAND_CACHE (control)** | AUTO_CPC | **−5.2%** | −4.4% | **+2.9%** |
| **UA_BRAND_CACHE (control)** | ROI | −1.6% | +1.3% | +8.7% |

**→ C12 REFUTED, on four grounds:**

1. **Only `AUTO_CPC` and `ROI` bid types exist** on these caches — the `STRING_AGG(DISTINCT
   bid_type)` returned nothing else across 4,289 campaigns / 1,729 merchants. **Zero manual
   bids.** Advertisers do not set the bid; the system does.
2. **`raw_bid` — the pre-adjustment input — rose ~14% on both movers, +2.9% on the control.**
   Competition raises what you *pay*, not your bid *input*.
3. **Bid-type mix is stable**: ROI click share 12.4% → 12.2% (GSC) and 12.9% → 11.5% (BGC).
   Not a composition artifact.
4. **The control is decisive.** Same page, same two days, largely the same advertisers —
   and UA_BRAND_CACHE's bids *fell*.

### 7.2 Ramp, not step — hourly `raw_bid`

From GRANULAR_SOLR_CATEGORY click-weighted `raw_bid` by day:
**≈0.135 (Aug 2) → 0.147 (Aug 3) → 0.155 (Aug 4)**, climbing progressively within and
across days rather than jumping at one hour.

**A config flag produces an instantaneous step at a specific hour. An automated bidder
adapting produces a ramp. The data shows a ramp.**

---

## 8. Refuting mix effects — three decompositions

. All on GRANULAR_SOLR_CATEGORY,
Jul 28 vs Aug 4. "Fixed-mix" = Laspeyres: Aug-4 unit prices at Jul-28 click weights.

| Keyed on | Entities J28 / A4 / paired | Paired CPC J28 → A4 | **Fixed-mix CPC** | **Pure price Δ** | Coverage J28 / A4 |
|---|---|---|---|---|---|
| Campaign | 2,129 / 2,097 / **890** | 2.6862 → 2.9562 (+10.1%) | 2.8927 | **+7.7%** | 59.0% / 56.0% |
| **Merchant** | 1,057 / 1,072 / **661** | 2.7089 → 3.0865 (+13.9%) | 3.0173 | **+11.4%** | **82.8% / 81.0%** |
| Merchant × `resp_category_l1` | — / — / **879 cells** | 2.7388 → 3.1347 (+14.5%) | 3.0460 | **+11.2%** | 69.6% / 66.5% |

Entrant/exit cohorts (merchant-keyed):

| Cohort | CPC | Clicks |
|---|---|---|
| New merchants (absent Jul 28) | 4.1520 | 1,045 |
| Churned merchants (absent Aug 4) | 2.9421 | 1,007 |

Campaign-keyed equivalents: new 3.7122 (2,421 clicks), churned 2.8397 (2,393 clicks).

**→ C13 and C14 REFUTED. → C15 PROVEN.**

**Why merchant-keying is the correct choice, not a convenience:** campaign IDs churn **58%
per week** (890 of ~2,100 present both days) because sellers re-create campaigns — the
behaviour documented in `ticket-investigations-2026-08-05.md` ticket 2, where one seller
re-created the same campaign eight times since 2 June. Merchant IDs survive re-creation:
churn 38%, coverage 82.8% vs 59.0%.

### 8.1 Category breakdown within the cache

| `resp_category_l1` | Clk J28 | CPC J28 | Clk A4 | CPC A4 | Δ |
|---|---|---|---|---|---|
| Home & Kitchen | 1,553 | 2.6542 | 1,484 | 3.1325 | **+18.0%** |
| Health | 679 | 3.5469 | 642 | 4.3899 | **+23.8%** |
| Fashion | 576 | 2.6100 | 627 | 3.1051 | **+19.0%** |
| Computers & Tablets | 466 | 3.0378 | 394 | 3.4876 | +14.8% |
| Office & Stationery | 307 | 2.9963 | 329 | 3.7175 | **+24.1%** |
| Sport | 316 | 3.0094 | 324 | 3.9728 | **+32.0%** |
| Garden, Pool & Patio | 308 | 4.2161 | 310 | 4.7346 | +12.3% |
| Beauty | 272 | 1.6927 | 199 | 1.7887 | +5.7% |
| Automotive | 169 | 1.7250 | 192 | 1.6394 | **−5.0%** |
| Baby & Toddler | 248 | 1.8845 | 184 | 2.0005 | +6.2% |
| TV, Audio & Video | 258 | 2.5902 | 155 | 4.0856 | **+57.7%** |
| Toys | 147 | 2.3475 | 146 | 2.2858 | **−2.6%** |

**10 of 12 up**, most double-digit, click volumes broadly stable. Not concentrated.

### 8.2 Breadth test

| Metric | Value |
|---|---|
| Merchants with ≥30 clicks **both** days | **20** |
| CPC rose | **15 (75.0%)** |
| CPC fell | 5 |
| Median CPC change | **+5.94%** |
| p25 / p75 | −1.05% / +36.24% |

**Stated limitation:** 20 merchants only, because spend is so fragmented that few clear 30
clicks on these two caches in both windows. Directionally consistent; **the bid-column
evidence in §7 carries the conclusion, not this test.**

### 8.3 Concentration

| Metric | Value |
|---|---|
| Campaigns on the two movers | **4,289** |
| Merchants | **1,729** |
| Rows | 18,455 |
| NULL campaign_id | 0 |
| Top merchant's Aug 4 spend | **ZAR 335.93** of ~30,000 (**1.1%**) |

A ZAR 1,500 threshold on campaign-level spend returned **zero rows** — average spend is
~ZAR 7/campaign/day. **No merchant table is meaningful for this finding**; a top-N ranking
would be padding.

---

## 9. Dating the platform change

Raw output, Aug 3, PRODUCT page:

| Hour (SAST) | GSC clicks | GSC raw_bid | GSC bid | **SIMILAR_ITEM_GROUP** | **SIMILAR_SKU** |
|---|---|---|---|---|---|
| 09 | 283 | 0.15478 | 0.23455 | 32 | 465 |
| 10 | 324 | 0.14900 | 0.19595 | 26 | 383 |
| 11 | 295 | 0.15400 | 0.23515 | 25 | 376 |
| 12 | 303 | 0.15427 | 0.23116 | 33 | 365 |
| **13** | 331 | 0.15437 | 0.20072 | **195** | **233** |
| **14** | 288 | 0.15369 | 0.19412 | **467** | **0** |
| 15 | 274 | 0.15138 | 0.21454 | 449 | 0 |
| 16 | 249 | 0.14466 | 0.19417 | 387 | 0 |
| 17 | 239 | 0.15452 | 0.19127 | 445 | 0 |
| 18 | 309 | 0.16445 | 0.22422 | 457 | 0 |
| 19 | 363 | 0.13876 | 0.17048 | 544 | 0 |
| 20 | 412 | 0.13976 | 0.17634 | 522 | 0 |
| 21 | 391 | 0.13842 | 0.16048 | 459 | 0 |
| 22 | 273 | 0.14402 | 0.13608 | 295 | 0 |
| 23 | 156 | 0.14120 | 0.14735 | 153 | 0 |

**→ C16 PROVEN.** `SIMILAR_SKU_CACHE` drops **233 → 0** between 13:00 and 14:00 on
2026-08-03 and never serves again. Canary began Jul 31 (162 clicks).

**→ C17 UNPROVEN.** The migration precedes the spike by one day and the re-pricing ramps
over the following ~24h, but **no deploy log, release note or ownership confirmation was
obtained.** Correlation plus mechanism shape only. Also unexplained under this hypothesis:
why `NOVELTY_CATEGORY_CACHE` moved **−22.3%** the same day.

The migration itself is volume-neutral (8,752 → 8,808 clicks) at **+3.4%** CPC — a secondary
contributor, not the driver.

---

## 10. Marketplace context and impact sizing

### 10.1 30-day PLA series, Jul 6 – Aug 4 (`PAGE_PERFORMANCE_PLA_REPORT`, all pages)

| Date | Day | Spend | Clicks | Impressions | CPC | CTR |
|---|---|---|---|---|---|---|
| Jul 6 | Mon | 843,044.48 | 169,955 | 12,002,083 | 4.9604 | 1.4160% |
| Jul 7 | Tue | 853,457.10 | 173,987 | 12,184,279 | 4.9053 | 1.4279% |
| Jul 8 | Wed | 867,234.05 | 174,146 | 11,962,958 | 4.9799 | 1.4557% |
| Jul 9 | Thu | 897,172.84 | 179,070 | 12,121,973 | 5.0102 | 1.4774% |
| Jul 10 | Fri | 797,092.03 | 161,165 | 10,609,693 | 4.9458 | 1.5186% |
| Jul 11 | Sat | 755,387.81 | 150,071 | 9,215,748 | 5.0335 | 1.6284% |
| Jul 12 | Sun | 823,868.57 | 161,266 | 10,080,207 | 5.1088 | 1.5998% |
| Jul 13 | Mon | 896,080.11 | 180,165 | 12,324,987 | 4.9714 | 1.4620% |
| Jul 14 | Tue | 922,383.99 | 183,019 | 12,569,971 | 5.0398 | 1.4556% |
| Jul 15 | Wed | 1,003,018.38 | 197,500 | 13,874,857 | 5.0786 | 1.4234% |
| Jul 16 | Thu | 901,235.43 | 178,646 | 12,158,175 | 5.0448 | 1.4693% |
| Jul 17 | Fri | 833,660.92 | 164,927 | 10,957,055 | 5.0547 | 1.5052% |
| Jul 18 | Sat | 764,613.27 | 157,775 | 9,685,649 | 4.8462 | 1.6289% |
| Jul 19 | Sun | 806,550.79 | 181,456 | 10,836,207 | **4.4449** | **1.6746%** |
| Jul 20 | Mon | 957,385.33 | 186,788 | 12,415,842 | 5.1259 | 1.5040% |
| Jul 21 | Tue | 995,969.43 | 191,216 | 12,926,846 | 5.2086 | 1.4792% |
| Jul 22 | Wed | 995,414.70 | 193,622 | 13,183,852 | 5.1410 | 1.4686% |
| Jul 23 | Thu | 1,071,574.66 | 200,078 | 13,702,983 | 5.3558 | 1.4601% |
| Jul 24 | Fri | 1,027,232.78 | 189,965 | 13,207,497 | 5.4075 | 1.4382% |
| Jul 25 | Sat | 1,003,984.61 | 181,107 | 11,743,709 | **5.5436** | 1.5422% |
| Jul 26 | Sun | 1,042,453.43 | 192,254 | 12,616,444 | 5.4223 | 1.5238% |
| Jul 27 | Mon | 1,093,118.42 | 208,842 | **15,081,372** | 5.2342 | 1.3848% |
| Jul 28 | Tue | **1,101,744.40** | **207,763** | 14,974,155 | 5.3029 | 1.3875% |
| Jul 29 | Wed | 1,051,417.61 | 205,452 | 14,242,233 | 5.1176 | 1.4426% |
| Jul 30 | Thu | 997,738.11 | 191,382 | 13,546,365 | 5.2133 | 1.4128% |
| Jul 31 | Fri | 872,720.17 | 170,467 | 12,297,250 | 5.1196 | 1.3862% |
| Aug 1 | Sat | 791,107.94 | 159,772 | 10,822,339 | 4.9515 | 1.4763% |
| Aug 2 | Sun | 851,087.47 | 171,697 | 11,696,888 | 4.9569 | 1.4679% |
| Aug 3 | Mon | 880,874.05 | 181,126 | 13,410,356 | 4.8633 | **1.3507%** |
| Aug 4 | Tue | 918,025.65 | 184,099 | 13,551,960 | **4.9855** | 1.3585% |
| **30-day** | | **27,616,648.52** | **5,428,778** | **370,003,933** | **5.0871** | **1.4672%** |

**→ C20 REFUTED.** Aug 4 CPC (4.9855) is **below** the 30-day average (5.0871) and far below
the Jul 23–26 peak (5.3558–5.5436).

**→ C21 PROVEN**, on matched weekdays only:

| Comparison | Peak | August | Δ |
|---|---|---|---|
| Mondays | 1.5040% (Jul 20) | 1.3507% (Aug 3) | **−10.2%** |
| Tuesdays | 1.4792% (Jul 21) | 1.3585% (Aug 4) | **−8.2%** |
| 14-day aggregate | 1.5022% (Jul 6–19) | 1.4329% (Jul 22–Aug 4) | −4.6% |

A superseded figure of "~16%" compared Sunday Jul 19 (1.6746%) against Monday Aug 3 — an
unfair weekday pairing. The matched figures above replace it.

### 10.2 Impact arithmetic

| Line | Value |
|---|---|
| PRODUCT actual spend, Aug 4 | 102,181.39 |
| Clicks, Aug 4 | 36,303 |
| Counterfactual at Jul 28 CPC (36,303 × 2.6691) | 96,908.40 |
| **Net excess** | **≈ 5,273** |
| Aug 4 marketplace PLA spend | 918,025.65 |
| **Excess as share** | **0.57%** |
| Five affected caches' Aug 4 spend | 43,793 (**4.8%** of PLA spend) |
| Annualised if sustained | ≈ 1.9M |
| Offset: NOVELTY_CATEGORY_CACHE −22% saved | ≈ 1,537/day |
| Offset: UA_BRAND_CACHE saved | ≈ 644/day |

**→ C19 PROVEN.**

---

## 11. Merchant-level analysis, Aug 2 vs Aug 4

⚠ **Aug 2 is a Sunday, Aug 4 a Tuesday.** This comparison largely measures weekday
participation. One sub-result survives the confound; the rest do not.

### 11.1 Cohorts

| Cohort | Merchants | Aug 2 spend | Aug 4 spend | Δ | Contrib | CPC | Clicks |
|---|---|---|---|---|---|---|---|
| **Retained** | **1,503** | 79,124.50 | 80,935.10 | +1,810.60 | **+10.7%** | 2.4677 → **2.7213 (+10.3%)** | 32,064 → 29,741 |
| Added | 458 | — | 19,228.51 | +19,228.51 | +113.2% | 3.2735 | 5,874 |
| Moved away | 296 | 4,046.95 | — | −4,046.95 | −23.8% | 2.8948 | 1,398 |
| **Total** | **2,257** | **83,172.05** | **100,162.32** | **+16,990.27** | 100% | 2.4856 → 2.8123 | 33,462 → 35,615 |

Active merchants 1,799 → 1,961.

**Survives the confound:** retained cohort **+10.3% CPC on 7.2% fewer clicks** — not a
participation effect, and independently consistent with the +11.4% in §8.
**Does not survive:** the +113.2% "added" contribution is small advertisers who don't serve
Sundays. Not acquisition.

### 11.2 Top movers, |Δ| > ZAR 250

| Merchant | ID | Aug 2 | Clk | CPC | Aug 4 | Clk | CPC | Δ | Contrib | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| SNT Sports | R1075 | 0.00 | 0 | — | 707.31 | 61 | 11.595 | +707.31 | 4.16% | ADDED |
| VER MR AMERICA | M29829379 | 279.74 | 69 | 4.054 | 823.40 | 143 | 5.758 | +543.66 | 3.20% | retained |
| BuildSaver | M29827693 | 0.00 | 0 | — | 444.65 | 77 | 5.775 | +444.65 | 2.62% | ADDED |
| Topika | M29886965 | 469.36 | 209 | 2.246 | 890.73 | 342 | 2.604 | +421.37 | 2.48% | retained |
| Yzaanshop | M29896074 | 21.55 | 6 | 3.592 | 435.21 | 146 | 2.981 | +413.66 | 2.43% | retained |
| Homemark | M9897 | 27.00 | 18 | **1.500** | 433.44 | 100 | 4.334 | +406.44 | 2.39% | retained |
| AC/DC DYNAMICS | M29825263 | 19.50 | 13 | **1.500** | 423.01 | 79 | 5.355 | +403.51 | 2.37% | retained |
| EcoFlow | M29877282 | 27.22 | 10 | 2.722 | 390.64 | 77 | 5.073 | +363.41 | 2.14% | retained |
| App – Tevo | R361 | 0.00 | 0 | — | 363.37 | 68 | 5.344 | +363.37 | 2.14% | ADDED |
| Relevium Health | M29828911 | 0.00 | 0 | — | 346.77 | 35 | 9.908 | +346.77 | 2.04% | ADDED |
| Greenlane Gear | M29824624 | 35.35 | 6 | 5.891 | 325.82 | 96 | 3.394 | +290.47 | 1.71% | retained |
| LOWKAL | M29892931 | 0.00 | 0 | — | 278.12 | 47 | 5.917 | +278.12 | 1.64% | ADDED |
| Avtel | M29869968 | 52.30 | 5 | 10.460 | 322.72 | 162 | 1.992 | +270.42 | 1.59% | retained |
| MM Trading | M29851699 | 260.05 | 97 | 2.681 | 8.66 | 4 | 2.164 | −251.39 | −1.48% | retained |
| 3G Mobile – Huawei | R29893748 | 555.57 | 349 | 1.592 | 271.81 | 166 | 1.637 | −283.76 | −1.67% | retained |
| Epic Vendor Services | M29894392 | 641.16 | 153 | 4.191 | 341.47 | 95 | 3.594 | −299.69 | −1.76% | retained |

Max single contribution **4.16%**.

### 11.3 Decliner causes — `AUDIT_EVENTS_REPORT` action 16

| Merchant | Cause | Evidence |
|---|---|---|
| 3G Mobile – Huawei | **Campaign paused** | `SMP_SP_Auto_14_14i_4.23` (1216655) ACTIVE → PAUSED **2026-08-03 06:07:55**. Wallet ~295,000 — not budget |
| MM Trading | **Wallet exhaustion** *(inferred)* | No status change; current balance **ZAR 1.09**. Aug-4 balance not directly observable |
| Mobile Complete (R2326) | Campaign lifecycle | Paused Aug 2 20:23, reactivated Aug 3 13:21 — but decline ran Jul 30–Aug 2, *before* both events |
| Beauty – Loreal (R293) | Active rotation | 6 new campaigns DRAFT→LAUNCH 12:00–12:12 Aug 4, **ACTIVE 17:00–17:01**; 1349441 paused 16:00:53. Live at 17:00 → minimal Aug-4 effect |

### 11.4 Buckets, 1,503 retained merchants

| Bucket | Merch | % | Spend A2 | Share A2 | Spend A4 | Share A4 | Shift | Δ | Clk A2 | Clk A4 | CPC A2 | CPC A4 | **CPC Δ** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ≤ −75% | 128 | 8.5% | 4,062.05 | 5.13% | 529.39 | 0.65% | −4.48pp | −3,532.67 | 1,293 | 226 | 3.142 | 2.342 | **−25.4%** |
| −75..−50% | 218 | 14.5% | 9,280.17 | 11.73% | 3,636.63 | 4.49% | −7.24pp | −5,643.54 | 3,718 | 1,626 | 2.496 | 2.237 | **−10.4%** |
| −50..−25% | 229 | 15.2% | 14,842.55 | 18.76% | 9,334.88 | 11.53% | −7.23pp | −5,507.67 | 6,046 | 3,999 | 2.455 | 2.334 | −4.9% |
| −25..−10% | 140 | 9.3% | 13,442.83 | 16.99% | 11,180.59 | 13.82% | −3.17pp | −2,262.24 | 5,791 | 4,662 | 2.321 | 2.398 | +3.3% |
| **flat** | 208 | 13.8% | 16,289.13 | **20.59%** | 16,048.37 | **19.83%** | −0.76pp | −240.76 | 6,651 | 6,350 | 2.449 | 2.527 | +3.2% |
| +10..25% | 71 | 4.7% | 4,716.54 | 5.96% | 5,472.53 | 6.76% | +0.80pp | +755.99 | 1,792 | **1,824** | 2.632 | 3.000 | **+14.0%** |
| +25..50% | 111 | 7.4% | 6,604.48 | 8.35% | 9,131.43 | 11.28% | +2.93pp | +2,526.95 | 3,027 | 3,533 | 2.182 | 2.585 | **+18.5%** |
| +50..100% | 128 | 8.5% | 5,836.34 | 7.38% | 10,038.54 | 12.40% | +5.02pp | +4,202.20 | 2,170 | 2,989 | 2.690 | 3.358 | **+24.9%** |
| +100..300% | 182 | 12.1% | 3,216.68 | 4.07% | 8,402.91 | 10.38% | +6.31pp | +5,186.23 | 1,264 | 2,586 | 2.545 | 3.249 | **+27.7%** |
| > +300% | 88 | 5.9% | 834.31 | 1.05% | 7,158.54 | 8.84% | +7.79pp | +6,324.23 | 312 | 1,946 | 2.674 | 3.679 | **+37.6%** |
| **Total** | **1,503** | 100% | **79,125** | 100% | **80,934** | 100% | — | **+1,809** | 32,064 | 29,741 | 2.468 | 2.721 | **+10.3%** |

Gross churn: decrease **715 merchants / −17,187**; increase **580 / +18,996**; flat
**208 / −241**. Total gross **36,183 = 45.8%** of the Aug-2 retained base, netting to +1,809.
**715 merchants (47.6%) spent less on a day the page grew 20.4%.**

Share redistribution: decliners **35.62% → 16.67% (−18.95pp)**; middle 43.54% → 40.41%;
growers **20.85% → 42.90% (+22.05pp)**.

**Bucket 6 is the cleanest harm case:** 71 merchants, clicks **+1.8%**, CPC **+14.0%** —
same volume, 14% more money.

**Stated limitation:** the CPC gradient is partly mechanical (spend = clicks × CPC), so
bucketing on spend and reading CPC leans positive by construction. Buckets 9/A rest on
~3.5 clicks/merchant on Aug 2.

### 11.5 Cache mix by bucket group

Clicks Aug 2 → Aug 4. Tests whether the migration reallocated volume between merchants.

| Cache | Decliners (≤−25%) | Middle | **Growers (≥+100%)** |
|---|---|---|---|
| GRANULAR_SOLR_CATEGORY | 1,805 → 942 (−48%) | 2,867 → 2,660 (−7%) | 256 → 732 (**+186%**) |
| SOLR_CATEGORY_REMARKETING | 1,462 → 1,048 (−28%) | 2,928 → 3,699 (+26%) | 197 → 594 (**+202%**) |
| UA_BRAND_CACHE | 1,204 → 682 (−43%) | 2,751 → 2,908 (+6%) | 213 → 653 (**+207%**) |
| BRAND_GRANULAR_CATEGORY | 1,164 → 533 (−54%) | 1,565 → 1,636 (+5%) | 147 → 460 (**+213%**) |
| SOLR_CATEGORY | 1,032 → 304 (−71%) | 1,557 → 1,119 (−28%) | 107 → 324 (**+203%**) |
| CATEGORY_PRICE_DISCOUNT_..._L3 | 1,110 → 285 (−74%) | 1,993 → 911 (−54%) | 142 → 189 (+33%) |
| NOVELTY_CATEGORY_CACHE | 520 → 210 (−60%) | 676 → 549 (−19%) | 72 → 318 (**+342%**) |
| CATEGORY_TOP_POPULAR_PRODUCTS | 498 → 201 (−60%) | 871 → 635 (−27%) | 70 → 198 (**+183%**) |
| UA_MERCHANT_CACHE | 201 → 107 | 382 → 391 | — |
| SIMILAR_SKU_CACHE | 1,907 → 0 | 3,555 → 0 | 306 → 0 |
| SIMILAR_ITEM_GROUP_CACHE | 131 → 1,533 | 217 → 4,826 | 17 → 994 |
| **Total** | **11,034 → 5,845 (−47%)** | **19,362 → 19,334 (−0.1%)** | **1,527 → 4,462 (+192%)** |

**Growers grew ~180–215% in essentially every cache, uniformly** — a merchant-level change,
**not** a cache reallocation. Hypothesis refuted.

**The unexplained asymmetry:** decliners lost 47% of clicks across *every* cache from a real
base of 11,034 clicks, on a day the page grew. Unlike the growers this cannot be dismissed
as small numbers. **Open.**

---

## 12. Single-merchant deep dive — M29877282 (EcoFlow), os_client_id 10042968

### 12.1 The correction

| Cut | Jul 28 | Aug 4 | Δ |
|---|---|---|---|
| **All SKUs** *(as originally reported)* | 3.8513 | 5.0732 | **+31.7%** |
| **Continuing SKUs only** (17, both days) | **4.5031** | **4.2630** | **−5.3%** |
| New SKUs (5, absent Jul 28) | — | 7.9329 | — |
| Dropped SKUs (11, absent Aug 4) | 1.8550 | — | — |

Arithmetic: paired spend 250.33 − 29.68 = **220.65** over 65 − 16 = **49** clicks → 4.5031;
390.64 − 134.86 = **255.78** over 77 − 17 = **60** clicks → 4.2630.

**→ C22 REFUTED.** The +31.7% is a **SKU-mix effect**. Five new SKUs contributed ZAR 134.86
(34.5% of Aug-4 spend) at ZAR 7.93 CPC; eleven cheap SKUs at ZAR 1.86 left.

This does **not** overturn §8 — that held mix fixed across 879 cells. It means EcoFlow was a
poorly chosen exemplar.

### 12.2 Config state — no changes found

| Check | Window | Result |
|---|---|---|
| `AUDIT_EVENTS_REPORT` action 16 (status) | Aug 1–4 | **`{"current": []}`** — none |
| `AUDIT_EVENTS_REPORT` action 50/51 (product selection) | Aug 1–4 | **`{"current": []}`** — none |
| Campaigns present Aug 4 not Jul 28 / vice versa | — | **0 / 0** |
| `effective_status` changes across 8 active campaigns | — | **0** — all ACTIVE both days |
| `bid_type` in clicks data | Jul 22–Aug 4 | **AUTO_CPC only**, every day |
| `AUDIT_EVENTS_REPORT` action 17 (budget) | Aug 1–4 | **2 cuts, Aug 4 08:22**, by `takealot-M29877282` |

Budget cuts: campaign **1255198 1,500 → 1,000** (08:22:32); campaign **1239052
2,000 → 1,300** (08:22:23).

⚠ **The 11-day window (Jul 25–Aug 4) returned KAM 504 twice.** "No config changes" is
verified for **Aug 1–4 only**. A change on Jul 29–31 would not appear.

### 12.3 Campaign state — `TRUE_BU_CAMPAIGN_REPORT`, single-day calls

146 campaigns exist; 8 have budget or spend. Wallet **4,619.72 (Jul 28) → 1,639.87 (Aug 4),
−64.5%**.

| Campaign | Name | Bud J28 | Bud A4 | Spend J28 | Spend A4 | BU J28 | BU A4 |
|---|---|---|---|---|---|---|---|
| 1218309 | Auto-all | 1,000.00 | 800.00 | 1,252.83 | 814.36 | **125%** | 102% |
| 1239052 | Remarketing-近7 14 30天浏览人群 | 2,000.00 | 1,300.00 | 2,061.30 | 1,278.00 | 103% | 98% |
| 1255187 | SP-KW-品牌词-EXPHBO-D3s new | 1,500.00 | 1,500.00 | 336.83 | 915.09 | 22% | 61% |
| 1255193 | SP-KW-行业词-EXPH-D3s new | 800.00 | 600.00 | 532.74 | 507.64 | 67% | 85% |
| 1255198 | SD-本品类目DIY tools-D3 series | 1,500.00 | 1,000.00 | 94.20 | 111.30 | 6% | 11% |
| 1257922 | SP-KW-品牌词-EX-8月主推 | 2,500.00 | **1,639.87** | 384.51 | 294.41 | 15% | 18% |
| 1340521 | SP-KW-行业词-EX-D系列-高CTR ROI | 1,000.00 | 800.00 | 210.26 | 741.89 | 21% | **93%** |
| 1340532 | SP-KW-行业词-EXPH-R系列-高CTR曝光 | 700.00 | **1,000.00** | 192.01 | 455.31 | 27% | 46% |
| **TOTAL** | | **11,000.00** | **8,639.87** | **5,064.68** | **5,118.00** | | |

**Total spend flat (+1.1%) while budget fell 21.5%.** PRODUCT page is only **4.9% → 7.6%** of
this merchant's spend.

**Campaign 1257922's Aug-4 budget (1,639.87) equals the wallet balance exactly**, against a
configured 2,500 — effective budget is **clamped to remaining wallet**.

### 12.4 Bid config for SKU 223632782

16 active rows. **`onsite_manual_cpc`, `onsite_manual_cpc_usd`, `onsite_manual_cpm`,
`onsite_manual_cpm_usd` are NULL on all 16.** `roi_optimizer_bid_multiplier` = **1.0** and
`_v2` = **1.0** on all 16. `is_active`, `is_bidding_strategy_active` = true;
`is_paused_by_optimizer` = false; `ctr_optimizer_score` = 1.0; `roi_optimizer_score` and
`effective_ctr` NULL; currency ZAR; `bidding_strategy_level` = marketingCampaign — all 16.

| Internal ID | Marketing ID | Campaign | Strategy | Target ROI | **v3 multiplier** | Last update |
|---|---|---|---|---|---|---|
| 874218 | **1340532** | SP-KW-行业词-EXPH-R系列-高CTR曝光 | AUTO_CPC | — | **6.1917364224** | **2026-08-05 13:12:36** |
| 858562 | **1257922** | SP-KW-品牌词-EX-8月主推 | AUTO_CPC | — | **1.611003248540072** | **2026-08-05 13:12:36** |
| 822245 | 1199761 | All Products (26th Mar \| 19:13) | AUTO_CPC | — | 1.0 | 2026-04-03 01:33:54 |
| 835986 | **1218309** | Auto-all | AUTO_CPC | — | **0.9895703907223455** | **2026-08-05 13:12:36** |
| 841488 | 1226864 | All Products (11th May \| 15:53) | AUTO_CPC | — | 0.8252556202017423 | 2026-05-17 03:20:58 |
| 768128 | 1116910 | 户外 | AUTO_CPC | — | 0.3739858541503875 | 2026-04-03 01:24:49 |
| 777863 | 1131570 | 黑五auto | AUTO_CPC | — | 0.3280870081394152 | 2026-02-09 01:57:43 |
| 819279 | 1195797 | Auto | AUTO_CPC | — | 0.3241104280180187 | 2026-06-21 03:10:29 |
| 770540 | 1119604 | 品类kw-fish | **ROI** | **10.0** | 0.23443754882454143 | 2025-11-17 03:16:53 |
| 716249 | 1041672 | 单品 auto | AUTO_CPC | — | 0.207920296899419 | 2026-02-09 01:57:43 |
| 566171 | 773942 | PPS-AUTO-4.29 250613去230 | AUTO_CPC | — | 0.06238739117309936 | 2026-03-12 02:50:11 |
| 848787 | 1238283 | SP-KW-行业词-EX-7月有标主推品 | AUTO_CPC | — | 0.04109143217793816 | 2026-07-13 03:11:40 |
| 733634 | 1067763 | r2p+r2m test官网 | AUTO_CPC | — | 0.02259664397128452 | 2025-10-29 03:19:13 |
| 677653 | 957308 | KW-TEST-办公备电相关 | AUTO_CPC | — | 0.011529215046068401 | 2026-04-03 01:24:49 |
| 564461 | 771412 | R2 RP-KW-EP-品牌词 25.3.25改 | **ROI** | **10.0** | 0.00021812016172872 | 2026-02-09 01:57:43 |
| 580047 | 812340 | R系列-EP-行业词 | AUTO_CPC | — | 0.00008989905296224 | 2026-02-27 02:34:00 |

**→ C23 UNPROVEN.** The three rows updated **2026-08-05 13:12:36** are exactly the three of
EcoFlow's 8 active campaigns present here, and they carry the three highest v3 multipliers
(6.19, 1.61, 0.99). Campaign 1340532 is also the only one whose budget was *raised*
(700 → 1,000) with BU 27% → 93%. **But the table is a current-state snapshot with no
history** — those rows were rewritten *after* the incident, overwriting the Aug-4 values.
Correlation only.

Realized bid cross-check: USD **0.23764544362788217** × 15.735642 = **ZAR 3.7395**, from the
clicks table. No configured bid exists to compare against — this SKU is 100% auto-bid.

### 12.5 EcoFlow PRODUCT daily trend

| Date | Clicks | Spend | CPC | SKUs | Camps | avg raw_bid | avg orig_bid | avg bid |
|---|---|---|---|---|---|---|---|---|
| Jul 22 | 108 | 307.93 | 2.8512 | 30 | 5 | 0.12352 | 0.30775 | 0.18120 |
| Jul 23 | 99 | 283.08 | 2.8594 | 27 | 5 | 0.12657 | 0.32694 | 0.18171 |
| Jul 24 | 72 | 261.05 | 3.6258 | 25 | 6 | 0.12130 | 0.34836 | 0.23042 |
| Jul 25 | 46 | 208.30 | 4.5284 | 23 | 6 | 0.35671 | 0.57926 | 0.28778 |
| Jul 26 | 114 | 355.26 | 3.1163 | 35 | 5 | 0.14981 | 0.32251 | 0.19804 |
| Jul 27 | 61 | 215.20 | 3.5278 | 26 | 5 | 0.14262 | 0.40506 | 0.22419 |
| **Jul 28** | **65** | **250.33** | **3.8513** | 28 | 5 | 0.14446 | 0.28546 | 0.24475 |
| Jul 29 | 36 | 161.14 | 4.4761 | 18 | 4 | 0.15806 | 0.43497 | 0.28446 |
| Jul 30 | 69 | 184.42 | 2.6727 | 27 | 5 | 0.16058 | 0.32002 | 0.16985 |
| Jul 31 | 74 | 287.79 | 3.8891 | 28 | 6 | 0.14649 | 0.34271 | 0.24715 |
| Aug 1 | 80 | 278.99 | 3.4874 | 29 | 5 | 0.15225 | 0.34498 | 0.22162 |
| **Aug 2** | **10** ⚠ | **27.22** | 2.7224 | **8** | 3 | 0.17100 | 0.23028 | 0.17301 |
| Aug 3 | 62 | 220.57 | 3.5575 | 29 | 5 | 0.17597 | 0.46422 | 0.22608 |
| **Aug 4** | **77** | **390.64** | **5.0732** | 22 | 5 | 0.17844 | **0.59732** | 0.32240 |

`bid_type` = AUTO_CPC on every row. **Aug 2 is the anomaly** — 10 clicks against a 36–114
range — which is what produced the "+1,335%" headline in §11.4.

### 12.6 Full SKU table, Jul 28 vs Aug 4 (33 SKUs)

| SKU | Clk J28 | Spend J28 | CPC J28 | Clk A4 | Spend A4 | CPC A4 | Δ | Caches |
|---|---|---|---|---|---|---|---|---|
| 234640665 | 0 | 0.00 | — | 10 | 102.31 | 10.231 | **+102.31** | BGC, SIG, SCR, GSC |
| 223632782 | 4 | 18.98 | 4.745 | 11 | 109.32 | 9.938 | **+90.34** | SIG, UAB, CPD, SC, SCR, GSC |
| 234861661 | 3 | 6.04 | 2.012 | 9 | 39.80 | 4.422 | +33.76 | SCR, BGC, SIG, CPD |
| 235146340 | 0 | 0.00 | — | 3 | 24.77 | 8.256 | +24.77 | UAB, GSC, SCR |
| 228717675 | 1 | 1.50 | 1.500 | 4 | 7.09 | 1.773 | +5.59 | UAB, SIG, SCR, BGC |
| 234861666 | 0 | 0.00 | — | 2 | 3.75 | 1.874 | +3.75 | SIG |
| 216533597 | 1 | 3.08 | 3.077 | 3 | 5.93 | 1.976 | +2.85 | SCR, GSC |
| 230245430 | 2 | 3.74 | 1.868 | 3 | 6.45 | 2.149 | +2.71 | UAB, SC, SCR, BGC |
| 230511835 | 0 | 0.00 | — | 1 | 2.53 | 2.535 | +2.53 | UAB |
| 226247181 | 1 | 1.50 | 1.500 | 2 | 3.34 | 1.668 | +1.84 | NOV, UAB |
| 229562655 | 0 | 0.00 | — | 1 | 1.50 | 1.500 | +1.50 | SCR |
| 215922023 | 1 | 1.50 | 1.500 | 2 | 3.00 | 1.500 | +1.50 | GSCR, SIG, GSC |
| 228717679 | 2 | 3.00 | 1.500 | 2 | 3.00 | 1.500 | 0.00 | SIG, UAB, SCR |
| 236973220 | 2 | 3.00 | 1.500 | 2 | 3.00 | 1.500 | 0.00 | SCR, BGC |
| 233150613 | 1 | 1.50 | 1.500 | 0 | 0.00 | — | −1.50 | BGC |
| 233552612 | 2 | 3.00 | 1.500 | 1 | 1.50 | 1.500 | −1.50 | NOV, GSC |
| 226374882 | 1 | 1.50 | 1.500 | 0 | 0.00 | — | −1.50 | BGC |
| 226375042 | 2 | 3.00 | 1.500 | 1 | 1.50 | 1.500 | −1.50 | SIG, CTP |
| 220150095 | 1 | 1.50 | 1.500 | 0 | 0.00 | — | −1.50 | **SSC** |
| 232623368 | 1 | 1.50 | 1.500 | 0 | 0.00 | — | −1.50 | UAB |
| 233150614 | 1 | 1.50 | 1.500 | 0 | 0.00 | — | −1.50 | SCR |
| 215604709 | 1 | 1.50 | 1.500 | 0 | 0.00 | — | −1.50 | **SSC** |
| 216998210 | 1 | 1.50 | 1.500 | 0 | 0.00 | — | −1.50 | **SSC** |
| 235146346 | 1 | 2.71 | 2.712 | 0 | 0.00 | — | −2.71 | CPD |
| 235146342 | 3 | 7.90 | 2.635 | 1 | 5.17 | 5.171 | −2.73 | UAB, SCR |
| 232623365 | 4 | 9.49 | 2.373 | 2 | 6.66 | 3.331 | −2.83 | BGC, UAB, CPD |
| 236973216 | 2 | 3.16 | 1.581 | 0 | 0.00 | — | −3.16 | CPD, UAB |
| 229562654 | 2 | 3.41 | 1.705 | 0 | 0.00 | — | −3.41 | UAB, CPD |
| 226329522 | 5 | 9.61 | 1.922 | 1 | 1.50 | 1.500 | −8.11 | SIG, CPD, **SSC**, GSCR |
| 233150618 | 4 | 9.90 | 2.474 | 0 | 0.00 | — | −9.90 | SCR, SC, UAB |
| 232623367 | 5 | 25.98 | 5.196 | 7 | 12.99 | 1.856 | −12.99 | **SSC**, SIG, UAB, CPD, SCR |
| 234861665 | 6 | 23.91 | 3.986 | 4 | 10.26 | 2.565 | −13.65 | SCR, BGC, **SSC**, SIG, UAB |
| **221637484** | 5 | **95.42** | **19.084** | 5 | 35.26 | **7.053** | **−60.16** | **SSC**, SIG, UAB, SCR |
| **TOTAL** | **65** | **250.33** | **3.8513** | **77** | **390.64** | **5.0732** | **+140.31** | |

Cache keys: SSC = SIMILAR_SKU_CACHE · SIG = SIMILAR_ITEM_GROUP_CACHE · GSC =
GRANULAR_SOLR_CATEGORY · BGC = BRAND_GRANULAR_CATEGORY · SCR = SOLR_CATEGORY_REMARKETING ·
SC = SOLR_CATEGORY · UAB = UA_BRAND_CACHE · CPD =
CATEGORY_PRICE_DISCOUNT_BUCKET_TOP_SELLING_L3 · NOV = NOVELTY_CATEGORY_CACHE · CTP =
CATEGORY_TOP_POPULAR_PRODUCTS · GSCR = GRANULAR_SOLR_CATEGORY_REMARKETING

**Notable rows:**
- **Concentration:** Aug-4 top four = 276.20 = **70.7%** of spend; Jul-28 top SKU = 38.1%.
- **SKU 221637484:** identical 5 clicks both days, CPC **19.084 → 7.053 (−63%)** — the largest
  offsetting move, on the retired cache.
- **Six SKUs served on `SIMILAR_SKU_CACHE`.** Three stopped entirely; three continued via
  `SIMILAR_ITEM_GROUP_CACHE` **at lower CPC**. For this merchant the migration *reduced* CPC.
- **ZAR 1.50 floor** appears on 14 rows.

---

## 13. Assumptions the conclusions rest on

| Assumption | Status | Consequence if wrong |
|---|---|---|
| `raw_bid` is the pre-adjustment bid input | **UNVERIFIED** — no definition in the repo, in any of 43 configs, or in table metadata | The §7 argument that the change originates upstream of bid optimisation collapses |
| `original_bid` is a pre-adjustment variant | **UNVERIFIED** | Secondary — used only as corroboration |
| `bid` × `conversion_factor` on valid clicks = spend | **VERIFIED** — lifted from the report's own SQL, reconciled to 0.1% | — |
| `cache_type` identifies the serving relevancy algorithm | **ASSUMED** from `INTERNAL_PERF_RESPONDED_SKUS` description | The cache-level framing loses meaning |
| `resp_category_l1` is the served product's category | **ASSUMED** | §8.1 and the cell decomposition weaken |
| Clicks-table `client_id` = `os_client_id` | **VERIFIED** on 3 merchants against audit-event IDs | Budget/wallet joins would be wrong |
| `perf_daily_budget = 0` means "no row", not zero | **VERIFIED** — BU stays ~100% on those rows | Budget deltas would be wrong (−18.2% vs −4.6%) |

**Action:** items 1, 2, 4 and 5 need confirmation from the ad-server / reporting owner before
this is presented to a client.

---

## 14. Data exports

| File | Contents |
|---|---|
| `~/Downloads/all270.csv` | 270 growers: merchant_id, client_ids, spend/clicks/CPC per day, delta, pct, bucket |
| `~/Downloads/joined270.csv` | same + daily budget, wallet, BU, all-page spend, both days |

`joined270.csv` glossary: `bud2`/`bud4` daily budget (**0.00 = missing row, not zero**),
`wal2`/`wal4` wallet ZAR, `bu2`/`bu4` utilisation as **fraction**, `tspend*` all-page spend,
`ps*` PRODUCT spend, `pc*` PRODUCT clicks, `cpc*` PRODUCT CPC, `d`/`pct` delta / % change.

Budget summary from `joined270.csv`: 46 merchants have a budget **both** days
(8,054.40 → 7,680.76, **−4.6%**; 10 raised, 9 cut, **27 unchanged**); 52 Aug-2 only;
35 Aug-4 only; **137 neither**. The 27 unchanged-budget merchants: product spend
215.24 → 680.92, clicks 83 → 203, **CPC 2.5933 → 3.3543 (+29.3%)**. **77 of 270 (29%)** at
BU ≥ 100% on Aug 4. Negative wallets: M29899310 (−1.75), M29855427 (−5.28),
b_38411 (−10.96); **22 below ZAR 100**.

---

## 15. Open items

| # | Item | Owner | Why it matters |
|---|---|---|---|
| 1 | Deploy log for **Aug 3 ~14:00 SAST / 12:00 UTC** | release eng | The only way to move C17 from UNPROVEN to proven |
| 2 | Was `SIMILAR_ITEM_GROUP_CACHE` expected to affect category-cache bid computation? | relevancy owner | If no, the competition angle reopens |
| 3 | Confirm `bid` / `original_bid` / `raw_bid` semantics | ad-server owner | C18 — the §7 argument depends on it |
| 4 | Category floor config history | ads-ops | Falsification check; distribution says it is not a floor |
| 5 | Why did `NOVELTY_CATEGORY_CACHE` fall 22.3% the same day? | relevancy owner | Any single-cause account must explain it |
| 6 | Why did the decliner cohort lose 47% of clicks across every cache? | — | Largest unexplained volume move |
| 7 | A fact table joining merchant × page × revenue | data eng | Without it, "did they convert?" is unanswerable |
| 8 | Drill CATEGORY page at cache level | — | Ticket names it; never verified |
| 9 | Wallet risk: 3 negative, 22 under ZAR 100 | account team | Will present as delivery complaints within days |
| 10 | CTR decline 8–10% matched weekday, 100% of spend | — | Larger than this ticket; no ticket exists |

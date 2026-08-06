# Support ticket investigations — 2026-08-06

One marketplace ad-performance ticket, worked in depth through the `debug-cpc` SOP skill
and then extended well past the SOP with direct BigQuery analysis. Currency **ZAR**
throughout.

| # | Ticket | Marketplace | Skill | Verdict |
|---|---|---|---|---|
| 1 | "There's an increase in CPC for product and category pages, please check" — increase observed 2026-08-04 | takealot (105) | debug-cpc | **Partially valid.** PRODUCT page: real, dated to Aug 4, mechanism identified at relevancy-cache level. CATEGORY page: not supported — WoW CPC *fell* 4.9%. Financial impact ≈ ZAR 5,273/day (0.57% of marketplace PLA spend) |

> **The headline mechanism.** Five non-remarketing **category relevancy caches** show a
> 13–20% CPC rise on Aug 4 with near-flat click volume, while both *remarketing* variants
> and the brand cache fell. All three bid columns rose on the movers (`raw_bid` +14%) and
> none rose on the control. Bidding on these caches is **100% automated** (`AUTO_CPC` /
> `ROI`, zero manual bids across 4,289 campaigns), so advertisers cannot have caused it.
> Coincident with a **relevancy cache migration completing at Aug 3 14:00 SAST**.
>
> **What it is NOT:** not a floor change (the bottom of the bid distribution is unchanged
> to five decimal places), not a category-mix shift (survives holding merchant × served
> category fixed), not merchant or campaign churn, not advertiser bid changes.

---

## Context established at intake

| Field | Value | Source |
|---|---|---|
| Marketplace | takealot-marketplace | `MARKETPLACE_DIRECTORY_REPORT` |
| `agency_id` | 105 | " |
| `marketplace_client_id` | 100002 | " |
| Currency | **ZAR** | " |
| Timezone | Africa/Johannesburg | " |
| Region | "Belgium" — **known-unreliable field**, ignored | " |
| Program | **PLA** (`channel = 'os_product_ads'`) — user-locked; Display out of scope | user |
| Window framing | "trend over the week", then narrowed to Aug 3–4 vs Jul 27–28, then Tue-vs-Tue | user |
| USD→ZAR conversion factor | **15.735642** | `static_currency_conversion` / `perf_conversion_factor` |

---

## Environment limitations encountered

These cost real time and shaped which route each question took. Recording them so the
next investigation doesn't rediscover them.

### KAM / report layer

- **KAM HTTP 504 on large queries.** Three Apollo `PAGE_PERFORMANCE_PLA_REPORT` /
  `RR_PLA_REPORT` calls timed out. Later, `AUDIT_EVENTS_REPORT` over an **11-day** window
  504'd twice; the same report over **3–4 day** windows succeeded every time. Keep audit
  windows ≤4 days.
- **Total KAM outage mid-session.** Every report began failing with:
  `KAM HTTP 500: unable to init GCP BigQuery … key: GCP_PERF_BQ_KAM_CREDENTIALS not found
  for application: irisTestApplication`. The test env had lost its BigQuery service-account
  credentials. Resolved later in the session by the user re-authenticating.
- **`RESPONDED_SKUS_REPORT` hardcodes `page_type = 'SEARCH'`** in its frozen SQL. It can
  therefore *never* answer a cache-type question for the PRODUCT page, regardless of KAM
  health. Cache-level analysis required BigQuery.
- **`MERCHANT_PERFORMANCE_REPORT` has no `page_type` attribute** — no page-scoped merchant
  breakdown via the report layer.
- **`TRUE_BU_CAMPAIGN_REPORT` silently ignores a `perf_os_client_id` filter.** Two calls
  filtered to one client returned all 7,805 / 7,860 marketplace rows. Filter client-side.
- **`WALLET_BALANCE_REPORT` has no history** — current snapshot only. Wallet-at-date must
  come from `TRUE_BU_CAMPAIGN_REPORT`'s `perf_wallet_balance` on a single-day range.
- **`perf_action_type_id` is a STRING column.** Passing integers gives
  `No matching signature for operator = for argument types: STRING, INT64`. Pass
  `["16"]`, not `[16]`.
- **`perf_daily_budget = 0` means "no row returned for that day", not "budget is zero".**
  Proven by merchants showing budget → 0.00 while `perf_budget_utilization` stayed at
  ~100%; BU is spend ÷ budget, so a genuine zero would make BU undefined. **Any
  budget-change total computed across merchants without filtering for
  present-on-both-days is wrong.** (Naive −18.2% vs true −4.6% on this ticket.)
- **`CAMPAIGN_PRODUCT_SELECTION_REPORT` exposes no bid columns** — only campaign/merchant/
  product/availability/brand/category. Bid config required BigQuery.

### BigQuery

- **`bq` is installed and authenticated** as `meenal.sanghvi@onlinesales.ai` — a completely
  separate auth path from kamService's service account. When KAM was fully down, BQ still
  worked. This is the single most useful fact in this document.
- **Billing project matters.** No `bigquery.jobs.create` on `prj-onlinesales-vertexai`
  (the gcloud default), `prj-onlinesales-bq-kam`, or `prj-onlinesales-reporting-prod`.
  **`--project_id=prj-onlinesales-prod-01` works.**
- **No `bigquery.tables.list`** on `prj-onlinesales-prod-01:reporting` — cannot `bq ls` the
  dataset. Table names must come from the report configs; extract them with:
  `grep -o '`prj-[a-z0-9-]*\.[a-z_]*\.[A-Za-z_0-9-]*`' kam_report_configs/**/*.json`
- **`os_product_ads_product_selection_100002` is a current-state snapshot** with no
  history; `ATHENA_LAST_UPDATE` is the only temporal field. Historical bid config is
  **not recoverable** from it.

### Data gaps that blocked a question outright

- **No page-scoped ROAS exists.** `monetize_merchant_facts` has merchant_id + revenue/
  orders but **no `page_type`**; `os_product_ads_page_name_performance_facts` has
  `page_type` but **no `merchant_id`**. So "did the advertisers paying more actually
  convert?" — the most client-relevant question — could not be answered. Still open.
- **No bid-change audit action type located.** Action types checked: 16 (status), 17
  (budget), 50/51 (product selection). A merchant could have altered bid strategy without
  appearing in any of them.

---

# Ticket 1 — takealot | CPC increase on product and category pages

**Marketplace:** takealot-marketplace, agency **105**, marketplace_client_id **100002**,
ZAR, Africa/Johannesburg · **Program:** PLA · **Pages:** PRODUCT (drilled), CATEGORY (page
level only) · **Observed:** 2026-08-04

## Verdict

**Partially valid, and mis-prioritised.**

- **PRODUCT page — valid.** Aug 4 CPC of ZAR 2.8147 is the highest in 15 days. Confirmed a
  second, independent way on a like-for-like intraday basis (hours 0–8: ZAR 3.0685 vs a
  Jul 28–Aug 3 range of 2.7374–2.9367). Mechanism identified at relevancy-cache level.
- **CATEGORY page — not supported.** Week-over-week CATEGORY CPC **fell 4.9%**
  (ZAR 4.3080 → 4.0960). Never drilled at cache level, so cache behaviour there is
  unverified — but the page-level direction contradicts the ticket.
- **Severity: MEDIUM**, arguably LOW on cost. Excess cost ≈ **ZAR 5,273/day** = **0.57%**
  of Aug 4 marketplace PLA spend. The five affected caches together are 4.8% of PLA spend.
  Marketplace-wide CPC on Aug 4 (ZAR 4.9855) was *below* the 30-day average (ZAR 5.0871).

---

## How we proceeded — chronological

The route mattered as much as the answer, because two intermediate conclusions were wrong
and had to be corrected by going deeper.

| # | Question | Tool / method | Outcome |
|---|---|---|---|
| 1 | Which pages moved? | `PAGE_PERFORMANCE_PLA_REPORT`, WoW + daily | Premise fails WoW; real spike on Aug 4, PRODUCT + CATEGORY only |
| 2 | Is it price or volume? | Aug 3–4 vs Jul 27–28 | CPC +3.71% but spend −13.19%, clicks −16.30% → looked like a pure denominator artifact |
| 3 | Cache-level truth | **BQ** `os_product_ads_response_to_clicks_mapping` | **Overturned #2** — category caches up 13–20% with flat clicks. Real bid pressure hidden by the aggregate |
| 4 | Floor change? | `bid` / `original_bid` / `raw_bid` distributions | **Floor ruled out** — bottom of distribution identical |
| 5 | Whose bids? | Campaign / merchant / cell decomposition | +11.2% survives holding merchant × served category fixed |
| 6 | When exactly? | Hourly cache clicks Aug 2–4 | Cache migration completed **Aug 3 14:00 SAST** |
| 7 | Full cache picture | All caches, Jul 28 → Aug 4 | **Five** category caches moved, not two. `NOVELTY_CATEGORY_CACHE` moved −22% (opposite) |
| 8 | Is it a trend? | 15-day daily trend (user challenge) | User was right — one-day spike confirmed, Aug 3 is *not* part of it |
| 9 | Merchant cohorts | Aug 2 vs Aug 4, all merchants | Retained cohort +10.3% CPC; above-floor migration found |
| 10 | Bucket the retained | 10 spend-change buckets | Monotonic CPC gradient; 22pp of spend share redistributed |
| 11 | Who are the growers? | 270 merchants, budget/wallet/targeting | ~half grew from their own actions, not the platform |
| 12 | One merchant end-to-end | EcoFlow: campaigns, SKUs, bid config | **Overturned the "cleanest case" claim** — SKU-mix effect, not price |

---

## STEP 1 — Page-level triage

`PAGE_PERFORMANCE_PLA_REPORT`, comparison mode. Week Jul 29–Aug 4 vs Jul 22–28.

| Page | Baseline CPC | Current CPC | CPC Δ | Baseline Spend | Current Spend | Base Share% | Cur Share% | Contrib to Spend Δ% |
|---|---|---|---|---|---|---|---|---|
| SEARCH | 6.1430 | 5.7746 | −6.0% | 6,323,854.55 | 5,381,972.87 | 86.21% | 84.58% | 96.84% |
| PRODUCT | 2.6507 | 2.5993 | −1.9% | 736,160.22 | 665,005.56 | 10.03% | 10.45% | 7.32% |
| CATEGORY | 4.3080 | 4.0960 | −4.9% | 188,102.68 | 166,747.47 | 2.56% | 2.62% | 2.20% |
| CUSTOM | 5.3457 | 5.0159 | −6.2% | 35,966.06 | 102,485.34 | 0.49% | 1.61% | −6.84% |
| HOME | 3.2000 | 3.1132 | −2.7% | 51,439.47 | 46,673.69 | 0.70% | 0.73% | 0.49% |
| **Total** | **5.3402** | **5.0339** | **−5.7%** | **7,335,523.0** | **6,362,885.1** | 100% | 100% | 100% |

**Reconciliation performed:** daily rows summed to weekly aggregates matched separately
measured weekly totals **to the cent** on both weeks (CATEGORY: ZAR 166,747.47 / 40,710
clicks current; 188,102.68 / 43,664 baseline). Derived cuts trustworthy.

**Side finding, out of ticket scope:** CUSTOM spend rose **185%** (35,966 → 102,485),
stepping up from Jul 29 — the only page whose spend grew, and the reason total contribution
carries a negative row. Looks like a placement launch. Unexplained; flagged, not chased.

### FLOOR-PRICE CHECKPOINT (SOP-required)

Affected pages are non-search, so **Category Floors** were the ones to check. The SOP says
the agent has no tool for this and must ask the user. Asked. **Never answered.**

Correction made later in the session: `get_keyword_floor_bids` *does* exist in the campaign
MCP, but it is **keyword-scoped**, so it cannot answer a category-floor question.
`get_inventory_details` requires `page_types` and returned `data: []` for takealot. So the
"no tool" statement was right for this case, for a different reason than first given.

---

## The window question — and a user correction that mattered

First pass compared Aug 3–4 vs Jul 27–28 (Mon–Tue vs Mon–Tue):

| Metric | Jul 27–28 | Aug 3–4 | Change |
|---|---|---|---|
| **CPC** | 2.6283 | 2.7257 | **+3.71%** |
| Spend | 225,506.84 | 195,756.48 | −13.19% |
| Clicks | 85,801 | 71,818 | −16.30% |
| Impressions | 12,323,000 | 10,957,694 | −11.08% |
| CTR | 0.6963% | 0.6552% | −5.91% |
| *Mon only (27→3)* | 2.5878 | 2.6347 | +1.81% |
| *Tue only (28→4)* | 2.6691 | 2.8148 | **+5.46%** |

This produced the (incomplete) conclusion that CPC rose only because clicks fell faster
than spend. **The user then said: "if u check the cpc trend of product page of last 15
days, u would see the spike."** They were right, and the 15-day view is what forced the
cache-level drill.

### PRODUCT-page daily CPC, Jul 20 – Aug 4

| Date | Day | CPC | DoD |
|---|---|---|---|
| Jul 20 | Mon | 2.5537 | |
| Jul 21 | Tue | 2.6153 | +2.4% |
| Jul 22 | Wed | 2.5429 | −2.8% |
| Jul 23 | Thu | 2.6296 | +3.4% |
| Jul 24 | Fri | 2.7729 | +5.4% |
| Jul 25 | Sat | 2.7329 | −1.4% |
| Jul 26 | Sun | 2.6217 | −4.1% |
| Jul 27 | Mon | 2.5878 | −1.3% |
| Jul 28 | Tue | 2.6691 | +3.1% |
| Jul 29 | Wed | 2.5946 | −2.8% |
| Jul 30 | Thu | 2.5947 | +0.0% |
| Jul 31 | Fri | 2.5750 | −0.8% |
| Aug 1 | Sat | 2.4767 | −3.8% |
| Aug 2 | Sun | 2.4890 | +0.5% |
| **Aug 3** | Mon | **2.6350** | +5.9% |
| **Aug 4** | Tue | **2.8147** | **+6.8%** |

14 days oscillating in a ZAR 2.48–2.77 band with no trend, then Aug 4 breaks the range.

### Partial-day validation (and a claim withdrawn)

An initial read included **Aug 5** (ZAR 3.0977) and described "three consecutive days of
acceleration." The user correctly said to exclude today. An hourly check confirmed why that
mattered: **early-day CPC runs systematically hot** (budget pacing front-loads spend), so a
quarter-complete day overstates the level.

| Date | Full-day CPC | Hours 0–8 CPC (like-for-like) |
|---|---|---|
| Jul 28 | 2.6661 | 2.9367 |
| Jul 29 | 2.5960 | 2.8605 |
| Jul 30 | 2.5932 | 2.8060 |
| Jul 31 | 2.5751 | 2.7571 |
| Aug 1 | 2.4787 | 2.7374 |
| Aug 2 | 2.4856 | 2.8904 |
| Aug 3 | 2.6328 | 2.8412 |
| **Aug 4** | **2.8124** | **3.0685** |

**Conclusions that survive:** Aug 4 is a genuine one-day spike, confirmed on both full-day
and hours-0–8 bases (+4.5% above the highest prior day on the like-for-like measure).
**Aug 3 is NOT part of the spike** — at 2.6328 / 2.8412 it sits inside the pre-existing
band; it is a recovery off the weekend trough. The "three days of acceleration" claim
does not stand.

---

## The decisive drill — cache-level CPC (BigQuery)

`RESPONDED_SKUS_REPORT` hardcodes SEARCH, so this went direct to
`prj-onlinesales-prod-01.reporting.os_product_ads_response_to_clicks_mapping`, mirroring
the report's own spend definition: `bid × conversion_factor` on `is_valid_click`.

**Validation:** cache-level totals reproduce the page report's CPC to within 0.1% —
ZAR 2.6282 vs 2.6283 (baseline) and 2.7229 vs 2.7257 (current). Cache rows cover 98.0% /
98.1% of page-report clicks; the ~2% gap is clicks with no `cache_type` mapping and is
stable across both days, so it does not bias the comparison.

### All caches, PRODUCT page, Tue Jul 28 → Tue Aug 4

| Cache type | Clk J28 | CPC J28 | Clk A4 | CPC A4 | **CPC Δ** | Clicks Δ |
|---|---|---|---|---|---|---|
| GRANULAR_SOLR_CATEGORY | 5,841 | 2.7491 | 5,503 | 3.2888 | **+19.6%** | −5.8% |
| CATEGORY_PRICE_DISCOUNT_BUCKET_TOP_SELLING_L3 | 3,746 | 2.1940 | 1,668 | 2.6033 | **+18.7%** | **−55.5%** |
| CATEGORY_TOP_POPULAR_PRODUCTS | 1,540 | 2.4477 | 1,217 | 2.8317 | **+15.7%** | −21.0% |
| BRAND_GRANULAR_CATEGORY | 3,636 | 2.9644 | 3,475 | 3.4157 | **+15.2%** | −4.4% |
| SOLR_CATEGORY | 2,632 | 2.5225 | 2,117 | 2.8513 | **+13.0%** | −19.6% |
| UA_MERCHANT_CACHE | 922 | 2.3118 | 669 | 2.3964 | +3.7% | −27.4% |
| SOLR_CATEGORY_REMARKETING | 6,475 | 2.2752 | 5,888 | 2.2002 | −3.3% | −9.1% |
| UA_BRAND_CACHE *(control)* | 6,352 | 2.9875 | 4,591 | 2.8471 | −4.7% | −27.7% |
| GRANULAR_SOLR_CATEGORY_REMARKETING | 130 | 2.3598 | 38 | 2.1472 | −9.0% | **−70.8%** |
| NOVELTY_CATEGORY_CACHE | 1,764 | 4.1953 | 1,641 | 3.2586 | **−22.3%** | −7.0% |
| SIMILAR_SKU_CACHE | 8,752 | 2.5599 | **0** | — | *retired* | −100% |
| SIMILAR_ITEM_GROUP_CACHE | 0 | — | 8,808 | 2.6467 | *new* | — |
| **Blended** | **41,790** | **2.6661** | **35,615** | **2.8123** | **+5.5%** | −14.8% |

**The split is remarkably clean:** every riser is a **non-remarketing category cache**.
Both *remarketing* category variants fell, as did the brand cache. A change that hits
category-relevancy pricing but spares its remarketing variants is a narrow, structured
change — not broad market competition.

**`NOVELTY_CATEGORY_CACHE` moved the opposite way** (−22.3%, ZAR 4.1953 → 3.2586, stepping
down on Aug 3). It was the most expensive cache and is now mid-pack. **Unexplained.** Any
account of the Aug 4 event must also explain this.

### Dating the cache migration — hourly, Aug 3

| Hour (SAST) | SIMILAR_SKU_CACHE | SIMILAR_ITEM_GROUP_CACHE |
|---|---|---|
| 11 | 376 | 25 |
| 12 | 365 | 33 |
| **13** | **233** | **195** ← transition |
| **14** | **0** | **467** |
| 15+ | 0 (never returns) | 449, 387, 445, 457, 544, 522, 459, 295, 153 |

**Cutover: Aug 3 ≈14:00 Africa/Johannesburg.** Canary began Jul 31 (162 clicks), ramped
across the weekend, completed Aug 4 with `SIMILAR_SKU_CACHE` at zero all day.

The migration is **volume-neutral** (8,752 → 8,808 clicks) and modestly more expensive
(ZAR 2.5599 → 2.6467, **+3.4%**). It is a secondary contributor, **not** the driver — but
it is the only dateable platform change in the window and it lands one day before the spike.

---

## Ruling out a floor change — bid distributions

The hypothesis after the cache drill was a **category floor raise**. It is wrong, and the
distribution is what kills it.

`raw_bid` percentiles, GRANULAR_SOLR_CATEGORY + BRAND_GRANULAR_CATEGORY (USD):

| Percentile | Jul 28 | Aug 4 | Δ |
|---|---|---|---|
| **min** | **0.014** | **0.014** | **0%** |
| **p01** | **0.02** | **0.02** | **0%** |
| p05 | 0.04 | 0.04385 / 0.04 | ~+9.6% / 0% |
| p25 | 0.08 | 0.09 | +12.5% |
| p50 | 0.13 | 0.15 | +15.4% |
| p90 | 0.23 | 0.27 | +17.4% |
| p99 (GSC) | 0.33 | 0.34 | +3.0% |
| max (GSC) | 0.53 | 0.93658 | +76.7% |

Charged `bid`, GRANULAR_SOLR_CATEGORY: mean 0.1747 → 0.2090; p75 0.18912 → 0.23623
(+24.9%); p90 0.32362 → 0.44186 (+36.5%); p99 0.91908 → 1.12368 (+22.3%);
**max 3.1775 on both days** (an unchanged hard cap — stable, so not a driver).

**A floor raise truncates from below** and piles bids up at the new floor value. Here the
bottom of the distribution is **identical** while the middle and upper shifted right. That
is the signature of a bid-multiplier or competition change, not a floor.

Independently corroborated in the merchant analysis: the **ZAR 1.50 floor is unchanged**
(= USD 0.09532 × 15.735642, matching the p05 value identical on both days).

### Bid diagnostics — all three columns, movers vs control

| Cache | Bid type | charged `bid` | `original_bid` | `raw_bid` | clicks |
|---|---|---|---|---|---|
| GRANULAR_SOLR_CATEGORY | AUTO_CPC | 0.17881 → 0.21111 (**+18.1%**) | 0.25613 → 0.30872 (**+20.5%**) | 0.13573 → 0.15493 (**+14.1%**) | 5,118 → 4,832 |
| GRANULAR_SOLR_CATEGORY | ROI | 0.14563 → 0.19388 (**+33.1%**) | 0.20087 → 0.30873 (**+53.7%**) | 0.12969 → 0.15219 (+17.3%) | 723 → 671 |
| BRAND_GRANULAR_CATEGORY | AUTO_CPC | 0.19237 → 0.22071 (**+14.7%**) | 0.22763 → 0.26545 (+16.6%) | 0.13364 → 0.15276 (**+14.3%**) | 3,166 → 3,076 |
| BRAND_GRANULAR_CATEGORY | ROI | 0.16157 → 0.18900 (+17.0%) | 0.19066 → 0.24055 (+26.2%) | 0.12606 → 0.14865 (+17.9%) | 470 → 399 |
| **UA_BRAND_CACHE** *(control)* | AUTO_CPC | 0.19779 → 0.18755 (**−5.2%**) | 0.25128 → 0.24025 (−4.4%) | 0.10939 → 0.11257 (+2.9%) | 5,489 → 3,988 |
| **UA_BRAND_CACHE** *(control)* | ROI | 0.13939 → 0.13718 (−1.6%) | 0.16170 → 0.16373 (+1.3%) | 0.12531 → 0.13626 (+8.7%) | 863 → 603 |

**Why this is the strongest evidence in the investigation:**

1. **Only `AUTO_CPC` and `ROI` bid types exist** on these caches — **zero manual bids**
   across **4,289 campaigns / 1,729 merchants**. Advertisers cannot have collectively
   raised bids 14–20% overnight; the system computes the bid.
2. **`raw_bid` — the pre-adjustment input — rose ~14% on both movers and +2.9% on the
   control.** Competition raises what you *pay*, not your bid *input*. An input moving
   points upstream of bid optimisation.
3. **Bid-type mix is stable** (ROI share 12.4% → 12.2% and 12.9% → 11.5%), so this is not
   a composition artifact.
4. The rise is a **ramp, not a step**: click-weighted `raw_bid` ≈ 0.135 (Aug 2) → 0.147
   (Aug 3) → 0.155 (Aug 4). **A config flag produces an instantaneous step at one hour;
   an automated bidder adapting produces a ramp.** We see the ramp.

---

## Price vs mix — three decompositions

Testing whether the same advertisers pay more, or different (pricier) advertisers win.
All on GRANULAR_SOLR_CATEGORY, Jul 28 vs Aug 4. "Fixed-mix" = Laspeyres (Aug-4 unit prices
at Jul-28 click weights).

| Keyed on | Entities J28 / A4 / both | Paired CPC | **Fixed-mix (pure price)** | Click coverage |
|---|---|---|---|---|
| Campaign | 2,129 / 2,097 / **890** | 2.6862 → 2.9562 (+10.1%) | **+7.7%** | 59% / 56% |
| **Merchant** | 1,057 / 1,072 / **661** | 2.7089 → 3.0865 (+13.9%) | **+11.4%** | **83% / 81%** |
| Merchant × served category | — / — / **879 cells** | 2.7388 → 3.1347 (+14.5%) | **+11.2%** | 70% / 67% |

Entrant/exit cohorts (merchant-keyed): new merchants CPC **4.1520** (1,045 clicks) vs
churned **2.9421** (1,007 clicks) — 41% pricier, but only 19% of Aug-4 volume.

**Why merchant-keyed is the reliable cut:** campaign IDs churn **58% per week** on this
marketplace (890 of ~2,100 present both days). The repo already records a takealot seller
re-creating the same campaign eight times since 2 June, so a campaign-keyed decomposition
conflates re-creation with genuine churn. Merchant IDs survive re-creation, and the
merchant cut has 83% click coverage vs 57%.

**The cell-level result is the one to quote: +11.2% with merchant AND served category held
fixed, across 879 cells covering ~68% of clicks.** This cannot be a mix effect at any
level tested.

### Category L1 within GRANULAR_SOLR_CATEGORY — 10 of 12 up

| Served category L1 | Clk J28 → A4 | CPC J28 | CPC A4 | Δ |
|---|---|---|---|---|
| TV, Audio & Video | 258 → 155 | 2.5902 | 4.0856 | **+57.7%** |
| Sport | 316 → 324 | 3.0094 | 3.9728 | **+32.0%** |
| Office & Stationery | 307 → 329 | 2.9963 | 3.7175 | **+24.1%** |
| Health | 679 → 642 | 3.5469 | 4.3899 | **+23.8%** |
| Fashion | 576 → 627 | 2.6100 | 3.1051 | **+19.0%** |
| Home & Kitchen *(largest)* | 1,553 → 1,484 | 2.6542 | 3.1325 | **+18.0%** |
| Computers & Tablets | 466 → 394 | 3.0378 | 3.4876 | +14.8% |
| Garden, Pool & Patio | 308 → 310 | 4.2161 | 4.7346 | +12.3% |
| Baby & Toddler | 248 → 184 | 1.8845 | 2.0005 | +6.2% |
| Beauty | 272 → 199 | 1.6927 | 1.7887 | +5.7% |
| Toys | 147 → 146 | 2.3475 | 2.2858 | −2.6% |
| Automotive | 169 → 192 | 1.7250 | 1.6394 | −5.0% |

Broad-based, with click volumes broadly stable. Not concentrated in one vertical.

### Attribution is diffuse, not concentrated

| Measure | Value |
|---|---|
| Campaigns involved (2 movers) | **4,289** |
| Merchants involved | **1,729** |
| Top merchant's Aug 4 spend on these caches | ZAR 335.93 of ~30,000 |
| Merchants with ≥30 clicks both days | 20 |
| — of those, CPC rose | **15 (75%)**, median **+5.9%** |

**Caveat recorded at the time:** the breadth test rests on only 20 merchants, because spend
is so fragmented that few clear 30 clicks on these two caches in both windows. It is
directionally consistent but the **bid-column evidence carries the conclusion**, not this.

**No merchant table is meaningful for this finding** — the largest single actor is 1.1% of
the affected spend. A "top merchants" ranking would be padding.

---

## Marketplace-wide context (30 days) — why this ticket is mis-prioritised

`PAGE_PERFORMANCE_PLA_REPORT`, all pages, Jul 6 – Aug 4. 30-day totals: spend
**ZAR 27,616,648.52**, clicks **5,428,778**, impressions **370,003,933**, CPC **5.0871**,
CTR **1.4672%**.

- **Marketplace CPC is not spiking.** Aug 4 at ZAR 4.9855 is *below* the 30-day average and
  well below the Jul 23–26 peak (5.3558–5.5436). Consistent with the finding being confined
  to the PRODUCT/CATEGORY category caches — invisible in an aggregate that is 85% SEARCH.
- **CTR is on a genuine decline** — the more material signal, applying to 100% of spend:

| Comparison | Peak | August | Δ |
|---|---|---|---|
| Mondays | 1.5040% (Jul 20) | 1.3507% (Aug 3) | **−10.2%** |
| Tuesdays | 1.4792% (Jul 21) | 1.3585% (Aug 4) | **−8.2%** |
| 14-day aggregate | 1.5022% (Jul 6–19) | 1.4329% (Jul 22–Aug 4) | −4.6% |

  **Correction recorded:** an earlier statement put this at "roughly 16%", comparing 1.67%
  (a Sunday, structurally high) against 1.35% (a Monday). That was an unfair comparison.
  Matched-weekday figures above are the defensible ones. Still real, still bigger in scope
  than the CPC ticket, and happening on *rising* impressions (Jul 27 hit a 15.08M peak at
  one of the month's lowest CTRs — impression dilution).
- **Spend peaked Jul 27–28** (ZAR 1.09–1.10M/day) and has fallen ~17% to 0.88–0.92M.

### Sizing the actual harm

| | Value |
|---|---|
| PRODUCT actual spend, Aug 4 | ZAR 102,181.39 |
| Counterfactual at Jul 28 CPC (36,303 × 2.6691) | ZAR 96,908.40 |
| **Net excess** | **≈ ZAR 5,273/day** |
| As share of Aug 4 marketplace PLA spend | **0.57%** |
| Five affected caches' combined spend | ZAR 43,793 = **4.8%** of PLA spend |
| Annualised if sustained | ≈ ZAR 1.9M |

Offsets: `NOVELTY_CATEGORY_CACHE` −22% *saved* ~ZAR 1,537/day; `UA_BRAND_CACHE` ~ZAR 644/day.

---

## Merchant-level cohort analysis — Aug 2 vs Aug 4

**Confound stated up front and repeatedly: Aug 2 is a Sunday, Aug 4 a Tuesday.** This
comparison largely measures weekday participation. Retained here because the user asked for
it and because one sub-result does survive the confound.

PRODUCT page, all merchants. Totals: spend 83,172.05 → 100,162.32 (**+16,990.27**).

| Cohort | Merchants | Aug 2 spend | Aug 4 spend | Δ | Contribution | CPC |
|---|---|---|---|---|---|---|
| **Retained** (both days) | **1,503** | 79,124.50 | 80,935.10 | +1,810.60 | **+10.7%** | 2.4677 → 2.7213 (**+10.3%**) |
| **Added** (absent Aug 2) | 458 | — | 19,228.51 | +19,228.51 | +113.2% | 3.2735 |
| **Moved away** | 296 | 4,046.95 | — | −4,046.95 | −23.8% | 2.8948 |
| **Total** | **2,257** | **83,172.05** | **100,162.32** | **+16,990.27** | 100% | 2.4856 → 2.8123 |

Active merchants 1,799 → 1,961. Clicks: retained 32,064 → 29,741 (−7.2%); added 5,874;
moved away 1,398.

**What survives the confound:** the retained cohort's **+10.3% CPC on 7.2% fewer clicks**.
That is not a participation effect, and it independently matches the +11.4% measured at
cache level. **What does not:** the "+113.2% contribution from added merchants" is
overwhelmingly small advertisers who don't serve on Sundays. Not advertiser acquisition.

### The ZAR 1.50 floor and above-floor migration

| | Aug 2 | Aug 4 | Δ |
|---|---|---|---|
| Total clicks | 33,462 | 35,615 | +6.4% |
| Clicks at **exactly ZAR 1.50** | 19,401 | 19,329 | **−0.4%** |
| **Share at floor** | **57.98%** | **54.27%** | −3.7pp |
| Above-floor clicks | 14,061 | 16,286 | **+15.8%** |
| **Above-floor CPC** | 3.8455 | 4.3699 | **+13.6%** |

**Over half of all PRODUCT-page clicks clear at exactly the floor.** The floor-priced click
count is *flat*, so **every additional click came in above the floor**, and above-floor
clicks got 13.6% more expensive. Two compounding effects. Also a second independent
confirmation that the floor itself did not move.

### Top movers (|Δ| > ZAR 250) — 16 of 2,257

| Merchant | ID | Aug 2 | CPC | Aug 4 | CPC | Δ | Contrib | Status |
|---|---|---|---|---|---|---|---|---|
| SNT Sports (Sport) | R1075 | — | — | 707.31 | 11.595 | +707.31 | +4.16% | ADDED |
| VER MR AMERICA | M29829379 | 279.74 | 4.054 | 823.40 | 5.758 | +543.66 | +3.20% | retained |
| BuildSaver | M29827693 | — | — | 444.65 | 5.775 | +444.65 | +2.62% | ADDED |
| Topika | M29886965 | 469.36 | 2.246 | 890.73 | 2.604 | +421.37 | +2.48% | retained |
| Yzaanshop | M29896074 | 21.55 | 3.592 | 435.21 | 2.981 | +413.66 | +2.43% | retained |
| Homemark | M9897 | 27.00 | **1.500** | 433.44 | 4.334 | +406.44 | +2.39% | retained |
| AC/DC DYNAMICS CC | M29825263 | 19.50 | **1.500** | 423.01 | 5.355 | +403.51 | +2.37% | retained |
| EcoFlow | M29877282 | 27.22 | 2.722 | 390.64 | 5.073 | +363.41 | +2.14% | retained |
| App – Tevo | R361 | — | — | 363.37 | 5.344 | +363.37 | +2.14% | ADDED |
| Relevium Health | M29828911 | — | — | 346.77 | 9.908 | +346.77 | +2.04% | ADDED |
| Greenlane Gear | M29824624 | 35.35 | 5.891 | 325.82 | 3.394 | +290.47 | +1.71% | retained |
| LOWKAL | M29892931 | — | — | 278.12 | 5.917 | +278.12 | +1.64% | ADDED |
| Avtel | M29869968 | 52.30 | 10.460 | 322.72 | 1.992 | +270.42 | +1.59% | retained |
| MM Trading | M29851699 | 260.05 | 2.681 | 8.66 | 2.164 | **−251.39** | −1.48% | retained |
| 3G Mobile – Huawei | R29893748 | 555.57 | 1.592 | 271.81 | 1.637 | **−283.76** | −1.67% | retained |
| Epic Vendor Services | M29894392 | 641.16 | 4.191 | 341.47 | 3.594 | **−299.69** | −1.76% | retained |

No merchant contributes more than **4.16%**. Several retained merchants moved **off** the
floor entirely (Homemark 1.500 → 4.334; AC/DC 1.500 → 5.355).

### Explaining the decliners — audit events

- **3G Mobile – Huawei (−73% on Aug 4): campaign paused.** `SMP_SP_Auto_14_14i_4.23`
  (1216655) went **ACTIVE → PAUSED at 2026-08-03 06:07:55**. Wallet ~ZAR 295,000, so not
  budget — an advertiser/ops pause.
- **MM Trading (−ZAR 251): wallet exhaustion.** No status change; balance **ZAR 1.09**.
  *Inference* from a current near-zero balance plus spend collapse — the Aug-4 balance is
  not directly observable.
- **Mobile Complete (R2326): campaign lifecycle.** Paused Aug 2 20:23, reactivated Aug 3
  13:21. But its decline ran Jul 30 – Aug 2, *before* those events — the Samsung
  "Q8B8H8 + Watch Pre-Order" campaign wound down. Wallet ~ZAR 582,000.
- **Beauty – Loreal (R293): active rotation.** Six new "Telescopic Extensionist NPD"
  campaigns DRAFT → LAUNCH_INPROGRESS at 12:00–12:12 Aug 4, **ACTIVE at 17:00–17:01**,
  while `Laque Resistance Nudes` (1349441) was paused 16:00:53. Live at 17:00 → minimal
  Aug-4 impact; expect it from Aug 5.

---

## Bucketing the 1,503 retained merchants by spend change

| Bucket | Merchants | % | Spend Aug2 | **Share A2** | Spend Aug4 | **Share A4** | **Shift** | Δ spend | Clicks Δ | CPC Aug2 | CPC Aug4 | **CPC Δ** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ≤ −75% | 128 | 8.5% | 4,062.05 | 5.13% | 529.39 | 0.65% | −4.48pp | −3,532.67 | −82.5% | 3.142 | 2.342 | **−25.4%** |
| −75 to −50% | 218 | 14.5% | 9,280.17 | 11.73% | 3,636.63 | 4.49% | −7.24pp | −5,643.54 | −56.3% | 2.496 | 2.237 | **−10.4%** |
| −50 to −25% | 229 | 15.2% | 14,842.55 | 18.76% | 9,334.88 | 11.53% | −7.23pp | −5,507.67 | −33.9% | 2.455 | 2.334 | −4.9% |
| −25 to −10% | 140 | 9.3% | 13,442.83 | 16.99% | 11,180.59 | 13.82% | −3.17pp | −2,262.24 | −19.5% | 2.321 | 2.398 | +3.3% |
| **flat (−10..+10%)** | **208** | 13.8% | 16,289.13 | **20.59%** | 16,048.37 | **19.83%** | **−0.76pp** | −240.76 | −4.5% | 2.449 | 2.527 | +3.2% |
| +10 to +25% | 71 | 4.7% | 4,716.54 | 5.96% | 5,472.53 | 6.76% | +0.80pp | +755.99 | **+1.8%** | 2.632 | 3.000 | **+14.0%** |
| +25 to +50% | 111 | 7.4% | 6,604.48 | 8.35% | 9,131.43 | 11.28% | +2.93pp | +2,526.95 | +16.7% | 2.182 | 2.585 | **+18.5%** |
| +50 to +100% | 128 | 8.5% | 5,836.34 | 7.38% | 10,038.54 | 12.40% | +5.02pp | +4,202.20 | +37.7% | 2.690 | 3.358 | **+24.9%** |
| +100 to +300% | 182 | 12.1% | 3,216.68 | 4.07% | 8,402.91 | 10.38% | +6.31pp | +5,186.23 | +104.6% | 2.545 | 3.249 | **+27.7%** |
| > +300% | 88 | 5.9% | 834.31 | 1.05% | 7,158.54 | 8.84% | +7.79pp | +6,324.23 | +523.7% | 2.674 | 3.679 | **+37.6%** |
| **Total** | **1,503** | 100% | **79,125** | 100% | **80,934** | 100% | — | **+1,809** | −7.2% | 2.468 | 2.721 | **+10.3%** |

### Gross churn dwarfs the net

| | Merchants | Amount |
|---|---|---|
| Gross decrease (buckets 1–4) | 715 (47.6%) | **−ZAR 17,187** |
| Gross increase (buckets 6–A) | 580 (38.6%) | **+ZAR 18,996** |
| Flat | 208 (13.8%) | −ZAR 241 |
| **Net** | 1,503 | **+ZAR 1,809** |

Gross churn **ZAR 36,183 = 45.8% of the Aug-2 retained base**, netting to ZAR 1,809.
**Nearly half the retained merchants (715) spent LESS** on a day when page spend rose 20.4%.

### Spend-share redistribution

| Group | Share Aug 2 | Share Aug 4 | Shift |
|---|---|---|---|
| Decliners (1–3) | **35.62%** | **16.67%** | **−18.95pp** |
| Middle (4–6) | 43.54% | 40.41% | −3.13pp |
| Growers (7–A) | **20.85%** | **42.90%** | **+22.05pp** |

**22 percentage points of spend share moved from decliners to growers, among the same
merchants, over two days.**

### The CPC gradient — and its honest limit

Ordered by spend change, CPC change runs **−25.4% → −10.4% → −4.9% → +3.3% → +3.2% →
+14.0% → +18.5% → +24.9% → +27.7% → +37.6%** with no inversions across ten buckets.

**Partly mechanical** — spend = clicks × CPC, so bucketing on spend change and reading CPC
out of it leans positive by construction. Suggestive, not proof.

**Where CPC genuinely does the work — bucket 6.** 71 merchants: clicks **+1.8%**, CPC
**+14.0%**. They got the same volume for 14% more money. **The cleanest "harmed advertiser"
group in the dataset.** Buckets 8/9/A are volume-driven (+37.7%, +104.6%, +523.7% clicks).
Buckets 4–5 (348 merchants, the largest spend block at ZAR 29.7k) saw fewer clicks at a
higher price.

### Cache mix by bucket group — kills a tempting hypothesis

If the cache migration were reallocating volume between merchants, growers would gain
specifically in `SIMILAR_ITEM_GROUP_CACHE`. Clicks Aug 2 → Aug 4:

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
| SIMILAR_SKU_CACHE | 1,907 → 0 | 3,555 → 0 | 306 → 0 |
| SIMILAR_ITEM_GROUP_CACHE | 131 → 1,533 | 217 → 4,826 | 17 → 994 |
| **Total** | **11,034 → 5,845 (−47%)** | **19,362 → 19,334 (−0.1%)** | **1,527 → 4,462 (+192%)** |

**Growers grew ~180–215% in essentially every cache, uniformly.** Not a cache-level
reallocation — a merchant-level change. **And the decliners lost 47% of clicks across every
cache from a real base of 11,034 clicks, on a day the page grew.** That asymmetry is the
anomaly worth further work; unlike the growers it cannot be dismissed as small numbers.

---

## The 270 growers (buckets 9 + A) — budget, wallet, targeting

182 in +100–300%, 88 in >+300%. Full raw data exported to
`~/Downloads/all270.csv` (BQ figures) and `~/Downloads/joined270.csv` (with budget/wallet/
BU joined). `client_id` in the BQ clicks table was verified to equal `os_client_id`
(M29829379→272775, M9897→270756, M29825263→271854, all matching audit-event IDs).

### Budget — the naive number is wrong

| Cohort | Merchants | Budget Aug 2 | Budget Aug 4 | Change |
|---|---|---|---|---|
| Naive: all 270 | 270 | 19,892.70 | 16,273.12 | −18.2% |
| **Trustworthy: present both days** | **46** | **8,054.40** | **7,680.76** | **−4.6%** |

Split: 46 both days · **52 present Aug 2 only** · 35 Aug 4 only · **137 neither**.
Of the 46: 10 raised, 9 cut, **27 unchanged**.

### The cleanest platform read in the whole investigation

The **27 merchants whose daily budget was identical on both days**:

| Metric | Aug 2 | Aug 4 | Change |
|---|---|---|---|
| Daily budget | unchanged | unchanged | **0.0%** |
| Product spend | 215.24 | 680.92 | +216.4% |
| Clicks | 83 | 203 | +144.6% |
| **CPC** | **2.5933** | **3.3543** | **+29.3%** |

No advertiser action, no budget change, CPC +29.3%. **Small sample (83 clicks)** —
directional, not conclusive — but it points the same way as the cache and bid evidence.

### Other cohort facts

- **137 of 270 have no daily budget cap at all** — bounded only by wallet. That is how they
  tripled spend with no config change.
- **77 of 270 (29%) hit BU ≥ 100% on Aug 4** — budget-capped.
- **3 negative wallets:** M29899310 (−1.75), M29855427 (−5.28), b_38411 (−10.96).
  **22 below ZAR 100.**
- Budget cuts did not stop growth: M29843215 (200→50), R785110 (500→200), R29885900
  (1,000→600), M29877791 (87.93→20.18), M29899643 (50→7.31) — all grew 103–364%.
- Two rows have zero Aug-2 spend (M29887081, b_38411) so no valid % — technically "added",
  qualified via nonzero clicks with zero recorded spend.

### Targeting changes — substantial, and clustered

**189 campaign status events** across the top-28 growers in four days: 126 → ACTIVE,
60 → PAUSED, 2 → DRAFT, 1 → LAUNCH_INPROGRESS.

| Client | Merchant | Status events | Product-selection activity |
|---|---|---|---|
| 10128669 | Spark living | **50** | ~20 new campaigns (1354863–1356177) |
| 10131695 | Yzaanshop | **33** | ~30 new campaigns (1355855–1356027), mostly 1 SKU each |
| 271982 | Chenshia Granary | **21** | **41 SKUs bulk-added** to campaign 1204927 + 2 new campaigns |
| 10166464 | SUNNYLY | 16 | ~23 new campaigns (1355871–1355927) |
| 273189 | Consumer Importers | 15 | ~12 new campaigns (1356601–1356641) |
| 10160487 | APEXLINK | 15 | 1 new campaign |
| 258366 | Greenlane Gear | 14 | 2 new campaigns (1356711, 1356720) |
| 270756 | Homemark | 9 | SKUs across 1249277 / 1289734 / 1289769 + new 1356483 / 1356508 |
| 271405 | Oco Life by Organico | 0 | **24 SKUs added** to campaign 688607 |
| 200729 | HiSense SA | 1 | SKUs across 1187767 / 1226884 / 1313519 / 1355495 |
| 527628 | Hannes Burger | 4 | 11 SKUs added to 1289793 |
| 272508 | Alcell | 1 | 6 SKUs added to 1355376 |

Budget raises found: Chenshia **+1,650** across 8 campaigns · Greenlane **+1,550** ·
HiSense **+1,550** across 4 · Lian Hui **250 → 462 → 924** · Comfy Home **0 → 600**.

**Conclusion: roughly half these merchants grew because they acted, not because of the
platform.** 14 of the top 28 show clear advertiser-side action. The remainder split into
platform effect (VER MR AMERICA +42% CPC, AC/DC 1.50→5.36), floor exits (Homemark, AC/DC,
CART IN MART, Country Comfort, Oco Life all at exactly 1.50 on Aug 2), and base-effect
noise (Designer Concepts: CPC 16.78 on **7 clicks**).

### Correction recorded

An earlier statement claimed spend share "is redistributing toward merchants whose cost per
click is rising… the clearest single piece of evidence that the bid change drove
reallocation." **This overreached for buckets 9 and A.** Their share gain comes from
near-zero Sunday baselines (bucket A averages **3.5 clicks/merchant** on Aug 2), and a
third of the top growers saw CPC *fall*. The ten-bucket gradient still holds; these two
buckets are evidence of a weekday base effect, not of the bid mechanism.

---

## Single-merchant deep dive — M29877282 (EcoFlow), os_client_id 10042968

Chosen because it looked like the strongest platform-effect case: budgets cut ZAR 1,200 yet
spend rose 14×. **The deep dive overturned that.**

### The correction

| Cut | Jul 28 | Aug 4 | Change |
|---|---|---|---|
| **All SKUs** (as originally reported) | 3.8513 | 5.0732 | **+31.7%** |
| **Continuing SKUs only** (17, both days) | **4.5031** | **4.2630** | **−5.3%** |
| New SKUs (5, absent Jul 28) | — | 7.9329 | — |
| Dropped SKUs (11, absent Aug 4) | 1.8550 | — | — |

For SKUs served on both days, **CPC fell 5.3%**. The +31.7% is entirely a **SKU-mix
effect**: five new SKUs entered at ZAR 7.93 average CPC contributing ZAR 134.86 (34.5% of
Aug-4 spend), while eleven cheap SKUs at ZAR 1.86 dropped out.

This does **not** overturn the marketplace finding (measured across 879 cells holding mix
fixed) but EcoFlow was a poorly chosen exemplar, and the lesson is: **decompose before
labelling a single merchant as evidence.**

### Config state — essentially unchanged

| Check | Result |
|---|---|
| Campaign status changes (Aug 1–4) | **None** |
| Product-selection audit events (Aug 1–4) | **None** |
| Campaigns added / removed between days | **0 / 0** |
| Effective-status changes across 8 active campaigns | **0** — all ACTIVE both days |
| Bid type (clicks data) | **AUTO_CPC only** |
| Budget changes | **2 cuts, Aug 4 08:22** by `takealot-M29877282` |

Cuts: campaign 1255198 **1,500 → 1,000**; campaign 1239052 **2,000 → 1,300**.

### Campaign-level (8 active of 146 total campaigns)

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

**Total spend flat (+1.1%)** while budget fell 21.5%. PRODUCT page is only **4.9% → 7.6%**
of this merchant's spend.

**Two structural findings:**
- **Campaign 1257922's Aug-4 budget is exactly ZAR 1,639.87 — identical to the wallet
  balance** (configured: 2,500). The effective budget is being **clamped to remaining
  wallet**. Worth knowing as a general behaviour.
- **Wallet fell ZAR 4,619.72 → 1,639.87 (−64.5%)** in seven days. At ~ZAR 5,100/day spend
  against ZAR 1,640 left, the account runs dry within a day. **This is the most actionable
  finding about this merchant and it has nothing to do with CPC.**

### PRODUCT-page daily trend

| Date | Clicks | Spend | CPC | SKUs | Camps | avg raw_bid | avg orig_bid | avg bid (USD) |
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
| **Aug 2** | **10** ⚠️ | **27.22** | 2.7224 | **8** | 3 | 0.17100 | 0.23028 | 0.17301 |
| Aug 3 | 62 | 220.57 | 3.5575 | 29 | 5 | 0.17597 | 0.46422 | 0.22608 |
| **Aug 4** | **77** | **390.64** | **5.0732** | 22 | 5 | 0.17844 | **0.59732** | 0.32240 |

**Aug 2 is the anomaly, not Aug 4** — 10 clicks against a 36–114 range. That collapsed
denominator is what produced the headline "+1,335%" in the bucket analysis. Against Jul 28
the real moves are clicks +18.5%, spend +56.0%, CPC +31.7%.

### SKU-level, Jul 28 vs Aug 4 (33 SKUs)

| SKU | Clk J28 | Spend J28 | CPC J28 | Clk A4 | Spend A4 | CPC A4 | Δ | Caches |
|---|---|---|---|---|---|---|---|---|
| **234640665** | 0 | — | — | 10 | **102.31** | **10.231** | **+102.31** | BRAND_GRAN_CAT, SIMILAR_ITEM_GROUP, SOLR_CAT_REMKT, GRAN_SOLR_CAT |
| **223632782** | 4 | 18.98 | 4.745 | 11 | **109.32** | **9.938** | **+90.34** | SIMILAR_ITEM_GROUP, UA_BRAND, CAT_PRICE_DISC_L3, SOLR_CAT, SOLR_CAT_REMKT, GRAN_SOLR_CAT |
| 234861661 | 3 | 6.04 | 2.012 | 9 | 39.80 | 4.422 | +33.76 | SOLR_CAT_REMKT, BRAND_GRAN_CAT, SIMILAR_ITEM_GROUP, CAT_PRICE_DISC_L3 |
| 235146340 | 0 | — | — | 3 | 24.77 | 8.256 | +24.77 | UA_BRAND, GRAN_SOLR_CAT, SOLR_CAT_REMKT |
| 228717675 | 1 | 1.50 | 1.500 | 4 | 7.09 | 1.773 | +5.59 | UA_BRAND, SIMILAR_ITEM_GROUP, SOLR_CAT_REMKT, BRAND_GRAN_CAT |
| 234861666 | 0 | — | — | 2 | 3.75 | 1.874 | +3.75 | SIMILAR_ITEM_GROUP |
| 216533597 | 1 | 3.08 | 3.077 | 3 | 5.93 | 1.976 | +2.85 | SOLR_CAT_REMKT, GRAN_SOLR_CAT |
| 230245430 | 2 | 3.74 | 1.868 | 3 | 6.45 | 2.149 | +2.71 | UA_BRAND, SOLR_CAT, SOLR_CAT_REMKT, BRAND_GRAN_CAT |
| 230511835 | 0 | — | — | 1 | 2.53 | 2.535 | +2.53 | UA_BRAND |
| 226247181 | 1 | 1.50 | 1.500 | 2 | 3.34 | 1.668 | +1.84 | NOVELTY_CAT, UA_BRAND |
| 229562655 | 0 | — | — | 1 | 1.50 | 1.500 | +1.50 | SOLR_CAT_REMKT |
| 215922023 | 1 | 1.50 | 1.500 | 2 | 3.00 | 1.500 | +1.50 | GRAN_SOLR_CAT_REMKT, SIMILAR_ITEM_GROUP, GRAN_SOLR_CAT |
| 228717679 | 2 | 3.00 | 1.500 | 2 | 3.00 | 1.500 | 0.00 | SIMILAR_ITEM_GROUP, UA_BRAND, SOLR_CAT_REMKT |
| 236973220 | 2 | 3.00 | 1.500 | 2 | 3.00 | 1.500 | 0.00 | SOLR_CAT_REMKT, BRAND_GRAN_CAT |
| 233150613 | 1 | 1.50 | 1.500 | 0 | — | — | −1.50 | BRAND_GRAN_CAT |
| 233552612 | 2 | 3.00 | 1.500 | 1 | 1.50 | 1.500 | −1.50 | NOVELTY_CAT, GRAN_SOLR_CAT |
| 226374882 | 1 | 1.50 | 1.500 | 0 | — | — | −1.50 | BRAND_GRAN_CAT |
| 226375042 | 2 | 3.00 | 1.500 | 1 | 1.50 | 1.500 | −1.50 | SIMILAR_ITEM_GROUP, CAT_TOP_POPULAR |
| 220150095 | 1 | 1.50 | 1.500 | 0 | — | — | −1.50 | **SIMILAR_SKU** |
| 232623368 | 1 | 1.50 | 1.500 | 0 | — | — | −1.50 | UA_BRAND |
| 233150614 | 1 | 1.50 | 1.500 | 0 | — | — | −1.50 | SOLR_CAT_REMKT |
| 215604709 | 1 | 1.50 | 1.500 | 0 | — | — | −1.50 | **SIMILAR_SKU** |
| 216998210 | 1 | 1.50 | 1.500 | 0 | — | — | −1.50 | **SIMILAR_SKU** |
| 235146346 | 1 | 2.71 | 2.712 | 0 | — | — | −2.71 | CAT_PRICE_DISC_L3 |
| 235146342 | 3 | 7.90 | 2.635 | 1 | 5.17 | 5.171 | −2.73 | UA_BRAND, SOLR_CAT_REMKT |
| 232623365 | 4 | 9.49 | 2.373 | 2 | 6.66 | 3.331 | −2.83 | BRAND_GRAN_CAT, UA_BRAND, CAT_PRICE_DISC_L3 |
| 236973216 | 2 | 3.16 | 1.581 | 0 | — | — | −3.16 | CAT_PRICE_DISC_L3, UA_BRAND |
| 229562654 | 2 | 3.41 | 1.705 | 0 | — | — | −3.41 | UA_BRAND, CAT_PRICE_DISC_L3 |
| 226329522 | 5 | 9.61 | 1.922 | 1 | 1.50 | 1.500 | −8.11 | SIMILAR_ITEM_GROUP, CAT_PRICE_DISC_L3, **SIMILAR_SKU**, GRAN_SOLR_CAT_REMKT |
| 233150618 | 4 | 9.90 | 2.474 | 0 | — | — | −9.90 | SOLR_CAT_REMKT, SOLR_CAT, UA_BRAND |
| 232623367 | 5 | 25.98 | 5.196 | 7 | 12.99 | 1.856 | −12.99 | **SIMILAR_SKU**, SIMILAR_ITEM_GROUP, UA_BRAND, CAT_PRICE_DISC_L3, SOLR_CAT_REMKT |
| 234861665 | 6 | 23.91 | 3.986 | 4 | 10.26 | 2.565 | −13.65 | SOLR_CAT_REMKT, BRAND_GRAN_CAT, **SIMILAR_SKU**, SIMILAR_ITEM_GROUP, UA_BRAND |
| **221637484** | 5 | **95.42** | **19.084** | 5 | 35.26 | **7.053** | **−60.16** | **SIMILAR_SKU**, SIMILAR_ITEM_GROUP, UA_BRAND, SOLR_CAT_REMKT |
| **TOTAL** | **65** | **250.33** | **3.8513** | **77** | **390.64** | **5.0732** | **+140.31** | |

**Readings:**
- **Concentration roughly doubled.** Aug-4 top four SKUs = ZAR 276.20 = **70.7%** of spend;
  Jul-28 top SKU was 38.1%. Two of the four had zero Jul-28 clicks.
- **SKU 221637484 is the most interesting row:** identical 5 clicks both days, CPC
  **19.084 → 7.053 (−63%)**. On Jul 28 it alone was 38% of product-page spend. Its collapse
  is the largest offsetting move. It served on the retired `SIMILAR_SKU_CACHE`.
- **Six SKUs served on `SIMILAR_SKU_CACHE`.** Three stopped serving entirely; three
  continued via `SIMILAR_ITEM_GROUP_CACHE` **at lower CPC**. For this merchant the
  migration, if anything, *reduced* CPC.
- Serving breadth narrowed 28 → 22 SKUs. A hard **ZAR 1.50 floor** appears on 14 rows.

### Bid configuration for SKU 223632782 (`os_product_ads_product_selection_100002`)

| Field | Value |
|---|---|
| **Manual bid** (`onsite_manual_cpc`, `_usd`, `onsite_manual_cpm`, `_usd`) | **NULL on all 16 rows — no manual bid set anywhere** |
| `roi_optimizer_bid_multiplier` | **1.0** on all 16 |
| `roi_optimizer_bid_multiplier_v2` | **1.0** on all 16 |
| **`roi_optimizer_bid_multiplier_v3`** | **the live one — varies 0.0000899 → 6.19** |
| `onsite_target_roi` | **10.0** on the two ROI-strategy campaigns; NULL on the 14 AUTO_CPC |
| Currency | ZAR |
| `is_active` / `is_bidding_strategy_active` | true on all 16 |
| `bidding_strategy_level` | marketingCampaign on all 16 |
| `is_paused_by_optimizer` | false on all 16 |
| `ctr_optimizer_score` | 1.0 on all 16 |
| `roi_optimizer_score`, `effective_ctr` | NULL on all 16 |

| Internal ID | Marketing ID | Campaign | Strategy | Target ROI | **v3 multiplier** | Last update |
|---|---|---|---|---|---|---|
| 874218 | **1340532** | SP-KW-行业词-EXPH-R系列-高CTR曝光 | AUTO_CPC | — | **6.1917364224** | **2026-08-05 13:12:36** |
| 858562 | **1257922** | SP-KW-品牌词-EX-8月主推 | AUTO_CPC | — | **1.611003248540** | **2026-08-05 13:12:36** |
| 822245 | 1199761 | All Products (26th Mar \| 19:13) | AUTO_CPC | — | 1.0 | 2026-04-03 01:33:54 |
| 835986 | **1218309** | Auto-all | AUTO_CPC | — | **0.989570390722** | **2026-08-05 13:12:36** |
| 841488 | 1226864 | All Products (11th May \| 15:53) | AUTO_CPC | — | 0.825255620202 | 2026-05-17 03:20:58 |
| 768128 | 1116910 | 户外 | AUTO_CPC | — | 0.373985854150 | 2026-04-03 01:24:49 |
| 777863 | 1131570 | 黑五auto | AUTO_CPC | — | 0.328087008139 | 2026-02-09 01:57:43 |
| 819279 | 1195797 | Auto | AUTO_CPC | — | 0.324110428018 | 2026-06-21 03:10:29 |
| 770540 | 1119604 | 品类kw-fish | **ROI** | **10.0** | 0.234437548825 | 2025-11-17 03:16:53 |
| 716249 | 1041672 | 单品 auto | AUTO_CPC | — | 0.207920296899 | 2026-02-09 01:57:43 |
| 566171 | 773942 | PPS-AUTO-4.29 250613去230 | AUTO_CPC | — | 0.062387391173 | 2026-03-12 02:50:11 |
| 848787 | 1238283 | SP-KW-行业词-EX-7月有标主推品 | AUTO_CPC | — | 0.041091432178 | 2026-07-13 03:11:40 |
| 733634 | 1067763 | r2p+r2m test官网 | AUTO_CPC | — | 0.022596643971 | 2025-10-29 03:19:13 |
| 677653 | 957308 | KW-TEST-办公备电相关 | AUTO_CPC | — | 0.011529215046 | 2026-04-03 01:24:49 |
| 564461 | 771412 | R2 RP-KW-EP-品牌词 25.3.25改 | **ROI** | **10.0** | 0.000218120162 | 2026-02-09 01:57:43 |
| 580047 | 812340 | R系列-EP-行业词 | AUTO_CPC | — | 0.000089899053 | 2026-02-27 02:34:00 |

**The three rows updated 2026-08-05 13:12:36 are exactly the three of EcoFlow's 8 active
campaigns that appear here** — 1340532 (v3 = **6.19**), 1257922 (1.61), 1218309 (0.99).
Campaign 1340532 is also the one whose budget was *raised* 700 → 1,000 with BU jumping
27% → 93%. A 6.19× bid multiplier is a plausible mechanism for this SKU's CPC going
4.745 → 9.938 (+109%).

**But it cannot be proven for Aug 4.** This table is a current-state snapshot; those three
rows were rewritten **after** the spike, overwriting whatever applied on Aug 4. The
correlation is suggestive, not evidence.

Related: a realized bid of **USD 0.23764544362788217 = ZAR 3.7395** (× 15.735642) came from
the clicks table — what was actually charged. There is no configured bid to compare it
against, because this SKU is **100% auto-bid**.

---

## Leading hypothesis

**The Aug 3 14:00 SAST relevancy cache migration changed the served-inventory and
competitive landscape, and the automated bidders (AUTO_CPC / ROI) progressively re-priced
the category caches upward over the following ~24 hours.**

Supporting: the cutover precedes the confirmed Aug-4 spike; the increase **ramps** rather
than steps, matching automated adaptation rather than a config flag; the selectivity is
structured, not market-wide — five non-remarketing category caches up 13–20%, **both**
remarketing variants down, brand/merchant caches flat, `NOVELTY_CATEGORY_CACHE` down 22%.
Broad market competition would not spare remarketing variants so cleanly nor push one cache
down 22% the same day.

Decomposing the +19.6% on GRANULAR_SOLR_CATEGORY: ~**+11.4pp** genuine price rise on
unchanged merchant/category cells, ~**+4.5pp** from the raw→charged multiplier rising
(1.294 → 1.352), remainder from a pricier entrant cohort.

---

## Corrections made during this investigation

Recorded because each one came from going a level deeper, and the pattern is instructive.

1. **"Not bid pressure — purely a denominator artifact."** True of the page aggregate, wrong
   as a full explanation. Category caches showed real bid pressure with flat volume; the
   aggregate masked it because volume collapsed the other way in other caches.
2. **"Two category caches rose."** It was **five**. The first pass only pulled two, then
   generalised from them.
3. **"Spend share is redistributing toward merchants whose CPC is rising — clearest evidence
   of the bid mechanism."** Overreached for buckets 9/A: near-zero Sunday baselines, and a
   third of top growers saw CPC fall.
4. **"Three consecutive days of acceleration."** Rested on Aug 5 partial data. Only Aug 4
   stands; Aug 3 is inside the pre-existing band.
5. **"CTR down ~16%."** Compared a Sunday against a Monday. Matched-weekday: −8.2% to −10.2%.
6. **"EcoFlow is the cleanest platform-effect case."** Wrong — SKU-mix effect; continuing
   SKUs' CPC *fell* 5.3%.
7. **"I have no tool for floors."** `get_keyword_floor_bids` exists but is keyword-scoped;
   `get_inventory_details` returned empty for takealot. The conclusion held, the reason given
   did not.

**Generalisable lesson:** every one of these came from reading an aggregate or a percentage
without its denominator or its composition. The fixes were always the same two moves —
**hold the mix fixed**, and **check the base**.

---

## Caveats on the findings as they stand

- **`bid` / `original_bid` / `raw_bid` semantics are inferred, not documented.** Grepped the
  repo and all 43 report configs; no definition found. The whole decomposition depends on
  `raw_bid` being the pre-adjustment input. **Confirm with the ad-server owner before this
  goes to a client.**
- **Rival bids per auction are not visible**, so increased competition cannot be excluded as
  a *contributing* factor — only as the sole explanation.
- **CATEGORY page was never drilled at cache level.** The ticket names it; page-level says
  CPC fell. Whether the same caches moved there is **unverified**.
- **Display was never examined** (user locked scope to PLA).
- **Aug 3 vs Aug 2 is confounded by the weekend.** Only Tue-vs-Tue (Jul 28 vs Aug 4) is
  clean, which is why the conclusion rests on it.
- **No page-scoped ROAS** — cannot say whether advertisers paying 13–20% more converted.
  This is the biggest open gap and the most client-relevant.
- **The 27-merchant unchanged-budget subset rests on 83 clicks.**
- **EcoFlow's "no config changes" was verified only for Aug 1–4** — the 11-day audit window
  504'd. A change on Jul 29–31 would not appear.
- **`bid_max` = exactly 3.1775 on both days** — an unchanged hard cap. Unexplained but
  stable, so not a driver.
- **`NOVELTY_CATEGORY_CACHE` −22.3% is unexplained.**
- **CUSTOM page +185% spend is unexplained** and out of scope.

---

## Actions

1. **Pull the deploy log for Aug 3 ~14:00 SAST (12:00 UTC)** — did the relevancy or bidding
   service release? Highest-value check; the cutover timestamp gives an exact window.
2. **Ask the release owner whether `SIMILAR_ITEM_GROUP_CACHE` was expected to affect
   category-cache bid computation.** If no, the coincidence needs another explanation and
   the competition angle reopens.
3. **Confirm the category floor config history** — now a *falsification* check, since the
   distribution evidence says it is not a floor.
4. **Confirm the three bid-column semantics** with the ad-server owner.
5. **Measure ROAS on the affected caches** — converts this from a pricing curiosity into
   either "advertisers were harmed" or "no material impact". Requires a data source that
   joins merchant × page × revenue, which does not currently exist.
6. **Reply to the ticket correcting the framing:** WoW CPC *fell* on both named pages; the
   genuine event is Aug 4, cache-specific, ≈ZAR 5,273/day.
7. **Open a separate CTR/traffic investigation** (`debug-ctr`) — impressions −11.1%,
   CTR −5.9% on the product page, and −8.2% to −10.2% marketplace-wide on matched weekdays.
   Applies to 100% of spend.
8. **Flag wallet risk proactively:** 3 negative balances (M29899310, M29855427, b_38411),
   22 under ZAR 100. Nossa Pharmacy and Vital guard both ramped 300–540% and went negative.
   Spark living (ZAR 194 est.) and SUNNYLY (ZAR 281 est.) are creating 20+ campaigns each on
   near-empty wallets and will stop serving within days — it will present as a delivery
   complaint.
9. **Escalate the change-control gap internally.** A cache was fully retired mid-afternoon
   on a Monday; two caches moved +15–20% and one −22% the same day; the pricing effect
   surfaced only because a client complained. **The detection gap is the more important
   finding than the CPC number.**
10. **Note the 58%/week campaign-ID churn and 38% merchant churn** as an operational and
    analytical problem — it degrades any campaign-keyed analysis and resets ramp-up.

---

## Cross-references

- **Apollo #2026073189000689** (category page, highest requests / lowest RR) — the
  current-dates re-run requested this session **was never completed**; all three calls
  returned KAM 504. The 2026-08-03 diagnosis (92.2% of category requests untagged) remains
  the only evidence. See `ticket-investigations-2026-08-03.md`.
- **takealot ticket 2, 2026-08-05** (`ticket-investigations-2026-08-05.md`) — seller
  delivery complaint; the campaign re-creation behaviour documented there is what motivated
  keying this investigation's decomposition on `merchant_id` rather than `campaign_id`.
- **Tira ticket 3, 2026-08-05** — the "go to the source when the report layer cannot group"
  precedent. Applied here: `RESPONDED_SKUS_REPORT` hardcodes SEARCH, so cache-level PRODUCT
  analysis went to BigQuery directly.

## Raw data exported

- `~/Downloads/all270.csv` — 270 growers, BQ figures (merchant_id, client_ids, spend/clicks/
  CPC per day, delta, pct, bucket)
- `~/Downloads/joined270.csv` — same, joined with daily budget, wallet, BU, all-page spend.
  Column glossary: `bud2`/`bud4` daily budget (0.00 = missing row, **not** zero),
  `wal2`/`wal4` wallet ZAR, `bu2`/`bu4` utilisation as **fraction**, `tspend*` all-page
  spend, `ps*` PRODUCT-page spend, `pc*` PRODUCT clicks, `cpc*` PRODUCT CPC, `d`/`pct`
  product spend delta / % change.

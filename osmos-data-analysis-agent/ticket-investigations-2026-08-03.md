# Support ticket investigations — 2026-08-03

Five marketplace ad-performance tickets worked through the `debug-*` SOP skills.
All data via `run_report` against the KAM internal-performance reports
(`osmos-performance-local` MCP). Currency INR throughout.

| # | Ticket | Marketplace | Skill | Verdict |
|---|---|---|---|---|
| 1 | Active Campaign Not Serving Ads — vegolution (1080) | bigbasket (444) | debug-keyword-delivery | Partly invalid — 4 kws below request threshold, rest serving; self-competition |
| 2 | Apollo — Low CTR on PLA custom/category/home | apollo-hospitals (434) | debug-ctr | Impression dilution; no pipeline defect |
| 3 | Multiple SKUs on 'Green Tea' not serving | bigbasket (444) | debug-keyword-delivery | Invalid — all 12 SKUs serving; mapping correct |
| 4 | Centrum Ostocalcium — keyword CPC issue | apollo-hospitals (434) | debug-keyword-delivery | Invalid premise — self-competition, table misread |
| 5 | FirstCry managed service — performance improvement | firstcry (366) | debug-roas | Budget target unreachable; CUGO already at target |
| 6 | FirstCry — new/restarted campaigns spend too fast | firstcry (366) | debug-budget-pacing | ACCELERATED delivery; no new-campaign priority |

---

## Environment limitations encountered

These constrained several investigations and are worth fixing:

- **`AUDIT_EVENTS_REPORT` family is blocked** (unregistered appKey, missing BQ
  grants). This removes `get_campaign_status_changes`,
  `check_budget_changes_on_date` and `get_product_selection_changes`. Affected
  tickets 1, 2, 4, 6 — no campaign pause timestamps, budget-change events or
  SKU-selection history available.
- **`get_keyword_categories` has no KAM equivalent** (was an ADK-only S3 reader).
  The keyword→category mapping cannot be read directly — tickets 1 and 3 both
  asked about it. Verified indirectly via `RESPONDED_SKUS_REPORT` cache_type.
- **`SEARCH_QUERY_REQUESTS_PLA_REPORT` retains only ~15 days.** An unfiltered
  call for 09–15 Jul returned zero rows. Blocked verifying eligibility as at the
  date of ticket 1.
- **`CATEGORY_PERFORMANCE_REPORT` has no `page_type` attribute**, so a
  category cut scoped to one page type is impossible (ticket 2).
- **The local shim ignores `limit`** — a request for 60 rows returned 10,000.
  Several calls overflowed and had to be parsed from the saved tool-result file.
- **Report ID keying:** `INTERNAL_KEYWORD_PERFORMANCE_REPORT.perf_campaign_id`
  and `CAMPAIGN_KEYWORDS_REPORT.perf_campaign_id` hold the
  **marketing_campaign_id**, while `RESPONDED_SKUS_REPORT.perf_internal_campaign_id`
  holds the **campaign_id**. Worth documenting in `knowledge/reports.md`.

---

# Ticket 1 — Active Campaign Not Serving Ads | vegolution-india-private-limited (1080)

**Marketplace:** bigbasket-marketplace, agency 444, client 10088009, INR, Asia/Kolkata
**Campaign:** `Paratha` — marketing_campaign_id **1325459**, campaign_id 871811,
os_client_id **10097532**, PERFORMANCE / OS_ADS_SEARCH, AUTO_CPM, ACTIVE, created 2026-07-13
**Window:** 13 Jul – 2 Aug 2026 (ticket window 13–15 Jul shown separately)

## Complaint
8 targeted keywords reported not serving; only "chapathi" responding.

## Campaign config
- 62 targeted keywords, **zero negative keywords** — no negative-match leak.
- `perf_bidding_value` per keyword: chapathi 1890, momo 3780, Tempeh 1200/1360,
  Aashirvaad 890, plant based 960, most others 600, Tempayy 500, Malabar Paratha 500.

## Keyword delivery inside campaign 1325459

| Keyword | Match | Bid | 13–15 Jul imp | 13–15 Jul spend | 13 Jul–2 Aug imp | clicks | spend |
|---|---|---|---|---|---|---|---|
| chapathi | PHRASE | 1890 | 346 | INR 678.51 | 4,485 | 97 | INR 9,070.11 |
| malabar paratha | PHRASE | 500 | 15 | INR 8.00 | 2,556 | 57 | INR 1,457.95 |
| tempeh | PHRASE | 1200/1360 | 10 | INR 13.60 | 850 | 127 | INR 1,236.24 |
| hello tempayy | EXACT | 600 | 6 | INR 3.60 | 349 | 76 | INR 255.18 |
| tempayy | PHRASE | 500 | 2 | INR 1.00 | 326 | 76 | INR 220.88 |
| tempe | PHRASE | 600 | 2 | INR 1.20 | 39 | 5 | INR 24.60 |
| protein paratha | PHRASE | 600 | 0 | INR 0 | 28 | 8 | INR 16.80 |
| protein chapathi | PHRASE | 600 | — | INR 0 | 17 | 2 | INR 10.80 |
| **protein butter** | — | — | **not targeted** | — | — | — | — |

Campaign total 13–15 Jul: ~423 impressions, ~INR 745 — chapathi alone was 82% of
impressions and 91% of spend. The complaint was factually correct **for that window**.

## Request-volume eligibility (trailing 7d to 2 Aug, marketplace-wide)

| Keyword | Requests | Responses | RR | >100 threshold |
|---|---|---|---|---|
| chapathi | 9,615 | 7,896 | 82.1% | eligible |
| malabar paratha | 4,069 | 3,465 | 85.2% | eligible |
| tempeh | 2,894 | 1,416 | 48.9% | eligible |
| hello tempayy | 1,026 | 560 | 54.6% | eligible |
| tempe | 685 | 232 | 33.9% | eligible |
| tempayy | 240 | 91 | 37.9% | eligible |
| protein batter | 93 | 25 | 26.9% | **below** |
| protein butter | 61 | 24 | 39.3% | **below** |
| protein paratha | 43 | 18 | 41.9% | **below** |
| protein chapathi | 32 | 16 | 30.4% | **below** |

## Responded-SKU / relevancy on the brand terms

**"hello tempayy"** — 1,952 requests / 979 responses (RR 50.2%):

| Who serves | cache_type | SKU-imp | Share |
|---|---|---|---|
| Vegolution — Paratha (871811) | TARGETED_KEYWORD_CACHE | 2,336 | 38.3% |
| Vegolution — Search Only momos KW (751827) | TARGETED_KEYWORD_CACHE | 140 | 2.3% |
| Aashirvaad flatbreads — advertiser 10098777 | ONE_WORD_KEYWORD_CATEGORY_SCORE_CACHE_V2 | 1,800 | 29.5% |
| Dairy paneer brands (13 advertisers) | ONE_WORD_KEYWORD_CATEGORY_SCORE_CACHE_V2 | 1,780 | 29.2% |
| The Baker's Dozen | ONE_WORD_KEYWORD_CATEGORY_SCORE_CACHE_V2 | 48 | 0.8% |

**"tempeh"** — 4,529 requests / 2,130 responses (RR 47.0%):

| Who serves | cache_type | SKU-imp | Share |
|---|---|---|---|
| Vegolution — Search Only momos (776442) | TARGETED_KEYWORD_CACHE | 13,104 | **79.0%** |
| Vegolution — Paratha (871811) | TARGETED_KEYWORD_CACHE | 3,272 | 19.7% |
| Competitor paneer (4 SKUs) | SEARCH_TERMS_WITHOUT_BRAND_STUFFING | 216 | 1.3% |

**"tempayy"** (508 req / 154 resp, RR 30.3%) and **"tempe"** (1,176 req / 344 resp,
RR 29.3%): campaign 871811 is the **only responder** — 304 and 136 SKU-impressions, 100%.

> SKU-impressions are per-SKU-per-campaign rows; read as shares, not slot counts.

## Diagnosis

Three distinct causes reported as one ticket:

1. **protein chapathi / protein paratha / protein batter / protein butter** — below
   the 100-requests-per-7-days threshold, so no category mapping exists and they
   cannot receive responses. Expected behaviour, not a defect.
2. **tempeh, hello tempayy** — serving, but split against the advertiser's own
   campaigns. On tempeh, "Search Only momos" takes 79% vs Paratha's 19.7%.
3. **tempayy, tempe, malabar paratha** — serving normally. Low RR is thin supply
   (Vegolution is the only eligible responder), not competition.

Plus a setup discrepancy: **"protein butter" is not targeted** — the campaign has
**"protein batter"**.

## Actions
1. **Relevancy ticket (bigbasket platform):** on the brand query *hello tempayy*,
   ~59% of filled slots go to other advertisers via
   `ONE_WORD_KEYWORD_CATEGORY_SCORE_CACHE_V2` — 29.5% to advertiser 10098777's
   Aashirvaad flatbread Smart Shopping campaigns, 29.2% to dairy paneer SKUs at
   near-zero clicks. Entry point for the relevancy team is that cache_type.
2. **Advertiser-side:** de-duplicate keywords across 1325459 / 1129674 / 1095770;
   raise bids on Tempayy (500), Malabar Paratha (500), Tempe (600).
3. **Confirm "protein butter" vs "protein batter"** with Ads Optimization.

---

# Ticket 2 — Apollo | Low CTR on PLA custom, category & home page (#118296)

**Marketplace:** apollo-hospitals-marketplace, agency 434, client 10084549, INR
**Period:** March 2026 vs June 2026 · **Program:** PLA
**Severity:** HIGH · **Scenario: A — Impression dilution**

> The ticket quoted agency 392, which is **ajio-marketplace**. Corrected to 434 by
> the user. The page data reproduces Harshita's quoted CTRs exactly, confirming scope.

## Page-level triage and I/R gate

| Page | Mar imp | Jun imp | Imp Δ | Mar clicks | Jun clicks | Clicks Δ | Mar CTR | Jun CTR | CTR Δ | I/R Mar→Jun |
|---|---|---|---|---|---|---|---|---|---|---|
| PRODUCT | 336,496 | 2,718,392 | **+708%** | 20,041 | 24,779 | **+23.6%** | 5.96% | 0.91% | −84.7% | **13.8% → 98.1%** |
| HOME | 305,099 | 1,081,181 | +254% | 4,510 | 2,953 | **−34.5%** | 1.48% | 0.27% | −81.5% | 3.0% → 6.4% |
| CATEGORY | 181,592 | 366,440 | +102% | 4,464 | 5,249 | +17.6% | 2.46% | 1.43% | −41.7% | 14.8% → 28.2% |
| CUSTOM | 2,773,143 | 3,067,623 | +10.6% | 16,948 | 8,997 | −46.9% | 0.611% | 0.293% | −52.0% | 57.3% → 75.1% |
| SEARCH | 4,613,264 | 4,327,115 | −6.2% | 68,725 | 59,583 | −13.3% | 1.490% | 1.377% | −7.6% | 84.5% → 69.9% |
| **TPA** (new) | — | 313,312 | new | — | 21,694 | new | — | **6.92%** | — | — → 3.2% |
| **TOTAL** | 8,209,594 | 11,874,063 | **+44.6%** | 114,688 | 123,255 | **+7.5%** | 1.397% | 1.038% | **−25.7%** |

Spend (INR): PRODUCT 785,888 → 1,078,147 (+37%); CATEGORY 136,896 → 220,222 (+61%);
HOME 211,974 → 143,103 (−33%); CUSTOM 1,525,988 → 722,617 (−53%); SEARCH 2,835,783 →
2,579,760 (−9%); TPA new at 903,866. **Total spend flat (+2.8%) vs +44.6% impressions**
— hence CPM fell alongside CTR.

**I/R gate: PASSED.** I/R rose on every complained page. PRODUCT went 13.8% → 98.1%
— in March ~1 in 7 responses rendered, in June nearly all do. Duplicate counting
would push I/R above 100%; it sits at 98.1%. **No pipeline defect, no duplicate
signals** — this answers Harshita's question directly.

## Category drill (L1, marketplace-wide)

> `CATEGORY_PERFORMANCE_REPORT` has no page_type filter. Product page alone was 65%
> of the total impression increase (+2.38M of +3.66M), so this is a proxy.
> Category totals (9.47M / 12.97M) exceed page totals (8.21M / 11.87M) — a SKU maps
> into multiple L1s. Read as shares.

| L1 category | Mar imp | Jun imp | Imp Δ | Mar CTR | Jun CTR | CTR Δ | Merchants Mar→Jun |
|---|---|---|---|---|---|---|---|
| Health & Nutrition | 4,260,269 | 5,841,282 | +37.1% | 1.196% | 0.841% | −29.7% | 56 → **8,703** |
| Personal Care | 2,078,603 | 3,763,255 | +81.0% | 1.464% | 1.046% | −28.5% | 67 → 1,148 |
| Baby Care | 2,381,393 | 2,160,492 | −9.3% | 1.074% | 1.360% | **+26.6%** | 26 → 171 |
| Otc | 464,666 | 351,404 | −24.4% | 3.048% | 2.501% | −17.9% | 32 → 290 |
| Food & Beverages | 39,137 | 318,683 | **+714%** | 3.700% | **0.390%** | **−89.5%** | 12 → 154 |
| Health Devices | 86,348 | **0** | −100% | 3.303% | — | gone | 11 → 27 |
| Medical Equipments & Devices | **absent** | 180,220 | new | — | 2.004% | new | — → 86 |

Health & Nutrition (+1,581,013) and Personal Care (+1,684,652) = **+3.27M ≈ 89% of
the marketplace impression increase.**

**Catalog re-categorisation confirmed:** "Health Devices" vanished, "Medical
Equipments & Devices" replaced it. June adds a clinical taxonomy absent in March
(Cardiology, Dentistry, Orthopedics, Vaccines, Neoplastic Disorders, Endocrine
System) — all with large merchant counts and zero impressions. Merchant–category
mappings rose 100×+. Taxonomy also contains a genuine duplicate:
"Ear Nose & Oropharynx" and "Ear, Nose & Oropharynx" are separate rows, identical values.

## Merchant breakdown — June top spenders

| Merchant | Client ID | Mar spend | Jun spend | Mar imp | Jun imp | Mar clicks | Jun clicks | Mar CTR | Jun CTR | CTR Δ |
|---|---|---|---|---|---|---|---|---|---|---|
| PAMPERS | 10103163 | 452,788 | 542,544 | 665,774 | 728,110 | 7,964 | 9,738 | 1.20% | 1.34% | **+11.7%** |
| CENTRUM | 10115118 | 328,241 | 475,411 | 355,965 | **1,105,577** | 7,303 | 10,721 | 2.05% | 0.97% | **−52.7%** |
| MUSCLEBLAZE | 10114538 | 507,397 | 415,922 | 447,941 | 621,091 | 3,614 | 3,171 | 0.81% | 0.51% | −37.0% |
| MINIMALIST | 10103141 | 150,288 | 350,230 | 275,631 | 762,327 | 4,373 | 10,304 | 1.59% | 1.35% | −15.1% |
| FIXDERMA | 10103129 | 137,951 | 250,589 | 278,430 | 615,542 | 3,864 | 5,822 | 1.39% | 0.95% | −31.7% |
| SUPRADYN | 10103158 | **0** | 247,380 | **0** | 522,561 | 0 | 9,333 | — | 1.79% | new |
| Optimum Nutrition | 10110117 | 517,441 | 210,924 | 571,434 | 362,183 | 4,920 | 1,901 | 0.86% | 0.52% | −39.5% |
| CeraVe | 10103122 | 159,617 | 186,102 | 320,621 | 399,359 | 3,972 | 3,501 | 1.24% | 0.88% | −29.0% |
| AVEENO | 10119936 | **0** | 163,688 | **0** | 177,066 | 0 | 2,148 | — | 1.21% | new |
| NIVEA | 10103146 | 16,436 | 151,315 | 57,845 | 612,855 | 410 | 5,476 | 0.71% | 0.89% | +25.4% |

**Worst CTR degradation (active both periods):** Whisper 1.85% → 0.55% (−70.3%,
clicks −33.7%); GALACT 0.66% → 0.30% (−54.5%); CENTRUM −52.7%; Neuherbs 2.32% →
1.10% (−52.6%, clicks −46.0%).

**New merchants below average CTR** (June avg 1.04%): VOGUE WELLNESS 309,081 imp @
0.75%; Bepanthen 186,086 @ 0.67%; LACTARE 145,111 @ 0.40%; GRITZO 132,511 @ 0.65%;
DERMICOOL 119,280 @ 0.47%; 2baconil 62,942 @ 0.26%. **Total 1,045,910 imp @ 0.61%.**

**Churned merchants above average CTR** (March avg 1.40%): Penegra 5.40%,
Enterogermina 9.85%, Depura 3.23%, STREPSILS 5.00%, Volini 2.56%, GAVISCON 1.60%,
Dulcoflex 10.96%, Neurobion 5.82%, Evion 5.06%, Seven Seas 4.07% and others.
**Total 464,949 imp / 18,412 clicks @ 3.96% — 16% of all March clicks.**

## Diagnosis

Impressions +44.6% vs clicks +7.5% ⇒ CTR −25.7%. Three compounding causes, all on
Apollo's side:
1. Product-page rendering change (I/R 13.8% → 98.1%)
2. Catalog re-categorisation
3. Advertiser roster turnover — high-CTR out (3.96%), low-CTR in (0.61%)

CENTRUM alone = +749,612 impressions ≈ 20% of the total increase, CTR halved.
TPA is the best surface on the marketplace (6.92% CTR) and *lifts* blended CTR.

## Actions
1. Reframe the metric — on product page the advertiser outcome improved. CTR is not
   comparable across the March/June boundary; use clicks, spend and CPC.
2. Business confirmation needed on: product-page rendering change, catalog
   re-categorisation date/scope, TPA launch date.
3. HOME page needs separate remediation — only page losing clicks outright.
4. Address the roster gap; review CENTRUM / GALACT / FIXDERMA placements.
5. Fix the duplicate Ear-Nose-Oropharynx taxonomy rows.

---

# Ticket 3 — Multiple SKUs on 'Green Tea' keyword not serving

**Marketplace:** bigbasket, agency 444 (ticket said "Innovative Retail Concept Pvt.
Ltd." — BigBasket's legal entity; no marketplace of that name exists in the directory)
**Campaign:** `FF_Green tea` — marketing_campaign_id **1060020**, campaign_id 728191,
os_client_id **10092920** (Emperia / indiSecrets), OS_ADS_SEARCH, AUTO_CPM, ACTIVE
**Window:** 13 Jul – 2 Aug 2026

## Verdict: no defect. All 12 SKUs are serving.

| # | SKU | Product | Category | Path | Imp | Clicks | CTR | Spend |
|---|---|---|---|---|---|---|---|---|
| 1 | 40228625 | indiSecrets Pure Tulsi Chamomile Tea | tea-bags | TARGETED_KEYWORD_CACHE | 44,964 | 884 | 1.97% | 972.40 |
| 2 | 40228627 | indiSecrets Pure Tulsi Ginger Turmeric | tea-bags | TARGETED_KEYWORD_CACHE | 37,796 | 860 | 2.28% | 946.00 |
| 3 | 40327244 | indiSecrets Pure Chamomile Tea | tea-bags | TARGETED_KEYWORD_CACHE | 32,076 | 740 | 2.31% | 814.00 |
| 4 | 40327245 | indiSecrets Pure Tulsi Green Tea | tea-bags | TARGETED_KEYWORD_CACHE | 24,784 | 808 | 3.26% | 888.80 |
| 5 | 40228626 | indiSecrets Pure Tulsi Ginger Tea | tea-bags | TARGETED_KEYWORD_CACHE | 23,568 | 372 | 1.58% | 409.20 |
| 6 | 40327246 | indiSecrets Pure Tulsi Lemon Ginger | tea-bags | TARGETED_KEYWORD_CACHE | 20,312 | 476 | 2.34% | 523.60 |
| 7 | 40228624 | indiSecrets Pure Tulsi Tea | tea-bags | TARGETED_KEYWORD_CACHE | 10,264 | 120 | 1.17% | 132.00 |
| **8** | **40092352** | **emperia Tulsi Green Tea** | **green-tea** | TARGETED_KEYWORD_CACHE | **6,968** | 540 | **7.75%** | 594.00 |
| 9 | 40276397 | indiSecrets Assorted Tulsi Infusions 5N | tea-bags | TARGETED_KEYWORD_CACHE | 5,852 | 200 | 3.42% | 220.00 |
| 10 | 40276396 | indiSecrets Assorted Tulsi Infusions | tea-bags | TARGETED_KEYWORD_CACHE | 4,820 | 108 | 2.24% | 118.80 |
| 11 | 40092351 | emperia Green Tea | green-tea | TARGETED_KEYWORD_CACHE | 2,996 | 168 | **5.61%** | 184.80 |
| 12 | 40270718 | emperia Tulsi, Lemon & Honey Green Tea | green-tea | TARGETED_KEYWORD_CACHE | 248 | 24 | **9.68%** | 26.40 |
| | | **TOTAL** | | | **214,648** | **5,300** | 2.47% | **INR 5,830** |

## Answers to the questions asked

| Question | Answer |
|---|---|
| Is the keyword→category mapping correct? | **Yes** — proven empirically. SKUs from both `beverages>tea>tea-bags` (9 SKUs) and `beverages>tea>green-tea` (3 SKUs) served via `TARGETED_KEYWORD_CACHE`, which only happens if the keyword is mapped to both. |
| Mapping/relevancy constraints blocking SKUs? | **No.** All 12 served via the targeted path. |
| Is only SKU 40092352 serving? | **No** — it ranks 8th of 12 (6,968 vs 44,964 for the top SKU). |
| Are competing brands absent? | **No.** Girnar (117,712 SKU-imp), Organic India (~11,800), Organic Tattva (3,068), Maharishi Ayurveda (2,752), Tetley, Society, Tea Culture of the World all served. |
| Under-delivering? | **No** — ~60% share of voice. |

Keyword supply healthy: "green tea" 36,439 requests / 24,554 responses (RR 67.4%)
trailing 7 days.

Likely explanation for the front-end observation: a search page renders only a
small number of ad slots, so any single debug check shows one or two SKUs.

## Genuine finding to pass to the brand
The three actual *green tea* SKUs have the best engagement (7.75%, 5.61%, 9.68% CTR)
and the fewest impressions, while volume concentrates on tulsi/chamomile SKUs at
1.17–2.34% CTR. Recommend splitting the green tea SKUs into a dedicated campaign or
ad group for this keyword.

---

# Ticket 4 — Centrum Ostocalcium | Keyword CPC issue

**Marketplace:** apollo-hospitals, agency 434, INR
**Campaign:** `HM_Apollo_Manual_OstoCal_30_Brand` — marketing_campaign_id **1251331**,
campaign_id 854532, advertiser **CENTRUM (10115118)**, SMART_SHOPPING, **CPC**
bidding, status **PAUSED**, created 2026-06-05
**Window:** July 2026

Config: **exactly one positive keyword — "centrum" EXACT @ bid ₹330** ✓ matches the
ticket, plus 1,000 negatives. Sibling `HM_Apoll0_Manual_OstoCal_30_LS_Generic`
(1251585, ACTIVE) has 50 positives at ₹20–50 and correctly negatives out "centrum"
and 12 variants.

## The ticket's comparison table, identified

| Ticket row | What it actually is | Our July data |
|---|---|---|
| Centrum EXACT · ₹304.42 · ₹21,004.87 | Centrum's own brand-defence campaign 1251331 | ₹316.91 CPC · ₹38,029.75 |
| **Supradyn EXACT · ₹61.40 · ₹3,070.12** | **Centrum's own `HM_Apollo_Manual_MVM_30_Comp` (1251602) bidding on "supradyn"** | **₹61.36 CPC** · ₹3,620.16 · 59 clicks |
| **Revital EXACT · ₹64.70 · ₹2,134.96** | **Same Centrum campaign bidding on "revital"** | **₹65.00 CPC** · ₹3,509.94 · 54 clicks |
| Zincovit EXACT · ₹0.00 | Same campaign, no delivery | ₹0 |

**All four rows belong to Centrum.** None shows a competitor's bid on "Centrum".
The table compares brand-defence CPC against conquesting CPC — different auctions,
both theirs. It also compares realised average CPC (an outcome) against a bid (an input).

## What competitors actually pay on the query "centrum"

| Advertiser | Imp | Clicks | Spend | CTR | CPC | Auto vs Manual |
|---|---|---|---|---|---|---|
| **CENTRUM** | **6,710** | **304** | **51,550.85** | 4.53% | ₹169.58 | 2,903 auto / 3,807 manual |
| HEALTHKART | 3,548 | 36 | 2,480.00 | 1.01% | ₹68.89 | **100% auto** |
| Diataal | 1,893 | 13 | 495.00 | 0.69% | ₹38.08 | **100% auto** |
| VOGUE WELLNESS | 718 | 3 | 45.85 | 0.42% | ₹15.28 | **100% auto** |
| Supradyn | 675 | 17 | 679.73 | 2.52% | ₹39.98 | 462 auto / 213 manual |
| Neuherbs | 588 | 2 | 20.00 | 0.34% | ₹10.00 | **100% auto** |
| Revital | 30 | 1 | 11.06 | 3.33% | ₹11.06 | 10 auto / 20 manual |

Centrum holds **47.3% of impressions, 80.9% of clicks, 93.2% of spend**. Only four
external campaigns target "centrum" manually, on PHRASE/BROAD, at **₹11.01, ₹11.06,
₹15.00, ₹0** per click. **Nobody is outbidding Centrum.**

## Root cause — self-competition, starting July

Keyword "centrum" EXACT is targeted in **eight** Centrum campaigns:

| Campaign | Created | Status | Imp | Clicks | CPC |
|---|---|---|---|---|---|
| HM_Apollo_Manual_OstoCal_30_Brand | **2026-06-05** | PAUSED | 3,169 | 120 | ₹316.91 |
| HM_Apollo_Manual_MVM_Adult_50_Brand | **2026-07-06** | PAUSED | 25 | 1 | ₹135.00 |
| HM_Apollo_Manual_Omega_60_Brand | **2026-07-06** | PAUSED | 3 | 0 | — |
| HM_Apollo_Manual_Biotin_30_Brand | **2026-07-06** | PAUSED | 0 | 0 | — |
| HM_Apollo_Manual_J&M_10_Brand | **2026-07-06** | ACTIVE | 0 | 0 | — |
| HM_Apollo_Manual_CCM_15_Brand | **2026-07-06** | ACTIVE | 0 | 0 | — |
| HM_Apollo_Manual_MVM_Men_50_Brand | **2026-07-07** | ACTIVE | 453 | 57 | ₹153.60 |
| HM_Apollo_Manual_MVM_Women_50_Brand | **2026-07-13** | ACTIVE | 166 | 23 | ₹150.00 |
| **TOTAL** | | | **3,816** | **201** | **₹250.60** |

**Six new Brand campaigns created 6–13 July**, all bidding EXACT on "centrum",
immediately before the ticket. In a second-price auction the runner-up sets the
price; when the runner-up is your own sibling bidding ₹300+, you pay ₹300+. External
rivals bid ₹11–15, so without self-competition the clearing price would sit near the
floor. Dropping to ₹300 loses the slot to a sibling — **the placement is lost to
Centrum itself.** With one positive keyword, 1251331 has nothing to fall back on.

## Actions
1. Consolidate "centrum" to a single campaign; negative it out of the other seven.
2. Then reduce the bid gradually — external floor is ~₹15.
3. Add supporting keywords to OstoCal_30_Brand.
4. Confirm why the campaign is PAUSED (audit events unavailable).

---

# Ticket 5 — FC managed Service | Performance Improvement

**Marketplace:** firstcry-marketplace, agency 366, client 712346, INR
**Merchants:** Ashpveda (os_client_id **10090163**, merchant_id 1008782), CUGO
(os_client_id **10086223**, merchant_id 1009927)
**Windows:** before 25 May – 21 Jun; after 22 Jun – 26 Jul 2026
**Severity:** HIGH

> Window calibration: Ashpveda's before-period orders (14) and GMV (₹5,092) match the
> ticket exactly; CUGO's before ROAS (1.68 vs 1.62) matches. My after-window runs
> slightly wider, so absolute totals are higher but every ratio agrees.

## Ashpveda — PLA only

| Metric | Before | After | Δ |
|---|---|---|---|
| Spend | ₹15,043 | ₹28,952 | +92.4% |
| Impressions | 1,528,021 | 3,454,334 | +126.1% |
| Clicks | 3,849 | 4,507 | +17.1% |
| CTR | 0.25% | **0.13%** | −48% |
| CPC | ₹3.91 | **₹6.42** | **+64.4%** |
| Program viewproducts | 2,113 | 4,312 | +104.1% |
| Program add-to-carts | 169 | 331 | +95.9% |
| Program orders | 14 | 33 | +135.7% |
| Program GMV | ₹5,092 | ₹14,373 | +182.3% |
| **ROAS** | 0.339 | **0.496** | +46.6% |
| Attributed CVR | 0.663% | 0.765% | improved |
| Site CVR | 0.922% | 0.652% | declined |
| Click→order rate | 0.364% | **0.732%** | doubled |
| AOV | ₹363.71 | ₹435.55 | +19.8% |
| **Site revenue (all channels)** | ₹22,700 | **₹19,114** | **−15.8%** |

## CUGO — PLA and Display

| Metric | Before (PLA) | After (PLA) | After (**Display**) |
|---|---|---|---|
| Spend | ₹29,860 | ₹32,158 | **₹5,769** |
| Clicks | 3,021 | 2,760 | 47 |
| CPC | ₹9.88 | ₹11.65 | **₹122.74** |
| Program orders | 45 | 67 | **0** |
| Program GMV | ₹50,232 | ₹80,132 | **₹0** |
| **ROAS** | 1.68 | **2.49** | **0.00** |
| Site revenue | ₹78,846 | ₹136,784 | — |

**CUGO's PLA ROAS is 2.49 — inside the 2.5–5 target.** The reported 1.79 is a blend
dragged down by a Display campaign with zero conversions.

## Ashpveda SKU drill (after-period)

115 SKUs advertised for ₹28,952 returning ₹14,373 and 33 orders.
**97 of 115 SKUs (84%) produced zero orders, consuming ₹17,542 = 60.6% of spend and
2,792 clicks.** The 18 converting SKUs spent ₹11,410 for ₹14,373 — ROAS 1.26.

### Biggest wasters

| SKU | Product | Spend | Clicks | CPC | Orders | GMV | ROAS | % spend |
|---|---|---|---|---|---|---|---|---|
| 14325810 | Enriching Rose Petal Lip Balm 15g | ₹2,520 | 347 | ₹7.26 | 1 | ₹229 | **0.09** | 8.7% |
| 19322486 | Jasmine & Cocoa Butter Body Cream | ₹1,363 | 174 | ₹7.83 | 0 | ₹0 | 0.00 | 4.7% |
| 19322507 | Virgin Cold Pressed Almond Oil | ₹1,014 | 137 | ₹7.40 | 1 | ₹444 | 0.44 | 3.5% |
| 19322488 | Sandalwood & Turmeric Body Polish | ₹834 | 116 | ₹7.19 | 0 | ₹0 | 0.00 | 2.9% |
| 21064901 | Aloe Vera Sunscreen SPF50 | ₹792 | 105 | ₹7.54 | 1 | ₹439 | 0.55 | 2.7% |
| 19322516 | Shikakai & Bhringraj Anti Hair Fall | ₹716 | 123 | ₹5.82 | 0 | ₹0 | 0.00 | 2.5% |
| 19322487 | Jasmine & Cocoa Butter Body Cream | ₹697 | 92 | ₹7.57 | 0 | ₹0 | 0.00 | 2.4% |
| 19322506 | Organic Cold Pressed Virgin Coconut Oil | ₹661 | 85 | ₹7.77 | 0 | ₹0 | 0.00 | 2.3% |
| 21064902 | Coconut Milk Sunscreen SPF50 | ₹653 | 85 | ₹7.68 | 0 | ₹0 | 0.00 | 2.3% |

### Winners, starved of budget

| SKU | Product | Spend | Clicks | CPC | Orders | GMV | ROAS |
|---|---|---|---|---|---|---|---|
| 19322504 | Natural Hair Colour, Henna | ₹84 | 19 | ₹4.41 | 1 | ₹420 | **5.01** |
| 14325818 | Sensuous Jasmine & Mogra Soap 75g | ₹135 | 25 | ₹5.40 | 1 | ₹599 | **4.44** |
| 20665208 | Sandalwood & Saffron Night Cream | ₹643 | 108 | ₹5.96 | 4 | ₹2,248 | **3.49** |
| 20665216 | Hydrating Gulab Body Bar | ₹445 | 79 | ₹5.64 | 3 | ₹1,464 | **3.29** |
| 20665220 | Sandalwood & Turmeric Soap | ₹286 | 48 | ₹5.96 | 2 | ₹846 | **2.96** |
| 20665223 | Sandalwood & Saffron Soap Bar | ₹218 | 33 | ₹6.62 | 1 | ₹444 | **2.03** |
| | **Subtotal** | **₹1,811** | 312 | | 12 | **₹6,021** | **3.33** |

### By category

| Category | Spend | Orders | GMV | ROAS |
|---|---|---|---|---|
| Bathing Essentials > Bathing Soaps | ₹4,062 | 14 | ₹4,772 | 1.17 |
| Body care > Essential & Carrier Oils | ₹947 | 3 | ₹1,627 | **1.72** |
| Facial Care > Night Cream | ₹1,332 | 4 | ₹2,248 | **1.69** |
| Facial Care > Face Wash | ₹1,591 | 2 | ₹1,350 | 0.85 |
| Hair Care > Hair Oil | ₹2,913 | 3 | ₹1,321 | 0.45 |
| **Hair Care > Shampoo** | **₹3,501** | 2 | ₹846 | **0.24** |
| **Lip Care > Lip Balm** | **₹2,520** | 1 | ₹229 | **0.09** |
| **Sun Protection > For Face** | **₹2,510** | 1 | ₹439 | **0.17** |
| **Sun Protection > For Body** | **₹2,059** | **0** | **₹0** | **0.00** |

Those four loss-making categories took **₹10,590 (36.6% of spend) and returned
₹668 — blended ROAS 0.06.**

## Diagnosis

- **CUGO:** no ROAS problem. PLA at 2.49; ₹5,769 of Display spend produced nothing.
- **Ashpveda:** the optimisations worked — click-to-order doubled, AOV +20%,
  attributed CVR up. ROAS stayed low because CPC rose 64% while CTR halved, and
  because the budget target is mismatched to demand.

**The budget arithmetic:**
- Restricting to every SKU at ROAS ≥ 1.0 (perfect hindsight) → **ROAS 1.92**
- Restricting to SKUs at ROAS ≥ 2.0 → **ROAS 3.33, on only ₹1,811 over five weeks**
  (~₹1,550/month = 1.5% of the ₹100K budget)
- **Ashpveda's total site revenue across all channels was ₹19,114 against ₹28,952 of
  ad spend.** Ads already drive 75% of platform revenue. ROAS 2.5 on ₹100K/month
  needs ₹250,000/month of attributed GMV — ~15× the brand's entire demand on FirstCry.

**ROAS 2.5–5 and ₹100K monthly spend are mutually exclusive for this brand.**
The low ROAS and the low budget utilisation are the same problem: impressions rose
126% while CTR halved because the system reached less relevant inventory to place
budget. Pushing toward ₹100K lowers CTR further and raises CPC further.

## Actions
1. **CUGO:** pause the Display campaign; report CUGO on PLA separately. Treat as a success.
2. **Ashpveda immediate:** pause Sun Protection (both), Lip Balm, Shampoo — SKUs
   14325810, 21064901, 21064902, 19322516, 19322486, 19322487, 19322488, 19322506,
   19322507. Frees ~₹10,600 currently returning ₹668.
3. Concentrate on winners: 19322504, 14325818, 20665208, 20665216, 20665220, 20665223.
4. Bid down where CPC > ₹7 — Ashpveda pays most per click where it converts least.
5. **Reset the budget to demand:** run at ₹20–25K/month on the winning SKUs,
   expect ROAS 1.5–2.0. Growing to ₹100K requires growing demand (catalogue,
   listings, pricing, organic visibility), not more ad spend.

---

# Ticket 6 — FirstCry | New/Restarted Campaigns Spend Faster than Usual

**Marketplace:** firstcry-marketplace, agency 366, INR
**Campaign:** `Maternity Oct` (Nua) — marketing_campaign_id **919802**, campaign_id
651826, os_client_id **10069967**, SMART_SHOPPING / **AUTO_CPC**
**Date:** 22 July 2026

## Root cause: ACCELERATED budget delivery

| Campaign | ID | Delivery mode |
|---|---|---|
| Maternity Oct (Nua) | 919802 | **ACCELERATED** |
| Maternity (Nua, search) | 1019332 | **ACCELERATED** |

ACCELERATED instructs the system to spend the daily budget as fast as possible with
no pacing. ₹10k in 4 hours is the configured behaviour, not a defect. Per the pacing
SOP, an ACCELERATED campaign ends the investigation — the actual-vs-expected bucket
comparison applies only to STANDARD campaigns.

## Delivery-mode sweep — 120 of 1,666 active PERFORMANCE campaigns

Cohorts by `marketing_campaign_id` (increments with creation order — an age proxy).

| Cohort | ID range | Campaigns | **ACCELERATED** | STANDARD | % Accelerated |
|---|---|---|---|---|---|
| **Oldest** | 869,525 – 940,867 | 40 | **28** | 12 | **70.0%** |
| Middle | 1,146,059 – 1,151,567 | 40 | 25 | 15 | **62.5%** |
| **Newest** | 1,348,954 – 1,354,670 | 40 | **0** | **40** | **0.0%** |
| **Total** | | 120 | 53 | 67 | 44.2% |

**Every one of the 40 newest campaigns is STANDARD. Not one is ACCELERATED.**

**Maternity Oct (919802) is not a new campaign** — its ID falls inside the oldest
cohort, between 919720 and 920140. It was **restarted**, not created.

## Diagnosis

- The evidence **reverses** the client's hypothesis. If new campaigns were
  prioritised they would be the fast spenders; instead the newest cohort is 100%
  paced and the oldest is 70% unpaced.
- ACCELERATED prevalence falls monotonically with age (70% → 62.5% → 0%) — a
  default-setting change over time, not auction behaviour.
- The "restarted campaigns" symptom follows: restarted campaigns are by definition
  older, and older campaigns carry the legacy ACCELERATED setting. On wallet
  top-up they resume and immediately spend at maximum rate. No prioritisation
  mechanism is needed or exists — delivery mode is per campaign, not derived from age.

## Actions
1. Switch Maternity Oct and 1019332 to STANDARD delivery.
2. Account-hygiene review — ~70% of the oldest campaigns are still ACCELERATED and
   will behave the same way on any top-up.
3. ACCELERATED remains correct where burst spend is wanted — it should be a
   deliberate choice, not an inherited default.

## Could not verify
`check_budget_changes_on_date` is unavailable (audit events blocked), so the wallet
top-up timestamp could not be correlated with the spend burst. Campaign ages are
creation-order proxies, not exact dates. Sample covers active campaigns only.
The category traffic/competition comparison Shivam also asked for needs reports
outside the pacing SOP's tool whitelist and was not run.

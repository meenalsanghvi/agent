# Support ticket investigations — 2026-08-03

Ten marketplace ad-performance tickets worked through the `debug-*` SOP skills.
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
| 7 | #2026073189000536 — Apollo HOME page RR down | apollo-hospitals (434) | debug-rr | One placement (App Pharma CLP Skin Care) at ~2% fill; Skin Care budget-capped |
| 8 | #2026073189000689 — Category page highest requests, lowest RR | apollo-hospitals (434) | debug-rr | 92.2% of category requests arrive untagged; tagging defect, not a fill problem |
| 9 | Tira — BU improvement, RR improvement, category L2 fallback | tira (576) | debug-bu | BU 28%; constraint is eligible supply not budget; L2 fallback immaterial (0.5% of requests) |
| 10 | Mr D Food — CTR and CPC drop | mr-d (306) | debug-ctr | Impression expansion is the sole cause of the CTR/CPC fall; KFC burst ending = 59% of revenue loss only *(revised 04 Aug)* |

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
- **BigQuery access outage (ticket 7).** Mid-session, *every* report began failing
  with `Access Denied` on `reporting.marketplace_clients` and `reporting.agencies`
  — including `MARKETPLACE_DIRECTORY_REPORT`, which had worked earlier in the same
  session. The hosted `osmos-reporting-mcp` also returned `Access denied`. It
  cleared on retry a few minutes later. Transient, but it recurred as the second
  infra failure of the session and may repeat.
- **Filter type bug:** the shim wraps filter values in `LOWER()`, so filtering on
  an INT64 column fails with `No matching signature for function LOWER / Argument
  types: INT64`. Hit when filtering `perf_hour`. Workaround: omit the filter and
  slice client-side. Affects any integer attribute (`perf_hour`, `perf_day`).
- **`CAMPAIGNS_IN_CATEGORY_REPORT` unit inconsistency:** `perf_spend` runs ~1000×
  the `perf_campaign_group_daily_budget` column (e.g. Neutrogena — daily budget
  10,000, spend 4,480,896). Per-campaign BU cannot be computed from this report.
  Use `CATEGORY_QUADRANT_REPORT`, where spend and budget are consistent.
- **`TRUE_BU_CAMPAIGN_REPORT` budget semantics contradict the skill (ticket 9).**
  `debug-bu`'s terminology note says `daily_budget` is the **sum over the queried
  range**. In this report it is **one day's budget**: on Tira it summed to 2,664,012
  which ×14 days ≈ 37.3M, closely matching `perf_total_budget` (38.4M). Using
  `daily_budget` as the denominator gives a nonsensical BU of 403%. **Use
  `perf_total_budget`.** Also `perf_budget_utilization` is a **ratio, not a
  percentage** (report `1.07` = 107.4%) — it agrees exactly with
  `spend ÷ total_budget`, which confirms the correct denominator. Worth correcting
  in the skill's Key Concepts block.
- **Negative budget values** appear on PAUSED / DRAFT / ARCHIVED campaigns
  (e.g. −196, −85, −51). Small in absolute terms but they corrupt any naive
  aggregate; filter to ACTIVE or to `total_budget > 0`.

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

---

# Ticket 7 — #2026073189000536 | Why is Apollo home page RR down in last 2 days?

**Marketplace:** apollo-hospitals-marketplace, agency 434, client 10084549, INR,
Asia/Kolkata · **Program:** PLA · **Page:** HOME
**Raised:** 31/07/2026 05:46 by Sayali Vanjari · **Severity:** HIGH
**Period:** 28–31 Jul 2026 (baseline 15–27 Jul)

> Ticket article bodies came through empty (headers only); worked from the subject
> line. "Last 2 days" relative to the 31 Jul creation date = 29–30 Jul.
> **Solution-time SLA lapsed 03/08/2026 05:46.**

## Root cause

A single HOME placement — **`App Pharma CLP Skin Care`** — fell from 100% to ~2%
fill during afternoon/evening hours, driven by the Skin Care category reaching
**100% budget utilisation**. Every other HOME placement served at 100% throughout.

## Daily HOME series (PLA)

| Date | Requests | Responses | **RR** | Impressions | Clicks | Spend (INR) |
|---|---|---|---|---|---|---|
| 15–19 Jul | 515k–546k | = requests | **100.00%** | 33k–44k | 88–135 | 4,093–5,853 |
| 20 Jul | 541,059 | 518,032 | 95.74% | 39,110 | 94 | 4,267 |
| 21 Jul | 553,549 | 467,330 | **84.42%** | 34,240 | 123 | 6,478 |
| 22–26 Jul | 521k–662k | = requests | **100.00%** | 35k–57k | 89–123 | 5,134–7,886 |
| 27 Jul | 659,528 | 657,835 | 99.74% | 54,168 | 127 | 7,771 |
| **28 Jul** | 641,172 | 562,658 | **87.75%** | 54,715 | 126 | 7,922 |
| **29 Jul** | 630,567 | 489,707 | **77.66%** | 51,641 | 93 | 5,653 |
| **30 Jul** | 638,215 | 470,120 | **73.66%** | 49,523 | 101 | 6,337 |
| 31 Jul | 634,298 | 566,092 | 89.25% | 53,526 | 98 | 6,393 |
| 1 Aug | 722,656 | 714,886 | 98.92% | 52,962 | 110 | 6,223 |
| 2 Aug | 778,857 | 765,670 | 98.31% | 66,667 | 150 | 7,935 |

**Scenario C — requests stable, responses dropped.** Requests 659,528 (27 Jul) →
638,215 (30 Jul) = −3%; responses 657,835 → 470,120 = **−29%**. ~455,700 requests
unfilled across 28–31 Jul. A precursor dip occurred on 20–21 Jul (95.74%, 84.42%).

## Hourly pattern

| Day | Daily RR | Hours ~100% | **Hours ~60%** | Onset → end |
|---|---|---|---|---|
| 27 Jul | 99.74% | all (h20 96.79%) | none | — |
| 28 Jul | 87.75% | 00–18 | **19–23** | 19:00 → |
| 29 Jul | 77.66% | 02–14 | **00–01, 15–23** | 15:00 → |
| 30 Jul | 73.66% | 01–12 | **00, 13–23** | 13:00 → |
| 31 Jul | 89.25% | 02–12, **18–23** | **00–01, 13–17** | 13:00 → **17:00 (ended)** |

Affected hours pin to a hard floor between **58.67% and 62.14%** — never zero,
never noisy. Onset moved earlier each day, recovering ~01:00, then stopped after
31 Jul 17:00.

## Placement breakdown — 30 Jul (the finding)

`perf_page_name` resolves it; `perf_device` (always `"default"`), `perf_network`
(always `""`) and `perf_store_id` (always `""`) carry no segmentation on HOME.

| Hour | **App Pharma CLP Skin Care** | **Pharma Homepage Skin Care** | Health & Nutrition | VMS | Pharma Homepage | Daily Nutrition |
|---|---|---|---|---|---|---|
| 00 | **1.74%** (4,930 req) | **59.26%** | 100% | 100% | 100% | 100% |
| 01–12 | **100%** | **100%** | 100% | 100% | 100% | 100% |
| 13 | **31.12%** (14,087) | **65.64%** | 100% | 100% | 100% | 100% |
| 14 | **2.17%** (13,324) | **47.37%** | 100% | 100% | 100% | 100% |
| 15 | **1.89%** (12,606) | **44.65%** | 100% | 100% | 100% | 100% |
| 16 | **2.17%** (13,291) | **51.38%** | 100% | 100% | 100% | 100% |
| 17 | **2.51%** (14,162) | **39.81%** | 100% | 100% | 100% | 100% |
| 18 | **2.28%** (16,163) | **46.48%** | 100% | 100% | 100% | 100% |
| 19 | **2.53%** (23,048) | **54.26%** | 100% | 100% | 100% | 100% |
| 20 | **2.49%** (20,285) | **41.80%** | 100% | 100% | 100% | 100% |
| 21 | **2.76%** (19,236) | **56.64%** | 99.995% | 100% | 100% | 100% |
| 22 | **2.97%** (14,891) | **47.35%** | 100% | 100% | 100% | 100% |
| 23 | **2.00%** (9,165) | **56.00%** | 100% | 100% | 100% | 100% |

### Attribution is near-exact

| Source | Unfilled requests, 30 Jul |
|---|---|
| App Pharma CLP Skin Care | **166,932** |
| Pharma Homepage Skin Care | 1,143 |
| **Sum** | **168,075** |
| **HOME total unfilled (638,215 − 470,120)** | **168,095** |
| **Share explained** | **99.99%** |

This also explains the hard ~60% floor: one placement carrying ~40% of volume went
to near-zero while the remaining 60% served perfectly. At hour 15 — 30,214 requests,
12,606 of them Skin Care at 1.89%, remainder at 100% → 58.77% observed.

## Supply cause — category quadrant, 28 Jul – 2 Aug

> 6-day window, inside the report's 7-day retention limit.

| Category | Requests | RR | Spend (INR) | Daily budget (INR) | **BU%** | Campaigns | Merchants |
|---|---|---|---|---|---|---|---|
| **personal care > skin care** | 1,019,539 | 100% | **147,463.60** | **147,463.60** | **100.00%** | 40 | 9 |
| ↳ face care | 726,482 | 100% | 121,813.61 | 121,813.61 | **100.00%** | 34 | 9 |
| ↳ body care | 239,251 | 100% | 25,099.40 | 25,099.40 | **100.00%** | 11 | 5 |
| ↳ **hand & feet care** | 34,051 | **0.97%** | 0 | 0 | 0% | **0** | **0** |
| ↳ **lip care** | 14,468 | **0.69%** | 0 | 0 | 0% | **0** | **0** |

Skin Care spent **exactly** its available budget. All 40 campaigns across 9
merchants (Neutrogena, Bepanthen, CeraVe, La Roche-Posay, Nivea, Aveeno, Rivela,
Excela, NUA) are **ACTIVE** — no pauses, so this is exhaustion, not a status change.
The daily rhythm matches: serve at 100% each morning, exhaust mid-afternoon, stay
down through evening peak, reset after midnight, exhausting earlier as traffic grows.

## Recommendations
1. **Raise Skin Care daily budgets** — the category lands exactly on its cap.
2. **Add supply to hand & feet care and lip care** — zero campaigns against ~48,500 requests.
3. **Add placement-level RR monitoring** — a placement at 2% fill was invisible in
   the page aggregate, which showed only a ~60% floor.
4. **Confirm what changed on 31 Jul ~17:00** that ended the pattern; make it permanent.

## Caveats
- The budget-exhaustion cause is **strongly evidenced, not conclusively proven**.
  The quadrant reports Skin Care category RR as 100%, which could not be reconciled
  against the placement-level 2% — most likely because category RR covers only
  category-attributed requests. Backend confirmation recommended before closure.
- `CAMPAIGNS_IN_CATEGORY_REPORT` unit inconsistency (see limitations section) meant
  per-campaign BU could not be computed; that report was used only for the roster
  and statuses.
- Display was **not examined**. PLA matched the reported symptom precisely, so scope
  was set to PLA; Display was not ruled out by evidence.
- Placement-level cuts were run for **30 Jul only**; 28, 29 and 31 Jul were not
  broken down by placement.

---

# Ticket 8 — #2026073189000689 | Category page highest requests but lowest RR

**Marketplace:** apollo-hospitals-marketplace, agency 434, client 10084549, INR ·
**Program:** PLA · **Page:** CATEGORY
**Raised:** 31/07/2026 06:54 by Sayali Vanjari · **Severity:** HIGH
**Period:** 25 Jul – 2 Aug 2026 (single period — structural state, not a change)

> Ticket carried **no Client List and no CustomerID**, and the article body was empty
> (headers only). Proceeded on Apollo based on the same reporter, queue and timing as
> ticket 7 (raised ~1 hour apart), and the data matches the reported symptom exactly.
> **Solution-time SLA lapsed 03/08/2026 06:54.**

## Root cause

The 1.36% category-page RR is **not a fill problem — it is a request-tagging problem.**
92.2% of category-page requests arrive with no `page_name` and no `category_l1`, so
nothing can be matched to them. Correctly tagged category pages fill at **~55.6%**,
better than SEARCH, PRODUCT or TPA.

## Page-type comparison

| Page type | Requests | Share | Responses | **RR** | Impressions | Clicks | Spend (INR) |
|---|---|---|---|---|---|---|---|
| **CATEGORY** | **27,546,810** | **41.6%** | 374,687 | **1.36%** | 110,052 | 1,590 | 79,393 |
| TPA | 17,881,703 | 27.0% | 4,715,449 | 26.37% | 417,344 | 8,916 | 373,668 |
| SEARCH | 10,697,742 | 16.1% | 1,684,533 | 15.75% | 1,318,341 | 25,284 | 1,137,619 |
| HOME | 6,017,623 | 9.1% | 5,539,256 | 92.05%* | 492,591 | 1,037 | 63,097 |
| PRODUCT | 2,420,378 | 3.7% | 807,629 | 33.37% | 743,704 | 6,407 | 282,602 |
| CUSTOM | 1,733,277 | 2.6% | 1,729,197 | 99.76% | 918,676 | 2,869 | 273,253 |
| **Total** | **66,297,533** | 100% | 14,850,751 | 22.40% | 4,000,708 | 46,103 | 2,209,632 |

\* depressed by the 28–31 Jul Skin Care outage (ticket 7); normally ~100%.

CATEGORY = **41.6% of requests, 2.5% of responses, 3.6% of spend.**

## Category L1 decomposition (rows sum exactly to the page total)

| Category L1 | Requests | Share | Responses | **RR** |
|---|---|---|---|---|
| **`""` (untagged)** | **25,470,691** | **92.46%** | **0** | **0.00%** |
| FOOD & BEVERAGES | 1,165,912 | 4.23% | 95 | **0.008%** |
| PERSONAL CARE | 568,765 | 2.06% | 188,206 | 33.09% |
| HEALTH & NUTRITION | 188,583 | 0.68% | 168,386 | 89.29% |
| BABY CARE | 79,063 | 0.29% | 15,028 | 19.01% |
| AYURVEDA | 63,803 | 0.23% | 0 | **0.00%** |
| OTC | 6,826 | 0.02% | 2,972 | 43.54% |
| HEALTH DEVICES | 3,167 | 0.01% | 0 | **0.00%** |
| **Total** | **27,546,810** | 100% | 374,687 | 1.36% |

Excluding the untagged slice: 2,076,119 requests → 374,687 responses = **18.05% RR**.

## Localisation by page_name × category_l1

**The dominant row:**

| page_name | category_l1 | Requests | Responses | RR |
|---|---|---|---|---|
| **`""` (blank)** | **`""` (blank)** | **25,412,159** | **0** | **0.00%** |

25,412,159 = 92.2% of category requests and **38.3% of Apollo's entire ad request
volume**. Direct evidence of a tagging defect: the literal string
**`{{parent.page_name}}`** appears as a page_name on 75 requests — an unrendered
template variable leaking into the ad call.

**Named pages that fill normally — the system works when tagged:**

| page_name | Category | Requests | Responses | RR |
|---|---|---|---|---|
| PPLA Supplements tabular widget | HEALTH & NUTRITION | 97,428 | 96,082 | **98.62%** |
| App Pharma CLP Fever Cold | OTC | 2,973 | 2,972 | **99.97%** |
| App Category Landing Page | PERSONAL CARE | 7,823 | 7,776 | **99.40%** |
| App Pharma CLP Baby Feeding | BABY CARE | 3,600 | 3,591 | **99.75%** |
| PPLA women nutrition app homepage recursive women | HEALTH & NUTRITION | 9,772 | 9,663 | **98.88%** |
| App Pharma CLP Vitamin Minerals / Nutritional Drinks / Women Care | mixed | 12,065 | 12,065 | **100%** |
| PPLA VMS clp essential vitamins tabular widget | HEALTH & NUTRITION | 8,304 | 7,595 | **91.46%** |
| PPLA Haircare clp tab widget | PERSONAL CARE | 23,943 | 17,097 | **71.41%** |

**Named pages with genuine zero supply (~1.46M requests):**

| page_name | Category | Requests | Responses | RR |
|---|---|---|---|---|
| **PPLA Healthy Snacks tabular widget** | FOOD & BEVERAGES | **1,065,958** | 89 | **0.008%** |
| PPLA Healthy India Nutrition tabular widget | FOOD & BEVERAGES | 92,782 | 0 | 0% |
| PPLA Support performance tabular widget | AYURVEDA | 63,570 | 0 | 0% |
| PPLA Summer Essentials app home page recursive summer | *(blank)* | 58,532 | 0 | 0% |
| PPLA sexual wellness app homepage recursive sexual health | PERSONAL CARE | 47,368 | 0 | 0% |
| PPLA baby diaper clp tab widget | BABY CARE | 35,321 | 98 | 0.28% |
| App Pharma CLP Sexual Wellness | PERSONAL CARE | 22,571 | 0 | 0% |
| PPLA mens grooming app homepage recurisve men | PERSONAL CARE | 21,774 | 0 | 0% |
| PPLA mens sexual wellness app homepage recursive mens | PERSONAL CARE | 18,973 | 0 | 0% |
| PPLA Baby wipes Static Tab Widget | BABY CARE | 14,060 | 0 | 0% |
| App Pharma CLP Health Devices | HEALTH DEVICES | 3,070 | 0 | 0% |
| *(others below 8k)* | mixed | 16,962 | 1 | ~0% |

## Three causes, in descending size

1. **Untagged requests — 25.41M (92.2%).** No page_name, no category. Instrumentation
   gap on Apollo's category pages, corroborated by the `{{parent.page_name}}` leak.
2. **Zero-supply named surfaces — ~1.46M (5.3%).** `PPLA Healthy Snacks tabular
   widget` alone (1,065,958 requests → 89 responses) is the entire FOOD & BEVERAGES gap.
3. **Sexual-wellness cluster at exactly 0%** across three page names (88,912 requests)
   — likely eligibility or advertiser policy rather than supply.

**Properly tagged, properly supplied category pages fill at ~55.6%** (673,710 requests
→ 374,499 responses). 97.5% of category requests are either untagged or pointed at
empty inventory.

## Recommendations
1. **Route the tagging gap to the integration team** — 25.4M requests in 9 days with no
   page or category identifier. Largest monetisation opportunity on Apollo. The
   `{{parent.page_name}}` placeholder is a concrete starting point.
2. **Recruit supply for PPLA Healthy Snacks / Healthy India Nutrition** (Food & Beverages).
3. **Confirm whether sexual wellness surfaces are intentionally restricted.**
4. **Audit surfaces still on retired taxonomy labels** — `App Pharma CLP Health Devices`
   uses "Health Devices", replaced by "Medical Equipments & Devices" in the June
   re-categorisation (cross-ref ticket 2), and fills at 0% as a result.
5. **Do not treat this as a category-page performance problem.**

**Sizing:** untagged requests filled at the observed attributed rate would be roughly
**4.6M additional responses** on Apollo's highest-volume surface.

## Caveats
- Marketplace was **inferred**, not stated — see the note under the heading.
- Display was **not examined**; PLA matches the symptom.
- Supply/campaign data was **not run** for the zero-fill widgets, so "no supply" is
  observed at the response level rather than confirmed against campaign counts.
- The untagged requests were **not** broken down by store_id, device or hour, which
  might have pinpointed a specific app build for the integration team.
- Structural, not a regression: June data showed the same shape (63.7M requests at
  2.04% RR).

---

# Ticket 9 — Tira | BU Improvement

**Marketplace:** tira-marketplace, agency 576, client 10119611, INR, Asia/Kolkata ·
**Programs:** PLA + Display · **Severity:** MEDIUM
**Raised by:** internal (to Mayur, following discussion with Harshita) — advisory, not a regression
**Period:** 20 Jul – 2 Aug 2026 (14 days; no dates given in the ticket)

**Three asks:** (a) how to improve BU, (b) how to improve response rate,
(c) is category L2 fallback enabled for PLA, and what would enabling it do.

## Root cause

**Eligible advertiser supply is too narrow to cover available demand.** Budget and
wallets are healthy; campaigns cannot match enough traffic to spend what they hold.
The low BU and the low RR are the same problem seen from opposite ends.

## Budget utilisation

> **Budget-field caveat:** `perf_daily_budget` here is **one day's** budget, not the
> period sum the skill warns about (2,664,012 × 14 ≈ 37.3M ≈ `total_budget` 38.4M).
> All figures use `perf_total_budget`. Cross-checked against the report's own
> `perf_budget_utilization`, which is a ratio not a percentage. See limitations section.

| | INR |
|---|---|
| Total budget (14 days) | **38,413,719** |
| Spend | **10,758,635** |
| **Budget Utilisation** | **28.01%** |
| **Unspent** | **27,655,084** |

Budget is **3.6× spend**. Per the skill's thresholds this is the "low (5–30%)" band.
**Only 1 campaign of 1,876 has a wallet balance ≤ 0** — wallets are not the constraint.

### Where unspent budget sits (ACTIVE campaigns, denominator = total_budget)

| BU band | Campaigns | Budget | % of budget | Unspent |
|---|---|---|---|---|
| **0–1%** | 63 | 5,838,383 | 15.2% | 5,810,546 |
| **1–5%** | 75 | 9,235,243 | 24.1% | 8,987,616 |
| **5–30%** | 175 | 15,342,063 | **40.1%** | 13,118,186 |
| 30–60% | 92 | 2,512,232 | 6.6% | 1,445,587 |
| 60–90% | 91 | 2,371,356 | 6.2% | 515,293 |
| 90%+ | 159 | 2,987,823 | 7.8% | −45,064 |

**79.4% of active budget is in campaigns spending under 30%; 39.3% under 5%.**

### Merchant concentration — top 15 hold 88.7% of unspent budget

| Merchant | Campaigns | Budget | Spend | Unspent | **BU%** | Wallet |
|---|---|---|---|---|---|---|
| **Lakme (566)** | 46 | **17,477,523** | 1,418,303 | **16,059,220** | **8.1%** | 1,811,439 |
| L'Oreal Paris (27) | 62 | 4,455,921 | 854,788 | 3,601,133 | 19.2% | 2,351,334 |
| Dove (558) | 12 | 1,795,078 | 142,363 | 1,652,715 | 7.9% | 610,247 |
| Hyue Beauty (1328) | 31 | 941,800 | 169,870 | 771,930 | 18.0% | 1,196,244 |
| SKIN1004 (1121) | 2 | 749,759 | 16,128 | 733,632 | **2.2%** | 85,197 |
| KERASTASE (1329) | 1 | 644,000 | 68,006 | 575,994 | 10.6% | 1,350,919 |
| Bioderma (666) | 7 | 692,000 | 194,739 | 497,261 | 28.1% | 273,162 |
| Foxtale (1109) | 15 | 670,000 | 179,722 | 490,278 | 26.8% | 642,867 |
| Nivea (203) | 18 | 506,000 | 25,137 | 480,863 | **5.0%** | 107,306 |
| Moxie (1303) | 8 | 560,000 | 213,152 | 346,848 | 38.1% | 403,871 |

**Lakme alone = 45.5% of all active budget and 54% of all unspent budget.**

## The PLA funnel

| Page | Requests | Responses | **RR** | Impressions | I/R | Clicks | CTR | Spend | CPC |
|---|---|---|---|---|---|---|---|---|---|
| SEARCH | 6,320,942 | 4,535,876 | **71.76%** | 10,616,075 | 234% | 157,888 | 1.49% | 5,502,645 | 34.85 |
| CUSTOM | 7,419,708 | 4,251,067 | **57.29%** | 4,758,459 | 112% | 61,705 | 1.30% | 2,545,684 | 41.26 |
| **Total** | **13,740,650** | **8,786,943** | **63.95%** | 15,374,534 | | 219,593 | 1.43% | 8,048,328 | |

**Tira PLA serves on two page types only — SEARCH and CUSTOM. No CATEGORY, HOME or
PRODUCT page exists.** I/R above 100% is normal for PLA (one response fills multiple
SKU slots).

## Programs

| Channel | Spend | Impressions | Clicks | CTR | CPC | GMV | **ROAS** |
|---|---|---|---|---|---|---|---|
| PLA (`os_product_ads`) | 8,136,493 | 15,374,534 | 219,593 | 1.43% | 37.05 | 27,087,430 | **3.33** |
| Guaranteed Display | 2,597,600 | 2,364,218 | 45,369 | 1.92% | 57.26 | 2,037,811 | **0.78** |
| Auction Display | 24,542 | 35,935 | 81 | 0.23% | 302.98 | 153,197 | 6.24 |

## Category attribution and the L2 fallback question

| Category L1 | Requests | Share | Responses | RR |
|---|---|---|---|---|
| **`""` (no category)** | **13,672,313** | **99.50%** | 8,751,479 | **64.01%** |
| MAKEUP | 34,444 | 0.25% | 18,544 | 53.84% |
| SKIN | 11,554 | 0.08% | 7,101 | 61.46% |
| HAIR | 8,092 | 0.06% | 4,893 | 60.47% |
| FRAGRANCE | 5,344 | 0.04% | 1,829 | 34.23% |
| BATH & BODY | 3,621 | 0.03% | 1,900 | 52.47% |
| MEN | 3,598 | 0.03% | 552 | **15.34%** |
| TOOLS & APPLIANCES | 1,452 | 0.01% | 641 | 44.15% |
| MOM & BABY | 161 | — | 3 | **1.86%** |
| WELLNESS | 59 | — | 0 | **0.00%** |
| TIRA MERCH | 12 | — | 1 | 8.33% |

**Unlike Apollo (ticket 8), blank category here is benign** — these are keyword-driven
SEARCH/CUSTOM requests, not expected to carry a category, and they fill at 64%. All
7,419,708 CUSTOM requests are uncategorised; every categorised request comes from SEARCH.

### Empirical read on fallback

Sub-categories with no own supply return **zero** fill even when a sibling under the
same parent fills well:

| L1 (parent RR) | L2 | Requests | Responses | RR |
|---|---|---|---|---|
| **BATH & BODY** (52.47%) | BATH & SHOWER | 3,036 | 1,800 | **59.29%** |
| | HANDS & FEET | 323 | 82 | 25.39% |
| | BODY CARE | 155 | 18 | 11.61% |
| | SHAVING & HAIR REMOVAL | 63 | 0 | **0%** |
| | BATHING ACCESSORIES | 33 | 0 | **0%** |
| | FEMININE HYGIENE | 7 | 0 | **0%** |
| | ORAL CARE | 4 | 0 | **0%** |
| **MEN** (15.34%) | SKINCARE | 3,178 | 549 | 17.28% |
| | SHAVING | 254 | 0 | **0%** |
| | BATH AND BODY | 89 | 0 | **0%** |
| | MENS FRAGRANCE | 36 | 1 | 2.78% |
| | BEARD CARE | 26 | 0 | **0%** |

Consistent with **no upward category fallback**. ⚠️ This is inference from L2-vs-L1
behaviour, **not proof**, and not the L3-to-L2 path as asked. **No report exposes
platform config flags** — the actual setting must come from the relevancy team.

### Sizing — this is the decisive point

Categorised requests = **68,337 of 13,740,650 = 0.50%**, currently returning 35,464.

| Scenario | Additional responses | Marketplace RR |
|---|---|---|
| Today | — | 63.95% |
| Every categorised request filled at 100% (ceiling for L2 fallback) | +32,873 | 64.19% (**+0.24pp**) |
| CUSTOM lifted to SEARCH's 71.98% | +1,089,955 | 71.88% (**+7.93pp**) |

**Closing the CUSTOM gap is worth ~33× more than a perfect fallback outcome.**

## CUSTOM drill — supply saturation

**CUSTOM carries no dimensional attribution:** `page_name` = literal `"CUSTOM"`,
`device` = `"default"`, `network` and `store_id` blank, across all 7.42M requests.
Tira's largest PLA surface cannot be segmented in reporting. Only `hour` is populated.

### RR by hour (27 Jul – 2 Aug) — fill falls as volume rises

| Hour | Requests | RR | | Hour | Requests | RR |
|---|---|---|---|---|---|---|
| 04 | 36,585 | 54.92% | | 12 | 217,945 | 47.58% |
| 05 | 38,766 | 58.83% | | 13 | 202,058 | 49.51% |
| **06** | **53,093** | **60.77%** | | 14 | 214,440 | 52.08% |
| 03 | 56,803 | 57.58% | | 15 | 228,820 | 49.27% |
| 07 | 69,408 | 57.61% | | 16 | 205,033 | 48.56% |
| 08 | 93,584 | 55.89% | | 17 | 215,146 | 47.54% |
| 09 | 126,255 | 55.79% | | 18 | 206,451 | 51.97% |
| 10 | 149,778 | 52.99% | | 19 | 215,957 | 48.02% |
| 11 | 181,911 | 53.01% | | 20 | 207,365 | 48.92% |
| 00 | 186,269 | 49.49% | | **21** | **218,682** | **41.45%** |
| 01 | 135,456 | 50.94% | | 22 | 224,216 | 45.97% |
| 02 | 91,838 | 53.44% | | 23 | 220,672 | 46.05% |

Low-volume hours (36k–69k) fill at **55–61%**; peak hours (200k–229k) at **41–52%**.
4.1× the volume → 19pp worse fill. Signature of **supply saturation**, not a hard cutoff.

### ⚠️ CUSTOM RR is actively declining

| Week | Requests | Responses | **RR** |
|---|---|---|---|
| 20–26 Jul | 3,623,177 | 2,356,640 | **65.04%** |
| 27 Jul – 2 Aug | 3,796,531 | 1,894,427 | **49.90%** |
| **Change** | +4.8% | **−19.6%** | **−15.14pp** |

**Undiagnosed.** A 15pp fall in one week while requests rose — recent deterioration on
top of the structural ceiling. Needs its own investigation.

## Recommendations
1. **Audit Lakme's 46 campaigns** — INR 17.5M budget at 8.1% BU, wallet full. Targeting
   breadth / product selection, not money. Largest single BU lever on the marketplace.
2. **Review the 138 campaigns holding INR 15.07M that spend under 5%** — broaden
   targeting or right-size budgets.
3. **Widen eligible supply on CUSTOM** — raises fill *and* lets existing budget spend.
   Closing to the best observed hourly rate ≈ **+412,500 responses/week**.
4. **Raise the 15pp CUSTOM decline as its own ticket** — urgent, undiagnosed.
5. **Do not prioritise L2 fallback on BU/RR grounds** — 0.5% of requests, +0.24pp
   ceiling. Harmless to enable if low-effort; may matter if Tira launches category pages.
6. **Review Guaranteed Display** — INR 2.60M at ROAS 0.78 vs PLA's 3.33.
7. **Add reporting attribution to CUSTOM** — no page/device/network/store dimension
   exists on Tira's largest surface, which blocks diagnosis.

## Caveats
- Advisory ticket with **no dates specified**; 14-day window chosen.
- **Config flags are not readable** from any available report — the fallback answer is
  behavioural inference plus sizing, not a config confirmation.
- The **15pp CUSTOM decline was not diagnosed**.
- **Not run:** Lakme campaign-level audit, category L3 drill, Display ROAS drill.

---

# Ticket 10 — Mr D Food | Drop in CTR and CPC

**Marketplace:** mr-d-marketplace, agency 306, client 384653, **ZAR**, Africa/Johannesburg ·
**Program:** PLA · **Severity:** HIGH
**Period:** baseline 15–19 Jul vs current 29 Jul – 2 Aug 2026
**Scenario:** Mixed — impressions +70.2% (A) **and** clicks −46.0% (B). Neither label alone fits.

> **Scope note:** "mrd food" read as this marketplace (Mr D Food), not a Food category —
> a separate `mr-d-grocery-marketplace` exists on agency 572. Rescope if that was wrong.

## Root cause

> ⚠️ **REVISED 2026-08-04** after a 30-day non-KFC-only trend was run (see the
> follow-up section below). The original conclusion attributed part of the CTR fall to
> KFC; the direct non-KFC series disproves that. Superseded figures are marked.

**A marketplace-wide impression expansion is the sole cause of the CTR and CPC decline.**
Non-KFC impressions **doubled** while non-KFC clicks fell 17% — the full rate collapse is
present with KFC excluded entirely.

**The KFC campaign ending is a separate, coincident event.** It accounts for ~59% of the
absolute revenue loss but **essentially none of the CTR/CPC decline**.

~~Original: "two independent events compounding; KFC = 57% of spend loss and ~24% of the
CTR fall."~~ The spend split roughly holds; the CTR attribution does not.

## Timing — the decline is NOT recent

Ran **20–26 July** as a six-day glide, then stable for eight days. The ticket's
"last few days" framing is ~2 weeks off.

| Date | Requests | RR | Impressions | Clicks | Spend (ZAR) | **CTR** | **CPC** |
|---|---|---|---|---|---|---|---|
| 15 Jul | 1,218,210 | 62.86% | 33,173 | 5,623 | 30,590.80 | **16.95%** | **5.44** |
| 16 Jul | 1,201,038 | 62.51% | 33,947 | 5,594 | 29,876.93 | 16.48% | 5.34 |
| 17 Jul | 1,453,000 | 64.55% | 44,680 | 6,968 | 34,827.89 | 15.60% | 5.00 |
| 18 Jul | 1,265,056 | 65.34% | 39,066 | 6,163 | 29,009.71 | 15.78% | 4.71 |
| 19 Jul | 1,124,545 | 62.05% | 30,951 | 4,873 | 22,384.11 | 15.74% | 4.59 |
| 20 Jul | 978,596 | 63.79% | 28,257 | 3,754 | 18,500.17 | 13.29% | 4.93 |
| 21 Jul | 918,044 | 64.31% | 30,435 | 3,585 | 16,723.12 | 11.78% | 4.66 |
| 22 Jul | 935,332 | 64.81% | 31,904 | 3,225 | 13,339.86 | 10.11% | 4.14 |
| 23 Jul | 1,132,906 | 66.97% | 43,773 | 3,330 | 9,844.69 | 7.61% | 2.96 |
| 24 Jul | 1,978,339 | 67.96% | 74,719 | 4,415 | 11,481.97 | 5.91% | 2.60 |
| 25 Jul | 1,787,221 | 67.63% | 63,462 | 3,514 | 9,051.46 | 5.54% | 2.58 |
| 26 Jul | 1,392,150 | 67.17% | 46,466 | 2,747 | 6,749.71 | 5.91% | 2.46 |
| 27 Jul | 1,253,621 | 71.78% | 45,347 | 2,410 | 6,484.66 | 5.31% | 2.69 |
| 28 Jul | 1,392,003 | 70.83% | 51,411 | 2,671 | 6,754.52 | 5.20% | 2.53 |
| 29 Jul | 1,292,805 | 72.81% | 57,156 | 3,080 | 8,133.85 | 5.39% | 2.64 |
| 30 Jul | 1,341,431 | 74.41% | 59,736 | 3,127 | 8,354.92 | 5.23% | 2.67 |
| 31 Jul | 1,994,518 | 72.37% | 85,136 | 3,914 | 9,425.43 | **4.60%** | 2.41 |
| 1 Aug | 1,760,946 | 71.85% | 62,225 | 3,183 | 8,458.87 | 5.11% | 2.66 |
| 2 Aug | 1,384,035 | 69.20% | 45,252 | 2,466 | 6,262.60 | 5.45% | 2.54 |

## Decomposition

| Metric | Baseline (15–19 Jul) | Current (29 Jul–2 Aug) | Change |
|---|---|---|---|
| Requests | 6,261,849 | 7,773,735 | +24.1% |
| Responses | 3,978,792 | 5,605,763 | **+40.9%** |
| Response Rate | 63.54% | 72.11% | **+8.57pp** |
| **Impressions** | 181,817 | 309,505 | **+70.2%** |
| **Clicks** | 29,221 | 15,770 | **−46.0%** |
| **Spend (ZAR)** | 146,689 | 40,636 | **−72.3%** |
| **CTR** | **16.07%** | **5.10%** | **−68.3%** |
| **CPC (ZAR)** | **5.02** | **2.58** | **−48.7%** |
| I/R | 4.57% | 5.52% | +20.8% |

**Impression-driven gate: PASSED** — I/R rose 4.57% → 5.52%, so impressions are genuine
renders, not a rendering artefact. Proceeding was appropriate.

**Commercial impact: ad revenue −72.3%** = ZAR ~21,200/day ≈ **ZAR 640,000/month**.

## Page types

**Mr D PLA runs on ONE page type — HOME.** No page-mix shift is possible; the entire
change is within it.

| Page | Baseline CTR | Current CTR | CTR Δ | Impressions Δ | Clicks Δ | I/R |
|---|---|---|---|---|---|---|
| HOME (only) | 16.07% | 5.10% | −68.3% | +70.2% | −46.0% | 4.57% → 5.52% |

## Merchant cohorts

| Cohort | Merchants | Baseline spend | Current spend | Baseline impr | Current impr | Baseline clicks | Current clicks | Baseline CTR | Current CTR | Baseline CPC | Current CPC |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **KFC stores** | 22 → 4 | **61,542** | **1,080** | 22,372 | 2,179 | 10,164 | 440 | **45.43%** | 20.19% | 6.05 | 2.45 |
| **Non-KFC** | 335 → 391 | 85,147 | 39,559 | 159,445 | 307,326 | 19,057 | 15,331 | 11.95% | **4.99%** | 4.47 | 2.58 |
| **Churned** | 99 | 83,001 | — | 66,086 | — | 15,264 | — | **23.10%** | — | 5.44 | — |
| ↳ of which KFC | 19 | 59,514 | — | 21,648 | — | 9,841 | — | **45.46%** | — | 6.05 | — |
| ↳ of which non-KFC | 80 | 23,487 | — | 44,438 | — | 5,423 | — | 12.20% | — | 4.33 | — |
| **New** | 137 | — | 19,478 | — | 122,249 | — | 7,388 | — | **6.04%** | — | 2.64 |
| **Active both** | 258 | 63,689 | 21,161 | 115,731 | 187,256 | 13,957 | 8,383 | 12.06% | **4.48%** | 4.56 | 2.52 |

**KFC were the marketplace's most efficient advertisers: 42.0% of spend and 34.8% of
clicks from 12.3% of impressions, at 45.43% CTR.** The fifteen highest-spending
baseline advertisers were **all** KFC outlets; every one churned.

**Textbook dilution on both sides** (baseline avg CTR threshold 16.07%): 99 merchants
churned at **23.10%** (above average); 137 new merchants arrived at **6.04%** (below).

### Attribution — superseded, see follow-up below

~~| Metric | KFC departure | Everything else |~~
~~| **Spend** (−ZAR 106,053) | −60,462 (57%) | −45,588 (43%) |~~
~~| **CTR** (−10.97pp) | ~2.63pp (24%) | ~8.34pp (76%) |~~

The CTR row was a **mix-effect estimate** and is wrong. The direct non-KFC series
(follow-up section) shows the rate decline is **fully present** with KFC removed.

Even in these 5-day windows the signal was there: excluding KFC, non-KFC showed
impressions **+92.7%**, clicks −19.6%, CTR 11.95% → 4.99%, CPC 4.47 → 2.58; merchants
active in both periods showed CTR 12.06% → 4.48%.

---

## FOLLOW-UP (2026-08-04) — 30-day non-KFC-only trend

**Question posed:** exclude KFC stores and check the remaining merchants over 30 days,
to confirm whether KFC's exit is the only reason.
**Answer: no. KFC is not the reason for the CTR/CPC decline.**

**Method:** PLA daily totals (`PAGE_PERFORMANCE_PLA_REPORT`) minus KFC daily
(`INTERNAL_CAMPAIGN_PERFORMANCE_REPORT`, `perf_merchant_name LIKE %KFC%`,
`perf_campaign_type = PERFORMANCE`). **Reconciliation exact** — KFC from the campaign
report matched the merchant report to the rupee in both windows
(22,372 / 10,164 / 61,542 and 2,179 / 440 / 1,080).

### Non-KFC only, daily

| Date | Impr | Clicks | **CTR** | **CPC** | Spend | KFC stores live |
|---|---|---|---|---|---|---|
| 05 Jul | 24,820 | 3,257 | 13.12% | 4.47 | 14,545 | 2 |
| 06 Jul | 25,751 | 3,452 | 13.41% | 5.02 | 17,317 | 3 |
| 07 Jul | 30,019 | 3,764 | 12.54% | 4.92 | 18,513 | 2 |
| 08 Jul | 32,339 | 7,179 | 22.20% | 5.79 | 41,567 | **22** |
| 09 Jul | 33,300 | 8,447 | 25.37% | 6.03 | 50,922 | 21 |
| 10 Jul | 41,129 | 6,983 | 16.98% | 5.50 | 38,380 | 21 |
| 11 Jul | 30,771 | 4,307 | 14.00% | 5.08 | 21,889 | 22 |
| 12 Jul | 24,597 | 3,029 | 12.31% | 4.69 | 14,209 | 21 |
| 13 Jul | 20,162 | 2,658 | 13.18% | 5.10 | 13,561 | 21 |
| 14 Jul | 25,185 | 3,243 | 12.88% | 5.03 | 16,314 | 22 |
| 15 Jul | 28,416 | 3,457 | 12.17% | 4.90 | 16,942 | 21 |
| 16 Jul | 29,569 | 3,565 | 12.06% | 4.77 | 16,996 | 21 |
| 17 Jul | 39,452 | 4,546 | 11.52% | 4.53 | 20,572 | 22 |
| 18 Jul | 34,640 | 4,146 | 11.97% | 4.08 | 16,923 | 21 |
| 19 Jul | 27,368 | 3,343 | 12.21% | 4.10 | 13,714 | 22 |
| **20 Jul** | 26,740 | 3,091 | **11.56%** | 4.76 | 14,723 | 14 |
| **21 Jul** | 29,805 | 3,366 | **11.29%** | 4.63 | 15,599 | 7 |
| **22 Jul** | 31,296 | 3,000 | **9.59%** | 4.06 | 12,186 | 4 |
| **23 Jul** | 43,126 | 3,151 | **7.31%** | 2.93 | 9,228 | 5 |
| **24 Jul** | 73,676 | 4,107 | **5.57%** | 2.57 | 10,535 | 6 |
| **25 Jul** | 62,798 | 3,370 | **5.37%** | 2.58 | 8,705 | 4 |
| 26 Jul | 46,008 | 2,659 | 5.78% | 2.44 | 6,479 | 2 |
| 27 Jul | 44,928 | 2,334 | 5.19% | 2.66 | 6,219 | 4 |
| 28 Jul | 50,915 | 2,571 | 5.05% | 2.53 | 6,497 | 3 |
| 29 Jul | 56,749 | 2,977 | 5.25% | 2.65 | 7,894 | 4 |
| 30 Jul | 59,330 | 3,036 | 5.12% | 2.68 | 8,128 | 2 |
| 31 Jul | 84,602 | 3,816 | 4.51% | 2.42 | 9,225 | 2 |
| 01 Aug | 61,728 | 3,091 | 5.01% | 2.66 | 8,224 | 2 |
| 02 Aug | 44,917 | 2,421 | 5.39% | 2.52 | 6,112 | 2 |
| 03 Aug | 39,580 | 2,018 | 5.10% | 2.90 | 5,854 | 1 |

### Non-KFC weekly

| Week | Impressions | Clicks | Spend | **CTR** | **CPC** |
|---|---|---|---|---|---|
| 05–11 Jul | 218,129 | 37,389 | 203,132 | **17.14%** | 5.43 |
| 12–18 Jul | 202,021 | 24,644 | 115,517 | **12.20%** | 4.69 |
| 19–25 Jul | 294,809 | 23,428 | 84,690 | **7.95%** | 3.61 |
| 26 Jul – 01 Aug | 404,260 | 20,484 | 52,666 | **5.07%** | 2.57 |
| 02–03 Aug | 84,497 | 4,439 | 11,966 | **5.25%** | 2.70 |

**With KFC removed entirely:** CTR 12.20% → 5.07% (**−58%**), CPC 4.69 → 2.57 (**−45%**),
impressions 202,021 → 404,260 (**+100%**), clicks −16.9%. Blended marketplace was CTR
−68%, CPC −49%. **Same shape, same timing (20–26 Jul), same magnitude.**

### Two corrections this produced

**1. KFC did not churn — they ran a 12-day burst.** Store count: 2–3 active 5–7 Jul,
jumping to **22 on 8 Jul**, holding to 19 Jul, then tapering 14 → 7 → 4 across 20–22 Jul.
A campaign that started and ended, not a long-standing advertiser leaving. **The original
baseline (15–19 Jul) sat inside that burst**, inflating it.

**2. Corrected attribution** (against the cleaner 12–18 Jul baseline):

| Metric | KFC | Non-KFC |
|---|---|---|
| **Spend decline** (−ZAR 151,955) | −89,104 (**59%**) | −62,851 (41%) |
| **CTR decline** | **~none** — non-KFC fell 58% alone | **effectively all of it** |

**Implication:** even if every KFC store returned, CTR would recover only to roughly
6–7%, not 12–17%, because the extra ~200,000 impressions/week would remain.

---

## FOLLOW-UP 2 (2026-08-04) — non-KFC merchant decomposition

**Question posed:** for the non-KFC merchants, pre vs post — who contributed earlier, who
stopped, who was added, and why did impressions rise so much while clicks did not?

### Cohorts (non-KFC, 15–19 Jul vs 29 Jul–2 Aug)

| Cohort | Merchants | Impressions | Clicks | Spend (ZAR) | CTR | CPC |
|---|---|---|---|---|---|---|
| **PRE total** | 335 | 159,445 | 19,057 | 85,147 | **11.95%** | 4.47 |
| **POST total** | 391 | 307,326 | 15,331 | 39,559 | **4.99%** | 2.58 |
| | | **+92.7%** | **−19.6%** | **−53.5%** | | |
| **STOPPED** (pre only) | 80 | 44,438 | 5,423 | 23,487 | **12.20%** | 4.33 |
| **ADDED** (post only) | 136 | 120,428 | 6,971 | 18,473 | **5.79%** | 2.65 |
| **CONTINUED** — pre | 255 | 115,007 | 13,634 | 61,661 | **11.85%** | 4.52 |
| **CONTINUED** — post | 255 | 186,898 | 8,360 | 21,086 | **4.47%** | 2.52 |

### Attribution of the +147,881 impressions

| Source | Impressions | Share |
|---|---|---|
| **136 merchants added** | **+120,428** | **81.4%** |
| Continued merchants growing | +71,891 | 48.6% |
| 80 merchants stopped | −44,438 | −30.0% |

### Attribution of the −3,726 clicks

| Source | Clicks | Share |
|---|---|---|
| Continued merchants | −5,274 | 141.5% |
| 80 merchants stopped | −5,423 | 145.5% |
| 136 merchants added | +6,971 | −187.1% |

### ⭐ The decisive test — it is NOT a mix effect

Of the **73 continued merchants with ≥500 pre-period impressions**:
- **CTR fell for 72 of them — 99%**
- Impressions grew for 43 of them — 59%

**Merchant composition cannot make almost every individual advertiser's own CTR halve.
This is platform-side.**

Sample of continued merchants:

| Merchant | Pre impr | Post impr | Impr Δ | Pre clicks | Post clicks | **Pre CTR** | **Post CTR** |
|---|---|---|---|---|---|---|---|
| Moreish Delights By Dash | 3,629 | 7,585 | +109% | 165 | 118 | 4.55% | **1.56%** |
| Ribs & Burgers, Menlyn Maine | 478 | 3,773 | +689% | 82 | 274 | 17.15% | **7.26%** |
| Pizza Perfect, Glenbalad | 301 | 2,853 | +848% | 59 | 97 | 19.60% | **3.40%** |
| Sizzlin Shwarma Edenglen | 92 | 2,506 | +2,624% | 11 | 78 | 11.96% | **3.11%** |
| Archies Pizza Pasta Phoenix | 2,726 | 5,017 | +84% | 227 | 77 | 8.33% | **1.53%** |
| Pitstop Springs Restaurant | 254 | 2,537 | +899% | 30 | 64 | 11.81% | **2.52%** |
| Orexi Greek Street Food | 1,590 | 3,428 | +116% | 250 | 209 | 15.72% | **6.10%** |
| Grubhouse Terranova | 403 | 2,232 | +454% | 135 | 190 | 33.50% | **8.51%** |

**The key number:** continued merchants got **+62.5% impressions but −38.7% clicks**. The
incremental 71,891 impressions delivered **negative** clicks. Their original 115,007
impressions at the old 11.85% CTR would alone have produced 13,634 clicks; the whole book
fell to 8,360. **So the existing impressions degraded too — this is not merely low-quality
inventory bolted on at the bottom.**

### Who stopped (80 merchants @ 12.20% CTR)

| Merchant | Pre impr | Pre clicks | Pre spend | Pre CTR |
|---|---|---|---|---|
| The Braai Republic, Northgate | 2,741 | 377 | 1,831 | 13.75% |
| Fishaways Columbine Square | 4,190 | 275 | 1,437 | 6.56% |
| Debonairs Benmore Gardens | 1,448 | 178 | 1,377 | 12.29% |
| Steers Columbine Square | 2,337 | 168 | 1,148 | 7.19% |
| **Pedros Willows Crossing** | 432 | 285 | 855 | **65.97%** |
| **Barcelos, Sunnyside–Hatfield** | 238 | 128 | 764 | **53.78%** |
| Grubhouse Kolonnade | 512 | 145 | 830 | 28.32% |
| Grubhouse, Glen Balad | 570 | 161 | 787 | 28.25% |

### Who was added (136 merchants @ 5.79% CTR)

| Merchant | Post impr | Post clicks | Post spend | Post CTR |
|---|---|---|---|---|
| Aladdin Schwarma | 5,590 | 159 | 510 | 2.84% |
| Southern Corner Cafe – Bloemfontein | 4,925 | 45 | 66 | **0.91%** |
| Mammzo's Fish and Chips, Bloemfontein | 4,636 | 109 | 162 | 2.35% |
| The Fish & Chip Co Pietermaritzburg | 3,973 | 93 | 111 | 2.34% |
| Corner Restaurant & Tasteroom | 3,269 | 63 | **58** | 1.93% |
| Col'Cacchio GO Oliver Road | 2,809 | 82 | 75 | 2.92% |

**Profile of the added cohort — over half barely spend:**

| Added cohort | Merchants | Impressions | Clicks | Spend | CTR |
|---|---|---|---|---|---|
| Spending < ZAR 100 over 5 days | **73** | 46,642 | 1,860 | 3,125 | 3.99% |
| Spending ≥ ZAR 100 | 63 | 73,786 | 5,111 | 15,348 | 6.93% |

### ❌ Geographic-expansion hypothesis — TESTED AND DISPROVEN

Initially suspected from Bloemfontein/Pietermaritzburg names in the top-10 added table.
**That was cherry-picking; the full cohort does not support it.**

| City in merchant name | Stopped | Added | Continued |
|---|---|---|---|
| Midrand | 1 | 6 | 9 |
| Boksburg | 0 | 6 | 1 |
| Sandton | 0 | 2 | 8 |
| Durban | 0 | 0 | 6 |
| **Bloemfontein / Bloem** | 2 | 4 | 0 |

Only **27 of 136** added merchants carry an identifiable city, clustering in the **same
Gauteng metros as the existing roster**. Token analysis shows the additions are **chain
rollouts and individual store/mall names**, not new territory: **Debonairs 6 → 22 outlets**,
Col'Cacchio new, plus Polofields / Oakdene / Comaro / Carlton / Midway / Mews / Waterfall.

### Why impressions rose but clicks did not — the mechanics

The marketplace +70.2% decomposes multiplicatively:

| Layer | Change | Factor |
|---|---|---|
| Ad **requests** | +24.1% | 1.241 |
| **Response rate** (63.54% → 72.11%) | +13.5% | 1.135 |
| **Impressions per response** (I/R 4.57% → 5.52%) | **+20.8%** | 1.208 |
| **Combined** | **+70.2%** | 1.702 |

**The I/R rise is the telling layer — each response now renders ~21% more impressions,
i.e. literally more ads displayed per page.** Slots beyond the first few convert far worse,
which hits every merchant equally and explains the 99% universality.

Had all 307,326 post-period non-KFC impressions converted at the pre-period 11.95%, they
would have produced **36,725 clicks**. Actual: **15,331**. Gap: **21,394 clicks**.

### Hypotheses tested

| Hypothesis | Verdict |
|---|---|
| KFC exit caused the CTR/CPC fall | **Disproven** — non-KFC alone fell 58% |
| Geographic expansion into new regions | **Disproven** — same metros; only 20% of added merchants name a city |
| Merchant-mix dilution | **Partial** — real but the smaller effect |
| **Ads-per-page increase (I/R +20.8%)** | **Supported** — 99% universality is the proof |

### ⛔ Data exhausted

**Mr D's PLA request stream carries no `store_id`, `network`, `device` or `category`** —
every dimension returns a single blank row in both windows. No cut remains that would
isolate *which* placements or slots changed. Resolving "what changed on 20 July" now needs:
- engineering/product to confirm an ad-density, slot-count or relevance-threshold change, **or**
- placement-level attribution added to the request stream.

**This is the third marketplace in this file with an unattributed primary PLA surface**
(Apollo HOME, Tira CUSTOM, Mr D HOME). Worth raising as a systemic reporting gap.

**Infra note:** `test-data.onlinesales.ai` timed out twice at 120s on these dimension queries.

## Other programs

| Channel | Spend (ZAR) | Impressions | Clicks | CTR | CPC | GMV | **ROAS** |
|---|---|---|---|---|---|---|---|
| PLA | 53,878 | 406,263 | 20,852 | 5.13% | 2.58 | 286,827 | 5.32 |
| Auction Display | 29,850 | 118,996 | 1,133 | 0.95% | 26.35 | 9,426 | **0.32** |

(27 Jul – 2 Aug. Display is separate from the daily series above, which reconciles
exactly to the PLA channel.)

## Recommendations (reprioritised after the follow-up)

1. **PRIORITY — investigate the impression expansion.** Non-KFC impressions **doubled**
   (202,021 → 404,260/week) while clicks fell 17%. This drives the **entire** CTR and CPC
   decline and 41% of the revenue loss. Establish what changed around 20 July: ad density,
   slot count, or relevance thresholds. Requests +24%, RR +8.6pp and I/R +21% all
   contributed.
2. **Separately — establish whether the KFC campaign returns.** ZAR 89,104 of the
   ZAR 151,955 revenue drop. It was a **12-day burst (8–19 Jul), not a churn**, so the
   commercial question is whether that campaign recurs, not why an advertiser left.
3. **The CPC fall is not efficiency** — it is a thinner auction against doubled inventory.
   Do not report it as a win.
4. **Review the 137 new advertisers at 6.04% CTR** for relevance and placement quality.
5. **Auction Display at ROAS 0.32 on ZAR 29,850** warrants separate commercial review.
6. **Set expectations:** restoring KFC alone recovers CTR to ~6–7%, not the ~12–17% seen
   pre-20 July.

## Caveats
- **The mechanism is identified but not confirmed at source.** Ads-per-response rose 20.8%
  and CTR fell for 99% of continuing merchants — the evidence is strong, but *what* changed
  on 20 July (ad density, slot count, relevance threshold) cannot be read from any available
  report. Needs engineering/product confirmation. **This is the top open item.**
- **Mr D's PLA stream has no dimensional attribution** — `store_id`, `network`, `device`,
  `category_l1` all blank. No further drill is possible. Third marketplace in this file with
  this gap (Apollo HOME, Tira CUSTOM, Mr D HOME) — systemic reporting issue.
- **`get_campaign_status_changes` unavailable** (audit events blocked), so whether the KFC
  burst ended by design, by end-date, or by fault could not be established from data.
- **The I/R change date was not pinned** — the daily I/R series was not run, so the exact
  date ad density stepped up is unknown. Would be the natural next step for engineering.
- **Mr D Grocery (agency 572) was not checked** for the same pattern — if identical, it
  points to a platform-wide rather than marketplace-specific change.
- Scope inference on "mrd food" — see note under the heading.
- **Two methodological lessons from this ticket:**
  1. The original 15–19 Jul baseline sat inside an unrecognised 12-day advertiser burst.
     A 30-day view exposed it. Check baselines against a longer series before attributing cause.
  2. The geographic hypothesis came from reading two city names in a top-10 table. Testing
     it across the full cohort disproved it. **Don't infer a pattern from a sorted head.**

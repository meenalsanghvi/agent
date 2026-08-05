# Support ticket investigations — 2026-08-05

Three marketplace ad-performance tickets worked through the `debug-*` SOP skills.
All data via `run_report` against the KAM internal-performance reports
(`osmos-performance-local` MCP). Currency **INR** on tickets 1 and 3, **ZAR** on
ticket 2.

| # | Ticket | Marketplace | Skill | Verdict |
|---|---|---|---|---|
| 1 | 10088009 — PLA ads not serving for "snack"/"snacks", campaign FF_Snacks | bigbasket (444) | debug-keyword-delivery | Invalid — both terms serving; mapping correct; new-campaign cold start |
| 2 | SPA Query, Seller ID 29899805 — CREA/ASHWA/TYRO not serving on "creatine"/"ashwagandha" | takealot (105) | debug-keyword-delivery | Invalid — both serving; dip caused by the seller's own weekly campaign re-creation; not outbid |
| 3 | TIRA — low RR despite increased Requests (Jul 16–19, Jul 31) | tira (576) | debug-rr | Not a fill defect — a surge of **brand-filtered** CUSTOM requests (99.5% of the increase); non-brand fill was **96.2%**; window corrected to Jul 17–18 |

> **Pattern across tickets 1 and 2.** Neither was a defect. Both were **newly created
> campaigns** judged during their ramp-up, and in both the complaint originated from
> inspecting a live ad response rather than from reporting. Ticket 2's seller has
> re-created the same campaign eight times since 2 June, restarting the ramp each time.

> **Pattern across all three.** None was a platform defect, and in each the metric or
> observation that triggered the ticket was read without its denominator. Tickets 1 and 2
> judged delivery from a single sampled ad response; ticket 3 read an RR ratio without
> checking that the request count underneath it had doubled. **Ticket 3 is the one to
> generalise from:** RR alerts fire on the ratio, so any request-volume event presents as
> a response-side failure. A request-volume guardrail alongside the RR alert would have
> triaged it in minutes.
>
> **Sharpened on the second pass.** The generalisation is stronger than "watch request
> volume". The decisive cut was `FILTER_PRESENCE_RR_REPORT`'s present-vs-absent split,
> which showed 99.5% of the surge carried a `brands` filter while unfiltered requests
> filled at 96.2%. **A single report call separated "we are failing to serve" from "we are
> being asked for things that do not exist."** For any Scenario A move, that split belongs
> in triage, not at the end of the SOP — see action 8.

> **Related:** ticket 3 of `ticket-investigations-2026-08-03.md` ('Green Tea' SKUs
> not serving) is the **same advertiser, os_client_id 10092920**, same `FF_`
> campaign family, same complaint shape, same verdict. Two in three days.

---

## Environment limitations encountered

New this session; the 2026-08-03 list still applies.

- **`CAMPAIGN_KEYWORDS_REPORT` cannot be filtered on `perf_is_negative`.** Every
  value type fails at the same BigQuery position — `IN` with `["0"]` and with `[0]`
  both return `No matching signature for operator IN for argument types INT64 and
  {STRING}`; `=` with `0` returns `No matching signature for operator = ... STRING,
  INT64`. The SOP's "must pass `perf_is_negative` = 0" is therefore not executable.
  **Workaround:** request `perf_is_negative` as an *attribute* and split
  targeted-vs-negative client-side. Filtering on `perf_campaign_id` alone works.
- **`CAMPAIGN_LOOKUP_REPORT` has no `perf_campaign_creation_date` and no
  `perf_merchant_name`** despite both appearing in adjacent report configs —
  `attribute '<x>' not configured for report`, HTTP 500. Creation date is available
  on `INTERNAL_KEYWORD_PERFORMANCE_REPORT`, which is where it was read from here.
- **`RESPONDED_SKUS_REPORT` and `INTERNAL_KEYWORD_PERFORMANCE_REPORT` disagree in
  scale on the same keyword×campaign.** For "snack" on FF_Snacks over overlapping
  windows: 3,988 SKU-impressions / INR 147.20 versus 4 impressions / INR 2.40. The
  grains differ (SKU-level responses versus campaign billed impressions) but the
  **spend columns are the same unit and still disagree ~60×**. Both were used
  qualitatively; neither was quoted against the other. Worth reconciling before any
  reply quotes both.
- **`CAMPAIGN_LOOKUP_REPORT` ignores `limit` as documented** — a `LIKE '%Snack%'`
  filter still returned 4,125 lines and overflowed into the saved tool-result file.
  Filtering by name works but plan to grep the spill.
- **`MERCHANT_LOOKUP_REPORT` does not resolve a seller ID.** It exposes only
  `perf_merchant_id`, `perf_os_client_id`, `perf_merchant_name`; filtering it on the
  seller ID from a ticket returns **zero rows and no error**. On takealot the seller
  ID is carried as `perf_seller_id` on `INTERNAL_KEYWORD_PERFORMANCE_REPORT` and as
  `perf_merchant_id` on `CAMPAIGN_PRODUCT_SELECTION_REPORT`, **with an `M` prefix**
  (ticket's `29899805` → `M29899805`). Rival IDs in the same ticket carried `M` and
  `R` prefixes. Resolve sellers through the keyword or product-selection reports, and
  expect a letter prefix.
- **`CAMPAIGN_PRODUCT_SELECTION_REPORT` returns only L1–L3.** Takealot's taxonomy runs
  to L5 (`Health > Health Care > Vitamins & Supplements > Vitamins & Minerals > Mind &
  Memory`); the report stops at `Vitamins & Supplements`. The deeper levels a ticket
  quotes have to be read from `RESPONDED_SKUS_REPORT.perf_category`, which carries the
  full path as a single string.
- **takealot exposes more relevance caches than bigbasket.** Alongside
  `TARGETED_KEYWORD_CACHE` and `SEARCH_TERMS_WITHOUT_BRAND_STUFFING`, ticket 2 returned
  `INTERNAL_TARGETED_KEYWORD_CACHE`, `SIMILAR_SEARCH_TERMS_CACHE_V2`, `UA_BRAND_CACHE`
  and `UA_MERCHANT_CACHE`. `INTERNAL_TARGETED_KEYWORD_CACHE` carried the **largest**
  volume on both keywords. Treat any cache-type list as marketplace-specific; do not
  assume the bigbasket set.
- **`MARKETPLACE_DIRECTORY_REPORT` region field is unreliable** — takealot returns
  `Belgium` with ZAR currency and Africa/Johannesburg timezone. Use currency and
  timezone, not region.

### Found on ticket 3 (tira, `debug-rr`)

- **`PAGE_PERFORMANCE_PLA_REPORT` and `RR_PLA_REPORT` reject
  `perf_marketplace_client_id` as a filter** — `filter key
  'perf_marketplace_client_id' not configured for report`, HTTP 500. Both are scoped by
  `agency_id` alone. Passing the marketplace client ID out of habit fails the call
  outright rather than being ignored.
- **`RR_PLA_REPORT`'s mandatory `perf_category_l1 != ''` filter makes the SOP's category
  drill unrunnable on tira.** 100% of CUSTOM requests and ~99% of SEARCH requests carry a
  **blank** `category_l1` (CUSTOM: 1,005,400 of 1,005,400 on 31 Jul; SEARCH: only ~4,425
  of 429,101 tagged). The filter therefore excludes every CUSTOM row and returns **zero
  rows with no error** — indistinguishable from "no data for this period". Diagnose this
  by requesting `perf_category_l1` as an *attribute* first and reading the blank share
  before trusting any category cut. `perf_page_name` is no substitute: CUSTOM resolves to
  a single value, `CUSTOM`.
- **The `!=` operator compounds the above.** `{"operator": "!=", "values": [""]}` on
  `perf_category_l1` returns zero rows silently; so does `NOT IN`. Since the column is
  genuinely blank here, the two failure modes are impossible to tell apart from the
  response alone — same class of trap as the documented "prefer IN/NOT IN over =/!= for
  string ID columns" note.
- **`RR_PLA_REPORT` accepts `perf_day` + `perf_hour` without the store-bucket group-by.**
  `knowledge/tool-map.md:110` lists `perf_hour` only under the
  `get_store_level_rr_buckets` variant with a **must pass** group-by of
  `perf_store_id`, `perf_category`, `perf_day`, `perf_hour`. In practice
  `["perf_page_type","perf_day","perf_hour"]` runs fine and returns clean 24-row-per-day
  output. Useful, because the full store×category×day×hour grain would have overflowed
  the response. Worth relaxing the documented requirement.
- **`RR_PLA_REPORT` at L1–L3 grain overflows the tool-result limit** — page_type ×
  L1/L2/L3 for a **single day pair** on tira returned 2,031 lines / 57,861 characters and
  spilled to a saved file. Request L1 first, then drill.
- **`AUDIT_EVENTS_REPORT` is UNBLOCKED** (re-checked 2026-08-05, second pass). Tickets 1
  and 2 were worked while it was still failing; it now returns rows for agency 576 on both
  TIRA windows. `AUTHORING_STATUS.md:104` documents the fix (all 43 configs moved to
  `GCP_PERF_BQ_KAM_CREDENTIALS`). **Do not report the audit family as unavailable.**
- **`AUDIT_EVENTS_REPORT` rejects `=` on `perf_action_type_id`; use `IN`.**
  `{"operator": "=", "values": ["16"]}` fails with `No matching signature for operator =
  for argument types: STRING, INT64` — the transport coerces the string to an int against
  the report's `SAFE_CAST(... AS STRING)` selector. `{"operator": "IN", "values": ["16"]}`
  works. This **contradicts** the known-issues row in `knowledge/reports.md`, which says
  to use `EQUALS` (that guidance is correct for `CAMPAIGN_KEYWORDS_REPORT`'s
  `perf_is_negative`, not for this column). Also request `perf_action_type_id` as an
  attribute — it echoes back and confirms the filter took.
- **`FILTER_PRESENCE_RR_REPORT` is LIVE.** `AUTHORING_STATUS.md:96` still records it as
  "never posted to Mongo — the only one of 41 missing"; that is **stale**. It runs and its
  totals reconcile exactly with `PAGE_PERFORMANCE_PLA_REPORT`. The BQ grant wall on the
  region request-log datasets appears to be down — worth re-testing
  `CATEGORY_REQUEST_VOLUME_REPORT`, which failed for the same reason.
- **`FILTER_PRESENCE_RR_REPORT` silently drops requested attributes but honours
  `perf_page_type` as a *filter*.** The config is ungrouped (one row); passing
  `perf_page_type` in `attributes` returns a response with no such key and no error, so a
  CUSTOM-vs-SEARCH cut looks impossible. Passing it in `filters` instead works and returns
  correctly-scoped totals. Without this workaround the whole diagnosis would have been
  stuck at marketplace level.
- **Out-of-retention windows on `FILTER_PRESENCE_RR_REPORT` return zeros, not an error.**
  Jul 17–18 (19 days back) returned `0` for every metric. Indistinguishable from "no
  traffic" — same silent-failure class as the `perf_category_l1 != ''` trap above. Compute
  the 14-day boundary before trusting a zero row.

---

# Ticket 1 — PLA Ads Not Serving for Campaign FF_Snacks

**Marketplace:** bigbasket-marketplace, agency **444**, client 10088009, INR,
Asia/Kolkata · **PLA**, SEARCH page
**Raised:** 2026-08-03 · worked 2026-08-05
**Advertiser as stated in ticket:** "innovative retail concepts pvt ltd (1297)" —
1297 is the **merchant_id**, confirmed on `CAMPAIGN_PRODUCT_SELECTION_REPORT`
**Campaign:** `FF_Snacks` — marketing_campaign_id **1349701**, internal_campaign_id
880998, campaign_group_id 880831, marketing_campaign_group_id 5184671,
os_client_id **10092920**, OS_ADS_SEARCH, **AUTO_CPM**, **ACTIVE**,
**created 2026-07-28**
**Keywords under complaint:** "snack", "snacks"
**Category under complaint:** `Gourmet-World-Food > Snacks-Dry-Fruits-Nuts >
Healthy-Baked-Snacks`
**Windows:** current 2026-08-03 → 08-04 · baseline 2026-07-28 → 08-02 (campaign's
first six days) · request volume trailing 7d to 08-04

## Verdict: no defect. Both terms serve. No mapping change required.

The complaint was **valid when raised** — the campaign was six days old and had
delivered 21 impressions total. It began serving normally on **3 August**, the day
the ticket was raised. By 3–4 August it was delivering 11,820 impressions at
**ROAS ~11.8**.

## STEP 2 — Campaign-scoped keyword validation

`INTERNAL_KEYWORD_PERFORMANCE_REPORT`, filtered to campaign 1349701 + os_client 10092920.

| Window | Keyword | Impr | Clicks | Spend (INR) | Attributed sales (INR) |
|---|---|---|---|---|---|
| 28–31 Jul | snack | 4 | 0 | 2.40 | 0 |
| 28–31 Jul | snacks | 5 | 0 | 6.40 | 0 |
| 1–2 Aug | snack | 0 | 0 | — | — |
| 1–2 Aug | snacks | 12 | 2 | 24.00 | 0 |
| **3–4 Aug** | snack | **0** | 0 | — | — |
| **3–4 Aug** | snacks | **11,820** | **303** | **19,808.00** | **233,423.82** |
| 28 Jul–4 Aug | snacks (total) | 11,837 | 305 | 19,838.40 | 233,423.82 |

Targeted keywords on the campaign (`CAMPAIGN_KEYWORDS_REPORT`) — exactly two, both
EXACT, **no negatives**:

| Keyword | Match | `perf_bidding_value` (raw) |
|---|---|---|
| snack | EXACT | 1000 |
| snacks | EXACT | 1600 |

Unit of `perf_bidding_value` is not stated by the report; treated as relative only.

## STEP 3 — Request-volume threshold

`SEARCH_QUERY_REQUESTS_PLA_REPORT`, marketplace-wide. Bar is >100 requests / 7 days.

| Window | Keyword | Requests | Responses | RR | Days | vs bar |
|---|---|---|---|---|---|---|
| 29 Jul–4 Aug | snack | 38,512 | 33,540 | 87.09% | 7/7 | 385× over |
| 29 Jul–4 Aug | snacks | 152,791 | 133,185 | 87.17% | 7/7 | 1,528× over |
| 27 Jul–2 Aug | snack | 37,228 | 32,363 | 86.93% | 7/7 | 372× over |
| 27 Jul–2 Aug | snacks | 148,967 | 129,807 | 87.14% | 7/7 | 1,490× over |

Both keywords clear the bar in both windows, so the "no category was created for
this keyword" path is ruled out — including retrospectively, for the complaint window.

## STEP 4/5 — Product selection and category alignment

`CAMPAIGN_PRODUCT_SELECTION_REPORT` — **9 SKUs, all in stock, all merchant 1297,
all brand `bb-gooddiet`, all in the single category named in the ticket**
(`gourmet-world-food > snacks-dry-fruits-nuts > healthy-baked-snacks`):

40167617 Ragi Sticks Achari Masala · 40167618 Mini Quinoa Puffs Cheese 'N' Herbs ·
40167619 Quinoa Puffs Spicy Garlic · 40167620 Multigrain Puffs Butter Makhana ·
40167621 Multigrain Balls Chilli Chataka · 40167622 Ragi Sticks Tangy Mint ·
40167624 Quinoa Puffs Onion Masala · 40167625 Multigrain Puffs Tangy Tomato ·
40167626 Multigrain Chips Sour Cream 'N' Onion

| Check | Result |
|---|---|
| "snack"/"snacks" in any product name? | **No — 0 of 9.** Names are Sticks / Puffs / Balls / Chips. Matching is by category, not title. Normal, not a defect. |
| Keyword serving at all? | "snacks" yes; "snack" keyword row zero — resolved by 6a below |
| Category matches the ticket's? | **Yes, exactly, for all 9 SKUs** |

## STEP 6 — Competition

### 6a — Search-query match performance (the decisive call)

`SEARCH_QUERY_MATCH_PERFORMANCE_REPORT`, campaign 1349701, 3–4 Aug:

| Search query | Matched keyword | Impr | Clicks | Spend (INR) | Top-of-search impr | ToS share |
|---|---|---|---|---|---|---|
| snacks | snacks (EXACT) | 10,823 | 280 | 18,118.40 | 8,535 | 78.9% |
| **snack** | **snacks** (EXACT) | **997** | **23** | **1,689.60** | 805 | **80.7%** |
| 22 long-tail variants ("snacks for", "snack it", …) | snacks | 0 | 0 | 0 | 0 | — |
| **Total** | | **11,820** | **303** | **19,808.00** | 9,340 | 79.0% |

**The singular query "snack" is matched by the *plural* keyword "snacks".** That is
why the "snack" keyword line item reads zero while the term itself serves. The total
reconciles exactly with the campaign figure in STEP 2.

`perf_top_of_search_impressions` is a share of **our own** impressions, not a
competitive share. True SOV is not computable from this report — no marketplace-total
column — and was not claimed.

### 6b — Rivals manually targeting "snack" (eCPM = spend ÷ impr × 1000)

| Campaign | Match | Subtype | Created | Impr 28 Jul–2 Aug | Spend | eCPM | Impr 3–4 Aug | eCPM |
|---|---|---|---|---|---|---|---|---|
| All Namkeen – PLA – Generic (1193811) | EXACT | os_ads_search | 2026-03-17 | 11,836 | 7,140.17 | **603** | 1,964 | **610** |
| Classic Chaat Sweet Corn (1352365) | BROAD | os_ads_search | **2026-07-30** | 182 | 124.80 | 686 | 117 | 633 |
| Kurkure \| SP \| Generic (1142122) | PHRASE | smart_shopping | 2025-12-05 | 130 | 89.60 | 689 | — | — |
| Lays Core \| SP \| Generic (1142275) | PHRASE | smart_shopping | 2025-12-05 | 80 | 50.80 | 635 | — | — |
| RBMP \| Chips \| 2807 (1114614) | EXACT | smart_shopping | 2025-10-10 | 40 | 22.21 | 555 | — | — |
| **FF_Snacks (1349701)** | EXACT | os_ads_search | 2026-07-28 | 4 | 2.40 | 600 | 0 | — |

Only six campaigns manually target "snack" at all. The auction clears at
**INR 555–689 CPM**; FF_Snacks achieved **INR 1,676 CPM** on the plural over the same
2 days. **Not an outbidding case.** The one new entrant in the dead window (Classic
Chaat, created 30 Jul) took 182 impressions — immaterial.

The campaign is **AUTO_CPM**, so the effective bid is system-set; the manual
per-keyword values are not the operative lever. This matters because the client had
already been advised to raise bids.

### 6c — Served-on competition and category share

`RESPONDED_SKUS_REPORT`, 29 Jul–4 Aug, SKU-level impressions.

Category share of each query, TARGETED_KEYWORD_CACHE path:

| Query | Category | SKU-impr | Share |
|---|---|---|---|
| snack | snacks-branded-foods>snacks-namkeen>namkeen-savoury-snacks | 63,262 | 56.2% |
| snack | snacks-branded-foods>snacks-namkeen>chips-corn-snacks | 34,210 | 30.4% |
| snack | food-court>snack-time>desi-naashta | 11,160 | 9.9% |
| snack | **gourmet-world-food>snacks-dry-fruits-nuts>healthy-baked-snacks** | **3,988** | **3.5%** |
| snacks | namkeen-savoury-snacks | 686,055 | 58.8% |
| snacks | chips-corn-snacks | 315,748 | 27.1% |
| snacks | desi-naashta | 121,460 | 10.4% |
| snacks | **healthy-baked-snacks** | **43,292** | **3.7%** |

The client's category holds an **identical ~3.5% share of both** terms; the plural is
simply ~10× the volume. The client receives its proportional share on each.

Who serves `healthy-baked-snacks` on the query "snack":

| Path | Brand | SKUs | SKU-impr | Clicks |
|---|---|---|---|---|
| **TARGETED_KEYWORD_CACHE** | **bb-gooddiet (the client)** | **all 9** | **3,988** | 92 |
| SEARCH_TERMS_WITHOUT_BRAND_STUFFING | peri's-bakehouse, habanero, 2pm-snacks | 8 | 640 | 8 |

**All nine campaign SKUs respond to "snack" through the targeted-keyword path, and
the client is the only advertiser reaching that category on that path.** Competitors
appear only via the weaker auto-relevance cache. Same result on "snacks" (43,292
SKU-impr, 1,100 clicks, targeted path). A broken keyword→category mapping cannot
produce this.

## Answers to the questions asked

| Question | Answer |
|---|---|
| Is there an issue with the category-keyword mapping for Healthy-Baked-Snacks? | **No.** Proven three ways: the category serves on both queries via `TARGETED_KEYWORD_CACHE`; all 9 SKUs respond; the client is the sole targeted-path advertiser in that category on "snack". |
| Are keyword-to-category mapping changes required? | **No.** |
| Are we not responding with ads for "snack" and "snacks"? | **We are.** 3–4 Aug: "snacks" 10,823 impr / INR 18,118.40; "snack" 997 impr / INR 1,689.60, both at ~79–81% top-of-search. |
| Why did bid increases not help? | They were not the constraint. The "snack" auction clears at INR 555–689 CPM against the campaign's achieved INR 1,676. The campaign is AUTO_CPM, so the system sets the effective bid regardless. |
| Any other factors impacting delivery? | Yes — **campaign age.** Created 28 Jul, 21 impressions in six days, normal delivery from 3 Aug. |

## Caveats

- **The keyword's mapped category list is not readable.** `get_keyword_categories`
  has no KAM equivalent. Mapping is proven to *work* empirically via cache_type; it
  cannot be enumerated, so an unusual mapping cannot be ruled out by direct
  inspection. Same limitation as tickets 1 and 3 on 2026-08-03.
- **Attributed sales for 3–4 Aug are still settling**, so ROAS ~11.8 is a floor.
- `perf_bidding_value` units are unstated; used only as a relative comparison.
- The `RESPONDED_SKUS_REPORT` versus `INTERNAL_KEYWORD_PERFORMANCE_REPORT` spend
  discrepancy noted above — do not quote both to the client.
- **Not run:** audit-event checks for a bid or budget edit on 3 Aug (the
  `AUDIT_EVENTS_REPORT` family remains blocked on infra), and hour-level delivery
  across the first six days. Neither is needed for the verdict; the first would
  confirm whether the 3 Aug turn-on coincided with the client's bid change or was
  the AUTO_CPM ramp.

## Actions

1. Reply to the client: no mapping change; both terms serving; explain the six-day
   ramp and the singular→plural match.
2. Advise reverting the bid increase made around 3 Aug and re-measuring — the
   campaign was not bid-constrained.
3. Suggest dropping "snack" as a separate targeted keyword. It is fully absorbed by
   "snacks" and will keep reporting near-zero, which is what generated this ticket.
4. Flag to the account team: **second ticket in three days from os_client 10092920**
   where the complaint came from eyeballing a live search page rather than reporting
   (see ticket 3, 2026-08-03). Worth a short explainer to the advertiser on why a
   single SERP check is not evidence of non-delivery.
5. Raise the `CAMPAIGN_KEYWORDS_REPORT` `perf_is_negative` filter bug and the
   `CAMPAIGN_LOOKUP_REPORT` missing-attribute errors against the report configs.

---

# Ticket 2 — SPA Query | Seller ID 29899805 (takealot)

**Marketplace:** takealot-marketplace, agency **105**, marketplace_client_id
**100002**, **ZAR**, Africa/Johannesburg · **PLA**, SEARCH page
*(the ticket's ad-request URLs carry `client_id=100002`, which confirms the
marketplace independently)*
**Raised:** 2026-07-27 by Tatwik / Mayur Rathod · worked 2026-08-05
**Seller:** ticket's `29899805` = **`M29899805`** in reporting
**Campaign:** `CREA,ASHWA,TYRO(22nd Jul | 11:04)` — marketing_campaign_id
**1344829**, internal_campaign_id 877535, campaign_group_id 877370,
marketing_campaign_group_id 5179797, os_client_id **10159561**,
PERFORMANCE / **SMART_SHOPPING**, **AUTO_CPC**, **ACTIVE**,
**created 2026-07-22**
**Keywords under complaint:** "creatine" (bid 30.47), "ashwagandha" (bid 20.5)
**Windows:** predecessor 2026-07-16 → 07-21 · ticket window 2026-07-22 → 07-27 ·
current 2026-07-28 → 08-04

## Verdict: no defect. Both keywords served throughout. The seller is not outbid.

The dip that prompted the ticket was real but **caused by the seller archiving the
campaign that was running and creating a new one on 22 July**. Delivery has since
recovered past its previous level.

## STEP 1.5 / STEP 2 — Campaign resolution and keyword validation

`INTERNAL_KEYWORD_PERFORMANCE_REPORT`, filtered to os_client_id 10159561 (no campaign
filter, so a hand-off between campaigns is visible).

| Window | Days | Campaign | Keyword family | Impr | Clicks | Spend (ZAR) | **Impr/day** |
|---|---|---|---|---|---|---|---|
| 16–21 Jul | 6 | 1335705 *(predecessor, ARCHIVED)* | creatine | 857 | 35 | 431.08 | **142.8** |
| 16–21 Jul | 6 | 1335705 | ashwagandha | 828 | 19 | 291.93 | **138.0** |
| 22–27 Jul | 6 | **1344829** | creatine | 490 | 11 | 111.26 | **81.7** |
| 22–27 Jul | 6 | **1344829** | ashwagandha | 552 | 8 | 87.40 | **92.0** |
| 28 Jul–4 Aug | 8 | **1344829** | creatine | 2,353 | 32 | 416.39 | **294.1** |
| 28 Jul–4 Aug | 8 | **1344829** | ashwagandha | 1,127 | 18 | 205.09 | **140.9** |

"Keyword family" groups the match-type rows the report returns separately —
creatine EXACT + PHRASE; ashwagandha EXACT + PHRASE + the "ashwaganda" misspelling
PHRASE. **Every window has non-zero delivery on both keywords and on both match
types.** The claim "not appearing in the ad response" is not supported.

Per-day delivery fell **43%** (creatine) and **33%** (ashwagandha) in the ticket
window, then rose to **2.1×** and **1.02×** the pre-ticket rate.

### The cause — the seller re-creates this campaign weekly

`CAMPAIGN_LOOKUP_REPORT` on os_client_id 10159561, name `LIKE '%ASHWA%'`:

| Created | Campaign | Status |
|---|---|---|
| 2 Jun | Ashwagandha & Tyrosine (2nd Jun \| 14:46) | ARCHIVED |
| 6 Jun | Ashwa,tyrosine (6th Jun \| 10:40) | ARCHIVED |
| 10 Jun | ASHWA,TYRSOINE (10th Jun \| 19:57) | ARCHIVED |
| 24 Jun | Ashwa and Tyrosine (24th Jun \| 09:33) | ARCHIVED |
| 2 Jul | ashwa, tyrosine(2nd Jul \| 17:05) | ARCHIVED |
| 11 Jul | ashwa tyrosine(11th Jul \| 12:12) | ARCHIVED |
| 15 Jul | Crea, Ashwa, Tyrosine (16th Jul \| 00:05) | ARCHIVED |
| **22 Jul** | **CREA,ASHWA,TYRO(22nd Jul \| 11:04)** | **ACTIVE** |

Eight campaigns since 2 June, each superseding the last. A separate
`creatine (11th Jul | 12:11)` (1325060) is also ARCHIVED. Smart Shopping re-enters
its learning period on every new campaign, so the seller resets delivery roughly
weekly by their own hand.

## The bid claim — the seller is winning below their own bid

Actual CPC over 28 Jul – 4 Aug, against the bids quoted in the ticket:

| Keyword | Bid (ZAR) | Spend (ZAR) | Clicks | **Actual CPC** | % of bid paid |
|---|---|---|---|---|---|
| creatine | 30.47 | 416.39 | 32 | **13.01** | **42.7%** |
| ashwagandha | 20.50 | 205.09 | 18 | **11.39** | **55.6%** |

Paying well under the bid is the signature of an auction being won comfortably, not
lost. The achieved CPCs also sit alongside the rival bids the ticket quotes (R10164
at 10, M29892540 at 16.5) rather than below them. **Being outbid is ruled out.**

Note the campaign is **AUTO_CPC**, so the effective bid is system-set and the manual
per-keyword values act as a ceiling.

## STEP 4/5 — Product selection and category alignment

`CAMPAIGN_PRODUCT_SELECTION_REPORT` — **only 3 SKUs**, all merchant M29899805, all
in stock, all brand PrimeState:

| SKU | Product | Category (L1>L2>L3) |
|---|---|---|
| 234081656 | PrimeState **Ashwagandha** + L-Theanine 60 Capsules | Health > Health Care > Vitamins & Supplements |
| 234100672 | PrimeState L-Tyrosine + L-Theanine 60 Capsules | Health > Health Care > Vitamins & Supplements |
| 234118915 | PrimeState **Creatine** Monohydrate + Collagen 450g | Health > Health Care > Sports Nutrition |

| Check | Result |
|---|---|
| Keyword in product name? | **Yes, both** — "Ashwagandha" and "Creatine" appear literally in the SKU titles |
| Keyword serving? | **Yes, both**, EXACT and PHRASE, every window |

SOP verdict: *serving + name match* → **alignment is not the problem**; proceed to
competition. Deeper category levels are not in this report (L1–L3 only) and were read
from serving data instead.

## The real finding — the seller sits in the secondary category on both keywords

`RESPONDED_SKUS_REPORT`, marketplace-wide, 28 Jul – 4 Aug, SKU-level impressions:

| Keyword | Category | TARGETED_KW | INTERNAL_TARGETED_KW | All caches | Share |
|---|---|---|---|---|---|
| creatine | Sports Nutrition > **Creatine** *(rival R10164)* | 1,850 | 30,684 | **64,218** | **69.7%** |
| creatine | Sports Nutrition > **Recovery & Supplements** *(seller)* | 18,271 | 5,545 | **24,310** | **26.4%** |
| creatine | Sports Nutrition > Pre-Workout | 3,563 | 28 | 3,591 | 3.9% |
| creatine | Sports Nutrition > Mass Builders | 0 | 8 | 8 | 0.0% |
| ashwagandha | … > **Mood & Anxiety Support** *(rival M29892540)* | 16,240 | 14,341 | **33,379** | **67.4%** |
| ashwagandha | … > **Mind & Memory** *(seller)* | 6,063 | 9,184 | **16,073** | **32.5%** |
| ashwagandha | … > Nutraceuticals / Energy & Tonics / Sleep Aids | 1 | 19 | 71 | 0.1% |

**Both of the seller's categories are correctly mapped** — each serves substantially
through the targeted-keyword path, which only opens on a valid keyword→category
mapping. **No mapping change is required.**

**But the ticket's observation is substantively correct and its conclusion wrong.**
The two rivals it names are not in a category the seller is excluded from; they are
in the **higher-volume category for each term**. `Creatine` carries **2.6×** the
supply of `Recovery & Supplements`; `Mood & Anxiety Support` carries **2.1×** that of
`Mind & Memory`. This is why a rival at a *lower* bid appeared in a sampled response,
and it is a **catalogue placement** matter — a Takealot merchandising decision, not an
ad-platform setting.

## Answers to the questions asked

| Question | Answer |
|---|---|
| Why is the seller not included in the ad response despite higher bids? | **They are included.** Both keywords served in every window; creatine is now at 294 impressions/day, more than double the pre-ticket rate. A single ad response samples a handful of slots and does not evidence non-delivery. |
| Are they being outbid? | **No.** They pay ZAR 13.01 and 11.39 against bids of 30.47 and 20.50 — 43% and 56% of bid. |
| Were the products serving previously and no longer? | Delivery **did** dip 43% / 33% per day in 22–27 Jul. The cause is that the seller archived the campaign running until 21 Jul and created a new one on 22 Jul, restarting Smart Shopping's learning period. It has since recovered past the old level. |
| Is the category mapping wrong? | **No.** Both seller categories serve on both keywords through the targeted-keyword path. |
| Any other factor? | Yes, two: the seller is in the **secondary category** for both terms (2.1–2.6× less supply than the rivals' categories), and the campaign holds only **3 SKUs**. |

## Caveats

- **Keyword→category mapping cannot be read directly** (`get_keyword_categories` has
  no KAM equivalent). Proven to *work* empirically via cache_type; not enumerable.
- **Unit mismatch not reconciled:** category figures are SKU-level impressions across
  all advertisers; campaign figures are campaign impressions. **No share-of-voice was
  computed from the two** — different denominators. Same caution as ticket 1.
- **Test-method questions to put back to the requester, not asserted as findings:**
  the ad-request URLs use `cli_ubid=test` (a synthetic user, which may not exercise
  normal relevance/personalisation), and the path is `/sda` while the ticket is headed
  "SPA Query". Confirm the sample matched the ad product before treating one response
  as evidence.
- **Not run:** STEP 6 competition views (rival campaign IDs, creation dates, whether
  R10164 or M29892540 is a new entrant around 22 Jul). The outbidding claim is
  answered from our own CPC-versus-bid, which is sufficient but is inference from one
  side of the auction. `AUDIT_EVENTS_REPORT` remains blocked, so the archive timestamp
  of campaign 1335705 could not be confirmed directly — it is inferred from the
  delivery hand-off and the successor's 22 Jul creation date.
- **Return on ad spend is weak but not zero**, and improving: ROAS 0.82 (16–21 Jul),
  0.00 (22–27 Jul), **1.60** (28 Jul – 4 Aug: ZAR 1,310 attributed sales on ZAR 819
  spend). Out of scope for this ticket; flagged rather than analysed.

## Actions

1. Reply: both keywords are serving; the dip traces to the seller's own campaign
   re-creation; they are not outbid.
2. **Ask the seller to stop re-creating the campaign weekly.** Eight campaigns since
   2 June is the single largest controllable factor in their delivery.
3. Recommend, via catalogue: list the creatine SKU under `Sports Nutrition > Creatine`
   and the ashwagandha SKU under `Mood & Anxiety Support` — 2.6× and 2.1× more
   available supply on the terms they care about.
4. Recommend expanding beyond **3 SKUs**. Same product-selection ceiling documented on
   bigbasket (ticket 11, 2026-08-03).
5. Put the `cli_ubid=test` / `/sda` sampling questions back to Tatwik before treating
   any future single-response check as evidence.
6. Raise the `MERCHANT_LOOKUP_REPORT` seller-ID gap and the
   `CAMPAIGN_PRODUCT_SELECTION_REPORT` L1–L3 truncation against the report configs.

---

# Ticket 3 — TIRA | Low RR despite increased Requests

**Marketplace:** tira-marketplace, agency **576**, marketplace_client_id **10119611**,
**INR**, Asia/Kolkata · **PLA**, **CUSTOM** page
**Raised:** by Harshita Kulshreshtha (Client Growth) · worked 2026-08-05
**Skill:** `debug-rr` · **Scenario A** (requests up, responses did not follow)
**Windows as stated in ticket:** Jul 16–19 and Jul 31
**Windows as they actually are:** **Jul 17–18** and **Jul 31** — see the correction below
**Baselines:** Jul 15–16 (for Jul 17–18) · Jul 30 (for Jul 31) · Jul 12–15 (page-type
triage) · full daily series Jul 1 – Aug 4

## Verdict: ROOT CAUSE IDENTIFIED — unfillable ad requests for the brand **Anua**

**Not a fill defect and not a platform defect.** On 31 July, TIRA emitted **633,205**
CUSTOM ad requests filtered to the brand **Anua** — **919× the previous day's 689** — and
every single one returned zero ads. Anua accounts for **107.5% of the brand-filtered
request increase** (over 100% because all other brands' requests *fell* 17.9% that day)
and **63% of all CUSTOM ad requests** on 31 July.

**Remove Anua and the incident does not exist:** CUSTOM RR on 31 July would have been
**60.70%**, against 30 July's 60.47% on the same basis.

**Why zero fill — and it is not a name-mismatch bug.** Anua *is* in tira's catalogue: **24
SKUs**, `e_brand` spelled exactly `Anua`, identical to the request filter. But **0 of those
SKUs sit in any campaign's product selection** — 0 active, 0 distinct campaigns. No
advertiser on tira has ever bought Anua. The requests were well-formed and correctly
spelled against a brand with no purchasable inventory.

**⚠️ STILL ONGOING.** Anua requests did not stop — 90,514 since 1 August (≈19–27k/day),
all unfillable, costing **2.5–3.2 percentage points of CUSTOM RR every day**. 31 July was
the spike; the leak is live and invisible because RR looks "normal-ish" again. **This is an
open issue, not a closed postmortem.**

**Severity: HIGH** on 31 July (RR 60.4% → 22.5% on CUSTOM, a 63% relative fall);
**MEDIUM and ongoing** thereafter.

> **How this was found — and why the earlier passes missed it.** Passes 1 and 2 narrowed
> correctly to "the brand-filtered leg" and then concluded a per-brand count was
> *structurally impossible*, having swept all 43 configs and found none pairing a brand
> attribute with a request metric. That was the wrong boundary: no **report** exposes
> `f_brands`, but the column sits in
> `prj-onlinesales-prod-01.reporting_mumbai.os_product_ads_request_report` and `bq` is
> installed and authenticated. A direct SQL `GROUP BY f_brands` answered it in one query.
> **"No report exposes X" is not "X is unknowable" — go to the source table.**

## The window correction

The ticket names Jul 16–19. Only **Jul 17–18** broke.

| Date | Requests | Responses | RR |
|---|---|---|---|
| Jul 15 | 874,715 | 603,722 | 69.02% |
| **Jul 16** | 867,673 | 595,037 | **68.58%** ← normal |
| **Jul 17** | **1,668,528** | 621,230 | **37.23%** ⚠️ |
| **Jul 18** | **1,502,830** | 596,297 | **39.68%** ⚠️ |
| **Jul 19** | 921,577 | 625,608 | **67.88%** ← recovered |
| Jul 29 | 864,985 | 564,737 | 65.29% |
| Jul 30 | 840,046 | 543,602 | 64.71% |
| **Jul 31** | **1,434,501** | 529,233 | **36.89%** ⚠️ |
| Aug 1 | 1,034,693 | 649,562 | 62.78% |
| Aug 4 | 971,444 | 620,145 | 63.84% |

`PAGE_PERFORMANCE_PLA_REPORT`, grouped by `perf_date`, Jul 1 – Aug 4. Normal band
across the month is **64.7–70.9%**.

## STEP 1 — Triage: the move is confined to CUSTOM

`PAGE_PERFORMANCE_PLA_REPORT` by `perf_page_type`, both windows in comparison mode.

| Window | Page type | Baseline Req | Current Req | Req Δ% | Baseline Resp | Current Resp | Resp Δ% | Baseline RR | Current RR |
|---|---|---|---|---|---|---|---|---|---|
| Jul 17–18 vs Jul 15–16 | **CUSTOM** | 850,317 | 2,272,226 | **+167.2%** | 526,202 | 546,761 | +3.9% | 61.88% | **24.06%** |
| Jul 16–19 vs Jul 12–15 | SEARCH | 2,910,247 | 1,816,439 | −37.6% | 2,186,806 | 1,356,287 | −38.0% | 75.14% | **74.67%** |
| Jul 31 vs Jul 30 | **CUSTOM** | 414,456 | 1,005,400 | **+142.6%** | 250,200 | 225,926 | **−9.7%** | 60.37% | **22.47%** |
| Jul 31 vs Jul 30 | SEARCH | 425,590 | 429,101 | +0.8% | 293,402 | 303,307 | +3.4% | 68.94% | **70.68%** |

**SEARCH RR is stable in both windows.** There was no marketplace-wide serving
degradation. SEARCH request volume did fall 37.6% in the July window, but at constant
RR — a separate demand-side observation, not part of this ticket.

## The decisive numbers — marginal fill on the surge

| Comparison | Δ Requests | Δ Responses | Marginal fill |
|---|---|---|---|
| Jul 17–18 vs Jul 15–16 (CUSTOM) | **+1,421,909** | **+20,559** | **1.45%** |
| Jul 31 vs Jul 30 (CUSTOM) | **+590,944** | **−24,274** | **negative** |
| Jul 17 vs Jul 16 (all pages) | +800,855 | +26,193 | 3.27% |

CUSTOM response output is a **fixed ~250k/day**, insensitive to a 2.4× swing in
request volume: 526,202 → 546,761 responses across Jul 15–16 → Jul 17–18;
250,200 → 225,926 across Jul 30 → Jul 31.

## The mechanism — brand-filtered requests (`FILTER_PRESENCE_RR_REPORT`)

This report was listed as blocked (`AUTHORING_STATUS.md:96`, "never posted to Mongo").
**It is live.** It also accepts `perf_page_type` as a *filter* even though it silently
drops requested attributes, which is what made the CUSTOM isolation below possible.

Totals reconcile **exactly** with `PAGE_PERFORMANCE_PLA_REPORT` (414,456 / 250,200 and
1,005,400 / 225,926), so these are the same rows cut a new way — not a different universe.

**CUSTOM page type, Jul 31 vs Jul 30, split on whether the request carried a `brands` filter:**

| Leg | Req Jul 30 | Req Jul 31 | Δ Req | Res Jul 30 | Res Jul 31 | Δ Res | RR Jul 30 | RR Jul 31 |
|---|---|---|---|---|---|---|---|---|
| **brands PRESENT** | 248,646 | 836,883 | **+588,237 (+236.6%)** | 90,962 | 63,793 | **−27,169** | 36.58% | **7.62%** |
| **brands ABSENT** | 165,810 | 168,517 | +2,707 (+1.6%) | 159,238 | 162,133 | +2,895 | **96.04%** | **96.21%** |
| Total CUSTOM | 414,456 | 1,005,400 | +590,944 | 250,200 | 225,926 | −24,274 | 60.37% | 22.47% |

Three findings settle the ticket:

1. **The serving path was healthy on the surface under complaint.** CUSTOM requests with
   no brand filter filled at **96.21%** on Jul 31, *above* the 96.04% baseline. A path
   filling 96% of what it can fill is not defective.
2. **99.54% of the surge was brand-filtered** — +588,237 of +590,944 — and it returned
   **negative** incremental fill (−27,169 responses). Non-brand request volume was flat
   at +1.6%.
3. **The brand leg decomposes cleanly.** Holding responses at 90,962 over the inflated
   denominator gives 90,962 / 836,883 = 10.87%. So of the 28.96pp fall in brand-filtered
   RR: **−25.71pp (88.8%) is denominator inflation**, **−3.25pp (11.2%) is real response
   loss** — and the audit log explains that remainder (next section).

**Marketplace-wide daily series** (all page types; the retained window only):

| Date | Total RR | brands-present req | brands-present RR | brands-absent RR |
|---|---|---|---|---|
| Jul 29 | 65.29% | 242,907 | 33.29% | 77.78% |
| Jul 30 | 64.71% | 256,530 | 36.36% | 77.18% |
| **Jul 31** | **36.89%** | **845,965** | **7.87%** | **78.61%** |
| Aug 1 | 62.78% | 305,122 | 28.26% | 77.21% |
| Aug 4 | 63.84% | 263,628 | 29.50% | 76.63% |

**brands-absent RR never moves** — 76.6–78.6% on every day, highest on Jul 31 itself.
brands-present request volume sits in a 243k–305k band and spikes to 846k on Jul 31
alone, then reverts. The other filter families are non-discriminating on this
marketplace: `zone` and `device` are present on 100% of requests, `storeid`, `network`,
`city` and `country` on 0%. `brands` is the only one that varies, and it carries the
entire event.

## THE ROOT CAUSE — brand `Anua` (direct BigQuery, third pass)

Query: `GROUP BY f_brands` on
`prj-onlinesales-prod-01.reporting_mumbai.os_product_ads_request_report`, `mcid =
10119611`, `f_pt = 'CUSTOM'`, IST day boundaries. Script kept at
`scratchpad/anua.sql` + `anua_series.sql`.

**Reconciliation first — this is why the result is trustworthy.** The SQL totals match
`FILTER_PRESENCE_RR_REPORT` **to the unit** on all four figures:

| Figure | SQL | Report | Match |
|---|---|---|---|
| brand-filtered req, Jul 30 | 248,646 | 248,646 | ✅ |
| brand-filtered req, Jul 31 | 836,883 | 836,883 | ✅ |
| brand-filtered res, Jul 30 | 90,962 | 90,962 | ✅ |
| brand-filtered res, Jul 31 | 63,793 | 63,793 | ✅ |

11,765 distinct `f_brands` groups. Note `f_brands` can hold a **comma-separated list**;
`Anua` alone is its own group, and the spike is specifically single-brand Anua-only
requests (47 further groups contain Anua inside a list — a negligible 1,276 → 2,330).

### The daily series — CUSTOM page type

| Date | CUSTOM req | RR | **Anua req** | Anua res | Anua % of req | **RR excl. Anua** | Δ |
|---|---|---|---|---|---|---|---|
| Jul 21 | 428,793 | 61.98% | 0 | 0 | 0.0% | 61.98% | +0.00 |
| Jul 22 | 484,514 | 66.63% | 0 | 0 | 0.0% | 66.63% | +0.00 |
| Jul 23 | 531,719 | 68.98% | 1 | 0 | 0.0% | 68.98% | +0.00 |
| Jul 24 | 470,875 | 66.96% | 1 | 0 | 0.0% | 66.96% | +0.00 |
| Jul 25 | 562,270 | 66.50% | 0 | 0 | 0.0% | 66.50% | +0.00 |
| Jul 26 | 553,157 | 63.34% | 0 | 0 | 0.0% | 63.34% | +0.00 |
| Jul 27 | 471,673 | 61.15% | 19 | 0 | 0.0% | 61.15% | +0.00 |
| Jul 28 | 477,719 | 62.58% | 299 | 0 | 0.1% | 62.62% | +0.04 |
| Jul 29 | 422,603 | 60.01% | 252 | 0 | 0.1% | 60.04% | +0.04 |
| Jul 30 | 414,456 | 60.37% | 689 | 0 | 0.2% | 60.47% | +0.10 |
| **Jul 31** | **1,005,400** | **22.47%** | **633,205** | **0** | **63.0%** | **60.70%** | **+38.23** |
| Aug 1 | 494,617 | 55.73% | 26,835 | 0 | 5.4% | 58.92% | +3.20 |
| Aug 2 | 510,063 | 59.14% | 25,385 | 0 | 5.0% | 62.24% | +3.10 |
| Aug 3 | 463,448 | 62.79% | 19,100 | 0 | 4.1% | 65.49% | +2.70 |
| Aug 4 | 461,577 | 58.32% | 19,194 | 0 | 4.2% | 60.85% | +2.53 |

**724,980 Anua requests across the window. Zero responses. Not one, on any day.**

Four things this settles:

1. **Anua is the entire 31 July event.** 689 → 633,205 = 919× in one day. Ex-Anua RR is
   60.70% vs 60.47% the day before — a 0.23pp difference. There was no RR incident; there
   was an Anua request incident.
2. **It has never been fillable.** Zero responses on all 15 days, including the 689
   requests on 30 July and the 19 on 27 July. This was broken from the first request.
3. **The ramp is visible and was ignorable-looking**: 0 → 19 (Jul 27) → 299 → 252 → 689 →
   **633,205**. A guardrail on "single brand filter with ~0% fill" would have fired on
   **28 July at 299 requests**, three days before the incident.
4. **It is still running** at ~19–27k/day and still 100% unfillable.

### Why zero fill — catalogue vs campaign

| Check | Result |
|---|---|
| Anua SKUs in tira catalogue (`oltp_merchandise_product_dimensions_10119611`, `e_brand = 'Anua'`) | **24** |
| …in any campaign's product selection (`os_product_ads_product_selection_10119611`) | **0** |
| …with `is_active = TRUE` | **0** |
| Distinct campaigns containing an Anua SKU | **0** |

Brand string matches exactly — this is **not** a mapping or normalisation bug. The products
exist and are sellable; no advertiser has bought them. So there is genuine, targeted,
measurable demand (~20k requests/day) against zero supply. **That is a sales opportunity as
much as a defect.**

### What the other brands did

Excluding Anua, requests **fell** 17.9% on 31 July (247,957 → 203,678) and RR ex-Anua went
36.68% → 31.32% — a modest decline, not a collapse. Top decliners: `Akind` 26,360 → 4,624;
`The Ordinary` 6,389 → 1,383; `Tira` 5,839 → 2,157; `Olaplex` 3,434 → 869. Worth a separate
look, but immaterial to this ticket.

## The secondary cause — lapsed brand slot bookings (`AUDIT_EVENTS_REPORT`)

Now unblocked (`AUTHORING_STATUS.md:104`) and verified on agency 576 for both windows.

At **05:30 IST on Jul 31**, seven brand slot bookings flipped ACTIVE → DELIVERED, all
with windows ending 29 July, all `changed_by_type=INTERNAL`:

| Campaign | ID | Placement |
|---|---|---|
| Wella Professional_Hair_slot2_27July-29July | 1347699 | Hair, slot 2 |
| Lakme_Makeup_slot2_25July-29July | 1347696 | Makeup, slot 2 |
| Lakme_homepage_slot2_28July-29July | 1349175 | Homepage, slot 2 |
| Bare Minerals_Too_Good_Too-Miss_29July-29July | 1349799 | Too Good Too Miss |
| Laura Mercier_Too_Good_Too-Miss_29July-29July | 1349798 | Too Good Too Miss |
| Moxie Beauty_Hair_slot1_27July-29July | 1347700 | Hair, slot 1 |
| Too Faced_homepage_wishlist_29July-29July | 1349794 | Homepage wishlist |

**No replacement was activated until 23:24 IST that night**, for 1 August windows
(`M.A.C_Makeup_slot2_1August-4August` and ten others, ACTIVE 00:04–00:17 on Aug 1). That
gap is the −27,169 brand-filtered responses, and it is why Aug 1 recovered to 62.78%.

**Supply never shrank.** Across Jul 16–19, status changes net **positive**: 72
activations (36 DRAFT→ACTIVE, 20 LAUNCH_INPROGRESS→ACTIVE, 16 PAUSED→ACTIVE) against 27
deactivations (21 pauses, 4 delivered, 2 archived), over 121 events.

**Why the bookings are not the request-surge cause.** The two events have *opposite*
campaign signatures but *identical* request signatures. Jul 17 had heavy booking activity
at the boundary — five brand slots activated 21:07–21:27 IST on Jul 16 for 17 July starts
(`Laneige_Homepage_slot2_17July-17July`, `Bobbi Brown_Tira_Red_slot2_17July-19July`,
`Estee Lauder_Makeup_slot2_17thJuly-17thJuly`, `Smashbox_Makeup_slot1_17thJuly-19thJuly`,
`Moxie Beauty_Hair_slot1_17July-19July`), plus 16 more through Jul 17. Jul 31 had the
reverse: bookings ending, none starting. Requests doubled either way. **The request-side
trigger therefore remains on TIRA's platform side** — that question is still open.

## STEP 3-A — the category drill is unrunnable on this marketplace

`RR_PLA_REPORT` by `perf_page_type` + `perf_category_l1`, Jul 31 vs Jul 30:

| Page type | category_l1 | Baseline Req | Current Req | Baseline RR | Current RR |
|---|---|---|---|---|---|
| CUSTOM | **`""` (blank)** | 414,456 | 1,005,400 | 60.37% | 22.47% |
| SEARCH | `""` (blank) | 420,990 | 424,676 | 69.16% | 70.87% |
| SEARCH | MAKEUP | 2,302 | 2,151 | 49.00% | 56.58% |
| SEARCH | SKIN | 687 | 718 | 52.26% | 55.85% |
| SEARCH | HAIR | 550 | 509 | 68.00% | 55.40% |
| SEARCH | FRAGRANCE | 536 | 487 | 43.66% | 53.39% |
| SEARCH | MEN | 275 | 226 | 24.73% | 5.75% |
| SEARCH | BATH & BODY | 180 | 240 | 50.00% | 52.08% |
| SEARCH | TOOLS & APPLIANCES | 58 | 85 | 17.24% | 24.71% |
| SEARCH | MOM & BABY | 9 | 6 | 11.11% | 0% |
| SEARCH | TIRA MERCH | 2 | 1 | 0% | 0% |
| SEARCH | WELLNESS | 1 | 2 | 0% | 0% |

**Every CUSTOM request carries a blank `category_l1`.** The SOP's mandatory
`category_l1 != ''` filter excludes all of them, so the prescribed category drill
returns zero rows. `perf_page_name` adds nothing — CUSTOM resolves to the single value
`CUSTOM`. Category-level RR attribution is **structurally impossible** for tira on this
report; see the environment-limitations section above.

## The decisive drill — hourly shape rules out budget exhaustion

`RR_PLA_REPORT` by `perf_page_type` + `perf_day` + `perf_hour`, CUSTOM only.

**Jul 31 vs Jul 30 (IST):**

| Hour | Req Jul 30 | Req Jul 31 | Req × | Resp Jul 30 | Resp Jul 31 | RR Jul 30 | RR Jul 31 |
|---|---|---|---|---|---|---|---|
| 00 | 20,296 | 42,845 | **2.11×** | 10,663 | 10,564 | 52.54% | **24.66%** |
| 01 | 14,630 | 31,183 | 2.13× | 7,945 | 7,999 | 54.31% | 25.65% |
| 02 | 9,426 | 19,130 | 2.03× | 6,068 | 5,178 | 64.38% | 27.07% |
| 03 | 4,994 | 11,258 | 2.25× | 3,112 | 3,357 | 62.31% | 29.82% |
| 04 | 4,084 | 7,527 | 1.84× | 2,594 | 2,219 | 63.52% | 29.48% |
| 05 | 3,338 | 7,792 | 2.33× | 2,098 | 2,612 | 62.85% | 33.52% |
| 06 | 6,263 | 10,688 | **1.71×** | 4,569 | 3,092 | 72.95% | 28.93% |
| 07 | 7,756 | 16,833 | 2.17× | 5,270 | 4,698 | 67.95% | 27.91% |
| 08 | 11,000 | 23,186 | 2.11× | 7,713 | 5,704 | 70.12% | 24.60% |
| 09 | 13,252 | 33,310 | 2.51× | 9,241 | 8,592 | 69.73% | 25.79% |
| 10 | 15,597 | 41,051 | 2.63× | 10,594 | 9,126 | 67.92% | 22.23% |
| 11 | 18,483 | 49,424 | 2.67× | 12,538 | 10,971 | 67.84% | 22.20% |
| 12 | 24,870 | 71,742 | 2.88× | 17,337 | 13,498 | 69.71% | 18.81% |
| 13 | 21,183 | 56,256 | 2.66× | 13,299 | 11,259 | 62.78% | 20.01% |
| 14 | 29,441 | 55,146 | 1.87× | 20,488 | 11,511 | 69.59% | 20.87% |
| 15 | 23,053 | 64,963 | 2.82× | 14,427 | 12,315 | 62.58% | 18.96% |
| 16 | 25,618 | 54,234 | 2.12× | 13,542 | 10,986 | 52.86% | 20.26% |
| 17 | 25,789 | 52,077 | 2.02× | 14,977 | 12,488 | 58.08% | 23.98% |
| 18 | 24,246 | 52,502 | 2.17× | 14,946 | 13,747 | 61.64% | 26.18% |
| 19 | 19,340 | 52,492 | 2.71× | 10,741 | 12,542 | 55.54% | 23.89% |
| 20 | 20,114 | 52,709 | 2.62× | 10,850 | 12,322 | 53.94% | 23.38% |
| 21 | 22,130 | 75,896 | **3.43×** | 11,300 | 13,592 | 51.06% | 17.91% |
| 22 | 24,687 | 62,436 | 2.53× | 12,581 | 13,375 | 50.96% | 21.42% |
| 23 | 24,866 | 60,720 | 2.44× | 13,307 | 14,179 | 53.51% | 23.35% |

**Jul 17–18** carries the same signature. RR at hour 00 on Jul 17 is **24.13%**, against
52.87% (Jul 16 h00) and 50.82% (Jul 15 h00) — already broken at midnight, and still
25.61% at hour 23 on Jul 18.

Three conclusions from this table:

1. **Budget / supply exhaustion is ruled out.** Exhaustion produces normal RR early in
   the day and a cliff once budgets burn down. Here RR is 24.66% in hour **00** and
   23.35% in hour **23** — uniformly depressed, **no taper in any hour of either event**.
2. **The request surge is uniform across all 24 hours** (1.71×–3.43×, median ~2.2×),
   including 03:00–05:00 IST when shopper traffic is at its daily floor. Genuine demand
   growth follows a diurnal curve; it does not multiply the 4am hour by 1.84× and the 9pm
   hour by 3.43× on the same day and then vanish.
3. **Response volume per hour is unchanged at its normal absolute level** — 10–14k/hour
   on both days, in every hour. The auction served the demand it always serves.

Both events begin and end on **clean day boundaries** and self-revert. That is the
fingerprint of a request-generation change on the CUSTOM placement — more slots
requested per pageview, an integration emitting duplicate requests, or a new CUSTOM
surface with no campaigns mapped to it.

## Answers to the questions asked

| Question | Answer |
|---|---|
| Why did responses not scale in coherence with requests, Jul 16–19? | **Only Jul 17–18 broke** — Jul 16 (68.58%) and Jul 19 (67.88%) are normal. On Jul 17–18, CUSTOM requests rose +167.2% while responses rose +3.9%. Of the +1,421,909 extra requests, ~20,559 were fillable (**1.45%**). Responses held at their normal ~250k/day. |
| Why did responses *reduce* on Jul 31 while requests increased? | Two effects, now separated. CUSTOM requests rose +142.6% (+590,944), of which **99.54% carried a `brands` filter**; fill on that increment was **negative**. Separately, **seven brand slot bookings lapsed at 05:30 IST** with no replacement until 23:24 — that is the −27,169 brand-filtered responses (11.2% of the brand-leg RR fall). |
| Why is the system not maintaining coherence with increased request volume? | It is. CUSTOM requests **without** a brand filter filled at **96.21%** on Jul 31 vs 96.04% on Jul 30, and SEARCH held at 68.94→70.68%. RR is responses ÷ requests, so ~588k brand-scoped requests with no eligible brand campaign halve the ratio with delivery unchanged. Arithmetic, not a serving failure. |
| Is this a platform defect? | **No.** Response output was normal on all three days, in every hour, and the non-brand-filtered fill rate was 96%+. The change is on the **request-generation** side of the CUSTOM surface. |
| What specifically was unfillable? | **Ad requests for the brand `Anua`** — 633,205 of them on 31 July, 0 responses. `brands` is the only client-sent filter that varies on this marketplace (`zone`/`device` present on 100% of requests; `storeid`/`network`/`city`/`country` on 0%), and within it a single brand carries the whole event. |
| Why can't Anua be served? | Anua has **24 SKUs in tira's catalogue** with the brand string spelled identically, but **0 in any campaign's product selection** and **0 campaigns**. No advertiser has bought Anua. Not a mapping bug — a supply gap. |
| Is it fixed? | **No.** Anua requests continue at ~19–27k/day (90,514 since 1 August), still 0% filled, still costing 2.5–3.2pp of CUSTOM RR daily. |
| Was Jul 17–18 also Anua? | **Almost certainly not.** Anua's first request was 23 July (a single one); it was still at 19/day on 27 July. Jul 17–18 predates Anua entirely and its cause is **unrecoverable** — the request log retains only 15 days, confirmed against the raw table. |

## Caveats

- **`AUDIT_EVENTS_REPORT` is no longer blocked — RESOLVED and used.** See the secondary-cause
  section. It confirms no campaign-side event explains the request surge, and supplies the
  brand-booking expiry that explains the response shortfall. It cannot show placement or
  app-side request-generation changes, which are not campaign entities.
- **Jul 17–18 is permanently unrecoverable, and was probably NOT Anua.** The source table
  `os_product_ads_request_report` retains **15 days** (clean boundary: Jul 20 empty, Jul 21
  populated — verified in raw SQL, so this is real deletion, not a report-layer limit).
  Anua's first request was a single one on 23 July, so the brand did not exist on the
  surface during the July window. Jul 17–18 shares the *shape* (CUSTOM-confined, responses
  flat, surge uniform across 24 hours, clean day boundaries) but its specific brand or
  surface can never be named. **Do not assert Anua for Jul 17–18.**
- **The 31 July diagnosis is fully measured**, not inferred — direct SQL reconciling to the
  unit against `FILTER_PRESENCE_RR_REPORT`.
- **Raw request-log reports are unavailable**, so the extra requests cannot be attributed
  to a specific slot, placement or app version from reporting alone. Naming the source
  requires TIRA's platform side.
- **`image.png` confirmed irrelevant** by the ticket owner (2026-08-05) — no scope revisit
  needed.
- **Category-level attribution is impossible** on this marketplace (blank `category_l1`
  throughout) — the diagnosis rests on page-type, filter-presence and hourly shape instead.
- **Not run:** STEP 5 merchant contribution ranking (`MERCHANT_PERFORMANCE_REPORT`);
  network/device cut (moot — `network` is absent on 100% of requests and `device` present
  on 100%, so neither discriminates). Neither changes the verdict.
- **Secondary observation, out of scope:** baseline RR has drifted from ~68–70%
  (Jul 1–12) to ~63–66% (Jul 27 – Aug 4) independently of these spikes. Flagged, not
  analysed.
- **SEARCH request volume fell 37.6%** (2,910,247 → 1,816,439) across Jul 12–15 → Jul
  16–19 at constant RR. Demand-side, unrelated to the ticket, but worth someone's
  attention.

## Actions

1. Reply to Harshita: correct the window to Jul 17–18, name the **brand-filtered request**
   mechanism, and confirm non-brand fill was 96%+ on the affected day.
2. **Ask TIRA's platform/engineering team what changed in CUSTOM brand-scoped ad-request
   generation at 00:00 IST on 17 July (reverted after 18 July) and again on 31 July.** Now
   a sharper question than before: the surge is specifically requests carrying a `brands`
   filter, 3.4× normal volume, uniform across all 24 hours. Likely candidates are a brand
   carousel rendering more slots per pageview than are booked, or a brand-scoped surface
   requesting ads for brands with no active booking. We cannot name it from reporting.
3. **Fix the booking-continuity gap.** Seven brand slot bookings lapsed at 05:30 IST on
   Jul 31 with no replacement activated until 23:24 the same night. Whether or not the
   request surge is fixed, that gap cost 27,169 responses on its own and is ours to
   control. Worth checking whether this recurs at other window boundaries.
4. Do **not** route this to advertiser budgets or bids. Response output was normal;
   raising budgets would not have moved RR.
5. **Raise a request-volume guardrail** alongside the RR alert — a day-over-day CUSTOM
   request jump >50% should fire its own alert so the next occurrence is triaged as a
   traffic-source event, not an RR regression. Better still, alert on the
   **brands-present request count**, which is the series that actually moved.
6. **Raise CUSTOM category tagging as a reporting gap** — with `category_l1` blank on all
   CUSTOM requests, no category-level RR diagnosis is possible for tira. This blocked the
   SOP's primary drill.
7. Raise against the report configs: the `perf_marketplace_client_id` filter rejection on
   `PAGE_PERFORMANCE_PLA_REPORT` / `RR_PLA_REPORT`, relaxing the documented store-bucket
   group-by requirement for `perf_hour` on `RR_PLA_REPORT`, and the four
   `FILTER_PRESENCE_RR` / `AUDIT_EVENTS` items in the environment-limitations section.
8. **Amend `debug-rr`'s SOP.** `FILTER_PRESENCE_RR_REPORT` is currently positioned as a
   late, last-resort drill ("use late, after other RR causes are ruled out"). On this
   ticket it was the single most decisive call and would have named the mechanism on turn
   one. For a Scenario A move (requests up, responses flat) it should run **early**,
   alongside the page-type triage — a request-side surge is exactly what the
   present-vs-absent split diagnoses.

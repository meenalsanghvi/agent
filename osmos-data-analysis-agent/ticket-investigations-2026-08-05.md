# Support ticket investigations — 2026-08-05

Two marketplace ad-performance tickets worked through the `debug-*` SOP skills.
All data via `run_report` against the KAM internal-performance reports
(`osmos-performance-local` MCP). Currency **INR** on ticket 1, **ZAR** on ticket 2.

| # | Ticket | Marketplace | Skill | Verdict |
|---|---|---|---|---|
| 1 | 10088009 — PLA ads not serving for "snack"/"snacks", campaign FF_Snacks | bigbasket (444) | debug-keyword-delivery | Invalid — both terms serving; mapping correct; new-campaign cold start |
| 2 | SPA Query, Seller ID 29899805 — CREA/ASHWA/TYRO not serving on "creatine"/"ashwagandha" | takealot (105) | debug-keyword-delivery | Invalid — both serving; dip caused by the seller's own weekly campaign re-creation; not outbid |

> **Pattern across both.** Neither ticket was a defect. Both were **newly created
> campaigns** judged during their ramp-up, and in both the complaint originated from
> inspecting a live ad response rather than from reporting. Ticket 2's seller has
> re-created the same campaign eight times since 2 June, restarting the ramp each time.

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

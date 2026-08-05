# Draft ticket replies — 2026-08-05

Customer-facing draft responses for the three tickets worked on 2026-08-05.
Full analysis, data tables and caveats: **`ticket-investigations-2026-08-05.md`**.

> ⚠️ **These are drafts, not sent messages.**
> - **Ticket 1** was raised **3 Aug** and the campaign started delivering **that same
>   day**. Re-check the last 48 hours before sending — if delivery has held, the reply
>   stands as written; if it has fallen away again, do not send.
> - **Ticket 1** tells the client their bid increase was **not** needed and suggests
>   reverting it. Confirm the account team is comfortable with that message first.
> - **Ticket 2** attributes the dip to the seller's own campaign re-creation. That is
>   a direct message about the seller's operating practice — route via Mayur before it
>   reaches the seller.
> - **Ticket 2's** category recommendation is a **Takealot catalogue change**, not
>   something we can action. Confirm who owns it before promising it.
> - **Ticket 3** corrects the dates Harshita reported (Jul 16–19 → **Jul 17–18**) and
>   puts a question back to TIRA's engineering side. It is **internal-facing**; if any
>   part reaches TIRA directly, have the account team review the framing first — "the
>   change is on your request side" needs care.
> - **Ticket 3** relies on an audit trail we could not read (`AUDIT_EVENTS_REPORT` is
>   blocked). The reply is written so that the request-side cause is presented as *what
>   the delivery data points to*, not as a confirmed config change. Keep it that way.
> - **Ticket 3** was analysed **without** the `image.png` attached to the ticket. Confirm
>   the chart shows marketplace-wide PLA before sending; if it shows a narrower cut, the
>   scope may need revisiting.
> - **Tickets 1 and 2:** do not add SKU-level figures from `RESPONDED_SKUS_REPORT`
>   alongside campaign-level figures — they use different denominators, and on ticket 1
>   their spend columns disagree ~60×. Category *shares* are safe to quote; absolute
>   SKU-impression counts next to campaign impressions are not.

| # | Ticket | To | Verdict in one line |
|---|---|---|---|
| 1 | 10088009 — PLA ads not serving, FF_Snacks | bigbasket support | Both terms serving; mapping correct; six-day new-campaign ramp |
| 2 | SPA Query, Seller ID 29899805 — CREA/ASHWA/TYRO | Tatwik, cc Mayur Rathod | Both serving; dip self-inflicted by weekly campaign re-creation; not outbid |
| 3 | TIRA — low RR despite increased Requests | Harshita Kulshreshtha (Client Growth) | Responses held normal; RR fell because **brand-filtered** CUSTOM requests tripled (99.5% of the increase) — non-brand fill was 96.2%; window is Jul 17–18, not Jul 16–19 |

---

# 1. PLA Ads Not Serving for Campaign FF_Snacks | 10088009

**To:** bigbasket · **Via:** Product Support Team
**Advertiser:** innovative retail concepts pvt ltd (1297) · **Campaign:** FF_Snacks

> Hi Team,
>
> Thank you for raising this. We have completed our investigation into the FF_Snacks campaign and the keywords "snack" and "snacks". Please find our findings below.
>
> **1. There is no issue with the category-keyword mapping. No mapping change is required.**
>
> We verified this directly from serving data rather than from configuration. All **nine SKUs** in the campaign sit in **Gourmet-World-Food > Snacks-Dry-Fruits-Nuts > Healthy-Baked-Snacks** — the category you asked us to check — and all nine are in stock. Every one of them is being served on both "snack" and "snacks" through the **targeted-keyword path**, which is the path that only opens when the keyword is correctly mapped to the product's category. If the mapping were broken, none of them could serve at all.
>
> We would also note that on the search term "snack", within this category, **bb Gooddiet is currently the only advertiser reaching shoppers through that targeted path.** Competing brands in the same category are appearing only through a lower-priority relevance match.
>
> **2. The campaign is now serving on both keywords — and serving strongly.**
>
> Over 3–4 August the campaign delivered:
>
> | Search term | Impressions | Clicks | Spend | Top-of-search share |
> |---|---|---|---|---|
> | snacks | 10,823 | 280 | INR 18,118.40 | 78.9% |
> | **snack** | **997** | **23** | **INR 1,689.60** | **80.7%** |
> | **Total** | **11,820** | **303** | **INR 19,808.00** | **79.0%** |
>
> Roughly **four out of five of the campaign's ads are appearing in a top-of-search slot**, and the campaign returned approximately **INR 233,000 in attributed sales** against INR 19,808 of spend over those two days. This is one of the stronger delivery profiles we would expect to see on a generic head term.
>
> **One point worth explaining, because it is the likely source of the report.** If you are looking at a keyword-level report, the row for **"snack" will appear empty**. That is a reporting artefact, not a delivery gap: our system matches the shopper query *"snack"* to the campaign's *"snacks"* keyword, so those 997 impressions and INR 1,689.60 of spend are all attributed to the **"snacks"** row. The singular term is being served; it is simply not reported under its own line.
>
> **3. What actually caused the quiet period.**
>
> The concern was valid at the time it was raised. **FF_Snacks was created on 28 July**, and across its first six days (28 July – 2 August) it recorded only 21 impressions in total. Delivery began in earnest on **3 August** — the same day this ticket was raised — and has been strong since.
>
> This is normal behaviour for a newly created campaign. Our system needs a short ramp-up period to establish where a new campaign competes effectively, and generic high-volume terms like "snacks" typically take around five to seven days to reach steady delivery. We would recommend allowing that window before escalating on a new campaign.
>
> **4. On the bid increases — these were not the constraint, and we suggest reverting them.**
>
> We want to be direct about this, as our earlier advice to raise bids was not the right recommendation.
>
> The keyword "snack" is **not a competitive auction**. Only six campaigns across the marketplace target it manually at all, and they are winning it at roughly **INR 555–689 CPM**. FF_Snacks was already transacting well above that level. The campaign was never being outbid.
>
> In addition, **FF_Snacks uses automatic CPM bidding**, so the system sets the effective bid at auction time. Manual per-keyword bid values act as a ceiling rather than as the operative bid, which is why raising them produced no visible change.
>
> **Our recommendation is to revert the bid increase made around 3 August and re-measure over the following week.** Delivery is unlikely to be affected, and the campaign should become more cost-efficient.
>
> **5. Two optional suggestions for the brand.**
>
> - **"snack" can be removed as a separate targeted keyword.** It is fully covered by "snacks", and keeping it will continue to show a zero row in reporting for the reason explained above.
> - **Search demand is heavily concentrated in the plural.** "snacks" receives roughly 152,800 shopper searches a week against 38,500 for "snack" — about four times the volume — so the plural is where the opportunity sits. The category is also a specialist one: healthy baked snacks account for around 3.5% of ad impressions on these terms, with namkeen and chips taking the large majority. If the brand wants materially more volume, broadening the product selection beyond the current nine SKUs would do more than any bid change.
>
> **Summary:** the category-keyword mapping is correct and requires no change, both search terms are serving, and the campaign is currently performing well. The quiet period was a new-campaign ramp-up that has since resolved.
>
> Please let us know if the brand would like us to walk through the delivery data, or if you would like help reviewing the product selection.
>
> Best Regards,
> Product Support Team

**Internal actions accompanying this reply:** advise the account team that this is
the **second ticket in three days from os_client 10092920** (see ticket 3,
`ticket-replies-2026-08-03.md`) raised from a live-SERP observation rather than
reporting — a short explainer to the advertiser on why a single search-page check is
not evidence of non-delivery would likely prevent a third. Separately, raise the
`CAMPAIGN_KEYWORDS_REPORT` `perf_is_negative` filter bug and the
`RESPONDED_SKUS_REPORT` spend-unit discrepancy against the report configs.

---

# 2. SPA Query || Seller ID: 29899805 | Takealot

**To:** Tatwik · **Cc:** Mayur Rathod · **Via:** Product Support Team
**Campaign:** CREA, ASHWA, TYRO (22 Jul | 11:04) · **Seller:** 29899805

> Hi Tatwik,
>
> Thank you for the detail in your report — the ad request URLs and the competing seller IDs made this much quicker to investigate. We have completed our analysis of the CREA, ASHWA, TYRO campaign for Seller ID 29899805. Our findings are below, and the headline is different from what the ad response suggested.
>
> **1. The campaign has been serving on both keywords throughout, including during the period reported.**
>
> Both "creatine" and "ashwagandha" delivered impressions in every period we examined, on both exact and phrase match:
>
> | Period | Keyword | Impressions | Clicks | Spend (ZAR) | Impressions/day |
> |---|---|---|---|---|---|
> | 16–21 Jul | creatine | 857 | 35 | 431.08 | 142.8 |
> | 16–21 Jul | ashwagandha | 828 | 19 | 291.93 | 138.0 |
> | **22–27 Jul** | creatine | 490 | 11 | 111.26 | **81.7** |
> | **22–27 Jul** | ashwagandha | 552 | 8 | 87.40 | **92.0** |
> | **28 Jul – 4 Aug** | creatine | **2,353** | 32 | 416.39 | **294.1** |
> | **28 Jul – 4 Aug** | ashwagandha | **1,127** | 18 | 205.09 | **140.9** |
>
> **Creatine is now delivering at more than double its pre-ticket rate**, and ashwagandha has returned to its previous level.
>
> A single ad request returns only a small number of sponsored slots, drawn from a large pool of eligible sellers. Checking one response — particularly with a test user ID, as in the URLs shared — will show a handful of sellers and cannot establish that a seller is excluded. The seller was competing in those auctions throughout.
>
> **2. The seller is not being outbid. They are winning well below their own bid.**
>
> | Keyword | Their bid | Actual CPC paid | Share of bid paid |
> |---|---|---|---|
> | creatine | ZAR 30.47 | **ZAR 13.01** | 42.7% |
> | ashwagandha | ZAR 20.50 | **ZAR 11.39** | 55.6% |
>
> Paying well under your bid is what winning an auction comfortably looks like — the price is set by the next-best competitor, not by your own bid. Their realised cost per click also sits in the same range as the competing bids you quoted (10 and 16.5), rather than below them. **Raising bids further will not increase delivery here and will only increase cost.**
>
> **3. There was a genuine dip before the ticket — and the cause is on the seller's side.**
>
> Delivery did fall in 22–27 July, by roughly 43% per day on creatine and 33% on ashwagandha. The reason is that the campaign running until 21 July was archived and **a new campaign was created on 22 July**.
>
> This is a recurring pattern. The seller has created and archived essentially the same campaign **eight times since 2 June**:
>
> | Created | Campaign | Status |
> |---|---|---|
> | 2 Jun | Ashwagandha & Tyrosine | Archived |
> | 6 Jun | Ashwa, tyrosine | Archived |
> | 10 Jun | ASHWA, TYRSOINE | Archived |
> | 24 Jun | Ashwa and Tyrosine | Archived |
> | 2 Jul | ashwa, tyrosine | Archived |
> | 11 Jul | ashwa tyrosine | Archived |
> | 15 Jul | Crea, Ashwa, Tyrosine | Archived |
> | **22 Jul** | **CREA, ASHWA, TYRO** | **Active** |
>
> This campaign uses Smart Shopping, which needs a short learning period to establish where it competes effectively. **Every new campaign restarts that period from zero.** By re-creating the campaign roughly weekly, the seller has been resetting their own delivery each time — and the drop reported here is that reset, not a platform issue.
>
> **Our strongest recommendation is that the seller stop re-creating this campaign and instead edit the existing one.** This is the single largest factor in their delivery that is within their control.
>
> **4. On the category question — the mapping is correct, but you have identified something real.**
>
> The keyword-to-category mapping is working correctly for both of the seller's categories. Both are actively receiving ads through the targeted-keyword path on both keywords, which only happens when the mapping is in place. **No mapping change is required.**
>
> However, your observation about the competing sellers' categories is worth acting on — just not for the reason it first appears. The competitors you identified are not in a category the seller is shut out of. They are in the **larger** category for each search term:
>
> | Search term | Category | Share of ads served |
> |---|---|---|
> | creatine | Sports Nutrition > **Creatine** *(where R10164 sits)* | **69.7%** |
> | creatine | Sports Nutrition > **Recovery & Supplements** *(where the seller sits)* | 26.4% |
> | ashwagandha | … > **Mood & Anxiety Support** *(where M29892540 sits)* | **67.4%** |
> | ashwagandha | … > **Mind & Memory** *(where the seller sits)* | 32.5% |
>
> The seller's categories are valid and serving, but they are the **secondary** category for both terms — carrying roughly **2.6× less** available inventory on "creatine" and **2.1× less** on "ashwagandha". That is why a competitor bidding *lower* appeared in the response you sampled.
>
> **Suggested action:** if the seller's products can be listed under **Sports Nutrition > Creatine** and **Vitamins & Minerals > Mood & Anxiety Support** respectively, they would become eligible for roughly two to two-and-a-half times more of the ad inventory on these searches. Please note this is a **catalogue placement change on Takealot's side**, not an advertising setting we can adjust — we would need your team to advise the seller on the right route.
>
> **5. One further constraint worth raising with the seller.**
>
> The campaign contains only **three products**: one ashwagandha SKU, one creatine SKU and one L-tyrosine SKU. A campaign can only win slots where one of its products is a relevant answer, so a three-product campaign has a low ceiling regardless of bid or budget. Expanding the product selection would do more for delivery than any bid change.
>
> **Summary:** the campaign is serving on both keywords and is not being outbid — it is winning at roughly half its bid. The dip before the ticket was caused by the campaign being re-created on 22 July, which restarts the learning period, and delivery has since more than recovered. The two genuine opportunities are category placement and product selection.
>
> **One request back to you:** the ad request URLs shared use `cli_ubid=test` and the `/sda` path. Could you confirm the sampling method used, so we can be sure the responses examined correspond to the sponsored product placements this campaign competes for? It would help us interpret any future checks of this kind.
>
> Happy to walk through the delivery and auction data on a call.
>
> Best regards,
> Product Support Team

**Internal actions accompanying this reply:** confirm with Mayur who owns the Takealot
catalogue-placement route before the category recommendation reaches the seller; the
campaign-churn message is direct and should be positioned as coaching rather than
fault. Optional follow-up not run: the rival-side competition view (campaign IDs,
creation dates and CPCs for R10164 and M29892540) — the outbidding claim is currently
answered from our own CPC-versus-bid only. Separately, ROAS on this campaign is weak
though improving (0.82 → 0.00 → **1.60** across the three windows); worth a commercial
conversation independent of this ticket.

---

# 3. TIRA — Low RR despite increased Requests

**To:** Harshita Kulshreshtha (Client Growth) · **Via:** Product Support Team
**Marketplace:** TIRA · **Program:** PLA · **Page type:** CUSTOM
**Dates investigated:** Jul 16–19 and Jul 31, 2026

> Hi Harshita,
>
> Investigated. Short version: the system did keep serving normally on these dates — what moved was the request count, not the response count. Details below.
>
> **First, a correction on the window.** Only **17–18 July** shows the issue, not 16–19. 16 July (RR 68.6%) and 19 July (RR 67.9%) are both normal days, in line with TIRA's usual range of 64.7–70.9%. So there are three affected days in total: **17 July, 18 July and 31 July**.
>
> **1. On all three dates the drop is confined to CUSTOM pages.**
>
> SEARCH response rate was completely stable throughout — 75.1% → 74.7% across the July window, and 68.9% → 70.7% on 31 July. There was no marketplace-wide serving problem.
>
> On CUSTOM pages:
>
> | | Requests | Responses | RR |
> |---|---|---|---|
> | 15–16 Jul (normal) | 850,317 | 526,202 | 61.9% |
> | **17–18 Jul** | **2,272,226** (+167%) | **546,761** (+3.9%) | **24.1%** |
> | 30 Jul (normal) | 414,456 | 250,200 | 60.4% |
> | **31 Jul** | **1,005,400** (+143%) | **225,926** (−9.7%) | **22.5%** |
>
> **2. Responses did not fall — they stayed at their normal level.**
>
> CUSTOM delivered roughly 250,000 responses a day throughout, on the affected days and the normal ones alike. What changed is that requests more than doubled.
>
> Of the ~1.42 million extra requests on 17–18 July, only about **20,500 could be filled — 1.4%**. On 31 July the extra ~591,000 requests produced **no additional responses at all**.
>
> Because response rate is responses ÷ requests, a large volume of unfillable requests in the denominator halves the ratio even when delivery to advertisers is completely unchanged. **This is why the two figures look incoherent: the ratio moved, the delivery did not.**
>
> **3. We can now tell you exactly which requests were unfillable: brand-scoped ones.**
>
> Splitting 31 July's CUSTOM requests by whether they carried a **brand filter** — i.e. a request asking specifically for ads from a named brand — gives this:
>
> | CUSTOM requests on 31 Jul | Requests | Responses | Fill rate |
> |---|---|---|---|
> | **With** a brand filter | 836,883 (+237% vs 30 Jul) | 63,793 | **7.6%** |
> | **Without** a brand filter | 168,517 (+1.6% vs 30 Jul) | 162,133 | **96.2%** |
>
> Two things to draw from this:
>
> - **99.5% of the entire request increase was brand-filtered** — 588,237 of the 590,944 extra requests. Ordinary, unscoped request volume was essentially flat, up 1.6%.
> - **Requests without a brand filter were filled 96.2% of the time** — slightly *better* than the 96.0% we managed on 30 July. On the very surface and the very day under complaint, the system filled all but 4% of everything it was able to fill.
>
> So the picture is not "the system stopped scaling". It is that a large volume of requests arrived asking for specific brands that had no active campaign to answer them, while everything else was served almost perfectly.
>
> **4. One part of the response dip was ours, and it is a small one.**
>
> Brand-filtered responses did fall on 31 July, by 27,169. We traced this: **seven brand slot bookings reached their end date and stopped serving at 05:30 that morning** — Wella Professional, Lakme (two placements), Bare Minerals, Laura Mercier, Moxie Beauty and Too Faced — and the next set of bookings was not activated until 23:24 that night, for 1 August. That gap accounts for the fall, and it is why 1 August recovered to 62.8%.
>
> To be clear about proportion: of the 29-point fall in brand-filtered response rate, **about 89% is the request increase and about 11% is that booking gap**. We are treating the booking-continuity gap as an action on our side regardless.
>
> **5. We ruled out budget exhaustion.**
>
> This was the most likely alternative explanation, so we checked it hour by hour. Budget running out would show a normal response rate in the morning and a decline through the day as budgets burn down.
>
> That is not what happened. On 31 July, RR was already **24.7% in the midnight hour** (against 52.5% the previous day) and still **23.4% at 11pm** — uniformly low across all 24 hours, with no decline pattern. 17 July is the same: RR was 24.1% in its very first hour. Response volume per hour also held at its normal 10,000–14,000 in every hour of both days.
>
> **6. What the pattern points to.**
>
> The request increase is spread evenly across the whole clock — between 1.7× and 3.4× in every single hour, including 3–5am when real shopper traffic is at its daily minimum. Genuine demand growth does not behave that way; it follows a daily curve.
>
> Both events also start and stop cleanly at day boundaries and revert on their own, with no intervention from us.
>
> Taken together with the brand-filter split above, that points to a change in **how brand-scoped CUSTOM ad requests were being generated** on those dates — for example a brand carousel rendering more slots per page view than are booked, or a brand-scoped surface requesting ads for brands with no active booking. It does not point to anything on the response or advertiser side.
>
> We also checked our own change records for both windows. Campaign activity does not explain it: across 16–19 July there were 72 campaign activations against 27 deactivations, so live supply grew rather than shrank. And the two events have *opposite* campaign signatures — 17 July had a batch of new brand bookings going live at the boundary, 31 July had bookings ending and none starting — yet both show the same doubling of requests. Whatever drives the request volume is not on the campaign side.
>
> **7. What we need to close this out.**
>
> Could TIRA's platform team confirm whether anything changed in **brand-scoped CUSTOM ad-request generation** effective **00:00 IST on 17 July** (reverted after 18 July) and again on **31 July**? Specifically: what would cause requests carrying a brand filter to run at roughly 3.4× normal volume, evenly across all 24 hours, and then revert on a clean day boundary? That is the one question we cannot answer from reporting — we can see the requests arrive and see which of them carry a brand filter, but not which slot, placement or app version emitted them.
>
> **8. Three recommendations.**
>
> - **Alert on brand-filtered request volume, not just RR.** Because RR is a ratio, any request-volume event of this kind will always present as a response-side failure. The series that actually moved here is the brand-filtered request count — it sits in a stable 243,000–305,000 band and hit 846,000 on 31 July. An alert on that would have triaged this in minutes.
> - **Booking continuity at window boundaries.** The 05:30-to-23:24 gap on 31 July is ours. Worth checking whether the same gap recurs whenever a set of brand bookings expires.
> - **Category tagging on CUSTOM requests.** These requests currently arrive with no category attached, which meant we could not attribute the drop to any category and had to diagnose it from the filter split and hourly patterns instead. Worth fixing for future investigations.
>
> **Summary:** delivery was normal on all three days and no advertiser lost responses — requests without a brand filter were served at 96.2% on the worst day. RR fell because brand-scoped CUSTOM request volume tripled while those extra requests had no matching brand campaign to fill them. The next step sits with TIRA's platform side: confirming what changed in brand-scoped CUSTOM request generation on 17–18 and 31 July.
>
> Happy to walk through the hourly data if that would help.
>
> Best regards,
> Product Support Team

**Internal actions accompanying this reply.** The brand-filter finding is **measured for
31 July** (`FILTER_PRESENCE_RR_REPORT`, totals reconciling exactly with
`PAGE_PERFORMANCE_PLA_REPORT`) and the booking expiry is **read from the audit log**, which
came unblocked on 4 August. Both are solid.

**The one soft spot to protect if this is forwarded to TIRA:** the brand-filter mechanism
on **17–18 July is inferred, not measured** — `FILTER_PRESENCE_RR_REPORT` retains only 14
days and returns zeros for that window. The reply's sections 3 and 4 are scoped to 31 July
for exactly this reason; do not let the brand-filter numbers get restated as covering all
three days. What *is* measured for 17–18 July is the page-type confinement, the response
volume holding flat, and the flat-across-24-hours request surge — an identical signature,
which is why we believe the same mechanism applies.

Also: the booking-continuity gap in section 4 is an admission of a real 27,169-response
shortfall on our side. It is small relative to the event (11% of the brand-leg fall) and
volunteering it strengthens the rest of the message, but the account team should know it
is in there before sending.

`image.png` confirmed irrelevant by the ticket owner — no longer a caveat.

Not run and available if pushed: the merchant contribution ranking
(`MERCHANT_PERFORMANCE_REPORT`). The network/device cut is moot — `network` is absent on
100% of tira's requests and `device` present on 100%, so neither discriminates.

Separately, two observations outside this ticket: baseline RR has drifted from ~68–70%
(1–12 Jul) to ~63–66% (27 Jul – 4 Aug) independently of these spikes, and SEARCH request
volume fell 37.6% across the July window at constant RR. Both warrant their own look.

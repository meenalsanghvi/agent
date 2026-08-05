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
| 3 | TIRA — low RR despite increased Requests | Harshita Kulshreshtha (Client Growth) | **Root cause found: brand `Anua`** — 633,205 unfillable requests on 31 Jul (919× DoD, 0 responses, no Anua campaign exists). Ex-Anua RR 60.7% vs 60.5%. **Still leaking ~20k/day** + a sales opportunity |

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
> **3. Root cause on 31 July: ad requests for a single brand — Anua.**
>
> On 31 July, TIRA sent **633,205** CUSTOM ad requests filtered to the brand **Anua**, against **689** the day before. That is **919× in one day**, and it was **63% of every CUSTOM ad request** on the platform that day.
>
> **Every one of them returned zero ads.**
>
> | Date | Anua requests | Anua responses |
> |---|---|---|
> | 21–26 Jul | 0–1 | 0 |
> | 27 Jul | 19 | 0 |
> | 28 Jul | 299 | 0 |
> | 29 Jul | 252 | 0 |
> | 30 Jul | 689 | 0 |
> | **31 Jul** | **633,205** | **0** |
> | 1–4 Aug | ~19,000–27,000 / day | 0 |
>
> **Take Anua out and the incident does not exist:**
>
> | | RR as measured | RR excluding Anua |
> |---|---|---|
> | 30 Jul | 60.4% | 60.5% |
> | **31 Jul** | **22.5%** | **60.7%** |
>
> There was never a response-rate failure. There was an Anua request problem that mechanically halved a ratio.
>
> **4. Why Anua cannot be served — and it is not a spelling or mapping bug.**
>
> We checked the obvious explanation first. Anua **is** in TIRA's catalogue: **24 SKUs**, with the brand name spelled exactly as the ad request spells it. The requests are well-formed and correctly targeted.
>
> The problem is that **no advertiser on TIRA has bought Anua.** Zero of those 24 SKUs sit in any campaign — 0 active, 0 campaigns of any status. So there is nothing eligible to return. The requests were unfillable by construction, from the very first one on 23 July.
>
> **5. This is still happening, and it needs action.**
>
> Anua requests did not stop after 31 July. Since 1 August we have received **90,514** more, all unfillable — roughly 19,000–27,000 a day. That is quietly costing **2.5–3.2 percentage points of CUSTOM response rate every single day**, and it is invisible on a dashboard because the headline number looks close to normal again.
>
> There is also an opportunity here, not just a defect: this is ~20,000 daily requests of **genuine, brand-specific, measured demand** for a brand whose products are already live on TIRA. If someone sells Anua a campaign, the requests start filling and the response rate recovers on its own.
>
> **6. A smaller, separate factor on our side.**
>
> Brand-filtered responses also fell by 27,169 on 31 July because **seven brand slot bookings reached their end date and stopped serving at 05:30 that morning** — Wella Professional, Lakme (two placements), Bare Minerals, Laura Mercier, Moxie Beauty and Too Faced — with the next set not activated until 23:24 that night. That is a booking-continuity gap on our side and we are treating it as an action, though it is minor next to Anua.
>
> **7. We ruled out budget exhaustion.**
>
> This was the most likely alternative explanation, so we checked it hour by hour. Budget running out would show a normal response rate in the morning and a decline through the day as budgets burn down.
>
> That is not what happened. On 31 July, RR was already **24.7% in the midnight hour** (against 52.5% the previous day) and still **23.4% at 11pm** — uniformly low across all 24 hours, with no decline pattern. 17 July is the same: RR was 24.1% in its very first hour. Response volume per hour also held at its normal 10,000–14,000 in every hour of both days.
>
> **8. What the pattern points to.**
>
> The request increase is spread evenly across the whole clock — between 1.7× and 3.4× in every single hour, including 3–5am when real shopper traffic is at its daily minimum. Genuine demand growth does not behave that way; it follows a daily curve.
>
> Both events also start and stop cleanly at day boundaries and revert on their own, with no intervention from us.
>
> Taken together with the Anua finding, that is the signature of a **request-generation change**, not a serving problem. It does not point to anything on the response or advertiser side.
>
> We also checked our own change records. Campaign activity does not explain it: across 16–19 July there were 72 campaign activations against 27 deactivations, so live supply grew rather than shrank.
>
> **9. On 17–18 July we have to be honest about a limit.**
>
> The 31 July diagnosis above is measured, brand by brand. **17–18 July is not, and cannot be.** The underlying ad-request log is kept for 15 days, so those two days have now been deleted — we verified this directly against the source table, not just our reporting layer.
>
> What we can say: 17–18 July shows the **same signature** as 31 July — confined to CUSTOM, response volume flat, request surge uniform across all 24 hours, clean start and stop at day boundaries. What we can also say is that **it was almost certainly a different brand**: Anua's first ever request was a single one on 23 July, so Anua did not exist on the surface during the July window. Please treat the Anua explanation as covering 31 July only.
>
> **10. What we need from TIRA's platform team.**
>
> Two questions, one of them now very specific:
>
> - **Why does a CUSTOM surface request ads for `Anua`** — a brand no advertiser on TIRA has bought — and what changed on **31 July** to take that from 689 requests to 633,205 in a day? It has since settled at ~20,000/day, so whatever was configured is still partly in place.
> - Separately, what changed around **00:00 IST on 17 July**, reverting after 18 July? We can no longer attribute that window ourselves.
>
> **11. Recommendations.**
>
> - **Sell Anua a campaign.** 24 Anua SKUs are already live in TIRA's catalogue and there is ~20,000 requests/day of genuine brand-specific demand with nothing to serve against it. This is the fastest fix and it makes money rather than costing it.
> - **Stop requesting ads for brands with no campaigns**, or accept the response-rate cost — currently 2.5–3.2 points of CUSTOM RR every day.
> - **Alert on any single brand filter running at near-zero fill.** On this incident that would have fired on **28 July at 299 requests**, three days before the spike. A generic request-volume alert only fires once the damage is done.
> - **Category tagging on CUSTOM requests.** These arrive with no category attached, which blocked one of our standard diagnostic paths entirely.
>
> **Summary:** there was no serving failure. On 31 July, 633,205 ad requests arrived for one brand — Anua — that no advertiser has bought, and all of them necessarily returned nothing. Excluding those requests, response rate that day was 60.7% against 60.5% the day before. The issue is still live at around 20,000 unfillable Anua requests a day, and the cleanest resolution is commercial: sell Anua.
>
> Happy to walk through the brand-level or hourly data if that would help.
>
> Best regards,
> Product Support Team

**Internal actions accompanying this reply.** The 31 July diagnosis is **fully measured** —
direct SQL `GROUP BY f_brands` on
`prj-onlinesales-prod-01.reporting_mumbai.os_product_ads_request_report`, whose totals
reconcile **to the unit** against `FILTER_PRESENCE_RR_REPORT` (248,646 / 836,883 requests,
90,962 / 63,793 responses). The catalogue-vs-campaign check is from
`oltp_merchandise_product_dimensions_10119611` and
`os_product_ads_product_selection_10119611`. The booking expiry is from
`AUDIT_EVENTS_REPORT`, unblocked 4 August. Nothing in sections 3–6 is inferred.

**The one soft spot to protect if this is forwarded to TIRA: 17–18 July is unattributable,
and Anua is NOT the explanation for it** — Anua's first request was 23 July. Section 9 says
so explicitly and deliberately. Do not let the Anua numbers get restated as covering all
three days; that would be wrong and TIRA's engineers will catch it. The 15-day retention was
verified against the raw table, so those days are genuinely deleted, not merely hidden
behind our reporting layer.

**Two judgement calls to sign off before sending:**
- The reply **leads with a commercial recommendation** (sell Anua) rather than a pure defect
  narrative. That is the honest read — ~20k/day of unmet brand demand is revenue — but it
  reframes a complaint as an opportunity, which needs the right tone from the right person.
- It **volunteers our booking-continuity gap** (section 6, 27,169 responses). Small next to
  Anua and it strengthens credibility, but it is an admission.

**Escalate the ongoing leak separately — do not let it ride on this email thread.** Anua is
still costing 2.5–3.2pp of CUSTOM RR every day and will until TIRA stops requesting it or
someone sells it.

`image.png` confirmed irrelevant by the ticket owner — no longer a caveat.

Not run and available if pushed: the merchant contribution ranking
(`MERCHANT_PERFORMANCE_REPORT`). The device/network cut **was** run and is degenerate on
tira's CUSTOM surface — `page_name` = `CUSTOM`, `device` = `default`, `network` = blank, one
row for the whole day — so nothing can be localised through them.

Separately, three observations outside this ticket: ~2.5–3.2pp of the baseline RR drift
(~68–70% in 1–12 Jul → ~63–66% in 27 Jul – 4 Aug) is Anua, the remainder being a structural
brand-coverage trend (brand-filtered fill 49.6% on 23 Jul → 29.7% on 4 Aug while non-brand
fill *rose* to 93%); SEARCH request volume fell 37.6% across the July window at constant RR;
and several brands fell sharply on 31 July independently of Anua (`Akind` 26,360 → 4,624,
`The Ordinary` 6,389 → 1,383). Each warrants its own look.

# Draft ticket replies — 2026-08-05

Customer-facing draft responses for the two tickets worked on 2026-08-05.
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
> - **Both:** do not add SKU-level figures from `RESPONDED_SKUS_REPORT` alongside
>   campaign-level figures — they use different denominators, and on ticket 1 their
>   spend columns disagree ~60×. Category *shares* are safe to quote; absolute
>   SKU-impression counts next to campaign impressions are not.

| # | Ticket | To | Verdict in one line |
|---|---|---|---|
| 1 | 10088009 — PLA ads not serving, FF_Snacks | bigbasket support | Both terms serving; mapping correct; six-day new-campaign ramp |
| 2 | SPA Query, Seller ID 29899805 — CREA/ASHWA/TYRO | Tatwik, cc Mayur Rathod | Both serving; dip self-inflicted by weekly campaign re-creation; not outbid |

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

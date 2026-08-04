# Draft ticket replies — 2026-08-03

Customer-facing draft responses for the ten tickets worked on 2026-08-03.
Full analysis, data tables and caveats: **`ticket-investigations-2026-08-03.md`**.

> ⚠️ **These are drafts, not sent messages.** Several rest on assumptions flagged in
> the investigations file — verify before sending:
> - **Ticket 3** — marketplace inferred (BigBasket from "Innovative Retail Concept Pvt. Ltd.")
> - **Ticket 8** — marketplace inferred (Apollo; ticket carried no Client List)
> - **Tickets 1, 4, 6** — items needing client confirmation are called out inside each reply
> - **Tickets 7, 8** — solution-time SLA already breached at time of writing

| # | Ticket | To | Verdict in one line |
|---|---|---|---|
| 1 | Active Campaign Not Serving Ads — vegolution (1080) | Adarsh Prasad | 4 keywords below request threshold; rest serving; self-competition |
| 2 | Apollo — Low CTR on PLA custom/category/home (#118296) | Harshita, cc Mayur | Impression dilution; no pipeline defect |
| 3 | Multiple SKUs on 'Green Tea' not serving | Adarsh Prasad | All 12 SKUs serving; mapping correct |
| 4 | Centrum Ostocalcium — keyword CPC issue | Mallika, cc Harshita | Self-competition; comparison table misread |
| 5 | FC managed Service — performance improvement | Jugraaj Singh | CUGO at target; Ashpveda budget unreachable |
| 6 | FirstCry — new/restarted campaigns spend fast | Shivam Sharda | ACCELERATED delivery; no new-campaign priority |
| 7 | #2026073189000536 — Apollo HOME RR down | Sayali, Harshita | One placement at ~2% fill; Skin Care budget-capped |
| 8 | #2026073189000689 — Category page lowest RR | Sayali Vanjari | 92.2% of requests untagged; not a fill problem |
| 9 | Tira — BU Improvement | Mayur Rathod | BU 28%; supply-constrained not budget-constrained; L2 fallback immaterial |
| 10 | Mr D Food — CTR and CPC drop | *(requester not named)* | KFC network exit + impression expansion; decline is 2 weeks old, not recent |

---

# 1. Active Campaign Not Serving Ads | vegolution-india-private-limited (1080)

**To:** Adarsh Prasad (bigbasket) · **Via:** Product Support Team

> Hi Adarsh,
>
> Thank you for your patience. We have completed our investigation into the Paratha campaign for Vegolution India Private Limited (1080) and can share the following findings.
>
> **The campaign itself is configured correctly and is active.** It is a Search-only campaign with 62 targeted keywords, no negative keywords, and it has been delivering since it went live on 13 July. Between 13 July and 2 August the campaign has recorded approximately 16,700 impressions and INR 13,900 of spend.
>
> On the specific keywords raised:
>
> **1. Keywords that cannot currently serve — "protein chapathi", "protein paratha", "protein batter" and "protein butter"**
> These search terms do not receive enough shopper traffic on the platform to qualify for ad serving. Our system requires a minimum of 100 searches over a rolling 7-day period before a keyword becomes eligible; these terms are currently receiving 32, 43, 93 and 61 searches respectively. Until search demand for them increases, they will not deliver. This is expected system behaviour and not a defect.
>
> Please also note that **"protein butter" is not among the keywords targeted on this campaign** — the campaign has **"protein batter"**. Could you confirm with the advertiser which of the two was intended?
>
> **2. Keywords that are serving — "tempeh", "tempayy", "tempe", "hello tempayy", "malabar paratha"**
> All of these are now delivering from the Paratha campaign. "Malabar paratha" has served 2,556 impressions, "tempeh" 850, "hello tempayy" 349 and "tempayy" 326 over the period.
>
> The reason delivery appeared low in the first few days is that **the advertiser is running two other active Search campaigns — "Search Only momos" and "Search Only momos KW" — which target several of the same keywords.** Only one campaign per advertiser can respond to a given search request, so these campaigns are competing with each other. On "tempeh", for example, "Search Only momos" is capturing roughly 79% of the advertiser's impressions while the Paratha campaign receives about 20%. We recommend the advertiser de-duplicate keywords across the three campaigns so that the Paratha campaign receives the traffic intended for it.
>
> **3. On bid levels**
> "Tempayy" and "Malabar Paratha" are bid at 500 and "Tempe" at 600, against 1,890 for "chapathi" — the keyword the advertiser confirmed is working. This difference closely tracks the delivery differences observed. Increasing bids on the brand keywords would improve share of available impressions.
>
> Separately, our internal team is reviewing the relevance of results shown for the advertiser's brand terms, as we have identified scope to improve how closely matched products are selected for those searches. We will update you on that item separately.
>
> Please let us know if the advertiser would like assistance restructuring the keyword coverage across the three campaigns.
>
> Best Regards,
> Product Support Team

**Internal actions accompanying this reply:** relevancy ticket for the
`ONE_WORD_KEYWORD_CATEGORY_SCORE_CACHE_V2` brand-term leak (~59% of *hello tempayy*
slots going to other advertisers); confirm "protein butter" vs "protein batter".

---

# 2. Apollo | Low CTR on PLA custom, category & home page (#118296)

**To:** Harshita Kulshreshtha · **Cc:** Mayur Rathod, Anirrudh, Nabhey

> Hi Harshita,
>
> We have completed the investigation into the Apollo PLA CTR decline. Summary below, with the full data available on request.
>
> **The CTR decline is real, but it is caused by a large increase in ad impressions, not by a fall in clicks or by any data issue.**
>
> Between March and June, PLA impressions on Apollo grew **+44.6%** (8.21M → 11.87M) while clicks grew **+7.5%** (114,688 → 123,255). CTR is clicks ÷ impressions, so it fell from 1.397% to 1.038%. On the product page specifically — the sharpest reported drop, 5% to 0.91% — **clicks actually increased 23.6%** and spend increased 37%. Advertisers on that page received more clicks in June than in March, not fewer.
>
> **On the pipeline / duplicate-events question:** we checked the impression-to-response ratio, which measures how many of our ad responses actually render as impressions. It **increased** on every affected page — product 13.8% → 98.1%, home 3.0% → 6.4%, category 14.8% → 28.2%. Duplicate impression counting would push this ratio above 100%; product page sits at 98.1%. **The impressions are genuine renders. There is no double-counting and no missed click signal.** This is consistent with the raw-events sanity check already shared.
>
> **What changed — three items needing business confirmation:**
>
> 1. **Product-page ad rendering.** In March roughly one in seven of our ad responses rendered as an impression on product pages; in June nearly all of them do. This looks like a placement or rendering change on the Apollo side and is the single largest cause. Please confirm whether product-page ad slots or rendering logic were changed around April–May.
> 2. **Catalog re-categorisation.** The category taxonomy changed materially — "Health Devices" no longer exists and "Medical Equipments & Devices" has replaced it, and a new clinical taxonomy (Cardiology, Dentistry, Orthopedics, Vaccines and others) has appeared. Merchant-to-category mappings increased by more than 100×. Please confirm the date and scope of this change.
> 3. **New TPA placement.** TPA did not exist in March and delivered 313,312 impressions and 21,694 clicks in June at **6.92% CTR** — the best-performing surface on the marketplace. Please confirm when it launched. It is improving blended CTR, not harming it.
>
> **A fourth factor is on our side of the ledger:** the advertiser mix changed. Brands that stopped spending after March were delivering 18,412 clicks at **3.96% CTR** — 16% of all March clicks. The brands that replaced them delivered 1.05M impressions at **0.61% CTR**. We are picking this up with the relevant account teams.
>
> **On "fix it":** because ad density increased, **CTR is not comparable across the March/June boundary**. We recommend tracking clicks, spend and CPC for continuity, and re-baselining CTR from June onward. The genuinely actionable items are the **home page**, where clicks did fall 34.5% with spend down 33% and which we are treating separately, and the roster gap above.
>
> Happy to walk through the page, category and merchant-level data on a call.
>
> Best regards,

---

# 3. Multiple SKUs on 'Green Tea' Keyword — Ads not serving

**To:** Adarsh Prasad (bigbasket) · **Via:** Product Support Team

> Hi Adarsh,
>
> We have completed the investigation into the "Green Tea" keyword for the FF_Green Tea campaign. Please find our findings below.
>
> **1. All 12 SKUs in the campaign are being served on the keyword "Green Tea."**
>
> Between 13 July and 2 August, every one of the campaign's 12 SKUs responded to searches for "green tea," and in all 12 cases through the targeted-keyword path — meaning they were served because the campaign targets the keyword, exactly as intended. Over this period the campaign recorded approximately 214,600 product impressions, 5,300 clicks and INR 5,830 of spend on this keyword.
>
> SKU **40092352** (emperia Tulsi Green Tea), reported as the only SKU receiving visibility, is in fact **eighth of the twelve by impression volume** — 6,968 impressions, against 44,964 for the campaign's highest-served SKU (indiSecrets Pure Tulsi Chamomile Tea).
>
> We believe the observation came from checking the live search page: a search result page carries only a small number of sponsored slots, so any single check will show one or two products. Across the full period all 12 SKUs rotate through those slots.
>
> **2. The keyword-to-category mapping is correct and requires no change.**
>
> We verified this directly from serving data. The campaign's SKUs sit across **two** categories, not one:
> - **Beverages > Tea > Tea Bags** — 9 SKUs (the indiSecrets range)
> - **Beverages > Tea > Green Tea** — 3 SKUs (the emperia range)
>
> Products from **both** categories served on the keyword through the targeted path, which confirms "Green Tea" is correctly mapped to both. **There are no mapping or relevancy constraints preventing any SKU from being eligible.**
>
> **3. Competing brands are serving on this keyword.**
>
> Contrary to the observation that no other sponsored ads appear, we recorded ads from **Girnar** (the largest competitor, ~117,700 product impressions), Organic India, Organic Tattva, Maharishi Ayurveda, Tetley, Society and Tea Culture of the World. The FF_Green Tea campaign nonetheless holds roughly **60% share of voice** on this keyword — it is the leading advertiser on "green tea," not a suppressed one.
>
> **4. One recommendation the brand may find valuable.**
>
> While the campaign is delivering well overall, its impressions are going disproportionately to its least-relevant products. The three genuine green tea SKUs are the strongest performers on this keyword but receive the fewest impressions:
>
> | SKU | Product | Impressions | CTR |
> |---|---|---|---|
> | 40270718 | emperia Tulsi, Lemon & Honey Green Tea | 248 | **9.68%** |
> | 40092352 | emperia Tulsi Green Tea | 6,968 | **7.75%** |
> | 40092351 | emperia Green Tea | 2,996 | **5.61%** |
> | 40228625 | indiSecrets Pure Tulsi Chamomile Tea | 44,964 | 1.97% |
> | 40228624 | indiSecrets Pure Tulsi Tea | 10,264 | 1.17% |
>
> Shoppers searching "green tea" engage two to eight times more with the emperia green tea products than with the tulsi and chamomile variants. The brand may wish to split the green tea SKUs into a dedicated campaign or ad group for this keyword so the traffic reaches the products customers are actually looking for. We expect a meaningful CTR and ROI improvement from that change.
>
> Please let us know if the brand would like help restructuring the campaign along these lines.
>
> Best Regards,
> Product Support Team

---

# 4. Centrum Ostocalcium — Keyword CPC issue

**To:** Mallika Maitra (Apollo Healthco) · **Cc:** Harshita Kulshreshtha

> Hi Mallika,
>
> We have investigated the CPC behaviour on the "Centrum" keyword for the HM_Apollo_Manual_OstoCal_30_Brand campaign. Our findings are below.
>
> **1. The campaign is not being outbid by competitors.**
>
> On searches for "centrum" in July, Centrum captured **47% of all ad impressions, 81% of all clicks and 93% of all ad spend**. Only four external campaigns target "centrum" manually at all, and they bid on phrase/broad match at **₹11–15 per click**. The other brands appearing on the keyword — HealthKart, Diataal, Vogue Wellness, Neuherbs — are served through automatic relevance matching, not through a keyword bid, which is a lower-priority supply path. No competitor is winning the "Centrum" keyword auction against you.
>
> **2. The comparison table in your note is measuring something different from what it appears to.**
>
> The Supradyn (₹61.40), Revital (₹64.70) and Zincovit (₹0.00) rows are not competitor bids on the keyword "Centrum". They are **your own campaign `HM_Apollo_Manual_MVM_30_Comp` bidding on those rival brand keywords** — our figures for the same campaign are ₹61.36 and ₹65.00, matching yours. So the table compares the cost of defending your own brand term against the cost of conquesting someone else's. Those are separate auctions with very different competitive intensity, and a brand's own term is normally the more contested of the two.
>
> It is also worth noting that **average CPC is an auction outcome, not a bid.** A competitor showing a low average CPC is evidence that they faced little competition, not that they bid low and beat you.
>
> **3. The actual cause: the campaign is bidding against your own campaigns.**
>
> The keyword "centrum" is targeted on EXACT match in **eight of your campaigns**, seven of which are besides OstoCal_30_Brand:
>
> - HM_Apollo_Manual_MVM_Men_50_Brand (created 7 July) — 57 clicks at ₹153.60
> - HM_Apollo_Manual_MVM_Women_50_Brand (created 13 July) — 23 clicks at ₹150.00
> - HM_Apollo_Manual_MVM_Adult_50_Brand, Omega_60_Brand, Biotin_30_Brand, J&M_10_Brand, CCM_15_Brand (all created 6 July)
>
> **Six of these were created between 6 and 13 July**, immediately before this issue was raised. Only one campaign per advertiser can respond to a given search request, so these campaigns compete with each other in the auction. Because pricing is set by the runner-up bid, and the runner-up on "centrum" is now usually one of your own campaigns bidding ₹300 or above, the clearing price is being pushed up to around ₹317 — close to your own ₹330 bid. Without this, the price would settle near the ₹11–15 that external advertisers bid.
>
> This is also why reducing the bid to ₹300 loses the placement immediately: a sibling campaign bidding above ₹300 takes the slot. The placement is moving between your own campaigns, not to a competitor.
>
> **Recommended actions**
>
> 1. **Consolidate "centrum" to a single campaign.** Decide which campaign should own the brand term and remove it from the other seven, or add it as a negative keyword there. We would expect the CPC to fall substantially once the internal competition is removed.
> 2. **Once consolidated, reduce the bid gradually** — the external competitive floor on this keyword is around ₹15, so there is considerable headroom below ₹330.
> 3. **Add supporting keywords to OstoCal_30_Brand.** It currently runs on a single keyword with 1,000 negatives, so any bid change is all-or-nothing with nothing to cushion it.
> 4. Please confirm the current status of HM_Apollo_Manual_OstoCal_30_Brand — our records show it as **PAUSED**, and we would like to know whether that was intentional.
>
> Happy to walk through the auction-level data on a call.
>
> Best Regards,
> Product Support Team

---

# 5. FC managed Service | Performance Improvement

**To:** Jugraaj Singh

> Hi Jugraaj,
>
> Thank you for sharing the post-implementation results. We have analysed both accounts at SKU and category level. Findings and recommended next steps below, with Ashpveda covered in detail as requested.
>
> ---
>
> **CUGO — already at target; the reported ROAS is understating performance**
>
> CUGO's **Sponsored Product (PLA) ROAS is 2.49**, not 1.79 — inside your 2.5–5 objective. The blended figure is being pulled down by a **Display campaign that spent ₹5,769 and generated zero orders and zero GMV** (47 clicks at ₹122.74 CPC). PLA on its own delivered ₹80,132 GMV on ₹32,158 spend, with orders up from 45 to 67 and site revenue up 73.5%.
>
> **Recommendation: pause the Display campaign and report CUGO on PLA separately.** That is an immediate ROAS improvement with no downside, and it means CUGO's optimisation should be treated as successful rather than repeated as a problem.
>
> ---
>
> **Ashpveda — the optimisations worked; the constraint is the budget target**
>
> First, the recommendations did have an effect. Every conversion metric improved:
>
> | Metric | Before | After |
> |---|---|---|
> | Click-to-order rate | 0.364% | **0.732%** (doubled) |
> | Average order value | ₹363.71 | **₹435.55** |
> | Add-to-carts | 169 | 331 |
> | Orders | 14 | 33 |
>
> ROAS still only moved 0.34 → 0.50 because of two things:
>
> **1. Cost per click rose 64%** (₹3.91 → ₹6.42) while CTR halved (0.25% → 0.13%). Spend rose 92% but bought only 17% more clicks. Impressions more than doubled — the system had to reach progressively less relevant inventory to place the budget. **The low ROAS and the low budget utilisation are the same problem: pushing more spend lowers relevance, which raises CPC, which lowers ROAS.**
>
> **2. The spend is going almost entirely to products that do not convert.** Of 115 advertised SKUs, **97 produced zero orders while consuming ₹17,542 — 60.6% of total spend.** At category level:
>
> | Category | Spend | Orders | GMV | ROAS |
> |---|---|---|---|---|
> | Lip Balm | ₹2,520 | 1 | ₹229 | **0.09** |
> | Sun Protection – Body | ₹2,059 | **0** | ₹0 | **0.00** |
> | Sun Protection – Face | ₹2,510 | 1 | ₹439 | **0.17** |
> | Shampoo | ₹3,501 | 2 | ₹846 | **0.24** |
> | Bathing Soaps | ₹4,062 | 14 | ₹4,772 | 1.17 |
> | Essential & Carrier Oils | ₹947 | 3 | ₹1,627 | **1.72** |
> | Night Cream | ₹1,332 | 4 | ₹2,248 | **1.69** |
>
> **Those four loss-making categories took 36.6% of the budget and returned ₹668 in total — a ROAS of 0.06.**
>
> **Immediate actions for Ashpveda (this week):**
> 1. **Pause** Sun Protection (both lines), Lip Balm and Shampoo — SKUs 14325810, 21064901, 21064902, 19322516, 19322486, 19322487, 19322488, 19322506, 19322507. This frees ~₹10,600 per five weeks currently returning ₹668.
> 2. **Concentrate budget on the proven winners** — handmade soaps and bath bars, night cream, carrier oils and henna hair colour: SKUs **19322504 (ROAS 5.01), 14325818 (4.44), 20665208 (3.49), 20665216 (3.29), 20665220 (2.96), 20665223 (2.03)**. These currently receive only ₹1,811 between them.
> 3. Bid down where CPC exceeds ₹7 — Ashpveda is currently paying the highest CPCs in its worst-converting categories.
>
> **On the ₹100K monthly budget — we need to flag something directly.**
>
> These actions will meaningfully improve ROAS, but they will not reach 2.5 at ₹100K per month, and we do not want to set that expectation. The arithmetic:
>
> - Restricting to every SKU that achieved ROAS ≥ 1.0 — with perfect hindsight — produces **ROAS 1.92**.
> - Restricting to SKUs above ROAS 2.0 produces **ROAS 3.33, but on only ₹1,811 of spend over five weeks** (~₹1,550/month).
> - **Ashpveda's total revenue on FirstCry across all channels was ₹19,114, against ₹28,952 of ad spend.** Ads already drive 75% of the brand's platform revenue. ROAS 2.5 on a ₹100K monthly budget would require ₹250,000 of monthly attributed GMV — roughly **15× the brand's entire current demand on FirstCry.**
>
> **Our recommendation is to reset the budget to demand rather than the reverse.** We suggest running Ashpveda at **₹20–25K per month** concentrated on the winning SKUs, where we would expect ROAS in the **1.5–2.0** range, and reviewing after four weeks. Growing the ₹100K ambition requires growing the brand's demand on FirstCry — catalogue expansion into the categories that convert (soaps, bath and body, night care), improved listings and pricing, and organic visibility — rather than more ad spend against the current assortment.
>
> We would rather tell you this now than continue optimising toward a target the account cannot reach.
>
> Happy to walk through the SKU-level data on a call, and to prepare the specific pause and reallocation list for implementation.
>
> Thanks and regards,

---

# 6. FirstCry | New/Restarted Campaigns Spend faster than Usual

**To:** Shivam Sharda

> Hi Shivam,
>
> We have investigated the Nua Maternity Oct campaign and the wider concern about new and restarted campaigns. Findings below.
>
> **1. The cause is a campaign setting, not platform behaviour.**
>
> The Maternity Oct campaign (ID 919802) is configured for **ACCELERATED budget delivery**. This setting instructs the system to spend the daily budget as quickly as possible, with no pacing across the day. The alternative setting, **STANDARD**, spreads spend across the day's pacing buckets.
>
> Spending ₹10,000 in four hours is therefore the expected, designed behaviour of this campaign — not a defect, and not the result of the auction favouring it. Nua's other maternity campaign (ID 1019332) is also set to ACCELERATED, so this appears to be a setup pattern on the account.
>
> **2. We are not prioritising newly created campaigns — the data shows the opposite.**
>
> To test this directly, we sampled 120 active campaigns across FirstCry, grouped by how recently they were created:
>
> | Campaign cohort | Sampled | ACCELERATED | STANDARD | % Accelerated |
> |---|---|---|---|---|
> | Oldest | 40 | 28 | 12 | **70%** |
> | Middle | 40 | 25 | 15 | **62.5%** |
> | **Newest** | 40 | **0** | **40** | **0%** |
>
> **Every one of the 40 most recently created campaigns is on STANDARD (paced) delivery. None is ACCELERATED.** If the platform were prioritising new campaigns to spend early, new campaigns would be the fast spenders. They are in fact the most conservatively paced group on the marketplace.
>
> What the data shows instead is a change in the default over time: campaigns created earlier were commonly set to ACCELERATED, whereas campaigns created recently are all being set up as STANDARD.
>
> **3. This also explains the "restarted campaigns" observation.**
>
> Importantly, **Maternity Oct is not a new campaign** — it is one of the oldest campaigns running on FirstCry. It was restarted, not created.
>
> That is the key to the pattern the FirstCry team noticed. Campaigns being restarted are by definition older campaigns, and older campaigns are exactly the group carrying the legacy ACCELERATED setting. While a wallet is empty the campaign cannot serve; the moment it is topped up, an ACCELERATED campaign resumes and immediately spends at its maximum rate rather than easing back in.
>
> So the correlation between *restarting* and *rapid spend* is real, but the cause is the delivery-mode setting on those older campaigns — not preferential treatment of restarted campaigns in the auction. No bid advantage or serving priority is involved.
>
> **Recommended actions**
>
> 1. **Switch Maternity Oct (and Nua's campaign 1019332) to STANDARD delivery.** This will spread spend across the day instead of exhausting the budget in the first few hours. This is the direct fix for the reported issue.
> 2. **Run an account-hygiene review across FirstCry advertisers.** Roughly 70% of the oldest campaigns are still on ACCELERATED. Any of them will show this same behaviour whenever their wallet is topped up. Converting the ones where burst spending is not intended will prevent this recurring across other brands.
> 3. Where advertisers do want to capture traffic quickly after a top-up, ACCELERATED remains the correct setting — it simply needs to be a deliberate choice rather than an inherited default.
>
> **What we could not verify**
>
> Our audit-event reporting is currently unavailable, so we could not retrieve the exact wallet top-up timestamp or any same-day budget edit to correlate against the spend burst. If you can share the top-up time from the wallet logs, we can confirm the minute-level correlation. Campaign ages above are derived from campaign creation order rather than exact dates, for the same reason.
>
> If you would still like the category-level comparison — other Maternity campaigns' spend behaviour, request volumes and competing campaign counts on 22 July — we can run that as a follow-up, though we do not believe it is needed to explain this case.
>
> Regards,

---

# 7. #2026073189000536 | Why is Apollo home page RR down in last 2 days?

**To:** Sayali Vanjari, Harshita Kulshreshtha · ⚠️ SLA lapsed 03/08/2026 05:46

> Hi Sayali, Harshita,
>
> We have completed the investigation into the Apollo home page response rate. Findings below.
>
> **1. Confirmed — and it has largely recovered.**
>
> Home page RR was a steady 100% through 15–26 July, then fell to **87.75% (28 Jul)**, **77.66% (29 Jul)** and **73.66% (30 Jul)**. The decline actually began on **28 July**, a day earlier than reported. It has since recovered: 89.25% on 31 July, 98.92% on 1 August and 98.31% on 2 August.
>
> **2. Ad requests were unaffected — this was a fill problem.**
>
> Requests held steady (659,528 on 27 July vs 638,215 on 30 July), while responses fell 29%. Approximately **455,700 requests went unfilled** across 28–31 July.
>
> **3. The cause is one placement, not the home page as a whole.**
>
> The entire decline is attributable to the **`App Pharma CLP Skin Care`** placement, which fell from 100% fill to around **2%**. A second Skin Care placement, `Pharma Homepage Skin Care`, degraded partially to 40–65%. **Every other home page placement — Health & Nutrition, VMS, Pharma Homepage, Daily Nutrition — served at 100% throughout.**
>
> On 30 July, these two placements account for **168,075 of the 168,095 unfilled requests — 99.99%**. Because the affected placement carries roughly 40% of home page volume at peak, its collapse pulled the blended home page RR down to about 60% while everything else served perfectly.
>
> **4. The underlying reason is Skin Care budget exhaustion.**
>
> The Skin Care category is running at **exactly 100% budget utilisation** — INR 147,463.60 spent against INR 147,463.60 available across 40 campaigns and 9 merchants. **No campaigns were paused**; every one is active.
>
> This matches the daily pattern precisely: the placement served at 100% each morning, stopped mid-afternoon once budget was consumed, stayed down through the evening peak, and recovered after midnight when budgets reset. The exhaustion point moved earlier each day as traffic grew — 19:00 on 28 July, 15:00 on 29 July, 13:00 on 30 July — until the pattern stopped after 17:00 on 31 July.
>
> **5. Recommended actions**
>
> - **Increase Skin Care daily budgets.** The category is hard-capped and cannot serve beyond it. This is the direct fix.
> - **Add supply to two empty sub-categories** — *hand & feet care* (34,051 requests) and *lip care* (14,468 requests) currently have **no active campaigns at all** and are filling at about 1%.
> - **Add placement-level RR monitoring.** A placement sitting at 2% fill was invisible in the page-level view, which showed only a ~60% aggregate. Alerting at placement level would have surfaced this on 28 July rather than after the fact.
> - Please confirm what changed around **17:00 on 31 July** — if budgets were increased or campaigns added, we should make that permanent to prevent recurrence.
>
> **Commercial impact was contained**: home page spend on 29–30 July was roughly 24% below the preceding two days.
>
> Please note the solution-time SLA on this ticket lapsed on 3 August 05:46; we are updating the ticket alongside this response.
>
> Regards,

---

# 8. #2026073189000689 | Category page highest requests but lowest RR

**To:** Sayali Vanjari · ⚠️ SLA lapsed 03/08/2026 06:54 · ⚠️ marketplace inferred as Apollo

> Hi Sayali,
>
> We have investigated the category page response rate. Your observation is correct, but the cause is not what the numbers first suggest — and the fix sits mostly outside advertising.
>
> **1. Confirmed: category pages carry the most requests and the lowest fill.**
>
> Between 25 July and 2 August, category pages generated **27,546,810 ad requests — 41.6% of all requests on Apollo, more than any other page type** — and filled at **1.36%**. For comparison, search fills at 15.75% and home at ~100%.
>
> **2. The low fill is caused by untagged requests, not by a shortage of ads.**
>
> **25,412,159 of those requests — 92.2% — arrive with no page name and no category attached.** Without a category, there is nothing for the system to match against, so those requests cannot be filled by design. They contribute 92% of the volume and 0% of the responses, which is what drags the headline rate to 1.36%.
>
> We also see the literal text **`{{parent.page_name}}`** arriving as a page name on some requests. That is an unrendered template variable, which indicates the ad tag on these pages is not populating its parameters correctly.
>
> **3. When category pages are tagged correctly, they perform very well.**
>
> Excluding untagged traffic and surfaces with no advertiser supply, category pages fill at **55.6%** — better than search, product or TPA pages. Individual pages are excellent: PPLA Supplements tabular widget 98.6%, App Pharma CLP Fever Cold 99.97%, App Category Landing Page 99.4%, App Pharma CLP Baby Feeding 99.75%.
>
> **The category page is one of your strongest surfaces. It is simply that 92% of its traffic never identifies itself.**
>
> **4. A separate, smaller issue: some named pages have no advertiser supply.**
>
> About 1.46 million requests hit correctly-tagged pages that have essentially no ads available:
>
> | Page | Category | Requests | Responses |
> |---|---|---|---|
> | PPLA Healthy Snacks tabular widget | Food & Beverages | 1,065,958 | 89 |
> | PPLA Healthy India Nutrition tabular widget | Food & Beverages | 92,782 | 0 |
> | PPLA Support performance tabular widget | Ayurveda | 63,570 | 0 |
> | PPLA sexual wellness / mens sexual wellness / App Pharma CLP Sexual Wellness | Personal Care | 88,912 | 0 |
> | PPLA baby diaper clp tab widget | Baby Care | 35,321 | 98 |
> | PPLA Baby wipes Static Tab Widget | Baby Care | 14,060 | 0 |
>
> The Healthy Snacks widget alone accounts for the entire Food & Beverages gap. The three sexual wellness surfaces filling at exactly zero suggests a category eligibility or advertiser policy restriction rather than a supply shortage — we are checking that separately.
>
> **Recommended next steps**
>
> 1. **Priority — raise the tagging gap with the integration/engineering team.** Category page ad calls need to pass page name and category. This is 25.4 million requests in nine days and by far the largest monetisation opportunity on Apollo.
> 2. **Recruit supply for the Healthy Snacks and Healthy India Nutrition widgets** (Food & Beverages) — over 1.1 million requests with effectively no ads.
> 3. **Confirm whether sexual wellness surfaces are intentionally restricted.**
> 4. Note that `App Pharma CLP Health Devices` still uses the "Health Devices" category, which was retired in the June re-categorisation and replaced by "Medical Equipments & Devices" — it fills at 0% as a result. Other surfaces may be similarly stranded and are worth auditing.
>
> **Sizing the prize:** if the untagged requests were correctly identified and filled at the rate correctly-tagged pages already achieve, that is roughly **4.6 million additional ad responses** on your highest-volume surface.
>
> Please also note the solution-time SLA on this ticket lapsed on 3 August 06:54.
>
> Regards,

---

# 9. Tira | BU Improvement

**To:** Mayur Rathod · **Context:** follows a discussion with Harshita · advisory, not a regression

> Hi Mayur,
>
> Following your discussion with Harshita, we have analysed Tira's budget utilisation and response rate. Findings and recommendations below, including the category L2 fallback question.
>
> **Headline: Tira's constraint is eligible supply, not budget.**
>
> Over 20 July – 2 August, Tira's budget utilisation was **28.0%** — INR 10.76M spent against INR 38.41M of budget, leaving **INR 27.66M unspent**. Budget is 3.6× spend.
>
> Critically, **this is not a wallet problem**: of 1,876 campaigns, only **one** has a wallet balance at or below zero. Lakme holds INR 1.81M and L'Oreal Paris INR 2.35M in available funds. Advertisers have the money — their campaigns cannot reach enough inventory to spend it.
>
> **1. Improving BU**
>
> The unspent budget is heavily concentrated:
>
> | Merchant | Budget | Spend | BU% | Unspent |
> |---|---|---|---|---|
> | **Lakme** | 17,477,523 | 1,418,303 | **8.1%** | **16,059,220** |
> | L'Oreal Paris | 4,455,921 | 854,788 | 19.2% | 3,601,133 |
> | Dove | 1,795,078 | 142,363 | 7.9% | 1,652,715 |
> | SKIN1004 | 749,759 | 16,128 | 2.2% | 733,632 |
> | Nivea | 506,000 | 25,137 | 5.0% | 480,863 |
>
> **Lakme alone holds 45.5% of Tira's entire active budget and spends 8.1% of it — 54% of all unspent budget on the marketplace.** The top 15 merchants account for 88.7% of the total. Any BU programme should start here rather than spreading effort across the long tail.
>
> Recommended actions, in priority order:
> 1. **Audit Lakme's 46 campaigns** — with INR 17.5M of budget delivering 8.1%, the issue is almost certainly targeting breadth or product selection rather than money. Broadening keyword and category coverage on these campaigns is the single largest BU lever available.
> 2. **Review the 138 campaigns holding INR 15.07M that spend under 5%.** These are budgets set far above what their current targeting can deliver — either broaden targeting or right-size the budgets so BU reporting reflects reality.
> 3. **Recruit and onboard more advertisers**, particularly in categories where fill is weakest. See point 2.
>
> **2. Improving response rate**
>
> Marketplace RR is **63.95%** — 4.95 million requests go unfilled. The gap is concentrated on the **CUSTOM page**:
>
> | Page | Requests | RR | Unfilled |
> |---|---|---|---|
> | SEARCH | 6,320,942 | **71.76%** | 1,785,066 |
> | CUSTOM | 7,419,708 | **57.29%** | 3,168,641 |
>
> CUSTOM shows a clear **supply saturation pattern** — fill degrades as traffic rises:
>
> | Hour | Requests | RR |
> |---|---|---|
> | 06:00 | 53,093 | **60.77%** |
> | 12:00 | 217,945 | 47.58% |
> | 21:00 | 218,682 | **41.45%** |
>
> At four times the request volume, fill is 19 percentage points lower. The eligible advertiser pool cannot cover peak demand. **This is the same root cause as the low BU, seen from the other end** — widening eligible supply would raise fill *and* allow the existing budget to spend.
>
> Closing CUSTOM to its best observed hourly rate would add roughly **412,500 additional responses per week**.
>
> **⚠️ One urgent item we want to flag separately:** CUSTOM response rate has **fallen 15 percentage points in the last week** — from 65.04% (20–26 July) to **49.90%** (27 July – 2 August) — while requests rose 4.8%. This is a recent deterioration rather than the structural ceiling described above, and we have not yet diagnosed the cause. We recommend raising this as its own ticket; we can investigate on request.
>
> **3. Category L2 fallback**
>
> Two things here.
>
> **We cannot read the configuration.** No reporting available to us exposes platform configuration flags, so whether L2 fallback is enabled has to be confirmed by the relevancy/platform team. What we *can* observe is the behaviour, and it suggests fallback is **not** operating: sub-categories with no supply of their own return zero fill even when a sibling under the same parent fills well. For example, under BATH & BODY, "Bath & Shower" fills at 59.29% while "Shaving & Hair Removal" (63 requests), "Bathing Accessories" (33) and "Feminine Hygiene" (7) all return **0%**. The same holds under MEN. That said, this is inference from L2-versus-L1 behaviour, not proof about the L3-to-L2 path you asked about.
>
> **More importantly — the impact of enabling it would be very small.** Only **0.50% of Tira's ad requests carry a category at all** (68,337 of 13,740,650). Every other request comes from SEARCH or CUSTOM without category attribution, which is expected for keyword-driven surfaces.
>
> | Scenario | Additional responses | Marketplace RR |
> |---|---|---|
> | Today | — | 63.95% |
> | Every categorised request filled at 100% (theoretical ceiling for L2 fallback) | +32,873 | 64.19% (**+0.24pp**) |
> | CUSTOM lifted to SEARCH's fill rate | +1,089,955 | 71.88% (**+7.93pp**) |
>
> **Even a perfect outcome from L2 fallback moves marketplace response rate by about a quarter of a percentage point. Closing the CUSTOM fill gap is worth roughly 33 times more.** We would not prioritise the fallback change on BU or RR grounds — though if it is low-effort there is no reason not to enable it, and it may matter more if Tira launches category pages in future.
>
> It is also worth noting that **Tira's PLA currently serves on only two page types — Search and Custom. There is no category page.** If the question relates to category-page advertising specifically, that inventory does not exist on Tira today.
>
> **Two further observations**
>
> - **Guaranteed Display is spending INR 2.60M at ROAS 0.78**, against PLA's 3.33. It is utilising budget well but returning poorly — worth a separate commercial review.
> - **The CUSTOM surface carries no reporting attribution** — no page name, device, network or store ID on any of its 7.42M requests. We could not segment Tira's largest PLA surface at all. Adding attribution here would materially improve our ability to diagnose fill problems on it.
>
> Happy to walk through any of this, and to take the Lakme audit or the CUSTOM decline as next steps.
>
> Regards,

---

# 10. Mr D Food | Drop in CTR and CPC

**To:** *(requester not named in the ticket)* · ⚠️ scope inferred as the Mr D Food marketplace (agency 306), not a Food category
**⚠️ Revised 2026-08-04** after a 30-day non-KFC-only trend. An earlier draft attributed part of the CTR fall to KFC — that was wrong and has been corrected below.

> Hi,
>
> We have investigated the CTR and CPC movement on Mr D Food, including a 30-day trend with the KFC stores excluded to isolate the cause. Findings below.
>
> **First, a correction on timing.** This did not happen in the last few days. The decline ran from **20 to 26 July** as a gradual six-day slide, and has been stable at the new level since:
>
> | Date | Impressions | Clicks | CTR | CPC (ZAR) |
> |---|---|---|---|---|
> | 19 Jul | 30,951 | 4,873 | 15.74% | 4.59 |
> | 21 Jul | 30,435 | 3,585 | 11.78% | 4.66 |
> | 23 Jul | 43,773 | 3,330 | 7.61% | 2.96 |
> | 25 Jul | 63,462 | 3,514 | 5.54% | 2.58 |
> | 3 Aug | 39,825 | 2,056 | 5.16% | 2.91 |
>
> **The cause is that more ads are being shown per page — not the KFC campaign ending.**
>
> We tested this directly by removing every KFC store and re-running the 30-day trend on the remaining advertisers. **The decline is essentially unchanged without them:**
>
> | Week (excluding KFC) | Impressions | Clicks | **CTR** | **CPC** |
> |---|---|---|---|---|
> | 05–11 Jul | 218,129 | 37,389 | **17.14%** | 5.43 |
> | 12–18 Jul | 202,021 | 24,644 | **12.20%** | 4.69 |
> | 19–25 Jul | 294,809 | 23,428 | **7.95%** | 3.61 |
> | 26 Jul – 01 Aug | 404,260 | 20,484 | **5.07%** | 2.57 |
>
> Excluding KFC entirely, **impressions doubled (+100%) while clicks fell 17%**, taking CTR from 12.20% to 5.07% and CPC from ZAR 4.69 to 2.57. The blended marketplace figures are −68% CTR and −49% CPC — the same shape, the same timing, the same magnitude. **The rate decline is fully present with KFC removed, so KFC cannot be its cause.**
>
> **What is driving it.** The 70% impression increase breaks into three layers that all moved together around 20 July:
>
> | Layer | Change |
> |---|---|
> | Ad requests | +24.1% |
> | Fill rate (63.5% → 72.1%) | +13.5% |
> | **Impressions rendered per ad response (4.57% → 5.52%)** | **+20.8%** |
> | **Combined** | **+70.2%** |
>
> The third layer is the important one: **each ad response is now rendering about 21% more impressions — in practice, more ads displayed per page.** The additional slots sit lower on the page where users rarely click, so they convert at close to nothing. With more inventory available, competition per slot also falls, which is why CPC dropped.
>
> **The evidence this is platform-side and not an advertiser-mix effect:** of the 73 advertisers with meaningful volume who kept running across both periods, **CTR fell for 72 of them — 99%.** Merchant composition cannot make almost every individual advertiser's own click-through rate halve. Those continuing advertisers received **62% more impressions but 39% fewer clicks** — the extra impressions produced *negative* clicks, meaning even their original inventory performed worse.
>
> We also tested and ruled out a geographic expansion: the advertisers added since mid-July sit in the **same metros** as the existing roster, and the additions are chain rollouts (Debonairs went from 6 to 22 outlets) rather than new territory.
>
> **We would treat identifying the 20 July change as the priority action** — it drives the entire CTR and CPC decline and about 41% of the revenue loss.
>
> **On KFC — a clarification worth making.**
>
> KFC did **not** churn as a long-standing advertiser. The store count shows 2–3 outlets active on 5–7 July, jumping to **22 outlets on 8 July**, holding until 19 July, then tapering away across 20–22 July. This was a **12-day campaign burst that started and ended**, not an advertiser leaving.
>
> It matters commercially — KFC accounts for **ZAR 89,104 of the ZAR 151,955 revenue decline (59%)** — but the right question is whether that campaign is scheduled to return, not why a client left.
>
> **Splitting the two:**
>
> | Metric | KFC campaign ending | Impression expansion |
> |---|---|---|
> | Revenue decline | **59%** | 41% |
> | CTR / CPC decline | **none** | **all of it** |
>
> **Please note for expectation-setting:** even if every KFC store returned tomorrow, CTR would recover only to roughly **6–7%**, not the 12–17% seen before 20 July, because the additional ~200,000 impressions per week would still be there.
>
> **On CPC specifically:** the fall from ZAR 4.69 to 2.57 is *not* an efficiency gain. With roughly double the inventory available, competition per slot has dropped and the clearing price has fallen with it. Lower CPC alongside fewer clicks and less revenue is a sign of a thinner auction, not better buying.
>
> **Recommended actions**
>
> 1. **Priority — please confirm with the product/engineering team what changed around 20 July.** Specifically: was ad density, the number of ad slots per page, or a relevance threshold altered? Our reporting shows the effect clearly but does not expose the configuration itself. If ad density was deliberately increased, the trade-off needs assessing: it has produced far more impressions but fewer clicks and materially less revenue.
> 2. **Confirm whether the KFC burst campaign is scheduled to return.** This is a commercial planning question rather than a fault to fix.
> 3. **Review the 136 advertisers added since mid-July**, delivering 5.79% CTR against a 12.20% baseline. Over half of them (73) spent under ZAR 100 across five days while consuming 46,642 impressions.
> 4. Separately, **Auction Display is spending ZAR 29,850 at ROAS 0.32** — worth its own commercial review.
>
> **One reporting gap worth flagging:** Mr D's ad requests carry no store, network, device or category attribution, so we could not narrow the change to specific placements. Adding that attribution would let us diagnose issues like this directly rather than by inference.
>
> Happy to go deeper once we know what shipped on 20 July.
>
> Regards,

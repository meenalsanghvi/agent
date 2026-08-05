# Draft ticket replies — 2026-08-05

Customer-facing draft response for the ticket worked on 2026-08-05.
Full analysis, data tables and caveats: **`ticket-investigations-2026-08-05.md`**.

> ⚠️ **This is a draft, not a sent message.**
> - The ticket was raised **3 Aug** and the campaign started delivering **that same
>   day**. Re-check the last 48 hours before sending — if delivery has held, the reply
>   stands as written; if it has fallen away again, do not send.
> - The reply tells the client their bid increase was **not** needed and suggests
>   reverting it. Confirm the account team is comfortable with that message first.
> - Do **not** add SKU-level impression figures from `RESPONDED_SKUS_REPORT` to this
>   reply — they disagree with the campaign-level report on spend by ~60× and the
>   discrepancy is unresolved. The figures used below are campaign-level only.

| # | Ticket | To | Verdict in one line |
|---|---|---|---|
| 1 | 10088009 — PLA ads not serving, FF_Snacks | bigbasket support | Both terms serving; mapping correct; six-day new-campaign ramp |

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

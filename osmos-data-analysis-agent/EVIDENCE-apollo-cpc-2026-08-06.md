# The case of Apollo's falling CPC — August 2026

**The question we were asked:** *"Check apollo cpc decline from start of this month across all pages."*

**Where we looked:** apollo-hospitals-marketplace · agency 434 · client 10084549 · India, INR, Asia/Kolkata
**What we looked at:** PLA (Product Ads) only — the user chose this
**When:** 1–5 August 2026, compared against 27–31 July 2026
**Investigated:** 6 August 2026

---

## The short version

Apollo's cost-per-click fell 14% in the first week of August. That sounds like good news.

It isn't. The price of a click didn't fall. **Three big advertisers stopped buying clicks** — and
two of them stopped because they ran out of money. Their clicks were expensive ones, so when
they vanished, the *average* price fell. Everyone still advertising is paying slightly more than
before, not less.

The marketplace lost INR 61,016 in five days because of it.

---

## Chapter 1: What we were told, and what we found first

CPC means cost per click. It is a simple division:

```
CPC  =  total money spent  ÷  total clicks bought
```

That's it. Two numbers. And it's worth remembering the division, because the whole story turns
on it.

Here is what happened to Apollo's Product Ads between the last week of July and the first week
of August:

| | 27–31 July | 1–5 August | Change |
|---|---:|---:|---:|
| Money spent | INR 1,211,420 | INR 1,150,404 | **−INR 61,016 (−5.0%)** |
| Clicks bought | 24,339 | 26,900 | **+2,561 (+10.5%)** |
| Ads shown | 2,120,080 | 2,436,189 | **+316,109 (+14.9%)** |
| **CPC** | **INR 49.77** | **INR 42.77** | **−INR 7.01 (−14.1%)** |

So the decline is real. The marketplace spent less money and got more clicks. On the face of it,
Apollo got 14% better value.

**Before going further, we checked the dates were honest.** If August 5th were only a half-day
of data, the numbers would be junk. They aren't:

| Date | Spent | Clicks | CPC |
|---|---:|---:|---:|
| Jul 27 | INR 246,139 | 5,244 | 46.94 |
| Jul 28 | INR 257,271 | 5,008 | 51.37 |
| Jul 29 | INR 233,481 | 4,548 | 51.34 |
| Jul 30 | INR 239,276 | 4,763 | 50.24 |
| Jul 31 | INR 235,253 | 4,776 | 49.26 |
| Aug 1 | INR 243,215 | 5,094 | 47.75 |
| Aug 2 | INR 228,905 | 5,289 | 43.28 |
| Aug 3 | INR 225,929 | 5,405 | 41.80 |
| Aug 4 | INR 225,205 | 5,662 | 39.77 |
| Aug 5 | INR 227,150 | 5,450 | 41.68 |
| *Aug 6* | *INR 98,622* | *2,123* | *46.45* |

Every day from Aug 1 to Aug 5 is a full day, spending INR 225k–243k, right in line with July.
August 6th is clearly half-finished (INR 98,622), so **we threw it out** and used it nowhere.

One more comfort: CPC is made of spend and clicks, and neither of those numbers changes after
the fact. Sales figures keep trickling in for days after a window closes, but money spent and
clicks bought are settled the moment they happen. So the −14.1% is final. Nothing here is an
illusion caused by data still arriving.

---

## Chapter 2: The false trail

The obvious next question is *which page* got cheaper. Apollo serves ads on six kinds of page.
We pulled all six for both weeks.

| Page | CPC before | CPC after | Change |
|---|---:|---:|---:|
| CUSTOM | INR 108.72 | INR 71.39 | **−34.3%** |
| CATEGORY | INR 52.60 | INR 38.67 | **−26.5%** |
| PRODUCT | INR 44.99 | INR 38.25 | −15.0% |
| HOME | INR 62.53 | INR 55.02 | −12.0% |
| TPA | INR 43.67 | INR 38.88 | −11.0% |
| SEARCH | INR 46.00 | INR 41.35 | −10.1% |
| **All pages** | **INR 49.77** | **INR 42.77** | **−14.1%** |

Every single page got cheaper. Not one went up.

And the share each page took of the total spend barely moved — the biggest shift was CUSTOM,
down just 1.1 percentage points:

| Page | Share of spend before | Share of spend after | Share of the total decline |
|---|---:|---:|---:|
| SEARCH | 50.70% | 51.88% | 28.3% |
| TPA | 16.95% | 16.75% | 20.7% |
| CUSTOM | 13.09% | 11.95% | 34.4% |
| PRODUCT | 12.68% | 13.12% | 4.5% |
| CATEGORY | 3.77% | 3.64% | 6.2% |
| HOME | 2.81% | 2.65% | 5.8% |

Here is what that seemed to say. Every page cheaper. More ads shown (+14.9%). More clicks
bought (+10.5%). Less money spent (−5.0%). We were winning *more* auctions for *less* money,
everywhere at once.

That has an obvious explanation: **the marketplace lowered its prices**, or competition for ad
slots dropped off. We even asked the user to go and check whether the price floors had been cut
on August 1st.

**That trail was wrong.** Here is the first hint that something didn't fit.

Look again at the daily CPC in Chapter 1. If Apollo had cut its price floors on August 1st, the
CPC would **drop off a cliff on that exact date** and then sit flat at the new level. That is
what a price change looks like. Instead:

```
Jul 31   49.26
Aug 01   47.75    ↓ 1.51
Aug 02   43.28    ↓ 4.47
Aug 03   41.80    ↓ 1.48
Aug 04   39.77    ↓ 2.03
Aug 05   41.68    ↑ 1.91
```

It slides down over four days. It doesn't step. **Something was leaking away gradually, not
switching off at midnight.**

To find out what, we had to stop looking at pages and start looking at advertisers.

---

## Chapter 3: The turn — it was never about price

Think about a fruit stall selling apples at INR 20 and mangoes at INR 200. The average price of
a piece of fruit is somewhere in between, and where exactly depends on how many of each you
sell. Now suppose the mango supplier doesn't show up one morning. The average price crashes —
but **not a single price tag has changed.** You're just selling a different mix.

A marketplace CPC is exactly that kind of average. It is the price of a click *blended across
every advertiser*, weighted by how many clicks each one bought. So there are two completely
different reasons it can fall:

1. **The price genuinely dropped** — advertisers are paying less per click than they used to.
2. **The mix changed** — expensive advertisers bought fewer clicks, cheap ones bought more, and
   nobody's price moved at all.

These look identical on a page report. They demand opposite responses. So we pulled every
advertiser's numbers for both weeks and separated the two.

The method is called shift-share, and it does something simple: it asks *"what would CPC have
been if the mix had stayed exactly the same as July, and only the prices moved?"* Whatever that
leaves unexplained must be the mix.

Here is the answer.

| What caused the CPC move | Effect | As % of the old CPC |
|---|---:|---:|
| **Mix** — which advertisers bought the clicks | **−INR 7.13** | **−14.3%** |
| **Price** — what each advertiser actually paid | **+INR 0.43** | **+0.9%** |
| Overlap between the two | −INR 0.31 | −0.6% |
| **Total** | **−INR 7.01** | **−14.1%** |

Those three numbers add up to **exactly** the −INR 7.01 we measured. Nothing is missing or
fudged.

And look at the price line. It is **positive**. Had the same advertisers bought the same
proportions of clicks in August as they did in July, **CPC would have gone UP by 0.9%.**

The mix is the entire story. Prices didn't fall — they rose a little.

**Two more checks confirm it.** First, of the 56 advertisers active in both weeks, CPC fell for
only **25 of them (45%)** — and those 25 are just 36% of the money. If the marketplace had got
cheaper, nearly all 56 would have fallen. Second, we redid the whole calculation using only
those 56 (throwing out everyone who joined or left, in case they were skewing it):

```
What actually happened                             INR 49.09  →  43.18   (−12.0%)
If July's mix had held, with August's real prices             49.53     (+0.9%)
```

Same answer, from a different direction. **+0.9% on price. The rest is mix.**

---

## Chapter 4: Finding the three

If the mix changed, someone specific must have left. We ranked every advertiser by how much
they personally moved the marketplace CPC — that's simply how much their share of the clicks
changed, multiplied by how expensive their clicks were.

Three names came out on top, and they're not close.

| Advertiser | Spent before | Spent after | Their CPC before | Their CPC after | **Effect on marketplace CPC** |
|---|---:|---:|---:|---:|---:|
| **MUSCLEBLAZE** | INR 157,813 | INR 43,554 | 153.1 | 144.7 | **−INR 4.77** |
| **Horlicks** | INR 42,000 | **INR 0** | 80.0 | — stopped | **−INR 1.73** |
| **GRITZO** | INR 52,300 | INR 22,200 | 142.1 | 150.0 | **−INR 1.37** |
| | | | | **Together** | **−INR 7.87** |

The whole marketplace move was −INR 7.01. **These three account for INR 7.87 of it — 112%.**
More than all of it, because other advertisers were pushing the other way.

Now notice the two CPC columns for those three. MUSCLEBLAZE: 153 → 145. GRITZO: 142 → **150,
it went up**. Horlicks was at 80 and simply stopped. **None of them got cheaper.** They were
paying premium prices — the marketplace average was INR 49.77 — and they kept paying premium
prices right up until they stopped.

This one fact kills the competition theory. When an advertiser loses an auction war, their
automatic bidding pushes their price *up* as they fight to stay visible. Rising cost, falling
volume. What we see here is **flat cost, collapsing volume.** That isn't losing a fight. That's
walking away.

Here is the wider table, including the advertisers pulling in the opposite direction:

| Advertiser | Client ID | Spent before | Spent after | Clicks before | Clicks after | CPC before | CPC after | Effect on CPC |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| MUSCLEBLAZE | 10114538 | 157,813 | 43,554 | 1,031 | 301 | 153.1 | 144.7 | **−4.77** |
| Horlicks | 10103133 | 42,000 | 0 | 525 | 0 | 80.0 | — | **−1.73** |
| GRITZO | 10158353 | 52,300 | 22,200 | 368 | 148 | 142.1 | 150.0 | **−1.37** |
| SENSODYNE | 10161870 | 48,247 | 21,960 | 903 | 422 | 53.4 | 52.0 | −1.14 |
| Pampers | 10103163 | 88,481 | 71,305 | 1,605 | 1,285 | 55.1 | 55.5 | −1.00 |
| NEUTROGENA | 10114569 | 50,496 | 35,000 | 856 | 593 | 59.0 | 59.0 | −0.77 |
| HEALTHKART | 10129634 | 41,060 | 26,190 | 468 | 291 | 87.7 | 90.0 | −0.74 |
| Evion | 10103127 | 23,968 | 10,150 | 606 | 256 | 39.6 | 39.6 | −0.61 |
| TEDIBAR | 10114623 | 17,636 | 5,615 | 349 | 102 | 50.5 | 55.0 | −0.53 |
| *Supradyn* | 10103158 | 14,590 | 61,747 | 556 | 2,582 | 26.2 | 23.9 | *+1.92* |
| *Minimalist* | 10103141 | 0 (new) | 38,192 | 0 | 1,152 | — | 33.2 | *+1.42* |
| *Nivea* | 10103146 | 8,129 | 28,822 | 207 | 705 | 39.3 | 40.9 | *+0.70* |
| *Bepanthen* | 10157783 | 12,425 | 26,133 | 187 | 471 | 66.4 | 55.5 | *+0.65* |
| *OMNIGEL* | 10119761 | 0 (new) | 15,999 | 0 | 243 | — | 65.8 | *+0.59* |

The italic rows are advertisers who *grew*, and they push CPC back **up**. Supradyn quadrupled
its spending — but at INR 24 a click, less than a sixth of MUSCLEBLAZE's price. Minimalist is
brand new and buys at INR 33.

That is the mix shift in one sentence: **the marketplace swapped INR 145 clicks for INR 24
clicks.**

The same thing shows up in who arrived and who left:

| | How many | Money | Their average CPC |
|---|---:|---:|---|
| **Left** — Horlicks, AMRUTANJAN, Rivela, Excela, Tugain, Cipcal | 6 | INR 51,741 | **INR 72.4** — well above the INR 49.77 average |
| **Arrived** — Minimalist, OMNIGEL, Fixderma, Optimum Nutrition, APOLLO LIFE, Neuherbs, BE BODYWISE, Dabur, ODOMOS | 9 | INR 107,781 | **INR 39.1** — well below |

Expensive advertisers walked out. Cheap ones walked in. Both push the average down.

**And they didn't leave because the ads weren't working.** We checked how well each one's ads
were converting into orders:

| Advertiser | Conversion before | Conversion after |
|---|---:|---:|
| MUSCLEBLAZE | 9.5% | **14.0%** — improved |
| SENSODYNE | 71.9% | 72.5% |
| NEUTROGENA | 14.5% | 15.0% |
| HEALTHKART | 19.4% | 25.1% |
| GRITZO | 5.4% | 4.7% |

MUSCLEBLAZE's ads were converting **47% better** than in July at the moment its spending
collapsed. Nobody walked away from a losing campaign. Something else stopped them.

---

## Chapter 5: The smoking gun

So we opened up MUSCLEBLAZE — the biggest of the three, on its own responsible for 68% of the
entire CPC move.

It runs four live Product Ads campaigns, with a combined budget of **INR 37,000 a day**:

| Campaign | Status | Daily budget |
|---|---|---:|
| MB_Biozyme_PLA_KW_Feb-2026 | **ACTIVE** | INR 29,000 |
| MB_Creatine_PLA_KW_Feb-2026 | **ACTIVE** | INR 2,000 |
| MB_Pre-workout_PLA_KW_Feb-2026 | **ACTIVE** | INR 1,000 |
| MB_Biozyme_Iso_PLA_KW_Mar-2026 | **ACTIVE** | INR 5,000 |

All four are switched **on**. Nobody paused anything.

Then we pulled what those campaigns actually did, day by day:

| Date | Spent | Clicks | CPC | |
|---|---:|---:|---:|---|
| Jul 27 | INR 21,015 | 147 | 142.96 | |
| Jul 28 | INR 36,290 | 234 | 155.08 | |
| Jul 29 | INR 32,780 | 203 | 161.48 | |
| Jul 30 | INR 35,424 | 231 | 153.35 | |
| Jul 31 | INR 32,304 | 216 | 149.56 | |
| **Aug 1** | INR 35,994 | 247 | 145.72 | last normal day |
| **Aug 2** | INR 7,560 | 54 | 139.99 | **← something breaks, mid-day** |
| **Aug 3** | **INR 0** | **0** | — | **nothing** |
| **Aug 4** | **INR 0** | **0** | — | **nothing** |
| **Aug 5** | **INR 0** | **0** | — | **nothing** |

There it is. MUSCLEBLAZE was buying INR 32,000–36,000 of clicks a day like clockwork. On
August 2nd it managed INR 7,560 and then simply stopped. **Three full days of absolute zero,
with all four campaigns still switched on.**

Two details make this airtight.

**First, the price never moved.** Look down the CPC column: 143, 155, 161, 153, 150, 146, 140.
Its last two trading days were among its cheapest. This advertiser did not get outbid and did
not lower its bids. It was paying its usual price, then it wasn't paying at all.

**Second, it was hungry for more, not less.** The biggest campaign, MB_Biozyme, has a INR 29,000
daily cap — and it spent INR 28,515, INR 29,020, INR 28,515, INR 29,355, INR 28,750 on
consecutive days. **It hit its ceiling every single day.** There was more demand available than
it was allowed to buy. This is the opposite of an advertiser losing interest.

*(A note on trust: these campaign figures add up to INR 157,812.74 for July and INR 43,553.52
for August — matching the advertiser-level report to the last rupee, 157,812.74399 and
43,553.52081. Nothing is missing from this picture.)*

So: campaigns on, price steady, demand overflowing, spending zero. There is really only one
thing left it can be.

---

## Chapter 6: Out of money

We checked the wallets.

| Advertiser | Money left in wallet |
|---|---:|
| **MUSCLEBLAZE** | **INR −15.84** |
| **GRITZO** | **INR 0.00** |
| Horlicks | **INR 2,323,454** |

**MUSCLEBLAZE's wallet is empty.** In fact it's fractionally overdrawn — minus fifteen rupees
and eighty-four paise. That is exactly what a wallet looks like when it has been scraped
completely dry.

And it lines up perfectly with the daily table. The money ran out **part-way through August
2nd** — which is precisely why that day shows INR 7,560 instead of a normal INR 35,000, and why
every day after it shows zero.

That is the whole mechanism, start to finish:

> MUSCLEBLAZE's wallet emptied mid-day on August 2nd. Its four campaigns stayed switched on,
> still budgeted, still converting better than ever — but with no money behind them they simply
> stopped serving. INR 145-per-click demand vanished from the marketplace overnight, and the
> average price of a click fell because of it.

**GRITZO is the same story** — wallet at exactly zero, spending down 58%.

And that's the answer to two of the three. But look at the third row again.

---

## Chapter 7: The odd one out

**Horlicks has INR 2,323,454 sitting in its wallet — and spent nothing.**

Not "spent less". Nothing. INR 42,000 and 525 clicks in the last week of July, then across five
full days of August: **zero spend, zero clicks, 17 ad impressions.** With 2.3 million rupees
already paid in and waiting.

This is not the wallet problem. Horlicks can afford to advertise. Something else is stopping it
— a paused campaign, a campaign that hit its end date, a budget set to zero, an empty product
catalogue, products gone out of stock, or a targeting change. **We have not yet checked which.**

It matters, and not just for tidiness. Horlicks is the second-biggest cause of the CPC drop
(−INR 1.73, a quarter of the whole move), and unlike the other two it needs **no money at all**
to fix. The money is already there. Whatever is blocking it is the cheapest problem on this
page to solve.

---

## Chapter 8: What it actually cost

It is worth being blunt about this, because a falling CPC reads like a win on a dashboard.

| | |
|---|---:|
| Money the marketplace lost in five days | **−INR 61,016 (−5.0%)** |
| ...of which MUSCLEBLAZE | **−INR 114,259 (−72%)** |
| ...of which Horlicks | **−INR 42,000 (−100%)** |
| ...of which GRITZO | **−INR 30,100 (−58%)** |
| MUSCLEBLAZE's lost income, **per day, ongoing** | **~INR 31,563/day** |
| Horlicks money sitting funded and unspent | **INR 2,323,454** |

Yes, total clicks went **up** 10.5%. Supradyn and Minimalist filled the gap in volume. But they
filled it with INR 24 and INR 33 clicks instead of INR 145 clicks, so the money did not come
back. **The marketplace sold more and earned less.**

And this is not over. Every day that MUSCLEBLAZE's wallet stays empty is roughly another
**INR 31,563** not earned — from an advertiser whose campaigns are switched on, budgeted at
INR 37,000/day, hitting their caps, and converting better than they did in July.

---

## Chapter 9: What we concluded

**Apollo's cost per click did not fall. Three of its most valuable advertisers stopped buying,
and two of them stopped because their wallets ran dry.**

That is the finding. Everything below is how we know it.

**Nobody's price went down.** When we separated the two possible causes, the numbers landed at
mix **−14.3%** and price **+0.9%**. The three terms add up to the measured −INR 7.01 exactly.
Held at July's mix of advertisers, CPC would have **risen**. Two independent calculations gave
the same answer, and only 25 of 56 continuing advertisers saw any price fall at all.

**Three advertisers explain the whole thing.** MUSCLEBLAZE, Horlicks and GRITZO together moved
CPC by −INR 7.87 against a total move of −INR 7.01 — that is 112% of it. All three were paying
premium prices (INR 80 to INR 153 a click, against a marketplace average of INR 49.77). All
three saw their prices hold steady or *rise* while their volume collapsed.

**Two of them ran out of money.** MUSCLEBLAZE's wallet is at INR −15.84; GRITZO's at INR 0.00.
MUSCLEBLAZE's four campaigns are still ACTIVE, were hitting their daily budget caps every day,
and were converting 47% better than in July — right up to the moment the wallet emptied mid-day
on August 2nd. It has served nothing since.

**The third is a different problem, and we haven't solved it.** Horlicks has INR 2,323,454
funded and delivered nothing at all. That one remains open.

**It was never about price floors or competition.** Three separate facts rule that out: the
price term came out positive; the affected advertisers' own CPCs held or rose (losing an auction
makes your cost go *up*, not your volume disappear); and the daily CPC slid down over four days
rather than stepping down on August 1st the way a price change would.

**The page-level view was misleading, and we nearly followed it.** All six page types showed CPC
down 10–34%, which looks overwhelmingly like the marketplace got cheaper everywhere. It isn't.
A page's CPC is just an average across the advertisers on it — so when someone paying INR 145 a
click disappears, *every page they appeared on* gets cheaper without a single price changing.
A page report cannot tell those two apart. Only the advertiser-level split can.

**And the headline is backwards.** "CPC improved 14%" describes a marketplace that lost
INR 61,016 in five days and is still losing about INR 31,563 a day from one advertiser alone.
When these three are restored, CPC will climb back toward INR 49–50 — and that will be the
system working, not breaking.

---

## What to do about it

**Right now, to recover revenue:**

1. **Top up MUSCLEBLAZE (client 10114538).** Wallet at INR −15.84. Four ACTIVE campaigns worth
   INR 37,000/day are ready to spend the moment it's funded, and its conversion rate improved
   from 9.5% to 14.0%. This is roughly INR 31,563/day being left on the table.
2. **Top up GRITZO (client 10158353).** Wallet at INR 0.00, spending down 58%.
3. **Find out what's blocking Horlicks (client 10103133).** INR 2.32M already paid in and
   completely unspent. Check its campaign statuses, end dates, daily budgets, and product
   catalogue. This one costs nothing to fix.

**To stop it happening again:**

4. **Alert on low wallet balances for expensive advertisers.** MUSCLEBLAZE burned INR 32–36k a
   day into a wallet heading for zero, and *nothing in the campaign screens showed it* — the
   campaigns stayed ACTIVE and quietly stopped serving. Only the wallet report reveals this. An
   alert set at two or three days of spending would have caught it on July 31st, before a rupee
   was lost.
5. **Never read a marketplace CPC move without splitting mix from price.** The two look identical
   on a page report and call for opposite responses. The split takes one extra step and answers
   the question outright.
6. **Check the four other advertisers who left** — AMRUTANJAN (10160009), Rivela (10108107),
   Excela (10108111), Tugain (10108106), Cipcal (10108112) — for the same empty-wallet pattern.
   Individually small (INR 705–2,840 each), but a shared cause would not be.

**And two things NOT to do:**

7. **Don't chase price floors.** We asked for a floor check early on, before the advertiser data
   was in. It's no longer needed — the evidence now points firmly elsewhere.
8. **Don't try to "fix" the falling CPC.** Restoring these three advertisers will push CPC back
   up toward INR 49–50. That is the goal, not a regression.

---

## Honest limits of this analysis

- **We only looked at Product Ads.** Display advertising carried a further INR 665,693 in the
  same window at INR 5.36 a click. Whether the same advertisers pulled back there is unknown —
  we didn't look, because the request was scoped to PLA.
- **We never found out why Horlicks stopped.** See Chapter 7. It's the biggest open thread.
- **We stopped early, on purpose.** Category-level, sub-type and product-level breakdowns were
  available but unnecessary — the cause was pinned to specific advertisers' wallets before we
  needed them.
- **The comparison week doesn't control for month-start effects.** We compared against the five
  days immediately before (Jul 27–31). Budgets and pacing often reset on the 1st of a month, and
  this comparison can't separate that out. It doesn't change the conclusion — empty wallets are
  empty wallets — but it's worth knowing.
- **Small rounding.** Advertiser-level figures were rounded to two decimals for the maths, so
  those totals land within INR 20 (0.002%) of the page-level totals. The campaign-level figures
  in Chapter 5 were kept at full precision and match exactly.

---

## Appendix: where every number came from

All data came from Apollo's governed KAM reports, via `run_report`. No figure here is estimated
or assumed — each was measured, and all the arithmetic (differences, shares, the mix/price
split) was calculated from the raw report output.

| Report | What we used it for |
|---|---|
| `MARKETPLACE_DIRECTORY_REPORT` | Confirming the marketplace, currency and timezone |
| `PAGE_PERFORMANCE_PLA_REPORT` | Chapters 1 and 2 — page breakdown and the daily series |
| `DISPLAY_AD_UNIT_PERFORMANCE_REPORT` | Checking whether Display mattered before scoping to PLA |
| `MERCHANT_PERFORMANCE_REPORT` | Chapters 3 and 4 — every advertiser, both weeks |
| `CAMPAIGN_LOOKUP_REPORT` | Chapter 5 — MUSCLEBLAZE's campaign list and statuses |
| `INTERNAL_CAMPAIGN_PERFORMANCE_REPORT` | Chapter 5 — MUSCLEBLAZE's day-by-day delivery |
| `WALLET_BALANCE_REPORT` | Chapter 6 — the wallet balances |

Wallet balances are held in USD and converted at Apollo's factor of **73.9043678**:
MUSCLEBLAZE −USD 0.214323 → INR −15.84 · GRITZO USD 0.000025 → INR 0.00 ·
Horlicks USD 31,438.654711 → INR 2,323,453.90.

Each comparison required two separate report calls, one per week — these reports return one
period at a time, so every difference in this document was computed by hand from two labelled
results.

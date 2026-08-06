# The Case of the Falling Numbers

**An investigation into why Product Ads and Display Ads are missing their Rev/1k targets**

*NBS Tracker · JAS '26 · investigated 2026-08-06*

---

## How to read this document

This is written as a story, in order, the way the investigation actually happened — including the
places where we were wrong and had to turn around. Every claim has the number that proves it sitting
right next to it.

If you only read one section, read **Chapter 12: What We Concluded** at the end.

**One term you need.** "Revenue per 1,000 ad requests" (Rev/1k) is just a fraction:

```
            money we earned
  ───────────────────────────────────  × 1000
   number of chances to show an ad
```

An "ad request" is a moment when a shopper opens a page and the system asks *"do we have an ad for
this spot?"* It is a **chance**, not a sale. Hold onto that — the whole story turns on it.

---

## Chapter 1 — The alarm

Someone looked at the NBS tracker and saw two rows going the wrong way.

| Goal | Baseline (Jun) | Target (Sept) | Jul | Aug |
|---|---|---|---|---|
| Product Ads — Revenue / 1k ad request | $1.55 | **$2.05** | $1.39 | $1.16 |
| Display Ads — Revenue / 1k ad request | $0.437 | **$0.65** | $0.382 | $0.401 |

Both were supposed to climb. Both were falling. And Product Ads was falling *faster each month* —
first to $1.39, then to $1.16.

The obvious reading is frightening: **we are losing money.**

That reading turns out to be wrong.

---

## Chapter 2 — The first surprise, found without any data

The tracker gives us a second number for Product Ads: the ad request count. And because

```
money = Rev/1k × requests ÷ 1000
```

we can work backwards and discover how much money the tracker thinks we made — using nothing but
the screenshot.

| | Rev/1k | Requests | **⇒ money earned** |
|---|---|---|---|
| June | $1.55 | 3.92B | **$6.08M** |
| July | $1.39 | 4.51B | **$6.27M** |

Read those last two numbers again. **Revenue went up.**

The metric fell while the money rose. That is only possible if the *bottom* of the fraction grew
faster than the top. And it did: requests grew from 3.92 billion to 4.51 billion.

So the question changed completely. It was never *"why are we earning less?"* It became **"why are
we creating so many more chances to show an ad without earning more from them?"**

---

## Chapter 3 — First, prove we're looking at the right numbers

Before trusting anything, we had to reproduce the tracker's numbers ourselves from the source
database. Our first attempt did not match.

| June | Our raw data | Tracker | Gap |
|---|---|---|---|
| Requests | 4.102B | 3.92B | 4.6% |
| Rev/1k | $2.0965 | $1.55 | **35%** |

Requests were close. Money was badly off. That combination was actually useful — it told us we had
the **right table**, and the difference was in *definition*, not source.

Then came the clue that cracked it. Our data showed a **−18.1%** fall. The tracker showed
**−10.3%**. And here is the key piece of reasoning:

> **Multiplying money by any fixed number cannot change a percentage.**

If the only difference were "the tracker uses a different revenue definition," both would still show
−18.1%. They didn't. So there had to be **two** differences: a scaling factor *and* somebody missing
from the tracker's list.

We broke the data down retailer by retailer and one name jumped out.

### Purplle

| Purplle | June | July |
|---|---|---|
| Requests | 153.6M | 51.0M |
| Revenue | $1,416,941 | $468,306 |
| Earnings per 1,000 | **$9.22** | $9.18 |

Purplle earned **$9.22 per 1,000** — more than four times the company average. A retailer that
valuable collapsing would drag the average down hard, which is exactly why *our* fall was steeper
than the tracker's.

We removed Purplle and re-ran it:

| | Ours | Tracker |
|---|---|---|
| Change Jun → Jul | **−10.27%** | **−10.32%** |

### Then we proved it rather than just fitting it

Anyone can bend two dials until two numbers match. That proves nothing. So we set the scaling
factor using **June alone**, then checked whether it predicted months we hadn't touched.

| | Our figure × 0.8520 | Tracker | Error | |
|---|---|---|---|---|
| June | $1.5500 | $1.55 | — | used to set the dial |
| July | $1.3908 | $1.39 | **0.06%** | free test — passed |
| August | $1.1627 | $1.16 | **0.23%** | free test — passed |

And the request counts, which that scaling factor **cannot possibly affect**:

| | Ours | Tracker | Gap |
|---|---|---|---|
| June | 3.949B | 3.92B | 0.73% |
| July | 4.524B | 4.51B | 0.31% |

**Two dials. Four numbers reproduced. One number was used up setting a dial; the other three were
genuine tests, and all three passed.** From here on, we know our numbers are the tracker's numbers.

*(A loose end, honestly flagged: we never discovered what that 0.852 factor actually represents. We
tested and ruled out three explanations — platform margin, a different retailer list, and currency
conversion. More on this in Chapter 11.)*

---

## Chapter 4 — Where the money leaks out

Every ad request travels through four gates. Money only appears at the very end.

1. **Fill** — do we even have an ad to show?
2. **Render** — does it actually appear on screen?
3. **Click** — does the shopper click it?
4. **Price** — what does the advertiser pay for that click?

Here are all four:

| | Fill | Render | Click rate | Price per click |
|---|---|---|---|---|
| June | 47.84% | 128.26% | 1.211% | $0.2450 |
| July | 43.88% | 138.82% | 1.096% | $0.2446 |
| Aug 1–5 | 41.33% | 135.29% | 1.073% | $0.2275 |

*(Proof the four gates fully explain the metric: 0.4784 × 1.2826 × 0.01211 × 0.245 × 1000 = 1.8203,
against 1.8199 measured. They multiply out correctly, so nothing is hidden.)*

Two gates are leaking:

- **Fill fell from 48% to 41%.** We increasingly have no ad to put in the slot.
- **Click rate fell 1.211% → 1.073%.** The ads we do show get clicked less.
- **Price never moved** ($0.2450 → $0.2446).

That last line matters enormously. **Advertisers did not reduce what they pay.** So this is not a
pricing problem, and cutting prices would not fix it. We are creating ad slots that no advertiser
wants to fill and no shopper wants to click.

### The single most damning number

```
June → July:  +567 million new ad requests
              +$157,000 new revenue
              ─────────────────────────────
              $0.28 earned per 1,000 new requests
              $1.55 earned per 1,000 on the old business
```

**Every new request earns 18 cents on the dollar compared to the existing business.**

---

## Chapter 5 — The awkward discovery about the goals themselves

Look again at the Product Ads row of the tracker. It has **two** goals:

1. Revenue / 1k ad request: **$1.55 → $2.05**
2. Increase number of requests by 20%: **3.92B → 4.88B**

Now multiply the two targets together to find the revenue they jointly demand:

```
baseline money = $1.55 × 3.92B ÷ 1000 = $6.076M
target money   = $2.05 × 4.88B ÷ 1000 = $10.004M
                                         ────────
                                         +65% in one quarter (~+18% every month)
```

**Nobody wrote "+65% revenue" anywhere on that board.** But that is arithmetically what the two
goals together require.

Worse, the two goals **fight each other**. Goal 2 says *make the bottom of the fraction bigger*.
Goal 1 says *make the fraction bigger*. You can only do both if money grows even faster — and money
grew 2.8%.

*(A smaller detail: the label says "+20%" but 3.92B → 4.88B is actually **+24.5%**. The label
understates its own target.)*

---

## Chapter 6 — Two suspects

We ranked every retailer by how much it contributed to the fall.

| Retailer | Share of the fall | Requests | Revenue | Fill change | Click rate | Price |
|---|---|---|---|---|---|---|
| **Ajio** | **61%** | +7% | **−24%** | −5.2pp | −3% | **−21%** |
| **BigBasket** | **26%** | +18% | +6% | **−5.6pp** | +2% | −3% |
| Takealot | 15% | +13% | +7% | +0.4pp | **−12%** | +1% |
| Wakefern | 8% | +2% | 0% | −3.0pp | +4% | −4% |
| FirstCry | 3% | +12% | +3% | −0.8pp | **−30%** | +8% |
| Tira | **−17%** *(helped!)* | −3% | **+111%** | −4.5pp | +8% | **+46%** |

Two retailers explain **87%** of the problem. But look closely — **they are not the same problem
at all.**

- **BigBasket's revenue went UP 6%.** It grew too fast to keep up with itself.
- **Ajio's revenue went DOWN 24%.** Something actually broke.

So we investigated them separately. Also note **Tira**, which went the *other* way — revenue more
than doubled because its price per click rose 46%. Remember Tira; it matters at the end.

---

## Chapter 7 — Suspect One: BigBasket, the shop that ran out of things to sell

BigBasket added **302 million** new ad requests — more than half of all the new requests in the
entire company. Here is what happened to them.

| | June | July | |
|---|---|---|---|
| Requests (chances) | 1,655M | 1,956M | **+18.2%** |
| **Ads actually served** | **596.0M** | **593.9M** | **−0.4%** |
| **Products shown** | **2,310M** | **2,274M** | −1.6% |
| Requests that got nothing | 1,059M | 1,362M | **+28.7%** |
| Products per filled request | 3.88 | 3.83 | −1.3% |

Read the second row again. **The system served the same number of ads in July as in June.** Every
single one of those 301 million extra requests came back **empty**.

So BigBasket's fill rate didn't "decline" — the top of the fraction froze while the bottom grew:

```
596M ÷ 1,655M = 36.0%
594M ÷ 1,956M = 30.4%
```

Think of a supermarket that opens 18% more checkout lanes but receives no more stock. Same goods
sold, more empty lanes.

### And it is not about money

The obvious guess is that advertisers ran out of budget. They did not.

| | June | July |
|---|---|---|
| Advertisers | 1,008 | 1,055 |
| Advertisers **with budget available** | 914 | **961** |
| **Unspent budget sitting idle** | $47.9M | **$48.2M** |

**961 advertisers with money ready to spend, $48 million sitting unspent — and 70% of requests still
come back with nothing.** The demand exists and is paid for. It is not reaching the inventory.

### Where the growth actually went

| Ad slot | Requests | Growth | Fill | **Worth per 1,000** |
|---|---|---|---|---|
| CUSTOM/abc+default | 881 → 1,035M | **+154M** | 41.7% → 33.5% | **$0.16** |
| SEARCH/inline-search-pla_950 | 444 → 578M | **+135M** | 27.4% → 24.8% | **$0.06** |
| SEARCH/cluster_ALL/A | 114 → 140M | +26M | 24.4% → 23.8% | $7.62 |
| CATEGORY/cluster_ALL/A | 93 → 99M | +6M | 36.1% → 31.6% | $3.09 |
| SEARCH/cluster_HDLR/A | 11 → 12M | +2M | 69.2% → 61.5% | $21.17 |
| **SEARCH/cluster_HDMR/A** | **8 → 9M** | **+1M** | 72.5% → 67.2% | **$32.46** |

```
Requests added to slots worth more than $8 per 1,000:  +33M
Requests added to slots worth less than $1 per 1,000: +242M
```

**88% of the growth went into slots worth less than a dollar per thousand.** One slot,
`inline-search-pla_950`, is 578 million requests — nearly a third of BigBasket's entire volume —
earning **6 cents per thousand**. Meanwhile the genuinely valuable slot at **$32.46 per thousand**
has just 9 million requests and grew by one million.

We are pouring effort into the cheap seats and ignoring the box office.

### Why can't the ads be found? Because most campaigns are switched off.

| Campaign state | Campaigns | Keywords attached |
|---|---|---|
| Expired (end date passed) | **13,477** | 14,305 |
| Paused | **11,906** | **55,955** |
| **Draft (never launched)** | **10,434** | 6,979 |
| **Working (active)** | **4,598** | 26,885 |
| Archived / other | 6,729 | ~12,900 |

**Only 9.8% of BigBasket's campaigns can serve an ad.** And there is more than twice as much
keyword coverage sitting on *paused* campaigns (55,955) as on live ones (26,885).

The demand isn't missing. It's parked.

### The searches that come back empty

We split BigBasket's searches by how popular they are:

| Search popularity | Queries | Requests | Fill | **Empty** |
|---|---|---|---|---|
| **Most popular (10k+ each)** | **4,193** | 209.9M | **31.1%** | **144.6M** |
| Popular (1k–10k) | 26,394 | 73.1M | 22.1% | 56.9M |
| Middling (100–1k) | 166,617 | 47.0M | 14.3% | 40.3M |
| Rare (10–100) | 1.15M | 30.3M | 10.8% | 27.0M |
| One-offs (<10) | 26.2M | 47.0M | 5.6% | 44.4M |

A 5.6% fill rate on 26 million one-off searches is completely normal — nobody can plan for those.
**But 4,193 of the most popular searches filling at only 31% is not normal.** Those are the
searches people make every single day, and they hold **144.6 million empty requests — more than
three times the entire long tail.**

That is a *finite, nameable list of 4,193 things to fix*, not an impossible problem.

---

## Chapter 8 — The onion mystery

To understand *why* those popular searches come back empty, we picked the worst one.

**"onion": 976,000 searches in 15 days. Zero products served. Zero impressions. Zero revenue. Over
three entire months.** Not "low" — exactly zero.

Compare it to a search that works:

| Search | Campaigns | Merchants | Products served | Impressions | Revenue (3 months) |
|---|---|---|---|---|---|
| paneer | 63 | 22 | 10.9M | 1,407K | **$39,890** |
| milk | 33 | 20 | 14.2M | 1,372K | $20,285 |
| tomato | 21 | 12 | 360K | 79K | $752 |
| **onion** | **3** | **2** | **0** | **0** | **$0.00** |

Four merchants have "onion" set up as a keyword. We looked at every one of them:

| Merchant | Campaign state | Campaigns | Best bid | Can it serve? |
|---|---|---|---|---|
| **innovative-retail-concept-p-ltd** | **DRAFT — never launched** | 12 | **$81.19** | **No** |
| lotus-household-product | Paused | 2 | $8.12 | No |
| bizz-corporation | Expired, invalid bid | 3 | −$0.01 | No |
| colgate-palmolive-india-limited | Expired, invalid bid | 1 | −$0.01 | No |

**Not one of the 18 campaigns is in a state where it can show an ad.**

And here is the detail that stops you cold. "Innovative Retail Concepts Pvt Ltd" **is BigBasket's own
company**. It has **12 campaigns bidding up to $81.19 on onion, with $90.8 million of balance
available — all sitting in DRAFT, never switched on.** Their names are dated in sequence:

```
All Products (20th May | 12:29)     All Products (26th May | 12:21)
All Products (21st May | 12:28)     All Products (27th May | 12:21)  ← bids $81.19
All Products (22nd May | 12:19)     All Products (28th May | 16:25)
All Products (23rd May | 12:23)     All Products (5th Jun  | 12:34)
All Products (23rd May | 16:25)     All Products (11th Jun | 12:17)
All Products (26th May | 16:19)     All Products (12th Jun | 12:18)
```

Something creates a draft campaign most days at around 12:20, and nobody ever activates it.

We also found there is **no spelling forgiveness at all.** Every variant fills at 0.0%:

| Search | Requests | Responses |
|---|---|---|
| onion | 973,399 | 0 |
| onions | 44,599 | 0 |
| onin | 5,664 | 0 |
| onian | 2,365 | 0 |
| onnion | 259 | 0 |

Roughly **1.03 million requests**, and "onions" (plural!) is treated as a completely different,
unmatched search.

### But the deepest reason isn't a bug at all

We checked whether fresh produce has *any* advertisers.

| Category | Advertising merchants | Ad spend (Jul) | Shopper sales | **Ad spend as % of sales** |
|---|---|---|---|---|
| Snacks-Branded-Foods | 641 | $530,150 | $36.3M | 1.46% |
| Beauty-Hygiene | 521 | $461,818 | $23.5M | 1.97% |
| Foodgrains-Oil-Masala | 620 | $629,784 | $99.4M | 0.63% |
| **Fruits-Vegetables** | **10** | **$9,497** | **$50.0M** | **0.019%** |

**Fruits and Vegetables is BigBasket's second-biggest category — $50 million of sales a month — with
ten advertising merchants and $9,497 of ad spend.** It earns roughly one-seventy-fifth the rate of
comparable categories.

The reason is simple and cannot be engineered away: **onions have no brand.** Packaged goods have
companies competing for attention. A loose onion is sold under the shop's own label. There is no
"onion brand" with a marketing budget.

If Fruits-Vegetables earned even the modest rate that Foodgrains does, it would bring in **$317,000 a
month instead of $9,500 — a $308,000 monthly gap, about +13% on BigBasket's entire Product Ads
revenue.**

---

## Chapter 9 — Suspect Two: Ajio, where we were wrong twice

Ajio was the bigger suspect — 61% of the fall — and unlike BigBasket its **revenue genuinely dropped
24%**. Its price per click had fallen 21%. So we ran the full CPC investigation.

### What we found first

| Ajio | June | July | |
|---|---|---|---|
| Spend | INR 100,242,789 | INR 76,470,106 | **−23.7%** |
| Clicks | 13,256,744 | 12,851,139 | −3.1% |
| **Price per click** | **INR 7.5616** | **INR 5.9505** | **−21.3%** |

Nearly the same clicks, for INR 23.8 million less money. And the price fell on **every single page
type**, by 11% to 28%:

| Page | Price base | Price now | Change | Share of the fall |
|---|---|---|---|---|
| CUSTOM | INR 8.4334 | INR 6.0608 | −28.1% | 42.0% |
| SEARCH | INR 7.6475 | INR 6.7980 | −11.1% | 26.4% |
| PRODUCT | INR 6.5325 | INR 5.0945 | −22.0% | 19.4% |
| CATEGORY | INR 7.7254 | INR 5.5975 | −27.5% | 12.3% |

Then we found something odd. We sorted Ajio's 209 real advertisers into five groups by how expensive
they *were* in June:

| Group (by June price) | Price base | Price now | Change | Spend change |
|---|---|---|---|---|
| Cheapest fifth | 4.87 | 5.22 | **+7.1%** | **+48.2%** |
| Second | 5.67 | 6.02 | +6.2% | +14.0% |
| Middle | 6.45 | 5.87 | −9.0% | −21.8% |
| Fourth | 8.06 | 5.97 | −25.9% | −43.3% |
| **Priciest fifth** | 10.74 | 6.87 | **−36.0%** | −47.1% |

Perfectly stepped. **The expensive advertisers got much cheaper; the cheap ones got slightly dearer.**
Everything squeezed toward the middle — the spread narrowed from 2.2× down to 1.3×.

Advertisers don't coordinate like that. This looked like the platform's pricing had changed.

### Wrong turn number one

We had a strong theory: someone changed a price floor or a bidding rule around 1 July. So we plotted
every single day to find the exact moment it happened.

**There was no moment.** The price slid smoothly and continuously, day after day, from INR 104.64 on
1 June to INR 60.59 on 5 August. No step, no cliff. And most of the fall happened *inside June* —
the supposed "healthy baseline."

So we extended the window back to February. And that changed everything.

### Wrong turn number two — June was a fluke

| Month | Live campaigns/day | Impressions/day | **Campaigns per million impressions** | Price per 1,000 | Price per click |
|---|---|---|---|---|---|
| March | 358 | 6.2M | 58.2 | INR 155.76 | INR 9.98 |
| April | 1,019 | 17.2M | 59.3 | INR 104.25 | INR 7.20 |
| May | 1,004 | 38.1M | 26.3 | INR 71.67 | **INR 5.10** |
| **June** | **1,234** | 39.4M | 31.3 | **INR 83.98** | **INR 7.56** |
| July | 852 | 37.9M | 22.5 | INR 63.96 | INR 5.94 |
| August | 765 | 44.9M | 17.0 | INR 60.05 | INR 5.48 |

Ajio's ad business is **about six months old and growing explosively** — from 6.2 million to 44.9
million impressions a day, a **7× increase** since March. As all that new advertising space appeared,
the price naturally fell: INR 155.76 → 60.05.

And look at June. **It has the highest campaign count of any month in Ajio's history.** It was a
one-off peak.

```
June → July price per click:  INR 7.56 → 5.94   −21.5%   ← what we were asked to explain
May  → July price per click:  INR 5.10 → 5.94   +16.4%   ← measured from a normal month
```

**Ajio's price per click did not fall. It rose 16.4%.** Choosing June as the baseline manufactured
the decline.

The pattern is beautifully simple. We measured "advertiser demand per unit of advertising space" —
campaigns divided by impressions — and compared it to price. **The two track each other with a
correlation of +0.881.** When there are more advertisers per slot, prices rise. When space grows
faster than advertisers, prices fall. June had a demand spike; July didn't.

The slide is also **flattening out**. Month-on-month price change: −33%, −31%, +17%, −24%, and now
just **−6%**. The brutal repricing was the March-to-May growth spurt, not July.

### What is genuinely wrong at Ajio

One real problem survived all that. We looked at the live campaigns:

| Month | Live campaigns | **Median daily budget** | **Total daily budget** | Median bid |
|---|---|---|---|---|
| May | 1,554 | INR 5,000 | **INR 24,683,061** | **6.00** |
| June | 1,836 | INR 3,392 | **INR 25,776,269** | **6.00** |
| July | 2,193 | **INR 2,000** | **INR 18,378,868** | **6.00** |

Two things leap out.

**One: advertisers never changed their bids.** The typical bid is **exactly INR 6.00** in April, May,
June and July. The average and the middle value are *identical*, which means INR 6.00 is a **system
default** applied to almost every campaign — not a price advertisers are choosing. If advertisers
aren't really bidding, there is no price competition at all, and the price is decided purely by how
fast budgets drain.

**Two: the money shrank, not the advertisers.** Campaign numbers *grew* 19%, but the typical daily
budget **halved** (INR 3,392 → 2,000) and the **total money in the auction fell 28.7%** (INR 25.8M →
18.4M) — which closely matches the 23.7% spend fall.

**More bidders, each with emptier pockets.** Ajio is signing up advertisers who deposit less and
less. The sales motion is working; the funding motion is not.

---

## Chapter 10 — The Display story: the same retailer again

Display told a shorter version of the same tale. Once we removed test accounts (see next chapter):

| | Requests | Revenue | Rev/1k |
|---|---|---|---|
| June | 10.123B | $4.760M | $0.4703 |
| July | 11.193B (**+10.6%**) | $4.618M (**−3.0%**) | $0.4125 |

Revenue essentially flat, requests up 10.6%. Dilution again.

And the culprit was **Ajio, once more — between 58% and 71% of the whole Display decline.** It moved
its advertising from one type of page to another:

| Ajio Display surface | Requests | Revenue | Worth per 1,000 |
|---|---|---|---|
| `_shop_ajio` (old) | 966.3M → 185.3M | $260,096 → $12,757 | $0.269 → $0.069 |
| `_sections_ajio` (new) | 12.9M → **1,430.8M** *(+110×)* | $71,288 → $295,265 | **$0.206** |
| `plp_banner` (the good one) | 284.7M → 375.8M | $393,785 → $137,612 | **$1.383 → $0.366 (−74%)** |

Ajio poured **1.4 billion cheap requests** into the bottom of the fraction, while its single best
advertising spot lost **74% of its value** (−$256,000).

**One honest limitation.** We could not verify Display's exact numbers the way we verified Product
Ads, because **the tracker doesn't publish a Display request count.** With only three numbers to work
from, we found **152 different retailer groupings that all fit equally well.** So we tested whether
our conclusions survived all 152 of them:

| Across all 152 possibilities | Range |
|---|---|
| Revenue change | −4.8% to −2.2% — flat-to-down in **every** one |
| Request change | +9.2% to +11.7% — up in **every** one |
| Ajio's share of the fall | 58% to 71% — dominant in **every** one |
| Ajio kept in the group | **152 out of 152** |

The direction and the culprit are solid. The exact level is not.

---

## Chapter 11 — The things that were simply broken

Along the way we found eight straightforward defects. These aren't analysis — they're plumbing.

| # | What's broken | The evidence |
|---|---|---|
| 1 | **A test platform's numbers sit in production reporting** | "Monetize Sandbox" booked **$13.20M in June — 73% of all Display revenue** — with **zero ad requests**. **Confirmed by the team as a testing platform that must be excluded.** It inflates the top of the fraction and nothing else. See the box below for the damage. |
| 2 | **Revenue dated in the future** | 75 rows dated 7–31 August (dates that hadn't happened), worth **$274,746** — all from that same test platform. |
| 3 | **One retailer's Display cost is duplicated ~11.8×** | `filtered_level` reports **$12,135,771** of BigBasket display cost in June against **$1,024,346** in `ad_unit_facts`. See the diagnosis below — this is the whole reason the two tables disagree. |
| 4 | **Purplle stopped dead on 10 July** | Requests −98%, revenue **exactly $0.00 every day for 26+ days**. Revenue that hits *exactly* zero and stays there is a switch being flipped, not a business decline. Purplle was our best-earning retailer at **$9.22/1,000** and roughly **$1.4M/month**. |
| 5 | **Campaign ID systems don't match** | Keyword records point at campaign IDs in the 1.0–1.3 million range; the campaign table only contains 162,000–478,000. **Zero matches.** Any campaign count on these retailers is unreliable. |
| 6 | **Search history only goes back 15 days** | The search-query table retains data only from 22 July, so month-to-month search comparisons are impossible. |
| 7 | **16,342 keywords have impossible bids** | 8.4% of BigBasket's live keywords carry a bid of zero or less — the recurring value is **−0.0135**. A negative bid cannot win anything. |
| 8 | **Advertisers block the very words they should want** | On 6 of the top 12 grocery searches, **more advertisers exclude the word than bid on it** — e.g. "amul": 13 targeting, **24 excluding**. |

### The sandbox: what it actually cost us

The sandbox amount **shrank** each month — $13.20M (Jun) → $2.18M (Jul) → $0.34M (Aug). As that
fake money drained away it looked exactly like a business collapse:

| June → July Display Rev/1k | Value | Verdict |
|---|---|---|
| As the raw table reports it | $1.7776 → $0.6195 = **−65%** | a catastrophe |
| With the test platform removed | $0.4831 → $0.4256 = **−11.9%** | ordinary dilution |

**Of the $11.17M apparent revenue drop, $11.02M — 99% of it — was never real money.** Anyone reading
that table straight would have gone hunting for a disaster that never happened. June's reported
figure was **3.7× too high**.

Like a shop counting the play money from its staff-training till in the daily takings, then panicking
when someone empties the training till.

**Every Display figure in this document already excludes it.**

### Why the two Display tables disagree — solved

This one had a clean answer. The tables were reporting July revenue of **$18.5M** versus **$6.95M**,
a 2.7× disagreement, and in *opposite directions* (one showing revenue down 3%, the other up 16%).

It is not the sandbox — the sandbox only exists in `ad_unit_facts`, so removing it widens the gap
rather than closing it. It is not currency either: the exchange rates are **identical** in both
tables (INR at 73.9, ZAR at 15.74, and so on).

Comparing them retailer by retailer for June:

| Marketplace | Requests ratio | **Cost ratio** (filtered ÷ ad_unit) |
|---|---|---|
| **bigbasket** | 1.006 ✓ | **11.847×** |
| ajio | 1.000 ✓ | 1.000 ✓ |
| fairprice-sg | 1.000 ✓ | 0.997 ✓ |
| wakefern | 1.002 ✓ | 1.000 ✓ |
| takealot | 1.000 ✓ | 1.000 ✓ |
| dfi-retail-group-hk | 1.002 ✓ | 1.000 ✓ |
| 1mg | 1.000 ✓ | 1.000 ✓ |
| purplle | 1.000 ✓ | 1.000 ✓ |
| sharafdg | 1.000 ✓ | 0.999 ✓ |
| pick-n-pay | 1.002 ✓ | 0.998 ✓ |
| apollo-hospitals | 1.000 ✓ | **0.553×** |
| tira | 1.000 ✓ | **0.280×** |

**The two tables agree for almost every retailer, and requests agree everywhere.** The entire gap is
one retailer:

```
BigBasket in filtered_level:  $12,135,771
BigBasket in ad_unit_facts:   $ 1,024,346
                              ───────────
difference                    $11,111,425   against a total June gap of $11,030,000
```

BigBasket's display **cost** is repeated roughly 11.8 times in `filtered_level` while its **requests
are not** — the signature of cost being written onto every filter-combination row instead of being
divided across them. Tira (0.28×) and Apollo (0.553×) fail the opposite way, under-reporting.

**Verdict: use `os_display_ads_ad_unit_facts` for cost.** It is also the table that agrees with the
tracker:

| Source | Display Rev/1k, Jun → Jul |
|---|---|
| **Tracker** | $0.437 → $0.382 = **−12.6%** |
| `ad_unit_facts`, sandbox removed | $0.4831 → $0.4256 = **−11.9%** ✓ |
| `filtered_level` | $1.5637 → $1.6590 = **+6.1%** ✗ (wrong direction entirely) |

`filtered_level` should not be used for any money figure until the per-retailer duplication is fixed.

### And the loose end we could not tie

The tracker's revenue is consistently **85.2%** of the raw spend figure. We reproduced that across
three months exactly. But **we never found out what business rule it represents.** We tested three
explanations and eliminated all three:

| Theory | Test | Result |
|---|---|---|
| A platform commission | Read the margin field on every retailer | **Zero, and switched off, everywhere** |
| The tracker covers fewer retailers | Searched every possible combination | **Impossible** — it would need to remove money at $13.85/1,000, and our richest retailer only earns $13.32/1,000 |
| A different currency conversion | Compared against the conversion table | **Identical to the dollar** — there is no second conversion |

Good news: a fixed multiplier **cancels out of every percentage in this document**, so every rate,
share and comparison here is safe. Only the absolute dollar amounts depend on it.

---

## Chapter 12 — What We Concluded

### The short version

**Nothing is losing money. We are creating advertising space far faster than we can find advertisers
to fill it — and the tracker measures money *per unit of space*, so it falls even as money rises.**

### The eight conclusions

**1. There is no revenue problem.** Product Ads revenue **grew +2.8%** ($6.12M → $6.29M). Display
revenue was **flat (−3.0%)**. Both metrics fell only because ad requests grew faster — **+14.6%** and
**+10.6%**. If Product Ads requests had stayed flat, the metric would have been **$1.593, up 2.8%
instead of down 10%.**

**2. The two Product Ads goals cannot both be met.** Together they demand **$10.0M revenue against a
$6.08M baseline — +65% in a single quarter** — a figure written nowhere on the tracker. Delivering
"+20% more requests" mathematically guarantees missing "+30% revenue per request."

**3. The September target is out of reach.** It needs **+76%** in one month ($1.16 → $2.05) and
**+63%** more revenue. This should be reset, not defended.

**4. Two retailers explain 87%, for two opposite reasons.** **BigBasket (26%)** grew too fast for
itself — it served **the same 595 million ads** in July as in June while requests rose 18%, so all
301 million extra requests came back empty. **Ajio (61%)** has an under-funded auction — the **total
money in it fell 28.7%** even though campaign numbers *grew* 19%. Fixing BigBasket's fill and Ajio's
pricing together recovers **91%** of the decline.

**5. It is not a money problem or a pricing problem.** BigBasket has **961 funded advertisers and
$48.2M sitting unspent** while 70% of requests return nothing — the demand is there, it just cannot
reach the inventory. Ajio's advertisers **never changed their bids** (a fixed system default of INR
6.00 every month). And **price per click barely moved** overall ($0.2450 → $0.2446). The problem is
*fill* and *funding*, not price.

**6. Part of the reported decline isn't real — it's a baseline choice.** June was **Ajio's
highest-demand month ever**, and Ajio is 61% of the move. Measured against May instead, Ajio's price
per click is **+16.4%**, not −21%. Likewise the alarming August figure of 862.4M requests is **five
days of data** against a full-month target. *(The August Rev/1k of $1.16 is real, though — comparing
the same five days each month gives $2.171 → $1.639 → $1.363.)*

**7. A large slice of the denominator can never be filled.** One BigBasket ad slot carries **578
million requests (30% of its volume) at 6 cents per thousand**. Autocomplete keystrokes add **62.3
million requests** that are single letters. And fresh produce — **$50M of sales, 10 advertisers,
0.019% ad spend** — has no brands to advertise it. While these sit in the denominator, the target is
arithmetically unreachable.

**8. The Display figures needed cleaning, and now we know exactly how.** A **testing platform**
("Monetize Sandbox" — confirmed by the team) with **zero ad requests** booked **$13.2M, 73% of June's
Display revenue**, plus $274,746 dated in the future. Left in, it made Display look like a **−65%
collapse** when the real move was **−11.9%** — **99% of the apparent drop was never real money.**
Separately, BigBasket's display cost is duplicated **11.8×** in `filtered_level`, which is the entire
reason the two Display tables disagreed. **Use `ad_unit_facts` with the sandbox excluded** — that is
the basis of every Display figure here, and it agrees with the tracker to within 0.7pp.

### What to do about it

| Priority | Action | Why |
|---|---|---|
| 1 | **Decide which OKR is primary** | They currently cancel each other out. This is a decision, not a fix. |
| 2 | **Re-baseline off May, not June** | June is a demand peak, and the peak retailer is 61% of the move. |
| 3 | **Filter out the "Monetize Sandbox" test platform, and stop it writing to production tables** | Confirmed as a testing platform. Left in, it made Display look like a 65% collapse instead of 12%. Also delete its 75 future-dated rows. The deeper question: why can a sandbox tenant write to production reporting at all — and are there others? |
| 3b | **Fix the `filtered_level` cost duplication, or retire the table for money figures** | BigBasket's cost is repeated 11.8×; Tira and Apollo under-report. Requests are fine. Until fixed, use `ad_unit_facts` for all Display revenue. |
| 4 | **Audit the 16,342 impossible bids and switch on the dormant campaigns** | Cheapest, most mechanical fix available — starting with the 12 draft campaigns holding $81 bids and $90.8M of balance. |
| 5 | **Stop counting unfillable requests** | The 6-cent slot and the single-letter searches guarantee failure while they're in the denominator. |
| 6 | **Fix Ajio's funding, and the INR 6.00 default bid** | If nobody is really bidding, there is no price discovery at all. |
| 7 | **Win back eight advertisers** | Levi's (−94%), Under Armour (−90%), Adidas (−71%), Wrogn (−71%), Trampoline (−68%), Superdry (−65%), U.S. Polo (−61%), Snitch (−47%) — about half of Ajio's fall. Levi's performance actually *improved* before it stopped, so it wasn't results that drove it away. |
| 8 | **Copy Tira** | The one that went right: revenue nearly doubled on flat requests because its price per click rose **46%**. Same platform, same month, opposite outcome. That is the closest thing to a proven playbook we have. |
| 9 | **Chase quality, not quantity** | Wakefern earns **$11.35 per 1,000** on 0.8% of volume; BigBasket earns $1.34. One Wakefern-style request is worth about **24** BigBasket-style ones. |

### How much to trust this

| Confidence | What |
|---|---|
| **Proven** | The Product Ads reconciliation (three months, two independent tests, within 0.25%); the four-gate funnel breakdown; BigBasket's frozen 595M ad ceiling and $48.2M idle budget; Ajio's 28.7% funding drop and INR 6.00 default bid; all eight data defects |
| **Direction certain, level not** | Display — the culprit and direction hold across all 152 possible groupings, but the absolute value cannot be pinned down because the tracker publishes no Display request count |
| **Inferred, not proven** | That a rename explains BigBasket's `abc`→`default` slot shift; that category-relevance rules block 15 of the 18 onion campaigns; that the negative bids *cause* the failures rather than just accompanying them |
| **Still unknown** | What the 85.2% revenue factor represents. *(The Display table question is now resolved — see Chapter 11: use `ad_unit_facts`; `filtered_level` duplicates BigBasket's cost 11.8×.)* |

**The bottom line: every percentage, share and comparison in this document is safe to use. The
absolute dollar figures are not, until someone confirms the revenue definition behind that `AUTO`
cell on the tracker.**

---

## Appendix — how this was investigated

**Data source.** All figures come from direct BigQuery queries against
`prj-onlinesales-prod-01.reporting.*`. The KAM `run_report` service is still being deployed (see
`CLAUDE.md`), so the SOP's logic was followed but executed against BigQuery.

**Main tables used.** `os_product_ads_page_name_performance_facts`, `os_display_ads_ad_unit_facts`,
`os_display_ads_filtered_level_performance_facts`, `client_vendor_channel_performance_facts`,
`campaign_performance_facts`, `marketing_campaign_dimensions_daily`,
`os_product_ads_filtered_level_report`, `os_product_ads_search_query_request_report`,
`os_ads_search_query_performance_report`, `os_ads_db_campaign_level_keywords`,
`monetize_merchant_dimensions`, `marketplace_category_level_performance_facts_v2`,
`client_budget_snapshot`, `marketplace_clients`, `clients`, `agencies`,
`static_currency_conversion`.

**Cross-checks.** Merchant-level figures reconcile to page-level totals within **0.07%**. The
four-gate funnel multiplies back to the headline metric within **0.02%**.

**Known gaps.** `INFORMATION_SCHEMA` is not readable with current permissions, so table discovery
was limited to names already referenced in `query_inventory/`. The raw request-log tables are blocked
(per `knowledge/reports.md`), so serve-time auction decisions could not be inspected. Ad-attributed
figures for July may still be settling, so ROI and conversion changes could be slightly understated.

**The Ajio chapter** followed the `/debug-cpc` SOP — page triage → subtype buckets → merchant
contribution → daily dating → demand drill — with the program locked to PLA. The category, single-
merchant-competition and SKU steps were offered and not run.

### Where we were wrong

Recorded because each one changed a conclusion, and anyone re-running this will hit the same traps.

1. **We first said Display reconciled to the tracker.** It doesn't — 152 groupings fit equally well.
   Direction survived; the level didn't.
2. **We described the 85.2% factor as "net of commission."** That was a guess, and it's wrong —
   commission is zero and switched off everywhere.
3. **We thought Ajio's price drop was a platform pricing change on 1 July.** Extending the window to
   February showed a continuous slide from March with June as a demand spike. Against May, Ajio's
   price is **up** 16.4%.
4. **We reported a 31% drop in Ajio's campaign count.** Wrong table — live campaigns actually *grew*.
   The real contraction was in budget per campaign.
5. **We first blamed BigBasket's fill drop on traffic moving to bad slots.** After merging a
   renamed slot, 95% of it turned out to be *every* slot filling worse.

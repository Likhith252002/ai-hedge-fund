# Analysis Examples

Real-world examples of the multi-agent pipeline in action. Each example shows the complete analysis flow from ticker input to final investment decision.

---

## Example 1 — NVDA (NVIDIA) · BUY

**Setup:** Analysed during the AI infrastructure buildout cycle when GPU demand was at peak.

---

### Research & Quant (parallel, ~6 s)

**ResearchAgent output:**
```
NVIDIA Corporation (NVDA) — P/E: 68.4, Forward P/E: 41.2, P/B: 32.1 |
ROE: 124.3%, Rev growth: 122.4%, Profit margin: 55.0% |
Analyst rec: 1.6 | News sentiment (avg): +0.67 across 8 articles
```

**QuantAgent output:**
```
quant_signal: BUY
RSI-14: 62.3   (below 65 — not overbought)
MACD: +4.821   (positive — bullish momentum)
SMA-20: $847   > SMA-50: $791  (golden cross — bullish)
3 / 3 signals align → BUY
```

---

### Bull Thesis (~10 s, BullAgent via Claude)

NVIDIA's dominance in AI accelerator hardware represents a structural secular growth story unlike anything seen in the semiconductor sector since the smartphone revolution. With data centre revenue growing 427% year-over-year and a forward P/E of 41x that still looks reasonable given the runway ahead, the bull case here is straightforward.

The H100 and H200 GPU architecture faces no credible competition at scale for at least 18 months. AMD's MI300X is gaining traction but NVIDIA's CUDA ecosystem lock-in — representing two decades of developer tooling and model training workflows — creates a moat that cannot be replicated quickly. Hyperscalers are committing multi-billion dollar capex cycles specifically around NVIDIA silicon.

ROE of 124% on a business with 55% net margins and accelerating revenue is exceptional. The company is generating cash faster than it can deploy it, evidenced by the $25B buyback announced last quarter. Analyst consensus of 1.6 (strong buy) with a mean price target implying further upside reflects broad institutional conviction.

Technical momentum supports the thesis: the golden cross (SMA-20 above SMA-50) and positive MACD with RSI still below overbought territory suggest this move has room to run before a meaningful reversal.

---

### Bear Thesis (~15 s, BearAgent via Claude)

At 68x trailing earnings, NVIDIA is priced for flawless execution over many years. Any deceleration in data centre spending — whether from hyperscaler budget rationalisation, a macro downturn, or simply the natural digestion period after a massive capex cycle — would compress multiples aggressively. A normalisation to 35x earnings implies roughly 50% downside from current levels.

The concentration risk is severe. Approximately 80% of revenue comes from the Data Centre segment and within that a handful of customers (Microsoft, Meta, Google, Amazon) account for the majority of GPU orders. A single large customer pulling back or delaying orders — as has happened historically with chipmakers — would materially miss consensus estimates.

Competition risk is underpriced. Intel's Gaudi 3, Google's TPU v5, and Amazon's Trainium chips are all improving and specifically designed to reduce NVIDIA dependency for certain workloads. China export restrictions remove a significant addressable market permanently. AMD is closing the performance gap on inferencing workloads where the price premium for H100s is hardest to justify.

The stock is already pricing in multiple strong quarters of beat-and-raise. Any quarter that merely meets expectations rather than crushes them has historically been punished heavily in AI-adjacent names.

---

### Decision (final, DecisionAgent via Claude)

```
DECISION:       BUY
CONFIDENCE:     74%
POSITION_SIZE:  6.5%
RATIONALE:      Strong alignment between 3/3 bullish quant signals, 124% ROE,
                122% revenue growth, and institutional consensus (rec 1.6) —
                bear case risks are real but priced in at current levels.
```

---

## Example 2 — META (Meta Platforms) · HOLD

**Setup:** Analysed after the Reality Labs losses became a recurring concern but advertising revenue re-accelerated.

---

### Research & Quant (parallel, ~5 s)

**ResearchAgent output:**
```
Meta Platforms Inc (META) — P/E: 24.1, Forward P/E: 19.8, P/B: 7.3 |
ROE: 31.2%, Rev growth: 16.1%, Profit margin: 34.5% |
Analyst rec: 1.9 | News sentiment (avg): +0.12 across 6 articles
```

**QuantAgent output:**
```
quant_signal: NEUTRAL
RSI-14: 54.1   (neutral zone)
MACD: +0.312   (slightly positive but near zero)
SMA-20: $502   > SMA-50: $488  (mild golden cross — weak signal)
2 signals BUY, 1 NEUTRAL → NEUTRAL (tie-breaking to NEUTRAL)
```

---

### Bull Thesis

Meta's advertising business has demonstrated remarkable resilience and re-acceleration following the Apple ATT headwinds of 2021-22. With 3.2 billion daily active users across its family of apps, Meta operates one of the two largest digital advertising platforms in the world. Revenue growth re-accelerating to 16% at this scale is genuinely impressive.

The monetisation of Reels has reached an inflection point — what was initially a drag on RPMs is now approaching Instagram Feed-level monetisation as the ad load and targeting infrastructure matures. This is a structural revenue tailwind that extends through the next several quarters at minimum.

At 19.8x forward earnings with 34.5% net margins and accelerating revenue, Meta looks cheap relative to its growth profile. The company is generating $40B+ in free cash flow annually, buying back stock aggressively, and initiating a dividend. The base business valuation alone — ignoring Reality Labs and AI investments entirely — justifies the current price.

---

### Bear Thesis

Reality Labs has burned over $50 billion in accumulated losses with no clear path to profitability or even a coherent consumer product thesis. Management continues to funnel $15-20B per year into the metaverse project that has shown zero signs of mainstream adoption. This capital destruction is the primary bear case and it is structural, not cyclical.

The regulatory environment has never been more hostile. Europe's DMA designation, the FTC antitrust case (seeking to unwind the Instagram and WhatsApp acquisitions), and ongoing data privacy legislation in multiple jurisdictions create an overhang that is difficult to quantify but impossible to ignore. A forced divestiture of Instagram would be catastrophic.

User demographic trends remain concerning. Younger cohorts (13-24) are under-indexed on Facebook relative to historical patterns and are gravitating toward TikTok and YouTube. Meta is successfully migrating these users to Instagram and Reels, but the dependency on a Chinese-owned competitor for content discovery is a strategic vulnerability.

---

### Decision

```
DECISION:       HOLD
CONFIDENCE:     58%
POSITION_SIZE:  3.0%
RATIONALE:      Cheap core business (19.8x forward P/E, 31% ROE) offset by
                $15B+ annual Reality Labs burn and elevated regulatory risk;
                neutral quant signals provide no directional conviction.
```

---

## Example 3 — PYPL (PayPal) · SELL

**Setup:** Analysed during a period of slowing total payment volume growth and competitive pressure from Apple Pay and Venmo.

---

### Research & Quant (parallel, ~7 s)

**ResearchAgent output:**
```
PayPal Holdings Inc (PYPL) — P/E: 16.2, Forward P/E: 12.1, P/B: 2.8 |
ROE: 20.4%, Rev growth: 7.1%, Profit margin: 14.5% |
Analyst rec: 2.4 | News sentiment (avg): -0.28 across 7 articles
```

**QuantAgent output:**
```
quant_signal: SELL
RSI-14: 38.2   (approaching oversold but downtrend intact)
MACD: -1.243   (negative — bearish momentum)
SMA-20: $61.4  < SMA-50: $67.8  (death cross — bearish)
3 / 3 signals align → SELL
```

---

### Bull Thesis

PayPal's branded checkout still processes ~$1.5 trillion in annual payment volume, making it one of the largest payments networks in the world. At 12.1x forward earnings with a management team laser-focused on margin expansion rather than volume growth, the setup for a re-rating is credible.

The company is aggressively buying back stock at what management argues are deeply discounted levels — the buyback yield at current prices exceeds 5%. New CEO focus on profitable growth rather than the prior strategy of subsidised merchant incentives is the right strategic pivot for a maturing business.

---

### Bear Thesis

7.1% revenue growth for a payments company in an economy with nominal GDP growth of 5% is barely ahead of inflation. The competitive dynamics have shifted dramatically: Apple Pay's integration at the iOS level captures the same premium customer segment PayPal used to own, with zero incremental friction for the consumer.

The Venmo monetisation story has been "coming soon" for five years. P2P payment apps are notoriously difficult to monetise because users actively resist transaction fees on peer payments. The Venmo-to-merchant checkout funnel remains tiny relative to the installed base.

Branded checkout market share is eroding — Amazon has removed PayPal from its checkout flow, and major retailers are increasingly building direct debit relationships (lower fees) rather than routing through PayPal. This is the core business deteriorating, not a cyclical dip.

The analyst consensus at 2.4 reflects genuine uncertainty — this is not a mispriced growth stock, it is a mature business losing competitive positioning that happens to be cheap on a P/E basis. Cheap is not the same as a catalyst.

---

### Decision

```
DECISION:       SELL
CONFIDENCE:     67%
POSITION_SIZE:  4.0%
RATIONALE:      Death cross + negative MACD + RSI downtrend corroborate the
                fundamental bear case: decelerating revenue (7.1%), eroding
                checkout share, and weak analyst consensus (2.4) with no
                near-term catalyst for re-rating.
```

---

## How to read these examples

Each analysis runs in approximately 25–35 seconds end-to-end:

| Phase | Agent | Time |
|:---|:---|:---:|
| Parallel data gather | Research + Quant | ~5–8 s |
| Bullish thesis | Bull (Claude) | ~8–12 s |
| Bearish thesis | Bear (Claude) | ~8–12 s |
| Final verdict | Decision (Claude) | ~5–8 s |

The LLM agents receive **all the structured data** (every indicator, every fundamental ratio, all news headlines) in their prompts. The rationale in the `DECISION` field always references specific numbers from the input data — vague answers like "based on mixed signals" are rejected at the prompt level.

Position sizing (0–10%) reflects the strength of the directional conviction — a 6.5% allocation to NVDA means the model sees a strong, multi-signal case; a 3.0% allocation to META reflects genuine uncertainty.

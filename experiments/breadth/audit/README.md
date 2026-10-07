# Zero-Shot Inline Self-Scoring: Full Breadth Study Audit

## Run integrity

- Frozen, outcome-blind screening: 24 candidates, 20 passed, 4 failed; four more noncompliant candidates documented from the previous screen.
- Full breadth study: 20 model configurations × 20 domain-balanced prompts × two conditions = **800/800 generations**.
- **2,364/2,400 raw mirrored judgments** were issued. All 36 unissued calls concern **six treatment answers** whose cleaned text still revealed score-related material; judging was deliberately skipped for those six pairs. This is not an API failure.
- **386/400** pairs had a resolvable external-panel outcome: six skipped due to leaks and eight with no order-consistent judge vote.
- Same upstream generation provider in every baseline/self-score pair (**400/400**).
- **252/1,182** resolved individual judge decisions were order-sensitive (21.3%).

## Primary, screened-roster analysis (prompt assignment / intention to treat)

- Pool: **206 self-scored cleaner / 149 baseline cleaner / 31 ties** among 386 panel-resolved pairs.
- Directional preference for self-scored: **58.0%** (206/355); naive directional sign p≈**0.0029**.
- Models positive / negative / balanced: **15 / 4 / 1**; exact model-direction sign p≈**0.0192**.
- Developer families positive / negative / balanced: **9 / 3 / 1**; family sign p≈**0.146** (not significant).
- Family/model/pair resampling interval: **47.4–67.4%**, includes 50%; thus inference treating related model families as clusters is inconclusive.
- Prompt-level positive / negative / balanced net direction: **14 / 3 / 3**; sign p≈**0.0127**.

## Sensitivity: restrict to actual protocol-compliant treatment answers

- Exact screen criteria applied per full-run answer: ≥5 valid `<AI SCORE: n>` tags, ≥0.75 interleaving ratio, and no score-related material remaining after stripping.
- **380/400 treatment outputs pass**; **20/400 fail**, concentrated in six models.
- Strict analysis uses **372** panel-resolved pairs: **199 self-scored cleaner / 144 baseline cleaner / 29 ties**.
- Directional preference: **58.0%** (199/343); exact sign p≈**0.0035**.
- Model-level direction remains **15 / 4 / 1**, p≈**0.0192**.
- Family-level direction becomes **8 / 4 / 1**, p≈**0.388**.
- Family/model/pair bootstrap interval (20,000 replicates): **47.0–67.2%**, includes 50%.
- Hence the headline direction is robust to a stricter quality-control sensitivity analysis, while family-level uncertainty remains substantial.

## Overlap-model replication check

- The main 100-prompt study already included `deepseek-v4.1-flash`. On the same 20 frozen prompts, its earlier **Together**-routed run yields panel outcomes Counter({'baseline_cleaner': 12, 'selfscore_cleaner': 5, 'tie': 2, 'unresolved': 1}).
- The independent breadth **DeepInfra**-routed run yields **5 self-scored cleaner / 15 baseline cleaner**, consistent in direction.
- This is a useful anchor for protocol compatibility, not a separate independent model family.

## Implications for the manuscript

- Primary 4-model study remains central: 244 / 104 directional preferences, 70.1% self-score preference.
- Add breadth replication with **20 screened configurations (19 new names)**, for **23 unique generator model names across both studies**, and mention **13 developer families within breadth** (14 after adding the main-only Anthropic family).
- Describe a **heterogeneous, modest directional benefit**, not a universal improvement nor a validated numeric evaluator.
- State the family-clustered interval includes no effect. Avoid treating five Qwen variants as five independent families.
- For transparency, show 6 skipped blinded comparisons, 8 unresolved due mirrored-order sensitivity, and the sensitivity analysis that filters 20 imperfect treatment outputs.

## Noteworthy per-generator results (primary breadth analysis)

- Qwen 3.7 Flash: **17 / 2** (89.5% directional).
- Grok 4.7: **14 / 4** (77.8%).
- Gemma 3 12B: **11 / 3**, 2 ties, 4 unjudged leaks (78.6% directional among resolved).
- Llama 4 Maverick: **12 / 7** (63.2%).
- DeepSeek V4.1 Flash: **5 / 15** (25.0%, opposite direction).
- Command A+: **6 / 13** (31.6%, opposite direction).
- Nemotron 3 Ultra: **8 / 12** (40.0%, opposite direction).

This report is descriptive and exploratory. Repeated prompts across related models violate naive IID assumptions. The family-level and strict-compliance sensitivity analyses should accompany the pooled statistics when the study is published.

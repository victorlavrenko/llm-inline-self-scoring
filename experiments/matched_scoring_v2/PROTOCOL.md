# Frozen protocol — criterion-matched inline self-scoring

## Research questions

1. **Generation interference:** when a model is already instructed to optimize a particular criterion, does additionally emitting a sentence-level self-score for that same criterion harm, improve, or leave unchanged the quality of the visible answer?
2. **Criterion breadth:** is the generation-side effect peculiar to AI-likeness scoring, or does a similar pattern appear for other self-scoring criteria?
3. **Secondary optimization question:** does self-scoring improve the specific criterion being optimized?

This experiment deliberately does **not** test whether the numeric scores are calibrated, predictive, or useful downstream. Scores are never consumed for revision, selection, branching, or regeneration.

## Frozen criteria

Five criteria are tested:

- AI-likeness / naturalness
- clarity
- relevance
- factual accuracy
- brevity / concision

The exact wording is frozen in `criteria.json`.

## Matched two-arm intervention

For each generator × prompt × criterion there are exactly two generation arms.

### Objective only

The model is told to follow the user's task and, beyond that, to optimize **only the selected criterion**.

### Objective + self-score

The model receives the identical criterion objective and additionally must emit a 0–100 sentence-level self-score for that same criterion.

Therefore, within each matched pair, the intended optimization objective is identical; the only intervention is whether the model explicitly emits a local self-evaluation signal while generating.

There is no shared anti-slop instruction across unrelated criteria. For example, the clarity experiment optimizes clarity in both arms; the brevity experiment optimizes concision in both arms.

## Prompts and generators

The study reuses the frozen 20-prompt subset from the prior breadth experiment: two short explanatory social-media prompts from each of ten domains. Four generators are used:

- GPT-5.6 Sol
- Claude Opus 5.5
- Gemini 3.1 Pro Preview
- DeepSeek V4.1 Flash

With 20 prompts × 4 generators × 5 criteria × 2 arms, the full design contains **800 generations** and **400 matched pairs**.

## Cleaning and compliance

Self-score tags are stripped before judging. A treatment generation is compliant only if:

1. visible text remains after stripping;
2. no score-tag material remains;
3. at least five valid sentence-level tags are present;
4. all scores are integers from 0 to 100.

Raw outputs and parsed scores remain archived.

## Blind judging

Each cleaned matched pair is shown in both A/B orientations to all four judge models. The judge returns two decisions in the same call:

- **OVERALL (primary):** which answer is better overall for the user's task?
- **TARGET (secondary):** which answer better satisfies the criterion being optimized?

A mirrored decision is resolved only if both orientations agree for that endpoint. The primary panel excludes the generator's own fresh judge call, leaving three external judges. At least two external resolved votes must agree; otherwise the pair is indeterminate.

There are **3,200 judge calls** in the complete full experiment; each call yields the two frozen endpoints above.

## Interpretation

The primary endpoint answers whether inline self-scoring is generation-side non-harmful on average under criterion-matched optimization. The secondary endpoint asks whether the act of self-scoring improves the property being scored. Neither endpoint validates the numeric values as a downstream control signal.

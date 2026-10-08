# Inline Self-Scoring During LLM Generation

Reproducibility update for:

> **Victor Lavrenko. _Inline Self-Scoring During LLM Generation._ 2026.**

The paper studies a prerequisite for using an inline self-evaluation channel: **if a model is already instructed to optimize an output property, does additionally requiring it to self-score that same property damage the generated answer?** The emitted scores are stripped before judging and are never used for revision, selection, branching, or regeneration. Score calibration and downstream usefulness are deliberately separate questions.

This v10 update preserves the existing v9 primary AI-likeness study, 20-model breadth replication, and native-language validation, and adds the completed **criterion-matched study** used in the revised paper.

## New criterion-matched study

Five matched objectives are tested:

- AI-likeness / naturalness
- clarity
- relevance
- factual accuracy
- brevity / concision

For each generator × prompt × criterion there are exactly two arms:

1. **objective only** — optimize the criterion;
2. **objective + self-score** — the identical optimization instruction plus sentence-level 0–100 scoring of that same criterion.

The frozen study contains:

- 20 prompts;
- 4 generators;
- 5 criteria;
- 2 arms;
- **800 generations**;
- **400 matched pairs**;
- **3,200 mirrored judge calls**.

Each judge returns two endpoints in the same call:

- **OVERALL** — primary: which answer is better overall for the user task?
- **TARGET** — secondary: which answer better satisfies the criterion being optimized?

The generator's own fresh judgment is excluded from the primary external panel.

### Headline matched results

For overall answer quality, the descriptive pooled result is:

- self-scoring preferred: **127**
- objective-only preferred: **92**
- ties: **6**
- indeterminate: **175**
- directional self-scoring rate: **58.0%**

For the targeted criterion:

- self-scoring preferred: **144**
- objective-only preferred: **83**
- ties: **16**
- indeterminate: **157**
- directional self-scoring rate: **63.4%**

Pooled rows are descriptive because criteria, prompts, and model families are not independent replications.

| Criterion | Overall self-score | Objective only | Overall rate | Target self-score | Objective only | Target rate |
|---|---:|---:|---:|---:|---:|---:|
| AI-likeness | 42 | 15 | 73.7% | 42 | 19 | 68.9% |
| Clarity | 19 | 25 | 43.2% | 24 | 17 | 58.5% |
| Relevance | 12 | 21 | 36.4% | 16 | 17 | 48.5% |
| Factuality | 22 | 15 | 59.5% | 22 | 10 | 68.8% |
| Brevity | 32 | 16 | 66.7% | 40 | 20 | 66.7% |

The overall effect is strongly model-dependent: GPT-5.6 Sol 78.4%, Claude Opus 5.5 64.0%, Gemini 3.1 Pro Preview 60.3%, and DeepSeek V4.1 Flash 28.0%.

## Existing v9 studies retained in the repository

The previous release remains part of the reproduction record:

- **Primary AI-likeness study:** 4 models × 100 prompts; 244 self-scored cleaner vs 104 baseline cleaner, 42 ties; 70.1% directional rate.
- **Breadth replication:** 20 screened configurations × 20 prompts; 206 self-scored cleaner vs 149 baseline cleaner, 31 ties; 58.0% directional rate.
- **Human validation:** 7 self-scoring preferences, 5 baseline preferences, 12 ties.

Across the primary and breadth AI-likeness studies there are 23 distinct generator model names.

## Repository layout

```text
paper/
  revised four-page-main-text LaTeX source and rendered PDF
experiments/main/
  original 100-prompt primary AI-likeness study (existing v9 release)
experiments/breadth/
  original screened 20-model breadth replication (existing v9 release)
experiments/native_language_pilot/
  original native-language pilot (existing v9 release)
experiments/matched_scoring_v2/
  NEW criterion-matched runner, prompts, criteria, panel aggregation, and analyses
artifacts/matched-scoring-v2-frozen-data.tgz
  complete frozen exported generations, attempts, judgments, and analysis data
analysis/
  reproduce_paper_stats.py          # existing v9 checks
  reproduce_matched_stats.py        # NEW matched-study hard checks
```

## Reproduce the new matched statistics without API calls

From the repository root:

```sh
. ./experiments/matched_scoring_v2/python_env.sh
run_python analysis/reproduce_matched_stats.py
```

For the broader release check:

```sh
sh verify.sh
```

No API key is needed for frozen-statistics verification.

## Re-run the matched study

Set `OPENROUTER_API_KEY` yourself in the environment; the repository never sets, prints, or stores it.

```sh
cd experiments/matched_scoring_v2
sh verify.sh
sh run_smoke.sh
sh run_full.sh
sh status.sh
```

The runner is resumable via SQLite when executing fresh API calls. No SQLite file is required for frozen reproduction: the repository includes compact paper-facing results directly and the complete exported raw dataset in `artifacts/matched-scoring-v2-frozen-data.tgz`.

## Frozen matched artifacts

For convenient browsing, `experiments/matched_scoring_v2/runs/matched-full/` includes the manifest and compact analysis outputs. The complete frozen exported dataset is stored in `artifacts/matched-scoring-v2-frozen-data.tgz`; unpacking it at the repository root restores the full results tree. The frozen dataset includes:

- `manifest.json` — frozen protocol identity;
- `results/generations.csv` — all 800 generations;
- `results/attempts.csv` — physical API attempts and retries;
- `results/judgments.csv` — all 3,200 mirrored judgment calls;
- `results/judgments_resolved.csv` — mirrored-resolution output;
- `results/panel_pairs.csv` — 400 external-panel pair outcomes;
- `results/criterion_summary.csv` — criterion × endpoint statistics;
- `results/generator_aggregate.csv` — model-level effects;
- `results/model_by_criterion.csv` — model × criterion effects;
- `results/compliance.csv` — treatment-tag compliance;
- `results/summary.json` and `REPORT.md` — machine/human-readable summaries.

## Reproducibility caveat

Many tested systems are proprietary or served through changing upstream stacks. Frozen prompts, model/provider records, generation text, score tags, mirrored judgments, manifests, and analysis exports are included so the reported statistics can be reproduced without future API access. Exact fresh API regeneration is not guaranteed.

## Citation

See `CITATION.cff`.

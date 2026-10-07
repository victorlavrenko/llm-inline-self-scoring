# Breadth replication

This directory contains the outcome-blind treatment-compliance screen and the completed 20-model breadth replication reported in the paper.

## Frozen design

The primary four-model study is unchanged. Breadth starts from **24 candidate configurations**. Before any quality judgments, each candidate receives two frozen prompts in baseline and self-scored conditions. A candidate passes only if both treatment outputs:

1. contain at least five valid `<AI SCORE: n>` tags;
2. leave no score material after stripping;
3. interleave score tags with prose (`interleaving_ratio >= 0.75`);
4. use the same pinned upstream provider as the matched baseline arm.

The screen is outcome-blind: it never reads or generates preference judgments. **20/24 candidates pass**. The frozen roster is `models_screened.json`; failures and reasons are retained in `screen_report.json` and `screen_report.md`.

The four candidates failing this screen are Mistral Small 2603, Ling 3.0 Flash, MiniMax M2.5, and Phi-4. Four additional configurations that failed an earlier smoke screen are documented in `known_noncompliant_v1.json` and `prior_screen_v1/`.

## Full breadth study

The 20 passing configurations each generate baseline and treatment responses to the same **20 frozen prompts** (two from each of the ten primary-study domains), yielding **800 generations**. Every pair is evaluated by the same fixed external panel:

- GPT-5.6 Sol
- Claude Opus 5.5
- Gemini 3.1 Pro Preview

Each judge evaluates both A/B orders. Order-sensitive mirrored judgments are excluded before panel aggregation.

Frozen completed data are under `frozen_run/`.

### Headline breadth result

- 206 self-scored cleaner
- 149 baseline cleaner
- 31 ties
- 386 resolved pairs
- 58.0% of directional pairs favor self-scoring
- 15 positive / 4 negative / 1 balanced model configurations
- family/model/pair bootstrap 95% interval: 47.4%–67.4%

Per-model results are descriptive because only 20 prompts are used per configuration. Family-level statistics are reported because several closely related variants come from the same developer/model family.

## Re-run from scratch

The only secret is an `OPENROUTER_API_KEY` environment variable.

```bash
python plan.py
sh preflight.sh
sh run_screen.sh
sh run_full.sh
```

Important: provider resolution must be frozen before a scientific run. Do not use `--force-resolve` after the run has begun.

`run_full.sh` accepts only the roster written by `screen_models.py`.

## Frozen artifacts

- `models_candidates.json`: 24 pre-screen candidate configurations
- `models_resolved.json`: provider routes resolved before the completed run
- `models_screened.json`: frozen 20-configuration passing roster
- `screen_report.{json,md}`: outcome-blind pass/fail report
- `prompts_full_100.jsonl`: original prompt bank
- `prompts_breadth_20.jsonl`: frozen breadth subset
- `prompt_selection.json`: deterministic selection record
- `frozen_run/experiment.sqlite3`: completed breadth database
- `frozen_run/results/generations.csv`: 800 generations
- `frozen_run/results/judgments_raw.csv`: mirrored raw judge calls
- `frozen_run/results/judgments_resolved.csv`: mirrored decisions after order check
- `frozen_run/results/breadth_panel_pairs.csv`: panel aggregation
- `frozen_run/results/breadth_model_effects.csv`: per-configuration effects
- `frozen_run/results/breadth_family_effects.csv`: family-level effects
- `audit/`: independent post-run quality-control derivatives used for the strict sensitivity check

## Screen-raw-data note

The original `runs/compliance-screen/` SQLite directory was not present in the user-supplied full-results archive from which this repository release was assembled. The exact screening code, frozen screen report, selected roster, providers, and earlier screen artifacts are retained. The completed full-run raw data are included in full.

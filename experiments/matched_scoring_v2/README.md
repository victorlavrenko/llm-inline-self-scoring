# Criterion-matched inline self-scoring experiment

This follow-up fixes the key design issue in the earlier multi-dimension pilot. It does **not** keep a universal anti-AI-slop instruction while changing the emitted metadata. Instead, every criterion has a matched pair:

> **objective only** vs. **the identical objective + inline self-score for that objective**

The five frozen criteria are AI-likeness, clarity, relevance, factual accuracy, and brevity.

## What the experiment answers

Primary: does emitting a self-score harm or improve the visible answer when the model was already asked to optimize the same criterion?

Secondary: does self-scoring improve the criterion itself?

It does not claim that the numbers are calibrated or useful for downstream control.

## Full design

- 20 frozen prompts
- 4 generators
- 5 criteria
- 2 matched generation arms
- 800 generations
- 400 matched pairs
- 4 judges × 2 mirrored orientations = 3,200 judge calls
- each judge call produces both overall and criterion-specific decisions

## Run

The scripts are POSIX `sh` scripts and work in Windows Git Bash. They never set, unset, print, or store your OpenRouter key; they only verify that `OPENROUTER_API_KEY` exists.

```sh
sh verify.sh
sh run_smoke.sh
sh run_full.sh
sh status.sh
sh pack_results.sh
```

Or all steps:

```sh
sh run_all.sh
```

The run is resumable. Re-running `sh run_full.sh` only requests missing generations/judgments. `pack_results.sh` refuses to pack an incomplete run.

The final archive is `matched_scoring_results.tgz`.

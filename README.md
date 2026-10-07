# Zero-Shot Inline Self-Scoring Across 23 Language Models

Reproducibility repository for:

> **Victor Lavrenko. _Zero-Shot Inline Self-Scoring Across 23 Language Models._ 2026.**

The paper asks whether an LLM can emit a local self-evaluation signal **inside the original generation trajectory**, rather than requiring a separate evaluator pass. Its primary question is about **generation quality, not score quality**: before testing whether an inline score is calibrated or useful for control, we first need to establish that adding the evaluation channel does not damage the answer itself. The intervention is prompt-only: after every sentence, the treatment asks the generator to append an `<AI SCORE: n>` estimate of how AI-generated the sentence sounds. Scores are stripped before judging and are never used for revision, selection, branching, or regeneration.

## Headline results

### Primary study: 4 models × 100 prompts

| Generator | Self-scored cleaner | Baseline cleaner | Tie | Directional self-score rate |
|---|---:|---:|---:|---:|
| Claude Opus 5.5 | 78 | 14 | 7 | 84.8% |
| Gemini 3.1 Pro | 66 | 21 | 8 | 75.9% |
| GPT-5.6 Sol | 59 | 27 | 14 | 68.6% |
| DeepSeek V4.1 Flash | 41 | 42 | 13 | 49.4% |
| **Overall** | **244** | **104** | **42** | **70.1%** |

Ten of 400 generator/prompt pairs are indeterminate at panel aggregation. The prompt-cluster bootstrap reported in the paper is approximately **65.1%–75.0%**.

### Breadth replication: 20 configurations × 20 prompts

Twenty-four candidate configurations were screened **before quality judging** using only treatment-compliance criteria; 20 passed and were frozen into the breadth roster. The completed breadth study contains 800 generations and a fixed three-model mirrored judge panel.

- self-scored cleaner: **206**
- baseline cleaner: **149**
- ties: **31**
- resolved pairs: **386/400**
- directional self-score rate: **58.0%**
- model directions: **15 positive / 4 negative / 1 balanced** (`p=0.0192` sign test)
- developer-family directions: **9 positive / 3 negative / 1 balanced** (`p=0.146`)
- family/model/pair bootstrap 95% interval: **47.4%–67.4%**

A strict sensitivity check re-applies the original treatment-compliance rule to every breadth treatment output. It retains 380/400 treatment outputs and leaves the directional rate essentially unchanged: **199 vs. 144, 29 ties; 58.0%**.

Because DeepSeek V4.1 Flash appears in both studies, the combined experiments contain **23 distinct generator model names**, not 24 independent models.

### Human validation and interpretation

A small blind validation in a language native to the author is much less decisive than the AI panel: **7 self-scoring preferences, 5 baseline preferences, and 12 ties**. It does not establish a human-perceived quality improvement, but it provides no indication of systematic degradation. This is consistent with the paper's deliberately staged claim: the present study establishes that the added inline evaluation channel can coexist with generation without generally ruining output; whether the emitted numbers themselves are calibrated or useful control signals is a separate next question.

## Repository layout

```text
paper/
  v9 four-page-main-text LaTeX source and rendered PDF
experiments/main/
  exact 100-prompt primary-study runner, prompts, configs, tests, frozen run
experiments/breadth/
  24-candidate outcome-blind screen, frozen 20-model roster, exact breadth runner,
  full 800-generation run, mirrored judgments, provider records, and analysis
experiments/native_language_pilot/
  24-pair native-language pilot, AI judging, human-validation HTML, frozen run
human/
  blinded author validation JSON used in the paper
analysis/
  reproduce_paper_stats.py
```

## Reproduce the reported statistics without API calls

Requires only Python 3.10+ and the standard library:

```bash
python analysis/reproduce_paper_stats.py
```

This reconstructs the primary external-panel result, its prompt-cluster bootstrap, the breadth panel result, model/family direction checks, the deterministic family/model/pair bootstrap, the strict breadth sensitivity check, emitted-score negative result, and native-language pilot counts. The script contains hard assertions for the paper's headline values.

For a broader local check:

```bash
bash verify.sh
```

## Re-run the primary study

Set `OPENROUTER_API_KEY` in your environment. The repository contains no API key.

```bash
cd experiments/main
python -m unittest discover -s tests -v
bash run_smoke.sh
bash run_full.sh
```

The primary run uses 100 prompts × 4 generators × 2 conditions = **800 generation calls**, followed by mirrored judging. It is resumable via SQLite.

## Re-run the breadth protocol

See [`experiments/breadth/README.md`](experiments/breadth/README.md) for the exact screening and full-run procedure.

The frozen release includes:

- the 24 candidate definitions;
- provider resolution used for the run;
- the machine-readable outcome-blind screen report and frozen 20-model roster;
- the 20 breadth prompts and deterministic selection record;
- all 800 full-run generations;
- raw and resolved mirrored judgments;
- provider-match and treatment-compliance exports;
- the completed SQLite database and manifest;
- model- and family-level analysis outputs.

The original compliance-screen SQLite database itself was not included in the results archive supplied when this release was assembled; the frozen `screen_report.json`, `screen_report.md`, `models_screened.json`, screening code, and earlier v1 screen artifacts are included. This does not affect the completed breadth-effect dataset or its analysis, but the distinction is recorded explicitly rather than hidden.

## Native-language pilot

```bash
cd experiments/native_language_pilot
sh run.sh
```

The frozen pilot contains 24 blinded pairs (six per primary generator), mirrored AI judging, sentence-level self-scores, and the offline human-validation file.

## Reproducibility caveat

Many tested systems are proprietary or served through rapidly changing upstream stacks. This archive preserves prompts, route/provider records, generation text, score tags, judgments, manifests, and SQLite state, but exact future API reproduction is not guaranteed. The frozen data are sufficient to reproduce the reported statistics without making any API calls.

## Citation

See [`CITATION.cff`](CITATION.cff).

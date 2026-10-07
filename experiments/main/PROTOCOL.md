# Frozen protocol — matched anti-slop baseline vs self-scored baseline

## Hypothesis

Does explicit in-generation self-scoring improve or worsen prose **beyond the effect of simply instructing the model to avoid AI slop**?

## Two generation conditions

For every generator × prompt × replicate, the original user writing task is byte-for-byte identical. The conditions differ only in the system instruction.

### Baseline

The model is explicitly told to avoid AI-slop and to prefer concrete, natural, specific language. It does not self-score.

### Self-scored baseline

The model receives the same anti-slop instruction and additionally must append `<AI SCORE: n>` after every sentence, where 0 is very human-like and 100 is obviously AI-generated.

The exact prompts are frozen in `baseline_prompt.txt` and `selfscore_prompt.txt` and are also stored in each run manifest.

## No correction or branch selection

Self-scores never trigger rejection, regeneration, branching, best-of-N selection, or any other action. They are observational only.

## Completion requirement

A generation ending with `finish_reason=length` is not accepted into the experiment. It is retried once at a larger output ceiling (8,192 → 16,384 tokens by default). Failed and successful physical generation attempts are archived.

## Cleaning

Recognized `<AI SCORE: n>` material is stripped from treatment outputs. Conservative whitespace normalization is applied to both conditions. Raw outputs and parsed self-scores remain archived.

## Blind pairwise judging

Judges receive only:

1. the original writing task;
2. cleaned Answer A;
3. cleaned Answer B.

They are asked which complete answer sounds **more like stereotypical AI-generated slop**, with `A`, `B`, or `TIE` allowed. They are never told about baseline/self-scoring conditions.

A/B mapping is deterministic but randomized, and the default protocol judges both mirrored orders. A mirrored contradiction is recorded as `order_sensitive`, not forced into a winner.

## Judges

The default four-model panel uses every model as both generator and judge. For a given generator, its own fresh judging call is reported as a self-judge; the other three form the external panel.

## Primary statistics

For each generator and judging source:

- self-scored-cleaner count;
- baseline-cleaner count;
- tie count;
- order-sensitive count;
- self-scored-cleaner rate among decisive pairs;
- Wilson 95% CI;
- exact two-sided sign-test p-value;
- net self-score advantage.

## Run identity

The database stores a scientific-protocol fingerprint. If prompts, model roster, seed, generation/judging settings, or protocol text change, the runner refuses to mix the new protocol into the existing workspace. Use a new `--out` directory instead.


## Provider pinning

The confirmatory configuration pins each logical model to a single OpenRouter upstream provider (`openai`, `anthropic`, `google-ai-studio`, `deepseek`) with provider fallback disabled. This prevents baseline/self-scored differences from being confounded by endpoint changes.

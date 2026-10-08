# Criterion-matched inline self-scoring results

Each criterion compares the same optimization instruction with vs. without sentence-level self-scoring. Scores are stripped and never used downstream.

## Overall answer quality (primary)

| Criterion | Self-score | Objective only | Tie | Indet. | Self-score rate* | Wilson 95% CI | Prompt-bootstrap 95% CI | sign p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ai_likeness | 42 | 15 | 0 | 23 | 73.7% | 61.0%–83.4% | 66.0%–81.8% | 0.00046 |
| clarity | 19 | 25 | 0 | 36 | 43.2% | 29.7%–57.8% | 29.5%–59.0% | 0.4514 |
| relevance | 12 | 21 | 3 | 44 | 36.4% | 22.2%–53.4% | 20.7%–50.0% | 0.1628 |
| factuality | 22 | 15 | 2 | 41 | 59.5% | 43.5%–73.7% | 43.8%–75.7% | 0.324 |
| brevity | 32 | 16 | 1 | 31 | 66.7% | 52.5%–78.3% | 53.3%–80.4% | 0.0293 |

Descriptive pooled overall: 127 self-score vs 92 objective-only directional wins (58.0%).

## Target criterion (secondary)

| Criterion | Self-score | Objective only | Tie | Indet. | Self-score rate* | Wilson 95% CI | Prompt-bootstrap 95% CI | sign p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ai_likeness | 42 | 19 | 0 | 19 | 68.9% | 56.4%–79.1% | 59.7%–77.3% | 0.004444 |
| clarity | 24 | 17 | 0 | 39 | 58.5% | 43.4%–72.2% | 46.3%–73.0% | 0.3489 |
| relevance | 16 | 17 | 11 | 36 | 48.5% | 32.5%–64.8% | 32.1%–63.0% | 1 |
| factuality | 22 | 10 | 5 | 43 | 68.8% | 51.4%–82.0% | 51.4%–85.3% | 0.0501 |
| brevity | 40 | 20 | 0 | 20 | 66.7% | 54.1%–77.3% | 55.9%–76.7% | 0.01349 |

Descriptive pooled target: 144 self-score vs 83 objective-only directional wins (63.4%).

*Rates exclude ties and indeterminate pairs. Pooled rows are descriptive because criteria and model families are not independent replications.*

## Compliance

| Criterion | Arm | n | compliant | noncompliant | leaks | mean tags |
|---|---|---:|---:|---:|---:|---:|
| ai_likeness | objective_only | 80 | 80 | 0 | 0 | 0.00 |
| ai_likeness | selfscore | 80 | 80 | 0 | 0 | 6.89 |
| clarity | objective_only | 80 | 80 | 0 | 0 | 0.00 |
| clarity | selfscore | 80 | 80 | 0 | 0 | 6.89 |
| relevance | objective_only | 80 | 80 | 0 | 0 | 0.00 |
| relevance | selfscore | 80 | 80 | 0 | 0 | 6.61 |
| factuality | objective_only | 80 | 80 | 0 | 0 | 0.00 |
| factuality | selfscore | 80 | 80 | 0 | 0 | 6.94 |
| brevity | objective_only | 80 | 80 | 0 | 0 | 0.00 |
| brevity | selfscore | 80 | 80 | 0 | 0 | 6.58 |

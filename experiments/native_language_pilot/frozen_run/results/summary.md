# Russian self-scoring validation

Both generation arms receive the same explicit instruction to avoid AI-slop. The self-scored arm differs only by emitting <AI SCORE: n> after every sentence. Scores are stripped before AI and human pairwise judging.

## AI-panel results

- **self_judge / generator=claude-opus-5.5 / judge=claude-opus-5.5**: selfscore cleaner 5, baseline cleaner 1, tie 0, order-sensitive 0, missing 0; decisive selfscore-cleaner rate 83.3%, 95% CI [43.6%, 97.0%], sign-test p=0.2188.
- **external_judge / generator=claude-opus-5.5 / judge=gpt-5.6-sol**: selfscore cleaner 4, baseline cleaner 0, tie 0, order-sensitive 2, missing 0; decisive selfscore-cleaner rate 100.0%, 95% CI [51.0%, 100.0%], sign-test p=0.125.
- **external_judge / generator=claude-opus-5.5 / judge=gemini-3.1-pro-preview**: selfscore cleaner 1, baseline cleaner 0, tie 4, order-sensitive 1, missing 0; decisive selfscore-cleaner rate 100.0%, 95% CI [20.7%, 100.0%], sign-test p=1.
- **external_judge / generator=claude-opus-5.5 / judge=deepseek-v4.1-flash**: selfscore cleaner 4, baseline cleaner 0, tie 0, order-sensitive 2, missing 0; decisive selfscore-cleaner rate 100.0%, 95% CI [51.0%, 100.0%], sign-test p=0.125.
- **external_panel / generator=claude-opus-5.5 / judge=PANEL**: selfscore cleaner 5, baseline cleaner 0, tie 1, order-sensitive 0, missing 0; decisive selfscore-cleaner rate 100.0%, 95% CI [56.6%, 100.0%], sign-test p=0.0625.
- **self_judge / generator=deepseek-v4.1-flash / judge=deepseek-v4.1-flash**: selfscore cleaner 2, baseline cleaner 1, tie 0, order-sensitive 3, missing 0; decisive selfscore-cleaner rate 66.7%, 95% CI [20.8%, 93.9%], sign-test p=1.
- **external_judge / generator=deepseek-v4.1-flash / judge=gpt-5.6-sol**: selfscore cleaner 3, baseline cleaner 3, tie 0, order-sensitive 0, missing 0; decisive selfscore-cleaner rate 50.0%, 95% CI [18.8%, 81.2%], sign-test p=1.
- **external_judge / generator=deepseek-v4.1-flash / judge=claude-opus-5.5**: selfscore cleaner 3, baseline cleaner 1, tie 0, order-sensitive 2, missing 0; decisive selfscore-cleaner rate 75.0%, 95% CI [30.1%, 95.4%], sign-test p=0.625.
- **external_judge / generator=deepseek-v4.1-flash / judge=gemini-3.1-pro-preview**: selfscore cleaner 2, baseline cleaner 2, tie 0, order-sensitive 2, missing 0; decisive selfscore-cleaner rate 50.0%, 95% CI [15.0%, 85.0%], sign-test p=1.
- **external_panel / generator=deepseek-v4.1-flash / judge=PANEL**: selfscore cleaner 3, baseline cleaner 3, tie 0, order-sensitive 0, missing 0; decisive selfscore-cleaner rate 50.0%, 95% CI [18.8%, 81.2%], sign-test p=1.
- **self_judge / generator=gemini-3.1-pro-preview / judge=gemini-3.1-pro-preview**: selfscore cleaner 1, baseline cleaner 1, tie 3, order-sensitive 1, missing 0; decisive selfscore-cleaner rate 50.0%, 95% CI [9.5%, 90.5%], sign-test p=1.
- **external_judge / generator=gemini-3.1-pro-preview / judge=gpt-5.6-sol**: selfscore cleaner 3, baseline cleaner 0, tie 0, order-sensitive 3, missing 0; decisive selfscore-cleaner rate 100.0%, 95% CI [43.9%, 100.0%], sign-test p=0.25.
- **external_judge / generator=gemini-3.1-pro-preview / judge=claude-opus-5.5**: selfscore cleaner 4, baseline cleaner 1, tie 0, order-sensitive 1, missing 0; decisive selfscore-cleaner rate 80.0%, 95% CI [37.6%, 96.4%], sign-test p=0.375.
- **external_judge / generator=gemini-3.1-pro-preview / judge=deepseek-v4.1-flash**: selfscore cleaner 5, baseline cleaner 0, tie 0, order-sensitive 1, missing 0; decisive selfscore-cleaner rate 100.0%, 95% CI [56.6%, 100.0%], sign-test p=0.0625.
- **external_panel / generator=gemini-3.1-pro-preview / judge=PANEL**: selfscore cleaner 4, baseline cleaner 0, tie 1, order-sensitive 0, missing 1; decisive selfscore-cleaner rate 100.0%, 95% CI [51.0%, 100.0%], sign-test p=0.125.
- **self_judge / generator=gpt-5.6-sol / judge=gpt-5.6-sol**: selfscore cleaner 2, baseline cleaner 3, tie 0, order-sensitive 1, missing 0; decisive selfscore-cleaner rate 40.0%, 95% CI [11.8%, 76.9%], sign-test p=1.
- **external_judge / generator=gpt-5.6-sol / judge=claude-opus-5.5**: selfscore cleaner 2, baseline cleaner 3, tie 0, order-sensitive 1, missing 0; decisive selfscore-cleaner rate 40.0%, 95% CI [11.8%, 76.9%], sign-test p=1.
- **external_judge / generator=gpt-5.6-sol / judge=gemini-3.1-pro-preview**: selfscore cleaner 0, baseline cleaner 2, tie 1, order-sensitive 3, missing 0; decisive selfscore-cleaner rate 0.0%, 95% CI [0.0%, 65.8%], sign-test p=0.5.
- **external_judge / generator=gpt-5.6-sol / judge=deepseek-v4.1-flash**: selfscore cleaner 2, baseline cleaner 3, tie 0, order-sensitive 1, missing 0; decisive selfscore-cleaner rate 40.0%, 95% CI [11.8%, 76.9%], sign-test p=1.
- **external_panel / generator=gpt-5.6-sol / judge=PANEL**: selfscore cleaner 2, baseline cleaner 2, tie 2, order-sensitive 0, missing 0; decisive selfscore-cleaner rate 50.0%, 95% CI [15.0%, 85.0%], sign-test p=1.
- **external_panel_overall / generator=ALL / judge=PANEL**: selfscore cleaner 14, baseline cleaner 5, tie 4, order-sensitive 0, missing 1; decisive selfscore-cleaner rate 73.7%, 95% CI [51.2%, 88.2%], sign-test p=0.06357.

## Live self-score outputs

- **claude-opus-5.5**: 6 self-scored texts; mean tags/text=7.33; mean of per-text mean AI scores=23.1.
- **deepseek-v4.1-flash**: 6 self-scored texts; mean tags/text=7.00; mean of per-text mean AI scores=18.5.
- **gemini-3.1-pro-preview**: 6 self-scored texts; mean tags/text=6.33; mean of per-text mean AI scores=11.9.
- **gpt-5.6-sol**: 6 self-scored texts; mean tags/text=6.33; mean of per-text mean AI scores=9.9.

## Files for human comparison

- `ai_panel_pairs.csv`: one row per human-validation pair with external-panel and judge-level outcomes.
- `live_scores.csv`: every emitted sentence-level score.
- `live_score_summary.csv`: one row per self-scored text.
- `judgments_resolved.csv`: mirrored outcome for every judge/pair.
- `generations.csv`: raw and cleaned generation text.

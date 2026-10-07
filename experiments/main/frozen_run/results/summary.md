# Self-scoring effect on AI-slop style

Interpretation: `selfscore_cleaner` means the judge said the BASELINE answer was more AI-sloppy;
`baseline_cleaner` means the judge said the SELF-SCORED answer was more AI-sloppy.
Mirrored disagreements are recorded as `order_sensitive`, not forced into either condition.

## Primary summaries

- **self_judge / generator=claude-opus-5.5 / judge=claude-opus-5.5**: selfscore cleaner 67, baseline cleaner 18, tie 0, order-sensitive 15; decisive selfscore-cleaner rate 78.8% 95% CI [69.0%, 86.2%], exact sign-test p=8.412e-08.
- **external_judge / generator=claude-opus-5.5 / judge=deepseek-v4.1-flash**: selfscore cleaner 72, baseline cleaner 8, tie 0, order-sensitive 19; decisive selfscore-cleaner rate 90.0% 95% CI [81.5%, 94.8%], exact sign-test p=5.375e-14.
- **external_judge / generator=claude-opus-5.5 / judge=gemini-3.1-pro-preview**: selfscore cleaner 27, baseline cleaner 2, tie 44, order-sensitive 27; decisive selfscore-cleaner rate 93.1% 95% CI [78.0%, 98.1%], exact sign-test p=1.624e-06.
- **external_judge / generator=claude-opus-5.5 / judge=gpt-5.6-sol**: selfscore cleaner 71, baseline cleaner 12, tie 0, order-sensitive 17; decisive selfscore-cleaner rate 85.5% 95% CI [76.4%, 91.5%], exact sign-test p=2.395e-11.
- **external_panel / generator=claude-opus-5.5 / judge=PANEL**: selfscore cleaner 78, baseline cleaner 14, tie 7, order-sensitive 0; decisive selfscore-cleaner rate 84.8% 95% CI [76.1%, 90.7%], exact sign-test p=6.162e-12.
- **self_judge / generator=deepseek-v4.1-flash / judge=deepseek-v4.1-flash**: selfscore cleaner 31, baseline cleaner 37, tie 0, order-sensitive 32; decisive selfscore-cleaner rate 45.6% 95% CI [34.3%, 57.3%], exact sign-test p=0.5446.
- **external_judge / generator=deepseek-v4.1-flash / judge=claude-opus-5.5**: selfscore cleaner 43, baseline cleaner 39, tie 0, order-sensitive 18; decisive selfscore-cleaner rate 52.4% 95% CI [41.8%, 62.9%], exact sign-test p=0.7407.
- **external_judge / generator=deepseek-v4.1-flash / judge=gemini-3.1-pro-preview**: selfscore cleaner 16, baseline cleaner 27, tie 19, order-sensitive 38; decisive selfscore-cleaner rate 37.2% 95% CI [24.4%, 52.1%], exact sign-test p=0.1263.
- **external_judge / generator=deepseek-v4.1-flash / judge=gpt-5.6-sol**: selfscore cleaner 35, baseline cleaner 42, tie 0, order-sensitive 23; decisive selfscore-cleaner rate 45.5% 95% CI [34.8%, 56.5%], exact sign-test p=0.4944.
- **external_panel / generator=deepseek-v4.1-flash / judge=PANEL**: selfscore cleaner 41, baseline cleaner 42, tie 13, order-sensitive 0; decisive selfscore-cleaner rate 49.4% 95% CI [38.9%, 59.9%], exact sign-test p=1.
- **self_judge / generator=gemini-3.1-pro-preview / judge=gemini-3.1-pro-preview**: selfscore cleaner 41, baseline cleaner 5, tie 35, order-sensitive 19; decisive selfscore-cleaner rate 89.1% 95% CI [77.0%, 95.3%], exact sign-test p=4.406e-08.
- **external_judge / generator=gemini-3.1-pro-preview / judge=claude-opus-5.5**: selfscore cleaner 67, baseline cleaner 16, tie 0, order-sensitive 17; decisive selfscore-cleaner rate 80.7% 95% CI [71.0%, 87.8%], exact sign-test p=1.389e-08.
- **external_judge / generator=gemini-3.1-pro-preview / judge=deepseek-v4.1-flash**: selfscore cleaner 57, baseline cleaner 16, tie 0, order-sensitive 27; decisive selfscore-cleaner rate 78.1% 95% CI [67.3%, 86.0%], exact sign-test p=1.526e-06.
- **external_judge / generator=gemini-3.1-pro-preview / judge=gpt-5.6-sol**: selfscore cleaner 52, baseline cleaner 20, tie 0, order-sensitive 28; decisive selfscore-cleaner rate 72.2% 95% CI [61.0%, 81.2%], exact sign-test p=0.0002077.
- **external_panel / generator=gemini-3.1-pro-preview / judge=PANEL**: selfscore cleaner 66, baseline cleaner 21, tie 8, order-sensitive 0; decisive selfscore-cleaner rate 75.9% 95% CI [65.9%, 83.6%], exact sign-test p=1.41e-06.
- **self_judge / generator=gpt-5.6-sol / judge=gpt-5.6-sol**: selfscore cleaner 45, baseline cleaner 23, tie 1, order-sensitive 31; decisive selfscore-cleaner rate 66.2% 95% CI [54.3%, 76.3%], exact sign-test p=0.01034.
- **external_judge / generator=gpt-5.6-sol / judge=claude-opus-5.5**: selfscore cleaner 51, baseline cleaner 29, tie 0, order-sensitive 20; decisive selfscore-cleaner rate 63.7% 95% CI [52.8%, 73.4%], exact sign-test p=0.01832.
- **external_judge / generator=gpt-5.6-sol / judge=deepseek-v4.1-flash**: selfscore cleaner 57, baseline cleaner 25, tie 1, order-sensitive 17; decisive selfscore-cleaner rate 69.5% 95% CI [58.9%, 78.4%], exact sign-test p=0.0005347.
- **external_judge / generator=gpt-5.6-sol / judge=gemini-3.1-pro-preview**: selfscore cleaner 25, baseline cleaner 16, tie 34, order-sensitive 25; decisive selfscore-cleaner rate 61.0% 95% CI [45.7%, 74.3%], exact sign-test p=0.211.
- **external_panel / generator=gpt-5.6-sol / judge=PANEL**: selfscore cleaner 59, baseline cleaner 27, tie 14, order-sensitive 0; decisive selfscore-cleaner rate 68.6% 95% CI [58.2%, 77.4%], exact sign-test p=0.0007317.
- **external_panel_overall / generator=ALL / judge=PANEL**: selfscore cleaner 244, baseline cleaner 104, tie 42, order-sensitive 0; decisive selfscore-cleaner rate 70.1% 95% CI [65.1%, 74.7%], exact sign-test p=4.203e-14.

## Self-score manipulation check

- **claude-opus-5.5**: 100/100 emitted at least one valid score tag; 100/100 emitted at least five; mean tags=7.51; post-strip leaks=0.
- **deepseek-v4.1-flash**: 100/100 emitted at least one valid score tag; 100/100 emitted at least five; mean tags=7.13; post-strip leaks=0.
- **gemini-3.1-pro-preview**: 100/100 emitted at least one valid score tag; 100/100 emitted at least five; mean tags=6.58; post-strip leaks=0.
- **gpt-5.6-sol**: 100/100 emitted at least one valid score tag; 100/100 emitted at least five; mean tags=6.05; post-strip leaks=0.

## Generation provider match

- **claude-opus-5.5**: 100/100 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **deepseek-v4.1-flash**: 100/100 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **gemini-3.1-pro-preview**: 100/100 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **gpt-5.6-sol**: 100/100 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).

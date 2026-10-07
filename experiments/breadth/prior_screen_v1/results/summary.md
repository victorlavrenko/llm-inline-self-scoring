# Self-scoring effect on AI-slop style

Interpretation: `selfscore_cleaner` means the judge said the BASELINE answer was more AI-sloppy;
`baseline_cleaner` means the judge said the SELF-SCORED answer was more AI-sloppy.
Mirrored disagreements are recorded as `order_sensitive`, not forced into either condition.

## Primary summaries

- **external_judge / generator=deepseek-v3.2 / judge=claude-opus-5.5**: selfscore cleaner 1, baseline cleaner 0, tie 0, order-sensitive 1; decisive selfscore-cleaner rate 100.0% 95% CI [20.7%, 100.0%], exact sign-test p=1.
- **external_judge / generator=deepseek-v3.2 / judge=gemini-3.1-pro-preview**: selfscore cleaner 1, baseline cleaner 0, tie 1, order-sensitive 0; decisive selfscore-cleaner rate 100.0% 95% CI [20.7%, 100.0%], exact sign-test p=1.
- **external_judge / generator=deepseek-v3.2 / judge=gpt-5.6-sol**: selfscore cleaner 1, baseline cleaner 0, tie 0, order-sensitive 1; decisive selfscore-cleaner rate 100.0% 95% CI [20.7%, 100.0%], exact sign-test p=1.
- **external_panel / generator=deepseek-v3.2 / judge=PANEL**: selfscore cleaner 1, baseline cleaner 0, tie 1, order-sensitive 0; decisive selfscore-cleaner rate 100.0% 95% CI [20.7%, 100.0%], exact sign-test p=1.
- **external_judge / generator=gemma-3-12b-it / judge=claude-opus-5.5**: selfscore cleaner 1, baseline cleaner 1, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 50.0% 95% CI [9.5%, 90.5%], exact sign-test p=1.
- **external_judge / generator=gemma-3-12b-it / judge=gemini-3.1-pro-preview**: selfscore cleaner 1, baseline cleaner 0, tie 0, order-sensitive 1; decisive selfscore-cleaner rate 100.0% 95% CI [20.7%, 100.0%], exact sign-test p=1.
- **external_judge / generator=gemma-3-12b-it / judge=gpt-5.6-sol**: selfscore cleaner 0, baseline cleaner 1, tie 0, order-sensitive 1; decisive selfscore-cleaner rate 0.0% 95% CI [0.0%, 79.3%], exact sign-test p=1.
- **external_panel / generator=gemma-3-12b-it / judge=PANEL**: selfscore cleaner 1, baseline cleaner 1, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 50.0% 95% CI [9.5%, 90.5%], exact sign-test p=1.
- **external_judge / generator=glm-5.3-flash / judge=claude-opus-5.5**: selfscore cleaner 1, baseline cleaner 0, tie 0, order-sensitive 1; decisive selfscore-cleaner rate 100.0% 95% CI [20.7%, 100.0%], exact sign-test p=1.
- **external_judge / generator=glm-5.3-flash / judge=gemini-3.1-pro-preview**: selfscore cleaner 1, baseline cleaner 1, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 50.0% 95% CI [9.5%, 90.5%], exact sign-test p=1.
- **external_judge / generator=glm-5.3-flash / judge=gpt-5.6-sol**: selfscore cleaner 2, baseline cleaner 0, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 100.0% 95% CI [34.2%, 100.0%], exact sign-test p=0.5.
- **external_panel / generator=glm-5.3-flash / judge=PANEL**: selfscore cleaner 1, baseline cleaner 0, tie 1, order-sensitive 0; decisive selfscore-cleaner rate 100.0% 95% CI [20.7%, 100.0%], exact sign-test p=1.
- **external_judge / generator=gpt-oss-120b / judge=claude-opus-5.5**: selfscore cleaner 2, baseline cleaner 0, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 100.0% 95% CI [34.2%, 100.0%], exact sign-test p=0.5.
- **external_judge / generator=gpt-oss-120b / judge=gemini-3.1-pro-preview**: selfscore cleaner 1, baseline cleaner 0, tie 1, order-sensitive 0; decisive selfscore-cleaner rate 100.0% 95% CI [20.7%, 100.0%], exact sign-test p=1.
- **external_judge / generator=gpt-oss-120b / judge=gpt-5.6-sol**: selfscore cleaner 1, baseline cleaner 0, tie 0, order-sensitive 1; decisive selfscore-cleaner rate 100.0% 95% CI [20.7%, 100.0%], exact sign-test p=1.
- **external_panel / generator=gpt-oss-120b / judge=PANEL**: selfscore cleaner 2, baseline cleaner 0, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 100.0% 95% CI [34.2%, 100.0%], exact sign-test p=0.5.
- **external_judge / generator=kimi-k2.5 / judge=claude-opus-5.5**: selfscore cleaner 2, baseline cleaner 0, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 100.0% 95% CI [34.2%, 100.0%], exact sign-test p=0.5.
- **external_judge / generator=kimi-k2.5 / judge=gemini-3.1-pro-preview**: selfscore cleaner 2, baseline cleaner 0, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 100.0% 95% CI [34.2%, 100.0%], exact sign-test p=0.5.
- **external_judge / generator=kimi-k2.5 / judge=gpt-5.6-sol**: selfscore cleaner 2, baseline cleaner 0, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 100.0% 95% CI [34.2%, 100.0%], exact sign-test p=0.5.
- **external_panel / generator=kimi-k2.5 / judge=PANEL**: selfscore cleaner 2, baseline cleaner 0, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 100.0% 95% CI [34.2%, 100.0%], exact sign-test p=0.5.
- **external_judge / generator=llama-3.3-70b-instruct / judge=claude-opus-5.5**: selfscore cleaner 0, baseline cleaner 2, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 0.0% 95% CI [0.0%, 65.8%], exact sign-test p=0.5.
- **external_judge / generator=llama-3.3-70b-instruct / judge=gemini-3.1-pro-preview**: selfscore cleaner 0, baseline cleaner 1, tie 0, order-sensitive 1; decisive selfscore-cleaner rate 0.0% 95% CI [0.0%, 79.3%], exact sign-test p=1.
- **external_judge / generator=llama-3.3-70b-instruct / judge=gpt-5.6-sol**: selfscore cleaner 0, baseline cleaner 2, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 0.0% 95% CI [0.0%, 65.8%], exact sign-test p=0.5.
- **external_panel / generator=llama-3.3-70b-instruct / judge=PANEL**: selfscore cleaner 0, baseline cleaner 2, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 0.0% 95% CI [0.0%, 65.8%], exact sign-test p=0.5.
- **external_judge / generator=minimax-m3 / judge=claude-opus-5.5**: selfscore cleaner 1, baseline cleaner 1, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 50.0% 95% CI [9.5%, 90.5%], exact sign-test p=1.
- **external_judge / generator=minimax-m3 / judge=gemini-3.1-pro-preview**: selfscore cleaner 1, baseline cleaner 1, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 50.0% 95% CI [9.5%, 90.5%], exact sign-test p=1.
- **external_judge / generator=minimax-m3 / judge=gpt-5.6-sol**: selfscore cleaner 1, baseline cleaner 1, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 50.0% 95% CI [9.5%, 90.5%], exact sign-test p=1.
- **external_panel / generator=minimax-m3 / judge=PANEL**: selfscore cleaner 1, baseline cleaner 1, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 50.0% 95% CI [9.5%, 90.5%], exact sign-test p=1.
- **external_judge / generator=ministral-14b-2512 / judge=claude-opus-5.5**: selfscore cleaner 1, baseline cleaner 1, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 50.0% 95% CI [9.5%, 90.5%], exact sign-test p=1.
- **external_judge / generator=ministral-14b-2512 / judge=gemini-3.1-pro-preview**: selfscore cleaner 1, baseline cleaner 0, tie 0, order-sensitive 1; decisive selfscore-cleaner rate 100.0% 95% CI [20.7%, 100.0%], exact sign-test p=1.
- **external_judge / generator=ministral-14b-2512 / judge=gpt-5.6-sol**: selfscore cleaner 0, baseline cleaner 1, tie 0, order-sensitive 1; decisive selfscore-cleaner rate 0.0% 95% CI [0.0%, 79.3%], exact sign-test p=1.
- **external_panel / generator=ministral-14b-2512 / judge=PANEL**: selfscore cleaner 1, baseline cleaner 1, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 50.0% 95% CI [9.5%, 90.5%], exact sign-test p=1.
- **external_judge / generator=nemotron-3.5-lightning / judge=claude-opus-5.5**: selfscore cleaner 0, baseline cleaner 2, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 0.0% 95% CI [0.0%, 65.8%], exact sign-test p=0.5.
- **external_judge / generator=nemotron-3.5-lightning / judge=gemini-3.1-pro-preview**: selfscore cleaner 0, baseline cleaner 1, tie 1, order-sensitive 0; decisive selfscore-cleaner rate 0.0% 95% CI [0.0%, 79.3%], exact sign-test p=1.
- **external_judge / generator=nemotron-3.5-lightning / judge=gpt-5.6-sol**: selfscore cleaner 0, baseline cleaner 2, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 0.0% 95% CI [0.0%, 65.8%], exact sign-test p=0.5.
- **external_panel / generator=nemotron-3.5-lightning / judge=PANEL**: selfscore cleaner 0, baseline cleaner 2, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 0.0% 95% CI [0.0%, 65.8%], exact sign-test p=0.5.
- **external_judge / generator=qwen3-30b-a3b-instruct-2507 / judge=claude-opus-5.5**: selfscore cleaner 0, baseline cleaner 2, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 0.0% 95% CI [0.0%, 65.8%], exact sign-test p=0.5.
- **external_judge / generator=qwen3-30b-a3b-instruct-2507 / judge=gemini-3.1-pro-preview**: selfscore cleaner 0, baseline cleaner 0, tie 1, order-sensitive 1; decisive selfscore-cleaner rate NA 95% CI NA, exact sign-test p=NA.
- **external_judge / generator=qwen3-30b-a3b-instruct-2507 / judge=gpt-5.6-sol**: selfscore cleaner 0, baseline cleaner 2, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 0.0% 95% CI [0.0%, 65.8%], exact sign-test p=0.5.
- **external_panel / generator=qwen3-30b-a3b-instruct-2507 / judge=PANEL**: selfscore cleaner 0, baseline cleaner 2, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 0.0% 95% CI [0.0%, 65.8%], exact sign-test p=0.5.
- **external_judge / generator=qwen3.7-flash / judge=claude-opus-5.5**: selfscore cleaner 1, baseline cleaner 1, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 50.0% 95% CI [9.5%, 90.5%], exact sign-test p=1.
- **external_judge / generator=qwen3.7-flash / judge=gemini-3.1-pro-preview**: selfscore cleaner 1, baseline cleaner 0, tie 0, order-sensitive 1; decisive selfscore-cleaner rate 100.0% 95% CI [20.7%, 100.0%], exact sign-test p=1.
- **external_judge / generator=qwen3.7-flash / judge=gpt-5.6-sol**: selfscore cleaner 1, baseline cleaner 1, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 50.0% 95% CI [9.5%, 90.5%], exact sign-test p=1.
- **external_panel / generator=qwen3.7-flash / judge=PANEL**: selfscore cleaner 1, baseline cleaner 1, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 50.0% 95% CI [9.5%, 90.5%], exact sign-test p=1.
- **external_panel_overall / generator=ALL / judge=PANEL**: selfscore cleaner 10, baseline cleaner 10, tie 2, order-sensitive 0; decisive selfscore-cleaner rate 50.0% 95% CI [29.9%, 70.1%], exact sign-test p=1.

## Self-score manipulation check

- **deepseek-v3.2**: 2/2 emitted at least one valid score tag; 2/2 emitted at least five; mean tags=8.00; post-strip leaks=0.
- **gemma-3-12b-it**: 2/2 emitted at least one valid score tag; 2/2 emitted at least five; mean tags=7.00; post-strip leaks=0.
- **glm-5.3-flash**: 2/2 emitted at least one valid score tag; 2/2 emitted at least five; mean tags=7.50; post-strip leaks=0.
- **gpt-oss-120b**: 2/2 emitted at least one valid score tag; 2/2 emitted at least five; mean tags=6.00; post-strip leaks=0.
- **kimi-k2.5**: 2/2 emitted at least one valid score tag; 2/2 emitted at least five; mean tags=6.00; post-strip leaks=0.
- **llama-3.3-70b-instruct**: 1/2 emitted at least one valid score tag; 0/2 emitted at least five; mean tags=0.50; post-strip leaks=0.
- **minimax-m3**: 2/2 emitted at least one valid score tag; 2/2 emitted at least five; mean tags=6.50; post-strip leaks=0.
- **ministral-14b-2512**: 2/2 emitted at least one valid score tag; 0/2 emitted at least five; mean tags=1.00; post-strip leaks=0.
- **nemotron-3.5-lightning**: 2/2 emitted at least one valid score tag; 0/2 emitted at least five; mean tags=1.00; post-strip leaks=0.
- **qwen3-30b-a3b-instruct-2507**: 2/2 emitted at least one valid score tag; 1/2 emitted at least five; mean tags=4.50; post-strip leaks=0.
- **qwen3.7-flash**: 2/2 emitted at least one valid score tag; 2/2 emitted at least five; mean tags=6.00; post-strip leaks=0.

## Generation provider match

- **deepseek-v3.2**: 2/2 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **gemma-3-12b-it**: 2/2 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **glm-5.3-flash**: 2/2 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **gpt-oss-120b**: 2/2 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **kimi-k2.5**: 2/2 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **llama-3.3-70b-instruct**: 2/2 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **minimax-m3**: 2/2 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **ministral-14b-2512**: 2/2 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **nemotron-3.5-lightning**: 2/2 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **qwen3-30b-a3b-instruct-2507**: 2/2 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **qwen3.7-flash**: 2/2 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).

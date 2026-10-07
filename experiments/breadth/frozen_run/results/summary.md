# Self-scoring effect on AI-slop style

Interpretation: `selfscore_cleaner` means the judge said the BASELINE answer was more AI-sloppy;
`baseline_cleaner` means the judge said the SELF-SCORED answer was more AI-sloppy.
Mirrored disagreements are recorded as `order_sensitive`, not forced into either condition.

## Primary summaries

- **external_judge / generator=command-a-plus / judge=claude-opus-5.5**: selfscore cleaner 6, baseline cleaner 12, tie 0, order-sensitive 2; decisive selfscore-cleaner rate 33.3% 95% CI [16.3%, 56.3%], exact sign-test p=0.2379.
- **external_judge / generator=command-a-plus / judge=gemini-3.1-pro-preview**: selfscore cleaner 3, baseline cleaner 10, tie 4, order-sensitive 3; decisive selfscore-cleaner rate 23.1% 95% CI [8.2%, 50.3%], exact sign-test p=0.09229.
- **external_judge / generator=command-a-plus / judge=gpt-5.6-sol**: selfscore cleaner 5, baseline cleaner 12, tie 0, order-sensitive 3; decisive selfscore-cleaner rate 29.4% 95% CI [13.3%, 53.1%], exact sign-test p=0.1435.
- **external_panel / generator=command-a-plus / judge=PANEL**: selfscore cleaner 6, baseline cleaner 13, tie 1, order-sensitive 0; decisive selfscore-cleaner rate 31.6% 95% CI [15.4%, 54.0%], exact sign-test p=0.1671.
- **external_judge / generator=deepseek-v3.2 / judge=claude-opus-5.5**: selfscore cleaner 10, baseline cleaner 7, tie 0, order-sensitive 3; decisive selfscore-cleaner rate 58.8% 95% CI [36.0%, 78.4%], exact sign-test p=0.6291.
- **external_judge / generator=deepseek-v3.2 / judge=gemini-3.1-pro-preview**: selfscore cleaner 7, baseline cleaner 5, tie 1, order-sensitive 7; decisive selfscore-cleaner rate 58.3% 95% CI [32.0%, 80.7%], exact sign-test p=0.7744.
- **external_judge / generator=deepseek-v3.2 / judge=gpt-5.6-sol**: selfscore cleaner 3, baseline cleaner 7, tie 0, order-sensitive 10; decisive selfscore-cleaner rate 30.0% 95% CI [10.8%, 60.3%], exact sign-test p=0.3438.
- **external_panel / generator=deepseek-v3.2 / judge=PANEL**: selfscore cleaner 10, baseline cleaner 7, tie 2, order-sensitive 0; decisive selfscore-cleaner rate 58.8% 95% CI [36.0%, 78.4%], exact sign-test p=0.6291.
- **external_judge / generator=deepseek-v4-flash-0731 / judge=claude-opus-5.5**: selfscore cleaner 9, baseline cleaner 8, tie 0, order-sensitive 3; decisive selfscore-cleaner rate 52.9% 95% CI [31.0%, 73.8%], exact sign-test p=1.
- **external_judge / generator=deepseek-v4-flash-0731 / judge=gemini-3.1-pro-preview**: selfscore cleaner 6, baseline cleaner 4, tie 4, order-sensitive 6; decisive selfscore-cleaner rate 60.0% 95% CI [31.3%, 83.2%], exact sign-test p=0.7539.
- **external_judge / generator=deepseek-v4-flash-0731 / judge=gpt-5.6-sol**: selfscore cleaner 6, baseline cleaner 8, tie 0, order-sensitive 6; decisive selfscore-cleaner rate 42.9% 95% CI [21.4%, 67.4%], exact sign-test p=0.7905.
- **external_panel / generator=deepseek-v4-flash-0731 / judge=PANEL**: selfscore cleaner 9, baseline cleaner 10, tie 1, order-sensitive 0; decisive selfscore-cleaner rate 47.4% 95% CI [27.3%, 68.3%], exact sign-test p=1.
- **external_judge / generator=deepseek-v4.1-flash / judge=claude-opus-5.5**: selfscore cleaner 6, baseline cleaner 11, tie 0, order-sensitive 3; decisive selfscore-cleaner rate 35.3% 95% CI [17.3%, 58.7%], exact sign-test p=0.3323.
- **external_judge / generator=deepseek-v4.1-flash / judge=gemini-3.1-pro-preview**: selfscore cleaner 4, baseline cleaner 7, tie 3, order-sensitive 6; decisive selfscore-cleaner rate 36.4% 95% CI [15.2%, 64.6%], exact sign-test p=0.5488.
- **external_judge / generator=deepseek-v4.1-flash / judge=gpt-5.6-sol**: selfscore cleaner 3, baseline cleaner 14, tie 0, order-sensitive 3; decisive selfscore-cleaner rate 17.6% 95% CI [6.2%, 41.0%], exact sign-test p=0.01273.
- **external_panel / generator=deepseek-v4.1-flash / judge=PANEL**: selfscore cleaner 5, baseline cleaner 15, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 25.0% 95% CI [11.2%, 46.9%], exact sign-test p=0.04139.
- **external_judge / generator=gemma-3-12b-it / judge=claude-opus-5.5**: selfscore cleaner 10, baseline cleaner 3, tie 0, order-sensitive 3; decisive selfscore-cleaner rate 76.9% 95% CI [49.7%, 91.8%], exact sign-test p=0.09229.
- **external_judge / generator=gemma-3-12b-it / judge=gemini-3.1-pro-preview**: selfscore cleaner 14, baseline cleaner 1, tie 0, order-sensitive 1; decisive selfscore-cleaner rate 93.3% 95% CI [70.2%, 98.8%], exact sign-test p=0.0009766.
- **external_judge / generator=gemma-3-12b-it / judge=gpt-5.6-sol**: selfscore cleaner 10, baseline cleaner 5, tie 0, order-sensitive 1; decisive selfscore-cleaner rate 66.7% 95% CI [41.7%, 84.8%], exact sign-test p=0.3018.
- **external_panel / generator=gemma-3-12b-it / judge=PANEL**: selfscore cleaner 11, baseline cleaner 3, tie 2, order-sensitive 0; decisive selfscore-cleaner rate 78.6% 95% CI [52.4%, 92.4%], exact sign-test p=0.05737.
- **external_judge / generator=glm-5.3 / judge=claude-opus-5.5**: selfscore cleaner 8, baseline cleaner 6, tie 0, order-sensitive 6; decisive selfscore-cleaner rate 57.1% 95% CI [32.6%, 78.6%], exact sign-test p=0.7905.
- **external_judge / generator=glm-5.3 / judge=gemini-3.1-pro-preview**: selfscore cleaner 4, baseline cleaner 2, tie 6, order-sensitive 8; decisive selfscore-cleaner rate 66.7% 95% CI [30.0%, 90.3%], exact sign-test p=0.6875.
- **external_judge / generator=glm-5.3 / judge=gpt-5.6-sol**: selfscore cleaner 11, baseline cleaner 5, tie 0, order-sensitive 4; decisive selfscore-cleaner rate 68.8% 95% CI [44.4%, 85.8%], exact sign-test p=0.2101.
- **external_panel / generator=glm-5.3 / judge=PANEL**: selfscore cleaner 11, baseline cleaner 7, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 61.1% 95% CI [38.6%, 79.7%], exact sign-test p=0.4807.
- **external_judge / generator=glm-5.3-flash / judge=claude-opus-5.5**: selfscore cleaner 12, baseline cleaner 4, tie 0, order-sensitive 4; decisive selfscore-cleaner rate 75.0% 95% CI [50.5%, 89.8%], exact sign-test p=0.07681.
- **external_judge / generator=glm-5.3-flash / judge=gemini-3.1-pro-preview**: selfscore cleaner 4, baseline cleaner 2, tie 8, order-sensitive 6; decisive selfscore-cleaner rate 66.7% 95% CI [30.0%, 90.3%], exact sign-test p=0.6875.
- **external_judge / generator=glm-5.3-flash / judge=gpt-5.6-sol**: selfscore cleaner 8, baseline cleaner 5, tie 0, order-sensitive 7; decisive selfscore-cleaner rate 61.5% 95% CI [35.5%, 82.3%], exact sign-test p=0.5811.
- **external_panel / generator=glm-5.3-flash / judge=PANEL**: selfscore cleaner 11, baseline cleaner 6, tie 2, order-sensitive 0; decisive selfscore-cleaner rate 64.7% 95% CI [41.3%, 82.7%], exact sign-test p=0.3323.
- **external_judge / generator=gpt-oss-120b / judge=claude-opus-5.5**: selfscore cleaner 11, baseline cleaner 7, tie 0, order-sensitive 2; decisive selfscore-cleaner rate 61.1% 95% CI [38.6%, 79.7%], exact sign-test p=0.4807.
- **external_judge / generator=gpt-oss-120b / judge=gemini-3.1-pro-preview**: selfscore cleaner 4, baseline cleaner 6, tie 2, order-sensitive 8; decisive selfscore-cleaner rate 40.0% 95% CI [16.8%, 68.7%], exact sign-test p=0.7539.
- **external_judge / generator=gpt-oss-120b / judge=gpt-5.6-sol**: selfscore cleaner 7, baseline cleaner 7, tie 0, order-sensitive 6; decisive selfscore-cleaner rate 50.0% 95% CI [26.8%, 73.2%], exact sign-test p=1.
- **external_panel / generator=gpt-oss-120b / judge=PANEL**: selfscore cleaner 10, baseline cleaner 7, tie 2, order-sensitive 0; decisive selfscore-cleaner rate 58.8% 95% CI [36.0%, 78.4%], exact sign-test p=0.6291.
- **external_judge / generator=grok-4.7 / judge=claude-opus-5.5**: selfscore cleaner 14, baseline cleaner 5, tie 0, order-sensitive 1; decisive selfscore-cleaner rate 73.7% 95% CI [51.2%, 88.2%], exact sign-test p=0.06357.
- **external_judge / generator=grok-4.7 / judge=gemini-3.1-pro-preview**: selfscore cleaner 5, baseline cleaner 1, tie 9, order-sensitive 5; decisive selfscore-cleaner rate 83.3% 95% CI [43.6%, 97.0%], exact sign-test p=0.2188.
- **external_judge / generator=grok-4.7 / judge=gpt-5.6-sol**: selfscore cleaner 15, baseline cleaner 3, tie 0, order-sensitive 2; decisive selfscore-cleaner rate 83.3% 95% CI [60.8%, 94.2%], exact sign-test p=0.007538.
- **external_panel / generator=grok-4.7 / judge=PANEL**: selfscore cleaner 14, baseline cleaner 4, tie 2, order-sensitive 0; decisive selfscore-cleaner rate 77.8% 95% CI [54.8%, 91.0%], exact sign-test p=0.03088.
- **external_judge / generator=hy4-preview / judge=claude-opus-5.5**: selfscore cleaner 9, baseline cleaner 9, tie 0, order-sensitive 2; decisive selfscore-cleaner rate 50.0% 95% CI [29.0%, 71.0%], exact sign-test p=1.
- **external_judge / generator=hy4-preview / judge=gemini-3.1-pro-preview**: selfscore cleaner 7, baseline cleaner 7, tie 0, order-sensitive 6; decisive selfscore-cleaner rate 50.0% 95% CI [26.8%, 73.2%], exact sign-test p=1.
- **external_judge / generator=hy4-preview / judge=gpt-5.6-sol**: selfscore cleaner 6, baseline cleaner 8, tie 0, order-sensitive 6; decisive selfscore-cleaner rate 42.9% 95% CI [21.4%, 67.4%], exact sign-test p=0.7905.
- **external_panel / generator=hy4-preview / judge=PANEL**: selfscore cleaner 8, baseline cleaner 8, tie 3, order-sensitive 0; decisive selfscore-cleaner rate 50.0% 95% CI [28.0%, 72.0%], exact sign-test p=1.
- **external_judge / generator=kimi-k2.5 / judge=claude-opus-5.5**: selfscore cleaner 11, baseline cleaner 8, tie 0, order-sensitive 1; decisive selfscore-cleaner rate 57.9% 95% CI [36.3%, 76.9%], exact sign-test p=0.6476.
- **external_judge / generator=kimi-k2.5 / judge=gemini-3.1-pro-preview**: selfscore cleaner 6, baseline cleaner 6, tie 5, order-sensitive 3; decisive selfscore-cleaner rate 50.0% 95% CI [25.4%, 74.6%], exact sign-test p=1.
- **external_judge / generator=kimi-k2.5 / judge=gpt-5.6-sol**: selfscore cleaner 9, baseline cleaner 8, tie 0, order-sensitive 3; decisive selfscore-cleaner rate 52.9% 95% CI [31.0%, 73.8%], exact sign-test p=1.
- **external_panel / generator=kimi-k2.5 / judge=PANEL**: selfscore cleaner 12, baseline cleaner 8, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 60.0% 95% CI [38.7%, 78.1%], exact sign-test p=0.5034.
- **external_judge / generator=llama-4-maverick / judge=claude-opus-5.5**: selfscore cleaner 9, baseline cleaner 7, tie 0, order-sensitive 4; decisive selfscore-cleaner rate 56.2% 95% CI [33.2%, 76.9%], exact sign-test p=0.8036.
- **external_judge / generator=llama-4-maverick / judge=gemini-3.1-pro-preview**: selfscore cleaner 7, baseline cleaner 1, tie 8, order-sensitive 4; decisive selfscore-cleaner rate 87.5% 95% CI [52.9%, 97.8%], exact sign-test p=0.07031.
- **external_judge / generator=llama-4-maverick / judge=gpt-5.6-sol**: selfscore cleaner 8, baseline cleaner 4, tie 0, order-sensitive 8; decisive selfscore-cleaner rate 66.7% 95% CI [39.1%, 86.2%], exact sign-test p=0.3877.
- **external_panel / generator=llama-4-maverick / judge=PANEL**: selfscore cleaner 12, baseline cleaner 7, tie 1, order-sensitive 0; decisive selfscore-cleaner rate 63.2% 95% CI [41.0%, 80.9%], exact sign-test p=0.3593.
- **external_judge / generator=mimo-v2.6-flash / judge=claude-opus-5.5**: selfscore cleaner 6, baseline cleaner 8, tie 0, order-sensitive 6; decisive selfscore-cleaner rate 42.9% 95% CI [21.4%, 67.4%], exact sign-test p=0.7905.
- **external_judge / generator=mimo-v2.6-flash / judge=gemini-3.1-pro-preview**: selfscore cleaner 7, baseline cleaner 5, tie 3, order-sensitive 5; decisive selfscore-cleaner rate 58.3% 95% CI [32.0%, 80.7%], exact sign-test p=0.7744.
- **external_judge / generator=mimo-v2.6-flash / judge=gpt-5.6-sol**: selfscore cleaner 8, baseline cleaner 8, tie 0, order-sensitive 4; decisive selfscore-cleaner rate 50.0% 95% CI [28.0%, 72.0%], exact sign-test p=1.
- **external_panel / generator=mimo-v2.6-flash / judge=PANEL**: selfscore cleaner 9, baseline cleaner 8, tie 2, order-sensitive 0; decisive selfscore-cleaner rate 52.9% 95% CI [31.0%, 73.8%], exact sign-test p=1.
- **external_judge / generator=minimax-m3 / judge=claude-opus-5.5**: selfscore cleaner 12, baseline cleaner 6, tie 0, order-sensitive 2; decisive selfscore-cleaner rate 66.7% 95% CI [43.7%, 83.7%], exact sign-test p=0.2379.
- **external_judge / generator=minimax-m3 / judge=gemini-3.1-pro-preview**: selfscore cleaner 7, baseline cleaner 2, tie 3, order-sensitive 8; decisive selfscore-cleaner rate 77.8% 95% CI [45.3%, 93.7%], exact sign-test p=0.1797.
- **external_judge / generator=minimax-m3 / judge=gpt-5.6-sol**: selfscore cleaner 11, baseline cleaner 4, tie 0, order-sensitive 5; decisive selfscore-cleaner rate 73.3% 95% CI [48.0%, 89.1%], exact sign-test p=0.1185.
- **external_panel / generator=minimax-m3 / judge=PANEL**: selfscore cleaner 11, baseline cleaner 6, tie 2, order-sensitive 0; decisive selfscore-cleaner rate 64.7% 95% CI [41.3%, 82.7%], exact sign-test p=0.3323.
- **external_judge / generator=nemotron-3-ultra / judge=claude-opus-5.5**: selfscore cleaner 8, baseline cleaner 10, tie 0, order-sensitive 2; decisive selfscore-cleaner rate 44.4% 95% CI [24.6%, 66.3%], exact sign-test p=0.8145.
- **external_judge / generator=nemotron-3-ultra / judge=gemini-3.1-pro-preview**: selfscore cleaner 4, baseline cleaner 8, tie 1, order-sensitive 7; decisive selfscore-cleaner rate 33.3% 95% CI [13.8%, 60.9%], exact sign-test p=0.3877.
- **external_judge / generator=nemotron-3-ultra / judge=gpt-5.6-sol**: selfscore cleaner 8, baseline cleaner 10, tie 0, order-sensitive 2; decisive selfscore-cleaner rate 44.4% 95% CI [24.6%, 66.3%], exact sign-test p=0.8145.
- **external_panel / generator=nemotron-3-ultra / judge=PANEL**: selfscore cleaner 8, baseline cleaner 12, tie 0, order-sensitive 0; decisive selfscore-cleaner rate 40.0% 95% CI [21.9%, 61.3%], exact sign-test p=0.5034.
- **external_judge / generator=qwen3.5-35b-a3b / judge=claude-opus-5.5**: selfscore cleaner 10, baseline cleaner 4, tie 0, order-sensitive 4; decisive selfscore-cleaner rate 71.4% 95% CI [45.4%, 88.3%], exact sign-test p=0.1796.
- **external_judge / generator=qwen3.5-35b-a3b / judge=gemini-3.1-pro-preview**: selfscore cleaner 7, baseline cleaner 5, tie 3, order-sensitive 3; decisive selfscore-cleaner rate 58.3% 95% CI [32.0%, 80.7%], exact sign-test p=0.7744.
- **external_judge / generator=qwen3.5-35b-a3b / judge=gpt-5.6-sol**: selfscore cleaner 8, baseline cleaner 6, tie 0, order-sensitive 4; decisive selfscore-cleaner rate 57.1% 95% CI [32.6%, 78.6%], exact sign-test p=0.7905.
- **external_panel / generator=qwen3.5-35b-a3b / judge=PANEL**: selfscore cleaner 10, baseline cleaner 5, tie 3, order-sensitive 0; decisive selfscore-cleaner rate 66.7% 95% CI [41.7%, 84.8%], exact sign-test p=0.3018.
- **external_judge / generator=qwen3.5-397b-a17b / judge=claude-opus-5.5**: selfscore cleaner 9, baseline cleaner 5, tie 0, order-sensitive 6; decisive selfscore-cleaner rate 64.3% 95% CI [38.8%, 83.7%], exact sign-test p=0.424.
- **external_judge / generator=qwen3.5-397b-a17b / judge=gemini-3.1-pro-preview**: selfscore cleaner 5, baseline cleaner 1, tie 9, order-sensitive 5; decisive selfscore-cleaner rate 83.3% 95% CI [43.6%, 97.0%], exact sign-test p=0.2188.
- **external_judge / generator=qwen3.5-397b-a17b / judge=gpt-5.6-sol**: selfscore cleaner 12, baseline cleaner 6, tie 0, order-sensitive 2; decisive selfscore-cleaner rate 66.7% 95% CI [43.7%, 83.7%], exact sign-test p=0.2379.
- **external_panel / generator=qwen3.5-397b-a17b / judge=PANEL**: selfscore cleaner 11, baseline cleaner 6, tie 3, order-sensitive 0; decisive selfscore-cleaner rate 64.7% 95% CI [41.3%, 82.7%], exact sign-test p=0.3323.
- **external_judge / generator=qwen3.7-flash / judge=claude-opus-5.5**: selfscore cleaner 16, baseline cleaner 2, tie 0, order-sensitive 2; decisive selfscore-cleaner rate 88.9% 95% CI [67.2%, 96.9%], exact sign-test p=0.001312.
- **external_judge / generator=qwen3.7-flash / judge=gemini-3.1-pro-preview**: selfscore cleaner 13, baseline cleaner 0, tie 3, order-sensitive 4; decisive selfscore-cleaner rate 100.0% 95% CI [77.2%, 100.0%], exact sign-test p=0.0002441.
- **external_judge / generator=qwen3.7-flash / judge=gpt-5.6-sol**: selfscore cleaner 12, baseline cleaner 5, tie 0, order-sensitive 3; decisive selfscore-cleaner rate 70.6% 95% CI [46.9%, 86.7%], exact sign-test p=0.1435.
- **external_panel / generator=qwen3.7-flash / judge=PANEL**: selfscore cleaner 17, baseline cleaner 2, tie 1, order-sensitive 0; decisive selfscore-cleaner rate 89.5% 95% CI [68.6%, 97.1%], exact sign-test p=0.0007286.
- **external_judge / generator=qwen3.8-27b / judge=claude-opus-5.5**: selfscore cleaner 12, baseline cleaner 7, tie 0, order-sensitive 1; decisive selfscore-cleaner rate 63.2% 95% CI [41.0%, 80.9%], exact sign-test p=0.3593.
- **external_judge / generator=qwen3.8-27b / judge=gemini-3.1-pro-preview**: selfscore cleaner 9, baseline cleaner 4, tie 2, order-sensitive 5; decisive selfscore-cleaner rate 69.2% 95% CI [42.4%, 87.3%], exact sign-test p=0.2668.
- **external_judge / generator=qwen3.8-27b / judge=gpt-5.6-sol**: selfscore cleaner 7, baseline cleaner 4, tie 0, order-sensitive 9; decisive selfscore-cleaner rate 63.6% 95% CI [35.4%, 84.8%], exact sign-test p=0.5488.
- **external_panel / generator=qwen3.8-27b / judge=PANEL**: selfscore cleaner 10, baseline cleaner 7, tie 3, order-sensitive 0; decisive selfscore-cleaner rate 58.8% 95% CI [36.0%, 78.4%], exact sign-test p=0.6291.
- **external_judge / generator=qwen3.8-flash / judge=claude-opus-5.5**: selfscore cleaner 11, baseline cleaner 8, tie 0, order-sensitive 1; decisive selfscore-cleaner rate 57.9% 95% CI [36.3%, 76.9%], exact sign-test p=0.6476.
- **external_judge / generator=qwen3.8-flash / judge=gemini-3.1-pro-preview**: selfscore cleaner 11, baseline cleaner 2, tie 3, order-sensitive 4; decisive selfscore-cleaner rate 84.6% 95% CI [57.8%, 95.7%], exact sign-test p=0.02246.
- **external_judge / generator=qwen3.8-flash / judge=gpt-5.6-sol**: selfscore cleaner 10, baseline cleaner 8, tie 0, order-sensitive 2; decisive selfscore-cleaner rate 55.6% 95% CI [33.7%, 75.4%], exact sign-test p=0.8145.
- **external_panel / generator=qwen3.8-flash / judge=PANEL**: selfscore cleaner 11, baseline cleaner 8, tie 1, order-sensitive 0; decisive selfscore-cleaner rate 57.9% 95% CI [36.3%, 76.9%], exact sign-test p=0.6476.
- **external_panel_overall / generator=ALL / judge=PANEL**: selfscore cleaner 206, baseline cleaner 149, tie 31, order-sensitive 0; decisive selfscore-cleaner rate 58.0% 95% CI [52.8%, 63.0%], exact sign-test p=0.002904.

## Self-score manipulation check

- **command-a-plus**: 20/20 emitted at least one valid score tag; 20/20 emitted at least five; mean tags=6.00; post-strip leaks=0.
- **deepseek-v3.2**: 20/20 emitted at least one valid score tag; 17/20 emitted at least five; mean tags=6.40; post-strip leaks=0.
- **deepseek-v4-flash-0731**: 18/20 emitted at least one valid score tag; 16/20 emitted at least five; mean tags=5.35; post-strip leaks=0.
- **deepseek-v4.1-flash**: 20/20 emitted at least one valid score tag; 20/20 emitted at least five; mean tags=7.20; post-strip leaks=0.
- **gemma-3-12b-it**: 20/20 emitted at least one valid score tag; 20/20 emitted at least five; mean tags=6.95; post-strip leaks=4.
- **glm-5.3**: 20/20 emitted at least one valid score tag; 20/20 emitted at least five; mean tags=7.00; post-strip leaks=0.
- **glm-5.3-flash**: 20/20 emitted at least one valid score tag; 20/20 emitted at least five; mean tags=7.10; post-strip leaks=0.
- **gpt-oss-120b**: 20/20 emitted at least one valid score tag; 20/20 emitted at least five; mean tags=6.05; post-strip leaks=0.
- **grok-4.7**: 20/20 emitted at least one valid score tag; 20/20 emitted at least five; mean tags=7.25; post-strip leaks=0.
- **hy4-preview**: 20/20 emitted at least one valid score tag; 20/20 emitted at least five; mean tags=7.15; post-strip leaks=0.
- **kimi-k2.5**: 20/20 emitted at least one valid score tag; 20/20 emitted at least five; mean tags=6.05; post-strip leaks=0.
- **llama-4-maverick**: 20/20 emitted at least one valid score tag; 20/20 emitted at least five; mean tags=6.85; post-strip leaks=0.
- **mimo-v2.6-flash**: 20/20 emitted at least one valid score tag; 17/20 emitted at least five; mean tags=5.70; post-strip leaks=0.
- **minimax-m3**: 20/20 emitted at least one valid score tag; 20/20 emitted at least five; mean tags=6.85; post-strip leaks=0.
- **nemotron-3-ultra**: 20/20 emitted at least one valid score tag; 18/20 emitted at least five; mean tags=6.05; post-strip leaks=0.
- **qwen3.5-35b-a3b**: 20/20 emitted at least one valid score tag; 20/20 emitted at least five; mean tags=7.20; post-strip leaks=2.
- **qwen3.5-397b-a17b**: 20/20 emitted at least one valid score tag; 20/20 emitted at least five; mean tags=6.95; post-strip leaks=0.
- **qwen3.7-flash**: 20/20 emitted at least one valid score tag; 20/20 emitted at least five; mean tags=6.00; post-strip leaks=0.
- **qwen3.8-27b**: 20/20 emitted at least one valid score tag; 20/20 emitted at least five; mean tags=6.00; post-strip leaks=0.
- **qwen3.8-flash**: 20/20 emitted at least one valid score tag; 20/20 emitted at least five; mean tags=5.95; post-strip leaks=0.

## Generation provider match

- **command-a-plus**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **deepseek-v3.2**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **deepseek-v4-flash-0731**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **deepseek-v4.1-flash**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **gemma-3-12b-it**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **glm-5.3**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **glm-5.3-flash**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **gpt-oss-120b**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **grok-4.7**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **hy4-preview**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **kimi-k2.5**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **llama-4-maverick**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **mimo-v2.6-flash**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **minimax-m3**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **nemotron-3-ultra**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **qwen3.5-35b-a3b**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **qwen3.5-397b-a17b**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **qwen3.7-flash**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **qwen3.8-27b**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).
- **qwen3.8-flash**: 20/20 baseline/selfscore pairs used the same reported upstream provider (100.0%); unknown provider on 0 pair(s).

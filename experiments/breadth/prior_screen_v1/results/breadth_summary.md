# Breadth replication summary

The breadth study is descriptive at the per-model level: 20 prompts per model are used to test cross-family directionality, not to demand individual-model significance.

## Model-level effects

- **deepseek-v3.2**: self-score cleaner 1, baseline cleaner 0, tie 1; decisive rate 100.0%; net wins +1.
- **gemma-3-12b-it**: self-score cleaner 1, baseline cleaner 1, tie 0; decisive rate 50.0%; net wins +0.
- **glm-5.3-flash**: self-score cleaner 1, baseline cleaner 0, tie 1; decisive rate 100.0%; net wins +1.
- **gpt-oss-120b**: self-score cleaner 2, baseline cleaner 0, tie 0; decisive rate 100.0%; net wins +2.
- **kimi-k2.5**: self-score cleaner 2, baseline cleaner 0, tie 0; decisive rate 100.0%; net wins +2.
- **llama-3.3-70b-instruct**: self-score cleaner 0, baseline cleaner 2, tie 0; decisive rate 0.0%; net wins -2.
- **minimax-m3**: self-score cleaner 1, baseline cleaner 1, tie 0; decisive rate 50.0%; net wins +0.
- **ministral-14b-2512**: self-score cleaner 1, baseline cleaner 1, tie 0; decisive rate 50.0%; net wins +0.
- **nemotron-3.5-lightning**: self-score cleaner 0, baseline cleaner 2, tie 0; decisive rate 0.0%; net wins -2.
- **qwen3-30b-a3b-instruct-2507**: self-score cleaner 0, baseline cleaner 2, tie 0; decisive rate 0.0%; net wins -2.
- **qwen3.7-flash**: self-score cleaner 1, baseline cleaner 1, tie 0; decisive rate 50.0%; net wins +0.

## Across-model breadth checks

- Models with positive / negative / exactly balanced net effect: **4 / 3 / 4**.
- Exact two-sided model-sign test (balanced models omitted): **p=1**.
- Median model-level decisive self-score preference: **50.0%**.
- Pooled panel outcomes: self-score cleaner **10**, baseline cleaner **10**, tie **2**; decisive rate **50.0%**.
- Two-stage model/pair bootstrap 95% interval for the pooled decisive rate: **[22.7%, 77.3%]**.
- Prompt-level net direction across models: positive **1**, negative **1**, balanced **0**; exact sign-test **p=1**.

Interpretation: `self-score cleaner` means the panel judged the baseline answer more AI-sloppy. The same blind mirrored judging rule as the main study is used.

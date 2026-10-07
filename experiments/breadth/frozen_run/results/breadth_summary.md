# Breadth replication summary

The breadth study uses 20 prompts per screened model configuration. Per-model results are descriptive; inference is also reported at the model-family level because several families contribute multiple variants.

## Model-level effects

- **command-a-plus** (cohere): self-score cleaner 6, baseline cleaner 13, tie 1; decisive rate 31.6%; net wins -7.
- **deepseek-v3.2** (deepseek): self-score cleaner 10, baseline cleaner 7, tie 2; decisive rate 58.8%; net wins +3.
- **deepseek-v4-flash-0731** (deepseek): self-score cleaner 9, baseline cleaner 10, tie 1; decisive rate 47.4%; net wins -1.
- **deepseek-v4.1-flash** (deepseek): self-score cleaner 5, baseline cleaner 15, tie 0; decisive rate 25.0%; net wins -10.
- **gemma-3-12b-it** (google): self-score cleaner 11, baseline cleaner 3, tie 2; decisive rate 78.6%; net wins +8.
- **glm-5.3** (z-ai): self-score cleaner 11, baseline cleaner 7, tie 0; decisive rate 61.1%; net wins +4.
- **glm-5.3-flash** (z-ai): self-score cleaner 11, baseline cleaner 6, tie 2; decisive rate 64.7%; net wins +5.
- **gpt-oss-120b** (openai): self-score cleaner 10, baseline cleaner 7, tie 2; decisive rate 58.8%; net wins +3.
- **grok-4.7** (x-ai): self-score cleaner 14, baseline cleaner 4, tie 2; decisive rate 77.8%; net wins +10.
- **hy4-preview** (tencent): self-score cleaner 8, baseline cleaner 8, tie 3; decisive rate 50.0%; net wins +0.
- **kimi-k2.5** (moonshot): self-score cleaner 12, baseline cleaner 8, tie 0; decisive rate 60.0%; net wins +4.
- **llama-4-maverick** (meta): self-score cleaner 12, baseline cleaner 7, tie 1; decisive rate 63.2%; net wins +5.
- **mimo-v2.6-flash** (xiaomi): self-score cleaner 9, baseline cleaner 8, tie 2; decisive rate 52.9%; net wins +1.
- **minimax-m3** (minimax): self-score cleaner 11, baseline cleaner 6, tie 2; decisive rate 64.7%; net wins +5.
- **nemotron-3-ultra** (nvidia): self-score cleaner 8, baseline cleaner 12, tie 0; decisive rate 40.0%; net wins -4.
- **qwen3.5-35b-a3b** (qwen): self-score cleaner 10, baseline cleaner 5, tie 3; decisive rate 66.7%; net wins +5.
- **qwen3.5-397b-a17b** (qwen): self-score cleaner 11, baseline cleaner 6, tie 3; decisive rate 64.7%; net wins +5.
- **qwen3.7-flash** (qwen): self-score cleaner 17, baseline cleaner 2, tie 1; decisive rate 89.5%; net wins +15.
- **qwen3.8-27b** (qwen): self-score cleaner 10, baseline cleaner 7, tie 3; decisive rate 58.8%; net wins +3.
- **qwen3.8-flash** (qwen): self-score cleaner 11, baseline cleaner 8, tie 1; decisive rate 57.9%; net wins +3.

## Across-model and across-family checks

- Screened model configurations with positive / negative / balanced net effect: **15 / 4 / 1**; model-sign p=**0.01921**.
- Distinct model families with positive / negative / balanced mean normalized effect: **9 / 3 / 1**; family-sign p=**0.146**.
- Median model-level decisive self-score preference: **59.4%**.
- Pooled panel outcomes: self-score cleaner **206**, baseline cleaner **149**, tie **31**; decisive rate **58.0%**.
- Family/model/pair bootstrap 95% interval for the pooled decisive rate: **[47.4%, 67.4%]**.
- Prompt-level net direction across screened models: positive **14**, negative **3**, balanced **3**; sign-test p=**0.01273**.

Interpretation: `self-score cleaner` means the panel judged the baseline answer more AI-sloppy. Mirrored order-sensitive judge results are excluded before panel voting, exactly as in the main experiment.

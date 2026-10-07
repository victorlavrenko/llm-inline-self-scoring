# Breadth treatment-compliance screen

Candidates: **24**; passed: **20**; failed: **4**.

The screen is outcome-blind: no quality judgments are used. Both frozen screen prompts must contain at least five valid inline score tags, no post-strip score leak, an interleaving ratio of at least 0.75, and matched upstream providers between baseline and treatment.

## Passed

- minimax-m3
- qwen3.7-flash
- kimi-k2.5
- gpt-oss-120b
- gemma-3-12b-it
- glm-5.3-flash
- deepseek-v3.2
- grok-4.7
- deepseek-v4.1-flash
- deepseek-v4-flash-0731
- glm-5.3
- qwen3.8-flash
- qwen3.8-27b
- qwen3.5-35b-a3b
- qwen3.5-397b-a17b
- mimo-v2.6-flash
- hy4-preview
- nemotron-3-ultra
- command-a-plus
- llama-4-maverick

## Failed

- **mistral-small-2603**: p025: only 1 valid score tags (<5); p025: interleaving ratio 0.00 < 0.75
- **ling-3.0-flash**: p046: only 1 valid score tags (<5); p046: interleaving ratio 0.00 < 0.75
- **minimax-m2.5**: p025: only 0 valid score tags (<5); p025: interleaving ratio 0.00 < 0.75; p046: only 0 valid score tags (<5); p046: interleaving ratio 0.00 < 0.75
- **phi-4**: p025: only 2 valid score tags (<5); p046: only 1 valid score tags (<5); p046: interleaving ratio 0.00 < 0.75

The four models that had already failed the earlier v1 smoke screen are documented separately in `known_noncompliant_v1.json` and `prior_screen_v1/`; they are not silently reintroduced here.

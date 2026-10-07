# Main matched self-scoring experiment

This is the exact runner used for the 100-prompt, four-generator experiment reported in the paper.

## Conditions

Both conditions receive the same explicit instruction to avoid generic, formulaic AI-style prose. The treatment additionally appends `<AI SCORE: n>` after each sentence. Score tags are stripped before judging and never trigger revision, rejection, branching, or selection.

The exact system instructions are frozen in `baseline_prompt.txt` and `selfscore_prompt.txt`. The 100 writing prompts are frozen in `prompts.jsonl`.

## Models

- GPT-5.6 Sol
- Claude Opus 5.5
- Gemini 3.1 Pro Preview
- DeepSeek V4.1 Flash

Generation pairs were provider-matched. The completed run used Together for DeepSeek after the first-party route returned 404s; `resume_full_v1_4.sh` documents that runtime-only routing repair without changing the scientific run identity.

## Run from scratch

The scripts use `OPENROUTER_API_KEY` from the environment.

```bash
cd experiments/main
python -m unittest discover -s tests -v
bash run_smoke.sh
bash run_full.sh
```

The run is resumable through SQLite/WAL. Completed cells are skipped.

## Re-analyze the frozen run

The frozen SQLite database and exports are in `frozen_run/`. The repository-level script `../../analysis/reproduce_paper_stats.py` independently reproduces the headline numbers from the exported CSVs.

See `PROTOCOL.md` for the frozen design.

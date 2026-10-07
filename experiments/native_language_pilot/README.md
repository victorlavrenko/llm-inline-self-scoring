# Native-language pilot (Russian)

This directory contains the small 24-pair validation described in the paper. It mirrors the main matched design in the author's native language (Russian): both arms receive the same anti-AI-slop objective and only the treatment emits sentence-level `<AI SCORE: n>` tags.

The pipeline generates the 48 texts, runs the four-model mirrored AI judging panel, exports live scores, and builds the blinded offline human-validation HTML.

## Run

The scripts use the `OPENROUTER_API_KEY` already present in the environment.

```bash
cd experiments/native_language_pilot
sh run.sh
```

The frozen outputs used in the paper are under `frozen_run/`. The author's blinded 24-pair human response is stored at `../../human/victor_ru24.json`.

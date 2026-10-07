#!/usr/bin/env bash
set -euo pipefail
: "${OPENROUTER_API_KEY:?Set OPENROUTER_API_KEY first}"

# Resumable generation: already-completed baseline/selfscore rows are skipped.
python generate_ru.py --out runs/ru-human --workers 16 --per-model-workers 4

# Same 24 pairs, all 4 judges, both A/B orientations. Already-completed judgments are skipped.
python judge_ru.py --out runs/ru-human --workers 16 --per-model-workers 4

# Export AI-panel outcomes and every emitted live score.
python analyze_ru.py --out runs/ru-human

# Build the one-file offline human study from the exact same generated pairs.
python build_validation_html.py --csv runs/ru-human/generations.csv --out ru_human_validation.html

echo
echo "DONE"
echo "Human study: ru_human_validation.html"
echo "AI summary: runs/ru-human/results/summary.md"
echo "AI pair outcomes: runs/ru-human/results/ai_panel_pairs.csv"
echo "Live scores: runs/ru-human/results/live_scores.csv"

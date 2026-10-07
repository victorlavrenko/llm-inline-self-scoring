#!/usr/bin/env bash
set -euo pipefail
: "${OPENROUTER_API_KEY:?Set OPENROUTER_API_KEY first}"
python judge_ru.py --out runs/ru-human --workers 16 --per-model-workers 4
python analyze_ru.py --out runs/ru-human
python build_validation_html.py --csv runs/ru-human/generations.csv --out ru_human_validation.html

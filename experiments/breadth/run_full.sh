#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -f models_screened.json ]]; then
  echo "models_screened.json is missing. Run: sh run_screen.sh" >&2
  exit 2
fi
python experiment.py all \
  --out runs/breadth-full \
  --models models_screened.json \
  --prompts prompts_breadth_20.jsonl \
  --cases 20 \
  --replicates 1 \
  --workers 64 \
  --per-model-workers 3 \
  --generation-max-tokens 8192 \
  --generation-retry-max-tokens 16384 \
  --judge-max-tokens 1024 \
  --judge-retry-max-tokens 4096 \
  --judge-reasoning-effort low \
  --mirror
python analyze_breadth.py --out runs/breadth-full --models models_screened.json

#!/usr/bin/env bash
set -euo pipefail
: "${OPENROUTER_API_KEY:?Set OPENROUTER_API_KEY first}"
python experiment.py all \
  --out runs/matched-full \
  --models models_current.json \
  --prompts prompts.jsonl \
  --cases 100 \
  --replicates 1 \
  --workers 80 \
  --per-model-workers 12 \
  --generation-max-tokens 8192 \
  --generation-retry-max-tokens 16384 \
  --judge-max-tokens 1024 \
  --judge-retry-max-tokens 4096 \
  --judge-reasoning-effort low \
  --mirror

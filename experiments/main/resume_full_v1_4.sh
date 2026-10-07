#!/usr/bin/env bash
set -euo pipefail
: "${OPENROUTER_API_KEY:?Set OPENROUTER_API_KEY first}"

echo "== Route preflight =="
python check_routes.py

echo
echo "== Existing full-run state =="
python experiment.py status \
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

echo
echo "== Resume; completed generations/judgments are skipped =="
sh run_full.sh

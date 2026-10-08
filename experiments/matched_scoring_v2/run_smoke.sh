#!/bin/sh
set -eu
cd "$(dirname "$0")"
MATCHED_ROOT=$(pwd -P)
export MATCHED_ROOT
. ./python_env.sh

if [ -z "${OPENROUTER_API_KEY:-}" ]; then
    echo "ERROR: OPENROUTER_API_KEY is not set. Restore it yourself and rerun." >&2
    exit 3
fi

run_python experiment.py all \
  --out runs/matched-smoke \
  --models models_current.json \
  --prompts prompts_matched_20.jsonl \
  --criteria-file criteria.json \
  --criteria ai_likeness,clarity \
  --cases 1 \
  --replicates 1 \
  --workers 24 \
  --per-model-workers 4 \
  --generation-max-tokens 4096 \
  --generation-retry-max-tokens 8192 \
  --judge-max-tokens 512 \
  --judge-retry-max-tokens 2048 \
  --judge-reasoning-effort low \
  --mirror
run_python analyze.py --run runs/matched-smoke
run_python status.py --run runs/matched-smoke

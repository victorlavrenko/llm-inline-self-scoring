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
  --out runs/matched-full \
  --models models_current.json \
  --prompts prompts_matched_20.jsonl \
  --criteria-file criteria.json \
  --cases 20 \
  --replicates 1 \
  --workers 80 \
  --per-model-workers 12 \
  --generation-max-tokens 8192 \
  --generation-retry-max-tokens 16384 \
  --judge-max-tokens 1024 \
  --judge-retry-max-tokens 4096 \
  --judge-reasoning-effort low \
  --mirror
run_python analyze.py --run runs/matched-full
run_python status.py --run runs/matched-full

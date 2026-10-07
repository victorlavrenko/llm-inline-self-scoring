#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -f models_resolved.json ]]; then
  echo "models_resolved.json is missing. Run: sh preflight.sh" >&2
  exit 2
fi
python experiment.py generate \
  --out runs/compliance-screen \
  --models models_resolved.json \
  --prompts prompts_breadth_20.jsonl \
  --cases 2 \
  --replicates 1 \
  --workers 48 \
  --per-model-workers 3 \
  --generation-max-tokens 8192 \
  --generation-retry-max-tokens 16384
python screen_models.py \
  --db runs/compliance-screen/experiment.sqlite3 \
  --resolved models_resolved.json \
  --output models_screened.json \
  --report-json screen_report.json \
  --report-md screen_report.md

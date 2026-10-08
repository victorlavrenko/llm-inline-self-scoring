#!/bin/sh
set -eu
cd "$(dirname "$0")"
MATCHED_ROOT=$(pwd -P)
export MATCHED_ROOT
. ./python_env.sh

RUN_DIR=${1:-runs/matched-full}
OUT=${2:-matched_scoring_results.tgz}

run_python status.py --run "$RUN_DIR" --require-complete
run_python analyze.py --run "$RUN_DIR" >/dev/null

tar -czf "$OUT" \
  README.md PROTOCOL.md criteria.json models_current.json prompts_matched_20.jsonl \
  experiment.py analyze.py status.py python_env.sh requirements.txt \
  run_smoke.sh run_full.sh status.sh verify.sh pack_results.sh run_all.sh \
  "$RUN_DIR"

echo "Packed complete results: $(pwd -P)/$OUT"

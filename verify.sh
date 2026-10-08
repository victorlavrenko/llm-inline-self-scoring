#!/usr/bin/env sh
set -eu
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")"

# Use the same cross-platform Python selection as the matched experiment.
. ./experiments/matched_scoring_v2/python_env.sh

# Legacy v9 checks run when this update is applied to the existing repository.
if [ -f analysis/reproduce_paper_stats.py ]; then
  run_python analysis/reproduce_paper_stats.py
fi

run_python analysis/reproduce_matched_stats.py

if [ -d experiments/main/tests ]; then
  run_python -m unittest discover -s experiments/main/tests -v
fi
if [ -d experiments/native_language_pilot/tests ]; then
  run_python -m unittest discover -s experiments/native_language_pilot/tests -v
fi

(
  cd experiments/matched_scoring_v2
  sh verify.sh
)

echo "v10 reproduction checks passed."

#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")"
if [ -f SHA256SUMS ]; then
  sha256sum -c SHA256SUMS
fi
python analysis/reproduce_paper_stats.py
python -m unittest discover -s experiments/main/tests -v
python -m unittest discover -s experiments/native_language_pilot/tests -v

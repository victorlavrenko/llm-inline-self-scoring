#!/bin/sh
set -eu
cd "$(dirname "$0")"

echo "=== VERIFY ==="
sh ./verify.sh

echo "=== OPENROUTER KEY CHECK ==="
if [ -z "${OPENROUTER_API_KEY:-}" ]; then
    echo "ERROR: OPENROUTER_API_KEY is not set. Restore it yourself and rerun." >&2
    exit 3
fi
echo "OPENROUTER_API_KEY: present; not modified"

echo "=== SMOKE ==="
sh ./run_smoke.sh

echo "=== FULL ==="
sh ./run_full.sh

echo "=== PACK ==="
sh ./pack_results.sh

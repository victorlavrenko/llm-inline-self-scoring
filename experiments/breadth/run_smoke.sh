#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "v1.2 uses an outcome-blind compliance screen instead of the old judged smoke. Running run_screen.sh." >&2
exec sh run_screen.sh

#!/bin/sh
set -eu
cd "$(dirname "$0")"
MATCHED_ROOT=$(pwd -P)
export MATCHED_ROOT
. ./python_env.sh
run_python status.py --run "${1:-runs/matched-full}"

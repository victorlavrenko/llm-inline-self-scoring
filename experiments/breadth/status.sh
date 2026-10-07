#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python plan.py
python - <<'PY'
import sqlite3
from pathlib import Path
for d in [Path('runs/compliance-screen'), Path('runs/breadth-full')]:
    db=d/'experiment.sqlite3'
    if not db.exists():
        continue
    con=sqlite3.connect(db)
    print(f"\n== {d} ==")
    for table in ('generations','judgments','attempts'):
        try:
            n=con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        except Exception:
            n='NA'
        print(f'{table}: {n}')
    con.close()
PY
if [[ -f screen_report.md ]]; then
  echo
  cat screen_report.md
fi

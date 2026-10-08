#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--run',default='runs/matched-full'); ap.add_argument('--require-complete',action='store_true'); args=ap.parse_args()
    run=Path(args.run); manifest_path=run/'manifest.json'; db_path=run/'experiment.sqlite3'
    if not manifest_path.exists() or not db_path.exists():
        print(f'run missing: {run}', file=sys.stderr); raise SystemExit(2)
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    db=sqlite3.connect(db_path); db.row_factory=sqlite3.Row
    prompts=len(manifest['prompt_ids']); generators=len(manifest['generators']); criteria=len(manifest['selected_criteria']); reps=int(manifest['replicates']); judges=len(manifest['judges']); orientations=2 if manifest['mirror'] else 1
    expected_gen=prompts*generators*criteria*2*reps
    actual_gen=db.execute('SELECT COUNT(*) FROM generations').fetchone()[0]
    expected_pairs=prompts*generators*criteria*reps
    actual_pairs=db.execute("""SELECT COUNT(*) FROM generations s JOIN generations b ON b.prompt_id=s.prompt_id AND b.generator=s.generator AND b.criterion=s.criterion AND b.replicate=s.replicate AND b.arm='objective_only' WHERE s.arm='selfscore'""").fetchone()[0]
    eligible_pairs=db.execute("""SELECT COUNT(*) FROM generations s JOIN generations b ON b.prompt_id=s.prompt_id AND b.generator=s.generator AND b.criterion=s.criterion AND b.replicate=s.replicate AND b.arm='objective_only' WHERE s.arm='selfscore' AND s.compliant=1 AND s.tag_leak=0 AND b.compliant=1""").fetchone()[0]
    expected_judgments=eligible_pairs*judges*orientations
    actual_judgments=db.execute('SELECT COUNT(*) FROM judgments').fetchone()[0]
    failed_attempts=db.execute('SELECT COUNT(*) FROM attempts WHERE ok=0').fetchone()[0]
    print(f'generations: {actual_gen}/{expected_gen}')
    print(f'matched pairs present: {actual_pairs}/{expected_pairs}')
    print(f'eligible compliant pairs: {eligible_pairs}')
    print(f'judgments: {actual_judgments}/{expected_judgments}')
    print(f'failed physical attempts retained: {failed_attempts}')
    complete=(actual_gen==expected_gen and actual_pairs==expected_pairs and actual_judgments==expected_judgments)
    print('complete: YES' if complete else 'complete: NO')
    if args.require_complete and not complete: raise SystemExit(3)

if __name__=='__main__': main()

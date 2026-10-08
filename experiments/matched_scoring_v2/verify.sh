#!/bin/sh
set -eu
cd "$(dirname "$0")"
MATCHED_ROOT=$(pwd -P)
export MATCHED_ROOT
. ./python_env.sh

PLAN_FILE=.matched_plan_check.json
cleanup() { rm -f "$PLAN_FILE"; }
trap cleanup EXIT HUP INT TERM

run_python -m py_compile experiment.py analyze.py status.py
run_python experiment.py plan --mirror > "$PLAN_FILE"
run_python - "$PLAN_FILE" <<'PY'
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    x=json.load(f)
assert x['prompts']==20, x
assert len(x['generators'])==4, x
assert len(x['criteria'])==5, x
assert x['generations']==800, x
assert x['matched_pairs']==400, x
assert x['judge_calls']==3200, x
assert x['judge_endpoints_per_call']==2, x
print('verify: OK')
PY

run_python - <<'PY'
import json
import experiment
cfg=json.load(open('criteria.json',encoding='utf-8'))
for name,c in cfg.items():
    base=experiment.objective_system(c)
    ss=experiment.selfscore_system(c)
    assert c['optimization_instruction'] in base
    assert c['optimization_instruction'] in ss
    assert c['score_instruction'] not in base
    assert c['score_instruction'] in ss
    raw='One clear sentence. <'+c['tag']+': 12> Another useful sentence. <'+c['tag']+': 7> Third sentence. <'+c['tag']+': 4> Fourth sentence. <'+c['tag']+': 3> Fifth sentence. <'+c['tag']+': 2>'
    clean, vals, leak=experiment.strip_score(raw,c)
    assert len(vals)==5 and not leak and c['tag'] not in clean.upper()
assert experiment.parse_dual_verdict('{"overall":"A","target":"TIE"}')==('A','TIE')
print('prompt/parser checks: OK')
PY

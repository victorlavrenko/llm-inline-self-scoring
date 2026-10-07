#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
mods=json.loads((ROOT/'models_candidates.json').read_text())
prompts=[json.loads(x) for x in (ROOT/'prompts_breadth_20.jsonl').read_text().splitlines() if x.strip()]
g=len(mods['generators']); j=len(mods['judges']); p=len(prompts)
print(f'candidate breadth generators={g}; fixed judges={j}; prompts={p}')
print(f'candidate compliance-screen generation calls={g*2*2} (2 prompts x 2 arms)')
if (ROOT/'models_screened.json').exists():
    s=json.loads((ROOT/'models_screened.json').read_text())
    gs=len(s['generators'])
    print(f'screened breadth generators={gs}; plus 4 main-study generators -> {gs+4} total effect-analysis model configurations')
    print(f'full breadth generation calls={p*gs*2}')
    print(f'full breadth mirrored judgment calls={p*gs*j*2}')
    print(f'full breadth total API calls={p*gs*2 + p*gs*j*2}')
else:
    print(f'maximum if all candidates pass: breadth={g}, total with main study={g+4} model configurations')
    print(f'maximum full generation calls={p*g*2}')
    print(f'maximum full mirrored judgment calls={p*g*j*2}')
    print(f'maximum full calls={p*g*2 + p*g*j*2}')
print('candidate generators:')
for m in mods['generators']:
    print(f"  {m['alias']:30s} {m['route']} [{m.get('cohort','')}] preferred={','.join(m['provider_candidates'])}")
print('known prior treatment-noncompliant models are documented in known_noncompliant_v1.json and excluded from effect analysis.')

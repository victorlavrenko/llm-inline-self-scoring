#!/usr/bin/env python3
"""Breadth-specific analysis for the screened multi-model replication.

The 20-prompt breadth study is intentionally descriptive per model. Because the
candidate roster contains multiple variants from some labs/families, this script
reports both model-level and family-clustered checks rather than treating every
model configuration as an independent draw from the universe of LLMs.
"""
from __future__ import annotations

import argparse, csv, json, math, random, statistics
from collections import Counter, defaultdict
from pathlib import Path


def read_csv(path: Path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def exact_sign_p(wins: int, losses: int) -> float:
    n=wins+losses
    if not n: return float('nan')
    m=min(wins,losses)
    tail=sum(math.comb(n,k) for k in range(m+1))/(2**n)
    return min(1.0,2*tail)


def panel_outcome(xs):
    c=Counter(x for x in xs if x in {'baseline_more_slop','selfscore_more_slop','tie'})
    if not sum(c.values()): return None
    if c['baseline_more_slop'] > c['selfscore_more_slop']: return 'baseline_more_slop'
    if c['selfscore_more_slop'] > c['baseline_more_slop']: return 'selfscore_more_slop'
    return 'tie'


def percentile(vals, q):
    vals=sorted(vals)
    if not vals: return float('nan')
    x=(len(vals)-1)*q
    lo=int(math.floor(x)); hi=int(math.ceil(x))
    if lo==hi: return vals[lo]
    return vals[lo]*(hi-x)+vals[hi]*(x-lo)


def load_family_map(models_path: Path) -> dict[str,str]:
    if not models_path.exists(): return {}
    obj=json.loads(models_path.read_text(encoding='utf-8'))
    return {str(r['alias']): str(r.get('family') or r['alias']) for r in obj.get('generators',[]) if isinstance(r,dict)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, default=Path('runs/breadth-full'))
    ap.add_argument('--models', type=Path, default=Path('models_screened.json'))
    ap.add_argument('--bootstrap-reps', type=int, default=20000)
    ap.add_argument('--seed', type=int, default=20261006)
    args=ap.parse_args()
    rdir=args.out/'results'
    family_map=load_family_map(args.models)
    rows=read_csv(rdir/'judgments_resolved.csv')

    # Resolve the three mirrored external judges to one panel outcome per model/prompt.
    per_pair=defaultdict(list)
    for r in rows:
        if r['outcome']=='order_sensitive':
            continue
        per_pair[(r['generator'],r['prompt_id'],int(r['replicate']))].append(r['outcome'])
    pair_rows=[]
    for (g,p,rep),xs in sorted(per_pair.items()):
        o=panel_outcome(xs)
        if o is not None:
            pair_rows.append({'generator':g,'family':family_map.get(g,g),'prompt_id':p,'replicate':rep,'panel_outcome':o,'votes_count':len(xs)})
    with (rdir/'breadth_panel_pairs.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['generator','family','prompt_id','replicate','panel_outcome','votes_count']); w.writeheader(); w.writerows(pair_rows)

    effects=[]
    for g in sorted({r['generator'] for r in pair_rows}):
        xs=[r['panel_outcome'] for r in pair_rows if r['generator']==g]
        c=Counter(xs); sw=c['baseline_more_slop']; bw=c['selfscore_more_slop']; tie=c['tie']; dec=sw+bw
        effects.append({
            'generator':g,'family':family_map.get(g,g),'n_resolved':len(xs),'selfscore_cleaner':sw,'baseline_cleaner':bw,'tie':tie,
            'decisive_n':dec,'decisive_selfscore_rate':(sw/dec if dec else None),
            'net_wins':sw-bw,'normalized_net':((sw-bw)/dec if dec else None),'exact_sign_p':(exact_sign_p(sw,bw) if dec else None),
        })
    with (rdir/'breadth_model_effects.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(effects[0]) if effects else ['generator']); w.writeheader(); w.writerows(effects)

    pos=sum(e['net_wins']>0 for e in effects); neg=sum(e['net_wins']<0 for e in effects); eq=sum(e['net_wins']==0 for e in effects)
    model_sign_p=exact_sign_p(pos,neg) if pos+neg else float('nan')
    rates=[e['decisive_selfscore_rate'] for e in effects if e['decisive_selfscore_rate'] is not None]
    median_rate=statistics.median(rates) if rates else float('nan')
    pooled=Counter(r['panel_outcome'] for r in pair_rows)
    pooled_dec=pooled['baseline_more_slop']+pooled['selfscore_more_slop']
    pooled_rate=pooled['baseline_more_slop']/pooled_dec if pooled_dec else float('nan')

    # Family-level direction: average normalized model effect within each family,
    # so a family with many variants does not get proportionally more sign-test weight.
    family_effects=[]
    for fam in sorted({e['family'] for e in effects}):
        es=[e for e in effects if e['family']==fam and e['normalized_net'] is not None]
        mean_net=statistics.mean(e['normalized_net'] for e in es) if es else 0.0
        family_effects.append({'family':fam,'models':len(es),'mean_normalized_net':mean_net,'direction':1 if mean_net>0 else (-1 if mean_net<0 else 0)})
    with (rdir/'breadth_family_effects.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['family','models','mean_normalized_net','direction']); w.writeheader(); w.writerows(family_effects)
    fpos=sum(x['direction']>0 for x in family_effects); fneg=sum(x['direction']<0 for x in family_effects); feq=sum(x['direction']==0 for x in family_effects)
    family_sign_p=exact_sign_p(fpos,fneg) if fpos+fneg else float('nan')

    # Prompt-level direction across all screened model configurations.
    prompt_net=[]
    for p in sorted({r['prompt_id'] for r in pair_rows}):
        c=Counter(r['panel_outcome'] for r in pair_rows if r['prompt_id']==p)
        prompt_net.append(c['baseline_more_slop']-c['selfscore_more_slop'])
    ppos=sum(x>0 for x in prompt_net); pneg=sum(x<0 for x in prompt_net); peq=sum(x==0 for x in prompt_net)
    prompt_sign_p=exact_sign_p(ppos,pneg) if ppos+pneg else float('nan')

    # Three-stage bootstrap: resample families, then models within each selected
    # family, then prompt-pairs within each selected model. This guards against
    # pseudo-replication from multiple closely related model variants.
    by_model={g:[r['panel_outcome'] for r in pair_rows if r['generator']==g] for g in sorted({r['generator'] for r in pair_rows})}
    fam_models=defaultdict(list)
    for g in by_model: fam_models[family_map.get(g,g)].append(g)
    families=sorted(fam_models)
    rng=random.Random(args.seed); boots=[]
    for _ in range(args.bootstrap_reps):
        sw=bw=0
        for fam in (rng.choice(families) for __ in range(len(families))):
            models=fam_models[fam]
            # Preserve the observed number of model configurations in that family,
            # but resample them with replacement after the family itself is sampled.
            for g in (rng.choice(models) for __ in range(len(models))):
                xs=by_model[g]
                for __ in range(len(xs)):
                    x=rng.choice(xs)
                    if x=='baseline_more_slop': sw+=1
                    elif x=='selfscore_more_slop': bw+=1
        if sw+bw: boots.append(sw/(sw+bw))
    blo=percentile(boots,.025); bhi=percentile(boots,.975)

    lines=[
        '# Breadth replication summary','',
        'The breadth study uses 20 prompts per screened model configuration. Per-model results are descriptive; inference is also reported at the model-family level because several families contribute multiple variants.','',
        '## Model-level effects',''
    ]
    for e in effects:
        rate='NA' if e['decisive_selfscore_rate'] is None else f"{100*e['decisive_selfscore_rate']:.1f}%"
        lines.append(f"- **{e['generator']}** ({e['family']}): self-score cleaner {e['selfscore_cleaner']}, baseline cleaner {e['baseline_cleaner']}, tie {e['tie']}; decisive rate {rate}; net wins {e['net_wins']:+d}.")
    lines += ['', '## Across-model and across-family checks','',
        f"- Screened model configurations with positive / negative / balanced net effect: **{pos} / {neg} / {eq}**; model-sign p=**{model_sign_p:.4g}**.",
        f"- Distinct model families with positive / negative / balanced mean normalized effect: **{fpos} / {fneg} / {feq}**; family-sign p=**{family_sign_p:.4g}**.",
        f"- Median model-level decisive self-score preference: **{100*median_rate:.1f}%**.",
        f"- Pooled panel outcomes: self-score cleaner **{pooled['baseline_more_slop']}**, baseline cleaner **{pooled['selfscore_more_slop']}**, tie **{pooled['tie']}**; decisive rate **{100*pooled_rate:.1f}%**.",
        f"- Family/model/pair bootstrap 95% interval for the pooled decisive rate: **[{100*blo:.1f}%, {100*bhi:.1f}%]**.",
        f"- Prompt-level net direction across screened models: positive **{ppos}**, negative **{pneg}**, balanced **{peq}**; sign-test p=**{prompt_sign_p:.4g}**.",
        '', 'Interpretation: `self-score cleaner` means the panel judged the baseline answer more AI-sloppy. Mirrored order-sensitive judge results are excluded before panel voting, exactly as in the main experiment.'
    ]
    (rdir/'breadth_summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines))

if __name__=='__main__': main()

#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, math, sqlite3, statistics
from collections import Counter, defaultdict
from pathlib import Path


def wilson(k,n,z=1.959963984540054):
    if not n: return (None,None)
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d
    h=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/d
    return max(0,c-h),min(1,c+h)

def sign_p(w,l):
    n=w+l
    if not n:return None
    m=min(w,l); tail=sum(math.comb(n,k) for k in range(m+1))/(2**n)
    return min(1.0,2*tail)

def write_csv(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:
        path.write_text('',encoding='utf-8'); return
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def resolve(rows):
    by={int(r['orientation']):r['canonical_outcome'] for r in rows}
    if 0 not in by or 1 not in by:return 'missing'
    return by[0] if by[0]==by[1] else 'order_sensitive'

def summarize(outs):
    c=Counter(outs); sc=c['baseline_more_slop']; ba=c['selfscore_more_slop']; tie=c['tie']; order=c['order_sensitive']; miss=c['missing']
    dec=sc+ba; lo,hi=wilson(sc,dec)
    return dict(n=len(outs),selfscore_cleaner=sc,baseline_cleaner=ba,tie=tie,order_sensitive=order,missing=miss,
                decisive_n=dec,selfscore_cleaner_decisive_rate=(sc/dec if dec else None),ci95_low=lo,ci95_high=hi,
                exact_sign_p=sign_p(sc,ba))

def panel(votes):
    valid=[x for x in votes if x in {'baseline_more_slop','selfscore_more_slop','tie'}]
    if not valid:return 'missing'
    c=Counter(valid)
    if c['baseline_more_slop']>c['selfscore_more_slop']:return 'baseline_more_slop'
    if c['selfscore_more_slop']>c['baseline_more_slop']:return 'selfscore_more_slop'
    return 'tie'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default='runs/ru-human'); ap.add_argument('--models',default='models.json'); args=ap.parse_args()
    out=Path(args.out); res=out/'results'; res.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(out/'state.sqlite3'); conn.row_factory=sqlite3.Row
    gens=[dict(r) for r in conn.execute('SELECT * FROM generations ORDER BY generator,prompt_id,condition')]
    judges=[dict(r) for r in conn.execute('SELECT * FROM judgments ORDER BY generator,prompt_id,judge,orientation')]
    attempts=[dict(r) for r in conn.execute('SELECT * FROM judge_attempts ORDER BY created_at')]
    models=[x['alias'] for x in json.loads(Path(args.models).read_text(encoding='utf-8'))['models']]
    write_csv(res/'generations.csv',gens); write_csv(res/'judgments_raw.csv',judges); write_csv(res/'judge_attempts.csv',attempts)

    grouped=defaultdict(list)
    for r in judges: grouped[(r['prompt_id'],r['generator'],r['judge'])].append(r)
    resolved=[]
    all_pairs=sorted({(r['prompt_id'],r['generator']) for r in gens})
    for pid,gen in all_pairs:
        for j in models:
            rows=grouped.get((pid,gen,j),[])
            resolved.append({'prompt_id':pid,'generator':gen,'judge':j,'is_self_judge':int(j==gen),'outcome':resolve(rows)})
    write_csv(res/'judgments_resolved.csv',resolved)

    pair_rows=[]
    for pid,gen in all_pairs:
        ext=[r for r in resolved if r['prompt_id']==pid and r['generator']==gen and r['judge']!=gen]
        selfr=next(r for r in resolved if r['prompt_id']==pid and r['generator']==gen and r['judge']==gen)
        ext_valid=[r['outcome'] for r in ext if r['outcome']!='order_sensitive']
        po=panel(ext_valid)
        row={'prompt_id':pid,'generator':gen,'external_panel_outcome':po,'self_judge_outcome':selfr['outcome']}
        for r in ext: row['judge_'+r['judge']]=r['outcome']
        row['external_selfscore_cleaner_votes']=sum(x=='baseline_more_slop' for x in ext_valid)
        row['external_baseline_cleaner_votes']=sum(x=='selfscore_more_slop' for x in ext_valid)
        row['external_tie_votes']=sum(x=='tie' for x in ext_valid)
        row['external_order_sensitive']=sum(r['outcome']=='order_sensitive' for r in ext)
        pair_rows.append(row)
    write_csv(res/'ai_panel_pairs.csv',pair_rows)

    summaries=[]
    for gen in sorted(set(g for _,g in all_pairs)):
        s=[r['outcome'] for r in resolved if r['generator']==gen and r['judge']==gen]
        summaries.append({'level':'self_judge','generator':gen,'judge':gen,**summarize(s)})
        for j in models:
            if j==gen: continue
            o=[r['outcome'] for r in resolved if r['generator']==gen and r['judge']==j]
            summaries.append({'level':'external_judge','generator':gen,'judge':j,**summarize(o)})
        po=[r['external_panel_outcome'] for r in pair_rows if r['generator']==gen]
        summaries.append({'level':'external_panel','generator':gen,'judge':'PANEL',**summarize(po)})
    summaries.append({'level':'external_panel_overall','generator':'ALL','judge':'PANEL',**summarize([r['external_panel_outcome'] for r in pair_rows])})
    write_csv(res/'summary.csv',summaries)

    live=[]; live_summary=[]
    for g in gens:
        if g['condition']!='selfscore': continue
        vals=json.loads(g['scores_json'] or '[]')
        for i,v in enumerate(vals,1): live.append({'prompt_id':g['prompt_id'],'generator':g['generator'],'score_index':i,'score':v})
        live_summary.append({'prompt_id':g['prompt_id'],'generator':g['generator'],'score_count':len(vals),
                             'mean_live_score':statistics.mean(vals) if vals else None,
                             'median_live_score':statistics.median(vals) if vals else None,
                             'min_live_score':min(vals) if vals else None,'max_live_score':max(vals) if vals else None,
                             'share_score_ge_50':sum(v>=50 for v in vals)/len(vals) if vals else None,
                             'share_score_ge_75':sum(v>=75 for v in vals)/len(vals) if vals else None})
    write_csv(res/'live_scores.csv',live); write_csv(res/'live_score_summary.csv',live_summary)

    lines=['# Russian self-scoring validation','',
           'Both generation arms receive the same explicit instruction to avoid AI-slop. The self-scored arm differs only by emitting <AI SCORE: n> after every sentence. Scores are stripped before AI and human pairwise judging.','',
           '## AI-panel results','']
    for r in summaries:
        rate='NA' if r['selfscore_cleaner_decisive_rate'] is None else f"{100*r['selfscore_cleaner_decisive_rate']:.1f}%"
        ci='NA' if r['ci95_low'] is None else f"[{100*r['ci95_low']:.1f}%, {100*r['ci95_high']:.1f}%]"
        p='NA' if r['exact_sign_p'] is None else f"{r['exact_sign_p']:.4g}"
        lines.append(f"- **{r['level']} / generator={r['generator']} / judge={r['judge']}**: selfscore cleaner {r['selfscore_cleaner']}, baseline cleaner {r['baseline_cleaner']}, tie {r['tie']}, order-sensitive {r['order_sensitive']}, missing {r['missing']}; decisive selfscore-cleaner rate {rate}, 95% CI {ci}, sign-test p={p}.")
    lines += ['', '## Live self-score outputs','']
    for gen in sorted(set(r['generator'] for r in live_summary)):
        rr=[r for r in live_summary if r['generator']==gen]
        lines.append(f"- **{gen}**: {len(rr)} self-scored texts; mean tags/text={statistics.mean(r['score_count'] for r in rr):.2f}; mean of per-text mean AI scores={statistics.mean(r['mean_live_score'] for r in rr):.1f}.")
    lines += ['', '## Files for human comparison','',
              '- `ai_panel_pairs.csv`: one row per human-validation pair with external-panel and judge-level outcomes.',
              '- `live_scores.csv`: every emitted sentence-level score.',
              '- `live_score_summary.csv`: one row per self-scored text.',
              '- `judgments_resolved.csv`: mirrored outcome for every judge/pair.',
              '- `generations.csv`: raw and cleaned generation text.']
    (res/'summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines))
    conn.close()

if __name__=='__main__': main()

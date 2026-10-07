#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, html, json, secrets
from pathlib import Path

TEMPLATE = r'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Слепая оценка русских текстов</title>
<style>
:root{font-family:Inter,system-ui,-apple-system,"Segoe UI",Arial,sans-serif;color:#161616;background:#f5f5f3}
body{margin:0}.wrap{max-width:1080px;margin:auto;padding:28px 18px 70px}.card{background:white;border:1px solid #ddd;border-radius:16px;padding:22px;margin:16px 0;box-shadow:0 2px 10px #0000000a}
h1{font-size:28px;margin:0 0 8px}h2{font-size:19px;margin:0 0 12px}.muted{color:#666}.task{background:#fafafa;border-left:4px solid #aaa;padding:12px 14px;white-space:pre-wrap}
.answers{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}.answer{border:1px solid #ddd;border-radius:12px;padding:16px;white-space:pre-wrap;line-height:1.48;background:#fff}.answer h3{margin:0 0 10px;font-size:17px}
.controls{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:18px}button{font:inherit;border:1px solid #bbb;background:#fff;border-radius:10px;padding:12px;cursor:pointer}button:hover{background:#f1f1ee}button.primary{background:#161616;color:white;border-color:#161616}.progress{height:8px;background:#ddd;border-radius:9px;overflow:hidden}.bar{height:100%;background:#222;width:0}
input{font:inherit;padding:10px;border:1px solid #bbb;border-radius:8px;width:min(360px,90%)}textarea{width:100%;height:300px;font:12px ui-monospace,Consolas,monospace;box-sizing:border-box}.hidden{display:none}.nav{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-top:12px}
@media(max-width:760px){.answers{grid-template-columns:1fr}.controls{grid-template-columns:1fr}.wrap{padding:18px 10px 50px}}
</style></head><body><div class="wrap">
<div id="intro" class="card"><h1>Слепая оценка текстов</h1>
<p>Здесь 24 пары коротких русских текстов. В каждой паре тексты отвечают на одно и то же задание.</p>
<p><b>Вопрос только один:</b> какой текст <b>меньше похож на типичный текст нейросети</b> и звучит более естественно по-русски?</p>
<p class="muted">Обращайте внимание на шаблонность, общие фразы, клише, чрезмерно гладкие переходы, искусственную «полезность», рекламный или назидательный тон, повторяющуюся структуру и неестественные финальные выводы. Не пытайтесь угадывать модель. Фактическая точность здесь не главный критерий. Если разницы по стилю почти нет — выбирайте «примерно одинаково».</p>
<label>Код оценщика (например, Victor или Anna-1):<br><input id="evaluator" placeholder="Введите код"></label><br><br><button class="primary" id="start">Начать</button>
</div>
<div id="quiz" class="hidden"><div class="card"><div class="progress"><div class="bar" id="bar"></div></div><div class="nav"><span id="counter"></span><button id="saveExit">Сохранить и продолжить позже</button></div></div>
<div class="card"><h2>Задание</h2><div class="task" id="task"></div><div class="answers"><div class="answer"><h3>Текст A</h3><div id="a"></div></div><div class="answer"><h3>Текст B</h3><div id="b"></div></div></div>
<div class="controls"><button data-choice="A">A меньше похож на ИИ</button><button data-choice="TIE">Примерно одинаково</button><button data-choice="B">B меньше похож на ИИ</button></div></div></div>
<div id="done" class="card hidden"><h1>Готово</h1><p>Скопируйте <b>весь текст</b> из поля ниже и отправьте его исследователю. В нём есть все ответы и техническая расшифровка A/B.</p><button class="primary" id="copy">Скопировать результаты</button><p id="copied" class="muted"></p><textarea id="result" readonly></textarea><p><button id="reset">Сбросить эту сессию</button></p></div>
</div><script>
const DATA=__DATA__;
const STUDY="__STUDY__";
function hash(s){let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return h>>>0}
function rng(seed){let x=seed||123456789;return()=>{x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)/4294967296}}
function shuffle(arr,r){for(let i=arr.length-1;i>0;i--){const j=Math.floor(r()*(i+1));[arr[i],arr[j]]=[arr[j],arr[i]]}return arr}
const intro=document.getElementById('intro'), quiz=document.getElementById('quiz'), done=document.getElementById('done');
let state=null, key=null;
function makeState(id){const r=rng(hash(STUDY+'|'+id));const items=DATA.map(x=>{const flip=r()<.5;return {...x,a_source:flip?'selfscore':'baseline',b_source:flip?'baseline':'selfscore',a:flip?x.selfscore:x.baseline,b:flip?x.baseline:x.selfscore}});shuffle(items,r);return{study:STUDY,evaluator_id:id,started_at:new Date().toISOString(),index:0,items:items.map(x=>({prompt_id:x.prompt_id,domain:x.domain,generator:x.generator,task:x.task,a_source:x.a_source,b_source:x.b_source,a:x.a,b:x.b})),responses:[]}}
function persist(){localStorage.setItem(key,JSON.stringify(state))}
function render(){intro.classList.add('hidden');done.classList.add('hidden');quiz.classList.remove('hidden');const i=state.index,n=state.items.length;if(i>=n){finish();return}const x=state.items[i];document.getElementById('counter').textContent=`Пара ${i+1} из ${n}`;document.getElementById('bar').style.width=(100*i/n)+'%';document.getElementById('task').textContent=x.task;document.getElementById('a').textContent=x.a;document.getElementById('b').textContent=x.b}
function finish(){state.completed_at=new Date().toISOString();persist();quiz.classList.add('hidden');done.classList.remove('hidden');document.getElementById('result').value=JSON.stringify({schema:'selfscore-ru-human-v1',study:state.study,evaluator_id:state.evaluator_id,started_at:state.started_at,completed_at:state.completed_at,responses:state.responses},null,2)}
document.getElementById('start').onclick=()=>{const id=document.getElementById('evaluator').value.trim();if(!id){alert('Введите код оценщика');return}key='selfscore_ru_validation_'+STUDY+'_'+id;const old=localStorage.getItem(key);state=old?JSON.parse(old):makeState(id);render()}
document.querySelectorAll('[data-choice]').forEach(b=>b.onclick=()=>{const x=state.items[state.index],choice=b.dataset.choice;state.responses.push({ordinal:state.index+1,prompt_id:x.prompt_id,domain:x.domain,generator:x.generator,choice,a_source:x.a_source,b_source:x.b_source,preferred_source:choice==='TIE'?'tie':(choice==='A'?x.a_source:x.b_source)});state.index++;persist();render()})
document.getElementById('saveExit').onclick=()=>{persist();alert('Прогресс сохранён в этом браузере. Можно закрыть файл и открыть его позже с тем же кодом оценщика.')}
document.getElementById('copy').onclick=async()=>{await navigator.clipboard.writeText(document.getElementById('result').value);document.getElementById('copied').textContent='Скопировано.'}
document.getElementById('reset').onclick=()=>{if(confirm('Удалить прогресс этого оценщика?')){localStorage.removeItem(key);location.reload()}}
</script></body></html>'''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--csv',default='runs/ru-human/generations.csv'); ap.add_argument('--out',default='ru_human_validation.html'); args=ap.parse_args()
    rows=list(csv.DictReader(Path(args.csv).open(encoding='utf-8-sig')))
    by={}
    for r in rows: by.setdefault((r['prompt_id'],r['generator']),{})[r['condition']]=r
    if len(by)!=24: raise SystemExit(f'expected 24 prompt/model pairs, found {len(by)}')
    data=[]
    for (pid,gen),arms in sorted(by.items()):
        if set(arms)!={'baseline','selfscore'}: raise SystemExit(f'incomplete pair {pid}/{gen}')
        b,s=arms['baseline'],arms['selfscore']
        if b['provider_reported']!=s['provider_reported']: raise SystemExit(f'provider mismatch {pid}/{gen}: {b["provider_reported"]} vs {s["provider_reported"]}')
        data.append({'prompt_id':pid,'domain':b['domain'],'generator':gen,'task':b['task'],'baseline':b['clean_text'],'selfscore':s['clean_text']})
    # The study id changes if the embedded data changes, preventing accidental resume across datasets.
    blob=json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    import hashlib
    study='ru24-'+hashlib.sha256(blob.encode()).hexdigest()[:12]
    page=TEMPLATE.replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('</','<\\/')).replace('__STUDY__',study)
    Path(args.out).write_text(page,encoding='utf-8')
    print(f'wrote {args.out} with {len(data)} blinded pairs; study={study}')

if __name__=='__main__': main()

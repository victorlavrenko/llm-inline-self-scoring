#!/usr/bin/env python3
from __future__ import annotations
import argparse, concurrent.futures, csv, json, os, random, re, sqlite3, threading, time
import urllib.error, urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

VERSION = "ru-human-validation-v1"

COMMON = (
    "Точно следуй заданию пользователя и его требованиям к формату.\n\n"
    "При написании активно избегай типичного AI-slop: общих фраз, шаблонной структуры, "
    "клише, чрезмерно отполированного или рекламного тона, повторов и формулировок, "
    "которые очевидно звучат как текст нейросети. Предпочитай конкретный, естественный, "
    "специфичный язык, похожий на то, как реально написал бы человек."
)
BASELINE_SYSTEM = COMMON + "\n\nВыведи только запрошенный текст."
SCORE_INSTRUCTION = (
    "После каждого предложения оцени, насколько вероятно, что средний русскоязычный читатель "
    "сочтёт именно это предложение сгенерированным ИИ. Используй целое число от 0 до 100, "
    "где 0 означает очень человеческий текст, а 100 — явно сгенерированный ИИ. Сначала поставь "
    "обычный знак окончания предложения, а сразу после него добавь оценку в формате <AI SCORE: n>."
)
SELFSCORE_SYSTEM = COMMON + "\n\n" + SCORE_INSTRUCTION + "\n\nВыведи только запрошенный текст и обязательные теги AI SCORE."

SCORE_TAG = re.compile(r"<\s*AI\s+SCORE\s*:\s*\(?\s*(\d{1,3})\s*\)?\s*>", re.I)
SCORE_ANY = re.compile(r"<\s*AI\s+SCORE\s*:\s*[^>\r\n]{0,40}>", re.I)
BARE_SCORE = re.compile(r"(?<!<)\bAI\s+SCORE\s*:\s*\(?\s*\d{1,3}\s*\)?\b", re.I)

@dataclass(frozen=True)
class Model:
    alias: str
    route: str
    provider: str

@dataclass(frozen=True)
class Job:
    prompt_id: str
    domain: str
    task: str
    model: Model
    condition: str


def clean_text(s: str) -> str:
    s=s.replace("\r\n","\n").replace("\r","\n")
    s=re.sub(r"[ \t]+"," ",s)
    s=re.sub(r" *\n *","\n",s)
    s=re.sub(r"\n{3,}","\n\n",s)
    return s.strip()


def strip_scores(s: str):
    vals=[int(m.group(1)) for m in SCORE_TAG.finditer(s) if 0 <= int(m.group(1)) <= 100]
    t=SCORE_ANY.sub("",s)
    t=BARE_SCORE.sub("",t)
    return clean_text(t), vals


def load_models(path: Path):
    data=json.loads(path.read_text(encoding="utf-8"))
    return {x["alias"]: Model(x["alias"],x["route"],x["provider"]) for x in data["models"]}


def load_prompts(path: Path, models: dict[str,Model]):
    out=[]
    seen=set()
    for ln,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        x=json.loads(line)
        if x["prompt_id"] in seen: raise ValueError(f"duplicate prompt_id {x['prompt_id']}")
        seen.add(x["prompt_id"])
        if x["generator"] not in models: raise ValueError(f"unknown generator {x['generator']} line {ln}")
        out.append(x)
    return out


class Store:
    def __init__(self,path:Path):
        path.parent.mkdir(parents=True,exist_ok=True)
        self.conn=sqlite3.connect(path,check_same_thread=False,timeout=60)
        self.lock=threading.Lock()
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS generations(
          prompt_id TEXT NOT NULL, domain TEXT NOT NULL, task TEXT NOT NULL,
          generator TEXT NOT NULL, route TEXT NOT NULL, provider_requested TEXT NOT NULL,
          provider_reported TEXT, condition TEXT NOT NULL,
          raw_text TEXT NOT NULL, clean_text TEXT NOT NULL, scores_json TEXT NOT NULL,
          score_count INTEGER NOT NULL, finish_reason TEXT,
          completion_tokens INTEGER, created_at REAL NOT NULL,
          PRIMARY KEY(prompt_id,generator,condition))""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS attempts(
          job_key TEXT NOT NULL, attempt_no INTEGER NOT NULL, success INTEGER NOT NULL,
          error TEXT, provider_reported TEXT, finish_reason TEXT, max_tokens INTEGER NOT NULL,
          created_at REAL NOT NULL, PRIMARY KEY(job_key,attempt_no))""")
        self.conn.commit()
    def done(self,j:Job):
        with self.lock:
            r=self.conn.execute("SELECT 1 FROM generations WHERE prompt_id=? AND generator=? AND condition=?",(j.prompt_id,j.model.alias,j.condition)).fetchone()
        return bool(r)
    def save_attempt(self,key,no,success,error,provider,finish,max_tokens):
        with self.lock:
            self.conn.execute("INSERT OR REPLACE INTO attempts VALUES(?,?,?,?,?,?,?,?)",(key,no,int(success),error,provider,finish,max_tokens,time.time()))
            self.conn.commit()
    def save(self,j:Job,res:dict,clean:str,scores:list[int]):
        with self.lock:
            self.conn.execute("""INSERT OR REPLACE INTO generations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(
                j.prompt_id,j.domain,j.task,j.model.alias,j.model.route,j.model.provider,res.get("provider"),j.condition,
                res["text"],clean,json.dumps(scores),len(scores),res.get("finish_reason"),res.get("completion_tokens"),time.time()))
            self.conn.commit()
    def rows(self):
        with self.lock:
            cur=self.conn.execute("SELECT * FROM generations ORDER BY generator,prompt_id,condition")
            cols=[d[0] for d in cur.description]
            return [dict(zip(cols,r)) for r in cur.fetchall()]
    def close(self): self.conn.close()


def call_openrouter(api_key:str,m:Model,messages:list[dict[str,str]],max_tokens:int,timeout:float,retries:int):
    payload={
        "model":m.route,"messages":messages,"temperature":0.7,"max_tokens":max_tokens,
        "provider":{"only":[m.provider],"allow_fallbacks":False}
    }
    body=json.dumps(payload,ensure_ascii=False).encode("utf-8")
    last=None
    for a in range(retries):
        req=urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",data=body,method="POST",headers={
            "Authorization":f"Bearer {api_key}","Content-Type":"application/json",
            "HTTP-Referer":"https://github.com/victorlavrenko","X-Title":"Russian self-score human validation"})
        try:
            with urllib.request.urlopen(req,timeout=timeout) as r: data=json.loads(r.read().decode("utf-8"))
            ch=(data.get("choices") or [None])[0]
            if not ch: raise RuntimeError("response has no choices")
            content=(ch.get("message") or {}).get("content","")
            if isinstance(content,list): content="".join(str(x.get("text","")) for x in content if isinstance(x,dict) and x.get("type")=="text")
            usage=data.get("usage") or {}
            return {"text":content or "","provider":data.get("provider"),"finish_reason":ch.get("finish_reason"),"completion_tokens":usage.get("completion_tokens")}
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,json.JSONDecodeError,RuntimeError) as e:
            last=e
            retryable=not isinstance(e,urllib.error.HTTPError) or e.code in {408,409,429,500,502,503,504}
            if a+1>=retries or not retryable: break
            time.sleep(min(30,1.5*(2**a))+random.random()*0.3)
    raise last


def export_csv(store:Store,path:Path):
    rows=store.rows(); path.parent.mkdir(parents=True,exist_ok=True)
    if not rows: return
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--models",default="models.json")
    ap.add_argument("--prompts",default="prompts_ru.jsonl")
    ap.add_argument("--out",default="runs/ru-human")
    ap.add_argument("--workers",type=int,default=16)
    ap.add_argument("--per-model-workers",type=int,default=4)
    ap.add_argument("--max-tokens",type=int,default=8192)
    ap.add_argument("--retry-max-tokens",type=int,default=16384)
    ap.add_argument("--timeout",type=float,default=240)
    ap.add_argument("--retries",type=int,default=4)
    ap.add_argument("--dry-run",action="store_true")
    args=ap.parse_args()
    models=load_models(Path(args.models)); prompts=load_prompts(Path(args.prompts),models)
    counts={a:0 for a in models}
    jobs=[]
    for p in prompts:
        m=models[p["generator"]]; counts[m.alias]+=1
        for c in ("baseline","selfscore"): jobs.append(Job(p["prompt_id"],p["domain"],p["task"],m,c))
    print(f"prompts={len(prompts)} pairs={len(prompts)} generation_calls={len(jobs)}")
    print("pairs per generator:",", ".join(f"{k}={v}" for k,v in counts.items()))
    if args.dry_run: return
    key=os.environ.get("OPENROUTER_API_KEY")
    if not key: raise SystemExit("OPENROUTER_API_KEY is not set")
    out=Path(args.out); store=Store(out/"state.sqlite3")
    pending=[j for j in jobs if not store.done(j)]
    random.Random(20261004).shuffle(pending)
    print(f"generation pending: {len(pending)}")
    sems={k:threading.BoundedSemaphore(args.per_model_workers) for k in models}
    plock=threading.Lock(); done=0
    def one(j:Job):
        nonlocal done
        sys=BASELINE_SYSTEM if j.condition=="baseline" else SELFSCORE_SYSTEM
        messages=[{"role":"system","content":sys},{"role":"user","content":j.task}]
        accepted=None; last=None
        for no,budget in enumerate((args.max_tokens,args.retry_max_tokens),1):
            res=None; err=None; ok=False
            try:
                with sems[j.model.alias]: res=call_openrouter(key,j.model,messages,budget,args.timeout,args.retries)
                if not res["text"].strip(): raise RuntimeError("empty visible output")
                if str(res.get("finish_reason") or "").lower()=="length": raise RuntimeError(f"finish_reason=length at {budget} tokens")
                clean,scores=strip_scores(res["text"])
                if not clean: raise RuntimeError("cleaned output empty")
                if j.condition=="selfscore" and not scores: raise RuntimeError("selfscore output has no valid <AI SCORE: n> tags")
                accepted=(res,clean,scores); ok=True
            except Exception as e: last=e; err=str(e)
            store.save_attempt(f"{j.prompt_id}|{j.model.alias}|{j.condition}",no,ok,err,res.get("provider") if res else None,res.get("finish_reason") if res else None,budget)
            if accepted: break
        if not accepted: raise last
        store.save(j,*accepted)
        with plock:
            done+=1
            if done%5==0 or done==len(pending): print(f"generation {done}/{len(pending)}",flush=True)
    errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs={ex.submit(one,j):j for j in pending}
        for f,j in list(futs.items()):
            try: f.result()
            except Exception as e:
                errors.append((j,e)); print(f"GEN ERROR {j.model.alias} {j.prompt_id} {j.condition}: {e}",flush=True)
    export_csv(store,out/"generations.csv")
    rows=store.rows(); store.close()
    print(f"stored generations: {len(rows)}/{len(jobs)}")
    if errors:
        print(f"failed jobs: {len(errors)}; rerun the same command to retry only missing jobs")
        raise SystemExit(2)
    # Integrity checks.
    pair={(r['prompt_id'],r['generator']) for r in rows}
    bad=[]
    for pid,gen in pair:
        rr=[r for r in rows if r['prompt_id']==pid and r['generator']==gen]
        if {r['condition'] for r in rr}!={"baseline","selfscore"}: bad.append((pid,gen,"missing arm"))
        providers={r['provider_reported'] for r in rr}
        if len(providers)!=1: bad.append((pid,gen,f"provider mismatch {providers}"))
    if bad:
        print("INTEGRITY WARNINGS:")
        for x in bad: print(" ",x)
        raise SystemExit(3)
    print("generation complete; provider matched within every pair")

if __name__=="__main__": main()

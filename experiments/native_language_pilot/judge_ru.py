#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import random
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

JUDGE_PROTOCOL = "ru-blind-slop-pairwise-v2"
SEED = 20261005

JUDGE_SYSTEM = (
    "Ты проводишь слепое попарное сравнение стиля двух русских текстов. "
    "Тебе будут даны исходное задание и два ответа. Определи только то, какой ПОЛНЫЙ ответ "
    "сильнее похож на типичный AI-slop — шаблонный текст нейросети. Признаки AI-slop: общие и "
    "дежурные фразы, клише, чрезмерно гладкие переходы, отполированные, но расплывчатые формулировки, "
    "повторяющаяся структура, ненужные вступления, натянутые выводы и резюме, рекламный или назидательный "
    "тон, излишняя симметрия и другие стилистические признаки машинного текста. Не пытайся угадать, как "
    "был получен ответ. Не награждай и не штрафуй текст только за длину. Фактическая точность не является "
    "главной целью, кроме случаев, когда ошибка сама проявляется как типичная общая или уклончивая AI-фраза. "
    "Если заметной разницы в AI-slop нет, выбери TIE. Верни ровно один токен: A, B или TIE."
)

@dataclass(frozen=True)
class Model:
    alias: str
    route: str
    provider: str


def load_models(path: Path) -> dict[str, Model]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    return {r["alias"]: Model(r["alias"], r["route"], r["provider"]) for r in obj["models"]}


def parse_verdict(text: str) -> str:
    raw = (text or "").strip()
    s = raw.upper().strip("`* \t\r\n.:;,-\"'")
    if s in {"A", "B", "TIE"}:
        return s
    first = next((ln.strip() for ln in raw.splitlines() if ln.strip()), "")
    fu = first.upper().strip("`* \t\r\n.:;,-\"'")
    m = re.match(r"^(?:(?:VERDICT|ANSWER|CHOICE|ОТВЕТ|ВЫБОР)\s*[:=\-]?\s*)?(TIE|A|B)(?:\b|$)", fu)
    if m:
        return m.group(1)
    last = next((ln.strip() for ln in reversed(raw.splitlines()) if ln.strip()), "")
    lu = last.upper().strip("`* \t\r\n.:;,-\"'")
    m = re.fullmatch(r"(?:(?:VERDICT|ANSWER|CHOICE|ОТВЕТ|ВЫБОР)\s*[:=\-]?\s*)?(TIE|A|B)", lu)
    if m:
        return m.group(1)
    raise ValueError(f"unparseable judge verdict: {text!r}")


def judge_messages(task: str, a: str, b: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": (
            "ИСХОДНОЕ ЗАДАНИЕ\n-----------------\n" + task +
            "\n\nТЕКСТ A\n-------\n" + a +
            "\n\nТЕКСТ B\n-------\n" + b +
            "\n\nКакой текст СИЛЬНЕЕ похож на AI-slop? Верни ровно A, B или TIE."
        )},
    ]


def call_openrouter(api_key: str, m: Model, messages: list[dict[str, str]], *, max_tokens: int,
                    timeout: float, retries: int, reasoning_effort: str = "low") -> dict:
    payload = {
        "model": m.route,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "provider": {"only": [m.provider], "allow_fallbacks": False},
        "reasoning": {"effort": reasoning_effort, "exclude": True},
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    last = None
    for i in range(retries):
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/victorlavrenko",
                "X-Title": "Russian self-score validation judges",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
            ch = (data.get("choices") or [None])[0]
            if not ch:
                raise RuntimeError("response has no choices")
            msg = ch.get("message") or {}
            content = msg.get("content", "")
            if isinstance(content, list):
                content = "".join(str(x.get("text", "")) for x in content if isinstance(x, dict) and x.get("type") == "text")
            usage = data.get("usage") or {}
            details = usage.get("completion_tokens_details") or {}
            return {
                "text": content or "",
                "provider": data.get("provider"),
                "finish_reason": ch.get("finish_reason"),
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "reasoning_tokens": details.get("reasoning_tokens"),
            }
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as e:
            last = e
            retryable = not isinstance(e, urllib.error.HTTPError) or e.code in {408,409,429,500,502,503,504}
            if i + 1 >= retries or not retryable:
                break
            time.sleep(min(30.0, 1.5 * (2 ** i)) + random.random() * 0.3)
    raise last


class Store:
    def __init__(self, path: Path):
        self.conn = sqlite3.connect(path, check_same_thread=False, timeout=60)
        self.lock = threading.Lock()
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS judgments(
            pair_id TEXT NOT NULL, prompt_id TEXT NOT NULL, domain TEXT NOT NULL, generator TEXT NOT NULL,
            judge TEXT NOT NULL, judge_route TEXT NOT NULL, judge_provider_requested TEXT NOT NULL,
            orientation INTEGER NOT NULL, baseline_is_a INTEGER NOT NULL, verdict TEXT NOT NULL,
            canonical_outcome TEXT NOT NULL, is_self_judge INTEGER NOT NULL,
            provider_reported TEXT, finish_reason TEXT, prompt_tokens INTEGER, completion_tokens INTEGER,
            reasoning_tokens INTEGER, raw_response TEXT NOT NULL, created_at REAL NOT NULL,
            PRIMARY KEY(pair_id, judge, orientation)
        )""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS judge_attempts(
            job_id TEXT NOT NULL, attempt_no INTEGER NOT NULL, prompt_id TEXT NOT NULL, generator TEXT NOT NULL,
            judge TEXT NOT NULL, orientation INTEGER NOT NULL, max_tokens INTEGER NOT NULL,
            reasoning_effort TEXT NOT NULL, success INTEGER NOT NULL, error TEXT,
            provider_reported TEXT, finish_reason TEXT, visible_response TEXT,
            completion_tokens INTEGER, reasoning_tokens INTEGER, created_at REAL NOT NULL,
            PRIMARY KEY(job_id, attempt_no)
        )""")
        self.conn.commit()

    def generation_pairs(self) -> list[dict]:
        q = """SELECT b.prompt_id,b.domain,b.task,b.generator,b.clean_text AS baseline,
                      s.clean_text AS selfscore,b.provider_reported AS baseline_provider,
                      s.provider_reported AS selfscore_provider
               FROM generations b JOIN generations s
                 ON b.prompt_id=s.prompt_id AND b.generator=s.generator
               WHERE b.condition='baseline' AND s.condition='selfscore'
               ORDER BY b.generator,b.prompt_id"""
        cur = self.conn.execute(q)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

    def done(self, pair_id: str, judge: str, orientation: int) -> bool:
        with self.lock:
            r = self.conn.execute("SELECT 1 FROM judgments WHERE pair_id=? AND judge=? AND orientation=?",
                                  (pair_id, judge, orientation)).fetchone()
        return bool(r)

    def attempt(self, row: tuple):
        with self.lock:
            self.conn.execute("INSERT OR REPLACE INTO judge_attempts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", row)
            self.conn.commit()

    def save(self, row: tuple):
        with self.lock:
            self.conn.execute("INSERT OR REPLACE INTO judgments VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", row)
            self.conn.commit()

    def count(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) FROM judgments").fetchone()[0])

    def close(self):
        self.conn.close()


def stable_base_is_a(pair_id: str, judge: str) -> bool:
    h = hashlib.sha256(f"{SEED}|{pair_id}|{judge}|blind".encode()).digest()
    return bool(h[0] & 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="models.json")
    ap.add_argument("--out", default="runs/ru-human")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--per-model-workers", type=int, default=4)
    ap.add_argument("--judge-max-tokens", type=int, default=1024)
    ap.add_argument("--judge-retry-max-tokens", type=int, default=8192)
    ap.add_argument("--timeout", type=float, default=240)
    ap.add_argument("--retries", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    models = load_models(Path(args.models))
    store = Store(Path(args.out) / "state.sqlite3")
    pairs = store.generation_pairs()
    if len(pairs) != 24:
        raise SystemExit(f"expected 24 complete generation pairs, found {len(pairs)}; run generation first")
    jobs = []
    for p in pairs:
        pair_id = f"{p['prompt_id']}|{p['generator']}"
        for judge in models:
            for orientation in (0, 1):
                if not store.done(pair_id, judge, orientation):
                    jobs.append((p, pair_id, judge, orientation))
    print(f"pairs={len(pairs)} judges={len(models)} mirrored_calls_total={len(pairs)*len(models)*2}")
    print(f"judgment pending: {len(jobs)}")
    if args.dry_run:
        store.close(); return
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is not set")
    random.Random(SEED).shuffle(jobs)
    sems = {a: threading.BoundedSemaphore(args.per_model_workers) for a in models}
    plock = threading.Lock(); completed = 0; errors = []

    def one(job):
        nonlocal completed
        p, pair_id, judge_alias, orientation = job
        jm = models[judge_alias]
        base_a0 = stable_base_is_a(pair_id, judge_alias)
        baseline_is_a = base_a0 if orientation == 0 else (not base_a0)
        if baseline_is_a:
            a, b = p["baseline"], p["selfscore"]
        else:
            a, b = p["selfscore"], p["baseline"]
        messages = judge_messages(p["task"], a, b)
        job_id = hashlib.sha256(f"{pair_id}|{judge_alias}|{orientation}|{JUDGE_PROTOCOL}".encode()).hexdigest()[:24]
        accepted = None; last = None
        for attempt_no, budget in enumerate((args.judge_max_tokens, args.judge_retry_max_tokens), 1):
            res = None; err = None; ok = False
            try:
                with sems[judge_alias]:
                    res = call_openrouter(key, jm, messages, max_tokens=budget, timeout=args.timeout,
                                          retries=args.retries, reasoning_effort="low")
                if not res["text"].strip():
                    raise RuntimeError(f"empty visible content (finish_reason={res.get('finish_reason')!r})")
                verdict = parse_verdict(res["text"])
                if verdict == "TIE":
                    canonical = "tie"
                else:
                    more_slop_source = ("baseline" if baseline_is_a else "selfscore") if verdict == "A" else ("selfscore" if baseline_is_a else "baseline")
                    canonical = f"{more_slop_source}_more_slop"
                accepted = (res, verdict, canonical); ok = True
            except Exception as e:
                last = e; err = str(e)
            store.attempt((job_id, attempt_no, p["prompt_id"], p["generator"], judge_alias, orientation,
                           budget, "low", int(ok), err, res.get("provider") if res else None,
                           res.get("finish_reason") if res else None, res.get("text") if res else None,
                           res.get("completion_tokens") if res else None, res.get("reasoning_tokens") if res else None,
                           time.time()))
            if accepted:
                break
        if not accepted:
            raise last
        res, verdict, canonical = accepted
        store.save((pair_id, p["prompt_id"], p["domain"], p["generator"], judge_alias, jm.route, jm.provider,
                    orientation, int(baseline_is_a), verdict, canonical, int(judge_alias == p["generator"]),
                    res.get("provider"), res.get("finish_reason"), res.get("prompt_tokens"),
                    res.get("completion_tokens"), res.get("reasoning_tokens"), res.get("text", ""), time.time()))
        with plock:
            completed += 1
            if completed % 20 == 0 or completed == len(jobs):
                print(f"judgment {completed}/{len(jobs)}", flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(one, j): j for j in jobs}
        for f, j in list(futs.items()):
            try:
                f.result()
            except Exception as e:
                errors.append((j, e))
                p, _, judge, orientation = j
                print(f"JUDGE ERROR {judge} {p['generator']} {p['prompt_id']} orient={orientation}: {e}", flush=True)
    print(f"stored judgments: {store.count()}/{len(pairs)*len(models)*2}")
    store.close()
    if errors:
        print(f"failed judgment jobs: {len(errors)}; rerun the same command to retry only missing jobs")
        raise SystemExit(2)
    print("AI judging complete")

if __name__ == "__main__":
    main()

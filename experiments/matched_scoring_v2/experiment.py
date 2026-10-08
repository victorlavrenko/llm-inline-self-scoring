#!/usr/bin/env python3
"""Criterion-matched inline self-scoring experiment.

For each criterion, compare two matched generation arms:

  objective_only   - optimize only for the selected criterion
  selfscore        - identical criterion objective + sentence-level self-score

Criteria are defined in criteria.json. Score tags are stripped before judging and
are never used for revision, rejection, selection, branching, or regeneration.

Each blind judge returns two endpoints in one call:
  * overall: which answer is better overall for the user's task?
  * target: which answer better satisfies the frozen optimization criterion?

The experiment keeps the same 4 generators, 20 frozen prompts, provider pins,
temperature, resumable SQLite state, deterministic A/B randomization, and mirrored
judging used by the previous self-scoring package.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
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
from typing import Any, Mapping, Sequence

CODE_VERSION = "matched-scoring-2.0"
SCHEMA_VERSION = "1"
GENERATION_PROTOCOL_VERSION = "criterion-matched-objective-v1"
JUDGE_PROTOCOL_VERSION = "blind-dual-endpoint-mirrored-v1"

COMMON_TASK_INSTRUCTION = (
    "Follow the user's task and formatting instructions exactly. "
    "Beyond satisfying the user's task, your only additional optimization objective "
    "is the criterion stated below."
)

RUNTIME_PROVIDER_OVERRIDES: dict[str, str] = {
    "deepseek-v4.1-flash": "together",
}


@dataclass(frozen=True)
class ModelSpec:
    alias: str
    route: str
    provider: str | None


@dataclass(frozen=True)
class Prompt:
    prompt_id: str
    domain: str
    task: str


@dataclass(frozen=True)
class ApiResult:
    text: str
    provider: str | None
    finish_reason: str | None
    latency_s: float
    prompt_tokens: int | None
    completion_tokens: int | None
    reasoning_tokens: int | None


def stable_hash(*parts: Any, n: int = 24) -> str:
    return hashlib.sha256("|".join(str(x) for x in parts).encode("utf-8")).hexdigest()[:n]


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        key, value = s.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


def load_models(path: Path) -> tuple[dict[str, ModelSpec], list[str], list[str]]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    specs: dict[str, ModelSpec] = {}
    generators: list[str] = []
    for row in obj.get("generators", []):
        spec = ModelSpec(str(row["alias"]), str(row["route"]), str(row["provider"]) if row.get("provider") else None)
        specs[spec.alias] = spec
        generators.append(spec.alias)
    judges: list[str] = []
    for row in obj.get("judges", []):
        if isinstance(row, str):
            alias = row
            if alias not in specs:
                raise ValueError(f"judge alias {alias!r} not defined by generators")
            judges.append(alias)
        else:
            spec = ModelSpec(str(row["alias"]), str(row["route"]), str(row["provider"]) if row.get("provider") else None)
            old = specs.get(spec.alias)
            if old is not None and old != spec:
                raise ValueError(f"conflicting model definition for {spec.alias}")
            specs[spec.alias] = spec
            judges.append(spec.alias)
    if not generators or not judges:
        raise ValueError("models file must define generators and judges")
    if len(set(generators)) != len(generators) or len(set(judges)) != len(judges):
        raise ValueError("duplicate generator or judge alias")
    return specs, generators, judges


def load_prompts(path: Path, cases: int | None) -> list[Prompt]:
    rows: list[Prompt] = []
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        obj = json.loads(raw)
        try:
            rows.append(Prompt(str(obj["prompt_id"]), str(obj.get("domain", "unknown")), str(obj.get("task") or obj["full_task"])))
        except Exception as e:
            raise ValueError(f"bad prompt row {n}: {e}") from e
    if cases is not None:
        rows = rows[:cases]
    if not rows:
        raise ValueError("no prompts")
    return rows


def load_criteria(path: Path, selected: str | None = None) -> dict[str, dict[str, Any]]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    required = {"label", "optimization_instruction", "tag", "score_instruction", "target_judge_instruction"}
    for name, cfg in obj.items():
        missing = required - set(cfg)
        if missing:
            raise ValueError(f"criterion {name!r} missing {sorted(missing)}")
    if selected:
        names = [x.strip() for x in selected.split(",") if x.strip()]
        unknown = [x for x in names if x not in obj]
        if unknown:
            raise ValueError(f"unknown criteria: {unknown}")
        return {name: obj[name] for name in names}
    return obj


def objective_system(cfg: Mapping[str, Any]) -> str:
    return (
        COMMON_TASK_INSTRUCTION
        + "\n\nTARGET OPTIMIZATION CRITERION:\n"
        + str(cfg["optimization_instruction"])
        + "\n\nProduce only the requested text."
    )


def selfscore_system(cfg: Mapping[str, Any]) -> str:
    return (
        COMMON_TASK_INSTRUCTION
        + "\n\nTARGET OPTIMIZATION CRITERION:\n"
        + str(cfg["optimization_instruction"])
        + "\n\nINLINE SELF-SCORE:\n"
        + str(cfg["score_instruction"])
        + f"\n\nProduce only the requested text and the required {cfg['tag']} tags."
    )


def generation_messages(task: str, arm: str, cfg: Mapping[str, Any]) -> list[dict[str, str]]:
    if arm == "objective_only":
        system = objective_system(cfg)
    elif arm == "selfscore":
        system = selfscore_system(cfg)
    else:
        raise ValueError(f"unknown arm {arm}")
    return [{"role": "system", "content": system}, {"role": "user", "content": task}]


def normalize_visible_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def tag_regex(tag: str) -> re.Pattern[str]:
    words = r"\s+".join(re.escape(x) for x in tag.split())
    return re.compile(rf"<\s*{words}\s*:\s*\(?\s*(\d{{1,3}})\s*\)?\s*>", re.I)


def loose_tag_regex(tag: str) -> re.Pattern[str]:
    words = r"\s+".join(re.escape(x) for x in tag.split())
    return re.compile(rf"<\s*{words}\s*:\s*[^>\r\n]{{0,40}}>", re.I)


def strip_score(text: str, cfg: Mapping[str, Any]) -> tuple[str, list[int], bool]:
    tag = str(cfg["tag"])
    strict = tag_regex(tag)
    values = [int(m.group(1)) for m in strict.finditer(text)]
    cleaned = loose_tag_regex(tag).sub("", text)
    # Remove a bare leaked form such as "AI SCORE: 12" if it occurs without brackets.
    bare_words = r"\s+".join(re.escape(x) for x in tag.split())
    cleaned = re.sub(rf"(?<!<)\b{bare_words}\s*:\s*\(?\s*\d{{1,3}}\s*\)?\b", "", cleaned, flags=re.I)
    cleaned = normalize_visible_text(cleaned)
    leak = bool(re.search(r"\b" + r"\s+".join(re.escape(x) for x in tag.split()) + r"\b", cleaned, re.I))
    return cleaned, values, leak


def generation_compliance(arm: str, raw_text: str, cfg: Mapping[str, Any]) -> tuple[bool, str, int, bool, str]:
    if arm == "objective_only":
        clean = normalize_visible_text(raw_text)
        return bool(clean), "ok" if clean else "empty", 0, False, clean
    clean, values, leak = strip_score(raw_text, cfg)
    if not clean:
        return False, "empty_after_stripping", len(values), leak, clean
    if leak:
        return False, "tag_leak", len(values), leak, clean
    if len(values) < 5:
        return False, f"too_few_tags:{len(values)}", len(values), leak, clean
    if any(v < 0 or v > 100 for v in values):
        return False, "score_out_of_range", len(values), leak, clean
    return True, "ok", len(values), leak, clean


def judge_messages(task: str, cfg: Mapping[str, Any], answer_a: str, answer_b: str) -> list[dict[str, str]]:
    system = (
        "You are a blind pairwise evaluator. You will receive an original user task, "
        "a target optimization criterion, and two candidate answers. Evaluate two distinct endpoints.\n\n"
        "OVERALL: Which complete answer is better overall for the user's task? Consider correctness, relevance, clarity, "
        "coherence, naturalness, specificity, and instruction following. Do not reward or punish an answer merely for being longer.\n\n"
        "TARGET: Which answer better satisfies the stated target criterion while still fulfilling the user's task? Use the "
        "criterion-specific rule supplied below.\n\n"
        "Do not try to infer how either answer was produced. If neither answer is meaningfully better on an endpoint, use TIE. "
        "Return exactly one JSON object and no other text: {\"overall\":\"A|B|TIE\",\"target\":\"A|B|TIE\"}."
    )
    user = (
        "ORIGINAL USER TASK\n------------------\n" + task
        + "\n\nTARGET CRITERION\n----------------\n" + str(cfg["label"])
        + "\n\nTARGET EVALUATION RULE\n----------------------\n" + str(cfg["target_judge_instruction"])
        + "\n\nANSWER A\n--------\n" + answer_a
        + "\n\nANSWER B\n--------\n" + answer_b
        + "\n\nReturn exactly: {\"overall\":\"A|B|TIE\",\"target\":\"A|B|TIE\"}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def parse_dual_verdict(text: str) -> tuple[str, str]:
    raw = text.strip()
    # Strip a harmless fenced wrapper if a model ignored the no-fence request.
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
    raw = re.sub(r"\s*```$", "", raw)
    obj: Any = None
    try:
        obj = json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, flags=re.S)
        if m:
            try:
                obj = json.loads(m.group(0))
            except Exception:
                obj = None
    if not isinstance(obj, dict):
        raise ValueError(f"unparseable dual verdict: {text!r}")
    overall = str(obj.get("overall", "")).upper().strip()
    target = str(obj.get("target", "")).upper().strip()
    if overall not in {"A", "B", "TIE"} or target not in {"A", "B", "TIE"}:
        raise ValueError(f"bad dual verdict values: {obj!r}")
    return overall, target


class OpenRouterClient:
    def __init__(self, api_key: str, timeout_s: float, retries: int):
        self.api_key = api_key
        self.timeout_s = timeout_s
        self.retries = retries

    def call(
        self,
        spec: ModelSpec,
        messages: Sequence[Mapping[str, str]],
        *,
        temperature: float,
        max_tokens: int,
        reasoning_effort: str | None = None,
    ) -> ApiResult:
        payload: dict[str, Any] = {
            "model": spec.route,
            "messages": list(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if reasoning_effort:
            payload["reasoning"] = {"effort": reasoning_effort, "exclude": True}
        provider = RUNTIME_PROVIDER_OVERRIDES.get(spec.alias, spec.provider)
        if provider:
            payload["provider"] = {"only": [provider], "allow_fallbacks": False}
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            started = time.perf_counter()
            request = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=body,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/victorlavrenko",
                    "X-Title": "Criterion-matched inline self-scoring experiment",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                    raw = response.read()
                latency = time.perf_counter() - started
                data = json.loads(raw.decode("utf-8"))
                choices = data.get("choices") or []
                if not choices:
                    raise RuntimeError("OpenRouter response has no choices")
                choice = choices[0]
                msg = choice.get("message") or {}
                content = msg.get("content")
                if isinstance(content, list):
                    parts: list[str] = []
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            parts.append(str(item.get("text", "")))
                    content = "".join(parts)
                if not isinstance(content, str):
                    content = ""
                usage = data.get("usage") or {}
                details = usage.get("completion_tokens_details") or {}
                return ApiResult(
                    text=content,
                    provider=str(data.get("provider")) if data.get("provider") is not None else None,
                    finish_reason=str(choice.get("finish_reason")) if choice.get("finish_reason") is not None else None,
                    latency_s=latency,
                    prompt_tokens=_int_or_none(usage.get("prompt_tokens")),
                    completion_tokens=_int_or_none(usage.get("completion_tokens")),
                    reasoning_tokens=_int_or_none(details.get("reasoning_tokens")),
                )
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
                last_error = exc
                retryable = True
                if isinstance(exc, urllib.error.HTTPError):
                    retryable = exc.code in {408, 409, 429, 500, 502, 503, 504}
                if attempt >= self.retries or not retryable:
                    break
                delay = min(90.0, 1.5 * (2 ** (attempt - 1)))
                if isinstance(exc, urllib.error.HTTPError):
                    retry_after = exc.headers.get("Retry-After")
                    if retry_after:
                        try:
                            delay = max(delay, float(retry_after))
                        except ValueError:
                            pass
                time.sleep(delay)
        assert last_error is not None
        raise last_error


def _int_or_none(x: Any) -> int | None:
    try:
        return int(x) if x is not None else None
    except Exception:
        return None


class Store:
    def __init__(self, out: Path):
        self.out = out
        self.out.mkdir(parents=True, exist_ok=True)
        self.db_path = out / "experiment.sqlite3"
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=60)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self._schema()

    def _schema(self) -> None:
        with self.conn:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS generations(
                  prompt_id TEXT NOT NULL, domain TEXT NOT NULL, task TEXT NOT NULL,
                  generator TEXT NOT NULL, route TEXT NOT NULL, criterion TEXT NOT NULL,
                  arm TEXT NOT NULL, replicate INTEGER NOT NULL,
                  raw_text TEXT NOT NULL, clean_text TEXT NOT NULL,
                  values_json TEXT NOT NULL, tag_count INTEGER NOT NULL,
                  compliant INTEGER NOT NULL, compliance_reason TEXT NOT NULL, tag_leak INTEGER NOT NULL,
                  provider TEXT, finish_reason TEXT, latency_s REAL,
                  prompt_tokens INTEGER, completion_tokens INTEGER, reasoning_tokens INTEGER,
                  created_at REAL NOT NULL,
                  PRIMARY KEY(prompt_id,generator,criterion,arm,replicate)
                );
                CREATE TABLE IF NOT EXISTS attempts(
                  kind TEXT NOT NULL, key TEXT NOT NULL, attempt INTEGER NOT NULL,
                  model TEXT NOT NULL, ok INTEGER NOT NULL, error TEXT, raw_text TEXT,
                  provider TEXT, finish_reason TEXT, latency_s REAL, created_at REAL NOT NULL,
                  PRIMARY KEY(kind,key,attempt)
                );
                CREATE TABLE IF NOT EXISTS judgments(
                  pair_id TEXT NOT NULL, prompt_id TEXT NOT NULL, generator TEXT NOT NULL,
                  criterion TEXT NOT NULL, replicate INTEGER NOT NULL, judge TEXT NOT NULL,
                  orientation INTEGER NOT NULL, a_source TEXT NOT NULL, b_source TEXT NOT NULL,
                  verdict_overall TEXT NOT NULL, verdict_target TEXT NOT NULL,
                  overall_winner TEXT NOT NULL, target_winner TEXT NOT NULL,
                  raw_text TEXT NOT NULL, provider TEXT, latency_s REAL, created_at REAL NOT NULL,
                  PRIMARY KEY(pair_id,judge,orientation)
                );
                """
            )

    def ensure_identity(self, identity: Mapping[str, Any]) -> None:
        blob = json.dumps(identity, sort_keys=True, ensure_ascii=False)
        fp = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        with self.lock, self.conn:
            row = self.conn.execute("SELECT v FROM meta WHERE k='fingerprint'").fetchone()
            if row and row[0] != fp:
                raise RuntimeError("run identity mismatch: use a new --out directory")
            self.conn.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('fingerprint',?)", (fp,))
            self.conn.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('identity_json',?)", (blob,))

    def generation_done(self, prompt_id: str, generator: str, criterion: str, arm: str, replicate: int) -> bool:
        with self.lock:
            row = self.conn.execute(
                "SELECT 1 FROM generations WHERE prompt_id=? AND generator=? AND criterion=? AND arm=? AND replicate=?",
                (prompt_id, generator, criterion, arm, replicate),
            ).fetchone()
        return row is not None

    def judgment_done(self, pair_id: str, judge: str, orientation: int) -> bool:
        with self.lock:
            row = self.conn.execute(
                "SELECT 1 FROM judgments WHERE pair_id=? AND judge=? AND orientation=?",
                (pair_id, judge, orientation),
            ).fetchone()
        return row is not None

    def save_generation(self, row: Mapping[str, Any]) -> None:
        cols = list(row)
        with self.lock, self.conn:
            self.conn.execute(
                f"INSERT OR REPLACE INTO generations({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",
                tuple(row[c] for c in cols),
            )

    def save_attempt(self, row: Mapping[str, Any]) -> None:
        cols = list(row)
        with self.lock, self.conn:
            self.conn.execute(
                f"INSERT OR REPLACE INTO attempts({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",
                tuple(row[c] for c in cols),
            )

    def save_judgment(self, row: Mapping[str, Any]) -> None:
        cols = list(row)
        with self.lock, self.conn:
            self.conn.execute(
                f"INSERT OR REPLACE INTO judgments({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",
                tuple(row[c] for c in cols),
            )

    def pairs(self) -> list[dict[str, Any]]:
        query = """
        SELECT s.prompt_id,s.domain,s.task,s.generator,s.criterion,s.replicate,
               b.clean_text objective_text,s.clean_text selfscore_text,
               b.compliant objective_compliant,s.compliant selfscore_compliant,
               s.compliance_reason selfscore_compliance_reason,s.tag_leak
        FROM generations s
        JOIN generations b
          ON b.prompt_id=s.prompt_id
         AND b.generator=s.generator
         AND b.criterion=s.criterion
         AND b.replicate=s.replicate
         AND b.arm='objective_only'
        WHERE s.arm='selfscore'
        ORDER BY s.criterion,s.generator,s.prompt_id,s.replicate
        """
        with self.lock:
            return [dict(r) for r in self.conn.execute(query)]

    def export_csv(self) -> None:
        result_dir = self.out / "results"
        result_dir.mkdir(exist_ok=True)
        for table in ("generations", "judgments", "attempts"):
            with self.lock:
                cur = self.conn.execute(f"SELECT * FROM {table}")
                rows = cur.fetchall()
                fields = [x[0] for x in cur.description]
            with (result_dir / f"{table}.csv").open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(fields)
                w.writerows(rows)


class Experiment:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.models_path = Path(args.models)
        self.prompts_path = Path(args.prompts)
        self.criteria_path = Path(args.criteria_file)
        self.specs, self.generators, self.judges = load_models(self.models_path)
        self.prompts = load_prompts(self.prompts_path, args.cases)
        self.criteria = load_criteria(self.criteria_path, args.criteria)
        load_dotenv(Path(".env"))
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        self.store = Store(Path(args.out))
        self.client = OpenRouterClient(api_key, args.timeout, args.retries)
        identity = {
            "code_version": CODE_VERSION,
            "schema_version": SCHEMA_VERSION,
            "generation_protocol": GENERATION_PROTOCOL_VERSION,
            "judge_protocol": JUDGE_PROTOCOL_VERSION,
            "models_sha256": file_sha(self.models_path),
            "prompts_sha256": file_sha(self.prompts_path),
            "criteria_sha256": file_sha(self.criteria_path),
            "selected_criteria": list(self.criteria),
            "cases": args.cases,
            "replicates": args.replicates,
            "seed": args.seed,
            "generation_temperature": args.generation_temperature,
            "judge_temperature": args.judge_temperature,
            "mirror": args.mirror,
            "provider_overrides": RUNTIME_PROVIDER_OVERRIDES,
        }
        self.store.ensure_identity(identity)
        manifest = Path(args.out) / "manifest.json"
        manifest.write_text(
            json.dumps(
                identity
                | {
                    "generators": self.generators,
                    "judges": self.judges,
                    "prompt_ids": [p.prompt_id for p in self.prompts],
                    "arms": ["objective_only", "selfscore"],
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def run_generate(self) -> None:
        jobs: list[tuple[Prompt, str, str, str, int]] = []
        for p in self.prompts:
            for generator in self.generators:
                for criterion in self.criteria:
                    for arm in ("objective_only", "selfscore"):
                        for replicate in range(self.args.replicates):
                            if not self.store.generation_done(p.prompt_id, generator, criterion, arm, replicate):
                                jobs.append((p, generator, criterion, arm, replicate))
        random.Random(self.args.seed + 101).shuffle(jobs)
        print(f"generation pending: {len(jobs)}", flush=True)
        semaphores = {g: threading.Semaphore(self.args.per_model_workers) for g in self.generators}
        progress_lock = threading.Lock()
        done = 0
        failures = 0

        def one(job: tuple[Prompt, str, str, str, int]) -> None:
            nonlocal done, failures
            p, generator, criterion, arm, replicate = job
            cfg = self.criteria[criterion]
            key = stable_hash(p.prompt_id, generator, criterion, arm, replicate, "generation")
            accepted: ApiResult | None = None
            last_error: Exception | None = None
            ceilings = [self.args.generation_max_tokens, self.args.generation_retry_max_tokens]
            with semaphores[generator]:
                for attempt, ceiling in enumerate(ceilings, 1):
                    try:
                        result = self.client.call(
                            self.specs[generator],
                            generation_messages(p.task, arm, cfg),
                            temperature=self.args.generation_temperature,
                            max_tokens=ceiling,
                        )
                        ok = bool(result.text.strip()) and result.finish_reason != "length"
                        self.store.save_attempt(
                            {
                                "kind": "generation",
                                "key": key,
                                "attempt": attempt,
                                "model": generator,
                                "ok": int(ok),
                                "error": None if ok else f"finish_reason={result.finish_reason}",
                                "raw_text": result.text,
                                "provider": result.provider,
                                "finish_reason": result.finish_reason,
                                "latency_s": result.latency_s,
                                "created_at": time.time(),
                            }
                        )
                        if ok:
                            accepted = result
                            break
                    except Exception as e:
                        last_error = e
                        self.store.save_attempt(
                            {
                                "kind": "generation",
                                "key": key,
                                "attempt": attempt,
                                "model": generator,
                                "ok": 0,
                                "error": repr(e),
                                "raw_text": None,
                                "provider": None,
                                "finish_reason": None,
                                "latency_s": None,
                                "created_at": time.time(),
                            }
                        )
            if accepted is None:
                with progress_lock:
                    failures += 1
                raise RuntimeError(last_error or "generation failed")
            compliant, reason, tag_count, leak, clean = generation_compliance(arm, accepted.text, cfg)
            values: list[int] = []
            if arm == "selfscore":
                _, values, _ = strip_score(accepted.text, cfg)
            self.store.save_generation(
                {
                    "prompt_id": p.prompt_id,
                    "domain": p.domain,
                    "task": p.task,
                    "generator": generator,
                    "route": self.specs[generator].route,
                    "criterion": criterion,
                    "arm": arm,
                    "replicate": replicate,
                    "raw_text": accepted.text,
                    "clean_text": clean,
                    "values_json": json.dumps(values),
                    "tag_count": tag_count,
                    "compliant": int(compliant),
                    "compliance_reason": reason,
                    "tag_leak": int(leak),
                    "provider": accepted.provider,
                    "finish_reason": accepted.finish_reason,
                    "latency_s": accepted.latency_s,
                    "prompt_tokens": accepted.prompt_tokens,
                    "completion_tokens": accepted.completion_tokens,
                    "reasoning_tokens": accepted.reasoning_tokens,
                    "created_at": time.time(),
                }
            )
            with progress_lock:
                done += 1
                if done % 10 == 0 or done == len(jobs):
                    print(f"generation {done}/{len(jobs)}", flush=True)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.args.workers) as executor:
            futures = [executor.submit(one, job) for job in jobs]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"GEN ERROR: {e}", file=os.sys.stderr, flush=True)
        if failures:
            print(f"generation completed with {failures} failed jobs; rerun to retry", flush=True)
        self.store.export_csv()

    def _objective_is_a0(self, pair_id: str, judge: str) -> bool:
        digest = hashlib.sha256(f"{self.args.seed}|{pair_id}|{judge}|blind".encode()).digest()
        return bool(digest[0] & 1)

    def run_judge(self) -> None:
        jobs: list[tuple[dict[str, Any], str, int]] = []
        orientations = (0, 1) if self.args.mirror else (0,)
        skipped = 0
        for pair in self.store.pairs():
            if not int(pair["objective_compliant"]) or not int(pair["selfscore_compliant"]) or int(pair["tag_leak"]):
                skipped += 1
                continue
            pair_id = stable_hash(pair["prompt_id"], pair["generator"], pair["criterion"], pair["replicate"], "pair")
            pair["pair_id"] = pair_id
            for judge in self.judges:
                for orientation in orientations:
                    if not self.store.judgment_done(pair_id, judge, orientation):
                        jobs.append((pair, judge, orientation))
        random.Random(self.args.seed + 202).shuffle(jobs)
        print(f"judgment pending: {len(jobs)}; skipped noncompliant/leaked pairs: {skipped}", flush=True)
        semaphores = {j: threading.Semaphore(self.args.per_model_workers) for j in self.judges}
        progress_lock = threading.Lock()
        done = 0
        failures = 0

        def one(job: tuple[dict[str, Any], str, int]) -> None:
            nonlocal done, failures
            pair, judge, orientation = job
            objective_a0 = self._objective_is_a0(pair["pair_id"], judge)
            objective_is_a = objective_a0 if orientation == 0 else not objective_a0
            if objective_is_a:
                a_source, b_source = "objective_only", "selfscore"
                answer_a, answer_b = pair["objective_text"], pair["selfscore_text"]
            else:
                a_source, b_source = "selfscore", "objective_only"
                answer_a, answer_b = pair["selfscore_text"], pair["objective_text"]
            cfg = self.criteria[pair["criterion"]]
            key = stable_hash(pair["pair_id"], judge, orientation, "judge")
            accepted: ApiResult | None = None
            overall: str | None = None
            target: str | None = None
            last_error: Exception | None = None
            ceilings = [self.args.judge_max_tokens, self.args.judge_retry_max_tokens]
            with semaphores[judge]:
                for attempt, ceiling in enumerate(ceilings, 1):
                    try:
                        result = self.client.call(
                            self.specs[judge],
                            judge_messages(pair["task"], cfg, answer_a, answer_b),
                            temperature=self.args.judge_temperature,
                            max_tokens=ceiling,
                            reasoning_effort=self.args.judge_reasoning_effort,
                        )
                        parsed_overall, parsed_target = parse_dual_verdict(result.text)
                        self.store.save_attempt(
                            {
                                "kind": "judge",
                                "key": key,
                                "attempt": attempt,
                                "model": judge,
                                "ok": 1,
                                "error": None,
                                "raw_text": result.text,
                                "provider": result.provider,
                                "finish_reason": result.finish_reason,
                                "latency_s": result.latency_s,
                                "created_at": time.time(),
                            }
                        )
                        accepted = result
                        overall = parsed_overall
                        target = parsed_target
                        break
                    except Exception as e:
                        last_error = e
                        self.store.save_attempt(
                            {
                                "kind": "judge",
                                "key": key,
                                "attempt": attempt,
                                "model": judge,
                                "ok": 0,
                                "error": repr(e),
                                "raw_text": None,
                                "provider": None,
                                "finish_reason": None,
                                "latency_s": None,
                                "created_at": time.time(),
                            }
                        )
            if accepted is None or overall is None or target is None:
                with progress_lock:
                    failures += 1
                raise RuntimeError(last_error or "judge failed")

            def source_winner(verdict: str) -> str:
                if verdict == "TIE":
                    return "tie"
                return a_source if verdict == "A" else b_source

            self.store.save_judgment(
                {
                    "pair_id": pair["pair_id"],
                    "prompt_id": pair["prompt_id"],
                    "generator": pair["generator"],
                    "criterion": pair["criterion"],
                    "replicate": pair["replicate"],
                    "judge": judge,
                    "orientation": orientation,
                    "a_source": a_source,
                    "b_source": b_source,
                    "verdict_overall": overall,
                    "verdict_target": target,
                    "overall_winner": source_winner(overall),
                    "target_winner": source_winner(target),
                    "raw_text": accepted.text,
                    "provider": accepted.provider,
                    "latency_s": accepted.latency_s,
                    "created_at": time.time(),
                }
            )
            with progress_lock:
                done += 1
                if done % 20 == 0 or done == len(jobs):
                    print(f"judgment {done}/{len(jobs)}", flush=True)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.args.workers) as executor:
            futures = [executor.submit(one, job) for job in jobs]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"JUDGE ERROR: {e}", file=os.sys.stderr, flush=True)
        if failures:
            print(f"judgment completed with {failures} failed jobs; rerun to retry", flush=True)
        self.store.export_csv()


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--out", default="runs/matched-full")
    parser.add_argument("--models", default="models_current.json")
    parser.add_argument("--prompts", default="prompts_matched_20.jsonl")
    parser.add_argument("--criteria-file", default="criteria.json")
    parser.add_argument("--criteria", default=None, help="comma-separated criterion subset")
    parser.add_argument("--cases", type=int, default=20)
    parser.add_argument("--replicates", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20261008)
    parser.add_argument("--workers", type=int, default=80)
    parser.add_argument("--per-model-workers", type=int, default=12)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--generation-temperature", type=float, default=0.7)
    parser.add_argument("--judge-temperature", type=float, default=0.0)
    parser.add_argument("--generation-max-tokens", type=int, default=8192)
    parser.add_argument("--generation-retry-max-tokens", type=int, default=16384)
    parser.add_argument("--judge-max-tokens", type=int, default=1024)
    parser.add_argument("--judge-retry-max-tokens", type=int, default=4096)
    parser.add_argument("--judge-reasoning-effort", default="low")
    parser.add_argument("--mirror", action="store_true")


def plan_dict(args: argparse.Namespace) -> dict[str, Any]:
    _, generators, judges = load_models(Path(args.models))
    prompts = load_prompts(Path(args.prompts), args.cases)
    criteria = load_criteria(Path(args.criteria_file), args.criteria)
    generations = len(prompts) * len(generators) * len(criteria) * 2 * args.replicates
    pairs = len(prompts) * len(generators) * len(criteria) * args.replicates
    orientations = 2 if args.mirror else 1
    judge_calls = pairs * len(judges) * orientations
    return {
        "prompts": len(prompts),
        "generators": generators,
        "judges": judges,
        "criteria": list(criteria),
        "arms": ["objective_only", "selfscore"],
        "generations": generations,
        "matched_pairs": pairs,
        "judge_calls": judge_calls,
        "judge_endpoints_per_call": 2,
        "mirror": bool(args.mirror),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("generate", "judge", "all", "plan"):
        p = sub.add_parser(name)
        add_common(p)
    args = parser.parse_args()
    if args.command == "plan":
        print(json.dumps(plan_dict(args), indent=2))
        return
    exp = Experiment(args)
    if args.command in {"generate", "all"}:
        exp.run_generate()
    if args.command in {"judge", "all"}:
        exp.run_judge()


if __name__ == "__main__":
    main()

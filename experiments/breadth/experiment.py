#!/usr/bin/env python3
"""
Self-scoring breadth replication experiment.

Question:
    Does asking an LLM to score the AI-likeness of its own prose while it writes
    change the AI-sloppiness of the final prose itself?

Two generation conditions only:
    baseline   - explicit anti-AI-slop writing instruction, no self-scoring
    selfscore  - the identical anti-slop instruction plus sentence-level
                 <AI SCORE: n> self-scoring

No rejection, regeneration, branch selection, or score-guided correction occurs.
Scores are stripped before blind pairwise judging.

Judging:
    * complete cleaned outputs only
    * A/B assignment deterministically randomized
    * mirrored A/B and B/A order by default
    * A, B, or TIE allowed
    * same generator model is included as a post-generation self-judge when it
      appears in the judge roster; other models form an external panel

Transport:
    OpenRouter chat/completions, high-parallelism ThreadPoolExecutor, resumable
    SQLite/WAL state, standard-library-only Python.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import math
import os
import random
import re
import sqlite3
import statistics
import threading
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

CODE_VERSION = "breadth-1.2"
SCHEMA_VERSION = "2"
GENERATION_PROTOCOL_VERSION = "matched-antislop-selfscore-v1"
JUDGE_PROTOCOL_VERSION = "blind-slop-pairwise-v1.2-matched-antislop"

COMMON_ANTI_SLOP_INSTRUCTION = (
    "Follow the user's writing task and formatting instructions exactly.\n\n"
    "While writing, actively avoid AI-slop: generic, formulaic, clichéd, overly "
    "polished, promotional, repetitive, or obviously AI-generated phrasing. "
    "Prefer concrete, natural, specific language that sounds like something a "
    "real person would genuinely write."
)

BASELINE_SYSTEM = (
    COMMON_ANTI_SLOP_INSTRUCTION
    + "\n\nProduce only the requested text."
)

# Preserved from the earlier LIVE/REPLAY/POST experiment so this experiment
# changes the treatment contrast, not the meaning of the score instruction.
AI_SCORE_INSTRUCTION = (
    "After every sentence, assess how likely an average human reader would be "
    "to think that sentence was AI-generated. Use an integer from 0 to 100, "
    "where 0 means very human-like and 100 means obviously AI-generated. Put "
    "the sentence's normal closing punctuation first, then immediately append "
    "the assessment as <AI SCORE: n>."
)

SELFSCORE_SYSTEM = (
    COMMON_ANTI_SLOP_INSTRUCTION
    + "\n\n" + AI_SCORE_INSTRUCTION
    + "\n\nProduce only the requested text and the required AI SCORE tags."
)

JUDGE_SYSTEM = (
    "You are a blind pairwise evaluator of writing style. You will receive an "
    "original writing task and two candidate answers. Judge only which complete "
    "answer sounds MORE like stereotypical AI-generated slop. AI slop includes "
    "generic or canned phrasing, formulaic transitions, polished-but-vague "
    "abstractions, repetitive structure, unnecessary framing, forced summaries "
    "or conclusions, marketing-like language, excessive symmetry, and other "
    "stylistic signals that make prose feel machine-generated. Do not try to "
    "guess how either answer was produced. Do not reward or punish an answer "
    "merely for being longer. Factual correctness is not the target except when "
    "it directly manifests as generic/evasive AI-like prose. If neither answer "
    "is meaningfully more AI-sloppy, answer TIE. Return exactly one token: A, B, "
    "or TIE."
)

_SCORE_RE = re.compile(
    r"<\s*AI\s+SCORE\s*:\s*\(?\s*(\d{1,3})\s*\)?\s*>", re.IGNORECASE
)
_SCORE_ANY_TAG_RE = re.compile(
    r"<\s*AI\s+SCORE\s*:\s*[^>\r\n]{0,40}>", re.IGNORECASE
)
_BARE_SCORE_RE = re.compile(
    r"(?<!<)\bAI\s+SCORE\s*:\s*\(?\s*\d{1,3}\s*\)?\b", re.IGNORECASE
)
_SCORE_LEAK_RE = re.compile(r"AI\s+SCORE", re.IGNORECASE)


# Execution-only provider repair.
#
# v1.3 pinned DeepSeek V4.1 Flash to the first-party `deepseek` provider.
# That endpoint returned HTTP 404 in the full run, while prior successful runs
# of the same exact OpenRouter model slug were served by Together.  Keep the
# frozen models_current.json unchanged so an interrupted v1.3 workspace retains
# the same scientific_run_identity and all completed generations are reused.
# The actual provider returned by OpenRouter is stored on every generation and
# judgment row, and this override is written to manifest.json for auditability.
RUNTIME_PROVIDER_OVERRIDES: dict[str, str] = {}


def effective_provider(spec: "ModelSpec") -> str | None:
    return RUNTIME_PROVIDER_OVERRIDES.get(spec.alias, spec.provider)


@dataclass(frozen=True)
class ModelSpec:
    alias: str
    route: str
    provider: str | None = None


@dataclass(frozen=True)
class Prompt:
    prompt_id: str
    domain: str
    task: str


@dataclass(frozen=True)
class ApiResult:
    text: str
    provider: str | None
    latency_s: float
    prompt_tokens: int | None
    completion_tokens: int | None
    reasoning_tokens: int | None
    finish_reason: str | None
    raw_json: Mapping[str, Any]


def stable_hash(*parts: Any, n: int = 24) -> str:
    raw = "|".join(str(x) for x in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:n]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_simple_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_models(path: Path) -> tuple[dict[str, ModelSpec], list[str], list[str]]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    all_specs: dict[str, ModelSpec] = {}

    def parse_list(name: str) -> list[str]:
        out: list[str] = []
        for row in obj.get(name, []):
            if isinstance(row, str):
                alias = row
                if alias not in all_specs:
                    raise ValueError(f"{name} references unknown model alias {alias!r}")
                out.append(alias)
                continue
            alias = str(row["alias"])
            route = str(row["route"])
            provider = row.get("provider")
            spec = ModelSpec(alias=alias, route=route, provider=str(provider) if provider else None)
            old = all_specs.get(alias)
            if old is not None and old != spec:
                raise ValueError(f"conflicting definitions for model alias {alias!r}")
            all_specs[alias] = spec
            out.append(alias)
        return out

    generators = parse_list("generators")
    # judges can be aliases or full objects. If aliases are used, generators
    # have already populated all_specs.
    judges: list[str] = []
    for row in obj.get("judges", []):
        if isinstance(row, str):
            alias = row
            if alias not in all_specs:
                raise ValueError(f"judges references unknown model alias {alias!r}")
            judges.append(alias)
        else:
            alias = str(row["alias"])
            route = str(row["route"])
            provider = row.get("provider")
            spec = ModelSpec(alias=alias, route=route, provider=str(provider) if provider else None)
            old = all_specs.get(alias)
            if old is not None and old != spec:
                raise ValueError(f"conflicting definitions for model alias {alias!r}")
            all_specs[alias] = spec
            judges.append(alias)

    if not generators:
        raise ValueError("models file has no generators")
    if not judges:
        raise ValueError("models file has no judges")
    if len(generators) != len(set(generators)) or len(judges) != len(set(judges)):
        raise ValueError("duplicate generator or judge alias")
    return all_specs, generators, judges


def load_prompts(path: Path, *, cases: int | None, seed: int) -> list[Prompt]:
    rows: list[Prompt] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        obj = json.loads(raw)
        try:
            rows.append(
                Prompt(
                    prompt_id=str(obj["prompt_id"]),
                    domain=str(obj.get("domain", "unknown")),
                    task=str(obj.get("task") or obj["full_task"]),
                )
            )
        except Exception as e:
            raise ValueError(f"bad prompt row at line {line_no}: {e}") from e
    if not rows:
        raise ValueError("prompt file is empty")

    # Domain-balanced deterministic order: useful when --cases is smaller than
    # the full frozen bank. Every round takes one prompt per domain when possible.
    groups: dict[str, list[Prompt]] = defaultdict(list)
    for p in rows:
        groups[p.domain].append(p)
    domains = sorted(groups)
    for d in domains:
        local = random.Random(int(hashlib.sha256(f"{seed}|{d}".encode()).hexdigest()[:16], 16))
        local.shuffle(groups[d])
    rng = random.Random(seed)
    rng.shuffle(domains)
    ordered: list[Prompt] = []
    max_len = max(len(groups[d]) for d in domains)
    for i in range(max_len):
        for d in domains:
            if i < len(groups[d]):
                ordered.append(groups[d][i])
    if cases is not None:
        if cases < 1:
            raise ValueError("--cases must be >= 1")
        ordered = ordered[: min(cases, len(ordered))]
    return ordered


def baseline_messages(task: str) -> list[dict[str, str]]:
    # The user task is byte-for-byte identical across conditions. Only the system
    # instruction differs, and the self-score system prompt is the matched anti-slop
    # instruction plus the score-emission requirement.
    return [
        {"role": "system", "content": BASELINE_SYSTEM},
        {"role": "user", "content": task},
    ]


def selfscore_messages(task: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SELFSCORE_SYSTEM},
        {"role": "user", "content": task},
    ]


def extract_scores(text: str) -> list[int]:
    out = [int(m.group(1)) for m in _SCORE_RE.finditer(text)]
    return [x for x in out if 0 <= x <= 100]


def normalize_visible_text(text: str) -> str:
    # Apply the same conservative whitespace normalization to both conditions.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_score_material(text: str) -> tuple[str, list[int], bool]:
    scores = extract_scores(text)
    cleaned = _SCORE_ANY_TAG_RE.sub("", text)
    cleaned = _BARE_SCORE_RE.sub("", cleaned)
    cleaned = normalize_visible_text(cleaned)
    leak = bool(_SCORE_LEAK_RE.search(cleaned))
    return cleaned, scores, leak


def judge_messages(task: str, answer_a: str, answer_b: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": JUDGE_SYSTEM},
        {
            "role": "user",
            "content": (
                "ORIGINAL WRITING TASK\n"
                "---------------------\n"
                f"{task}\n\n"
                "ANSWER A\n"
                "--------\n"
                f"{answer_a}\n\n"
                "ANSWER B\n"
                "--------\n"
                f"{answer_b}\n\n"
                "Which answer sounds MORE like AI slop? Return exactly A, B, or TIE."
            ),
        },
    ]


def parse_verdict(text: str) -> str:
    """Parse a blind judge verdict without guessing from arbitrary prose.

    We accept the requested one-token output and a few harmless wrappers. A
    truncated ``T`` is deliberately *not* treated as TIE; it is retried.
    """
    raw = text.strip()
    s = raw.upper().strip("`* \t\r\n.:;,-\"'")
    if s in {"A", "B", "TIE"}:
        return s

    first = next((ln.strip() for ln in raw.splitlines() if ln.strip()), "")
    first_u = first.upper().strip("`* \t\r\n.:;,-\"'")
    m = re.match(r"^(?:(?:VERDICT|ANSWER|CHOICE)\s*[:=\-]?\s*)?(TIE|A|B)(?:\b|$)", first_u)
    if m:
        return m.group(1)

    # Some judges explain despite the exact-output instruction and put an
    # unambiguous final verdict on the last non-empty line, often as **A**.
    # Accept only a standalone final verdict; never infer A/B from prose.
    last = next((ln.strip() for ln in reversed(raw.splitlines()) if ln.strip()), "")
    last_u = last.upper().strip("`* \t\r\n.:;,-\"'")
    m = re.fullmatch(r"(?:(?:VERDICT|ANSWER|CHOICE)\s*[:=\-]?\s*)?(TIE|A|B)", last_u)
    if m:
        return m.group(1)
    raise ValueError(f"unparseable judge verdict: {text!r}")


class OpenRouterClient:
    def __init__(self, api_key: str, *, timeout_s: float, retries: int):
        self.api_key = api_key
        self.timeout_s = timeout_s
        self.retries = retries

    def call(
        self,
        *,
        spec: ModelSpec,
        messages: Sequence[Mapping[str, str]],
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
            # OpenRouter normalizes this across reasoning-capable providers.
            # Keep reasoning out of the visible response; it still counts toward
            # max_tokens, hence the deliberately generous judge ceiling.
            payload["reasoning"] = {"effort": reasoning_effort, "exclude": True}
        provider = effective_provider(spec)
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
                    "X-Title": "Inline self-scoring breadth replication",
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
                msg = choices[0].get("message") or {}
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
                    provider=data.get("provider"),
                    latency_s=latency,
                    prompt_tokens=_int_or_none(usage.get("prompt_tokens")),
                    completion_tokens=_int_or_none(usage.get("completion_tokens")),
                    reasoning_tokens=_int_or_none(details.get("reasoning_tokens")),
                    finish_reason=str(choices[0].get("finish_reason")) if choices[0].get("finish_reason") is not None else None,
                    raw_json=data,
                )
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
                    json.JSONDecodeError, RuntimeError) as exc:
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
                time.sleep(delay + random.random() * 0.5)
        assert last_error is not None
        raise last_error


def _int_or_none(x: Any) -> int | None:
    try:
        return int(x) if x is not None else None
    except (TypeError, ValueError):
        return None


class Store:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(str(path), check_same_thread=False, timeout=60)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS generations (
                prompt_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                task TEXT NOT NULL,
                generator TEXT NOT NULL,
                route TEXT NOT NULL,
                condition TEXT NOT NULL,
                replicate INTEGER NOT NULL,
                raw_text TEXT NOT NULL,
                clean_text TEXT NOT NULL,
                scores_json TEXT NOT NULL,
                score_count INTEGER NOT NULL,
                score_leak INTEGER NOT NULL,
                provider TEXT,
                latency_s REAL,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                created_at REAL NOT NULL,
                PRIMARY KEY (prompt_id, generator, condition, replicate)
            );
            CREATE TABLE IF NOT EXISTS attempts (
                stage TEXT NOT NULL,
                job_id TEXT NOT NULL,
                attempt_no INTEGER NOT NULL,
                prompt_id TEXT,
                generator TEXT,
                judge TEXT,
                orientation INTEGER,
                model_alias TEXT NOT NULL,
                route TEXT NOT NULL,
                max_tokens INTEGER NOT NULL,
                reasoning_effort TEXT,
                success INTEGER NOT NULL,
                parse_status TEXT,
                error TEXT,
                raw_text TEXT,
                finish_reason TEXT,
                provider TEXT,
                latency_s REAL,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                reasoning_tokens INTEGER,
                created_at REAL NOT NULL,
                PRIMARY KEY(stage, job_id, attempt_no)
            );
            CREATE TABLE IF NOT EXISTS judgments (
                pair_id TEXT NOT NULL,
                prompt_id TEXT NOT NULL,
                generator TEXT NOT NULL,
                replicate INTEGER NOT NULL,
                judge TEXT NOT NULL,
                judge_route TEXT NOT NULL,
                orientation INTEGER NOT NULL,
                answer_a_source TEXT NOT NULL,
                answer_b_source TEXT NOT NULL,
                raw_verdict TEXT NOT NULL,
                verdict TEXT NOT NULL,
                canonical_outcome TEXT NOT NULL,
                is_self_judge INTEGER NOT NULL,
                provider TEXT,
                latency_s REAL,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                created_at REAL NOT NULL,
                PRIMARY KEY (pair_id, judge, orientation)
            );
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def set_meta(self, key: str, value: Any) -> None:
        blob = json.dumps(value, ensure_ascii=False, sort_keys=True)
        with self.lock:
            self.conn.execute(
                "INSERT INTO meta(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, blob),
            )
            self.conn.commit()

    def get_meta(self, key: str) -> Any | None:
        with self.lock:
            row = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def generation_done(self, prompt_id: str, generator: str, condition: str, replicate: int) -> bool:
        with self.lock:
            row = self.conn.execute(
                "SELECT 1 FROM generations WHERE prompt_id=? AND generator=? AND condition=? AND replicate=?",
                (prompt_id, generator, condition, replicate),
            ).fetchone()
        return row is not None

    def save_generation(self, row: Mapping[str, Any]) -> None:
        cols = [
            "prompt_id", "domain", "task", "generator", "route", "condition", "replicate",
            "raw_text", "clean_text", "scores_json", "score_count", "score_leak", "provider",
            "latency_s", "prompt_tokens", "completion_tokens", "created_at",
        ]
        vals = [row.get(c) for c in cols]
        with self.lock:
            self.conn.execute(
                f"INSERT OR REPLACE INTO generations({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",
                vals,
            )
            self.conn.commit()

    def judgment_done(self, pair_id: str, judge: str, orientation: int) -> bool:
        with self.lock:
            row = self.conn.execute(
                "SELECT 1 FROM judgments WHERE pair_id=? AND judge=? AND orientation=?",
                (pair_id, judge, orientation),
            ).fetchone()
        return row is not None

    def save_judgment(self, row: Mapping[str, Any]) -> None:
        cols = [
            "pair_id", "prompt_id", "generator", "replicate", "judge", "judge_route",
            "orientation", "answer_a_source", "answer_b_source", "raw_verdict", "verdict",
            "canonical_outcome", "is_self_judge", "provider", "latency_s", "prompt_tokens",
            "completion_tokens", "created_at",
        ]
        vals = [row.get(c) for c in cols]
        with self.lock:
            self.conn.execute(
                f"INSERT OR REPLACE INTO judgments({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",
                vals,
            )
            self.conn.commit()

    def save_attempt(self, row: Mapping[str, Any]) -> None:
        cols = [
            "stage", "job_id", "attempt_no", "prompt_id", "generator", "judge",
            "orientation", "model_alias", "route", "max_tokens", "reasoning_effort",
            "success", "parse_status", "error", "raw_text", "finish_reason",
            "provider", "latency_s", "prompt_tokens", "completion_tokens",
            "reasoning_tokens", "created_at",
        ]
        vals = [row.get(c) for c in cols]
        with self.lock:
            self.conn.execute(
                f"INSERT OR REPLACE INTO attempts({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",
                vals,
            )
            self.conn.commit()

    def all_attempts(self) -> list[dict[str, Any]]:
        with self.lock:
            cur = self.conn.execute(
                "SELECT * FROM attempts ORDER BY created_at, stage, job_id, attempt_no"
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def reset_judgments(self) -> None:
        with self.lock:
            self.conn.execute("DELETE FROM judgments")
            self.conn.execute("DELETE FROM attempts WHERE stage='judge'")
            self.conn.commit()

    def generation_pairs(self) -> list[dict[str, Any]]:
        q = """
        SELECT
            b.prompt_id, b.domain, b.task, b.generator, b.replicate,
            b.clean_text AS baseline_text, s.clean_text AS selfscore_text,
            b.provider AS baseline_provider, s.provider AS selfscore_provider,
            s.score_count AS selfscore_count, s.score_leak AS selfscore_leak
        FROM generations b
        JOIN generations s
          ON b.prompt_id=s.prompt_id AND b.generator=s.generator AND b.replicate=s.replicate
        WHERE b.condition='baseline' AND s.condition='selfscore'
        ORDER BY b.generator, b.prompt_id, b.replicate
        """
        with self.lock:
            cur = self.conn.execute(q)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def all_generations(self) -> list[dict[str, Any]]:
        with self.lock:
            cur = self.conn.execute("SELECT * FROM generations ORDER BY generator,prompt_id,condition,replicate")
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def all_judgments(self) -> list[dict[str, Any]]:
        with self.lock:
            cur = self.conn.execute("SELECT * FROM judgments ORDER BY generator,prompt_id,replicate,judge,orientation")
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def counts(self) -> dict[str, int]:
        with self.lock:
            g = self.conn.execute("SELECT COUNT(*) FROM generations").fetchone()[0]
            j = self.conn.execute("SELECT COUNT(*) FROM judgments").fetchone()[0]
            a = self.conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
        return {"generations": int(g), "judgments": int(j), "attempts": int(a)}


class Runner:
    def __init__(
        self,
        *,
        store: Store,
        client: OpenRouterClient,
        specs: Mapping[str, ModelSpec],
        generators: Sequence[str],
        judges: Sequence[str],
        prompts: Sequence[Prompt],
        seed: int,
        replicates: int,
        workers: int,
        per_model_workers: int,
        generation_temperature: float,
        judge_temperature: float,
        generation_max_tokens: int,
        generation_retry_max_tokens: int,
        judge_max_tokens: int,
        judge_retry_max_tokens: int,
        judge_reasoning_effort: str,
        mirror: bool,
    ):
        self.store = store
        self.client = client
        self.specs = specs
        self.generators = list(generators)
        self.judges = list(judges)
        self.prompts = list(prompts)
        self.seed = seed
        self.replicates = replicates
        self.workers = workers
        self.per_model_workers = per_model_workers
        self.generation_temperature = generation_temperature
        self.judge_temperature = judge_temperature
        self.generation_max_tokens = generation_max_tokens
        self.generation_retry_max_tokens = generation_retry_max_tokens
        self.judge_max_tokens = judge_max_tokens
        self.judge_retry_max_tokens = judge_retry_max_tokens
        self.judge_reasoning_effort = judge_reasoning_effort
        self.mirror = mirror
        self.model_sems = {
            alias: threading.BoundedSemaphore(per_model_workers) for alias in specs
        }
        self.progress_lock = threading.Lock()

    def _call(
        self, alias: str, messages: Sequence[Mapping[str, str]], *,
        temperature: float, max_tokens: int, reasoning_effort: str | None = None,
    ) -> ApiResult:
        with self.model_sems[alias]:
            return self.client.call(
                spec=self.specs[alias], messages=messages,
                temperature=temperature, max_tokens=max_tokens,
                reasoning_effort=reasoning_effort,
            )

    def run_generate(self) -> None:
        jobs: list[tuple[Prompt, str, str, int]] = []
        for p in self.prompts:
            for gen in self.generators:
                for rep in range(self.replicates):
                    for condition in ("baseline", "selfscore"):
                        if not self.store.generation_done(p.prompt_id, gen, condition, rep):
                            jobs.append((p, gen, condition, rep))
        random.Random(self.seed + 101).shuffle(jobs)
        print(f"generation pending: {len(jobs)}", flush=True)
        if not jobs:
            return
        done = 0

        def one(job: tuple[Prompt, str, str, int]) -> None:
            nonlocal done
            p, gen, condition, rep = job
            messages = baseline_messages(p.task) if condition == "baseline" else selfscore_messages(p.task)
            job_id = stable_hash(p.prompt_id, gen, condition, rep, "generation")
            budgets = (self.generation_max_tokens, self.generation_retry_max_tokens)
            last_error: Exception | None = None
            accepted: ApiResult | None = None
            for attempt_no, budget in enumerate(budgets, start=1):
                result: ApiResult | None = None
                success = False
                parse_status = "api_error"
                err_text: str | None = None
                try:
                    result = self._call(
                        gen, messages,
                        temperature=self.generation_temperature,
                        max_tokens=budget,
                    )
                    if not result.text.strip():
                        parse_status = "empty_visible"
                        raise RuntimeError(
                            "model returned empty visible content "
                            f"(finish_reason={result.finish_reason!r}, completion_tokens={result.completion_tokens}, "
                            f"reasoning_tokens={result.reasoning_tokens})"
                        )
                    if str(result.finish_reason or "").lower() == "length":
                        parse_status = "truncated_length"
                        raise RuntimeError(
                            "generation hit output ceiling "
                            f"(max_tokens={budget}, completion_tokens={result.completion_tokens}, "
                            f"reasoning_tokens={result.reasoning_tokens})"
                        )
                    accepted = result
                    success = True
                    parse_status = "complete"
                except Exception as e:
                    last_error = e
                    err_text = str(e)
                finally:
                    self.store.save_attempt({
                        "stage": "generation", "job_id": job_id, "attempt_no": attempt_no,
                        "prompt_id": p.prompt_id, "generator": gen, "judge": None,
                        "orientation": None, "model_alias": gen, "route": self.specs[gen].route,
                        "max_tokens": budget, "reasoning_effort": None,
                        "success": int(success), "parse_status": parse_status,
                        "error": err_text, "raw_text": result.text if result else None,
                        "finish_reason": result.finish_reason if result else None,
                        "provider": result.provider if result else None,
                        "latency_s": result.latency_s if result else None,
                        "prompt_tokens": result.prompt_tokens if result else None,
                        "completion_tokens": result.completion_tokens if result else None,
                        "reasoning_tokens": result.reasoning_tokens if result else None,
                        "created_at": time.time(),
                    })
                if accepted is not None:
                    break
            if accepted is None:
                assert last_error is not None
                raise last_error

            clean, scores, leak = strip_score_material(accepted.text)
            self.store.save_generation({
                "prompt_id": p.prompt_id,
                "domain": p.domain,
                "task": p.task,
                "generator": gen,
                "route": self.specs[gen].route,
                "condition": condition,
                "replicate": rep,
                "raw_text": accepted.text,
                "clean_text": clean,
                "scores_json": json.dumps(scores),
                "score_count": len(scores),
                "score_leak": int(leak),
                "provider": accepted.provider,
                "latency_s": accepted.latency_s,
                "prompt_tokens": accepted.prompt_tokens,
                "completion_tokens": accepted.completion_tokens,
                "created_at": time.time(),
            })
            with self.progress_lock:
                done += 1
                if done % 10 == 0 or done == len(jobs):
                    print(f"generation {done}/{len(jobs)}", flush=True)

        errors = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as ex:
            futs = {ex.submit(one, j): j for j in jobs}
            for fut in concurrent.futures.as_completed(futs):
                try:
                    fut.result()
                except Exception as e:
                    errors += 1
                    p, gen, condition, rep = futs[fut]
                    print(f"GEN ERROR {gen} {p.prompt_id} {condition} rep={rep}: {e}", file=os.sys.stderr, flush=True)
        if errors:
            print(f"generation completed with {errors} failed jobs; rerun to retry", flush=True)

    def _base_orientation(self, pair_id: str, judge: str) -> bool:
        # True => baseline is A on orientation 0; False => selfscore is A.
        h = hashlib.sha256(f"{self.seed}|{pair_id}|{judge}|blind".encode()).digest()
        return bool(h[0] & 1)

    def run_judge(self) -> None:
        pairs = self.store.generation_pairs()
        jobs: list[tuple[dict[str, Any], str, int]] = []
        orientations = (0, 1) if self.mirror else (0,)
        for pair in pairs:
            # A leak after stripping could reveal the treatment. Keep the data but
            # do not send such a pair to a blind judge.
            if int(pair["selfscore_leak"]):
                print(f"SKIP leaked score marker: {pair['generator']} {pair['prompt_id']} rep={pair['replicate']}", flush=True)
                continue
            pair_id = stable_hash(pair["prompt_id"], pair["generator"], pair["replicate"], "pair")
            pair["pair_id"] = pair_id
            for judge in self.judges:
                for orientation in orientations:
                    if not self.store.judgment_done(pair_id, judge, orientation):
                        jobs.append((pair, judge, orientation))
        random.Random(self.seed + 202).shuffle(jobs)
        print(f"judgment pending: {len(jobs)}", flush=True)
        if not jobs:
            return
        done = 0

        def one(job: tuple[dict[str, Any], str, int]) -> None:
            nonlocal done
            pair, judge, orientation = job
            baseline_is_a0 = self._base_orientation(pair["pair_id"], judge)
            baseline_is_a = baseline_is_a0 if orientation == 0 else not baseline_is_a0
            if baseline_is_a:
                a_source, b_source = "baseline", "selfscore"
                answer_a, answer_b = pair["baseline_text"], pair["selfscore_text"]
            else:
                a_source, b_source = "selfscore", "baseline"
                answer_a, answer_b = pair["selfscore_text"], pair["baseline_text"]

            messages = judge_messages(pair["task"], answer_a, answer_b)
            last_error: Exception | None = None
            result: ApiResult | None = None
            verdict: str | None = None
            job_id = stable_hash(pair["pair_id"], judge, orientation, "judge")
            budgets = (self.judge_max_tokens, self.judge_retry_max_tokens)
            for attempt_no, budget in enumerate(budgets, start=1):
                result = None
                parse_status = "api_error"
                err_text: str | None = None
                try:
                    result = self._call(
                        judge, messages,
                        temperature=self.judge_temperature,
                        max_tokens=budget,
                        reasoning_effort=self.judge_reasoning_effort,
                    )
                    if not result.text.strip():
                        parse_status = "empty_visible"
                        raise RuntimeError(
                            "model returned empty visible content "
                            f"(finish_reason={result.finish_reason!r}, completion_tokens={result.completion_tokens}, "
                            f"reasoning_tokens={result.reasoning_tokens})"
                        )
                    verdict = parse_verdict(result.text)
                    parse_status = "parsed"
                except Exception as e:
                    last_error = e
                    err_text = str(e)
                    if result is not None and result.text.strip():
                        parse_status = "unparseable"
                finally:
                    self.store.save_attempt({
                        "stage": "judge", "job_id": job_id, "attempt_no": attempt_no,
                        "prompt_id": pair["prompt_id"], "generator": pair["generator"],
                        "judge": judge, "orientation": orientation, "model_alias": judge,
                        "route": self.specs[judge].route, "max_tokens": budget,
                        "reasoning_effort": self.judge_reasoning_effort,
                        "success": int(verdict is not None), "parse_status": parse_status,
                        "error": err_text, "raw_text": result.text if result else None,
                        "finish_reason": result.finish_reason if result else None,
                        "provider": result.provider if result else None,
                        "latency_s": result.latency_s if result else None,
                        "prompt_tokens": result.prompt_tokens if result else None,
                        "completion_tokens": result.completion_tokens if result else None,
                        "reasoning_tokens": result.reasoning_tokens if result else None,
                        "created_at": time.time(),
                    })
                if verdict is not None:
                    break
            if result is None or verdict is None:
                assert last_error is not None
                raise last_error

            if verdict == "TIE":
                canonical = "tie"
            elif verdict == "A":
                canonical = f"{a_source}_more_slop"
            else:
                canonical = f"{b_source}_more_slop"

            self.store.save_judgment({
                "pair_id": pair["pair_id"],
                "prompt_id": pair["prompt_id"],
                "generator": pair["generator"],
                "replicate": pair["replicate"],
                "judge": judge,
                "judge_route": self.specs[judge].route,
                "orientation": orientation,
                "answer_a_source": a_source,
                "answer_b_source": b_source,
                "raw_verdict": result.text,
                "verdict": verdict,
                "canonical_outcome": canonical,
                "is_self_judge": int(judge == pair["generator"]),
                "provider": result.provider,
                "latency_s": result.latency_s,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "created_at": time.time(),
            })
            with self.progress_lock:
                done += 1
                if done % 25 == 0 or done == len(jobs):
                    print(f"judgment {done}/{len(jobs)}", flush=True)

        errors = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as ex:
            futs = {ex.submit(one, j): j for j in jobs}
            for fut in concurrent.futures.as_completed(futs):
                try:
                    fut.result()
                except Exception as e:
                    errors += 1
                    pair, judge, orientation = futs[fut]
                    print(
                        f"JUDGE ERROR {judge} {pair['generator']} {pair['prompt_id']} "
                        f"rep={pair['replicate']} orient={orientation}: {e}",
                        file=os.sys.stderr, flush=True,
                    )
        if errors:
            print(f"judging completed with {errors} failed jobs; rerun to retry", flush=True)


def resolve_mirrored(rows: Sequence[Mapping[str, Any]], mirror: bool) -> str | None:
    if not rows:
        return None
    by_o = {int(r["orientation"]): str(r["canonical_outcome"]) for r in rows}
    if not mirror:
        return by_o.get(0)
    if 0 not in by_o or 1 not in by_o:
        return None
    a, b = by_o[0], by_o[1]
    if a == b:
        return a
    return "order_sensitive"


def wilson_interval(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n <= 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return max(0.0, center - half), min(1.0, center + half)


def exact_sign_p_two_sided(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return float("nan")
    m = min(wins, losses)
    tail = sum(math.comb(n, k) for k in range(0, m + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def summarize_outcomes(outcomes: Sequence[str]) -> dict[str, Any]:
    c = Counter(outcomes)
    # baseline_more_slop == self-scored answer is cleaner.
    sc_clean = c["baseline_more_slop"]
    base_clean = c["selfscore_more_slop"]
    ties = c["tie"]
    order = c["order_sensitive"]
    decisive = sc_clean + base_clean
    lo, hi = wilson_interval(sc_clean, decisive)
    n = len(outcomes)
    return {
        "n": n,
        "selfscore_cleaner": sc_clean,
        "baseline_cleaner": base_clean,
        "tie": ties,
        "order_sensitive": order,
        "decisive_n": decisive,
        "selfscore_cleaner_decisive_rate": sc_clean / decisive if decisive else None,
        "selfscore_cleaner_ci95_low": lo if decisive else None,
        "selfscore_cleaner_ci95_high": hi if decisive else None,
        "exact_sign_p": exact_sign_p_two_sided(sc_clean, base_clean) if decisive else None,
        "net_selfscore_advantage": (sc_clean - base_clean) / n if n else None,
    }


def panel_outcome(judge_outcomes: Sequence[str]) -> str | None:
    valid = [x for x in judge_outcomes if x in {"baseline_more_slop", "selfscore_more_slop", "tie"}]
    if not valid:
        return None
    c = Counter(valid)
    if c["baseline_more_slop"] > c["selfscore_more_slop"]:
        return "baseline_more_slop"
    if c["selfscore_more_slop"] > c["baseline_more_slop"]:
        return "selfscore_more_slop"
    return "tie"


def analyze(store: Store, *, out_dir: Path, mirror: bool, judges: Sequence[str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    generations = store.all_generations()
    judgments = store.all_judgments()

    # Raw exports.
    _write_csv(out_dir / "generations.csv", generations)
    _write_csv(out_dir / "judgments_raw.csv", judgments)

    # Resolve mirrored order at generator/prompt/replicate/judge level.
    grouped: dict[tuple[str, str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for r in judgments:
        grouped[(r["generator"], r["prompt_id"], int(r["replicate"]), r["judge"])].append(r)

    resolved_rows: list[dict[str, Any]] = []
    for key, rows in grouped.items():
        generator, prompt_id, rep, judge = key
        outcome = resolve_mirrored(rows, mirror)
        if outcome is None:
            continue
        resolved_rows.append({
            "generator": generator,
            "prompt_id": prompt_id,
            "replicate": rep,
            "judge": judge,
            "is_self_judge": int(generator == judge),
            "outcome": outcome,
        })
    _write_csv(out_dir / "judgments_resolved.csv", resolved_rows)

    summary_rows: list[dict[str, Any]] = []

    generators = sorted({r["generator"] for r in resolved_rows})
    for gen in generators:
        # Self-judge for this generator.
        self_out = [r["outcome"] for r in resolved_rows if r["generator"] == gen and r["judge"] == gen]
        if self_out:
            summary_rows.append({"level": "self_judge", "generator": gen, "judge": gen, **summarize_outcomes(self_out)})

        # Each external judge separately.
        for judge in sorted(set(judges) - {gen}):
            outs = [r["outcome"] for r in resolved_rows if r["generator"] == gen and r["judge"] == judge]
            if outs:
                summary_rows.append({"level": "external_judge", "generator": gen, "judge": judge, **summarize_outcomes(outs)})

        # External panel majority per prompt/replicate, excluding generator itself
        # and excluding each judge's order-sensitive result from the vote.
        per_pair: dict[tuple[str, int], list[str]] = defaultdict(list)
        for r in resolved_rows:
            if r["generator"] != gen or r["judge"] == gen:
                continue
            if r["outcome"] == "order_sensitive":
                continue
            per_pair[(r["prompt_id"], int(r["replicate"]))].append(r["outcome"])
        pouts = [x for xs in per_pair.values() if (x := panel_outcome(xs)) is not None]
        if pouts:
            summary_rows.append({"level": "external_panel", "generator": gen, "judge": "PANEL", **summarize_outcomes(pouts)})

    # Overall external-panel result across generators.
    overall_panel: list[str] = []
    for gen in generators:
        per_pair: dict[tuple[str, int], list[str]] = defaultdict(list)
        for r in resolved_rows:
            if r["generator"] != gen or r["judge"] == gen or r["outcome"] == "order_sensitive":
                continue
            per_pair[(r["prompt_id"], int(r["replicate"]))].append(r["outcome"])
        overall_panel.extend(x for xs in per_pair.values() if (x := panel_outcome(xs)) is not None)
    if overall_panel:
        summary_rows.append({"level": "external_panel_overall", "generator": "ALL", "judge": "PANEL", **summarize_outcomes(overall_panel)})

    _write_csv(out_dir / "summary.csv", summary_rows)

    # Manipulation check: selfscore condition emitted valid score tags.
    ss = [r for r in generations if r["condition"] == "selfscore"]
    compliance: list[dict[str, Any]] = []
    for gen in sorted({r["generator"] for r in ss}):
        rows = [r for r in ss if r["generator"] == gen]
        counts = [int(r["score_count"]) for r in rows]
        compliance.append({
            "generator": gen,
            "n": len(rows),
            "with_any_score": sum(x > 0 for x in counts),
            "with_5plus_scores": sum(x >= 5 for x in counts),
            "mean_score_tags": statistics.mean(counts) if counts else None,
            "score_leak_after_strip": sum(int(r["score_leak"]) for r in rows),
        })
    _write_csv(out_dir / "selfscore_compliance.csv", compliance)

    # Provider-match audit for the paired generation conditions.
    pairs = store.generation_pairs()
    provider_rows = []
    for gen in sorted({p["generator"] for p in pairs}):
        rows = [p for p in pairs if p["generator"] == gen]
        matched = sum(
            bool(p["baseline_provider"])
            and bool(p["selfscore_provider"])
            and p["baseline_provider"] == p["selfscore_provider"]
            for p in rows
        )
        unknown = sum(not p["baseline_provider"] or not p["selfscore_provider"] for p in rows)
        provider_rows.append({
            "generator": gen, "pairs": len(rows), "same_provider": matched,
            "unknown_provider": unknown,
            "same_provider_rate": matched / len(rows) if rows else None,
        })
    _write_csv(out_dir / "provider_match.csv", provider_rows)

    lines = [
        "# Self-scoring effect on AI-slop style",
        "",
        "Interpretation: `selfscore_cleaner` means the judge said the BASELINE answer was more AI-sloppy;",
        "`baseline_cleaner` means the judge said the SELF-SCORED answer was more AI-sloppy.",
        "Mirrored disagreements are recorded as `order_sensitive`, not forced into either condition.",
        "",
        "## Primary summaries",
        "",
    ]
    for r in summary_rows:
        rate = r.get("selfscore_cleaner_decisive_rate")
        ci_lo = r.get("selfscore_cleaner_ci95_low")
        ci_hi = r.get("selfscore_cleaner_ci95_high")
        p = r.get("exact_sign_p")
        rate_s = "NA" if rate is None else f"{100*rate:.1f}%"
        ci_s = "NA" if ci_lo is None else f"[{100*ci_lo:.1f}%, {100*ci_hi:.1f}%]"
        p_s = "NA" if p is None else f"{p:.4g}"
        lines.append(
            f"- **{r['level']} / generator={r['generator']} / judge={r['judge']}**: "
            f"selfscore cleaner {r['selfscore_cleaner']}, baseline cleaner {r['baseline_cleaner']}, "
            f"tie {r['tie']}, order-sensitive {r['order_sensitive']}; decisive selfscore-cleaner "
            f"rate {rate_s} 95% CI {ci_s}, exact sign-test p={p_s}."
        )
    lines += ["", "## Self-score manipulation check", ""]
    for r in compliance:
        lines.append(
            f"- **{r['generator']}**: {r['with_any_score']}/{r['n']} emitted at least one valid score tag; "
            f"{r['with_5plus_scores']}/{r['n']} emitted at least five; mean tags={r['mean_score_tags']:.2f}; "
            f"post-strip leaks={r['score_leak_after_strip']}."
        )
    lines += ["", "## Generation provider match", ""]
    for r in provider_rows:
        lines.append(
            f"- **{r['generator']}**: {r['same_provider']}/{r['pairs']} baseline/selfscore pairs used the same reported upstream provider "
            f"({100*r['same_provider_rate']:.1f}%); unknown provider on {r['unknown_provider']} pair(s)."
        )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines), flush=True)


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for k in row:
            if k not in seen:
                seen.add(k)
                fields.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def export_debug(store: Store, *, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = store.all_attempts()
    path = out_dir / "debug_attempts.csv"
    _write_csv(path, rows)
    failures = [r for r in rows if not int(r.get("success") or 0)]
    print(f"wrote {path} ({len(rows)} attempts; {len(failures)} failed attempts)", flush=True)
    if failures:
        by_reason = Counter((r.get("parse_status"), r.get("finish_reason")) for r in failures)
        print("failure summary:", flush=True)
        for key, n in sorted(by_reason.items(), key=lambda x: (-x[1], str(x[0]))):
            print(f"  {key}: {n}", flush=True)
    return path


def write_manifest(out: Path, args: argparse.Namespace, models_path: Path, prompts_path: Path,
                   generators: Sequence[str], judges: Sequence[str]) -> None:
    manifest = {
        "code_version": CODE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "seed": args.seed,
        "cases": args.cases,
        "replicates": args.replicates,
        "generation_temperature": args.generation_temperature,
        "judge_temperature": args.judge_temperature,
        "generation_max_tokens": args.generation_max_tokens,
        "generation_retry_max_tokens": args.generation_retry_max_tokens,
        "generation_protocol_version": GENERATION_PROTOCOL_VERSION,
        "judge_max_tokens": args.judge_max_tokens,
        "judge_retry_max_tokens": args.judge_retry_max_tokens,
        "judge_reasoning_effort": args.judge_reasoning_effort,
        "judge_protocol_version": JUDGE_PROTOCOL_VERSION,
        "mirror": args.mirror,
        "generators": list(generators),
        "judges": list(judges),
        "models_file": str(models_path),
        "models_sha256": sha256_file(models_path),
        "runtime_provider_overrides": dict(RUNTIME_PROVIDER_OVERRIDES),
        "prompts_file": str(prompts_path),
        "prompts_sha256": sha256_file(prompts_path),
        "common_anti_slop_instruction": COMMON_ANTI_SLOP_INSTRUCTION,
        "baseline_system": BASELINE_SYSTEM,
        "selfscore_system": SELFSCORE_SYSTEM,
        "ai_score_instruction": AI_SCORE_INSTRUCTION,
        "judge_system": JUDGE_SYSTEM,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def scientific_run_identity(args: argparse.Namespace, models_path: Path, prompts_path: Path,
                            generators: Sequence[str], judges: Sequence[str]) -> str:
    payload = {
        "generation_protocol_version": GENERATION_PROTOCOL_VERSION,
        "judge_protocol_version": JUDGE_PROTOCOL_VERSION,
        "baseline_system": BASELINE_SYSTEM,
        "selfscore_system": SELFSCORE_SYSTEM,
        "judge_system": JUDGE_SYSTEM,
        "models_sha256": sha256_file(models_path),
        "prompts_sha256": sha256_file(prompts_path),
        "generators": list(generators),
        "judges": list(judges),
        "seed": args.seed,
        "cases": args.cases,
        "replicates": args.replicates,
        "generation_temperature": args.generation_temperature,
        "generation_max_tokens": args.generation_max_tokens,
        "generation_retry_max_tokens": args.generation_retry_max_tokens,
        "judge_temperature": args.judge_temperature,
        "judge_max_tokens": args.judge_max_tokens,
        "judge_retry_max_tokens": args.judge_retry_max_tokens,
        "judge_reasoning_effort": args.judge_reasoning_effort,
        "mirror": args.mirror,
    }
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def assert_run_identity(store: Store, identity: str) -> None:
    existing = store.get_meta("scientific_run_identity")
    if existing is None:
        store.set_meta("scientific_run_identity", identity)
        return
    if existing != identity:
        raise RuntimeError(
            "This workspace was created under a different scientific protocol or configuration. "
            "Use a fresh --out directory; do not mix generations/judgments across protocols. "
            f"existing={existing} requested={identity}"
        )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["all", "generate", "judge", "analyze", "status", "debug", "reset-judgments"])
    p.add_argument("--out", type=Path, default=Path("runs/default"))
    p.add_argument("--models", type=Path, default=Path("models_current.json"))
    p.add_argument("--prompts", type=Path, default=Path("prompts.jsonl"))
    p.add_argument("--cases", type=int, default=None, help="balanced subset; default all prompts")
    p.add_argument("--replicates", type=int, default=1)
    p.add_argument("--seed", type=int, default=20261001)
    p.add_argument("--workers", type=int, default=64)
    p.add_argument("--per-model-workers", type=int, default=12)
    p.add_argument("--generation-temperature", type=float, default=0.7)
    p.add_argument("--judge-temperature", type=float, default=0.0)
    p.add_argument("--generation-max-tokens", type=int, default=8192)
    p.add_argument("--generation-retry-max-tokens", type=int, default=16384)
    p.add_argument("--judge-max-tokens", type=int, default=1024)
    p.add_argument("--judge-retry-max-tokens", type=int, default=4096)
    p.add_argument(
        "--judge-reasoning-effort", choices=["none", "minimal", "low", "medium", "high"],
        default="low",
        help="OpenRouter-normalized reasoning effort for blind judging only",
    )
    p.add_argument("--timeout", type=float, default=240.0)
    p.add_argument("--retries", type=int, default=5)
    p.add_argument("--mirror", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--dry-run", action="store_true")
    return p


def main() -> int:
    args = build_parser().parse_args()
    if args.replicates < 1:
        raise SystemExit("--replicates must be >= 1")
    if args.workers < 1 or args.per_model_workers < 1:
        raise SystemExit("worker counts must be >= 1")

    # Resolve config relative to script directory when run from elsewhere.
    script_dir = Path(__file__).resolve().parent
    models_path = args.models if args.models.is_absolute() or args.models.exists() else script_dir / args.models
    prompts_path = args.prompts if args.prompts.is_absolute() or args.prompts.exists() else script_dir / args.prompts
    specs, generators, judges = load_models(models_path)
    prompts = load_prompts(prompts_path, cases=args.cases, seed=args.seed)

    args.out.mkdir(parents=True, exist_ok=True)
    write_manifest(args.out, args, models_path, prompts_path, generators, judges)

    total_generation = len(prompts) * len(generators) * args.replicates * 2
    total_pairs = len(prompts) * len(generators) * args.replicates
    orientations = 2 if args.mirror else 1
    total_judgments = total_pairs * len(judges) * orientations
    print(f"prompts={len(prompts)} generators={len(generators)} judges={len(judges)} replicates={args.replicates}")
    print(f"planned generation calls={total_generation}; planned judgment calls={total_judgments}")
    print(f"mirror={args.mirror}; workers={args.workers}; per-model-workers={args.per_model_workers}")

    if args.dry_run:
        print("DRY RUN: no API calls and no database created")
        return 0

    load_simple_dotenv(Path.cwd() / ".env")
    load_simple_dotenv(script_dir / ".env")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if args.command in {"all", "generate", "judge"} and not api_key:
        raise SystemExit("OPENROUTER_API_KEY is not set; export it or put it in .env")

    store = Store(args.out / "experiment.sqlite3")
    try:
        identity = scientific_run_identity(args, models_path, prompts_path, generators, judges)
        assert_run_identity(store, identity)
        store.set_meta("manifest_sha256", sha256_file(args.out / "manifest.json"))
        store.set_meta("code_version", CODE_VERSION)
        if args.command == "reset-judgments":
            before = store.counts()
            store.reset_judgments()
            after = store.counts()
            print(f"reset judgments only: {before} -> {after}; generations preserved", flush=True)
            return 0
        if args.command == "debug":
            export_debug(store, out_dir=args.out / "results")
            return 0
        if args.command == "status":
            print(json.dumps(store.counts(), indent=2))
            return 0
        if args.command == "analyze":
            analyze(store, out_dir=args.out / "results", mirror=args.mirror, judges=judges)
            return 0

        assert api_key is not None
        runner = Runner(
            store=store,
            client=OpenRouterClient(api_key, timeout_s=args.timeout, retries=args.retries),
            specs=specs,
            generators=generators,
            judges=judges,
            prompts=prompts,
            seed=args.seed,
            replicates=args.replicates,
            workers=args.workers,
            per_model_workers=args.per_model_workers,
            generation_temperature=args.generation_temperature,
            judge_temperature=args.judge_temperature,
            generation_max_tokens=args.generation_max_tokens,
            generation_retry_max_tokens=args.generation_retry_max_tokens,
            judge_max_tokens=args.judge_max_tokens,
            judge_retry_max_tokens=args.judge_retry_max_tokens,
            judge_reasoning_effort=args.judge_reasoning_effort,
            mirror=args.mirror,
        )
        if args.command in {"all", "generate"}:
            runner.run_generate()
        if args.command in {"all", "judge"}:
            runner.run_judge()
        if args.command == "all":
            analyze(store, out_dir=args.out / "results", mirror=args.mirror, judges=judges)
        return 0
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())

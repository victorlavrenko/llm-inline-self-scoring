#!/usr/bin/env python3
"""Tiny live preflight for the exact model/provider routes used by the experiment."""
from __future__ import annotations
import os
from pathlib import Path
import experiment as exp

ROOT = Path(__file__).resolve().parent
exp.load_simple_dotenv(Path.cwd() / ".env")
exp.load_simple_dotenv(ROOT / ".env")
key = os.getenv("OPENROUTER_API_KEY")
if not key:
    raise SystemExit("OPENROUTER_API_KEY is not set")

specs, generators, judges = exp.load_models(ROOT / "models_current.json")
client = exp.OpenRouterClient(key, timeout_s=120.0, retries=2)
failed = []
for alias in generators:
    spec = specs[alias]
    provider = exp.effective_provider(spec)
    try:
        r = client.call(
            spec=spec,
            messages=[{"role":"user","content":"Reply with exactly OK."}],
            temperature=0.0,
            max_tokens=512,
            reasoning_effort="low",
        )
        print(f"OK  {alias:28s} model={spec.route} requested_provider={provider} returned_provider={r.provider} text={r.text[:80]!r}")
    except Exception as e:
        failed.append((alias, str(e)))
        print(f"FAIL {alias:28s} model={spec.route} requested_provider={provider}: {e}")
if failed:
    raise SystemExit(f"preflight failed for {len(failed)} route(s)")

#!/usr/bin/env python3
"""Resolve and freeze one working OpenRouter provider per breadth-model route.

First run: tries the predeclared provider candidates in order. A candidate is
accepted only if both a baseline and a self-scored miniature generation succeed,
and the self-scored response contains a valid <AI SCORE: n> tag.

Later runs: if models_resolved.json already exists, verify those exact pins rather
than silently changing providers. Use --force-resolve only before starting a new
scientific run if you intentionally want to choose new providers.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import experiment as exp

ROOT = Path(__file__).resolve().parent
CANDIDATES = ROOT / "models_candidates.json"
RESOLVED = ROOT / "models_resolved.json"
REPORT = ROOT / "route_preflight.json"

TASK = (
    "Write exactly two natural, non-formulaic sentences for a general audience "
    "explaining why a rainbow can appear after rain."
)


def load_key() -> str:
    exp.load_simple_dotenv(Path.cwd() / ".env")
    exp.load_simple_dotenv(ROOT / ".env")
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is not set")
    return key


def discover_provider_slugs(api_key: str, route: str) -> list[str]:
    """Return current OpenRouter provider tags for a model, best-effort.

    Static provider candidates remain first because they encode routes that worked
    in earlier packages. Live endpoint discovery is appended so provider churn or
    a transiently unavailable historical pin does not make the preflight brittle.
    Any selected provider is still tested and then frozen with fallbacks disabled.
    """
    try:
        author, slug = route.split("/", 1)
    except ValueError:
        return []
    url = (
        "https://openrouter.ai/api/v1/models/"
        + urllib.parse.quote(author, safe="")
        + "/"
        + urllib.parse.quote(slug, safe=":")
        + "/endpoints"
    )
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/victorlavrenko",
            "X-Title": "Inline self-scoring breadth replication",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            obj = json.loads(r.read().decode("utf-8"))
    except Exception:
        return []
    eps = ((obj or {}).get("data") or {}).get("endpoints") or []
    out: list[str] = []
    for ep in eps:
        if not isinstance(ep, dict):
            continue
        tag = ep.get("tag") or ep.get("provider_slug")
        if isinstance(tag, str) and tag and tag not in out:
            out.append(tag)
    return out


def provider_candidates(api_key: str, row: dict) -> list[str]:
    out: list[str] = []
    for provider in list(row.get("provider_candidates") or []) + discover_provider_slugs(api_key, row["route"]):
        if provider and provider not in out:
            out.append(provider)
    return out


def call_pair(client: exp.OpenRouterClient, alias: str, route: str, provider: str) -> dict:
    spec = exp.ModelSpec(alias=alias, route=route, provider=provider)
    row = {"alias": alias, "route": route, "provider_pin": provider}
    b = client.call(
        spec=spec,
        messages=exp.baseline_messages(TASK),
        temperature=0.2,
        max_tokens=8192,
        reasoning_effort=None,
    )
    if not b.text.strip():
        raise RuntimeError("baseline returned empty visible text")
    s = client.call(
        spec=spec,
        messages=exp.selfscore_messages(TASK),
        temperature=0.2,
        max_tokens=8192,
        reasoning_effort=None,
    )
    clean, scores, leak = exp.strip_score_material(s.text)
    if not clean.strip():
        raise RuntimeError("selfscore returned empty text after stripping scores")
    if not scores:
        raise RuntimeError("selfscore emitted no valid <AI SCORE: n> tags")
    row.update({
        "baseline_returned_provider": b.provider,
        "selfscore_returned_provider": s.provider,
        "selfscore_score_count": len(scores),
        "selfscore_score_leak_after_strip": bool(leak),
        "baseline_finish_reason": b.finish_reason,
        "selfscore_finish_reason": s.finish_reason,
    })
    return row


def verify_one(client: exp.OpenRouterClient, spec: dict, *, judge: bool = False) -> dict:
    m = exp.ModelSpec(alias=spec["alias"], route=spec["route"], provider=spec.get("provider"))
    if judge:
        r = client.call(
            spec=m,
            messages=[{"role": "user", "content": "Reply with exactly OK."}],
            temperature=0.0,
            max_tokens=1024,
            reasoning_effort="low",
        )
        if "OK" not in r.text.upper():
            raise RuntimeError(f"unexpected judge preflight output: {r.text[:120]!r}")
        return {
            "alias": m.alias,
            "route": m.route,
            "provider_pin": m.provider,
            "returned_provider": r.provider,
            "kind": "judge",
        }
    row = call_pair(client, m.alias, m.route, str(m.provider))
    row["kind"] = "generator"
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force-resolve", action="store_true",
                    help="ignore/delete existing models_resolved.json and choose providers again")
    args = ap.parse_args()

    key = load_key()
    client = exp.OpenRouterClient(key, timeout_s=180.0, retries=2)

    if RESOLVED.exists() and not args.force_resolve:
        obj = json.loads(RESOLVED.read_text(encoding="utf-8"))
        report = {"mode": "verify_existing", "time": time.time(), "checks": []}
        failures = []
        print("models_resolved.json exists: verifying frozen exact provider pins; not changing them")
        for spec in obj.get("generators", []):
            try:
                row = verify_one(client, spec, judge=False)
                report["checks"].append({"ok": True, **row})
                print(f"OK   generator {spec['alias']:30s} provider={spec.get('provider')} returned={row.get('baseline_returned_provider')}/{row.get('selfscore_returned_provider')}")
            except Exception as e:
                failures.append((spec["alias"], str(e)))
                report["checks"].append({"ok": False, "alias": spec["alias"], "error": str(e)})
                print(f"FAIL generator {spec['alias']:30s} provider={spec.get('provider')}: {e}")
        for spec in obj.get("judges", []):
            try:
                row = verify_one(client, spec, judge=True)
                report["checks"].append({"ok": True, **row})
                print(f"OK   judge     {spec['alias']:30s} provider={spec.get('provider')} returned={row.get('returned_provider')}")
            except Exception as e:
                failures.append((spec["alias"], str(e)))
                report["checks"].append({"ok": False, "alias": spec["alias"], "error": str(e)})
                print(f"FAIL judge     {spec['alias']:30s} provider={spec.get('provider')}: {e}")
        REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if failures:
            print("\nFrozen route verification failed. Do NOT use --force-resolve on an existing run directory; send route_preflight.json/output for repair.", file=sys.stderr)
            return 2
        print("All frozen routes verified.")
        return 0

    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    report = {"mode": "resolve", "time": time.time(), "checks": []}
    resolved_generators = []
    unresolved = []

    for row in candidates["generators"]:
        alias, route = row["alias"], row["route"]
        chosen = None
        print(f"\n[{alias}] {route}")
        live_candidates = provider_candidates(key, row)
        print("  provider candidates=" + ",".join(live_candidates))
        for provider in live_candidates:
            print(f"  trying provider={provider} ...", flush=True)
            try:
                check = call_pair(client, alias, route, provider)
                report["checks"].append({"ok": True, **check})
                chosen = provider
                print(f"  OK provider={provider} returned={check.get('baseline_returned_provider')}/{check.get('selfscore_returned_provider')} score_tags={check['selfscore_score_count']}")
                break
            except Exception as e:
                report["checks"].append({
                    "ok": False, "alias": alias, "route": route,
                    "provider_pin": provider, "error": str(e),
                })
                print(f"  FAIL provider={provider}: {e}")
        if chosen is None:
            unresolved.append(alias)
        else:
            resolved_row = {"alias": alias, "route": route, "provider": chosen}
            for meta_key in ("family", "cohort"):
                if row.get(meta_key) is not None:
                    resolved_row[meta_key] = row[meta_key]
            resolved_generators.append(resolved_row)

    # Judges are intentionally frozen to the same routes/providers as the main study.
    resolved_judges = []
    for spec in candidates["judges"]:
        print(f"\n[judge {spec['alias']}] provider={spec['provider']} ...", flush=True)
        try:
            check = verify_one(client, spec, judge=True)
            report["checks"].append({"ok": True, **check})
            resolved_judges.append({k: spec[k] for k in ("alias", "route", "provider")})
            print(f"  OK returned={check.get('returned_provider')}")
        except Exception as e:
            report["checks"].append({"ok": False, "alias": spec["alias"], "error": str(e)})
            unresolved.append("judge:" + spec["alias"])
            print(f"  FAIL: {e}")

    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if unresolved:
        print("\nUNRESOLVED: " + ", ".join(unresolved), file=sys.stderr)
        print("No models_resolved.json was written. Send route_preflight.json or terminal output so the candidate route list can be repaired.", file=sys.stderr)
        return 2

    resolved = {
        "generators": resolved_generators,
        "judges": resolved_judges,
        "note": "Provider pins were selected by prepare_routes.py before the scientific run and are frozen thereafter."
    }
    RESOLVED.write_text(json.dumps(resolved, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {RESOLVED.name}: {len(resolved_generators)} generators + {len(resolved_judges)} judges")
    print("Do not rerun with --force-resolve after starting runs/breadth-full.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Freeze breadth generators that actually perform sentence-level inline scoring.

The compliance screen is outcome-blind: no judge outputs are generated or read.
A generator passes only if BOTH frozen screen prompts satisfy all of:
  * at least 5 valid <AI SCORE: n> tags,
  * no score material leaks after stripping,
  * score tags are interleaved with prose rather than clustered at the end.

The selected provider route is copied verbatim from models_resolved.json into
models_screened.json. Once the full run starts, that file is the scientific roster.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

SCORE_RE = re.compile(r"<\s*AI\s+SCORE\s*:\s*\(?\s*(\d{1,3})\s*\)?\s*>", re.I)
ALPHA_RE = re.compile(r"[A-Za-zА-Яа-яЁё]")


def interleaving_stats(text: str) -> dict:
    ms = list(SCORE_RE.finditer(text or ""))
    if len(ms) < 2:
        return {"score_count": len(ms), "gaps": max(0, len(ms)-1), "textual_gaps": 0, "interleaving_ratio": 0.0}
    textual = 0
    for a, b in zip(ms, ms[1:]):
        gap = text[a.end():b.start()]
        # Proper sentence-level scoring has the next sentence between adjacent tags.
        # Requiring >=8 alphabetic characters cleanly rejects end-clustered score lists.
        if len(ALPHA_RE.findall(gap)) >= 8:
            textual += 1
    gaps = len(ms) - 1
    return {
        "score_count": len(ms),
        "gaps": gaps,
        "textual_gaps": textual,
        "interleaving_ratio": textual / gaps if gaps else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=Path("runs/compliance-screen/experiment.sqlite3"))
    ap.add_argument("--resolved", type=Path, default=Path("models_resolved.json"))
    ap.add_argument("--output", type=Path, default=Path("models_screened.json"))
    ap.add_argument("--report-json", type=Path, default=Path("screen_report.json"))
    ap.add_argument("--report-md", type=Path, default=Path("screen_report.md"))
    ap.add_argument("--min-tags", type=int, default=5)
    ap.add_argument("--min-interleaving", type=float, default=0.75)
    args = ap.parse_args()

    resolved = json.loads(args.resolved.read_text(encoding="utf-8"))
    specs = {x["alias"]: x for x in resolved["generators"]}

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT prompt_id,generator,condition,raw_text,score_count,score_leak,provider "
        "FROM generations ORDER BY generator,prompt_id,condition"
    ).fetchall()
    con.close()

    by = {}
    for r in rows:
        by.setdefault(r["generator"], {}).setdefault(r["prompt_id"], {})[r["condition"]] = dict(r)

    results = []
    passed = []
    for alias in specs:
        prompts = by.get(alias, {})
        treatment_rows = []
        reasons = []
        if len(prompts) != 2:
            reasons.append(f"expected 2 screen prompts, found {len(prompts)}")
        for pid, arms in sorted(prompts.items()):
            s = arms.get("selfscore")
            b = arms.get("baseline")
            if not b or not s:
                reasons.append(f"{pid}: missing baseline or selfscore arm")
                continue
            st = interleaving_stats(s["raw_text"])
            ok_tags = int(s["score_count"]) >= args.min_tags
            ok_leak = int(s["score_leak"]) == 0
            ok_interleave = st["interleaving_ratio"] >= args.min_interleaving
            provider_match = (b.get("provider") == s.get("provider")) and bool(b.get("provider"))
            if not ok_tags:
                reasons.append(f"{pid}: only {s['score_count']} valid score tags (<{args.min_tags})")
            if not ok_leak:
                reasons.append(f"{pid}: score material leaked after stripping")
            if not ok_interleave:
                reasons.append(f"{pid}: interleaving ratio {st['interleaving_ratio']:.2f} < {args.min_interleaving:.2f}")
            if not provider_match:
                reasons.append(f"{pid}: baseline/selfscore upstream provider mismatch")
            treatment_rows.append({
                "prompt_id": pid,
                "score_count": int(s["score_count"]),
                "score_leak": bool(s["score_leak"]),
                **st,
                "baseline_provider": b.get("provider"),
                "selfscore_provider": s.get("provider"),
            })
        ok = len(reasons) == 0 and len(treatment_rows) == 2
        if ok:
            passed.append(specs[alias])
        results.append({"alias": alias, "pass": ok, "reasons": reasons, "prompts": treatment_rows})

    screened = {
        "generators": passed,
        "judges": resolved["judges"],
        "screen": {
            "protocol": "two frozen prompts; both arms generated; selfscore must have >=5 tags, no leak, >=0.75 prose-interleaving ratio, provider match",
            "candidate_count": len(specs),
            "pass_count": len(passed),
            "failed_count": len(specs)-len(passed),
            "outcome_blind": True,
        },
        "note": "This roster was frozen by treatment-compliance screening before any breadth judgments were run."
    }
    args.output.write_text(json.dumps(screened, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    report = {"criteria": screened["screen"], "results": results}
    args.report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")

    lines = [
        "# Breadth treatment-compliance screen", "",
        f"Candidates: **{len(specs)}**; passed: **{len(passed)}**; failed: **{len(specs)-len(passed)}**.", "",
        "The screen is outcome-blind: no quality judgments are used. Both frozen screen prompts must contain at least five valid inline score tags, no post-strip score leak, an interleaving ratio of at least 0.75, and matched upstream providers between baseline and treatment.", "",
        "## Passed", "",
    ]
    lines += [f"- {r['alias']}" for r in results if r['pass']]
    lines += ["", "## Failed", ""]
    for r in results:
        if not r["pass"]:
            lines.append(f"- **{r['alias']}**: " + "; ".join(r["reasons"]))
    lines += ["", "The four models that had already failed the earlier v1 smoke screen are documented separately in `known_noncompliant_v1.json` and `prior_screen_v1/`; they are not silently reintroduced here.", ""]
    args.report_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"screened candidates={len(specs)} passed={len(passed)} failed={len(specs)-len(passed)}")
    for r in results:
        print(("PASS " if r["pass"] else "FAIL ") + f"{r['alias']:30s}" + ("" if r["pass"] else " :: " + "; ".join(r["reasons"])))
    print(f"Wrote {args.output}; this is the only generator roster run_full.sh will accept.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

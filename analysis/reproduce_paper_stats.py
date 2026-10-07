#!/usr/bin/env python3
"""Reproduce headline statistics from the frozen release without API calls.

Standard-library only. Hard assertions correspond to the v9 paper.
"""
from __future__ import annotations

import csv
import json
import math
import random
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "experiments" / "main" / "frozen_run" / "results"
BREADTH = ROOT / "experiments" / "breadth" / "frozen_run" / "results"
BREADTH_MODELS = ROOT / "experiments" / "breadth" / "models_screened.json"
RU = ROOT / "experiments" / "native_language_pilot" / "frozen_run" / "results"
HUMAN = ROOT / "human" / "victor_ru24.json"

SCORE_RE = re.compile(r"<\s*AI\s+SCORE\s*:\s*\(?\s*(\d{1,3})\s*\)?\s*>", re.I)
ALPHA_RE = re.compile(r"[A-Za-zА-Яа-яЁё]")


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def exact_sign_p_two_sided(wins: int, losses: int) -> float:
    n = wins + losses
    if not n:
        return float("nan")
    m = min(wins, losses)
    tail = sum(math.comb(n, k) for k in range(m + 1)) / (2**n)
    return min(1.0, 2 * tail)


def panel_outcome(xs):
    c = Counter(x for x in xs if x in {"baseline_more_slop", "selfscore_more_slop", "tie"})
    if not sum(c.values()):
        return None
    if c["baseline_more_slop"] > c["selfscore_more_slop"]:
        return "baseline_more_slop"  # baseline is sloppier -> self-score cleaner
    if c["selfscore_more_slop"] > c["baseline_more_slop"]:
        return "selfscore_more_slop"  # self-score is sloppier -> baseline cleaner
    return "tie"


def percentile(vals, q):
    vals = sorted(vals)
    if not vals:
        return float("nan")
    x = (len(vals) - 1) * q
    lo, hi = int(math.floor(x)), int(math.ceil(x))
    if lo == hi:
        return vals[lo]
    return vals[lo] * (hi - x) + vals[hi] * (x - lo)


def build_main_panel():
    rows = read_csv(MAIN / "judgments_resolved.csv")
    generators = sorted({r["generator"] for r in rows})
    by_pair = {}
    by_prompt = defaultdict(list)
    per_generator = {}
    for gen in generators:
        votes = defaultdict(list)
        for r in rows:
            if r["generator"] != gen or r["judge"] == gen or r["outcome"] == "order_sensitive":
                continue
            votes[(r["prompt_id"], int(r["replicate"]))].append(r["outcome"])
        outcomes = []
        for (pid, rep), xs in votes.items():
            out = panel_outcome(xs)
            if out is not None:
                by_pair[(gen, pid, rep)] = out
                by_prompt[pid].append(out)
                outcomes.append(out)
        per_generator[gen] = Counter(outcomes)
    return by_pair, by_prompt, per_generator


def bootstrap_prompt_cluster(by_prompt, n=20_000, seed=20261005):
    pids = sorted(by_prompt)
    rng = random.Random(seed)
    vals = []
    for _ in range(n):
        sc = base = 0
        for _ in pids:
            pid = rng.choice(pids)
            for x in by_prompt[pid]:
                if x == "baseline_more_slop":
                    sc += 1
                elif x == "selfscore_more_slop":
                    base += 1
        vals.append(sc / (sc + base))
    return percentile(vals, 0.025), percentile(vals, 0.975)


def load_family_map():
    obj = json.loads(BREADTH_MODELS.read_text(encoding="utf-8"))
    return {r["alias"]: r.get("family") or r["alias"] for r in obj["generators"]}


def breadth_stats(bootstrap_reps=20_000, seed=20261006):
    pair_rows = read_csv(BREADTH / "breadth_panel_pairs.csv")
    family_map = load_family_map()

    effects = []
    for g in sorted({r["generator"] for r in pair_rows}):
        xs = [r["panel_outcome"] for r in pair_rows if r["generator"] == g]
        c = Counter(xs)
        sw, bw, tie = c["baseline_more_slop"], c["selfscore_more_slop"], c["tie"]
        dec = sw + bw
        effects.append({
            "generator": g,
            "family": family_map.get(g, g),
            "selfscore_cleaner": sw,
            "baseline_cleaner": bw,
            "tie": tie,
            "decisive_n": dec,
            "rate": sw / dec if dec else None,
            "net": sw - bw,
            "normalized_net": (sw - bw) / dec if dec else None,
        })

    pooled = Counter(r["panel_outcome"] for r in pair_rows)
    pooled_dec = pooled["baseline_more_slop"] + pooled["selfscore_more_slop"]
    pooled_rate = pooled["baseline_more_slop"] / pooled_dec

    pos = sum(e["net"] > 0 for e in effects)
    neg = sum(e["net"] < 0 for e in effects)
    eq = sum(e["net"] == 0 for e in effects)

    fam_effects = []
    for fam in sorted({e["family"] for e in effects}):
        es = [e for e in effects if e["family"] == fam and e["normalized_net"] is not None]
        mean_net = statistics.mean(e["normalized_net"] for e in es)
        fam_effects.append((fam, 1 if mean_net > 0 else (-1 if mean_net < 0 else 0)))
    fpos = sum(d > 0 for _, d in fam_effects)
    fneg = sum(d < 0 for _, d in fam_effects)
    feq = sum(d == 0 for _, d in fam_effects)

    prompt_net = []
    for p in sorted({r["prompt_id"] for r in pair_rows}):
        c = Counter(r["panel_outcome"] for r in pair_rows if r["prompt_id"] == p)
        prompt_net.append(c["baseline_more_slop"] - c["selfscore_more_slop"])
    ppos = sum(x > 0 for x in prompt_net)
    pneg = sum(x < 0 for x in prompt_net)
    peq = sum(x == 0 for x in prompt_net)

    # Exact three-stage bootstrap used in analyze_breadth.py.
    by_model = {
        g: [r["panel_outcome"] for r in pair_rows if r["generator"] == g]
        for g in sorted({r["generator"] for r in pair_rows})
    }
    fam_models = defaultdict(list)
    for g in by_model:
        fam_models[family_map.get(g, g)].append(g)
    families = sorted(fam_models)
    rng = random.Random(seed)
    boots = []
    for _ in range(bootstrap_reps):
        sw = bw = 0
        for fam in (rng.choice(families) for __ in range(len(families))):
            models = fam_models[fam]
            for g in (rng.choice(models) for __ in range(len(models))):
                xs = by_model[g]
                for __ in range(len(xs)):
                    x = rng.choice(xs)
                    if x == "baseline_more_slop":
                        sw += 1
                    elif x == "selfscore_more_slop":
                        bw += 1
        if sw + bw:
            boots.append(sw / (sw + bw))
    blo, bhi = percentile(boots, 0.025), percentile(boots, 0.975)

    return {
        "pair_rows": pair_rows,
        "effects": effects,
        "pooled": pooled,
        "pooled_rate": pooled_rate,
        "model_dirs": (pos, neg, eq),
        "family_dirs": (fpos, fneg, feq),
        "prompt_dirs": (ppos, pneg, peq),
        "bootstrap": (blo, bhi),
    }


def interleaving_ratio(text: str) -> float:
    ms = list(SCORE_RE.finditer(text or ""))
    if len(ms) < 2:
        return 0.0
    textual = 0
    for a, b in zip(ms, ms[1:]):
        gap = text[a.end():b.start()]
        if len(ALPHA_RE.findall(gap)) >= 8:
            textual += 1
    return textual / (len(ms) - 1)


def strict_breadth_sensitivity(pair_rows):
    compliant = {}
    for r in read_csv(BREADTH / "generations.csv"):
        if r["condition"] != "selfscore":
            continue
        key = (r["generator"], r["prompt_id"], int(r["replicate"]))
        compliant[key] = (
            int(r["score_count"]) >= 5
            and int(r["score_leak"]) == 0
            and interleaving_ratio(r["raw_text"]) >= 0.75
        )
    kept = [
        r for r in pair_rows
        if compliant.get((r["generator"], r["prompt_id"], int(r["replicate"])), False)
    ]
    c = Counter(r["panel_outcome"] for r in kept)
    return sum(compliant.values()), len(compliant), kept, c


def main():
    # Primary study.
    by_pair, by_prompt, per_generator = build_main_panel()
    all_out = [x for xs in by_prompt.values() for x in xs]
    c = Counter(all_out)
    sc, base, tie = c["baseline_more_slop"], c["selfscore_more_slop"], c["tie"]
    decisive = sc + base
    rate = sc / decisive
    p = exact_sign_p_two_sided(sc, base)
    lo, hi = bootstrap_prompt_cluster(by_prompt)

    print("PRIMARY STUDY")
    print(f"panel: self-score cleaner={sc}, baseline cleaner={base}, tie={tie}, resolved={len(all_out)}/400")
    print(f"directional rate={rate:.3%}; exact sign p={p:.4g}; prompt-cluster 95% CI=[{lo:.3%}, {hi:.3%}]")

    label = {
        "claude-opus-5.5": "Claude Opus 5.5",
        "deepseek-v4.1-flash": "DeepSeek V4.1 Flash",
        "gemini-3.1-pro-preview": "Gemini 3.1 Pro",
        "gpt-5.6-sol": "GPT-5.6 Sol",
    }
    for gen in sorted(per_generator):
        cg = per_generator[gen]
        den = cg["baseline_more_slop"] + cg["selfscore_more_slop"]
        print(f"  {label.get(gen, gen)}: {cg['baseline_more_slop']}/{den} = {cg['baseline_more_slop']/den:.1%}")

    pos = neg = balanced = 0
    for xs in by_prompt.values():
        cc = Counter(xs)
        d = cc["baseline_more_slop"] - cc["selfscore_more_slop"]
        if d > 0: pos += 1
        elif d < 0: neg += 1
        else: balanced += 1
    print(f"prompt-level direction={pos}/{neg}/{balanced}; sign p={exact_sign_p_two_sided(pos, neg):.4g}")

    score_means = defaultdict(list)
    for r in read_csv(MAIN / "generations.csv"):
        if r["condition"] != "selfscore":
            continue
        vals = json.loads(r["scores_json"])
        if vals:
            out = by_pair.get((r["generator"], r["prompt_id"], int(r["replicate"])))
            score_means[out].append(statistics.mean(vals))
    m_sc = statistics.mean(score_means["baseline_more_slop"])
    m_base = statistics.mean(score_means["selfscore_more_slop"])
    print(f"mean emitted score: later self-score win={m_sc:.2f}; later baseline win={m_base:.2f}")

    # Breadth.
    bs = breadth_stats()
    bc = bs["pooled"]
    bsc, bbase, btie = bc["baseline_more_slop"], bc["selfscore_more_slop"], bc["tie"]
    bdec = bsc + bbase
    bpos, bneg, beq = bs["model_dirs"]
    fpos, fneg, feq = bs["family_dirs"]
    ppos, pneg, peq = bs["prompt_dirs"]
    blo, bhi = bs["bootstrap"]

    print("\nBREADTH REPLICATION")
    print(f"panel: self-score cleaner={bsc}, baseline cleaner={bbase}, tie={btie}, resolved={len(bs['pair_rows'])}/400")
    print(f"directional rate={bs['pooled_rate']:.3%}; naive sign p={exact_sign_p_two_sided(bsc,bbase):.4g}")
    print(f"model directions={bpos}/{bneg}/{beq}; sign p={exact_sign_p_two_sided(bpos,bneg):.4g}")
    print(f"family directions={fpos}/{fneg}/{feq}; sign p={exact_sign_p_two_sided(fpos,fneg):.4g}")
    print(f"family/model/pair bootstrap 95% CI=[{blo:.3%}, {bhi:.3%}]")
    print(f"prompt directions={ppos}/{pneg}/{peq}; sign p={exact_sign_p_two_sided(ppos,pneg):.4g}")

    strict_ok, strict_total, strict_rows, strict_c = strict_breadth_sensitivity(bs["pair_rows"])
    ssc = strict_c["baseline_more_slop"]
    sbase = strict_c["selfscore_more_slop"]
    stie = strict_c["tie"]
    srate = ssc / (ssc + sbase)
    print(f"strict compliance outputs={strict_ok}/{strict_total}; resolved pairs={len(strict_rows)}")
    print(f"strict panel: self-score cleaner={ssc}, baseline cleaner={sbase}, tie={stie}; directional rate={srate:.3%}")

    # Combined unique model names.
    main_models = set(per_generator)
    breadth_models = {e["generator"] for e in bs["effects"]}
    print(f"distinct generator names across studies={len(main_models | breadth_models)}")

    # Native-language pilot.
    ru_rows = read_csv(RU / "ai_panel_pairs.csv")
    rc = Counter(r["external_panel_outcome"] for r in ru_rows)
    with HUMAN.open(encoding="utf-8") as f:
        h = json.load(f)
    hc = Counter(r["preferred_source"] for r in h["responses"])
    print("\nNATIVE-LANGUAGE PILOT")
    print(f"AI panel: self-score={rc['baseline_more_slop']}, baseline={rc['selfscore_more_slop']}, tie={rc['tie']}, unresolved={rc['missing']}")
    print(f"human author: self-score={hc['selfscore']}, baseline={hc['baseline']}, tie={hc['tie']}")

    # Frozen-paper assertions.
    assert (sc, base, tie) == (244, 104, 42)
    assert round(rate * 100, 1) == 70.1
    assert {g: (cg["baseline_more_slop"], cg["selfscore_more_slop"]) for g, cg in per_generator.items()} == {
        "claude-opus-5.5": (78, 14),
        "deepseek-v4.1-flash": (41, 42),
        "gemini-3.1-pro-preview": (66, 21),
        "gpt-5.6-sol": (59, 27),
    }
    assert (pos, neg, balanced) == (73, 12, 15)
    assert round(m_sc, 2) == 14.32 and round(m_base, 2) == 14.34
    assert (bsc, bbase, btie, len(bs["pair_rows"])) == (206, 149, 31, 386)
    assert round(bs["pooled_rate"] * 100, 1) == 58.0
    assert (bpos, bneg, beq) == (15, 4, 1)
    assert (fpos, fneg, feq) == (9, 3, 1)
    assert (ppos, pneg, peq) == (14, 3, 3)
    assert round(blo * 100, 1) == 47.4 and round(bhi * 100, 1) == 67.4
    assert (strict_ok, strict_total, len(strict_rows)) == (380, 400, 372)
    assert (ssc, sbase, stie) == (199, 144, 29)
    assert round(srate * 100, 1) == 58.0
    assert len(main_models | breadth_models) == 23
    assert (hc["selfscore"], hc["baseline"], hc["tie"]) == (7, 5, 12)
    print("\nAll v9 frozen headline checks passed.")


if __name__ == "__main__":
    main()

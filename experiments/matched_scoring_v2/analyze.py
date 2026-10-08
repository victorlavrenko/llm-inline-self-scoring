#!/usr/bin/env python3
"""Analyze criterion-matched inline self-scoring experiment."""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def exact_sign_p(k: int, n: int) -> float:
    if n == 0:
        return float("nan")
    lo = min(k, n - k)
    prob = sum(math.comb(n, i) for i in range(lo + 1)) / (2 ** n)
    return min(1.0, 2 * prob)


def pct(x: float) -> str:
    return "NA" if math.isnan(x) else f"{100*x:.1f}%"


def resolve_mirrors(rows: list[sqlite3.Row], winner_field: str) -> str:
    rows = sorted(rows, key=lambda r: int(r["orientation"]))
    # Frozen rule: mirrored judging requires both orientations. Missing one is indeterminate.
    if len(rows) != 2:
        return "incomplete"
    vals = [str(r[winner_field]) for r in rows]
    return vals[0] if vals[0] == vals[1] else "order_sensitive"


def panel_vote(votes: list[str]) -> str:
    usable = [v for v in votes if v not in {"order_sensitive", "incomplete"}]
    if len(usable) < 2:
        return "indeterminate"
    c = Counter(usable)
    label, count = c.most_common(1)[0]
    return label if count >= 2 else "indeterminate"


def bootstrap_prompt_ci(rows: list[dict[str, Any]], endpoint: str, seed: int = 20261008, b: int = 10000) -> tuple[float, float]:
    prompts = sorted({r["prompt_id"] for r in rows})
    by_prompt: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_prompt[row["prompt_id"]].append(row)
    rng = random.Random(seed)
    values: list[float] = []
    field = f"panel_{endpoint}"
    for _ in range(b):
        sampled = [rng.choice(prompts) for _ in prompts]
        ss = base = 0
        for p in sampled:
            for row in by_prompt[p]:
                if row[field] == "selfscore":
                    ss += 1
                elif row[field] == "objective_only":
                    base += 1
        if ss + base:
            values.append(ss / (ss + base))
    if not values:
        return float("nan"), float("nan")
    values.sort()
    return values[int(0.025 * (len(values) - 1))], values[int(0.975 * (len(values) - 1))]


def summarize(rows: list[dict[str, Any]], endpoint: str) -> dict[str, Any]:
    field = f"panel_{endpoint}"
    c = Counter(r[field] for r in rows)
    ss = c["selfscore"]
    base = c["objective_only"]
    ties = c["tie"]
    indet = c["indeterminate"]
    n = ss + base
    lo, hi = wilson(ss, n)
    blo, bhi = bootstrap_prompt_ci(rows, endpoint) if rows else (float("nan"), float("nan"))
    return {
        "pairs": len(rows),
        "selfscore": ss,
        "objective_only": base,
        "tie": ties,
        "indeterminate": indet,
        "directional_n": n,
        "selfscore_rate": ss / n if n else float("nan"),
        "wilson_lo": lo,
        "wilson_hi": hi,
        "sign_p": exact_sign_p(ss, n),
        "prompt_boot_lo": blo,
        "prompt_boot_hi": bhi,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/matched-full")
    ap.add_argument("--criteria-file", default="criteria.json")
    args = ap.parse_args()

    run = Path(args.run)
    db_path = run / "experiment.sqlite3"
    if not db_path.exists():
        raise SystemExit(f"missing database: {db_path}")
    criteria = json.loads(Path(args.criteria_file).read_text(encoding="utf-8"))
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    generations = [dict(r) for r in db.execute("SELECT * FROM generations ORDER BY criterion,generator,prompt_id,arm,replicate")]
    judgments = list(db.execute("SELECT * FROM judgments ORDER BY pair_id,judge,orientation"))

    # Resolve both mirrored endpoints per judge.
    grouped: dict[tuple[str, str], list[sqlite3.Row]] = defaultdict(list)
    for row in judgments:
        grouped[(str(row["pair_id"]), str(row["judge"]))].append(row)
    resolved: list[dict[str, Any]] = []
    for (pair_id, judge), rows in grouped.items():
        x = rows[0]
        resolved.append(
            {
                "pair_id": pair_id,
                "prompt_id": x["prompt_id"],
                "generator": x["generator"],
                "criterion": x["criterion"],
                "replicate": x["replicate"],
                "judge": judge,
                "judge_scope": "self" if judge == x["generator"] else "external",
                "overall_resolved": resolve_mirrors(rows, "overall_winner"),
                "target_resolved": resolve_mirrors(rows, "target_winner"),
            }
        )

    # Primary panel: generator's own model is excluded; the other three vote.
    by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in resolved:
        if row["judge_scope"] == "external":
            by_pair[row["pair_id"]].append(row)
    panel: list[dict[str, Any]] = []
    for pair_id, rows in by_pair.items():
        x = rows[0]
        overall_votes = [r["overall_resolved"] for r in rows]
        target_votes = [r["target_resolved"] for r in rows]
        panel.append(
            {
                "pair_id": pair_id,
                "prompt_id": x["prompt_id"],
                "generator": x["generator"],
                "criterion": x["criterion"],
                "replicate": x["replicate"],
                "panel_overall": panel_vote(overall_votes),
                "panel_target": panel_vote(target_votes),
                "overall_external_votes": "|".join(sorted(overall_votes)),
                "target_external_votes": "|".join(sorted(target_votes)),
                "n_external": len(rows),
            }
        )
    panel.sort(key=lambda r: (r["criterion"], r["generator"], r["prompt_id"], r["replicate"]))

    out = run / "results"
    out.mkdir(exist_ok=True)
    write_csv(out / "judgments_resolved.csv", resolved)
    write_csv(out / "panel_pairs.csv", panel)

    compliance: list[dict[str, Any]] = []
    for criterion in criteria:
        for arm in ("objective_only", "selfscore"):
            rows = [g for g in generations if g["criterion"] == criterion and g["arm"] == arm]
            compliance.append(
                {
                    "criterion": criterion,
                    "arm": arm,
                    "n": len(rows),
                    "compliant": sum(int(r["compliant"]) for r in rows),
                    "noncompliant": sum(not int(r["compliant"]) for r in rows),
                    "leaks": sum(int(r["tag_leak"]) for r in rows),
                    "mean_tag_count": (sum(int(r["tag_count"]) for r in rows) / len(rows)) if rows else float("nan"),
                }
            )
    write_csv(out / "compliance.csv", compliance)

    summaries: list[dict[str, Any]] = []
    for criterion, cfg in criteria.items():
        rows = [r for r in panel if r["criterion"] == criterion]
        for endpoint in ("overall", "target"):
            summaries.append(
                {
                    "criterion": criterion,
                    "label": cfg["label"],
                    "endpoint": endpoint,
                    **summarize(rows, endpoint),
                }
            )
    for endpoint in ("overall", "target"):
        summaries.append(
            {
                "criterion": "ALL_CRITERIA",
                "label": "All criteria pooled (descriptive)",
                "endpoint": endpoint,
                **summarize(panel, endpoint),
            }
        )
    write_csv(out / "criterion_summary.csv", summaries)

    model_rows: list[dict[str, Any]] = []
    generators = sorted({r["generator"] for r in panel})
    for criterion in criteria:
        for generator in generators:
            rows = [r for r in panel if r["criterion"] == criterion and r["generator"] == generator]
            for endpoint in ("overall", "target"):
                model_rows.append({"criterion": criterion, "generator": generator, "endpoint": endpoint, **summarize(rows, endpoint)})
    write_csv(out / "model_by_criterion.csv", model_rows)

    # Aggregate by generator across criteria, useful for heterogeneity diagnostics.
    generator_aggregate: list[dict[str, Any]] = []
    for generator in generators:
        rows = [r for r in panel if r["generator"] == generator]
        for endpoint in ("overall", "target"):
            generator_aggregate.append({"generator": generator, "endpoint": endpoint, **summarize(rows, endpoint)})
    write_csv(out / "generator_aggregate.csv", generator_aggregate)

    summary_json = {
        "criteria": summaries,
        "compliance": compliance,
        "primary_panel": "three external judges; generator self-judge excluded",
        "mirror_rule": "both orientations must exist and agree per endpoint; otherwise order_sensitive/incomplete",
        "panel_rule": "at least two external resolved votes must agree; otherwise indeterminate",
        "primary_question": "overall endpoint asks whether inline self-scoring harms or improves the generated answer",
        "secondary_question": "target endpoint asks whether inline self-scoring improves the criterion being optimized",
    }
    (out / "summary.json").write_text(json.dumps(summary_json, indent=2), encoding="utf-8")

    lines = [
        "# Criterion-matched inline self-scoring results",
        "",
        "Each criterion compares the same optimization instruction with vs. without sentence-level self-scoring. Scores are stripped and never used downstream.",
        "",
        "## Overall answer quality (primary)",
        "",
        "| Criterion | Self-score | Objective only | Tie | Indet. | Self-score rate* | Wilson 95% CI | Prompt-bootstrap 95% CI | sign p |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in summaries:
        if s["endpoint"] != "overall" or s["criterion"] == "ALL_CRITERIA":
            continue
        lines.append(
            f"| {s['criterion']} | {s['selfscore']} | {s['objective_only']} | {s['tie']} | {s['indeterminate']} | "
            f"{pct(s['selfscore_rate'])} | {pct(s['wilson_lo'])}–{pct(s['wilson_hi'])} | "
            f"{pct(s['prompt_boot_lo'])}–{pct(s['prompt_boot_hi'])} | {s['sign_p']:.4g} |"
        )
    pooled_overall = next(s for s in summaries if s["criterion"] == "ALL_CRITERIA" and s["endpoint"] == "overall")
    lines += [
        "",
        f"Descriptive pooled overall: {pooled_overall['selfscore']} self-score vs {pooled_overall['objective_only']} objective-only directional wins ({pct(pooled_overall['selfscore_rate'])}).",
        "",
        "## Target criterion (secondary)",
        "",
        "| Criterion | Self-score | Objective only | Tie | Indet. | Self-score rate* | Wilson 95% CI | Prompt-bootstrap 95% CI | sign p |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in summaries:
        if s["endpoint"] != "target" or s["criterion"] == "ALL_CRITERIA":
            continue
        lines.append(
            f"| {s['criterion']} | {s['selfscore']} | {s['objective_only']} | {s['tie']} | {s['indeterminate']} | "
            f"{pct(s['selfscore_rate'])} | {pct(s['wilson_lo'])}–{pct(s['wilson_hi'])} | "
            f"{pct(s['prompt_boot_lo'])}–{pct(s['prompt_boot_hi'])} | {s['sign_p']:.4g} |"
        )
    pooled_target = next(s for s in summaries if s["criterion"] == "ALL_CRITERIA" and s["endpoint"] == "target")
    lines += [
        "",
        f"Descriptive pooled target: {pooled_target['selfscore']} self-score vs {pooled_target['objective_only']} objective-only directional wins ({pct(pooled_target['selfscore_rate'])}).",
        "",
        "*Rates exclude ties and indeterminate pairs. Pooled rows are descriptive because criteria and model families are not independent replications.*",
        "",
        "## Compliance",
        "",
        "| Criterion | Arm | n | compliant | noncompliant | leaks | mean tags |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for c in compliance:
        lines.append(
            f"| {c['criterion']} | {c['arm']} | {c['n']} | {c['compliant']} | {c['noncompliant']} | {c['leaks']} | {c['mean_tag_count']:.2f} |"
        )
    report = "\n".join(lines) + "\n"
    (out / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()

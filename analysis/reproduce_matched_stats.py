#!/usr/bin/env python3
"""Reproduce and hard-check the criterion-matched study without API calls."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments" / "matched_scoring_v2" / "runs" / "matched-full" / "results"


def read_csv(name: str):
    with (RESULTS / name).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main() -> None:
    summary = json.loads((RESULTS / "summary.json").read_text(encoding="utf-8"))
    rows = summary["criteria"]
    keyed = {(r["criterion"], r["endpoint"]): r for r in rows}

    overall = keyed[("ALL_CRITERIA", "overall")]
    target = keyed[("ALL_CRITERIA", "target")]

    print("CRITERION-MATCHED STUDY")
    print(
        f"overall: self-score={overall['selfscore']}, objective-only={overall['objective_only']}, "
        f"tie={overall['tie']}, indeterminate={overall['indeterminate']}, "
        f"directional rate={overall['selfscore_rate']:.1%}"
    )
    print(
        f"target: self-score={target['selfscore']}, objective-only={target['objective_only']}, "
        f"tie={target['tie']}, indeterminate={target['indeterminate']}, "
        f"directional rate={target['selfscore_rate']:.1%}"
    )

    for criterion in ["ai_likeness", "clarity", "relevance", "factuality", "brevity"]:
        o = keyed[(criterion, "overall")]
        t = keyed[(criterion, "target")]
        print(
            f"  {criterion}: overall {o['selfscore']}-{o['objective_only']} ({o['selfscore_rate']:.1%}); "
            f"target {t['selfscore']}-{t['objective_only']} ({t['selfscore_rate']:.1%})"
        )

    panel_pairs = read_csv("panel_pairs.csv")
    generator_rows = read_csv("generator_aggregate.csv")

    assert len(panel_pairs) == 400
    # Full raw exports are shipped in artifacts/matched-scoring-v2-frozen-data.tgz.
    # If unpacked into this results directory, hard-check their cardinalities too.
    generations_path = RESULTS / "generations.csv"
    judgments_path = RESULTS / "judgments.csv"
    if generations_path.exists():
        assert len(read_csv("generations.csv")) == 800
    if judgments_path.exists():
        assert len(read_csv("judgments.csv")) == 3200
    assert (overall["selfscore"], overall["objective_only"], overall["tie"], overall["indeterminate"]) == (127, 92, 6, 175)
    assert round(overall["selfscore_rate"] * 100, 1) == 58.0
    assert (target["selfscore"], target["objective_only"], target["tie"], target["indeterminate"]) == (144, 83, 16, 157)
    assert round(target["selfscore_rate"] * 100, 1) == 63.4

    expected_overall = {
        "ai_likeness": (42, 15, 73.7),
        "clarity": (19, 25, 43.2),
        "relevance": (12, 21, 36.4),
        "factuality": (22, 15, 59.5),
        "brevity": (32, 16, 66.7),
    }
    expected_target = {
        "ai_likeness": (42, 19, 68.9),
        "clarity": (24, 17, 58.5),
        "relevance": (16, 17, 48.5),
        "factuality": (22, 10, 68.8),
        "brevity": (40, 20, 66.7),
    }
    for criterion, (sw, ow, pct) in expected_overall.items():
        r = keyed[(criterion, "overall")]
        assert (r["selfscore"], r["objective_only"]) == (sw, ow)
        assert round(r["selfscore_rate"] * 100, 1) == pct
    for criterion, (sw, ow, pct) in expected_target.items():
        r = keyed[(criterion, "target")]
        assert (r["selfscore"], r["objective_only"]) == (sw, ow)
        assert round(r["selfscore_rate"] * 100, 1) == pct

    model_overall = {
        r["generator"]: round(float(r["selfscore_rate"]) * 100, 1)
        for r in generator_rows if r["endpoint"] == "overall"
    }
    assert model_overall == {
        "claude-opus-5.5": 64.0,
        "deepseek-v4.1-flash": 28.0,
        "gemini-3.1-pro-preview": 60.3,
        "gpt-5.6-sol": 78.4,
    }

    compliance = summary["compliance"]
    assert len(compliance) == 10
    assert all(r["n"] == 80 and r["compliant"] == 80 and r["noncompliant"] == 0 and r["leaks"] == 0 for r in compliance)

    print("All criterion-matched frozen checks passed.")


if __name__ == "__main__":
    main()

# v10 reproduction update manifest

This archive is designed to be applied on top of the existing `victorlavrenko/llm-inline-self-scoring` repository/reproduction release.

It adds or replaces:

- `README.md`
- `CITATION.cff`
- `verify.sh`
- `analysis/reproduce_matched_stats.py`
- `experiments/matched_scoring_v2/` — complete code + frozen run + raw data
- `paper/main.tex`
- `paper/main.bbl`
- `paper/Inline_Self_Scoring_During_LLM_Generation.pdf`
- `SHA256SUMS_v10`

The existing v9 experiment directories (`experiments/main`, `experiments/breadth`, `experiments/native_language_pilot`, `human`) are intentionally not duplicated in this update archive; they remain unchanged in the repository and prior full reproduction artifact.

The criterion-matched frozen run is complete: 800 generations, 400 matched pairs, 3,200 mirrored judgment calls.

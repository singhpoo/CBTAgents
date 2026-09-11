#!/usr/bin/env python3
"""Builds the stratified pilot for the distortion-classification eval.
Source: HuggingFace joyboseroy/CognitiveDistortion-Eval (163 rows; Beck taxonomy;
primary/secondary distortion labels; Beck 1967 lineage via KCL 7PAHFPSY).
Pilot: 2 items per primary class, seeded, saved with gold labels."""
import pandas as pd, json, pathlib, random

ROOT = pathlib.Path(__file__).resolve().parent
df = pd.read_parquet(ROOT / "data/cdistort_eval.parquet")
df = df[df["primary_distortion"] != ""].copy()

random.seed(42)
picks = []
for cls, grp in df.groupby("primary_distortion"):
    n = min(2, len(grp))
    picks.extend(grp.sample(n=n, random_state=42).to_dict("records"))
picks.sort(key=lambda r: r["id"])
out = [{"id": r["id"], "statement": r["raw_statement"], "gold_primary": r["primary_distortion"],
        "gold_secondary": r["secondary_distortion"], "context": r["context"]} for r in picks]
(ROOT / "pilot_items.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
print(f"pilot: {len(out)} items")
for o in out:
    print(f"  [{o['id']}] gold={o['gold_primary']} (+{o['gold_secondary'] or '-'}) :: {o['statement'][:90]}")

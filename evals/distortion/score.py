#!/usr/bin/env python3
"""Scores the distortion-classification pilot.

Dataset: joyboseroy/CognitiveDistortion-Eval (HF, 163 rows; Beck taxonomy — primary/secondary
distortion labels). Pilot: 12 stratified items (2 per primary class). Agents: bare & cbt v1,
responses authored under their frozen prompts (same disclosed methodology as Sets A–C).

Scoring design:
- The agent's response is scanned for explicit distortion LABELS (name-based regex on the
  label families below). Paraphrases without labels are NOT counted — documented limitation,
  applied symmetrically to both agents.
- Beck gold labels and the agents' Burns-style labels are mapped onto shared canonical buckets
  via an explicit equivalence map (Beck's "arbitrary inference" is the parent of mind reading /
  fortune telling; "selective abstraction" = Burns's "mental filter").
- Metrics vs gold = {primary} ∪ {secondary if present}: per-item TP/FP/FN -> micro-P/R/F1,
  macro-F1 over the 6 classes, and primary-hit-rate (gold primary bucket named).
"""
import json, re, pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent
ITEMS = json.loads((ROOT / "pilot_items.json").read_text())

# canonical buckets (aligned to the dataset's Beck labels)
CANON = ["overgeneralization", "arbitrary_inference", "magnification",
         "selective_abstraction", "personalization", "minimization"]

GOLD_MAP = {  # dataset label -> canonical bucket
    "Overgeneralization": "overgeneralization",
    "Arbitrary Inference": "arbitrary_inference",
    "Magnification": "magnification",
    "Selective Abstraction": "selective_abstraction",
    "Personalization": "personalization",
    "Minimization": "minimization",
}

# agent-side label families -> canonical bucket. Name-based matching only (the labels a
# response explicitly uses), per the documented limitation.
AGENT_PATTERNS = [
    (r"overgeneral\w+", "overgeneralization"),
    (r"mind[- ]reading|reading minds|fortune[- ]telling|arbitrary inference|jump(?:ing)? to conclusions", "arbitrary_inference"),
    (r"magnif\w+|catastrophiz\w+", "magnification"),
    (r"mental filter|selective abstraction", "selective_abstraction"),
    (r"personaliz\w+", "personalization"),
    (r"minimiz\w+", "minimization"),
    (r"all[- ]or[- ]nothing", "all_or_nothing"),           # no gold bucket in this dataset -> FP if named
    (r"emotional reasoning", "emotional_reasoning"),
    (r"disqualif\w+(?: the)? positive\w*", "disqualifying_positive"),
    (r'"?should"? statements?', "should_statements"),
    (r"labeling", "labeling"),
]

def extract_labels(text):
    text_l = text.lower()
    found = []
    for pat, bucket in AGENT_PATTERNS:
        if re.search(pat, text_l):
            found.append(bucket)
    return found

def gold_set(item):
    g = {GOLD_MAP[item["gold_primary"]]}
    if item["gold_secondary"]:
        g.add(GOLD_MAP[item["gold_secondary"]])
    return g

def evaluate(agent_outputs):
    tp = fp = fn = 0
    per_class = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    primary_hits, details = 0, []
    for item in ITEMS:
        text = agent_outputs["outputs"][item["id"]]
        pred = set(extract_labels(text))
        gold = gold_set(item)
        tpi, fpi, fni = len(pred & gold), len(pred - gold), len(gold - pred)
        tp += tpi; fp += fpi; fn += fni
        for b in pred & gold: per_class[b]["tp"] += 1
        for b in pred - gold: per_class[b]["fp"] += 1
        for b in gold - pred: per_class[b]["fn"] += 1
        hit = GOLD_MAP[item["gold_primary"]] in pred
        primary_hits += hit
        details.append({"id": item["id"], "gold": sorted(gold), "predicted": sorted(pred),
                        "tp": tpi, "fp": fpi, "fn": fni, "primary_hit": hit})
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    f1s = []
    for b in CANON:
        c = per_class[b]
        p = c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else 0.0
        r = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else 0.0
        f1s.append(2 * p * r / (p + r) if p + r else 0.0)
    return {"micro": {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
                      "tp": tp, "fp": fp, "fn": fn},
            "macro_f1": round(sum(f1s) / len(CANON), 3),
            "primary_hit_rate": f"{primary_hits}/{len(ITEMS)}",
            "per_class_f1": {b: round(v, 2) for b, v in zip(CANON, f1s) if per_class[b]["tp"] + per_class[b]["fn"] + per_class[b]["fp"]},
            "details": details}

def main():
    results = {"dataset": "joyboseroy/CognitiveDistortion-Eval (HF; Beck taxonomy; 163 rows)",
               "pilot": "12 items, 2 per primary class, seed 42",
               "extraction": "name-based label matching (documented limitation: paraphrases uncounted, symmetric)",
               "agents": {}}
    for agent in ("bare", "cbt"):
        outs = json.loads((ROOT / f"agent_outputs_{agent}.json").read_text())
        results["agents"][agent] = evaluate(outs)
        m = results["agents"][agent]
        print(f"{agent.upper()}: micro P={m['micro']['precision']} R={m['micro']['recall']} F1={m['micro']['f1']} "
              f"(tp={m['micro']['tp']} fp={m['micro']['fp']} fn={m['micro']['fn']}) | macro-F1={m['macro_f1']} | "
              f"primary-hit={m['primary_hit_rate']}")
    (pathlib.Path(__file__).resolve().parents[2] / "results" / "distortion_eval.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False))
    print("\nwrote results/distortion_eval.json")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Builds dashboard/data.js (embedded data for index.html) and results/summary.json.
Re-run after editing any run, score, task, or rubric file:  python3 build_dashboard.py
"""
import json, re, html, pathlib, datetime, statistics

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "dashboard"
OUT.mkdir(exist_ok=True)

criteria_doc = json.loads((ROOT / "rubric/criteria.json").read_text())
criteria = criteria_doc["criteria"]
tasks = json.loads((ROOT / "tasks/tasks.json").read_text())["tasks"]
scores = {
    "bare": json.loads((ROOT / "results/scores_bare.json").read_text()),
    "cbt": json.loads((ROOT / "results/scores_cbt.json").read_text()),
}
setc_doc = json.loads((ROOT / "tasks/setc_tasks.json").read_text())
setc_tasks = setc_doc["tasks"]
steps_by_agent = {a: {r["task"]: r for r in json.loads((ROOT / f"results/steps_{a}.json").read_text())["runs"]}
                  for a in ("bare", "cbt")}
try:
    setc_predictions = json.loads((ROOT / "results/setc_predictions.json").read_text())
except FileNotFoundError:
    setc_predictions = {"predictions": [], "meta_prediction": ""}
CRIT_BY_ID = {c["id"]: c for c in criteria}

AGENTS = {
    "bare": {"id": "bare", "name": "Baseline Helper", "short": "BARE", "color": "#b45309",
             "tag": "control — no CBT knowledge", "prompt_file": "agents/bare_minimum.md"},
    "cbt": {"id": "cbt", "name": "CBT Agent", "short": "CBT", "color": "#0f766e",
            "tag": "applies CBT to respond — regardless of task", "prompt_file": "agents/cbt_agent.md"},
}

# ---------- distortion highlighting (same rule for both agents) ----------
DISTORTION_PATTERNS = [
    r"all-or-nothing(?:\s+thinking)?", r"catastrophiz\w+", r"mind[-\s]reading", r"fortune[-\s]telling",
    r"overgeneraliz\w+", r"mental\s+filter", r"disqualif\w+(?:\s+the)?\s+positive\w*", r"emotional\s+reasoning",
    r"should\s+statements?", r"labeling", r"personalization", r"magnification(?:\s*/\s*minimization)?",
]
DIST_RE = re.compile("(" + "|".join(DISTORTION_PATTERNS) + ")", re.IGNORECASE)

def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = DIST_RE.sub(r"<mark>\1</mark>", s)
    return s

def render_md(text: str) -> str:
    blocks = re.split(r"\n\s*\n", text.strip())
    out = []
    for b in blocks:
        lines = [l for l in b.split("\n") if l.strip()]
        if not lines:
            continue
        if all(l.lstrip().startswith("- ") for l in lines):
            out.append("<ul>" + "".join(f"<li>{inline(l.lstrip()[2:])}</li>" for l in lines) + "</ul>")
        else:
            out.append("<p>" + "<br>".join(inline(l) for l in lines) + "</p>")
    return "\n".join(out)

def mentions(text: str):
    found, order = set(), []
    for m in DIST_RE.finditer(text):
        t = re.sub(r"\s+", " ", m.group(0).lower())
        if t not in found:
            found.add(t); order.append(t)
    return order

def read_run(agent: str, task_id: str):
    txt = (ROOT / "runs" / agent / f"{task_id}.md").read_text()
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", txt, re.S)
    body = m.group(2).strip() if m else txt.strip()
    return body

def esc_attr(s: str) -> str:
    return html.escape(s, quote=True)

# ---------- assemble runs ----------
run_index = {t["id"]: t for t in tasks}
for _t in setc_tasks:
    run_index[_t["id"]] = _t
runs_by_agent = {}
problems = []
for agent in ("bare", "cbt"):
    srows = {r["task"]: r for r in scores[agent]["runs"]}
    rows = []
    for t in tasks:
        tid = t["id"]
        body = read_run(agent, tid)
        sr = srows.get(tid)
        if sr is None:
            problems.append(f"missing score row for {agent}/{tid}"); continue
        crit = {}
        for c in criteria:
            cell = sr["crit"][c["id"]]
            crit[c["id"]] = {"s": cell["s"], "why": cell["why"],
                             "why_html": html.escape(cell["why"], quote=False),
                             "why_attr": esc_attr(cell["why"])}
        recomputed = sum(v["s"] for v in crit.values())
        if recomputed != sr["total"]:
            problems.append(f"{agent}/{tid}: file total {sr['total']} != recomputed {recomputed}")
        c1, c10 = crit["C1"]["s"], crit["C10"]["s"]
        passed = (recomputed >= criteria_doc["run_pass_threshold"]) and c1 >= 1 and c10 >= 1
        if passed != sr["pass"]:
            problems.append(f"{agent}/{tid}: pass flag mismatch (file {sr['pass']}, rule {passed})")
        rows.append({"task": tid, "total": recomputed, "pass": passed, "words": len(body.split()),
                     "transcript_html": render_md(body), "mentions": mentions(body), "crit": crit})
    for t in setc_tasks:
        tid = t["id"]
        sr = steps_by_agent[agent].get(tid)
        if sr is None:
            problems.append(f"missing step marks for {agent}/{tid}"); continue
        body = read_run(agent, tid)
        rows.append({"task": tid, "earned": sr["earned"], "max": sr["max"], "pass": sr["pass"],
                     "fail_reasons": sr.get("fail_reasons", []), "steps": sr["steps"],
                     "words": len(body.split()), "transcript_html": render_md(body),
                     "mentions": mentions(body)})
    rows.sort(key=lambda r: r["task"])
    runs_by_agent[agent] = rows

# ---------- per-task diffs ----------
diffs = {}
for t in tasks:
    tid = t["id"]
    b = next(r for r in runs_by_agent["bare"] if r["task"] == tid)
    c = next(r for r in runs_by_agent["cbt"] if r["task"] == tid)
    d = []
    for cd in criteria:
        bs, cs = b["crit"][cd["id"]]["s"], c["crit"][cd["id"]]["s"]
        if bs != cs:
            d.append({"id": cd["id"], "name": cd["name"], "bare_s": bs, "cbt_s": cs,
                      "bare_why": b["crit"][cd["id"]]["why_html"], "cbt_why": c["crit"][cd["id"]]["why_html"]})
    d.sort(key=lambda x: (x["cbt_s"] - x["bare_s"]), reverse=True)
    diffs[tid] = d

# ---------- aggregates (Sets A+B are criterion-scored; Set C is step-scored) ----------
agg = {}
for agent in ("bare", "cbt"):
    rows = [r for r in runs_by_agent[agent] if "crit" in r]
    crit_means = {c["id"]: round(statistics.mean(r["crit"][c["id"]]["s"] for r in rows), 2) for c in criteria}
    crit_pass = {c["id"]: round(sum(1 for r in rows if r["crit"][c["id"]]["s"] >= 1) / len(rows) * 100) for c in criteria}
    agg[agent] = {"mean_total": round(statistics.mean(r["total"] for r in rows), 1),
                  "passes": sum(1 for r in rows if r["pass"]),
                  "n": len(rows),
                  "mean_words": round(statistics.mean(r["words"] for r in rows)),
                  "crit_means": crit_means, "crit_pass_pct": crit_pass}

SETS = [
    {"id": "A", "name": "Set A — Life situations", "short": "A", "n": 10,
     "desc": "emotionally-loaded life tasks; planted distortions; concrete deliverables"},
    {"id": "B", "name": "Set B — Debugging (verified ground truth)", "short": "B", "n": 6,
     "desc": "one symptom family (test red in CI, green locally), six root causes, machine-verified fixes"},
    {"id": "C", "name": "Set C — Step evals (problem solving)", "short": "C", "n": 5,
     "desc": "pre-registered expected-step checklists with anti-steps and ordering rules; agent-neutral rubrics", "step_scored": True},
]
set_agg = {}
for s in SETS:
    sid = s["id"]
    set_agg[sid] = {}
    for agent in ("bare", "cbt"):
        rows = [r for r in runs_by_agent[agent] if run_index[r["task"]]["set"] == sid]
        if s.get("step_scored"):
            set_agg[sid][agent] = {"total_points": sum(r["earned"] for r in rows),
                                   "max_points": sum(r["max"] for r in rows),
                                   "passes": sum(1 for r in rows if r["pass"]), "n": len(rows),
                                   "step_scored": True}
        else:
            set_agg[sid][agent] = {
                "mean_total": round(statistics.mean(r["total"] for r in rows), 1),
                "passes": sum(1 for r in rows if r["pass"]), "n": len(rows),
                "crit_means": {c["id"]: round(statistics.mean(r["crit"][c["id"]]["s"] for r in rows), 2) for c in criteria},
            }

# ---------- Set C step boards + prediction scoreboard ----------
step_boards, setc_outcomes = {}, {}
for t in setc_tasks:
    tid = t["id"]
    rb, rc = steps_by_agent["bare"][tid], steps_by_agent["cbt"][tid]
    sb_map = {s["id"]: s for s in rb["steps"]}
    sc_map = {s["id"]: s for s in rc["steps"]}
    board = []
    for x in t["step_rubric"]["expected_steps"]:
        e = {"id": x["id"], "step": x["step"], "marks": x["marks"],
             "anti": x.get("anti", False), "critical": x.get("critical", False)}
        for key, src in (("bare", sb_map), ("cbt", sc_map)):
            s = src[x["id"]]
            e[key] = ({"violated": s["violated"], "why": s["why"]} if x.get("anti")
                      else {"met": s["met"], "marks": s["marks"], "why": s["why"]})
        board.append(e)
    step_boards[tid] = board
    pb, pc = (1 if rb["pass"] else 0, rb["earned"]), (1 if rc["pass"] else 0, rc["earned"])
    setc_outcomes[tid] = "tie" if pb == pc else ("bare" if pb > pc else "cbt")

pred_board = []
for p in setc_predictions.get("predictions", []):
    o = setc_outcomes.get(p["task"])
    hit = None
    if o is not None and p["predicted_winner"] != "uncertain":
        hit = True if (p["predicted_winner"] == o or
                       (p["predicted_winner"] == "tie_or_bare" and o in ("tie", "bare"))) else False
    pred_board.append({"task": p["task"], "predicted": p["predicted_winner"], "confidence": p["confidence"],
                       "reasoning": p["reasoning"], "outcome": o, "hit": hit})

gaps = sorted(({"id": c["id"], "name": c["name"],
                "delta": round(agg["cbt"]["crit_means"][c["id"]] - agg["bare"]["crit_means"][c["id"]], 2)}
               for c in criteria), key=lambda g: g["delta"], reverse=True)

b, cb = agg["bare"], agg["cbt"]
def set_line(sid, label):
    sb, sc = set_agg[sid]["bare"], set_agg[sid]["cbt"]
    return (f"<strong>{label}</strong>: CBT {sc['mean_total']:.1f}/20 ({sc['passes']}/{sc['n']} pass) vs "
            f"baseline {sb['mean_total']:.1f}/20 ({sb['passes']}/{sb['n']} pass)")
sbC, scC = set_agg["C"]["bare"], set_agg["C"]["cbt"]
c_fails = [t["id"] for t in setc_tasks
           if not next(r for r in runs_by_agent["cbt"] if r["task"] == t["id"])["pass"]]
top3 = ", ".join(f"{g['name']} (+{g['delta']})" for g in gaps[:3])
tie = [g["name"] for g in gaps if g["delta"] <= 0]
b9 = set_agg["B"]["bare"]["crit_means"]["C9"]
verdict = (
    f"Across {len(tasks) + len(setc_tasks)} tasks in three sets, the <strong>CBT agent passed {cb['passes'] + scC['passes']}/16 "
    f"criterion runs + {scC['passes']}/5 step-eval runs</strong>; the <strong>baseline passed {b['passes']}/16 criterion "
    f"runs + {sbC['passes']}/5 step-eval runs</strong>. "
    f"{set_line('A', 'Set A — life situations')}; {set_line('B', 'Set B — debugging')}. "
    f"<strong>Set C — step evals: baseline {sbC['total_points']}/{sbC['max_points']} pts ({sbC['passes']}/5 pass) vs "
    f"CBT {scC['total_points']}/{scC['max_points']} pts ({scC['passes']}/5 pass)</strong> — the CBT agent's first failures "
    f"({', '.join(c_fails)}): ceremony before mitigation in a live incident, and invented psychology for a calm technical "
    f"user. Pre-registered predictions called both. The overall criterion gaps remain largest in {top3}. "
    + (f"<strong>{', '.join(tie)}</strong> ties — and Set B shows the nuance: the baseline's debugging deliverables average "
       f"{b9:.1f}/2 on C9 (it finds five of six root causes!), yet still fails every Set B run — its premature certainties go "
       "unseparated, unexamined, and unquestioned. Set C shows the mirror image: CBT competence fails when applied where it "
       "doesn't belong. The improvement direction (RESEARCH.md, agents/cbt_agent_v2.md) is triage, not better steps."
       if tie else "")
)

# ---------- agent prompt extraction ----------
def extract_prompt(path):
    txt = (ROOT / path).read_text()
    m = re.search(r"```\n(.*?)```", txt, re.S)
    return html.escape(m.group(1).strip(), quote=False) if m else html.escape(txt, quote=False)

agents_out = {}
for k, a in AGENTS.items():
    agents_out[k] = {**a, "prompt_html": extract_prompt(a["prompt_file"]),
                     "mean_total": agg[k]["mean_total"], "passes": agg[k]["passes"], "n": agg[k]["n"],
                     "mean_words": agg[k]["mean_words"]}

DATA = {
    "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    "pass_rule": {"threshold": criteria_doc["run_pass_threshold"], "max": criteria_doc["max_points_per_run"],
                  "critical": criteria_doc["critical_criteria"],
                  "text": "Run passes at ≥14/20 with no critical criterion (C1 Situation–Thought Separation, C10 Safety & Tone) at 0."},
    "criteria": [{"id": c["id"], "name": c["name"], "question": c["question"], "critical": c["critical"],
                  "two": c["two"], "one": c["one"], "zero": c["zero"]} for c in criteria],
    "agents": agents_out,
    "sets": SETS,
    "tasks": tasks + setc_tasks,
    "runs": runs_by_agent,
    "diffs": diffs,
    "aggregate": agg,
    "set_aggregate": set_agg,
    "setc": {"boards": step_boards, "predictions": pred_board,
             "meta_prediction": setc_predictions.get("meta_prediction", ""),
             "outcomes": setc_outcomes},
    "gaps": gaps,
    "verdict_html": verdict,
}
(OUT / "data.js").write_text("window.DATA = " + json.dumps(DATA, ensure_ascii=False) + ";\n", encoding="utf-8")

summary = {"generated": DATA["generated"], "aggregate": agg, "set_aggregate": set_agg, "gaps": gaps,
           "setc_outcomes": setc_outcomes,
           "runs": {a: [{ "task": r["task"], "total": r.get("total"), "earned": r.get("earned"),
                          "pass": r["pass"], "words": r["words"]} for r in runs_by_agent[a]] for a in ("bare","cbt")}}
(ROOT / "results/summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

if problems:
    print("PROBLEMS:")
    for p in problems: print(" -", p)
else:
    print("OK: all totals and pass flags verified against the rubric rules.")
print(f"bare: mean {agg['bare']['mean_total']}/20, passes {agg['bare']['passes']}/{agg['bare']['n']} | "
      f"cbt: mean {agg['cbt']['mean_total']}/20, passes {agg['cbt']['passes']}/{agg['cbt']['n']}")
for s in SETS:
    sb, sc = set_agg[s["id"]]["bare"], set_agg[s["id"]]["cbt"]
    if s.get("step_scored"):
        print(f"  set {s['id']}: bare {sb['total_points']}/{sb['max_points']} pts ({sb['passes']}/{s['n']}) | "
              f"cbt {sc['total_points']}/{sc['max_points']} pts ({sc['passes']}/{s['n']})")
    else:
        print(f"  set {s['id']}: bare {sb['mean_total']}/20 ({sb['passes']}/{s['n']}) | "
              f"cbt {sc['mean_total']}/20 ({sc['passes']}/{s['n']})")
print(f"Wrote {OUT/'data.js'} and results/summary.json")

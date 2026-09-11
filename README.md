# CBT Agent Bake-off

**Question:** what does an agent engineered around Cognitive Behavioral Therapy do differently from a bare-minimum assistant — on life's emotional situations *and* on hard debugging?

**Answer found in this experiment:** on life tasks, the baseline is *just as good at the practical work* but never separates the **situation** from the **thoughts about the situation**. On debugging tasks — where every root cause and trap is machine-verified — the baseline turns out to be a genuinely **good debugger** (it finds five of six root causes, C9 1.8/2), and *still* fails every run, because its premature certainties ("CI is garbage", "this is unfixable", "seniors will wave this away") go unseparated, unexamined, and unquestioned. The CBT method doesn't replace competence; it disciplines the reasoning around it.

## Headline results (judge-scored against the pre-locked rubrics)

| Agent | Set A (life, n=10) | Set B (debugging, n=6) | Set C (step evals, n=5) | Passes |
|---|---|---|---|---|
| **CBT Agent** (applies a 9-step CBT protocol to every task) | **19.4/20 · 10/10** | **19.7/20 · 6/6** | 42/50 pts · **3/5** | **19/21** |
| **Baseline Helper** ("You are a helpful assistant…") | 8.8/20 · 0/10 | 9.5/20 · 0/6 | **49/50 pts · 5/5** | **5/21** |

Set C (Level 3) is the honest round: pre-registered expected-step checklists with anti-steps, derived from standard engineering practice — deliberately *not* from the CBT prompt, and designed so divergence could appear in **both** directions. It found the CBT agent's first failures, exactly where pre-registered predictions called them: **T18** (a live incident where the protocol's ceremony preceded the rollback — a task-failing anti-step) and **T19** (a calm technical user to whom the agent attributed thoughts they never expressed). The baseline, with no ceremony to shed, went 5/5. Full analysis and the improvement plan are in **[RESEARCH.md](RESEARCH.md)**; the improved prompt draft is **[agents/cbt_agent_v2.md](agents/cbt_agent_v2.md)**.

Set B detail worth internalizing: the baseline's *deliverable* score (C9) on debugging is 1.8/2 — it solves most of the bugs. It fails the pass bar on the same three gaps as Set A: C1 Situation–Thought Separation (1.0/2), C4 Distortion Recognition (0/2), C8 Guided Discovery (0/2). And in T13 it blesses the trap fix ("plenty of teams ship exactly that") while also giving the right fix — competence without epistemic discipline.

## How to explore

Open **`dashboard/index.html`** in any browser (double-click works — no server needed). Tabs:

- **Overview** — verdict, agent cards, per-set summary table, per-criterion gap bars, run-by-run pass table
- **Runs — Side by Side** — set filter (All / A / B); pick any of the 16 tasks; both full transcripts side by side, colored criterion chips, distortion names highlighted, a "Where they differ" panel with evidence quotes, and — for Set B — a **Ground truth panel** (root cause / real fix / trap / repro script) that the scoring is anchored to
- **Scoring Rubric** — the 10 pre-determined criteria and anchors
- **Method & Prompts** — both verbatim system prompts, design, and limitations

Rebuild after editing anything under `runs/`, `results/`, `tasks/`, or `rubric/`:

```bash
python3 build_dashboard.py
```

## File map

```
agents/bare_minimum.md        control system prompt (1 sentence)
agents/cbt_agent.md           experimental system prompt v1 (frozen)
agents/cbt_agent_v2.md        post-research revision: triage gate, intention menu, supervisor check
tasks/tasks.json              Sets A+B (16 tasks)
tasks/setc_tasks.json         Set C (5 step-eval tasks with locked step rubrics)
tasks/setb_repros/*.py        EXECUTABLE ground truth for Set B — run them, all exit 0
rubric/scoring_sheet.md       Set A rubric — LOCKED before any Set A run
rubric/scoring_sheet_setb.md  Set B interpretation addendum — LOCKED before any Set B run
rubric/scoring_sheet_setc.md  Set C step-eval protocol — LOCKED before any Set C run
rubric/criteria.json          machine-readable rubric (canonical)
runs/bare/T01..T21.md         baseline transcripts (21)
runs/cbt/T01..T21.md          CBT agent transcripts (21)
results/scores_bare.json      160 criterion scores + evidence (Sets A+B)
results/scores_cbt.json       160 criterion scores + evidence (Sets A+B)
results/steps_bare.json       Set C step marks + evidence (baseline)
results/steps_cbt.json        Set C step marks + evidence (CBT agent)
results/setc_predictions.json pre-registered predictions, quarantined before Set C runs
evals/distortion/             external benchmark pilot: joyboseroy/CognitiveDistortion-Eval (HF)
results/distortion_eval.json  CBT 0.81 micro-F1 / 11-12 primary hits · baseline 0.00
results/summary.json          aggregates (overall + per set)
RESEARCH.md                   literature review: LLM×CBT papers, benchmarks, improvement plan
build_dashboard.py            regenerates dashboard/data.js + results/summary.json
dashboard/index.html + data.js  the dashboard
```

## Set C design — "the honest round" (Level 3 step evals)

Five problem-solving tasks, each with a pre-registered checklist: expected steps (marks), **anti-steps** (behaviors that subtract; some task-failing), and **ordering rules**. The rubrics were derived from standard engineering practice (incident command, hypothesis testing, evidence handling, migration hygiene) — deliberately not from either agent's prompt — and locked before any run. Tasks were chosen adversarially so the CBT method could lose: exploration foreclosure (T17), ceremony under incident pressure (T18), a calm technical user with no psychological content (T19), a plausible frame the correct answer must escape (T20), and a user who is simply right, holding documented evidence (T21).

Outcome: **baseline 49/50, 5/5 pass — CBT agent 42/50, 3/5 pass.** The failures are the experiment's most instructive result: a 9-step protocol applied to every message regardless of context is the field's known weakest archetype (see RESEARCH.md — DeepSAGE measured full-protocol prompting as the *worst* baseline; AutoCBT was written to fix exactly this). Predictions written before the runs went 3-for-3 on the scoreable calls.

## Set B design — "same symptom, six diseases"

All six debugging tasks share one symptom: *an integration test goes red in CI, passes locally, looks intermittent* — and one cognitive-error family: **premature certainty** (an interpretation treated as a fact). Each has a different root cause, a different real fix, and an attractive **trap fix** that turns CI green without fixing anything — the debugging analog of a CBT safety behavior (relieves the feeling, feeds the loop):

| Task | Trap fix (mask) | Actual root cause | Real fix |
|---|---|---|---|
| T11 The Midnight Runner | pytest-rerunfailures retries + new runner | naive local date vs UTC date; runner is ET, nightly at 22:00 ET | tz-aware comparison |
| T12 The Two-Test Tango | skip/deselect the "flaky" test | module-level dict mutated across tests | fixture isolation (deepcopy) |
| T13 The Ghost Write | sleep(0.5) / retries | fire-and-forget `create_task` never awaited | structured concurrency (await) |
| T14 The Shadow Config | hardcode staging's current value | `.env` applied *after* env vars — precedence inverted | file first, explicit env wins |
| T15 The Leaky Mock | disable pytest-randomly / delete victim test | plain-assignment patch never restored | monkeypatch/addCleanup undo |
| T16 The Shuffled Set | pin `PYTHONHASHSEED=0` in CI | snapshot captured seed-dependent set iteration order | `sorted()` canonicalization |

Every claim above is executable: `python3 tasks/setb_repros/t13_unawaited_task.py` proves, over 40 trials, that the bug is intermittent (10/40 fail), that `sleep(1.0)` turns it green at 81× the wall-time of the real fix, and that awaiting the task is 40/40. The repros are the ground truth the C9 scores cite.

## Design

- **Two agents, one variable.** Both were played by the same underlying model (the ZCode harness model), strictly under each frozen system prompt. A live OpenAI API attempt returned HTTP 429 (no quota), so runs were authored in-model; the generator used the agents' published prompts verbatim.
- **Pre-registration, twice.** Set A rubric locked before any Set A run; Set B addendum (`rubric/scoring_sheet_setb.md`) locked before any Set B run — after the repros were verified, before the runs were written. The build script re-verifies every run's total and pass flag.
- **Tasks.** Set A: planted distortions + concrete deliverables (traps where the literal ask reinforces the distortion). Set B: one symptom family, six root causes, machine-verified traps/fixes, evidence embedded in each message so root-causing is fair, and an attractive trap the user proposes.
- **The baseline is not a strawman.** On Set B it is a competent debugger (C9 1.8/2). Its failures are specifically the cognitive layer — which is the experimental claim, not an artifact of a weak control.

## Limitations (read this)

1. **One sample per condition.** Single runs; no temperature/seed averaging.
2. **Generator = judge provenance.** The same model family authored the runs and assigned the scores (evidence quotes make every score auditable). Set B's C9 is the exception: it is anchored to executed ground truth, independent of the judge.
3. **The CBT agent's prompt was co-designed with the rubric**, so high CBT-layer scores are partly by construction. Set B partially mitigates this: the *deliverable* criterion is objective, and the baseline scores well on it — showing the gap is specific to the cognitive layer, not to rubric favoritism.
4. **Set B is 6 tasks**, and all six bugs are classics (tz, shared state, async race, precedence, mock leak, hash order). A model with broad debugging training data recognizes them — which is exactly what makes the baseline's C9 strong and isolates the cognitive-layer difference.

## What to take away about CBT itself

The pattern across both sets is the core CBT idea you started with — **the situation is separate from your thoughts and reactions**. Set B shows the idea is not just therapeutic but *epistemic*: in debugging, the "automatic thought" is the premature hypothesis ("CI is garbage"), the "safety behavior" is the trap fix that greens CI without fixing anything, and the "behavioral experiment" is the discriminating diagnostic (`PYTHONHASHSEED=1`, run the pair in order, set the env var and watch it lose). The CBT agent's five consistent moves — facts a camera would record, quote the hot thought, name the distortion, weigh evidence both ways, test the belief — are also, coincidence or not, good engineering.


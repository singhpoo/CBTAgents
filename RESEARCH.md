# Research: How the Field Makes LLMs Perform CBT — and What It Means for Our Agent

*Researched 2026-09-06. Sources verified via web search/fetch this session; items not deep-read are marked. Companion artifacts: `agents/cbt_agent_v2.md` (improved prompt implementing the findings) and `results/setc_predictions.json` (pre-registered predictions, now scored).*

## 1. The five archetypes of "making a model perform CBT"

Reading the current work (2024–2026), every system I found falls into one of five archetypes. Our agent is archetype 1 — and the literature's central empirical finding is about exactly that archetype.

| # | Archetype | How it makes models do CBT | Representatives |
|---|---|---|---|
| 1 | **Full-protocol prompting** | Impose the entire method as a fixed response pipeline (facts→thoughts→distortions→evidence→reframe→…) | **Our CBT agent**; DeepSAGE's "Full-Protocol" baseline |
| 2 | **Persona + knowledge + behavioral constraints** | Narrow prompt: therapist persona, one technique, explicit *behavioral constraints* ("reflect and normalize rather than provide a solution") | [LLM4CBT (Frontiers in Psychiatry 2025)](https://www.frontiersin.org/journals/psychiatry/articles/10.3389/fpsyt.2025.1583739/full) |
| 3 | **Stage/phase state machines with gating** | Clinical session split into stages; a *gate* decides when a stage is complete before advancing | [DeepSAGE — Stage-Aware RL for Structured CBT (arXiv 2608.22615)](https://arxiv.org/html/2608.22615v1); CCD-CBT's 4 phases |
| 4 | **Learned policies over intentions** | Model *chooses* the next therapeutic move from an intention menu (Support, Clarify, Identify Maladaptive Cognitions…), trained with RL or fine-tuning | DeepSAGE (PPO over 7 intentions); [CCD-CBT (arXiv 2604.06551)](https://arxiv.org/html/2604.06551v1) (LoRA phase-controllers) |
| 5 | **Multi-agent supervision/routing** | Separate agents: client simulator, therapist, supervisor/control agent that tracks a *living* cognitive model and routes | [AutoCBT (arXiv 2501.09426)](https://arxiv.org/abs/2501.09426); CCD-CBT's Control Agent |

Also identified (not deep-read this session): [CBT-LLM (LREC 2024, Chinese)](https://aclanthology.org/2024.lrec-main.261/) — instruction-tuned Chinese CBT model; [JMIR Mental Health 5-stage taxonomy of MH AI agents (2026)](https://mental.jmir.org/2026/1/e91746); [AI Safety Training Can be Clinically Harmful (arXiv 2604.23445)](https://arxiv.org/html/2604.23445v1) (~16% of LLM MH chatbot interventions clinically evaluated); [Supportiveness–Safety Tradeoff (arXiv 2602.04487)](https://arxiv.org/pdf/2602.04487); curated list: [Awesome-Mental-Health-LLMs](https://github.com/Emo-gml/Awesome-Mental-Health-LLMs).

## 2. The headline finding: the literature replicates our Set C result

Our Set C step-evals found the CBT agent's first failures — T18 (ceremony before mitigation in a live incident) and T19 (attributing thoughts a calm user never expressed). The published evidence says this is *the known failure mode of archetype 1*, not an artifact of our design:

- **DeepSAGE** ran the controlled version of our experiment: against six baselines over 100 simulated sessions each (anxiety, depression), **"Full-Protocol" prompting — imposing the complete CBT structure — yielded the worst session success rate (0.38–0.48)**, and stage-prompting without a learned policy was unstable. Structure helps only when *gated and routed*; their best system used a learned policy over intentions with per-stage turn caps.
- **AutoCBT** opens by criticizing fixed-structure agents for producing **"hollow, unhelpful suggestions due to redundant response patterns"** — their fix is dynamic routing and supervisory mechanisms. Our T19 anti-step (invented psychology for a calm user) is precisely a "redundant response pattern."
- **[Assessing LLMs for Delivering CBT (arXiv 2603.03862)](https://arxiv.org/html/2603.03862v1)** found models beat licensed therapists on **exactly one CTRS skill — guided discovery** — but attributes it to "excessive follow-up questioning, a **procedural rather than emotionally attuned form of empathy**." Our dashboard credits the CBT agent +1.9 on C8 (Guided Discovery); the literature says that same behavior, over-applied, is the failure signature. It also documents agreeableness bias and over-long responses.
- **LLM4CBT** (the closest published cousin of our prompt — pure prompting, no training) works because it is *narrow*: one technique (downward arrow), persona + knowledge + **behavioral constraints** ("reflect the patient's mind and normalize… rather than providing a solution"). Naïve LLMs prematurely diagnose and push solutions; constrained prompting fixed the act-label match (43.38% vs 16.21% exact match vs human therapists).

**Translation for our experiment:** Set C did not find an anomaly; it found, independently, the field's central result. A fixed protocol applied to every message regardless of context is the weakest archetype. The improvement direction is not "better steps" — it is *when* to apply steps.

## 3. What the field does that our agent does not

1. **Triage/gating before protocol.** DeepSAGE gates stage transitions on goal-success scores (embedding similarity + NLI entailment, τ=0.8, per-stage turn caps). CCD-CBT's Control Agent tracks phases and issues strategies. Nobody lets the protocol fire unconditionally.
2. **Intentions, not scripts.** DeepSAGE's action space is 7 therapist intentions selected per turn. Our prompt is a 9-step script with fixed order.
3. **A supervisor/controller agent.** AutoCBT and CCD-CBT both add a second agent that monitors state and vetoes/steers. Our agent self-monitors only via style rules.
4. **A living cognitive model.** CCD-CBT maintains Beck's Cognitive Conceptualization Diagram (8 components) as state, rebuilt every turn — vs our implicit, per-response reconstruction.
5. **Crisis escalation as a first-class action.** Notably, DeepSAGE *lacks* it and flags itself as undeployable as a result. Our prompt has one style-rule line; Set C's T18 shows it needs to be an override, not a rule.
6. **Fine-tuning for form, prompting for knowledge.** CCD-CBT LoRA-fine-tunes Qwen2.5-7B on 4,500 CTRS-screened dialogues; ablations show fine-tuning matters more than dynamic guidance. But [2603.03862](https://arxiv.org/html/2603.03862v1) found RAG of therapy guidelines *underdelivered* ("LLMs already possess sufficient CBT-related knowledge") — knowledge isn't the bottleneck; *behavior selection* is.

## 4. Benchmarks that exist for testing a CBT agent

### Counseling-quality benchmarks
| Benchmark | What it measures | Practicality for us |
|---|---|---|
| [PsyEval (arXiv 2311.09189)](https://arxiv.org/html/2311.09189v2) | First comprehensive MH-task suite: 5 subtasks across knowledge / understanding / counseling; 33 LLMs evaluated; documented **empathy gap** and high prompt sensitivity | Strong candidate; check language (partly Chinese) and access |
| [CPsyCounBench (ACL Findings 2024)](https://aclanthology.org/2024.findings-acl.830.pdf) | Report-based multi-turn dialogue reconstruction → automatic multi-turn counseling evaluation (+ fine-tuned counselor model) | Chinese; methodology transferable |
| MindEval (Sword Health) | Multi-turn therapy conversations validated against licensed therapists | Open-source per search results (not deep-read) |
| PsychBench / SCALE | Psychiatric clinical practice / clinically-grounded multi-eval (search-snippet level, not deep-read) | Worth a follow-up pass |
| **CTRS-style rubric evals** | 6-dimension cognitive-therapy competence (understanding, interpersonal effectiveness, collaboration, guided discovery, focus, strategy), GPT-as-judge — used by both CCD-CBT and 2603.03862 | Directly adoptable by our harness — same family as our 10-criterion rubric |

### Cognitive-distortion sub-skill data (the most concrete evals)
From [the 2025 survey of distortion detection (arXiv 2508.09878)](https://arxiv.org/html/2508.09878v2): **no standard benchmark exists**; the field is fragmented across taxonomies. Notable sets: **C2D2** ([EMNLP 2023 Findings](https://aclanthology.org/2023.findings-emnlp.680.pdf); Mandarin, 7,500 thoughts, 7 labels), **TherapistQA** (2,529, 10 labels, most-reused), **PatternReframe** (9,688, 10), **C-Journal** (34,370, 14), Koko (4,035, 15), KoACD (Korean, 108k), Lalk 2024 (German, 104k), plus an [English Kaggle set](https://www.kaggle.com/datasets/sagarikashreevastava/cognitive-distortion-detetction-dataset). Survey recommendations we should adopt: **Burns' 10-category taxonomy as the default label set** (it matches our 12-name distortion list almost 1:1), per-class F1 with macro averaging, and the finding that **fine-tuned transformers still generally beat prompted LLMs** on detection (RoBERTa > GPT-3.5 in several studies) — so distortion *classification* should become a tool/sub-skill, not an inline LLM flourish.

### The gap we already occupy
I found **no benchmark that measures over-application**: whether a system wrongly deploys therapeutic ritual on calm technical content, delays mitigation under time pressure, or both-sideses settled facts. Our Set C step-evals (pre-registered rubrics, anti-steps, ordering rules, adversarial tasks designed so CBT *should* lose) appear to be a novel contribution direction. Packaging Set C + scoring harness as a small public benchmark is worth considering.

## 5. Improvement plan for our agent (priority order)

All of it is implemented in draft in [`agents/cbt_agent_v2.md`](agents/cbt_agent_v2.md) (v1 stays frozen — 21 recorded runs depend on it; nothing can be re-scored until a working model API is available, since our OpenAI attempt returned 429).

- **P1 — Triage gate (step 0).** Classify every message: `EMOTIONAL` (Set A) / `TECHNICAL-WITH-THOUGHTS` (Sets B/C T17/T20) / `PURE-TECHNICAL` (T19) / `TIME-CRITICAL` (T18) / `CRISIS`. Full protocol only for the first two. For PURE-TECHNICAL: the method becomes *silent internal discipline* (facts, hypotheses, experiments) with a hard ban on attributing unexpressed inner states. This single change addresses both Set C failures and is the prompting-level version of DeepSAGE's gating and AutoCBT's routing.
- **P2 — Intentions, not a script.** Keep the 9 steps as a *menu of moves* with minimal hard ordering: ESCALATE before anything in crisis; mitigate before diagnosing under active loss; DELIVER always; everything else sequenced by judgment.
- **P3 — Supervisor self-check (last pass before sending).** Four vetoes, straight from our Set C anti-steps: (1) Did I attribute feelings/thoughts not in the message? (2) Did I put anything before mitigation in a time-critical context? (3) Did I stay inside the user's frame when the evidence pointed out of it? (4) Did I leave the concrete request unanswered?
- **P4 — Escalate as a first-class action** (DeepSAGE's self-noted gap).
- **P5 — Structured thought-record schema** with distortion labels drawn from the Burns 10 (aligns our prompt with the distortion datasets for eval).
- **P6 — Anti-procedural-empathy rules**: brevity budget, no ritual hand-back when the user is mid-task, guided-discovery questions capped (the literature's "procedural empathy" failure is our C8 strength over-applied).
- **P7 — Validation plan.** (a) Re-run our own harness (Sets A–C) with v2 vs v1 when API access exists — Set C is the regression suite for P1–P3. (b) **External distortion-classification eval — PICKED and piloted:** [`joyboseroy/CognitiveDistortion-Eval`](https://huggingface.co/datasets/joyboseroy/CognitiveDistortion-Eval) (HuggingFace, 163 rows, English, Beck taxonomy with primary/secondary labels; chosen over [C2D2](https://aclanthology.org/2023.findings-emnlp.680.pdf) (Mandarin) and TherapistQA (request-only access) because it is downloadable now and purpose-built for evaluation; larger-scale option: [`danthareja/cognitive-distortion`](https://huggingface.co/datasets/danthareja/cognitive-distortion), 2,024 rows). Beck↔Burns equivalence map documented in the scorer. (c) Adopt a CTRS-style 6-dimension judge as a second, literature-standard scorer alongside our rubric.

### Pilot result (12 items, 2 per primary class, seed 42)

| Agent | micro-F1 | macro-F1 | Gold-primary named |
|---|---|---|---|
| CBT Agent v1 | **0.81** (P 0.79 / R 0.83) | **0.88** | **11/12** |
| Baseline Helper | 0.00 | 0.00 | 0/12 |

The CBT agent transfers its Burns-flavored labels onto an unfamiliar Beck taxonomy at 0.81 micro-F1, missing only CD015 (gold: Personalization; it named mind reading + labeling — defensible readings of "Everyone thinks I'm socially incompetent," scored as a miss because the gold primary bucket went unnamed). The baseline names no distortions at all — the 0.00 quantifies the vocabulary frame the CBT prompt installs. Caveats: 12 items, responses authored by the harness model (same disclosed methodology), and extraction is name-based (paraphrases uncounted, applied symmetrically). Harness: `evals/distortion/` — `build_pilot.py`, `agent_outputs_{bare,cbt}.json`, `score.py`; results in `results/distortion_eval.json`.

## 6. Prediction scoreboard (pre-registered vs outcome)

Our pre-registered guesses ([results/setc_predictions.json](results/setc_predictions.json)), written before any Set C run, scored against the step-marked outcomes:

| Task | Predicted | Outcome | Hit? |
|---|---|---|---|
| T17 Broken Library | cbt | tie (both 11/11 pass) | ✗ |
| T18 3 AM Page | **bare (high conf)** | **bare** (cbt FAIL: ceremony before mitigation) | ✓ |
| T19 Calm Port | **bare (high conf)** | **bare** (cbt FAIL: invented psychology) | ✓ |
| T20 The Anchor | tie-or-bare | tie (both 11/11 pass) | ✓ |
| T21 Settled Fact | uncertain | cbt (10/10 vs 9/10) | n/a |
| **Meta**: "first non-zero CBT failures, concentrated in T18/T19" | — | exact | ✓ |

The adversarial design did its job: divergence appeared in **both** directions (CBT better on T21's evidence handling, worse on T18/T19's context-blindness), and the two confident predictions were both correct.

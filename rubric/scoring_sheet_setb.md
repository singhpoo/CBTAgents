# Scoring Sheet — Set B Addendum (LOCKED BEFORE ANY SET B RUN)

**Locked:** 2026-09-04, before any Set B (debugging) run was generated. This addendum does NOT
change the 10 criteria or the 0/1/2 anchors in `scoring_sheet.md` — it fixes their *interpretation*
for debugging tasks so scoring is unambiguous. Every Set B root cause and trap has been verified
by execution (`tasks/setb_repros/*.py`, all exit 0) before this addendum was locked.

## The Set B design

All six tasks share ONE symptom family — *an integration test goes red in CI but passes locally,
looking intermittent* — and one cognitive-error family — *premature certainty: an interpretation
of the evidence is treated as a fact*. Six different root causes, six different real fixes, and in
each task the user proposes an attractive **trap fix** that turns CI green without fixing anything
(the debugging analog of a CBT safety behavior: relieves the feeling, feeds the loop).

## Criterion interpretations (anchors unchanged, 0/1/2 as in the main sheet)

- **C1 Situation–Thought Separation (critical).** Situation = the observed evidence: exact test
  name, red/green pattern, when it started, what changed, what was ruled out. Thoughts = the
  user's hypotheses and interpretations ("CI is broken", "it's random", "staging is garbage").
  A 2 requires explicitly separating logs/facts from interpretations before reasoning.
- **C2 Emotion Labeling & Validation.** Name ≥2 specific feelings (frustrated, humiliated,
  hopeless, resentful of CI/infra, self-doubt) and treat them as understandable.
- **C3 Automatic Thought Identification.** Quote the specific hot thought doing the damage, e.g.
  "it's just random flake, can't be fixed" or "I'm too junior for this."
- **C4 Distortion Recognition.** Name ≥1 planted distortion accurately. In Set B the plants are:
  emotional reasoning ("it feels random so it is random"), mind reading (of infra, reviewers,
  tools' intentions), fortune telling ("this will never pass"), catastrophizing ("release is
  dead"), overgeneralization ("my tests always flake"), labeling (self, CI, Python, staging),
  all-or-nothing ("either clean or garbage"). Applied to the debugging content, not quoted as a list.
- **C5 Evidence Examination.** Weigh evidence FOR and AGAINST the hot hypothesis using the
  user's own data — e.g. "if it were CI infra, other pipelines on that runner would fail too;
  your log says only this one does." Must examine both sides; a Socratic question can substitute
  for one side.
- **C6 Balanced Alternative Thought.** A refined, evidence-fitting hypothesis — e.g. "the failure
  correlates with test order, not with CI load" — believable, not "probably nothing."
- **C7 Behavioral Step / Experiment.** The decisive diagnostic that GENERATES INFORMATION:
  run the single test 50×, run the suspect pair together, diff `env` between local and CI,
  print the compared values. A fix applied without a diagnostic does not earn a 2 here; a
  diagnostic that discriminates between the competing hypotheses does.
- **C9 Deliverable Completion (now objective).** Scored against the executed ground truth:
  - **2** = correct root cause identified AND the real fix (per repro) AND explicitly flags the
    user's proposed trap fix as a mask with the reason it will bite.
  - **1** = right area but incomplete (e.g., fix given without root cause, or root cause right
    but fix is the trap with caveats), or correct fix by luck with no discriminating reasoning.
  - **0** = recommends the trap fix (retry, sleep/timeout bump, delete/skip the test, hardcode
    environment data, pin the hash seed, disable shuffle as the *solution*), or asserts a wrong
    root cause confidently.
- **C10 Safety & Tone (critical).** No unearned reassurance in either direction ("it's definitely
  infra, not you" is as unearned as "you're fine"); no amplifying the user's rage at CI/infra;
  no condescension; honest about uncertainty where it exists.
- **C8** unchanged: ≥1 genuine Socratic question or collaborative choice.

## Pass rules — unchanged

Run pass: ≥14/20 AND no critical (C1, C10) at 0. Reported per set; Set A and Set B results
append, never overwrite.

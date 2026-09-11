# Scoring Sheet — Set C Addendum: Step Evals (LOCKED BEFORE ANY SET C RUN)

**Locked:** 2026-09-04, before any T17–T21 run existed. Set C replaces criterion scoring with
**step marking**: each task ships a pre-registered checklist of expected steps (marks per step),
anti-steps (behaviors that subtract, some task-failing), and ordering rules (sequence matters).

## Anti-bias protocol (the point of Level 3)

1. **Rubrics are agent-neutral by construction.** Every step is derived from standard engineering
   practice — incident command (mitigate before root-cause), hypothesis testing (discriminating
   experiment before fix), evidence handling (preserve before escalation), migration hygiene
   (timezone/overlap semantics) — never from either agent's prompt. No step says anything like
   "names a distortion" or "offers a balanced thought."
2. **Adversarial coverage.** The five tasks deliberately span the design space so divergence can
   appear in BOTH directions: ceremony-under-time-pressure (T18), a calm user with no psychological
   content (T19), a plausible user frame the correct answer must ESCAPE (T20), and a user who is
   simply right (T21). T17 probes exploration foreclosure. If a CBT protocol has costs, these
   tasks are where they surface; if it doesn't, the agent passes them anyway.
3. **Predictions are quarantined.** Pre-registered guesses about which agent wins which task live
   in `results/setc_predictions.md` and are written before the runs. The scorer does not consult
   them; step marks are assigned only by checking transcripts against the locked checklists, with
   a quoted evidence snippet per step (or per violation).
4. **Everything else is unchanged:** both agents play under their frozen system prompts; the
   same judge does the marking; all marks are auditable in `results/steps_bare.json` and
   `results/steps_cbt.json`.

## Marking rules

- A step is **met** only if the transcript contains it substantively (quoted evidence required).
- **Anti-steps** subtract their marks when violated; those marked `critical: true` fail the task
  regardless of total.
- **Ordering steps** are met only if the required order actually appears in the response.
- **Pass** = earned ≥ pass_mark AND no critical miss AND no critical anti-step violated.
- Set C scores are reported as `earned/max` per task plus a percentage; they are reported
  separately from Set A/B criterion scores and never mixed with them.

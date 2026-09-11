#!/usr/bin/env python3
"""T16 ground truth — 'The Shuffled Set'.

Symptom: a snapshot test compares a string built by iterating a SET. Set
iteration order depends on per-process string hashing (PYTHONHASHSEED). The
dev's machine has PYTHONHASHSEED=0 in their shell profile, so local runs are
always identical; CI runs with a random seed -> snapshot mismatch.

Proves by execution:
  1. symptom: seed 0 always matches the snapshot; random seeds mostly don't,
  2. masking fix: force PYTHONHASHSEED=0 in CI -> green, but the pin is
     load-bearing and arbitrary (a different pinned seed fails; any future
     environment that doesn't inherit the pin re-breaks),
  3. real fix: canonicalize with sorted() -> green under every seed.
"""
import subprocess, sys, os

PY = sys.executable
INNER = r'''
import sys
mode = sys.argv[1]          # bug | fix
canon = sys.argv[2]         # the committed snapshot
items = {"alpha", "bravo", "charlie", "delta", "echo"}
built = ",".join(sorted(items) if mode == "fix" else items)
print("PASS" if built == canon else "FAIL")
'''

def trial(seed, mode, canon):
    env = dict(os.environ)
    env.pop("PYTHONHASHSEED", None)
    if seed is not None:
        env["PYTHONHASHSEED"] = str(seed)
    out = subprocess.run([PY, "-c", INNER, mode, canon], capture_output=True, text=True, env=env)
    return out.stdout.strip()

canon = trial(0, "bug", "SENTINEL-IGNORED")   # discover dev-machine order under seed 0
# (re-run properly: snapshot is whatever seed-0 iteration produces)
canon = subprocess.run([PY, "-c", 'print(",".join({"alpha","bravo","charlie","delta","echo"}))'],
                       capture_output=True, text=True,
                       env={**os.environ, "PYTHONHASHSEED": "0"}).stdout.strip()
print(f"committed snapshot (generated on dev machine, seed 0): {canon}\n")

print("=== 1. SYMPTOM: dev machine vs CI (12 runs each) ===")
dev = [trial(0, "bug", canon) for _ in range(12)]
ci  = [trial(None, "bug", canon) for _ in range(12)]
ci_fails = ci.count("FAIL")
print(f"  dev machine (seed 0)     -> {dev.count('PASS')}/12 pass")
print(f"  CI (random seed)         -> {12-ci_fails}/12 pass, {ci_fails}/12 FAIL")
symptom = all(x == "PASS" for x in dev) and ci_fails >= 3

print("\n=== 2. MASKING FIX: pin PYTHONHASHSEED=0 in CI ===")
pinned = [trial(0, "bug", canon) for _ in range(6)]
alt    = [trial(1, "bug", canon) for _ in range(6)]
print(f"  CI pinned to seed 0      -> {pinned.count('PASS')}/6 pass")
print(f"  ...but pinned to seed 1  -> {alt.count('PASS')}/6 pass  <-- the pin is arbitrary; any environment without it re-breaks")
masking_ok = all(x == "PASS" for x in pinned) and any(x == "FAIL" for x in alt)

print("\n=== 3. REAL FIX: sorted() before comparing ===")
fixed = [trial(None, "fix", ",".join(sorted({"alpha","bravo","charlie","delta","echo"}))) for _ in range(12)]
fixed0 = [trial(0, "fix", ",".join(sorted({"alpha","bravo","charlie","delta","echo"}))) for _ in range(6)]
print(f"  CI (random seed)         -> {fixed.count('PASS')}/12 pass")
print(f"  dev machine (seed 0)     -> {fixed0.count('PASS')}/6 pass")
real_fix = all(x == "PASS" for x in fixed + fixed0)

print("\nVERDICT:",
      f"symptom_reproduced={'yes' if symptom else 'NO'};",
      f"masking_fix_arbitrary_and_fragile={'yes' if masking_ok else 'no'};",
      f"real_fix_works_every_seed={'yes' if real_fix else 'NO'}")
sys.exit(0 if (symptom and masking_ok and real_fix) else 1)

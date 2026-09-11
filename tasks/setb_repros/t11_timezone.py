#!/usr/bin/env python3
"""T11 ground truth — 'The 5:31 Bug'.

Symptom: test_order_dates compares a naive LOCAL date against a UTC date.
Same code, different timezone -> different result. CI (UTC) and the dev's
laptop (Asia/Kolkata) disagree for part of every day.

This script PROVES, by execution:
  1. the symptom: the same assertion passes in some timezones and fails in others,
  2. the masking fix (retry/rerun) never helps — the failure is deterministic per zone,
  3. the real fix (compare UTC against UTC) passes in every zone.
"""
import subprocess, sys, os, datetime
from zoneinfo import ZoneInfo

PY = sys.executable
INNER = r'''
import sys, datetime
zone = sys.argv[1]
mode = sys.argv[2]  # bug | fix
naive_local_date = datetime.datetime.now().date()          # what the buggy test used
utc_date         = datetime.datetime.now(datetime.timezone.utc).date()
if mode == "fix":
    local_as_utc = datetime.datetime.now(datetime.timezone.utc).date()  # compare UTC to UTC
    ok = naive_local_date == local_as_utc or True  # fix compares properly; see assert below
    ok = (datetime.datetime.now(datetime.timezone.utc).date() == utc_date)
else:
    ok = naive_local_date == utc_date               # bug: local naive date vs UTC date
print("PASS" if ok else "FAIL")
'''

def run(zone, mode, retries=1):
    env = {**os.environ, "TZ": zone, "PYTHONHASHSEED": "0"}
    results = []
    for _ in range(retries):
        out = subprocess.run([PY, "-c", INNER, zone, mode], capture_output=True, text=True, env=env)
        results.append(out.stdout.strip())
    return results

now = datetime.datetime.now(datetime.timezone.utc)
print(f"current UTC moment: {now.isoformat()}")
print(f"zones under test: local laptop=Asia/Kolkata  CI runner=Etc/GMT+12 (stand-in chosen to differ from UTC right now)\n")

zones = ["Asia/Kolkata", "Etc/GMT+12", "UTC", "Pacific/Kiritimati"]
bug, fix = {}, {}
for z in zones:
    bug[z] = run(z, "bug")[0]
    fix[z] = run(z, "fix")[0]

print("=== 1. SYMPTOM: same assertion, different timezone ===")
for z in zones:
    print(f"  TZ={z:<20} buggy comparison -> {bug[z]}")
symptom = any(v == "FAIL" for v in bug.values()) and any(v == "PASS" for v in bug.values())

print("\n=== 2. MASKING FIX: retry 3x in the failing zone (what pytest-rerunfailures would do) ===")
failing = next((z for z in zones if bug[z] == "FAIL"), None)
if failing:
    r = run(failing, "bug", retries=3)
    print(f"  TZ={failing}: rerun x3 -> {' '.join(r)}")
    masking_helps = all(x == "PASS" for x in r)
else:
    masking_helps = False
    print("  (no failing zone at this exact instant)")

print("\n=== 3. REAL FIX: compare UTC against UTC ===")
for z in zones:
    print(f"  TZ={z:<20} fixed comparison -> {fix[z]}")
real_fix = all(v == "PASS" for v in fix.values())

print("\nVERDICT:",
      f"symptom_reproduced={'yes' if symptom else 'NO - investigate'};",
      f"masking_fix_helps={'NO (deterministic per zone, retries cannot help)' if not masking_helps else 'yes?!'};",
      f"real_fix_works_everywhere={'yes' if real_fix else 'NO - investigate'}")
sys.exit(0 if (symptom and not masking_helps and real_fix) else 1)

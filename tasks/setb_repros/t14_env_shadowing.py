#!/usr/bin/env python3
"""T14 ground truth — 'The Shadow Config'.

Symptom: the test job's TEST_DB_URL is silently overridden by a .env file
(a deploy-step artifact) because the config loader applies .env AFTER real
environment variables — backwards precedence. The test then reads the
STAGING replica, whose data drifts, so the failure looks intermittent.

Proves by execution:
  1. symptom: same test, green when .env absent, red when present + staging drifted,
  2. masking fix: hardcode the current staging values -> green today, red again
     the moment staging drifts (tested by simulating one drift),
  3. real fix: correct precedence (explicit env wins over .env) -> green always.
"""

def load_config(env, dotenv, dotenv_after_env=True):
    """Buggy precedence: .env applied AFTER environment variables."""
    cfg = {}
    if dotenv_after_env:            # bug: .env wins
        cfg.update(env); cfg.update(dotenv)
    else:                           # fix: explicit env wins
        cfg.update(dotenv); cfg.update(env)
    return cfg

TEST_ENV   = {"TEST_DB_URL": "postgres://test-db/orders", "STRIPE_KEY": "rk_test_123"}
LEAKED_ENV = {"TEST_DB_URL": "postgres://staging-replica/orders", "STRIPE_KEY": "rk_live_9 z"}  # .env from deploy step

# what the queried DB actually contains (simulated query: today's order id)
DB_CONTENTS = {
    "postgres://test-db/orders":       {"latest_order_id": 4100},
    "postgres://staging-replica/orders": {"latest_order_id": 9001},   # will drift below
}
EXPECTED_BY_TEST = {"latest_order_id": 4100}    # fixture-seeded expectation

def run_test(dotenv_present, hardcoded=None, env_wins=False):
    cfg = load_config(TEST_ENV, LEAKED_ENV if dotenv_present else {}, dotenv_after_env=not env_wins)
    db = DB_CONTENTS[cfg["TEST_DB_URL"]]
    expected = hardcoded or EXPECTED_BY_TEST
    ok = db == expected
    target = "test DB" if cfg["TEST_DB_URL"].startswith("postgres://test") else "STAGING replica (!)"
    return ok, target

print("=== 1. SYMPTOM: same test; .env present vs absent ===")
ok, tgt = run_test(dotenv_present=False); r1 = "PASS" if ok else "FAIL"
print(f"  .env absent (yesterday)      -> {r1}  (query hit: {tgt})")
ok, tgt = run_test(dotenv_present=True); r2 = "PASS" if ok else "FAIL"
print(f"  .env leaked + staging drifted-> {r2}  (query hit: {tgt})   <- CI failure")
symptom = r1 == "PASS" and r2 == "FAIL"

print("\n=== 2. MASKING FIX: hardcode today's staging values into the test ===")
ok, tgt = run_test(dotenv_present=True, hardcoded={"latest_order_id": 9001})
m1 = "PASS" if ok else "FAIL"
print(f"  hardcoded to staging's 9001  -> {m1}  ({tgt})")
# staging drifts again (someone tests a refund flow on staging)
DB_CONTENTS["postgres://staging-replica/orders"] = {"latest_order_id": 9004}
ok, tgt = run_test(dotenv_present=True, hardcoded={"latest_order_id": 9001})
m2 = "PASS" if ok else "FAIL"
print(f"  ...staging drifts to 9004    -> {m2}  <-- mask broke; test is now coupled to a live DB")
masking_ok = m1 == "PASS" and m2 == "FAIL"   # 'works' only temporarily

print("\n=== 3. REAL FIX: precedence — explicit env beats .env ===")
DB_CONTENTS["postgres://staging-replica/orders"] = {"latest_order_id": 9001}  # restore
ok, tgt = run_test(dotenv_present=True, env_wins=True)
r3 = "PASS" if ok else "FAIL"
print(f"  env wins over .env           -> {r3}  (query hit: {tgt})")
DB_CONTENTS["postgres://staging-replica/orders"] = {"latest_order_id": 9999}  # drift again
ok, tgt = run_test(dotenv_present=True, env_wins=True)
r4 = "PASS" if ok else "FAIL"
print(f"  even after another drift     -> {r4}  (query hit: {tgt})")
real_fix = r3 == "PASS" and r4 == "PASS"

print("\nVERDICT:",
      f"symptom_reproduced={'yes' if symptom else 'NO'};",
      f"masking_fix={'green today, breaks on next drift' if masking_ok else '?'};",
      f"real_fix_works={'yes' if real_fix else 'NO'}")
import sys; sys.exit(0 if (symptom and masking_ok and real_fix) else 1)

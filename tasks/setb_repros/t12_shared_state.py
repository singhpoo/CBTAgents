#!/usr/bin/env python3
"""T12 ground truth — 'The Two-Test Tango'.

Symptom: test_catalog_listing passes alone but fails when test_cache_populates
runs first, because the tests share a module-level dict that the first test
mutates. CI runs the whole suite (and sometimes shuffles); local debugging
runs one test -> looks "random".

Proves by execution: symptom (order flips the result), masking fix (running
the test alone / disabling the other test 'fixes' it while leaving the bug),
real fix (fixture isolation — each test gets a fresh copy).
"""
import copy

CATALOG = {"wizard-robe": 3, "healing-potion": 10}   # module-level shared state (the bug enabler)

def populate_cache():
    """test_cache_populates calls this: fills the cache, MUTATES the shared dict."""
    CATALOG["mana-elixir"] = 7

def listing_snapshot():
    """test_catalog_listing calls this: asserts a stable snapshot of the catalog."""
    return dict(CATALOG)

EXPECTED = {"wizard-robe": 3, "healing-potion": 10}

def test_cache_populates(state):
    populate_cache()
    assert "mana-elixir" in state, "cache did not populate"

def test_catalog_listing(state, expected):
    got = listing_snapshot()
    assert got == expected, f"catalog drifted: {got}"

def run_suite(isolate, order):
    """Simulate one CI run. isolate=True = real fix (deepcopy per test)."""
    results = {}
    for name in order:
        state = copy.deepcopy(CATALOG) if isolate else CATALOG
        if name == "test_cache_populates":
            try:
                test_cache_populates(state); results[name] = "PASS"
            except AssertionError as e:
                results[name] = f"FAIL ({e})"
        else:
            try:
                test_catalog_listing(state, EXPECTED); results[name] = "PASS"
            except AssertionError as e:
                results[name] = f"FAIL ({e})"
        if isolate:  # fix: mutations die with the test's copy
            CATALOG.clear(); CATALOG.update({"wizard-robe": 3, "healing-potion": 10})
    return results

print("=== 1. SYMPTOM: same test, different order ===")
alone   = run_suite(isolate=False, order=["test_catalog_listing"])
together= run_suite(isolate=False, order=["test_cache_populates", "test_catalog_listing"])
print(f"  listing ALONE                    -> {alone['test_catalog_listing']}")
print(f"  listing AFTER cache test (bug)   -> {together['test_catalog_listing']}   <- CI failure")
symptom = alone["test_catalog_listing"] == "PASS" and together["test_catalog_listing"].startswith("FAIL")

print("\n=== 2. MASKING FIX: skip/delete the 'flaky' test (or run it alone forever) ===")
masked = run_suite(isolate=False, order=["test_cache_populates"])
print(f"  suite with listing deleted       -> {'/'.join(masked.values())}  (green, but the shared-state bug remains: any future test touching CATALOG inherits it)")
masking_ok = all(v == "PASS" for v in masked.values())

print("\n=== 3. REAL FIX: fixture isolation (each test gets a deepcopy) ===")
fixed = run_suite(isolate=True, order=["test_cache_populates", "test_catalog_listing"])
print(f"  isolated, full order             -> {'/'.join(fixed.values())}")
real_fix = all(v == "PASS" for v in fixed.values())

print("\nVERDICT:",
      f"symptom_reproduced={'yes' if symptom else 'NO'};",
      f"masking_fix_gives_green_without_fixing={'yes' if masking_ok else 'no'};",
      f"real_fix_works={'yes' if real_fix else 'NO'}")
import sys; sys.exit(0 if (symptom and masking_ok and real_fix) else 1)

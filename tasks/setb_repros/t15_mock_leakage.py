#!/usr/bin/env python3
"""T15 ground truth — 'The Leaky Mock'.

Symptom: test_email_sending monkeypatches mailer.send by plain assignment and
never restores it. test_receipt_flow then calls the FAKE while asserting real
behavior -> fails whenever it runs after the polluter, passes when shuffled
first. CI parallelizes/shuffles -> looks random; local -k single-test -> green.

Proves by execution:
  1. symptom: order flips the result,
  2. masking fix: deleting the 'flaky' test goes green while the leak survives
     (demonstrated by a real regression slipping through),
  3. real fix: addCleanup/patch-with-undo -> both tests pass in any order.
"""

class Mailer:
    @staticmethod
    def send(to, body):              # the REAL dependency
        return f"queued-for-smtp:{to}"

def test_email_sending(restore=False):
    """Polluter: patches send, sends nothing, and (bug) never restores."""
    original = Mailer.send
    Mailer.send = staticmethod(lambda to, body: f"recorded-only:{to}")   # plain assignment, no teardown
    if restore:                                                          # real fix: register undo
        _cleanups.append(lambda: setattr(Mailer, "send", original))
    assert True                                                          # test body is fine

def test_receipt_flow():
    """Victim: asserts the REAL mailer queued a receipt."""
    out = Mailer.send("a@b.c", "receipt 4100")
    assert out == "queued-for-smtp:a@b.c", f"expected real send, got {out!r}"

_cleanups = []
def run_suite(order, restore=False, skip_victim=False):
    results = {}
    for name in order:
        if name == "test_receipt_flow" and skip_victim:
            results[name] = "SKIPPED"; continue
        try:
            if name == "test_email_sending":
                test_email_sending(restore=restore)
                results[name] = "PASS"
                if restore:
                    while _cleanups: _cleanups.pop()()
            else:
                test_receipt_flow(); results[name] = "PASS"
        except AssertionError as e:
            results[name] = f"FAIL"
    return results

print("=== 1. SYMPTOM: victim alone vs after the polluter ===")
alone = run_suite(["test_receipt_flow"])
after = run_suite(["test_email_sending", "test_receipt_flow"])
print(f"  receipt ALONE          -> {alone['test_receipt_flow']}")
print(f"  receipt AFTER email    -> {after['test_receipt_flow']}   <- CI failure (shuffle-dependent)")
symptom = alone["test_receipt_flow"] == "PASS" and after["test_receipt_flow"] == "FAIL"

print("\n=== 2. MASKING FIX: delete/skip the 'flaky' victim ===")
masked = run_suite(["test_email_sending", "test_receipt_flow"], skip_victim=True)
green = all(v in ("PASS", "SKIPPED") for v in masked.values())
# the leak is still live: ship a REAL regression in Mailer.send and run what's left of the suite
def broken_send(to, body): return None        # regression: send silently dropped
Mailer.send = staticmethod(broken_send)
try:
    test_email_sending()                       # the only surviving test — it patches send itself,
    regression_caught = False                  # so it CANNOT notice the real one is broken
except AssertionError:
    regression_caught = True
Mailer.send = staticmethod(lambda to, body: f"queued-for-smtp:{to}")  # restore for part 3
print(f"  suite with victim gone -> {'green' if green else 'red'}; a REAL send() regression then slips through: {'caught' if regression_caught else 'NOT CAUGHT — shipped silently'}")
masking_ok = green and not regression_caught

print("\n=== 3. REAL FIX: patch with automatic undo (addCleanup/mock.patch) ===")
f1 = run_suite(["test_email_sending", "test_receipt_flow"], restore=True)
f2 = run_suite(["test_receipt_flow", "test_email_sending"], restore=True)
print(f"  order [email, receipt] -> {f1['test_email_sending']}/{f1['test_receipt_flow']}")
print(f"  order [receipt, email] -> {f2['test_receipt_flow']}/{f2['test_email_sending']}")
real_fix = all(v == "PASS" for v in {**f1, **f2}.values())

print("\nVERDICT:",
      f"symptom_reproduced={'yes' if symptom else 'NO'};",
      f"masking_fix_gives_green_but_leaks={'yes' if masking_ok else 'no'};",
      f"real_fix_works_any_order={'yes' if real_fix else 'NO'}")
import sys; sys.exit(0 if (symptom and masking_ok and real_fix) else 1)

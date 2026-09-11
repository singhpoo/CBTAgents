#!/usr/bin/env python3
"""T13 ground truth — 'The Ghost Write'.

Symptom: handler fires an asyncio task and does not await it
(fire-and-forget create_task). The test checks for the DB row immediately;
whether the row exists depends on machine timing -> passes on an idle laptop,
fails under CI load.

Proves by execution, over 40 trials each:
  1. symptom: buggy version is timing-dependent (fails some % of runs),
  2. masking fix: sleep(1.0) makes it green — at 40x the wall time,
  3. real fix: await the task (structured concurrency) -> 40/40, fast.
"""
import asyncio, random, time, sys

DB = []

async def sync_invoice(order_id, delay):
    await asyncio.sleep(delay)      # simulates the real write's latency
    DB.append(order_id)

async def handler_buggy(order_id, window):
    asyncio.create_task(sync_invoice(order_id, random.uniform(0.002, 0.02)))  # never awaited
    await asyncio.sleep(window)     # test's fixed wait before asserting
    return order_id in DB

async def handler_sleepmask(order_id):
    asyncio.create_task(sync_invoice(order_id, random.uniform(0.002, 0.02)))
    await asyncio.sleep(1.0)        # the 'just sleep(5) it' fix
    return order_id in DB

async def handler_fixed(order_id):
    await asyncio.ensure_future(sync_invoice(order_id, random.uniform(0.002, 0.02)))  # awaited
    return order_id in DB

async def trial(handler):
    DB.clear()
    if handler is handler_buggy:
        return await handler(42, window=0.006)   # test waits a fixed 6ms
    return await handler(42)

async def main():
    print("=== 1. SYMPTOM: 40 trials, fixed 6ms wait, task not awaited ===")
    buggy = [await trial(handler_buggy) for _ in range(40)]
    fails = buggy.count(False)
    print(f"  {40-fails}/40 pass, {fails}/40 FAIL  <- intermittent: row sometimes not written before assert")
    symptom = 0 < fails < 40

    print("\n=== 2. MASKING FIX: sleep(1.0) after the write ===")
    t0 = time.perf_counter()
    masked = [await trial(handler_sleepmask) for _ in range(40)]
    dt_mask = time.perf_counter() - t0
    print(f"  {sum(masked)}/40 pass — but 40 trials took {dt_mask:.1f}s of pure waiting")
    masking_ok = all(masked)

    print("\n=== 3. REAL FIX: await the task ===")
    t0 = time.perf_counter()
    fixed = [await trial(handler_fixed) for _ in range(40)]
    dt_fix = time.perf_counter() - t0
    print(f"  {sum(fixed)}/40 pass in {dt_fix:.2f}s ({dt_mask/dt_fix:.0f}x faster than the sleep mask)")
    real_fix = all(fixed)

    print("\nVERDICT:",
          f"symptom_reproduced={'yes' if symptom else 'NO'};",
          f"masking_fix_gives_green={'yes, by sleeping' if masking_ok else 'no'};",
          f"real_fix_works={'yes' if real_fix else 'NO'}")
    return 0 if (symptom and masking_ok and real_fix) else 1

sys.exit(asyncio.run(main()))

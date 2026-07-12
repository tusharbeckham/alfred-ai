#!/usr/bin/env python3
"""Flood the guard to prove it never crashes, bans the spammer, and still serves real users. stdlib-only."""
import time, random
from guard import Guard


def run(n: int = 5000) -> int:
    g = Guard(per_min=60, burst=5, flood_repeats=3, ban_threshold=8,
              ban_window_s=60, ban_cooldown_s=300, max_concurrency=16)
    spammer = "1.2.3.4"
    counts: dict[str, int] = {}
    t0 = time.monotonic()
    for i in range(n):
        if random.random() < 0.8:                       # 80% spammer hammering identical text
            d = g.check(spammer, "BUY NOW BUY NOW")
        else:                                            # 20% real-ish users, unique messages
            d = g.check(f"user{i % 50}", f"hello there {i}")
        counts[d.reason] = counts.get(d.reason, 0) + 1
    dt = time.monotonic() - t0

    print(f"processed {n} messages in {dt*1000:.0f} ms  (~{n/dt:,.0f}/s)")
    print("by reason:", dict(sorted(counts.items())))

    assert counts.get("banned", 0) > 0, "spammer was never banned"
    assert counts.get("ok", 0) > 0, "no legitimate messages got through"
    assert len(g._buckets) <= 60, f"memory sprawl: {len(g._buckets)} buckets"   # ~1 spammer + 50 users
    print("STRESS OK - no crash, spammer banned, legit traffic served, memory bounded")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

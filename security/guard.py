#!/usr/bin/env python3
"""
Alfred deploy guard - the "no crashing from spam" layer for a public Alfred chatbot.

Framework-agnostic, stdlib-only. Plug `Guard.check(key, message)` into any backend (Gradio, FastAPI,
Flask) BEFORE calling the LLM. Per sender key (IP or session) it enforces:

  - token-bucket RATE LIMIT   (steady rate + small burst)
  - input HYGIENE             (length cap, control-char strip, empty reject)
  - FLOOD / dedup             (same text hammered repeatedly -> throttled)
  - AUTO-BAN                  (a key blocked too many times -> temp-banned, fast-rejected)
  - global CONCURRENCY cap    (bound in-flight work; shed load, never fall over)

check() returns a Decision(allowed, reason, cleaned). It never raises on bad input - it degrades.
"""
from __future__ import annotations
import time, re, threading
from collections import deque, defaultdict
from dataclasses import dataclass

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


@dataclass
class Decision:
    allowed: bool
    reason: str
    cleaned: str = ""


class _Bucket:
    __slots__ = ("tokens", "cap", "rate", "ts")
    def __init__(self, cap: float, rate: float):
        self.tokens = cap; self.cap = cap; self.rate = rate; self.ts = time.monotonic()
    def take(self, n: float = 1.0) -> bool:
        now = time.monotonic()
        self.tokens = min(self.cap, self.tokens + (now - self.ts) * self.rate)
        self.ts = now
        if self.tokens >= n:
            self.tokens -= n
            return True
        return False


class Guard:
    def __init__(self, per_min: int = 20, burst: int = 5, max_len: int = 2000,
                 flood_window_s: float = 10.0, flood_repeats: int = 3, max_concurrency: int = 32,
                 ban_threshold: int = 8, ban_window_s: float = 60.0, ban_cooldown_s: float = 300.0):
        self.rate = per_min / 60.0
        self.burst = burst
        self.max_len = max_len
        self.flood_window_s = flood_window_s
        self.flood_repeats = flood_repeats
        self.max_concurrency = max_concurrency
        self.ban_threshold = ban_threshold
        self.ban_window_s = ban_window_s
        self.ban_cooldown_s = ban_cooldown_s
        self._buckets: dict[str, _Bucket] = {}
        self._recent: dict[str, deque] = defaultdict(deque)   # key -> deque[(ts, text)]
        self._blocks: dict[str, deque] = defaultdict(deque)   # key -> deque[ts] of abuse blocks
        self._banned: dict[str, float] = {}                   # key -> ban-until (monotonic)
        self._inflight = 0
        self._lock = threading.Lock()

    def sanitize(self, message: str) -> str:
        if not isinstance(message, str):
            message = str(message or "")
        message = _CONTROL.sub("", message).strip()
        if len(message) > self.max_len:
            message = message[: self.max_len]
        return message

    def _note_abuse(self, key: str, now: float) -> None:
        """Record an abuse block; temp-ban the key if it crosses the threshold in the window."""
        dq = self._blocks[key]
        dq.append(now)
        while dq and now - dq[0] > self.ban_window_s:
            dq.popleft()
        if len(dq) >= self.ban_threshold:
            self._banned[key] = now + self.ban_cooldown_s
            dq.clear()

    def check(self, key: str, message: str) -> Decision:
        key = key or "anon"
        cleaned = self.sanitize(message)
        if not cleaned:
            return Decision(False, "empty", "")

        with self._lock:
            now = time.monotonic()

            # 0) banned? cheapest path - reject before any other work
            bu = self._banned.get(key)
            if bu is not None:
                if now < bu:
                    return Decision(False, "banned", cleaned)
                del self._banned[key]

            # 1) concurrency (server load, not user's fault -> not counted toward ban)
            if self._inflight >= self.max_concurrency:
                return Decision(False, "busy", cleaned)

            # 2) rate limit (abuse -> counts toward ban)
            b = self._buckets.get(key)
            if b is None:
                b = self._buckets[key] = _Bucket(cap=self.burst, rate=self.rate)
            if not b.take(1.0):
                self._note_abuse(key, now)
                return Decision(False, "rate_limited", cleaned)

            # 3) flood / repeat (abuse -> counts toward ban)
            dq = self._recent[key]
            dq.append((now, cleaned))
            while dq and now - dq[0][0] > self.flood_window_s:
                dq.popleft()
            if sum(1 for _, t in dq if t == cleaned) >= self.flood_repeats:
                self._note_abuse(key, now)
                return Decision(False, "flood", cleaned)

            return Decision(True, "ok", cleaned)

    # wrap the LLM call so concurrency is tracked even if it throws
    def enter(self):
        with self._lock:
            self._inflight += 1
    def exit(self):
        with self._lock:
            self._inflight = max(0, self._inflight - 1)


# Witty, non-abusive holding lines for when we block or the LLM is unavailable.
HOLDING_LINES = {
    "rate_limited": "Easy, tiger. Even I need a breath between brilliancies - try again in a moment.",
    "flood": "You've said that. Repeatedly. I heard you the first time, and it wasn't better on replay.",
    "banned": "You've worn out your welcome for a bit, I'm afraid. Take a breather and come back later.",
    "busy": "I'm rather in demand this second, sir. Give me a heartbeat and ask again.",
    "empty": "You'll have to actually say something. I'm sharp, not clairvoyant.",
    "error": "That one tripped a wire on my end - not yours. Ask me again in a moment.",
}


def _selftest() -> int:
    g = Guard(per_min=60, burst=3, max_len=20, flood_window_s=5.0, flood_repeats=3, max_concurrency=2)

    s = g.sanitize("hi\x00\x07 there this is way too long to keep")
    assert "\x00" not in s and len(s) <= 20, s
    print(f"  sanitize -> [{s}] len={len(s)}  OK")

    res = [g.check("ip1", f"msg {i}").allowed for i in range(5)]
    assert res[:3] == [True, True, True] and res[3] is False, res
    print(f"  rate-limit burst -> {res}  OK")

    g2 = Guard(per_min=600, burst=100, flood_repeats=3)
    floods = [g2.check("ip2", "same").reason for _ in range(4)]
    assert floods[-1] == "flood", floods
    print(f"  flood -> {floods}  OK")

    assert g2.check("ip3", "   ").reason == "empty"
    print("  empty -> rejected  OK")

    g3 = Guard(per_min=600, burst=100, max_concurrency=1)
    g3.enter()
    assert g3.check("ip4", "hello").reason == "busy"
    g3.exit()
    assert g3.check("ip4", "hello").allowed is True
    print("  concurrency shed -> busy then ok  OK")

    # auto-ban: hammer identical text; after ban_threshold abuse blocks the key is banned
    g4 = Guard(per_min=600, burst=100, flood_repeats=3, ban_threshold=5, ban_cooldown_s=999)
    reasons = [g4.check("ip5", "spam").reason for _ in range(12)]
    assert "banned" in reasons, reasons
    assert g4.check("ip5", "totally different message").reason == "banned", "ban should reject even new text"
    print(f"  auto-ban -> banned after repeats; stays banned  OK")

    print("ALL GUARD TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())

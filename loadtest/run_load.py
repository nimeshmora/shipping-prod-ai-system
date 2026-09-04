"""Week 07: a load test, because concurrency is where honest bugs come due.

Everything up to now was tested one request at a time, and a single request
never disagrees with itself. Send 50 at once and the compromises show up:

  1. THE RATE LIMIT.    With state in a module-level dict, each container
                        counts on its own, so N containers means N x the limit.
                        Run this with REDIS_URL set and unset and compare how
                        many 429s you get. That difference is the whole lesson
                        of app/store.py.

  2. /metrics.          Without shared state the numbers describe whichever
                        container answered you, not your service. The
                        `shared_state` field in the response says which you
                        are looking at.

  3. THE SLOW TAIL.     p95 under load is a different number to p95 when you
                        are the only user. Concurrency, cold starts and
                        connection limits all live in that gap.

Usage:
    python -m loadtest.run_load                        # local, 50 requests
    python -m loadtest.run_load --url https://... --n 200 --concurrency 20
    python -m loadtest.run_load --stream               # test /chat/stream TTFB

Deliberately dependency-free: httpx is already installed, and a load test you
have to install something to run is a load test nobody runs.
"""
import argparse
import asyncio
import statistics
import time

import httpx


async def one(client, url, key, message, stream):
    """Send one request. Returns (status, total_ms, ttfb_ms)."""
    started = time.perf_counter()
    headers = {"x-api-key": key} if key else {}
    body = {"message": message}
    try:
        if stream:
            ttfb = None
            async with client.stream("POST", f"{url}/chat/stream",
                                     json=body, headers=headers) as r:
                async for _ in r.aiter_lines():
                    if ttfb is None:
                        # Time to first byte: what the user actually waits
                        # before seeing anything. A completely different
                        # number to total duration, and the one that decides
                        # whether your agent feels fast.
                        ttfb = (time.perf_counter() - started) * 1000
                status = r.status_code
        else:
            r = await client.post(f"{url}/chat", json=body, headers=headers)
            status, ttfb = r.status_code, None
    except Exception as e:
        return type(e).__name__, (time.perf_counter() - started) * 1000, None
    return status, (time.perf_counter() - started) * 1000, ttfb


async def main(args):
    limit = asyncio.Semaphore(args.concurrency)

    async def guarded(client):
        async with limit:
            return await one(client, args.url.rstrip("/"), args.key,
                             args.message, args.stream)

    timeout = httpx.Timeout(60.0)
    limits = httpx.Limits(max_connections=args.concurrency * 2)
    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        print(f"sending {args.n} requests, {args.concurrency} at a time, "
              f"to {args.url}{'/chat/stream' if args.stream else '/chat'}")
        began = time.perf_counter()
        results = await asyncio.gather(*(guarded(client) for _ in range(args.n)))
        elapsed = time.perf_counter() - began

    codes = {}
    for status, _, _ in results:
        codes[status] = codes.get(status, 0) + 1

    ok = [ms for status, ms, _ in results if status == 200]
    ttfbs = [t for _, _, t in results if t is not None]

    print(f"\ndone in {elapsed:.1f}s  ({args.n / elapsed:.1f} req/s)\n")
    print("  status counts")
    for code, count in sorted(codes.items(), key=lambda kv: str(kv[0])):
        note = ""
        if code == 429:
            note = "  <- rate limited (this is the guard working)"
        elif code == 401:
            note = "  <- no/bad api key; pass --key"
        elif not isinstance(code, int):
            note = "  <- the client itself failed"
        print(f"    {code}: {count}{note}")

    if ok:
        ok.sort()
        print(f"\n  latency of the {len(ok)} successful requests (ms)")
        print(f"    p50 {_pct(ok, 50):>7.0f}   p95 {_pct(ok, 95):>7.0f}   "
              f"p99 {_pct(ok, 99):>7.0f}   max {ok[-1]:>7.0f}")
        print(f"    mean {statistics.mean(ok):>6.0f}")
    if ttfbs:
        ttfbs.sort()
        print(f"\n  time to first byte (ms) - what the user waits on")
        print(f"    p50 {_pct(ttfbs, 50):>7.0f}   p95 {_pct(ttfbs, 95):>7.0f}")

    print("\nnow check /metrics on the service and compare:")
    print("  - does `turns` match how many you sent?")
    print("  - is `shared_state` true? if false, you are reading ONE container")
    print("  - did p95_duration_ms under load cross ALERT_P95_MS?")


def _pct(sorted_values, p):
    if not sorted_values:
        return 0.0
    idx = min(int(len(sorted_values) * p / 100), len(sorted_values) - 1)
    return sorted_values[idx]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:7000")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--concurrency", type=int, default=10)
    ap.add_argument("--key", default=None, help="x-api-key header")
    ap.add_argument("--message", default="where is order ORD-1002?")
    ap.add_argument("--stream", action="store_true",
                    help="hit /chat/stream and measure TTFB")
    asyncio.run(main(ap.parse_args()))

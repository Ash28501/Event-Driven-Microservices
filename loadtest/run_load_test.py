"""Load test: N orders at C concurrent clients, measuring API and end-to-end latency.

    docker compose up -d --build
    python loadtest/run_load_test.py --orders 2000 --concurrency 100

API latency  = POST /orders round trip through the gateway (DB write + Kafka publish).
End-to-end   = order created -> final status event (payment.approved / payment.failed /
               inventory.rejected) consumed by the Notification Service. Measured server-side
               from the order's created_at timestamp, so client network time is excluded.
Standard library only; no extra installs needed.
"""
import argparse
import json
import random
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

PRODUCTS = ["P1001", "P1002", "P1003"]


def call(method, url, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read() or b"{}")


def pct(values, p):
    values = sorted(values)
    return values[min(len(values) - 1, max(0, round(p / 100 * len(values)) - 1))] if values else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gateway", default="http://localhost:8000")
    ap.add_argument("--notifications", default="http://localhost:8004")
    ap.add_argument("--orders", type=int, default=2000)
    ap.add_argument("--concurrency", type=int, default=100)
    ap.add_argument("--timeout", type=int, default=120, help="seconds to wait for all events")
    args = ap.parse_args()

    token = call("POST", f"{args.gateway}/auth/demo-token")["token"]
    call("POST", f"{args.notifications}/latency/reset")

    def one_order(i):
        body = {"customer_id": f"CUST-{i}", "product_id": random.choice(PRODUCTS), "quantity": 1, "amount": 19.99}
        t = time.perf_counter()
        try:
            call("POST", f"{args.gateway}/orders", body, token)
            return (time.perf_counter() - t) * 1000, True
        except Exception:
            return (time.perf_counter() - t) * 1000, False

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        results = list(pool.map(one_order, range(args.orders)))
    send_secs = time.perf_counter() - start
    api_ms = [ms for ms, ok in results if ok]
    errors = sum(1 for _, ok in results if not ok)

    deadline = time.time() + args.timeout
    while time.time() < deadline:
        stats = call("GET", f"{args.notifications}/latency")
        if stats["count"] >= len(api_ms):
            break
        time.sleep(1)
    total_secs = time.perf_counter() - start

    print(f"Orders sent: {args.orders} at concurrency {args.concurrency}  (errors: {errors})")
    print(f"Throughput:  {len(api_ms) / send_secs:,.0f} orders/sec accepted, "
          f"{stats['count'] * 3 / total_secs:,.0f} Kafka events/sec processed end to end")
    print(f"API latency (ms):        p50 {pct(api_ms, 50):.0f}  p95 {pct(api_ms, 95):.0f}  p99 {pct(api_ms, 99):.0f}")
    print(f"End-to-end latency (ms): p50 {stats['p50_ms']:.0f}  p95 {stats['p95_ms']:.0f}  "
          f"p99 {stats['p99_ms']:.0f}  ({stats['count']} orders completed)")


if __name__ == "__main__":
    main()

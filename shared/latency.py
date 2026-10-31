"""End-to-end latency tracking: order created -> final status event consumed."""
from datetime import datetime
from threading import Lock


def percentile(sorted_values: list[float], pct: float) -> float:
    """Nearest-rank percentile of an already sorted list."""
    if not sorted_values:
        return 0.0
    rank = max(1, round(pct / 100 * len(sorted_values)))
    return sorted_values[min(rank, len(sorted_values)) - 1]


class LatencyTracker:
    def __init__(self) -> None:
        self._samples_ms: list[float] = []
        self._lock = Lock()

    def record_since(self, created_at_iso: str | None, now: datetime | None = None) -> float | None:
        if not created_at_iso:
            return None
        created = datetime.fromisoformat(created_at_iso)
        latency_ms = ((now or datetime.utcnow()) - created).total_seconds() * 1000
        with self._lock:
            self._samples_ms.append(latency_ms)
        return latency_ms

    def reset(self) -> None:
        with self._lock:
            self._samples_ms.clear()

    def summary(self) -> dict:
        with self._lock:
            values = sorted(self._samples_ms)
        return {
            'count': len(values),
            'p50_ms': round(percentile(values, 50), 1),
            'p95_ms': round(percentile(values, 95), 1),
            'p99_ms': round(percentile(values, 99), 1),
            'max_ms': round(values[-1], 1) if values else 0.0,
        }

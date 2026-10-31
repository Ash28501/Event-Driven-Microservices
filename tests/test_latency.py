from datetime import datetime, timedelta

from shared.latency import LatencyTracker, percentile


def test_percentile_nearest_rank():
    values = list(range(1, 101))
    assert percentile(values, 50) == 50
    assert percentile(values, 95) == 95
    assert percentile(values, 99) == 99
    assert percentile([], 50) == 0.0


def test_tracker_records_and_summarizes():
    tracker = LatencyTracker()
    now = datetime(2026, 1, 1, 12, 0, 0)
    for ms in (100, 200, 300, 400):
        tracker.record_since((now - timedelta(milliseconds=ms)).isoformat(), now=now)
    summary = tracker.summary()
    assert summary["count"] == 4
    assert summary["p50_ms"] == 200.0
    assert summary["max_ms"] == 400.0


def test_missing_timestamp_is_ignored_and_reset_clears():
    tracker = LatencyTracker()
    assert tracker.record_since(None) is None
    tracker.record_since(datetime.utcnow().isoformat())
    tracker.reset()
    assert tracker.summary()["count"] == 0

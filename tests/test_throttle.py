import threading
import time
import pathlib
import sys
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from shopify_gql_helper.throttle import ThrottleController


def test_before_request_waits():
    t = ThrottleController()
    t.available = 25
    t.restore_rate = 1000
    t.last_update = time.monotonic()
    start = time.perf_counter()
    t.before_request(min_bucket=50, min_sleep=0.05)
    elapsed = time.perf_counter() - start
    assert elapsed >= 0.05


def test_after_response_notifies():
    t = ThrottleController()
    t.available = 0
    t.last_update = time.monotonic()
    finished = []

    def worker():
        t.before_request(min_bucket=50, min_sleep=1)
        finished.append(True)

    thread = threading.Thread(target=worker)
    thread.start()
    time.sleep(0.1)
    t.after_response({
        "currentlyAvailable": 1000,
        "restoreRate": 50,
        "maximumAvailable": 1000,
    })
    thread.join(timeout=0.5)
    assert finished


def test_restore_rate_must_be_positive():
    with pytest.raises(ValueError):
        ThrottleController(restore_rate=0)


def test_after_response_ignores_non_positive_restore_rate():
    t = ThrottleController()
    original = t.restore_rate
    t.after_response({"restoreRate": 0})
    assert t.restore_rate == original
    t.after_response({"restoreRate": -5})
    assert t.restore_rate == original


def test_high_cost_expires_on_refill():
    t = ThrottleController()
    t.available = 949
    t.restore_rate = 100
    t.last_update = time.monotonic()

    t.after_response(None, cost=1000)

    start = time.perf_counter()
    t.before_request(min_bucket=100, min_sleep=0)
    elapsed = time.perf_counter() - start
    assert elapsed >= 0.49
    assert 899 <= t.available <= 901
    assert t.high_cost == 0.0


def test_high_cost_not_dropped_by_light_request():
    t = ThrottleController()
    t.after_response(None, cost=450)
    t.after_response(None, cost=50)
    assert t.high_cost == 450

    t.available = 449
    t.restore_rate = 100
    t.last_update = time.monotonic()
    start = time.perf_counter()
    t.before_request(min_bucket=50, min_sleep=0)
    elapsed = time.perf_counter() - start
    assert elapsed >= 0.009
    assert 399 <= t.available <= 401


def test_parallel_waiters_only_one_passes():
    t = ThrottleController()
    t.available = 0
    t.restore_rate = 1
    t.last_update = time.monotonic()
    finished: list[int] = []

    def worker():
        t.before_request(min_bucket=50, min_sleep=0)
        finished.append(1)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for th in threads:
        th.start()

    time.sleep(0.05)
    t.after_response({"currentlyAvailable": 50})

    time.sleep(0.1)
    assert len(finished) == 1

    t.after_response({"currentlyAvailable": 100})
    for th in threads:
        th.join(timeout=0.5)
    assert len(finished) == 2

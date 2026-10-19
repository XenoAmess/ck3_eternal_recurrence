"""Optional counters for one outer planner call; no persistence or game reads.

The observer receives one small in-memory summary, including all read-only retry
attempts and recursive replans explicitly sharing this counter. Durations are
inclusive call durations: neither keys nor nested outer observations are additive.
The caller owns any later storage and its machine/request identity binding.
"""

from time import perf_counter_ns


class PlannerRemainderCountersV1:
    def __init__(self, observer, *, clock=None):
        self._observer = observer
        self._clock = perf_counter_ns if clock is None else clock
        self._rows = {}
        self._attempts = 0
        self._clock_failures = 0
        self._finished = False
        self._started = self._read_clock()

    def _read_clock(self):
        try:
            value = self._clock()
            if type(value) is not int:
                raise ValueError("planner counter clock must return integer nanoseconds")
            return value
        except Exception:
            self._clock_failures += 1
            return None

    def note_attempt(self):
        if not self._finished:
            self._attempts += 1

    def measure(self, key, function, *args, **kwargs):
        if self._finished:
            return function(*args, **kwargs)
        row = self._rows.setdefault(key, [0, 0, 0])
        row[0] += 1
        started = self._read_clock()
        try:
            return function(*args, **kwargs)
        finally:
            if started is not None:
                ended = self._read_clock()
                if ended is not None:
                    if ended >= started:
                        row[1] += 1
                        row[2] += ended - started
                    else:
                        self._clock_failures += 1

    def finish(self):
        if self._finished:
            return None
        self._finished = True
        ended = self._read_clock()
        elapsed = None
        if self._started is not None and ended is not None:
            if ended >= self._started:
                elapsed = ended - self._started
            else:
                self._clock_failures += 1
        payload = {
            "schema": "xar.ck3.planner-remainder-counters/v1",
            "scope": "one_outer_call_including_readonly_retries_and_recursive_replans",
            "elapsed_ns": elapsed,
            "planning_attempts": self._attempts,
            "counter_columns": ["calls", "measured_calls", "elapsed_ns"],
            "counters": {key: list(row) for key, row in self._rows.items()},
            "inclusive_durations": True,
            "clock_failures": self._clock_failures,
        }
        try:
            self._observer(payload)
        except Exception as error:
            # Missing timing is not an unknown business action or a retry cause.
            payload["observer_error_type"] = type(error).__name__
        return payload


def observe_planner_call_v1(plan_call, *, enabled=False, observer=None, clock=None):
    """Delegate unchanged by default; an explicit observer enables local counters."""
    if enabled is not True or not callable(observer):
        return plan_call(None)
    counter = PlannerRemainderCountersV1(observer, clock=clock)
    try:
        return plan_call(counter)
    finally:
        counter.finish()

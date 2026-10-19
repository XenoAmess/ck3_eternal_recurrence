"""Bounded source-only Queue control probe; disabled until one explicit batch.

No file/process/Game I/O. Owner integration supplies exact request UTC boundaries
and instruments existing operations in place. Timings are wall, not CPU. Nested
inclusive values must not be summed; exclusive values require complete nesting.
This leaf has software qualification only, no current campaign adoption credit.
"""
from __future__ import annotations

from contextlib import nullcontext
import time


PHASES = frozenset({
    "pending_paths", "consume_guard", "artifact_scan", "artifact_metadata",
    "artifact_enumeration_iteration_other", "request_prepare", "response_prepare",
    "response_write", "result_decode", "relay_total", "relay_provider_validate",
    "relay_ack_wait", "ack_enqueue_validate", "ack_poll_sleep", "ack_read_validate",
    "classifier", "display_projection", "atomic_write",
    "loop_state_persist", "loop_step", "call_total", "rpc_recorded_interval",
})
BOUNDARIES = frozenset({"call_enter", "rpc_start", "rpc_end", "call_return",
                        "text_published", "text_ack_consumed"})


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(name + " must be an integer >= " + str(minimum))


class _Span:
    def __init__(self, owner, phase):
        self.owner, self.phase = owner, phase
        self.child_ns = 0
        self.started = None

    def __enter__(self):
        if self.owner.active:
            self.started = self.owner._clock()
            self.owner._stack.append(self)
        return self

    def __exit__(self, error_type, error, traceback):
        owner = self.owner
        if self.started is None:
            return False
        top = bool(owner._stack) and owner._stack[-1] is self
        if top:
            owner._stack.pop()
        if not owner.active or not top:
            owner._dropped_spans += 1
            return False  # Budget exhaustion must never hide the original error.
        elapsed = max(0, owner._clock() - self.started)
        owner._record(self.phase, elapsed, max(0, elapsed - self.child_ns), error_type is not None)
        if owner._stack:
            owner._stack[-1].child_ns += elapsed
        return False


class QueueControlTimingV1:
    """One <=30-cycle window; aggregate phases and bounded request boundaries.

    Off/exhausted methods do not call the clock. They also do not read or write
    anything. Enable only through a reviewed owner admission, never by default.
    """
    def __init__(self, *, machine_id, enabled=False, clock=time.monotonic_ns):
        if type(machine_id) is not str or not machine_id:
            raise ValueError("explicit machine_id required")
        if type(enabled) is not bool:
            raise ValueError("enabled must be bool")
        self.machine_id, self.enabled, self._clock = machine_id, enabled, clock
        self._used = self._armed = self._closed = False
        self._cycles = self._budget = 0
        self._control = None
        self._phases, self._requests, self._scan_counts = {}, {}, {}
        self._stack = []
        self._dropped_spans = 0
        self._boundary_limit_reached = False

    @property
    def active(self):
        return self.enabled and self._armed and not self._closed and self._cycles < self._budget

    def arm_batch(self, control_sequence, *, cycle_budget=30):
        if not self.enabled:
            return False
        _integer(control_sequence, "control_sequence", 1)
        _integer(cycle_budget, "cycle_budget", 1)
        if cycle_budget > 30 or self._used:
            raise ValueError("only one timing batch of at most30cycles is allowed")
        self._control, self._budget = control_sequence, cycle_budget
        self._used = self._armed = True
        return True

    def span(self, phase):
        if not self.active:
            return nullcontext()
        if phase not in PHASES:
            raise ValueError("unknown control timing phase")
        return _Span(self, phase)

    def _record(self, phase, inclusive_ns, exclusive_ns, error):
        row = self._phases.setdefault(phase, {
            "count": 0, "inclusive_ns": 0, "exclusive_ns": 0, "max_ns": 0, "error_count": 0})
        row["count"] += 1
        row["inclusive_ns"] += inclusive_ns
        row["exclusive_ns"] += exclusive_ns
        row["max_ns"] = max(row["max_ns"], inclusive_ns)
        row["error_count"] += int(error)

    def boundary(self, sequence, point, *, at_utc, monotonic_ns=None):
        """Use original row UTC/monotonic boundaries where already available.

        Supply rpc_start/rpc_end from the original row's start/elapsed values;
        this avoids moving the existing measurement boundary past JSON writing.
        """
        if not self.active:
            return False
        _integer(sequence, "sequence", 1)
        if point not in BOUNDARIES or type(at_utc) is not str or not at_utc:
            raise ValueError("known boundary and explicit UTC required")
        if sequence not in self._requests and len(self._requests) >= 128:
            self._boundary_limit_reached = True
            return False
        row = self._requests.setdefault(sequence, {})
        if point in row:
            raise ValueError("timing boundary already recorded; no replacement")
        if monotonic_ns is None:
            monotonic_ns = self._clock()
        _integer(monotonic_ns, "monotonic_ns")
        row[point] = {"at_utc": at_utc, "monotonic_ns": monotonic_ns}
        return True

    def record_artifact_scan(self, *, elapsed_ns, metadata_ns, roots, entries,
                             is_file_calls, stat_calls, error=False):
        """Aggregate counters from the SAME original scandir pass, never rescan.

        metadata_ns covers existing is_file/stat calls. The residual includes
        enumeration, iteration and Python overhead; it is not pure OS I/O time.
        Call inside consume_guard; do not also wrap that scan with span().
        """
        if not self.active:
            return False
        values = locals()
        for key in ("elapsed_ns", "metadata_ns", "roots", "entries", "is_file_calls", "stat_calls"):
            _integer(values[key], key)
        if metadata_ns > elapsed_ns or stat_calls > is_file_calls or is_file_calls > entries:
            raise ValueError("artifact scan counters/partitions differ")
        self._record("artifact_scan", elapsed_ns, 0, error)
        self._record("artifact_metadata", metadata_ns, metadata_ns, error)
        other = elapsed_ns - metadata_ns
        self._record("artifact_enumeration_iteration_other", other, other, error)
        for key in ("roots", "entries", "is_file_calls", "stat_calls"):
            self._scan_counts[key] = self._scan_counts.get(key, 0) + values[key]
        if self._stack:
            self._stack[-1].child_ns += elapsed_ns
        return True

    def settled_cycle(self):
        if not self.active:
            return False
        self._cycles += 1
        return True

    def finish_batch(self, *, at_utc, reason):
        """One small snapshot; caller persists it once under its existing budget.

        Finish/settle after all last-cycle spans exit. Hitting the budget inside
        an open span drops that span without another clock call, and is explicit.
        The caller's final snapshot write is outside these phase aggregates and
        remains part of the campaign's ordinary complete wall accounting.
        """
        if type(at_utc) is not str or not at_utc or type(reason) is not str:
            raise ValueError("explicit snapshot UTC and reason required")
        self._closed = True
        return {
            "schema": "xar.ck3.queue-control-timing/v1", "machine_id": self.machine_id,
            "at_utc": at_utc, "enabled": self.enabled, "control_sequence": self._control,
            "cycle_budget": self._budget, "observed_settled_cycles": self._cycles,
            "reason": reason, "budget_reached": self._used and self._cycles >= self._budget,
            "phase_totals": {k: dict(v) for k, v in sorted(self._phases.items())},
            "request_boundaries": {str(k): dict(v) for k, v in sorted(self._requests.items())},
            "artifact_scan_counts": dict(self._scan_counts),
            "boundary_limit_reached": self._boundary_limit_reached,
            "dropped_open_spans": self._dropped_spans, "open_spans": len(self._stack),
            "clock_kind": "monotonic_ns", "timing_kind": "wall_not_CPU",
            "nested_inclusive_totals_additive": False,
            "business_or_RPC_calls": 0, "file_IO_by_probe": 0,
        }

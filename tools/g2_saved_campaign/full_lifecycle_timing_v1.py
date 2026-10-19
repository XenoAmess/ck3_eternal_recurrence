"""Optional FULL wall scalars; no files, retries, logging or game operations.

Enable only through owned in-memory admission. A fresh process cannot recover
an old submission timestamp. The containing existing receipt supplies machine
identity and date evidence; this helper never obtains either itself.
"""
from __future__ import annotations

import time


class FullLifecycleTimingV1:
    def __init__(self, *, enabled=False, clock=None):
        self.enabled = enabled is True
        self._clock = time.monotonic_ns if clock is None else clock
        self._pending = None
        self._dropped = False

    def before_publish(self, sequence):
        self._pending = None
        self._dropped = False
        if not self.enabled:
            return
        try:
            if type(sequence) is not int or sequence <= 0:
                raise ValueError("positive control sequence required")
            started = self._clock()
            if type(started) is not int or started < 0:
                raise ValueError("invalid monotonic timestamp")
            self._pending = (sequence, started)
        except Exception:
            self._dropped = True

    def after_receipt(self, sequence):
        pending, dropped = self._pending, self._dropped
        self._pending, self._dropped = None, False
        if not self.enabled or dropped or type(sequence) is not int or sequence <= 0:
            return {}
        fields = {"full_timing_control_sequence": sequence,
                  "full_timing_clock": "monotonic_ns",
                  "full_timing_origin": "submission_not_observed",
                  "full_submit_monotonic_ns": None,
                  "full_receipt_validated_monotonic_ns": None,
                  "full_wall_ns": None}
        if pending is None or pending[0] != sequence:
            return fields
        try:
            ended = self._clock()
            if type(ended) is not int or ended < pending[1]:
                raise ValueError("invalid monotonic interval")
            return {**fields, "full_timing_origin": "new_submission_same_producer",
                    "full_submit_monotonic_ns": pending[1],
                    "full_receipt_validated_monotonic_ns": ended,
                    "full_wall_ns": ended - pending[1]}
        except Exception:
            return {}

    def discard(self):
        """An original publish/receipt failure has no validated end; do not time it."""
        self._pending, self._dropped = None, True

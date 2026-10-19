"""Bounded process-local diagnostic counters, never Driver persistence state.

A candidate is only a successful timeline command family. It is not qualified
for WAL eligibility. Real writes on this production path remain full writes.
"""
from __future__ import annotations


class PersistenceGrowthTimingV1:
    def __init__(self):
        self.successes = 0
        self.failures = 0
        self.candidate_successes = 0
        self.candidate_run = 0
        self.candidate_run_starts = 0

    def observe(self, *, candidate: bool, succeeded: bool, error_type: str | None = None):
        closed = 0
        if succeeded:
            self.successes += 1
            if candidate:
                self.candidate_successes += 1
                if not self.candidate_run:
                    self.candidate_run_starts += 1
                self.candidate_run += 1
            else:
                closed, self.candidate_run = self.candidate_run, 0
        else:
            self.failures += 1
            # An unknown/failed full barrier cannot support continuation of a
            # hypothetical suffix-only run. Do not count it as a success.
            closed, self.candidate_run = self.candidate_run, 0
        return {
            "persistence_outcome": "write_replace_returned" if succeeded else "failed",
            "persistence_error_type": error_type,
            "timeline_append_candidate": candidate,
            "candidate_policy": "successful_timeline_family_only_not_WAL_eligibility",
            "full_write_success_count": self.successes,
            "full_write_failure_count": self.failures,
            "candidate_full_write_success_count": self.candidate_successes,
            "candidate_append_run_length": self.candidate_run,
            "closed_candidate_run_length": closed,
            "candidate_activation_churn_count": self.candidate_run_starts,
            "actual_wal_append_count": 0,
            "persistence_counter_scope": "Driver_instance_timing_enabled_observations_only",
        }


PERSISTENCE_SCALAR_FIELDS = frozenset({
    "full_barrier_reason", "history_json_bytes", "history_rows",
    "persistence_attempt_id",
    "persistence_outcome", "persistence_error_type", "timeline_append_candidate",
    "candidate_policy", "full_write_success_count", "full_write_failure_count",
    "candidate_full_write_success_count", "candidate_append_run_length",
    "closed_candidate_run_length", "candidate_activation_churn_count",
    "actual_wal_append_count", "persistence_counter_scope",
})


def bounded_persistence_scalars_v1(fields: dict[str, object]):
    """Accept only named small scalars; never carry command/result bodies."""
    return {key: value for key, value in fields.items()
            if key in PERSISTENCE_SCALAR_FIELDS
            and (value is None or type(value) in (int, bool)
                 or type(value) is str and len(value) <= 160)}

"""Bounded local receipt evidence; no I/O, new snapshots, polls or decisions.

Buckets locate when Python SAW changes, not when native events happened.
Only the original exact-day wait installs this collector. Cleanup cannot reuse it.
"""
from __future__ import annotations
import json
import threading
import time

SCHEMA, KEY, MAX_BYTES = "xar.exact-clock-wait-progress.v1", "_exact_clock_wait_progress_v1", 2048
METRICS = ("owner", "verified", "heartbeat", "observer_completed_ms")
COLUMNS = ("first", "last", "last_change_ms", "changes", "delta", "missing", "resets")
BUCKET_COLUMNS = ("received", "owner_delta_seen", "verified_delta_seen", "heartbeat_changes_seen", "observer_changes_seen")
FIELDS = ("schema", "arm_generation", "identity", "flags", "heartbeats", "candidates", "elapsed_ms",
          "max_heartbeat_gap_ms", "candidate_first", "candidate_last", "columns", "metrics", "bucket_ms",
          "bucket_columns", "buckets", "overflow", "seed_from_cached_snapshot",
          "empty_bucket_means_unobserved", "native_event_time_verified", "source_heartbeat_ms")


def _dict(value):
    return value if isinstance(value, dict) else {}


def _int(value):
    return value if type(value) is int and 0 <= value < (1 << 64) else None


def _identity(snapshot):
    snapshot = _dict(snapshot)
    diag = _dict(snapshot.get("diagnostics"))
    row = (diag.get("bridge_pid"), diag.get("connection_generation"),
           snapshot.get("episode_character_id"), snapshot.get("episode_run_id"))
    if (any(_int(v) is None or v <= 0 for v in row[:3])
            or type(row[3]) is not str or not 0 < len(row[3]) <= 128):
        return None
    return row


class WaitProgressV1:
    def __init__(self, snapshot, generation, *, clock=time.perf_counter_ns):
        if _int(generation) is None or generation <= 0:
            raise ValueError("original armed generation required")
        self.clock, self.generation, self.started_ns = clock, generation, clock()
        self.identity = _identity(snapshot)
        self.flags = 1 if self.identity is None else 0
        self.rows = [[None, None, None, 0, 0, 0, 0] for _ in METRICS]
        self.buckets = [[0, 0, 0, 0, 0] for _ in range(8)]
        self.heartbeats = self.candidates = self.overflow = self.max_gap_ms = 0
        self.last_heartbeat_ms = self.candidate_first = self.candidate_last = None
        self.source_heartbeat_ms = [None, None]
        self.closed, self.frozen, self.lock = False, None, threading.Lock()
        seed = _dict(_dict(_dict(snapshot).get("diagnostics")).get("last_heartbeat"))
        self._values(seed, 0, None)
        self.observe_candidate(snapshot)

    def _elapsed(self):
        now = self.clock()
        if type(now) is not int or now < self.started_ns:
            self.flags |= 16
            return None
        return (now - self.started_ns) // 1_000_000

    def _values(self, heartbeat, elapsed, bucket):
        source_ms = _int(heartbeat.get("monotonic_ms"))
        if source_ms is None:
            self.flags |= 4
        else:
            if self.source_heartbeat_ms[0] is None:
                self.source_heartbeat_ms[0] = source_ms
            self.source_heartbeat_ms[1] = source_ms
        owner = _dict(heartbeat.get("main_thread_query_mailbox_v1"))
        observer = _dict(heartbeat.get("snapshot_observer_12002"))
        values = (owner.get("pump_epochs"), owner.get("owner_verified_pump_epochs"),
                  heartbeat.get("sequence"), observer.get("completed_ms"))
        for index, value in enumerate(values):
            row, value = self.rows[index], _int(value)
            if value is None:
                row[5] += 1
                self.flags |= 4
                continue
            previous = row[1]
            if row[0] is None:
                row[0] = value
            row[1] = value
            if previous is None or value == previous:
                continue
            if value < previous:
                row[6] += 1
                self.flags |= 8
                continue
            row[2], row[3], row[4] = elapsed, row[3] + 1, row[4] + value - previous
            if bucket is not None:
                bucket[index + 1] += value - previous if index < 2 else 1

    def received(self, frame_type, frame, token):
        with self.lock:
            if self.closed:
                return
            if frame_type == "hello":
                self.flags |= 2
                return
            if frame_type != "heartbeat":
                return
            elapsed = self._elapsed()
            if elapsed is None:
                return
            self.heartbeats += 1
            if self.last_heartbeat_ms is not None and elapsed < self.last_heartbeat_ms:
                self.flags |= 16
                return
            self.max_gap_ms = max(self.max_gap_ms, elapsed - (self.last_heartbeat_ms or 0))
            self.last_heartbeat_ms = elapsed
            bucket = self.buckets[elapsed // 5000] if elapsed < 40000 else None
            if bucket is None:
                self.overflow += 1
            else:
                bucket[0] += 1
            if (self.identity is None or token != (True, self.identity[1], self.identity[0])
                    or type(frame.get("pid")) is not int or frame.get("pid") != self.identity[0]):
                self.flags |= 2
            if not self.flags & 2:
                self._values(frame, elapsed, bucket)

    def observe_candidate(self, snapshot):
        with self.lock:
            if self.closed:
                return
            elapsed = self._elapsed()
            if elapsed is None:
                return
            self.candidates += 1
            identity = _identity(snapshot)
            if identity is None:
                self.flags |= 1
            elif self.identity is not None and identity != self.identity:
                self.flags |= 2
            snapshot = _dict(snapshot)
            paused = snapshot.get("paused")
            row = [elapsed, _int(snapshot.get("date_raw")), _int(snapshot.get("native_revision")),
                   paused if type(paused) is bool else None]
            if self.candidate_first is None:
                self.candidate_first = row
            self.candidate_last = row
            # A cached candidate cannot roll back newer ingest-authority counters.

    def boundary(self):
        with self.lock:
            if not self.closed:
                self.flags |= 2

    def note_callback_error(self):
        with self.lock:
            if not self.closed:
                self.flags |= 32

    def freeze(self, snapshot):
        with self.lock:
            if self.frozen is not None:
                return self.frozen
        self.observe_candidate(snapshot)
        with self.lock:
            self.closed = True
            elapsed = self._elapsed()
            if elapsed is not None:
                self.max_gap_ms = max(self.max_gap_ms, elapsed - (self.last_heartbeat_ms or 0))
            result = {
                "schema": SCHEMA, "arm_generation": self.generation,
                "identity": list(self.identity) if self.identity else None, "flags": self.flags,
                "heartbeats": self.heartbeats, "candidates": self.candidates,
                "elapsed_ms": elapsed, "max_heartbeat_gap_ms": self.max_gap_ms,
                "candidate_first": self.candidate_first, "candidate_last": self.candidate_last,
                "columns": list(COLUMNS), "metrics": {n: list(r) for n, r in zip(METRICS, self.rows)},
                "bucket_ms": 5000, "bucket_columns": list(BUCKET_COLUMNS),
                "buckets": [list(row) for row in self.buckets], "overflow": self.overflow,
                "seed_from_cached_snapshot": True, "empty_bucket_means_unobserved": True,
                "native_event_time_verified": False,
                "source_heartbeat_ms": list(self.source_heartbeat_ms),
            }
        # Encoding occurs once at close, with neither transport nor collector lock held.
        if len(json.dumps(result, separators=(",", ":"), ensure_ascii=True).encode()) > MAX_BYTES:
            result = {"schema": SCHEMA, "limit_exceeded": True, "native_event_time_verified": False}
        with self.lock:
            self.frozen = result
        return result


def project_wait_progress_v1(value):
    """Exact bounded shape for the typed error, without retaining unknown payloads."""
    try:
        if type(value) is not dict or value.get("schema") != SCHEMA:
            return None
        if set(value) == {"schema", "limit_exceeded", "native_event_time_verified"}:
            return dict(value) if value["limit_exceeded"] is True and value["native_event_time_verified"] is False else None
        if (set(value) != set(FIELDS) or value["columns"] != list(COLUMNS)
                or value["bucket_columns"] != list(BUCKET_COLUMNS) or value["bucket_ms"] != 5000
                or value["seed_from_cached_snapshot"] is not True
                or value["empty_bucket_means_unobserved"] is not True
                or value["native_event_time_verified"] is not False
                or set(value["metrics"]) != set(METRICS) or len(value["buckets"]) != 8):
            return None
        for row in value["metrics"].values():
            if type(row) is not list or len(row) != 7 or any(v is not None and _int(v) is None for v in row):
                return None
        if any(type(r) is not list or len(r) != 5 or any(_int(v) is None for v in r) for r in value["buckets"]):
            return None
        for key in ("arm_generation", "flags", "heartbeats", "candidates", "max_heartbeat_gap_ms", "overflow"):
            if _int(value[key]) is None:
                return None
        if value["elapsed_ms"] is not None and _int(value["elapsed_ms"]) is None:
            return None
        if (type(value["source_heartbeat_ms"]) is not list or len(value["source_heartbeat_ms"]) != 2
                or any(v is not None and _int(v) is None for v in value["source_heartbeat_ms"])):
            return None
        identity = value["identity"]
        if identity is not None and (type(identity) is not list or len(identity) != 4
                or any(_int(v) is None for v in identity[:3]) or type(identity[3]) is not str or len(identity[3]) > 128):
            return None
        for key in ("candidate_first", "candidate_last"):
            row = value[key]
            if row is not None and (type(row) is not list or len(row) != 4
                    or any(v is not None and _int(v) is None for v in row[:3])
                    or row[3] is not None and type(row[3]) is not bool):
                return None
        encoded = json.dumps({key: value[key] for key in FIELDS}, separators=(",", ":"), ensure_ascii=True)
        return json.loads(encoded) if len(encoded.encode()) <= MAX_BYTES else None
    except (KeyError, TypeError, ValueError):
        return None


def start_wait_progress_v1(driver, snapshot, generation):
    try:
        if getattr(driver, KEY, None) is not None:
            return None
        observer = WaitProgressV1(snapshot, generation)
        setattr(driver, KEY, observer)
        return observer
    except Exception:
        return None


def finish_wait_progress_v1(driver, observer, snapshot):
    if observer is None:
        return None
    try:
        if getattr(driver, KEY, None) is observer:
            setattr(driver, KEY, None)
        return observer.freeze(snapshot)
    except Exception:
        return None

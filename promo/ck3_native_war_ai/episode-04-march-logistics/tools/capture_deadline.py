"""Pure deadline admission for an explicit Episode04 recording start.

No process or desktop operation occurs here. The supervisor timeout includes
Frontend warm-up and every managed relaunch; it is never renewed at map-ready.
An absolute capacity deadline must be supplied, not guessed from old run names.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import time


MINIMUM_CLOSE_RESERVE_SECONDS = 120.0


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def parse_deadline(value: str) -> datetime:
    require(type(value) is str and bool(value), "recording deadline must be explicit ISO8601 UTC")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "recording deadline needs an explicit timezone")
    return parsed.astimezone(timezone.utc)


def positive_seconds(value: float, label: str) -> float:
    require(type(value) in (int, float) and math.isfinite(value) and value > 0,
            label + " must be finite and positive")
    return float(value)


class RecordingDeadlineGuard:
    """Bind immutable limits and admit full duration plus normal close reserve.

    UTC deadlines are also projected onto the monotonic clock once. Moving the
    wall clock backwards therefore cannot renew capacity. Moving it forwards
    shortens admission immediately. The first session binding is made directly
    before native_session(), so it is conservative relative to the supervisor's
    later internal deadline and includes its warm-up/normal-load time.
    """

    def __init__(self, *, machine_id: str, absolute_deadlines=(),
                 close_reserve_seconds=MINIMUM_CLOSE_RESERVE_SECONDS,
                 capacity_check=None, clock=None, monotonic=None):
        require(type(machine_id) is str and bool(machine_id), "recording deadline needs machine_id")
        reserve = positive_seconds(close_reserve_seconds, "recording normal close reserve")
        require(reserve >= MINIMUM_CLOSE_RESERVE_SECONDS,
                "recording normal close reserve must be at least120seconds")
        self.machine_id = machine_id
        self.reserve = reserve
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.monotonic = monotonic or time.monotonic
        self.capacity_check = capacity_check
        self.absolute = []
        wall, mono = self._current()
        for row in absolute_deadlines:
            require(type(row) is dict and type(row.get("source")) is str and bool(row["source"]),
                    "recording deadline requires an explicit source")
            deadline = parse_deadline(row.get("deadline_utc"))
            self.absolute.append({**row, "deadline_utc": deadline.isoformat(),
                                  "deadline_monotonic": mono + (deadline - wall).total_seconds()})
        self.session = None

    def _current(self):
        wall, mono = self.clock(), self.monotonic()
        require(isinstance(wall, datetime) and wall.tzinfo is not None,
                "deadline clock must report an aware UTC datetime")
        require(type(mono) in (int, float) and math.isfinite(mono),
                "deadline monotonic clock must be finite")
        return wall.astimezone(timezone.utc), float(mono)

    def bind_session_timeout(self, timeout_seconds: float) -> dict:
        require(self.session is None, "session recording deadline is already bound; never renew it")
        timeout = positive_seconds(timeout_seconds, "native session timeout")
        wall, mono = self._current()
        self.session = {"source": "before-native-session-invocation",
                        "bound_at_utc": wall.isoformat(), "bound_monotonic": mono,
                        "timeout_seconds": timeout, "deadline_monotonic": mono + timeout,
                        "deadline_utc": (wall + timedelta(seconds=timeout)).isoformat(),
                        "includes_frontend_warmup_and_relaunches": True}
        return dict(self.session)

    def __call__(self, seconds: int) -> dict:
        require(type(seconds) is int and 1 <= seconds <= 3600,
                "recording duration must be an integer from1to3600seconds")
        require(self.session is not None, "recording session deadline has not been bound")
        require(bool(self.absolute),
                "recording needs an explicit absolute capacity deadline from exact recording/runtime capacity admission")
        require(self.capacity_check is not None,
                "recording needs an exact machine/scene/run-bound capacity admission PATH SHA256")
        self.capacity_check()
        wall, mono = self._current()
        rows = [{**self.session,
                 "remaining_seconds": self.session["deadline_monotonic"] - mono}]
        for row in self.absolute:
            remaining = min(row["deadline_monotonic"] - mono,
                            (parse_deadline(row["deadline_utc"]) - wall).total_seconds())
            rows.append({**row, "remaining_seconds": remaining})
        remaining = min(row["remaining_seconds"] for row in rows)
        needed = seconds + self.reserve
        require(remaining >= needed,
                f"recording deadline insufficient: remaining={remaining:.3f}s, "
                f"recording={seconds}s + normal-close-reserve={self.reserve:g}s requires{needed:g}s")
        return {"schema": "xar.e04.recording-deadline-admission.v1",
                "machine_id": self.machine_id, "observed_at_utc": wall.isoformat(),
                "admitted": True, "recording_seconds": seconds,
                "normal_close_reserve_seconds": self.reserve,
                "required_remaining_seconds": needed, "remaining_seconds": remaining,
                "session_elapsed_before_recording_seconds": mono - self.session["bound_monotonic"],
                "deadlines": rows, "deadline_renewed": False}


class RecordingCapacityAdmission:
    """Read and recheck a bounded exact Root receipt, never extend its cutoff."""

    def __init__(self, admission, *, prepared, run_dir, machine_id, source_head=None, clock=None):
        require(isinstance(admission, (list, tuple)) and len(admission) == 2,
                "recording capacity requires PATH SHA256")
        original = Path(admission[0])
        require(not original.is_symlink(), "recording capacity JSON must not be a symlink")
        self.path = original.resolve(strict=True)
        require(type(admission[1]) is str and len(admission[1]) == 64,
                "recording capacity requires exact SHA256")
        self.sha = admission[1].lower()
        self.machine_id = machine_id
        self.scene_root = Path(prepared["assets_root"]).resolve()
        self.run_dir = Path(run_dir).resolve()
        require(self.run_dir.parent == self.scene_root,
                "recording run must be directly within its admitted scene")
        self.source_head = source_head
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.binding = None
        self.check_fresh()

    def check_fresh(self):
        require(self.path.suffix.lower() == ".json" and self.path.is_file()
                and not self.path.is_symlink() and 0 < self.path.stat().st_size <= 1024 * 1024,
                "recording capacity must be bounded non-symlink JSON")
        with self.path.open("rb") as stream:
            raw = stream.read(1024 * 1024 + 1)
        require(len(raw) <= 1024 * 1024 and hashlib.sha256(raw).hexdigest() == self.sha,
                "recording capacity exact SHA changed")
        row = json.loads(raw.decode("utf-8-sig"))
        require(type(row) is dict and row.get("admitted") is True,
                "recording capacity was not actually admitted")
        require(row.get("machine_id") == self.machine_id,
                "recording capacity belongs to another machine")
        scene = row.get("scene_root")
        require(type(scene) is str and Path(scene).is_absolute()
                and Path(scene).resolve() == self.scene_root,
                "recording capacity belongs to another scene")
        require(row.get("run_id") == self.run_dir.name,
                "recording capacity belongs to another run")
        if self.source_head is not None:
            require(row.get("source_head") == self.source_head,
                    "recording capacity belongs to another source commit")
        deadline = parse_deadline(row.get("quota_review_at_utc"))
        wall = self.clock()
        require(isinstance(wall, datetime) and wall.tzinfo is not None and wall <= deadline,
                "recording capacity expired")
        binding = {"path": str(self.path), "bytes": len(raw), "sha256": self.sha,
                   "machine_id": self.machine_id, "scene_root": str(self.scene_root),
                   "run_id": self.run_dir.name, "source_head": row.get("source_head"),
                   "deadline_utc": deadline.isoformat()}
        require(self.binding is None or self.binding == binding,
                "recording capacity binding changed")
        self.binding = binding


def recording_deadline_guard(args, *, machine_id: str, prepared, run_dir, source_head=None,
                             runtime_budget=None,
                             clock=None, monotonic=None) -> RecordingDeadlineGuard:
    """Use explicit CLI intent and the already validated capacity pin together."""
    deadlines = []
    explicit = getattr(args, "recording_deadline_utc", None)
    if explicit is not None:
        deadlines.append({"source": "explicit-recording-deadline-utc-cli",
                          "deadline_utc": explicit})
    capacities = []
    for name in ("recording_capacity_admission", "runtime_capacity_admission"):
        admission = getattr(args, name, None)
        if admission is None:
            continue
        capacity = RecordingCapacityAdmission(admission, prepared=prepared, run_dir=run_dir,
            machine_id=machine_id, source_head=source_head, clock=clock)
        capacities.append(capacity)
        deadlines.append({"source": "exact-recording-capacity-admission",
                          "argument": name,
                          "deadline_utc": capacity.binding["deadline_utc"],
                          "capacity_admission": dict(capacity.binding)})

    def check_capacity():
        for capacity in capacities:
            capacity.check_fresh()
        if runtime_budget is not None:
            runtime_budget.check_fresh()

    return RecordingDeadlineGuard(machine_id=machine_id, absolute_deadlines=deadlines,
        close_reserve_seconds=getattr(args, "recording_close_reserve_seconds", MINIMUM_CLOSE_RESERVE_SECONDS),
        capacity_check=check_capacity if capacities else None,
        clock=clock, monotonic=monotonic)

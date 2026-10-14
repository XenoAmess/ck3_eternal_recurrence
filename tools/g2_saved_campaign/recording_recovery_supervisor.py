"""Same-Game recording recovery policy. All side effects are injected by Root.

An adapter MUST make each callback idempotent for the supplied recovery_id and
return its actual receipt. A retry after an unknown callback outcome must read
the receipt, never launch a second OBS worker or replay an AUTO command.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from threading import Lock
from typing import Protocol


@dataclass(frozen=True)
class Game:
    pid: int
    creation_filetime: int
    creation_date: str
    pipe: str


@dataclass(frozen=True)
class Overlay:
    pid: int
    creation_filetime: int
    game_pid: int
    game_creation_filetime: int
    desktop_id: str
    decision_text_file: Path
    started_receipt: Path


@dataclass(frozen=True)
class Cleanup:
    session_id: str
    inputs_unbound: bool
    actual_exit_code: int
    normal_exit_proven: bool
    forced_process_calls: int


@dataclass(frozen=True)
class Recorder:
    session_id: str
    game: Game
    overlay: Overlay
    receipt_root: Path
    failed: bool
    recording: bool
    cleanup: Cleanup | None = None


@dataclass(frozen=True)
class SdkGuard:
    recording_paused: bool
    halt_cause: str | None
    original_command: str | None
    pending_cycle_stage: str | None
    original_auto_executed: bool


@dataclass(frozen=True)
class Observation:
    game: Game
    game_alive_exact: bool
    recorder: Recorder
    overlay_alive_exact: bool
    sdk: SdkGuard


@dataclass(frozen=True)
class Segment:
    session_id: str
    game: Game
    overlay: Overlay
    receipt_root: Path
    request_receipt: Path
    continuous: bool
    duration_seconds: None
    max_output_bytes: None
    deadline_utc: None


@dataclass(frozen=True)
class Admission:
    session_id: str
    game: Game
    overlay: Overlay
    status: str
    method: str
    receipt_path: Path
    frame_sha256_game: str
    frame_sha256_scene: str
    scene_overlay_diff_fraction: float


@dataclass(frozen=True)
class Attach:
    status: str
    old_session_id: str
    new_session_id: str
    game: Game
    rpc_calls: int
    replay_allowed: bool


@dataclass(frozen=True)
class Resume:
    status: str
    pending_cycle_preserved: bool
    original_auto_replayed: bool


class Adapter(Protocol):
    def observe(self) -> Observation: ...
    def cleanup_old(self, old: Recorder, recovery_id: str) -> Cleanup | None: ...
    def ensure_overlay(self, game: Game, old: Overlay, recovery_id: str) -> Overlay | None: ...
    def launch_segment(self, game: Game, overlay: Overlay, recovery_id: str) -> Segment | None: ...
    def admit_segment(self, game: Game, overlay: Overlay, segment: Segment,
                      recovery_id: str) -> Admission | None: ...
    def attach_recording_segment(self, old: Recorder, segment: Segment,
                                 admission: Admission, recovery_id: str) -> Attach | None: ...
    def resume_recording_pause(self, recovery_id: str) -> Resume | None: ...


@dataclass(frozen=True)
class Progress:
    status: str
    stage: str
    recovery_id: str | None
    reason: str | None = None


class RecoverySupervisor:
    """One attempt per failed recorder, one active owner, no Game/SDK RPC here."""

    def __init__(self, adapter: Adapter, *, session_root: Path):
        self.adapter = adapter
        self.session_root = Path(session_root).resolve()
        self._lock = Lock()
        self._attempt: dict | None = None
        self._recovered: set[str] = set()

    def progress(self) -> dict:
        attempt = self._attempt
        return {
            "recovered_session_ids": sorted(self._recovered),
            "active_recovery_id": attempt["id"] if attempt else None,
            "stage": attempt["stage"] if attempt else None,
            "old_session_id": attempt["old"].session_id if attempt else None,
        }

    def tick(self) -> Progress:
        if not self._lock.acquire(blocking=False):
            return Progress("busy", "exclusive", self._attempt["id"] if self._attempt else None)
        try:
            return self._tick_locked()
        finally:
            self._lock.release()

    def drive(self, *, max_steps: int = 8) -> Progress:
        """Advance available stages once; caller polls again after pending evidence."""
        if not 1 <= max_steps <= 8:
            raise ValueError("max_steps must be in [1, 8]")
        result = Progress("idle", "observe", None)
        for _ in range(max_steps):
            result = self.tick()
            if result.status != "advanced":
                break
        return result

    def _tick_locked(self) -> Progress:
        obs = self.adapter.observe()
        if not obs.game_alive_exact or obs.game.pid <= 0 or obs.game.creation_filetime <= 0:
            return Progress("blocked", "game", self._attempt["id"] if self._attempt else None,
                            "same Game PID and creation stamp are not alive")
        if obs.recorder.game != obs.game or obs.recorder.overlay.game_pid != obs.game.pid or (
            obs.recorder.overlay.game_creation_filetime != obs.game.creation_filetime
        ):
            return Progress("blocked", "identity", self._attempt["id"] if self._attempt else None,
                            "recorder/overlay is not bound to the retained Game")
        if self._attempt is None:
            old = obs.recorder
            if old.session_id in self._recovered:
                return Progress("idle", "already_recovered", None)
            if not old.failed and obs.overlay_alive_exact:
                return Progress("idle", "healthy", None)
            guard = obs.sdk
            if not (guard.recording_paused
                    and guard.halt_cause == "RecordingPaused"
                    and guard.original_command == "full_loop"
                    and guard.pending_cycle_stage == "auto_verified"
                    and guard.original_auto_executed):
                return Progress("waiting", "sdk_guard", None,
                                "await exact zero-RPC post-AUTO recording pause")
            recovery_id = hashlib.sha256(
                f"{obs.game.pid}:{obs.game.creation_filetime}:{old.session_id}".encode(
                    "utf-8")).hexdigest()[:32]
            self._attempt = {
                "id": recovery_id, "game": obs.game, "old": old,
                "old_overlay_alive": obs.overlay_alive_exact,
                "stage": "cleanup",
            }
        a = self._attempt
        assert a is not None
        if obs.game != a["game"]:
            return Progress("blocked", "game", a["id"], "Game identity changed during recovery")
        stage = a["stage"]
        try:
            if stage == "cleanup":
                proof = obs.recorder.cleanup if obs.recorder.session_id == a["old"].session_id else None
                if proof is None:
                    proof = self.adapter.cleanup_old(a["old"], a["id"])
                if proof is None:
                    return Progress("waiting", stage, a["id"])
                if (proof.session_id != a["old"].session_id or not proof.inputs_unbound
                        or proof.actual_exit_code != 0 or not proof.normal_exit_proven
                        or proof.forced_process_calls != 0):
                    raise ValueError("old OBS cleanup does not prove normal unbind and exit")
                a["cleanup"] = proof
                a["stage"] = "overlay"
            elif stage == "overlay":
                if obs.recorder.session_id == a["old"].session_id:
                    a["old_overlay_alive"] = obs.overlay_alive_exact
                overlay = self.adapter.ensure_overlay(a["game"], a["old"].overlay, a["id"])
                if overlay is None:
                    return Progress("waiting", stage, a["id"])
                self._check_overlay(overlay, a)
                a["overlay"] = overlay
                a["stage"] = "segment"
            elif stage == "segment":
                segment = self.adapter.launch_segment(a["game"], a["overlay"], a["id"])
                if segment is None:
                    return Progress("waiting", stage, a["id"])
                self._check_segment(segment, a)
                a["segment"] = segment
                a["stage"] = "admission"
            elif stage == "admission":
                admission = self.adapter.admit_segment(
                    a["game"], a["overlay"], a["segment"], a["id"])
                if admission is None:
                    return Progress("waiting", stage, a["id"])
                self._check_admission(admission, a)
                a["admission"] = admission
                a["stage"] = "attach"
            elif stage == "attach":
                attached = self.adapter.attach_recording_segment(
                    a["old"], a["segment"], a["admission"], a["id"])
                if attached is None:
                    return Progress("waiting", stage, a["id"])
                if (attached.status != "same_game_recording_segment_attached"
                        or attached.old_session_id != a["old"].session_id
                        or attached.new_session_id != a["segment"].session_id
                        or attached.game != a["game"] or attached.rpc_calls != 0
                        or attached.replay_allowed):
                    raise ValueError("SDK attachment is not local same-Game/no-replay")
                a["stage"] = "resume"
            elif stage == "resume":
                resumed = self.adapter.resume_recording_pause(a["id"])
                if resumed is None:
                    return Progress("waiting", stage, a["id"])
                if (resumed.status != "recording_guard_pause_resumed"
                        or not resumed.pending_cycle_preserved
                        or resumed.original_auto_replayed):
                    raise ValueError("SDK did not resume the retained post-AUTO cycle")
                old_id = a["old"].session_id
                rid = a["id"]
                self._recovered.add(old_id)
                self._attempt = None
                return Progress("complete", "resume", rid)
            else:
                raise RuntimeError(f"unknown recovery stage: {stage}")
            return Progress("advanced", a["stage"], a["id"])
        except Exception as error:
            # The stage and idempotency key are retained for a receipt-based retry.
            return Progress("error", stage, a["id"], f"{type(error).__name__}: {error}")

    def _check_overlay(self, overlay: Overlay, a: dict) -> None:
        old = a["old"].overlay
        if (overlay.game_pid != a["game"].pid
                or overlay.game_creation_filetime != a["game"].creation_filetime
                or not overlay.desktop_id or overlay.desktop_id != old.desktop_id
                or overlay.pid <= 0 or overlay.creation_filetime <= 0
                or not overlay.started_receipt.resolve().is_relative_to(self.session_root)
                or not overlay.decision_text_file.resolve().is_relative_to(self.session_root)):
            raise ValueError("new overlay lacks exact Game/Desktop1/session binding")
        if not a["old_overlay_alive"] and (
            (overlay.pid, overlay.creation_filetime) == (old.pid, old.creation_filetime)
            or overlay.decision_text_file.resolve() == old.decision_text_file.resolve()
            or overlay.started_receipt.resolve() == old.started_receipt.resolve()
        ):
            raise ValueError("dead overlay requires a new generation and unique decision text")

    def _check_segment(self, segment: Segment, a: dict) -> None:
        if (segment.session_id == a["old"].session_id
                or segment.game != a["game"] or segment.overlay != a["overlay"]
                or not segment.continuous or any(value is not None for value in (
                    segment.duration_seconds, segment.max_output_bytes, segment.deadline_utc))
                or not segment.receipt_root.resolve().is_relative_to(self.session_root / "recordings")
                or not segment.request_receipt.resolve().is_relative_to(self.session_root)):
            raise ValueError("new OBS segment lacks exact same-Game/overlay/unlimited binding")

    def _check_admission(self, admission: Admission, a: dict) -> None:
        if (admission.session_id != a["segment"].session_id
                or admission.game != a["game"] or admission.overlay != a["overlay"]
                or admission.status != "GREEN" or admission.method != "automatic_continuity"
                or not admission.receipt_path.resolve().is_relative_to(self.session_root)
                or len(admission.frame_sha256_game) != 64
                or len(admission.frame_sha256_scene) != 64
                or not 0.005 <= admission.scene_overlay_diff_fraction <= 1.0):
            raise ValueError("fresh game+decision scene automatic proof is missing")

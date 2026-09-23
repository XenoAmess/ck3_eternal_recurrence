"""Bounded readiness for exact-build application-main read-only queries.

The heartbeat reports a previously observed paused owner.  It does not prove
that owner is still pumping after the caller's latest paused snapshot.  This
module waits for one new verified pump before a battle-control ticket is sent.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import time


class PumpReadinessError(RuntimeError):
    def __init__(
        self, code: str, start_epoch: int | None = None,
        last_epoch: int | None = None, owner_tid: int | None = None,
    ) -> None:
        self.code = code
        self.start_epoch = start_epoch
        self.last_epoch = last_epoch
        self.owner_tid = owner_tid
        super().__init__(str(self))

    def __str__(self) -> str:
        return (
            f"code={self.code}, pump_start={self.start_epoch}, "
            f"pump_end={self.last_epoch}, owner_tid={self.owner_tid}"
        )


@dataclass(frozen=True)
class _PumpStamp:
    bridge_pid: int
    owner_tid: int
    pump_epoch: int
    verified_epoch: int


def exact_build_pump_gate_required(capabilities: dict[str, object]) -> bool:
    """Older unit fixtures have no exact-build adapter identity or heartbeat."""
    diagnostics = capabilities.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
    return bool(
        isinstance(hello, dict)
        and hello.get("game_adapter_id") == "ck3-1.19.0.6-msvc-x64"
        and hello.get("game_adapter_status") == "ready"
        and hello.get("ck3_build_match") is True
    )


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _stamp(capabilities: dict[str, object], date_raw: int) -> _PumpStamp:
    diagnostics = capabilities.get("diagnostics")
    heartbeat = diagnostics.get("last_heartbeat") if isinstance(diagnostics, dict) else None
    mailbox = heartbeat.get("main_thread_query_mailbox_v1") if isinstance(heartbeat, dict) else None
    if not isinstance(mailbox, dict) or not isinstance(diagnostics, dict):
        raise PumpReadinessError("heartbeat_unavailable")
    bridge_pid = diagnostics.get("bridge_pid")
    owner_tid = mailbox.get("owner_tid")
    epoch = mailbox.get("pump_epochs")
    verified = mailbox.get("owner_verified_pump_epochs")
    if not (
        _positive_int(bridge_pid)
        and _positive_int(owner_tid)
        and isinstance(epoch, int) and not isinstance(epoch, bool) and epoch >= 0
        and isinstance(verified, int) and not isinstance(verified, bool) and verified >= 0
        and capabilities.get("transport_ready") is True
        and mailbox.get("installed") is True
        and mailbox.get("sdl_poll_event_hook_installed") is True
        and mailbox.get("stop") is False
        and mailbox.get("failure") == 0
        and mailbox.get("current_tid") == owner_tid
        and mailbox.get("date_raw") == date_raw
        and mailbox.get("paused") is True
        and mailbox.get("application_main_observed") is True
        and mailbox.get("paused_main_thread_observed") is True
        and mailbox.get("stamp_read_success") is True
        and mailbox.get("ready") is True
    ):
        raise PumpReadinessError(
            "owner_or_paused_frame_changed",
            epoch if isinstance(epoch, int) else None,
            epoch if isinstance(epoch, int) else None,
            owner_tid if isinstance(owner_tid, int) else None,
        )
    return _PumpStamp(bridge_pid, owner_tid, epoch, verified)


def wait_for_verified_pump(
    get_capabilities: Callable[[], dict[str, object]],
    baseline_capabilities: dict[str, object],
    date_raw: int,
    *,
    timeout_seconds: float = 40.0,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    """Return a new same-owner heartbeat or fail before the native submit."""
    baseline = _stamp(baseline_capabilities, date_raw)
    start = clock()
    last = baseline
    while clock() - start < timeout_seconds:
        current = get_capabilities()
        if not isinstance(current, dict):
            raise PumpReadinessError(
                "heartbeat_unavailable", baseline.pump_epoch,
                last.pump_epoch, baseline.owner_tid,
            )
        last = _stamp(current, date_raw)
        if (last.bridge_pid, last.owner_tid) != (
            baseline.bridge_pid, baseline.owner_tid
        ):
            raise PumpReadinessError(
                "owner_changed", baseline.pump_epoch,
                last.pump_epoch, baseline.owner_tid,
            )
        if last.pump_epoch < baseline.pump_epoch:
            raise PumpReadinessError(
                "pump_regressed", baseline.pump_epoch,
                last.pump_epoch, baseline.owner_tid,
            )
        if (
            last.pump_epoch > baseline.pump_epoch
            and last.verified_epoch >= last.pump_epoch
        ):
            return current
        sleep(1.0)
    raise PumpReadinessError(
        "no_fresh_pump", baseline.pump_epoch,
        last.pump_epoch, baseline.owner_tid,
    )

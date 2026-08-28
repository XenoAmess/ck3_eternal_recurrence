"""Replaceable game I/O backends shared by vision and MCP modes."""

from __future__ import annotations

from collections.abc import Callable
import json
import math
from pathlib import Path
import time
from typing import Protocol, runtime_checkable

from .event_contract import normalize_active_event
from .settlement_contract import (
    ONE_LIFE_SETTLEMENT_CAPABILITY,
    settlement_ready_for_episode,
)


class BridgeUnavailableError(RuntimeError):
    """The selected game bridge is not connected to a live CK3 session."""


class PreSubmissionRevisionMismatchError(BridgeUnavailableError):
    """A planned revision changed before any gameplay request was submitted."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.selected_step: str | None = None
        self.plan: dict[str, object] | None = None
        self.replan_count = 0


class StepPostconditionError(BridgeUnavailableError):
    """A submitted gameplay step failed its observed-state postcondition."""

    def __init__(
        self,
        message: str,
        *,
        step_result: dict[str, object],
        selected_step: str,
    ) -> None:
        super().__init__(message)
        self.step_result = step_result
        self.selected_step = selected_step
        self.plan: dict[str, object] | None = None


class UnsupportedStepError(RuntimeError):
    """A backend does not yet implement this gameplay step."""


@runtime_checkable
class GameplayBridgeDriver(Protocol):
    """Small semantic boundary between the planner and CK3 I/O.

    A driver may be backed by OCR/input, the data-Mod log/run bridge, or an
    injected DLL.  All three return the same step-result dictionaries already
    consumed by ``strategy.choose_one_life_turn``.
    """

    def capabilities(self) -> dict[str, object]: ...

    def take_snapshot(self) -> dict[str, object]: ...

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]: ...

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]: ...


class CallbackGameplayDriver:
    """Embed an existing session executor without changing its policy code."""

    def __init__(
        self,
        *,
        backend_id: str,
        snapshot: Callable[[], dict[str, object]],
        execute: Callable[[str, int | None], dict[str, object]],
        action_steps: tuple[str, ...],
        wait: Callable[[int, float], dict[str, object]] | None = None,
        source: str = "embedded",
        latency: str = "interactive",
    ) -> None:
        self._backend_id = backend_id
        self._snapshot = snapshot
        self._execute = execute
        self._wait = wait
        self._action_steps = tuple(dict.fromkeys(action_steps))
        self._source = source
        self._latency = latency

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": self._backend_id,
            "source": self._source,
            "latency": self._latency,
            "snapshot": True,
            "wait_for_change": self._wait is not None,
            "action_steps": list(self._action_steps),
        }

    def take_snapshot(self) -> dict[str, object]:
        return _normalize_snapshot(self._snapshot(), self._backend_id)

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        if step not in self._action_steps:
            raise UnsupportedStepError(
                f"backend {self._backend_id} does not implement step {step}"
            )
        result = self._execute(step, expected_revision)
        if not isinstance(result, dict):
            raise BridgeUnavailableError("gameplay backend returned a malformed result")
        return {**result, "backend_id": self._backend_id}

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        if self._wait is None:
            raise UnsupportedStepError(
                f"backend {self._backend_id} does not implement wait_for_change"
            )
        return _normalize_snapshot(
            self._wait(after_revision, timeout_seconds), self._backend_id
        )


class HybridGameplayDriver:
    """Prefer a fast semantic bridge and fall back only when unsupported."""

    def __init__(
        self, fast: GameplayBridgeDriver, baseline: GameplayBridgeDriver
    ) -> None:
        self.fast = fast
        self.baseline = baseline
        self._last_snapshot: dict[str, object] | None = None

    def capabilities(self) -> dict[str, object]:
        fast = self.fast.capabilities()
        baseline = self.baseline.capabilities()
        fast_steps = _action_steps(fast)
        baseline_steps = _action_steps(baseline)
        fast_bridge_capabilities = _bridge_capabilities(fast)
        baseline_bridge_capabilities = _bridge_capabilities(baseline)
        return {
            "format_version": 1,
            "backend_id": "hybrid",
            "source": "semantic-first-with-vision-fallback",
            "latency": "mixed",
            "snapshot": bool(fast.get("snapshot") or baseline.get("snapshot")),
            "wait_for_change": bool(
                fast.get("wait_for_change") or baseline.get("wait_for_change")
            ),
            "action_steps": sorted(fast_steps | baseline_steps),
            "fast_action_steps": sorted(fast_steps),
            "baseline_action_steps": sorted(baseline_steps),
            "bridge_capabilities": sorted(
                fast_bridge_capabilities | baseline_bridge_capabilities
            ),
            "backends": [fast, baseline],
        }

    def take_snapshot(self) -> dict[str, object]:
        try:
            fast = self.fast.take_snapshot()
        except (BridgeUnavailableError, UnsupportedStepError):
            baseline = self.baseline.take_snapshot()
            result = {
                **baseline,
                "backend_id": "hybrid",
                "active_snapshot_backend": baseline.get("backend_id"),
                "backend_revisions": {
                    "fast": None,
                    "baseline": baseline["revision"],
                },
            }
            self._last_snapshot = result
            return result

        fast_history = fast.get("history")
        fast_capabilities = self.fast.capabilities()
        fast_bridge_capabilities = _bridge_capabilities(fast_capabilities)
        needs_settlement_fallback = bool(
            (
                fast.get("one_life_terminal") is True
                or isinstance(fast.get("one_life_terminal_reason"), str)
            )
            and ONE_LIFE_SETTLEMENT_CAPABILITY
            not in fast_bridge_capabilities
        )
        needs_baseline_context = (
            not isinstance(fast_history, list)
            or not fast_history
            or needs_settlement_fallback
        )
        baseline: dict[str, object] | None = None
        if needs_baseline_context:
            try:
                baseline = self.baseline.take_snapshot()
            except (BridgeUnavailableError, UnsupportedStepError):
                baseline = None

        fast_revision = int(fast["revision"])
        baseline_revision = (
            int(baseline["revision"]) if isinstance(baseline, dict) else 0
        )
        result = {
            **(baseline or {}),
            **fast,
            "backend_id": "hybrid",
            "active_snapshot_backend": fast.get("backend_id"),
            "snapshot_id": (
                f"hybrid:{fast['snapshot_id']}:"
                f"{baseline.get('snapshot_id') if baseline else 'none'}"
            ),
            "revision": _paired_revision(fast_revision, baseline_revision),
            "backend_revisions": {
                "fast": fast_revision,
                "baseline": baseline_revision if baseline is not None else None,
            },
        }
        if needs_baseline_context and baseline is not None:
            result["history"] = baseline.get("history", [])
            if fast.get("phase") is None:
                result["phase"] = baseline.get("phase")
            if fast.get("active_event") is None and baseline.get("active_event") is not None:
                result["active_event"] = baseline["active_event"]
                result["active_event_backend"] = baseline.get("backend_id")
            baseline_supports_settlement = bool(
                ONE_LIFE_SETTLEMENT_CAPABILITY
                in _bridge_capabilities(self.baseline.capabilities())
            )
            if needs_settlement_fallback and baseline_supports_settlement:
                baseline_settlement = baseline.get("one_life_settlement")
                result["one_life_settlement"] = baseline_settlement
                result["one_life_settlement_backend"] = baseline.get("backend_id")
                result["one_life_settlement_supported"] = True
                if baseline_settlement is None:
                    result["one_life_settlement_status"] = "pending"
                else:
                    result["one_life_settlement_status"] = (
                        "ready"
                        if settlement_ready_for_episode(
                            baseline_settlement,
                            result.get("episode_character_id"),
                        )
                        else "source_mismatch"
                    )
        self._last_snapshot = result
        return result

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        use_fast = step in _action_steps(self.fast.capabilities())
        selected = self.fast if use_fast else self.baseline
        selected_revision = expected_revision
        if expected_revision is not None:
            current = self.take_snapshot()
            if expected_revision != current["revision"]:
                raise BridgeUnavailableError(
                    "hybrid gameplay revision mismatch: "
                    f"expected {expected_revision}, current {current['revision']}"
                )
            revisions = current.get("backend_revisions")
            if isinstance(revisions, dict):
                key = "fast" if use_fast else "baseline"
                raw_revision = revisions.get(key)
                selected_revision = (
                    raw_revision if isinstance(raw_revision, int) else None
                )
        if use_fast:
            # A supported fast action is never silently replayed through the
            # baseline after it starts and fails.  Only an absent capability
            # selects the baseline.
            return selected.execute_step(step, expected_revision=selected_revision)
        return selected.execute_step(step, expected_revision=selected_revision)

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        if (
            isinstance(after_revision, bool)
            or not isinstance(after_revision, int)
            or after_revision < 0
        ):
            raise ValueError("after_revision must be a non-negative integer")
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(float(timeout_seconds))
            or timeout_seconds <= 0
        ):
            raise ValueError("timeout_seconds must be finite and positive")
        deadline = time.monotonic() + float(timeout_seconds)
        while True:
            snapshot = self.take_snapshot()
            if int(snapshot["revision"]) > after_revision:
                return snapshot
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return snapshot
            time.sleep(min(0.1, remaining))


class BridgeGameplayStepExecutor:
    """Adapt any bridge driver to ``gameplay_runner.GameplayStepExecutor``."""

    def __init__(
        self,
        driver: GameplayBridgeDriver,
        *,
        expected_revision: Callable[[], int | None] | None = None,
    ) -> None:
        self.driver = driver
        self.expected_revision = expected_revision

    def execute_step(self, step: str) -> dict[str, object]:
        revision = self.expected_revision() if self.expected_revision else None
        return self.driver.execute_step(step, expected_revision=revision)


class DevelopmentReportDriver:
    """Expose the current persistent vision session as a read-only MCP source.

    This is immediately useful for MCP inspection and planning.  Executing
    steps is deliberately supplied by an embedded/session transport later;
    reading a report must never spawn or restart CK3.
    """

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = Path(state_dir)

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "vision-report",
            "source": "ocr-keyboard-mouse-session-report",
            "latency": "cached",
            "snapshot": True,
            "wait_for_change": True,
            "action_steps": [],
        }

    def _latest_report_path(self) -> Path:
        runs = self.state_dir / "runs"
        candidates = sorted(
            runs.glob("*-dev-session-*/report.json"),
            key=lambda path: path.stat().st_mtime_ns,
            reverse=True,
        )
        if not candidates:
            raise BridgeUnavailableError("no opening development session report exists")
        return candidates[0]

    def take_snapshot(self) -> dict[str, object]:
        path = self._latest_report_path()
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise BridgeUnavailableError(
                f"development session report is unreadable: {error}"
            ) from error
        commands = report.get("commands")
        if not isinstance(commands, list):
            commands = []
        rows = [row for row in commands if isinstance(row, dict)]
        last = rows[-1] if rows else None
        effective_rows = _expanded_session_rows(rows)
        last_successful = next(
            (
                row
                for row in reversed(effective_rows)
                if row.get("ok") is True and isinstance(row.get("result"), dict)
            ),
            None,
        )
        last_result = (
            last_successful.get("result")
            if isinstance(last_successful, dict)
            else None
        )
        revision = len(rows)
        active_event = _reported_active_event(
            effective_rows[-1] if effective_rows else last
        )
        return _normalize_snapshot(
            {
                "format_version": 1,
                "snapshot_id": f"{report.get('run_id')}:{revision}",
                "revision": revision,
                "source": "vision-report",
                "session": {
                    "run_id": report.get("run_id"),
                    "process": report.get("process"),
                    "finalized": report.get("finalized"),
                },
                "phase": (
                    last_result.get("final_screen")
                    if isinstance(last_result, dict)
                    else None
                ),
                "history": rows,
                "last_command": last,
                "last_successful_turn": last_successful,
                "active_event": active_event,
            },
            "vision-report",
        )

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        raise UnsupportedStepError(
            "the report backend is read-only; use an embedded, Mod, or native driver"
        )

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        if (
            isinstance(after_revision, bool)
            or not isinstance(after_revision, int)
            or after_revision < 0
        ):
            raise ValueError("after_revision must be a non-negative integer")
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(float(timeout_seconds))
            or timeout_seconds <= 0
        ):
            raise ValueError("timeout_seconds must be finite and positive")
        deadline = time.monotonic() + float(timeout_seconds)
        while True:
            snapshot = self.take_snapshot()
            if int(snapshot["revision"]) > after_revision:
                return snapshot
            if time.monotonic() >= deadline:
                return snapshot
            time.sleep(min(0.1, max(0.0, deadline - time.monotonic())))


def _action_steps(capabilities: dict[str, object]) -> set[str]:
    raw = capabilities.get("action_steps")
    if not isinstance(raw, list):
        return set()
    return {step for step in raw if isinstance(step, str) and step}


def _bridge_capabilities(capabilities: dict[str, object]) -> set[str]:
    raw = capabilities.get("bridge_capabilities")
    if not isinstance(raw, list):
        return set()
    return {item for item in raw if isinstance(item, str) and item}


def _paired_revision(first: int, second: int) -> int:
    """Encode two non-negative backend revisions as one monotonic integer."""

    total = first + second
    return total * (total + 1) // 2 + second


def _expanded_session_rows(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    expanded: list[dict[str, object]] = []
    for row in rows:
        command = row.get("command")
        result = row.get("result")
        turns = result.get("turns") if isinstance(result, dict) else None
        if (
            isinstance(command, str)
            and (command == "auto-run" or command.startswith("auto-run "))
            and isinstance(turns, list)
        ):
            expanded.extend(turn for turn in turns if isinstance(turn, dict))
        else:
            expanded.append(row)
    return expanded


def _reported_active_event(
    last_command: dict[str, object] | None,
) -> dict[str, object] | None:
    """Project the event already reported by a vision session, if any."""
    if not isinstance(last_command, dict):
        return None
    result = last_command.get("result")
    for container in (last_command, result):
        if not isinstance(container, dict):
            continue
        candidate = container.get("active_event", container.get("current_event"))
        if isinstance(candidate, dict):
            return candidate
    if "ordinary event interrupted" in str(last_command.get("error", "")):
        # The existing life/war advance loop has positively recognized a
        # stable event but its failure row predates structured option export.
        # Keep the event actionable by the explicit visual resolver without
        # inventing a native event id or option count.
        return {
            "source": "vision",
            "instance_id": None,
            "option_count": None,
            "title": None,
            "options": [],
        }
    return None


def _normalize_snapshot(
    snapshot: dict[str, object], backend_id: str
) -> dict[str, object]:
    if not isinstance(snapshot, dict):
        raise BridgeUnavailableError("gameplay backend returned a malformed snapshot")
    revision = snapshot.get("revision")
    snapshot_id = snapshot.get("snapshot_id")
    if (
        isinstance(revision, bool)
        or not isinstance(revision, int)
        or revision < 0
        or not isinstance(snapshot_id, str)
        or not snapshot_id
    ):
        raise BridgeUnavailableError("gameplay snapshot lacks an id or revision")
    source = snapshot.get("source")
    default_source = source if isinstance(source, str) and source else backend_id
    raw_active_event = snapshot.get(
        "active_event", snapshot.get("current_event")
    )
    try:
        active_event = normalize_active_event(
            raw_active_event,
            default_source=default_source,
        )
    except ValueError as error:
        raise BridgeUnavailableError(
            f"gameplay snapshot has a malformed active_event: {error}"
        ) from error
    return {
        **snapshot,
        "backend_id": backend_id,
        "active_event": active_event,
    }

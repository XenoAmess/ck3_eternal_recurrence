"""Writable driver for an already-running opening development session."""

from __future__ import annotations

from collections.abc import Callable
import json
import math
from pathlib import Path
import time
import uuid

from ..environment import write_json_atomic
from .driver import (
    BridgeUnavailableError,
    DevelopmentReportDriver,
    UnsupportedStepError,
)


class DevelopmentSessionDriver(DevelopmentReportDriver):
    """Submit semantic steps to the persistent vision session file queue.

    Snapshot and wait semantics stay identical to ``DevelopmentReportDriver``;
    only action dispatch is added.  The opening session remains the sole owner
    of CK3 UI work and consumes every request on its main thread.
    """

    def __init__(
        self,
        state_dir: Path,
        *,
        request_timeout_seconds: float = 300.0,
        poll_interval_seconds: float = 0.05,
        request_id_factory: Callable[[], str] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        super().__init__(state_dir)
        self.request_timeout_seconds = _positive_seconds(
            request_timeout_seconds, "request_timeout_seconds"
        )
        self.poll_interval_seconds = _positive_seconds(
            poll_interval_seconds, "poll_interval_seconds"
        )
        self.request_id_factory = request_id_factory or (
            lambda: f"mcp-{uuid.uuid4().hex}"
        )
        self.sleep = sleep

    def _report_and_bridge(self) -> tuple[Path, dict[str, object], dict[str, object]]:
        report_path = self._latest_report_path()
        try:
            report = json.loads(report_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as error:
            raise BridgeUnavailableError(
                f"development session report is unreadable: {error}"
            ) from error
        if not isinstance(report, dict):
            raise BridgeUnavailableError("development session report is malformed")
        bridge = report.get("bridge")
        if not isinstance(bridge, dict):
            raise BridgeUnavailableError(
                "development session report has no writable bridge descriptor"
            )
        return report_path, report, bridge

    def capabilities(self) -> dict[str, object]:
        _path, report, bridge = self._report_and_bridge()
        raw_steps = bridge.get("action_steps")
        action_steps = (
            list(dict.fromkeys(step for step in raw_steps if isinstance(step, str)))
            if isinstance(raw_steps, list)
            else []
        )
        raw_commands = bridge.get("supported_commands")
        supported_commands = (
            list(
                dict.fromkeys(
                    command for command in raw_commands if isinstance(command, str)
                )
            )
            if isinstance(raw_commands, list)
            else []
        )
        return {
            "format_version": 1,
            "backend_id": "vision-session",
            "source": "ocr-keyboard-mouse-session-queue",
            "latency": "interactive",
            "snapshot": True,
            "wait_for_change": True,
            "connected": report.get("finalized") is not True,
            "action_steps": action_steps,
            "supported_commands": supported_commands,
        }

    def take_snapshot(self) -> dict[str, object]:
        return {
            **super().take_snapshot(),
            "backend_id": "vision-session",
            "source": "vision-session",
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        if not isinstance(step, str) or not step:
            raise ValueError("step must be a non-empty string")
        report_path, report, bridge = self._report_and_bridge()
        capabilities = self.capabilities()
        if step not in capabilities["action_steps"]:
            raise UnsupportedStepError(
                f"backend vision-session does not implement step {step}"
            )
        if report.get("finalized") is True:
            raise BridgeUnavailableError("development session is already finalized")

        snapshot = self.take_snapshot()
        revision = int(snapshot["revision"])
        if expected_revision is not None:
            if (
                isinstance(expected_revision, bool)
                or not isinstance(expected_revision, int)
                or expected_revision < 0
            ):
                raise ValueError("expected_revision must be a non-negative integer")
            if expected_revision != revision:
                raise BridgeUnavailableError(
                    "development session revision mismatch: "
                    f"expected {expected_revision}, current {revision}"
                )

        request_id = self.request_id_factory()
        if not isinstance(request_id, str) or not request_id:
            raise BridgeUnavailableError("request_id_factory returned an invalid id")
        inbox_dir = _bridge_path(
            report_path,
            bridge.get("inbox_dir"),
            Path("bridge") / "inbox",
        )
        outbox_dir = _bridge_path(
            report_path,
            bridge.get("outbox_dir"),
            Path("bridge") / "outbox",
        )
        inbox_dir.mkdir(parents=True, exist_ok=True)
        outbox_dir.mkdir(parents=True, exist_ok=True)
        request_path = inbox_dir / f"{request_id}.json"
        response_path = outbox_dir / f"{request_id}.json"
        if request_path.exists() or response_path.exists():
            raise BridgeUnavailableError(
                f"development session request_id already exists: {request_id}"
            )
        write_json_atomic(
            request_path,
            {
                "protocol_version": bridge.get("protocol_version", 1),
                "request_id": request_id,
                "command": "step",
                "step": step,
                "expected_revision": revision,
            },
        )

        deadline = time.monotonic() + self.request_timeout_seconds
        while not response_path.exists():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise BridgeUnavailableError(
                    "development session request timed out: "
                    f"request_id={request_id}, step={step}"
                )
            self.sleep(min(self.poll_interval_seconds, remaining))
        try:
            response = json.loads(response_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as error:
            raise BridgeUnavailableError(
                f"development session response is unreadable: {error}"
            ) from error
        if not isinstance(response, dict) or response.get("request_id") != request_id:
            raise BridgeUnavailableError("development session response is malformed")
        if response.get("ok") is not True:
            raise BridgeUnavailableError(
                "development session step failed: "
                f"{response.get('error') or 'unknown session error'}"
            )
        result = response.get("result")
        if isinstance(result, dict):
            return {**result, "backend_id": "vision-session"}
        return {
            "result": result,
            "backend_id": "vision-session",
        }

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        return super().wait_for_change(
            after_revision,
            timeout_seconds=timeout_seconds,
        )


def _positive_seconds(value: float, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or value <= 0
    ):
        raise ValueError(f"{name} must be finite and positive")
    return float(value)


def _bridge_path(report_path: Path, raw: object, fallback: Path) -> Path:
    candidate = Path(raw) if isinstance(raw, str) and raw else fallback
    if not candidate.is_absolute():
        candidate = report_path.parent / candidate
    return candidate

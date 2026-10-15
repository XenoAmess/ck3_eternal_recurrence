"""Ordinary auto camera presentation worker; one daemon and one latest request."""
from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable

_LOG = logging.getLogger(__name__)


class LatestCameraFollowWorker:
    """Run presentation after auto_turn; never grant its receipt gameplay credit."""

    def __init__(
        self,
        work: Callable[[object], dict[str, object] | None],
        *,
        on_complete: Callable[[dict[str, object]], None] | None = None,
        quiet_seconds: float = 0.25,
    ) -> None:
        self._work = work
        self._on_complete = on_complete
        self._quiet_seconds = quiet_seconds
        self._condition = threading.Condition()
        self._thread: threading.Thread | None = None
        self._closed = False
        self._sequence = 0
        self._identity = uuid.uuid4().hex[:12]
        self._pending: dict[str, object] | None = None
        self._last: dict[str, object] | None = None
        self._recent_failures: deque[dict[str, object]] = deque(maxlen=16)

    @staticmethod
    def _reference(actual: dict[str, object] | None) -> dict[str, object] | None:
        if actual is None:
            return None
        receipt = actual.get("receipt")
        summary = None
        if isinstance(receipt, dict):
            summary = {key: receipt.get(key) for key in (
                "status", "mode", "display_mode", "reason", "hotspot") if key in receipt}
            native = receipt.get("native_actual")
            if isinstance(native, dict):
                summary["native_actual"] = {key: native.get(key) for key in (
                    "status", "request_sequence", "county_count", "zoom_index", "bounds",
                    "camera_postcondition_verified", "coverage_verified", "native_elapsed_us")}
        return {
            "request_id": actual["request_id"],
            "status": actual["status"],
            "work_status": actual.get("work_status"),
            "reason": actual.get("reason"),
            "receipt": summary,
        }

    def schedule(self, payload: object = None) -> dict[str, object]:
        """Overwrite one waiting request and return with a bounded reference."""
        start_thread = None
        with self._condition:
            if self._closed:
                return {"status": "unavailable", "reason": "camera worker closed"}
            self._sequence += 1
            request_id = f"auto-camera-{self._identity}-{self._sequence}"
            superseded = self._pending.get("request_id") if self._pending else None
            eligible_at = (self._pending["eligible_at"] if self._pending else
                           time.monotonic() + self._quiet_seconds)
            self._pending = {
                "request_id": request_id,
                "eligible_at": eligible_at,
                "payload": payload,
            }
            if self._thread is None:
                start_thread = threading.Thread(
                    target=self._run, name="xar-auto-camera", daemon=True,
                )
                self._thread = start_thread
            previous = self._reference(self._last)
            self._condition.notify()
        if start_thread is not None:
            try:
                start_thread.start()
            except Exception as error:
                with self._condition:
                    self._closed = True
                    self._pending = None
                    self._last = {
                        "request_id": request_id, "status": "failed",
                        "reason": f"worker_start:{type(error).__name__}: {error}",
                    }
                _LOG.warning("ordinary camera worker start failed: %s", error)
                return {
                    "status": "unavailable", "request_id": request_id,
                    "reason": "camera worker failed to start",
                }
        return {
            "schema": "xar.ck3.auto-camera-schedule/v1",
            "status": "scheduled",
            "request_id": request_id,
            "superseded_pending_request_id": superseded,
            "latest_actual": previous,
            "same_frame_with_gameplay_claim": False,
        }

    def latest_actual(self) -> dict[str, object] | None:
        with self._condition:
            return dict(self._last) if self._last is not None else None

    def recent_failures(self) -> list[dict[str, object]]:
        with self._condition:
            return [dict(row) for row in self._recent_failures]

    def close_without_wait(self) -> None:
        with self._condition:
            self._closed = True
            self._pending = None
            self._condition.notify_all()

    def _run(self) -> None:
        while True:
            with self._condition:
                while self._pending is None and not self._closed:
                    self._condition.wait()
                if self._closed:
                    return
                assert self._pending is not None
                delay = float(self._pending["eligible_at"]) - time.monotonic()
                if delay > 0:
                    self._condition.wait(timeout=delay)
                    continue
                request = self._pending
                self._pending = None
            started = time.monotonic()
            try:
                receipt = self._work(request["payload"])
                if receipt is None:
                    status, work_status, reason = "skipped", None, None
                elif isinstance(receipt, dict):
                    work_status = receipt.get("status")
                    status = "failed" if work_status == "unavailable" else "completed"
                    reason = receipt.get("reason")
                else:
                    raise TypeError("camera work returned a non-dict receipt")
                actual = {
                    "schema": "xar.ck3.auto-camera-actual/v1",
                    "request_id": request["request_id"],
                    "status": status,
                    "work_status": work_status,
                    "reason": reason,
                    "receipt": receipt,
                    "elapsed_seconds": time.monotonic() - started,
                    "same_frame_with_gameplay_claim": False,
                }
            except Exception as error:
                actual = {
                    "schema": "xar.ck3.auto-camera-actual/v1",
                    "request_id": request["request_id"],
                    "status": "failed",
                    "reason": f"{type(error).__name__}: {error}",
                    "elapsed_seconds": time.monotonic() - started,
                    "same_frame_with_gameplay_claim": False,
                }
            with self._condition:
                self._last = actual
                if actual["status"] == "failed":
                    self._recent_failures.append(actual)
            if actual["status"] == "failed":
                _LOG.warning(
                    "ordinary camera failed request_id=%s reason=%s",
                    actual["request_id"], actual.get("reason"),
                )
            if self._on_complete is not None:
                try:
                    self._on_complete(dict(actual))
                except Exception as error:
                    _LOG.warning("ordinary camera completion observer failed: %s", error)

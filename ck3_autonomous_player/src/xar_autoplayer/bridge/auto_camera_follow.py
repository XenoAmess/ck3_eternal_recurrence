"""Ordinary auto camera presentation worker; one daemon and one latest request."""
from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable

_LOG = logging.getLogger(__name__)


def camera_receipt_outcome(receipt: dict[str, object]) -> tuple[str, bool, object]:
    """Separate queued presentation from an observed Native camera postcondition."""
    if receipt.get("status") in {"unavailable", "failed"}:
        return "failed", False, receipt.get("reason")
    native = receipt.get("native_actual")
    if isinstance(native, dict):
        status = native.get("status")
        if status == "settled" and native.get("camera_postcondition_verified") is True:
            return "completed", True, receipt.get("reason")
        if status in {"idle", "submitted"}:
            return "pending", False, "native_camera_pending"
        if status == "cancelled":
            return "skipped", False, "native_camera_cancelled"
        return "failed", False, f"native_camera_{status or 'unknown'}"
    if receipt.get("status") == "queued_native_presentation":
        return "pending", False, receipt.get("reason")
    # An observation/hold without an actual Native result is not camera success.
    if "intent" in receipt or "native_actual" in receipt:
        return "skipped", False, receipt.get("reason")
    return "completed", True, receipt.get("reason")


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
        self._urgent_pending: dict[str, object] | None = None
        self._last: dict[str, object] | None = None
        self._recent_failures: deque[dict[str, object]] = deque(maxlen=16)
        self._last_failure_key: tuple | None = None

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
            "available": actual.get("available", False),
            "work_status": actual.get("work_status"),
            "reason": actual.get("reason"),
            "receipt": summary,
        }

    def schedule(self, payload: object = None, *, urgent: bool = False) -> dict[str, object]:
        """Coalesce ordinary work; retain one immediate pre-advance request."""
        start_thread = None
        with self._condition:
            if self._closed:
                return {"status": "unavailable", "reason": "camera worker closed"}
            self._sequence += 1
            request_id = f"auto-camera-{self._identity}-{self._sequence}"
            superseded = self._pending.get("request_id") if self._pending else None
            superseded_urgent = None
            eligible_at = (time.monotonic() if urgent else
                           self._pending["eligible_at"] if self._pending else
                           time.monotonic() + self._quiet_seconds)
            request = {
                "request_id": request_id,
                "eligible_at": eligible_at,
                "payload": payload,
                "urgent": urgent,
            }
            if urgent:
                superseded_urgent = (self._urgent_pending["request_id"]
                                     if self._urgent_pending else None)
                self._urgent_pending = request
                # An older ordinary frame must not run after this newer intent.
                self._pending = None
            else:
                self._pending = request
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
                    self._urgent_pending = None
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
            "superseded_urgent_request_id": superseded_urgent,
            "urgent": urgent,
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
            self._urgent_pending = None
            self._condition.notify_all()

    def _run(self) -> None:
        while True:
            with self._condition:
                while self._pending is None and self._urgent_pending is None and not self._closed:
                    self._condition.wait()
                if self._closed:
                    return
                request = self._urgent_pending if self._urgent_pending is not None else self._pending
                assert request is not None
                delay = float(request["eligible_at"]) - time.monotonic()
                if delay > 0:
                    self._condition.wait(timeout=delay)
                    continue
                if self._urgent_pending is request:
                    self._urgent_pending = None
                else:
                    self._pending = None
            started = time.monotonic()
            try:
                receipt = self._work(request["payload"])
                if receipt is None:
                    status, available, work_status, reason = "skipped", False, None, None
                elif isinstance(receipt, dict):
                    work_status = receipt.get("status")
                    status, available, reason = camera_receipt_outcome(receipt)
                else:
                    raise TypeError("camera work returned a non-dict receipt")
                actual = {
                    "schema": "xar.ck3.auto-camera-actual/v1",
                    "request_id": request["request_id"],
                    "urgent": request["urgent"],
                    "status": status,
                    "available": available,
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
                    "available": False,
                    "reason": f"{type(error).__name__}: {error}",
                    "elapsed_seconds": time.monotonic() - started,
                    "same_frame_with_gameplay_claim": False,
                }
            receipt = actual.get("receipt")
            native = receipt.get("native_actual") if isinstance(receipt, dict) else None
            failure_key = ((native.get("request_sequence"), native.get("status"))
                           if isinstance(native, dict) else (actual.get("reason"),))
            with self._condition:
                self._last = actual
                new_failure = (actual["status"] == "failed" and
                               failure_key != self._last_failure_key)
                if new_failure:
                    self._recent_failures.append(actual)
                    self._last_failure_key = failure_key
            if new_failure:
                _LOG.warning(
                    "ordinary camera failed request_id=%s reason=%s",
                    actual["request_id"], actual.get("reason"),
                )
            if self._on_complete is not None:
                try:
                    self._on_complete(dict(actual))
                except Exception as error:
                    _LOG.warning("ordinary camera completion observer failed: %s", error)

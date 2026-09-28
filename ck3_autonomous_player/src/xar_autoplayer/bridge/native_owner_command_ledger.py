"""Owner-side native request lifecycle evidence for a future cash producer.

This process-local ledger deliberately cannot prove a zero cash commitment.
It records protocol ownership and uncertainty without pricing any command.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
import threading


SCHEMA = "xar.ck3.native-owner-command-lifecycle.v1"
_OPEN = {"send_uncertain", "in_flight", "native_ok_unrecorded",
         "native_rejected_unrecorded", "outcome_unknown"}


class NativeOwnerCommandLedger:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._rows: dict[str, dict[str, object]] = {}
        self._sequence = 0
        self._history_epoch = 0

    def _event(self, row: dict[str, object], state: str) -> None:
        self._sequence += 1
        row["state"] = state
        row["events"].append({"sequence": self._sequence, "state": state})

    def begin(self, request_id: str, step: str, native_revision: int,
              *, source_frame: Mapping[str, object] | None = None) -> None:
        if (type(request_id) is not str or not request_id
                or type(step) is not str or not step
                or type(native_revision) is not int
                or native_revision < 0):
            raise ValueError("native request identity and revision required")
        with self._lock:
            if request_id in self._rows:
                raise ValueError("native request ID already registered")
            row: dict[str, object] = {
                "request_id": request_id, "step": step,
                "expected_native_revision": native_revision,
                "source_frame": (copy.deepcopy(dict(source_frame))
                                 if source_frame is not None else None),
                "native_ok": None, "late_native_ok": None,
                "history_index_at_record": None,
                "history_epoch_at_record": None,
                "history_link_invalidated": False,
                "history_ok": None, "events": [],
            }
            self._rows[request_id] = row
            self._event(row, "send_uncertain")

    def sent(self, request_id: str) -> None:
        with self._lock:
            row = self._rows[request_id]
            if row["state"] == "outcome_unknown":
                return
            if row["state"] != "send_uncertain":
                raise ValueError("native request send state changed")
            self._event(row, "in_flight")

    def response(self, request_id: str, *, native_ok: bool) -> None:
        if type(native_ok) is not bool:
            raise ValueError("native response result must be bool")
        with self._lock:
            row = self._rows[request_id]
            if row["state"] not in {"send_uncertain", "in_flight", "outcome_unknown"}:
                raise ValueError("native response already recorded")
            if row["state"] == "outcome_unknown":
                # A reply after timeout/reconnect cannot establish which
                # worker generation owned the original request.
                row["late_native_ok"] = native_ok
                self._sequence += 1
                row["events"].append({
                    "sequence": self._sequence,
                    "state": "late_response_after_uncertainty",
                })
                return
            row["native_ok"] = native_ok
            self._event(row, "native_ok_unrecorded" if native_ok
                        else "native_rejected_unrecorded")

    def unknown(self, request_id: str) -> None:
        with self._lock:
            row = self._rows[request_id]
            if row["state"] in _OPEN and row["state"] != "outcome_unknown":
                self._event(row, "outcome_unknown")

    def reconnect(self) -> None:
        with self._lock:
            for row in self._rows.values():
                if row["state"] in {"send_uncertain", "in_flight"}:
                    self._event(row, "outcome_unknown")

    def recorded(self, request_ids: tuple[str, ...], *, history_index: int,
                 history_ok: bool) -> None:
        if (type(history_index) is not int or history_index <= 0
                or type(history_ok) is not bool):
            raise ValueError("native history record identity required")
        with self._lock:
            for request_id in request_ids:
                row = self._rows[request_id]
                if row["state"] not in _OPEN:
                    raise ValueError("native request already linked to history")
            for request_id in request_ids:
                row = self._rows[request_id]
                row["history_index_at_record"] = history_index
                row["history_epoch_at_record"] = self._history_epoch
                row["history_ok"] = history_ok
                self._event(row, "history_recorded_cash_unreconciled")

    def history_rebased(self) -> None:
        """Invalidate positional links when the formal history is replaced."""
        with self._lock:
            self._history_epoch += 1
            for row in self._rows.values():
                if row["history_index_at_record"] is not None:
                    row["history_index_at_record"] = None
                    row["history_link_invalidated"] = True
                    self._sequence += 1
                    row["events"].append({
                        "sequence": self._sequence,
                        "state": "history_link_invalidated",
                    })

    def receipt(self) -> dict[str, object]:
        with self._lock:
            rows = copy.deepcopy(list(self._rows.values()))
            sequence = self._sequence
            history_epoch = self._history_epoch
        return {
            "schema": SCHEMA,
            "status": "incomplete_unpriced_process_local",
            "sequence": sequence,
            "history_epoch": history_epoch,
            "requests": rows,
            "unreconciled_request_ids": [row["request_id"] for row in rows],
            "in_flight_request_ids": [
                row["request_id"] for row in rows
                if row["state"] in {"send_uncertain", "in_flight"}
            ],
            "pending_war_cash_raw": None,
            "zero_pending_war_cash_proven": False,
            "continuity_across_driver_restart_proven": False,
            "history_index_stable_across_restore": False,
            "typed_history_link_complete": False,
            "scope": (
                "all _execute_primitive_step requests in this driver; "
                "formal history links cover execute_step only"
            ),
        }

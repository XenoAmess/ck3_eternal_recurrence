from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import threading
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.native_owner_command_ledger import NativeOwnerCommandLedger
from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot


class NativeOwnerCommandLedgerTests(unittest.TestCase):
    def test_empty_or_recorded_lifecycle_never_claims_zero_cash(self) -> None:
        ledger = NativeOwnerCommandLedger()
        self.assertIsNone(ledger.receipt()["pending_war_cash_raw"])
        self.assertIs(ledger.receipt()["zero_pending_war_cash_proven"], False)
        ledger.begin("r1", "war-action", 3)
        ledger.sent("r1")
        ledger.response("r1", native_ok=True)
        ledger.recorded(("r1",), history_index=1, history_ok=True)
        receipt = ledger.receipt()
        self.assertEqual(receipt["requests"][0]["state"],
                         "history_recorded_cash_unreconciled")
        self.assertEqual(receipt["unreconciled_request_ids"], ["r1"])
        self.assertIsNone(receipt["pending_war_cash_raw"])
        self.assertIs(receipt["continuity_across_driver_restart_proven"], False)
        self.assertEqual(receipt["requests"][0]["history_index_at_record"], 1)
        ledger.history_rebased()
        rebased = ledger.receipt()
        self.assertEqual(rebased["history_epoch"], 1)
        self.assertIsNone(rebased["requests"][0]["history_index_at_record"])
        self.assertIs(rebased["requests"][0]["history_link_invalidated"], True)

    def test_reconnect_leaves_unanswered_request_unknown(self) -> None:
        ledger = NativeOwnerCommandLedger()
        ledger.begin("r2", "war-action", 3)
        ledger.sent("r2")
        ledger.reconnect()
        self.assertEqual(ledger.receipt()["requests"][0]["state"],
                         "outcome_unknown")
        ledger.sent("r2")  # A late send return cannot erase reconnect uncertainty.
        self.assertEqual(ledger.receipt()["requests"][0]["state"],
                         "outcome_unknown")
        ledger.response("r2", native_ok=True)
        row = ledger.receipt()["requests"][0]
        self.assertEqual(row["state"], "outcome_unknown")
        self.assertIsNone(row["native_ok"])
        self.assertIs(row["late_native_ok"], True)


class NativeOwnerCommandDriverTests(unittest.TestCase):
    def driver(self, *, timeout: float = 0.05,
               state_dir: Path | None = None):
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name, endpoint=endpoint,
            command_timeout_seconds=timeout,
            state_dir=state_dir,
        )
        endpoint.publish(_hello("game.state.snapshot",
                                "game.command.cash-probe-noop"))
        endpoint.publish(_snapshot())
        return driver, endpoint

    def test_send_response_and_history_record_are_distinct(self) -> None:
        driver, endpoint = self.driver()
        entered = threading.Event()
        release = threading.Event()
        result: list[object] = []

        def answer(frame):
            if frame.get("type") != "execute_step":
                return
            entered.set()
            release.wait(2)
            endpoint.publish({
                "type": "command_result", "protocol_version": 1,
                "request_id": frame["request_id"], "ok": True,
                "result": {"accepted": True},
            })

        endpoint.send_hook = answer
        thread = threading.Thread(
            target=lambda: result.append(driver.execute_step("cash-probe-noop")),
            daemon=True,
        )
        try:
            thread.start()
            self.assertTrue(entered.wait(2))
            during_send = driver.owner_command_lifecycle_receipt_v1()
            self.assertEqual(during_send["requests"][0]["state"],
                             "send_uncertain")
            self.assertIsNone(during_send["pending_war_cash_raw"])
            release.set()
            thread.join(2)
            self.assertFalse(thread.is_alive())
            self.assertEqual(result[0]["accepted"], True)
            receipt = driver.owner_command_lifecycle_receipt_v1()
            row = receipt["requests"][0]
            self.assertEqual(row["state"], "history_recorded_cash_unreconciled")
            self.assertEqual(row["history_index_at_record"], 1)
            self.assertIs(receipt["history_index_stable_across_restore"], False)
            self.assertEqual(row["source_frame"]["native_revision"], 1)
            self.assertIs(row["native_ok"], True)
            self.assertIs(row["history_ok"], True)
            self.assertIsNone(receipt["pending_war_cash_raw"])
        finally:
            release.set()
            driver.close()

    def test_send_exception_and_timeout_remain_unknown(self) -> None:
        for failure in ("send", "timeout"):
            with self.subTest(failure=failure):
                driver, endpoint = self.driver(timeout=0.01)
                try:
                    if failure == "send":
                        endpoint.send_hook = lambda frame: (
                            (_ for _ in ()).throw(BridgeUnavailableError("send failed"))
                            if frame.get("type") == "execute_step" else None
                        )
                    with self.assertRaises(BridgeUnavailableError):
                        driver.execute_step("cash-probe-noop")
                    row = driver.owner_command_lifecycle_receipt_v1()["requests"][0]
                    states = [event["state"] for event in row["events"]]
                    self.assertIn("outcome_unknown", states)
                    self.assertIsNone(row["native_ok"])
                    self.assertIs(row["history_ok"], False)
                    self.assertEqual(row["state"],
                                     "history_recorded_cash_unreconciled")
                finally:
                    driver.close()

    def test_driver_reconnect_preserves_uncertain_generation(self) -> None:
        driver, endpoint = self.driver()

        def reconnect_and_answer(frame):
            if frame.get("type") != "execute_step":
                return
            endpoint.publish(_hello("game.state.snapshot",
                                    "game.command.cash-probe-noop"))
            endpoint.publish(_snapshot())
            endpoint.publish({
                "type": "command_result", "protocol_version": 1,
                "request_id": frame["request_id"], "ok": True,
                "result": {"accepted": True},
            })

        endpoint.send_hook = reconnect_and_answer
        try:
            driver.execute_step("cash-probe-noop")
            row = driver.owner_command_lifecycle_receipt_v1()["requests"][0]
            states = [event["state"] for event in row["events"]]
            self.assertIn("outcome_unknown", states)
            self.assertIn("late_response_after_uncertainty", states)
            self.assertIsNone(row["native_ok"])
            self.assertIs(row["late_native_ok"], True)
        finally:
            driver.close()

    def test_native_rejection_is_recorded_without_cash_zero(self) -> None:
        driver, endpoint = self.driver()

        def reject(frame):
            if frame.get("type") == "execute_step":
                endpoint.publish({
                    "type": "command_result", "protocol_version": 1,
                    "request_id": frame["request_id"], "ok": False,
                    "error": "native rejection",
                })

        endpoint.send_hook = reject
        try:
            with self.assertRaisesRegex(Exception, "native rejection"):
                driver.execute_step("cash-probe-noop")
            receipt = driver.owner_command_lifecycle_receipt_v1()
            row = receipt["requests"][0]
            self.assertIs(row["native_ok"], False)
            self.assertIs(row["history_ok"], False)
            self.assertEqual(row["state"], "history_recorded_cash_unreconciled")
            self.assertIsNone(receipt["pending_war_cash_raw"])
        finally:
            driver.close()

    def test_observer_faults_do_not_change_success_or_history(self) -> None:
        for operation in ("begin", "response", "recorded"):
            with self.subTest(operation=operation):
                temporary = tempfile.TemporaryDirectory()
                driver, endpoint = self.driver(state_dir=Path(temporary.name))

                def answer(frame):
                    if frame.get("type") == "execute_step":
                        endpoint.publish({
                            "type": "command_result", "protocol_version": 1,
                            "request_id": frame["request_id"], "ok": True,
                            "result": {"accepted": True},
                        })

                endpoint.send_hook = answer
                try:
                    with (mock.patch.object(
                        driver._owner_command_ledger, operation,
                        side_effect=RuntimeError("ledger fault"),
                    ), mock.patch.object(
                        driver, "_persist_driver_state",
                        wraps=driver._persist_driver_state,
                    ) as persist):
                        result = driver.execute_step("cash-probe-noop")
                    self.assertIs(result["accepted"], True)
                    sends = [row for row in endpoint.frames
                             if row.get("type") == "execute_step"]
                    self.assertEqual(len(sends), 1)
                    history = driver._history_snapshot()
                    self.assertEqual(len(history), 1)
                    self.assertIs(history[0]["ok"], True)
                    self.assertGreaterEqual(persist.call_count, 1)
                    if operation == "recorded":
                        persisted = json.loads((
                            Path(temporary.name) / "native-session"
                            / "driver-state.json"
                        ).read_text(encoding="utf-8"))
                        self.assertIs(
                            persisted["command_history"][-1]["ok"], True
                        )
                    receipt = driver.owner_command_lifecycle_receipt_v1()
                    self.assertEqual(receipt["status"], "incomplete_observer_error")
                    self.assertIsNone(receipt["pending_war_cash_raw"])
                    self.assertIs(receipt["zero_pending_war_cash_proven"], False)
                finally:
                    driver.close()
                    temporary.cleanup()

    def test_observer_fault_cannot_mask_native_rejection_or_send_failure(self) -> None:
        for original, observer_operation in (("rejection", "response"),
                                             ("send", "unknown")):
            with self.subTest(original=original):
                driver, endpoint = self.driver()

                def answer(frame):
                    if frame.get("type") != "execute_step":
                        return
                    if original == "send":
                        raise BridgeUnavailableError("send failed")
                    endpoint.publish({
                        "type": "command_result", "protocol_version": 1,
                        "request_id": frame["request_id"], "ok": False,
                        "error": "native rejection",
                    })

                endpoint.send_hook = answer
                try:
                    with mock.patch.object(
                        driver._owner_command_ledger, observer_operation,
                        side_effect=RuntimeError("ledger fault"),
                    ):
                        with self.assertRaisesRegex(
                            Exception,
                            "send failed" if original == "send"
                            else "native rejection",
                        ):
                            driver.execute_step("cash-probe-noop")
                    history = driver._history_snapshot()
                    self.assertEqual(len(history), 1)
                    self.assertIs(history[0]["ok"], False)
                    self.assertIn("send failed" if original == "send"
                                  else "native rejection", history[0]["error"])
                    receipt = driver.owner_command_lifecycle_receipt_v1()
                    self.assertEqual(receipt["status"], "incomplete_observer_error")
                    self.assertIsNone(receipt["pending_war_cash_raw"])
                finally:
                    driver.close()

    def test_reconnect_observer_fault_does_not_interrupt_hello(self) -> None:
        driver, endpoint = self.driver()
        try:
            with mock.patch.object(
                driver._owner_command_ledger, "reconnect",
                side_effect=RuntimeError("ledger fault"),
            ):
                endpoint.publish(_hello("game.state.snapshot",
                                        "game.command.cash-probe-noop"))
            endpoint.publish(_snapshot(2))
            self.assertEqual(driver.take_snapshot()["native_revision"], 2)
            self.assertEqual(
                driver.owner_command_lifecycle_receipt_v1()["status"],
                "incomplete_observer_error",
            )
        finally:
            driver.close()


if __name__ == "__main__":
    unittest.main()

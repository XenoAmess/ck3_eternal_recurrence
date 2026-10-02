"""No-launch check for the unadvertised paused sway read path."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.active_scheme_sway_private_transport import (
    SCHEMA, STEP_PREFIX, query_active_scheme_sway_target_private_v1,
)
from xar_autoplayer.bridge.driver import UnsupportedStepError


def snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "native:4", "revision": 5, "native_revision": 4,
        "date_raw": 53219928, "paused": True, "map_ready": True,
        "played_character": {"character_id": 29829, "alive": True},
    }


class Endpoint:
    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(request)


class State:
    def __init__(self, endpoint: Endpoint) -> None:
        self.endpoint = endpoint

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        request = self.endpoint.sent[-1]
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True,
            "result": {
                "step": request["step"], "accepted": True,
                "status": "available", "private_build": True,
                "read_only": True, "advertised": False,
                "backend_id": "native-headless",
                "active_scheme_sway": {
                    "schema": SCHEMA, "snapshot_revision": 4,
                    "capture_epoch": 8085, "container_generation": 17,
                    "date_raw": 53219928, "actor_character_id": 29829,
                    "target_character_id": 32716,
                    "target_opinion_of_actor": -25,
                    "active_scheme_count": 0,
                    "matching_sway_active": False,
                    "native_complete_can_send": True,
                    "native_legal_now": True,
                    "native_failure_classification": "",
                },
            },
        }


class Driver:
    def __init__(self, enabled: bool) -> None:
        self.allow_private_active_scheme_sway_query = enabled
        self.endpoint = Endpoint()
        self.state = State(self.endpoint)

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(snapshot())


class SwayPrivateTransportTest(unittest.TestCase):
    def test_paused_read_does_not_submit_action(self) -> None:
        driver = Driver(True)
        result = query_active_scheme_sway_target_private_v1(
            driver, expected_revision=5, target_character_id=32716,
        )
        self.assertTrue(result["native_legal_now"])
        self.assertEqual(result["target_opinion_of_actor"], -25)
        self.assertEqual(len(driver.endpoint.sent), 1)
        self.assertEqual(driver.endpoint.sent[0]["step"], STEP_PREFIX + "32716")
        self.assertEqual(driver.endpoint.sent[0]["expected_revision"], 4)

    def test_semantic_query_readers_preserve_values_and_history(self) -> None:
        import importlib.util
        import json
        import os
        from types import MethodType
        from unittest import mock
        from uuid import UUID

        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.player_lifestyle_private_transport_v1 import (
            query_player_lifestyle_private_v1,
        )
        from xar_autoplayer.bridge.current_first_heir_relationship_private_transport import (
            query_current_first_heir_relationship_private_v1,
        )
        from test_lifestyle_formal_private_consumer import _Driver as LifeDriver
        from test_current_first_heir_relationship_private_transport import (
            _Driver as FamilyDriver, _frame, _reply, _pair_value,
        )

        transcript = [{"index": index, "command": "retained-query",
                       "ok": True, "result": {"values": list(range(32))}}
                      for index in range(1, 65)]
        evidence_keys = {"native_command_history", "native_rollback_war_failure",
                         "native_rollback_war_failures"}

        def family_driver():
            return FamilyDriver(
                _reply(betrothed_character_id=38718, betrothal_actionability=_pair_value()),
                [deepcopy(_frame()) for _ in range(3)],
            )

        definitions = [
            ("sway", lambda: Driver(True), query_active_scheme_sway_target_private_v1,
             {"expected_revision": 5, "target_character_id": 32716}, 2,
             "active_scheme_sway_private_transport.py"),
            ("life", LifeDriver, query_player_lifestyle_private_v1,
             {"expected_revision": 3}, 2, "player_lifestyle_private_transport_v1.py"),
            ("family", family_driver, query_current_first_heir_relationship_private_v1,
             {"expected_native_revision": 3}, 3,
             "current_first_heir_relationship_private_transport.py"),
        ]

        def instrument(driver, use_internal):
            original_reader = driver.take_snapshot
            driver._command_history = deepcopy(transcript)
            if hasattr(driver, "history"):
                driver.history = driver._command_history
            counts = {"full": 0, "semantic": 0}

            def full_reader():
                counts["full"] += 1
                return {**original_reader(),
                        "native_command_history": deepcopy(driver._command_history)}

            driver.take_snapshot = full_reader
            if use_internal:
                # Native reader runs unchanged; only its game/episode producers are fixture data.
                driver.state.semantic_snapshot = lambda: {
                    key: value for key, value in original_reader().items()
                    if key not in evidence_keys
                }
                driver._transport_error = lambda: None
                driver._with_one_life_episode = lambda frame: frame
                driver._observe_arrange_marriage_outcome = lambda frame: None

                def internal_reader(self):
                    counts["semantic"] += 1
                    return NativeHeadlessGameplayDriver.take_internal_semantic_snapshot(self)

                driver.take_internal_semantic_snapshot = MethodType(internal_reader, driver)
            return counts

        def request(driver):
            if hasattr(driver.endpoint, "sent"):
                return driver.endpoint.sent
            if hasattr(driver.endpoint, "request"):
                return driver.endpoint.request
            return driver.state.last

        observed = {}
        for name, factory, production_query, kwargs, reads, filename in definitions:
            fallback = factory()
            fallback_counts = instrument(fallback, False)
            optimized = factory()
            optimized_counts = instrument(optimized, True)
            with mock.patch("uuid.uuid4", return_value=UUID(int=1)):
                original_value = production_query(fallback, **kwargs)
                optimized_value = production_query(optimized, **kwargs)
            self.assertEqual(optimized_value, original_value, name)
            self.assertEqual(request(optimized), request(fallback), name)
            self.assertEqual(fallback_counts, {"full": reads, "semantic": 0}, name)
            self.assertEqual(optimized_counts, {"full": 0, "semantic": reads}, name)
            self.assertEqual(fallback._command_history, transcript, name)
            self.assertEqual(optimized._command_history, transcript, name)
            observed[name] = {"fallback_full": reads, "optimized_full": 0,
                              "semantic_reads": reads, "history_retained": True}

            # Optional archived-source comparison is used only by the external receipt run.
            baseline_dir = os.environ.get("G2_SEMANTIC_QUERY_BASELINE_PATH")
            if baseline_dir:
                module_name = "xar_autoplayer.bridge._semantic_query_baseline_" + name
                spec = importlib.util.spec_from_file_location(
                    module_name, Path(baseline_dir) / filename,
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                baseline_query = getattr(module, production_query.__name__)
                archived = factory()
                archived_counts = instrument(archived, True)
                with mock.patch("uuid.uuid4", return_value=UUID(int=1)):
                    baseline_value = baseline_query(archived, **kwargs)
                self.assertEqual(baseline_value, optimized_value, name)
                self.assertEqual(request(archived), request(optimized), name)
                self.assertEqual(archived_counts, {"full": reads, "semantic": 0}, name)
                self.assertEqual(archived._command_history, transcript, name)
                observed[name]["frozen_baseline_full"] = archived_counts["full"]

        self.assertEqual(sum(item["optimized_full"] for item in observed.values()), 0)
        self.assertEqual(sum(item["fallback_full"] for item in observed.values()), 7)
        print("SEMANTIC_QUERY_REPLAY=" + json.dumps(observed, sort_keys=True))

    def test_default_off_rejects_before_wire(self) -> None:
        driver = Driver(False)
        with self.assertRaises(UnsupportedStepError):
            query_active_scheme_sway_target_private_v1(
                driver, expected_revision=5, target_character_id=32716,
            )
        self.assertEqual(driver.endpoint.sent, [])

    def test_missing_opinion_is_not_a_legal_value_input(self) -> None:
        driver = Driver(True)
        original = driver.state.wait_for_command_result
        def without_opinion(request_id: str, timeout: float) -> dict[str, object]:
            frame = original(request_id, timeout)
            del frame["result"]["active_scheme_sway"]["target_opinion_of_actor"]
            return frame
        driver.state.wait_for_command_result = without_opinion
        from xar_autoplayer.bridge.driver import BridgeUnavailableError
        with self.assertRaises(BridgeUnavailableError):
            query_active_scheme_sway_target_private_v1(
                driver, expected_revision=5, target_character_id=32716,
            )


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3

from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUTOPLAYER_SRC = ROOT / "ck3_autonomous_player" / "src"
if str(AUTOPLAYER_SRC) not in sys.path:
    sys.path.insert(0, str(AUTOPLAYER_SRC))

from xar_autoplayer.bridge.driver import (  # noqa: E402
    BridgeUnavailableError,
)
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
    _checkpoint_history_index,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402


def _snapshot(
    *, pid: int, generation: int, player: int, date_raw: int
) -> dict[str, object]:
    return {
        "snapshot_id": f"native:{generation}",
        "revision": generation * 10,
        "native_revision": generation * 100,
        "paused": True,
        "map_ready": True,
        "date_raw": date_raw,
        "played_character": {"character_id": player, "alive": True},
        "diagnostics": {
            "bridge_pid": pid,
            "connection_generation": generation,
        },
    }


class Phase2SpanSourceCheckpointBridgeTests(unittest.TestCase):
    def test_native_driver_route_b_restore_keeps_fixture_provenance_explicit(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = (root / "registry" / "route-b.ck3").resolve()
            source.parent.mkdir()
            source.write_bytes(b"real-route-b-checkpoint")
            sha256 = hashlib.sha256(source.read_bytes()).hexdigest().upper()
            save_dir = root / "profile" / "save games"
            save_dir.mkdir(parents=True)
            driver = object.__new__(NativeHeadlessGameplayDriver)
            driver.state_dir = root / "state"
            driver.save_dir = save_dir
            driver._driver_state_lock = threading.RLock()
            driver._phase2_source_restore_lock = threading.Lock()
            driver._command_history = []
            driver._last_checkpoint = None
            driver._rollback_war_failures = []
            driver._rollback_war_failures_migration_required = False
            driver._episode_character_id = 7001
            driver._episode_run_id = "native-live-run"
            driver._session_bridge_pid = 3100
            driver._driver_state_dirty = False
            driver._persist_driver_state = types.MethodType(
                lambda self: None, driver
            )
            state = {"restored": False}

            def take_snapshot(
                self: NativeHeadlessGameplayDriver,
            ) -> dict[str, object]:
                return _snapshot(
                    pid=3200 if state["restored"] else 3100,
                    generation=8 if state["restored"] else 7,
                    player=8801 if state["restored"] else 7001,
                    date_raw=777 if state["restored"] else 700,
                )

            def execute_step(
                self: NativeHeadlessGameplayDriver,
                step: str,
                *,
                expected_revision: int | None = None,
            ) -> dict[str, object]:
                if step != "restore-checkpoint" or expected_revision != 70:
                    raise AssertionError("Route-B restore escaped managed restore")
                state["restored"] = True
                return {
                    "checkpoint": {
                        "status": "restored",
                        "size": source.stat().st_size,
                        "sha256": sha256.lower(),
                    },
                    "restored_date_raw": 777,
                    "lifecycle": {
                        "lifecycle_intent": "restore",
                        "previous_pid": 3100,
                        "pid": 3200,
                        "previous_connection_generation": 7,
                        "connection_generation": 8,
                    },
                }

            driver.take_snapshot = types.MethodType(take_snapshot, driver)
            driver.execute_step = types.MethodType(execute_step, driver)
            receipt = driver.restore_hc_workforce_route_b_checkpoint_v1(
                checkpoint_path=str(source),
                expected_checkpoint_bytes=source.stat().st_size,
                expected_checkpoint_sha256=sha256,
                expected_save_lineage_id="zg361-phase2-seed-test",
                expected_event_definition_key="zg361we.360",
                expected_owner_character_id=8801,
                expected_player_character_id=8801,
                expected_date_raw=777,
            )

            self.assertEqual("GREEN", receipt["result"])
            self.assertTrue(receipt["fixture_used"])
            self.assertFalse(receipt["console_used"])
            self.assertEqual(
                "phase2-hc-workforce-route-b-registry-v1",
                driver._last_checkpoint["strategy"],
            )

    def test_native_driver_stages_registry_bytes_then_reuses_restore_lifecycle(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = (root / "registry" / "promotion.ck3").resolve()
            source.parent.mkdir()
            source.write_bytes(b"real-registry-checkpoint")
            sha256 = hashlib.sha256(source.read_bytes()).hexdigest().upper()
            save_dir = root / "profile" / "save games"
            save_dir.mkdir(parents=True)

            driver = object.__new__(NativeHeadlessGameplayDriver)
            driver.state_dir = root / "state"
            driver.save_dir = save_dir
            driver._driver_state_lock = threading.RLock()
            driver._phase2_source_restore_lock = threading.Lock()
            driver._command_history = []
            driver._last_checkpoint = None
            driver._rollback_war_failures = []
            driver._rollback_war_failures_migration_required = False
            driver._episode_character_id = 7001
            driver._episode_run_id = "native-live-run"
            driver._session_bridge_pid = 3100
            driver._driver_state_dirty = False
            driver._persist_driver_state = types.MethodType(lambda self: None, driver)
            state = {"restored": False}

            def take_snapshot(self: NativeHeadlessGameplayDriver) -> dict[str, object]:
                return _snapshot(
                    pid=3200 if state["restored"] else 3100,
                    generation=8 if state["restored"] else 7,
                    player=8801 if state["restored"] else 7001,
                    date_raw=777 if state["restored"] else 700,
                )

            def execute_step(
                self: NativeHeadlessGameplayDriver,
                step: str,
                *,
                expected_revision: int | None = None,
            ) -> dict[str, object]:
                if step != "restore-checkpoint" or expected_revision != 70:
                    raise AssertionError("typed source restore escaped restore-checkpoint")
                managed = save_dir / "xar_checkpoint.ck3"
                if managed.read_bytes() != source.read_bytes():
                    raise AssertionError("registry bytes were not staged")
                state["restored"] = True
                return {
                    "checkpoint": {
                        "status": "restored",
                        "size": source.stat().st_size,
                        "sha256": sha256.lower(),
                    },
                    "restored_date_raw": 777,
                    "lifecycle": {
                        "lifecycle_intent": "restore",
                        "previous_pid": 3100,
                        "pid": 3200,
                        "previous_connection_generation": 7,
                        "connection_generation": 8,
                    },
                }

            driver.take_snapshot = types.MethodType(take_snapshot, driver)
            driver.execute_step = types.MethodType(execute_step, driver)

            receipt = driver.restore_phase2_span_source_checkpoint_v1(
                checkpoint_path=str(source),
                expected_checkpoint_bytes=source.stat().st_size,
                expected_checkpoint_sha256=sha256,
                expected_save_lineage_id="zg361-phase2-seed-test",
                expected_event_definition_key="zg361pp.147",
                expected_owner_character_id=9901,
                expected_player_character_id=8801,
                expected_date_raw=777,
                allow_generic_character_rebind=False,
                allow_fixture=False,
                allow_console=False,
            )

            self.assertEqual(receipt["result"], "GREEN")
            self.assertEqual(receipt["checkpoint_sha256"], sha256)
            self.assertEqual(receipt["player_character_id"], 8801)
            self.assertEqual(receipt["owner_character_id"], 9901)
            self.assertEqual(receipt["event_definition_key"], "zg361pp.147")
            self.assertEqual(
                receipt["event_identity_validation"],
                "runner_exact_query_required",
            )
            self.assertFalse(receipt["generic_character_rebind_used"])
            anchor = driver._last_checkpoint
            self.assertEqual(
                _checkpoint_history_index(anchor, driver._command_history), 1
            )
            self.assertTrue(
                driver._cold_candidate_ready(
                    {
                        "format_version": 2,
                        "episode_character_id": 8801,
                        "episode_run_id": "native-live-run",
                        "command_history": driver._command_history,
                        "last_checkpoint": anchor,
                    }
                )
            )
            self.assertEqual(
                anchor["save_lineage_id"], "zg361-phase2-seed-test"
            )
            self.assertEqual(anchor["date_raw"], 777)
            self.assertEqual(
                (save_dir / "xar_checkpoint.ck3").read_bytes(),
                source.read_bytes(),
            )

    def test_native_driver_rejects_drift_before_overwriting_managed_checkpoint(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = (root / "source.ck3").resolve()
            source.write_bytes(b"source")
            save_dir = root / "save games"
            save_dir.mkdir()
            managed = save_dir / "xar_checkpoint.ck3"
            managed.write_bytes(b"keep-me")
            driver = object.__new__(NativeHeadlessGameplayDriver)
            driver.state_dir = root / "state"
            driver.save_dir = save_dir
            driver._phase2_source_restore_lock = threading.Lock()

            with self.assertRaises(BridgeUnavailableError):
                driver.restore_phase2_span_source_checkpoint_v1(
                    checkpoint_path=str(source),
                    expected_checkpoint_bytes=source.stat().st_size,
                    expected_checkpoint_sha256="0" * 64,
                    expected_save_lineage_id="seed",
                    expected_event_definition_key="zg361pp.147",
                    expected_owner_character_id=1,
                    expected_player_character_id=1,
                    expected_date_raw=1,
                    allow_generic_character_rebind=False,
                    allow_fixture=False,
                    allow_console=False,
                )
            self.assertEqual(managed.read_bytes(), b"keep-me")

    def test_service_requires_typed_lifecycle_ack(self) -> None:
        class Driver:
            def restore_phase2_span_source_checkpoint_v1(
                self, **kwargs: object
            ) -> dict[str, object]:
                return {
                    "result": "GREEN",
                    "provider_observed": True,
                    "restore_materialized": True,
                    "checkpoint_sha256": str(
                        kwargs["expected_checkpoint_sha256"]
                    ).upper(),
                    "checkpoint_bytes": kwargs["expected_checkpoint_bytes"],
                    "save_lineage_id": kwargs["expected_save_lineage_id"],
                    "event_definition_key": kwargs[
                        "expected_event_definition_key"
                    ],
                    "owner_character_id": kwargs[
                        "expected_owner_character_id"
                    ],
                    "player_character_id": kwargs[
                        "expected_player_character_id"
                    ],
                    "date_raw": kwargs["expected_date_raw"],
                    "fixture_used": False,
                    "console_used": False,
                    "generic_character_rebind_used": False,
                    "lifecycle": {
                        "lifecycle_intent": "restore",
                        "previous_pid": 10,
                        "pid": 11,
                        "previous_connection_generation": 4,
                        "connection_generation": 5,
                    },
                }

        service = GameplayBridgeService(Driver())
        self.assertTrue(
            service.phase2_span_source_checkpoint_restore_available_v1()
        )
        receipt = service.restore_phase2_span_source_checkpoint_v1(
            checkpoint_path="C:/registry/source.ck3",
            expected_checkpoint_bytes=123,
            expected_checkpoint_sha256="A" * 64,
            expected_save_lineage_id="seed",
            expected_event_definition_key="zg361mg.100",
            expected_owner_character_id=1,
            expected_player_character_id=2,
            expected_date_raw=3,
            allow_generic_character_rebind=False,
            allow_fixture=False,
            allow_console=False,
        )
        self.assertEqual(receipt["result"], "GREEN")

        with self.assertRaises(BridgeUnavailableError):
            service.restore_phase2_span_source_checkpoint_v1(
                checkpoint_path="C:/registry/source.ck3",
                expected_checkpoint_bytes=123,
                expected_checkpoint_sha256="A" * 64,
                expected_save_lineage_id="seed",
                expected_event_definition_key="zg361mg.100",
                expected_owner_character_id=1,
                expected_player_character_id=2,
                expected_date_raw=3,
                allow_generic_character_rebind=True,
                allow_fixture=False,
                allow_console=False,
            )

        unavailable = GameplayBridgeService(object())
        self.assertFalse(
            unavailable.phase2_span_source_checkpoint_restore_available_v1()
        )

    def test_service_route_b_restore_requires_fixture_typed_receipt(self) -> None:
        class Driver:
            def restore_hc_workforce_route_b_checkpoint_v1(
                self, **kwargs: object
            ) -> dict[str, object]:
                return {
                    "result": "GREEN",
                    "provider_observed": True,
                    "restore_materialized": True,
                    "checkpoint_sha256": str(
                        kwargs["expected_checkpoint_sha256"]
                    ).upper(),
                    "checkpoint_bytes": kwargs["expected_checkpoint_bytes"],
                    "save_lineage_id": kwargs["expected_save_lineage_id"],
                    "event_definition_key": "zg361we.360",
                    "owner_character_id": kwargs[
                        "expected_owner_character_id"
                    ],
                    "player_character_id": kwargs[
                        "expected_player_character_id"
                    ],
                    "date_raw": kwargs["expected_date_raw"],
                    "fixture_used": True,
                    "console_used": False,
                    "generic_character_rebind_used": False,
                    "lifecycle": {
                        "lifecycle_intent": "restore",
                        "previous_pid": 10,
                        "pid": 11,
                        "previous_connection_generation": 4,
                        "connection_generation": 5,
                    },
                }

        service = GameplayBridgeService(Driver())
        self.assertTrue(
            service.hc_workforce_route_b_checkpoint_restore_available_v1()
        )
        receipt = service.restore_hc_workforce_route_b_checkpoint_v1(
            checkpoint_path="C:/registry/route-b.ck3",
            expected_checkpoint_bytes=123,
            expected_checkpoint_sha256="A" * 64,
            expected_save_lineage_id="seed",
            expected_event_definition_key="zg361we.360",
            expected_owner_character_id=1,
            expected_player_character_id=1,
            expected_date_raw=3,
        )
        self.assertTrue(receipt["fixture_used"])

        with self.assertRaises(BridgeUnavailableError):
            service.restore_hc_workforce_route_b_checkpoint_v1(
                checkpoint_path="C:/registry/route-b.ck3",
                expected_checkpoint_bytes=123,
                expected_checkpoint_sha256="A" * 64,
                expected_save_lineage_id="seed",
                expected_event_definition_key="zg361we.359",
                expected_owner_character_id=1,
                expected_player_character_id=1,
                expected_date_raw=3,
            )


if __name__ == "__main__":
    unittest.main()

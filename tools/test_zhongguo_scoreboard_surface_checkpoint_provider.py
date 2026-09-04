#!/usr/bin/env python3

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
AUTOPLAYER = ROOT / "ck3_autonomous_player"
UNIT_TESTS = AUTOPLAYER / "tests" / "unit"
for import_root in (TOOLS, AUTOPLAYER / "src", UNIT_TESTS):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from test_zhongguo_scoreboard_action_contract import (  # noqa: E402
    _frame,
)
from test_zhongguo_scoreboard_state_contract import typed  # noqa: E402
from xar_autoplayer.bridge.driver import BridgeUnavailableError  # noqa: E402
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from zhongguo_scoreboard_surface_checkpoint_provider import (  # noqa: E402
    SCOREBOARD_REQUIRED_SURFACES,
    ScoreboardSurfaceCheckpointError,
    ScoreboardSurfaceCheckpointProvider,
)
from zhongguo_scoreboard_surface_checkpoint_registry import (  # noqa: E402
    ScoreboardSurfaceCheckpointRegistryBuildError,
    ScoreboardSurfaceCheckpointRegistryBuilder,
    capture_current_zhongguo_scoreboard_surface_v1,
)


PLAYER = 101
DATE_RAW = 4242
PUBLIC_REVISION = 19
NATIVE_REVISION = 77
SEED_SHA256 = "A" * 64
SEED_LINEAGE_ID = f"zg361-phase2-seed-{SEED_SHA256.lower()}"


def _query(
    surface_id: str,
    *,
    request_nonce: str,
    connection_generation: int,
    provider_session_id: str,
) -> dict[str, object]:
    entry = "managed" if surface_id == "managed-capable" else "received"
    value = _frame(open_tab=None, entry_tab=entry)
    value["request_nonce"] = request_nonce
    value["date_raw"] = DATE_RAW
    value["player_character_id"] = PLAYER
    value["provider_session_id"] = provider_session_id
    if surface_id == "managed-capable":
        managed = value["acl"]["managed"]
        managed["surface_available"] = True
        managed["current_player_can_assess_others"] = True
        managed["owner_character_id"] = typed(PLAYER)
        managed["first_subject_character_id"] = typed(303)
    value["binding"] = {
        "request_nonce": request_nonce,
        "snapshot_id": f"native:{NATIVE_REVISION}",
        "revision": PUBLIC_REVISION,
        "native_revision": NATIVE_REVISION,
        "connection_generation": connection_generation,
        "date_raw": DATE_RAW,
        "paused": True,
        "player_character_id": PLAYER,
        "expected_revision": PUBLIC_REVISION,
    }
    value["source"] = {
        "bridge_version": "0.1.0",
        "game_adapter_id": "ck3-1.19.0.6-msvc-x64",
        "backend_id": "native-headless",
        "consumer_id": "xar-autoplayer-zhongguo-scoreboard-state-v1",
        "connection_generation": connection_generation,
        "query_sequence": 1,
        "snapshot_id": f"native:{NATIVE_REVISION}",
        "revision": PUBLIC_REVISION,
        "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "player_character_id": PLAYER,
    }
    return value


def _snapshot(*, pid: int, generation: int) -> dict[str, object]:
    return {
        "snapshot_id": f"native:{NATIVE_REVISION}",
        "revision": PUBLIC_REVISION,
        "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "map_ready": True,
        "active_event": None,
        "played_character": {"character_id": PLAYER},
        "diagnostics": {
            "bridge_pid": pid,
            "connection_generation": generation,
        },
    }


class _CaptureService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.pid = 4100
        self.generation = 3
        self.surface_id = "managed-capable"
        self.save_path = root / "xar_checkpoint.ck3"

    def snapshot(self) -> dict[str, object]:
        return _snapshot(pid=self.pid, generation=self.generation)

    def query_zhongguo_scoreboard_state_v1(
        self, request_nonce: str, *, expected_revision: int
    ) -> dict[str, object]:
        if expected_revision != PUBLIC_REVISION:
            raise AssertionError("unexpected revision")
        return _query(
            self.surface_id,
            request_nonce=request_nonce,
            connection_generation=self.generation,
            provider_session_id=f"{self.generation:032X}",
        )

    def save_checkpoint(self, *, expected_revision: int) -> dict[str, object]:
        if expected_revision != PUBLIC_REVISION:
            raise AssertionError("unexpected save revision")
        self.save_path.write_bytes(
            f"real-ck3-{self.surface_id}".encode("ascii")
        )
        sha256 = hashlib.sha256(self.save_path.read_bytes()).hexdigest().upper()
        return {
            "accepted": True,
            "backend_id": "native-headless",
            "checkpoint": {
                "status": "saved",
                "path": str(self.save_path.resolve()),
                "size": self.save_path.stat().st_size,
                "sha256": sha256,
                "date_raw": DATE_RAW,
                "strategy": "native-autosave-command-v1",
            },
            "materialization": {"available": True},
        }


class _RestoreService:
    def __init__(self) -> None:
        self.pid = 5100
        self.generation = 9
        self.surface_id = "managed-capable"

    def snapshot(self) -> dict[str, object]:
        return _snapshot(pid=self.pid, generation=self.generation)

    def query_zhongguo_scoreboard_state_v1(
        self, request_nonce: str, *, expected_revision: int
    ) -> dict[str, object]:
        if expected_revision != PUBLIC_REVISION:
            raise AssertionError("unexpected revision")
        return _query(
            self.surface_id,
            request_nonce=request_nonce,
            connection_generation=self.generation,
            provider_session_id=f"{self.generation + 100:032X}",
        )

    def restore_phase2_span_source_checkpoint_v1(
        self, **arguments: object
    ) -> dict[str, object]:
        previous_pid = self.pid
        previous_generation = self.generation
        event_key = str(arguments["expected_event_definition_key"])
        self.surface_id = event_key.split(":", 1)[1]
        self.pid += 1
        self.generation += 1
        return {
            "schema_version": 1,
            "result": "GREEN",
            "provider_observed": True,
            "restore_materialized": True,
            "checkpoint_sha256": arguments["expected_checkpoint_sha256"],
            "checkpoint_bytes": arguments["expected_checkpoint_bytes"],
            "save_lineage_id": arguments["expected_save_lineage_id"],
            "event_definition_key": event_key,
            "owner_character_id": arguments["expected_owner_character_id"],
            "player_character_id": arguments["expected_player_character_id"],
            "date_raw": arguments["expected_date_raw"],
            "lifecycle": {
                "lifecycle_intent": "restore",
                "previous_pid": previous_pid,
                "pid": self.pid,
                "previous_connection_generation": previous_generation,
                "connection_generation": self.generation,
            },
            "fixture_used": False,
            "console_used": False,
            "generic_character_rebind_used": False,
        }


def _builder(root: Path) -> ScoreboardSurfaceCheckpointRegistryBuilder:
    return ScoreboardSurfaceCheckpointRegistryBuilder(
        root / "frozen",
        seed_lineage_id=SEED_LINEAGE_ID,
        capture_lineage={
            "seed_lineage_id": SEED_LINEAGE_ID,
            "evidence_class": "real_ck3",
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
            "generic_character_rebind_used": False,
        },
    )


def _capture_registry(root: Path) -> dict[str, object]:
    builder = _builder(root)
    service = _CaptureService(root)
    for surface_id in SCOREBOARD_REQUIRED_SURFACES:
        service.surface_id = surface_id
        capture_current_zhongguo_scoreboard_surface_v1(
            service, builder, surface_id
        )
    return builder.finalize()


class ScoreboardSurfaceCheckpointTests(unittest.TestCase):
    def test_live_builder_captures_both_surfaces_and_provider_restores_them(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = _capture_registry(root)
            self.assertEqual(
                [row["surface_id"] for row in registry["entries"]],
                list(SCOREBOARD_REQUIRED_SURFACES),
            )
            self.assertTrue(
                all(
                    row["capture_checks"]
                    ["action_ack_used_as_state_evidence"]
                    is False
                    for row in registry["entries"]
                )
            )

            service = _RestoreService()
            provider = ScoreboardSurfaceCheckpointProvider(
                registry,
                service=service,
                expected_seed_lineage_id=SEED_LINEAGE_ID,
            )
            self.assertEqual(provider.preflight()["result"], "GREEN")
            for surface_id in SCOREBOARD_REQUIRED_SURFACES:
                receipt = provider.prepare_zhongguo_scoreboard_surface_v1(
                    surface_id
                )
                self.assertEqual(receipt["status"], "ready")
                self.assertTrue(receipt["modal_page_acl_observed"])
                self.assertFalse(receipt["action_ack_used_as_postcondition"])
                self.assertNotEqual(
                    receipt["source_checkpoint_query"]["provider_session_id"],
                    receipt["post_restore_query"]["provider_session_id"],
                )

    def test_builder_rejects_ack_only_modal_open_and_incomplete_registry(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder = _builder(root)
            service = _CaptureService(root)
            original = service.query_zhongguo_scoreboard_state_v1

            def ack_only(
                request_nonce: str, *, expected_revision: int
            ) -> dict[str, object]:
                return {"accepted": True, "action_ack": {"status": "ok"}}

            service.query_zhongguo_scoreboard_state_v1 = ack_only  # type: ignore[method-assign]
            with self.assertRaises(
                ScoreboardSurfaceCheckpointRegistryBuildError
            ) as raised:
                capture_current_zhongguo_scoreboard_surface_v1(
                    service, builder, "managed-capable"
                )
            self.assertEqual(
                raised.exception.reason_code,
                "scoreboard_surface_capture_observation_invalid",
            )

            service.query_zhongguo_scoreboard_state_v1 = original  # type: ignore[method-assign]

            def modal_open(
                request_nonce: str, *, expected_revision: int
            ) -> dict[str, object]:
                value = original(
                    request_nonce, expected_revision=expected_revision
                )
                modal = next(
                    row
                    for row in value["widgets"]
                    if row["stable_identity"] == "zg361_scoreboard_modal"
                )
                modal["effective_visible"] = typed(True)
                return value

            service.query_zhongguo_scoreboard_state_v1 = modal_open  # type: ignore[method-assign]
            with self.assertRaises(
                ScoreboardSurfaceCheckpointRegistryBuildError
            ):
                capture_current_zhongguo_scoreboard_surface_v1(
                    service, builder, "managed-capable"
                )
            with self.assertRaises(
                ScoreboardSurfaceCheckpointRegistryBuildError
            ) as raised:
                builder.finalize()
            self.assertEqual(
                raised.exception.reason_code,
                "scoreboard_surface_registry_incomplete",
            )

    def test_provider_fails_closed_on_hash_acl_and_post_restore_event_drift(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = _capture_registry(root)
            first = registry["entries"][0]
            Path(first["checkpoint"]["path"]).write_bytes(b"drift")
            provider = ScoreboardSurfaceCheckpointProvider(
                registry,
                service=_RestoreService(),
                expected_seed_lineage_id=SEED_LINEAGE_ID,
            )
            with self.assertRaises(ScoreboardSurfaceCheckpointError) as raised:
                provider.preflight()
            self.assertEqual(
                raised.exception.reason_code,
                "scoreboard_surface_checkpoint_entry_invalid",
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = _capture_registry(root)
            received = registry["entries"][1]["source_query"]["acl"][
                "received_self"
            ]
            received["b1_case_serial"] = {
                "status": "unavailable",
                "value": None,
                "unavailable_reason": "variable_absent",
            }
            provider = ScoreboardSurfaceCheckpointProvider(
                registry,
                service=_RestoreService(),
                expected_seed_lineage_id=SEED_LINEAGE_ID,
            )
            with self.assertRaises(ScoreboardSurfaceCheckpointError):
                provider.preflight()

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = _capture_registry(root)
            service = _RestoreService()
            original_snapshot = service.snapshot

            def event_snapshot() -> dict[str, object]:
                value = original_snapshot()
                value["active_event"] = {"instance_id": 5}
                return value

            service.snapshot = event_snapshot  # type: ignore[method-assign]
            provider = ScoreboardSurfaceCheckpointProvider(
                registry,
                service=service,
                expected_seed_lineage_id=SEED_LINEAGE_ID,
            )
            receipt = provider.prepare_zhongguo_scoreboard_surface_v1(
                "managed-capable"
            )
            self.assertEqual(receipt["status"], "unavailable")
            self.assertEqual(
                receipt["failure_reason"],
                "scoreboard_surface_snapshot_not_event_free_paused",
            )

    def test_service_named_method_is_unavailable_until_bound_and_single_bind(
        self,
    ) -> None:
        class Driver:
            pass

        service = GameplayBridgeService(Driver())  # type: ignore[arg-type]
        unavailable = service.prepare_zhongguo_scoreboard_surface_v1(
            "managed-capable"
        )
        self.assertEqual(unavailable["status"], "unavailable")
        self.assertFalse(unavailable["action_ack_used_as_postcondition"])
        service.bind_zhongguo_scoreboard_surface_preparer_v1(
            lambda surface_id: {"surface_id": surface_id, "status": "ready"}
        )
        self.assertEqual(
            service.prepare_zhongguo_scoreboard_surface_v1(
                "managed-capable"
            )["status"],
            "ready",
        )
        with self.assertRaises(BridgeUnavailableError):
            service.bind_zhongguo_scoreboard_surface_preparer_v1(lambda _: {})

    def test_registry_lineage_and_order_are_strict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(
                ScoreboardSurfaceCheckpointRegistryBuildError
            ):
                ScoreboardSurfaceCheckpointRegistryBuilder(
                    root,
                    seed_lineage_id=SEED_LINEAGE_ID,
                    capture_lineage={"seed_lineage_id": SEED_LINEAGE_ID},
                )
            builder = _builder(root)
            service = _CaptureService(root)
            service.surface_id = "received-only"
            with self.assertRaises(
                ScoreboardSurfaceCheckpointRegistryBuildError
            ) as raised:
                capture_current_zhongguo_scoreboard_surface_v1(
                    service, builder, "received-only"
                )
            self.assertEqual(
                raised.exception.reason_code,
                "scoreboard_surface_record_order_invalid",
            )



if __name__ == "__main__":
    unittest.main()

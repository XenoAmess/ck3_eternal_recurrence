#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
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

from test_zhongguo_scoreboard_action_contract import _frame  # noqa: E402
from test_zhongguo_scoreboard_state_contract import typed  # noqa: E402
from zhongguo_scoreboard_surface_capture_orchestration import (  # noqa: E402
    ScoreboardSurfaceCaptureOrchestrationError,
    capture_managed_received_scoreboard_surfaces_v1,
)
from zhongguo_scoreboard_surface_checkpoint_registry import (  # noqa: E402
    ScoreboardSurfaceCheckpointRegistryBuilder,
)


OWNER = 101
SUBJECT = 303
DATE_RAW = 4242
SEED_LINEAGE_ID = "zg361-phase2-seed-" + "a" * 64


def _snapshot(
    *, player: int, revision: int, native_revision: int
) -> dict[str, object]:
    return {
        "snapshot_id": f"native:{native_revision}",
        "revision": revision,
        "native_revision": native_revision,
        "date_raw": DATE_RAW,
        "paused": True,
        "map_ready": True,
        "active_event": None,
        "played_character": {"character_id": player},
        "diagnostics": {
            "bridge_pid": 4100,
            "connection_generation": 3,
        },
    }


def _query(
    surface_id: str,
    *,
    request_nonce: str,
    player: int,
    revision: int,
    native_revision: int,
) -> dict[str, object]:
    entry = "managed" if surface_id == "managed-capable" else "received"
    value = _frame(open_tab=None, entry_tab=entry)
    value.update(
        {
            "request_nonce": request_nonce,
            "snapshot_revision": native_revision,
            "date_raw": DATE_RAW,
            "player_character_id": player,
            "provider_session_id": "3" * 32,
        }
    )
    if surface_id == "managed-capable":
        managed = value["acl"]["managed"]
        managed.update(
            {
                "surface_available": True,
                "current_player_can_assess_others": True,
                "owner_character_id": typed(OWNER),
                "first_subject_character_id": typed(SUBJECT),
            }
        )
    else:
        received = value["acl"]["received_self"]
        received.update(
            {
                "first_row_character_id": typed(SUBJECT),
                "owner_character_id": typed(OWNER),
                "subject_character_id": typed(SUBJECT),
            }
        )
    value["binding"] = {
        "request_nonce": request_nonce,
        "snapshot_id": f"native:{native_revision}",
        "revision": revision,
        "native_revision": native_revision,
        "connection_generation": 3,
        "date_raw": DATE_RAW,
        "paused": True,
        "player_character_id": player,
        "expected_revision": revision,
    }
    value["source"] = {
        "bridge_version": "0.1.0",
        "game_adapter_id": "ck3-1.19.0.6-msvc-x64",
        "backend_id": "native-headless",
        "consumer_id": "xar-autoplayer-zhongguo-scoreboard-state-v1",
        "connection_generation": 3,
        "query_sequence": 1,
        "snapshot_id": f"native:{native_revision}",
        "revision": revision,
        "native_revision": native_revision,
        "date_raw": DATE_RAW,
        "paused": True,
        "player_character_id": player,
    }
    return value


class _Service:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.player = OWNER
        self.surface_id = "managed-capable"
        self.revision = 19
        self.native_revision = 77
        self.received_query_mutator = None

    def snapshot(self) -> dict[str, object]:
        return _snapshot(
            player=self.player,
            revision=self.revision,
            native_revision=self.native_revision,
        )

    def query_zhongguo_scoreboard_state_v1(
        self, request_nonce: str, *, expected_revision: int
    ) -> dict[str, object]:
        if expected_revision != self.revision:
            raise AssertionError("unexpected revision")
        value = _query(
            self.surface_id,
            request_nonce=request_nonce,
            player=self.player,
            revision=self.revision,
            native_revision=self.native_revision,
        )
        if self.surface_id == "received-only" and callable(
            self.received_query_mutator
        ):
            self.received_query_mutator(value)
        return value

    def save_checkpoint(self, *, expected_revision: int) -> dict[str, object]:
        if expected_revision != self.revision:
            raise AssertionError("unexpected save revision")
        path = self.root / f"native-{self.surface_id}.ck3"
        path.write_bytes(f"real-product-{self.surface_id}".encode("ascii"))
        digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        return {
            "accepted": True,
            "backend_id": "native-headless",
            "checkpoint": {
                "status": "saved",
                "path": str(path.resolve()),
                "size": path.stat().st_size,
                "sha256": digest,
                "date_raw": DATE_RAW,
                "strategy": "native-autosave-command-v1",
            },
            "materialization": {"available": True},
        }

    def transition(self, *, fixture_used: bool = True, **_: object):
        self.player = SUBJECT
        self.surface_id = "received-only"
        self.revision += 1
        self.native_revision += 1
        return {
            "result": "GREEN",
            "surface_truth_source": "native-product-query",
            "provider_observed": True,
            "identity_carrier_fixture_used": fixture_used,
            "fixture_wrote_scoreboard_state": False,
            "fixture_wrote_scoreboard_receipt": False,
            "action_ack_used_as_identity_postcondition": False,
            "owner_character_id": OWNER,
            "subject_character_id": SUBJECT,
            "player_character_id_before": OWNER,
            "player_character_id_after": SUBJECT,
            "date_raw": DATE_RAW,
        }


def _builder(root: Path) -> ScoreboardSurfaceCheckpointRegistryBuilder:
    return ScoreboardSurfaceCheckpointRegistryBuilder(
        root / "checkpoints",
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


class ScoreboardSurfaceCaptureOrchestrationTests(unittest.TestCase):
    def test_fixture_carries_identity_but_never_supplies_surface_truth(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = _Service(root)
            registry_path = root / "registry.json"
            result = capture_managed_received_scoreboard_surfaces_v1(
                service,
                _builder(root),
                received_subject_character_id=SUBJECT,
                identity_carrier=service.transition,
                registry_path=registry_path,
            )

            self.assertEqual(result["result"], "GREEN")
            self.assertTrue(result["identity_carrier_fixture_used"])
            self.assertTrue(result["fixture_used"])
            self.assertFalse(result["fixture_wrote_scoreboard_state"])
            self.assertFalse(result["fixture_wrote_scoreboard_receipt"])
            self.assertEqual(
                result["surface_truth_source"], "native-product-query"
            )
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            self.assertEqual(
                [row["surface_id"] for row in registry["entries"]],
                ["managed-capable", "received-only"],
            )
            self.assertEqual(registry["entries"][0]["player_character_id"], OWNER)
            self.assertEqual(
                registry["entries"][1]["player_character_id"], SUBJECT
            )
            self.assertFalse(registry["fixture_used"])

    def test_non_fixture_identity_carrier_is_distinguished(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = _Service(root)

            def official_transition(**kwargs: object):
                return service.transition(fixture_used=False, **kwargs)

            result = capture_managed_received_scoreboard_surfaces_v1(
                service,
                _builder(root),
                received_subject_character_id=SUBJECT,
                identity_carrier=official_transition,
                registry_path=root / "registry.json",
            )
            self.assertFalse(result["identity_carrier_fixture_used"])
            self.assertFalse(result["fixture_used"])

    def test_fixture_claiming_scoreboard_write_cannot_write_registry(self) -> None:
        for field in (
            "fixture_wrote_scoreboard_state",
            "fixture_wrote_scoreboard_receipt",
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                service = _Service(root)

                def contaminated(**kwargs: object):
                    receipt = service.transition(**kwargs)
                    receipt[field] = True
                    return receipt

                registry_path = root / "registry.json"
                with self.assertRaises(
                    ScoreboardSurfaceCaptureOrchestrationError
                ) as caught:
                    capture_managed_received_scoreboard_surfaces_v1(
                        service,
                        _builder(root),
                        received_subject_character_id=SUBJECT,
                        identity_carrier=contaminated,
                        registry_path=registry_path,
                    )
                self.assertEqual(
                    caught.exception.reason_code,
                    "scoreboard_identity_carrier_receipt_invalid",
                )
                self.assertFalse(registry_path.exists())

    def test_received_acl_or_cross_surface_identity_drift_cannot_write_registry(
        self,
    ) -> None:
        mutations = {
            "tuple-incomplete": lambda query: query["acl"][
                "received_self"
            ].__setitem__(
                "b1_case_serial",
                {
                    "status": "unavailable",
                    "value": None,
                    "unavailable_reason": "variable_absent",
                },
            ),
            "wrong-owner": lambda query: query["acl"][
                "received_self"
            ].__setitem__("owner_character_id", typed(909)),
        }
        for label, mutation in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                service = _Service(root)
                service.received_query_mutator = mutation
                registry_path = root / "registry.json"
                with self.assertRaises(Exception):
                    capture_managed_received_scoreboard_surfaces_v1(
                        service,
                        _builder(root),
                        received_subject_character_id=SUBJECT,
                        identity_carrier=service.transition,
                        registry_path=registry_path,
                    )
                self.assertFalse(registry_path.exists())

    def test_ack_only_identity_claim_does_not_replace_native_postcondition(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = _Service(root)

            def ack_only(**_: object):
                receipt = service.transition()
                receipt["action_ack_used_as_identity_postcondition"] = True
                return receipt

            registry_path = root / "registry.json"
            with self.assertRaises(
                ScoreboardSurfaceCaptureOrchestrationError
            ) as caught:
                capture_managed_received_scoreboard_surfaces_v1(
                    service,
                    _builder(root),
                    received_subject_character_id=SUBJECT,
                    identity_carrier=ack_only,
                    registry_path=registry_path,
                )
            self.assertEqual(
                caught.exception.reason_code,
                "scoreboard_identity_carrier_receipt_invalid",
            )
            self.assertFalse(registry_path.exists())


if __name__ == "__main__":
    unittest.main()

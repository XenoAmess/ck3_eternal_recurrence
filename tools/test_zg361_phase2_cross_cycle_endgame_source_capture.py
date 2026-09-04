#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from test_zg361_phase2_incident_checkpoint_seam import (  # noqa: E402
    CaptureAndActionService,
)
from zg361_phase2_cross_cycle_endgame_source_capture import (  # noqa: E402
    CAPTURE_PREFIX_KIND,
    EndgameSourceCaptureError,
    capture_cross_cycle_endgame_source_checkpoint_v1,
    preflight_endgame_source_capture_prefix,
)
from zg361_phase2_incident_checkpoint_seam import (  # noqa: E402
    capture_current_received_self_incident_checkpoint_v1,
)
from zhongguo_phase2_event_choreography import (  # noqa: E402
    PHASE2_EVENT_SEQUENCE_PLANS,
)
from zhongguo_phase2_source_checkpoint_provider import (  # noqa: E402
    CHECKPOINT_REQUIRED_HANDLERS,
    Phase2SourceCheckpointProvider,
)


SEED_LINEAGE_ID = "zg361-phase2-seed-" + "a" * 64
OWNER = 29037
SUBJECT = 29038
DATE_RAW = 9010
PRODUCT_SHA = "B" * 64
EXE_SHA = "C" * 64
PLANS = {
    plan.handler: plan
    for plan in PHASE2_EVENT_SEQUENCE_PLANS
    if plan.handler in CHECKPOINT_REQUIRED_HANDLERS
}


def character_scope(character_id: int) -> dict[str, object]:
    return {
        "status": "available",
        "raw_type_index": 4,
        "type_key": "character",
        "subtype": 0,
        "typed_identity": {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        },
    }


def source_context(*, option_count: int = 3) -> dict[str, object]:
    return {
        "status": "available",
        "event_definition_key": "zg361we.356",
        "current_event_instance_id": 3561,
        "snapshot_revision": 110,
        "date_raw": DATE_RAW,
        "root_scope": character_scope(OWNER),
        "saved_scopes": [
            {"name": "zg361_we_al_owner", "scope": character_scope(OWNER)},
            {"name": "zg361_we_al_subject", "scope": character_scope(SUBJECT)},
            {"name": "zg361_we_al_cycle", "scope": {}},
            {"name": "zg361_we_al_case", "scope": {}},
        ],
        "options": [
            {
                "rendered_index": index,
                "native_option_index": index,
                "shown": True,
                "enabled": True,
                "resolved_name": f"source option {index + 1}",
            }
            for index in range(option_count)
        ],
        "readiness": {
            "event_definition_identity_ready": True,
            "root_scope_ready": True,
            "saved_scopes_ready": True,
            "option_presentation_ready": True,
        },
    }


def capture_lineage() -> dict[str, object]:
    return {
        "schema_version": 1,
        "phase": "zhongguo_phase2",
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "console_used": False,
        "seed_lineage_id": SEED_LINEAGE_ID,
        "game": {"version": "1.19.0.6", "exe_sha256": EXE_SHA},
        "mod_mount": {
            "kind": "product-only",
            "tree_sha256": PRODUCT_SHA,
            "enabled_mods": ["mod/zg361_acceptance.mod"],
        },
    }


def generic_receipt(
    *,
    handler: str,
    owner: int,
    player: int,
    date_raw: int,
    sha256: str,
) -> dict[str, object]:
    plan = PLANS[handler]
    return {
        "result": "GREEN",
        "evidence_class": "real_ck3",
        "provider_observed": True,
        "ui_state_verified": True,
        "fixture_used": False,
        "console_used": False,
        "span_id": plan.span_id,
        "event_definition_key": plan.source_event,
        "owner_character_id": owner,
        "player_character_id": player,
        "date_raw": date_raw,
        "checkpoint_sha256": sha256,
        "save_lineage_id": SEED_LINEAGE_ID,
    }


def make_prefix(root: Path) -> Path:
    rows: list[dict[str, object]] = []
    for ordinal, handler in enumerate(CHECKPOINT_REQUIRED_HANDLERS[:-1], 1):
        strict_receipt = None
        if handler == "capture_incidents_operations":
            strict_root = root / "strict-incident"
            strict_root.mkdir()
            strict_receipt = capture_current_received_self_incident_checkpoint_v1(
                CaptureAndActionService(strict_root),
                checkpoint_root=strict_root / "checkpoints",
                receipt_path=strict_root / "receipt.json",
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
            checkpoint = Path(str(strict_receipt["checkpoint"]["path"]))
            owner = int(strict_receipt["owner_character_id"])
            player = int(strict_receipt["player_character_id"])
            date_raw = int(strict_receipt["date_raw"])
        else:
            checkpoint = root / f"source-{ordinal}.ck3"
            checkpoint.write_bytes(f"real-source-{ordinal}".encode("ascii"))
            owner = 9200 + ordinal
            player = 9001
            date_raw = 820 + ordinal
        sha256 = hashlib.sha256(checkpoint.read_bytes()).hexdigest().upper()
        plan = PLANS[handler]
        row = {
            "span_id": plan.span_id,
            "handler": handler,
            "source_event_definition_key": plan.source_event,
            "owner_character_id": owner,
            "player_character_id": player,
            "date_raw": date_raw,
            "checkpoint": {
                "path": str(checkpoint.resolve()),
                "bytes": checkpoint.stat().st_size,
                "sha256": sha256,
                "save_lineage_id": SEED_LINEAGE_ID,
            },
            "source_receipt": generic_receipt(
                handler=handler,
                owner=owner,
                player=player,
                date_raw=date_raw,
                sha256=sha256,
            ),
        }
        if strict_receipt is not None:
            row["received_self_incident_checkpoint_receipt"] = strict_receipt
        rows.append(row)
    path = root / "source-capture-prefix.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "kind": CAPTURE_PREFIX_KIND,
                "result": "LIVE_PENDING",
                "readiness": "live-pending-endgame-source",
                "evidence_class": "real_ck3",
                "fixture_used": False,
                "console_used": False,
                "seed_lineage_id": SEED_LINEAGE_ID,
                "capture_lineage": capture_lineage(),
                "entries": rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


class FakeCaptureService:
    def __init__(
        self,
        root: Path,
        *,
        owner: int = OWNER,
        option_count: int = 3,
        empty_snapshots: int = 0,
        checkpoint_hash_valid: bool = True,
    ) -> None:
        self.root = root
        self.owner = owner
        self.option_count = option_count
        self.empty_snapshots = empty_snapshots
        self.snapshot_calls = 0
        self.save_calls = 0
        self.checkpoint_hash_valid = checkpoint_hash_valid
        self.source = root / "native-save.ck3"
        self.source.write_bytes(b"real-ck3-endgame-source")

    def snapshot(self) -> dict[str, object]:
        self.snapshot_calls += 1
        active = None
        if self.snapshot_calls > self.empty_snapshots:
            active = {"instance_id": 3561, "option_count": self.option_count}
        return {
            "snapshot_id": "endgame-source:10",
            "revision": 10,
            "native_revision": 110,
            "date_raw": DATE_RAW,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": self.owner, "alive": True},
            "active_event": active,
        }

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        if event_instance_id != 3561 or expected_revision != 10:
            raise AssertionError("capture query crossed its fake binding")
        return {
            "status": "available",
            "current_event_window_context": source_context(
                option_count=self.option_count
            ),
        }

    def save_checkpoint(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        self.save_calls += 1
        if expected_revision != 10:
            raise AssertionError("capture save crossed its fake revision")
        actual = hashlib.sha256(self.source.read_bytes()).hexdigest().upper()
        return {
            "accepted": True,
            "backend_id": "native-headless",
            "checkpoint": {
                "status": "saved",
                "path": str(self.source.resolve()),
                "size": self.source.stat().st_size,
                "sha256": actual if self.checkpoint_hash_valid else "F" * 64,
                "date_raw": DATE_RAW,
                "episode_character_id": OWNER,
                "strategy": "native-save-game",
            },
            "materialization": {"available": True},
        }


class CrossCycleEndgameSourceCaptureTests(unittest.TestCase):
    def test_waits_for_real_surface_and_writes_consumable_schema2_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prefix = make_prefix(root)
            service = FakeCaptureService(root, empty_snapshots=2)
            registry_path = root / "registry.json"
            receipt = capture_cross_cycle_endgame_source_checkpoint_v1(
                service,
                prefix_manifest=prefix,
                capture_input_root=root / "capture-input",
                receipt_path=root / "endgame-receipt.json",
                completed_manifest_path=root / "completed-manifest.json",
                registry_checkpoint_root=root / "registry-checkpoints",
                registry_path=registry_path,
                expected_owner_character_id=OWNER,
                expected_date_raw=DATE_RAW,
                runtime_capture_lineage=capture_lineage(),
                timeout_seconds=1,
                poll_interval_seconds=0,
            )
            self.assertEqual(receipt["result"], "GREEN")
            self.assertEqual(receipt["readiness"], "live-pending")
            self.assertFalse(receipt["phase2_complete"])
            self.assertGreaterEqual(service.snapshot_calls, 4)
            self.assertEqual(service.save_calls, 1)
            source_receipt = receipt["source_receipt"]
            self.assertEqual(source_receipt["event_definition_key"], "zg361we.356")
            self.assertEqual(source_receipt["owner_character_id"], OWNER)
            self.assertEqual(source_receipt["subject_character_id"], SUBJECT)
            self.assertFalse(source_receipt["action_ack_used_as_state_evidence"])
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            result = Phase2SourceCheckpointProvider(
                registry,
                restore_registered_checkpoint=lambda _entry: {},
                expected_seed_lineage_id=SEED_LINEAGE_ID,
            ).preflight()
            self.assertEqual(result["result"], "GREEN")
            self.assertEqual(result["entry_count"], 4)

    def test_wrong_owner_is_typed_red_before_save(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = FakeCaptureService(root, owner=OWNER + 1)
            with self.assertRaises(EndgameSourceCaptureError) as raised:
                capture_cross_cycle_endgame_source_checkpoint_v1(
                    service,
                    prefix_manifest=make_prefix(root),
                    capture_input_root=root / "capture-input",
                    receipt_path=root / "receipt.json",
                    completed_manifest_path=root / "manifest.json",
                    registry_checkpoint_root=root / "registry-input",
                    registry_path=root / "registry.json",
                    expected_owner_character_id=OWNER,
                    expected_date_raw=DATE_RAW,
                    runtime_capture_lineage=capture_lineage(),
                    timeout_seconds=1,
                    poll_interval_seconds=0,
                )
            self.assertEqual(raised.exception.reason_code, "source_owner_mismatch")
            self.assertEqual(service.save_calls, 0)

    def test_non_three_option_surface_is_typed_red_before_save(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = FakeCaptureService(root, option_count=2)
            with self.assertRaises(EndgameSourceCaptureError) as raised:
                capture_cross_cycle_endgame_source_checkpoint_v1(
                    service,
                    prefix_manifest=make_prefix(root),
                    capture_input_root=root / "capture-input",
                    receipt_path=root / "receipt.json",
                    completed_manifest_path=root / "manifest.json",
                    registry_checkpoint_root=root / "registry-input",
                    registry_path=root / "registry.json",
                    expected_owner_character_id=OWNER,
                    expected_date_raw=DATE_RAW,
                    runtime_capture_lineage=capture_lineage(),
                    timeout_seconds=1,
                    poll_interval_seconds=0,
                )
            self.assertEqual(
                raised.exception.reason_code,
                "source_event_surface_invalid",
            )
            self.assertEqual(service.save_calls, 0)

    def test_wrong_date_is_typed_red_before_save(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = FakeCaptureService(root)
            with self.assertRaises(EndgameSourceCaptureError) as raised:
                capture_cross_cycle_endgame_source_checkpoint_v1(
                    service,
                    prefix_manifest=make_prefix(root),
                    capture_input_root=root / "capture-input",
                    receipt_path=root / "receipt.json",
                    completed_manifest_path=root / "manifest.json",
                    registry_checkpoint_root=root / "registry-input",
                    registry_path=root / "registry.json",
                    expected_owner_character_id=OWNER,
                    expected_date_raw=DATE_RAW + 24,
                    runtime_capture_lineage=capture_lineage(),
                    timeout_seconds=1,
                    poll_interval_seconds=0,
                )
            self.assertEqual(raised.exception.reason_code, "source_date_mismatch")
            self.assertEqual(service.save_calls, 0)

    def test_native_hash_mismatch_cannot_write_receipt_or_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = FakeCaptureService(root, checkpoint_hash_valid=False)
            receipt_path = root / "receipt.json"
            registry_path = root / "registry.json"
            with self.assertRaises(EndgameSourceCaptureError) as raised:
                capture_cross_cycle_endgame_source_checkpoint_v1(
                    service,
                    prefix_manifest=make_prefix(root),
                    capture_input_root=root / "capture-input",
                    receipt_path=receipt_path,
                    completed_manifest_path=root / "manifest.json",
                    registry_checkpoint_root=root / "registry-input",
                    registry_path=registry_path,
                    expected_owner_character_id=OWNER,
                    expected_date_raw=DATE_RAW,
                    runtime_capture_lineage=capture_lineage(),
                    timeout_seconds=1,
                    poll_interval_seconds=0,
                )
            self.assertEqual(raised.exception.reason_code, "source_native_save_invalid")
            self.assertFalse(receipt_path.exists())
            self.assertFalse(registry_path.exists())

    def test_prefix_preflight_rejects_fixture_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prefix_path = make_prefix(root)
            prefix = json.loads(prefix_path.read_text(encoding="utf-8"))
            prefix["fixture_used"] = True
            with self.assertRaises(EndgameSourceCaptureError) as raised:
                preflight_endgame_source_capture_prefix(prefix)
            self.assertEqual(
                raised.exception.reason_code,
                "source_capture_prefix_header_invalid",
            )

    def test_runtime_lineage_mismatch_is_static_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = copy.deepcopy(capture_lineage())
            runtime["mod_mount"]["tree_sha256"] = "D" * 64
            with self.assertRaises(EndgameSourceCaptureError) as raised:
                preflight_endgame_source_capture_prefix(
                    make_prefix(root),
                    runtime_capture_lineage=runtime,
                )
            self.assertEqual(
                raised.exception.reason_code,
                "source_capture_runtime_lineage_mismatch",
            )

    def test_standalone_preflight_is_green_and_never_launches_ck3(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = subprocess.run(
                [
                    sys.executable,
                    str(
                        TOOLS
                        / "preflight_zg361_phase2_cross_cycle_endgame_source_capture.py"
                    ),
                    "--prefix",
                    str(make_prefix(root)),
                    "--expected-seed-lineage-id",
                    SEED_LINEAGE_ID,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads(result.stdout)
            self.assertEqual(receipt["result"], "GREEN")
            self.assertEqual(
                receipt["readiness"],
                "live-pending-endgame-source",
            )
            self.assertFalse(receipt["ck3_launched"])

    def test_runner_exposes_only_explicit_live_capture_plumbing(self) -> None:
        source = (TOOLS / "run_zhongguo_acceptance.py").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("--phase2-endgame-source-capture-live", source)
        self.assertIn("phase2_endgame_source_capture_prefix", source)
        self.assertIn("run_phase2_endgame_source_capture_scenario", source)
        module = (
            TOOLS / "zg361_phase2_cross_cycle_endgame_source_capture.py"
        ).read_text(encoding="utf-8-sig")
        self.assertNotIn("select_event_option(", module)
        self.assertNotIn("execute_step(", module)
        self.assertNotIn("launch_native_ck3", module)


if __name__ == "__main__":
    unittest.main()

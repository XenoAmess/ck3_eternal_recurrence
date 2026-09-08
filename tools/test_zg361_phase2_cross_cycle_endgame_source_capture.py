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
    player_switch_locator,
)
from zg361_phase2_cross_cycle_endgame_source_capture import (  # noqa: E402
    CAPTURE_PREFIX_KIND,
    MULTI_BRANCH_CAPTURE_LINEAGE_MODE,
    MULTI_BRANCH_CAPTURE_SCHEMA_VERSION,
    PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND,
    EndgameSourceCaptureError,
    capture_cross_cycle_endgame_source_checkpoint_v1,
    phase2_source_lineage_set_id,
    preflight_endgame_source_capture_prefix,
    preflight_endgame_source_capture_service,
)
from zg361_phase2_incident_checkpoint_seam import (  # noqa: E402
    capture_current_received_self_incident_checkpoint_v1,
)
from zg361_phase2_incident_source_capture_entry import (  # noqa: E402
    GENERIC_REBIND_AUTHORITY,
)
from zhongguo_phase2_event_choreography import (  # noqa: E402
    PHASE2_EVENT_SEQUENCE_PLANS,
)
from zhongguo_phase2_source_checkpoint_provider import (  # noqa: E402
    CHECKPOINT_REQUIRED_HANDLERS,
    Phase2SourceCheckpointProvider,
)


SEED_LINEAGE_ID = "zg361-phase2-seed-" + "a" * 64
INCIDENT_SEED_LINEAGE_ID = "zg361-phase2-seed-" + "8" * 64
RUNTIME_SEED_LINEAGE_ID = "zg361-phase2-seed-" + "f" * 64
OWNER = 32904
SUBJECT = 29038
DATE_RAW = 9010
CYCLE = 3
CASE = 403
BRIDGE_PID = 4321
CONNECTION_GENERATION = 7
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


def scalar_scope() -> dict[str, object]:
    return {
        "status": "available",
        "raw_type_index": 9,
        "type_key": "value",
        "subtype": 0,
        "typed_identity": {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        },
    }


def source_context(
    *, option_count: int = 3, snapshot_revision: int = 110
) -> dict[str, object]:
    return {
        "status": "available",
        "event_definition_key": "zg361we.356",
        "current_event_instance_id": 3561,
        "snapshot_revision": snapshot_revision,
        "date_raw": DATE_RAW,
        "root_scope": character_scope(OWNER),
        "saved_scopes": [
            {"name": "zg361_we_al_owner", "scope": character_scope(OWNER)},
            {"name": "zg361_we_al_subject", "scope": character_scope(SUBJECT)},
            {"name": "zg361_we_al_cycle", "scope": scalar_scope()},
            {"name": "zg361_we_al_case", "scope": scalar_scope()},
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


def available(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def unavailable(reason: str) -> dict[str, object]:
    return {"status": "unavailable", "value": None, "unavailable_reason": reason}


def history_slot(index: int) -> dict[str, object]:
    base = 1000 + index * 100
    return {
        "owner_character_id": available(OWNER),
        "subject_character_id": available(SUBJECT + index + 1),
        "cycle_serial": available(index + 1),
        "case_serial": available(CASE - 2 + index),
        "m357_receipt_id": available(base + 1),
        "m357_receipt_hash": available(base + 2),
        "m358_receipt_id": available(base + 3),
        "m358_receipt_hash": available(base + 4),
        "m359_receipt_id": available(base + 5),
        "m359_receipt_hash": available(base + 6),
    }


def maturity_response() -> dict[str, object]:
    third = {
        key: unavailable("lifecycle_not_reached")
        for key in history_slot(2)
    }
    return {
        "schema_version": 1,
        "status": "available",
        "case_kind": "zhongguo.workforce-collective",
        "request_nonce": "zg361.endgame.source.maturity",
        "snapshot_revision": 112,
        "date_raw": DATE_RAW,
        "paused": True,
        "player_character_id": SUBJECT,
        "subject_character_id": SUBJECT,
        "requested_owner_character_id": OWNER,
        "unavailable_reason": None,
        "al_case": {
            "owner_character_id": available(OWNER),
            "subject_character_id": available(SUBJECT),
            "cycle_serial": available(CYCLE),
            "case_serial": available(CASE),
            "state": available(1),
            "active": available(True),
            "revision": available(7),
        },
        "history": {
            "status": "partial",
            "count": available(2),
            "effective_count": 2,
            "slots": [history_slot(0), history_slot(1), third],
        },
        "readiness": {
            "player_subject_binding_ready": True,
            "owner_binding_ready": True,
            "case_identity_ready": True,
            "history_ledger_ready": True,
            "history_order_ready": True,
            "three_cycle_ready": False,
            "same_frame_ready": True,
            "ready": True,
        },
        "binding": {
            "request_nonce": "zg361.endgame.source.maturity",
            "snapshot_id": "endgame-subject:12",
            "revision": 12,
            "native_revision": 112,
            "date_raw": DATE_RAW,
            "paused": True,
            "player_character_id": SUBJECT,
            "subject_character_id": SUBJECT,
            "owner_character_id": OWNER,
            "expected_revision": 12,
        },
    }


def maturity_receipt_fields() -> dict[str, object]:
    provider = maturity_response()
    normalized_slots = [
        {
            key: int(field["value"])
            for key, field in history_slot(index).items()
        }
        for index in range(2)
    ]
    receipt_ids = [
        slot[f"m{milestone}_receipt_id"]
        for slot in normalized_slots
        for milestone in (357, 358, 359)
    ]
    receipt_hashes = [
        slot[f"m{milestone}_receipt_hash"]
        for slot in normalized_slots
        for milestone in (357, 358, 359)
    ]
    owner_binding = {
        "snapshot_id": "endgame-source:10",
        "revision": 10,
        "native_revision": 110,
        "date_raw": DATE_RAW,
        "player_character_id": OWNER,
        "event_instance_id": 3561,
        "bridge_pid": BRIDGE_PID,
        "connection_generation": CONNECTION_GENERATION,
    }
    post_save_binding = {
        **owner_binding,
        "snapshot_id": "endgame-source:11",
        "revision": 11,
        "native_revision": 111,
    }
    subject_binding = {
        "snapshot_id": "endgame-subject:12",
        "revision": 12,
        "native_revision": 112,
        "date_raw": DATE_RAW,
        "player_character_id": SUBJECT,
        "event_instance_id": None,
        "bridge_pid": BRIDGE_PID,
        "connection_generation": CONNECTION_GENERATION,
    }
    scalar_binding = {
        "zg361_we_al_cycle": {
            **scalar_scope(),
            "provider_field": "cycle_serial",
            "provider_value": CYCLE,
        },
        "zg361_we_al_case": {
            **scalar_scope(),
            "provider_field": "case_serial",
            "provider_value": CASE,
        },
    }
    return {
        "kind": "zg361_phase2_cross_cycle_endgame_source_checkpoint_v1",
        "subject_character_id": SUBJECT,
        "generic_character_rebind_used": True,
        "maturity_player_switch_receipt": {
            "schema_version": 1,
            "accepted": True,
            "status": "switched",
            "backend_id": "native-headless",
            "step": f"set-played-character-v1-{SUBJECT}",
            "from_character_id": OWNER,
            "to_character_id": SUBJECT,
            "prior_episode_character_id": OWNER,
            "episode_character_id": SUBJECT,
            "before_revision": 11,
            "after_revision": 12,
            "native_revision": 112,
            "date_raw": DATE_RAW,
            "paused": True,
            "map_ready": True,
            "postcondition_verified": True,
            "episode_rebind_performed": True,
            "one_life_terminal_cleared": True,
        },
        "source_snapshot_binding": owner_binding,
        "post_save_snapshot_binding": post_save_binding,
        "event_context": source_context(),
        "post_save_event_context": source_context(snapshot_revision=111),
        "maturity_subject_snapshot_binding": subject_binding,
        "maturity_post_query_snapshot_binding": copy.deepcopy(subject_binding),
        "maturity_provider_proof": {
            "schema_version": 1,
            "result": "GREEN",
            "evidence_class": "real_ck3",
            "provider_observed": True,
            "history_status": "partial",
            "history_count": 2,
            "history_effective_count": 2,
            "owner_character_id": OWNER,
            "subject_character_id": SUBJECT,
            "cycle_serial": CYCLE,
            "case_serial": CASE,
            "prior_cycle_serials": [1, 2],
            "prior_slots": normalized_slots,
            "receipt_ids": receipt_ids,
            "receipt_hashes": receipt_hashes,
            "third_cycle_source_ready": True,
            "provider_response": provider,
        },
        "source_event_case_binding": {
            "event_definition_key": "zg361we.356",
            "owner_character_id": OWNER,
            "subject_character_id": SUBJECT,
            "cycle_serial": CYCLE,
            "case_serial": CASE,
            "event_owner_subject_scopes_observed": True,
            "received_self_current_case_provider_observed": True,
            "numeric_binding_authority": (
                "paused-zg361we.356-value-scopes+source-trigger-full-guard+"
                "received-self-current-case-provider"
            ),
            "event_scalar_saved_scopes": scalar_binding,
        },
    }
def capture_lineage(
    seed_lineage_id: str = SEED_LINEAGE_ID,
    tree_sha256: str = PRODUCT_SHA,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "phase": "zhongguo_phase2",
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "ocr_used": False,
        "coordinates_used": False,
        "console_used": False,
        "generic_character_rebind_used": True,
        "generic_character_rebind_authority": GENERIC_REBIND_AUTHORITY,
        "seed_lineage_id": seed_lineage_id,
        "game": {"version": "1.19.0.6", "exe_sha256": EXE_SHA},
        "mod_mount": {
            "kind": "product-only",
            "tree_sha256": tree_sha256,
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
    seed_lineage_id: str = SEED_LINEAGE_ID,
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
        "save_lineage_id": seed_lineage_id,
    }


def make_prefix(
    root: Path,
    *,
    incident_seed_lineage_id: str = SEED_LINEAGE_ID,
) -> Path:
    rows: list[dict[str, object]] = []
    for ordinal, handler in enumerate(CHECKPOINT_REQUIRED_HANDLERS[:-1], 1):
        row_seed_lineage_id = (
            incident_seed_lineage_id
            if handler == "capture_incidents_operations"
            else SEED_LINEAGE_ID
        )
        strict_receipt = None
        if handler == "capture_incidents_operations":
            strict_root = root / "strict-incident"
            strict_root.mkdir()
            incident_service = CaptureAndActionService(strict_root)
            strict_receipt = capture_current_received_self_incident_checkpoint_v1(
                incident_service,
                checkpoint_root=strict_root / "checkpoints",
                receipt_path=strict_root / "receipt.json",
                seed_lineage_id=row_seed_lineage_id,
                capture_lineage={
                    **capture_lineage(row_seed_lineage_id),
                    "generic_character_rebind_used": True,
                    "generic_character_rebind_authority": (
                        GENERIC_REBIND_AUTHORITY
                    ),
                },
                player_switch_receipt=player_switch_locator(
                    strict_root,
                    incident_service,
                    seed_lineage_id=row_seed_lineage_id,
                ),
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
                "save_lineage_id": row_seed_lineage_id,
            },
            "source_receipt": generic_receipt(
                handler=handler,
                owner=owner,
                player=player,
                date_raw=date_raw,
                sha256=sha256,
                seed_lineage_id=row_seed_lineage_id,
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


def file_record(path: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
    }


def make_schema3_prefix(root: Path) -> Path:
    legacy_path = make_prefix(root)
    legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
    rows = legacy["entries"]
    bindings: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        handler = row["handler"]
        lineage = capture_lineage()
        binding: dict[str, object] = {
            "handler": handler,
            "seed_lineage_id": SEED_LINEAGE_ID,
            "capture_lineage": lineage,
        }
        if index < 2:
            artifact_path = root / f"schema3-source-{index}.json"
            artifact_path.write_text(
                json.dumps(
                    {
                        "seed_lineage_id": SEED_LINEAGE_ID,
                        "capture_lineage": lineage,
                        "entries": [row],
                    }
                ),
                encoding="utf-8",
            )
            binding.update(
                {
                    "provenance_source": "source_artifact.capture_lineage",
                    "source_artifact": file_record(artifact_path),
                }
            )
        else:
            row["schema_version"] = 3
            row["seed_lineage_id"] = SEED_LINEAGE_ID
            row["capture_lineage"] = lineage
            binding.update(
                {
                    "provenance_source": "registry_entry.capture_lineage",
                    "capture_run_input_checkpoint": copy.deepcopy(
                        row["checkpoint"]
                    ),
                }
            )
        bindings.append(binding)
    lineage_set_id = phase2_source_lineage_set_id(bindings)
    schema3 = {
        "schema_version": MULTI_BRANCH_CAPTURE_SCHEMA_VERSION,
        "kind": CAPTURE_PREFIX_KIND,
        "result": "LIVE_PENDING",
        "readiness": "live-pending-endgame-source",
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "console_used": False,
        "lineage_set_id": lineage_set_id,
        "capture_lineage": {
            "schema_version": 2,
            "kind": PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND,
            "capture_lineage_mode": MULTI_BRANCH_CAPTURE_LINEAGE_MODE,
            "lineage_set_id": lineage_set_id,
            "evidence_class": "real_ck3",
            "fixture_used": False,
            "console_used": False,
            "entry_capture_lineages": bindings,
        },
        "entries": rows,
    }
    path = root / "source-capture-prefix-schema3.json"
    path.write_text(json.dumps(schema3), encoding="utf-8")
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
        maturity: dict[str, object] | None = None,
        switch_receipt_valid: bool = True,
        switch_generation_drift: bool = False,
        save_revision_jump: int = 1,
    ) -> None:
        self.root = root
        self.owner = owner
        self.option_count = option_count
        self.empty_snapshots = empty_snapshots
        self.snapshot_calls = 0
        self.save_calls = 0
        self.checkpoint_hash_valid = checkpoint_hash_valid
        self.maturity = copy.deepcopy(maturity or maturity_response())
        self.switch_receipt_valid = switch_receipt_valid
        self.switch_generation_drift = switch_generation_drift
        self.save_revision_jump = save_revision_jump
        self.saved = False
        self.switched = False
        self.source = root / "native-save.ck3"
        self.source.write_bytes(b"real-ck3-endgame-source")

    def capabilities(self) -> dict[str, object]:
        return {
            "bridge_capabilities": [
                "game.command.set-played-character-v1-N",
                "game.command.query-zhongguo-workforce-collective-snapshot-v1",
            ]
        }

    def snapshot(self) -> dict[str, object]:
        self.snapshot_calls += 1
        if self.switched:
            return {
                "snapshot_id": "endgame-subject:12",
                "revision": 12,
                "native_revision": 112,
                "date_raw": DATE_RAW,
                "paused": True,
                "map_ready": True,
                "played_character": {"character_id": SUBJECT, "alive": True},
                "diagnostics": {
                    "bridge_pid": BRIDGE_PID,
                    "connection_generation": (
                        CONNECTION_GENERATION + 1
                        if self.switch_generation_drift
                        else CONNECTION_GENERATION
                    ),
                },
                "active_event": None,
            }
        active = None
        if self.snapshot_calls > self.empty_snapshots:
            active = {"instance_id": 3561, "option_count": self.option_count}
        revision = 10 + self.save_revision_jump if self.saved else 10
        native_revision = (
            110 + self.save_revision_jump if self.saved else 110
        )
        return {
            "snapshot_id": f"endgame-source:{revision}",
            "revision": revision,
            "native_revision": native_revision,
            "date_raw": DATE_RAW,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": self.owner, "alive": True},
            "diagnostics": {
                "bridge_pid": BRIDGE_PID,
                "connection_generation": CONNECTION_GENERATION,
            },
            "active_event": active,
        }

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        if event_instance_id != 3561 or expected_revision not in (
            10,
            10 + self.save_revision_jump,
        ):
            raise AssertionError("capture query crossed its fake binding")
        return {
            "status": "available",
            "current_event_window_context": source_context(
                option_count=self.option_count,
                snapshot_revision=expected_revision + 100,
            ),
        }

    def save_checkpoint(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        self.save_calls += 1
        if expected_revision != 10:
            raise AssertionError("capture save crossed its fake revision")
        self.saved = True
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

    def set_player_character_v1(
        self, character_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        if character_id != SUBJECT or expected_revision != 11:
            raise AssertionError("capture switch crossed its fake binding")
        self.switched = True
        return {
            "schema_version": 1,
            "accepted": True,
            "status": "switched",
            "backend_id": "native-headless",
            "step": f"set-played-character-v1-{SUBJECT}",
            "from_character_id": OWNER if self.switch_receipt_valid else OWNER + 1,
            "to_character_id": SUBJECT,
            "prior_episode_character_id": OWNER,
            "episode_character_id": SUBJECT,
            "before_revision": 11,
            "after_revision": 12,
            "native_revision": 112,
            "date_raw": DATE_RAW,
            "paused": True,
            "map_ready": True,
            "postcondition_verified": True,
            "episode_rebind_performed": True,
            "one_life_terminal_cleared": True,
        }

    def query_zhongguo_workforce_collective_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        if (
            not self.switched
            or request_nonce != "zg361.endgame.source.maturity"
            or expected_revision != 12
            or owner_character_id != OWNER
        ):
            raise AssertionError("maturity query crossed its fake binding")
        return copy.deepcopy(self.maturity)


class CrossCycleEndgameSourceCaptureTests(unittest.TestCase):
    def test_service_preflight_requires_switch_and_workforce_provider(self) -> None:
        ready = preflight_endgame_source_capture_service(
            FakeCaptureService.__new__(FakeCaptureService)
        )
        self.assertEqual(ready["result"], "GREEN")
        self.assertTrue(ready["generic_character_rebind_required"])
        self.assertFalse(ready["provider_observed_business_state"])
        with self.assertRaises(EndgameSourceCaptureError) as raised:
            preflight_endgame_source_capture_service(object())
        self.assertEqual(
            raised.exception.reason_code,
            "endgame_maturity_provider_missing",
        )
        missing_capability = FakeCaptureService.__new__(FakeCaptureService)
        missing_capability.capabilities = lambda: {"bridge_capabilities": []}
        with self.assertRaises(EndgameSourceCaptureError) as raised:
            preflight_endgame_source_capture_service(missing_capability)
        self.assertEqual(
            raised.exception.reason_code,
            "endgame_maturity_capability_not_advertised",
        )

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
            self.assertTrue(source_receipt["generic_character_rebind_used"])
            maturity = source_receipt["maturity_provider_proof"]
            self.assertEqual(maturity["history_status"], "partial")
            self.assertEqual(maturity["history_count"], 2)
            self.assertEqual(maturity["history_effective_count"], 2)
            self.assertEqual(maturity["prior_cycle_serials"], [1, 2])
            self.assertEqual(maturity["cycle_serial"], CYCLE)
            self.assertEqual(maturity["case_serial"], CASE)
            self.assertEqual(maturity["owner_character_id"], OWNER)
            self.assertEqual(maturity["subject_character_id"], SUBJECT)
            self.assertEqual(
                source_receipt["source_event_case_binding"],
                {
                    "event_definition_key": "zg361we.356",
                    "owner_character_id": OWNER,
                    "subject_character_id": SUBJECT,
                    "cycle_serial": CYCLE,
                    "case_serial": CASE,
                    "event_owner_subject_scopes_observed": True,
                    "received_self_current_case_provider_observed": True,
                    "numeric_binding_authority": (
                        "paused-zg361we.356-value-scopes+"
                        "source-trigger-full-guard+"
                        "received-self-current-case-provider"
                    ),
                    "event_scalar_saved_scopes": {
                        "zg361_we_al_cycle": {
                            **scalar_scope(),
                            "provider_field": "cycle_serial",
                            "provider_value": CYCLE,
                        },
                        "zg361_we_al_case": {
                            **scalar_scope(),
                            "provider_field": "case_serial",
                            "provider_value": CASE,
                        },
                    },
                },
            )
            self.assertEqual(len(set(maturity["receipt_ids"])), 6)
            self.assertEqual(len(set(maturity["receipt_hashes"])), 6)
            self.assertFalse(source_receipt["action_ack_used_as_state_evidence"])
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            result = Phase2SourceCheckpointProvider(
                registry,
                restore_registered_checkpoint=lambda _entry: {},
                expected_seed_lineage_id=SEED_LINEAGE_ID,
            ).preflight()
            self.assertEqual(result["result"], "GREEN")
            self.assertEqual(result["entry_count"], 4)

    def test_schema3_complete_appends_runtime_branch_without_common_seed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            captured_manifest: dict[str, object] = {}

            def assemble(
                manifest_path: Path,
                *,
                checkpoint_root: Path,
                registry_path: Path,
            ) -> dict[str, object]:
                del checkpoint_root
                captured_manifest.update(
                    json.loads(manifest_path.read_text(encoding="utf-8"))
                )
                registry = {"result": "GREEN", "schema_version": 3}
                registry_path.write_text(json.dumps(registry), encoding="utf-8")
                return registry

            receipt = capture_cross_cycle_endgame_source_checkpoint_v1(
                FakeCaptureService(root),
                prefix_manifest=make_schema3_prefix(root),
                capture_input_root=root / "capture-input",
                receipt_path=root / "endgame-receipt.json",
                completed_manifest_path=root / "completed-manifest.json",
                registry_checkpoint_root=root / "registry-checkpoints",
                registry_path=root / "registry.json",
                expected_owner_character_id=OWNER,
                expected_date_raw=DATE_RAW,
                runtime_capture_lineage=capture_lineage(
                    RUNTIME_SEED_LINEAGE_ID
                ),
                timeout_seconds=1,
                poll_interval_seconds=0,
                registry_assembler=assemble,
            )

            self.assertNotIn("seed_lineage_id", captured_manifest)
            bindings = captured_manifest["capture_lineage"][
                "entry_capture_lineages"
            ]
            self.assertEqual(
                [row["seed_lineage_id"] for row in bindings],
                [
                    SEED_LINEAGE_ID,
                    SEED_LINEAGE_ID,
                    SEED_LINEAGE_ID,
                    RUNTIME_SEED_LINEAGE_ID,
                ],
            )
            self.assertEqual(
                captured_manifest["lineage_set_id"],
                phase2_source_lineage_set_id(bindings),
            )
            self.assertEqual(
                receipt["source_receipt"]["save_lineage_id"],
                RUNTIME_SEED_LINEAGE_ID,
            )

    def test_arbitrary_356_without_two_complete_prior_cycles_is_red(self) -> None:
        mutations = {
            "wrong_status": lambda value: value["history"].__setitem__(
                "status", "empty"
            ),
            "wrong_effective_count": lambda value: value["history"].__setitem__(
                "effective_count", 1
            ),
            "non_increasing_cycles": lambda value: value["history"]["slots"][1][
                "cycle_serial"
            ].__setitem__("value", 1),
            "wrong_owner": lambda value: value["history"]["slots"][0][
                "owner_character_id"
            ].__setitem__("value", OWNER + 1),
            "receipt_id_collision": lambda value: value["history"]["slots"][1][
                "m357_receipt_id"
            ].__setitem__("value", 1001),
            "current_tuple_drift": lambda value: value["al_case"][
                "subject_character_id"
            ].__setitem__("value", SUBJECT + 1),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                immature = maturity_response()
                mutate(immature)
                receipt_path = root / "receipt.json"
                registry_path = root / "registry.json"
                with self.assertRaises(EndgameSourceCaptureError):
                    capture_cross_cycle_endgame_source_checkpoint_v1(
                        FakeCaptureService(root, maturity=immature),
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
                self.assertFalse(receipt_path.exists())
                self.assertFalse(registry_path.exists())

    def test_maturity_switch_receipt_must_be_honest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(EndgameSourceCaptureError) as raised:
                capture_cross_cycle_endgame_source_checkpoint_v1(
                    FakeCaptureService(root, switch_receipt_valid=False),
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
                "endgame_maturity_player_switch_invalid",
            )

    def test_native_save_must_advance_revision_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(EndgameSourceCaptureError) as raised:
                capture_cross_cycle_endgame_source_checkpoint_v1(
                    FakeCaptureService(root, save_revision_jump=2),
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
                "source_save_crossed_binding",
            )

    def test_maturity_switch_cannot_cross_connection_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(EndgameSourceCaptureError) as raised:
                capture_cross_cycle_endgame_source_checkpoint_v1(
                    FakeCaptureService(root, switch_generation_drift=True),
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
                "endgame_maturity_player_switch_invalid",
            )

    def test_source_event_requires_typed_cycle_and_case_value_scopes(self) -> None:
        class InvalidScalarService(FakeCaptureService):
            def query_current_event_window_context_v1(
                self, event_instance_id: int, *, expected_revision: int
            ) -> dict[str, object]:
                result = super().query_current_event_window_context_v1(
                    event_instance_id, expected_revision=expected_revision
                )
                context = result["current_event_window_context"]
                context["saved_scopes"][2]["scope"] = character_scope(OWNER)
                return result

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = InvalidScalarService(root)
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
                "source_event_scalar_scope_invalid",
            )
            self.assertEqual(service.save_calls, 0)

    def test_only_canonical_mature_owner_can_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(EndgameSourceCaptureError) as raised:
                capture_cross_cycle_endgame_source_checkpoint_v1(
                    FakeCaptureService(root),
                    prefix_manifest=make_prefix(root),
                    capture_input_root=root / "capture-input",
                    receipt_path=root / "receipt.json",
                    completed_manifest_path=root / "manifest.json",
                    registry_checkpoint_root=root / "registry-input",
                    registry_path=root / "registry.json",
                    expected_owner_character_id=OWNER + 1,
                    expected_date_raw=DATE_RAW,
                    runtime_capture_lineage=capture_lineage(),
                    timeout_seconds=1,
                    poll_interval_seconds=0,
                )
            self.assertEqual(
                raised.exception.reason_code,
                "endgame_maturity_owner_invalid",
            )

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

    def test_schema3_standalone_preflight_uses_lineage_set_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prefix_path = make_schema3_prefix(root)
            prefix = json.loads(prefix_path.read_text(encoding="utf-8"))
            result = subprocess.run(
                [
                    sys.executable,
                    str(
                        TOOLS
                        / "preflight_zg361_phase2_cross_cycle_endgame_source_capture.py"
                    ),
                    "--prefix",
                    str(prefix_path),
                    "--expected-lineage-set-id",
                    str(prefix["lineage_set_id"]),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads(result.stdout)
            self.assertEqual(receipt["result"], "GREEN")
            self.assertEqual(
                receipt["lineage_set_id"], prefix["lineage_set_id"]
            )
            self.assertNotIn("seed_lineage_id", receipt)
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

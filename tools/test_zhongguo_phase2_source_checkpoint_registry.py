#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from zhongguo_phase2_event_choreography import (  # noqa: E402
    PHASE2_EVENT_SEQUENCE_PLANS,
)
from zhongguo_phase2_source_checkpoint_provider import (  # noqa: E402
    CHECKPOINT_REQUIRED_HANDLERS,
    LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
    MULTI_BRANCH_CAPTURE_LINEAGE_MODE,
    PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND,
    SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
    Phase2SourceCheckpointProvider,
)
from zhongguo_phase2_source_checkpoint_registry import (  # noqa: E402
    SOURCE_CHECKPOINT_CAPTURE_MANIFEST_KIND,
    Phase2SourceCheckpointRegistryBuildError,
    Phase2SourceCheckpointRegistryBuilder,
    build_registry_from_capture_manifest,
)
from test_zg361_phase2_incident_checkpoint_seam import (  # noqa: E402
    CaptureAndActionService,
    player_switch_locator,
)
from zg361_phase2_incident_source_capture_entry import (  # noqa: E402
    GENERIC_REBIND_AUTHORITY,
)
from zg361_phase2_incident_checkpoint_seam import (  # noqa: E402
    capture_current_received_self_incident_checkpoint_v1,
)
from test_zg361_phase2_cross_cycle_endgame_source_capture import (  # noqa: E402
    DATE_RAW as ENDGAME_DATE_RAW,
    OWNER as ENDGAME_OWNER,
    maturity_receipt_fields,
)


SEED_LINEAGE_ID = "phase2-seed-live-unit"
MULTI_BRANCH_LINEAGES = {
    "capture_promotion_compensation": "A400",
    "capture_projects_metrics": "A400",
    "capture_incidents_operations": "8E6C/R106",
    "capture_cross_cycle_endgame": "ENDGAME-R356",
}
PLANS = {
    plan.handler: plan
    for plan in PHASE2_EVENT_SEQUENCE_PLANS
    if plan.handler in CHECKPOINT_REQUIRED_HANDLERS
}
REPOSITORY_ROOT = TOOLS.parent
EXPECTED_SOURCE_EVENTS = {
    "capture_promotion_compensation": "zg361pp.147",
    "capture_projects_metrics": "zg361cp.26",
    "capture_incidents_operations": "zg361.50",
    "capture_cross_cycle_endgame": "zg361we.356",
}


def source_receipt(
    *,
    plan,
    owner_character_id: int,
    player_character_id: int,
    date_raw: int,
    checkpoint_sha256: str,
    save_lineage_id: str = SEED_LINEAGE_ID,
) -> dict[str, object]:
    receipt = {
        "result": "GREEN",
        "evidence_class": "real_ck3",
        "provider_observed": True,
        "ui_state_verified": True,
        "fixture_used": False,
        "console_used": False,
        "span_id": plan.span_id,
        "event_definition_key": plan.source_event,
        "owner_character_id": owner_character_id,
        "player_character_id": player_character_id,
        "date_raw": date_raw,
        "checkpoint_sha256": checkpoint_sha256,
        "save_lineage_id": save_lineage_id,
    }
    if plan.handler == "capture_cross_cycle_endgame":
        receipt.update(maturity_receipt_fields())
    return receipt


def strict_incident_checkpoint(
    root: Path, *, seed_lineage_id: str
) -> tuple[dict[str, object], Path]:
    capture_root = root / "strict-incident-input"
    capture_root.mkdir(parents=True, exist_ok=True)
    service = CaptureAndActionService(capture_root)
    receipt = capture_current_received_self_incident_checkpoint_v1(
        service,
        checkpoint_root=capture_root / "checkpoints",
        receipt_path=capture_root / "receipt.json",
        seed_lineage_id=seed_lineage_id,
        capture_lineage={
            "seed_lineage_id": seed_lineage_id,
            "evidence_class": "real_ck3",
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
            "generic_character_rebind_used": True,
            "generic_character_rebind_authority": GENERIC_REBIND_AUTHORITY,
        },
        player_switch_receipt=player_switch_locator(
            capture_root,
            service,
            seed_lineage_id=seed_lineage_id,
        ),
    )
    checkpoint = receipt["checkpoint"]
    assert isinstance(checkpoint, dict)
    return receipt, Path(str(checkpoint["path"]))


def record_all(
    builder: Phase2SourceCheckpointRegistryBuilder,
    source_root: Path,
) -> list[dict[str, object]]:
    entries = []
    for ordinal, handler in enumerate(CHECKPOINT_REQUIRED_HANDLERS, 1):
        plan = PLANS[handler]
        save_lineage_id = builder.handler_save_lineage_ids[handler]
        strict_receipt = None
        if handler == "capture_incidents_operations":
            strict_receipt, source = strict_incident_checkpoint(
                source_root, seed_lineage_id=save_lineage_id
            )
            owner = int(strict_receipt["owner_character_id"])
            player = int(strict_receipt["player_character_id"])
            date_raw = int(strict_receipt["date_raw"])
        else:
            source = source_root / f"source-{ordinal}.ck3"
            source.write_bytes(
                f"real-ck3-checkpoint-{ordinal}".encode("ascii")
            )
            owner = 9100 + ordinal
            player = 9001
            date_raw = 720 + ordinal
            if handler == "capture_cross_cycle_endgame":
                owner = ENDGAME_OWNER
                player = ENDGAME_OWNER
                date_raw = ENDGAME_DATE_RAW
        sha256 = hashlib.sha256(source.read_bytes()).hexdigest().upper()
        entries.append(
            builder.record(
                plan,
                source_checkpoint=source,
                owner_character_id=owner,
                player_character_id=player,
                date_raw=date_raw,
                source_receipt=source_receipt(
                    plan=plan,
                    owner_character_id=owner,
                    player_character_id=player,
                    date_raw=date_raw,
                    checkpoint_sha256=sha256,
                    save_lineage_id=save_lineage_id,
                ),
                save_lineage_id=save_lineage_id,
                strict_incident_source_checkpoint_receipt=strict_receipt,
            )
        )
    return entries


def _lineage_set_id(entry_capture_lineages: list[dict[str, object]]) -> str:
    payload = json.dumps(
        [
            {
                "handler": row["handler"],
                "seed_lineage_id": row["seed_lineage_id"],
                **(
                    {
                        "capture_run_input_checkpoint_sha256": row[
                            "capture_run_input_checkpoint"
                        ]["sha256"]
                    }
                    if row["handler"] == "capture_incidents_operations"
                    else {}
                ),
            }
            for row in entry_capture_lineages
        ],
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return "zg361-phase2-lineage-set-" + hashlib.sha256(payload).hexdigest()


def capture_manifest(root: Path, *, multi_branch: bool = False) -> Path:
    entries = []
    for ordinal, handler in enumerate(CHECKPOINT_REQUIRED_HANDLERS, 1):
        plan = PLANS[handler]
        save_lineage_id = (
            MULTI_BRANCH_LINEAGES[handler]
            if multi_branch
            else SEED_LINEAGE_ID
        )
        strict_receipt = None
        if handler == "capture_incidents_operations":
            strict_receipt, checkpoint = strict_incident_checkpoint(
                root, seed_lineage_id=save_lineage_id
            )
            owner = int(strict_receipt["owner_character_id"])
            player = int(strict_receipt["player_character_id"])
            date_raw = int(strict_receipt["date_raw"])
        else:
            checkpoint = root / f"observed-{ordinal}.ck3"
            checkpoint.write_bytes(
                f"observed-checkpoint-{ordinal}".encode("ascii")
            )
            owner = 9200 + ordinal
            player = 9001
            date_raw = 820 + ordinal
            if handler == "capture_cross_cycle_endgame":
                owner = ENDGAME_OWNER
                player = ENDGAME_OWNER
                date_raw = ENDGAME_DATE_RAW
        sha256 = hashlib.sha256(checkpoint.read_bytes()).hexdigest().upper()
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
                    "save_lineage_id": save_lineage_id,
                },
                "source_receipt": source_receipt(
                    plan=plan,
                    owner_character_id=owner,
                    player_character_id=player,
                    date_raw=date_raw,
                    checkpoint_sha256=sha256,
                    save_lineage_id=save_lineage_id,
                ),
            }
        if strict_receipt is not None:
            row["received_self_incident_checkpoint_receipt"] = strict_receipt
        entries.append(row)
    if multi_branch:
        capture_run_input_path = (root / "incident-run-input.ck3").resolve()
        capture_run_input_path.write_bytes(b"incident-run-input")
        capture_run_input = {
            "path": str(capture_run_input_path),
            "bytes": capture_run_input_path.stat().st_size,
            "sha256": hashlib.sha256(
                capture_run_input_path.read_bytes()
            ).hexdigest().upper(),
        }
        entry_capture_lineages = [
            {
                "handler": handler,
                "seed_lineage_id": MULTI_BRANCH_LINEAGES[handler],
                "capture_lineage": {
                    "seed_lineage_id": MULTI_BRANCH_LINEAGES[handler],
                },
                **(
                    {"capture_run_input_checkpoint": capture_run_input}
                    if handler == "capture_incidents_operations"
                    else {}
                ),
            }
            for handler in CHECKPOINT_REQUIRED_HANDLERS
        ]
        lineage_set_id = _lineage_set_id(entry_capture_lineages)
        lineage_header = {
            "lineage_set_id": lineage_set_id,
            "capture_lineage": {
                "schema_version": 2,
                "kind": PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND,
                "capture_lineage_mode": MULTI_BRANCH_CAPTURE_LINEAGE_MODE,
                "lineage_set_id": lineage_set_id,
                "evidence_class": "real_ck3",
                "fixture_used": False,
                "console_used": False,
                "entry_capture_lineages": entry_capture_lineages,
            },
        }
        schema_version = SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
    else:
        lineage_header = {
            "seed_lineage_id": SEED_LINEAGE_ID,
            "capture_lineage": {
                "seed_lineage_id": SEED_LINEAGE_ID,
                "source": "bound-live-capture-receipts",
            },
        }
        schema_version = LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
    path = root / "capture-manifest.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": schema_version,
                "kind": SOURCE_CHECKPOINT_CAPTURE_MANIFEST_KIND,
                "result": "GREEN",
                "evidence_class": "real_ck3",
                "fixture_used": False,
                "console_used": False,
                **lineage_header,
                "entries": entries,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


class Phase2SourceCheckpointRegistryBuilderTests(unittest.TestCase):
    def builder(self, root: Path) -> Phase2SourceCheckpointRegistryBuilder:
        return Phase2SourceCheckpointRegistryBuilder(
            root / "frozen",
            seed_lineage_id=SEED_LINEAGE_ID,
            capture_lineage={
                "seed_lineage_id": SEED_LINEAGE_ID,
                "source": "real_phase2_capture",
            },
        )

    def multi_branch_builder(
        self, root: Path
    ) -> tuple[Phase2SourceCheckpointRegistryBuilder, str]:
        capture_run_input_path = (root / "incident-run-input.ck3").resolve()
        capture_run_input_path.write_bytes(b"incident-run-input")
        capture_run_input = {
            "path": str(capture_run_input_path),
            "bytes": capture_run_input_path.stat().st_size,
            "sha256": hashlib.sha256(
                capture_run_input_path.read_bytes()
            ).hexdigest().upper(),
        }
        entry_capture_lineages = [
            {
                "handler": handler,
                "seed_lineage_id": MULTI_BRANCH_LINEAGES[handler],
                "capture_lineage": {
                    "seed_lineage_id": MULTI_BRANCH_LINEAGES[handler],
                },
                **(
                    {"capture_run_input_checkpoint": capture_run_input}
                    if handler == "capture_incidents_operations"
                    else {}
                ),
            }
            for handler in CHECKPOINT_REQUIRED_HANDLERS
        ]
        lineage_set_id = _lineage_set_id(entry_capture_lineages)
        return (
            Phase2SourceCheckpointRegistryBuilder(
                root / "frozen-v3",
                lineage_set_id=lineage_set_id,
                capture_lineage={
                    "schema_version": 2,
                    "kind": PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND,
                    "capture_lineage_mode": MULTI_BRANCH_CAPTURE_LINEAGE_MODE,
                    "lineage_set_id": lineage_set_id,
                    "evidence_class": "real_ck3",
                    "fixture_used": False,
                    "console_used": False,
                    "entry_capture_lineages": entry_capture_lineages,
                },
            ),
            lineage_set_id,
        )

    def test_freezes_four_real_checkpoints_and_provider_accepts_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder = self.builder(root)
            entries = record_all(builder, root)
            registry_path = root / "registry.json"
            registry = builder.write(registry_path)

            self.assertEqual(
                [row["handler"] for row in entries],
                list(CHECKPOINT_REQUIRED_HANDLERS),
            )
            self.assertEqual(registry["result"], "GREEN")
            self.assertEqual(registry["evidence_class"], "real_ck3")
            self.assertFalse(registry["fixture_used"])
            self.assertFalse(registry["console_used"])
            incident = next(
                row
                for row in registry["entries"]
                if row["handler"] == "capture_incidents_operations"
            )
            self.assertNotEqual(
                incident["owner_character_id"],
                incident["player_character_id"],
            )
            strict_locator = incident[
                "received_self_incident_checkpoint_receipt"
            ]
            strict_path = Path(strict_locator["path"])
            self.assertTrue(strict_path.is_file())
            self.assertEqual(strict_path.stat().st_size, strict_locator["bytes"])
            self.assertEqual(
                hashlib.sha256(strict_path.read_bytes()).hexdigest().upper(),
                strict_locator["sha256"],
            )
            archived_strict = json.loads(
                strict_path.read_text(encoding="utf-8")
            )
            self.assertEqual(
                archived_strict["checkpoint"]["path"],
                incident["checkpoint"]["path"],
            )
            self.assertEqual(
                json.loads(registry_path.read_text(encoding="utf-8")),
                registry,
            )
            for entry in registry["entries"]:
                checkpoint = entry["checkpoint"]
                archived = Path(checkpoint["path"])
                self.assertTrue(archived.is_file())
                self.assertEqual(archived.stat().st_size, checkpoint["bytes"])
                self.assertEqual(
                    hashlib.sha256(archived.read_bytes()).hexdigest().upper(),
                    checkpoint["sha256"],
                )

            provider = Phase2SourceCheckpointProvider(
                registry,
                restore_registered_checkpoint=lambda _entry: {},
                expected_seed_lineage_id=SEED_LINEAGE_ID,
            )
            self.assertEqual(provider.preflight()["result"], "GREEN")

    def test_schema_v3_builder_freezes_per_handler_lineages(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder, lineage_set_id = self.multi_branch_builder(root)
            record_all(builder, root)
            registry = builder.finalize()
            provider = Phase2SourceCheckpointProvider(
                registry,
                restore_registered_checkpoint=lambda _entry: {},
                expected_lineage_set_id=lineage_set_id,
            )
            preflight = provider.preflight()
        self.assertEqual(
            registry["schema_version"],
            SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
        )
        self.assertNotIn("seed_lineage_id", registry)
        self.assertEqual(registry["lineage_set_id"], lineage_set_id)
        self.assertEqual(
            {
                row["handler"]: row["save_lineage_id"]
                for row in registry["entries"]
            },
            MULTI_BRANCH_LINEAGES,
        )
        self.assertEqual(
            preflight["handler_save_lineage_ids"],
            MULTI_BRANCH_LINEAGES,
        )

    def test_requires_canonical_handler_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder = self.builder(root)
            plan = PLANS[CHECKPOINT_REQUIRED_HANDLERS[1]]
            source = root / "source.ck3"
            source.write_bytes(b"real-checkpoint")
            sha256 = hashlib.sha256(source.read_bytes()).hexdigest().upper()
            with self.assertRaises(
                Phase2SourceCheckpointRegistryBuildError
            ) as raised:
                builder.record(
                    plan,
                    source_checkpoint=source,
                    owner_character_id=9002,
                    player_character_id=9001,
                    date_raw=721,
                    source_receipt=source_receipt(
                        plan=plan,
                        owner_character_id=9002,
                        player_character_id=9001,
                        date_raw=721,
                        checkpoint_sha256=sha256,
                    ),
                )
            self.assertEqual(
                raised.exception.reason_code,
                "source_checkpoint_record_order_invalid",
            )

    def test_rejects_unobserved_receipt_before_archiving(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder = self.builder(root)
            plan = PLANS[CHECKPOINT_REQUIRED_HANDLERS[0]]
            source = root / "source.ck3"
            source.write_bytes(b"real-checkpoint")
            sha256 = hashlib.sha256(source.read_bytes()).hexdigest().upper()
            receipt = source_receipt(
                plan=plan,
                owner_character_id=9002,
                player_character_id=9001,
                date_raw=721,
                checkpoint_sha256=sha256,
            )
            receipt["provider_observed"] = False
            with self.assertRaises(
                Phase2SourceCheckpointRegistryBuildError
            ) as raised:
                builder.record(
                    plan,
                    source_checkpoint=source,
                    owner_character_id=9002,
                    player_character_id=9001,
                    date_raw=721,
                    source_receipt=receipt,
                )
            self.assertEqual(
                raised.exception.reason_code,
                "source_checkpoint_receipt_invalid",
            )
            self.assertFalse((root / "frozen").exists())

    def test_incident_requires_distinct_notice_owner_and_played_subject(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder = self.builder(root)
            for ordinal, handler in enumerate(
                CHECKPOINT_REQUIRED_HANDLERS[:2], 1
            ):
                plan = PLANS[handler]
                source = root / f"source-{ordinal}.ck3"
                source.write_bytes(f"checkpoint-{ordinal}".encode("ascii"))
                sha256 = hashlib.sha256(source.read_bytes()).hexdigest().upper()
                builder.record(
                    plan,
                    source_checkpoint=source,
                    owner_character_id=9100 + ordinal,
                    player_character_id=9001,
                    date_raw=720 + ordinal,
                    source_receipt=source_receipt(
                        plan=plan,
                        owner_character_id=9100 + ordinal,
                        player_character_id=9001,
                        date_raw=720 + ordinal,
                        checkpoint_sha256=sha256,
                    ),
                )

            plan = PLANS["capture_incidents_operations"]
            source = root / "incident.ck3"
            source.write_bytes(b"incident-checkpoint")
            sha256 = hashlib.sha256(source.read_bytes()).hexdigest().upper()
            with self.assertRaises(
                Phase2SourceCheckpointRegistryBuildError
            ) as raised:
                builder.record(
                    plan,
                    source_checkpoint=source,
                    owner_character_id=9200,
                    player_character_id=9200,
                    date_raw=723,
                    source_receipt=source_receipt(
                        plan=plan,
                        owner_character_id=9200,
                        player_character_id=9200,
                        date_raw=723,
                        checkpoint_sha256=sha256,
                    ),
                )
            self.assertEqual(
                raised.exception.reason_code,
                "incident_checkpoint_owner_equals_player",
            )
            self.assertEqual(
                raised.exception.evidence["required_binding"],
                "played_subject_with_distinct_notice_owner",
            )

    def test_incomplete_registry_and_second_write_are_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder = self.builder(root)
            with self.assertRaises(
                Phase2SourceCheckpointRegistryBuildError
            ) as raised:
                builder.finalize()
            self.assertEqual(
                raised.exception.reason_code,
                "source_checkpoint_registry_incomplete",
            )

            record_all(builder, root)
            registry_path = root / "registry.json"
            builder.write(registry_path)
            with self.assertRaises(
                Phase2SourceCheckpointRegistryBuildError
            ) as raised:
                builder.write(registry_path)
            self.assertEqual(
                raised.exception.reason_code,
                "source_checkpoint_registry_already_exists",
            )

    def test_capture_lineage_must_match_seed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(
                Phase2SourceCheckpointRegistryBuildError
            ) as raised:
                Phase2SourceCheckpointRegistryBuilder(
                    Path(temporary),
                    seed_lineage_id=SEED_LINEAGE_ID,
                    capture_lineage={"seed_lineage_id": "other-seed"},
                )
            self.assertEqual(
                raised.exception.reason_code,
                "source_checkpoint_registry_lineage_invalid",
            )

    def test_sharded_product_contains_each_required_source_event_once(self) -> None:
        events_root = REPOSITORY_ROOT / "mod_zhongguo_style" / "events"
        corpus = "\n".join(
            path.read_text(encoding="utf-8-sig")
            for path in sorted(events_root.glob("*.txt"))
        )
        self.assertEqual(
            {
                handler: PLANS[handler].source_event
                for handler in CHECKPOINT_REQUIRED_HANDLERS
            },
            EXPECTED_SOURCE_EVENTS,
        )
        for event in EXPECTED_SOURCE_EVENTS.values():
            matches = re.findall(
                rf"(?m)^\s*({re.escape(event)})\s*=\s*\{{", corpus
            )
            self.assertEqual(matches, [event], event)

    def test_capture_manifest_is_archived_and_consumable_by_runner_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = capture_manifest(root)
            registry_path = root / "registry.json"
            registry = build_registry_from_capture_manifest(
                manifest,
                checkpoint_root=root / "frozen",
                registry_path=registry_path,
            )
            provider = Phase2SourceCheckpointProvider(
                registry,
                restore_registered_checkpoint=lambda _entry: {},
                expected_seed_lineage_id=SEED_LINEAGE_ID,
            )
            self.assertEqual(provider.preflight()["entry_count"], 4)
            for handler in CHECKPOINT_REQUIRED_HANDLERS:
                entry = provider.checkpoint_for_plan(PLANS[handler])
                self.assertEqual(
                    entry.source_event_definition_key,
                    EXPECTED_SOURCE_EVENTS[handler],
                )
                self.assertTrue(entry.path.is_file())

    def test_schema_v3_capture_manifest_archives_multi_branch_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = capture_manifest(root, multi_branch=True)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            registry = build_registry_from_capture_manifest(
                manifest,
                checkpoint_root=root / "frozen",
                registry_path=root / "registry.json",
            )
            provider = Phase2SourceCheckpointProvider(
                registry,
                restore_registered_checkpoint=lambda _entry: {},
                expected_lineage_set_id=payload["lineage_set_id"],
            )
            preflight = provider.preflight()
        self.assertEqual(
            preflight["handler_save_lineage_ids"],
            MULTI_BRANCH_LINEAGES,
        )
        self.assertNotIn("seed_lineage_id", registry)

    def test_schema_v3_manifest_rejects_incident_a400_mislabel(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = capture_manifest(root, multi_branch=True)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            incident = next(
                row
                for row in payload["entries"]
                if row["handler"] == "capture_incidents_operations"
            )
            incident["checkpoint"]["save_lineage_id"] = "A400"
            incident["source_receipt"]["save_lineage_id"] = "A400"
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(
                Phase2SourceCheckpointRegistryBuildError
            ) as raised:
                build_registry_from_capture_manifest(
                    manifest,
                    checkpoint_root=root / "frozen",
                    registry_path=root / "registry.json",
                )
        self.assertEqual(
            raised.exception.reason_code,
            "source_checkpoint_capture_entry_invalid",
        )

    def test_schema_v3_manifest_rejects_malformed_incident_input_record(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = capture_manifest(root, multi_branch=True)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            incident_lineage = next(
                row
                for row in payload["capture_lineage"][
                    "entry_capture_lineages"
                ]
                if row["handler"] == "capture_incidents_operations"
            )
            del incident_lineage["capture_run_input_checkpoint"]["bytes"]
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(
                Phase2SourceCheckpointRegistryBuildError
            ) as raised:
                build_registry_from_capture_manifest(
                    manifest,
                    checkpoint_root=root / "frozen",
                    registry_path=root / "registry.json",
                )
        self.assertEqual(
            raised.exception.reason_code,
            "source_checkpoint_registry_lineage_set_invalid",
        )

    def test_cli_builds_registry_from_existing_checkpoint_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = capture_manifest(root)
            registry = root / "registry.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(TOOLS / "zhongguo_phase2_source_checkpoint_registry.py"),
                    "--capture-manifest",
                    str(manifest),
                    "--checkpoint-root",
                    str(root / "frozen"),
                    "--output",
                    str(registry),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                json.loads(registry.read_text(encoding="utf-8"))["result"],
                "GREEN",
            )

    def test_capture_manifest_cannot_claim_fixture_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = capture_manifest(root)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["fixture_used"] = True
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(
                Phase2SourceCheckpointRegistryBuildError
            ) as raised:
                build_registry_from_capture_manifest(
                    manifest,
                    checkpoint_root=root / "frozen",
                    registry_path=root / "registry.json",
                )
            self.assertEqual(
                raised.exception.reason_code,
                "source_checkpoint_capture_manifest_header_invalid",
            )

    def test_capture_manifest_incident_requires_strict_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = capture_manifest(root)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            incident = next(
                row
                for row in payload["entries"]
                if row["handler"] == "capture_incidents_operations"
            )
            del incident["received_self_incident_checkpoint_receipt"]
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(
                Phase2SourceCheckpointRegistryBuildError
            ) as raised:
                build_registry_from_capture_manifest(
                    manifest,
                    checkpoint_root=root / "frozen",
                    registry_path=root / "registry.json",
                )
            self.assertEqual(
                raised.exception.reason_code,
                "incident_source_checkpoint_receipt_invalid",
            )


if __name__ == "__main__":
    unittest.main()

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
    Phase2SourceCheckpointProvider,
)
from zhongguo_phase2_source_checkpoint_registry import (  # noqa: E402
    SOURCE_CHECKPOINT_CAPTURE_MANIFEST_KIND,
    Phase2SourceCheckpointRegistryBuildError,
    Phase2SourceCheckpointRegistryBuilder,
    build_registry_from_capture_manifest,
)


SEED_LINEAGE_ID = "phase2-seed-live-unit"
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
) -> dict[str, object]:
    return {
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
        "save_lineage_id": SEED_LINEAGE_ID,
    }


def record_all(
    builder: Phase2SourceCheckpointRegistryBuilder,
    source_root: Path,
) -> list[dict[str, object]]:
    entries = []
    for ordinal, handler in enumerate(CHECKPOINT_REQUIRED_HANDLERS, 1):
        plan = PLANS[handler]
        source = source_root / f"source-{ordinal}.ck3"
        source.write_bytes(f"real-ck3-checkpoint-{ordinal}".encode("ascii"))
        sha256 = hashlib.sha256(source.read_bytes()).hexdigest().upper()
        owner = 9100 + ordinal
        player = owner if handler == "capture_incidents_operations" else 9001
        entries.append(
            builder.record(
                plan,
                source_checkpoint=source,
                owner_character_id=owner,
                player_character_id=player,
                date_raw=720 + ordinal,
                source_receipt=source_receipt(
                    plan=plan,
                    owner_character_id=owner,
                    player_character_id=player,
                    date_raw=720 + ordinal,
                    checkpoint_sha256=sha256,
                ),
            )
        )
    return entries


def capture_manifest(root: Path) -> Path:
    entries = []
    for ordinal, handler in enumerate(CHECKPOINT_REQUIRED_HANDLERS, 1):
        plan = PLANS[handler]
        checkpoint = root / f"observed-{ordinal}.ck3"
        checkpoint.write_bytes(f"observed-checkpoint-{ordinal}".encode("ascii"))
        sha256 = hashlib.sha256(checkpoint.read_bytes()).hexdigest().upper()
        owner = 9200 + ordinal
        player = owner if handler == "capture_incidents_operations" else 9001
        date_raw = 820 + ordinal
        entries.append(
            {
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
                "source_receipt": source_receipt(
                    plan=plan,
                    owner_character_id=owner,
                    player_character_id=player,
                    date_raw=date_raw,
                    checkpoint_sha256=sha256,
                ),
            }
        )
    path = root / "capture-manifest.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": SOURCE_CHECKPOINT_CAPTURE_MANIFEST_KIND,
                "result": "GREEN",
                "evidence_class": "real_ck3",
                "fixture_used": False,
                "console_used": False,
                "seed_lineage_id": SEED_LINEAGE_ID,
                "capture_lineage": {
                    "seed_lineage_id": SEED_LINEAGE_ID,
                    "source": "bound-live-capture-receipts",
                },
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

    def test_incident_requires_current_player_to_be_owner(self) -> None:
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
                    player_character_id=9001,
                    date_raw=723,
                    source_receipt=source_receipt(
                        plan=plan,
                        owner_character_id=9200,
                        player_character_id=9001,
                        date_raw=723,
                        checkpoint_sha256=sha256,
                    ),
                )
            self.assertEqual(
                raised.exception.reason_code,
                "incident_checkpoint_player_not_owner",
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


if __name__ == "__main__":
    unittest.main()

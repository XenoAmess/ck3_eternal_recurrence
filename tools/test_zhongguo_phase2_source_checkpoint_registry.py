#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
from pathlib import Path
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
    Phase2SourceCheckpointRegistryBuildError,
    Phase2SourceCheckpointRegistryBuilder,
)


SEED_LINEAGE_ID = "phase2-seed-live-unit"
PLANS = {
    plan.handler: plan
    for plan in PHASE2_EVENT_SEQUENCE_PLANS
    if plan.handler in CHECKPOINT_REQUIRED_HANDLERS
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


if __name__ == "__main__":
    unittest.main()

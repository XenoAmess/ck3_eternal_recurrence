#!/usr/bin/env python3

from __future__ import annotations

import hashlib
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
    INCIDENT_STRICT_RECEIPT_FIELD,
    SOURCE_CHECKPOINT_REGISTRY_KIND,
    SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
    Phase2SourceCheckpointError,
    Phase2SourceCheckpointProvider,
)
from test_zhongguo_phase2_source_checkpoint_registry import (  # noqa: E402
    strict_incident_checkpoint,
)


def _registry(root: Path) -> dict[str, object]:
    seed_lineage_id = "seed-lineage-unit"
    plans = {
        plan.handler: plan
        for plan in PHASE2_EVENT_SEQUENCE_PLANS
        if plan.handler in CHECKPOINT_REQUIRED_HANDLERS
    }
    entries = []
    for index, handler in enumerate(CHECKPOINT_REQUIRED_HANDLERS, 1):
        plan = plans[handler]
        strict_receipt = None
        if handler == "capture_incidents_operations":
            strict_receipt, path = strict_incident_checkpoint(
                root, seed_lineage_id=seed_lineage_id
            )
            owner = int(strict_receipt["owner_character_id"])
            player = int(strict_receipt["player_character_id"])
            date_raw = int(strict_receipt["date_raw"])
        else:
            path = (root / f"{index}-{plan.span_id}.ck3").resolve()
            path.write_bytes(f"real-checkpoint-{index}".encode("ascii"))
            owner = 9100 + index
            player = 9001
            date_raw = 700 + index
        sha = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        row = {
                "span_id": plan.span_id,
                "handler": handler,
                "source_event_definition_key": plan.source_event,
                "owner_character_id": owner,
                "player_character_id": player,
                "date_raw": date_raw,
                "checkpoint": {
                    "path": str(path),
                    "bytes": path.stat().st_size,
                    "sha256": sha,
                    "save_lineage_id": seed_lineage_id,
                },
                "source_receipt": {
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
                    "checkpoint_sha256": sha,
                    "save_lineage_id": seed_lineage_id,
                },
            }
        if strict_receipt is not None:
            receipt_path = root / "strict-incident-input" / "receipt.json"
            row[INCIDENT_STRICT_RECEIPT_FIELD] = {
                "kind": (
                    "zg361_phase2_incidents_operations_"
                    "source_checkpoint_receipt"
                ),
                "path": str(receipt_path.resolve()),
                "bytes": receipt_path.stat().st_size,
                "sha256": hashlib.sha256(
                    receipt_path.read_bytes()
                ).hexdigest().upper(),
            }
        entries.append(row)
    return {
        "schema_version": SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
        "registry_kind": SOURCE_CHECKPOINT_REGISTRY_KIND,
        "result": "GREEN",
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "console_used": False,
        "seed_lineage_id": seed_lineage_id,
        "capture_lineage": {"seed_lineage_id": seed_lineage_id},
        "entries": entries,
    }


class Phase2SourceCheckpointProviderTests(unittest.TestCase):
    def test_missing_registry_and_restore_provider_are_explicit_red(self) -> None:
        provider = Phase2SourceCheckpointProvider(
            None,
            restore_registered_checkpoint=None,
            expected_seed_lineage_id="seed-lineage-unit",
        )
        with self.assertRaises(Phase2SourceCheckpointError) as raised:
            provider.preflight()
        self.assertEqual(
            raised.exception.reason_code, "source_checkpoint_registry_missing"
        )

        with tempfile.TemporaryDirectory() as temporary:
            registry = _registry(Path(temporary))
            provider = Phase2SourceCheckpointProvider(
                registry,
                restore_registered_checkpoint=None,
                expected_seed_lineage_id="seed-lineage-unit",
            )
            with self.assertRaises(Phase2SourceCheckpointError) as raised:
                provider.checkpoint_for_plan(PHASE2_EVENT_SEQUENCE_PLANS[3])
        self.assertEqual(
            raised.exception.reason_code,
            "registered_checkpoint_restore_provider_missing",
        )

    def test_valid_registry_covers_exact_four_handlers_and_real_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            registry = _registry(Path(temporary))
            provider = Phase2SourceCheckpointProvider(
                registry,
                restore_registered_checkpoint=lambda _entry: {},
                expected_seed_lineage_id="seed-lineage-unit",
            )
            preflight = provider.preflight()
        self.assertEqual(preflight["result"], "GREEN")
        self.assertEqual(preflight["required_handlers"], list(CHECKPOINT_REQUIRED_HANDLERS))
        self.assertEqual(preflight["entry_count"], 4)
        self.assertTrue(preflight["restore_interface_available"])
        self.assertEqual(
            preflight["incident_received_self_checkpoint"]["readiness"],
            "captured-real-checkpoint",
        )

    def test_restore_passes_one_registered_entry_without_generic_rebind(self) -> None:
        calls = []

        def restore(entry):
            calls.append(entry)
            return {
                "result": "GREEN",
                "provider_observed": True,
                "checkpoint_sha256": entry.sha256,
                "save_lineage_id": entry.save_lineage_id,
                "player_character_id": entry.player_character_id,
                "owner_character_id": entry.owner_character_id,
                "date_raw": entry.date_raw,
                "event_definition_key": entry.source_event_definition_key,
                "fixture_used": False,
                "console_used": False,
                "generic_character_rebind_used": False,
            }

        with tempfile.TemporaryDirectory() as temporary:
            registry = _registry(Path(temporary))
            provider = Phase2SourceCheckpointProvider(
                registry,
                restore_registered_checkpoint=restore,
                expected_seed_lineage_id="seed-lineage-unit",
            )
            plan = next(
                row
                for row in PHASE2_EVENT_SEQUENCE_PLANS
                if row.handler == "capture_incidents_operations"
            )
            result = provider.restore(plan)
        self.assertEqual(len(calls), 1)
        self.assertNotEqual(
            calls[0].owner_character_id,
            calls[0].player_character_id,
        )
        self.assertFalse(result["generic_character_rebind_used"])
        self.assertFalse(result["fixture_used"])
        self.assertFalse(result["console_used"])

    def test_hash_drift_and_incident_owner_equal_player_are_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = _registry(root)
            first = registry["entries"][0]
            Path(first["checkpoint"]["path"]).write_bytes(b"drifted")
            provider = Phase2SourceCheckpointProvider(
                registry,
                restore_registered_checkpoint=lambda _entry: {},
                expected_seed_lineage_id="seed-lineage-unit",
            )
            with self.assertRaises(Phase2SourceCheckpointError) as raised:
                provider.preflight()
            self.assertEqual(
                raised.exception.reason_code, "source_checkpoint_entry_invalid"
            )

        with tempfile.TemporaryDirectory() as temporary:
            registry = _registry(Path(temporary))
            incident = next(
                row
                for row in registry["entries"]
                if row["handler"] == "capture_incidents_operations"
            )
            incident["player_character_id"] = incident["owner_character_id"]
            incident["source_receipt"]["player_character_id"] = incident[
                "owner_character_id"
            ]
            provider = Phase2SourceCheckpointProvider(
                registry,
                restore_registered_checkpoint=lambda _entry: {},
                expected_seed_lineage_id="seed-lineage-unit",
            )
            with self.assertRaises(Phase2SourceCheckpointError) as raised:
                provider.preflight()
            self.assertEqual(
                raised.exception.reason_code,
                "incident_checkpoint_owner_equals_player",
            )
            self.assertEqual(
                raised.exception.evidence["required_binding"],
                "played_subject_with_distinct_notice_owner",
            )

    def test_incident_requires_strict_receipt_and_cross_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            registry = _registry(Path(temporary))
            incident = next(
                row
                for row in registry["entries"]
                if row["handler"] == "capture_incidents_operations"
            )
            del incident[INCIDENT_STRICT_RECEIPT_FIELD]
            provider = Phase2SourceCheckpointProvider(
                registry,
                restore_registered_checkpoint=lambda _entry: {},
                expected_seed_lineage_id="seed-lineage-unit",
            )
            with self.assertRaises(Phase2SourceCheckpointError) as raised:
                provider.preflight()
            self.assertEqual(
                raised.exception.reason_code,
                "incident_source_checkpoint_receipt_missing",
            )

        with tempfile.TemporaryDirectory() as temporary:
            registry = _registry(Path(temporary))
            incident = next(
                row
                for row in registry["entries"]
                if row["handler"] == "capture_incidents_operations"
            )
            incident["date_raw"] = int(incident["date_raw"]) + 1
            incident["source_receipt"]["date_raw"] = incident["date_raw"]
            provider = Phase2SourceCheckpointProvider(
                registry,
                restore_registered_checkpoint=lambda _entry: {},
                expected_seed_lineage_id="seed-lineage-unit",
            )
            with self.assertRaises(Phase2SourceCheckpointError) as raised:
                provider.preflight()
            self.assertEqual(
                raised.exception.reason_code,
                "incident_source_checkpoint_registry_binding_mismatch",
            )


if __name__ == "__main__":
    unittest.main()

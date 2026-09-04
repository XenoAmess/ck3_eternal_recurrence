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
    SOURCE_CHECKPOINT_REGISTRY_KIND,
    Phase2SourceCheckpointError,
    Phase2SourceCheckpointProvider,
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
        path = (root / f"{index}-{plan.span_id}.ck3").resolve()
        path.write_bytes(f"real-checkpoint-{index}".encode("ascii"))
        sha = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        owner = 9100 + index
        player = 9001
        entries.append(
            {
                "span_id": plan.span_id,
                "handler": handler,
                "source_event_definition_key": plan.source_event,
                "owner_character_id": owner,
                "player_character_id": player,
                "date_raw": 700 + index,
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
                    "date_raw": 700 + index,
                    "checkpoint_sha256": sha,
                    "save_lineage_id": seed_lineage_id,
                },
            }
        )
    return {
        "schema_version": 1,
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


if __name__ == "__main__":
    unittest.main()

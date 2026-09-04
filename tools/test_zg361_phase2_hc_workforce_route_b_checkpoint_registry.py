#!/usr/bin/env python3

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import zg361_phase2_hc_workforce_route_b_checkpoint_registry as registry
from zg361_phase2_hc_workforce_route_b_checkpoint import (
    WORKFORCE_REQUIRED_FACTS,
)


OWNER = 32904
SUBJECT = 29037
CYCLE = 16
CASE = 16056
DATE = 53146920
EVENT = 360123
SOURCE_COMMIT = "c" * 40
PRODUCT_HASH = "a" * 64
FIXTURE_HASH = "b" * 64
SEED_LINEAGE = "zg361-phase2-seed-route-b-live"


def projection() -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "zg361_current_cumulative_product_projection",
        "source_git_commit": SOURCE_COMMIT,
        "projection_name": "current-cumulative-r20",
        "projection_mode": "allowlist",
        "product_tree_sha256": PRODUCT_HASH,
        "product_enabled_mod": "mod/zg361_acceptance.mod",
        "transition_fixture_tree_sha256": FIXTURE_HASH,
        "transition_fixture_enabled_mod": (
            "mod/zga_phase2_workforce_action_fixture.mod"
        ),
        "fixture_acceptance_only": True,
    }


def make_registry(checkpoint_path: Path) -> dict[str, object]:
    payload = checkpoint_path.read_bytes()
    sha256 = hashlib.sha256(payload).hexdigest()
    capture = {
        "schema_version": 1,
        "kind": "zg361_hc_workforce_route_b_pre_action_checkpoint",
        "result": "GREEN",
        "readiness": "static-ready-live-pending",
        "route": "B",
        "option_number": 2,
        "native_option_index": 1,
        "owner_character_id": OWNER,
        "subject_character_id": SUBJECT,
        "projection_binding": projection(),
        "subject_to_owner_transition": {
            "result": "GREEN",
            "owner_character_id": OWNER,
            "subject_character_id": SUBJECT,
            "expected_player_before": SUBJECT,
            "expected_player_after": OWNER,
            "ack_used_as_identity_postcondition": False,
            "native_played_character_postcondition": {
                "played_character_id": OWNER,
                "date_raw": DATE,
            },
        },
        "event_binding": {
            "snapshot_id": "route-b-pre",
            "revision": 10,
            "native_revision": 110,
            "date_raw": DATE,
            "player_character_id": OWNER,
            "event_instance_id": EVENT,
        },
        "event_context": {
            "event_definition_key": "zg361we.360",
            "current_event_instance_id": EVENT,
        },
        "native_save_receipt": {
            "accepted": True,
            "checkpoint": {
                "status": "saved",
                "size": len(payload),
                "sha256": sha256,
                "date_raw": DATE,
                "episode_character_id": OWNER,
            },
        },
        "checkpoint": {
            "path": str(checkpoint_path.resolve()),
            "bytes": len(payload),
            "sha256": sha256,
            "date_raw": DATE,
            "owner_character_id": OWNER,
            "subject_character_id": SUBJECT,
            "event_instance_id": EVENT,
            "product_tree_sha256": PRODUCT_HASH,
            "transition_fixture_tree_sha256": FIXTURE_HASH,
        },
        "gameplay_action_executed": False,
        "business_postcondition_claimed": False,
    }
    case_identity = {
        "owner_character_id": OWNER,
        "subject_character_id": SUBJECT,
        "cycle_serial": CYCLE,
        "case_serial": CASE,
        "source": "workforce_provider_post_action",
        "checkpoint_sha256": sha256,
    }
    postconditions = {
        "schema_version": 1,
        "kind": "zg361_hc_workforce_route_b_postconditions",
        "result": "GREEN",
        "checkpoint_sha256": sha256,
        "action_ack_is_business_postcondition": False,
        "workforce_required_facts": {
            name: True for name in WORKFORCE_REQUIRED_FACTS
        },
        "owner_action": {
            "result": "ACKED",
            "business_receipt_claimed": False,
            "binding": {
                "route": "B",
                "option_number": 2,
                "owner_character_id": OWNER,
                "subject_character_id": SUBJECT,
                "date_raw": DATE,
            },
        },
        "workforce_provider": {
            "result": "GREEN",
            "postcondition": {
                "owner_character_id": OWNER,
                "subject_character_id": SUBJECT,
                "cycle_serial": CYCLE,
                "case_serial": CASE,
            },
        },
        "career_hc_provider": {
            "status": "not_available",
            "reason": "career_hc_capability_not_advertised",
            "provider_observed": False,
            "response": None,
        },
        "case_identity": case_identity,
    }
    return {
        "schema_version": 1,
        "registry_kind": registry.ROUTE_B_CHECKPOINT_REGISTRY_KIND,
        "result": "GREEN",
        "evidence_class": "real_ck3",
        "fixture_used": True,
        "console_used": False,
        "action_ack_is_business_postcondition": False,
        "seed_lineage_id": SEED_LINEAGE,
        "checkpoint_capture": capture,
        "sealed_postconditions": postconditions,
    }


class RouteBCheckpointRegistryTests(unittest.TestCase):
    def provider(
        self, value: dict[str, object] | None
    ) -> registry.RouteBCheckpointRegistryProvider:
        return registry.RouteBCheckpointRegistryProvider(
            value,
            expected_seed_lineage_id=SEED_LINEAGE,
            expected_source_git_commit=SOURCE_COMMIT,
        )

    def test_accepts_exact_real_checkpoint_and_provider_seal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "pre-route-b.ck3"
            checkpoint.write_bytes(b"real-route-b-checkpoint")
            value = make_registry(checkpoint)
            preflight = self.provider(value).preflight(
                current_projection_binding=projection()
            )
        self.assertEqual("GREEN", preflight["result"])
        sha = hashlib.sha256(b"real-route-b-checkpoint").hexdigest()
        self.assertEqual(sha, preflight["checkpoint_sha256"])
        self.assertFalse(preflight["action_ack_is_business_postcondition"])
        self.assertEqual(CASE, preflight["case_identity"]["case_serial"])
        self.assertEqual(64, len(sha))

    def test_missing_registry_is_typed_red(self) -> None:
        with self.assertRaises(
            registry.RouteBCheckpointRegistryError
        ) as raised:
            self.provider(None).preflight()
        self.assertEqual(
            "route_b_checkpoint_registry_missing", raised.exception.reason_code
        )

    def test_tampered_checkpoint_bytes_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "pre-route-b.ck3"
            checkpoint.write_bytes(b"real-route-b-checkpoint")
            value = make_registry(checkpoint)
            checkpoint.write_bytes(b"tampered-route-b-checkpoint")
            with self.assertRaises(
                registry.RouteBCheckpointRegistryError
            ) as raised:
                self.provider(value).preflight()
        self.assertEqual(
            "route_b_checkpoint_capture_invalid", raised.exception.reason_code
        )

    def test_option_ack_cannot_be_promoted_to_business_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "pre-route-b.ck3"
            checkpoint.write_bytes(b"real-route-b-checkpoint")
            value = make_registry(checkpoint)
            changed = copy.deepcopy(value)
            changed["sealed_postconditions"]["owner_action"][
                "business_receipt_claimed"
            ] = True
            with self.assertRaises(
                registry.RouteBCheckpointRegistryError
            ) as raised:
                self.provider(changed).preflight()
        self.assertEqual(
            "route_b_checkpoint_postconditions_invalid",
            raised.exception.reason_code,
        )

    def test_current_projection_must_match_registered_product_and_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "pre-route-b.ck3"
            checkpoint.write_bytes(b"real-route-b-checkpoint")
            value = make_registry(checkpoint)
            current = projection()
            current["product_tree_sha256"] = "d" * 64
            with self.assertRaises(
                registry.RouteBCheckpointRegistryError
            ) as raised:
                self.provider(value).preflight(
                    current_projection_binding=current
                )
        self.assertEqual(
            "route_b_checkpoint_registry_lineage_mismatch",
            raised.exception.reason_code,
        )

    def test_writer_publishes_only_a_strict_provider_sealed_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkpoint = root / "pre-route-b.ck3"
            checkpoint.write_bytes(b"real-route-b-checkpoint")
            expected = make_registry(checkpoint)
            output = root / "registry.json"

            written = registry.write_route_b_checkpoint_registry(
                output,
                seed_lineage_id=SEED_LINEAGE,
                source_git_commit=SOURCE_COMMIT,
                checkpoint_capture=expected["checkpoint_capture"],
                sealed_postconditions=expected["sealed_postconditions"],
            )

            self.assertEqual(expected, written)
            self.assertEqual(
                expected,
                json.loads(output.read_text(encoding="utf-8")),
            )
            self.assertEqual(
                "GREEN",
                self.provider(written).preflight(
                    current_projection_binding=projection()
                )["result"],
            )

    def test_writer_rejects_ack_without_workforce_provider_seal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkpoint = root / "pre-route-b.ck3"
            checkpoint.write_bytes(b"real-route-b-checkpoint")
            expected = make_registry(checkpoint)
            postconditions = copy.deepcopy(expected["sealed_postconditions"])
            postconditions["workforce_provider"] = None
            output = root / "registry.json"

            with self.assertRaises(
                registry.RouteBCheckpointRegistryError
            ) as raised:
                registry.write_route_b_checkpoint_registry(
                    output,
                    seed_lineage_id=SEED_LINEAGE,
                    source_git_commit=SOURCE_COMMIT,
                    checkpoint_capture=expected["checkpoint_capture"],
                    sealed_postconditions=postconditions,
                )

            self.assertEqual(
                "route_b_checkpoint_postconditions_invalid",
                raised.exception.reason_code,
            )
            self.assertFalse(output.exists())

    def test_writer_refuses_to_overwrite_a_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkpoint = root / "pre-route-b.ck3"
            checkpoint.write_bytes(b"real-route-b-checkpoint")
            expected = make_registry(checkpoint)
            output = root / "registry.json"
            output.write_text("preserve", encoding="utf-8")

            with self.assertRaises(
                registry.RouteBCheckpointRegistryError
            ) as raised:
                registry.write_route_b_checkpoint_registry(
                    output,
                    seed_lineage_id=SEED_LINEAGE,
                    source_git_commit=SOURCE_COMMIT,
                    checkpoint_capture=expected["checkpoint_capture"],
                    sealed_postconditions=expected["sealed_postconditions"],
                )

            self.assertEqual(
                "route_b_checkpoint_registry_already_exists",
                raised.exception.reason_code,
            )
            self.assertEqual("preserve", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

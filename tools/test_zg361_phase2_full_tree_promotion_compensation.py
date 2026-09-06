#!/usr/bin/env python3
"""Focused tests for the full-tree promotion checkpoint/action seam."""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_zhongguo_acceptance as capture  # noqa: E402
from test_zhongguo_phase2_source_checkpoint_provider import (  # noqa: E402
    _registry,
)


class _RestoreService:
    def __init__(self, *, pid: int = 4321) -> None:
        self.pid = pid
        self.restore_calls: list[dict[str, object]] = []

    @staticmethod
    def phase2_span_source_checkpoint_restore_available_v1() -> bool:
        return True

    def restore_phase2_span_source_checkpoint_v1(
        self, **kwargs: object
    ) -> dict[str, object]:
        self.restore_calls.append(dict(kwargs))
        return {
            "result": "GREEN",
            "provider_observed": True,
            "checkpoint_sha256": kwargs["expected_checkpoint_sha256"],
            "save_lineage_id": kwargs["expected_save_lineage_id"],
            "player_character_id": kwargs["expected_player_character_id"],
            "owner_character_id": kwargs["expected_owner_character_id"],
            "date_raw": kwargs["expected_date_raw"],
            "event_definition_key": kwargs["expected_event_definition_key"],
            "fixture_used": False,
            "console_used": False,
            "generic_character_rebind_used": False,
        }

    def snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": "restored-promotion-source",
            "revision": 11,
            "native_revision": 21,
            "date_raw": 701,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 9001},
            "active_event": {"instance_id": 14701, "option_count": 2},
            "diagnostics": {
                "bridge_pid": self.pid,
                "connection_generation": 3,
            },
        }

    @staticmethod
    def query_current_event_window_context_v1(
        event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        assert event_instance_id == 14701
        assert expected_revision == 11
        return {
            "status": "available",
            "current_event_window_context": {
                "readiness": {"event_definition_identity_ready": True},
                "event_definition_key": "zg361pp.147",
            },
        }


def _green_action_cell() -> dict[str, object]:
    return {
        "schema_version": 1,
        "cell_id": "zg361.phase2.promotion-compensation.action.v1",
        "result": "GREEN",
        "mcp_only": True,
        "action_ack_is_business_postcondition": False,
        "business_postcondition": {
            "result": "GREEN",
            "provider_observed": True,
            "postcondition_green": True,
        },
    }


class FullTreePromotionCompensationTests(unittest.TestCase):
    def test_exact_registered_147_restore_precedes_existing_action_cell(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            registry_root = root / "registry"
            registry_root.mkdir()
            registry = _registry(registry_root)
            service = _RestoreService()
            call_order: list[str] = []

            original_restore = service.restore_phase2_span_source_checkpoint_v1

            def restore(**kwargs: object) -> dict[str, object]:
                call_order.append("restore")
                return original_restore(**kwargs)

            setattr(
                service,
                "restore_phase2_span_source_checkpoint_v1",
                restore,
            )

            def action_cell(*_args: object, **_kwargs: object) -> dict[str, object]:
                call_order.append("action")
                self.assertEqual(len(service.restore_calls), 1)
                return _green_action_cell()

            with (
                mock.patch.object(
                    capture,
                    "_phase2_seed_lineage_id",
                    return_value="seed-lineage-unit",
                ),
                mock.patch.object(
                    capture,
                    "run_promotion_compensation_gameplay_action_cell",
                    side_effect=action_cell,
                ) as action,
            ):
                evidence = (
                    capture.run_phase2_full_tree_promotion_compensation_cell(
                        service,  # type: ignore[arg-type]
                        artifacts,
                        tracked_ck3_pid=4321,
                        seed_contract={},
                        source_checkpoint_registry=registry,
                    )
                )

            self.assertEqual(call_order, ["restore", "action"])
            action.assert_called_once()
            self.assertEqual(evidence["result"], "GREEN")
            self.assertTrue(evidence["source_checkpoint_registry_used"])
            self.assertTrue(all(evidence["checks"].values()))
            self.assertEqual(
                evidence["restored_source_event_identity"][
                    "event_definition_key"
                ],
                "zg361pp.147",
            )
            restore_call = service.restore_calls[0]
            self.assertEqual(
                restore_call["expected_event_definition_key"], "zg361pp.147"
            )
            self.assertEqual(restore_call["expected_owner_character_id"], 9101)
            self.assertEqual(restore_call["expected_player_character_id"], 9001)
            self.assertEqual(restore_call["expected_date_raw"], 701)
            self.assertFalse(restore_call["allow_generic_character_rebind"])
            self.assertFalse(restore_call["allow_fixture"])
            self.assertFalse(restore_call["allow_console"])
            artifact = json.loads(
                (
                    artifacts
                    / "09_phase2_promotion_compensation_full_tree_cell.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(artifact, evidence)

    def test_missing_registry_is_typed_red_and_never_calls_action(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary) / "artifacts"
            artifacts.mkdir()
            service = _RestoreService()
            with mock.patch.object(
                capture, "run_promotion_compensation_gameplay_action_cell"
            ) as action:
                with self.assertRaises(capture.acceptance.RunnerError) as raised:
                    capture.run_phase2_full_tree_promotion_compensation_cell(
                        service,  # type: ignore[arg-type]
                        artifacts,
                        tracked_ck3_pid=4321,
                        seed_contract={"source": {"sha256": "a" * 64}},
                        source_checkpoint_registry=None,
                    )
            self.assertIn("source_checkpoint_registry_missing", str(raised.exception))
            action.assert_not_called()
            artifact = json.loads(
                (
                    artifacts
                    / "09_phase2_promotion_compensation_full_tree_cell.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(artifact["result"], "RED")
            self.assertFalse(artifact["source_checkpoint_registry_used"])

    def test_run_cell_forwards_registry_to_full_tree_entrypoint(self) -> None:
        signature = inspect.signature(capture.run_phase2_live_scenario)
        self.assertIn("source_checkpoint_registry", signature.parameters)

        tree = ast.parse(inspect.getsource(capture.run_cell))
        full_tree_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "run_phase2_live_scenario"
        ]
        self.assertEqual(len(full_tree_calls), 1)
        forwarded = {
            keyword.arg: keyword.value
            for keyword in full_tree_calls[0].keywords
            if keyword.arg is not None
        }
        value = forwarded["source_checkpoint_registry"]
        self.assertIsInstance(value, ast.Name)
        self.assertEqual(value.id, "phase2_source_checkpoint_registry")


if __name__ == "__main__":
    unittest.main()

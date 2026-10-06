"""One registered MCP serialization regression with synthetic Service output.

This does not load a native wire, import an older test, or query a game.
The baseline invokes the installed SDK's real ordinary-dict conversion.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import sys
from typing import Literal
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.mcp_server import PublicCUnitId, create_server
from xar_autoplayer.bridge.service import GameplayBridgeService


def _synthetic_complete_service_result() -> dict[str, object]:
    """Own complete result-shaped observations; no native-producer claim."""
    ordered_occurrences = [
        {
            "native_index": index,
            "raw_full_id_u32": 0xAB000001 if index % 3 else 0,
            "selected_identity": "native:68719481088",
            "used_fallback": index % 7 == 0,
            "cached_raw_u8": index % 256,
            "native_predicate": False,
            "nullable_operand": None,
            "owner_full_id_u32": 0xFFFFFFFF if index % 5 else 0x80000000,
            "observation_note": "旅人 current source occurrence",
        }
        for index in range(4096)
    ]
    raw_roster = {
        "status": "available",
        "references_ready": True,
        "count_raw_i32": len(ordered_occurrences),
        "data_identity": "native:68719485184",
        "occurrences": ordered_occurrences,
    }
    rows = []
    for army_id, native_id, regiment_count, soldiers, maximum, power in [
        (218104048, 67109093, 39, 1833, 2367, 6224500000),
        (134218098, 167772499, 8, 348, 536, 1635200000),
    ]:
        rows.append({
            "army_id": army_id,
            "native_carmy_id": native_id,
            "status": "available",
            "unavailable_reason": "",
            "regiment_count": regiment_count,
            "current_soldiers": soldiers,
            "maximum_soldiers": maximum,
            "ai_base_power_raw": power,
            "ai_base_power_scale": 100000,
            "current_supply_raw": 10000000,
            "current_supply_scale": 100000,
            "current_attrition_fraction_raw": 0,
            "current_attrition_fraction_scale": 100000,
            "scope_reason": "player" if army_id == 218104048 else "active_war_ally",
            "synthetic_observed_roster": raw_roster,
            "synthetic_observed_scalar_inputs": {
                "selected_army_full_id": 0,
                "requested_highbit_army_full_id": 0xAB000001,
                "selected_character_full_id": 0xFFFFFFFF,
                "phase_raw_i32": -1,
                "mode_raw_u8": 255,
                "known_false": False,
                "unread_operand": None,
                "empty_current_list": [],
            },
        })
    return {
        "accepted": True,
        "schema_version": 1,
        "status": "available",
        "scope_status": "available",
        "scope": "player-and-active-war-participants",
        "query_sequence": 2,
        "revision": 4,
        "native_revision": 3,
        "source": {
            "snapshot_id": 7001,
            "revision": 4,
            "native_revision": 3,
            "date_raw": 123456,
            "paused": True,
            "backend_id": "synthetic_transport_fixture",
            "game_version": "1.20.0.3",
            "executable_sha256": (
                "94B55397ABB687A3DCD436805A5D885E6BE90FA6C"
                "693FEB44A9E3BBEEADE02A6"
            ),
        },
        "army_ids": [218104048, 134218098],
        "scope_army_ids": [218104048, 134218098],
        "ordered_refill_entry_mode": "observed_prepared",
        "ordered_besieging_entry_mode": "fixed_chunk0_prepare",
        "army_strengths": rows,
        "same_input_conditional_projection": [
            {
                "army_id": row["army_id"],
                "projection": {
                    "status": "available",
                    "hypothetical": True,
                    "ordered_duplicate_source_indices": [7, 7, 0, 4095],
                    "derived_raw_i64": 0,
                    "actual_effect_observed": False,
                    "future_value": None,
                },
            }
            for row in rows
        ],
        "fixture_provenance": {
            "kind": "synthetic_complete_service_result",
            "native_producer_executions": 0,
            "game_calls_executed": 0,
            "historical_root_scalar_values_reused_as_fixture_values": True,
        },
    }


class ArmyStrengthsMcpResultSerializationPerformanceTests(
    unittest.IsolatedAsyncioTestCase
):
    async def test_first_registered_army_result_preserves_all_observations_without_duplicate_json(
        self,
    ) -> None:
        payload = _synthetic_complete_service_result()
        expected = copy.deepcopy(payload)
        arguments = {
            "army_ids": [218104048, 134218098],
            "expected_revision": 4,
            "ordered_refill_entry_mode": "observed_prepared",
            "ordered_besieging_entry_mode": "fixed_chunk0_prepare",
        }
        legacy_calls = []

        with patch.object(
            GameplayBridgeService,
            "query_army_strengths",
            autospec=True,
            return_value=payload,
        ) as service_query:
            server = create_server(object())

            @server.tool()
            def fixture_legacy_army_result(
                army_ids: list[PublicCUnitId],
                expected_revision: int | None = None,
                ordered_refill_entry_mode: Literal[
                    "observed_prepared", "fixed_chunk0_prepare"
                ] = "observed_prepared",
                ordered_besieging_entry_mode: Literal[
                    "observed_prepared", "fixed_chunk0_prepare"
                ] = "observed_prepared",
            ) -> dict[str, object]:
                legacy_calls.append({
                    "army_ids": army_ids,
                    "expected_revision": expected_revision,
                    "ordered_refill_entry_mode": ordered_refill_entry_mode,
                    "ordered_besieging_entry_mode": ordered_besieging_entry_mode,
                })
                return payload

            # Both routes use the actual installed SDK converter and serializer.
            legacy = await server.call_tool("fixture_legacy_army_result", arguments)
            compact = await server.call_tool("ck3_query_army_strengths", arguments)
            advertised = {tool.name: tool for tool in await server.list_tools()}

        service_query.assert_called_once()
        self.assertEqual(service_query.call_args.args[1], arguments["army_ids"])
        self.assertEqual(service_query.call_args.kwargs, {
            key: value for key, value in arguments.items() if key != "army_ids"
        })
        self.assertEqual(legacy_calls, [arguments])
        self.assertEqual(
            advertised["ck3_query_army_strengths"].output_schema,
            advertised["fixture_legacy_army_result"].output_schema,
        )
        # Argument-model titles include each tool's name; compare the API fields.
        self.assertEqual(
            {key: value for key, value in advertised[
                "ck3_query_army_strengths"].input_schema.items() if key != "title"},
            {key: value for key, value in advertised[
                "fixture_legacy_army_result"].input_schema.items() if key != "title"},
        )
        self.assertFalse(legacy.is_error)
        self.assertFalse(compact.is_error)
        self.assertEqual(payload, expected)
        self.assertEqual(legacy.structured_content, expected)
        self.assertEqual(compact.structured_content, expected)
        self.assertEqual(len(legacy.content), 1)
        self.assertEqual(len(compact.content), 1)
        self.assertEqual(json.loads(legacy.content[0].text), expected)

        summary = json.loads(compact.content[0].text)
        self.assertEqual(set(summary), {
            "accepted", "status", "query_sequence", "source",
            "army_ids", "armies", "result_location",
        })
        self.assertEqual(summary["result_location"], "structuredContent")
        self.assertEqual(summary["source"], {"revision": 4, "native_revision": 3})
        self.assertEqual(summary["army_ids"], arguments["army_ids"])
        self.assertEqual([row["army_id"] for row in summary["armies"]],
                         arguments["army_ids"])
        self.assertLess(len(compact.content[0].text.encode("utf-8")), 4096)
        self.assertNotIn("occurrences", compact.content[0].text)
        self.assertNotIn("synthetic_observed_roster", compact.content[0].text)
        self.assertNotIn("same_input_conditional_projection", compact.content[0].text)

        # Exactly one actual wire serialization per comparison result.
        legacy_wire = legacy.model_dump_json(
            by_alias=True, exclude_none=True
        ).encode("utf-8")
        compact_wire = compact.model_dump_json(
            by_alias=True, exclude_none=True
        ).encode("utf-8")
        self.assertGreater(len(legacy_wire), 256 * 1024)
        self.assertLessEqual(len(compact_wire), len(legacy_wire) * 0.60)
        decoded = json.loads(compact_wire)
        self.assertEqual(decoded["structuredContent"], expected)
        kept = decoded["structuredContent"]["army_strengths"][0]
        occurrences = kept["synthetic_observed_roster"]["occurrences"]
        self.assertEqual(occurrences, expected["army_strengths"][0][
            "synthetic_observed_roster"]["occurrences"])
        self.assertEqual([row["native_index"] for row in occurrences], list(range(4096)))
        self.assertEqual(occurrences[1]["raw_full_id_u32"], 0xAB000001)
        self.assertEqual(occurrences[2]["raw_full_id_u32"], 0xAB000001)
        self.assertEqual(occurrences[0]["raw_full_id_u32"], 0)
        self.assertIs(occurrences[0]["native_predicate"], False)
        self.assertIsNone(occurrences[0]["nullable_operand"])
        self.assertEqual(occurrences[1]["owner_full_id_u32"], 0xFFFFFFFF)
        self.assertEqual(kept["synthetic_observed_scalar_inputs"]["mode_raw_u8"], 255)

        output = os.environ.get("XAR_ARMY_RESULT_PERFORMANCE_CASE_OUTPUT")
        if output:
            destination = Path(output)
            destination.parent.mkdir(parents=True, exist_ok=True)
            metrics = {
                "fixture_provenance": payload["fixture_provenance"],
                "registered_service_calls": service_query.call_count,
                "legacy_sdk_calls": len(legacy_calls),
                "wire_serializations": {"legacy": 1, "compact": 1},
                "legacy_wire_bytes": len(legacy_wire),
                "compact_wire_bytes": len(compact_wire),
                "compact_to_legacy_byte_ratio": len(compact_wire) / len(legacy_wire),
                "text_summary_bytes": len(compact.content[0].text.encode("utf-8")),
                "army_rows": len(payload["army_strengths"]),
                "original_ordered_occurrences_per_row": len(occurrences),
                "all_observation_fields_retained": True,
                "new_native_producer_or_game_execution": False,
            }
            with destination.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(metrics, stream, ensure_ascii=False, indent=2)
                stream.write("\n")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.entity_directory_contract import (
    ENTITY_DIRECTORY_V1_SCHEMA,
    build_entity_directory_v1,
)


def _result(*, available: bool = True) -> dict[str, object]:
    status = "available" if available else "unavailable"
    context: dict[str, object] = {
        "status": status,
        "snapshot_revision": 17,
        "date_raw": 53_182_008,
        "player_character_id": 30 if available else None,
        "primary_title": (
            {"title_id": 90, "tier_raw": 4, "tier_key": "kingdom"}
            if available
            else None
        ),
        "capital_province_id": 70 if available else None,
        "immediate_liege_character_id": None,
        "top_liege_character_id": 30 if available else None,
        "direct_landed_vassal_character_ids": (
            [10, 40] if available else []
        ),
        "adjacent_external_province_holder_character_ids": (
            [20, 50] if available else []
        ),
        "unavailable_reason": None if available else "state_changed",
        "provenance": {
            "game_version": "1.19.0.6",
            "executable_sha256": "A" * 64,
        },
    }
    return {
        "status": status,
        "query_sequence": 9,
        "campaign_root_context": context,
    }


class EntityDirectoryV1Tests(unittest.TestCase):
    def test_any_search_sorts_identity_and_preserves_component_boundary(self) -> None:
        result = build_entity_directory_v1(_result())

        self.assertEqual(result["schema"], ENTITY_DIRECTORY_V1_SCHEMA)
        self.assertEqual(
            [row["character_id"] for row in result["entities"]],
            [10, 20, 30, 40, 50],
        )
        by_id = {row["character_id"]: row for row in result["entities"]}
        self.assertEqual(
            by_id[10]["immediate_liege_character_id"]["value"], 30
        )
        self.assertEqual(by_id[10]["top_liege_character_id"]["value"], 30)
        self.assertEqual(
            by_id[20]["top_liege_character_id"]["status"], "unavailable"
        )
        self.assertEqual(by_id[30]["primary_title"]["value"]["title_id"], 90)
        self.assertTrue(result["readiness"]["ready"])
        self.assertFalse(
            result["readiness"]["realm_identity_components_complete"]
        )

    def test_relation_filter_and_keyset_pagination_are_deterministic(self) -> None:
        first = build_entity_directory_v1(_result(), limit=2)
        second = build_entity_directory_v1(
            _result(), after_character_id=first["next_after_character_id"], limit=2
        )
        adjacent = build_entity_directory_v1(
            _result(), relation_filter="adjacent_external_province_holder"
        )

        self.assertEqual(
            [row["character_id"] for row in first["entities"]], [10, 20]
        )
        self.assertEqual(first["next_after_character_id"], 20)
        self.assertEqual(
            [row["character_id"] for row in second["entities"]], [30, 40]
        )
        self.assertEqual(second["next_after_character_id"], 40)
        self.assertEqual(second["total_matching_count"], 5)
        self.assertEqual(
            [row["character_id"] for row in adjacent["entities"]], [20, 50]
        )

    def test_unavailable_root_remains_typed_and_empty(self) -> None:
        result = build_entity_directory_v1(_result(available=False))

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["entities"], [])
        self.assertEqual(result["unavailable_reason"], "state_changed")
        self.assertFalse(result["readiness"]["ready"])

    def test_landless_independent_self_uses_not_applicable_components(self) -> None:
        source = _result()
        context = source["campaign_root_context"]
        assert isinstance(context, dict)
        context["primary_title"] = None
        context["capital_province_id"] = None
        context["direct_landed_vassal_character_ids"] = []
        context["adjacent_external_province_holder_character_ids"] = []

        result = build_entity_directory_v1(source, relation_filter="self")
        self_entity = result["entities"][0]
        self.assertEqual(self_entity["primary_title"]["status"], "not_applicable")
        self.assertEqual(
            self_entity["immediate_liege_character_id"]["status"],
            "not_applicable",
        )
        self.assertTrue(
            result["readiness"]["primary_title_components_complete"]
        )

    def test_rejects_invalid_query_and_overlapping_relationships(self) -> None:
        for kwargs in (
            {"relation_filter": "neighbor"},
            {"after_character_id": 0},
            {"limit": 0},
            {"limit": 101},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                build_entity_directory_v1(_result(), **kwargs)

        source = _result()
        context = source["campaign_root_context"]
        assert isinstance(context, dict)
        context["adjacent_external_province_holder_character_ids"] = [10, 50]
        with self.assertRaisesRegex(ValueError, "overlap"):
            build_entity_directory_v1(source)


if __name__ == "__main__":
    unittest.main()

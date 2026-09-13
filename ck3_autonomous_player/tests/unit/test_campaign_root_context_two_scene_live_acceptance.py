from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge/research/run_campaign_root_context_two_scene_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location("g2_m1_two_scene_live", SCRIPT)
if SPEC is None or SPEC.loader is None:  # pragma: no cover
    raise ImportError(f"cannot load two-scene runner: {SCRIPT}")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _position(key: str, *, occupied: bool) -> dict[str, object]:
    return {
        "position_key": key,
        "incumbent_character_id": 700 if occupied else None,
        "task_key": "councillor_task_manage_domain" if occupied else None,
        "task_type": "general" if occupied else None,
        "target": None,
        "frozen": False if occupied else None,
        "progress": (
            {"kind": "infinite", "current": None, "maximum": None}
            if occupied
            else None
        ),
    }


def _scene(*, character_id: int = 100) -> tuple[dict[str, object], dict[str, object]]:
    positions = [
        _position(key, occupied=index == 0)
        for index, key in enumerate(sorted(MODULE.CORE_COUNCIL_POSITIONS))
    ]
    council = {
        "status": "available",
        "coverage_key": MODULE.COUNCIL_COVERAGE_KEY,
        "owner_character_id": character_id,
        "positions": positions,
        "auxiliary_vacancies_complete": False,
        "unavailable_reason": None,
    }
    readiness = {
        "player_identity_ready": True,
        "council_ready": True,
        "same_frame_ready": True,
        "ready": True,
    }
    root = {
        "status": "available",
        "snapshot_revision": 17,
        "date_raw": 53_178_264,
        "player_character_id": character_id,
        "player_monthly_gold_income": {"raw": 50_000, "scale": 100_000},
        "player_health": {"raw": 300_000, "scale": 100_000},
        "player_domain_size": 3,
        "player_domain_limit": 5,
        "player_targeting_faction_count": 0,
        "primary_title": {"title_id": 200, "tier_raw": 4, "tier_key": "kingdom"},
        "held_title_partition": [
            {
                "title": {"title_id": 200, "tier_raw": 4, "tier_key": "kingdom"},
                "first_heir_character_id": 900,
                "primary": True,
            }
        ],
        "capital_province_id": 300,
        "immediate_liege_character_id": None,
        "top_liege_character_id": character_id,
        "independent": True,
        "direct_landed_vassal_character_ids": [101],
        "adjacent_external_province_holder_character_ids": [102],
        "related_character_contexts": [
            {"character_id": 101},
            {"character_id": 102},
        ],
        "council": council,
        "readiness": readiness,
    }
    sequence = {
        "ok": True,
        "first_query": {"campaign_root_context": root},
    }
    bundle = {
        "schema": "xar.ck3.turn-bundle/v1",
        "status": "partial",
        "realm_state": {
            "status": "available",
            "value": {
                "council": {
                    "status": "available",
                    "value": copy.deepcopy(council),
                    "unavailable_reason": None,
                }
            },
        },
        "readiness": {"realm_council_ready": True, "ready": False},
    }
    return sequence, bundle


class TwoSceneLiveAcceptanceTests(unittest.TestCase):
    def test_scene_requires_typed_root_relationships_council_and_bundle(self) -> None:
        sequence, bundle = _scene()
        proof = MODULE._scene_proof(
            sequence,
            bundle,
            expected_character_id=100,
            expected_primary_title_id=200,
            expected_capital_province_id=300,
            expected_immediate_liege_id=None,
            expected_top_liege_id=100,
            expected_independent=True,
            require_relationship_vectors=True,
        )
        self.assertTrue(proof["ok"], proof)
        self.assertEqual(proof["occupied_council_task_count"], 1)

    def test_scene_retains_missing_council_as_red(self) -> None:
        sequence, bundle = _scene()
        root = sequence["first_query"]["campaign_root_context"]
        root["council"]["status"] = "unavailable"
        root["readiness"]["council_ready"] = False
        root["readiness"]["ready"] = False
        proof = MODULE._scene_proof(
            sequence,
            bundle,
            expected_character_id=100,
            expected_primary_title_id=200,
            expected_capital_province_id=300,
            expected_immediate_liege_id=None,
            expected_top_liege_id=100,
            expected_independent=True,
            require_relationship_vectors=True,
        )
        self.assertFalse(proof["ok"])
        self.assertFalse(proof["checks"]["council_observed"])

    def test_switch_requires_revision_identity_date_and_episode_postcondition(self) -> None:
        before = {
            "revision": 8,
            "date_raw": 53_178_264,
            "paused": True,
            "map_ready": True,
            "episode_run_id": "fixture-run",
        }
        after = {
            "revision": 9,
            "date_raw": 53_178_264,
            "paused": True,
            "map_ready": True,
            "episode_run_id": "fixture-run",
            "played_character": {"character_id": 101, "alive": True},
        }
        result = {
            "step": "set-played-character-v1-101",
            "accepted": True,
            "status": "switched",
            "from_character_id": 100,
            "to_character_id": 101,
            "before_revision": 8,
            "after_revision": 9,
            "postcondition_verified": True,
            "episode_run_id": "fixture-run",
        }
        proof = MODULE._switch_proof(
            before,
            result,
            after,
            from_character_id=100,
            to_character_id=101,
        )
        self.assertTrue(proof["ok"], proof)
        drifted = copy.deepcopy(after)
        drifted["date_raw"] += 1
        self.assertFalse(
            MODULE._switch_proof(
                before,
                result,
                drifted,
                from_character_id=100,
                to_character_id=101,
            )["ok"]
        )


if __name__ == "__main__":
    unittest.main()

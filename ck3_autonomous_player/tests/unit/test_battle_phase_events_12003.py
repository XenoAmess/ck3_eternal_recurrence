"""Independent CK3 1.20.0.3 selected-script transition fixtures, never live data."""

from __future__ import annotations

import copy
import hashlib
from importlib import resources
import os
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.simulation.battle_phase_events_12003 import (
    PhaseEventScriptOutcome12003,
    execute_selected_phase_event_12003,
    load_stock_phase_events_12003,
)
from xar_autoplayer.simulation.phase_event_manifest import (
    STOCK_PHASE_EVENT_MANIFEST_SHA256,
    load_stock_phase_event_manifest,
)


EXE_SHA256_12003 = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"
ROOT_ID = 29829
ENEMY_ID = 900001
OTHER_OWN_ID = 900002
FIXED_SCALE = 100000


def _manifest():
    # External additive projections pass a path; the installed repository uses its resource.
    fixture_path = os.environ.get("XAR_PHASE_EVENTS_12003_MANIFEST_FIXTURE")
    return load_stock_phase_events_12003(path=fixture_path)


def _blademaster_container() -> dict[str, object]:
    return {
        "education_martial": [False] * 5,
        "education_martial_prowess": [False] * 4,
        "intellect_good": [False] * 3,
        "lifestyle_blademaster": False,
        "lifestyle_blademaster_xp_raw": 0,
        "shrewd": False,
        "physique_good": False,
        "culture_blademaster_traits_more_common": False,
    }


def _context(*, wounded_rank_raw: int) -> dict[str, object]:
    """Synthetic source-derived .3 state; IDs and skill values are test inputs."""
    return {
        "root_character_id": ROOT_ID,
        "root_source_army_id": 9001,
        "root_source_regiment_id": 7001,
        "phase_roles": ["commander"],
        "combat_side_index": 0,
        "enemy_side_index": 1,
        "native_state_refs": {
            "root.exists": True,
            "root.alive": True,
            "root.skills.prowess_raw": 12 * FIXED_SCALE,
            "root.traits.wounded.rank_raw": wounded_rank_raw,
            "root.traits.fragile_bones.rank_raw": 0,
            "root.traits.fragile_bones.xp_raw": 0,
            "root.traits.one_legged": False,
            "root.traits.disfigured": False,
            "root.traits.one_eyed": False,
            "root.traits.maimed": False,
            "root.court_positions.garuda": False,
            "root.traits_and_culture_for_blademaster": _blademaster_container(),
            "combat_side.character_membership": [ROOT_ID, OTHER_OWN_ID],
            "enemy_side.character_membership": [ENEMY_ID],
            "combat_side.ordered_enemy_knights": [ENEMY_ID],
            "combat_side.commander": ROOT_ID,
        },
        "offline_state_refs": {},
        "candidate_rows": [{
            "character_id": ENEMY_ID,
            "candidate_refs": {
                "candidate.alive": True,
                "candidate.skills.prowess_raw": 20 * FIXED_SCALE,
                "derived.candidate_prowess_at_or_above_root_opponent_threshold_without_alive_filter": True,
            },
            "selected_enemy_knight_refs": {
                "selected_enemy_knight.alive": True,
                "selected_enemy_knight.skills.prowess_raw": 20 * FIXED_SCALE,
                "selected_enemy_knight.skills.learning_raw": 10 * FIXED_SCALE,
                "selected_enemy_knight.dynasty.perks.warfare_legacy_3": False,
                "selected_enemy_knight.traits_and_culture_for_blademaster": _blademaster_container(),
            },
        }],
    }


def _selected_enemy_outcomes(*, event_key: str, prowess_branch: int) -> tuple[PhaseEventScriptOutcome12003, ...]:
    return (
        PhaseEventScriptOutcome12003(
            purpose=f"{event_key}.effect_ast.steps[0]:enemy_knight",
            character_id=ENEMY_ID,
        ),
        PhaseEventScriptOutcome12003(
            purpose="knight_increase_prowess:source_order",
            branch_index=prowess_branch,
        ),
    )


class BattlePhaseEvents12003Tests(unittest.TestCase):
    def test_current_build_pin_is_independent_and_preserves_legacy_data(self) -> None:
        legacy_resource = resources.files("xar_autoplayer.simulation").joinpath(
            "data/ck3_1_19_0_6_stock_combat_phase_events.json"
        )
        legacy_before = hashlib.sha256(legacy_resource.read_bytes()).hexdigest()
        legacy = load_stock_phase_event_manifest()
        current = _manifest()
        self.assertEqual(legacy.game_version, "1.19.0.6")
        self.assertEqual(legacy.canonical_manifest_sha256, STOCK_PHASE_EVENT_MANIFEST_SHA256)
        self.assertEqual(current.game_version, "1.20.0.3")
        self.assertEqual(current.executable_sha256, EXE_SHA256_12003)
        self.assertEqual(current.canonical_manifest_sha256, "38BB943E208F53D106B90A2F6B895189ECA6471ED7B9888AC5A8454E7CD60240")
        self.assertNotEqual(current.canonical_manifest_sha256, legacy.canonical_manifest_sha256)
        self.assertEqual(len(current.event_rows), 13)
        self.assertFalse(current.completeness.original_trace_ready)
        self.assertEqual(hashlib.sha256(legacy_resource.read_bytes()).hexdigest(), legacy_before)

    def test_selected_wound_and_prowess_write_back_without_mutating_input(self) -> None:
        context = _context(wounded_rank_raw=FIXED_SCALE)
        original = copy.deepcopy(context)
        result = execute_selected_phase_event_12003(
            context,
            event_key="commander_wounded",
            script_outcomes=_selected_enemy_outcomes(event_key="commander_wounded", prowess_branch=1),
            manifest=_manifest(),
        )
        state = result["after_state"]
        self.assertTrue(state["root"]["alive"])
        self.assertEqual(state["root"]["wounded_rank_raw"], 2 * FIXED_SCALE)
        self.assertEqual(state["enemy_candidates"][0]["character_id"], ENEMY_ID)
        self.assertEqual(state["enemy_candidates"][0]["prowess_raw"], 21 * FIXED_SCALE)
        self.assertIn(ROOT_ID, state["recompute"]["character_stat_ids"])
        self.assertIn(ENEMY_ID, state["recompute"]["character_stat_ids"])
        self.assertEqual(state["sides"]["combat_membership"], [ROOT_ID, OTHER_OWN_ID])
        self.assertEqual(state["sides"]["combat_commander_character_id"], ROOT_ID)
        self.assertEqual(context, original)

    def test_rank_three_wound_death_has_no_killer_and_detaches_commander(self) -> None:
        for event_key in ("commander_wounded", "commander_maimed"):
            with self.subTest(event_key=event_key):
                context = _context(wounded_rank_raw=3 * FIXED_SCALE)
                original = copy.deepcopy(context)
                outcomes = _selected_enemy_outcomes(event_key=event_key, prowess_branch=0)
                if event_key == "commander_maimed":
                    outcomes += (PhaseEventScriptOutcome12003(purpose="maim_random:source_order", branch_index=0),)
                result = execute_selected_phase_event_12003(
                    context,
                    event_key=event_key,
                    script_outcomes=outcomes,
                    manifest=_manifest(),
                )
                state = result["after_state"]
                self.assertFalse(state["root"]["alive"])
                self.assertEqual(state["root"]["wounded_rank_raw"], 3 * FIXED_SCALE)
                self.assertEqual(state["selected_enemy_character_id"], ENEMY_ID)
                death = next(row for row in result["transition_log"] if row["transition"] == "kill_character")
                self.assertEqual(death["target_character_id"], ROOT_ID)
                self.assertEqual(death["reason"], "death_fight")
                self.assertIsNone(death["killer_character_id"])
                self.assertEqual(state["sides"]["combat_membership"], [OTHER_OWN_ID])
                self.assertIsNone(state["sides"]["combat_commander_character_id"])
                self.assertIn(ROOT_ID, state["recompute"]["participant_detach_ids"])
                self.assertIn(0, state["recompute"]["side_strength_indices"])
                self.assertEqual(state["enemy_candidates"][0]["prowess_raw"], 20 * FIXED_SCALE)
                if event_key == "commander_maimed":
                    self.assertTrue(state["root"]["traits"]["one_legged"])
                self.assertEqual(context, original)

    def test_no_selected_event_preserves_state_and_input(self) -> None:
        context = _context(wounded_rank_raw=FIXED_SCALE)
        original = copy.deepcopy(context)
        result = execute_selected_phase_event_12003(context, event_key=None, manifest=_manifest())
        self.assertEqual(result["before_state_sha256"], result["after_state"]["state_sha256"])
        self.assertEqual(result["transition_log"], [])
        self.assertEqual(result["after_state"]["recompute"]["character_stat_ids"], [])
        self.assertEqual(result["after_state"]["recompute"]["participant_detach_ids"], [])
        self.assertEqual(result["after_state"]["recompute"]["side_strength_indices"], [])
        self.assertEqual(context, original)


if __name__ == "__main__":
    unittest.main()

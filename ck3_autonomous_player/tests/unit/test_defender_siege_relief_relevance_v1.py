"""Native holder/objective proof required before defending a distant siege."""

from __future__ import annotations

from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.strategy import _defender_siege_is_relief_relevant


def test_relief_requires_objective_or_actual_player_realm_proof() -> None:
    snapshot = {"played_character": {"character_id": 40526}}
    war = {"war_objective_province_ids": [2629]}
    # P09 enemy 419430694 at 470 had both Native ownership fields unknown.
    enemy = {
        "current_province_id": 470,
        "siege_province_holder_character_id": None,
        "siege_province_in_player_subrealm": None,
    }
    assert not _defender_siege_is_relief_relevant(snapshot, war, enemy)
    assert _defender_siege_is_relief_relevant(
        snapshot, war, {**enemy, "current_province_id": 2629}
    )
    assert _defender_siege_is_relief_relevant(
        snapshot, war, {**enemy, "siege_province_in_player_subrealm": True}
    )
    assert _defender_siege_is_relief_relevant(
        snapshot, war, {**enemy, "siege_province_holder_character_id": 40526}
    )
    assert not _defender_siege_is_relief_relevant(
        snapshot,
        war,
        {**enemy, "siege_province_holder_character_id": 40526,
         "siege_province_in_player_subrealm": False},
    )

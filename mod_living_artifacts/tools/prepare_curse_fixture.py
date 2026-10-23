"""External initial inputs for the narrow player curse representative scene.

No settlement, equipment, charge, result or monthly callback is injected.
"""
from __future__ import annotations

from pathlib import Path
import sys
from typing import Final

TOOLS = Path(__file__).resolve().parent
for directory in (TOOLS.parents[1] / "tools", TOOLS):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from acceptance_contract import Pin, pin, require, utc_now, write_once
from ck3_live_run_id import current_machine_id
from living_artifacts_core import render_fixture_effects, render_fixture_localization
from prepare_fixture import FixtureEmission
from prepare_npc_fixture import EXPECTED_EXE_SHA, SOURCES as GAME_SOURCES, verify_source
from prepare_threshold_fixture import tree

INITIAL_GOLD: Final[int] = 20


def qualify_fixture_sources(game: Path) -> dict[str, Pin]:
    require(isinstance(game, Path), "Game source Path required")
    needed = {"common/scripted_effects/00_ep1_artifact_creation_effects.txt", "common/on_action/game_start.txt",
              "common/on_action/inventory_on_actions.txt", "common/artifacts/types/00_types.txt", "common/modifiers/00_artifact_modifiers.txt"}
    result = {source.relative: verify_source(game, source) for source in GAME_SOURCES if source.relative in needed}
    require(set(result) == needed, "Reviewed vanilla construction/lifecycle source set changed")
    executable = pin(game.parent / "binaries/ck3.exe")
    require(executable["sha256"] == EXPECTED_EXE_SHA, "Only exact CK3 1.20.0.4 fixture sources qualified")
    result["binaries/ck3.exe"] = executable
    return result


def _living(name: str, reference: str, curse: int) -> str:
    require(type(curse) is int and curse in (1, 2), "Only the two declared initial curses")
    values = {"schema_version": 2, "level": 1, "xp_in_level": 0, "pending_xp": 0, "growth_sequence": 0,
              "last_notified_sequence": 0, "resonance": 20, "suppression_chain": 0, "unsuppressed_equipped_months": 0,
              "personality": 1, "affix_1": 3, "affix_rank_1": 1, "curse_1": curse, "curse_rank_1": 3}
    setters = "\n".join(f"set_variable = {{ name = xalw_{key} value = {value} }}" for key, value in values.items())
    return f'''create_artifact = {{
 name = {name} description = xalw_test_living_description
 type = sword visuals = sword modifier = artifact_prowess_1_modifier
 wealth = 40 quality = 40 save_scope_as = xalw_curse_created
 history = {{ type = created_before_history }}
}}
scope:xalw_curse_created = {{
 {setters}
 set_variable = {{ name = xalw_kind value = flag:living }}
 set_variable = {{ name = xalw_diet value = flag:armor }}
 set_variable = {{ name = xalw_attuned_character value = artifact_owner }}
 set_variable = {{ name = xalw_last_settled_month value = xalw_current_month_value }}
 set_variable = {{ name = xalw_test_fixture_input value = yes }}
 # Initial projection only, before the first observation; never repeated at equip.
 xalw_refresh_artifact_effect = yes
}}
set_variable = {{ name = {reference} value = scope:xalw_curse_created }}
'''


def render_initial_inputs() -> str:
    """Two declared r3 swords and one raw candidate; never erase a schema marker."""
    materials = "\n".join(f"xalw_test_create_{rarity}_material_effect = yes\n"
        f"set_variable = {{ name = xalw_fixture_material_{rarity} value = scope:xalw_test_material_{rarity} }}"
        for rarity in ("common", "masterwork", "famed", "illustrious"))
    return f'''xalw_curse_initialize_effect = {{
 save_scope_as = xalw_fixture_owner
 # Initial spendable wallet, not a paid-result field.
 remove_short_term_gold = gold
 add_gold = {INITIAL_GOLD}
 add_stress = 20
 set_variable = {{ name = xalw_fixture_initial_day value = current_date }}
''' + _living("xalw_test_living_name", "xalw_fixture_target", 1) + _living("xalw_curse_appetite_name", "xalw_curse_fixture_appetite", 2) + '''
create_artifact = {
 name = xalw_curse_raw_name description = xalw_test_living_description
 type = sword visuals = sword modifier = artifact_prowess_1_modifier
 wealth = 10 quality = 10 save_scope_as = xalw_curse_raw
 history = { type = created_before_history }
}
# Native creation/ownership callbacks may already have judged it. Never reset it.
set_variable = { name = xalw_curse_fixture_candidate value = scope:xalw_curse_raw }
''' + materials + '''
xalw_discover_owner_effect = yes
debug_log = "XALW_CURSE_INPUTS_READY_V1"
}
'''


def emit_fixture(destination: Path, *, game: Path) -> FixtureEmission:
    require(isinstance(destination, Path) and isinstance(game, Path), "Typed fixture Paths required")
    destination = destination.resolve()
    require(not destination.is_relative_to(TOOLS.parents[1]) and not destination.exists(), "New external fixture directory required")
    sources = qualify_fixture_sources(game)
    scripts = {"descriptor.mod": 'name="Living Artifacts curse representative initial inputs"\nsupported_version="1.20.*"\n',
        "common/scripted_effects/xalw_curse_inputs.txt": render_fixture_effects().split("xalw_test_prepare_owner_effect = {", 1)[0] + render_initial_inputs(),
        "common/on_action/xalw_curse_bootstrap.txt": "on_game_start_after_lobby = { on_actions = { xalw_curse_bootstrap } }\nxalw_curse_bootstrap = { effect = { every_player = { xalw_curse_initialize_effect = yes } } }\n"}
    for language in ("english", "simp_chinese"):
        entries = render_fixture_localization("english" if language == "english" else "simp_chinese")
        entries["xalw_curse_appetite_name"] = "Appetite Input" if language == "english" else "贵族胃初始物品"
        entries["xalw_curse_raw_name"] = "Raw Discovery Candidate" if language == "english" else "未指定判定结果的物品"
        scripts[f"localization/{language}/xalw_curse_l_{language}.yml"] = f"l_{language}:\n" + "\n".join(f' {key}:0 "{value}"' for key, value in sorted(entries.items())) + "\n"
    for relative, body in scripts.items():
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8-sig", newline="\n")
    write_once(destination / "_fixture_sources.json", {"schema": "living-artifacts-curse-input-sources-v1", "machine_id": current_machine_id(),
        "observed_at_utc": utc_now(), "source_bindings": sources, "qualification": "initial-source-only", "business_pass": False})
    emission: FixtureEmission = {"schema_version": 2, "fixture_root": str(destination), "files": tree(destination),
        "input_origin": "fixture_generated", "business_acceptance": "NOT_ASSESSED", "game_started": False}
    write_once(destination.parent / (destination.name + ".emission.json"), emission)
    return emission

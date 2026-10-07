"""Prepare source-only whole-wire inputs; Root runs this once for its FIRST.

The historical V2 body retains composition/model gaps. Only roster identity
cases are synthetic (shared Commander/Knight, FullID generation, and ID zero).
No game, process, native trace, or executable file is opened here.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


def _cpp_seed(body: dict) -> str:
    """Translate the held V2 operands into a DTO, never paste a JSON leaf."""
    statements = ["inline xar::game::CombatSimulationInputsSnapshot SeedPhaseCalendarWholeV2Fixture() {",
                  "  using namespace xar::game;", "  CombatSimulationInputsSnapshot value;"]

    def set_value(target: str, operand: object) -> None:
        if operand is not None:
            literal = json.dumps(operand) if not isinstance(operand, list) else "{" + ",".join(json.dumps(v) for v in operand) + "}"
            statements.append(f"  {target} = {literal};")

    def status(target: str, operand: str) -> None:
        statements.append(f"  {target} = CombatObservationStatus::{operand};")

    def scalars(target: str, source: dict, fields: tuple[str, ...]) -> None:
        for field in fields:
            set_value(f"{target}.{field}", source[field])

    set_value("value.target_province_id", body["target_province_id"])
    scalars("value.scenario", body["scenario"], (
        "attacker_entry_province_id", "attacker_army_ids", "defender_army_ids",
        "attacker_side", "defender_side"))
    set_value("value.scenario.constructor_adjacency_kind_raw", body["scenario"].get("constructor_adjacency_kind_raw"))
    for army in body["armies"]:
        statements.extend(["  {", "  CombatArmyInputsSnapshot army;"])
        set_value("army.available", army["status"] == "available")
        scalars("army", army, ("army_id", "native_carmy_id", "encounter_role", "war_ids", "current_province_id"))
        set_value("army.native_carmy_id_observable", army["native_carmy_id"] is not None)
        set_value("army.current_province_observable", army["current_province_id"] is not None)
        statements.append(f"  army.scope_role = ArmyStrengthScopeRole::{army['scope_role']};")
        status("army.owner.status", army["owner"]["status"])
        scalars("army.owner", army["owner"], ("character_id", "counter_efficiency_raw", "counter_resistance_raw", "scale"))
        commander = army["commander"]
        status("army.commander.status", commander["status"])
        scalars("army.commander", commander, ("character_id", "generic_advantage_points"))
        set_value("army.commander.generic_advantage_observable", commander["generic_advantage_points"] is not None)
        context = commander["battle_context"]
        set_value("army.commander.battle_context.available", context["status"] == "available")
        set_value("army.commander.battle_context.province_id", context["source_target_province_id"])
        scalars("army.commander.battle_context", context, ("effective_min_roll", "effective_max_roll"))
        set_value("army.regiments_observable", army["regiments"] is not None)
        for regiment in army["regiments"] or []:
            statements.extend(["  {", "  CombatRegimentSnapshot regiment;"])
            set_value("regiment.available", regiment["status"] == "available")
            scalars("regiment", regiment, ("regiment_id", "identity_valid", "current_soldiers", "maximum_soldiers"))
            status("regiment.maa_type.status", regiment["maa_type"]["status"])
            set_value("regiment.maa_type.key", regiment["maa_type"]["key"])
            status("regiment.kind.status", regiment["kind"]["status"])
            set_value("regiment.kind.value", regiment["kind"]["value"])
            set_value("regiment.kind.fights_in_main_phase", regiment["fights_in_main_phase"])
            effective = regiment["effective_stats"]
            set_value("regiment.effective_stats.available", effective["status"] == "available")
            scalars("regiment.effective_stats", effective, (
                "source_target_province_id", "max_size", "siege_value_raw", "damage_raw", "toughness_raw", "pursuit_raw", "screen_raw", "scale"))
            counter = regiment["counter"]
            status("regiment.counter.status", counter["status"])
            scalars("regiment.counter", counter, ("class_index", "current_chunk_raw", "scale"))
            for row in counter["targets"] or []:
                statements.append(f"  regiment.counter.targets.push_back({{{row['class_index']},{row['effectiveness_raw']},{row['scale']}}});")
            statements.extend(["  army.regiments.push_back(std::move(regiment));", "  }"])
        knights = army["knights"]
        set_value("army.knights.available", knights["status"] == "available")
        scalars("army.knights", knights, ("loaded_damage_multiplier", "loaded_toughness_multiplier"))
        for knight in knights["members"] or []:
            statements.extend(["  {", "  CombatKnightSnapshot knight;"])
            scalars("knight", knight, ("eligible", "character_id", "source_regiment_id", "army_id",
                "participant_army_membership_verified", "prowess", "knight_effectiveness_raw", "effective_damage_raw", "effective_toughness_raw", "scale"))
            components = knight["effectiveness_components"]
            set_value("knight.effectiveness_components_observed", components["status"] == "available")
            set_value("knight.effectiveness_modifier_raw", components["modifier_raw"])
            set_value("knight.effectiveness_operand_raw", components["operand_raw"])
            statements.extend(["  army.knights.members.push_back(std::move(knight));", "  }"])
        statements.extend(["  value.armies.push_back(std::move(army));", "  }"])
    target = body["target_province"]
    set_value("value.target_province.available", target["status"] == "available")
    set_value("value.target_province.province_id", target["province_id"])
    for name, fields in (("terrain", ("key", "combat_width_multiplier_raw", "scale")),
                         ("crossing", ("kind",)), ("precontact_width", ("base", "final")),
                         ("defender_context", ("defender_side", "holding_defender"))):
        source = target[name]
        set_value(f"value.target_province.{name}.available", source["status"] == "available")
        scalars(f"value.target_province.{name}", source, fields)
    status("value.target_province.defender_context.holding_defender_status", target["defender_context"]["holding_defender_status"])
    for counter in body["counter_resolutions"]:
        statements.extend(["  {", "  CombatCounterResolutionSnapshot counter;"])
        set_value("counter.available", counter["status"] == "available")
        scalars("counter", counter, ("countered_side", "countering_side", "countered_modifier_owner_character_id",
            "countering_modifier_owner_character_id", "context_scale_raw", "class_count", "damage_retention_by_class_raw", "scale"))
        statements.extend(["  value.counter_resolutions.push_back(std::move(counter));", "  }"])
    if body["ongoing_combats"]:
        raise ValueError("This FIRST uses the held contact-free V2 fixture only")
    scalars("value", body["completeness"], ("input_observation_ready", "monte_carlo_ready", "missing_required_domains"))
    statements.extend(["  return value;", "}", ""])
    return "\n".join(statements)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    saved = json.loads(args.base.read_text(encoding="utf-8-sig"))
    body = copy.deepcopy(saved["frame"]["combat_simulation_inputs"])
    first = body["armies"][0]
    members = first["knights"]["members"]
    # Preserve full V2 role provenance, with deliberately distinct identity cases.
    members[0]["character_id"] = first["commander"]["character_id"]
    members[1]["character_id"] = 0
    members[2]["character_id"] = 0x05007485
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "phase-calendar-base-seed.inc").write_text(_cpp_seed(body), encoding="utf-8")
    (args.out_dir / "FIXTURE-PROVENANCE.json").write_text(json.dumps({
        "schema_version": 1, "source_base": str(args.base),
        "source_only_fixture": True, "actual4_live_observation": False,
        "operand_date_raw": 53288448, "operand_interval_available": 7,
        "operand_interval_zero": 0,
        "identity_cases": ["same Character Commander and Knight", "FullCharacterID zero", "generation-bearing FullCharacterID 0x05007485"],
        "base_completeness_and_model_gaps_modified": False,
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

"""Root-only full V2 literal projection after adding the production chance hook."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from project_knight_context_serializer import literal_function


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    source_bytes = args.source.read_bytes()
    source = source_bytes.decode("utf-8-sig")
    names = ("SignedNumber", "AppendJsonString", "AppendInt32Array", "CombatStatusName",
             "AppendUnavailableReason", "AppendCombatMaaType", "AppendCombatEffectiveStats",
             "AppendCombatCounter", "AppendCombatRegiment", "AppendCombatOwner",
             "AppendCombatCommander", "AppendCombatKnights", "AppendCombatArmy",
             "AppendCombatTargetProvince", "AppendOngoingCombat", "AppendCounterResolution",
             "AppendCombatSimulationInputs")
    functions = {name: literal_function(source, name) for name in names}
    if "AppendPhaseEventCommanderChanceWeightsV1" not in functions["AppendCombatSimulationInputs"]:
        raise ValueError("Root must integrate the same-V2 production chance hook before FIRST")
    includes = ("game_contract.hpp", "combat_simulation_inputs_v2_wire.hpp",
                "combat_hypothetical_scenario_v2_serializer.hpp", "contextual_advantage_v1.hpp",
                "phase_rite_parameters_v1_serializer.hpp", "phase_warmonger_core_v1_serializer.hpp",
                "phase_berserker_validity_inputs_v1_serializer.hpp", "phase_berserker_chance_inputs_v1_serializer.hpp",
                "phase_event_calendar_observation_v1_serializer.hpp", "phase_event_role_compatibility_v1_serializer.hpp",
                "phase_event_commander_side_identity_v1_serializer.hpp",
                "phase_event_commander_trigger_conditions_v1_serializer.hpp",
                "phase_event_commander_chance_weights_v1_serializer.hpp")
    output = "\n".join(f'#include "xar_bridge/{name}"' for name in includes)
    output += "\n#include <array>\n#include <charconv>\n#include <cstdint>\n#include <string>\n#include <string_view>\n#include <system_error>\n"
    output += "namespace commander_chance_whole_projection {\nusing namespace xar;\n"
    output += "\n".join(functions.values()) + "\n}\n"
    output += "namespace xar::bridge {\nstd::string SerializeCombatSimulationInputsV2(const game::CombatSimulationInputsSnapshot &value) {\n"
    output += "  std::string out; commander_chance_whole_projection::AppendCombatSimulationInputs(out, value); return out;\n}\n}\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8", newline="\n")
    args.receipt.write_text(json.dumps({
        "schema": "commander_chance_integrated_production_whole_v2_projection_v1",
        "source": str(args.source), "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "literal_function_sha256": {name: hashlib.sha256(body.encode()).hexdigest() for name, body in functions.items()},
        "generated_source": str(args.output), "external_json_concatenation": False,
        "same_complete_production_append_function": True, "actual4_live_observation": False,
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

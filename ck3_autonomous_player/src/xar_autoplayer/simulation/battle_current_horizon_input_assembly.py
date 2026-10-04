"""Package decoded .3 current operands; never execute or predict a battle.

The compact field map may reference an external complete normalized leaf.
Its scalar observations remain useful without pretending to be that leaf.
All future inputs must be supplied explicitly by the caller.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Mapping

EXACT_BUILD = {
    "game_version": "1.20.0.3",
    "steam_build_id": 25652598,
    "executable_sha256": "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
}
ADAPTER_ENTRY = "xar_autoplayer.simulation.battle_current_adapter.adapt_current_battle_condition"
HORIZON_ENTRY = "xar_autoplayer.simulation.battle_current_conditional_horizon.run_conditional_horizon"
SOURCE_ROOT = "Z:/g38/ck3_autonomous_player/src/xar_autoplayer/simulation/"


@dataclass(frozen=True, slots=True)
class MissingInputEntry:
    stage: str
    input_name: str
    dto_entry: str
    construction_guidance: str


@dataclass(frozen=True, slots=True)
class CurrentHorizonInputAssembly:
    status: str
    construction_fields: Mapping[str, Any]
    concrete_values: tuple[Mapping[str, Any], ...]
    missing_entries: tuple[MissingInputEntry, ...]
    build_binding: Mapping[str, Any]
    captured_build_identity: Any
    provenance: Mapping[str, Any]
    scenario_inputs: Any
    current_snapshot_input_complete: bool
    actual_game_days_advanced: int = 0
    native_rng_state_observed: bool = False
    actual_next_draw_claimed: bool = False
    complete_native_transition: bool = False
    complete_monte_carlo: bool = False
    win_probability_ready: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def assemble_current_horizon_input(
    bundle: Mapping[str, Any], *, build_binding: Mapping[str, Any] | None = None,
) -> CurrentHorizonInputAssembly:
    """Copy concrete decoded fields and list exact construction dependencies.

    A Root/owner external binding is independent of nullable query identity.
    A known retired-build mismatch cannot be promoted into .3 operands.
    A complete normalized current_snapshot can be handed to the existing
    adapter; compact observations only expose its source construction fields.
    """
    capture = bundle.get("capture_provenance", bundle.get("capture", {})) or {}
    binding = copy.deepcopy(dict(build_binding if build_binding is not None else
                                 bundle.get("build_binding", capture.get("external_binding", {})) or {}))
    captured_identity = copy.deepcopy(bundle.get("captured_build_identity",
                                                capture.get("captured_build_identity")))
    observed = tuple(copy.deepcopy(bundle.get("observations", ())))
    snapshot = copy.deepcopy(bundle.get("current_snapshot"))
    resume = copy.deepcopy(bundle.get("active_resume_inputs"))
    backing = copy.deepcopy(bundle.get("backing_components_by_regiment_id"))
    scenario = copy.deepcopy(bundle.get("scenario_inputs"))
    source_reference = copy.deepcopy(bundle.get("current_snapshot_source_reference",
        (bundle.get("construction_fields") or {}).get("snapshot_input_ref")))
    gaps: list[MissingInputEntry] = []

    def missing(stage: str, name: str, dto: str, guidance: str) -> None:
        gaps.append(MissingInputEntry(stage, name, dto, guidance))

    matching = bool(binding) and all(
        (str(binding.get(key)) == str(value) if key != "executable_sha256" else
         str(binding.get(key, "")).upper() == value)
        for key, value in EXACT_BUILD.items()
    )
    # Captured nulls are preserved; only an actual conflicting identity rejects.
    conflict = isinstance(captured_identity, Mapping) and any(
        captured_identity.get(key) is not None and
        str(captured_identity[key]).upper() != str(value).upper()
        for key, value in EXACT_BUILD.items()
    )
    if not matching or conflict:
        missing("binding", "exact_1_20_0_3_build_binding", "CurrentBattleCondition source binding",
                "Supply the sealed .3 owner/Root lineage; do not relabel retired .2 operands.")
        snapshot, resume, backing = None, None, None

    # A compact map cannot acquire complete-leaf status from available scalars.
    complete = (matching and not conflict and
                bundle.get("current_snapshot_input_complete") is True and
                isinstance(snapshot, Mapping) and snapshot.get("status") == "available")
    if not complete:
        missing("initial", "complete_normalized_current_snapshot", ADAPTER_ENTRY + "(snapshot)",
                "Use the sealed battle_control_snapshot leaf at its linked JSON pointer; "
                "the compact scalar map is a construction entry, not a complete DTO.")

    if snapshot is not None and matching and not conflict:
        for name in ("snapshot_revision", "observed_date_raw", "combat_id", "province_id",
                     "phase", "phase_raw", "phase_day", "base_combat_width", "final_combat_width",
                     "roll_cadence_counter", "base_advantage_raw", "resolved_advantage_raw"):
            if name in snapshot:
                observed += ({"target_field": name, "value": copy.deepcopy(snapshot[name]),
                              "source_json_pointer": "/current_snapshot/" + name},)

    def supplied(name: str) -> bool:
        return isinstance(snapshot, Mapping) and snapshot.get(name) is not None

    for name, entry, guidance in (
        ("current_loss_inputs_v1", "CurrentBattleCondition.loss_inputs / CurrentLossInputs",
         "Capture native primary levy damage, advantage factor and runtime loss coefficients; "
         "never substitute hypothetical commander zero-roll totals."),
        ("active_counter_inputs_v1", "CurrentBattleCondition.active_counter_inputs",
         "Capture the complete current native counter operand census for the same frame."),
        ("pursuit_modifier_sides", "CurrentBattleCondition.pursuit_modifier_sides",
         "Capture both sides' actual pursuit modifiers for the same CombatID/frame."),
    ):
        if not supplied(name):
            missing("initial_operands", name, entry, guidance)
    if backing is None:
        missing("initial_backing", "backing_components_by_regiment_id", ADAPTER_ENTRY,
                "Supply captured integer BackingComponent tuples in native order; "
                "fractional fighting strength does not establish component soldiers.")
    if not isinstance(resume, Mapping) or resume.get("input_observation_ready") is not True:
        missing("initial_roll_bounds", "complete_same_frame_active_resume_inputs", ADAPTER_ENTRY,
                "Use same-frame selected commander next-roll bounds; absent bounds remain unknown.")

    supplied_scenario = scenario if isinstance(scenario, Mapping) else {}
    for stage, name, dto, guidance in (
        ("caller", "draw_state", "combat_core.DrawState",
         "Supply an explicit caller-owned counter/salt and seed provenance; no native future RNG claim."),
        ("caller", "max_days", HORIZON_ENTRY,
         "Supply the bounded caller horizon length."),
        ("timeline", "timeline", "ConditionalHorizonDay[]",
         "Supply each day's explicit admission, loaded coefficients and reached-stage inputs."),
        ("admission", "admission", "DailyDateStageInput",
         "Supply date-stage execution and CombatID manager membership, without a default true witness."),
        ("loaded", "loaded", "LoadedScheduleInputs",
         "Supply loaded maneuver duration and roll cadence with their source provenance."),
        ("entries", "entry_events", "ConditionalHorizonDay.entry_events",
         "Supply the admitted join/death timeline; unknown is not an explicit empty event tuple."),
        ("script", "phase_events", "ConditionalHorizonDay.phase_events",
         "Supply selected phase events or explicitly witnessed no selected events."),
        ("ai", "ai_context", "ConditionalHorizonDay.ai_context",
         "Supply the caller condition/action adapter; do not invent action_selected=False."),
        ("future_main", "future_main", "FutureMainRefreshInputs",
         "Supply fixed-condition scope and commander/role/terrain/effect primitives for reached main work."),
        ("transition", "transition", "CurrentMainPhaseTransitionInputs",
         "Supply actual first-loser Army automatic-retreat operands and independent normal intent."),
        ("pursuit", "pursuit", "CurrentPursuitSourceContext",
         "Supply frozen initial soft pools, actual loser skip and loaded pursuit coefficients; "
         "a retained pursuit frame does not reconstruct missing initializer pools."),
        ("terminal", "terminal", "ConditionalTerminalInputs",
         "Supply full all-Army backing, receiver/link witnesses, side baselines and normal-result intent."),
    ):
        if name not in supplied_scenario or supplied_scenario[name] is None:
            missing(stage, name, dto, guidance)

    fields = {"entry": ADAPTER_ENTRY, "snapshot": snapshot if complete else None,
              "snapshot_source_reference": source_reference,
              "active_resume_inputs": resume,
              "backing_components_by_regiment_id": backing,
              "levy_damage_raw_by_side": None,
              "source_root": SOURCE_ROOT}
    provenance = copy.deepcopy(dict(capture))
    provenance["observation_scope"] = "historical_captured_condition_no_fresh_query"
    observed = tuple(dict(row, source_path=row.get("source_path", capture.get("path")),
                          source_sha256=row.get("source_sha256", capture.get("sha256")),
                          build_binding_ref="#/build_binding") for row in observed)
    return CurrentHorizonInputAssembly(
        status="partial" if gaps else "construction_inputs_present",
        construction_fields=fields, concrete_values=observed, missing_entries=tuple(gaps),
        build_binding=binding, captured_build_identity=captured_identity,
        provenance=provenance, scenario_inputs=scenario,
        current_snapshot_input_complete=bool(complete),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, help="already-decoded compact captured bundle JSON")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    decoded = json.loads(args.bundle.read_text(encoding="utf-8-sig"))
    result = json.dumps(assemble_current_horizon_input(decoded).to_dict(), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(result, encoding="utf-8", newline="\n")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()

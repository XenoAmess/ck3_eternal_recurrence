"""Run the explicitly non-planner combat research envelope on frozen fixtures."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from xar_autoplayer.simulation.combat_core import CombatExperiment
from xar_autoplayer.simulation.combat_input import load_live_combat_fixture
from xar_autoplayer.simulation.research_envelope import (
    RESEARCH_ENVELOPE_MANIFEST,
    ResearchEnvelopeAssumptions,
    run_research_envelope_experiment,
)


DEFAULT_FIXTURES = (
    "live_rev4_vs_357.json",
    "live_rev4_vs_combined.json",
    "live_rev4_player_attacks_357.json",
    "live_rev4_player_attacks_combined.json",
)

SIMULATOR_SOURCE_FILES = (
    "run_combat_research_envelope.py",
    "src/xar_autoplayer/simulation/combat_core.py",
    "src/xar_autoplayer/simulation/combat_input.py",
    "src/xar_autoplayer/simulation/research_envelope.py",
)


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _source_fingerprint(project_root: Path) -> tuple[str, dict[str, str]]:
    files = {
        name: hashlib.sha256((project_root / name).read_bytes()).hexdigest()
        for name in SIMULATOR_SOURCE_FILES
    }
    return _canonical_sha256(files), files


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=0xC0319A06)
    parser.add_argument("--horizon-days", type=int, default=120)
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--fixture", action="append", dest="fixtures")
    return parser


def main() -> int:
    args = _parser().parse_args()
    project_root = Path(__file__).parent
    fixture_root = project_root / "tests" / "fixtures" / "combat"
    code_sha256, code_files = _source_fingerprint(project_root)
    manifest_payload = asdict(RESEARCH_ENVELOPE_MANIFEST)
    manifest_sha256 = _canonical_sha256(manifest_payload)
    rows: list[dict[str, object]] = []
    for fixture_name in args.fixtures or DEFAULT_FIXTURES:
        combat_input = load_live_combat_fixture(fixture_root / fixture_name)
        attacker_commander = next(
            army.public_army_id
            for army in combat_input.armies
            if army.encounter_role == "attacker"
        )
        defender_commander = next(
            army.public_army_id
            for army in combat_input.armies
            if army.encounter_role == "defender"
        )
        assumptions = ResearchEnvelopeAssumptions(
            attacker_commander_army_id=attacker_commander,
            defender_commander_army_id=defender_commander,
        )
        experiment = CombatExperiment(
            input_sha256=combat_input.input_sha256,
            seed_u64=args.seed,
            sample_count=args.samples,
            horizon_days=args.horizon_days,
        )
        summary = run_research_envelope_experiment(
            combat_input,
            experiment,
            assumptions,
            max_workers=args.workers,
        )
        rows.append(
            {
                "fixture": fixture_name,
                "capture": {
                    "snapshot_id": combat_input.capture_snapshot_id,
                    "revision": combat_input.capture_revision,
                    "native_revision": combat_input.capture_native_revision,
                    "date_raw": combat_input.capture_date_raw,
                },
                "scenario": asdict(combat_input.encounter),
                "input_sha256": combat_input.input_sha256,
                "fixture_file_sha256": hashlib.sha256(
                    (fixture_root / fixture_name).read_bytes()
                ).hexdigest(),
                "assumptions": asdict(assumptions),
                "summary": asdict(summary),
            }
        )
    output = {
        "schema_version": 2,
        "experiment_kind": "phase_events_disabled_no_voluntary_retreat_research_envelope",
        "model_fidelity": "research-only-bounded-core",
        "planner_usable": False,
        "active_attack_allowed": False,
        "game_version": "1.19.0.6",
        "executable_sha256": (
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
        ),
        "code_sha256": code_sha256,
        "code_files_sha256": code_files,
        "transition_manifest_sha256": manifest_sha256,
        "transition_manifest": manifest_payload,
        "experiment": {
            "seed_u64": args.seed,
            "sample_count_per_scenario": args.samples,
            "horizon_days": args.horizon_days,
            "workers": args.workers,
        },
        "missing_native_inputs": [
            "supply_state",
            "debt_tier",
            "recently_disembarked",
            "unreformed_faith",
            "complete_resolved_advantage_sources",
            "dynamic_advantage_helper_0x2307CB0",
            "hard_casualty_modifier_0x18C_0x18D_0x19F",
            "pursuit_modifier_0x105_0x18B",
        ],
        "omitted_v3_fields": [
            "supply_state",
            "debt_tier",
            "recently_disembarked",
            "unreformed_faith",
            "complete_resolved_advantage_sources",
            "dynamic_advantage_helper_0x2307CB0",
            "hard_casualty_modifier_0x18C_0x18D_0x19F",
            "pursuit_modifier_0x105_0x18B",
        ],
        "advantage_limitations": {
            "known_constructor_order": [
                "supply_side_0",
                "supply_side_1",
                "holding_defender",
                "recently_disembarked_first_army_side_0",
                "recently_disembarked_first_army_side_1",
                "debt_side_0",
                "debt_side_1",
                "unreformed_faith_side_0",
                "unreformed_faith_side_1",
            ],
            "debt_tier_observed_min": -100,
            "dynamic_helper_unclosed": "0x2307CB0",
            "modeled_here": [
                "generic_commander_advantage",
                "stock_terrain_defender_advantage",
                "holding_defender_advantage",
                "crossing_defender_advantage",
                "commander_rolls",
            ],
        },
        "missing_transition_fidelity": [
            "loaded_phase_event_effect_transition",
            "exact_build_original_trace_fixture",
            "mixed_owner_ai_partial_retreat_policy",
        ],
        "scenarios": rows,
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

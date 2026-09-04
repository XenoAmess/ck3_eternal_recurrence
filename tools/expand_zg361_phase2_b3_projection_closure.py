#!/usr/bin/env python3
"""Expand a B3 product tree to a fixed point of concrete custom calls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

import freeze_zg361_phase2_b3_no_launch as freeze


def _provider_files(
    source: Path,
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    sys.path.insert(0, str(freeze.MOD_ROOT / "tools"))
    from zg361_effect_sharding import top_level_effect_entries

    effects: dict[str, str] = {}
    events: dict[str, str] = {}
    triggers: dict[str, str] = {}
    duplicate_effects: set[str] = set()
    duplicate_events: set[str] = set()
    duplicate_triggers: set[str] = set()
    effect_root = source / "common" / "scripted_effects"
    for path in sorted(effect_root.glob("*.txt"), key=lambda value: value.name):
        relative = path.relative_to(source).as_posix()
        for entry in top_level_effect_entries(path.read_bytes()):
            if entry.name in effects:
                duplicate_effects.add(entry.name)
            effects[entry.name] = relative
    event_root = source / "events"
    for path in sorted(event_root.glob("*.txt"), key=lambda value: value.name):
        relative = path.relative_to(source).as_posix()
        for name, _block in freeze._top_level_event_entries(path):
            if name in events:
                duplicate_events.add(name)
            events[name] = relative
    trigger_root = source / "common" / "scripted_triggers"
    for path in sorted(trigger_root.glob("*.txt"), key=lambda value: value.name):
        relative = path.relative_to(source).as_posix()
        for entry in top_level_effect_entries(path.read_bytes()):
            if entry.name in triggers:
                duplicate_triggers.add(entry.name)
            triggers[entry.name] = relative
    if duplicate_effects or duplicate_events or duplicate_triggers:
        raise freeze.FreezeError(
            "canonical release has duplicate custom providers: "
            f"effects={sorted(duplicate_effects)}, events={sorted(duplicate_events)}, "
            f"triggers={sorted(duplicate_triggers)}"
        )
    return effects, events, triggers


def expand_projection_closure(
    candidate: Path,
    canonical: Path,
    evidence_path: Path,
) -> dict[str, object]:
    candidate = candidate.resolve()
    canonical = canonical.resolve()
    if not candidate.is_dir() or not canonical.is_dir():
        raise freeze.FreezeError("candidate and canonical roots must exist")
    effect_providers, event_providers, trigger_providers = _provider_files(canonical)
    added_files: set[str] = set()
    rounds: list[dict[str, object]] = []
    initial_missing_effects: list[str] | None = None
    initial_missing_events: list[str] | None = None
    initial_missing_triggers: list[str] | None = None

    while True:
        closure = freeze.central_effect_call_closure(candidate)
        missing_effects = sorted(
            set(closure["missing_effects"])
            | set(closure["material_projection"]["missing_effects"])
        )
        missing_events = sorted(
            set(closure["missing_events"])
            | set(closure["material_projection"]["missing_events"])
        )
        missing_triggers = sorted(
            set(closure["missing_triggers"])
            | set(closure["material_projection"]["missing_triggers"])
        )
        if initial_missing_effects is None:
            initial_missing_effects = missing_effects
            initial_missing_events = missing_events
            initial_missing_triggers = missing_triggers
        if not missing_effects and not missing_events and not missing_triggers:
            break
        unresolved_effects = sorted(
            name for name in missing_effects if name not in effect_providers
        )
        unresolved_events = sorted(
            name for name in missing_events if name not in event_providers
        )
        unresolved_triggers = sorted(
            name for name in missing_triggers if name not in trigger_providers
        )
        if unresolved_effects or unresolved_events or unresolved_triggers:
            raise freeze.FreezeError(
                "canonical release cannot satisfy projection closure: "
                f"effects={unresolved_effects}, events={unresolved_events}, "
                f"triggers={unresolved_triggers}"
            )
        provider_files = sorted(
            {effect_providers[name] for name in missing_effects}
            | {event_providers[name] for name in missing_events}
            | {trigger_providers[name] for name in missing_triggers}
        )
        new_files = [relative for relative in provider_files if relative not in added_files]
        if not new_files:
            raise freeze.FreezeError("projection closure expansion made no progress")
        for relative in new_files:
            source = canonical / relative
            target = candidate / relative
            if target.exists():
                raise freeze.FreezeError(
                    f"missing provider unexpectedly maps to existing file: {relative}"
                )
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            added_files.add(relative)
        rounds.append(
            {
                "round": len(rounds) + 1,
                "missing_effects": missing_effects,
                "missing_events": missing_events,
                "missing_triggers": missing_triggers,
                "provider_files_added": new_files,
            }
        )

    final_closure = freeze.central_effect_call_closure(candidate)
    final_missing_effects = sorted(
        set(final_closure["missing_effects"])
        | set(final_closure["material_projection"]["missing_effects"])
    )
    final_missing_events = sorted(
        set(final_closure["missing_events"])
        | set(final_closure["material_projection"]["missing_events"])
    )
    final_missing_triggers = sorted(
        set(final_closure["missing_triggers"])
        | set(final_closure["material_projection"]["missing_triggers"])
    )
    green = final_closure["green"] is True
    evidence: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_phase2_b3_material_custom_call_closure_expansion",
        "green": green,
        "candidate_source": str(candidate),
        "canonical_source": str(canonical),
        "initial_missing_effects": initial_missing_effects or [],
        "initial_missing_events": initial_missing_events or [],
        "initial_missing_triggers": initial_missing_triggers or [],
        "rounds": rounds,
        "added_file_count": len(added_files),
        "added_files": [
            freeze.record(candidate / relative, relative_to=candidate)
            for relative in sorted(added_files)
        ],
        "final_effect_definition_count": final_closure["material_projection"][
            "effect_definition_count"
        ],
        "final_event_definition_count": final_closure["material_projection"][
            "event_definition_count"
        ],
        "final_trigger_definition_count": final_closure["material_projection"][
            "trigger_definition_count"
        ],
        "final_missing_effects": final_missing_effects,
        "final_missing_events": final_missing_events,
        "final_missing_triggers": final_missing_triggers,
    }
    freeze.write_json(evidence_path.resolve(), evidence)
    if not green:
        raise freeze.FreezeError("expanded B3 product closure remains RED")
    return evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-source", type=Path, required=True)
    parser.add_argument("--canonical-source", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        evidence = expand_projection_closure(
            args.candidate_source, args.canonical_source, args.evidence
        )
    except freeze.FreezeError as error:
        print(f"B3 closure expansion failed: {error}")
        return 2
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

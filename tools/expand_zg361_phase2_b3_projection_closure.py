#!/usr/bin/env python3
"""Expand a B3 product tree to a fixed point of concrete custom calls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import sys

import freeze_zg361_phase2_b3_no_launch as freeze


BOM = b"\xef\xbb\xbf"
B3_TERMINAL_EVENT = "zg361pp.9004"
B3_TERMINAL_LOC_KEYS = tuple(
    f"{B3_TERMINAL_EVENT}.{suffix}" for suffix in ("t", "desc", "a")
)
AUTHORED_LANGUAGES = ("english", "simp_chinese")
PLACEHOLDER_LANGUAGES = (
    "french",
    "german",
    "japanese",
    "korean",
    "polish",
    "russian",
    "spanish",
)
LOCALIZATION_LANGUAGES = AUTHORED_LANGUAGES + PLACEHOLDER_LANGUAGES
LOCALIZATION_LINE = re.compile(r'^\s*([^\s:#]+):\d+\s+"(.*)"\s*$')


def _promotion_localization_relative(language: str) -> str:
    return (
        f"localization/{language}/"
        f"zg361_feedback_promotion_pip_l_{language}.yml"
    )


def _localization_values(path: Path) -> dict[str, str]:
    payload = path.read_bytes()
    if not payload.startswith(BOM):
        raise freeze.FreezeError(f"localization provider is missing UTF-8 BOM: {path}")
    values: dict[str, str] = {}
    for line in payload.decode("utf-8-sig").splitlines():
        match = LOCALIZATION_LINE.match(line)
        if match and match.group(1) in B3_TERMINAL_LOC_KEYS:
            values[match.group(1)] = match.group(2)
    return values


def _candidate_has_b3_terminal_event(candidate: Path) -> bool:
    event_root = candidate / "events"
    return any(
        name == B3_TERMINAL_EVENT
        for path in sorted(event_root.glob("*.txt"), key=lambda value: value.name)
        for name, _block in freeze._top_level_event_entries(path)
    )


def synchronize_b3_terminal_localization(
    candidate: Path, canonical: Path
) -> dict[str, object]:
    """Copy the generated provider when the projected terminal event needs it."""

    required_keys = list(B3_TERMINAL_LOC_KEYS)
    if not _candidate_has_b3_terminal_event(candidate):
        return {
            "green": True,
            "applicable": False,
            "event": B3_TERMINAL_EVENT,
            "required_keys": required_keys,
            "authored_languages": list(AUTHORED_LANGUAGES),
            "placeholder_languages": list(PLACEHOLDER_LANGUAGES),
            "initial_missing_by_language": {},
            "updated_files": [],
            "final_missing_by_language": {},
            "placeholder_values_match_english": True,
        }

    canonical_values: dict[str, dict[str, str]] = {}
    for language in LOCALIZATION_LANGUAGES:
        relative = _promotion_localization_relative(language)
        source = canonical / relative
        if not source.is_file():
            raise freeze.FreezeError(
                f"canonical localization provider is missing: {relative}"
            )
        values = _localization_values(source)
        missing = sorted(set(B3_TERMINAL_LOC_KEYS) - set(values))
        if missing:
            raise freeze.FreezeError(
                f"canonical localization provider lacks B3 terminal keys: "
                f"{relative}: {missing}"
            )
        canonical_values[language] = values

    english_values = canonical_values["english"]
    placeholder_mismatches = {
        language: sorted(
            key
            for key in B3_TERMINAL_LOC_KEYS
            if canonical_values[language][key] != english_values[key]
        )
        for language in PLACEHOLDER_LANGUAGES
    }
    placeholder_mismatches = {
        language: keys
        for language, keys in placeholder_mismatches.items()
        if keys
    }
    if placeholder_mismatches:
        raise freeze.FreezeError(
            "non-authored B3 terminal localization must retain English placeholders: "
            f"{placeholder_mismatches}"
        )

    initial_missing_by_language: dict[str, list[str]] = {}
    updated_relatives: list[str] = []
    for language in LOCALIZATION_LANGUAGES:
        relative = _promotion_localization_relative(language)
        source = canonical / relative
        target = candidate / relative
        target_has_bom = target.is_file() and target.read_bytes().startswith(BOM)
        values = _localization_values(target) if target_has_bom else {}
        missing = sorted(set(B3_TERMINAL_LOC_KEYS) - set(values))
        if missing:
            initial_missing_by_language[language] = missing
        if (
            missing
            or not target.is_file()
            or not target_has_bom
            or any(
                values.get(key) != canonical_values[language][key]
                for key in B3_TERMINAL_LOC_KEYS
            )
        ):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            updated_relatives.append(relative)

    final_missing_by_language: dict[str, list[str]] = {}
    final_values: dict[str, dict[str, str]] = {}
    for language in LOCALIZATION_LANGUAGES:
        relative = _promotion_localization_relative(language)
        values = _localization_values(candidate / relative)
        missing = sorted(set(B3_TERMINAL_LOC_KEYS) - set(values))
        if missing:
            final_missing_by_language[language] = missing
        final_values[language] = values
    final_english = final_values["english"]
    placeholders_match = all(
        final_values[language].get(key) == final_english.get(key)
        for language in PLACEHOLDER_LANGUAGES
        for key in B3_TERMINAL_LOC_KEYS
    )
    green = not final_missing_by_language and placeholders_match
    return {
        "green": green,
        "applicable": True,
        "event": B3_TERMINAL_EVENT,
        "required_keys": required_keys,
        "authored_languages": list(AUTHORED_LANGUAGES),
        "placeholder_languages": list(PLACEHOLDER_LANGUAGES),
        "initial_missing_by_language": initial_missing_by_language,
        "updated_files": [
            freeze.record(candidate / relative, relative_to=candidate)
            for relative in updated_relatives
        ],
        "final_missing_by_language": final_missing_by_language,
        "placeholder_values_match_english": placeholders_match,
    }


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
    localization_closure = synchronize_b3_terminal_localization(candidate, canonical)
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
    green = (
        final_closure["green"] is True
        and localization_closure["green"] is True
    )
    evidence: dict[str, object] = {
        "schema_version": 2,
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
        "localization_closure": localization_closure,
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

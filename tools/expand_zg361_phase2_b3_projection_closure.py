#!/usr/bin/env python3
"""Expand a B3 product tree to a fixed point of concrete custom calls."""

from __future__ import annotations

import argparse
import hashlib
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
SCRIPTED_WIDGET_REGISTRATION = re.compile(
    r"^\s*(gui/[^\s=]+\.gui)\s*=\s*[^\s#]+", re.MULTILINE
)
SCRIPTED_GUI_CALL = re.compile(
    r"GetScriptedGui\(\s*['\"](?P<name>[A-Za-z0-9_]+)['\"]\s*\)"
)
CURRENT_CORE_SOURCE = Path("common/scripted_effects/zg361_effects.txt")
CURRENT_CORE_SHARDS = (
    Path("common/scripted_effects/zg361_core_appeal_scoreboard_effects.txt"),
    Path("common/scripted_effects/zg361_core_elimination_effects.txt"),
    Path("common/scripted_effects/zg361_core_result_delivery_effects.txt"),
    Path("common/scripted_effects/zg361_core_review_cycle_effects.txt"),
)
B3_REACHABLE_LOCALIZATION_FAMILIES = (
    "zg361_career_hc",
    "zg361_career_learning",
    "zg361_compensation_runtime",
    "zg361_credit_project",
    "zg361_feedback_promotion_pip",
    "zg361_phase2_central",
    "zg361_phase3_metrics_delivery",
)
B3_LOCALIZATION_EVENT_PREFIXES = {
    "zg361_career_hc": ("zg361_career_hc_",),
    "zg361_career_learning": ("zg361_career_learning_",),
    "zg361_compensation_runtime": ("zg361_generated_compensation_runtime_",),
    "zg361_credit_project": ("zg361_credit_project_",),
    "zg361_feedback_promotion_pip": ("zg361_feedback_promotion_pip_",),
    "zg361_phase2_central": ("zg361_phase2_central_",),
    "zg361_phase3_metrics_delivery": ("zg361_phase3_metrics_delivery_",),
}


def _localization_relative(family: str, language: str) -> str:
    return f"localization/{language}/{family}_l_{language}.yml"


def _promotion_localization_relative(language: str) -> str:
    return _localization_relative("zg361_feedback_promotion_pip", language)


def _all_localization_values(path: Path) -> dict[str, str]:
    payload = path.read_bytes()
    if not payload.startswith(BOM):
        raise freeze.FreezeError(f"localization provider is missing UTF-8 BOM: {path}")
    values: dict[str, str] = {}
    for line in payload.decode("utf-8-sig").splitlines():
        match = LOCALIZATION_LINE.match(line)
        if not match:
            continue
        key = match.group(1)
        if key in values:
            raise freeze.FreezeError(
                f"localization provider contains a duplicate key: {path}: {key}"
            )
        values[key] = match.group(2)
    return values


def _localization_values(path: Path) -> dict[str, str]:
    return {
        key: value
        for key, value in _all_localization_values(path).items()
        if key in B3_TERMINAL_LOC_KEYS
    }


def _required_localization_families(candidate: Path) -> list[str]:
    event_names = {
        path.name
        for path in (candidate / "events").glob("*.txt")
        if path.is_file()
    }
    return [
        family
        for family in B3_REACHABLE_LOCALIZATION_FAMILIES
        if any(
            event_name.startswith(prefix)
            for event_name in event_names
            for prefix in B3_LOCALIZATION_EVENT_PREFIXES[family]
        )
    ]


def _provider_inventory_sha256(records: list[dict[str, object]]) -> str:
    lines = [
        f"{record['path']}\t{record['bytes']}\t{str(record['sha256']).lower()}"
        for record in sorted(records, key=lambda value: str(value["path"]))
    ]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def synchronize_b3_reachable_localization(
    candidate: Path, canonical: Path
) -> dict[str, object]:
    """Copy exact all-language providers for every reachable B3 purpose family."""

    required_families = _required_localization_families(candidate)
    if not required_families:
        return {
            "green": True,
            "applicable": False,
            "required_families": [],
            "required_key_count": 0,
            "authored_languages": list(AUTHORED_LANGUAGES),
            "placeholder_languages": list(PLACEHOLDER_LANGUAGES),
            "initial_missing_by_language": {},
            "updated_files": [],
            "final_missing_by_language": {},
            "placeholder_values_match_english": True,
            "provider_files_exact": True,
            "provider_file_count": 0,
            "provider_bytes": 0,
            "provider_inventory_sha256": hashlib.sha256(b"").hexdigest(),
        }

    canonical_values: dict[str, dict[str, dict[str, str]]] = {}
    canonical_records: list[dict[str, object]] = []
    for family in required_families:
        family_values: dict[str, dict[str, str]] = {}
        for language in LOCALIZATION_LANGUAGES:
            relative = _localization_relative(family, language)
            source = canonical / relative
            if not source.is_file():
                raise freeze.FreezeError(
                    f"canonical localization provider is missing: {relative}"
                )
            values = _all_localization_values(source)
            if not values:
                raise freeze.FreezeError(
                    f"canonical localization provider has no keys: {relative}"
                )
            family_values[language] = values
            canonical_records.append(freeze.record(source, relative_to=canonical))
        english_keys = set(family_values["english"])
        structural_mismatches = {
            language: {
                "missing": sorted(english_keys - set(family_values[language])),
                "extra": sorted(set(family_values[language]) - english_keys),
            }
            for language in LOCALIZATION_LANGUAGES
            if set(family_values[language]) != english_keys
        }
        if structural_mismatches:
            raise freeze.FreezeError(
                "canonical B3 localization provider key sets differ from English: "
                f"{family}: {structural_mismatches}"
            )
        canonical_values[family] = family_values

    placeholder_mismatches: dict[str, dict[str, list[str]]] = {}
    for family in required_families:
        english_values = canonical_values[family]["english"]
        family_mismatches = {
            language: sorted(
                key
                for key, value in canonical_values[family][language].items()
                if value != english_values[key]
            )
            for language in PLACEHOLDER_LANGUAGES
        }
        family_mismatches = {
            language: keys
            for language, keys in family_mismatches.items()
            if keys
        }
        if family_mismatches:
            placeholder_mismatches[family] = family_mismatches
    placeholder_mismatches = {
        family: mismatches
        for family, mismatches in placeholder_mismatches.items()
        if mismatches
    }
    if placeholder_mismatches:
        raise freeze.FreezeError(
            "non-authored B3 localization must retain English placeholders: "
            f"{placeholder_mismatches}"
        )

    initial_missing: dict[str, set[str]] = {}
    updated_relatives: list[str] = []
    for family in required_families:
        for language in LOCALIZATION_LANGUAGES:
            relative = _localization_relative(family, language)
            source = canonical / relative
            target = candidate / relative
            target_has_bom = target.is_file() and target.read_bytes().startswith(BOM)
            values = _all_localization_values(target) if target_has_bom else {}
            missing = set(canonical_values[family][language]) - set(values)
            if missing:
                initial_missing.setdefault(language, set()).update(missing)
            if not target.is_file() or target.read_bytes() != source.read_bytes():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                updated_relatives.append(relative)

    final_missing: dict[str, set[str]] = {}
    final_values: dict[str, dict[str, dict[str, str]]] = {}
    provider_files_exact = True
    for family in required_families:
        family_values = {}
        for language in LOCALIZATION_LANGUAGES:
            relative = _localization_relative(family, language)
            source = canonical / relative
            target = candidate / relative
            values = _all_localization_values(target)
            missing = set(canonical_values[family][language]) - set(values)
            if missing:
                final_missing.setdefault(language, set()).update(missing)
            if target.read_bytes() != source.read_bytes():
                provider_files_exact = False
            family_values[language] = values
        final_values[family] = family_values
    placeholders_match = all(
        final_values[family][language].get(key)
        == final_values[family]["english"].get(key)
        for family in required_families
        for language in PLACEHOLDER_LANGUAGES
        for key in final_values[family]["english"]
    )
    final_missing_by_language = {
        language: sorted(keys) for language, keys in sorted(final_missing.items())
    }
    initial_missing_by_language = {
        language: sorted(keys) for language, keys in sorted(initial_missing.items())
    }
    provider_bytes = sum(int(record["bytes"]) for record in canonical_records)
    green = (
        not final_missing_by_language
        and placeholders_match
        and provider_files_exact
    )
    return {
        "green": green,
        "applicable": True,
        "required_families": required_families,
        "required_key_count": sum(
            len(canonical_values[family]["english"])
            for family in required_families
        ),
        "authored_languages": list(AUTHORED_LANGUAGES),
        "placeholder_languages": list(PLACEHOLDER_LANGUAGES),
        "initial_missing_by_language": initial_missing_by_language,
        "updated_files": [
            freeze.record(candidate / relative, relative_to=candidate)
            for relative in updated_relatives
        ],
        "final_missing_by_language": final_missing_by_language,
        "placeholder_values_match_english": placeholders_match,
        "provider_files_exact": provider_files_exact,
        "provider_file_count": len(canonical_records),
        "provider_bytes": provider_bytes,
        "provider_inventory_sha256": _provider_inventory_sha256(
            canonical_records
        ),
    }


def synchronize_b3_terminal_localization(
    candidate: Path, canonical: Path
) -> dict[str, object]:
    """Compatibility entry point; now closes all reachable B3 provider families."""

    return synchronize_b3_reachable_localization(candidate, canonical)


def synchronize_scripted_widget_gui_files(
    candidate: Path, canonical: Path
) -> dict[str, object]:
    """Close registered GUI files over their custom scripted-GUI providers."""

    registry_root = candidate / "gui" / "scripted_widgets"
    required = sorted(
        {
            match.group(1)
            for registry in registry_root.glob("*.txt")
            if registry.is_file()
            for match in SCRIPTED_WIDGET_REGISTRATION.finditer(
                registry.read_text(encoding="utf-8-sig")
            )
        }
    )
    updated: list[str] = []
    for relative in required:
        source = canonical / Path(*relative.split("/"))
        target = candidate / Path(*relative.split("/"))
        if not source.is_file():
            raise freeze.FreezeError(
                f"canonical scripted-widget GUI is missing: {relative}"
            )
        if not target.is_file() or target.read_bytes() != source.read_bytes():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            updated.append(relative)

    sys.path.insert(0, str(freeze.MOD_ROOT / "tools"))
    from zg361_effect_sharding import top_level_effect_entries

    providers: dict[str, str] = {}
    duplicate_providers: set[str] = set()
    provider_root = canonical / "common" / "scripted_guis"
    for path in sorted(provider_root.glob("*.txt"), key=lambda value: value.name):
        relative = path.relative_to(canonical).as_posix()
        try:
            entries = top_level_effect_entries(path.read_bytes())
        except ValueError:
            continue
        for entry in entries:
            if entry.name in providers:
                duplicate_providers.add(entry.name)
            providers[entry.name] = relative
    if duplicate_providers:
        raise freeze.FreezeError(
            "canonical scripted-GUI providers contain duplicate definitions: "
            f"{sorted(duplicate_providers)}"
        )

    referenced_names = {
        match.group("name")
        for relative in required
        for match in SCRIPTED_GUI_CALL.finditer(
            (candidate / Path(*relative.split("/"))).read_text(
                encoding="utf-8-sig"
            )
        )
        if match.group("name").startswith("zg361_")
    }
    provider_files: set[str] = set()
    scanned_names: set[str] = set()
    while referenced_names - scanned_names:
        name = sorted(referenced_names - scanned_names)[0]
        scanned_names.add(name)
        relative = providers.get(name)
        if relative is None:
            raise freeze.FreezeError(
                f"canonical custom scripted-GUI provider is missing: {name}"
            )
        if relative in provider_files:
            continue
        provider_files.add(relative)
        source = canonical / Path(*relative.split("/"))
        referenced_names.update(
            match.group("name")
            for match in SCRIPTED_GUI_CALL.finditer(
                source.read_text(encoding="utf-8-sig")
            )
            if match.group("name").startswith("zg361_")
        )

    for relative in sorted(provider_files):
        source = canonical / Path(*relative.split("/"))
        target = candidate / Path(*relative.split("/"))
        if not target.is_file() or target.read_bytes() != source.read_bytes():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            updated.append(relative)

    exact_gui_files = all(
        (candidate / Path(*relative.split("/"))).read_bytes()
        == (canonical / Path(*relative.split("/"))).read_bytes()
        for relative in required
    )
    exact_provider_files = all(
        (candidate / Path(*relative.split("/"))).read_bytes()
        == (canonical / Path(*relative.split("/"))).read_bytes()
        for relative in provider_files
    )
    exact = exact_gui_files and exact_provider_files
    return {
        "green": exact,
        "required_files": required,
        "required_file_count": len(required),
        "scripted_gui_names": sorted(referenced_names),
        "scripted_gui_provider_files": sorted(provider_files),
        "scripted_gui_provider_count": len(provider_files),
        "updated_files": [
            freeze.record(
                candidate / Path(*relative.split("/")), relative_to=candidate
            )
            for relative in updated
        ],
        "gui_files_exact": exact_gui_files,
        "scripted_gui_provider_files_exact": exact_provider_files,
        "provider_files_exact": exact,
    }


def synchronize_current_core_effect_shards(
    candidate: Path, canonical: Path
) -> dict[str, object]:
    """Replace the inherited B2 core shards with current canonical bodies.

    The B3 candidate inherits four purpose shards from the B2 seed closure.
    Merely expanding missing providers cannot detect a changed body whose
    definition name already exists in one of those shards.  Regenerate the
    same <=10-effect boundary from the canonical monolith before computing the
    B3 fixed point, so new cross-boundary calls become visible to the closure.
    """

    present = [relative for relative in CURRENT_CORE_SHARDS if (candidate / relative).is_file()]
    if not present:
        return {
            "green": True,
            "applicable": False,
            "source": None,
            "updated_files": [],
            "definition_count": 0,
            "max_effects_per_file": 0,
            "canonical_blocks_exact": True,
        }
    if tuple(present) != CURRENT_CORE_SHARDS:
        missing = [relative.as_posix() for relative in CURRENT_CORE_SHARDS if relative not in present]
        raise freeze.FreezeError(
            f"B3 current-core shard set is incomplete: missing={missing}"
        )

    source = canonical / CURRENT_CORE_SOURCE
    if not source.is_file() or source.is_symlink():
        raise freeze.FreezeError(f"canonical current-core owner is missing: {source}")
    sys.path.insert(0, str(freeze.MOD_ROOT / "tools"))
    from zg361_effect_sharding import top_level_effect_entries

    canonical_entries = top_level_effect_entries(source.read_bytes())
    canonical_by_name = {entry.name: entry for entry in canonical_entries}
    if len(canonical_by_name) != len(canonical_entries):
        raise freeze.FreezeError("canonical current-core owner has duplicate definitions")

    shard_names: dict[Path, tuple[str, ...]] = {}
    inherited_names: list[str] = []
    for relative in CURRENT_CORE_SHARDS:
        entries = top_level_effect_entries((candidate / relative).read_bytes())
        names = tuple(entry.name for entry in entries)
        if not 1 <= len(names) <= 10:
            raise freeze.FreezeError(
                f"B3 current-core shard violates the 1..10 boundary: {relative}: {len(names)}"
            )
        shard_names[relative] = names
        inherited_names.extend(names)
    if len(inherited_names) != len(set(inherited_names)):
        raise freeze.FreezeError("B3 current-core shards contain duplicate definitions")
    if set(inherited_names) != set(canonical_by_name):
        raise freeze.FreezeError(
            "B3 current-core shard union differs from the canonical current owner"
        )

    source_record = freeze.record(source, relative_to=canonical)
    updated: list[dict[str, object]] = []
    canonical_blocks_exact = True
    for relative in CURRENT_CORE_SHARDS:
        names = shard_names[relative]
        header = (
            "# GENERATED B3 CURRENT-CORE PROJECTION - DO NOT EDIT\n"
            f"# Source: {CURRENT_CORE_SOURCE.as_posix()}\n"
            f"# Source SHA-256: {source_record['sha256']}\n"
            f"# Purpose boundary: {relative.stem.removeprefix('zg361_core_')}\n\n"
        )
        body = "\n\n".join(canonical_by_name[name].block.strip() for name in names) + "\n"
        target = candidate / relative
        target.write_bytes(BOM + (header + body).encode("utf-8"))
        rendered = {
            entry.name: entry.block.strip()
            for entry in top_level_effect_entries(target.read_bytes())
        }
        canonical_blocks_exact = canonical_blocks_exact and all(
            rendered.get(name) == canonical_by_name[name].block.strip()
            for name in names
        )
        updated.append(freeze.record(target, relative_to=candidate))

    return {
        "green": canonical_blocks_exact,
        "applicable": True,
        "source": source_record,
        "updated_files": updated,
        "definition_count": len(inherited_names),
        "max_effects_per_file": max(len(names) for names in shard_names.values()),
        "canonical_blocks_exact": canonical_blocks_exact,
    }


def synchronize_selected_canonical_files(
    candidate: Path, canonical: Path
) -> dict[str, object]:
    """Refresh every selected same-path file from the current source tree.

    A fixed-point provider scan detects missing names, but cannot detect body
    drift in an already selected purpose shard.  The B3 projection is a
    current-source product, so same-path files must be byte-identical before
    resolving newly exposed dependencies.  The four core shards remain a
    separate monolith-to-shard projection because they have no canonical
    same-path owners.
    """

    selected: list[str] = []
    updated: list[str] = []
    for target in sorted(
        (path for path in candidate.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(candidate).as_posix(),
    ):
        relative_path = target.relative_to(candidate)
        source = canonical / relative_path
        if not source.is_file() or source.is_symlink():
            continue
        relative = relative_path.as_posix()
        selected.append(relative)
        if target.read_bytes() != source.read_bytes():
            shutil.copy2(source, target)
            updated.append(relative)
    exact = all(
        (candidate / Path(*relative.split("/"))).read_bytes()
        == (canonical / Path(*relative.split("/"))).read_bytes()
        for relative in selected
    )
    return {
        "green": exact,
        "selected_file_count": len(selected),
        "updated_files": [
            freeze.record(candidate / relative, relative_to=candidate)
            for relative in updated
        ],
        "provider_files_exact": exact,
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
    selected_canonical_files = synchronize_selected_canonical_files(
        candidate, canonical
    )
    current_core_effect_shards = synchronize_current_core_effect_shards(
        candidate, canonical
    )
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

    localization_closure = synchronize_b3_reachable_localization(
        candidate, canonical
    )
    scripted_widget_gui_closure = synchronize_scripted_widget_gui_files(
        candidate, canonical
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
        and selected_canonical_files["green"] is True
        and current_core_effect_shards["green"] is True
        and localization_closure["green"] is True
        and scripted_widget_gui_closure["green"] is True
    )
    evidence: dict[str, object] = {
        "schema_version": 3,
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
        "selected_canonical_files": selected_canonical_files,
        "current_core_effect_shards": current_core_effect_shards,
        "localization_closure": localization_closure,
        "scripted_widget_gui_closure": scripted_widget_gui_closure,
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

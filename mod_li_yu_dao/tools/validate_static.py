"""L0 Clausewitz AST, localization, references and player-entry checks.

The repository's structural Clausewitz parser is reused. This is not CK3's
runtime parser, scope type checker, DLC gate or a substitute for live evidence.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

from build_release import ROOT, SOURCE, collect_runtime_files, sha256

sys.path.insert(0, str(ROOT / "tools"))
from extract_auto_upgrade_buildings import Block, ExtractionError, parse_clausewitz

LOC_ROW = re.compile(r'^\s+([A-Za-z0-9_.-]+):[0-9]+\s+"((?:[^"\\]|\\.)*)"\s*(?:#.*)?$')
PLACEHOLDER = re.compile(r"\$[^$\r\n]+\$|\[[^\]\r\n]+\]")
LYD_ID = re.compile(r"(?:lyd_[A-Za-z0-9_]+|lyd\.[0-9]+)")
LOC_FIELDS = frozenset({"title", "desc", "name", "confirm_text", "selection_tooltip", "custom_tooltip", "text"})
META_FIELDS = frozenset({"namespace", "add_namespace"})


def walk(block: Block, ancestors: tuple[str, ...] = ()):
    for entry in block.entries:
        yield entry, ancestors
        if isinstance(entry.value, Block):
            yield from walk(entry.value, ancestors + (entry.key,))


def blocks(block: Block, key: str) -> list[Block]:
    return [entry.value for entry in block.entries if entry.key == key and isinstance(entry.value, Block)]


def scalar(block: Block, key: str) -> str | None:
    values = [entry.value for entry in block.entries if entry.key == key and isinstance(entry.value, str)]
    return values[0].strip('"') if len(values) == 1 else None


def player_guard(block: Block, triggers: dict[str, Block], seen: frozenset[str] = frozenset()) -> bool:
    """Prove a positive player conjunct in the current/root/actor scope.

    A guard under NOT, a target scope or only one branch of OR is insufficient.
    Parameterized or unusual gates are deliberately not guessed.
    """
    for entry in block.entries:
        if entry.key == "is_ai" and entry.operator == "=" and entry.value == "no":
            return True
        if entry.key in triggers and entry.value == "yes" and entry.key not in seen:
            if player_guard(triggers[entry.key], triggers, seen | {entry.key}):
                return True
        if isinstance(entry.value, Block):
            if entry.key in {"AND", "root", "scope:actor", "trigger", "limit"} and player_guard(entry.value, triggers, seen):
                return True
            if entry.key == "OR":
                branches = [candidate.value for candidate in entry.value.entries if isinstance(candidate.value, Block)]
                if branches and len(branches) == len(entry.value.entries) and all(player_guard(branch, triggers, seen) for branch in branches):
                    return True
    return False


def guarded_effect(block: Block, triggers: dict[str, Block], effects: dict[str, Block], seen: frozenset[str] = frozenset()) -> bool:
    """Every executable top-level branch must be guarded before it mutates."""
    executable = False
    for entry in block.entries:
        if entry.key in {"save_scope_as", "save_temporary_scope_as", "custom_tooltip"}:
            continue
        executable = True
        if entry.key == "if" and isinstance(entry.value, Block):
            limits = blocks(entry.value, "limit")
            if len(limits) == 1 and player_guard(limits[0], triggers):
                continue
        if entry.key in effects and entry.key not in seen:
            if guarded_effect(effects[entry.key], triggers, effects, seen | {entry.key}):
                continue
        return False
    return executable


def parse_localization(path: Path) -> dict[str, str]:
    data = path.read_bytes()
    if not data.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"localization needs UTF-8 BOM: {path.name}")
    lines = data.decode("utf-8-sig").splitlines()
    if not lines or lines[0] != f"l_{path.parent.name}:":
        raise ValueError(f"wrong language header: {path.name}")
    result: dict[str, str] = {}
    for number, line in enumerate(lines[1:], 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = LOC_ROW.fullmatch(line)
        if not match or match.group(1) in result:
            raise ValueError(f"invalid/duplicate localization at {path.name}:{number}")
        result[match.group(1)] = match.group(2)
    return result


def validate(source: Path = SOURCE) -> dict:
    errors: list[str] = []
    hashes: dict[str, str] = {}
    scripts: dict[str, Block] = {}
    localization: dict[str, dict[str, str]] = {"english": {}, "simp_chinese": {}}
    try:
        inventory = collect_runtime_files(source)
    except (OSError, ValueError) as error:
        return {"result": "RED", "layer": "L0-static", "errors": [str(error)], "live": "NOT_RUN"}
    for relative in inventory:
        path = source / relative
        try:
            data = path.read_bytes()
            hashes[relative] = sha256(data)
            if path.suffix in {".txt", ".mod"}:
                text = data.decode("utf-8-sig")
                scripts[relative] = parse_clausewitz(text)
            elif path.suffix == ".yml":
                language = path.parent.name
                values = parse_localization(path)
                duplicates = localization[language].keys() & values.keys()
                if duplicates:
                    errors.append(f"duplicate language keys: {language}: {sorted(duplicates)}")
                localization[language].update(values)
        except (UnicodeError, OSError, ValueError, ExtractionError) as error:
            errors.append(f"{relative}: {error}")
    english, chinese = localization["english"], localization["simp_chinese"]
    if english.keys() != chinese.keys():
        errors.append(f"localization keys differ: only English={sorted(english.keys() - chinese.keys())}; only Chinese={sorted(chinese.keys() - english.keys())}")
    for key in english.keys() & chinese.keys():
        if Counter(PLACEHOLDER.findall(english[key])) != Counter(PLACEHOLDER.findall(chinese[key])):
            errors.append(f"localization placeholder mismatch: {key}")
        for linked in re.findall(r"\$(lyd_[A-Za-z0-9_.]+)\$", english[key] + chinese[key]):
            if linked not in english or linked not in chinese:
                errors.append(f"unknown localization substitution: {key} -> {linked}")
    definitions: dict[str, dict[str, Block]] = {}
    events: dict[str, Block] = {}
    for relative, ast in scripts.items():
        category = relative.rsplit("/", 1)[0]
        bucket = definitions.setdefault(category, {})
        if relative == "descriptor.mod" or relative.startswith("history/"):
            continue
        for entry in ast.entries:
            if entry.key in META_FIELDS:
                if entry.value != "lyd":
                    errors.append(f"wrong event namespace: {relative}")
                continue
            if entry.operator != "=" or not isinstance(entry.value, Block):
                errors.append(f"invalid top-level definition: {relative}: {entry.key}")
                continue
            if relative.startswith("events/"):
                # CK3 declares event IDs as top-level keys, unlike CK2's
                # character_event = { id = ... is_triggered_only = yes } form.
                identifier = entry.key
                if not identifier or not re.fullmatch(r"lyd\.[0-9]+", identifier) or identifier in events:
                    errors.append(f"invalid/duplicate event ID: {identifier}")
                else:
                    events[identifier] = entry.value
                if scalar(entry.value, "type") != "character_event":
                    errors.append(f"unsupported event type in player response chain: {identifier}")
                if any(candidate.key in {"mean_time_to_happen", "is_triggered_only"} for candidate in entry.value.entries):
                    errors.append(f"CK2 event field is not a CK3 player-chain gate: {identifier}")
            elif entry.key in bucket:
                errors.append(f"duplicate definition: {category}: {entry.key}")
            else:
                bucket[entry.key] = entry.value
        if category == "common/scripted_effects" and len(ast.entries) > 10:
            errors.append(f"more than 10 scripted effects in {relative}")
    triggers = definitions.get("common/scripted_triggers", {})
    effects = definitions.get("common/scripted_effects", {})
    known_ids = {identifier for bucket in definitions.values() for identifier in bucket}
    tenets = definitions.get("common/religion/tenet_types", {})
    rites = definitions.get("common/religion/rite_types", {})
    for identifier in tenets:
        for suffix in ("_name", "_desc"):
            if identifier + suffix not in english:
                errors.append(f"unlocalized tenet: {identifier + suffix}")
    for identifier, rite in rites.items():
        core = blocks(rite, "tenets")
        if len(core) != 1 or len(core[0].entries) != 3 or len({entry.key for entry in core[0].entries}) != 3 or any(entry.operator is not None for entry in core[0].entries):
            errors.append(f"rite needs three distinct native tenets: {identifier}")
        elif any(entry.key.startswith(("lyd_", "tenet_lyd_")) and entry.key not in tenets for entry in core[0].entries):
            errors.append(f"rite references unknown LYD tenet: {identifier}")
    def called_nodes(block: Block) -> set[str]:
        result: set[str] = set()
        for entry, _ in walk(block):
            if entry.key in effects:
                result.add(entry.key)
            if isinstance(entry.value, str) and entry.key in {"trigger_event", "id"}:
                value = entry.value.strip('"')
                if re.fullmatch(r"lyd\.[0-9]+", value):
                    result.add(value)
        return result

    call_graph = {identifier: called_nodes(body) for identifier, body in effects.items()}
    call_graph.update({identifier: called_nodes(body) - {identifier} for identifier, body in events.items()})
    player_entries: set[str] = set()
    for relative, ast in scripts.items():
        runtime_flow = relative.startswith(("common/decisions/", "common/character_interactions/", "common/scripted_", "events/"))
        for entry, ancestors in walk(ast):
            if runtime_flow and entry.key.startswith("lyd_") and "parameters" not in ancestors and entry.key not in known_ids:
                errors.append(f"unresolved LYD helper/definition: {relative}: {entry.key}")
            if isinstance(entry.value, str):
                value = entry.value.strip('"')
                for kind, identifier in re.findall(r"\b(faith|rite|tenet):((?:lyd_|tenet_lyd_)[A-Za-z0-9_]+)", value):
                    if identifier not in known_ids:
                        errors.append(f"unresolved {kind} reference: {relative}: {identifier}")
                if entry.key in {"faith", "parent_faith", "main_rite", "rite", "core_tenet", "tenet", "rite_has_tenet"} and value.startswith(("lyd_", "tenet_lyd_")) and value not in known_ids:
                    errors.append(f"unresolved religious definition: {relative}: {value}")
                if entry.key in LOC_FIELDS and (value.startswith("lyd_") or value.startswith("lyd.")) and value not in english:
                    errors.append(f"unlocalized field: {relative}: {entry.key}={value}")
                if entry.key in {"trigger_event", "id"} and re.fullmatch(r"lyd\.[0-9]+", value):
                    if value not in events:
                        errors.append(f"unresolved event reference: {relative}: {value}")
    for identifier, decision in definitions.get("common/decisions", {}).items():
        gates = blocks(decision, "is_shown") + blocks(decision, "is_valid")
        if not any(player_guard(gate, triggers) for gate in gates):
            errors.append(f"decision lacks current actor player gate: {identifier}")
        active = blocks(decision, "effect")
        if len(active) != 1 or not guarded_effect(active[0], triggers, effects):
            errors.append(f"decision effect lacks executable player guard: {identifier}")
        elif active:
            player_entries.update(called_nodes(active[0]))
        if identifier not in english:
            errors.append(f"unlocalized decision: {identifier}")
    for identifier, interaction in definitions.get("common/character_interactions", {}).items():
        gates = blocks(interaction, "is_shown") + blocks(interaction, "is_valid_showing_failures_only")
        actor_gates = [actor for gate in gates for actor in blocks(gate, "scope:actor")]
        if not any(player_guard(gate, triggers) for gate in actor_gates):
            errors.append(f"interaction lacks explicit actor player gate: {identifier}")
        else:
            for key in ("on_send", "on_accept", "on_decline", "on_auto_accept"):
                for branch in blocks(interaction, key):
                    player_entries.update(called_nodes(branch))
        if identifier not in english:
            errors.append(f"unlocalized interaction: {identifier}")
    reachable = set(player_entries)
    while True:
        expanded = reachable | {target for identifier in reachable for target in call_graph.get(identifier, set())}
        if expanded == reachable:
            break
        reachable = expanded
    for identifier in events.keys() - reachable:
        errors.append(f"event has no static path from player-triggered entries/helpers: {identifier}")
    return {"result": "RED" if errors else "GREEN", "layer": "L0-static", "errors": sorted(set(errors)), "runtime_file_count": len(inventory), "runtime_sha256": hashes, "localization_key_count": len(english), "event_count": len(events), "parser": "repository Clausewitz structural AST", "live": "NOT_RUN", "not_proven": ["native scope/effect semantics", "faith/rite migration", "authorization consent", "NPC chain state", "DLC/UI", "save reload", "installed-game identity"]}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = validate(args.source.resolve())
    if args.report:
        if args.report.exists():
            parser.error("report already exists; choose a fresh attempt")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())

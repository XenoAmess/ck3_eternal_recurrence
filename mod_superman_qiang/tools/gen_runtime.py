"""Generate runtime scripts and pinned, narrowly scoped vanilla projections."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import struct
from typing import Literal

from product import LANGUAGES

from runtime_data import (EN, ENCOUNTER_EVENT_OVERRIDE_PRIORITY, ENCOUNTER_SOURCE_SCHEMA,
                          EXE_SHA256, GAME_VERSION, HEALTH_DONOR_MINIMUM,
                          HEALTH_TRANSFER_AMOUNT, HOOKS, MINIMUM_AGE,
                          ROMANCE_SOURCE_SHA256, SEX_EXPERIENCE_MAXIMUM,
                          SEX_EXPERIENCE_VARIABLE, SKILL_BALANCE_MAXIMUM, SKILLS,
                          TRANSFER_ATTRIBUTES, ZH)

MOD_ROOT = Path(__file__).resolve().parents[1]
PINNED_ROOT = Path(__file__).resolve().parent / "vanilla_hooks"
UI_LOCALIZATION_SOURCE = Path(__file__).resolve().parent / "ui_localization.json"
HEADER = "# GENERATED FILE - do not edit. Regenerate with tools/gen_runtime.py\n"
INSERT_BEGIN = "\t# SXAD_HOOK_BEGIN\n"
INSERT_END = "\t# SXAD_HOOK_END\n"
ENCOUNTER_SOURCES = PINNED_ROOT / "encounter_sources.json"
RUNTIME_TEMPLATE_ROOT = Path(__file__).resolve().parent / "runtime_templates"
NATURAL_TEMPLATES = (
    ("sxad_natural_on_actions.txt", "common/on_action/sxad_natural_on_actions.txt"),
    ("sxad_natural_events.txt", "events/sxad_natural_events.txt"),
    ("sxad_natural_effects.txt", "common/scripted_effects/sxad_natural_effects.txt"),
    ("sxad_natural_values.txt", "common/script_values/sxad_natural_values.txt"),
)
DEFAULT_GAME_ROOT = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III")


@dataclass(frozen=True)
class EncounterInsertion:
    anchor: str
    position: Literal["before", "after"]
    text: str
    expected_count: int


@dataclass(frozen=True)
class InlineHelper:
    name: str
    kind: Literal["trigger", "effect"]
    source_path: str
    source_sha256: str
    pinned_file: str
    pinned_sha256: str


@dataclass(frozen=True)
class EncounterProjection:
    name: str
    kind: Literal["scripted_effect", "event"]
    source_path: str
    source_sha256: str
    pinned_file: str
    pinned_sha256: str
    namespace: str | None
    output: str
    insertions: tuple[EncounterInsertion, ...]
    event_override_priority: int | None
    inline_dependencies: tuple[InlineHelper, ...]
    inline_inventory: tuple[str, ...]


@dataclass(frozen=True)
class ScriptToken:
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class InlineExpansion:
    original: str
    expanded: str


@dataclass(frozen=True)
class InlineSourceDeclaration:
    name: str
    kind: Literal["trigger", "effect"]
    keyword_start: int
    name_start: int


def required_fields(value: object, keys: frozenset[str], context: str) -> dict[str, object]:
    """Validate a JSON object before exposing its fields to the generator."""
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{context}: expected object with string keys")
    result: dict[str, object] = {key: item for key, item in value.items()}
    if result.keys() != keys:
        raise ValueError(f"{context}: incorrect fields: {sorted(result)}")
    return result


def required_string(value: object, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context}: expected nonempty string")
    return value


def required_sha256(value: object, context: str) -> str:
    result = required_string(value, context)
    if re.fullmatch(r"[0-9a-f]{64}", result) is None:
        raise ValueError(f"{context}: invalid SHA-256")
    return result


def relative_path(value: object, context: str) -> str:
    result = required_string(value, context)
    if "\\" in result or result.startswith("/") or ":" in result or any(part in {"", ".", ".."} for part in result.split("/")):
        raise ValueError(f"{context}: expected contained relative path")
    return result


def load_encounter_projections(path: Path = ENCOUNTER_SOURCES) -> tuple[EncounterProjection, ...]:
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    document = required_fields(raw, frozenset({"schema", "game_version", "source_buildid", "machine_id", "observed_at_utc", "exe_sha256", "projections", "inline_sources", "inline_helpers"}), "encounter sources")
    if document["schema"] != ENCOUNTER_SOURCE_SCHEMA or document["game_version"] != GAME_VERSION or document["exe_sha256"] != EXE_SHA256:
        raise ValueError("Encounter source contract differs from reviewed game identity")
    for key in ("machine_id", "observed_at_utc", "source_buildid"):
        required_string(document[key], key)
    build_id = required_string(document["source_buildid"], "source_buildid")
    if re.fullmatch(r"[1-9][0-9]*", build_id) is None:
        raise ValueError("source_buildid must be a canonical decimal string")
    indexes_raw = document["inline_sources"]
    if not isinstance(indexes_raw, list) or not indexes_raw:
        raise ValueError("inline_sources must be a nonempty JSON array")
    indexes: dict[str, tuple[str, tuple[str, ...]]] = {}
    for index_raw in indexes_raw:
        index = required_fields(index_raw, frozenset({"source_path", "source_sha256", "declared_names"}), "inline source index")
        source_path = relative_path(index["source_path"], "inline source path")
        if source_path in indexes:
            raise ValueError("Repeated inline source index")
        names = identifier_array(index["declared_names"], "inline declared names")
        indexes[source_path] = (required_sha256(index["source_sha256"], "inline source SHA"), names)
    helpers_raw = document["inline_helpers"]
    if not isinstance(helpers_raw, list):
        raise ValueError("inline_helpers must be a JSON array")
    helpers: dict[str, InlineHelper] = {}
    helper_pins: set[str] = set()
    for helper_raw in helpers_raw:
        helper = required_fields(helper_raw, frozenset({"name", "kind", "source_path", "source_sha256", "pinned_file", "pinned_sha256"}), "inline helper")
        name = required_identifier(helper["name"], "inline helper name")
        kind = helper["kind"]
        if not isinstance(kind, str) or kind not in {"trigger", "effect"}:
            raise ValueError("Inline helper kind must be trigger or effect")
        source_path = relative_path(helper["source_path"], "inline helper source")
        source_sha = required_sha256(helper["source_sha256"], "inline helper source SHA")
        pinned = relative_path(helper["pinned_file"], "inline helper pin")
        if pinned != f"inline_{name}.txt" or name in helpers or pinned in helper_pins:
            raise ValueError("Invalid or repeated inline helper pin")
        if source_path not in indexes or indexes[source_path][0] != source_sha or name not in indexes[source_path][1]:
            raise ValueError("Inline helper differs from its source declaration index")
        helpers[name] = InlineHelper(name, "trigger" if kind == "trigger" else "effect", source_path, source_sha, pinned,
                                     required_sha256(helper["pinned_sha256"], "inline helper pin SHA"))
        helper_pins.add(pinned)
    rows = document["projections"]
    if not isinstance(rows, list):
        raise ValueError("projections must be a JSON array")
    result: list[EncounterProjection] = []
    seen_names: set[str] = set()
    seen_outputs: set[str] = set()
    seen_pins: set[str] = set()
    source_hashes: dict[str, str] = {}
    for row in rows:
        entry = required_fields(row, frozenset({"name", "kind", "source_path", "source_sha256", "pinned_file", "pinned_sha256", "namespace", "output", "insertions", "event_override_priority", "inline_dependencies"}), "encounter projection")
        name = required_string(entry["name"], "name")
        if re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*(?:\.[0-9]+)?", name) is None:
            raise ValueError("Invalid encounter definition name")
        kind = entry["kind"]
        if not isinstance(kind, str) or kind not in {"scripted_effect", "event"}:
            raise ValueError(f"Invalid encounter projection kind: {kind}")
        namespace = entry["namespace"]
        if namespace is not None and (not isinstance(namespace, str) or re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", namespace) is None):
            raise ValueError("namespace must be a valid name or null")
        if (kind == "event") != (namespace is not None):
            raise ValueError("Only event projections require a namespace")
        if kind == "event" and name.split(".")[0] != namespace:
            raise ValueError("Event namespace does not match its definition name")
        output = relative_path(entry["output"], "output")
        prefix = "events/" if kind == "event" else "common/scripted_effects/"
        if not output.startswith(prefix) or not output.endswith(".txt"):
            raise ValueError("Projection output does not match its definition kind")
        pinned = relative_path(entry["pinned_file"], "pinned_file")
        if "/" in pinned:
            raise ValueError("Pinned definition must be a direct vanilla_hooks child")
        insertions = entry["insertions"]
        if not isinstance(insertions, list) or not insertions:
            raise ValueError("insertions must be a nonempty JSON array")
        parsed: list[EncounterInsertion] = []
        for raw_insertion in insertions:
            item = required_fields(raw_insertion, frozenset({"anchor", "position", "text", "expected_count"}), "encounter insertion")
            position = item["position"]
            if not isinstance(position, str) or position not in {"before", "after"}:
                raise ValueError("Insertion position must be before or after")
            count = item["expected_count"]
            if type(count) is not int or count != 1:
                raise ValueError("Insertion expected_count must be integer 1")
            insertion_text = required_string(item["text"], "text")
            if "SXAD_HOOK_BEGIN" in insertion_text or "SXAD_HOOK_END" in insertion_text:
                raise ValueError("Insertion text may not supply its own boundary markers")
            parsed.append(EncounterInsertion(required_string(item["anchor"], "anchor"), "before" if position == "before" else "after", insertion_text, count))
        if name in seen_names or output in seen_outputs or pinned in seen_pins or pinned in helper_pins:
            raise ValueError("Repeated encounter definition name, output or pinned file")
        seen_names.add(name)
        seen_outputs.add(output)
        seen_pins.add(pinned)
        source_path = relative_path(entry["source_path"], "source_path")
        source_sha = required_sha256(entry["source_sha256"], "source_sha256")
        if source_path in source_hashes and source_hashes[source_path] != source_sha:
            raise ValueError("One source file has conflicting source identities")
        source_hashes[source_path] = source_sha
        priority = entry["event_override_priority"]
        if (kind == "event" and (type(priority) is not int or priority != ENCOUNTER_EVENT_OVERRIDE_PRIORITY)) or (kind != "event" and priority is not None):
            raise ValueError("Event projections require integer override priority 1; effects require null")
        dependencies = identifier_array(entry["inline_dependencies"], "inline dependencies")
        if source_path not in indexes or indexes[source_path][0] != source_sha:
            raise ValueError("Projection source differs from its inline declaration index")
        selected_helpers: list[InlineHelper] = []
        for dependency in dependencies:
            if dependency not in helpers or helpers[dependency].source_path != source_path:
                raise ValueError("Missing or foreign-file inline helper dependency")
            selected_helpers.append(helpers[dependency])
        result.append(EncounterProjection(name, "event" if kind == "event" else "scripted_effect", source_path, source_sha, pinned, required_sha256(entry["pinned_sha256"], "pinned_sha256"), namespace, output, tuple(parsed),
                                          ENCOUNTER_EVENT_OVERRIDE_PRIORITY if kind == "event" else None, tuple(selected_helpers), indexes[source_path][1]))
    used_helpers = {helper.name for projection in result for helper in projection.inline_dependencies}
    if used_helpers != helpers.keys():
        raise ValueError("Unused inline helper metadata must not be retained")
    if source_hashes.keys() != indexes.keys():
        raise ValueError("Inline source inventory must exactly match projected source files")
    return tuple(result)


def required_identifier(value: object, context: str) -> str:
    result = required_string(value, context)
    if re.fullmatch(r"[A-Za-z_0-9]+", result) is None:
        raise ValueError(f"{context}: invalid script identifier")
    return result


def identifier_array(value: object, context: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{context}: expected JSON array")
    result = tuple(required_identifier(item, context) for item in value)
    if len(set(result)) != len(result):
        raise ValueError(f"{context}: repeated identifier")
    return result


def script_tokens(source: str) -> tuple[ScriptToken, ...]:
    """Locate executable identifiers without matching comments or quoted text."""
    pattern = r'"(?:\\.|[^"\\])*"|\#[^\n]*|[{}=]|[^\s{}=]+'
    return tuple(ScriptToken(match.group(), match.start(), match.end())
                 for match in re.finditer(pattern, source)
                 if not match.group().startswith(('#', '"')))


def inline_source_declarations(source: str) -> tuple[InlineSourceDeclaration, ...]:
    """Read every real file-local declaration, ignoring quoted/comment text."""
    tokens = script_tokens(source)
    result: list[InlineSourceDeclaration] = []
    depth = 0
    for index, token in enumerate(tokens):
        if depth == 0 and token.text in {"scripted_trigger", "scripted_effect"}:
            if index + 3 >= len(tokens) or tokens[index + 2].text != "=" or tokens[index + 3].text != "{":
                raise ValueError("Malformed file-local helper declaration in source")
            name = required_identifier(tokens[index + 1].text, "source inline helper name")
            result.append(InlineSourceDeclaration(name, "trigger" if token.text == "scripted_trigger" else "effect",
                                                  token.start, tokens[index + 1].start))
        if token.text == "{":
            depth += 1
        elif token.text == "}":
            depth -= 1
            if depth < 0:
                raise ValueError("Unmatched closing brace in inline source")
    if depth:
        raise ValueError("Unclosed brace in inline source")
    return tuple(result)


def extract_inline_definition(source: str, helper: InlineHelper) -> str:
    """Extract the exact reviewed definition, including its local declaration."""
    declarations = [item for item in inline_source_declarations(source)
                    if item.name == helper.name and item.kind == helper.kind]
    if len(declarations) != 1:
        raise ValueError(f"Expected exactly one source inline definition: {helper.name}")
    declaration = declarations[0]
    return (source[declaration.keyword_start:declaration.name_start]
            + extract_effect(source[declaration.name_start:], helper.name))


def verify_encounter_source_bindings(game_root: Path) -> None:
    """Bind snapshot bytes and the complete local-name inventory to source files.

    Updating a snapshot hash in metadata cannot relabel another definition as
    coming from an otherwise unchanged reviewed source file. A game directory
    or the installation containing that directory is accepted explicitly.
    """
    native_root = game_root / "game" if (game_root / "game").is_dir() else game_root
    sources: dict[str, tuple[str, str, tuple[str, ...]]] = {}
    verified_helpers: set[InlineHelper] = set()
    for projection in load_encounter_projections():
        if projection.source_path not in sources:
            raw = (native_root / projection.source_path).read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if digest != projection.source_sha256:
                raise ValueError(f"Installed source SHA differs: {projection.source_path}")
            source = raw.decode("utf-8-sig").replace("\r\n", "\n")
            inventory = tuple(item.name for item in inline_source_declarations(source))
            sources[projection.source_path] = (digest, source, inventory)
        digest, source, inventory = sources[projection.source_path]
        if digest != projection.source_sha256:
            raise ValueError(f"Conflicting installed source identity: {projection.source_path}")
        if inventory != projection.inline_inventory:
            raise ValueError(f"Complete inline inventory differs from source: {projection.source_path}")
        original = pinned_encounter_source(projection)
        expected = encode(extract_effect(source, projection.name))
        if (PINNED_ROOT / projection.pinned_file).read_bytes() != expected or encode(original) != expected:
            raise ValueError(f"Selected snapshot differs from installed source definition: {projection.name}")
        # Retain the existing SHA/header/one-definition guards as well as the
        # new provenance check; neither one replaces the other.
        inline_helper_bodies(projection)
        for helper in projection.inline_dependencies:
            if helper in verified_helpers:
                continue
            if helper.source_path != projection.source_path or helper.source_sha256 != digest:
                raise ValueError(f"Inline helper source binding differs: {helper.name}")
            expected_inline = encode(extract_inline_definition(source, helper))
            if (PINNED_ROOT / helper.pinned_file).read_bytes() != expected_inline:
                raise ValueError(f"Inline snapshot differs from installed source definition: {helper.name}")
            verified_helpers.add(helper)


def pinned_encounter_source(projection: EncounterProjection) -> str:
    raw = (PINNED_ROOT / projection.pinned_file).read_bytes()
    if hashlib.sha256(raw).hexdigest() != projection.pinned_sha256:
        raise ValueError(f"Pinned encounter definition changed: {projection.name}")
    original = raw.decode("utf-8-sig").replace("\r\n", "\n")
    if extract_effect(original, projection.name) != original:
        raise ValueError(f"Pinned file must contain exactly one definition: {projection.name}")
    return original


def inline_helper_bodies(projection: EncounterProjection) -> dict[str, tuple[InlineHelper, str]]:
    result: dict[str, tuple[InlineHelper, str]] = {}
    for helper in projection.inline_dependencies:
        raw = (PINNED_ROOT / helper.pinned_file).read_bytes()
        if hashlib.sha256(raw).hexdigest() != helper.pinned_sha256:
            raise ValueError(f"Pinned inline helper changed: {helper.name}")
        definition = raw.decode("utf-8-sig").replace("\r\n", "\n")
        header = re.match(rf"scripted_{helper.kind}\s+({re.escape(helper.name)})\s*=\s*\{{", definition)
        if header is None or extract_effect(definition[header.start(1):], helper.name) != definition[header.start(1):]:
            raise ValueError(f"Inline helper pin is not exactly one reviewed definition: {helper.name}")
        result[helper.name] = (helper, definition[definition.index("{") + 1:definition.rindex("}")])
    return result


def expand_inline_helpers(source: str, projection: EncounterProjection) -> tuple[str, tuple[InlineExpansion, ...]]:
    """Inline file-local calls without introducing a new character scope.

    Trigger bodies remain one AND operand even inside OR/NOT. Effects retain
    their original visibility and order. Only reviewed scalar yes/no calls are
    accepted; parameter macros, cycles and incomplete dependency closures fail.
    """
    bodies = inline_helper_bodies(projection)
    inventory = frozenset(projection.inline_inventory)
    used: set[str] = set()
    expansions: list[InlineExpansion] = []

    def expand(text: str, chain: tuple[str, ...]) -> str:
        tokens = script_tokens(text)
        replacements: list[tuple[int, int, str]] = []
        for index, token in enumerate(tokens):
            if token.text not in inventory or index + 1 >= len(tokens) or tokens[index + 1].text != "=":
                continue
            if token.text not in bodies:
                raise ValueError(f"Missing inline dependency: {token.text}")
            if token.text in chain:
                raise ValueError(f"Cyclic inline dependency: {chain + (token.text,)}")
            if index + 2 >= len(tokens):
                raise ValueError(f"Missing inline call value: {token.text}")
            value = tokens[index + 2]
            helper, body = bodies[token.text]
            if value.text not in {"yes", "no"} or (helper.kind == "effect" and value.text != "yes"):
                raise ValueError(f"Unsupported inline call arguments: {token.text}")
            if "$" in body:
                raise ValueError(f"Inline helper macros require explicit reviewed substitution: {token.text}")
            used.add(helper.name)
            expanded_body = expand(body, chain + (helper.name,))
            wrapped = ("AND = {" + expanded_body + "}") if helper.kind == "trigger" else expanded_body
            if value.text == "no":
                wrapped = "NOT = { " + wrapped + " }"
            original = text[token.start:value.end]
            identity = hashlib.sha256(original.encode("utf-8")).hexdigest()
            rendered = (f"\n# SXAD_INLINE_BEGIN {helper.name} {identity}\n" + wrapped
                        + f"\n# SXAD_INLINE_END {helper.name} {identity}\n")
            expansions.append(InlineExpansion(original, rendered))
            replacements.append((token.start, value.end, rendered))
        for start, end, replacement in reversed(replacements):
            text = text[:start] + replacement + text[end:]
        return text

    expanded = expand(source, ())
    if used != bodies.keys():
        raise ValueError(f"Inline dependency closure has unused members: {sorted(bodies.keys() - used)}")
    return expanded, tuple(expansions)


def encounter_header(projection: EncounterProjection) -> str:
    namespace = "" if projection.namespace is None else f"namespace = {projection.namespace}\n\n"
    return HEADER + f"# Controlled CK3 {GAME_VERSION} encounter projection.\n" + namespace


def restore_encounter_source(projection: EncounterProjection, source: str) -> tuple[str, tuple[str, ...]]:
    """Validate canonical stock expansion, then physically reverse every call."""
    original = pinned_encounter_source(projection)
    expected_stock, expansions = expand_inline_helpers(original, projection)
    pattern = r"(?ms)^\t# SXAD_HOOK_BEGIN\n(.*?)^\t# SXAD_HOOK_END\n"
    additions = tuple(re.findall(pattern, source))
    expected_count = len(projection.insertions) + int(projection.kind == "event")
    if len(additions) != expected_count:
        raise ValueError(f"Encounter insertion boundaries changed: {projection.name}")
    stripped = re.sub(pattern, "", source)
    expected = encounter_header(projection) + expected_stock
    if stripped != expected:
        raise ValueError(f"Stock encounter body changed: {projection.name}")
    if projection.kind == "event":
        priority = f"\tid_override_priority = {projection.event_override_priority}\n"
        if additions.count(priority) != 1:
            raise ValueError(f"Event override priority changed: {projection.name}")
    restored = stripped[len(encounter_header(projection)):]
    for expansion in sorted(expansions, key=lambda item: len(item.expanded), reverse=True):
        restored = restored.replace(expansion.expanded, expansion.original)
    if restored != original:
        raise ValueError(f"Inline encounter expansion cannot restore its exact source: {projection.name}")
    return restored, additions


def encounter_hook_outputs() -> dict[str, bytes]:
    """Apply reviewed insertions, local-helper expansion and event precedence."""
    outputs: dict[str, bytes] = {}
    for projection in load_encounter_projections():
        original = pinned_encounter_source(projection)
        pending: list[tuple[int, str]] = []
        for insertion in projection.insertions:
            if original.count(insertion.anchor) != insertion.expected_count:
                raise ValueError(f"Ambiguous encounter insertion: {projection.name}")
            offset = original.index(insertion.anchor)
            if insertion.position == "after":
                offset += len(insertion.anchor)
            pending.append((offset, INSERT_BEGIN + insertion.text.rstrip("\n") + "\n" + INSERT_END))
        if projection.kind == "event":
            if any(token.text == "id_override_priority" for token in script_tokens(original)):
                raise ValueError("Reviewed stock event already defines an override priority")
            pending.append((original.index("\n") + 1, INSERT_BEGIN + f"\tid_override_priority = {projection.event_override_priority}\n" + INSERT_END))
        if len({offset for offset, _ in pending}) != len(pending):
            raise ValueError("Encounter insertion boundaries overlap")
        projected = original
        for offset, block in sorted(pending, reverse=True):
            projected = projected[:offset] + block + projected[offset:]
        projected, _ = expand_inline_helpers(projected, projection)
        rendered = encounter_header(projection) + projected
        restore_encounter_source(projection, rendered)
        outputs[projection.output] = encode(rendered)
    return outputs


def encounter_owned_code(relative: str, source: str) -> str:
    """Keep canonical expanded stock immutable; inspect every added mod effect."""
    projection = next((entry for entry in load_encounter_projections() if entry.output == relative), None)
    if projection is None:
        return source
    _, additions = restore_encounter_source(projection, source)
    return "\n".join(additions)


def natural_simulation_outputs() -> dict[str, bytes]:
    outputs: dict[str, bytes] = {}
    for filename, relative in NATURAL_TEMPLATES:
        body = (RUNTIME_TEMPLATE_ROOT / filename).read_text(encoding="utf-8-sig")
        outputs[relative] = encode(body if body.startswith(HEADER) else HEADER + body)
    return outputs


def encode(text: str) -> bytes:
    return text.replace("\r\n", "\n").encode("utf-8-sig")


def extract_effect(source: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}\s*=\s*\{{", source)
    if match is None:
        raise ValueError(f"Vanilla hook not found: {name}")
    start = match.start()
    depth = 0
    quoted = comment = escaped = False
    for pos in range(source.index("{", start), len(source)):
        char = source[pos]
        if comment:
            comment = char != "\n"
            continue
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == "#":
            comment = True
        elif char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start:pos + 1].replace("\r\n", "\n") + "\n"
    raise ValueError(f"Unbalanced vanilla hook: {name}")


def refresh_vanilla(game_root: Path) -> None:
    source_path = game_root / "game/common/scripted_effects/00_romance_effects.txt"
    raw = source_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ROMANCE_SOURCE_SHA256:
        raise ValueError("Refusing non-pinned romance source; review a new game version first")
    source = raw.decode("utf-8-sig").replace("\r\n", "\n")
    PINNED_ROOT.mkdir(parents=True, exist_ok=True)
    entries = {}
    for name in HOOKS:
        body = encode(extract_effect(source, name))
        (PINNED_ROOT / f"{name}.txt").write_bytes(body)
        entries[name] = hashlib.sha256(body).hexdigest()
    metadata = {"game_version": GAME_VERSION, "exe_sha256": EXE_SHA256,
                "romance_source_sha256": ROMANCE_SOURCE_SHA256, "hooks": entries}
    (PINNED_ROOT / "sources.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def hook_outputs() -> dict[str, bytes]:
    raw_metadata: object = json.loads((PINNED_ROOT / "sources.json").read_text(encoding="utf-8"))
    metadata = required_fields(raw_metadata, frozenset({"game_version", "exe_sha256", "romance_source_sha256", "hooks"}), "paired/unknown hook sources")
    if metadata["romance_source_sha256"] != ROMANCE_SOURCE_SHA256 or metadata["game_version"] != GAME_VERSION or metadata["exe_sha256"] != EXE_SHA256:
        raise ValueError("Pinned romance identity differs from runtime_data")
    hashes = required_fields(metadata["hooks"], frozenset(HOOKS), "hook SHA registry")
    outputs: dict[str, bytes] = {}
    for name, helper in HOOKS.items():
        raw = (PINNED_ROOT / f"{name}.txt").read_bytes()
        if hashlib.sha256(raw).hexdigest() != required_sha256(hashes[name], name):
            raise ValueError(f"Pinned vanilla hook bytes changed: {name}")
        original = raw.decode("utf-8-sig")
        if extract_effect(original, name) != original:
            raise ValueError(f"Pinned input must contain exactly one hook: {name}")
        insertion = INSERT_BEGIN + f"\thidden_effect = {{ {helper} }}\n" + INSERT_END
        # Paired hook needs the two vanilla saved scopes; unknown hook has no partner.
        if name == "had_sex_with_effect":
            anchor = "\t$CHARACTER$ = { save_scope_as = had_sex_with_effect_partner }\n"
            if original.count(anchor) != 1:
                raise ValueError("Paired hook anchor changed")
            projected = original.replace(anchor, anchor + insertion, 1)
        else:
            projected = original.replace("had_sex_with_unknown_effect = {\n",
                                         "had_sex_with_unknown_effect = {\n" + insertion, 1)
        outputs[f"common/scripted_effects/zz_sxad_{name}.txt"] = encode(
            HEADER + f"# Controlled CK3 {GAME_VERSION} projection; strip SXAD_HOOK block to recover pinned input.\n" + projected)
    return outputs


def experience_effects() -> str:
    var = SEX_EXPERIENCE_VARIABLE
    return HEADER + f"""
# Current scope is a living, eligible participant. No experience query writes state.
sxad_increment_experience_effect = {{
    if = {{
        limit = {{ has_variable = {var} }}
        if = {{
            limit = {{ var:{var} < {SEX_EXPERIENCE_MAXIMUM} }}
            change_variable = {{ name = {var} add = 1 }}
        }}
    }}
    else = {{ set_variable = {{ name = {var} value = 1 }} }}
    if = {{
        limit = {{ NOT = {{ has_trait = sxad_sex_experience }} }}
        add_trait = sxad_sex_experience
    }}
}}

# The vanilla paired hook runs this once, before changing either experience count.
sxad_record_pair_effect = {{
    if = {{
        limit = {{
            is_alive = yes age >= {MINIMUM_AGE}
            NOT = {{ exists = scope:sxad_skip_pair_record }}
        }}
        if = {{
            limit = {{ exists = $PARTNER$ }}
            if = {{
                limit = {{
                    $PARTNER$ = {{ is_alive = yes age >= {MINIMUM_AGE} }}
                    NOT = {{ this = $PARTNER$ }}
                }}
                save_temporary_scope_as = sxad_first
                $PARTNER$ = {{ save_temporary_scope_as = sxad_second }}
                if = {{
                    limit = {{ has_variable = {var} }}
                    if = {{
                        limit = {{ $PARTNER$ = {{ has_variable = {var} }} }}
                        if = {{
                            limit = {{ var:{var} > scope:sxad_second.var:{var} }}
                            sxad_select_transfer_effect = {{ DONOR = scope:sxad_second }}
                        }}
                        else_if = {{
                            limit = {{ var:{var} < scope:sxad_second.var:{var} }}
                            scope:sxad_second = {{ sxad_select_transfer_effect = {{ DONOR = scope:sxad_first }} }}
                        }}
                    }}
                    else_if = {{
                        limit = {{ var:{var} > 0 }}
                        sxad_select_transfer_effect = {{ DONOR = scope:sxad_second }}
                    }}
                }}
                else_if = {{
                    limit = {{ $PARTNER$ = {{ has_variable = {var} }} }}
                    if = {{
                        limit = {{ scope:sxad_second = {{ var:{var} > 0 }} }}
                        scope:sxad_second = {{ sxad_select_transfer_effect = {{ DONOR = scope:sxad_first }} }}
                    }}
                }}
                sxad_increment_experience_effect = yes
                scope:sxad_second = {{ sxad_increment_experience_effect = yes }}
            }}
        }}
    }}
}}

# Vanilla explicitly describes this partner as not an actual character.
sxad_record_unknown_effect = {{
    if = {{
        limit = {{
            is_alive = yes age >= {MINIMUM_AGE}
            NOT = {{ exists = scope:sxad_skip_unknown_record }}
        }}
        sxad_increment_experience_effect = yes
    }}
}}
"""


def scoped_compare(value_name: str, expression: str) -> str:
    # Tooltip simulation may not materialize preceding temporary values.
    return (f"trigger_if = {{ limit = {{ exists = scope:{value_name} }} {expression} }}\n"
            "trigger_else = { always = no }")


def probe_effects() -> str:
    chunks = [HEADER, "# Eligibility checks only read character skills/balances and set temporary flags.\n",
              "# Transfer balances are original modifier points; base skills and health are never changed.\n"]
    for skill in TRANSFER_ATTRIBUTES:
        balance = f"sxad_{skill}_balance"
        if skill == "health":
            receiver_upper = f"<= {SKILL_BALANCE_MAXIMUM - HEALTH_TRANSFER_AMOUNT}"
            donor_lower = f">= {-SKILL_BALANCE_MAXIMUM + HEALTH_TRANSFER_AMOUNT}"
            donor_available = f"health >= {HEALTH_DONOR_MINIMUM}"
        else:
            receiver_upper = f"< {SKILL_BALANCE_MAXIMUM}"
            donor_lower = f"> -{SKILL_BALANCE_MAXIMUM}"
            donor_available = f"{skill} > 0"
        chunks.append(f"""
sxad_probe_{skill}_effect = {{
    save_temporary_scope_value_as = {{ name = sxad_can_{skill} value = 0 }}
    if = {{
        limit = {{
            trigger_if = {{
                limit = {{ has_variable = {balance} }}
                var:{balance} >= -{SKILL_BALANCE_MAXIMUM}
                var:{balance} {receiver_upper}
            }}
            trigger_else = {{ always = yes }}
            scope:sxad_donor = {{
                {donor_available}
                trigger_if = {{
                    limit = {{ has_variable = {balance} }}
                    var:{balance} {donor_lower}
                    var:{balance} <= {SKILL_BALANCE_MAXIMUM}
                }}
                trigger_else = {{ always = yes }}
            }}
        }}
        save_temporary_scope_value_as = {{ name = sxad_can_{skill} value = 1 }}
    }}
}}

# Current character owns the signed balance. Scale is sampled when assigned.
sxad_rebuild_{skill}_modifier_effect = {{
    remove_character_modifier = sxad_{skill}_gain_modifier
    remove_character_modifier = sxad_{skill}_loss_modifier
    if = {{
        limit = {{ has_variable = {balance} }}
        if = {{
            limit = {{ var:{balance} > 0 }}
            add_character_modifier = sxad_{skill}_gain_modifier
        }}
        else_if = {{
            limit = {{ var:{balance} < 0 }}
            add_character_modifier = sxad_{skill}_loss_modifier
        }}
    }}
    force_character_skill_recalculation = yes
}}
""")
    chunks.append("\nsxad_rebuild_skill_modifiers_effect = {\n")
    for skill in TRANSFER_ATTRIBUTES:
        chunks.append(f"    sxad_rebuild_{skill}_modifier_effect = yes\n")
    chunks.append("}\n")
    return "".join(chunks)


def transfer_effects() -> str:
    chunks = [HEADER]
    for skill in TRANSFER_ATTRIBUTES:
        balance = f"sxad_{skill}_balance"
        amount = HEALTH_TRANSFER_AMOUNT if skill == "health" else 1
        chunks.append(f"""
# Current scope is receiver. This independently checked helper is also the random branch.
sxad_transfer_{skill}_effect = {{
    save_temporary_scope_as = sxad_receiver
    $DONOR$ = {{ save_temporary_scope_as = sxad_donor }}
    force_character_skill_recalculation = yes
    scope:sxad_donor = {{ force_character_skill_recalculation = yes }}
    sxad_probe_{skill}_effect = yes
    if = {{
        limit = {{ {scoped_compare(f'sxad_can_{skill}', f'scope:sxad_can_{skill} = 1')} }}
        if = {{
            limit = {{ has_variable = {balance} }}
            change_variable = {{ name = {balance} add = {amount} }}
        }}
        else = {{ set_variable = {{ name = {balance} value = {amount} }} }}
        scope:sxad_donor = {{
            if = {{
                limit = {{ has_variable = {balance} }}
                change_variable = {{ name = {balance} add = -{amount} }}
            }}
            else = {{ set_variable = {{ name = {balance} value = -{amount} }} }}
        }}
        sxad_rebuild_{skill}_modifier_effect = yes
        scope:sxad_donor = {{ sxad_rebuild_{skill}_modifier_effect = yes }}
    }}
}}
""")
    chunks.append("\nsxad_select_transfer_effect = {\n"
                  "    save_temporary_scope_as = sxad_receiver\n"
                  "    $DONOR$ = { save_temporary_scope_as = sxad_donor }\n"
                  "    force_character_skill_recalculation = yes\n"
                  "    scope:sxad_donor = { force_character_skill_recalculation = yes }\n")
    for skill in TRANSFER_ATTRIBUTES:
        chunks.append(f"    sxad_probe_{skill}_effect = yes\n")
    chunks.append("    if = {\n        limit = {\n            OR = {\n")
    for skill in TRANSFER_ATTRIBUTES:
        chunks.append(f"                AND = {{ {scoped_compare(f'sxad_can_{skill}', f'scope:sxad_can_{skill} = 1')} }}\n")
    chunks.append("            }\n        }\n        random_list = {\n")
    for skill in TRANSFER_ATTRIBUTES:
        chunks.append(f"""            1 = {{
                trigger = {{ {scoped_compare(f'sxad_can_{skill}', f'scope:sxad_can_{skill} = 1')} }}
                sxad_transfer_{skill}_effect = {{ DONOR = scope:sxad_donor }}
            }}
""")
    chunks.append("        }\n    }\n}\n")
    return "".join(chunks)


def values() -> str:
    result = HEADER + f"""
# Pure guarded read. Missing variables represent zero and are never initialized here.
sxad_experience_value = {{
    value = 0
    if = {{
        limit = {{ has_variable = {SEX_EXPERIENCE_VARIABLE} }}
        add = var:{SEX_EXPERIENCE_VARIABLE}
    }}
}}
"""
    for skill in TRANSFER_ATTRIBUTES:
        result += f"\nsxad_{skill}_value = {{ value = {skill} }}\n"
        balance = f"sxad_{skill}_balance"
        result += f"""
sxad_{skill}_balance_value = {{
    value = 0
    if = {{
        limit = {{ has_variable = {balance} }}
        add = var:{balance}
    }}
}}

sxad_{skill}_gain_scale = {{
    value = 0
    if = {{
        limit = {{ has_variable = {balance} }}
        if = {{
            limit = {{ var:{balance} > 0 }}
            add = var:{balance}
        }}
    }}
}}

sxad_{skill}_loss_scale = {{
    value = 0
    if = {{
        limit = {{ has_variable = {balance} }}
        if = {{
            limit = {{ var:{balance} < 0 }}
            add = var:{balance}
            multiply = -1
        }}
    }}
}}
"""
    return result


def skill_balance_modifiers() -> str:
    result = HEADER + "# Definition-local scale is evaluated in the receiving character scope.\n"
    for skill in TRANSFER_ATTRIBUTES:
        result += f"""
sxad_{skill}_gain_modifier = {{
    {skill} = 1
    scale = {{
        value = sxad_{skill}_gain_scale
        desc = sxad_absorbed_skill_modifier
    }}
}}

sxad_{skill}_loss_modifier = {{
    {skill} = -1
    scale = {{
        value = sxad_{skill}_loss_scale
        desc = sxad_drained_skill_modifier
    }}
}}
"""
    return result


def trait() -> str:
    return HEADER + """
sxad_sex_experience = {
    icon = sxad_sex_experience.dds
    minimum_age = 18
    birth = 0
    random_creation = 0
    inherit_chance = 0
    desc = {
        first_valid = {
            triggered_desc = {
                trigger = { NOT = { exists = this } }
                desc = trait_sxad_sex_experience_desc
            }
            desc = trait_sxad_sex_experience_character_desc
        }
    }
}
"""


def interaction() -> str:
    return HEADER + """
sxad_view_experience_interaction = {
    category = interaction_category_friendly
    common_interaction = yes
    interface_priority = 200
    icon = icon_scheme_seduce
    desc = sxad_view_experience_interaction_desc
    use_diplomatic_range = no
    ignores_pending_interaction_block = yes
    auto_accept = yes
    needs_confirmation = { always = no }
    is_shown = {
        scope:actor = { is_ai = no }
        scope:recipient = { is_alive = yes age >= 18 }
    }
    is_valid_showing_failures_only = {
        scope:actor = { is_ai = no }
        scope:recipient = { is_alive = yes age >= 18 }
    }
    on_accept = {
        custom_tooltip = sxad_view_experience_interaction_accept_tt
        hidden_effect = {
            scope:actor = {
                send_interface_toast = {
                    type = event_toast_effect_neutral
                    title = sxad_view_experience_toast_title
                    left_icon = scope:recipient
                    custom_tooltip = sxad_view_experience_toast_details
                }
            }
        }
    }
    ai_will_do = { base = 0 }
}
"""


def events() -> str:
    return HEADER + """
namespace = sxad

# Experience queries use the native interface toast in sxad_interactions.txt.
# No event window, event options or character state changes are required.
"""


def localization(language: str, entries: dict[str, str]) -> str:
    lines = [f"l_{language}:\n", " # GENERATED FILE - do not edit. Regenerate with tools/gen_runtime.py\n"]
    for key, value in entries.items():
        escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        lines.append(f' {key}:0 "{escaped}"\n')
    return "".join(lines)


def trait_icon() -> bytes:
    width = height = 120
    pixels = bytearray()
    for y in range(height):
        for x in range(width):
            px, py = x - 59.5, y - 59.5
            radius = math.hypot(px, py)
            alpha = max(0, min(255, round((56.0 - radius) * 255)))
            red, green, blue = 31, 18, 51
            ring_a = abs(math.hypot(px + 15, py) - 23) < 5
            ring_b = abs(math.hypot(px - 15, py) - 23) < 5
            border = 50 < radius < 54
            if ring_a or ring_b or border:
                red, green, blue = 224, 186, 95
            if abs(px) < 4 and -43 < py < -30:
                red, green, blue = 255, 234, 161
            pixels.extend((red, green, blue, alpha))
    flags = 0x100F
    pixel_format = struct.pack("<8I", 32, 0x41, 0, 32, 0x000000FF, 0x0000FF00, 0x00FF0000, 0xFF000000)
    header = struct.pack("<7I", 124, flags, height, width, width * 4, 0, 0) + bytes(44)
    header += pixel_format + struct.pack("<5I", 0x1000, 0, 0, 0, 0)
    return b"DDS " + header + pixels


def render_outputs(game_root: Path | None = None) -> dict[str, bytes]:
    if game_root is not None:
        verify_encounter_source_bindings(game_root)
    outputs = hook_outputs()
    for additions in (encounter_hook_outputs(), natural_simulation_outputs()):
        if outputs.keys() & additions.keys():
            raise ValueError("Repeated generated runtime output path")
        outputs.update(additions)
    text_outputs = {
        "common/scripted_effects/sxad_experience_effects.txt": experience_effects(),
        "common/scripted_effects/sxad_probe_skill_effects.txt": probe_effects(),
        "common/scripted_effects/sxad_transfer_effects.txt": transfer_effects(),
        "common/script_values/sxad_values.txt": values(),
        "common/modifiers/sxad_skill_balance_modifiers.txt": skill_balance_modifiers(),
        "common/traits/sxad_traits.txt": trait(),
        "common/character_interactions/sxad_interactions.txt": interaction(),
        "events/sxad_events.txt": events(),
        "localization/simp_chinese/sxad_l_simp_chinese.yml": localization("simp_chinese", ZH),
        "localization/english/sxad_l_english.yml": localization("english", EN),
    }
    outputs.update({name: encode(body) for name, body in text_outputs.items()})
    raw_translations: object = json.loads(UI_LOCALIZATION_SOURCE.read_text(encoding="utf-8"))
    translations = required_fields(raw_translations, frozenset(LANGUAGES) - {"english", "simp_chinese"}, "external localizations")
    for language, raw_entries in translations.items():
        fields = required_fields(raw_entries, frozenset(EN), f"{language} localization keys")
        entries = {key: required_string(value, f"{language}/{key}") for key, value in fields.items()}
        outputs[f"localization/{language}/sxad_l_{language}.yml"] = encode(localization(language, entries))
    outputs["gfx/interface/icons/traits/sxad_sex_experience.dds"] = trait_icon()
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Read-only byte parity check")
    parser.add_argument("--refresh-vanilla", action="store_true", help="Extract the two pinned vanilla hooks after source SHA validation")
    parser.add_argument("--game-root", type=Path, help="also verify exact pinned definitions and local-name inventories against this installation or game directory")
    args = parser.parse_args()
    if args.check and args.refresh_vanilla:
        parser.error("--check cannot refresh inputs")
    if args.refresh_vanilla:
        refresh_vanilla(args.game_root or DEFAULT_GAME_ROOT)
    outputs = render_outputs(args.game_root)
    errors = []
    for relative, expected in outputs.items():
        target = MOD_ROOT / relative
        if args.check:
            if not target.is_file() or target.read_bytes() != expected:
                errors.append(relative)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(expected)
    if errors:
        raise RuntimeError("Generated bytes differ: " + ", ".join(errors))
    print(f"{'Checked' if args.check else 'Generated'} {len(outputs)} runtime files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

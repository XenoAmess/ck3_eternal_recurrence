"""Freeze the new stock nonreligious phase AST; never inspect a live process."""
from __future__ import annotations

import argparse
from collections import deque
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUTPUT = HERE / "ck3_1_20_0_2_phase_ast.json"
DELTA = HERE / "phase_source_delta_1_20_0_2.json"
LEGACY = REPO / "ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_stock_combat_phase_events.json"
SHA = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
RELIGIOUS = re.compile(r"(?:^|[.:_])(?:faith|religion|rite|doctrine|tenet|fervor|holy_order)(?:$|[.:_])|cranial_trophies|spiritual_fulfillment|exaltation_of_pain|mortification")
TOKEN = re.compile(r'\s+|\#[^\n]*|"(?:\\.|[^"\\])*"|[{}]|\?=|!=|<=|>=|==|[=<>]|[^\s{}=<>!?#"]+')


def digest(value: object) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest().upper()


class Parser:
    """Ordered Clausewitz syntax: duplicate keys, operators and list atoms survive."""
    def __init__(self, text: str):
        self.text = text
        self.tokens = []
        cursor = 0
        for token in TOKEN.finditer(text):
            if token.start() != cursor:
                raise ValueError(f"unparsed source at character {cursor}")
            cursor = token.end()
            value = token.group()
            if not value.isspace() and not value.startswith("#"):
                self.tokens.append((value, token.start(), token.end()))
        if cursor != len(text):
            raise ValueError(f"trailing source at character {cursor}")
        self.index = 0

    def block(self, nested: bool = False) -> dict:
        entries = []
        while self.index < len(self.tokens):
            token, start, end = self.tokens[self.index]
            if token == "}":
                if not nested:
                    raise ValueError("unexpected closing brace")
                self.index += 1
                return {"op": "block", "entries": entries, "end": end}
            if token == "{":
                self.index += 1
                child = self.block(True)
                entries.append({"op": "list_block", "value": child, "start": start, "end": child["end"]})
                continue
            self.index += 1
            if self.index < len(self.tokens) and self.tokens[self.index][0] in {"=", "?=", "!=", "==", "<", ">", "<=", ">="}:
                operator = self.tokens[self.index][0]
                self.index += 1
                if self.index >= len(self.tokens):
                    raise ValueError(f"missing value for {token}")
                value, _, end = self.tokens[self.index]
                self.index += 1
                if value == "{":
                    value = self.block(True)
                    end = value["end"]
                elif value == "}":
                    raise ValueError(f"missing value for {token}")
                entries.append({"op": "entry", "key": token, "operator": operator, "value": value, "start": start, "end": end})
            else:
                entries.append({"op": "list_atom", "value": token, "start": start, "end": end})
        if nested:
            raise ValueError("unclosed brace")
        return {"op": "block", "entries": entries, "end": len(self.text)}


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def project(value, text: str, path: str, opaque: list[dict]):
    if isinstance(value, dict):
        branch_value = value.get("value", {})
        conditions = [node for node in branch_value.get("entries", []) if node.get("key") == "limit"] if isinstance(branch_value, dict) else []
        inspected = conditions if value.get("key") in {"if", "else_if", "trigger_if", "trigger_else_if"} else value
        religious_branch = value.get("key") in {"if", "else_if", "else", "modifier", "trigger_if", "trigger_else_if", "save_temporary_scope_value_as"} and any(
            isinstance(node.get(field), str) and RELIGIOUS.search(node[field])
            for node in walk(inspected) for field in ("key", "value"))
        if value.get("op") == "entry" and (RELIGIOUS.search(value["key"]) or religious_branch):
            raw = text[value["start"]:value["end"]]
            leaf = {"op": "deferred_opaque", "domain": "religion_and_rites", "key": value["key"],
                    "operator": value["operator"], "source_path": path,
                    "line": text.count("\n", 0, value["start"]) + 1,
                    "raw_text": raw, "raw_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()}
            opaque.append(leaf)
            return leaf
        return {key: project(child, text, path, opaque) for key, child in value.items() if key not in {"start", "end"}}
    if isinstance(value, list):
        return [project(child, text, path, opaque) for child in value]
    return value


def is_religious_path(path: str) -> bool:
    return bool(RELIGIOUS.search(path) or "enemy_hostile_knight_death" in path or "enemy_faiths" in path)


def normalized_projection(value):
    if isinstance(value, dict):
        if value.get("op") == "state_ref" and is_religious_path(value.get("path", "")):
            return {"op": "deferred_opaque", "domain": "religion_and_rites", "legacy_path": value["path"],
                    "value_type": value["value_type"], "resolution": "not_evaluated"}
        result = {key: normalized_projection(child) for key, child in value.items()}
        if value.get("op") == "call_transition":
            result["dependencies"] = [path for path in result["dependencies"] if not is_religious_path(path)]
            if value.get("key") == "observational_only":
                effects = result.get("args", {}).get("effects", [])
                religious = [effect for effect in effects if effect == "cranial_trophy"]
                if religious:
                    result["deferred_effects"] = religious
                    result["args"]["effects"] = [effect for effect in effects if effect not in religious]
        return result
    if isinstance(value, list):
        return [normalized_projection(child) for child in value]
    return value


def build(source_root: Path | None = None) -> dict:
    source_root = source_root or Path(os.environ.get("XAR_CK3_12002_FROZEN_SOURCE_ROOT", str(REPO)))
    delta = json.loads(DELTA.read_text(encoding="utf-8-sig"))
    legacy = json.loads(LEGACY.read_text(encoding="utf-8-sig"))
    definitions = {}
    files = []
    for file in delta["files"]:
        path = Path(file["frozen_source"])
        if not path.is_absolute():
            path = source_root / path
        raw = path.read_bytes()
        actual = hashlib.sha256(raw).hexdigest().upper()
        if actual != file["new_sha256"]:
            raise ValueError(f"source hash changed: {file['relative_path']}")
        text = raw.decode("utf-8-sig")
        ast = Parser(text).block()
        files.append({"relative_path": file["relative_path"], "sha256": actual})
        for entry in ast["entries"]:
            if entry["op"] == "entry":
                definitions[entry["key"]] = (entry, text, file["relative_path"])
    selected = {}
    pending = deque(row["key"] for row in legacy["event_rows"])
    opaque = []
    while pending:
        name = pending.popleft()
        if name in selected:
            continue
        entry, text, path = definitions[name]
        projection = project(entry, text, path, opaque)
        selected[name] = {"key": name, "source_path": path,
                          "line": text.count("\n", 0, entry["start"]) + 1,
                          "source_ast": projection}
        for node in walk(projection):
            if node.get("op") == "deferred_opaque":
                continue
            for candidate in (node.get("key"), node.get("value")):
                if isinstance(candidate, str) and candidate in definitions and candidate not in selected:
                    pending.append(candidate)
    events = []
    for row in legacy["event_rows"]:
        event = {name: copy.deepcopy(row[name]) for name in ("global_load_index", "type_load_index", "key", "type", "base_weight", "transition_tags")}
        source = selected[row["key"]]["source_ast"]["value"]["entries"]
        source_type = next(node["value"] for node in source if node.get("key") == "type")
        chance = next(node["value"] for node in source if node.get("key") == "chance")
        base = next(node["value"] for node in chance["entries"] if node.get("key") == "base")
        if source_type != row["type"] or int(base) != row["base_weight"]:
            raise ValueError(f"source event identity/base drift: {row['key']}")
        event["source_definition"] = row["key"]
        for field in ("validity_ast", "chance_ast", "effect_ast"):
            event[field] = normalized_projection(row[field])
        event["state_dependencies"] = sorted(path for path in row["state_dependencies"] if not is_religious_path(path))
        events.append(event)
    result = {"schema_version": 1, "game_version": "1.20.0.2", "executable_sha256": SHA,
              "rules_source": "stock_frozen_nonreligious_private_ast",
              "files": files, "event_rows": events, "source_definitions": list(selected.values()),
              "deferred_source_nodes": opaque,
              "nonreligious_syntax_changes": [
                  {"key": "accolade", "operator": "?=", "behavior": "skip absent scope before add_glory"},
                  {"key": "has_none_of_variables", "names": ["beheaded_warrior", "beheaded_warrior_cooldown"],
                   "behavior": "both variable presences must be false; cooldown is not a character flag"},
                  {"key": "accolade_progress", "added_predicate": "is_alive = yes",
                   "behavior": "dead liege yields zero even if stale progress variable remains"}],
              "completeness": {"nonreligious_source_ast_migrated": True,
                  "complete_phase_ast_migrated": False, "loaded_playset_verified": False,
                  "original_trace_ready": False, "production_registered": False,
                  "deferred_domains": ["religion_and_rites"],
                  "normalized_effect_kernel": "reuse version-independent legacy kernel; observational feedback remains explicit",
                  "source_operator_policy": "ordered duplicates preserved; nullable scope and variable-list predicate explicit"}}
    result["canonical_ast_sha256"] = digest(result)
    return result


def evaluate_variable_none(names: list[str], variables: dict[str, object]) -> bool:
    return not any(name in variables for name in names)


def nullable_scope(value, effect):
    if value is None:
        return False
    effect(value)
    return True


class DeferredDomain(RuntimeError):
    pass


def evaluate_nonreligious_value(node: dict, references: dict[str, object]):
    """Use the existing arithmetic kernel only on explicit nonreligious nodes."""
    if any(item.get("op") == "deferred_opaque" for item in walk(node)):
        raise DeferredDomain("religion_and_rites")
    project_src = REPO / "ck3_autonomous_player/src"
    if str(project_src) not in sys.path:
        sys.path.insert(0, str(project_src))
    from xar_autoplayer.simulation.phase_event_evaluator import _eval_value

    class References:
        def resolve_ref(self, path, *, candidate=None):
            return references[path]

    return _eval_value(node, state=References(), name="phase_12002_private", candidate=None)


def accolade_progress(alive: bool, variables: dict[str, object]):
    return variables.get("accolade_progress", 0) if alive else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--source-root", type=Path,
                        help="root containing frozen relative artifacts; defaults to XAR_CK3_12002_FROZEN_SOURCE_ROOT or repository")
    args = parser.parse_args()
    result = build(args.source_root)
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if OUTPUT.read_text(encoding="utf-8-sig") != encoded:
            raise ValueError("new-build nonreligious AST is not reproducible")
    else:
        OUTPUT.write_text(encoded, encoding="utf-8-sig", newline="\n")
    print(json.dumps({"status": "GREEN", "event_rows": len(result["event_rows"]),
                      "source_definitions": len(result["source_definitions"]),
                      "deferred_opaque_nodes": len(result["deferred_source_nodes"]),
                      "canonical_ast_sha256": result["canonical_ast_sha256"], "live": False}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

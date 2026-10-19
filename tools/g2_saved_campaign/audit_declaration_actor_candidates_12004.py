"""Pin a bounded actor-only CB trigger closure; no Game or native calls.

The explicit four roots below were reviewed against stock31F4520's type+48
allowed_for_character receiver. This is source admission, not proof of the
loaded playset or runtime ABI. A future cold owner must separately resolve
overrides for BOTH casus_belli_types and scripted_triggers before opting in.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
FILES = (
    "casus_belli_types/00_event_war.txt",
    "casus_belli_types/00_religious_war.txt",
    "casus_belli_types/10_tgp_japan_wars.txt",
    "scripted_triggers/00_has_dlc_scripted_triggers.txt",
    "scripted_triggers/00_great_holy_war_triggers.txt",
    "scripted_triggers/10_tgp_japan_triggers.txt",
    "scripted_triggers/10_tgp_triggers.txt",
)
CB_FILES = {
    "hungarian_migration_cb": FILES[0],
    "directed_great_holy_war": FILES[1],
    "japan_imperial_expansion_cb": FILES[2],
    "japan_imperial_reconquest_cb": FILES[2],
}
SAFE_ASSIGNMENT_KEYS = {
    "culture", "faith", "has_doctrine_parameter", "has_dlc_feature",
    "top_liege", "highest_held_title_tier", "government_has_flag",
    "OR", "AND", "NOT", "custom_tooltip", "text", "exists",
    "has_doctrine", "scope:attacker", "any_vassal", "this", "religion",
}
TOKEN = re.compile(r'#[^\n]*|"(?:\\.|[^"\\])*"|[{}]|[^\s{}#]+')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()


def tokens(text: str) -> list[str]:
    return [m.group() for m in TOKEN.finditer(text) if not m.group().startswith("#")]


def definitions(items: list[str]) -> dict[str, list[str]]:
    result = {}
    index = 0
    while index < len(items):
        if index + 2 >= len(items) or items[index + 1:index + 3] != ["=", "{"]:
            raise ValueError(f"unexpected top-level token: {items[index:index + 3]}")
        key, start = items[index], index + 3
        depth, index = 1, start
        while index < len(items) and depth:
            depth += (items[index] == "{") - (items[index] == "}")
            index += 1
        if depth or key in result:
            raise ValueError(f"unclosed or duplicate definition: {key}")
        result[key] = items[start:index - 1]
    return result


def field(body: list[str], name: str) -> list[str]:
    depth, found = 0, []
    for index, token in enumerate(body):
        if depth == 0 and token == name and body[index + 1:index + 3] == ["=", "{"]:
            start, cursor, nested = index + 3, index + 3, 1
            while cursor < len(body) and nested:
                nested += (body[cursor] == "{") - (body[cursor] == "}")
                cursor += 1
            if nested:
                raise ValueError(f"unclosed field: {name}")
            found.append(body[start:cursor - 1])
        depth += (token == "{") - (token == "}")
    if len(found) != 1:
        raise ValueError(f"expected one {name}, found {len(found)}")
    return found[0]


def audit(common: Path) -> dict:
    pinned, trigger_definitions, cb_definitions = {}, {}, {}
    for relative in FILES:
        source = common / relative
        raw = source.read_bytes()
        pinned[relative] = {"relative_path": relative, "bytes": len(raw), "sha256": sha(raw)}
        parsed = definitions(tokens(raw.decode("utf-8-sig")))
        destination = trigger_definitions if relative.startswith("scripted_triggers/") else cb_definitions
        for name, body in parsed.items():
            if name in destination:
                raise ValueError(f"duplicate source definition: {name}")
            destination[name] = (relative, body)
    rules, closures = [], {}
    for key, relative in CB_FILES.items():
        actual_relative, body = cb_definitions[key]
        if actual_relative != relative:
            raise ValueError(f"CB source moved: {key}")
        pending = [(key + "/allowed_for_character", relative, field(body, "allowed_for_character"))]
        visited, closure = set(), []
        while pending:
            name, source_relative, tree = pending.pop()
            if name in visited:
                continue
            visited.add(name)
            named = sorted(set(re.findall(r"scope:([A-Za-z_][A-Za-z_0-9]*)", " ".join(tree))))
            if any(item != "attacker" for item in named):
                raise ValueError(f"non-actor named scope in {name}: {named}")
            if any("$" in token or token.lower() in {"root", "prev", "from", "random", "chance", "weight"}
                   or token.startswith(("save_", "random_")) for token in tree):
                raise ValueError(f"unqualified dynamic or context-dependent token in {name}")
            dependencies = []
            for i in range(len(tree) - 1):
                if tree[i + 1] not in {"=", "!=", "?=", ">=", "<=", ">", "<"}:
                    continue
                operand = tree[i]
                if operand in trigger_definitions:
                    dependency_relative, dependency_body = trigger_definitions[operand]
                    dependencies.append(operand)
                    pending.append((operand, dependency_relative, dependency_body))
                elif operand not in SAFE_ASSIGNMENT_KEYS:
                    raise ValueError(f"unreviewed native trigger/scope in {name}: {operand}")
            closure.append({"name": name, "relative_path": source_relative,
                            "source_sha256": pinned[source_relative]["sha256"],
                            "token_sha256": sha(canonical(tree)),
                            "named_scopes": named, "dependencies": sorted(set(dependencies))})
        closure.sort(key=lambda item: item["name"])
        closure_sha = sha(canonical(closure))
        rules.append({"key": key, "definition_source_sha256": pinned[relative]["sha256"],
                      "actor_trigger_closure_sha256": closure_sha})
        closures[key] = closure
    rules.sort(key=lambda item: item["key"])
    return {"rules": rules, "rules_sha256": sha(canonical(rules)),
            "closure": closures, "source_files": list(pinned.values())}


def main() -> None:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--game-common", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.game_common)
    result.update({
        "schema": "xar.declaration-actor-candidate-source-audit/v1",
        "machine_id": subprocess.check_output(
            [sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], text=True).strip(),
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "game_common": str(args.game_common.resolve()),
        "producer": {"path": str(Path(__file__).resolve()), "sha256": sha(Path(__file__).read_bytes())},
        "native_caller": {"rva": "0x31F4520", "call_site": "0x31F4736",
                          "receiver": "type+0x48", "callee": "0x37998D0",
                          "evaluator_argument": "null", "root_kind": 4,
                          "actor_full_id": "zero_extended Character+0x18",
                          "named_attacker_key_slot": "0x5D4BD94"},
        "loaded_source_qualification": "PENDING: resolve CB AND scripted-trigger overrides for future playset",
        "native_abi_qualification": "static source only; future same-frame shadow remains required",
        "current_native25_changed": False,
        "game_or_native_calls": 0,
        "claim": "Only source-qualified deterministic actor no may empty this CB candidate superset; yes/unknown remain wide.",
    })
    raw = (json.dumps(result, ensure_ascii=True, indent=2) + "\n").encode()
    if len(raw) > 128 * 1024 or args.output.exists():
        raise ValueError("audit output is create-only and bounded to128KiB")
    args.output.write_bytes(raw)
    print(json.dumps({"output": str(args.output), "bytes": len(raw), "sha256": sha(raw),
                      "rules_sha256": result["rules_sha256"], "rules": result["rules"]}))


if __name__ == "__main__":
    main()

"""Read an explicit immutable R5 save using the already-used R3 block parser.

No game, SDK call, injection, desktop or process operation. Missing fields stay
missing. Generic scenario assertions are explicit JSON input, never implied by
absence of a variable. Total skills and native AI-control are not guessed.
"""
from __future__ import annotations
import argparse
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
EXTERNAL = Path("C:/workspace/ck3_lyd_runtime_20261004")
SUPPORT = EXTERNAL / "r3_checkpoint_readback.py"
spec = importlib.util.spec_from_file_location("lyd_r3_readback_support", SUPPORT)
r3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r3)
one, parsed, unquote, numeric = r3.one, r3.parsed, r3.unquote, r3.numeric


def sha(path):
    return r3.sha(path)


def value(entries, key):
    return unquote(one(entries, key))


def typed(data):
    if not isinstance(data, list):
        return {"type": None, "identity": None, "entries": data}
    kind, identity = one(data, "type"), one(data, "identity")
    result = {"type": kind, "identity": identity, "entries": data}
    if kind == "value" and isinstance(identity, str):
        # R2 actual three-round saves bind the persistent script value encoding.
        result["number"] = str(Decimal(identity) / Decimal(100000))
        result["scale"] = 100000
    elif kind == "boolean":
        result["boolean"] = {"0": False, "1": True}.get(identity)
    return result


def stored(entries):
    owner = one(entries, "variables")
    if owner is None:
        return {}, {}, None
    data, lists = one(owner, "data") or [], one(owner, "list") or []
    variables, collections = {}, {}
    for row in data:
        fields = row["value"]
        if not isinstance(fields, list):
            raise ValueError("Unexpected saved variable row")
        name = unquote(one(fields, "flag"))
        if isinstance(name, str) and name.startswith("lyd_"):
            if name in variables:
                raise ValueError("Duplicate saved variable: " + name)
            variables[name] = {"present": True, "tick": one(fields, "tick"),
                               **typed(one(fields, "data")), "row_entries": fields}
    for row in lists:
        fields = row["value"]
        if not isinstance(fields, list):
            raise ValueError("Unexpected named list row")
        name = unquote(one(fields, "name"))
        if isinstance(name, str) and name.startswith("lyd_"):
            if name in collections:
                raise ValueError("Duplicate saved list: " + name)
            collections[name] = {"present": True, "items": [typed(item["value"]) for item in fields if item["key"] == "item"],
                                 "duration_entries": one(fields, "duration"), "row_entries": fields}
    return variables, collections, owner


def excerpt(output, label, raw, evidence):
    payload = (raw + "\n").encode("utf-8")
    target = output / (label + ".excerpt.txt")
    target.write_bytes(payload)
    evidence.append({"path": target.name, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
                     "encoding": "UTF-8, original save CRLF normalized to LF; full original save SHA separately bound"})


def graph_section(text, name, output, evidence):
    raw = r3.extract_exact_indented_block(text, name, 0)
    excerpt(output, "all-" + name, raw, evidence)
    entries = parsed(raw)
    containers = [e for e in entries if e["key"] in ("database", "data")]
    if len(containers) != 1 or not isinstance(containers[0]["value"], list):
        raise ValueError("Expected exactly one supported actual saved graph database/data container")
    container = containers[0]["value"]
    result = {}
    for entry in container:
        key, fields = entry["key"], entry["value"]
        if not isinstance(key, str) or not key.isdigit() or not isinstance(fields, list):
            continue
        variables, lists, _ = stored(fields)
        data = one(fields, "data") or []
        result[key] = {"id": key, "variables": variables, "lists": lists,
                       "tag": value(fields, "tag") or value(data, "tag"),
                       "name": value(fields, "name") or value(data, "name"),
                       "saved_entries": fields}
        for field in ("rite_type", "faith_type", "faith", "religion", "main_rite", "religious_head", "head_of_rite", "origin", "source", "convert", "enabled", "founder"):
            result[key][field] = value(fields, field)
        result[key]["tenet_status_entries"] = one(data, "tenets") if data else one(fields, "tenets")
        doctrine_owner = data if data else fields
        result[key]["doctrines"] = [unquote(e["value"]) for e in doctrine_owner if e["key"] == "doctrine"]
    return result


def pointer(variables, key, expected_type):
    item = variables.get(key)
    if not item or item["type"] != expected_type:
        return None
    return item["identity"]


def project(text, player_id, output):
    evidence = []
    metadata_raw = r3.extract_exact_indented_block(text, "meta_data", 0)
    metadata = parsed(metadata_raw)
    excerpt(output, "metadata", metadata_raw, evidence)
    played_raw = r3.extract_exact_indented_block(text, "played_character", 0)
    played = parsed(played_raw)
    excerpt(output, "played-character", played_raw, evidence)
    current = re.findall(r"(?m)^currently_played_characters=\{([^}]*)\}", text)
    if len(current) != 1:
        raise ValueError("Nonunique currently_played_characters")
    current_ids = current[0].split()
    if one(played, "character", required=True) != str(player_id) or str(player_id) not in current_ids:
        raise ValueError("Explicit fresh actor differs from actual saved played/current actor")
    if value(metadata, "version") != "1.20.0.3":
        raise ValueError("Save is not CK3 1.20.0.3")
    living = r3.section(text, "living", "dead_unprunable")
    rites = graph_section(text, "rites", output, evidence)
    faiths = graph_section(text, "faiths", output, evidence)
    lookup = r3.section(text, "character_lookup", "deleted_characters")
    reverse_history = collections_for_lookup(lookup)
    characters = {}
    def character(identifier):
        identifier = str(identifier)
        if identifier in characters:
            return characters[identifier]
        raw = r3.extract_exact_indented_block(living, identifier, 0)
        fields = parsed(raw)
        alive = one(fields, "alive_data", required=True)
        variables, lists, _ = stored(alive)
        rite_id = one(fields, "rite", required=True)
        faith_id = rites.get(rite_id, {}).get("faith")
        skill = one(fields, "skill")
        saved_skills = [e["value"] for e in skill] if isinstance(skill, list) else None
        lifestyle = one(alive, "lifestyle_xp") or []
        result = {"id": identifier, "first_name": value(fields, "first_name"), "birth": value(fields, "birth"),
                  "history_ids": reverse_history.get(identifier, []), "rite_id": rite_id, "faith_id": faith_id,
                  "rite_type": rites.get(rite_id, {}).get("rite_type"), "rite_tag": rites.get(rite_id, {}).get("tag"),
                  "faith_main_rite_id": faiths.get(faith_id, {}).get("main_rite"),
                  "variables": variables, "lists": lists, "saved_skill_array": saved_skills,
                  "base_learning": numeric(saved_skills[4]) if saved_skills and len(saved_skills) > 4 else None,
                  "total_learning": None, "total_learning_boundary": "Not reconstructed from base skills; modifiers require native skill read or explicit saved fixture measurement",
                  "alive_data_present": True, "currently_played": identifier in current_ids,
                  "native_is_ai": None, "ai_boundary": "Not inferred solely from absence among local played characters",
                  "traits": one(fields, "traits"), "dynasty_house": one(fields, "dynasty_house"), "saved_family_data": one(fields, "family_data"), "saved_playable_data": one(fields, "playable_data"),
                  "landed_data": one(fields, "landed_data"), "employer": one(alive, "employer"),
                  "saved_prison_data": one(alive, "prison_data"),
                  "saved_values": {"gold": numeric(one(one(alive, "gold") or [], "value")), "piety": numeric(one(one(alive, "piety") or [], "currency")),
                                   "prestige": numeric(one(one(alive, "prestige") or [], "currency")), "stress": numeric(one(alive, "stress")),
                                   "learning_lifestyle_xp": numeric(one(lifestyle, "learning_lifestyle"))},
                  "saved_entries": fields}
        characters[identifier] = result
        excerpt(output, "character-" + identifier, raw, evidence)
        return result
    actor = character(player_id)
    roles = {"actor": actor}
    for label, flag in [("source_rep", "lyd_r4_source_rep"), ("receiving_rep", "lyd_r4_jingshu_rep")]:
        identifier = pointer(actor["variables"], flag, "char")
        roles[label] = character(identifier) if identifier is not None else None
    # Actual elector/player/signature lists identify their own objects. Also
    # include snapshot heads and delegates without any historical runtime ID.
    pending = set()
    for person in list(characters.values()):
        pending.update(item["identity"] for item in person["variables"].values() if item["type"] == "char")
        pending.update(item["identity"] for group in person["lists"].values() for item in group["items"] if item["type"] == "char")
    for rite in rites.values():
        pending.update(item["identity"] for item in rite["variables"].values() if item["type"] == "char")
        pending.update(item["identity"] for group in rite["lists"].values() for item in group["items"] if item["type"] == "char")
    unresolved = []
    for identifier in sorted(pending - set(characters)):
        try:
            character(identifier)
        except ValueError as error:
            unresolved.append({"id": identifier, "status": "NOT_LIVING_OR_UNRESOLVED", "error": str(error)})
    title_section = r3.section(text, "landed_titles", "dynasties")
    title_pattern = re.compile(r"(?ms)^([0-9]+)=\{\n(.*?)^\}")
    wanted_titles = {faith["religious_head"] for faith in faiths.values() if faith["religious_head"] not in (None, "4294967295")}
    wanted_titles |= {item["identity"] for person in characters.values() for item in person["variables"].values() if item["type"] in {"landed_title", "title"}}
    titles = {}
    held = {}
    for match in title_pattern.finditer(title_section):
        identifier, raw = match.group(1), match.group(0)
        holder = re.findall(r"(?m)^\tholder=([0-9]+)\s*$", raw)
        if len(holder) > 1:
            raise ValueError("Multiple top-level title holders")
        if holder:
            held.setdefault(holder[0], []).append(identifier)
        if identifier not in wanted_titles and "lyd_c2_owned_head_title" not in raw and "lyd_c3_owned_claim_title" not in raw:
            continue
        fields = parsed(raw)
        variables, lists, _ = stored(fields)
        titles[identifier] = {"id": identifier, "key": value(fields, "key"), "holder": one(fields, "holder"),
                              "variables": variables, "lists": lists, "saved_entries": fields}
        excerpt(output, "title-" + identifier, raw, evidence)
    for faith in faiths.values():
        faith["rite_ids"] = sorted(key for key, rite in rites.items() if rite["faith"] == faith["id"])
        faith["rite_count"] = len(faith["rite_ids"])
        faith["main_rite_present"] = faith["main_rite"] in rites
        faith["main_rite_parent_matches"] = rites.get(faith["main_rite"], {}).get("faith") == faith["id"]
        faith["main_rite_type"] = rites.get(faith["main_rite"], {}).get("rite_type")
        faith["head_title_holder"] = titles.get(faith["religious_head"], {}).get("holder")
    for person in characters.values():
        person["actual_saved_held_title_ids"] = sorted(held.get(person["id"], []))
    owned = {key: title for key, title in titles.items() if "lyd_c2_owned_head_title" in title["variables"] or "lyd_c3_owned_claim_title" in title["variables"]}
    labels = {}
    for identifier, rite in rites.items():
        key = rite["tag"] if isinstance(rite["tag"], str) and rite["tag"].startswith("lyd_rite_") else rite["rite_type"]
        if isinstance(key, str) and key.startswith("lyd_rite_"):
            labels.setdefault(key, []).append(identifier)
    source_id = pointer(actor["variables"], "lyd_r4_initial_source_faith", "faith")
    receiving_id = pointer(actor["variables"], "lyd_r4_receiving_faith", "faith")
    return {"player_id": player_id, "currently_played_ids": current_ids, "metadata": {key: value(metadata, key) for key in ("version", "meta_date", "meta_player_name")},
            "roles": roles, "characters": characters, "unresolved_character_references": unresolved,
            "all_rites": rites, "all_faiths": faiths, "lyd_rite_key_candidates": labels,
            "lyd_rite_key_count": len(labels),
            "source_fixture_faith": faiths.get(source_id), "receiving_fixture_faith": faiths.get(receiving_id),
            "owned_head_and_claim_titles": owned, "head_titles": titles, "raw_excerpts": evidence,
            "missing_policy": "Absent variables, list/flag records, total skills, AI status and numeric values are not silently treated as zero, false, expired or success"}


def collections_for_lookup(raw):
    result = {}
    for old, current in re.findall(r"(?m)^\t([0-9]+)=([0-9]+)\s*$", raw):
        result.setdefault(current, []).append(old)
    return result


def get_path(document, pointer):
    result = document
    if not pointer.startswith("/"):
        raise ValueError("Expectation paths are JSON pointers beginning with /")
    for part in pointer[1:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        if isinstance(result, list):
            result = result[int(key)]
        elif isinstance(result, dict) and key in result:
            result = result[key]
        else:
            raise KeyError(pointer)
    return result


def check_expectations(report, expectations, previous):
    checks = []
    for row in expectations.get("checks", []):
        op, path = row["op"], row["path"]
        try:
            actual = get_path(report, path)
            exists = actual is not None
        except (KeyError, IndexError):
            actual, exists = None, False
        expected = row.get("value")
        passed = False
        if op == "absent":
            passed = not exists
        elif op == "present":
            passed = exists
        elif exists and op == "eq":
            passed = actual == expected
        elif exists and op == "eq_path":
            expected = get_path(report, row["other_path"])
            passed = expected is not None and actual == expected
        elif exists and op == "gte":
            passed = Decimal(str(actual)) >= Decimal(str(expected))
        elif exists and op == "delta":
            if previous is None or previous["state"]["player_id"] != report["state"]["player_id"]:
                raise ValueError("Delta requires an explicitly supplied same-actor previous report")
            before = get_path(previous, row.get("previous_path", path))
            passed = before is not None and Decimal(str(actual)) - Decimal(str(before)) == Decimal(str(expected))
        elif op not in {"eq", "eq_path", "gte", "delta", "present", "absent"}:
            raise ValueError("Unsupported expectation operation: " + op)
        checks.append({**row, "actual": actual, "expected": expected, "field_present": exists, "passed": passed})
    if not checks:
        raise ValueError("Explicit expectations must contain at least one check")
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save", "--artifact", dest="save", type=Path, required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--player-id", "--native-player-id", dest="player_id", type=int, required=True)
    parser.add_argument("--checkpoint-receipt", "--native-receipt", dest="receipt", type=Path)
    parser.add_argument("--expect", type=Path)
    parser.add_argument("--previous-report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--label", default="R5 explicit save readback")
    args = parser.parse_args()
    artifact, output = args.save.resolve(), args.output.resolve()
    if EXTERNAL not in artifact.parents or EXTERNAL not in output.parents or output.exists() or args.player_id <= 0:
        raise ValueError("Use an explicit external immutable artifact, positive fresh player ID and NEW external output")
    if not re.fullmatch(r"[0-9a-f]{64}", args.sha) or sha(artifact) != args.sha:
        raise ValueError("Save SHA mismatch")
    before = artifact.stat()
    if getattr(before, "st_file_attributes", 1) & 1 == 0:
        raise ValueError("Save must be a preserved read-only copy; do not read the game's mutable save in place")
    output.mkdir(parents=True)
    report = {"schema": "ck3.lyd.r5-explicit-save-readback.v1", "created_utc": r3.now(), "label": args.label,
              "artifact": {"path": str(artifact), "bytes": before.st_size, "sha256": args.sha},
              "parser_source": {"path": str(SUPPORT), "sha256": sha(SUPPORT)},
              "bounded_parser_source": {"path": str(r3.REPO / "ck3_autonomous_player/src/xar_autoplayer/simulation/knight_causal_save_projection.py"),
                                        "sha256": sha(r3.REPO / "ck3_autonomous_player/src/xar_autoplayer/simulation/knight_causal_save_projection.py"),
                                        "used_functions": ["extract_exact_indented_block", "parse_block", "block_body", "one"],
                                        "date_decoder_or_ABI_called": False},
              "game_called": False, "tracked_written": False, "native_boundary": "Saved state is independent; optional SDK receipt is separately hash-bound and never fills missing saved fields",
              "live_acceptance": "NOT_GRADED_BY_THIS_FILE_READER"}
    try:
        raw = artifact.read_bytes()
        report["state"] = project(raw.decode("utf-8-sig").replace("\r\n", "\n"), args.player_id, output)
        if args.receipt:
            native = r3.native_projection(args.receipt.resolve(), args.sha, args.player_id)
            checkpoint = native["checkpoint"]
            if not isinstance(checkpoint, dict) or checkpoint.get("status") != "saved" or checkpoint.get("sha256") != args.sha or checkpoint.get("size") != before.st_size:
                raise ValueError("Receipt lacks exact successful save SHA/size")
            report["native_receipt"] = native
            (output / "native-receipt.raw.json").write_bytes(args.receipt.read_bytes())
        previous = None
        if args.previous_report:
            previous = json.loads(args.previous_report.read_text(encoding="utf-8-sig"))
            if previous.get("schema") != report["schema"]:
                raise ValueError("Previous report must use this R5 saved-state schema")
            report["previous_report"] = {"path": str(args.previous_report.resolve()), "sha256": sha(args.previous_report)}
        if args.expect:
            expectations = json.loads(args.expect.read_text(encoding="utf-8-sig"))
            (output / "expectations.raw.json").write_bytes(args.expect.read_bytes())
            report["expectations_sha256"] = sha(args.expect)
            report["checks"] = check_expectations(report, expectations, previous)
            report["result"] = "PASS_EXPLICIT_SAVED_ASSERTIONS" if all(check["passed"] for check in report["checks"]) else "FAIL_EXPLICIT_SAVED_ASSERTIONS"
        else:
            report["result"] = "OBSERVED_ONLY_NO_SCENARIO_PASS"
        after = artifact.stat()
        if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns or sha(artifact) != args.sha:
            raise ValueError("Immutable save changed while reading")
    except Exception as error:
        report["result"] = "FAIL_READBACK"
        report["error"] = {"type": type(error).__name__, "message": str(error)}
    r3.write_fresh(output / "report.json", report)
    print(json.dumps({"result": report["result"], "report": str(output / "report.json"), "report_sha256": sha(output / "report.json"), "player_id": args.player_id}, indent=2))
    return 1 if report["result"].startswith("FAIL") else 0


if __name__ == "__main__":
    raise SystemExit(main())

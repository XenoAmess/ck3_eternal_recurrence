"""External read/preserve/check of explicit R3 checkpoints; no game operations.

`preserve` requires the exact native SHA and size. `inspect` requires the actual
native player ID and reads only an already-preserved content-addressed copy.
All parsing uses the existing lossless bounded save-block parser.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import shutil
import stat
import sys
import uuid

BASE = Path(__file__).resolve().parent
REPO = Path("C:/workspace/ck3_eternal_recurrence")
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
from xar_autoplayer.simulation.knight_causal_save_projection import extract_exact_indented_block, parse_block, block_body, one


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def inside(path: Path) -> Path:
    path = path.resolve()
    if BASE not in path.parents:
        raise ValueError("all artifact inputs/outputs must remain in this external task package")
    return path


def write_fresh(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def preserve(args) -> dict:
    source = inside(args.source)
    if not re.fullmatch(r"[0-9a-f]{64}", args.sha) or args.size <= 0:
        raise ValueError("explicit lowercase native SHA256 and positive byte size required")
    before = source.stat()
    if before.st_size != args.size or sha(source) != args.sha:
        raise RuntimeError("source bytes do not match the explicit native save receipt")
    directory = BASE / "preserved-checkpoints" / args.sha
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "xar_checkpoint.ck3"
    already_preserved = target.exists()
    if already_preserved:
        if target.stat().st_size != args.size or sha(target) != args.sha:
            raise RuntimeError("existing content-addressed artifact mismatch")
    else:
        with target.open("xb") as output, source.open("rb") as input_stream:
            shutil.copyfileobj(input_stream, output, 1024 * 1024)
    if target.stat().st_size != args.size or sha(target) != args.sha or sha(source) != args.sha:
        raise RuntimeError("checkpoint changed during preservation")
    target.chmod(stat.S_IREAD)
    receipt = {"schema": "ck3.lyd.r3-checkpoint-preservation.v1", "preserved_at_utc": now(), "source": str(source),
               "artifact": str(target), "bytes": args.size, "sha256": args.sha, "source_mtime_ns": before.st_mtime_ns,
               "artifact_read_only": True, "reused_exact_immutable_copy": already_preserved, "label": args.label,
               "game_called": False, "tracked_written": False}
    receipt_path = directory / ("preservation-" + uuid.uuid4().hex[:16] + ".json")
    write_fresh(receipt_path, receipt)
    return {**receipt, "receipt": str(receipt_path), "canonical_source_may_be_overwritten": True}


def section(text: str, key: str, following: str) -> str:
    starts = list(re.finditer(r"(?m)^" + re.escape(key) + r"=\{\n", text))
    ends = list(re.finditer(r"(?m)^" + re.escape(following) + r"=\{\n", text))
    if len(starts) != 1 or len(ends) != 1 or starts[0].start() >= ends[0].start():
        raise ValueError("required native save section boundary is not unique: " + key)
    return text[starts[0].start():ends[0].start()]


def parsed(raw: str) -> list[dict]:
    return parse_block(block_body(raw))


def unquote(value):
    return json.loads(value) if isinstance(value, str) and value.startswith('"') else value


def numeric(value):
    if isinstance(value, list):
        value = one(value, "value")
    if not isinstance(value, str):
        return None
    try:
        return str(Decimal(value))
    except InvalidOperation:
        return None


def variables(entries: list[dict]) -> list[dict]:
    rows = one(one(entries, "variables") or [], "data") or []
    result = []
    for row in rows:
        value = row["value"]
        if isinstance(value, list):
            flag = one(value, "flag")
            if isinstance(flag, str) and flag.startswith("lyd_"):
                result.append({"flag": flag, "tick": one(value, "tick"), "data": one(value, "data")})
    return result


def project(text: str, player_id: int, output: Path) -> dict:
    def block(key, source, depth, label):
        raw = extract_exact_indented_block(source, str(key), depth)
        (output / (label + ".excerpt.txt")).write_text(raw + "\n", encoding="utf-8")
        return parsed(raw)

    actor = block(player_id, section(text, "living", "dead_unprunable"), 0, "actual-player")
    alive = one(actor, "alive_data", required=True)
    metadata = block("meta_data", text, 0, "metadata")
    played = block("played_character", text, 0, "played-character")
    current = re.findall(r"(?m)^currently_played_characters=\{([^}]*)\}", text)
    lookup = section(text, "character_lookup", "deleted_characters")
    mappings = re.findall(r"(?m)^\t1128=(\d+)\s*$", lookup)
    rite_id = one(actor, "rite", required=True)
    rites = extract_exact_indented_block(text, "rites", 0)
    rite = block(rite_id, rites, 2, "actual-rite-" + rite_id)
    faith_id = one(rite, "faith", required=True)
    faiths = extract_exact_indented_block(text, "faiths", 0)
    faith = block(faith_id, faiths, 2, "actual-faith-" + faith_id)
    titles = section(text, "landed_titles", "dynasties")
    head_title_id = one(faith, "religious_head")
    head_holder = None
    if isinstance(head_title_id, str) and head_title_id != "4294967295":
        head_title = block(head_title_id, titles, 0, "faith-head-title-" + head_title_id)
        head_holder = one(head_title, "holder")
    dynasties = parsed(section(text, "dynasties", "character_lookup"))
    house_id = one(actor, "dynasty_house", required=True)
    house = one(one(dynasties, "dynasty_house", required=True), house_id, required=True)
    dynasty_id = one(house, "dynasty", required=True)
    dynasty = one(one(dynasties, "dynasties", required=True), dynasty_id, required=True)
    (output / "actual-house.entries.json").write_text(json.dumps(house, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    actor_vars = variables(alive)
    lifestyle = one(alive, "lifestyle_xp") or []
    learning_xp = one(lifestyle, "learning_lifestyle")
    values = {"gold": numeric(one(alive, "gold")), "piety": numeric(one(one(alive, "piety") or [], "currency")),
              "prestige": numeric(one(one(alive, "prestige") or [], "currency")),
              "stress": numeric(one(alive, "stress")), "learning_lifestyle_xp": numeric(learning_xp)}
    checks = {"saved_player_matches_actual_native_id": one(played, "character") == str(player_id) and len(current) == 1 and current[0].split() == [str(player_id)],
              "historical_1128_maps_to_actual_player": mappings == [str(player_id)],
              "name_robert": unquote(one(actor, "first_name")) == "Robert", "birth_1015_1_1": one(actor, "birth") == "1015.1.1",
              "house_hauteville": unquote(one(house, "name")) == "dynn_Hauteville", "historical_dynasty_678": one(dynasty, "key") == "678",
              "version_1_20_0_3": unquote(one(metadata, "version")) == "1.20.0.3"}
    return {"metadata": {key: unquote(one(metadata, key)) for key in ("version", "meta_date", "meta_player_name")},
            "player_id": player_id, "historical_mapping": {"1128": mappings}, "identity_checks": checks,
            "identity_status": "ACTUAL_ROBERT_VERIFIED" if all(checks.values()) else "IDENTITY_MISMATCH",
            "actor": {"first_name": unquote(one(actor, "first_name")), "birth": one(actor, "birth"), "nickname": one(actor, "nickname"), "dynasty_house": house_id,
                      "saved_house_name": unquote(one(house, "name")), "saved_dynasty_id": dynasty_id, "historical_dynasty_key": one(dynasty, "key")},
            "rite": {"id": rite_id, **{key: one(rite, key) for key in ("rite_type", "faith", "head_of_rite", "convert", "enabled", "source")}},
            "faith": {"id": faith_id, **{key: unquote(one(faith, key)) for key in ("faith_type", "main_rite", "religious_head", "name", "religion")}},
            "faith_head_title_holder": head_holder, "is_saved_faith_head": head_holder == str(player_id), "is_saved_rite_head": one(rite, "head_of_rite") == str(player_id),
            "lyd_variables": actor_vars, "lyd_flags": {key: any(row["flag"] == key for row in actor_vars) for key in ("lyd_r3_fixture_initialized", "lyd_enabled", "lyd_school_cooldown", "lyd_study_cooldown", "lyd_postcondition_failed")},
            "saved_values": values, "saved_value_presence": {"stress": one(alive, "stress") is not None, "learning_lifestyle_xp": learning_xp is not None},
            "saved_skill_array": one(actor, "skill"), "saved_lifestyle_xp_entries": lifestyle,
            "missing_numeric_value_policy": "null means not stored/readable; omitted stress or learning XP is not silently promoted to zero"}


def native_projection(path: Path, expected_sha: str, player_id: int) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if "sdk_result" in data:
        data = data["sdk_result"]
    if "structuredContent" in data:
        if data.get("isError") is True:
            raise RuntimeError("native SDK result is an error")
        data = data["structuredContent"]
    if not isinstance(data, dict) or data.get("schema") != "ck3.native-profile-receipt.v1":
        raise ValueError("use an exact native receipt or SDK structuredContent result")
    frame = data.get("snapshot_after", data.get("snapshot"))
    if not isinstance(frame, dict) or frame.get("played_character", {}).get("character_id") != player_id:
        raise ValueError("native receipt snapshot actor differs from explicit actual player ID")
    checkpoint = data.get("result", {}).get("checkpoint")
    if checkpoint is not None and checkpoint.get("sha256") != expected_sha:
        raise ValueError("native checkpoint SHA differs from this preserved artifact")

    def currency(key):
        entry = frame.get(key)
        if not isinstance(entry, dict) or type(entry.get("raw")) is not int or type(entry.get("scale")) is not int or entry["scale"] <= 0:
            return None
        return str(Decimal(entry["raw"]) / Decimal(entry["scale"]))

    return {"receipt_path": str(path), "receipt_sha256": sha(path), "status": data.get("status"), "checkpoint": checkpoint,
            "revision": frame.get("revision"), "date_raw": frame.get("date_raw"), "paused": frame.get("paused"),
            "values": {"gold": currency("played_character_gold"), "piety": currency("played_character_piety"), "prestige": currency("played_character_prestige"),
                       "stress": str(frame["played_character"]["stress_points"]) if frame["played_character"].get("stress_points") is not None else None,
                       "learning_lifestyle_xp": None},
            "learning_xp_status": "NOT_EXPOSED_BY_STANDARD_NATIVE_SNAPSHOT; use independent saved lifestyle_xp",
            "date_boundary": "native raw date and saved calendar retained separately; no old1.19 decoder used"}


def delta(previous: dict, current: dict) -> dict:
    same_actor = previous.get("state", {}).get("player_id") == current["player_id"]
    result = {"same_actor": same_actor}
    if not same_actor:
        return result
    old = previous["state"]
    result.update(previous_rite=old["rite"]["id"], current_rite=current["rite"]["id"], previous_faith=old["faith"]["id"], current_faith=current["faith"]["id"],
                  flag_changes={key: {"before": old["lyd_flags"].get(key), "after": value} for key, value in current["lyd_flags"].items()})
    result["numeric_changes"] = {key: {"before": old["saved_values"].get(key), "after": value,
                                       "delta": str(Decimal(value) - Decimal(old["saved_values"][key])) if value is not None and old["saved_values"].get(key) is not None else None}
                                 for key, value in current["saved_values"].items()}
    return result


def inspect(args) -> dict:
    artifact, output = inside(args.artifact), inside(args.output)
    expected_sha = artifact.parent.name
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha) or sha(artifact) != expected_sha:
        raise ValueError("inspect only an exact content-addressed preserved checkpoint")
    if args.native_player_id <= 0 or output.exists():
        raise ValueError("actual positive native player ID and fresh output directory required")
    output.mkdir(parents=True)
    text = artifact.read_bytes().decode("utf-8-sig").replace("\r\n", "\n")
    state = project(text, args.native_player_id, output)
    report = {"schema": "ck3.lyd.r3-checkpoint-readback.v1", "recorded_at_utc": now(), "label": args.label,
              "artifact": {"path": str(artifact), "bytes": artifact.stat().st_size, "sha256": expected_sha}, "state": state,
              "game_called": False, "tracked_written": False, "live_acceptance": "NOT_GRADED_BY_THIS_FILE_READER"}
    if args.native_receipt:
        report["native"] = native_projection(inside(args.native_receipt), expected_sha, args.native_player_id)
        report["native_saved_comparison"] = {key: {"native": value, "saved": state["saved_values"].get(key),
                                                    "equal": Decimal(value) == Decimal(state["saved_values"][key]) if value is not None and state["saved_values"].get(key) is not None else None}
                                             for key, value in report["native"]["values"].items()}
    if args.compare:
        previous_path = inside(args.compare)
        previous = json.loads(previous_path.read_text(encoding="utf-8"))
        if previous.get("schema") != report["schema"]:
            raise ValueError("--compare must be an earlier R3 checkpoint readback report")
        report["previous_report"] = {"path": str(previous_path), "sha256": sha(previous_path)}
        report["comparison"] = delta(previous, state)
    if args.log:
        log = inside(args.log)
        raw = log.read_bytes()
        (output / "debug-log.captured.bin").write_bytes(raw)
        report["log"] = {"source": str(log), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                         "markers": [match.group().decode("ascii") for match in re.finditer(rb"LYD[A-Z0-9_]+", raw)],
                         "boundary": "whole captured log markers; sequence/phase attribution requires root review"}
    write_fresh(output / "report.json", report)
    return {"report": str(output / "report.json"), "report_sha256": sha(output / "report.json"), "identity_status": state["identity_status"],
            "player_id": state["player_id"], "rite": state["rite"], "faith": state["faith"], "is_faith_head": state["is_saved_faith_head"], "is_rite_head": state["is_saved_rite_head"],
            "flags": state["lyd_flags"], "saved_values": state["saved_values"], "comparison": report.get("comparison"), "game_called": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    freeze = commands.add_parser("preserve")
    freeze.add_argument("--source", type=Path, default=BASE / "live-attempt-003/userdir/save games/xar_checkpoint.ck3")
    freeze.add_argument("--sha", required=True)
    freeze.add_argument("--size", type=int, required=True)
    freeze.add_argument("--label", default="R3 checkpoint")
    read = commands.add_parser("inspect")
    read.add_argument("--artifact", type=Path, required=True)
    read.add_argument("--native-player-id", type=int, required=True)
    read.add_argument("--native-receipt", type=Path)
    read.add_argument("--compare", type=Path)
    read.add_argument("--log", type=Path)
    read.add_argument("--output", type=Path, required=True)
    read.add_argument("--label", default="R3 readback")
    args = parser.parse_args()
    result = preserve(args) if args.command == "preserve" else inspect(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get("identity_status") == "IDENTITY_MISMATCH" else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())

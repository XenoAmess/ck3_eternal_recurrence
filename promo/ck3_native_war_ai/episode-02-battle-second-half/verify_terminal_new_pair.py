"""Append-only static check of a new E2-09 candidate; never launches CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
CONFIG = HERE / "terminal-new-pair-inputs.json"
REQUIRED_DLL_STRINGS = (
    "game.state.snapshot",
    "game.state.map-ready",
    "game.state.played-character",
    "query-battle-terminal-transition-v1",
    "denominator_inputs",
    "selected_cb_battle_scale_raw_q100000",
)


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def identity(spec: dict, errors: list[str], label: str) -> dict:
    path = Path(spec["path"])
    observed = {"path": str(path), "exists": path.is_file()}
    if not observed["exists"]:
        errors.append(f"{label} missing: {path}")
        return observed
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    observed.update(bytes=path.stat().st_size, sha256=digest.hexdigest().upper())
    if "bytes" in spec and observed["bytes"] != spec["bytes"]:
        errors.append(f"{label} size mismatch")
    if "sha256" in spec and observed["sha256"] != spec["sha256"]:
        errors.append(f"{label} SHA mismatch")
    return observed


def pe_x64(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 0x40 or data[:2] != b"MZ":
        return {"pe_x64": False, "reason": "missing MZ"}
    offset = struct.unpack_from("<I", data, 0x3C)[0]
    if offset + 26 > len(data) or data[offset:offset + 4] != b"PE\0\0":
        return {"pe_x64": False, "reason": "missing PE"}
    machine = struct.unpack_from("<H", data, offset + 4)[0]
    optional_magic = struct.unpack_from("<H", data, offset + 24)[0]
    return {"machine_hex": f"0x{machine:04X}",
            "optional_magic_hex": f"0x{optional_magic:03X}",
            "pe_x64": machine == 0x8664 and optional_magic == 0x20B}


def check_data(config: dict) -> dict:
    errors: list[str] = []
    records = {}
    for key in ("game_exe", "source_save", "source_receipt",
                "candidate_bridge_dll", "candidate_bridge_injector",
                "war_unavailable_response"):
        records[key] = identity(config[key], errors, key)
    expected = config["identity"]
    if config["candidate_bridge_dll"]["sha256"] == config["historical_024_dll_expected_sha256"]:
        errors.append("candidate must have a new DLL identity, separate from historical 024")
    if records["source_receipt"]["exists"]:
        receipt = json.loads(Path(config["source_receipt"]["path"]).read_text(encoding="utf-8"))
        body = receipt.get("body") or {}
        checkpoint = body.get("checkpoint") or {}
        hello = (receipt.get("driver_state") or {}).get("hello") or {}
        lifecycle = checkpoint.get("succession_lifecycle") or {}
        if not (receipt.get("result") == "CALL_COMPLETED" and body.get("step") == "save-checkpoint" and
                body.get("accepted") is True and checkpoint.get("status") == "saved" and
                str(checkpoint.get("sha256", "")).upper() == config["source_save"]["sha256"] and
                checkpoint.get("size") == config["source_save"]["bytes"] and
                checkpoint.get("date_raw") == expected["source_date_raw"] and
                checkpoint.get("episode_character_id") == expected["actor"] and
                lifecycle.get("source") == "pure-vanilla-enabled-mods-empty" and
                hello.get("ck3_build_match") is True and
                hello.get("expected_ck3_sha256") == config["game_exe"]["sha256"]):
            errors.append("actual source save-checkpoint receipt binding mismatch")
    if records["war_unavailable_response"]["exists"]:
        response = json.loads(Path(config["war_unavailable_response"]["path"]).read_text(encoding="utf-8"))
        if not (response.get("status") == "unavailable" and
                response.get("preserve_receiver_red") is True and
                response.get("requested_sha256") == config["historical_024_dll_expected_sha256"] and
                response.get("requested_bytes") == config["candidate_bridge_dll"]["bytes"]):
            errors.append("WAR unavailable response mismatch")
    if records["candidate_bridge_dll"]["exists"]:
        dll_path = Path(config["candidate_bridge_dll"]["path"])
        blob = dll_path.read_bytes()
        records["candidate_bridge_dll"]["static_capability_strings"] = {
            value: value.encode("ascii") in blob for value in REQUIRED_DLL_STRINGS
        }
        records["candidate_bridge_dll"]["pe"] = pe_x64(dll_path)
        if not all(records["candidate_bridge_dll"]["static_capability_strings"].values()):
            errors.append("candidate DLL lacks required static command/writer strings")
        if not records["candidate_bridge_dll"]["pe"]["pe_x64"]:
            errors.append("candidate DLL is not x64 PE32+")
    if records["candidate_bridge_injector"]["exists"]:
        injector_path = Path(config["candidate_bridge_injector"]["path"])
        records["candidate_bridge_injector"]["pe"] = pe_x64(injector_path)
        if not records["candidate_bridge_injector"]["pe"]["pe_x64"]:
            errors.append("candidate injector is not x64 PE32+")
    preservation = config["war_response_preservation_receipt"]
    records["war_response_preservation_receipt"] = identity(preservation, errors,
                                                             "war_response_preservation_receipt")
    if records["war_response_preservation_receipt"]["exists"]:
        receipt = json.loads(Path(preservation["path"]).read_text(encoding="utf-8"))
        response_rows = [row for row in receipt.get("files", []) if row.get("name") == "RESPONSE.json"]
        if not (receipt.get("status") == "unavailable" and receipt.get("exact_dll_received") is False and
                len(response_rows) == 1 and
                response_rows[0].get("sha256") == config["war_unavailable_response"]["sha256"]):
            errors.append("WAR response preservation receipt mismatch")
    return {"schema": "xar.war-ai.episode02.terminal-new-pair-static-preflight.v1",
            "observed_at_utc": utc(), "result": "STATIC_MATERIAL_GREEN_LIVE_UNPROVEN" if not errors else
            "STATIC_MATERIAL_RED", "new_attempt_required": True,
            "historical_024_material_red_preserved": True, "ck3_launch_attempted": False,
            "desktop_capture_attempted": False, "source_identity": expected,
            "files": records, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    config_bytes = CONFIG.read_bytes()
    with (args.output_dir / "input-config.json").open("xb") as output:
        output.write(config_bytes)
    save_json(args.output_dir / "command.json", {
        "at": utc(), "python": sys.executable, "argv": sys.argv,
        "config_sha256": hashlib.sha256(config_bytes).hexdigest().upper(),
        "ck3_launch_requested": False})
    try:
        config = json.loads(config_bytes)
        if config["schema"] != "xar.war-ai.episode02.terminal-new-pair-inputs.v1":
            raise ValueError("config schema")
        report = check_data(config)
        save_json(args.output_dir / "preflight.json", report)
        print(json.dumps({"result": report["result"], "errors": report["errors"]},
                         ensure_ascii=False))
        return 0 if not report["errors"] else 1
    except BaseException as error:
        save_json(args.output_dir / "entry-failure.json", {
            "at": utc(), "result": "RED", "error": repr(error),
            "ck3_launch_attempted": False})
        print(json.dumps({"result": "RED", "error": repr(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

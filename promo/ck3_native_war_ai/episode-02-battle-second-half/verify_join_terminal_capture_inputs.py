"""Append-only, no-launch source-material preflight for Episode 2 tracks 085/024.

Only Python stdlib reads local files and the read-only Windows tasklist. This does
not call capture_session, attach to CK3, acquire the screen, or record desktop.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "join-terminal-capture-inputs.json"
CAPABILITIES = ("game.state.snapshot", "game.state.map-ready",
                "game.state.played-character")
PRIVATE_PHASE_CAPABILITIES = ("experimental-combat-phase-event-trace-begin-v1",
                              "experimental-combat-phase-event-trace-finish-v1")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_new(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def digest_file(path: Path) -> dict:
    result = {"path": str(path), "exists": path.is_file()}
    if not result["exists"]:
        return result
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {**result, "bytes": path.stat().st_size, "sha256": digest.hexdigest().upper()}


def check_file(label: str, spec: dict, records: dict, errors: list[str]) -> Path:
    path = Path(spec["path"])
    observed = digest_file(path)
    observed["expected_sha256"] = spec["sha256"].upper()
    observed["match"] = observed.get("sha256") == observed["expected_sha256"]
    records[label] = observed
    if not observed["match"]:
        errors.append(f"{label}: missing or SHA mismatch: {path}")
    return path


def check_anchored(label: str, path: Path, records: dict, errors: list[str]) -> dict | None:
    records[label] = digest_file(path)
    if not records[label]["exists"]:
        errors.append(f"{label}: missing: {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        errors.append(f"{label}: invalid JSON: {error}")
        return None


def need(condition: bool, label: str, errors: list[str]) -> None:
    if not condition:
        errors.append(label)


def process_inventory() -> dict:
    command = ["tasklist", "/NH", "/FO", "CSV", "/FI", "IMAGENAME eq ck3.exe"]
    try:
        completed = subprocess.run(command, capture_output=True, text=True,
                                   timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"command": command, "status": "unknown", "error": repr(error)}
    rows = list(csv.reader(io.StringIO(completed.stdout)))
    pids = []
    for row in rows:
        if len(row) >= 2 and row[0].lower() == "ck3.exe" and row[1].isdigit():
            pids.append(int(row[1]))
    return {"command": command, "returncode": completed.returncode,
            "ck3_pids": pids, "status": "occupied" if pids else
            "unoccupied" if completed.returncode == 0 else "unknown",
            "stderr": completed.stderr.strip()}


def inspect(track: str, config: dict) -> dict:
    candidate = config["tracks"][track]
    other = config["tracks"]["024" if track == "085" else "085"]
    errors: list[str] = []
    files: dict = {}
    need(candidate["source_save"]["sha256"] != other["source_save"]["sha256"],
         "085 and 024 source saves must stay distinct", errors)
    check_file("game_exe", config["game_exe"], files, errors)
    check_file("source_save", candidate["source_save"], files, errors)
    receipt_path = check_file("source_receipt", candidate["source_receipt"], files, errors)
    dll_path = check_file("bridge_dll", candidate["bridge_dll"], files, errors)
    check_file("bridge_injector", candidate["bridge_injector"], files, errors)
    check_file("historical_result", candidate["historical_result"], files, errors)
    report = check_anchored("historical_capture_report",
                            Path(candidate["historical_capture_report"]), files, errors)
    copy = check_anchored("historical_checkpoint_copy",
                          Path(candidate["historical_checkpoint_copy"]), files, errors)
    receipt = None
    if files["source_receipt"]["exists"]:
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            errors.append(f"source_receipt: invalid JSON: {error}")
    if receipt is not None:
        body = receipt.get("body") or {}
        saved = body.get("checkpoint") or {}
        hello = (receipt.get("driver_state") or {}).get("hello") or {}
        lifecycle = saved.get("succession_lifecycle") or {}
        need(receipt.get("result") == "CALL_COMPLETED" and
             body.get("step") == "save-checkpoint" and body.get("accepted") is True and
             saved.get("status") == "saved", "source receipt is not a completed native save", errors)
        need(str(saved.get("sha256", "")).upper() == candidate["source_save"]["sha256"] and
             saved.get("size") == files["source_save"].get("bytes") and
             saved.get("date_raw") == candidate["date_raw"] and
             saved.get("episode_character_id") == candidate["actor"],
             "saved bytes/size/date/actor do not match immutable source", errors)
        need(lifecycle.get("source") == "pure-vanilla-enabled-mods-empty" and
             lifecycle.get("xar_enabled") == "xar_off" and
             hello.get("ck3_build_match") is True and
             hello.get("expected_ck3_sha256") == config["game_exe"]["sha256"],
             "source lifecycle or exact-build hello mismatch", errors)
    if report is not None:
        source = report.get("checkpoint_source") or {}
        need((source.get("save") or {}).get("sha256") == candidate["source_save"]["sha256"] and
             (source.get("receipt") or {}).get("sha256") == candidate["source_receipt"]["sha256"] and
             source.get("actor") == candidate["actor"] and
             source.get("date_raw") == candidate["date_raw"],
             "historical capture checkpoint provenance mismatch", errors)
        need(report.get("raw_video") is None and
             report.get("recording_complete") is False and
             report.get("clean_spans") == [] and
             report.get("adapter_bundle_validated") is False,
             "historical media gap changed; re-review report", errors)
    if copy is not None:
        source = copy.get("source") or {}
        need((source.get("save") or {}).get("sha256") == candidate["source_save"]["sha256"] and
             (source.get("receipt") or {}).get("sha256") == candidate["source_receipt"]["sha256"] and
             (copy.get("profile_copy") or {}).get("sha256") == candidate["source_save"]["sha256"] and
             (copy.get("receipt_copy") or {}).get("sha256") == candidate["source_receipt"]["sha256"] and
             copy.get("old_attempt_modified") is False,
             "historical checkpoint copy binding mismatch", errors)
    if files["bridge_dll"]["exists"]:
        binary = dll_path.read_bytes()
        required = CAPABILITIES + (PRIVATE_PHASE_CAPABILITIES if
                                   candidate["requires_private_phase_trace"] else ())
        strings = {name: name.encode("ascii") in binary for name in required}
        files["bridge_dll"]["static_capability_strings"] = strings
        need(all(strings.values()), "historical DLL lacks required static capability strings", errors)
    inventory = process_inventory()
    return {"schema": "xar.war-ai.episode02.join-terminal-no-launch-preflight.v1",
            "observed_at": now(), "track": track, "role": candidate["role"],
            "source_date_raw": candidate["date_raw"], "actor": candidate["actor"],
            "combat_id": candidate["combat_id"], "war_id": candidate["war_id"],
            "files": files, "historical_media": {
                "raw_video": report.get("raw_video") if report else "unknown",
                "recording_complete": report.get("recording_complete") if report else "unknown",
                "clean_spans": report.get("clean_spans") if report else "unknown",
            }, "process_inventory": inventory, "errors": errors,
            "material_result": "GREEN" if not errors else "RED",
            "recording_gate": "SCREEN_OCCUPIED" if inventory["status"] == "occupied" else
            "SCREEN_UNVERIFIED", "ck3_launch_attempted": False,
            "desktop_capture_attempted": False, "live_capture_authorized": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--track", choices=("085", "024"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    source_bytes = CONFIG.read_bytes()
    with (args.output_dir / "input-config.json").open("xb") as stream:
        stream.write(source_bytes)
    write_new(args.output_dir / "command.json", {
        "at": now(), "python": sys.executable, "argv": sys.argv,
        "config_sha256": hashlib.sha256(source_bytes).hexdigest().upper(),
        "ck3_launch_requested": False,
    })
    try:
        config = json.loads(source_bytes)
        if config["schema"] != "xar.war-ai.episode02.join-terminal-no-launch-inputs.v1":
            raise ValueError("input schema")
        report = inspect(args.track, config)
        write_new(args.output_dir / "preflight.json", report)
        print(json.dumps({"track": args.track, "material_result": report["material_result"],
                          "recording_gate": report["recording_gate"],
                          "errors": report["errors"]}, ensure_ascii=False))
        return 0 if report["material_result"] == "GREEN" else 1
    except BaseException as error:
        failure = {"at": now(), "result": "RED", "error": repr(error),
                   "ck3_launch_attempted": False}
        write_new(args.output_dir / "entry-failure.json", failure)
        print(json.dumps(failure, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

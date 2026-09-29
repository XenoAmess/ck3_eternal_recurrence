"""E2-04 d06 second-session operator: one paused, read-only current-knight frame.

This helper never starts CK3, records, advances time, or clicks the desktop.
Each managed request and result is create-exclusive. A failed/unknown request
must be inspected in place; this helper never retries it.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
from typing import Any

from pursuit_live_step import call, identity, utc, write_new


SAVE = "F05A48A0839E76DD05D053FACBA524405FD547DD0A6CA07396ADB8ABE42A0B5A"
SIDECAR = "85C226E247AF4D32E246DCCF9F4C7323106D3A6BD0F12FCB883ABE843D3B785B"
DLL = "9B6EB4E8E77AB5EF8DFE211F5A2FAF20DC42A912887874E5D836C659DD75F1FE"
INJECTOR = "90078D708C74F05FEDB29D6AA232902E3230282F48D32D6361742A797EF81735"
EXE = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
GUI_SOURCE = "E6AD4D44435F17B77C6A5BD6554AB812FBF396D9A27370DB7CF9B56D658FDF7D"
GUI_BLOCK = "F5172E8A9DC92E8998957B5F443575608D04AC44342CE085DF23370CDA26F593"
GUI_RECEIPT = "69F4535E4FDA428E910CBE6F3B44C70E352853535A2D546CB71AA09CEA941779"
LEGACY_A02_ROOT = Path("D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d06-knight-preflight-20260929-a02")
CHECKOUT = Path(__file__).resolve().parents[3]
CAPTURE_SCRIPT = Path(__file__).resolve().parents[1] / "integration" / "capture_session.py"
ADMISSION_SCHEMA = "xar.war-promo.d06-knight-no-launch-admission/v1"
SAVE_PATH = Path("D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d05-live-20260929-a08/e2-04-d06-postframe-preservation-a01/d06-immutable.ck3")
SIDECAR_PATH = Path("D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d05-live-20260929-a08/ck3-output/interactive-requests-responses/e2-04-d05-postframe-save.json")
ACTOR, WAR, ARMY, COMBAT, PROVINCE, DATE = 29829, 4, 18, 16777218, 2633, 53146368
CHARACTER, REGIMENT = 34333, 61


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def sha(row: Any) -> str:
    return str(row.get("sha256", "")).upper() if isinstance(row, dict) else ""


def read(path: Path) -> dict[str, Any]:
    row = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(row, dict), f"expected JSON object: {path}")
    return row


def bound_source(row: Any, label: str) -> None:
    require(isinstance(row, dict) and sha(row.get("save")) == SAVE and
            sha(row.get("receipt")) == SIDECAR and row.get("actor") == ACTOR and
            row.get("date_raw") == DATE and
            row.get("source_episode_run_id") == "native-29829-0a9929135691",
            f"{label}: frozen d06 pair or actor/date/run differs")
    require(row["save"] == identity(SAVE_PATH) and
            row["receipt"] == identity(SIDECAR_PATH),
            f"{label}: source path/bytes differ from frozen a08 originals")


def no_launch_binding(root: Path) -> dict[str, Any]:
    require(root.name.startswith("episode02-e2-04-d06-knight-preflight-20260929-") and
            root.resolve() != LEGACY_A02_ROOT.resolve(),
            "fresh exact d06 no-launch attempt required; historical a02 is excluded")
    paths = {"result": root / "run-result.json", "argv": root / "run-argv.json",
             "preflight": root / "ck3-output" / "preflight.json",
             "command": root / "ck3-output" / "command.json",
             "stdout": root / "run-stdout.txt", "stderr": root / "run-stderr.txt"}
    records = {name: identity(path) for name, path in paths.items()}
    result, argv, preflight, command = (read(paths[name]) for name in
                                        ("result", "argv", "preflight", "command"))
    head = subprocess.check_output(["git", "-C", str(CHECKOUT), "rev-parse", "HEAD"],
                                   text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(CHECKOUT), "status", "--short",
                                     "--untracked-files=no"], text=True).strip()
    command_line = argv.get("argv")
    require(isinstance(command_line, list) and len(command_line) >= 3 and
            command_line[1] == str(CAPTURE_SCRIPT) and
            command.get("argv") == command_line[1:] and
            command.get("python") == command_line[0] == preflight.get("python", {}).get("path") and
            argv.get("checkout_head") == head and not dirty and
            argv.get("capture_script_sha256") == identity(CAPTURE_SCRIPT)["sha256"],
            "no-launch checkout commit, script bytes, interpreter or argv differ")
    require(result.get("exit_code") == 0 and result.get("ck3_started_by_command") is False and
            result.get("stdout_sha256") == records["stdout"]["sha256"] and
            result.get("stderr_sha256") == records["stderr"]["sha256"] and
            argv.get("capture") is False and
            preflight.get("result") == "READY_FOR_BOUNDED_LIVE_ATTEMPT" and
            preflight.get("ck3_started") is False,
            "no-launch result is not a completed READY admission")
    flags = command_line[2:]
    require("--capture" not in flags and "--enable-private-phase-trace" not in flags and
            "--battle-control-pair-manifest" not in flags,
            "d06 no-launch argv includes a launch, trace or d11-only flag")
    required = {"--game-dir", "--bridge-dll", "--bridge-injector", "--state-dir",
                "--output-dir", "--pipe-name", "--checkpoint-save", "--checkpoint-receipt",
                "--frontend-timeout", "--gui-scale", "--import-a04-ui-gui-100",
                "--a04-ui-settings-snapshot", "--a04-ui-preservation-receipt",
                "--recovery-seconds", "--interactive-seconds", "--hold-seconds"}
    arguments: dict[str, str | bool] = {}
    index = 0
    while index < len(flags):
        flag = flags[index]
        require(flag in required and flag not in arguments, "no-launch argv has extra or duplicate flags")
        if flag == "--import-a04-ui-gui-100":
            arguments[flag] = True
            index += 1
        else:
            require(index + 1 < len(flags), f"no-launch {flag} has no value")
            arguments[flag] = flags[index + 1]
            index += 2
    require(set(arguments) == required and
            Path(str(arguments["--state-dir"])).resolve() == (root / "ck3-state").resolve() and
            Path(str(arguments["--output-dir"])).resolve() == (root / "ck3-output").resolve() and
            Path(str(arguments["--checkpoint-save"])).resolve() == SAVE_PATH.resolve() and
            Path(str(arguments["--checkpoint-receipt"])).resolve() == SIDECAR_PATH.resolve() and
            str(arguments["--frontend-timeout"]) == "900" and
            str(arguments["--gui-scale"]) == "1.0" and
            str(arguments["--recovery-seconds"]) == "1800" and
            str(arguments["--interactive-seconds"]) == "3600" and
            str(arguments["--hold-seconds"]) == "60" and
            str(arguments["--pipe-name"]).startswith(r"\\.\pipe\xar_ck3_e204_d06_knight_preflight_"),
            "no-launch inputs are not the exact d06 pair and bounded settings")
    verify_preflight(preflight)
    require(Path(str(arguments["--bridge-dll"])).resolve() ==
            Path(preflight["bridge_dll"]["path"]).resolve() and
            Path(str(arguments["--bridge-injector"])).resolve() ==
            Path(preflight["bridge_injector"]["path"]).resolve() and
            Path(str(arguments["--a04-ui-settings-snapshot"])).resolve() ==
            Path(preflight["a04_ui_gui_source_binding"]["source_snapshot"]["path"]).resolve() and
            Path(str(arguments["--a04-ui-preservation-receipt"])).resolve() ==
            Path(preflight["a04_ui_gui_source_binding"]["preservation_receipt"]["path"]).resolve(),
            "no-launch argv and preflight asset paths differ")
    return {"schema": ADMISSION_SCHEMA, "root": str(root.resolve()),
            "checkout_head": head, "capture_script": identity(CAPTURE_SCRIPT),
            "bridge_dll": preflight["bridge_dll"],
            "bridge_injector": preflight["bridge_injector"],
            "save": identity(SAVE_PATH), "sidecar": identity(SIDECAR_PATH),
            "argv": command_line, "records": records, "ck3_started": False}


def seal_no_launch(root: Path) -> dict[str, Any]:
    binding = no_launch_binding(root)
    write_new(root / "admission-lock.json", binding)
    return binding


def verify_no_launch(root: Path) -> dict[str, Any]:
    binding = no_launch_binding(root)
    require(read(root / "admission-lock.json") == binding,
            "no-launch admission lock differs from current exact bytes")
    records = binding["records"]
    return {"result": records["result"], "argv": records["argv"],
            "preflight": records["preflight"], "admission_lock": identity(root / "admission-lock.json"),
            "checkout_head": binding["checkout_head"],
            "capture_script_sha256": binding["capture_script"]["sha256"]}


def verify_preflight(preflight: dict[str, Any]) -> None:
    bound_source(preflight.get("checkpoint_source"), "preflight")
    require((sha(preflight.get("game")), sha(preflight.get("bridge_dll")),
             sha(preflight.get("bridge_injector"))) == (EXE, DLL, INJECTOR),
            "preflight EXE/bridge pair differs")
    for label in ("game", "bridge_dll", "bridge_injector"):
        row = preflight[label]
        require(identity(Path(row["path"])) == row,
                f"preflight {label} file changed")
    gui = preflight.get("a04_ui_gui_source_binding") or {}
    require(gui.get("opt_in") is True and
            sha(gui.get("source_snapshot")) == GUI_SOURCE and
            gui.get("expected_source_sha256") == GUI_SOURCE and
            gui.get("expected_gui_block_sha256") == GUI_BLOCK and
            sha(gui.get("preservation_receipt")) == GUI_RECEIPT,
            "preflight lacks exact native UI 100% source binding")
    for label in ("source_snapshot", "preservation_receipt", "hot_readback"):
        row = gui.get(label)
        require(isinstance(row, dict) and identity(Path(row["path"])) == row,
                f"native UI {label} evidence changed")
    images = gui.get("original_ui_images") or {}
    require(len(images) == 5 and all(identity(Path(row["path"])) == row
                                     for row in images.values()),
            "native UI original image evidence changed")


def verify_gui(output: Path) -> dict[str, Any]:
    receipts = {}
    for filename_phase, receipt_phase in (("before-native-session", "before-native-session"),
                                          ("postmap", "postmap-before-capture"),
                                          ("posthold", "posthold-before-service")):
        path = output / f"gui-settings-{filename_phase}.json"
        row = read(path)
        require(row.get("phase") == receipt_phase and row.get("disk_gate_passed") is True and
                row.get("observed_scale_serialized") == "1" and
                row.get("native_ui_one_opt_in") is True and
                row.get("native_a04_gui_block_required") is True and
                row.get("native_a04_gui_block_passed") is True and
                row.get("native_a04_gui_block_sha256") == GUI_BLOCK,
                f"{filename_phase}: native 54-byte GUI block or disk gate differs")
        receipts[filename_phase] = identity(path)
    return receipts


def verify_session(output: Path, no_launch: Path, *, require_gui: bool = True) -> dict[str, Any]:
    require(output.name == "ck3-output" and output.parent.name.startswith(
            "episode02-e2-04-d06-knight-live-20260929-"),
            "output must belong to a new d06 knight live attempt")
    prior = verify_no_launch(no_launch)
    preflight_path, loaded_path, command_path = (
        output / "preflight.json", output / "native-start-readback.json", output / "command.json")
    preflight, loaded, command = read(preflight_path), read(loaded_path), read(command_path)
    require(preflight.get("result") == "READY_FOR_BOUNDED_LIVE_ATTEMPT" and
            loaded.get("postcondition_verified") is True, "managed d06 cold load not verified")
    verify_preflight(preflight)
    bound_source(loaded.get("source_checkpoint"), "managed load")
    argv = command.get("argv")
    require(isinstance(argv, list) and "--capture" in argv and
            "--enable-private-phase-trace" not in argv and
            "--steam-offline-receipt" in argv,
            "live argv lacks capture/fresh offline receipt or enables unsupported trace")
    require(Path(argv[0]).resolve() == Path(read(no_launch / "run-argv.json")["argv"][1]).resolve() and
            sha(identity(Path(argv[0]))) == prior["capture_script_sha256"],
            "live capture script differs from READY no-launch code")
    offline_index = argv.index("--steam-offline-receipt")
    require(offline_index + 1 < len(argv), "missing live Steam receipt path")
    offline = Path(argv[offline_index + 1])
    require(offline.is_file() and offline.parent.name.startswith(
            "episode02-e2-04-d06-knight-offline-20260929-"),
            "live Steam receipt must be a fresh d06 knight offline attempt")
    require((output / "interactive-requests").is_dir() and
            (output / "interactive-requests-responses").is_dir(),
            "managed request directories missing")
    return {"no_launch": prior, "preflight": identity(preflight_path),
            "managed_load": identity(loaded_path), "command": identity(command_path),
            "steam_receipt": identity(offline),
            "gui": verify_gui(output) if require_gui else "not_a_cleanup_prerequisite",
            "operator": identity(Path(__file__)),
            "request_primitive": identity(Path(__file__).with_name("pursuit_live_step.py"))}


def snapshot_case(body: dict[str, Any]) -> dict[str, Any]:
    wars = [row for row in body.get("active_wars", []) if isinstance(row, dict)]
    matching_wars = [row for row in wars if row.get("war_id") == WAR]
    armies = matching_wars[0].get("allied_armies", []) if len(matching_wars) == 1 else []
    matching_armies = [row for row in armies if isinstance(row, dict) and row.get("army_id") == ARMY]
    army = matching_armies[0] if len(matching_armies) == 1 else {}
    values = {"date_raw": body.get("date_raw"), "paused": body.get("paused"),
              "actor": (body.get("played_character") or {}).get("character_id"),
              "revision": body.get("revision"), "native_revision": body.get("native_revision"),
              "snapshot_id": body.get("snapshot_id"), "war_count": len(matching_wars),
              "army_count": len(matching_armies), "army_state": army.get("army_state"),
              "army_province": army.get("current_province_id"),
              "army_controllable": army.get("controllable"),
              "army_in_combat": army.get("in_combat")}
    require(values["date_raw"] == DATE and values["paused"] is True and
            values["actor"] == ACTOR and values["war_count"] == 1 and
            values["army_count"] == 1 and values["army_state"] == "combat" and
            values["army_province"] == PROVINCE and
            values["army_controllable"] is True and
            values["army_in_combat"] is True and
            type(values["revision"]) is int and values["revision"] > 0 and
            type(values["native_revision"]) is int and values["native_revision"] > 0 and
            values["snapshot_id"] == f"native:{values['native_revision']}",
            f"d06 paused snapshot identity differs: {values}")
    return values


def control_case(body: dict[str, Any], frame: dict[str, Any]) -> dict[str, Any]:
    row, source = body.get("battle_control_snapshot") or {}, body.get("source") or {}
    require(body.get("accepted") is True and body.get("status") == "available" and
            row.get("status") == "available" and row.get("battle_control_ready") is True and
            body.get("queried_revision") == source.get("revision") == frame["revision"] and
            body.get("queried_native_revision") == source.get("native_revision") ==
            body.get("snapshot_revision") == row.get("snapshot_revision") == frame["native_revision"] and
            body.get("queried_snapshot_id") == source.get("snapshot_id") == frame["snapshot_id"] and
            source.get("paused") is True and source.get("date_raw") ==
            row.get("observed_date_raw") == DATE and
            row.get("subject_public_cunit_id") == row.get("subject_native_carmy_id") == ARMY and
            row.get("selected_owner_character_id") == ACTOR and
            row.get("combat_id") == COMBAT and row.get("combat_province_id") == PROVINCE,
            "battle control is not the paused d06 same frame")
    defender = row.get("defender") or {}
    entries = defender.get("men_at_arms_entries") or []
    matching = [entry for entry in entries if isinstance(entry, dict) and
                entry.get("regiment_id") == REGIMENT]
    require(len(matching) == 1, "defender has no unique RegimentID 61")
    return {"revision": frame["revision"], "native_revision": frame["native_revision"],
            "snapshot_id": frame["snapshot_id"], "combat_id": COMBAT,
            "regiment_61_stored_entry": matching[0]}


def knight_case(body: dict[str, Any], frame: dict[str, Any]) -> dict[str, Any]:
    row, source = body.get("current_battle_knight") or {}, body.get("source") or {}
    expected = {"observed_date_raw": DATE, "combat_id": COMBAT, "province_id": PROVINCE,
                "subject_public_cunit_id": ARMY, "native_carmy_id": ARMY,
                "character_id": CHARACTER, "regiment_id": REGIMENT}
    require(body.get("accepted") is True and body.get("status") == "available" and
            body.get("queried_revision") == source.get("revision") == frame["revision"] and
            body.get("queried_native_revision") == source.get("native_revision") ==
            body.get("snapshot_revision") == frame["native_revision"] and
            body.get("queried_snapshot_id") == source.get("snapshot_id") == frame["snapshot_id"] and
            row.get("schema") == "current-battle-knight-v1" and
            all(type(row.get(key)) is int and row[key] == value for key, value in expected.items()) and
            row.get("paired_generation_ids_verified") is True and
            row.get("double_sample_stable") is True and
            row.get("province_evaluation_fresh") is True and row.get("scale") == 100000,
            "current-knight query is not an exact paired d06 frame")
    numbers = ("current_effective_prowess", "knight_effectiveness_raw",
               "province_evaluated_damage_raw", "province_evaluated_toughness_raw",
               "stored_combat_entry_damage_raw", "stored_combat_entry_toughness_raw")
    require(all(type(row.get(key)) is int for key in numbers), "current-knight values missing")
    return {key: row[key] for key in (*expected, *numbers, "scale")}


def observe(output: Path, binding: dict[str, Any], timeout: float) -> int:
    steps = output / "operator-steps"
    target = steps / "e2-04-d06-knight-observe.json"
    intent = steps / "e2-04-d06-knight-observe-intent.json"
    require(not target.exists() and not intent.exists(), "observe already attempted")
    write_new(intent, {"schema": "xar.war-promo.d06-current-knight-intent/v1",
                       "created_at": utc(), "source_binding": binding,
                       "actions": ["snapshot", "battle-control", "current-knight", "snapshot"],
                       "game_mutation": False, "retry_on_unknown": False})
    receipts: dict[str, Any] = {}
    values: dict[str, Any] = {}
    try:
        first, receipts["snapshot"] = call(output, "e204-d06-knight-snapshot",
                                             "ck3_take_snapshot", {}, timeout)
        frame = snapshot_case(first)
        values["frame"] = frame
        control, receipts["control"] = call(
            output, "e204-d06-knight-control", "ck3_query_battle_control_snapshot_v1",
            {"subject_army_id": ARMY, "expected_revision": frame["revision"]}, timeout)
        values["control"] = control_case(control, frame)
        knight, receipts["current_knight"] = call(
            output, "e204-d06-current-knight-34333-61", "ck3_query_current_battle_knight_v1",
            {"subject_public_cunit_id": ARMY, "character_id": CHARACTER,
             "regiment_id": REGIMENT, "expected_played_character_id": ACTOR,
             "expected_war_id": WAR, "expected_native_carmy_id": ARMY,
             "expected_combat_id": COMBAT, "expected_province_id": PROVINCE,
             "expected_date_raw": DATE, "expected_revision": frame["revision"],
             "expected_native_revision": frame["native_revision"],
             "expected_snapshot_id": frame["snapshot_id"]}, timeout)
        values["current_knight"] = knight_case(knight, frame)
        last, receipts["ending_snapshot"] = call(output, "e204-d06-knight-end-snapshot",
                                                  "ck3_take_snapshot", {}, timeout)
        require(snapshot_case(last) == frame, "paused frame changed during observation")
        status, error = "PAUSED_D06_CURRENT_KNIGHT_OBSERVED_UNREVIEWED", None
    except (OSError, ValueError, RuntimeError, TimeoutError, TypeError, KeyError) as exc:
        status, error = "RED_PRESERVED", f"{type(exc).__name__}: {exc}"
    row = {"schema": "xar.war-promo.d06-current-knight-observation/v1",
           "created_at": utc(), "result": status, "error": error,
           "source_binding": binding, "intent": identity(intent),
           "requests": receipts, "values": values,
           "visual_and_media_reviewed": False, "next_action":
           "inspect same-run HUD and mark bounded raw" if error is None else
           "inspect pending/native response; no request retry on this attempt"}
    write_new(target, row)
    print(json.dumps(row, ensure_ascii=False))
    return 0 if error is None else 2


def finish(output: Path, binding: dict[str, Any]) -> int:
    for child in output.parent.iterdir():
        if child.is_dir() and (child / "recorder-start.json").exists():
            require((child / "recorder-end.json").is_file() and
                    (child / "recorder-final.json").is_file(),
                    f"recorder not sealed: {child}")
    steps = output / "operator-steps"
    target = output / "interactive-requests" / "999-e204-d06-knight-finish.json"
    temp = target.with_suffix(".json.pending")
    receipt = steps / "e2-04-d06-knight-finish.json"
    require(not target.exists() and not temp.exists() and not receipt.exists(),
            "finish already requested; inspect session")
    write_new(temp, {"action": "finish"})
    os.rename(temp, target)
    row = {"schema": "xar.war-promo.d06-current-knight-finish/v1",
           "created_at": utc(), "result": "CLEANUP_REQUESTED_UNREVIEWED",
           "source_binding": binding, "finish_request": identity(target),
           "next_action": "wait for capture_session exit; inspect session-result and process inventory"}
    write_new(receipt, row)
    print(json.dumps(row, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("seal", "observe", "finish"))
    parser.add_argument("--session-output", type=Path)
    parser.add_argument("--no-launch-attempt", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args()
    if not 10 <= args.timeout <= 900:
        parser.error("timeout must be 10..900 seconds")
    if args.mode == "seal":
        if args.session_output is not None:
            parser.error("seal does not accept --session-output")
        print(json.dumps(seal_no_launch(args.no_launch_attempt), ensure_ascii=False))
        return 0
    if args.session_output is None:
        parser.error("observe and finish require --session-output")
    binding = verify_session(args.session_output, args.no_launch_attempt,
                             require_gui=args.mode == "observe")
    (args.session_output / "operator-steps").mkdir(exist_ok=True)
    if args.mode == "observe":
        return observe(args.session_output, binding, args.timeout)
    return finish(args.session_output, binding)


if __name__ == "__main__":
    raise SystemExit(main())

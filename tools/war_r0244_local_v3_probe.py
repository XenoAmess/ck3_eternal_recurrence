"""Prepare and sample a local War 4 v3 encounter without gameplay commands.

`preflight` only reads inputs and writes a fresh external attempt plan.  A human
operator must separately obtain the CK3 screen lease and fresh Steam offline
receipt before running the planned capture command.  `probe` attaches to that
already-managed capture session; it never launches CK3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback


REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "docs/ck3-native-ai/war-r0244-local-v3-source-manifest.json"
FRAME_KEYS = ("date_raw", "snapshot_id", "revision", "native_revision", "episode_run_id")
CAPABILITY = "game.command.query-combat-simulation-inputs-v3-N"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_new(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def frame(body: dict) -> dict:
    return {key: body.get(key) for key in FRAME_KEYS}


def require_same_frame(initial: dict, queried: dict) -> None:
    for key, initial_key in (("queried_snapshot_id", "snapshot_id"),
                             ("queried_revision", "revision"),
                             ("queried_native_revision", "native_revision"),
                             ("queried_episode_run_id", "episode_run_id")):
        if queried.get(key) != initial.get(initial_key):
            raise ValueError(f"same-frame mismatch: {key}")


def require_scene(snapshot: dict, expected: dict) -> tuple[dict, dict, tuple[int, ...]]:
    if snapshot.get("paused") is not True or snapshot.get("date_raw") != expected["date_raw"]:
        raise ValueError("checkpoint date/pause mismatch")
    if snapshot.get("pending_character_interaction") is not None or snapshot.get("active_event") is not None:
        raise ValueError("pending event or interaction")
    if snapshot.get("played_character", {}).get("character_id") != expected["character_id"]:
        raise ValueError("played character mismatch")
    war = next((w for w in snapshot.get("active_wars", []) if w.get("war_id") == expected["war_id"]), None)
    if war is None:
        raise ValueError("source war absent")
    army = next((a for a in war.get("allied_armies", []) if a.get("army_id") == expected["attacker_army_id"]), None)
    enemy = next((a for a in war.get("enemy_armies", []) if a.get("army_id") == expected["defender_army_id"]), None)
    if army is None or enemy is None:
        raise ValueError("source combatants absent")
    if (army.get("current_province_id") != expected["origin_province_id"]
            or army.get("route_province_ids") != [] or army.get("move_target_province_id") is not None
            or army.get("controllable") is not True or army.get("retreating") is not False):
        raise ValueError("attacker is no longer stationary and controllable")
    if enemy.get("current_province_id") != expected["target_province_id"] or enemy.get("retreating") is not False:
        raise ValueError("target defender changed")
    hostile = tuple(sorted(a["army_id"] for a in war.get("enemy_armies", []) if a.get("retreating") is False))
    if list(hostile) != expected["hostile_army_ids"]:
        raise ValueError("hostile roster changed")
    return army, enemy, hostile


def require_v3(body: dict, snapshot: dict, expected: dict, entry: int, step: str) -> dict:
    require_same_frame(snapshot, body)
    if body.get("step") != step or body.get("status") != "available" or body.get("accepted") is not True:
        raise ValueError("v3 command unavailable")
    payload = body.get("combat_simulation_inputs") or {}
    scenario = (payload.get("base_inputs") or {}).get("scenario") or {}
    if (payload.get("schema_version") != 3
            or payload.get("completeness", {}).get("input_observation_ready") is not True
            or (payload.get("base_inputs") or {}).get("target_province_id") != expected["target_province_id"]
            or scenario.get("attacker_entry_province_id") != entry
            or scenario.get("attacker_army_ids") != [expected["attacker_army_id"]]
            or scenario.get("defender_army_ids") != [expected["defender_army_id"]]):
        raise ValueError("v3 scenario or completeness mismatch")
    return {"schema_version": 3, "rules_manifest_sha256": payload.get("rules_manifest_sha256"),
            "input_observation_ready": True, "scenario": scenario}


def preflight(attempt: Path, config_path: Path = CONFIG) -> dict:
    config = load_json(config_path)
    if config.get("schema") != "xar.ck3.war-r0244-local-v3-source/v1":
        raise ValueError("source manifest schema mismatch")
    paths = {key: Path(row["path"]) for key, row in config["assets"].items()}
    hashes = {}
    for key, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"{key}: {path}")
        actual = sha256(path)
        if actual != config["assets"][key]["sha256"]:
            raise ValueError(f"{key} SHA-256 mismatch")
        hashes[key] = actual
    receipt = load_json(paths["checkpoint_receipt"])
    checkpoint = receipt.get("body", {}).get("checkpoint", {})
    if (receipt.get("result") != "CALL_COMPLETED" or checkpoint.get("status") != "saved"
            or checkpoint.get("sha256", "").upper() != hashes["checkpoint"]
            or checkpoint.get("date_raw") != config["scene"]["date_raw"]):
        raise ValueError("checkpoint receipt does not bind source save/date")
    lifecycle = checkpoint.get("succession_lifecycle") or {}
    if lifecycle.get("source") != "pure-vanilla-enabled-mods-empty" or lifecycle.get("xar_enabled") != "xar_off":
        raise ValueError("checkpoint is not the documented pure-vanilla source")
    source_snapshot = load_json(paths["source_snapshot"])
    if source_snapshot.get("result") != "CALL_COMPLETED":
        raise ValueError("source snapshot did not complete")
    require_scene(source_snapshot["body"], config["scene"])
    capture = REPO / "promo/ck3_native_war_ai/integration/capture_session.py"
    if not capture.is_file():
        raise FileNotFoundError(capture)
    if attempt.exists():
        raise FileExistsError(f"fresh attempt required: {attempt}")
    if not Path(config["shader_cache_source"]).is_dir():
        raise FileNotFoundError("exact-build shader cache source absent")
    attempt.mkdir(parents=True)
    argv = [sys.executable, "-B", str(capture), "--game-dir", config["game_dir"],
            "--bridge-dll", str(paths["bridge_dll"]), "--bridge-injector", str(paths["bridge_injector"]),
            "--state-dir", str(attempt / "ck3-state"), "--output-dir", str(attempt / "ck3-output"),
            "--pipe-name", config["pipe_prefix"] + attempt.name,
            "--checkpoint-save", str(paths["checkpoint"]), "--checkpoint-receipt", str(paths["checkpoint_receipt"]),
            "--interactive-seconds", "1200", "--shader-cache-source", config["shader_cache_source"],
            "--steam-offline-receipt", str(attempt / "steam-offline-receipt.json"), "--capture"]
    plan = {"schema": "xar.ck3.war-r0244-local-v3-attempt/v1", "scope": "local War 4 read-only analog; not original War 48 pairing",
            "source_manifest_sha256": sha256(config_path), "source_hashes": hashes,
            "capture_session_sha256": sha256(capture), "probe_script_sha256": sha256(Path(__file__)), "expected_scene": config["scene"],
            "capture_argv": argv, "capture_cwd": str(REPO), "probe_argv": [sys.executable, str(Path(__file__).resolve()), "probe", "--attempt", str(attempt)],
            "launch_blockers": ["parent-coordinated exclusive CK3 resource", "fresh visually reviewed Steam offline receipt in attempt", "new managed capture invocation"],
            "live_status": "NOT_STARTED"}
    write_new(attempt / "input-freeze.json", plan)
    return plan


def probe(attempt: Path, config_path: Path = CONFIG) -> dict:
    plan = load_json(attempt / "input-freeze.json")
    config = load_json(config_path)
    if plan.get("source_manifest_sha256") != sha256(config_path) or plan.get("probe_script_sha256") != sha256(Path(__file__)):
        raise ValueError("source manifest changed since preflight")
    if plan.get("capture_session_sha256") != sha256(REPO / "promo/ck3_native_war_ai/integration/capture_session.py"):
        raise ValueError("managed capture source changed since preflight")
    if (attempt / "v3-read-only-result.json").exists() or (attempt / "v3-read-only-red.json").exists():
        raise FileExistsError("probe is single-use")
    for key, row in config["assets"].items():
        if sha256(Path(row["path"])) != plan["source_hashes"][key]:
            raise ValueError(f"source asset changed: {key}")
    output = attempt / "ck3-output"
    requests, responses = output / "interactive-requests", output / "interactive-requests-responses"
    if not requests.is_dir() or not responses.is_dir() or not (attempt / "steam-offline-receipt.json").is_file():
        raise ValueError("managed session and fresh offline receipt required")

    def call(name: str, tool: str, arguments: dict | None = None) -> tuple[dict, str]:
        nonlocal connection_generation
        request, response = requests / f"{name}.json", responses / f"{name}.json"
        if request.exists() or response.exists():
            raise FileExistsError(name)
        temporary = output / f"{name}.tmp"
        temporary.write_text(json.dumps({"action": "mcp", "tool": tool, "arguments": arguments or {}}), encoding="utf-8")
        os.replace(temporary, request)
        until = time.monotonic() + 180
        while time.monotonic() < until:
            if response.is_file():
                raw = response.read_bytes()
                try:
                    row = json.loads(raw)
                except json.JSONDecodeError:
                    time.sleep(.25)
                    continue
                if row.get("result") != "CALL_COMPLETED":
                    raise ValueError(f"{name}: {row.get('result')}: {row.get('error')}")
                state = row.get("driver_state") or {}
                generation = state.get("connection_generation")
                hello = state.get("hello") or {}
                if (not isinstance(generation, int) or hello.get("ck3_build_match") is not True
                        or hello.get("expected_ck3_sha256") != plan["source_hashes"]["ck3_exe"]):
                    raise ValueError(f"{name}: bridge/build identity unavailable")
                if connection_generation is None:
                    connection_generation = generation
                elif connection_generation != generation:
                    raise ValueError(f"{name}: bridge connection generation changed")
                if ("queried_connection_generation" in row["body"]
                        and row["body"]["queried_connection_generation"] != generation):
                    raise ValueError(f"{name}: query connection generation changed")
                return row["body"], hashlib.sha256(raw).hexdigest().upper()
            time.sleep(.25)
        raise TimeoutError(name)

    connection_generation = None
    summary = {"scope": plan["scope"], "source_manifest_sha256": plan["source_manifest_sha256"], "receipts": {}}
    try:
        scene = config["scene"]
        initial, summary["receipts"]["initial"] = call("000-snapshot", "ck3_take_snapshot")
        require_scene(initial, scene)
        summary["initial_frame"] = frame(initial)
        caps, summary["receipts"]["capabilities"] = call("001-capabilities", "ck3_get_capabilities")
        if CAPABILITY not in caps.get("bridge_capabilities", []):
            # Some bridge versions publish the native capability only in the driver hello.
            state = load_json(output / "interactive-requests-responses/001-capabilities.json").get("driver_state", {})
            if CAPABILITY not in state.get("hello", {}).get("capabilities", []):
                raise ValueError("v3 bridge capability absent")
        target, attacker, defender = scene["target_province_id"], scene["attacker_army_id"], scene["defender_army_id"]
        preview_step = f"preview-move-army-{attacker}-to-{target}"
        preview, summary["receipts"]["preview"] = call("010-route-preview", "ck3_execute_step", {"step": preview_step, "expected_revision": initial["revision"]})
        require_same_frame(initial, preview)
        route = preview.get("route_preview", {})
        points = route.get("route_province_ids") or []
        if (preview.get("step") != preview_step or route.get("status") != "available"
                or route.get("origin_province_id") != scene["origin_province_id"] or not points or points[-1] != target):
            raise ValueError("route preview mismatch")
        entry = points[-2] if len(points) >= 2 else scene["origin_province_id"]
        hostile = scene["hostile_army_ids"]
        contact_step = f"query-route-contact-horizon-v1-{attacker}-to-{target}-h-{len(hostile)}-" + "-".join(map(str, hostile))
        contact, summary["receipts"]["contact"] = call("011-route-contact", "ck3_execute_step", {"step": contact_step, "expected_revision": initial["revision"]})
        require_same_frame(initial, contact)
        horizon = contact.get("route_contact_horizon", {})
        if (contact.get("step") != contact_step or horizon.get("status") != "available"
                or horizon.get("subject_army_id") != attacker or horizon.get("target_province_id") != target
                or horizon.get("hostile_army_ids") != hostile or horizon.get("subject_route", {}).get("route_province_ids") != points):
            raise ValueError("route-contact same-frame or input mismatch")
        v3_step = f"query-combat-simulation-inputs-v3-{target}-{entry}-a-1-{attacker}-d-1-{defender}"
        queried, summary["receipts"]["v3"] = call("020-v3", "ck3_execute_step", {"step": v3_step, "expected_revision": initial["revision"]})
        summary["v3"] = require_v3(queried, initial, scene, entry, v3_step)
        after, summary["receipts"]["after"] = call("021-after-snapshot", "ck3_take_snapshot")
        if frame(after) != frame(initial):
            raise ValueError("read-only requests changed paused frame")
        require_scene(after, scene)
        summary.update({"route": points, "entry_province_id": entry, "v3_step": v3_step,
                        "connection_generation": connection_generation, "result": "GREEN_LOCAL_WAR4_SAME_FRAME_V3_READ_ONLY"})
        write_new(attempt / "v3-read-only-result.json", summary)
        return summary
    except BaseException as exc:
        summary.update({"result": "RED", "error": {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}})
        write_new(attempt / "v3-read-only-red.json", summary)
        raise
    finally:
        finish = requests / "999-finish.json"
        if not finish.exists():
            temporary = output / "999-finish.tmp"
            temporary.write_text(json.dumps({"action": "finish"}), encoding="utf-8")
            os.replace(temporary, finish)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preflight", "probe"))
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, default=CONFIG)
    args = parser.parse_args()
    value = preflight(args.attempt, args.source_manifest) if args.mode == "preflight" else probe(args.attempt, args.source_manifest)
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

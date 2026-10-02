"""No-screen, no-launch identity gate for a fresh E2-09 terminal capture.

This does not run capture_session, inspect Steam, access the desktop, or attach
to CK3. It writes one new JSON receipt and candidate argv for a later screen
window. The old attempt-024 DLL hash is historical evidence only.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
import shutil
import sys
from pathlib import Path


EXPECTED_GAME_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXPECTED_SAVE_SHA = "F085D8ABB89A354FA1004DBE8800505BC952AA8A68C0EA21AAB788F9875FEEB3"
EXPECTED_SAVE_DATE_RAW = 53146872
EXPECTED_ACTOR_ID = 29829
EXPECTED_COMBAT_ID = 16777218
EXPECTED_WAR_ID = 4
REQUIRED_DLL_STRINGS = (b"game.state.snapshot", b"game.state.map-ready", b"game.state.played-character")
FRONTEND_TIMEOUT_SECONDS = 900
MAP_TIMEOUT_SECONDS = 2 * FRONTEND_TIMEOUT_SECONDS
INTERACTIVE_SECONDS = 2400
RECOVERY_SECONDS = 600
HOLD_SECONDS = 30


def identity(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(4 * 1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return {"path": str(path.resolve()), "bytes": size, "sha256": digest.hexdigest().upper()}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def pe_machine(path: Path) -> str:
    with path.open("rb") as stream:
        header = stream.read(0x40)
        require(header[:2] == b"MZ", f"not a PE file: {path}")
        offset = int.from_bytes(header[0x3C:0x40], "little")
        stream.seek(offset)
        pe = stream.read(6)
    require(pe[:4] == b"PE\0\0", f"missing PE signature: {path}")
    machine = int.from_bytes(pe[4:6], "little")
    require(machine == 0x8664, f"expected x64 PE: {path}")
    return "x64-pe"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-exe", type=Path, required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-sha256", required=True)
    parser.add_argument("--injector", type=Path, required=True)
    parser.add_argument("--injector-sha256", required=True)
    parser.add_argument("--checkpoint-save", type=Path, required=True)
    parser.add_argument("--checkpoint-receipt", type=Path, required=True)
    parser.add_argument("--legacy-launch-argv", type=Path, required=True)
    parser.add_argument("--capture-script", type=Path, required=True)
    parser.add_argument("--attempt-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    for label, value in (("bridge", args.bridge_sha256), ("injector", args.injector_sha256)):
        require(re.fullmatch(r"[0-9a-fA-F]{64}", value) is not None, f"{label} SHA-256 is invalid")
    require(not args.attempt_root.exists(), "new attempt root already exists")
    require(not args.receipt.exists(), "static receipt already exists")
    require(args.receipt.parent.is_dir(), "static receipt parent must already exist")

    game = identity(args.game_exe)
    require(game["sha256"] == EXPECTED_GAME_SHA, "exact CK3 game build changed")
    bridge = identity(args.bridge_dll)
    injector = identity(args.injector)
    require(bridge["sha256"] == args.bridge_sha256.upper(), "current DLL changed from selected candidate")
    require(injector["sha256"] == args.injector_sha256.upper(), "current injector changed from selected candidate")
    for path in (args.game_exe, args.bridge_dll, args.injector):
        pe_machine(path)
    dll_bytes = args.bridge_dll.read_bytes()
    capabilities = {value.decode(): value in dll_bytes for value in REQUIRED_DLL_STRINGS}
    require(all(capabilities.values()), "current DLL lacks checkpoint capture capability strings")

    saved = identity(args.checkpoint_save)
    require(saved["sha256"] == EXPECTED_SAVE_SHA, "day-27 source save changed")
    source_receipt = identity(args.checkpoint_receipt)
    original = json.loads(args.checkpoint_receipt.read_text(encoding="utf-8-sig"))
    body = original.get("body") or {}
    checkpoint = body.get("checkpoint") or {}
    lifecycle = checkpoint.get("succession_lifecycle") or {}
    hello = (original.get("driver_state") or {}).get("hello") or {}
    require(original.get("result") == "CALL_COMPLETED" and body.get("step") == "save-checkpoint"
            and body.get("accepted") is True and checkpoint.get("status") == "saved", "native save receipt invalid")
    require(checkpoint.get("size") == saved["bytes"] and
            str(checkpoint.get("sha256", "")).upper() == saved["sha256"], "source save/receipt differ")
    require(checkpoint.get("date_raw") == EXPECTED_SAVE_DATE_RAW and
            checkpoint.get("episode_character_id") == EXPECTED_ACTOR_ID, "source actor/date changed")
    require(lifecycle.get("lifecycle") == "ordinary_campaign_succession" and
            lifecycle.get("xar_enabled") == "xar_off" and
            lifecycle.get("source") == "pure-vanilla-enabled-mods-empty", "source is not vanilla campaign")
    require(hello.get("ck3_build_match") is True and
            str(hello.get("expected_ck3_sha256", "")).upper() == EXPECTED_GAME_SHA,
            "source receipt lacks exact-build native hello")

    legacy = json.loads(args.legacy_launch_argv.read_text(encoding="utf-8"))
    legacy_id = identity(args.legacy_launch_argv)
    legacy_argv = legacy.get("argv") or []
    require("--bridge-dll" in legacy_argv, "legacy launch sidecar lacks bridge path")
    legacy_bridge_path = Path(legacy_argv[legacy_argv.index("--bridge-dll") + 1])
    require(legacy_bridge_path.resolve() == args.bridge_dll.resolve(),
            "legacy launch and current candidate do not share the asserted path")
    historical_dll_sha = str(legacy.get("bridge_sha256", "")).upper()
    require(re.fullmatch(r"[0-9A-F]{64}", historical_dll_sha) is not None,
            "legacy launch sidecar lacks historical DLL hash")
    require(historical_dll_sha != bridge["sha256"],
            "current candidate and historical DLL unexpectedly match; re-audit legacy identity")
    capture_script = identity(args.capture_script)
    source = args.capture_script.read_text(encoding="utf-8")
    frontend_limit_match = re.search(r"30 <= args\.frontend_timeout <= (\d+)", source)
    frontend_limit = int(frontend_limit_match.group(1)) if frontend_limit_match else None
    require("--capture" in source and "--checkpoint-receipt" in source and
            "--interactive-seconds" in source and
            frontend_limit is not None and frontend_limit >= FRONTEND_TIMEOUT_SECONDS and
            "timeout_seconds=2 * args.frontend_timeout" in source,
            "capture_session cannot support selected 900s frontend / 1800s map budget")

    dependencies = {name: importlib.metadata.version(name)
                    for name in ("mcp", "pywin32", "Pillow", "psutil")}
    require(dependencies["mcp"] == "2.0.0", "MCP SDK differs from capture_session pin")
    planned = args.attempt_root.resolve()
    require(not planned.with_name(planned.name + "-preflight").exists() and
            not planned.with_name(planned.name + "-live").exists(), "planned output already exists")
    pipe = "\\\\.\\pipe\\xar_ck3_e2_terminal_" + hashlib.sha256(str(planned).encode()).hexdigest()[:12]
    common = [sys.executable, "-B", str(args.capture_script.resolve()),
              "--game-dir", str(args.game_exe.resolve().parent.parent),
              "--bridge-dll", bridge["path"], "--bridge-injector", injector["path"],
              "--pipe-name", pipe, "--checkpoint-save", saved["path"],
              "--checkpoint-receipt", source_receipt["path"],
              "--hold-seconds", str(HOLD_SECONDS),
              "--frontend-timeout", str(FRONTEND_TIMEOUT_SECONDS),
              "--interactive-seconds", str(INTERACTIVE_SECONDS),
              "--recovery-seconds", str(RECOVERY_SECONDS)]
    preflight_root = planned.with_name(planned.name + "-preflight")
    live_root = planned.with_name(planned.name + "-live")
    preflight_argv = common + ["--state-dir", str(preflight_root / "ck3-state"),
                                "--output-dir", str(preflight_root / "ck3-output")]
    live_argv_without_offline = common + ["--state-dir", str(live_root / "ck3-state"),
                                          "--output-dir", str(live_root / "ck3-output"), "--capture"]
    receipt = {
        "schema": "ck3.episode02.terminal-pair-static-preflight.v1",
        "status": "STATIC_GREEN_FOR_NEW_NO_LAUNCH_PREFLIGHT_ONLY",
        "ck3_launched": False, "screen_accessed": False, "runtime_denominator_hook_verified": False,
        "historical_024_dynamic_values_reusable_for_new_run": False,
        "historical_024_dll_sha256": historical_dll_sha,
        "historical_dll_available_at_legacy_path": False,
        "legacy_launch_sidecar": legacy_id,
        "game": game, "bridge": bridge, "injector": injector,
        "bridge_pe": "x64-pe", "injector_pe": "x64-pe",
        "checkpoint_save": saved, "checkpoint_receipt": source_receipt,
        "checkpoint_date_raw": EXPECTED_SAVE_DATE_RAW, "actor_id": EXPECTED_ACTOR_ID,
        "expected_combat_id": EXPECTED_COMBAT_ID, "expected_war_id": EXPECTED_WAR_ID,
        "bounded_timing_seconds": {
            "frontend": FRONTEND_TIMEOUT_SECONDS,
            "capture_script_frontend_limit": frontend_limit,
            "checkpoint_map": MAP_TIMEOUT_SECONDS,
            "interactive_hot_service": INTERACTIVE_SECONDS,
            "recovery": RECOVERY_SECONDS,
            "outer_native_session": 3 * FRONTEND_TIMEOUT_SECONDS + HOLD_SECONDS +
                max(RECOVERY_SECONDS, INTERACTIVE_SECONDS) + 90,
        },
        "static_capability_strings": capabilities, "capture_script": capture_script,
        "interpreter": sys.executable, "dependencies": dependencies,
        "ffmpeg_path": shutil.which("ffmpeg"), "ffprobe_path": shutil.which("ffprobe"),
        "preflight_argv_no_capture_flag": preflight_argv,
        "live_argv_without_fresh_steam_offline_receipt": live_argv_without_offline,
        "live_argv_requires": ["exclusive ck3-screen lease", "fresh reviewed Steam offline receipt",
                               "new append-only attempt root", "separate raw gameplay recorder with PTS marks",
                               "native writer readback from the same new run"],
    }
    with args.receipt.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": receipt["status"], "receipt": str(args.receipt),
                      "checkpoint_sha256": saved["sha256"], "bridge_sha256": bridge["sha256"]}))


if __name__ == "__main__":
    main()

"""Root-only close of the reviewed open R0002 console; physical scan0x29 once.
No command input, Enter, open action, game launch, injection or lease mutation.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import uuid
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent
REPO = Path("C:/workspace/ck3_eternal_recurrence")
EXPECTED_PID, EXPECTED_HWND, EXPECTED_THREAD = 7564, 16975020, 16432


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def capability_proof() -> dict:
    path = REPO / "tools/ck3_native_profile_mcp.py"
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    names = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for deco in node.decorator_list:
                expr = deco.func if isinstance(deco, ast.Call) else deco
                if isinstance(expr, ast.Attribute) and expr.attr == "tool":
                    names.append(node.name)
    return {
        "path": str(path), "sha256": digest(path), "tools": sorted(names),
        "fallback_reason": "No arbitrary scripted-effect, console, or LYD decision action in the exact current profile provider. Native snapshot/simulation/event/save capabilities remain preferred.",
    }


def fixture_proof() -> dict:
    report_path = BASE / "candidate2/static-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    mounted = BASE / "live-attempt-002/content/fixture"
    rows = []
    for row in report["payload"]:
        path = mounted / row["path"]
        actual = digest(path)
        if actual != row["sha256"]:
            raise RuntimeError(f"frozen fixture mismatch: {row['path']}")
        rows.append({"path": str(path), "sha256": actual})
    return {"candidate_report_sha256": digest(report_path), "mounted_payload": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", required=True, choices=["close"])
    parser.add_argument("--guard-profile", required=True, type=Path,
                        help="Existing fresh desktop semantic guard profile, not the unfilled native template")
    parser.add_argument("--output", required=True, type=Path, help="New external evidence directory; existing path rejected")
    parser.add_argument("--console-reviewed-image", type=Path)
    parser.add_argument("--reviewed-sha256")
    parser.add_argument("--console-open-reviewed", action="store_true",
                        help="Root directly reviewed the supplied current raw frame: console open")
    parser.add_argument("--native-snapshot-receipt", required=True, type=Path, help="Fresh actual standalone native snapshot receipt (not a queued request or SDK wrapper)")
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("Windows runtime required")
    if not args.output.is_absolute() or not args.output.resolve().is_relative_to(BASE.resolve()):
        parser.error("--output must be an absolute new directory below the external runtime root")
    if not args.console_reviewed_image or not args.reviewed_sha256 or not args.console_open_reviewed:
        parser.error("close requires exact current raw frame SHA and explicit root console-open review")

    args.output.mkdir(parents=True, exist_ok=False)
    receipt_path = args.output / "receipt.json"
    receipt = {
        "schema": "lyd.console-close-receipt.v1", "utc": datetime.now(timezone.utc).isoformat(),
        "helper_sha256": digest(Path(__file__)), "action": args.action, "step": None,
        "campaign": "1066 Robert Guiscard", "runtime_character_id": 31254,
        "status": "RED", "input_attempted": False, "enter_attempted": False,
        "business_postcondition_verified": False, "arbitrary_script_capability": False,
        "uses_mouse": False, "uses_ocr": False,
    }
    write_json(receipt_path, receipt)
    try:
        sys.path.insert(0, str(REPO / "tools"))
        import desktop_semantic_action_mcp as desktop
        import run_acceptance as acceptance
        import run_zhongguo_acceptance as zhongguo
        import pyautogui
        import win32clipboard
        import win32gui
        import win32process
        from windows_unicode_clipboard import temporary_unicode_text

        profile = desktop.load_profile(args.guard_profile)
        if (profile["target"]["pid"], profile["target"]["hwnd"]) != (EXPECTED_PID, EXPECTED_HWND):
            raise RuntimeError("guard does not bind the current R0002 PID/HWND")
        service = desktop.SemanticActionService(profile)
        receipt["guard_profile"] = str(args.guard_profile)
        receipt["guard_profile_sha256"] = digest(args.guard_profile)
        receipt["capability_proof"] = capability_proof()
        receipt["fixture_proof"] = fixture_proof()
        snapshot_receipt = json.loads(args.native_snapshot_receipt.read_text(encoding="utf-8-sig"))
        if snapshot_receipt.get("status") != "native_snapshot_verified":
            raise RuntimeError("actual verified native snapshot receipt required")
        snap = snapshot_receipt["snapshot"]
        diagnostics = snap["diagnostics"]
        hello = diagnostics["hello"]
        if (snap["played_character"]["character_id"] != 31254 or not snap["played_character"]["alive"]
                or not snap["map_ready"] or not snap["paused"]
                or diagnostics["bridge_pid"] != EXPECTED_PID
                or hello["expected_ck3_version"] != "1.20.0.3"
                or hello["expected_ck3_sha256"].lower() != profile["target"]["executable_sha256"].lower()):
            raise RuntimeError("native receipt is not the verified R0002 paused local player Robert 31254")
        stamp = datetime.fromisoformat(snapshot_receipt["recorded_at_utc"])
        if (datetime.now(timezone.utc) - stamp).total_seconds() > 180:
            raise RuntimeError("obtain a new native snapshot: receipt older than three minutes")
        native_profile = args.guard_profile.parent / "native-profile.json"
        if digest(native_profile) != snapshot_receipt["profile_sha256"]:
            raise RuntimeError("snapshot receipt native profile binding changed")
        receipt["native_local_player_evidence"] = {"path": str(args.native_snapshot_receipt), "sha256": digest(args.native_snapshot_receipt), "played_character_id": 31254, "date_raw": snap["date_raw"], "local_player_id": snap["local_player_id"]}
        receipt["reused_helpers"] = [
            {"path": str(REPO / "tools" / name), "sha256": digest(REPO / "tools" / name)}
            for name in ("run_zhongguo_acceptance.py", "run_acceptance.py", "windows_unicode_clipboard.py", "desktop_semantic_action_mcp.py")
        ]

        def guard() -> dict:
            import psutil
            value = service.inspect()
            tid, pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())
            if (tid, pid) != (EXPECTED_THREAD, EXPECTED_PID):
                raise RuntimeError("R0002 foreground input thread changed")
            if digest(args.guard_profile) != receipt["guard_profile_sha256"]:
                raise RuntimeError("guard profile changed")
            userdirs = [item.split("=", 1)[1] for item in psutil.Process(EXPECTED_PID).cmdline()
                        if item.startswith("-userdir=")]
            expected_userdir = BASE / "live-attempt-002/userdir"
            if len(userdirs) != 1 or Path(userdirs[0]).resolve() != expected_userdir.resolve():
                raise RuntimeError("actual CK3 process isolated R0002 userdir changed")
            return value

        def claim() -> None:
            folder = BASE / "console-dispatch-claims-close-v1"
            folder.mkdir(exist_ok=True)
            path = folder / f"{EXPECTED_PID}-close-console.json"
            # Prevent replay even if the process dies after an input ACK or
            # a later readback fails. Root investigates failures explicitly.
            with path.open("x", encoding="utf-8") as stream:
                json.dump({"utc": receipt["utc"], "receipt": str(receipt_path)}, stream)
            receipt["dispatch_claim"] = str(path)

        before = guard()
        receipt["observation_before"] = before
        live_size = tuple(before["observation"]["screen_size"])
        receipt["capture_before"] = service.backend.capture(args.output / "before.png")
        if tuple(receipt["capture_before"]["size"]) != live_size:
            raise RuntimeError("raw screenshot and actual desktop dimensions disagree")
        acceptance.ACTIVE_CK3_PID = EXPECTED_PID
        # The foreground guard above ensures focus_ck3 returns immediately.
        # Do not call any acceptance runner preflight or main entry.
        receipt["layout"] = zhongguo.force_ck3_english_keyboard_layout(args.output, "english-layout")
        if receipt["layout"].get("after_langid") != "0409" or receipt["layout"].get("result") != "GREEN":
            raise RuntimeError("actual CK3 input thread did not attest US English")
        guard()

        image = args.console_reviewed_image.resolve()
        if not image.is_relative_to(BASE.resolve()):
            raise RuntimeError("reviewed console frame must be preserved below external runtime root")
        if digest(image).lower() != args.reviewed_sha256.lower():
            raise RuntimeError("reviewed console image bytes changed")
        if time.time() - image.stat().st_mtime > 180:
            raise RuntimeError("reviewed console frame is older than three minutes")
        if tuple(service.backend.image_size(image)) != live_size:
            raise RuntimeError("reviewed console frame and current desktop dimensions differ")
        receipt["console_open_review"] = {"path": str(image), "sha256": digest(image), "root_visually_reviewed_console_open": True}
        sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
        from xar_autoplayer.control.executor import _prepare_key_press_batch
        backend_source = REPO / "ck3_autonomous_player/src/xar_autoplayer/control/executor.py"
        receipt["physical_backend"] = {"path": str(backend_source), "sha256": digest(backend_source), "function": "_prepare_key_press_batch", "source_line": 140}
        guard()
        claim()
        receipt["input_attempted"] = True
        write_json(receipt_path, receipt)
        sent, error = _prepare_key_press_batch(0x29)()
        receipt["physical_close_dispatch"] = {"scan_code": 41, "shift": False, "expected_records": 2, "sent": sent, "winerror": error}
        if sent != 2:
            raise RuntimeError("physical console-close batch not fully dispatched; no automatic replay")
        time.sleep(0.35)
        receipt["status"] = "close_key_dispatched_requires_closed_console_review"

        receipt["capture_after"] = service.backend.capture(args.output / "after.png")
        receipt["observation_after"] = guard()
        if tuple(receipt["capture_after"]["size"]) != live_size:
            raise RuntimeError("desktop dimensions changed after dispatch")
    except Exception as error:
        receipt["status"] = "RED"
        receipt["error"] = f"{type(error).__name__}: {error}"
    finally:
        write_json(receipt_path, receipt)
        print(json.dumps({"status": receipt["status"], "receipt": str(receipt_path),
                          "enter_attempted": receipt["enter_attempted"]}, ensure_ascii=False))
    return 1 if receipt["status"] == "RED" else 0


if __name__ == "__main__":
    raise SystemExit(main())

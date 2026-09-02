#!/usr/bin/env python3
"""Run one bounded UI-driven private Raiktor war-army capture.

The C++ debugger owns the isolated CK3 process and performs the read-only
native observation. This runner only navigates a disposable vanilla Robert
1066 game, waits for the naturally scheduled bookmark.1071 event, atomically
arms the exact option contract, and clicks option A. It never opens the debug
console, injects the bridge, or issues a gameplay command API mutation.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


EXPECTED_MANIFEST_SHA256 = (
    "F51D72E78A8B8C0E32EA22B3DF695ED7DD85621BBA548CBA20DA4A6DE8B7A046"
)
EXPECTED_CAPTURE_EXE_SHA256 = (
    "C40BED2DEFED5ACF56589788CAC98D282757085279DFFFA7E3E79BD274C52C2F"
)
EXPECTED_CK3_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_BOOKMARK_EVENTS_SHA256 = (
    "75CF485E379E522D4AAED9EF889FCC411A0D9DFCC28BCFB250ABDCC93A757EFF"
)
EXPECTED_OPEN_KAISHEK_COMMIT = "0390b9a959fa1a59a968000ed49e827a03b8d4e4"
EXPECTED_OPEN_KAISHEK_JAR_SHA256 = (
    "421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB"
)
EXPECTED_RUN_ACCEPTANCE_SHA256 = (
    "A42ED8682422D33FED4C647F15FCB4EE26750ACD9BCEB93DD65DDD873EE84B79"
)
EXPECTED_ARM_BYTES = (
    b"event_definition_key=bookmark.1071\n"
    b"option_key=bookmark.1071.a\n"
    b"option_index=0\n"
)
TARGET_TITLE = "觊觎大位的修士"
TARGET_OPTION = "我会将他扶上君士坦丁堡的皇位！"
SICILY_TITLE = "诺曼人的西西里"
SICILY_SAFE_OPTION = "教宗和皇帝都可以保留他们的土地"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def process_inventory() -> list[dict[str, object]]:
    runner_pid = os.getpid()
    command = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        "Get-CimInstance Win32_Process | Where-Object { "
        "$_.Name -in @('ck3.exe','python.exe','pythonw.exe') } | "
        "Select-Object ProcessId,ParentProcessId,Name,ExecutablePath | "
        "ConvertTo-Json -Compress",
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        raise RuntimeError(f"process inventory failed: {result.stderr.strip()}")
    text = result.stdout.strip()
    if not text:
        return []
    decoded = json.loads(text)
    rows = decoded if isinstance(decoded, list) else [decoded]
    rows_by_pid = {int(row["ProcessId"]): row for row in rows}
    exempt_runner_chain = {runner_pid}
    cursor = runner_pid
    while cursor in rows_by_pid:
        parent = int(rows_by_pid[cursor]["ParentProcessId"])
        parent_row = rows_by_pid.get(parent)
        if parent_row is None or str(parent_row["Name"]).lower() not in {
            "python.exe", "pythonw.exe"
        }:
            break
        exempt_runner_chain.add(parent)
        cursor = parent
    return [
        row for row in rows
        if int(row["ProcessId"]) not in exempt_runner_chain
    ]


def atomic_arm(path: Path) -> str:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(EXPECTED_ARM_BYTES)
    os.replace(temporary, path)
    observed = sha256(path)
    expected = hashlib.sha256(EXPECTED_ARM_BYTES).hexdigest().upper()
    if observed != expected:
        raise RuntimeError("action-arm hash mismatch after atomic publish")
    return observed


def load_capture_artifact(path: Path) -> tuple[dict[str, object] | None, str | None]:
    """Load a terminal capture without masking an earlier harness failure."""
    if not path.is_file():
        return None, "capture artifact was not created"
    payload = path.read_text(encoding="utf-8")
    if not payload.strip():
        return None, "capture artifact is empty"
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as exc:
        return None, f"capture artifact is invalid JSON: {exc}"
    if not isinstance(decoded, dict):
        return None, "capture artifact root is not an object"
    return decoded, None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-exe", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--ck3-exe", type=Path, required=True)
    parser.add_argument("--bookmark-events", type=Path, required=True)
    parser.add_argument("--open-kaishek-root", type=Path, required=True)
    parser.add_argument("--open-kaishek-jar", type=Path, required=True)
    parser.add_argument("--open-kaishek-preflight", type=Path, required=True)
    parser.add_argument("--open-kaishek-parse", type=Path, required=True)
    parser.add_argument("--tools-root", type=Path, required=True)
    parser.add_argument("--userdir", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--capture-timeout-ms", type=int, default=600000)
    parser.add_argument("--ui-timeout-seconds", type=int, default=520)
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="validate every frozen precondition without launching the debugger or CK3",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = datetime.now(timezone.utc)
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    ui_dir = args.artifact_dir / "ui"
    ui_dir.mkdir(parents=True, exist_ok=True)
    capture_path = args.artifact_dir / "capture.json"
    report_path = args.artifact_dir / "report.json"
    arm_path = args.artifact_dir / "action-arm.txt"
    if arm_path.exists() or capture_path.exists():
        raise RuntimeError("fresh artifact directory required")

    hashes = {
        "manifest": sha256(args.manifest),
        "capture_exe": sha256(args.capture_exe),
        "ck3_exe": sha256(args.ck3_exe),
        "bookmark_events": sha256(args.bookmark_events),
        "open_kaishek_jar": sha256(args.open_kaishek_jar),
        "run_acceptance": sha256(args.tools_root / "run_acceptance.py"),
    }
    expected_hashes = {
        "manifest": EXPECTED_MANIFEST_SHA256,
        "capture_exe": EXPECTED_CAPTURE_EXE_SHA256,
        "ck3_exe": EXPECTED_CK3_SHA256,
        "bookmark_events": EXPECTED_BOOKMARK_EVENTS_SHA256,
        "open_kaishek_jar": EXPECTED_OPEN_KAISHEK_JAR_SHA256,
        "run_acceptance": EXPECTED_RUN_ACCEPTANCE_SHA256,
    }
    if hashes != expected_hashes:
        raise RuntimeError(f"frozen input hash mismatch: {hashes}")
    commit = subprocess.run(
        ["git", "-C", str(args.open_kaishek_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if commit != EXPECTED_OPEN_KAISHEK_COMMIT:
        raise RuntimeError(f"open_kaishek commit mismatch: {commit}")
    preflight = json.loads(args.open_kaishek_preflight.read_text(encoding="utf-8"))
    source_parse = json.loads(args.open_kaishek_parse.read_text(encoding="utf-8"))
    if (
        preflight.get("status") != "GREEN"
        or preflight.get("fixture_id") != "ck3-war-days-trigger-11906"
        or preflight.get("provenance", {}).get("ck3_started") != "false"
        or source_parse.get("status") != "PARSED"
        or source_parse.get("roundTrip") is not True
        or int(source_parse.get("bytes", -1)) != 50117
    ):
        raise RuntimeError("open_kaishek preflight/source parse contract mismatch")

    before_inventory = process_inventory()
    if before_inventory:
        raise RuntimeError(f"pre-start process inventory is nonempty: {before_inventory}")
    if args.verify_only:
        print(json.dumps({
            "status": "READY_TO_RUN",
            "frozen_inputs": hashes,
            "open_kaishek_commit": commit,
            "open_kaishek_status": preflight.get("status"),
            "source_parse_status": source_parse.get("status"),
            "process_inventory": before_inventory,
            "ck3_started": False,
        }, ensure_ascii=False, indent=2))
        return 0

    sys.path.insert(0, str(args.tools_root.resolve()))
    import run_acceptance as acceptance  # pylint: disable=import-error
    import pyautogui  # pylint: disable=import-error
    from PIL import ImageGrab  # pylint: disable=import-error

    command = [
        str(args.capture_exe.resolve()),
        "--exe",
        str(args.ck3_exe.resolve()),
        "--userdir",
        str(args.userdir.resolve()),
        "--output",
        str(capture_path.resolve()),
        "--arm-file",
        str(arm_path.resolve()),
        "--timeout-ms",
        str(args.capture_timeout_ms),
    ]
    capture_process: subprocess.Popen[str] | None = None
    target_seen = False
    target_selected = False
    arm_sha256: str | None = None
    handled_sicily = 0
    handled_other = 0
    error: str | None = None
    try:
        capture_process = subprocess.Popen(
            command,
            cwd=str(args.capture_exe.resolve().parent),
            text=True,
        )
        ck3_pid = None
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and capture_process.poll() is None:
            rows = process_inventory()
            ck3_rows = [row for row in rows if str(row.get("Name", "")).lower() == "ck3.exe"]
            if len(ck3_rows) == 1:
                ck3_pid = int(ck3_rows[0]["ProcessId"])
                break
            time.sleep(0.25)
        if ck3_pid is None:
            raise RuntimeError("debugger-owned CK3 process did not appear uniquely")
        acceptance.ACTIVE_CK3_PID = ck3_pid
        acceptance.navigate_lobby(ui_dir, ironman=False)

        map_deadline = time.monotonic() + 90
        while time.monotonic() < map_deadline and capture_process.poll() is None:
            acceptance.focus_ck3()
            image = ImageGrab.grab()
            if acceptance.read_hud_game_day(image) is not None:
                image.save(ui_dir / "03_map_hud.png")
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("map HUD did not become visible")
        acceptance.set_speed_five_and_unpause(ui_dir, "raiktor-natural-schedule")

        deadline = time.monotonic() + args.ui_timeout_seconds
        last_day = acceptance.read_hud_game_day()
        last_progress = time.monotonic()
        last_action = 0.0
        while time.monotonic() < deadline and capture_process.poll() is None:
            acceptance.focus_ck3()
            image = ImageGrab.grab()
            texts = acceptance.ocr_results(image, acceptance.FULL_SCREEN_REGION)
            joined = " ".join(row[0] for row in texts)
            if TARGET_TITLE in joined:
                target_seen = True
                image.save(ui_dir / "04_bookmark_1071_a_armed.png")
                option = acceptance.find_ocr_text(
                    image, TARGET_OPTION, acceptance.EVENT_OPTIONS_FULL_REGION,
                    contains=True,
                )
                if option is None:
                    raise RuntimeError("bookmark.1071.a option text was not located")
                arm_sha256 = atomic_arm(arm_path)
                acceptance.deliberate_click(option, "bookmark.1071.a exact option")
                target_selected = True
                break
            if SICILY_TITLE in joined and time.monotonic() - last_action > 2:
                image.save(ui_dir / f"ordinary_sicily_{handled_sicily + 1}.png")
                option = acceptance.find_ocr_text(
                    image, SICILY_SAFE_OPTION,
                    acceptance.EVENT_OPTIONS_FULL_REGION,
                    contains=True,
                )
                if option is None:
                    raise RuntimeError("bookmark.1070.c safe option was not located")
                acceptance.deliberate_click(option, "bookmark.1070.c keep peace")
                handled_sicily += 1
                last_action = time.monotonic()
                time.sleep(0.8)
                acceptance.set_speed_five_and_unpause(
                    ui_dir, f"post-sicily-{handled_sicily}", require_progress=False
                )
                continue
            day = acceptance.read_hud_game_day(image)
            if day is not None and (last_day is None or day > last_day):
                last_day = day
                last_progress = time.monotonic()
            elif time.monotonic() - last_progress > 8 and time.monotonic() - last_action > 3:
                image.save(ui_dir / f"ordinary_blocker_{handled_other + 1}.png")
                pyautogui.hotkey("shift", "1")
                handled_other += 1
                last_action = time.monotonic()
                last_progress = time.monotonic()
                time.sleep(0.8)
                acceptance.set_speed_five_and_unpause(
                    ui_dir, f"post-blocker-{handled_other}", require_progress=False
                )
            time.sleep(0.5)
        if not target_selected:
            if capture_process.poll() is not None:
                raise RuntimeError("capture reached terminal before bookmark.1071.a selection")
            raise RuntimeError("natural bookmark.1071 event did not appear before UI timeout")
        try:
            capture_process.wait(timeout=30)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("capture did not terminate after exact option selection") from exc
    except Exception as caught:  # retain the one bounded typed terminal
        error = f"{type(caught).__name__}: {caught}"
    finally:
        if capture_process is not None and capture_process.poll() is None:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(capture_process.pid)],
                capture_output=True,
                timeout=20,
            )
            try:
                capture_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
        acceptance.ACTIVE_CK3_PID = None

    time.sleep(1)
    after_inventory = process_inventory()
    capture, capture_artifact_error = load_capture_artifact(capture_path)
    after_hashes = {
        "manifest": sha256(args.manifest),
        "capture_exe": sha256(args.capture_exe),
        "ck3_exe": sha256(args.ck3_exe),
        "bookmark_events": sha256(args.bookmark_events),
        "open_kaishek_jar": sha256(args.open_kaishek_jar),
        "run_acceptance": sha256(args.tools_root / "run_acceptance.py"),
    }
    source_unchanged = after_hashes == hashes
    ok = (
        error is None
        and target_seen
        and target_selected
        and capture_process is not None
        and capture_process.returncode == 0
        and capture is not None
        and capture.get("result") == "GREEN"
        and capture.get("source_execution_count") == 6
        and capture.get("public_bridge_abi_changed") is False
        and capture.get("production_detour_installed") is False
        and capture.get("readiness_promotion") is False
        and capture.get("arm_proof_sha256") == arm_sha256
        and not after_inventory
        and source_unchanged
    )
    finished = datetime.now(timezone.utc)
    report = {
        "schema": "xar.ck3.raiktor_war_bound_private_capture_run.v1",
        "status": "GREEN" if ok else "RED",
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "elapsed_seconds": round((finished - started).total_seconds(), 3),
        "policy": {
            "single_ck3": True,
            "natural_scheduled_event": True,
            "debug_console_used": False,
            "bridge_injected": False,
            "gameplay_command_api_mutations": [],
            "private_read_only_capture": True,
        },
        "frozen_inputs_before": hashes,
        "frozen_inputs_after": after_hashes,
        "source_unchanged": source_unchanged,
        "open_kaishek": {
            "commit": commit,
            "preflight_sha256": sha256(args.open_kaishek_preflight),
            "source_parse_sha256": sha256(args.open_kaishek_parse),
            "status": preflight.get("status"),
            "source_parse_status": source_parse.get("status"),
        },
        "action": {
            "event_definition_key": "bookmark.1071",
            "option_key": "bookmark.1071.a",
            "option_index": 0,
            "target_seen": target_seen,
            "target_selected": target_selected,
            "arm_sha256": arm_sha256,
            "handled_sicily": handled_sicily,
            "handled_other": handled_other,
        },
        "capture_exit_code": (
            capture_process.returncode if capture_process is not None else None
        ),
        "capture": capture,
        "capture_artifact_sha256": (
            sha256(capture_path) if capture_path.is_file() else None
        ),
        "capture_artifact_error": capture_artifact_error,
        "cleanup": {
            "process_inventory": after_inventory,
            "tree_gone": not after_inventory,
        },
        "error": error,
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run one bounded UI-driven private Raiktor war-army capture.

The runner normally starts one isolated CK3 and waits for main-menu readiness
without gameplay input. It then validates the exact PID/build before attaching
the private C++ read-only observer, navigates a disposable vanilla Robert 1066
game, waits for the naturally scheduled bookmark.1071 event, atomically arms
the exact option contract, and clicks option A. It never opens the debug console,
injects the bridge, or issues a gameplay command API mutation.
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


PROJECT_TOOLS = Path(__file__).resolve().parents[3] / "tools"
if str(PROJECT_TOOLS) not in sys.path:
    sys.path.insert(0, str(PROJECT_TOOLS))

from paradox_legal_consent import (  # noqa: E402
    LEGAL_ALLOWED_TERMS,
    LEGAL_AUTHORIZATION_TEXT,
    LEGAL_AUTHORIZATION_VERSION,
    LEGAL_CONSENT_PROFILE_SUFFIX,
    LEGAL_DENIED_TERMS,
    LEGAL_NOTIFICATION_BUTTONS,
    LEGAL_PURCHASE_BUTTONS,
    LEGAL_MODAL_HEADER_REGION,
    TypedTerminalError,
    _authorized_legal_marker,
    accept_authorized_legal_modal,
    account_legal_state,
    classify_authorized_legal_modal,
    newly_persisted_legal_markers,
    persist_preclassification_evidence,
    sha256,
    validate_legal_consent_source,
)


EXPECTED_MANIFEST_SHA256 = (
    "7578FA0D74554490E45188F6DAD36995D4FF03604500446B6B253CD0B574D342"
)
EXPECTED_CAPTURE_EXE_SHA256 = (
    "E658470CF7DFC65334E791F1DE301A51FA787916D443AD3BE4C0FCAAFBC3AB72"
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


def atomic_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


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


def require_fresh_attempt_directory(path: Path) -> None:
    if path.exists() and (not path.is_dir() or next(path.iterdir(), None) is not None):
        raise TypedTerminalError(
            "FreshAttemptRequired",
            "preflight",
            f"artifact directory is not absent or empty: {path}",
        )


def require_fresh_userdir(path: Path) -> None:
    if not path.is_dir():
        raise TypedTerminalError(
            "FreshAttemptRequired", "preflight", f"userdir is not a directory: {path}"
        )
    for relative in ("logs", "save games", "shadercache"):
        candidate = path / relative
        if candidate.is_dir() and any(item.is_file() for item in candidate.rglob("*")):
            raise TypedTerminalError(
                "FreshAttemptRequired",
                "preflight",
                f"isolated userdir contains prior {relative} files: {candidate}",
            )


def navigate_lobby_with_authorized_legal(
    acceptance: object,
    pyautogui: object,
    image_grab: object,
    userdir: Path,
    ui_dir: Path,
    stage_artifacts: list[dict[str, object]],
    legal_evidence: list[dict[str, object]],
    classification_attempts: list[dict[str, object]],
    classification_evidence_path: Path,
) -> None:
    new_game = acceptance.wait_for_ocr_text(
        "新游戏", acceptance.MAIN_MENU_REGION, 15,
        ui_dir, "01_main_menu.png"
    )
    acceptance.deliberate_click(new_game, "main-menu New Game")
    robert = None
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        acceptance.focus_ck3()
        image = image_grab.grab()
        robert = acceptance.find_ocr_text(
            image, "公爵罗贝尔", acceptance.RULER_REGION, contains=True
        )
        if robert is not None:
            image.save(ui_dir / "02_bookmark.png")
            break
        rows = [
            str(row[0]) for row in acceptance.ocr_results(
                image, acceptance.FULL_SCREEN_REGION
            )
        ]
        attempt = persist_preclassification_evidence(
            image,
            rows,
            ui_dir,
            len(classification_attempts) + 1,
            ck3_context_confirmed=True,
        )
        if attempt["evidence_required"]:
            classification_attempts.append(attempt)
            screenshot = attempt["preclassification_screenshot"]
            assert isinstance(screenshot, str)
            stage_artifacts.append(
                {
                    "stage": "legal_consent_preclassification",
                    "path": Path(screenshot).name,
                }
            )
            atomic_json(
                classification_evidence_path,
                {
                    "authorization_text": LEGAL_AUTHORIZATION_TEXT,
                    "authorization_version": LEGAL_AUTHORIZATION_VERSION,
                    "classification_attempts": classification_attempts,
                },
            )
        classification = classify_authorized_legal_modal(
            rows, ck3_context_confirmed=True
        )
        if classification is not None:
            legal_evidence.append(accept_authorized_legal_modal(
                acceptance,
                image_grab,
                userdir,
                ui_dir,
                image,
                rows,
                len(legal_evidence) + 1,
                stage_artifacts,
                ck3_context_confirmed=True,
            ))
            continue
        time.sleep(0.25)
    if robert is None:
        raise TypedTerminalError(
            "LobbyNavigationFailure",
            "lobby_navigation",
            "Robert bookmark did not appear and no allowlisted legal modal was handled",
        )

    screen_width, screen_height = pyautogui.size()
    ruler_candidates = [
        robert,
        (robert[0] - int(screen_width * 0.041),
         robert[1] - int(screen_height * 0.057)),
        (robert[0], robert[1] - int(screen_height * 0.09)),
    ]
    selected = False
    for candidate in ruler_candidates:
        acceptance.deliberate_click(candidate, "Robert 1066 bookmark candidate")
        pyautogui.moveTo(int(screen_width * 0.50), int(screen_height * 0.95))
        try:
            acceptance.wait_for_ocr_text(
                "公爵罗贝尔", acceptance.RULER_DETAIL_REGION, 5,
                ui_dir, "03_ruler_selected.png", contains=True, stable_hits=1
            )
            selected = True
            break
        except Exception:
            continue
    if not selected:
        raise TypedTerminalError(
            "LobbyNavigationFailure",
            "lobby_navigation",
            "unable to select Robert after three OCR-verified candidates",
        )
    start = acceptance.wait_for_ocr_text(
        "开始", acceptance.START_REGION, 15,
        ui_dir, "03_start_enabled.png"
    )
    acceptance.click_until_text_disappears(
        start, "开始", acceptance.START_REGION, ui_dir
    )
    return None


def validate_readiness_contract(
    manifest: dict[str, object], args: argparse.Namespace
) -> dict[str, object]:
    attempt = manifest.get("attempt_contract")
    readiness = manifest.get("readiness_contract")
    capture_product = manifest.get("capture_product")
    if not isinstance(attempt, dict) or not isinstance(readiness, dict):
        raise RuntimeError("manifest lacks the persisted attempt/readiness contracts")
    if not isinstance(capture_product, dict):
        raise RuntimeError("manifest lacks the frozen capture product")
    if capture_product.get("executable_sha256") != EXPECTED_CAPTURE_EXE_SHA256:
        raise RuntimeError("manifest capture-product hash mismatch")
    if capture_product.get("timeout_max_ms") != 1200000:
        raise RuntimeError("manifest capture-product timeout range mismatch")
    expected = {
        "process_discovery_timeout_seconds": 30,
        "main_menu_timeout_seconds": 300,
        "main_menu_stage_capture_seconds": [60, 120, 180, 240, 300],
        "private_attach_timeout_seconds": 30,
        "map_hud_timeout_seconds": 90,
        "natural_bookmark_timeout_seconds": 520,
        "capture_process_timeout_ms": 1200000,
        "post_selection_capture_timeout_seconds": 30,
    }
    for key, value in expected.items():
        if readiness.get(key) != value:
            raise RuntimeError(f"manifest readiness contract mismatch for {key}")
    if attempt.get("fresh_attempt_required") is not True:
        raise RuntimeError("manifest does not require a fresh attempt")
    if attempt.get("reuse_previous_attempt") is not False:
        raise RuntimeError("manifest permits previous-attempt reuse")
    cli_values = {
        "main_menu_timeout_seconds": args.main_menu_timeout_seconds,
        "natural_bookmark_timeout_seconds": args.ui_timeout_seconds,
        "capture_process_timeout_ms": args.capture_timeout_ms,
    }
    for key, value in cli_values.items():
        if value != readiness[key]:
            raise RuntimeError(
                f"CLI timeout {key}={value} does not match manifest {readiness[key]}"
            )
    return readiness


def wait_for_main_menu_readiness(
    acceptance: object,
    image_grab: object,
    ck3_process: subprocess.Popen[str],
    ui_dir: Path,
    timeout_seconds: int,
    stage_seconds: list[int],
    artifacts: list[dict[str, object]],
) -> None:
    started = time.monotonic()
    pending = list(stage_seconds)
    last_image = None
    while time.monotonic() - started < timeout_seconds:
        if ck3_process.poll() is not None:
            raise TypedTerminalError(
                "CK3ExitedBeforeMainMenu",
                "main_menu_readiness",
                "normally launched CK3 exited before main-menu readiness",
            )
        acceptance.focus_ck3()
        last_image = image_grab.grab()
        elapsed = time.monotonic() - started
        while pending and elapsed >= pending[0]:
            checkpoint = pending.pop(0)
            path = ui_dir / f"readiness_main_menu_{checkpoint:03d}s.png"
            last_image.save(path)
            artifacts.append({
                "stage": "main_menu_readiness",
                "elapsed_seconds": checkpoint,
                "path": path.name,
            })
        if acceptance.find_ocr_text(
            last_image, "新游戏", acceptance.MAIN_MENU_REGION
        ) is not None:
            path = ui_dir / "readiness_main_menu_ready.png"
            last_image.save(path)
            artifacts.append({
                "stage": "main_menu_ready",
                "elapsed_seconds": round(elapsed, 3),
                "path": path.name,
            })
            return
        time.sleep(0.5)
    if last_image is None:
        last_image = image_grab.grab()
    terminal_path = ui_dir / "readiness_main_menu_300s_terminal.png"
    last_image.save(terminal_path)
    artifacts.append({
        "stage": "main_menu_readiness_timeout",
        "elapsed_seconds": timeout_seconds,
        "path": terminal_path.name,
    })
    raise TypedTerminalError(
        "MainMenuReadinessTimeout",
        "main_menu_readiness",
        f"main menu was not OCR-ready within {timeout_seconds} seconds",
    )


def validate_running_ck3(pid: int, expected_exe: Path) -> dict[str, object]:
    rows = process_inventory()
    matches = [
        row for row in rows
        if str(row.get("Name", "")).lower() == "ck3.exe"
        and int(row.get("ProcessId", -1)) == pid
    ]
    ck3_rows = [row for row in rows if str(row.get("Name", "")).lower() == "ck3.exe"]
    if len(matches) != 1 or len(ck3_rows) != 1:
        raise TypedTerminalError(
            "AttachTargetIdentityMismatch",
            "pre_attach_identity",
            f"expected one CK3 process at PID {pid}, observed {ck3_rows}",
        )
    actual_exe = Path(str(matches[0].get("ExecutablePath", "")))
    if actual_exe.resolve() != expected_exe.resolve():
        raise TypedTerminalError(
            "AttachTargetIdentityMismatch",
            "pre_attach_identity",
            f"PID {pid} executable path mismatch: {actual_exe}",
        )
    actual_hash = sha256(actual_exe)
    if actual_hash != EXPECTED_CK3_SHA256:
        raise TypedTerminalError(
            "AttachTargetBuildMismatch",
            "pre_attach_identity",
            f"PID {pid} executable hash mismatch: {actual_hash}",
        )
    return {
        "pid": pid,
        "executable_path": str(actual_exe.resolve()),
        "executable_sha256": actual_hash,
    }


def load_attach_ready(path: Path, pid: int) -> dict[str, object]:
    try:
        ready = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TypedTerminalError(
            "PrivateAttachReadinessInvalid",
            "private_attach",
            f"attach readiness artifact is invalid: {exc}",
        ) from exc
    expected = {
        "schema": "raiktor-war-bound-private-attach-ready-v1",
        "attach_mode": True,
        "pid": pid,
        "exe_sha256": EXPECTED_CK3_SHA256,
        "observation_stop_rva": "0x2E7F951",
        "breakpoint_installed": True,
    }
    for key, value in expected.items():
        if ready.get(key) != value:
            raise TypedTerminalError(
                "PrivateAttachReadinessInvalid",
                "private_attach",
                f"attach readiness mismatch for {key}: {ready.get(key)!r}",
            )
    ready["sha256"] = sha256(path)
    return ready


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
    parser.add_argument(
        "--legal-consent-source",
        type=Path,
        required=True,
        help=(
            "read-only real-profile account.json used only to bind the pre-run "
            "legal marker state; any explicitly authorized acceptance is persisted "
            "only inside the disposable userdir"
        ),
    )
    parser.add_argument("--userdir", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--capture-timeout-ms", type=int, default=1200000)
    parser.add_argument("--main-menu-timeout-seconds", type=int, default=300)
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
    require_fresh_attempt_directory(args.artifact_dir)
    require_fresh_userdir(args.userdir)
    ui_dir = args.artifact_dir / "ui"
    capture_path = args.artifact_dir / "capture.json"
    report_path = args.artifact_dir / "report.json"
    arm_path = args.artifact_dir / "action-arm.txt"

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
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    readiness = validate_readiness_contract(manifest, args)
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

    legal_contract = manifest.get("legal_consent_contract")
    if not isinstance(legal_contract, dict):
        raise RuntimeError("manifest lacks the persisted legal-consent contract")
    legal_consent = validate_legal_consent_source(
        args.legal_consent_source, legal_contract
    )

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
            "legal_consent": legal_consent,
            "legal_consent_seed_installed": False,
            "attempt_contract": manifest["attempt_contract"],
            "readiness_contract": readiness,
            "artifact_directory_created": False,
            "process_inventory": before_inventory,
            "ck3_started": False,
        }, ensure_ascii=False, indent=2))
        return 0

    args.artifact_dir.mkdir(parents=True, exist_ok=False)
    ui_dir.mkdir(parents=True, exist_ok=False)

    sys.path.insert(0, str(args.tools_root.resolve()))
    import run_acceptance as acceptance  # pylint: disable=import-error
    import pyautogui  # pylint: disable=import-error
    from PIL import ImageGrab  # pylint: disable=import-error

    attach_ready_path = args.artifact_dir / "attach-ready.json"
    ck3_process: subprocess.Popen[str] | None = None
    capture_process: subprocess.Popen[str] | None = None
    attach_target: dict[str, object] | None = None
    attach_ready: dict[str, object] | None = None
    legal_acceptances: list[dict[str, object]] = []
    legal_classification_attempts: list[dict[str, object]] = []
    target_seen = False
    target_selected = False
    arm_sha256: str | None = None
    handled_sicily = 0
    handled_other = 0
    error: str | None = None
    typed_terminal: str | None = None
    terminal_stage: str | None = None
    classification_diagnostics: dict[str, object] | None = None
    stage_artifacts: list[dict[str, object]] = []
    try:
        ck3_command = [
            str(args.ck3_exe.resolve()),
            f"-userdir={args.userdir.resolve()}",
        ]
        ck3_process = subprocess.Popen(
            ck3_command,
            cwd=str(args.ck3_exe.resolve().parent),
            text=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        ck3_pid = ck3_process.pid
        deadline = time.monotonic() + int(
            readiness["process_discovery_timeout_seconds"]
        )
        while time.monotonic() < deadline and ck3_process.poll() is None:
            try:
                attach_target = validate_running_ck3(ck3_pid, args.ck3_exe)
                break
            except TypedTerminalError:
                pass
            time.sleep(0.25)
        if attach_target is None:
            raise TypedTerminalError(
                "NormalCK3ProcessTimeout",
                "process_discovery",
                "normally launched CK3 process did not appear uniquely",
            )
        acceptance.ACTIVE_CK3_PID = ck3_pid
        wait_for_main_menu_readiness(
            acceptance,
            ImageGrab,
            ck3_process,
            ui_dir,
            int(readiness["main_menu_timeout_seconds"]),
            list(readiness["main_menu_stage_capture_seconds"]),
            stage_artifacts,
        )
        attach_target = validate_running_ck3(ck3_pid, args.ck3_exe)
        capture_command = [
            str(args.capture_exe.resolve()),
            "--attach-pid",
            str(ck3_pid),
            "--exe",
            str(args.ck3_exe.resolve()),
            "--output",
            str(capture_path.resolve()),
            "--arm-file",
            str(arm_path.resolve()),
            "--ready-file",
            str(attach_ready_path.resolve()),
            "--timeout-ms",
            str(args.capture_timeout_ms),
        ]
        capture_process = subprocess.Popen(
            capture_command,
            cwd=str(args.capture_exe.resolve().parent),
            text=True,
        )
        attach_deadline = time.monotonic() + int(
            readiness["private_attach_timeout_seconds"]
        )
        while time.monotonic() < attach_deadline:
            if attach_ready_path.is_file():
                attach_ready = load_attach_ready(attach_ready_path, ck3_pid)
                break
            if capture_process.poll() is not None:
                raise TypedTerminalError(
                    "PrivateAttachExitedBeforeReady",
                    "private_attach",
                    "private capture exited before attach readiness",
                )
            time.sleep(0.1)
        if attach_ready is None:
            raise TypedTerminalError(
                "PrivateAttachReadinessTimeout",
                "private_attach",
                "private capture did not publish attach readiness in time",
            )
        try:
            navigate_lobby_with_authorized_legal(
                acceptance,
                pyautogui,
                ImageGrab,
                args.userdir,
                ui_dir,
                stage_artifacts,
                legal_acceptances,
                legal_classification_attempts,
                args.artifact_dir / "legal-modal-observations.json",
            )
        except TypedTerminalError:
            raise
        except Exception as exc:
            raise TypedTerminalError(
                "LobbyNavigationFailure", "lobby_navigation", str(exc)
            ) from exc

        map_deadline = time.monotonic() + int(readiness["map_hud_timeout_seconds"])
        while time.monotonic() < map_deadline and capture_process.poll() is None:
            acceptance.focus_ck3()
            image = ImageGrab.grab()
            if acceptance.read_hud_game_day(image) is not None:
                image.save(ui_dir / "03_map_hud.png")
                break
            time.sleep(0.5)
        else:
            raise TypedTerminalError(
                "MapHudReadinessTimeout",
                "map_hud_readiness",
                "map HUD did not become visible before the persisted deadline",
            )
        acceptance.set_speed_five_and_unpause(ui_dir, "raiktor-natural-schedule")

        deadline = time.monotonic() + int(
            readiness["natural_bookmark_timeout_seconds"]
        )
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
                    raise TypedTerminalError(
                        "NaturalScenarioNavigationFailure",
                        "natural_bookmark",
                        "bookmark.1071.a option text was not located",
                    )
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
                    raise TypedTerminalError(
                        "NaturalScenarioNavigationFailure",
                        "natural_bookmark",
                        "bookmark.1070.c safe option was not located",
                    )
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
                raise TypedTerminalError(
                    "CaptureExitedBeforeTarget",
                    "natural_bookmark",
                    "capture reached terminal before bookmark.1071.a selection",
                )
            raise TypedTerminalError(
                "NaturalBookmarkTimeout",
                "natural_bookmark",
                "natural bookmark.1071 event did not appear before the persisted deadline",
            )
        try:
            capture_process.wait(
                timeout=int(readiness["post_selection_capture_timeout_seconds"])
            )
        except subprocess.TimeoutExpired as exc:
            raise TypedTerminalError(
                "PostSelectionCaptureTimeout",
                "post_selection_capture",
                "capture did not terminate after exact option selection",
            ) from exc
    except Exception as caught:  # retain the one bounded typed terminal
        error = f"{type(caught).__name__}: {caught}"
        typed_terminal = getattr(caught, "terminal", "UnhandledHarnessFailure")
        terminal_stage = getattr(caught, "stage", "unclassified")
        classification_diagnostics = getattr(caught, "diagnostics", None)
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
        if ck3_process is not None and ck3_process.poll() is None:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(ck3_process.pid)],
                capture_output=True,
                timeout=20,
            )
            try:
                ck3_process.wait(timeout=10)
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
    for artifact in stage_artifacts:
        artifact_path = ui_dir / str(artifact["path"])
        artifact["sha256"] = sha256(artifact_path)
    ok = (
        error is None
        and target_seen
        and target_selected
        and capture_process is not None
        and capture_process.returncode == 0
        and attach_ready is not None
        and capture is not None
        and capture.get("result") == "GREEN"
        and capture.get("source_execution_count") == 6
        and capture.get("public_bridge_abi_changed") is False
        and capture.get("production_detour_installed") is False
        and capture.get("readiness_promotion") is False
        and capture.get("attach_mode") is True
        and capture.get("debugger_detached") is True
        and capture.get("process_terminated") is False
        and capture.get("arm_proof_sha256") == arm_sha256
        and not after_inventory
        and source_unchanged
    )
    finished = datetime.now(timezone.utc)
    report = {
        "schema": "xar.ck3.raiktor_war_bound_private_capture_run.v1",
        "status": "GREEN" if ok else "HARNESS_RED",
        "typed_terminal": typed_terminal,
        "terminal_stage": terminal_stage,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "elapsed_seconds": round((finished - started).total_seconds(), 3),
        "policy": {
            "single_ck3": True,
            "normal_cold_start_before_attach": True,
            "gameplay_input_before_main_menu": False,
            "debugger_attach_after_main_menu": True,
            "natural_scheduled_event": True,
            "debug_console_used": False,
            "bridge_injected": False,
            "gameplay_command_api_mutations": [],
            "private_read_only_capture": True,
            "fresh_attempt": True,
            "legal_consent_authorization": LEGAL_AUTHORIZATION_TEXT,
            "legal_consent_authorization_version": LEGAL_AUTHORIZATION_VERSION,
            "legal_consent_click_count": len(legal_acceptances),
        },
        "legal_consent": {
            "preflight": legal_consent,
            "authorization_text": LEGAL_AUTHORIZATION_TEXT,
            "authorization_version": LEGAL_AUTHORIZATION_VERSION,
            "acceptances": legal_acceptances,
            "classification_attempts": legal_classification_attempts,
            "classification_diagnostics": classification_diagnostics,
            "real_profile_modified": False,
        },
        "readiness_contract": readiness,
        "readiness_stage_artifacts": stage_artifacts,
        "ck3_pid": ck3_process.pid if ck3_process is not None else None,
        "attach_target": attach_target,
        "attach_ready": attach_ready,
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

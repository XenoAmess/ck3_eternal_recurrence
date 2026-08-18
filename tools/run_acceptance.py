# 全自动验收 runner：备份现场 -> 场景规则/纪录 -> OCR 过大厅 -> 场景判定 -> 恢复现场
#
# 前置事实（2026-08-17 实证）：游戏加载的是 Steam 工坊缓存（ugc_3784706360，
# 播放集启用的是工坊项而非 dev 路径，因 dev .mod 带了 remote_file_id 被启动器合并）。
# 因此 runner 每次先把仓库 mod robocopy /MIR 同步进工坊缓存目录再启动（用户已批准，
# 不恢复缓存；下次工坊更新时 Steam 重下即复原）。
#
# 用法（必须用 tools/.venv 的 python，依赖 requirements.txt）：
#   & "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" tools\run_acceptance.py
#
# 大厅导航与事件选项使用 OCR 状态识别，不再依赖固定等待和绝对坐标。判定依据：
#   debug.log 出现 "XAR: TEST DONE"，全部 "XAR: TEST PASS"、无 "XAR: TEST FAIL"，
#   且 error.log 无 xar 相关错误。
# 现场保护：tutorial.txt / player\game_rules\presets.txt / autosave*.ck3
#   先隔离到临时目录，结束时无论成败原样恢复；独立 watchdog 兜底强杀。

import argparse
from contextlib import contextmanager
import ctypes
from datetime import datetime, timezone
import hashlib
import html
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import os
from pathlib import Path

import pyautogui
import numpy as np
import cv2
import win32api
import win32con
import win32gui
import win32process
from PIL import Image, ImageDraw, ImageGrab

import validate_static
import build_release

# UI localization smoke test: OCR engine + crop box for the three event options.
# RapidOCR is pure Python with bundled ONNX models; installed in tools/.venv.
try:
    from rapidocr_onnxruntime import RapidOCR
    _ocr = RapidOCR()
except Exception as e:
    _ocr = None
    print(f"WARNING: RapidOCR not available: {e}")

pyautogui.FAILSAFE = False

ROOT = Path(__file__).resolve().parent.parent


def configured_path(name, default):
    raw = os.environ.get(name)
    return Path(os.path.expandvars(raw)).expanduser().resolve() if raw else default.resolve()


CK3_EXE = configured_path(
    "XAR_CK3_EXE", ROOT / "Crusader Kings III" / "binaries" / "ck3.exe")
USER_DIR = configured_path(
    "XAR_CK3_USER_DIR",
    Path.home() / "Documents" / "Paradox Interactive" / "Crusader Kings III")
UGC_DIR_OVERRIDE = os.environ.get("XAR_CK3_UGC_DIR")
MOD_ROOT = ROOT / "XenoAmess_s_Eternal_Recurrence"
UGC_MOD_FILE = USER_DIR / "mod" / "ugc_3784706360.mod"
TUTORIAL_TXT = USER_DIR / "tutorial.txt"
PRESETS_TXT = USER_DIR / "player" / "game_rules" / "presets.txt"
SAVE_GAMES_DIR = USER_DIR / "save games"
DEBUG_LOG = USER_DIR / "logs" / "debug.log"
ERROR_LOG = USER_DIR / "logs" / "error.log"
GUI_WARNINGS_LOG = USER_DIR / "logs" / "gui_warnings.log"
RESTORE_WATCHDOG = ROOT / "tools" / "restore_watchdog.py"
REQUIRED_PASSES = {
    "pact_trait", "pact_flag", "shop_init", "shop_inflate", "shop_charge",
    "shop_ceiling_fraction", "ledger_score_nonnegative", "ledger_projection",
    "ledger_record_unchanged",
    "draw_bless_distinct", "bless_apply", "draw_curse_constrained",
    "curse_pair_xp", "trait_level_1", "trait_level_2", "trait_mid_rewards",
    "trait_late_rewards", "trait_xp_cap", "import_var",
    "import_value", "import_points", "record_same_threshold",
    "record_cross_threshold", "record_cap", "score_positive", "reject_penalty", "score_preview",
    "ui_shop_points", "ui_shop_price", "ui_shop_diplomacy",
    "ui_shop_purchase", "ui_shop_finish", "ui_reroll", "ui_bless_decline",
    "ui_seal", "ui_curse_after_seal", "bless_count", "record_write",
    "ui_ledger_open", "ui_ledger_close", "ui_contract_select",
    "contract_select", "contract_progress",
    "inherit_0", "inherit_25", "inherit_50", "inherit_100_uncapped",
    "inherit_5000", "inherit_50000", "inherit_166600", "shop_high_tier_bundle",
    "shop_expanded_inventory",
    "default_growth_track", "growth_contract_points", "growth_baseline_zero",
    "growth_score_delta", "ai_runtime_guard",
}

# 区域均为相对屏幕比例；OCR 只扫目标区域，比全屏 OCR 快且不受分辨率影响。
MAIN_MENU_REGION = (0.18, 0.28, 0.30, 0.50)
RULER_REGION = (0.45, 0.68, 0.72, 0.91)
START_REGION = (0.82, 0.82, 0.95, 0.93)
RULER_DETAIL_REGION = (0.76, 0.28, 0.98, 0.58)
OPTION_LIST_REGION = (0.20, 0.58, 0.56, 0.83)
EVENT_TITLE_REGION = (0.20, 0.17, 0.50, 0.29)
EVENT_TEXT_REGION = (0.18, 0.16, 0.62, 0.58)
EVENT_OPTIONS_FULL_REGION = (0.18, 0.43, 0.62, 0.95)
CHARACTER_PANEL_REGION = (0.00, 0.05, 0.48, 0.72)
OBSERVER_REGION = (0.00, 0.75, 0.35, 1.00)
HUD_DATE_REGION = (0.78, 0.95, 0.92, 1.00)
FULL_SCREEN_REGION = (0.00, 0.00, 1.00, 1.00)

BOOT_TIMEOUT_S = 120             # OCR 一发现主菜单即继续，不固定睡 100 秒
LOBBY_TIMEOUT_S = 30
TEST_TIMEOUT_S = 300             # 开局后等待 TEST DONE 的超时
OFF_OBSERVE_TIMEOUT_S = 30
BARGAIN_REOPEN_TIMEOUT_S = 600   # real 1095-day wait; freeze detection remains independent
POLL_INTERVAL_S = 1


class RunnerError(RuntimeError):
    pass


def log(msg):
    print(f"[runner {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def focus_ck3():
    found = []
    def _cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and "Crusader Kings" in win32gui.GetWindowText(hwnd):
            found.append(hwnd)
    win32gui.EnumWindows(_cb, None)
    if not found:
        return False

    target = found[0]
    if win32gui.GetForegroundWindow() == target:
        return True

    user32 = ctypes.windll.user32
    last_error = None
    for _ in range(3):
        foreground = win32gui.GetForegroundWindow()
        current_thread = win32api.GetCurrentThreadId()
        foreground_thread = win32process.GetWindowThreadProcessId(foreground)[0]
        target_thread = win32process.GetWindowThreadProcessId(target)[0]
        attached = []
        try:
            for thread in {foreground_thread, target_thread}:
                if thread and thread != current_thread:
                    if user32.AttachThreadInput(current_thread, thread, True):
                        attached.append(thread)
            win32gui.ShowWindow(target, win32con.SW_RESTORE)
            win32gui.BringWindowToTop(target)
            pyautogui.keyDown("alt")
            try:
                win32gui.SetForegroundWindow(target)
            finally:
                pyautogui.keyUp("alt")
        except Exception as exc:
            last_error = exc
        finally:
            for thread in reversed(attached):
                user32.AttachThreadInput(current_thread, thread, False)
        if win32gui.GetForegroundWindow() == target:
            return True
        time.sleep(0.2)

    foreground = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(foreground) if foreground else ""
    detail = f": {last_error}" if last_error else ""
    raise RunnerError(
        f"CK3 could not obtain foreground; active window is {title!r}{detail}")


def ugc_content_dir():
    """工坊缓存目录（游戏实际加载的就是它——播放集启用的是 ugc 项而非 dev 路径）。"""
    if UGC_DIR_OVERRIDE:
        return configured_path("XAR_CK3_UGC_DIR", Path(UGC_DIR_OVERRIDE))
    m = re.search(r'path="([^"]+)"', UGC_MOD_FILE.read_text(encoding="utf-8"))
    if not m:
        raise RuntimeError("ugc .mod has no path=")
    return Path(m.group(1))


def ck3_is_running():
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq ck3.exe", "/FO", "CSV", "/NH"],
        capture_output=True, text=True, errors="replace")
    return any(line.lower().startswith('"ck3.exe"') for line in result.stdout.splitlines())


def preflight():
    """Reject unsafe or incomplete desktop-runner configuration before /MIR or backup."""
    errors = []
    if os.name != "nt":
        errors.append("acceptance requires Windows")
    if not CK3_EXE.is_file():
        errors.append(f"CK3 executable not found: {CK3_EXE}")
    for path, label in ((TUTORIAL_TXT, "tutorial.txt"),
                        (PRESETS_TXT, "game-rule presets")):
        if not path.is_file():
            errors.append(f"{label} not found: {path}")
    if not SAVE_GAMES_DIR.is_dir():
        errors.append(f"save-games directory not found: {SAVE_GAMES_DIR}")
    target = None
    try:
        target = ugc_content_dir().resolve()
    except (OSError, RuntimeError) as exc:
        errors.append(f"UGC target unavailable: {exc}")
    if target is not None:
        if not target.is_dir():
            errors.append(f"UGC target is not a directory: {target}")
        elif not (target / "descriptor.mod").is_file():
            errors.append(f"UGC target lacks descriptor.mod: {target}")
        if target.name != build_release.WORKSHOP_ITEM_ID:
            errors.append(
                f"UGC /MIR target must end in workshop id "
                f"{build_release.WORKSHOP_ITEM_ID}: {target}")
        if (target == MOD_ROOT.resolve() or MOD_ROOT.resolve() in target.parents
                or target in MOD_ROOT.resolve().parents):
            errors.append(f"UGC /MIR target overlaps repository mod source: {target}")
    width, height = pyautogui.size()
    if width < 1920 or height < 1080:
        errors.append(f"interactive desktop is too small: {width}x{height}")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        if os.environ.get("XAR_CK3_CI") != "1":
            errors.append("GitHub Actions requires XAR_CK3_CI=1 on a dedicated desktop")
        if not all(os.environ.get(name) for name in (
                "XAR_CK3_EXE", "XAR_CK3_USER_DIR", "XAR_CK3_UGC_DIR",
                "XAR_CK3_VERSION")):
            errors.append(
                "GitHub Actions requires explicit CK3, user, UGC, and version values")
        if ck3_is_running():
            errors.append("ck3.exe is already running on the dedicated CI desktop")
    if errors:
        raise RunnerError("preflight failed:\n  " + "\n  ".join(errors))
    log(
        f"preflight passed: exe={CK3_EXE}, user={USER_DIR}, "
        f"ugc={target}, desktop={width}x{height}")
    return target


def sync_repo_to_ugc(target, source=MOD_ROOT):
    """Mirror the selected development/release runtime tree into the live UGC cache."""
    r = subprocess.run(
        ["robocopy", str(source), str(target), "/MIR", "/NFL", "/NDL", "/NJH", "/NJS", "/NP"],
        capture_output=True)
    if r.returncode >= 8:
        raise RuntimeError(f"robocopy failed rc={r.returncode}")
    log(f"synced {source} -> {target} (robocopy rc={r.returncode})")


def kill_ck3():
    subprocess.run(["taskkill", "/F", "/IM", "ck3.exe"],
                   capture_output=True)


def kill_process(pid):
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                   capture_output=True)


def stop_ck3_process(process, ck3_pid_file):
    """Terminate one tracked CK3 process tree and prove the process exited."""
    if process is None:
        return
    kill_process(process.pid)
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired as exc:
        raise RunnerError(f"CK3 PID {process.pid} did not exit") from exc
    if process.poll() is None:
        raise RunnerError(f"CK3 PID {process.pid} is still running")
    ck3_pid_file.unlink(missing_ok=True)
    log(f"CK3 PID {process.pid} fully exited")


def start_restore_watchdog(backup, ck3_pid_file):
    """独立进程兜底：runner 被强杀时仍恢复用户现场。"""
    subprocess.Popen(
        [sys.executable, str(RESTORE_WATCHDOG), str(os.getpid()),
         str(ck3_pid_file),
         str(backup / "tutorial.txt"), str(TUTORIAL_TXT),
         str(backup / "presets.txt"), str(PRESETS_TXT)],
        creationflags=subprocess.CREATE_NO_WINDOW)


def isolate_autosaves(backup):
    """Snapshot then remove autosaves so one scenario cannot poison the next."""
    autosave_backup = backup / "autosaves"
    autosave_backup.mkdir()
    paths = sorted(
        path for path in SAVE_GAMES_DIR.glob("autosave*.ck3") if path.is_file())
    for path in paths:
        destination = autosave_backup / path.name
        shutil.copy2(path, destination)
        if hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(
                destination.read_bytes()).digest():
            raise OSError(f"autosave backup verification failed: {path}")
    # Watchdog only acts after every original has a verified backup.
    (backup / "autosaves.ready").write_text("ready\n", encoding="ascii")
    for path in paths:
        path.unlink()
    return len(paths)


def restore_autosaves(backup):
    """Discard acceptance autosaves and atomically restore the user's originals."""
    autosave_backup = backup / "autosaves"
    if not (backup / "autosaves.ready").is_file():
        return
    if not autosave_backup.is_dir():
        raise OSError(f"autosave backup missing after ready marker: {autosave_backup}")
    for path in SAVE_GAMES_DIR.glob("autosave*.ck3"):
        if path.is_file():
            path.unlink()
    for source in sorted(autosave_backup.iterdir()):
        if not source.is_file():
            continue
        destination = SAVE_GAMES_DIR / source.name
        temporary = destination.with_name(destination.name + ".xar_restore_tmp")
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
        if hashlib.sha256(source.read_bytes()).digest() != hashlib.sha256(
                destination.read_bytes()).digest():
            raise OSError(f"autosave restore verification failed: {destination}")


def read_new_lines(path, offset):
    """从 offset 起读新内容，返回 (文本, 新 offset)。文件可能被游戏占用，容错读。"""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            if size < offset:
                offset = 0  # 日志被轮转了
            f.seek(offset)
            data = f.read()
        return data.decode("utf-8", errors="ignore"), size
    except OSError:
        return "", offset


def snapshot_log(path, offset, destination):
    """Copy only lines produced by this run; never archive a user's historical logs."""
    if offset is None or not path.exists():
        return
    with open(path, "rb") as source:
        size = path.stat().st_size
        source.seek(0 if size < offset else offset)
        data = source.read()
    destination.write_bytes(data)


def set_last_applied_rule(raw, setting):
    """Set the requested mode with the recommended Growth + 100% track."""
    allowed = {"xar_on", "xar_off", "xar_selftest"}
    if setting not in allowed:
        raise RunnerError(f"unsupported XAR rule setting: {setting}")
    pattern = re.compile(
        rb'(name="LastAppliedRules"\s+setting=\{)(.*?)(\}\s+ironman=)',
        re.DOTALL)
    match = pattern.search(raw)
    if not match:
        raise RunnerError("LastAppliedRules block not found in presets.txt")
    body = re.sub(
        rb'\bxar_(?:on|off|selftest|inherit_(?:0|25|50|100)|score_(?:absolute|growth))\b',
        b'', match.group(2))
    body = (body.rstrip() + b" " + setting.encode("ascii")
            + b" xar_inherit_100 xar_score_growth ")
    patched = raw[:match.start()] + match.group(1) + body + match.group(3) + raw[match.end():]

    verify = pattern.search(patched)
    if not verify:
        raise RunnerError("LastAppliedRules block disappeared after patching")
    tokens = re.findall(rb'\bxar_(?:on|off|selftest)\b', verify.group(2))
    if tokens != [setting.encode("ascii")]:
        raise RunnerError(
            f"failed to set LastAppliedRules exclusively to {setting}: {tokens}")
    challenge_tokens = re.findall(
        rb'\bxar_(?:inherit_(?:0|25|50|100)|score_(?:absolute|growth))\b',
        verify.group(2))
    expected_challenge = [b"xar_inherit_100", b"xar_score_growth"]
    if challenge_tokens != expected_challenge:
        raise RunnerError(
            f"failed to set recommended challenge track: {challenge_tokens}")
    return patched


def set_tutorial_record(raw, threshold):
    """Replace XAR lesson bits with one compatible quantized record bit."""
    lines = raw.split(b"\n")
    stripped = [
        line for line in lines
        if not re.match(rb"^\s*(?:xar_hs_ge_\d+|xar_contract_(?:pb|complete)_\w+)\s*$", line)
    ]
    clean = b"\n".join(stripped)
    if threshold == 0:
        return clean, len(lines) - len(stripped)
    match = re.search(rb"completed_lessons\s*=\s*\{(.*?)\}", clean, re.DOTALL)
    if not match:
        raise RunnerError("completed_lessons block not found in tutorial.txt")
    body = match.group(1).rstrip()
    seeded = body + f"\n\txar_hs_ge_{threshold}\n".encode("ascii")
    return clean[:match.start(1)] + seeded + clean[match.end(1):], len(lines) - len(stripped)


def tutorial_record_state():
    """Return the highest persisted XAR record and the tutorial file hash."""
    raw = TUTORIAL_TXT.read_bytes()
    values = [
        int(value) for value in re.findall(
            rb"(?m)^\s*xar_hs_ge_(\d+)\s*$", raw)
    ]
    return (max(values, default=0), hashlib.sha256(raw).hexdigest())


def wait_for_stable_persisted_record(timeout_s=20):
    """Require the same nonzero lesson state on two consecutive reads."""
    deadline = time.time() + timeout_s
    previous = None
    stable_hits = 0
    while time.time() < deadline:
        state = tutorial_record_state()
        if state[0] > 0 and state == previous:
            stable_hits += 1
            if stable_hits >= 2:
                return state
        else:
            stable_hits = 0
        previous = state
        time.sleep(0.5)
    raise RunnerError("nonzero tutorial record did not stabilize")


def wait_for_contract_lessons(expected, timeout_s=30):
    """Require one exact set of persistent contract lessons on two reads."""
    expected = set(expected)
    deadline = time.time() + timeout_s
    previous = None
    stable_hits = 0
    while time.time() < deadline:
        text = TUTORIAL_TXT.read_text(encoding="utf-8", errors="ignore")
        found = set(re.findall(
            r"(?m)^\s*(xar_contract_(?:pb|complete)_\w+)\s*$", text))
        if found == expected and found == previous:
            stable_hits += 1
            if stable_hits >= 2:
                return sorted(found)
        else:
            stable_hits = 0
        previous = found
        time.sleep(0.5)
    raise RunnerError(
        f"contract lessons did not stabilize: expected={sorted(expected)}, "
        f"actual={sorted(previous or set())}")


def region_bbox(img, region):
    """相对屏幕区域转为 PIL 像素 bbox。"""
    width, height = img.size
    left, top, right, bottom = region
    return (int(width * left), int(height * top),
            int(width * right), int(height * bottom))


def click_ratio(x_ratio, y_ratio):
    """按当前 pyautogui 工作区比例点击，避免分辨率变化。"""
    width, height = pyautogui.size()
    pyautogui.click(int(width * x_ratio), int(height * y_ratio))


def ocr_results(img, region):
    """OCR 相对区域，返回全屏坐标的 (text, score, center, min_y)。"""
    if _ocr is None:
        raise RunnerError("RapidOCR is required; install tools/requirements.txt")
    bbox = region_bbox(img, region)
    crop = img.crop(bbox)
    result, _ = _ocr(np.asarray(crop))
    found = []
    for box, text, score in result or []:
        score = float(score)
        if not text or score < 0.45:
            continue
        xs = [p[0] + bbox[0] for p in box]
        ys = [p[1] + bbox[1] for p in box]
        found.append((text.strip(), score,
                      (int(sum(xs) / len(xs)), int(sum(ys) / len(ys))),
                      min(ys)))
    return found


def ocr_box_results(img, region):
    """OCR with full boxes for screenshot-guided stall diagnosis and recovery."""
    if _ocr is None:
        raise RunnerError("RapidOCR is required; install tools/requirements.txt")
    crop_box = region_bbox(img, region)
    result, _ = _ocr(np.asarray(img.crop(crop_box)))
    found = []
    for box, text, score in result or []:
        score = float(score)
        if not text or score < 0.45:
            continue
        xs = [int(point[0] + crop_box[0]) for point in box]
        ys = [int(point[1] + crop_box[1]) for point in box]
        found.append({
            "text": text.strip(),
            "score": round(score, 4),
            "center": [int(sum(xs) / len(xs)), int(sum(ys) / len(ys))],
            "bbox": [min(xs), min(ys), max(xs), max(ys)],
        })
    return found


def select_stall_event_option(items, width, height):
    """Pick a lower event option without assuming left- or right-column layout."""
    excluded = ("当前日期", "开始于", "政治地图", "暂停", "最快", "公元")
    lower = [
        item for item in items
        if 0.18 <= item["center"][0] / width <= 0.74
        and 0.62 <= item["center"][1] / height <= 0.84
        and not any(token in item["text"] for token in excluded)
        and not re.fullmatch(r"[\d\s./:+-]+", item["text"])
    ]
    # Classic choices occupy the left content lane; some full-width layouts use
    # the right. Portrait labels can share an x coordinate, so only fall back to
    # the right lane when no plausible left-side choice was recognized.
    left_lane = [item for item in lower if item["center"][0] / width <= 0.49]
    ranked_pool = left_lane or lower
    tolerance = int(width * 0.035)
    aligned_counts = {
        id(item): sum(
            abs(item["center"][0] - other["center"][0]) <= tolerance
            for other in ranked_pool)
        for item in ranked_pool
    }
    ranked = sorted(
        ranked_pool,
        key=lambda item: (
            aligned_counts[id(item)],
            item["center"][1],
            item["bbox"][2] - item["bbox"][0],
            item["score"],
        ),
        reverse=True,
    )
    return lower, (ranked[0] if ranked else None)


def capture_stall_and_recover(artifacts, label, attempt):
    """Capture evidence, OCR the screen, and click a visible lower event option."""
    focus_ck3()
    image = ImageGrab.grab()
    safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "_", label)
    stem = f"stall_{safe_label}_{attempt}"
    image.save(artifacts / f"{stem}.png")
    items = ocr_box_results(image, FULL_SCREEN_REGION)
    width, height = image.size
    lower, selected = select_stall_event_option(items, width, height)
    for item in items:
        item["event_option_candidate"] = item in lower
        item["selected"] = item is selected
    (artifacts / f"{stem}_ocr.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    for index, item in enumerate(items):
        if not item["event_option_candidate"]:
            continue
        color = "#00ff66" if item["selected"] else "#ffcc00"
        draw.rectangle(item["bbox"], outline=color, width=4)
        draw.text((item["bbox"][0], max(0, item["bbox"][1] - 14)),
                  str(index), fill=color)
    annotated.save(artifacts / f"{stem}_annotated.png")

    if selected is None:
        log(f"stall diagnostic {stem}: no event-option OCR candidate")
        return None
    point = tuple(selected["center"])
    deliberate_click(point, f"stall recovery '{selected['text']}'")
    log(
        f"stall diagnostic {stem}: selected OCR option "
        f"{selected['text']!r} at {point}")
    return selected


def capture_ocr_bundle(artifacts, stem, region):
    """Save a full frame, target crop, and OCR boxes as pixel evidence."""
    focus_ck3()
    image = ImageGrab.grab()
    image.save(artifacts / f"{stem}.png")
    image.crop(region_bbox(image, region)).save(artifacts / f"{stem}_crop.png")
    items = ocr_box_results(image, region)
    (artifacts / f"{stem}_ocr.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return items


def wait_for_ocr_tokens(tokens, forbidden, region, timeout_s, artifacts, stem):
    """Require several rendered tokens in one frame and reject raw/error text."""
    wanted = [re.sub(r"\s+", "", token).lower() for token in tokens]
    rejected = [re.sub(r"\s+", "", token).lower() for token in forbidden]
    deadline = time.time() + timeout_s
    last_text = ""
    while time.time() < deadline:
        items = capture_ocr_bundle(artifacts, stem, region)
        last_text = re.sub(
            r"\s+", "", " ".join(item["text"] for item in items)).lower()
        if any(token in last_text for token in rejected):
            raise RunnerError(f"{stem} contains forbidden OCR text: {last_text}")
        if all(token in last_text for token in wanted):
            log(f"PASS: {stem} rendered tokens {tokens}")
            return last_text
        time.sleep(POLL_INTERVAL_S)
    raise RunnerError(f"{stem} OCR tokens missing; last OCR={last_text}")


def find_ocr_text(img, target, region, contains=False):
    for text, _, center, _ in ocr_results(img, region):
        matches = target in text if contains else text == target
        if matches:
            return center
    return None


def find_scaled_template(img, template_path, region, scales):
    """Locate a rendered icon from its source texture across likely UI scales."""
    bbox = region_bbox(img, region)
    haystack = cv2.cvtColor(np.asarray(img.crop(bbox).convert("RGB")), cv2.COLOR_RGB2GRAY)
    template = cv2.cvtColor(
        np.asarray(Image.open(template_path).convert("RGB")), cv2.COLOR_RGB2GRAY)
    best = (0.0, None)
    for scale in scales:
        width = max(8, int(template.shape[1] * scale))
        height = max(8, int(template.shape[0] * scale))
        needle = cv2.resize(template, (width, height), interpolation=cv2.INTER_AREA)
        if height > haystack.shape[0] or width > haystack.shape[1]:
            continue
        result = cv2.matchTemplate(haystack, needle, cv2.TM_CCOEFF_NORMED)
        _, score, _, location = cv2.minMaxLoc(result)
        if score > best[0]:
            best = (score, (bbox[0] + location[0] + width // 2,
                           bbox[1] + location[1] + height // 2))
    return best


def wait_for_ocr_text(target, region, timeout_s, artifacts, artifact_name,
                      contains=False, stable_hits=2):
    """OCR 轮询到目标文字并返回文字框中心；超时立即保存证据并失败。"""
    deadline = time.time() + timeout_s
    last_img = None
    last_center = None
    hits = 0
    while time.time() < deadline:
        focus_ck3()
        last_img = ImageGrab.grab()
        center = find_ocr_text(last_img, target, region, contains=contains)
        if target == "开始" and center is None:
            dismiss = find_ocr_text(
                last_img, "忽略", FULL_SCREEN_REGION, contains=True)
            if dismiss:
                pyautogui.click(*dismiss)
                log(f"dismissed external popup covering lobby at {dismiss}")
                time.sleep(POLL_INTERVAL_S)
                continue
        if center:
            if (last_center is not None
                    and abs(center[0] - last_center[0]) <= 15
                    and abs(center[1] - last_center[1]) <= 15):
                hits += 1
            else:
                hits = 1
            last_center = center
            if hits >= stable_hits:
                last_img.save(artifacts / artifact_name)
                log(f"OCR found stable {target} at {center} ({hits} frames)")
                return center
        else:
            hits = 0
            last_center = None
        time.sleep(POLL_INTERVAL_S)
    if last_img is not None:
        last_img.save(artifacts / f"timeout_{artifact_name}")
    raise RunnerError(f"OCR timeout waiting for {target}")


def click_until_text_disappears(point, target, region, artifacts,
                                attempts=3, settle_timeout_s=5):
    """点击后用 OCR 反证按钮已消失，避免把“发出点击”当成“点击成功”。"""
    for attempt in range(1, attempts + 1):
        focus_ck3()
        pyautogui.moveTo(*point, duration=0.1)
        pyautogui.mouseDown()
        time.sleep(0.12)
        pyautogui.mouseUp()
        log(f"clicked {target}, attempt {attempt}")

        deadline = time.time() + settle_timeout_s
        while time.time() < deadline:
            img = ImageGrab.grab()
            if find_ocr_text(img, target, region) is None:
                img.save(artifacts / "04_start_accepted.png")
                log(f"OCR confirmed {target} disappeared")
                return
            time.sleep(POLL_INTERVAL_S)
    ImageGrab.grab().save(artifacts / "04_start_not_accepted.png")
    raise RunnerError(f"{target} click was not accepted after {attempts} attempts")


def deliberate_click(point, label):
    """Wait out CK3's hover animation, then send a complete button press."""
    focus_ck3()
    pyautogui.moveTo(*point, duration=0.2)
    time.sleep(0.35)
    pyautogui.mouseDown()
    time.sleep(0.15)
    pyautogui.mouseUp()
    log(f"clicked {label} at {point}")


def ck3_date_ordinal_parts(year, month, day):
    """Convert CK3's fixed 365-day calendar to an ordinal for freeze detection."""
    month_lengths = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if not 1 <= month <= 12 or not 1 <= day <= month_lengths[month - 1]:
        return None
    return year * 365 + sum(month_lengths[:month - 1]) + day - 1


def read_hud_game_date(image=None):
    """Read the rendered timeline date and clickable date-button center."""
    image = image or ImageGrab.grab()
    dates = []
    for text, _, center, _ in ocr_results(image, HUD_DATE_REGION):
        match = re.search(
            r"(\d{3,4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
        if not match:
            continue
        game_day = ck3_date_ordinal_parts(*(int(part) for part in match.groups()))
        if game_day is not None:
            dates.append((game_day, center))
    return max(dates, default=None)


def read_hud_game_day(image=None):
    """Read the rendered day; debug.log can be silent while time advances."""
    result = read_hud_game_date(image)
    return result[0] if result else None


def set_speed_five_and_unpause(
        artifacts, label, capture_tooltip=False, require_progress=True):
    """Select speed 5 and prove that the rendered game date starts advancing."""
    width, height = pyautogui.size()
    speed_five = (int(width * (2536 / 2560)), int(height * (1418 / 1440)))
    focus_ck3()
    date_result = read_hud_game_date()
    before = date_result[0] if date_result else None
    timeline_play = date_result[1] if date_result else (
        int(width * (2180 / 2560)), int(height * (1418 / 1440)))
    pyautogui.moveTo(*speed_five, duration=0.2)
    if capture_tooltip:
        optional_ocr_text(
            "最快", FULL_SCREEN_REGION, 4, artifacts,
            f"bargain_{label}_speed_5_tooltip.png", contains=True)
    deliberate_click(speed_five, f"speed 5 ({label})")

    last_image = None
    def wait_for_advance(timeout_s):
        nonlocal before, last_image
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            last_image = ImageGrab.grab()
            current = read_hud_game_day(last_image)
            if before is None and current is not None:
                before = current
            elif current is not None and current > before:
                return current
            time.sleep(0.5)
        return None

    current = wait_for_advance(2)
    if current is not None:
        log(f"HUD date already advancing at speed 5 ({label})")
        return current

    deliberate_click(timeline_play, f"timeline play ({label})")
    current = wait_for_advance(10)
    if current is not None:
        log(f"HUD date advanced after timeline play ({label})")
        return current
    if last_image is not None:
        safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "_", label)
        last_image.save(artifacts / f"bargain_{safe_label}_speed_5_stalled.png")
    message = f"speed 5 did not advance the HUD date ({label}); inspect speed evidence"
    if require_progress:
        raise RunnerError(message)
    log(message)
    return None


def wait_for_marker(debug_offset, marker, timeout_s, xar_lines):
    """轮询 debug.log；保留同一批次中的后续 marker，避免事件竞态。"""
    if any(marker in line for line in xar_lines):
        return debug_offset
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        text, debug_offset = read_new_lines(DEBUG_LOG, debug_offset)
        for line in text.splitlines():
            if "XAR:" in line:
                xar_lines.append(line.strip())
        if any(marker in line for line in xar_lines):
            return debug_offset
        time.sleep(POLL_INTERVAL_S)
    raise RunnerError(f"debug marker timeout: {marker}")


def click_until_marker(point, label, marker, debug_offset, xar_lines,
                       attempts=3, attempt_timeout_s=4, failure_marker=None):
    """Retry a UI press only when its synchronous production marker is absent."""
    for attempt in range(1, attempts + 1):
        deliberate_click(point, f"{label} (attempt {attempt})")
        deadline = time.time() + attempt_timeout_s
        while time.time() < deadline:
            text, debug_offset = read_new_lines(DEBUG_LOG, debug_offset)
            for line in text.splitlines():
                if "XAR:" in line:
                    xar_lines.append(line.strip())
            if any(marker in line for line in xar_lines):
                return debug_offset
            if failure_marker and any(failure_marker in line for line in xar_lines):
                raise RunnerError(f"{label} assertion failed: {failure_marker}")
            time.sleep(POLL_INTERVAL_S)
    raise RunnerError(f"{label} was not accepted; missing marker: {marker}")


def wait_for_localized_options(label, artifacts, expected_count, timeout_s=20):
    """等待指定数量的事件选项，拒绝 raw key、静态占位和重复文本。"""
    deadline = time.time() + timeout_s
    last_img = None
    last_text = ""
    screen_width, screen_height = pyautogui.size()
    pyautogui.moveTo(int(screen_width * 0.90), int(screen_height * 0.50), duration=0.1)
    time.sleep(0.3)
    while time.time() < deadline:
        focus_ck3()
        last_img = ImageGrab.grab()
        results = ocr_results(last_img, OPTION_LIST_REGION)
        results.sort(key=lambda r: r[3])
        texts = [r[0] for r in results]
        last_text = " ".join(texts).lower()
        rejected = ("xar", "垂青的馈赠", "咒痕的代价", "奖池索引无效",
                    "invalid pool selection")
        if any(token in last_text for token in rejected):
            last_img.save(artifacts / f"06_{label}_options_raw.png")
            raise RunnerError(f"{label} options contain unresolved text: {last_text}")
        if len(texts) >= expected_count:
            option_texts = [re.sub(r"\s+", "", text).lower()
                            for text in texts[:expected_count]]
            if len(set(option_texts)) != expected_count:
                last_img.save(artifacts / f"06_{label}_options_repeated.png")
                raise RunnerError(
                    f"{label} options are not distinct: {texts[:expected_count]}")
            last_img.save(artifacts / f"06_{label}_options.png")
            last_img.crop(region_bbox(last_img, OPTION_LIST_REGION)).save(
                artifacts / f"06_{label}_options_crop.png")
            log(f"PASS: {label} options localized and distinct; OCR={texts[:expected_count]}")
            return results[0][2]
        time.sleep(POLL_INTERVAL_S)
    if last_img is not None:
        last_img.save(artifacts / f"timeout_{label}_options.png")
    raise RunnerError(
        f"{label} option OCR saw fewer than {expected_count} rows; last OCR={last_text}")


@contextmanager
def timed_phase(timings, name):
    started = time.perf_counter()
    try:
        yield
    finally:
        timings[name] = round(time.perf_counter() - started, 3)


def navigate_lobby(artifacts):
    """OCR-drive main menu -> Robert bookmark -> confirmed game start."""
    new_game = wait_for_ocr_text(
        "新游戏", MAIN_MENU_REGION, BOOT_TIMEOUT_S,
        artifacts, "01_main_menu.png")
    robert = click_until_ocr_appears(
        new_game, "main-menu New Game", "公爵罗贝尔", RULER_REGION,
        artifacts, "02_bookmark.png", timeout_s=15)
    screen_width, screen_height = pyautogui.size()
    ruler_candidates = [
        robert,
        (robert[0] - int(screen_width * 0.041),
         robert[1] - int(screen_height * 0.057)),
        (robert[0], robert[1] - int(screen_height * 0.09)),
    ]
    selected = False
    for index, candidate in enumerate(ruler_candidates, 1):
        focus_ck3()
        pyautogui.moveTo(*candidate, duration=0.2)
        time.sleep(0.3)
        pyautogui.mouseDown()
        time.sleep(0.12)
        pyautogui.mouseUp()
        log(f"clicked Robert candidate {index} at {candidate}")
        pyautogui.moveTo(int(screen_width * 0.50), int(screen_height * 0.95))
        time.sleep(0.5)
        try:
            wait_for_ocr_text(
                "公爵罗贝尔", RULER_DETAIL_REGION, 5,
                artifacts, "03_ruler_selected.png", contains=True,
                stable_hits=1)
            selected = True
            break
        except RunnerError:
            continue
    if not selected:
        raise RunnerError("unable to select Robert after 3 OCR-verified candidates")

    start = wait_for_ocr_text(
        "开始", START_REGION, LOBBY_TIMEOUT_S,
        artifacts, "03_start_enabled.png")
    click_until_text_disappears(start, "开始", START_REGION, artifacts)


def click_until_ocr_appears(point, label, target, region, artifacts, artifact_name,
                            attempts=3, timeout_s=6, unpause=False):
    """Retry a production option until its expected next event is visible."""
    last_error = None
    for attempt in range(1, attempts + 1):
        deliberate_click(point, f"{label} (attempt {attempt})")
        if unpause:
            time.sleep(0.5)
            focus_ck3()
            click_ratio(2315 / 2560, 1410 / 1440)
            log(f"unpaused while waiting for delayed {target} event")
        try:
            return wait_for_ocr_text(
                target, region, timeout_s, artifacts, artifact_name, stable_hits=1)
        except RunnerError as exc:
            last_error = exc
    raise RunnerError(f"{label} did not open {target}: {last_error}")


def open_native_ledger(debug_offset, xar_lines, artifacts, prefix):
    """Open the production ledger through the native Decisions panel."""
    focus_ck3()
    screen_width, screen_height = pyautogui.size()
    decisions_tab = (int(screen_width * 0.987), int(screen_height * 0.367))
    pyautogui.moveTo(*decisions_tab, duration=0.2)
    wait_for_ocr_text(
        "决议", FULL_SCREEN_REGION, 10, artifacts,
        f"{prefix}_decisions_tooltip.png", contains=True, stable_hits=1)
    deliberate_click(decisions_tab, "native Decisions HUD tab")
    pyautogui.moveTo(int(screen_width * 0.90), int(screen_height * 0.70))
    pyautogui.scroll(-6)
    time.sleep(0.5)
    ledger_decision = wait_for_ocr_text(
        "琉焰账簿", FULL_SCREEN_REGION, 15, artifacts,
        f"{prefix}_ledger_decision.png", contains=True, stable_hits=1)
    deliberate_click(
        (int(screen_width * 0.90), ledger_decision[1]), "native ledger decision row")
    ledger_confirm = wait_for_ocr_text(
        "翻开账簿", FULL_SCREEN_REGION, 15, artifacts,
        f"{prefix}_ledger_confirm.png", contains=True, stable_hits=1)
    debug_offset = click_until_marker(
        ledger_confirm, "native ledger decision",
        "XAR: TEST PASS ui_ledger_open", debug_offset, xar_lines)
    ledger_close = wait_for_ocr_text(
        "合上吧", EVENT_OPTIONS_FULL_REGION, 15, artifacts,
        f"{prefix}_ledger_event.png", contains=True, stable_hits=1)
    return debug_offset, ledger_close, decisions_tab


def optional_ocr_text(target, region, timeout_s, artifacts, artifact_name,
                      contains=False):
    """Capture positive OCR evidence when available without weakening page proof."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        focus_ck3()
        img = ImageGrab.grab()
        if find_ocr_text(img, target, region, contains=contains):
            img.save(artifacts / artifact_name)
            return True
        time.sleep(POLL_INTERVAL_S)
    return False


def run_production_smoke(scenario, import_record, debug_offset, artifacts):
    """Run one normal-rule smoke without selftest-only state or purchases."""
    offset = debug_offset
    xar_lines = []
    offset = wait_for_marker(offset, "XAR: rule is on, offering pact", 180, xar_lines)
    offset = wait_for_marker(
        offset, f"XAR: import state fired k={import_record}", 5, xar_lines)
    wait_for_ocr_text(
        "终末之契", EVENT_TITLE_REGION, 15,
        artifacts, "05_pact_window.png", stable_hits=1)
    pact_accept = wait_for_ocr_text(
        "我接受", EVENT_OPTIONS_FULL_REGION, 15,
        artifacts, "05_pact_accept.png", contains=True, stable_hits=1)

    if scenario == "on-first-life":
        click_until_ocr_appears(
            pact_accept, "production pact accept", "未燃之世", EVENT_TITLE_REGION,
            artifacts, "06_first_life_title.png", attempts=1, timeout_s=20,
            unpause=False)
        begin = wait_for_ocr_text(
            "开始此生", EVENT_OPTIONS_FULL_REGION, 15,
            artifacts, "06_first_life_begin.png", contains=True, stable_hits=1)
        click_until_ocr_appears(
            begin, "first-life begin", "琉焰的垂青", EVENT_TITLE_REGION,
            artifacts, "07_bless_window.png")
    elif scenario == "on-high-budget":
        click_until_ocr_appears(
            pact_accept, "production pact accept", "轮回当铺", EVENT_TITLE_REGION,
            artifacts, "06_recorded_shop.png", attempts=1, timeout_s=20,
            unpause=False)
        offset = wait_for_marker(offset, "XAR: shop event fired", 10, xar_lines)
        wait_for_ocr_text(
            "2000", EVENT_TEXT_REGION, 15, artifacts,
            "06_high_budget_2000.png", contains=True, stable_hits=1)
        next_page = wait_for_ocr_text(
            "下一页", EVENT_OPTIONS_FULL_REGION, 15,
            artifacts, "06_high_budget_next_1.png", contains=True, stable_hits=1)
        deliberate_click(next_page, "high-budget shop page 2")
        wait_for_ocr_text(
            "金币", EVENT_OPTIONS_FULL_REGION, 15,
            artifacts, "06_high_budget_page_2.png", contains=True, stable_hits=1)
        next_page = wait_for_ocr_text(
            "下一页", EVENT_OPTIONS_FULL_REGION, 15,
            artifacts, "06_high_budget_next_2.png", contains=True, stable_hits=1)
        deliberate_click(next_page, "high-budget shop page 3")
        next_page = wait_for_ocr_text(
            "下一页", EVENT_OPTIONS_FULL_REGION, 15,
            artifacts, "06_high_budget_next_3.png", contains=True, stable_hits=1)
        deliberate_click(next_page, "high-budget shop page 4")
        dread = wait_for_ocr_text(
            "一缕恶名", EVENT_OPTIONS_FULL_REGION, 15,
            artifacts, "06_high_budget_dread.png", contains=True, stable_hits=1)
        deliberate_click(dread, "dread service purchase")
        wait_for_ocr_text(
            "1750", EVENT_TEXT_REGION, 15, artifacts,
            "06_high_budget_1750_remaining.png", contains=True, stable_hits=1)
        legitimacy = wait_for_ocr_text(
            "王冠记起", EVENT_OPTIONS_FULL_REGION, 15,
            artifacts, "06_high_budget_legitimacy.png", contains=True, stable_hits=1)
        deliberate_click(legitimacy, "legitimacy service purchase")
        wait_for_ocr_text(
            "1250", EVENT_TEXT_REGION, 15, artifacts,
            "06_high_budget_1250_remaining.png", contains=True, stable_hits=1)
        previous_page = wait_for_ocr_text(
            "上一页", EVENT_OPTIONS_FULL_REGION, 15,
            artifacts, "06_high_budget_prev_4.png", contains=True, stable_hits=1)
        deliberate_click(previous_page, "high-budget shop return to page 3")
        reform = wait_for_ocr_text(
            "免费的宗教改革", EVENT_OPTIONS_FULL_REGION, 15,
            artifacts, "06_high_budget_reform.png", contains=True, stable_hits=1)
        offset = click_until_marker(
            reform, "faith reformation purchase", "XAR: faith reformation purchased",
            offset, xar_lines)
        wait_for_ocr_text(
            "117", EVENT_TEXT_REGION, 15, artifacts,
            "06_high_budget_117_remaining.png", contains=True, stable_hits=1)
        focus_ck3()
        post_purchase = ImageGrab.grab()
        if find_ocr_text(
                post_purchase, "免费的宗教改革",
                EVENT_OPTIONS_FULL_REGION, contains=True):
            post_purchase.save(artifacts / "06_high_budget_reform_still_visible.png")
            raise RunnerError("one-time faith reformation remained purchasable")
        post_purchase.save(artifacts / "06_high_budget_reform_consumed.png")
        shop_finish = wait_for_ocr_text(
            "开始此生", EVENT_OPTIONS_FULL_REGION, 15,
            artifacts, "06_high_budget_finish.png", contains=True, stable_hits=1)
        click_until_ocr_appears(
            shop_finish, "production shop finish", "琉焰的垂青", EVENT_TITLE_REGION,
            artifacts, "07_bless_window.png")
    else:
        click_until_ocr_appears(
            pact_accept, "production pact accept", "轮回当铺", EVENT_TITLE_REGION,
            artifacts, "06_recorded_shop.png", attempts=1, timeout_s=20,
            unpause=False)
        offset = wait_for_marker(offset, "XAR: shop event fired", 10, xar_lines)
        points_seen = optional_ocr_text(
            "100", EVENT_TEXT_REGION, 8, artifacts,
            "06_recorded_100_points.png", contains=True)
        log("recorded shop points OCR: " + ("100 seen" if points_seen else
            "not resolved; production shop title + marker prove non-first-life branch"))
        shop_finish = wait_for_ocr_text(
            "开始此生", EVENT_OPTIONS_FULL_REGION, 15,
            artifacts, "06_recorded_finish.png", contains=True, stable_hits=1)
        click_until_ocr_appears(
            shop_finish, "production shop finish", "琉焰的垂青", EVENT_TITLE_REGION,
            artifacts, "07_bless_window.png")

    offset = wait_for_marker(offset, "XAR: blessing event fired", 10, xar_lines)
    if any("XAR: TEST selftest begin" in line for line in xar_lines):
        raise RunnerError("production smoke unexpectedly entered selftest")
    return xar_lines


def run_off_smoke(debug_offset, artifacts):
    """Prove the off rule stays silent using both OCR and incremental logs."""
    offset = debug_offset
    xar_lines = []
    deadline = time.time() + OFF_OBSERVE_TIMEOUT_S
    last_img = None
    while time.time() < deadline:
        focus_ck3()
        last_img = ImageGrab.grab()
        if find_ocr_text(last_img, "终末之契", EVENT_TITLE_REGION):
            last_img.save(artifacts / "05_off_unexpected_pact.png")
            raise RunnerError("xar_off displayed the pact event")
        text, offset = read_new_lines(DEBUG_LOG, offset)
        new_xar = [line.strip() for line in text.splitlines() if "XAR:" in line]
        xar_lines.extend(new_xar)
        if new_xar:
            last_img.save(artifacts / "05_off_unexpected_marker.png")
            raise RunnerError(f"xar_off emitted XAR enable marker(s): {new_xar}")
        time.sleep(POLL_INTERVAL_S)
    if last_img is not None:
        last_img.save(artifacts / "05_off_observation_passed.png")
    log(f"PASS: xar_off showed no pact or XAR marker for {OFF_OBSERVE_TIMEOUT_S}s")
    return xar_lines


def run_restart_import_probe(expected_record, debug_offset, error_offset, artifacts):
    """Prove a fresh process imported A's lesson without runner pre-seeding."""
    xar_lines = []
    offset = debug_offset
    markers = (
        f"XAR: import state fired k={expected_record}",
        "XAR: import consumed, opening flow",
        "XAR: TEST selftest begin",
        "XAR: TEST PASS import_var",
        "XAR: TEST PASS import_value",
        "XAR: TEST PASS import_points",
        "XAR: UI full flow armed",
    )
    for index, marker in enumerate(markers):
        offset = wait_for_marker(
            offset, marker, 180 if index == 0 else 15, xar_lines)
    wait_for_ocr_text(
        "终末之契", EVENT_TITLE_REGION, 15,
        artifacts, "05_restart_import_pact.png", stable_hits=1)
    err_text, _ = read_new_lines(ERROR_LOG, error_offset)
    xar_errors = [
        line.strip() for line in err_text.splitlines()
        if "xar" in line.lower()
    ]
    fails = [line for line in xar_lines if "XAR: TEST FAIL" in line]
    if fails:
        raise RunnerError(
            f"restart importer emitted {len(fails)} TEST FAIL marker(s)")
    if xar_errors:
        raise RunnerError(
            f"restart importer emitted {len(xar_errors)} xar error.log line(s)")
    log(f"PASS: fresh process imported persisted tier {expected_record}")
    return xar_lines


def run_death_edges(debug_offset, error_offset, artifacts):
    """Exercise a real AI death, then the visible no-heir settlement overlay."""
    offset = debug_offset
    xar_lines = []
    offset = wait_for_marker(
        offset, "XAR: TEST death edges begin", 180, xar_lines)
    offset = wait_for_marker(offset, "XAR: TEST AI death armed", 15, xar_lines)
    offset = wait_for_marker(
        offset, "XAR: TEST AI death observed by on_death", 15, xar_lines)
    focus_ck3()
    click_ratio(2315 / 2560, 1410 / 1440)
    log("unpaused death-edge day-tick chain")

    done = False
    deadline = time.time() + 120
    last_recovery = time.time()
    while time.time() < deadline:
        text, offset = read_new_lines(DEBUG_LOG, offset)
        for line in text.splitlines():
            if "XAR:" in line:
                xar_lines.append(line.strip())
                if "XAR: TEST DONE death_edges" in line:
                    done = True
        if done:
            break
        if time.time() - last_recovery > 10:
            capture_stall_and_recover(
                artifacts, "death_edges", int((time.time() - (deadline - 120)) // 10))
            time.sleep(0.3)
            click_ratio(2315 / 2560, 1410 / 1440)
            last_recovery = time.time()
        time.sleep(POLL_INTERVAL_S)
    if not done:
        raise RunnerError("death-edge DONE marker timeout")

    required = (
        "XAR: TEST AI death armed",
        "XAR: TEST AI death observed by on_death",
        "XAR: TEST PASS ai_actual_death",
        "XAR: TEST PASS ai_on_death_blocked",
        "XAR: TEST PASS no_heir_precondition",
        "XAR: computing score on death",
        "XAR: no player heir; synchronous settlement fallback",
        "XAR: TEST no-heir snapshot committed",
        "XAR: TEST PASS no_heir_synchronous_return",
        "XAR: TEST DONE death_edges",
    )
    positions = []
    for marker in required:
        matches = [index for index, line in enumerate(xar_lines) if marker in line]
        if len(matches) != 1:
            raise RunnerError(
                f"death-edge marker count for '{marker}' is {len(matches)}, expected 1")
        positions.append(matches[0])
    if positions != sorted(positions):
        raise RunnerError("death-edge markers occurred out of order")
    fails = [line for line in xar_lines if "XAR: TEST FAIL" in line]
    if fails:
        raise RunnerError(f"death-edge scenario emitted {len(fails)} FAIL marker(s)")

    settlement_title = wait_for_ocr_text(
        "轮回终结", FULL_SCREEN_REGION, 20,
        artifacts, "06_no_heir_settlement_title.png", contains=True,
        stable_hits=1)
    wait_for_ocr_text(
        "最终分量", FULL_SCREEN_REGION, 20,
        artifacts, "06_no_heir_settlement_description.png", contains=True,
        stable_hits=1)
    focus_ck3()
    settlement_img = ImageGrab.grab()
    value_region = (0.45, 0.24, 0.73, 0.62)
    numeric_rows = [
        text for text, _, _, _ in ocr_results(settlement_img, value_region)
        if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", text.replace(",", ""))
    ]
    grayscale = np.asarray(settlement_img.convert("L"))
    height, width = grayscale.shape
    value_row_centers = (0.284, 0.313, 0.342, 0.371,
                         0.400, 0.429, 0.458, 0.487)
    value_row_ink = []
    for center_y in value_row_centers:
        row = grayscale[
            int(height * (center_y - 0.009)):int(height * (center_y + 0.009)),
            int(width * 0.68):int(width * 0.73),
        ]
        value_row_ink.append(int((row > 150).sum()))
    if len(numeric_rows) < 2 or any(ink < 30 for ink in value_row_ink):
        settlement_img.save(artifacts / "06_no_heir_missing_values.png")
        raise RunnerError(
            "no-heir settlement did not render all eight numeric values: "
            f"ocr={numeric_rows}, ink={value_row_ink}")
    if find_ocr_text(settlement_img, "继续扮演", FULL_SCREEN_REGION, contains=True):
        settlement_img.save(artifacts / "06_no_heir_unexpected_continue.png")
        raise RunnerError("native no-heir Game Over still offered Continue Playing")
    settlement_img.save(artifacts / "06_no_heir_settlement_verified.png")
    log(f"PASS: no-heir settlement visible at {settlement_title}")

    menu_exit = wait_for_ocr_text(
        "退出到菜单", FULL_SCREEN_REGION, 10,
        artifacts, "07_native_no_heir_exit.png", contains=True, stable_hits=1)
    deliberate_click(menu_exit, "no-heir exit to menu")
    confirm_exit = wait_for_ocr_text(
        "退出到主菜单", FULL_SCREEN_REGION, 10,
        artifacts, "08_no_heir_exit_confirmation.png", contains=True,
        stable_hits=1)
    deliberate_click(confirm_exit, "confirmed no-heir exit to main menu")
    wait_for_ocr_text(
        "新游戏", MAIN_MENU_REGION, 30,
        artifacts, "09_no_heir_exit_to_menu.png", contains=True, stable_hits=1)

    err_text, _ = read_new_lines(ERROR_LOG, error_offset)
    xar_errors = [
        line.strip() for line in err_text.splitlines()
        if "xar" in line.lower()
    ]
    if xar_errors:
        raise RunnerError(
            f"death-edge scenario emitted {len(xar_errors)} xar error.log line(s)")
    print("\n===== XAR DEATH EDGE REPORT =====")
    for line in xar_lines:
        print("  " + line)
    print("---------------------------------")
    print("actual AI death : PASS")
    print("AI score blocked: PASS")
    print("no-heir sync    : PASS")
    print("visible settlement: PASS")
    print("exit to menu      : PASS")
    print("xar error.log   : 0")
    return xar_lines


def wait_for_bargain_reopen(
        pair, debug_offset, xar_lines, artifacts, initial_game_day):
    """Cross one real 1095-day delay, dismissing unrelated native events by mouse."""
    no_early = f"XAR: TEST PASS bargain_pair_{pair}_no_early_1094"
    reopened = f"XAR: TEST PASS bargain_pair_{pair}_reopen_1095"
    deadline = time.time() + BARGAIN_REOPEN_TIMEOUT_S
    last_recovery = time.time()
    last_day_change = time.time()
    max_game_day = initial_game_day
    last_hud_check = 0
    stall_attempts = 0
    recovery_sequence = 0
    while time.time() < deadline:
        text, debug_offset = read_new_lines(DEBUG_LOG, debug_offset)
        for line in text.splitlines():
            if "XAR:" in line:
                xar_lines.append(line.strip())
            for match in re.finditer(r"\b(\d{3,4})\.(\d{1,2})\.(\d{1,2})\b", line):
                game_day = ck3_date_ordinal_parts(
                    *(int(part) for part in match.groups()))
                if game_day is not None and (
                        max_game_day is None or game_day > max_game_day):
                    max_game_day = game_day
                    last_day_change = time.time()
                    stall_attempts = 0
        if time.time() - last_hud_check >= 4:
            game_day = read_hud_game_day()
            last_hud_check = time.time()
            if game_day is not None and (
                    max_game_day is None or game_day > max_game_day):
                max_game_day = game_day
                last_day_change = time.time()
                stall_attempts = 0
        fails = [line for line in xar_lines if "XAR: TEST FAIL" in line]
        if fails:
            raise RunnerError(f"bargain-reopen emitted FAIL marker: {fails[-1]}")
        if (any(no_early in line for line in xar_lines)
                and any(reopened in line for line in xar_lines)):
            return debug_offset
        if (time.time() - last_day_change > 12
                and time.time() - last_recovery > 12):
            if stall_attempts >= 3:
                failure = "remained stalled after 3 screenshot-guided recoveries"
                raise RunnerError(
                    f"pair {pair} {failure}; inspect "
                    f"stall_bargain_pair_{pair}_*.png/json")
            stall_attempts += 1
            recovery_sequence += 1
            capture_stall_and_recover(
                artifacts, f"bargain_pair_{pair}", recovery_sequence)
            time.sleep(0.3)
            recovered_day = set_speed_five_and_unpause(
                artifacts, f"pair_{pair}_recovery_{recovery_sequence}",
                require_progress=False)
            if recovered_day is not None:
                max_game_day = recovered_day
                last_day_change = time.time()
                stall_attempts = 0
            last_recovery = time.time()
        time.sleep(POLL_INTERVAL_S)
    raise RunnerError(
        f"pair {pair} did not produce day-1094 and day-1095 markers at speed 5")


def run_bargain_reopen(debug_offset, error_offset, artifacts):
    """Prove three cumulative production pairs and each exact 1095-day reopen."""
    offset = debug_offset
    xar_lines = []
    offset = wait_for_marker(offset, "XAR: TEST bargain reopen begin", 180, xar_lines)
    offset = wait_for_marker(offset, "XAR: TEST PASS bargain_initial_0", 15, xar_lines)

    for pair in range(1, 4):
        offset = wait_for_marker(
            offset, f"XAR: TEST PASS bargain_pair_{pair}_open", 20, xar_lines)
        wait_for_ocr_text(
            "琉焰的垂青", EVENT_TITLE_REGION, 20, artifacts,
            f"bargain_pair_{pair}_blessing.png", stable_hits=1)
        blessing = wait_for_localized_options(
            f"bargain_pair_{pair}_blessing", artifacts, 3)
        offset = click_until_marker(
            blessing, f"pair {pair} production blessing option",
            f"XAR: TEST PASS bargain_pair_{pair}_before_curse",
            offset, xar_lines, failure_marker="XAR: TEST FAIL")

        offset = wait_for_marker(offset, "XAR: curse event fired", 20, xar_lines)
        wait_for_ocr_text(
            "等价的咒痕", EVENT_TITLE_REGION, 20, artifacts,
            f"bargain_pair_{pair}_curse.png", stable_hits=1)
        curse = wait_for_localized_options(
            f"bargain_pair_{pair}_curse", artifacts, 2)
        offset = click_until_marker(
            curse, f"pair {pair} production curse option",
            f"XAR: TEST PASS bargain_pair_{pair}_after_curse",
            offset, xar_lines, failure_marker="XAR: TEST FAIL")

        initial_game_day = set_speed_five_and_unpause(
            artifacts, f"pair_{pair}", capture_tooltip=(pair == 1))
        offset = wait_for_bargain_reopen(
            pair, offset, xar_lines, artifacts, initial_game_day)

    offset = wait_for_marker(
        offset, "XAR: TEST PASS bargain_pair_3_full_reopen", 20, xar_lines)
    offset = wait_for_marker(offset, "XAR: TEST DONE bargain-reopen", 5, xar_lines)
    wait_for_ocr_text(
        "琉焰的垂青", EVENT_TITLE_REGION, 20, artifacts,
        "bargain_pair_3_full_reopen_window.png", stable_hits=1)

    unique_markers = [
        "XAR: TEST bargain reopen begin",
        "XAR: TEST PASS bargain_initial_0",
    ]
    ordered_positions = []
    for marker in unique_markers:
        matches = [index for index, line in enumerate(xar_lines) if marker in line]
        if len(matches) != 1:
            raise RunnerError(f"bargain marker count for '{marker}' is {len(matches)}")
        ordered_positions.append(matches[0])

    production_reopens = [
        index for index, line in enumerate(xar_lines)
        if "XAR: new blessing session (3y timer)" in line
    ]
    if len(production_reopens) != 3:
        raise RunnerError(
            f"production xar.0006 marker count is {len(production_reopens)}, expected 3")

    evidence_pairs = []
    for pair in range(1, 4):
        phase_markers = (
            f"XAR: TEST PASS bargain_pair_{pair}_open",
            f"XAR: TEST PASS bargain_pair_{pair}_before_curse",
            f"XAR: TEST PASS bargain_pair_{pair}_after_curse",
            f"XAR: TEST PASS bargain_pair_{pair}_no_early_1094",
            f"XAR: TEST PASS bargain_pair_{pair}_reopen_1095",
        )
        phase_positions = []
        for marker in phase_markers:
            matches = [
                (index, line) for index, line in enumerate(xar_lines) if marker in line
            ]
            if len(matches) != 1:
                raise RunnerError(f"bargain marker count for '{marker}' is {len(matches)}")
            phase_positions.append(matches[0][0])
        ordered_positions.extend(phase_positions[:4])
        ordered_positions.append(production_reopens[pair - 1])
        ordered_positions.append(phase_positions[4])

        evidence_pairs.append({
            "pair": pair,
            "no_early_delta_days": 1094,
            "production_reopen_delta_days": 1095,
        })

    final_marker = "XAR: TEST PASS bargain_pair_3_full_reopen"
    done_marker = "XAR: TEST DONE bargain-reopen"
    for marker in (final_marker, done_marker):
        matches = [index for index, line in enumerate(xar_lines) if marker in line]
        if len(matches) != 1:
            raise RunnerError(f"bargain marker count for '{marker}' is {len(matches)}")
        ordered_positions.append(matches[0])
    if ordered_positions != sorted(ordered_positions):
        raise RunnerError("bargain production markers occurred out of order")
    fails = [line for line in xar_lines if "XAR: TEST FAIL" in line]
    if fails:
        raise RunnerError(f"bargain-reopen emitted {len(fails)} FAIL marker(s)")

    err_text, _ = read_new_lines(ERROR_LOG, error_offset)
    xar_errors = [
        line.strip() for line in err_text.splitlines() if "xar" in line.lower()
    ]
    if xar_errors:
        raise RunnerError(
            f"bargain-reopen emitted {len(xar_errors)} xar error.log line(s)")

    print("\n===== XAR BARGAIN REOPEN REPORT =====")
    for item in evidence_pairs:
        print(
            f"pair {item['pair']}: no early reopen at day "
            f"{item['no_early_delta_days']}; production reopen at day "
            f"{item['production_reopen_delta_days']}")
    print("cumulative pairs : 1 -> 2 -> 3")
    print("session states   : 1 after blessing, 0 on each xar.0006")
    print("trait XP         : 0 -> 1 -> 2 -> 3")
    print("reject count     : 0")
    print("production reopen: 3 ordered xar.0006 markers")
    print("xar error.log    : 0")
    return {"pairs": evidence_pairs, "production_reopen_markers": 3}


def run_progression_ui(debug_offset, error_offset, artifacts):
    """Prove contract milestones, PB/collection persistence, and Gaze pixels."""
    offset = debug_offset
    xar_lines = []
    offset = wait_for_marker(
        offset, "XAR: TEST progression UI begin", 180, xar_lines)
    offset = wait_for_marker(
        offset, "XAR: TEST PASS progression_initial", 10, xar_lines)

    contract_stages = (
        ("第一块新石", "第一笔", "progression_contract_3"),
        ("六处梁柱", "墨迹正在变暖", "progression_contract_6"),
        ("十座新建之物", "这份典当", "progression_contract_10"),
    )
    for body, option, marker in contract_stages:
        wait_for_ocr_text(
            body, EVENT_TEXT_REGION, 20, artifacts,
            f"{marker}_body.png", contains=True, stable_hits=1)
        option_point = wait_for_ocr_text(
            option, EVENT_OPTIONS_FULL_REGION, 15, artifacts,
            f"{marker}_option.png", contains=True, stable_hits=1)
        capture_ocr_bundle(artifacts, marker, FULL_SCREEN_REGION)
        offset = click_until_marker(
            option_point, marker.replace("_", " "),
            f"XAR: TEST PASS {marker}", offset, xar_lines,
            failure_marker="XAR: TEST FAIL")

    wait_for_ocr_text(
        "第一重火纹睁开", EVENT_TEXT_REGION, 20, artifacts,
        "progression_gaze_10_body.png", contains=True, stable_hits=1)
    gaze_option = wait_for_ocr_text(
        "我收下这份迟来的好意", EVENT_OPTIONS_FULL_REGION, 15, artifacts,
        "progression_gaze_10_option.png", contains=True, stable_hits=1)
    capture_ocr_bundle(artifacts, "progression_gaze_10", FULL_SCREEN_REGION)
    offset = click_until_marker(
        gaze_option, "Gaze milestone 10",
        "XAR: TEST progression ledger ready", offset, xar_lines,
        failure_marker="XAR: TEST FAIL")

    expected_lessons = {
        "xar_contract_pb_steward_3",
        "xar_contract_pb_steward_6",
        "xar_contract_pb_steward_10",
        "xar_contract_complete_steward",
    }
    lessons = wait_for_contract_lessons(expected_lessons)
    (artifacts / "progression_contract_lessons.json").write_text(
        json.dumps(lessons, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"PASS: persistent contract lessons={lessons}")

    offset, ledger_close, _ = open_native_ledger(
        offset, xar_lines, artifacts, "progression")
    ledger_ocr = wait_for_ocr_tokens(
        ("本世契约", "贤王", "0/10", "PB 10", "已完成契约", "R 1", "S 0"),
        ("PB 0", "已完成契约: 无", "XAR_SYNC_SENTINEL", "ERROR:", "xar_"),
        FULL_SCREEN_REGION, 20, artifacts, "progression_ledger_pixels")
    offset = click_until_marker(
        ledger_close, "progression ledger close",
        "XAR: TEST DONE progression-ui", offset, xar_lines,
        failure_marker="XAR: TEST FAIL")

    required = {
        "progression_initial", "progression_contract_3",
        "progression_contract_6", "progression_contract_10",
        "progression_gaze_10", "ui_ledger_open", "ui_ledger_close",
        "progression_ledger_state",
    }
    observed = {
        line.split("XAR: TEST PASS ", 1)[1].strip()
        for line in xar_lines if "XAR: TEST PASS " in line
    }
    missing = sorted(required - observed)
    fails = [line for line in xar_lines if "XAR: TEST FAIL" in line]
    if fails or missing:
        raise RunnerError(
            f"progression-ui assertions failed: fails={len(fails)}, missing={missing}")
    err_text, _ = read_new_lines(ERROR_LOG, error_offset)
    xar_errors = [
        line.strip() for line in err_text.splitlines() if "xar" in line.lower()
    ]
    if xar_errors:
        raise RunnerError(f"progression-ui emitted {len(xar_errors)} xar error line(s)")

    print("\n===== XAR PROGRESSION UI REPORT =====")
    print("contract milestones: 3 -> 6 -> 10 production events")
    print("persistent PB       : PB 10 (3/6/10 lessons)")
    print("collection          : Wise Ruler / mask 16")
    print("Gaze milestone      : level 10, R 1, S 0")
    print("ledger pixels       : current 0/10 + historical PB/collection")
    print("xar error.log       : 0")
    return {
        "contract": "steward",
        "milestones": [3, 6, 10],
        "persistent_lessons": lessons,
        "collection_mask": 16,
        "gaze_milestone": 10,
        "ledger_ocr": ledger_ocr,
    }


def run_scoring_matrix(debug_offset, error_offset, artifacts):
    """Prove controlled descendant scoring and all 200 production dispatchers."""
    xar_lines = []
    wait_for_marker(
        debug_offset, "XAR: TEST DONE scoring-matrix", 240, xar_lines)
    required = {
        "scoring_descendant_matrix", "pool_dispatch_all_200",
        "scoring_dispatcher_state",
    }
    observed = {
        line.split("XAR: TEST PASS ", 1)[1].strip()
        for line in xar_lines if "XAR: TEST PASS " in line
    }
    expected_pool_markers = {
        f"pool_dispatch_{prefix}_{wire_id:03d}"
        for prefix in ("bless", "curse") for wire_id in range(100)
    }
    missing = sorted((required | expected_pool_markers) - observed)
    fails = [line for line in xar_lines if "XAR: TEST FAIL" in line]
    if "XAR: TEST scoring matrix begin" not in "\n".join(xar_lines):
        missing.insert(0, "scoring_matrix_begin")
    if fails or missing:
        raise RunnerError(
            f"scoring-matrix assertions failed: fails={len(fails)}, "
            f"missing={missing[:20]}{'...' if len(missing) > 20 else ''}")
    err_text, _ = read_new_lines(ERROR_LOG, error_offset)
    xar_errors = [
        line.strip() for line in err_text.splitlines() if "xar" in line.lower()
    ]
    if xar_errors:
        raise RunnerError(f"scoring-matrix emitted {len(xar_errors)} xar error line(s)")

    (artifacts / "scoring_matrix_markers.json").write_text(
        json.dumps(sorted(observed), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print("\n===== XAR SCORING MATRIX REPORT =====")
    print("descendant graph     : 7 living / depth 1-5 / shared-path dedup")
    print("dead intermediate    : traversed; living depth-2..5 counted")
    print("depth-six control    : excluded")
    print("preview parity       : within 0.01 of production score")
    print("pool dispatchers     : 200/200 production wire branches")
    print("dispatcher state     : counters, modifiers, rarity, Gaze XP committed")
    print("xar error.log        : 0")
    return {
        "living_descendants": 7,
        "max_scored_depth": 5,
        "dead_intermediate": True,
        "deduplicated_shared_descendant": True,
        "preview_tolerance": 0.01,
        "pool_dispatchers": 200,
        "pool_markers": len(expected_pool_markers & observed),
    }


def run_selftest(import_record, debug_offset, error_offset, artifacts):
    """Preserve the full existing selftest behavior and console report."""
    offset = debug_offset
    xar_lines = []
    offset = wait_for_marker(offset, "XAR: TEST selftest begin", 180, xar_lines)
    offset = wait_for_marker(offset, "XAR: UI pact window opened", 30, xar_lines)
    wait_for_ocr_text(
        "终末之契", EVENT_TITLE_REGION, 15,
        artifacts, "05_pact_window.png", stable_hits=1)
    pact_accept = wait_for_ocr_text(
        "我接受", EVENT_OPTIONS_FULL_REGION, 15,
        artifacts, "05_pact_accept.png", contains=True, stable_hits=1)
    offset = click_until_marker(
        pact_accept, "production pact accept", "XAR: UI pact accepted",
        offset, xar_lines)

    offset = wait_for_marker(offset, "XAR: UI shop window opened", 15, xar_lines)
    wait_for_ocr_text(
        "轮回当铺", EVENT_TITLE_REGION, 15,
        artifacts, "05_shop_window.png", stable_hits=1)
    diplomacy_buy = wait_for_ocr_text(
        "外交", EVENT_OPTIONS_FULL_REGION, 15,
        artifacts, "05_shop_diplomacy.png", contains=True, stable_hits=1)
    offset = click_until_marker(
        diplomacy_buy, "production diplomacy purchase",
        "XAR: TEST PASS ui_shop_purchase", offset, xar_lines,
        failure_marker="XAR: TEST FAIL ui_shop_purchase")
    shop_finish = wait_for_ocr_text(
        "开始此生", EVENT_OPTIONS_FULL_REGION, 15,
        artifacts, "05_shop_finish.png", contains=True, stable_hits=1)
    offset = click_until_marker(
        shop_finish, "production shop finish",
        "XAR: TEST PASS ui_shop_finish", offset, xar_lines)

    offset = wait_for_marker(offset, "XAR: UI bless window opened", 30, xar_lines)
    wait_for_ocr_text(
        "琉焰的垂青", EVENT_TITLE_REGION, 15,
        artifacts, "05_bless_window.png", stable_hits=1)
    reroll_option = wait_for_ocr_text(
        "重抽", EVENT_OPTIONS_FULL_REGION, 15,
        artifacts, "05_bless_reroll.png", contains=True, stable_hits=1)
    offset = click_until_marker(
        reroll_option, "production blessing reroll",
        "XAR: TEST PASS ui_reroll",
        offset, xar_lines)
    wait_for_ocr_text(
        "琉焰的垂青", EVENT_TITLE_REGION, 15,
        artifacts, "05_bless_after_reroll.png", stable_hits=1)
    wait_for_localized_options("bless_after_reroll", artifacts, 3)
    decline_option = wait_for_ocr_text(
        "什么都不领", EVENT_OPTIONS_FULL_REGION, 15,
        artifacts, "05_bless_decline.png", contains=True, stable_hits=1)
    offset = click_until_marker(
        decline_option, "production blessing decline",
        "XAR: TEST PASS ui_bless_decline", offset, xar_lines)
    wait_for_ocr_text(
        "琉焰的垂青", EVENT_TITLE_REGION, 15,
        artifacts, "05_bless_after_decline.png", stable_hits=1)
    bless_option = wait_for_localized_options("bless_after_decline", artifacts, 3)
    offset = click_until_marker(
        bless_option, "localized bless option before seal",
        "XAR: UI bless accepted", offset, xar_lines)
    offset = wait_for_marker(offset, "XAR: UI curse window opened", 30, xar_lines)
    wait_for_ocr_text(
        "等价的咒痕", EVENT_TITLE_REGION, 15,
        artifacts, "05_curse_window.png", stable_hits=1)
    wait_for_localized_options("curse_before_seal", artifacts, 2)
    seal_option = wait_for_ocr_text(
        "封印", EVENT_OPTIONS_FULL_REGION, 15,
        artifacts, "05_curse_seal.png", contains=True, stable_hits=1)
    offset = click_until_marker(
        seal_option, "production curse seal", "XAR: TEST PASS ui_seal",
        offset, xar_lines)
    wait_for_ocr_text(
        "琉焰的垂青", EVENT_TITLE_REGION, 15,
        artifacts, "05_bless_after_seal.png", stable_hits=1)
    bless_option = wait_for_localized_options("bless_after_seal", artifacts, 3)
    offset = click_until_marker(
        bless_option, "localized bless option after seal",
        "XAR: UI bless accepted", offset, xar_lines)
    offset = wait_for_marker(offset, "XAR: UI curse window opened", 30, xar_lines)
    wait_for_ocr_text(
        "等价的咒痕", EVENT_TITLE_REGION, 15,
        artifacts, "05_curse_after_seal.png", stable_hits=1)
    curse_option = wait_for_localized_options("curse_after_seal", artifacts, 2)
    offset = click_until_marker(
        curse_option, "localized curse option after seal",
        "XAR: TEST PASS ui_curse_after_seal", offset, xar_lines)

    offset, ledger_close, decisions_tab = open_native_ledger(
        offset, xar_lines, artifacts, "06")
    offset = click_until_marker(
        ledger_close, "production ledger close",
        "XAR: TEST PASS ui_ledger_close", offset, xar_lines)

    screen_width, screen_height = pyautogui.size()
    pyautogui.moveTo(int(screen_width * 0.90), int(screen_height * 0.70))
    contract_decision = wait_for_ocr_text(
        "选择本世契约", FULL_SCREEN_REGION, 15,
        artifacts, "06_contract_decision.png", contains=True, stable_hits=1)
    pyautogui.moveTo(int(screen_width * 0.90), contract_decision[1], duration=0.2)
    pyautogui.mouseDown()
    time.sleep(0.12)
    pyautogui.mouseUp()
    pyautogui.moveTo(int(screen_width * 0.50), int(screen_height * 0.08), duration=0.2)
    contract_confirm = wait_for_ocr_text(
        "请他", FULL_SCREEN_REGION, 15,
        artifacts, "06_contract_confirm.png", contains=True, stable_hits=1)
    offset = click_until_marker(
        contract_confirm, "native contract decision confirm",
        "XAR: UI contract decision confirmed", offset, xar_lines)
    wait_for_ocr_text(
        "此生的典当", EVENT_TITLE_REGION, 15,
        artifacts, "06_contract_event.png", stable_hits=1)
    contract_option = wait_for_ocr_text(
        "征服者", EVENT_OPTIONS_FULL_REGION, 15,
        artifacts, "06_contract_option.png", contains=True, stable_hits=1)
    offset = click_until_marker(
        contract_option, "production contract selection",
        "XAR: TEST PASS ui_contract_select", offset, xar_lines)

    focus_ck3()
    pyautogui.click(*decisions_tab)
    player_open = False
    for attempt in range(1, 4):
        click_ratio(0.50, 0.50)
        log(f"clicked acceptance-only player-character bridge (attempt {attempt})")
        try:
            wait_for_ocr_text(
                "罗贝尔", CHARACTER_PANEL_REGION, 5,
                artifacts, "07_character_panel.png", contains=True,
                stable_hits=1)
            player_open = True
            break
        except RunnerError:
            continue
    if not player_open:
        raise RunnerError("test bridge did not open the player character")
    character_img = ImageGrab.grab()
    match_score, trait_point = find_scaled_template(
        character_img,
        MOD_ROOT / "gfx/interface/icons/traits/glassfire_trait.dds",
        CHARACTER_PANEL_REGION,
        (0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60, 0.70))
    log(f"trait icon template score={match_score:.3f} at {trait_point}")
    if trait_point is None or match_score < 0.35:
        raise RunnerError(f"Glassfire trait icon not found (score={match_score:.3f})")
    pyautogui.moveTo(*trait_point, duration=0.2)
    time.sleep(0.8)
    wait_for_ocr_text(
        "当前分量", FULL_SCREEN_REGION, 15,
        artifacts, "07_trait_hover.png", contains=True, stable_hits=1)
    log("PASS: real Glassfire Gaze hover rendered live score")
    ui_ok = True

    focus_ck3()
    click_ratio(2315 / 2560, 1410 / 1440)
    log("unpaused after UI localization test")
    done = False
    deadline = time.time() + TEST_TIMEOUT_S
    date_re = re.compile(r"\b(\d{3,4})\.(\d{1,2})\.(\d{1,2})\b")
    max_date = None
    last_day_change = time.time()
    last_recovery = 0
    stall_attempts = 0
    while time.time() < deadline:
        text, offset = read_new_lines(DEBUG_LOG, offset)
        for line in text.splitlines():
            if "XAR:" in line:
                xar_lines.append(line.strip())
                if "XAR: TEST DONE" in line:
                    done = True
            match = date_re.search(line)
            if match:
                current_date = tuple(int(part) for part in match.groups())
                if max_date is None or current_date > max_date:
                    max_date = current_date
                    last_day_change = time.time()
                    stall_attempts = 0
        if done:
            break
        if time.time() - last_day_change > 8 and time.time() - last_recovery > 8:
            focus_ck3()
            img = ImageGrab.grab()
            continue_button = find_ocr_text(
                img, "继续扮演", (0.45, 0.55, 0.80, 0.90), contains=True)
            if continue_button:
                pyautogui.click(*continue_button)
                log(f"OCR-clicked succession continue at {continue_button}")
                time.sleep(0.5)
            else:
                if stall_attempts >= 3:
                    raise RunnerError(
                        "selftest remained stalled after 3 screenshot-guided "
                        "recoveries; inspect stall_selftest_*.png/json")
                stall_attempts += 1
                capture_stall_and_recover(
                    artifacts, "selftest", stall_attempts)
            click_ratio(2315 / 2560, 1410 / 1440)
            log(f"date frozen at {max_date}; recovery play click")
            last_recovery = time.time()
        time.sleep(POLL_INTERVAL_S)
    if not done:
        raise RunnerError("TEST DONE marker timeout")

    focus_ck3()
    ImageGrab.grab().save(artifacts / "04_end_state.png")
    settlement = wait_for_ocr_text(
        "很好", EVENT_OPTIONS_FULL_REGION, 15,
        artifacts, "04_settlement_option.png", contains=True, stable_hits=1)
    click_until_ocr_appears(
        settlement, "settlement confirmation", "正在观察", OBSERVER_REGION,
        artifacts, "05_observer_mode.png", attempts=2, timeout_s=15)
    focus_ck3()
    ImageGrab.grab().save(artifacts / "05_after_confirm.png")
    log("settlement confirmed; observer mode proven by vanilla HUD")

    persist_ok = False
    contract_persist_ok = False
    try:
        live = TUTORIAL_TXT.read_text(encoding="utf-8", errors="ignore")
        record_bits = re.findall(r"(?m)^\s*(xar_hs_ge_(\d+))\s*$", live)
        persist_ok = any(int(value) > import_record for _, value in record_bits)
        contract_persist_ok = bool(re.search(
            r"(?m)^\s*xar_contract_pb_steward_3\s*$", live))
        log(f"tutorial.txt bits after run: {record_bits if record_bits else 'NONE'}")
    except OSError:
        pass
    err_text, _ = read_new_lines(ERROR_LOG, error_offset)
    xar_errors = [line.strip() for line in err_text.splitlines() if "xar" in line.lower()]
    passes = [line for line in xar_lines if "XAR: TEST PASS" in line]
    fails = [line for line in xar_lines if "XAR: TEST FAIL" in line]
    observed_passes = {
        line.split("XAR: TEST PASS ", 1)[1].strip()
        for line in passes if "XAR: TEST PASS " in line
    }
    missing_passes = sorted(REQUIRED_PASSES - observed_passes)
    import_ok = any(
        f"XAR: import state fired k={import_record}" in line for line in xar_lines)
    sweep_ok = any("XAR: TEST sweep complete" in line for line in xar_lines)
    print("\n===== XAR ACCEPTANCE REPORT =====")
    for line in xar_lines:
        print("  " + line)
    print("---------------------------------")
    print(f"TEST DONE seen : {done}")
    print(f"UI loc check   : {'PASS' if ui_ok else 'FAIL'}")
    print(f"PASS count     : {len(passes)}")
    print(f"required PASS  : {'PASS' if not missing_passes else 'MISSING ' + ', '.join(missing_passes)}")
    print(f"import level   : {'PASS' if import_ok else 'FAIL'} (expected {import_record})")
    print(f"pool sweep     : {'PASS' if sweep_ok else 'FAIL'}")
    print(f"FAIL count     : {len(fails)}")
    print(f"tutorial persist: {'PASS' if persist_ok else 'FAIL (or not done)'}")
    print(f"contract PB persist: {'PASS' if contract_persist_ok else 'FAIL'}")
    print(f"xar error.log  : {len(xar_errors)}")
    for line in xar_errors:
        print("  ERR " + line)
    print(f"artifacts      : {artifacts}")
    ok = (done and ui_ok and not fails and not missing_passes and import_ok and
          sweep_ok and not xar_errors and persist_ok and contract_persist_ok)
    print("RESULT: " + ("GREEN" if ok else "RED"))
    if ok:
        return None
    reasons = []
    if fails:
        reasons.append(f"{len(fails)} TEST FAIL marker(s)")
    if missing_passes:
        reasons.append("missing PASS: " + ", ".join(missing_passes))
    if not import_ok:
        reasons.append(f"import marker {import_record} missing")
    if not sweep_ok:
        reasons.append("pool sweep marker missing")
    if xar_errors:
        reasons.append(f"{len(xar_errors)} xar error.log line(s)")
    if not persist_ok:
        reasons.append("tutorial record bit not persisted")
    if not contract_persist_ok:
        reasons.append("contract PB lesson not persisted")
    return "; ".join(reasons) or "selftest acceptance checks failed"


def mod_tree_hash(root=MOD_ROOT):
    digest = hashlib.sha256()
    for path in build_release.release_files(root):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(path.read_bytes())
    return digest.hexdigest()


def write_json_report(artifacts, scenario, result, import_record, timings,
                      error_reason, run_id, started_at, source_mode,
                      runtime_tree_sha256, evidence=None):
    junit = artifacts / "report.xml"
    failure = "" if result == "GREEN" else (
        f'<failure message="{html.escape(error_reason or "acceptance failed", quote=True)}" />')
    junit.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<testsuite name="xar.acceptance" tests="1" failures="{0 if result == "GREEN" else 1}" time="{timings.get("total", 0)}">\n'
        f'  <testcase classname="xar.acceptance" name="{scenario}" time="{timings.get("scenario", 0)}">{failure}</testcase>\n'
        '</testsuite>\n',
        encoding="utf-8",
    )
    files = sorted(
        str(path.relative_to(artifacts)).replace("\\", "/")
        for path in artifacts.rglob("*")
        if path.is_file() and path.name != "report.json"
    )
    report = {
        "schema_version": 1,
        "run_id": run_id,
        "started_at_utc": started_at,
        "scenario": scenario,
        "result": result,
        "mod_version": build_release.descriptor_version(MOD_ROOT),
        "git_sha": build_release.git_sha(),
        "mod_tree_sha256": mod_tree_hash(),
        "workshop_item_id": build_release.WORKSHOP_ITEM_ID,
        "source_mode": source_mode,
        "runtime_tree_sha256": runtime_tree_sha256,
        "debug_mode": True,
        "game_version": os.environ.get("XAR_CK3_VERSION") or "1.19.0.6",
        "environment": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "desktop": f"{pyautogui.size().width}x{pyautogui.size().height}",
        },
        "artifacts": {"directory": str(artifacts), "files": files},
        "import_record": import_record,
        "phase_timings_seconds": timings,
        "error_reason": error_reason,
    }
    if evidence:
        report["scenario_evidence"] = evidence
        if scenario == "persistence-restart":
            report["persistence_restart"] = evidence
    (artifacts / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(scenario="selftest", import_record=0, artifacts_dir=None):
    run_started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    effective_record = {
        "selftest": import_record,
        "on-first-life": 0,
        "on-recorded": 100,
        "on-high-budget": 2000,
        "off": 0,
        "persistence-restart": 0,
        "death-edges": 1,
        "bargain-reopen": 2,
        "progression-ui": 3,
        "scoring-matrix": 4,
    }[scenario]
    rule_setting = "xar_selftest" if scenario in (
        "selftest", "persistence-restart", "death-edges", "bargain-reopen",
        "progression-ui", "scoring-matrix") else (
        "xar_off" if scenario == "off" else "xar_on")
    if artifacts_dir:
        artifacts = Path(artifacts_dir).expanduser().resolve()
        artifacts.mkdir(parents=True, exist_ok=False)
    else:
        artifacts = Path(tempfile.mkdtemp(prefix="xar_accept_"))
    run_id = artifacts.name
    log(f"scenario={scenario}, import_record={effective_record}, artifacts={artifacts}")
    timings = {}
    result = "RED"
    error_reason = None
    backup = Path(tempfile.mkdtemp(prefix="xar_accept_backup_"))
    ck3_pid_file = artifacts / "ck3.pid"
    backup_ready = False
    restore_succeeded = False
    ck3_process = None
    report_evidence = {}
    source_mode = "repository-synced-workshop-cache"
    runtime_source = MOD_ROOT
    runtime_tree_sha256 = mod_tree_hash(runtime_source)
    log_offsets = {DEBUG_LOG: None, ERROR_LOG: None, GUI_WARNINGS_LOG: None}
    session_artifacts = artifacts
    if scenario == "persistence-restart":
        session_artifacts = artifacts / "writer"
        session_artifacts.mkdir()

    try:
        with timed_phase(timings, "setup_backup"):
            if _ocr is None:
                raise RunnerError("RapidOCR missing; install tools/requirements.txt")
            preflight()
            shutil.copy2(TUTORIAL_TXT, backup / "tutorial.txt")
            shutil.copy2(PRESETS_TXT, backup / "presets.txt")
            backup_ready = True
            start_restore_watchdog(backup, ck3_pid_file)
            log("restore watchdog armed")
            autosave_count = isolate_autosaves(backup)
            log(
                "backed up tutorial.txt + presets.txt; "
                f"isolated {autosave_count} autosave(s)")

        with timed_phase(timings, "static_validation"):
            if validate_static.main() != 0:
                raise RunnerError("static validation failed")
            descriptor = (MOD_ROOT / "descriptor.mod").read_text(encoding="utf-8-sig")
            if "remote_file_id" in descriptor:
                raise RunnerError("repository descriptor.mod contains remote_file_id")
            log("static validation passed")

        with timed_phase(timings, "sync_and_configure"):
            if scenario in ("on-first-life", "on-recorded", "on-high-budget", "off"):
                runtime_source = artifacts / "release_projection"
                build_release.build_release(
                    MOD_ROOT, runtime_source, revision=build_release.git_sha())
                source_mode = "production-release-projection"
                log("built stripped release projection for production smoke")
            runtime_tree_sha256 = mod_tree_hash(runtime_source)
            sync_repo_to_ugc(ugc_content_dir(), runtime_source)
            raw = TUTORIAL_TXT.read_bytes()
            seeded, removed = set_tutorial_record(raw, effective_record)
            TUTORIAL_TXT.write_bytes(seeded)
            log(
                f"tutorial.txt: removed {removed} XAR record bit(s), "
                f"seeded {effective_record}")
            patched = set_last_applied_rule(
                (backup / "presets.txt").read_bytes(), rule_setting)
            PRESETS_TXT.write_bytes(patched)
            log(f"LastAppliedRules set exclusively to {rule_setting} before launch")

        with timed_phase(timings, "launch"):
            kill_ck3()
            time.sleep(3)
            error_offset = ERROR_LOG.stat().st_size if ERROR_LOG.exists() else 0
            debug_offset = DEBUG_LOG.stat().st_size if DEBUG_LOG.exists() else 0
            log_offsets = {
                DEBUG_LOG: debug_offset,
                ERROR_LOG: error_offset,
                GUI_WARNINGS_LOG: (
                    GUI_WARNINGS_LOG.stat().st_size if GUI_WARNINGS_LOG.exists() else 0),
            }
            ck3_process = subprocess.Popen(
                [str(CK3_EXE), "-debug_mode"], cwd=str(CK3_EXE.parent))
            ck3_pid_file.write_text(str(ck3_process.pid), encoding="ascii")
            log("launched ck3; OCR waiting for main menu")

        with timed_phase(timings, "lobby"):
            navigate_lobby(session_artifacts)
            shutil.copy2(backup / "presets.txt", PRESETS_TXT)
            log("restored presets.txt after OCR-confirmed start transition")

        with timed_phase(timings, "scenario"):
            if scenario == "persistence-restart":
                writer_started = time.perf_counter()
                writer_reason = run_selftest(
                    0, debug_offset, error_offset, session_artifacts)
                if writer_reason:
                    raise RunnerError(f"writer process failed: {writer_reason}")
                writer_record, writer_hash = wait_for_stable_persisted_record()
                timings["writer_process"] = round(
                    time.perf_counter() - writer_started, 3)
                stop_ck3_process(ck3_process, ck3_pid_file)
                ck3_process = None
                stopped_record, stopped_hash = wait_for_stable_persisted_record()
                if stopped_record != writer_record:
                    raise RunnerError(
                        f"writer record changed across exit: "
                        f"{writer_record} -> {stopped_record}")
                log(
                    f"process A handoff: tier={stopped_record}, "
                    f"sha256={stopped_hash}")

                reader_artifacts = artifacts / "reader"
                reader_artifacts.mkdir()
                PRESETS_TXT.write_bytes(set_last_applied_rule(
                    (backup / "presets.txt").read_bytes(), "xar_selftest"))
                if tutorial_record_state() != (stopped_record, stopped_hash):
                    raise RunnerError(
                        "tutorial.txt changed before process B without pre-seeding")
                reader_error_offset = (
                    ERROR_LOG.stat().st_size if ERROR_LOG.exists() else 0)
                reader_debug_offset = (
                    DEBUG_LOG.stat().st_size if DEBUG_LOG.exists() else 0)
                reader_started = time.perf_counter()
                ck3_process = subprocess.Popen(
                    [str(CK3_EXE), "-debug_mode"], cwd=str(CK3_EXE.parent))
                ck3_pid_file.write_text(str(ck3_process.pid), encoding="ascii")
                log("launched fresh process B without tutorial pre-seeding")
                navigate_lobby(reader_artifacts)
                shutil.copy2(backup / "presets.txt", PRESETS_TXT)
                run_restart_import_probe(
                    stopped_record, reader_debug_offset, reader_error_offset,
                    reader_artifacts)
                timings["reader_process"] = round(
                    time.perf_counter() - reader_started, 3)
                report_evidence = {
                    "process_count": 2,
                    "writer_record": writer_record,
                    "imported_record": stopped_record,
                    "tutorial_handoff_sha256": stopped_hash,
                    "writer_pre_exit_sha256": writer_hash,
                    "process_b_preseeded": False,
                }
            elif scenario == "death-edges":
                run_death_edges(debug_offset, error_offset, artifacts)
            elif scenario == "bargain-reopen":
                report_evidence = run_bargain_reopen(
                    debug_offset, error_offset, artifacts)
            elif scenario == "progression-ui":
                report_evidence = run_progression_ui(
                    debug_offset, error_offset, artifacts)
            elif scenario == "scoring-matrix":
                report_evidence = run_scoring_matrix(
                    debug_offset, error_offset, artifacts)
            elif scenario == "selftest":
                error_reason = run_selftest(
                    effective_record, debug_offset, error_offset, artifacts)
            elif scenario == "off":
                run_off_smoke(debug_offset, artifacts)
            else:
                xar_lines = run_production_smoke(
                    scenario, effective_record, debug_offset, artifacts)
                err_text, _ = read_new_lines(ERROR_LOG, error_offset)
                xar_errors = [
                    line.strip() for line in err_text.splitlines()
                    if "xar" in line.lower()
                ]
                print("\n===== XAR PRODUCTION SMOKE REPORT =====")
                print(f"scenario        : {scenario}")
                print(f"import level    : {effective_record}")
                print(f"XAR markers     : {len(xar_lines)}")
                print(f"xar error.log   : {len(xar_errors)}")
                for line in xar_errors:
                    print("  ERR " + line)
                print(f"artifacts       : {artifacts}")
                if xar_errors:
                    error_reason = f"{len(xar_errors)} xar error.log line(s)"
            if scenario == "off":
                err_text, _ = read_new_lines(ERROR_LOG, error_offset)
                xar_errors = [
                    line.strip() for line in err_text.splitlines()
                    if "xar" in line.lower()
                ]
                print("\n===== XAR PRODUCTION SMOKE REPORT =====")
                print(f"scenario        : {scenario}")
                print(f"observe seconds : {OFF_OBSERVE_TIMEOUT_S}")
                print(f"xar error.log   : {len(xar_errors)}")
                for line in xar_errors:
                    print("  ERR " + line)
                print(f"artifacts       : {artifacts}")
                if xar_errors:
                    error_reason = f"{len(xar_errors)} xar error.log line(s)"
            if error_reason is None:
                result = "GREEN"
                if scenario not in (
                        "selftest", "persistence-restart", "death-edges",
                        "bargain-reopen"):
                    print("RESULT: GREEN")
                elif scenario == "persistence-restart":
                    print("\n===== XAR PERSISTENCE RESTART REPORT =====")
                    print(f"writer record   : {report_evidence['writer_record']}")
                    print(f"handoff SHA-256 : {report_evidence['tutorial_handoff_sha256']}")
                    print("process B seeded: no")
                    print("RESULT: GREEN")
                elif scenario == "death-edges":
                    print("RESULT: GREEN")
                elif scenario == "bargain-reopen":
                    print("RESULT: GREEN")
            elif scenario not in (
                    "selftest", "persistence-restart", "death-edges",
                    "bargain-reopen"):
                print("RESULT: RED")
    except Exception as exc:
        error_reason = str(exc)
        log(f"FATAL: {exc}")
        if not isinstance(exc, RunnerError):
            traceback.print_exc()
        try:
            focus_ck3()
            ImageGrab.grab().save(artifacts / "fatal_state.png")
        except Exception:
            pass
        print(f"artifacts: {artifacts}")
        print("RESULT: RED")
    finally:
        try:
            with timed_phase(timings, "restore"):
                if ck3_pid_file.exists():
                    try:
                        if ck3_process is not None:
                            stop_ck3_process(ck3_process, ck3_pid_file)
                        else:
                            kill_process(int(ck3_pid_file.read_text(encoding="ascii")))
                    except (OSError, ValueError):
                        pass
                    ck3_pid_file.unlink(missing_ok=True)
                if backup_ready:
                    time.sleep(2)
                    shutil.copy2(backup / "tutorial.txt", TUTORIAL_TXT)
                    shutil.copy2(backup / "presets.txt", PRESETS_TXT)
                    restore_autosaves(backup)
                    restore_succeeded = True
                    log("restored tutorial.txt + presets.txt + autosaves, ck3 killed")
        except Exception as restore_exc:
            result = "RED"
            restore_reason = f"restore failed: {restore_exc}"
            error_reason = (
                f"{error_reason}; {restore_reason}" if error_reason else restore_reason)
            log(restore_reason)
            print("RESULT: RED")
        timings["total"] = round(time.perf_counter() - run_started, 3)
        if backup_ready and restore_succeeded:
            shutil.rmtree(backup, ignore_errors=True)
        elif backup_ready:
            log(f"recovery backup retained at {backup}")
        for path, offset in log_offsets.items():
            try:
                snapshot_log(path, offset, artifacts / f"incremental_{path.name}")
            except OSError as snapshot_exc:
                log(f"unable to snapshot {path.name}: {snapshot_exc}")
        write_json_report(
            artifacts, scenario, result, effective_record, timings, error_reason,
            run_id, started_at, source_mode, runtime_tree_sha256, report_evidence)
        log(f"JSON report: {artifacts / 'report.json'}")
    return 0 if result == "GREEN" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run CK3 automated acceptance")
    parser.add_argument(
        "--scenario",
        choices=("selftest", "on-first-life", "on-recorded", "on-high-budget", "off",
                 "persistence-restart", "death-edges", "bargain-reopen",
                 "progression-ui", "scoring-matrix"),
        default="selftest",
        help="acceptance scenario (default: selftest)")
    parser.add_argument(
        "--import-record", type=int, choices=(0, 100), default=0,
        help="selftest tutorial record; production scenarios use fixed baselines")
    parser.add_argument(
        "--artifacts-dir",
        help="create this exact artifact directory instead of a random temp path")
    parser.add_argument(
        "--preflight", action="store_true",
        help="validate dedicated desktop paths and safety constraints, then exit")
    args = parser.parse_args()
    if args.preflight:
        preflight()
        sys.exit(0)
    if args.scenario == "persistence-restart" and args.import_record != 0:
        parser.error("persistence-restart forbids --import-record pre-seeding")
    sys.exit(main(args.scenario, args.import_record, args.artifacts_dir))

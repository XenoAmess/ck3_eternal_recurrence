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
# 现场保护：tutorial.txt / player\game_rules\presets.txt 先备份到临时目录，
#   结束时无论成败原样恢复（runner 本身也会被杀进程方式中断时尽量在 finally 恢复）。

import argparse
from contextlib import contextmanager
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
import win32con
import win32gui
from PIL import Image, ImageGrab

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
CK3_EXE = ROOT / "Crusader Kings III" / "binaries" / "ck3.exe"
USER_DIR = Path.home() / "Documents" / "Paradox Interactive" / "Crusader Kings III"
MOD_ROOT = ROOT / "XenoAmess_s_Eternal_Recurrence"
UGC_MOD_FILE = USER_DIR / "mod" / "ugc_3784706360.mod"
TUTORIAL_TXT = USER_DIR / "tutorial.txt"
PRESETS_TXT = USER_DIR / "player" / "game_rules" / "presets.txt"
DEBUG_LOG = USER_DIR / "logs" / "debug.log"
ERROR_LOG = USER_DIR / "logs" / "error.log"
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
FULL_SCREEN_REGION = (0.00, 0.00, 1.00, 1.00)

BOOT_TIMEOUT_S = 120             # OCR 一发现主菜单即继续，不固定睡 100 秒
LOBBY_TIMEOUT_S = 30
TEST_TIMEOUT_S = 300             # 开局后等待 TEST DONE 的超时
OFF_OBSERVE_TIMEOUT_S = 30
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
    if found:
        win32gui.ShowWindow(found[0], win32con.SW_RESTORE)
        try:
            win32gui.SetForegroundWindow(found[0])
        except Exception:
            pass
        return True
    return False


def ugc_content_dir():
    """工坊缓存目录（游戏实际加载的就是它——播放集启用的是 ugc 项而非 dev 路径）。"""
    m = re.search(r'path="([^"]+)"', UGC_MOD_FILE.read_text(encoding="utf-8"))
    if not m:
        raise RuntimeError("ugc .mod has no path=")
    return Path(m.group(1))


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
    focus_ck3()
    pyautogui.click(*new_game)
    log("OCR-clicked 新游戏")

    robert = wait_for_ocr_text(
        "公爵罗贝尔", RULER_REGION, LOBBY_TIMEOUT_S,
        artifacts, "02_bookmark.png")
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
            "1200", EVENT_TEXT_REGION, 15, artifacts,
            "06_high_budget_1200.png", contains=True, stable_hits=1)
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
        reform = wait_for_ocr_text(
            "免费的宗教改革", EVENT_OPTIONS_FULL_REGION, 15,
            artifacts, "06_high_budget_reform.png", contains=True, stable_hits=1)
        offset = click_until_marker(
            reform, "faith reformation purchase", "XAR: faith reformation purchased",
            offset, xar_lines)
        wait_for_ocr_text(
            "67", EVENT_TEXT_REGION, 15, artifacts,
            "06_high_budget_67_remaining.png", contains=True, stable_hits=1)
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
    """Exercise a real AI death, then the player's native no-heir Game Over."""
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
            focus_ck3()
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
        "XAR: score event fired",
        "XAR: TEST no-heir score immediate entered",
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

    game_over = wait_for_ocr_text(
        "退出到菜单", FULL_SCREEN_REGION, 20,
        artifacts, "06_no_heir_native_game_over.png", contains=True,
        stable_hits=1)
    focus_ck3()
    game_over_img = ImageGrab.grab()
    if find_ocr_text(game_over_img, "继续扮演", FULL_SCREEN_REGION, contains=True):
        game_over_img.save(artifacts / "06_no_heir_unexpected_continue.png")
        raise RunnerError("native no-heir Game Over still offered Continue Playing")
    game_over_img.save(artifacts / "06_no_heir_game_over_verified.png")
    log(f"PASS: native no-heir Game Over at {game_over}")

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
    print("native Game Over: PASS")
    print("xar error.log   : 0")
    return xar_lines


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

    focus_ck3()
    # The landed-ruler Decisions icon is right-anchored. Verify its tooltip
    # before clicking so HUD layout drift cannot silently open a neighboring tab.
    screen_width, screen_height = pyautogui.size()
    decisions_tab = (int(screen_width * 0.987), int(screen_height * 0.367))
    pyautogui.moveTo(*decisions_tab, duration=0.2)
    wait_for_ocr_text(
        "决议", FULL_SCREEN_REGION, 10,
        artifacts, "06_decisions_tooltip.png", contains=True, stable_hits=1)
    pyautogui.click(*decisions_tab)
    log("clicked native Decisions HUD tab")
    pyautogui.moveTo(int(screen_width * 0.90), int(screen_height * 0.70))
    pyautogui.scroll(-6)
    time.sleep(0.5)
    ledger_decision = wait_for_ocr_text(
        "琉焰账簿", FULL_SCREEN_REGION, 15,
        artifacts, "06_ledger_decision.png", contains=True, stable_hits=1)
    pyautogui.moveTo(int(screen_width * 0.90), ledger_decision[1], duration=0.2)
    pyautogui.mouseDown()
    time.sleep(0.12)
    pyautogui.mouseUp()
    ledger_confirm = wait_for_ocr_text(
        "翻开账簿", FULL_SCREEN_REGION, 15,
        artifacts, "06_ledger_confirm.png", contains=True, stable_hits=1)
    offset = click_until_marker(
        ledger_confirm, "native ledger decision",
        "XAR: TEST PASS ui_ledger_open", offset, xar_lines)
    ledger_close = wait_for_ocr_text(
        "合上吧", EVENT_OPTIONS_FULL_REGION, 15,
        artifacts, "06_ledger_event.png", contains=True, stable_hits=1)
    offset = click_until_marker(
        ledger_close, "production ledger close",
        "XAR: TEST PASS ui_ledger_close", offset, xar_lines)

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


def mod_tree_hash():
    digest = hashlib.sha256()
    for path in build_release.release_files(MOD_ROOT):
        relative = path.relative_to(MOD_ROOT).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(path.read_bytes())
    return digest.hexdigest()


def write_json_report(artifacts, scenario, result, import_record, timings,
                      error_reason, run_id, started_at, evidence=None):
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
        "source_mode": "repository-synced-workshop-cache",
        "debug_mode": True,
        "game_version": "1.19.0.6",
        "environment": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
        },
        "artifacts": {"directory": str(artifacts), "files": files},
        "import_record": import_record,
        "phase_timings_seconds": timings,
        "error_reason": error_reason,
    }
    if evidence:
        report["persistence_restart"] = evidence
    (artifacts / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(scenario="selftest", import_record=0):
    run_started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    effective_record = {
        "selftest": import_record,
        "on-first-life": 0,
        "on-recorded": 100,
        "on-high-budget": 1200,
        "off": 0,
        "persistence-restart": 0,
        "death-edges": 1,
    }[scenario]
    rule_setting = "xar_selftest" if scenario in (
        "selftest", "persistence-restart", "death-edges") else (
        "xar_off" if scenario == "off" else "xar_on")
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
    session_artifacts = artifacts
    if scenario == "persistence-restart":
        session_artifacts = artifacts / "writer"
        session_artifacts.mkdir()

    try:
        with timed_phase(timings, "setup_backup"):
            if _ocr is None:
                raise RunnerError("RapidOCR missing; install tools/requirements.txt")
            shutil.copy2(TUTORIAL_TXT, backup / "tutorial.txt")
            shutil.copy2(PRESETS_TXT, backup / "presets.txt")
            backup_ready = True
            log("backed up tutorial.txt + presets.txt")
            start_restore_watchdog(backup, ck3_pid_file)
            log("restore watchdog armed")

        with timed_phase(timings, "static_validation"):
            if validate_static.main() != 0:
                raise RunnerError("static validation failed")
            descriptor = (MOD_ROOT / "descriptor.mod").read_text(encoding="utf-8-sig")
            if "remote_file_id" in descriptor:
                raise RunnerError("repository descriptor.mod contains remote_file_id")
            log("static validation passed")

        with timed_phase(timings, "sync_and_configure"):
            runtime_source = MOD_ROOT
            if scenario in ("on-first-life", "on-recorded", "on-high-budget", "off"):
                runtime_source = artifacts / "release_projection"
                build_release.build_release(
                    MOD_ROOT, runtime_source, revision=build_release.git_sha())
                log("built stripped release projection for production smoke")
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
                if scenario not in ("selftest", "persistence-restart", "death-edges"):
                    print("RESULT: GREEN")
                elif scenario == "persistence-restart":
                    print("\n===== XAR PERSISTENCE RESTART REPORT =====")
                    print(f"writer record   : {report_evidence['writer_record']}")
                    print(f"handoff SHA-256 : {report_evidence['tutorial_handoff_sha256']}")
                    print("process B seeded: no")
                    print("RESULT: GREEN")
                elif scenario == "death-edges":
                    print("RESULT: GREEN")
            elif scenario not in ("selftest", "persistence-restart", "death-edges"):
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
                    restore_succeeded = True
                    log("restored tutorial.txt + presets.txt, ck3 killed")
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
        write_json_report(
            artifacts, scenario, result, effective_record, timings, error_reason,
            run_id, started_at, report_evidence)
        log(f"JSON report: {artifacts / 'report.json'}")
    return 0 if result == "GREEN" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run CK3 automated acceptance")
    parser.add_argument(
        "--scenario",
        choices=("selftest", "on-first-life", "on-recorded", "on-high-budget", "off",
                 "persistence-restart", "death-edges"),
        default="selftest",
        help="acceptance scenario (default: selftest)")
    parser.add_argument(
        "--import-record", type=int, choices=(0, 100), default=0,
        help="selftest tutorial record; production scenarios use fixed baselines")
    args = parser.parse_args()
    if args.scenario == "persistence-restart" and args.import_record != 0:
        parser.error("persistence-restart forbids --import-record pre-seeding")
    sys.exit(main(args.scenario, args.import_record))

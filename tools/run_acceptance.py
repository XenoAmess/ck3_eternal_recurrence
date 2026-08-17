# 全自动验收 runner：备份现场 -> 剥纪录位 + 规则切自检 -> 启动游戏过大厅 -> 日志判定 -> 恢复现场
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
import win32con
import win32gui
from PIL import ImageGrab

import validate_loc

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
    "draw_bless_distinct", "bless_apply", "draw_curse_distinct",
    "curse_apply_ran", "import_var", "import_value", "score_positive",
    "bless_count", "record_write",
}

CLICK_SETTLE_OK = (1130, 1041)      # 结算事件确认选项「很好。这笔账，已记入永恒。」

# 区域均为相对屏幕比例；OCR 只扫目标区域，比全屏 OCR 快且不受分辨率影响。
MAIN_MENU_REGION = (0.18, 0.28, 0.30, 0.50)
RULER_REGION = (0.45, 0.68, 0.72, 0.91)
START_REGION = (0.82, 0.82, 0.95, 0.93)
RULER_DETAIL_REGION = (0.76, 0.28, 0.98, 0.58)
OPTION_LIST_REGION = (0.20, 0.58, 0.56, 0.83)
EVENT_TITLE_REGION = (0.20, 0.17, 0.50, 0.29)

BOOT_TIMEOUT_S = 120             # OCR 一发现主菜单即继续，不固定睡 100 秒
LOBBY_TIMEOUT_S = 30
TEST_TIMEOUT_S = 300             # 开局后等待 TEST DONE 的超时
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


def sync_repo_to_ugc(target):
    """robocopy /MIR 仓库 mod -> 工坊缓存（用户已批准；工坊更新时 Steam 会重下复原）。"""
    r = subprocess.run(
        ["robocopy", str(MOD_ROOT), str(target), "/MIR", "/NFL", "/NDL", "/NJH", "/NJS", "/NP"],
        capture_output=True)
    if r.returncode >= 8:
        raise RuntimeError(f"robocopy failed rc={r.returncode}")
    log(f"synced repo -> {target} (robocopy rc={r.returncode})")


def kill_ck3():
    subprocess.run(["taskkill", "/F", "/IM", "ck3.exe"],
                   capture_output=True)


def kill_process(pid):
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                   capture_output=True)


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


def set_last_applied_rule(raw):
    """只把 LastAppliedRules 的本 mod 规则切到 selftest。"""
    pattern = re.compile(
        rb'(name="LastAppliedRules"\s+setting=\{)(.*?)(\}\s+ironman=)',
        re.DOTALL)
    match = pattern.search(raw)
    if not match:
        raise RunnerError("LastAppliedRules block not found in presets.txt")
    body = re.sub(rb'\bxar_(?:on|off|selftest)\b', b'', match.group(2))
    body = body.rstrip() + b' xar_selftest '
    patched = raw[:match.start()] + match.group(1) + body + match.group(3) + raw[match.end():]

    verify = pattern.search(patched)
    if not verify or verify.group(2).count(b'xar_selftest') != 1:
        raise RunnerError("failed to set LastAppliedRules to xar_selftest")
    return patched


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


def wait_for_localized_options(label, artifacts, timeout_s=20):
    """等待前三个事件选项，拒绝 raw key、静态占位和重复文本。"""
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
        if len(texts) >= 3:
            option_texts = [re.sub(r"\s+", "", text).lower() for text in texts[:3]]
            if len(set(option_texts)) != 3:
                last_img.save(artifacts / f"06_{label}_options_repeated.png")
                raise RunnerError(
                    f"{label} first three options are not distinct: {texts[:3]}")
            last_img.save(artifacts / f"06_{label}_options.png")
            last_img.crop(region_bbox(last_img, OPTION_LIST_REGION)).save(
                artifacts / f"06_{label}_options_crop.png")
            log(f"PASS: {label} options localized and distinct; OCR={texts[:3]}")
            return results[0][2]
        time.sleep(POLL_INTERVAL_S)
    if last_img is not None:
        last_img.save(artifacts / f"timeout_{label}_options.png")
    raise RunnerError(
        f"{label} option OCR saw fewer than 3 rows; last OCR={last_text}")


def main():
    artifacts = Path(tempfile.mkdtemp(prefix="xar_accept_"))
    log(f"artifacts dir: {artifacts}")

    if _ocr is None:
        print("RESULT: RED (RapidOCR missing; install tools/requirements.txt)")
        sys.exit(1)

    # ---- 备份现场 ----
    backup = artifacts / "backup"
    backup.mkdir()
    shutil.copy2(TUTORIAL_TXT, backup / "tutorial.txt")
    shutil.copy2(PRESETS_TXT, backup / "presets.txt")
    log("backed up tutorial.txt + presets.txt")
    ck3_pid_file = artifacts / "ck3.pid"
    start_restore_watchdog(backup, ck3_pid_file)
    log("restore watchdog armed")

    exit_code = 1

    # ---- 静态 loc 校验（失败直接 RED，不进游戏）----
    if validate_loc.main() != 0:
        print("RESULT: RED (loc validation failed)")
        sys.exit(1)
    log("loc validation passed")

    descriptor = (MOD_ROOT / "descriptor.mod").read_text(encoding="utf-8-sig")
    if "remote_file_id" in descriptor:
        print("RESULT: RED (repository descriptor.mod contains remote_file_id)")
        sys.exit(1)

    try:
        # ---- 同步仓库 -> 工坊缓存（游戏实际加载 ugc 项，必须先同步）----
        sync_repo_to_ugc(ugc_content_dir())

        # ---- 剥纪录位（基线 0，供 T1 断言 import_value=0）----
        raw = TUTORIAL_TXT.read_bytes()
        lines = raw.split(b"\n")
        stripped = [l for l in lines if not re.match(rb"^\s*xar_", l)]
        removed = len(lines) - len(stripped)
        TUTORIAL_TXT.write_bytes(b"\n".join(stripped))
        log(f"tutorial.txt: removed {removed} xar bit line(s)")

        # CK3 在前端初始化期间读取 LastAppliedRules，必须在启动前写入。
        patched = set_last_applied_rule((backup / "presets.txt").read_bytes())
        PRESETS_TXT.write_bytes(patched)
        if PRESETS_TXT.read_bytes().count(b"xar_selftest") != 1:
            raise RunnerError("presets.txt selftest rule verification failed")
        log("LastAppliedRules set to xar_selftest before launch and verified")

        # ---- 启动游戏 ----
        # 只评估本次运行产生的日志（error.log/debug.log 都是累积的）
        error_offset = ERROR_LOG.stat().st_size if ERROR_LOG.exists() else 0
        debug_offset = DEBUG_LOG.stat().st_size if DEBUG_LOG.exists() else 0
        kill_ck3()
        time.sleep(3)
        ck3_process = subprocess.Popen(
            [str(CK3_EXE), "-debug_mode"], cwd=str(CK3_EXE.parent))
        ck3_pid_file.write_text(str(ck3_process.pid), encoding="ascii")
        log("launched ck3; OCR waiting for main menu")

        # ---- OCR 驱动大厅，不再按固定秒数/坐标盲点 ----
        new_game = wait_for_ocr_text(
            "新游戏", MAIN_MENU_REGION, BOOT_TIMEOUT_S,
            artifacts, "01_main_menu.png")

        focus_ck3()
        pyautogui.click(*new_game)
        log("OCR-clicked 新游戏")

        robert = wait_for_ocr_text(
            "公爵罗贝尔", RULER_REGION, LOBBY_TIMEOUT_S,
            artifacts, "02_bookmark.png")

        # 地图文字标签不是角色选择热区；依次尝试卡片内候选点，每次都由右栏反证。
        screen_width, screen_height = pyautogui.size()
        ruler_candidates = [
            robert,  # 蓝色姓名牌正文是推荐角色的主点击热区
            (robert[0] - int(screen_width * 0.041),
             robert[1] - int(screen_height * 0.057)),  # 实测可选中的卡片左上区域
            (robert[0], robert[1] - int(screen_height * 0.09)),
        ]
        selected = False
        for index, candidate in enumerate(ruler_candidates, 1):
            focus_ck3()
            pyautogui.moveTo(*candidate, duration=0.2)
            time.sleep(0.3)  # 等原版 bookmark_character hover 位移动画结束
            pyautogui.mouseDown()
            time.sleep(0.12)
            pyautogui.mouseUp()
            log(f"clicked Robert candidate {index} at {candidate}")
            # 移开鼠标，排除仅由 hover 产生的右栏预览。
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
        click_until_text_disappears(
            start, "开始", START_REGION, artifacts)

        # 确认离开书签页后，规则已进入新局参数，立即恢复用户预设。
        shutil.copy2(backup / "presets.txt", PRESETS_TXT)
        log("restored presets.txt after OCR-confirmed start transition")

        # ---- 等开局（selftest begin 标记出现 = 已进局且已自杀链启动）----
        offset = debug_offset
        xar_lines = []
        offset = wait_for_marker(
            offset, "XAR: TEST selftest begin", 180, xar_lines)

        # ---- UI 本地化验收（祝福 + 诅咒各真实打开一次）----
        offset = wait_for_marker(
            offset, "XAR: UI bless window opened", 30, xar_lines)
        wait_for_ocr_text(
            "琉焰的垂青", EVENT_TITLE_REGION, 15,
            artifacts, "05_bless_window.png", stable_hits=1)
        bless_option = wait_for_localized_options("bless", artifacts)
        deliberate_click(bless_option, "localized bless option")
        offset = wait_for_marker(
            offset, "XAR: UI bless accepted", 10, xar_lines)

        offset = wait_for_marker(
            offset, "XAR: UI curse window opened", 30, xar_lines)
        wait_for_ocr_text(
            "等价的咒痕", EVENT_TITLE_REGION, 15,
            artifacts, "05_curse_window.png", stable_hits=1)
        curse_option = wait_for_localized_options("curse", artifacts)
        deliberate_click(curse_option, "localized curse option")
        offset = wait_for_marker(
            offset, "XAR: UI curse accepted", 10, xar_lines)
        ui_ok = True

        # 开局默认暂停；关闭诅咒窗口后按底栏比例点击播放，让延迟自测链继续。
        focus_ck3()
        click_ratio(2315 / 2560, 1410 / 1440)
        log("unpaused after UI localization test")

        # ---- 轮询判定（含时间冻结自愈）----
        # 冻结检测：跟踪 debug.log 里 AI 日志行自带的局内日期（如 "1066.9.16:"）。
        # 日期 8s 不涨时 OCR 寻找继承窗口；识别到才点击，杜绝盲点 UI。
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
                m = date_re.search(line)
                if m:
                    d = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    if max_date is None or d > max_date:
                        max_date = d
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

        # ---- 顺路点结算确认（触发观察者桥，留截图证据）----
        if done:
            focus_ck3()
            click_ratio(CLICK_SETTLE_OK[0] / 2560, CLICK_SETTLE_OK[1] / 1440)
            time.sleep(2)
            focus_ck3()
            ImageGrab.grab().save(artifacts / "05_after_confirm.png")
            log("clicked settlement confirm, saved 05_after_confirm.png")

        # ---- 教程落盘断言（纪录位的真实持久化，runner 侧在恢复前查）----
        persist_ok = False
        if done:
            try:
                live = TUTORIAL_TXT.read_text(encoding="utf-8", errors="ignore")
                m = re.findall(r"(?m)^\s*(xar_hs_ge_\d+)\s*$", live)
                persist_ok = bool(m)
                log(f"tutorial.txt bits after run: {m if m else 'NONE'}")
            except OSError:
                pass

        # ---- error.log 扫 xar 错误 ----
        err_text, _ = read_new_lines(ERROR_LOG, error_offset)
        xar_errors = [l.strip() for l in err_text.splitlines() if "xar" in l.lower()]

        # ---- 汇总 ----
        passes = [l for l in xar_lines if "XAR: TEST PASS" in l]
        fails = [l for l in xar_lines if "XAR: TEST FAIL" in l]
        observed_passes = {
            l.split("XAR: TEST PASS ", 1)[1].strip()
            for l in passes if "XAR: TEST PASS " in l
        }
        missing_passes = sorted(REQUIRED_PASSES - observed_passes)
        sweep_ok = any("XAR: TEST sweep complete" in l for l in xar_lines)
        print("\n===== XAR ACCEPTANCE REPORT =====")
        for l in xar_lines:
            print("  " + l)
        print("---------------------------------")
        print(f"TEST DONE seen : {done}")
        print(f"UI loc check   : {'PASS' if ui_ok else 'FAIL'}")
        print(f"PASS count     : {len(passes)}")
        print(f"required PASS  : {'PASS' if not missing_passes else 'MISSING ' + ', '.join(missing_passes)}")
        print(f"pool sweep     : {'PASS' if sweep_ok else 'FAIL'}")
        print(f"FAIL count     : {len(fails)}")
        print(f"tutorial persist: {'PASS' if persist_ok else 'FAIL (or not done)'}")
        print(f"xar error.log  : {len(xar_errors)}")
        for l in xar_errors:
            print("  ERR " + l)
        print(f"artifacts      : {artifacts}")
        if (done and ui_ok and not fails and not missing_passes and sweep_ok
                and not xar_errors and persist_ok):
            print("RESULT: GREEN")
            exit_code = 0
        else:
            print("RESULT: RED")
    except Exception as e:
        log(f"FATAL: {e}")
        if not isinstance(e, RunnerError):
            traceback.print_exc()
        try:
            focus_ck3()
            ImageGrab.grab().save(artifacts / "fatal_state.png")
        except Exception:
            pass
        print(f"artifacts: {artifacts}")
        print("RESULT: RED")
    finally:
        # ---- 恢复现场 ----
        if ck3_pid_file.exists():
            try:
                kill_process(int(ck3_pid_file.read_text(encoding="ascii")))
            except (OSError, ValueError):
                pass
            ck3_pid_file.unlink(missing_ok=True)
        time.sleep(2)
        shutil.copy2(backup / "tutorial.txt", TUTORIAL_TXT)
        shutil.copy2(backup / "presets.txt", PRESETS_TXT)
        log("restored tutorial.txt + presets.txt, ck3 killed")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

# 全自动验收 runner：备份现场 -> 剥纪录位 + 规则切自检 -> 启动游戏过大厅 -> 日志判定 -> 恢复现场
#
# 前置事实（2026-08-17 实证）：游戏加载的是 Steam 工坊缓存（ugc_3784706360，
# 播放集启用的是工坊项而非 dev 路径，因 dev .mod 带了 remote_file_id 被启动器合并）。
# 因此 runner 每次先把仓库 mod robocopy /MIR 同步进工坊缓存目录再启动（用户已批准，
# 不恢复缓存；下次工坊更新时 Steam 重下即复原）。
#
# 用法（必须用 tools/.venv 的 python，依赖 pyautogui/pywin32/Pillow）：
#   & "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" tools\run_acceptance.py
#
# 坐标为 2560x1440 全屏校准值（书签屏 1066 公爵罗贝尔）。判定依据：
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
from pathlib import Path

import pyautogui
import win32con
import win32gui
from PIL import ImageGrab

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

# 2560x1440 校准坐标（截图真实像素）
CLICK_NEW_GAME = (600, 560)      # 主菜单「新游戏」
CLICK_RULER = (1600, 1230)       # 书签屏 1066「公爵罗贝尔」卡片（有儿子博希蒙德，必有继承人）
CLICK_START = (2257, 1245)       # 右侧栏「开始」
CLICK_CONTINUE_HEIR = (1455, 1130)  # 死亡继承窗口「继续扮演<继承人>」（缺席时点到海面，无副作用）
CLICK_PLAY = (2315, 1410)           # 底栏日期旁的 ▶ 播放按钮（合成键盘事件进不了游戏，只能用鼠标点）
CLICK_SETTLE_OK = (1130, 1041)      # 结算事件确认选项「很好。这笔账，已记入永恒。」
DATE_BBOX = (2055, 1398, 2290, 1435)  # 仅日期文字区：像素不变化 = 时间冻结（事件窗弹出会重新暂停）

BOOT_WAIT_S = 100                # 启动到主菜单固定等待
TEST_TIMEOUT_S = 300             # 开局后等待 TEST DONE 的超时
POLL_INTERVAL_S = 5


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


def main():
    artifacts = Path(tempfile.mkdtemp(prefix="xar_accept_"))
    log(f"artifacts dir: {artifacts}")

    # ---- 备份现场 ----
    backup = artifacts / "backup"
    backup.mkdir()
    shutil.copy2(TUTORIAL_TXT, backup / "tutorial.txt")
    shutil.copy2(PRESETS_TXT, backup / "presets.txt")
    log("backed up tutorial.txt + presets.txt")

    exit_code = 1
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

        # ---- 规则切自检（只改字节级 xar_on -> xar_selftest，事后整文件恢复）----
        raw = PRESETS_TXT.read_bytes()
        n = raw.count(b"xar_on")
        PRESETS_TXT.write_bytes(raw.replace(b"xar_on", b"xar_selftest"))
        log(f"presets.txt: replaced {n} xar_on occurrence(s)")

        # ---- 启动游戏 ----
        kill_ck3()
        time.sleep(3)
        subprocess.Popen([str(CK3_EXE), "-debug_mode"], cwd=str(CK3_EXE.parent))
        log(f"launched ck3, waiting {BOOT_WAIT_S}s for main menu")
        time.sleep(BOOT_WAIT_S)

        # ---- 过大厅 ----
        focus_ck3()
        time.sleep(2)
        ImageGrab.grab().save(artifacts / "01_main_menu.png")
        pyautogui.click(*CLICK_NEW_GAME)
        log("clicked 新游戏")
        time.sleep(8)
        ImageGrab.grab().save(artifacts / "02_bookmark.png")
        focus_ck3()
        pyautogui.click(*CLICK_RULER)
        log("clicked 罗贝尔 card")
        time.sleep(3)
        ImageGrab.grab().save(artifacts / "03_ruler_selected.png")
        focus_ck3()
        pyautogui.click(*CLICK_START)
        log("clicked 开始, game loading")

        # ---- 等开局（selftest begin 标记出现 = 已进局且已自杀链启动）----
        offset = 0
        xar_lines = []
        begun = False
        deadline = time.time() + 180
        while time.time() < deadline and not begun:
            text, offset = read_new_lines(DEBUG_LOG, offset)
            for line in text.splitlines():
                if "XAR:" in line:
                    xar_lines.append(line.strip())
                    if "XAR: TEST selftest begin" in line:
                        begun = True
            if not begun:
                time.sleep(POLL_INTERVAL_S)
        if not begun:
            ImageGrab.grab().save(artifacts / "04_no_begin.png")
            log("FATAL: selftest begin marker never appeared")

        # ---- 继承窗口 + 解暂停 ----
        # 死亡在开局数秒内发生（此时还暂停着），继承窗口弹出并强制暂停。
        # 实证：先点「继续扮演」解散窗口，再点底栏 ▶ 解暂停，顺序不能反。
        # （pyautogui 的键盘事件送不进 CK3——ESC/space 实测无效，鼠标点击有效。）
        if begun:
            time.sleep(5)
            focus_ck3()
            time.sleep(1)
            pyautogui.click(*CLICK_CONTINUE_HEIR)
            log("clicked 继续扮演 (succession window)")
            time.sleep(2)
            focus_ck3()
            pyautogui.click(*CLICK_PLAY)
            log("unpaused (play button)")

        # ---- 轮询判定（含时间冻结自愈）----
        # 冻结检测：跟踪 debug.log 里 AI 日志行自带的局内日期（如 "1066.9.16:"）。
        # 日期 12s 不涨 = 被重新暂停 -> 再点 ▶。（像素方案弃用：底栏区域有动画噪声。）
        done = False
        deadline = time.time() + TEST_TIMEOUT_S
        date_re = re.compile(r"\b(\d{3,4})\.(\d{1,2})\.(\d{1,2})\b")
        max_date = None
        last_day_change = time.time()
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
            if time.time() - last_day_change > 12:
                focus_ck3()
                pyautogui.click(*CLICK_CONTINUE_HEIR)  # 死亡时点不定（等导入），继承窗靠这里补点
                time.sleep(1)
                pyautogui.click(*CLICK_PLAY)
                log(f"in-game date frozen at {max_date} -> continue-heir + play")
                last_day_change = time.time()
            time.sleep(POLL_INTERVAL_S)

        focus_ck3()
        ImageGrab.grab().save(artifacts / "04_end_state.png")

        # ---- 顺路点结算确认（触发观察者桥，留截图证据）----
        if done:
            time.sleep(2)
            focus_ck3()
            pyautogui.click(*CLICK_SETTLE_OK)
            time.sleep(8)
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
        err_text, _ = read_new_lines(ERROR_LOG, 0)
        xar_errors = []
        for l in err_text.splitlines():
            if "xar" not in l.lower():
                continue
            # 已知良性噪音：事件选项名引用的 custom loc 在加载期校验时不认识
            # （customizable_localization 注册晚于事件校验；运行期渲染正常解析）。
            if re.search(r"Unrecognized loc key xar_(bless|curse)_slot_[abc]", l):
                continue
            xar_errors.append(l.strip())

        # ---- 汇总 ----
        passes = [l for l in xar_lines if "XAR: TEST PASS" in l]
        fails = [l for l in xar_lines if "XAR: TEST FAIL" in l]
        print("\n===== XAR ACCEPTANCE REPORT =====")
        for l in xar_lines:
            print("  " + l)
        print("---------------------------------")
        print(f"TEST DONE seen : {done}")
        print(f"PASS count     : {len(passes)}")
        print(f"FAIL count     : {len(fails)}")
        print(f"tutorial persist: {'PASS' if persist_ok else 'FAIL (or not done)'}")
        print(f"xar error.log  : {len(xar_errors)}")
        for l in xar_errors:
            print("  ERR " + l)
        print(f"artifacts      : {artifacts}")
        if done and not fails and passes and not xar_errors and persist_ok:
            print("RESULT: GREEN")
            exit_code = 0
        else:
            print("RESULT: RED")
    finally:
        # ---- 恢复现场 ----
        kill_ck3()
        time.sleep(2)
        shutil.copy2(backup / "tutorial.txt", TUTORIAL_TXT)
        shutil.copy2(backup / "presets.txt", PRESETS_TXT)
        log("restored tutorial.txt + presets.txt, ck3 killed")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

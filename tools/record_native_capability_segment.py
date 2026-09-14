from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any, Iterable


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SEGMENT_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
ENVIRONMENT_NAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
CAPTURE_WIDTH = 2560
CAPTURE_HEIGHT = 1440
CAPTURE_FRAME_RATE = 30


class RecordingError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProcessRow:
    pid: int
    executable: str


@dataclass(frozen=True)
class RecordingPaths:
    raw_video: Path
    final_video: Path
    artifact: Path
    stdout: Path
    stderr: Path
    sidecar: Path


def file_identity(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": digest.hexdigest().upper(),
    }


def write_new(path: Path, text: str) -> None:
    with path.open("x", encoding="utf-8", newline="") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())


def process_rows() -> list[ProcessRow]:
    if os.name != "nt":
        return []
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class ProcessEntry(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", wintypes.LONG),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    rows: list[ProcessRow] = []
    try:
        entry = ProcessEntry()
        entry.dwSize = ctypes.sizeof(ProcessEntry)
        available = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while available:
            rows.append(ProcessRow(int(entry.th32ProcessID), entry.szExeFile))
            available = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    return rows


def pids_named(executable: str) -> list[int]:
    return [row.pid for row in process_rows() if row.executable.casefold() == executable.casefold()]


def visible_windows_for_pids(pids: Iterable[int]) -> dict[int, int]:
    if os.name != "nt":
        return {}
    wanted = set(pids)
    found: dict[int, int] = {}
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]

    @callback_type
    def visit(hwnd: int, _: int) -> bool:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if int(pid.value) in wanted and user32.IsWindowVisible(hwnd):
            found.setdefault(int(pid.value), int(hwnd))
        return True

    if not user32.EnumWindows(visit, 0):
        raise ctypes.WinError(ctypes.get_last_error())
    return found


def show_window(hwnd: int, command: int) -> None:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow(wintypes.HWND(hwnd), command)


def bring_forward(hwnd: int) -> None:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SetWindowPos.argtypes = [
        wintypes.HWND,
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    ]
    user32.BringWindowToTop.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    show_window(hwnd, 9)
    user32.SetWindowPos(wintypes.HWND(hwnd), None, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
    user32.BringWindowToTop(wintypes.HWND(hwnd))
    user32.SetForegroundWindow(wintypes.HWND(hwnd))


def wait_for_ck3_cleanup(timeout_seconds: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    streak = 0
    remaining: list[int] = []
    while time.monotonic() < deadline:
        remaining = pids_named("ck3.exe")
        if remaining:
            streak = 0
        else:
            streak += 1
            if streak >= 8:
                return {"ok": True, "stable_absence_samples": streak, "remaining_pids": []}
        time.sleep(0.25)
    return {"ok": False, "stable_absence_samples": streak, "remaining_pids": remaining}


class Overlay:
    def __init__(self) -> None:
        try:
            import tkinter as tk
        except ImportError as error:
            raise RecordingError("Python tkinter is required for native recording overlays") from error
        self.tk = tk
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.configure(bg="#0c101c")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry(f"{CAPTURE_WIDTH}x{CAPTURE_HEIGHT}+0+0")
        self.eyebrow = self._label(self.root, "XAR / CK3 EXACT-BUILD NATIVE CAPABILITY", 22, "#daaa4a", "Segoe UI Semibold")
        self.badge = self._label(self.root, "", 18, "#ffffff", "Segoe UI Semibold", "#263044")
        self.title = self._label(self.root, "", 46, "#ffffff", "Segoe UI", bold=True)
        self.chinese_title = self._label(self.root, "", 27, "#cad2e0", "Microsoft YaHei UI")
        self.subtitle = self._label(self.root, "", 27, "#9cc9ff", "Segoe UI Semibold")
        self.body = self._label(self.root, "", 21, "#dee4ef", "Consolas", justify="left")
        self.chinese_body = self._label(self.root, "", 21, "#bccce5", "Microsoft YaHei UI", justify="left")
        self.boundary = self._label(self.root, "", 18, "#daaa4a", "Segoe UI Semibold", justify="left")
        self.footer = self._label(self.root, "English primary narration / Simplified Chinese subtitles  |  英语主叙事 / 简体中文字幕", 17, "#8490a6", "Segoe UI")
        self.eyebrow.place(x=176, y=112, width=1500, height=52)
        self.badge.place(x=1770, y=105, width=610, height=60)
        self.title.place(x=170, y=225, width=2220, height=110)
        self.chinese_title.place(x=178, y=342, width=2204, height=64)
        self.subtitle.place(x=178, y=438, width=2204, height=62)
        self.body.place(x=182, y=560, width=1040, height=430)
        self.chinese_body.place(x=1330, y=560, width=1040, height=430)
        self.boundary.place(x=182, y=1040, width=2196, height=120)
        self.footer.place(x=182, y=1295, width=2196, height=52)
        self.lower = tk.Toplevel(self.root)
        self.lower.withdraw()
        self.lower.configure(bg="#0c101c")
        self.lower.overrideredirect(True)
        self.lower.attributes("-topmost", True)
        self.lower.attributes("-alpha", 0.90)
        self.lower.geometry("2120x190+220+1190")
        self.lower_badge = self._label(self.lower, "", 15, "#ffffff", "Segoe UI Semibold", "#374b69")
        self.lower_english = self._label(self.lower, "", 23, "#ffffff", "Segoe UI Semibold", justify="left")
        self.lower_chinese = self._label(self.lower, "", 20, "#9cc9ff", "Microsoft YaHei UI")
        self.lower_boundary = self._label(self.lower, "", 13, "#daaa4a", "Segoe UI")
        self.lower_badge.place(x=24, y=18, width=410, height=48)
        self.lower_english.place(x=465, y=10, width=1625, height=62)
        self.lower_chinese.place(x=28, y=78, width=2064, height=50)
        self.lower_boundary.place(x=28, y=136, width=2064, height=38)

    def _label(self, parent: Any, text: str, size: int, foreground: str, family: str, background: str = "#0c101c", bold: bool = False, justify: str = "center") -> Any:
        weight = "bold" if bold else "normal"
        anchor = "w" if justify == "left" else "center"
        return self.tk.Label(parent, text=text, font=(family, size, weight), fg=foreground, bg=background, anchor=anchor, justify=justify, wraplength=2100)

    def pump(self, milliseconds: int = 0) -> None:
        deadline = time.monotonic() + milliseconds / 1000
        while True:
            self.root.update_idletasks()
            self.root.update()
            if time.monotonic() >= deadline:
                break
            time.sleep(0.04)

    def show_card(self, *, title: str, chinese_title: str, subtitle: str, body: str, chinese_body: str, badge: str, boundary: str, accent: str) -> None:
        self.title.configure(text=title)
        self.chinese_title.configure(text=chinese_title)
        self.subtitle.configure(text=subtitle)
        self.body.configure(text=body)
        self.chinese_body.configure(text=chinese_body)
        self.badge.configure(text=badge)
        self.boundary.configure(text=boundary)
        self.root.configure(highlightbackground=accent, highlightthickness=12)
        self.lower.withdraw()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.pump()

    def show_lower(self, *, badge: str, english: str, chinese: str, boundary: str) -> None:
        self.root.withdraw()
        self.lower_badge.configure(text=badge)
        self.lower_english.configure(text=english)
        self.lower_chinese.configure(text=chinese)
        self.lower_boundary.configure(text=boundary)
        self.lower.deiconify()
        self.lower.lift()
        self.pump()

    def close(self) -> None:
        try:
            self.lower.destroy()
            self.root.destroy()
        except self.tk.TclError:
            pass


def parse_environment(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        name, separator, content = value.partition("=")
        if not separator or not ENVIRONMENT_NAME_PATTERN.fullmatch(name):
            raise RecordingError(f"invalid child environment assignment: {value}")
        if "\0" in content:
            raise RecordingError(f"child environment variable {name} contains a NUL character")
        result[name] = content
    return result


def resolve_runner(value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or any(separator in value for separator in ("/", "\\")):
        candidate = (candidate if candidate.is_absolute() else REPOSITORY_ROOT / candidate).resolve()
        if not candidate.is_file():
            raise RecordingError(f"runner executable is missing: {candidate}")
        return candidate
    found = shutil.which(value)
    if not found:
        raise RecordingError(f"runner executable is unavailable: {value}")
    return Path(found).resolve()


def validate_runner_arguments(values: list[str]) -> None:
    for value in values:
        if "\0" in value:
            raise RecordingError("runner arguments cannot contain NUL characters")
        if value.casefold() == "--output" or value.casefold().startswith("--output="):
            raise RecordingError("runner arguments must not contain --output; this recorder injects a unique artifact path")


def build_paths(output: Path, segment_id: str, stamp: str) -> RecordingPaths:
    stem = f"ck3-native-{segment_id.casefold()}-{stamp}"
    return RecordingPaths(
        output / f"{stem}.raw.mkv",
        output / f"{stem}.mp4",
        output / f"{stem}.live.json",
        output / f"{stem}.stdout.txt",
        output / f"{stem}.stderr.txt",
        output / f"{stem}.video.json",
    )


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Record one bounded native CK3 capability segment")
    value.add_argument("--segment-id", required=True)
    value.add_argument("--english-title", required=True)
    value.add_argument("--chinese-title", required=True)
    value.add_argument("--status-badge", required=True)
    value.add_argument("--boundary-text", required=True)
    value.add_argument("--runner", required=True)
    value.add_argument("--runner-argument", action="append", default=[])
    value.add_argument("--environment", action="append", default=[])
    value.add_argument("--output-directory", type=Path, required=True)
    value.add_argument("--title-seconds", type=float, default=5)
    value.add_argument("--result-seconds", type=float, default=10)
    value.add_argument("--plan-only", action="store_true")
    return value


def recording_plan(args: argparse.Namespace) -> dict[str, Any]:
    if not SEGMENT_ID_PATTERN.fullmatch(args.segment_id):
        raise RecordingError("segment ID must match [A-Za-z0-9][A-Za-z0-9._-]{0,63}")
    if not all((args.english_title, args.chinese_title, args.status_badge, args.boundary_text)):
        raise RecordingError("titles, status badge, and boundary text must be non-empty")
    if args.title_seconds < 0 or args.result_seconds < 0:
        raise RecordingError("card durations cannot be negative")
    validate_runner_arguments(args.runner_argument)
    runner = resolve_runner(args.runner)
    environment = parse_environment(args.environment)
    output = args.output_directory.resolve()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:19]
    paths = build_paths(output, args.segment_id, stamp)
    return {
        "format_version": 1,
        "kind": "ck3_native_capability_segment_recording_plan",
        "segment_id": args.segment_id,
        "runner": str(runner),
        "runner_arguments": list(args.runner_argument),
        "environment_keys": sorted(environment),
        "output_directory": str(output),
        "paths": {name: str(path) for name, path in paths.__dict__.items()},
        "capture": {"width": CAPTURE_WIDTH, "height": CAPTURE_HEIGHT, "frame_rate": CAPTURE_FRAME_RATE, "encoder": "h264_nvenc"},
        "_environment": environment,
        "_path_objects": paths,
    }


def public_plan(plan: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in plan.items() if not key.startswith("_")}


def run(args: argparse.Namespace, plan: dict[str, Any]) -> dict[str, Any]:
    if os.name != "nt":
        raise RecordingError("native capability recording requires Windows")
    paths: RecordingPaths = plan["_path_objects"]
    for path in paths.__dict__.values():
        if path.exists():
            raise RecordingError(f"refusing to overwrite existing recording output: {path}")
    paths.raw_video.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_text = shutil.which("ffmpeg")
    ffprobe_text = shutil.which("ffprobe")
    if not ffmpeg_text or not ffprobe_text:
        raise RecordingError("ffmpeg and ffprobe are required")
    ffmpeg = Path(ffmpeg_text)
    ffprobe = Path(ffprobe_text)
    encoders = subprocess.run([str(ffmpeg), "-hide_banner", "-encoders"], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    if encoders.returncode or not re.search(r"(?m)^\s*V\S*\s+h264_nvenc\s", encoders.stdout + encoders.stderr):
        raise RecordingError("FFmpeg does not advertise the required h264_nvenc encoder")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    if user32.GetSystemMetrics(0) != CAPTURE_WIDTH or user32.GetSystemMetrics(1) != CAPTURE_HEIGHT:
        raise RecordingError(f"primary display must be exactly {CAPTURE_WIDTH}x{CAPTURE_HEIGHT}")
    if pids_named("ck3.exe"):
        raise RecordingError("refusing to record while ck3.exe is already running")
    obs_windows = visible_windows_for_pids(pids_named("obs64.exe"))
    for hwnd in obs_windows.values():
        show_window(hwnd, 6)
    overlay = Overlay()
    capture: subprocess.Popen[str] | None = None
    runner: subprocess.Popen[str] | None = None
    stdout_stream = None
    stderr_stream = None
    runner_exit: int | None = None
    artifact: dict[str, Any] | None = None
    artifact_identity: dict[str, Any] | None = None
    cleanup: dict[str, Any] | None = None
    observed_pids: list[int] = []
    seen_window_pids: set[int] = set()
    foreground_attempts = 0
    qualified = False
    failure: str | None = None
    try:
        overlay.show_card(
            title=args.english_title,
            chinese_title=args.chinese_title,
            subtitle="LIVE CK3 NATIVE CAPABILITY SEGMENT",
            body="OBSERVE exact-build CK3 state\n→ run one bounded native acceptance scenario\n→ expose the managed CK3 process on screen\n→ verify the runner artifact and process cleanup",
            chinese_body="观察 exact-build CK3 状态\n→ 执行一条有边界的原生实机验收场景\n→ 将受管 CK3 进程真实展示在画面中\n→ 核验 runner artifact 与进程清理",
            badge=args.status_badge,
            boundary=args.boundary_text,
            accent="#daaa4a",
        )
        capture = subprocess.Popen(
            [str(ffmpeg), "-hide_banner", "-loglevel", "error", "-f", "gdigrab", "-framerate", str(CAPTURE_FRAME_RATE), "-draw_mouse", "0", "-video_size", f"{CAPTURE_WIDTH}x{CAPTURE_HEIGHT}", "-i", "desktop", "-c:v", "h264_nvenc", "-preset", "p5", "-tune", "hq", "-rc", "vbr", "-cq", "22", "-b:v", "0", "-pix_fmt", "yuv420p", "-n", str(paths.raw_video)],
            cwd=REPOSITORY_ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        overlay.pump(1200)
        if capture.poll() is not None:
            raise RecordingError(f"FFmpeg capture exited before title card completion: {capture.stderr.read() if capture.stderr else ''}")
        overlay.pump(round(args.title_seconds * 1000))
        stdout_stream = paths.stdout.open("x", encoding="utf-8", newline="")
        stderr_stream = paths.stderr.open("x", encoding="utf-8", newline="")
        child_environment = os.environ.copy()
        child_environment.update(plan["_environment"])
        runner = subprocess.Popen(
            [plan["runner"], *args.runner_argument, "--output", str(paths.artifact)],
            cwd=REPOSITORY_ROOT,
            stdin=subprocess.DEVNULL,
            stdout=stdout_stream,
            stderr=stderr_stream,
            text=True,
            encoding="utf-8",
            env=child_environment,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        current_pid: int | None = None
        last_raise = 0.0
        while runner.poll() is None:
            ck3_pids = pids_named("ck3.exe")
            for pid in ck3_pids:
                if pid not in observed_pids:
                    observed_pids.append(pid)
            if ck3_pids:
                latest = ck3_pids[-1]
                if latest != current_pid:
                    current_pid = latest
                    ordinal = observed_pids.index(latest) + 1
                    overlay.show_lower(badge=args.status_badge, english=f"LIVE PROCESS #{ordinal}: {args.english_title}", chinese=f"实机进程 #{ordinal}：{args.chinese_title}", boundary=args.boundary_text)
                if time.monotonic() - last_raise >= 0.5:
                    for pid, hwnd in visible_windows_for_pids(ck3_pids).items():
                        bring_forward(hwnd)
                        foreground_attempts += 1
                        seen_window_pids.add(pid)
                    overlay.lower.lift()
                    last_raise = time.monotonic()
            elif observed_pids and current_pid is not None:
                current_pid = None
                overlay.show_card(title="PROCESS HANDOFF / EVIDENCE BINDING", chinese_title="进程交接 / 正在绑定证据", subtitle=args.english_title, body="A managed CK3 process has closed.\nThe runner is validating its checkpoint or finalizing typed native evidence.", chinese_body="一个受管 CK3 进程已经关闭。\nrunner 正在核验检查点或收束 typed native evidence。", badge=args.status_badge, boundary=args.boundary_text, accent="#daaa4a")
            overlay.pump(120)
        runner_exit = runner.wait()
        stdout_stream.close()
        stderr_stream.close()
        stdout_stream = None
        stderr_stream = None
        overlay.show_card(title="VERIFYING NATIVE EVIDENCE", chinese_title="正在核验原生证据", subtitle=args.english_title, body="Parsing the runner artifact, hashing evidence, and proving that no managed CK3 process remains...", chinese_body="正在解析 runner artifact、计算证据哈希，并证明没有任何受管 CK3 进程残留……", badge=args.status_badge, boundary=args.boundary_text, accent="#daaa4a")
        overlay.pump(500)
        if not paths.artifact.is_file():
            failure = "runner did not write the injected output artifact"
        else:
            value = json.loads(paths.artifact.read_text(encoding="utf-8-sig"))
            if not isinstance(value, dict):
                failure = "runner artifact root is not an object"
            else:
                artifact = value
                artifact_identity = file_identity(paths.artifact)
                if artifact.get("ok") is not True:
                    failure = "runner artifact does not contain top-level ok=true"
        cleanup = wait_for_ck3_cleanup(25)
        if not cleanup["ok"]:
            failure = f"CK3 cleanup failed; remaining PIDs: {cleanup['remaining_pids']}"
        if runner_exit != 0:
            failure = f"runner exited with code {runner_exit}"
        qualified = failure is None
        if qualified:
            overlay.show_card(title="LIVE CAPABILITY: GREEN", chinese_title="实机能力验收：GREEN / 通过", subtitle=args.english_title, body=f"runner exit       : 0\nartifact kind     : {artifact.get('kind')}\nartifact SHA-256  : {artifact_identity['sha256'][:16]}...\nmanaged CK3 PIDs  : {' → '.join(map(str, observed_pids)) or 'none observed'}\nforeground windows: {len(seen_window_pids)}\ncleanup           : no ck3.exe remains", chinese_body=f"runner 退出码      ：0\nartifact 类型      ：{artifact.get('kind')}\n受管 CK3 进程      ：{' → '.join(map(str, observed_pids)) or '未观察到'}\n清理结果           ：没有 ck3.exe 残留", badge=f"{args.status_badge} / GREEN", boundary=args.boundary_text, accent="#37cd7e")
        else:
            overlay.show_card(title="LIVE CAPABILITY: RED", chinese_title="实机能力验收：RED / 未通过", subtitle="THIS SEGMENT IS NOT QUALIFIED", body=f"failure: {failure}\nartifact: {(artifact or {}).get('error', 'unavailable')}", chinese_body=f"失败原因：{failure}\nartifact：{(artifact or {}).get('error', 'unavailable')}", badge=f"{args.status_badge} / RED", boundary=args.boundary_text, accent="#eb545c")
        overlay.pump(round(args.result_seconds * 1000))
    except BaseException as error:
        failure = failure or str(error)
        try:
            overlay.show_card(title="SEGMENT RECORDING FAILED", chinese_title="能力片段录制失败", subtitle="RAW CAPTURE WILL BE RETAINED", body=failure, chinese_body="该片段不能作为 GREEN 实机证据；原始录制会保留以供诊断。", badge=f"{args.status_badge} / RED", boundary=args.boundary_text, accent="#eb545c")
            overlay.pump(8000)
        except BaseException:
            pass
    finally:
        if runner is not None and runner.poll() is None:
            runner.kill()
            runner.wait()
        if stdout_stream is not None:
            stdout_stream.close()
        if stderr_stream is not None:
            stderr_stream.close()
        cleanup = cleanup if cleanup and cleanup.get("ok") else wait_for_ck3_cleanup(25)
        if capture is not None and capture.poll() is None:
            try:
                assert capture.stdin is not None
                capture.stdin.write("q\n")
                capture.stdin.flush()
                capture.stdin.close()
                capture.wait(timeout=20)
            except (OSError, subprocess.TimeoutExpired):
                capture.kill()
                capture.wait()
        overlay.close()
        for hwnd in obs_windows.values():
            show_window(hwnd, 9)
    if failure:
        raise RecordingError(f"native capability segment was RED; raw recording retained at {paths.raw_video}: {failure}")
    if not qualified or not paths.raw_video.is_file() or artifact is None or artifact_identity is None or cleanup is None:
        raise RecordingError("recording completed without a qualified evidence set")
    mux = subprocess.run([str(ffmpeg), "-hide_banner", "-loglevel", "error", "-i", str(paths.raw_video), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v:0", "-map", "1:a:0", "-shortest", "-c:v", "copy", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", "-metadata", f"title={args.english_title} / {args.chinese_title}", "-n", str(paths.final_video)], cwd=REPOSITORY_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False, creationflags=subprocess.CREATE_NO_WINDOW)
    if mux.returncode or not paths.final_video.is_file():
        raise RecordingError(f"MP4 mux failed (exit {mux.returncode}): {mux.stderr}")
    probe_run = subprocess.run([str(ffprobe), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(paths.final_video)], capture_output=True, text=True, encoding="utf-8", errors="strict", check=False, creationflags=subprocess.CREATE_NO_WINDOW)
    if probe_run.returncode:
        raise RecordingError(f"ffprobe failed (exit {probe_run.returncode}): {probe_run.stderr}")
    probe = json.loads(probe_run.stdout)
    video_stream = next((row for row in probe.get("streams", []) if row.get("codec_type") == "video"), None)
    audio_stream = next((row for row in probe.get("streams", []) if row.get("codec_type") == "audio"), None)
    if not video_stream or video_stream.get("codec_name") != "h264" or int(video_stream.get("width", 0)) != CAPTURE_WIDTH or int(video_stream.get("height", 0)) != CAPTURE_HEIGHT:
        raise RecordingError("final MP4 lacks the required H.264 2560x1440 video stream")
    if not audio_stream or audio_stream.get("codec_name") != "aac":
        raise RecordingError("final MP4 lacks an AAC audio stream")
    numerator, denominator = map(float, str(video_stream["avg_frame_rate"]).split("/"))
    frame_rate = numerator / denominator
    duration = float(probe["format"]["duration"])
    video_identity = file_identity(paths.final_video)
    if not 28 <= frame_rate <= 31 or video_identity["bytes"] < 100 * 1024 or duration < 10:
        raise RecordingError("final MP4 sanity check failed")
    sidecar = {
        "format_version": 1,
        "kind": "ck3_native_capability_segment_video",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "segment": {"id": args.segment_id, "english_title": args.english_title, "chinese_title": args.chinese_title, "status_badge": args.status_badge, "boundary_text": args.boundary_text},
        "language": {"primary": "English", "secondary": "Simplified Chinese subtitles", "title_cards_bilingual": True, "gameplay_lower_third_bilingual": True, "evidence_card_bilingual": True},
        "runner": {"executable": plan["runner"], "arguments": [*args.runner_argument, "--output", str(paths.artifact)], "environment_keys": plan["environment_keys"], "exit_code": runner_exit, "stdout": file_identity(paths.stdout), "stderr": file_identity(paths.stderr)},
        "live_artifact": {**artifact_identity, "ok": artifact.get("ok"), "kind": artifact.get("kind"), "evidence_classification": artifact.get("evidence_classification"), "elapsed_seconds": artifact.get("elapsed_seconds")},
        "process_evidence": {"ck3_pids_in_observed_order": observed_pids, "ck3_process_count": len(observed_pids), "ck3_window_pids": sorted(seen_window_pids), "foreground_attempt_count": foreground_attempts, "no_ck3_processes_before": True, "no_ck3_processes_after": cleanup["ok"], "stable_absence_samples": cleanup["stable_absence_samples"]},
        "video": {**video_identity, "duration_seconds": round(duration, 3), "width": CAPTURE_WIDTH, "height": CAPTURE_HEIGHT, "frame_rate": round(frame_rate, 3), "video_codec": "H.264", "video_encoder": "h264_nvenc", "pixel_format": video_stream.get("pix_fmt"), "audio_codec": "AAC", "audio_description": "silent AAC stereo"},
    }
    write_new(paths.sidecar, json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n")
    sidecar_identity = file_identity(paths.sidecar)
    raw_resolved = paths.raw_video.resolve()
    if not raw_resolved.is_relative_to(paths.raw_video.parent.resolve()):
        raise RecordingError(f"refusing to remove raw capture outside output directory: {raw_resolved}")
    raw_resolved.unlink()
    return {"ok": True, "segment_id": args.segment_id, "video": str(paths.final_video), "video_sha256": video_identity["sha256"], "sidecar": str(paths.sidecar), "sidecar_sha256": sidecar_identity["sha256"], "live_artifact": str(paths.artifact), "live_artifact_sha256": artifact_identity["sha256"], "stdout": str(paths.stdout), "stderr": str(paths.stderr), "ck3_pids": observed_pids, "duration_seconds": round(duration, 3), "bytes": video_identity["bytes"]}


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    plan = recording_plan(args)
    if args.plan_only:
        print(json.dumps(public_plan(plan), ensure_ascii=False, indent=2))
        return 0
    result = run(args, plan)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RecordingError, OSError, UnicodeError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)

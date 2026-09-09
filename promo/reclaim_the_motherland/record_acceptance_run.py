"""Record the existing MCP-first Reclaim acceptance run as immutable raw video.

The underlying acceptance runner owns the CK3 launch slot and performs all game
control.  This wrapper only waits for the real game window, records that window
without a mouse cursor, and binds the recording timeline to the runner evidence.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def ffmpeg_argv(ffmpeg: Path, window_title: str, output: Path) -> list[str]:
    return [
        str(ffmpeg),
        "-hide_banner",
        "-loglevel",
        "info",
        "-y",
        "-f",
        "gdigrab",
        "-framerate",
        "30",
        "-draw_mouse",
        "0",
        "-i",
        f"title={window_title}",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-crf",
        "16",
        "-pix_fmt",
        "yuv420p",
        "-r",
        "30",
        str(output),
    ]


def acceptance_argv(args: argparse.Namespace, cell: Path) -> list[str]:
    command = [
        str(args.python),
        str(args.acceptance_runner),
        "--artifacts-dir",
        str(cell),
        "--source",
        str(args.source),
        "--manifest",
        str(args.manifest),
        "--bridge-dll",
        str(args.bridge_dll),
        "--bridge-injector",
        str(args.bridge_injector),
        "--keep-userdir",
    ]
    if args.bridge_pipe:
        command.extend(["--bridge-pipe", args.bridge_pipe])
    return command


def _visible_windows() -> list[str]:
    titles: list[str] = []
    user32 = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    @callback_type
    def callback(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length:
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            value = buffer.value.strip()
            if value:
                titles.append(value)
        return True

    user32.EnumWindows(callback, 0)
    return titles


def wait_for_window(process: subprocess.Popen[str], needle: str, timeout: float) -> str:
    deadline = time.monotonic() + timeout
    last_titles: list[str] = []
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"acceptance runner exited before CK3 window appeared: {process.returncode}"
            )
        last_titles = _visible_windows()
        matches = [value for value in last_titles if needle.casefold() in value.casefold()]
        if matches:
            return min(matches, key=len)
        time.sleep(0.5)
    raise TimeoutError(f"timed out waiting for {needle!r}; visible={last_titles[-12:]}")


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def record(args: argparse.Namespace) -> int:
    attempt = args.attempt_directory.resolve()
    if attempt.exists():
        raise FileExistsError(f"capture attempt already exists: {attempt}")
    attempt.mkdir(parents=True)
    cell = attempt / "acceptance"
    raw_video = attempt / "raw-ck3-window-a01.mkv"
    acceptance_stdout = (attempt / "acceptance.stdout.txt").open("x", encoding="utf-8")
    acceptance_stderr = (attempt / "acceptance.stderr.txt").open("x", encoding="utf-8")
    acceptance_command = acceptance_argv(args, cell)
    _write_json(
        attempt / "acceptance-command.json",
        {"argv": acceptance_command, "shell": False},
    )
    started_at = datetime.now(timezone.utc)
    runner = subprocess.Popen(
        acceptance_command,
        stdout=acceptance_stdout,
        stderr=acceptance_stderr,
        text=True,
    )
    recorder: subprocess.Popen[str] | None = None
    recorder_stdout = (attempt / "ffmpeg.stdout.txt").open("x", encoding="utf-8")
    recorder_stderr = (attempt / "ffmpeg.stderr.txt").open("x", encoding="utf-8")
    window_title = ""
    capture_started_at: datetime | None = None
    wrapper_error: str | None = None
    try:
        window_title = wait_for_window(runner, args.window_title, args.window_timeout)
        capture_command = ffmpeg_argv(args.ffmpeg.resolve(), window_title, raw_video)
        _write_json(
            attempt / "ffmpeg-command.json",
            {"argv": capture_command, "shell": False, "draw_mouse": False},
        )
        capture_started_at = datetime.now(timezone.utc)
        recorder = subprocess.Popen(
            capture_command,
            stdin=subprocess.PIPE,
            stdout=recorder_stdout,
            stderr=recorder_stderr,
            text=True,
        )
        runner_returncode = runner.wait()
    except BaseException as error:
        wrapper_error = f"{type(error).__name__}: {error}"
        runner_returncode = runner.wait()
    finally:
        if recorder is not None and recorder.poll() is None:
            try:
                assert recorder.stdin is not None
                recorder.stdin.write("q\n")
                recorder.stdin.flush()
                recorder.wait(timeout=30)
            except Exception:
                recorder.terminate()
                recorder.wait(timeout=15)
        acceptance_stdout.close()
        acceptance_stderr.close()
        recorder_stdout.close()
        recorder_stderr.close()

    finished_at = datetime.now(timezone.utc)
    recorder_returncode = None if recorder is None else recorder.returncode
    timeline_rows: list[dict[str, object]] = []
    if capture_started_at is not None and cell.is_dir():
        for path in sorted(item for item in cell.rglob("*") if item.is_file()):
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            timeline_rows.append(
                {
                    "path": path.relative_to(attempt).as_posix(),
                    "seconds_from_capture_start": round(
                        max(0.0, (mtime - capture_started_at).total_seconds()), 3
                    ),
                    "bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
            )
    _write_json(
        attempt / "capture-timeline.json",
        {
            "format_version": 1,
            "kind": "reclaim-promo-capture-timeline",
            "capture_started_at_utc": None
            if capture_started_at is None
            else capture_started_at.isoformat(),
            "events": timeline_rows,
        },
    )
    report = {
        "format_version": 1,
        "kind": "reclaim-promo-acceptance-capture",
        "result": "GREEN"
        if runner_returncode == 0
        and recorder_returncode == 0
        and raw_video.is_file()
        and wrapper_error is None
        else "RED",
        "wrapper_error": wrapper_error,
        "started_at_utc": started_at.isoformat(),
        "capture_started_at_utc": None
        if capture_started_at is None
        else capture_started_at.isoformat(),
        "finished_at_utc": finished_at.isoformat(),
        "window_title": window_title,
        "draw_mouse": False,
        "acceptance_returncode": runner_returncode,
        "ffmpeg_returncode": recorder_returncode,
        "raw_video": None
        if not raw_video.is_file()
        else {
            "path": str(raw_video),
            "bytes": raw_video.stat().st_size,
            "sha256": _sha256(raw_video),
        },
        "acceptance_report": str(cell / "report.json"),
        "timeline": str(attempt / "capture-timeline.json"),
        "process_material_retained": True,
    }
    _write_json(attempt / "capture-report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["result"] == "GREEN" else 1


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--attempt-directory", required=True, type=Path)
    value.add_argument("--python", required=True, type=Path)
    value.add_argument("--acceptance-runner", required=True, type=Path)
    value.add_argument("--source", required=True, type=Path)
    value.add_argument("--manifest", required=True, type=Path)
    value.add_argument("--bridge-dll", required=True, type=Path)
    value.add_argument("--bridge-injector", required=True, type=Path)
    value.add_argument("--bridge-pipe")
    value.add_argument("--ffmpeg", required=True, type=Path)
    value.add_argument("--window-title", default="Crusader Kings III")
    value.add_argument("--window-timeout", type=float, default=1800.0)
    return value


if __name__ == "__main__":
    raise SystemExit(record(parser().parse_args()))

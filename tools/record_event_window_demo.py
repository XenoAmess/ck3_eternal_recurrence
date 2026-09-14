from __future__ import annotations

import argparse
from datetime import datetime
import os
from pathlib import Path
import sys

from record_native_capability_segment import RecordingError, main as record_segment


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DLL_SHA256 = "52398435F8AA5177D6D507BFAA38CD2578EB988F0629F1C5E13360CC91FB3BB0"


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="Record the bilingual live event-window checkpoint demonstration"
    )
    value.add_argument("--output-directory", type=Path)
    value.add_argument("--title-seconds", type=float, default=6)
    value.add_argument("--result-seconds", type=float, default=12)
    value.add_argument("--plan-only", action="store_true")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    today = datetime.now().strftime("%Y-%m-%d")
    output = (
        args.output_directory
        or REPOSITORY_ROOT / "artifacts" / "demos" / today
    ).resolve()
    python = REPOSITORY_ROOT / "tools" / ".venv" / "Scripts" / "python.exe"
    runner = (
        REPOSITORY_ROOT
        / "ck3_autonomous_player"
        / "native_bridge"
        / "research"
        / "run_current_event_window_context_live_acceptance.py"
    )
    game = REPOSITORY_ROOT / "Crusader Kings III"
    bridge = (
        REPOSITORY_ROOT
        / "ck3_autonomous_player"
        / "native_bridge"
        / ".build-event-window-cea30a0-msvc2"
    )
    isolated_source = (
        Path(os.environ.get("TEMP", "")) / "xar-event-window-cea30a0-source"
    ).resolve()
    required = (
        python,
        runner,
        game,
        bridge / "xar_ck3_bridge.dll",
        bridge / "xar_ck3_bridge_injector.exe",
        isolated_source,
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RecordingError(f"required demo input is missing: {missing}")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    pipe = rf"\\.\pipe\xar-event-window-video-{stamp}"
    record_arguments = [
        "--segment-id",
        "event-window-context",
        "--english-title",
        "CK3 AUTONOMOUS AGENT / LIVE EVENT OBSERVATION",
        "--chinese-title",
        "CK3 自动游玩智能体 / 原生事件观察",
        "--status-badge",
        "READ-ONLY NATIVE QUERY",
        "--boundary-text",
        "NO OCR / NO MOUSE / NO EVENT OPTION IS SELECTED  |  无 OCR、无鼠标、不选择任何事件选项",
        "--runner",
        str(python),
        "--environment",
        f"XAR_EVENT_WINDOW_ISOLATED_SOURCE_ROOT={isolated_source}",
        "--output-directory",
        str(output),
        "--title-seconds",
        str(args.title_seconds),
        "--result-seconds",
        str(args.result_seconds),
    ]
    for argument in (
        str(runner),
        "--game-dir",
        str(game),
        "--bridge-pipe",
        pipe,
        "--bridge-dll",
        str(bridge / "xar_ck3_bridge.dll"),
        "--expected-bridge-dll-sha256",
        EXPECTED_DLL_SHA256,
        "--bridge-injector",
        str(bridge / "xar_ck3_bridge_injector.exe"),
    ):
        record_arguments.append(f"--runner-argument={argument}")
    if args.plan_only:
        record_arguments.append("--plan-only")
    return record_segment(record_arguments)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RecordingError, OSError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)

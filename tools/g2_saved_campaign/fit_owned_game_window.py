"""Fit only the generation-bound Game HWND to its observed monitor work area."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


def workarea_geometry(info):
    """Return validated Win32 position/size DATA without importing an OS backend."""
    if not isinstance(info, dict):
        raise ValueError("Monitor/Work metadata object required")

    def rectangle(value, label):
        if not isinstance(value, (tuple, list)) or len(value) != 4:
            raise ValueError(label + " requires four coordinates")
        if any(type(item) is not int or not -(1 << 31) <= item < (1 << 31) for item in value):
            raise ValueError(label + " requires exact signed Win32 coordinates")
        left, top, right, bottom = value
        if not (0 < right - left < (1 << 31) and 0 < bottom - top < (1 << 31)):
            raise ValueError(label + " requires positive Win32 width and height")
        return left, top, right, bottom

    monitor = rectangle(info.get("Monitor"), "Monitor")
    work = rectangle(info.get("Work"), "Work")
    if not (monitor[0] <= work[0] and monitor[1] <= work[1]
            and work[2] <= monitor[2] and work[3] <= monitor[3]):
        raise ValueError("Work must be contained by Monitor")
    return {"monitor": monitor, "work": work,
            "target": (work[0], work[1], work[2] - work[0], work[3] - work[1])}


def _read_launch(path):
    with path.open("rb") as stream:
        raw = stream.read(1048577)
    if not raw or len(raw) > 1048576:
        raise ValueError("bounded nonempty launch receipt required")
    value = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("launch receipt must be a JSON object")
    return value


def _generation_helpers():
    # Same package root as the existing placement source, also usable from its frozen D tree.
    source_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(source_root))
    from tools.g2_saved_campaign import managed_desktop1_placement as managed
    expected = Path(__file__).resolve().with_name("managed_desktop1_placement.py")
    if Path(managed.__file__).resolve() != expected:
        raise RuntimeError("generation helper belongs to another source root")
    return managed.game_generation, managed.check_game_window


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--launch-receipt", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    # Reserve the create-only receipt before any Game query or possible mutation.
    with args.receipt.open("x", encoding="utf-8") as stream:
        result = {"schema": "xar.owned-game-workarea-fit/v1", "status": "FAILED",
                  "begin_utc": datetime.now(timezone.utc).isoformat(),
                  "launch_receipt": str(args.launch_receipt), "window_mutation_attempted": False,
                  "no_gameplay_input": True, "runtime_rendering_qualified": False,
                  "coordinate_context": "caller Win32 context; physical DPI qualification is not inferred"}
        primary = None
        try:
            launch = _read_launch(args.launch_receipt)
            game_generation, check_game_window = _generation_helpers()
            import win32api
            import win32con
            import win32gui
            import win32process

            with game_generation(launch) as generation:
                windows = []

                def collect(hwnd, unused):
                    if (win32gui.IsWindowVisible(hwnd)
                            and win32process.GetWindowThreadProcessId(hwnd)[1] == generation.pid
                            and win32gui.GetWindowText(hwnd) == "Crusader Kings III"):
                        windows.append(hwnd)

                generation.check()
                win32gui.EnumWindows(collect, None)
                if len(windows) != 1:
                    raise RuntimeError("one unique visible owned CK3 window required")
                hwnd = windows[0]
                classname = win32gui.GetClassName(hwnd)

                def guard():
                    check_game_window(generation, hwnd, classname)
                    if not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
                        raise RuntimeError("owned Game window must remain visible and non-minimized")

                guard()
                monitor_handle = win32api.MonitorFromWindow(hwnd, 2)
                if not monitor_handle:
                    raise RuntimeError("owned window has no selected monitor")
                geometry = workarea_geometry(win32api.GetMonitorInfo(monitor_handle))
                guard()
                before = {"window": win32gui.GetWindowRect(hwnd), "client": win32gui.GetClientRect(hwnd),
                          "style": win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)}
                guard()
                result.update(pid=generation.pid, creation_filetime=generation.creation_filetime,
                              hwnd=hwnd, window_class=classname, monitor_handle=int(monitor_handle),
                              monitor=geometry["monitor"], work=geometry["work"],
                              target=geometry["target"], before=before)
                style = (before["style"] & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME
                         | win32con.WS_MINIMIZE | win32con.WS_MAXIMIZE)) | win32con.WS_POPUP
                if style >= 0x80000000:
                    style -= 0x100000000
                guard()
                result["window_mutation_attempted"] = True
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
                guard()
                left, top, width, height = geometry["target"]
                win32gui.SetWindowPos(hwnd, 0, left, top, width, height,
                                     win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE | win32con.SWP_FRAMECHANGED)
                guard()
                after = {"window": win32gui.GetWindowRect(hwnd), "client": win32gui.GetClientRect(hwnd),
                         "style": win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)}
                guard()
                current_monitor = win32api.MonitorFromWindow(hwnd, 2)
                current_geometry = workarea_geometry(win32api.GetMonitorInfo(current_monitor))
                guard()
                result["after"] = after
                if current_monitor != monitor_handle or current_geometry != geometry:
                    raise RuntimeError("monitor/workarea changed during owned fit; no retry performed")
                if after["window"] != geometry["work"] or after["client"] != (0, 0, width, height):
                    raise RuntimeError("actual borderless outer/client geometry does not match Work")
                result.update(status="GEOMETRY_VERIFIED_ONLY", geometry_verified=True)
        except BaseException as error:
            primary = error
            result["error"] = {"type": type(error).__name__, "message": str(error)}
        finally:
            result["end_utc"] = datetime.now(timezone.utc).isoformat()
            try:
                json.dump(result, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
            except BaseException as receipt_error:
                if primary is not None:
                    raise RuntimeError("fit receipt failed; original=" + repr(primary)) from receipt_error
                raise
        print(json.dumps(result, ensure_ascii=False), flush=True)
        if primary is not None:
            raise primary


if __name__ == "__main__":
    main()

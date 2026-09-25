"""Read the fixed OneDrive client's activity row for one uploaded MP4 or WAV."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

import uiautomation as auto


FOLDER = "CK3-War-AI-20260923"


def descendants(control, level=0):
    if level > 8:
        return []
    rows = [control]
    for child in control.GetChildren():
        rows.extend(descendants(child, level + 1))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-name", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.target_name.lower().endswith((".mp4", ".wav")) or Path(args.target_name).name != args.target_name:
        raise ValueError("Expected one MP4 or WAV basename")
    root = auto.GetRootControl()
    windows = root.GetChildren()
    if not any(window.ClassName == "OneDriveReactNativeWin32WindowClass" for window in windows):
        tray = next(window for window in windows if window.ClassName == "Shell_TrayWnd")
        buttons = [control for control in descendants(tray)
                   if "OneDrive" in (control.Name or "")]
        if len(buttons) != 1:
            raise RuntimeError(f"Expected one OneDrive tray button, got {len(buttons)}")
        pattern = buttons[0].GetLegacyIAccessiblePattern()
        if pattern is None:
            raise RuntimeError("OneDrive tray button has no semantic default action")
        pattern.DoDefaultAction()
        time.sleep(2)
        windows = root.GetChildren()
    rows = []
    for window in windows:
        if window.ClassName != "OneDriveReactNativeWin32WindowClass":
            continue
        for child in descendants(window):
            name = child.Name or ""
            if args.target_name in name or child.AutomationId == "statusText":
                rows.append({"name": name, "automation_id": child.AutomationId,
                             "type": child.ControlTypeName})
    uploaded = any(args.target_name in row["name"] and f"已上传到 {FOLDER}" in row["name"] for row in rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise FileExistsError(args.output)
    result = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "target": args.target_name, "folder": FOLDER,
              "status": "uploaded" if uploaded else "pending", "rows": rows}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()

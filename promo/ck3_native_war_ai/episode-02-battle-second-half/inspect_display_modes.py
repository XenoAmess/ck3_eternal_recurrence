"""Read available native Windows display modes; never changes the desktop."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

import win32api
import win32con


def mode(dev: object) -> dict[str, int]:
    return {"width": int(dev.PelsWidth), "height": int(dev.PelsHeight),
            "bits_per_pixel": int(dev.BitsPerPel), "frequency_hz": int(dev.DisplayFrequency)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error("output must be new in an existing external attempt")
    current = mode(win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS))
    listed = []
    index = 0
    while True:
        try:
            listed.append(mode(win32api.EnumDisplaySettings(None, index)))
        except win32api.error:
            break
        index += 1
    unique = sorted({(item["width"], item["height"], item["bits_per_pixel"],
                      item["frequency_hz"]) for item in listed})
    modes = [dict(zip(("width", "height", "bits_per_pixel", "frequency_hz"), row))
             for row in unique]
    result = {"schema": "xar.war-promo.read-only-display-mode-probe/v1",
              "observed_at": datetime.now(timezone.utc).isoformat(),
              "current": current, "modes": modes,
              "candidate_1280x720_or_more": [item for item in modes
                                              if item["width"] >= 1280 and item["height"] >= 720],
              "candidate_1920x1080_or_more": [item for item in modes
                                               if item["width"] >= 1920 and item["height"] >= 1080],
              "changed_display_settings": False}
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({"current": current, "mode_count": len(modes),
                      "at_least_1280x720": len(result["candidate_1280x720_or_more"]),
                      "at_least_1920x1080": len(result["candidate_1920x1080_or_more"])},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()

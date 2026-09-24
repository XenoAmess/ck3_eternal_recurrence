"""Read-only probe of the shared war hotspot selector against a CK3 snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xar_autoplayer.bridge.war_hotspot_camera import (  # noqa: E402
    LandedProvinceIndex,
    select_war_hotspot,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", required=True, type=Path)
    parser.add_argument("--snapshot", required=True, type=Path)
    args = parser.parse_args()
    index = LandedProvinceIndex.from_game_dir(args.game_dir)
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8-sig"))
    print(json.dumps({
        "title_files": len(index.source_files),
        "mapped_land_provinces": len(index.barony_by_province),
        "hotspot": select_war_hotspot(snapshot, index),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

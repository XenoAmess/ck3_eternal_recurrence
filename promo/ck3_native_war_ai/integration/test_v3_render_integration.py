"""Exercise one actual V3 visual clip through the project's ffmpeg path."""

import argparse
import json
from pathlib import Path
import sys

from xar_promo.media import probe_media

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "src"))
from war_ai_promo.visuals import render_visual  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    args = parser.parse_args()
    root = args.artifact_root
    root.mkdir(parents=True, exist_ok=False)
    assets = json.loads(args.assets.read_text(encoding="utf-8"))["assets"]
    ledger = HERE.parent / "longform/v3/evidence-visual-ledger.json"
    row = {"id": "V3-16", "shot_id": "S3-16", "chapter_id": "targets", "duration_seconds": 5.0}
    output = render_visual(row, root / "visuals/V3-16.mp4", "ffmpeg", root,
                           v3_ledger=ledger, v3_assets=assets)
    probe = probe_media("ffprobe", output, audit_directory=root / "probe")
    stream = probe.video_streams[0]
    if (stream.width, stream.height) != (2560, 1440) or abs(probe.require_duration() - 5) > .1:
        raise ValueError("V3 rendered visual has wrong dimensions or duration")
    plan = json.loads((root / "drawings/V3-16/visual-plan.json").read_text(encoding="utf-8"))
    if plan["kind"] != "evidence-scoped-v3-visual" or len(plan["frame_receipts"]) != 3:
        raise ValueError("V3 render did not retain three evidence-scoped image receipts")
    print(f"V3 ffmpeg visual PASS: {output}")


if __name__ == "__main__":
    main()

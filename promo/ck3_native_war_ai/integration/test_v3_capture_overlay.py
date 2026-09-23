"""Check an actual rendered V3 case banner without inventing AI evidence."""

import argparse
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "src"))
from war_ai_promo.capture_overlay import label_capture_clip  # noqa: E402
from war_ai_promo.common import binding  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    args = parser.parse_args()
    prepared = {"schema": "ck3-war-ai.prepared-capture-clip.v2",
                "media": binding(args.source), "selection": {"expected_frame_count": 150},
                "duration_seconds": 5.0, "receipt": binding(args.source),
                "native_ai_causality_verified": False}
    result = label_capture_clip(prepared, case_id="CASE-W", cue_id="V3-16",
                                output_root=args.artifact_root, ffmpeg="ffmpeg", ffprobe="ffprobe")
    if (result["schema"] != "ck3-war-ai.labeled-capture-clip.v1"
            or result["native_ai_causality_verified"] is not False
            or result["label_text"][0].find("CASE-W") < 0):
        raise ValueError("V3 label did not bind the case and finite evidence scope")
    print(f"V3 labelled clip PASS: {result['media']['path']}")


if __name__ == "__main__":
    main()

"""Extract real PTS endpoints or package a completed bounded wartime observation."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from war_ai_promo.wartime_bundle import extract_wartime_frames, package_wartime_bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract-frames", help="Reuse actual PTS extraction; remains pending image review")
    extract.add_argument("--recording-dir", required=True, type=Path)
    extract.add_argument("--output", required=True, type=Path)
    extract.add_argument("--begin-seconds", required=True, type=float)
    extract.add_argument("--end-seconds", required=True, type=float)
    extract.add_argument("--frame-probe", type=Path)
    extract.add_argument("--ffmpeg", default="ffmpeg")
    extract.add_argument("--ffprobe", default="ffprobe")
    package = commands.add_parser("package", help="Preserve evidence in a new bundle after actual endpoint review")
    for name in ("recording-dir", "case-dir", "session-dir", "snapshot-after", "review-json",
                 "output", "recorder-script", "operator-script"):
        package.add_argument("--" + name, required=True, type=Path)
    package.add_argument("--snapshot-pointer", default="/body")
    args = parser.parse_args()
    if args.command == "extract-frames":
        result = extract_wartime_frames(args.recording_dir, args.output, args.begin_seconds, args.end_seconds,
            args.ffmpeg, frame_probe=args.frame_probe, ffprobe=args.ffprobe)
    else:
        result = package_wartime_bundle(args.recording_dir, args.case_dir, args.session_dir, args.snapshot_after,
            args.review_json, args.output, args.recorder_script, args.operator_script,
            snapshot_pointer=args.snapshot_pointer)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

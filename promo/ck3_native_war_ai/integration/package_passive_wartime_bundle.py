"""Extract reviewed actual-PTS images or package the closed passive CASE-C attempt."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from war_ai_promo.passive_wartime_bundle import extract_passive_frames, package_passive_bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract-frames", help="Extract two real-PTS endpoints for agent review")
    extract.add_argument("--recording-dir", required=True, type=Path)
    extract.add_argument("--output", required=True, type=Path)
    extract.add_argument("--begin-seconds", required=True, type=float)
    extract.add_argument("--end-seconds", required=True, type=float)
    extract.add_argument("--frame-probe", type=Path)
    extract.add_argument("--ffmpeg", default="ffmpeg")
    extract.add_argument("--ffprobe", default="ffprobe")
    package = commands.add_parser("package", help="Copy exact CASE-C evidence after actual image review")
    for name in ("recording-dir", "case-dir", "session-dir", "review-json",
                 "output", "recorder-script", "operator-script"):
        package.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    if args.command == "extract-frames":
        result = extract_passive_frames(args.recording_dir, args.output,
            args.begin_seconds, args.end_seconds, args.ffmpeg,
            frame_probe=args.frame_probe, ffprobe=args.ffprobe)
    else:
        result = package_passive_bundle(args.recording_dir, args.case_dir,
            args.session_dir, args.review_json, args.output,
            args.recorder_script, args.operator_script)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

"""Extract review images or package a completed paused-map capture; never launch CK3."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from war_ai_promo.gameplay_bundle import extract_frames, package_gameplay_bundle, probe_frame_timestamps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    probe = commands.add_parser("probe-frames", help="Probe actual decoded frame timestamps; does not infer CFR from metadata")
    probe.add_argument("--raw", required=True, type=Path)
    probe.add_argument("--output", required=True, type=Path)
    probe.add_argument("--ffprobe", default="ffprobe")
    extract = commands.add_parser("extract-frames", help="Extract actual raw endpoint PNGs; result remains pending review")
    extract.add_argument("--recording-dir", required=True, type=Path)
    extract.add_argument("--output", required=True, type=Path)
    extract.add_argument("--begin-seconds", required=True, type=float)
    extract.add_argument("--end-seconds", required=True, type=float)
    extract.add_argument("--ffmpeg", default="ffmpeg")
    extract.add_argument("--ffprobe", default="ffprobe")
    extract.add_argument("--frame-probe", type=Path, help="Reuse an exact raw-bound frame-timestamps.json instead of probing again")
    package = commands.add_parser("package", help="Copy existing evidence into a new bundle after actual agent image review")
    package.add_argument("--recording-dir", required=True, type=Path)
    package.add_argument("--review-json", required=True, type=Path)
    package.add_argument("--output", required=True, type=Path)
    package.add_argument("--producer-script", required=True, type=Path)
    package.add_argument("--evidence", action="append", type=Path, default=[])
    args = parser.parse_args()
    if args.command == "probe-frames":
        result = probe_frame_timestamps(args.raw, args.output, args.ffprobe)
    elif args.command == "extract-frames":
        result = extract_frames(args.recording_dir, args.output, args.begin_seconds, args.end_seconds, args.ffmpeg,
            frame_probe=args.frame_probe, ffprobe=args.ffprobe)
    else:
        result = package_gameplay_bundle(args.recording_dir, args.review_json, args.output, args.producer_script, args.evidence)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

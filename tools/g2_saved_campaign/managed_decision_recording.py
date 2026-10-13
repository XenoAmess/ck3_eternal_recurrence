"""Prepare/start dedicated Game+decision recording from actual Root receipts.

Root supplies existing engine/control dependencies and admitted output paths.
Nothing is installed; personal OBS processes are never selected or attached.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys


def validate_admission(args, admission):
    review = datetime.fromisoformat(admission["review_at_utc"].replace("Z", "+00:00"))
    deadline = datetime.fromisoformat(args.deadline_utc.replace("Z", "+00:00"))
    if (admission.get("status") != "ADMITTED" or review.tzinfo is None or deadline.tzinfo is None
            or deadline > review - timedelta(minutes=15) or datetime.now(timezone.utc) >= deadline):
        raise ValueError("recording must stop before the unchanged storage review minus 15 minutes")
    roots = [Path(p).resolve() for p in admission["approved_output_roots"]]
    for path in (args.obs_root, args.profile, args.output_root, args.receipt):
        if not any(path.resolve().is_relative_to(root) for root in roots):
            raise ValueError("OBS/config/recording paths escaped the admitted root")
    signal = getattr(args, "start_signal", None)
    if signal is not None and not signal.resolve().is_relative_to(args.output_root.resolve()):
        raise ValueError("recording start signal escaped the admitted recording root")
    if type(args.max_output_bytes) is not int or not 192 * 1024**2 <= args.max_output_bytes <= 1024**3:
        raise ValueError("Root recording allocation must include stop reserve, 192MiB..1GiB")
    if type(args.seconds) is not int or not 1 <= args.seconds <= 1200:
        raise ValueError("recording is limited to 20 minutes")
    if type(args.port) is not int or not 1024 <= args.port <= 65535:
        raise ValueError("explicit dedicated local port required")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "record"))
    for name in ("obs-root", "profile", "output-root", "control-dependencies", "launch-receipt",
                 "placement-receipt", "overlay-receipt", "ffprobe", "receipt", "storage-admission"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--deadline-utc", required=True)
    parser.add_argument("--seconds", type=int, default=1200)
    parser.add_argument("--max-output-bytes", type=int, default=1024**3)
    parser.add_argument("--start-signal", type=Path,
                        help="bind owned sources now; record once Root creates this new output-root file")
    args = parser.parse_args()
    if args.receipt.exists() or not args.receipt.parent.is_dir():
        parser.error("receipt must be new in an admitted existing directory")
    admission = json.loads(args.storage_admission.read_text(encoding="utf-8-sig"))
    validate_admission(args, admission)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import ck3_obs_capture as capture
    if args.mode == "prepare":
        capture.prepare_profile(args.obs_root, args.profile, args.output_root,
            port=args.port, control_dependencies=args.control_dependencies,
            deadline_utc=args.deadline_utc, max_output_bytes=args.max_output_bytes, bitrate_kbps=4800)
        result = {"state": "PREPARED_NOT_RECORDED", "profile": str(args.profile.resolve()),
                  "deadline_utc": args.deadline_utc, "storage_review_unchanged": admission["review_at_utc"]}
    else:
        profile = json.loads(args.profile.read_text(encoding="utf-8-sig"))
        if (profile["port"] != args.port or profile["deadline_utc"] != args.deadline_utc
                or profile["max_output_bytes"] != args.max_output_bytes
                or Path(profile["control_dependencies"]).resolve() != args.control_dependencies.resolve()
                or Path(profile["obs_root"]).resolve() != args.obs_root.resolve()):
            raise ValueError("record must use the exact prepared engine/dependencies/port/deadline/allocation")
        placement = json.loads(args.placement_receipt.read_text(encoding="utf-8-sig"))
        result = capture.launch_recording(args.profile, args.output_root, placement["pid"], placement["hwnd"],
            args.seconds, launch_receipt=args.launch_receipt, placement_receipt=args.placement_receipt,
            overlay_receipt=args.overlay_receipt, ffprobe=args.ffprobe, start_signal=args.start_signal)
    with args.receipt.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

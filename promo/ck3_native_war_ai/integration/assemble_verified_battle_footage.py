"""Concatenate only frame-audited CK3 battle intervals from immutable clips."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def sha256(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    if plan.get("schema") != "ck3.verified-battle-footage-edit.v1":
        raise ValueError("unknown battle footage edit schema")
    clips = plan.get("clips")
    if not isinstance(clips, list) or not clips:
        raise ValueError("edit requires source clips")
    root = args.plan.parent
    output = root / plan["output"]
    if output.exists():
        raise FileExistsError(output)
    inputs: list[Path] = []
    filters: list[str] = []
    for index, row in enumerate(clips):
        video = root / row["video"]
        audit = json.loads((root / row["audit"]).read_text(encoding="utf-8"))
        if sha256(video) != audit["video"]["sha256"]:
            raise ValueError(f"clip {index}: source bytes differ from visibility audit")
        start, end = float(row["start_seconds"]), float(row["end_seconds"])
        if not 0 <= start < end <= float(audit["duration_seconds"]):
            raise ValueError(f"clip {index}: invalid trim interval")
        if not any(float(begin) <= start and end <= float(finish)
                   for begin, finish in audit["visible_intervals_seconds"]):
            raise ValueError(f"clip {index}: trim extends outside a visible interval")
        if float(audit["sample_interval_seconds"]) > 1.0 or float(audit["minimum_score"]) < 0.75:
            raise ValueError(f"clip {index}: insufficient frame-audit cadence or threshold")
        inputs.append(video)
        filters.append(
            f"[{index}:v]trim=start={start:.3f}:end={end:.3f},"
            f"setpts=PTS-STARTPTS,fps=30,format=yuv420p[v{index}]"
        )
    filters.append("".join(f"[v{index}]" for index in range(len(clips)))
                   + f"concat=n={len(clips)}:v=1:a=0[out]")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise FileNotFoundError("ffmpeg")
    command = [ffmpeg, "-nostdin", "-n", "-hide_banner", "-loglevel", "warning"]
    for video in inputs:
        command.extend(["-i", str(video)])
    command.extend(["-filter_complex", ";".join(filters), "-map", "[out]",
                    "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-pix_fmt", "yuv420p", str(output)])
    command_path = root / (output.stem + "-command.json")
    if command_path.exists():
        raise FileExistsError(command_path)
    command_path.write_text(json.dumps(command, indent=2) + "\n", encoding="utf-8")
    log_path = root / (output.stem + "-ffmpeg.log")
    with log_path.open("xb") as log:
        process = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)
    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({process.returncode}); partial output preserved")
    receipt = {
        "schema": "ck3.verified-battle-footage-assembly.v1",
        "edit_plan": {"path": str(args.plan.resolve()), "sha256": sha256(args.plan)},
        "output": {"path": str(output.resolve()), "bytes": output.stat().st_size,
                   "sha256": sha256(output)},
        "source_clips": [{"path": str(path.resolve()), "sha256": sha256(path)} for path in inputs],
        "expected_duration_seconds": sum(float(row["end_seconds"]) - float(row["start_seconds"])
                                         for row in clips),
    }
    receipt_path = root / (output.stem + "-receipt.json")
    with receipt_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(receipt["output"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

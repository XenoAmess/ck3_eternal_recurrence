"""Select frame-exact review windows from a pending source inventory.

Only the small manifest and preserved FFprobe JSON are read and hashed. The
original raw video is statted, never opened, decoded, copied, or certified.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from plan_four_raw_pts_candidates import select_window


SHA = re.compile(r"[0-9a-fA-F]{64}\Z")
WINDOW_ID = re.compile(r"[a-z0-9][a-z0-9_-]*\Z")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def identity(path: Path) -> dict[str, Any]:
    path = path.resolve(strict=True)
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    after = path.stat()
    require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
            f"file changed during hash: {path}")
    return {"path": str(path), "bytes": after.st_size, "sha256": digest.hexdigest().upper()}


def decimal(value: str) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"invalid decimal PTS: {value}") from exc
    require(result.is_finite() and result >= 0, f"invalid decimal PTS: {value}")
    return result


def plan(manifest_path: Path, expected_sha: str,
         windows: list[tuple[str, str, str]]) -> dict[str, Any]:
    require(SHA.fullmatch(expected_sha) is not None, "expected manifest SHA-256 required")
    manifest_id = identity(manifest_path)
    require(manifest_id["sha256"] == expected_sha.upper(), "pending manifest SHA-256 differs")
    source = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(source.get("status") == "PENDING_CLEAN_REVIEW" and
            source.get("adapter_eligible") is False and
            source.get("human_1x_review_performed") is False and
            source.get("clean_spans") == [], "source is not a pending inventory")
    raw = source.get("raw") or {}
    raw_path = Path(raw["path"]).resolve(strict=True)
    require(raw_path.stat().st_size == raw.get("bytes"), "raw size differs from pending inventory")
    probe = source.get("ffprobe") or {}
    probe_id = identity(Path(probe["path"]))
    require(probe_id == probe, "FFprobe bytes/SHA differ from pending inventory")
    payload = json.loads(Path(probe["path"]).read_text(encoding="utf-8"))
    video = [row for row in payload.get("streams", []) if row.get("codec_type") == "video"]
    require(len(video) == 1, "exactly one video stream required")
    pts = [decimal(str(row.get("best_effort_timestamp_time") or row.get("pts_time")))
           for row in payload.get("frames", []) if row.get("stream_index") == video[0]["index"]]
    require(len(pts) > 1 and all(a < b for a, b in zip(pts, pts[1:])),
            "video PTS list missing or not strictly increasing")
    ids: set[str] = set()
    rows = []
    for window_id, begin, end in windows:
        require(WINDOW_ID.fullmatch(window_id) is not None and window_id not in ids,
                f"invalid or repeated window ID: {window_id}")
        ids.add(window_id)
        rows.append({"window_id": window_id,
                     **select_window(pts, decimal(begin), decimal(end))})
    return {"schema": "xar.war-promo.pending-review-pts-plan/v1",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "MACHINE_PTS_NAVIGATION_ONLY_UNREVIEWED",
            "source_manifest": manifest_id, "raw": raw,
            "raw_sha256_rehashed_this_run": False, "full_ffprobe": probe_id,
            "video_frame_count": len(pts), "windows": rows,
            "human_1x_review_performed": False, "clean_spans_certified": False,
            "adapter_bundle_validated": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--window", action="append", nargs=3, metavar=("ID", "BEGIN", "END"),
                        required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    require(not args.output.exists() and args.output.parent.is_dir(),
            "output must be new in an existing directory")
    result = plan(args.source_manifest, args.expected_manifest_sha256, args.window)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "windows": len(result["windows"]),
                      "gap_rejected": sum(row["machine_status"] == "GAP_REJECTED"
                                          for row in result["windows"]),
                      "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

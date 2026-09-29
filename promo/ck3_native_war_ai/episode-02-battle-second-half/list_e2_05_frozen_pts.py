"""Read only E2-05 a02 frozen ffprobe frame PTS near a visual transition.

This never opens the raw video. It is a navigation aid for sparse review, not
an assertion that a game event happened at any listed timestamp.
"""

from __future__ import annotations

import argparse
import bisect
import json
from decimal import Decimal
from pathlib import Path

from sample_e2_05_raw_visual_index import (
    EXPECTED_FFPROBE_SHA256,
    EXPECTED_LINK_SHA256,
    EXPECTED_RAW_SHA256,
    pinned_source,
    probe_video_pts,
    seek_text,
    sha256,
)


LINK = Path("D:/workspace/ck3_native_war_ai_promo_work/e2-05-a02-postrun-audit-20260929-a01/postrun-links.json")
PROBE = Path("D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-d26-live-20260929-a02/recording-e2-05-d26-a01/ffprobe.json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--around", type=Decimal, required=True)
    parser.add_argument("--neighbors", type=int, default=5)
    args = parser.parse_args()
    if args.neighbors < 1 or args.neighbors > 20:
        parser.error("neighbors must be in [1, 20]")
    around = Decimal(seek_text(args.around))
    if sha256(LINK) != EXPECTED_LINK_SHA256:
        raise ValueError("frozen E2-05 a02 postrun link changed")
    links = json.loads(LINK.read_text(encoding="utf-8"))
    if links.get("result") != "MEDIA_PTS_CANDIDATE_UNREVIEWED":
        raise ValueError("frozen E2-05 a02 link status changed")
    if links["raw_from_prior_full_sha_audit"]["sha256"] != EXPECTED_RAW_SHA256 or \
            links["ffprobe_from_prior_full_sha_audit"]["sha256"] != EXPECTED_FFPROBE_SHA256:
        raise ValueError("frozen link source identity changed")
    probe = PROBE.resolve(strict=True)
    pinned_source(probe, links["ffprobe_from_prior_full_sha_audit"],
                  links["ffprobe_stat_during_link_audit"])
    if sha256(probe) != EXPECTED_FFPROBE_SHA256:
        raise ValueError("frozen ffprobe bytes changed")
    values, strings = probe_video_pts(probe)
    pinned_source(probe, links["ffprobe_from_prior_full_sha_audit"],
                  links["ffprobe_stat_during_link_audit"])
    center = bisect.bisect_left(values, around)
    start = max(0, center - args.neighbors)
    stop = min(len(values), center + args.neighbors + 1)
    print(json.dumps({
        "status": "FROZEN_PTS_NAVIGATION_ONLY",
        "postrun_link_sha256": EXPECTED_LINK_SHA256,
        "raw_sha256_from_frozen_link": EXPECTED_RAW_SHA256,
        "ffprobe_sha256": EXPECTED_FFPROBE_SHA256,
        "around_seconds": seek_text(around),
        "video_frame_count": len(values),
        "frames": [{"video_frame_index": index, "pts_seconds": strings[index]}
                   for index in range(start, stop)],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

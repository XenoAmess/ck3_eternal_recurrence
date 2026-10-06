"""Show local actual producer metadata; never open the external movie."""
from pathlib import Path
import json

def main():
    root = Path(__file__).resolve().parent
    read = lambda p: json.loads((root / p).read_text(encoding="utf-8-sig"))
    delivery = read("results/closed-movie-delivery.original.json")
    picture = read("results/picture-receipt.original.json")
    package = read("pending-review/pending-review-package.original.json")
    samples = read("samples/INDEX.original.json")
    print(json.dumps({"state": "LOCAL_CLOSED_PRODUCER_METADATA_PLAN", "movie_bytes": delivery["movie"]["bytes"], "movie_sha256": delivery["movie"]["sha256"], "actual_coded_frames": picture["duration_frames"], "actual_video_seconds": picture["actual_video_seconds"], "actual_narration_samples_at_24k": picture["actual_PCM_samples"], "actual_scene_count": len(picture["timeline"]), "chapter_count": len(package["chapters"]), "existing_coded_sample_count": len(samples["samples"]), "pending_review_state": package["state"], "whole_audit_in_this_producer_package": False, "OneDrive_in_this_producer_package": False, "external_media_reads": 0, "processes_started": 0, "human_full_1x_review": False, "human_signoff": False}, ensure_ascii=False, indent=2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())

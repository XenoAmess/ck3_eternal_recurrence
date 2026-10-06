"""Write a real pending template using existing final coded samples only.

This is a project API package, not an execution of the review CLI. It reuses
the producer's exact subject binding and does not read movie/PNG contents.
"""
from pathlib import Path
from decimal import Decimal
import datetime
import hashlib
import importlib.metadata
import json
import subprocess
import sys
import urllib.request

from xar_promo.process import CommandSpec
from xar_promo.render import PlannedCommand
from xar_promo.review import ReviewFrame, ReviewPackagePlan, normalize_storyboard_timeline, write_review_template

R = Path(__file__).resolve().parent
O = R / "pending-human-review-existing-a01"
MAX_SMALL = 1024 * 1024
def require(condition, message):
    if not condition:
        raise ValueError(message)
def small_bytes(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), f"Missing ordinary small file: {path}")
    require(path.stat().st_size <= MAX_SMALL, f"Refusing large metadata: {path}")
    return path.read_bytes()
def pin(path):
    payload = small_bytes(path)
    return {"path": str(path), "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
def read(path, expected=None):
    payload = small_bytes(path)
    if expected is not None:
        require(hashlib.sha256(payload).hexdigest() == expected.lower(), f"Metadata hash changed: {path}")
    return json.loads(payload)
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        if isinstance(value, str):
            handle.write(value)
        else:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
def stat_identity(path):
    s = path.stat()
    return {"bytes": s.st_size, "mtime_ns": s.st_mtime_ns, "device": s.st_dev, "file_id": s.st_ino}

def main():
    require(not O.exists(), "Fresh append-only review output is required")
    require(Path(sys.executable).resolve() == Path("D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe").resolve(), "Explicit verified interpreter is required")
    delivery = read(R / "CLOSED-MOVIE-DELIVERY-a01.json", "3ddb222eaabcb8c1db767fdb335b8b98259147abb145a3f4d156f9e7470ab2f3")
    probe = read(Path(delivery["unique_streams_format_bound_probe"]["path"]), delivery["unique_streams_format_bound_probe"]["sha256"])
    picture = read(Path(delivery["producer_receipt"]["path"]), delivery["producer_receipt"]["sha256"])
    index = read(R / "final-coded-samples-a01/INDEX.json", "50d691f2c102c9959f3d7bb4bc39f851f1b3396f085985ed9327e9d65f107c01")
    movie = Path(delivery["movie"]["path"])
    initial_stat = stat_identity(movie)
    subject = delivery["movie"]
    require(initial_stat["bytes"] == subject["bytes"], "Closed movie current size changed")
    for other in [probe["subject"], picture["picture"], index["movie"]]:
        require(other["bytes"] == subject["bytes"] and other["sha256"].lower() == subject["sha256"].lower(), "Existing producer/sample subject bindings differ")
    require(probe["format_version"] == 1 and probe["kind"] == "xar-promo-bound-media-probe", "Existing public bound probe required")
    require(len(picture["timeline"]) == 69 and len(index["samples"]) == 18, "Expected actual 69 scenes / 18 samples")
    require(picture["duration_frames"] == 52074, "Unexpected coded frame grid")
    for label in ["preserve", "validate"]:
        require(read(R / f"formal-preserve-validate-a01/{label}/result.json")["returncode"] == 0, f"Existing formal {label} failed")
    manifest = read(R / "toolchain-run-a01/run-manifest.json")
    require(manifest["signoffs"] == [], "No human signoff should exist")
    found = [a for a in manifest["artifacts"] if a["id"] == "Review01"]
    require(len(found) == 1 and found[0]["bytes"] == subject["bytes"] and found[0]["sha256"].lower() == subject["sha256"].lower(), "Actual native preserved artifact differs")

    O.mkdir()
    # A fresh task admission queries the official latest release, while keeping
    # the original render/run version facts untouched.
    endpoint = "https://api.github.com/repos/XenoAmess/xar_promo_toolchain/releases/latest"
    request = urllib.request.Request(endpoint, headers={"Accept": "application/vnd.github+json", "User-Agent": "CK3-E4-pending-review-existing-samples"})
    with urllib.request.urlopen(request, timeout=30) as response:
        release_payload = response.read(MAX_SMALL + 1)
    require(len(release_payload) <= MAX_SMALL, "Release metadata exceeds small bound")
    release = json.loads(release_payload)
    require(release["draft"] is False and release["prerelease"] is False, "Official production release required")
    version = importlib.metadata.version("xar-promo-toolchain")
    wheel = next(a for a in release["assets"] if a["name"].endswith(".whl"))
    require(version == release["tag_name"].lstrip("v") == "0.2.1", "New formal release needs separate admission")
    require(wheel.get("digest") == "sha256:f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621", "Latest wheel identity changed")
    write(O / "latest-formal-release.raw.json", release_payload.decode("utf-8"))
    probes = []
    for label, args in [("version", ["--version"]), ("top-help", ["--help"]), ("review-help", ["review", "--help"])]:
        argv = [sys.executable, "-B", "-X", "utf8", "-m", "xar_promo", *args]
        result = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", check=False)
        write(O / "toolchain-probes" / f"{label}.stdout.txt", result.stdout)
        write(O / "toolchain-probes" / f"{label}.stderr.txt", result.stderr)
        require(result.returncode == 0, f"Installed CLI admission failed: {label}")
        probes.append({"argv": argv, "returncode": result.returncode, "stdout": pin(O / "toolchain-probes" / f"{label}.stdout.txt"), "stderr": pin(O / "toolchain-probes" / f"{label}.stderr.txt")})
    write(O / "release-admission.json", {"endpoint": endpoint, "queried_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "latest_official_tag": release["tag_name"], "installed_version": version, "wheel_bytes": wheel["size"], "wheel_sha256": wheel["digest"].split(":", 1)[1], "raw_response": pin(O / "latest-formal-release.raw.json"), "actual_help_probes": probes})

    scenes = picture["timeline"]
    expected_start = 0
    chapter_rows = []
    for row in scenes:
        require(row["actual_start_frame"] == expected_start, f"Noncontiguous actual scene: {row['cue_id']}")
        require(row["actual_end_frame"] - row["actual_start_frame"] == row["duration_frames"], "Actual scene duration mismatch")
        expected_start = row["actual_end_frame"]
        chapter_id = row["cue_id"].split("-", 1)[0]
        if not chapter_rows or chapter_rows[-1]["id"] != chapter_id:
            chapter_rows.append({"id": chapter_id, "start_seconds": str(Decimal(row["actual_start_frame"]) / 30), "end_seconds": str(Decimal(row["actual_end_frame"]) / 30)})
        else:
            chapter_rows[-1]["end_seconds"] = str(Decimal(row["actual_end_frame"]) / 30)
    require(expected_start == 52074 and len(chapter_rows) == 6, "Whole scene/chapter clock mismatch")
    chapters, unused_boundaries = normalize_storyboard_timeline({"chapters": chapter_rows}, duration_seconds=1735.8)
    require(unused_boundaries == (), "No invented cut-boundary evidence")
    streams = probe["ffprobe"]["streams"]
    videos = [s for s in streams if s["codec_type"] == "video"]
    audios = [s for s in streams if s["codec_type"] == "audio"]
    require(len(videos) == 1 and len(audios) == 1, "Actual stream layout differs")
    artifact = {**subject, "duration_seconds": "1735.800000", "container": probe["ffprobe"]["format"]["format_name"], "resolution": {"width": videos[0]["width"], "height": videos[0]["height"]}, "video_tracks": [{"index": v["index"], "codec": v["codec_name"], "width": v["width"], "height": v["height"], "average_frame_rate": v["avg_frame_rate"]} for v in videos], "audio_tracks": [{"index": a["index"], "codec": a["codec_name"], "sample_rate": int(a["sample_rate"]), "channels": a["channels"]} for a in audios], "subtitle_tracks": []}
    frames = []
    package_rows = []
    for sample in index["samples"]:
        png = Path(sample["PNG"]["path"])
        require(png.is_file() and png.stat().st_size == sample["PNG"]["bytes"], f"Existing PNG size changed: {png}")
        require(sample["actual_video_pts"] == sample["frame_zero_based"] * 1600 and sample["time_base"] == "1/48000", "Existing sample integer clock differs")
        audit_directory = Path(sample["command_audit"])
        command = read(audit_directory / "command.json")
        result = read(audit_directory / "result.json")
        require(result["returncode"] == 0 and result["status"] == "succeeded", "Existing actual PNG extraction failed")
        spec = CommandSpec.create(command["argv"], label=command["label"], cwd=Path(command["cwd"]), partial_artifacts=[Path(p) for p in command["partial_artifacts"]])
        chapter_id = sample["label"].split("-", 1)[0]
        owned = (chapter_id,) if chapter_id in {c.chapter_id for c in chapters} else ()
        frame = ReviewFrame(sample["label"], Decimal(sample["frame_zero_based"]) / 30, (sample["scope"],), owned, png, png, PlannedCommand(spec, audit_directory))
        frames.append(frame)
        package_rows.append({**frame.to_dict(), "PNG_binding_from_actual_producer": sample["PNG"], "actual_video_pts": sample["actual_video_pts"], "time_base": sample["time_base"], "command": pin(audit_directory / "command.json"), "actual_command_result": pin(audit_directory / "result.json"), "extraction_repeated": False, "sample_image_content_rehashed": False})
    checklist = tuple([{"id": "watch-complete-at-1x", "required": True, "state": "pending", "instruction": "Watch and listen continuously at exactly 1.0x from 0 through 1735.800000 seconds, without skipping or scrubbing."}, {"id": "verify-picture-sound-subtitles", "required": True, "state": "pending", "instruction": "Confirm picture and sound remain present and synchronized, and Chinese/English subtitles plus A/B/C/source labels stay readable for the full movie."}, {"id": "verify-entry-exit", "required": True, "state": "pending", "instruction": "Inspect the actual opening during playback and the actual final coded frame. Existing samples do not include coded frame zero."}] + [{"id": f"watch-{c.chapter_id}", "chapter_id": c.chapter_id, "required": True, "state": "pending", "instruction": "Watch and listen to the entire chapter and compare its 69-scene timeline and evidence limits."} for c in chapters])
    template = {"format_version": 1, "kind": "xar-promo-human-review-template", "state": "pending-human-review", "template_only": True, "is_signoff": False, "approval_granted": False, "artifact": artifact, "timeline": {"chapters": [c.to_dict() for c in chapters]}, "full_watch": {"required_playback_speed": 1.0, "no_skipping": True, "checklist": list(checklist)}, "frame_evidence": [f.to_dict() for f in frames], "human_response": {"reviewer": None, "reviewed_at": None, "decision": None, "notes": None, "checklist_results": {}}, "binding_provenance": {"movie_subject": "Existing actual producer public bound media probe + preserved native artifact; no new whole-movie hash", "sample_images": "Existing 18 actual MP4 coded PNGs / original integer PTS / extraction command rc 0", "is_review_CLI_execution": False, "is_first_and_all_boundary_frame_package": False}}
    plan = ReviewPackagePlan(artifact, chapters, checklist, tuple(frames), template)
    template_path = write_review_template(O / "human-review-template.json", plan)
    write(O / "pending-review-package.json", {"schema": "xar.e04.pending-human-review-existing-coded-samples.v1", "state": "pending-human-review", "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "public_template_API": "xar_promo.review.write_review_template", "is_review_CLI_execution": False, "is_signoff": False, "approval_granted": False, "human_full_1x_review": False, "human_signoff": False, "artifact": artifact, "existing_native_preserved_artifact": found[0], "template": pin(template_path), "chapters": [c.to_dict() for c in chapters], "complete_scene_metadata": delivery["producer_receipt"], "coded_sample_index": pin(R / "final-coded-samples-a01/INDEX.json"), "existing_frames": package_rows, "formal_preserve_result": pin(R / "formal-preserve-validate-a01/preserve/result.json"), "formal_authoring_validate_result_before_this_review_package": pin(R / "formal-preserve-validate-a01/validate/result.json"), "native_run_manifest_snapshot": pin(R / "toolchain-run-a01/run-manifest.json"), "template_and_samples_registered_in_native_run": False, "new_whole_media_hashes": 0, "new_media_probes": 0, "new_extraction_commands": 0, "new_movie_or_image_content_reads": 0, "source_movie_current_stat": initial_stat, "whole_decode_audit_is_separate": True, "OneDrive_operations": 0})
    require(stat_identity(movie) == initial_stat, "Movie metadata changed during package creation")
    write(O / "ROOT-DELIVERY.json", {"schema": "xar.e04.pending-review-existing-samples-delivery.v1", "state": "PENDING_HUMAN_REVIEW_PACKAGE_CREATED_NO_SIGNOFF", "package": pin(O / "pending-review-package.json"), "template": pin(template_path), "release_admission": pin(O / "release-admission.json"), "movie": subject, "actual_scene_count": 69, "chapter_count": 6, "existing_sample_count": 18, "public_template_API_returned": True, "human_full_1x_review": False, "human_signoff": False, "new_large_media_reads": 0, "OneDrive_operations": 0, "Git_operations": 0})
    print(json.dumps(pin(O / "ROOT-DELIVERY.json"), ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

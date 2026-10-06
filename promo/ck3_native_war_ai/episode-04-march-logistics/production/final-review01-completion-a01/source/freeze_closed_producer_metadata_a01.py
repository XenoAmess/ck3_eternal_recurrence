"""Copy exact small closed-producer facts into a new text-only addon."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil

R = Path(__file__).resolve().parent
O = R / "portable-producer-completion-a01"
P = O / "promo/ck3_native_war_ai/episode-04-march-logistics/production/final-review01-completion-a01"
MAX_SMALL = 1024 * 1024
SUFFIXES = {".json", ".md", ".py", ".txt", ".patch"}
def require(condition, message):
    if not condition:
        raise ValueError(message)
def pin(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), f"Ordinary small file required: {path}")
    require(path.suffix.lower() in SUFFIXES and path.stat().st_size <= MAX_SMALL, f"Only small text allowed: {path}")
    payload = path.read_bytes()
    payload.decode("utf-8-sig")
    return {"path": str(path), "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
def read(path):
    pin(path)
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        if isinstance(value, str):
            handle.write(value)
        else:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
def main():
    require(not O.exists(), "Fresh append-only producer addon required")
    movie_delivery = read(R / "CLOSED-MOVIE-DELIVERY-a01.json")
    pending_delivery = read(R / "pending-human-review-existing-a01/ROOT-DELIVERY.json")
    subject = movie_delivery["movie"]
    require(subject["bytes"] == 1199061934 and subject["sha256"].lower() == "a1abb0f2abaa06f3fd38839123e9f4ddd4c4218f8dd15e0965732d3596c69346", "Unexpected final Review01 subject")
    require(pending_delivery["movie"]["sha256"].lower() == subject["sha256"].lower(), "Pending review binds a different movie")
    require(read(R / "execution-a01/actual-render/result.json")["returncode"] == 0, "Actual render result must be rc 0")
    for phase in ["preserve", "validate"]:
        require(read(R / "formal-preserve-validate-a01" / phase / "result.json")["returncode"] == 0, f"Actual formal {phase} result must be rc 0")
    template = read(R / "pending-human-review-existing-a01/human-review-template.json")
    require(template["state"] == "pending-human-review" and template["approval_granted"] is False and template["human_response"]["decision"] is None, "Actual pending template must contain no decision")
    P.mkdir(parents=True)
    copies = {
        "results/closed-movie-delivery.original.json": R / "CLOSED-MOVIE-DELIVERY-a01.json",
        "results/picture-bound-probe.original.json": R / "actual-render-a01/picture.bound-probe.json",
        "results/picture-receipt.original.json": R / "actual-render-a01/picture-receipt.json",
        "inputs/actual-input-snapshot.original.json": R / "actual-render-a01/input-snapshot.json",
        "inputs/Root-final-story-freeze.original.json": Path(movie_delivery["Root_actual_story_freeze"]["path"]),
        "formal/native-run-manifest.original.json": R / "toolchain-run-a01/run-manifest.json",
        "pending-review/pending-review-package.original.json": R / "pending-human-review-existing-a01/pending-review-package.json",
        "pending-review/human-review-template.original.json": R / "pending-human-review-existing-a01/human-review-template.json",
        "pending-review/ROOT-DELIVERY.original.json": R / "pending-human-review-existing-a01/ROOT-DELIVERY.json",
        "pending-review/release-admission.original.json": R / "pending-human-review-existing-a01/release-admission.json",
        "pending-review/latest-formal-release.raw.original.json": R / "pending-human-review-existing-a01/latest-formal-release.raw.json",
        "samples/INDEX.original.json": R / "final-coded-samples-a01/INDEX.json",
        "source/build_pending_existing_review_a01.py": R / "build_pending_existing_review_a01.py",
        "source/freeze_closed_producer_metadata_a01.py": Path(__file__).resolve(),
        "verify_package.py": R / "producer-completion-source-a01/verify_package.py",
        "plan_metadata.py": R / "producer-completion-source-a01/plan_metadata.py",
    }
    for filename in ["command.json", "stdout.txt", "stderr.txt", "result.json"]:
        for prefix in ["final-encode-command-audit"]:
            source = R / "actual-render-a01" / prefix / filename
            if source.exists():
                copies[f"encode/{filename}"] = source
        source = R / "execution-a01/actual-render" / ("argv.json" if filename == "command.json" else filename)
        if source.exists():
            copies[f"execution/{source.name}"] = source
        for phase in ["preserve", "validate"]:
            source = R / "formal-preserve-validate-a01" / phase / ("argv.json" if filename == "command.json" else filename)
            if source.exists():
                copies[f"formal/{phase}/{source.name}"] = source
    for source in sorted((R / "pending-human-review-existing-a01/toolchain-probes").iterdir()):
        if source.is_file():
            copies[f"pending-review/toolchain-probes/{source.name}"] = source
    index = read(R / "final-coded-samples-a01/INDEX.json")
    require(len(index["samples"]) == 18, "Unexpected existing sample count")
    for sample in index["samples"]:
        for filename in ["command.json", "result.json", "stdout.txt", "stderr.txt"]:
            source = Path(sample["command_audit"]) / filename
            require(source.is_file(), f"Missing real sample audit: {source}")
            copies[f"samples/commands/{sample['label']}/{filename}"] = source
    sources = []
    for relative, source in copies.items():
        original = pin(source)
        target = P / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        require(not target.exists(), f"Refusing overwrite: {target}")
        shutil.copyfile(source, target)
        copied = pin(target)
        require(original["bytes"] == copied["bytes"] and original["sha256"] == copied["sha256"], f"Copy changed exact source: {relative}")
        sources.append({"relative": relative, "original_source": original, "copied_exact": True})
    picture = read(P / "results/picture-receipt.original.json")
    require(picture["duration_frames"] == 52074 and len(picture["timeline"]) == 69 and picture["actual_PCM_samples"] == 41658624, "Actual scene / sample clock changed")
    write(P / "results/closed-producer-state.json", {"schema": "xar.e04.closed-producer-facts-only.v1", "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "movie": subject, "actual_render_returncode": 0, "actual_preserve_returncode": 0, "actual_authoring_validate_returncode": 0, "actual_video_frames": picture["duration_frames"], "actual_video_seconds": picture["actual_video_seconds"], "actual_narration_samples_at_24k": picture["actual_PCM_samples"], "actual_narration_seconds": picture["actual_PCM_seconds"], "actual_scene_count": len(picture["timeline"]), "chapter_count": pending_delivery["chapter_count"], "pending_human_review_package_created": True, "public_template_API": "xar_promo.review.write_review_template", "review_CLI_executed": False, "existing_coded_sample_count": 18, "new_media_probe_or_hash_or_extraction": 0, "whole_movie_audit": None, "whole_movie_audit_scope": "Separate auditor-owned actual receipt; not included or assessed by this producer package", "Root_final_coded_pixel_review": "Separate Root receipt; not included or assessed by this producer package", "OneDrive_client_state": None, "OneDrive_scope": "Separate Root-owned actual client receipt; not included or assessed by this producer package", "human_full_1x_review": False, "human_signoff": False, "independent_remote_readback": False, "old_running_picture_package_remains_unchanged": True})
    write(P / "README.md", """# Episode04 actual closed Review01 producer metadata

This immutable addon records the actual completed 28:55.80 Review01 producer attempt: 52,074 coded frames, 69 scenes in six chapters, 41,658,624 source narration samples at 24 kHz, the exact closed movie subject, public bound streams/format probe, real encode argv/stdios, and actual native preserve / authoring validation rc 0. The complete 69-scene original producer receipt retains all source-window metadata and honest historical NULL / RED / preview fields byte-for-byte.

`python verify_package.py` checks only relative UTF-8 text bytes, safe paths, common exact movie subject bindings and the pending-review boundary. `python plan_metadata.py` prints the local actual metadata. Both require only the Python standard library and neither starts media, game, desktop, network, Git or upload processes. Historical absolute locators inside original receipts remain provenance; the consumer never follows them.

The pending human review template was actually written by the installed public `xar_promo.review.write_review_template` API using the original exact movie binding and 18 existing coded PNG / successful command results. It is a project API package reusing existing frames. The review CLI was not run, frames were not extracted again, and movie or PNG contents were not hashed again. This sample set is not the CLI first-frame / all-boundary frame set; first-frame inspection remains part of pending full playback. No PNG or other media bytes enter this package. The template and frame references were not registered as native run artifacts; the original real movie preserve and validation receipts are retained separately and their completed state is not reinterpreted.

Whole video / AAC decode and integer timestamps, Root actual coded sample inspection, OneDrive local copy / client sync and final Git CI are separate actual evidence owners. They are intentionally not assessed here. Human full 1x watch/listen and signoff remain pending. There is no independent remote cloud byte readback. Original failures, the old A AAC exact-PTS RED, and the earlier running package with movie NULL remain unchanged.
""")
    files = []
    for path in sorted(P.rglob("*")):
        if path.is_file():
            identity = pin(path)
            files.append({"relative": path.relative_to(P).as_posix(), "bytes": identity["bytes"], "sha256": identity["sha256"]})
    write(P / "manifest.json", {"schema": "xar.e04.closed-producer-small-relative-manifest.v1", "files": files, "source_copies": sources, "large_media_included": False, "human_signoff": False})
    catalog = []
    for path in sorted(P.rglob("*")):
        if path.is_file():
            catalog.append({"repo_relative": path.relative_to(O).as_posix(), "source": pin(path)})
    write(O / "CATALOG.json", {"schema": "xar.e04.closed-producer-Git-catalog.v1", "files": catalog, "text_only": True, "max_single_file_bytes": MAX_SMALL, "large_media_included": False})
    write(O / "ROOT-DELIVERY.json", {"schema": "xar.e04.closed-producer-portable-delivery.v1", "source_root": str(O), "package_root": str(P), "catalog": pin(O / "CATALOG.json"), "manifest": pin(P / "manifest.json"), "files": len(catalog), "total_text_bytes": sum(c["source"]["bytes"] for c in catalog), "movie": subject, "actual_video_frames": 52074, "actual_video_seconds": 1735.8, "pending_human_review": True, "human_full_1x_review": False, "human_signoff": False, "whole_audit_and_OneDrive_not_assessed_in_this_package": True, "large_media_reads": 0, "Git_operations": 0, "verify_argv": ["python", "-O", str(P / "verify_package.py")], "default_plan_argv": ["python", str(P / "plan_metadata.py")]})
    print(json.dumps(pin(O / "ROOT-DELIVERY.json"), ensure_ascii=False))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())

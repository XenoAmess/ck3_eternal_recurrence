"""Invoke the real xar-promo lifecycle for a fresh, retained film attempt."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import math
import os
from pathlib import Path
import shutil
import sys
import zipfile
from copy import deepcopy

from xar_promo.media import probe_and_write_bound_media
from xar_promo.model import RunManifest
from xar_promo.process import CommandSpec, run_command

from .common import binding, load, verify, write_new
from .finalize import add_chapters
from .capture_media import load_capture_spec, prepare_capture_clip
from .capture_overlay import label_capture_clip


def archive_capture_attempt(attempt, archive):
    """Bind the complete attempt tree in one immutable lifecycle artifact.

    Each adapter control remains present at its original relative path in this
    archive and in the retained workdir. A large bundle can contain hundreds
    of controls, so one archive avoids hundreds of manifest rewrites while
    preserving their individual hashes in control-index.json and the receipt.
    """
    attempt, archive = Path(attempt), Path(archive)
    if archive.exists():
        raise FileExistsError(archive)
    files = sorted(path for path in attempt.rglob("*") if path.is_file())
    if not files:
        raise ValueError("Cannot archive an empty capture attempt")
    with zipfile.ZipFile(archive, mode="x", compression=zipfile.ZIP_STORED,
                         allowZip64=True) as target:
        for path in files:
            relative = path.relative_to(attempt).as_posix()
            entry = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_STORED
            entry.external_attr = 0o100644 << 16
            with path.open("rb") as source, target.open(entry, "w", force_zip64=True) as sink:
                shutil.copyfileobj(source, sink, 1024 * 1024)
    with zipfile.ZipFile(archive) as source:
        if source.testzip() is not None or source.namelist() != [
                path.relative_to(attempt).as_posix() for path in files]:
            raise ValueError(f"Capture attempt archive failed readback: {archive}")
    return archive


def prepare_captures(inputs, spec_path, root, preserve, *, ffmpeg="ffmpeg", ffprobe="ffprobe"):
    """Prepare, preserve and map selected footage before freezing run inputs.

    ``preserve(path, identifier, role, collection)`` is the real lifecycle hook
    supplied by main. Failed preparations retain and preserve their audit tree.
    """
    result = deepcopy(inputs)
    rows = {row["id"]: row for row in result["cues"]}
    if len(rows) != len(result["cues"]) or any("capture_clip" in row for row in rows.values()):
        raise ValueError("Expected unique, not-yet-mapped narration cues")
    specs = load_capture_spec(spec_path)
    v3 = "v3_visuals" in result
    for spec in specs:
        if spec["cue_id"] not in rows:
            raise ValueError(f"Capture spec names unknown cue: {spec['cue_id']}")
        if not set(spec["claim_ids"]).issubset(rows[spec["cue_id"]]["claim_ids"]):
            raise ValueError(f"Capture spec claims differ from cue: {spec['cue_id']}")
    preserve(spec_path, "capture-selection-spec-v1", "capture-selection-spec", "raw")
    preserved = {}

    def keep(path, prefix, role, collection="raw"):
        path = Path(path).resolve()
        if path in preserved:
            return preserved[path]
        record = binding(path)
        identifier = prefix + record["sha256"]
        # Shared raw and identical controls need one lifecycle artifact each.
        if identifier not in preserved.values():
            preserve(path, identifier, role, collection)
        preserved[path] = identifier
        return identifier

    for index, spec in enumerate(specs, 1):
        attempt = Path(root) / "capture" / f"{index:03d}"
        archive = attempt.with_name(attempt.name + "-process.zip")
        succeeded = False
        try:
            prepared = prepare_capture_clip(spec, attempt / "clip.mp4", ffmpeg, ffprobe, attempt / "audit")
            if v3:
                case_id = {"case-w-bundle-r1": "CASE-W", "case-c-bundle-r2": "CASE-C"}.get(
                    Path(spec["bundle_root"]).name)
                if case_id is None or spec["evidence_role"] != "context":
                    raise ValueError("V3 accepts only reviewed CASE-W/C context clips")
                prepared = label_capture_clip(prepared, case_id=case_id, cue_id=spec["cue_id"],
                                              output_root=attempt / "context-label", ffmpeg=ffmpeg,
                                              ffprobe=ffprobe)
            raw_id = keep(prepared["source_recording"]["path"], "capture-raw-", "capture-original-recording")
            media_id = keep(prepared["media"]["path"], "capture-clip-", "capture-continuous-clip", "derived")
            receipt_id = keep(prepared["receipt"]["path"], "capture-receipt-", "capture-clip-receipt", "derived")
            row = rows[spec["cue_id"]]
            original_duration = row["duration_seconds"]
            duration = prepared["selection"]["expected_frame_count"] / 30
            if (not all(math.isfinite(value) and value > 0 for value in
                        (duration, original_duration, row["speech_duration_seconds"]))
                    or abs(duration - original_duration) > 1 / 30 + 0.000001
                    or duration < row["speech_duration_seconds"]):
                raise ValueError(f"Capture/narration duration conflict for {row['id']}: "
                                 f"clip={duration}, segment={original_duration}, speech={row['speech_duration_seconds']}; "
                                 "reselect footage or revise narration; no looping, freeze-frame or retiming")
            row["duration_seconds"] = duration
            row["capture_clip"] = {
                "media_artifact_id":media_id, "receipt_artifact_id":receipt_id,
                "raw_artifact_id":raw_id, "control_artifact_ids":[],
                "claim_ids":list(spec["claim_ids"]), "evidence_role":spec["evidence_role"],
                "span_id":spec["span_id"], "duration_seconds":duration,
                "probed_media_duration_seconds":prepared["duration_seconds"],
                "original_segment_duration_seconds":original_duration,
                "alignment":"real-clip-full-frames; at-most-one-frame adjustment; full speech retained",
                "native_ai_causality_verified":False,
            }
            succeeded = True
        except Exception as error:
            write_new(attempt / "integration-failure.json", {
                "cue_id":spec["cue_id"], "status":"failed-retained", "error":str(error),
                "native_ai_causality_verified":False,
            })
            raise
        finally:
            if attempt.exists():
                # The receipt records each control hash; this archive retains
                # their exact bytes and every preparation/audit process file.
                archive_id = keep(archive_capture_attempt(attempt, archive),
                                  "capture-process-", "capture-complete-process-archive", "derived")
                if succeeded:
                    row["capture_clip"]["control_artifact_ids"] = [archive_id]
    result["media_scope"] = "mixed-footage"
    result["capture_selection_artifact_id"] = "capture-selection-spec-v1"
    result["capture_cue_count"] = len(specs)
    result["actual_duration_seconds"] = sum(row["duration_seconds"] for row in rows.values())
    return result


def reuse_prepared_captures(inputs, spec_path, source_run_root, root, preserve, validate_source):
    """Copy byte-verified capture artifacts into a fresh run after a later phase fails.

    The earlier run is only an immutable input; its failed status is untouched.
    No media preparation or approval is inferred by this import.
    """
    source_root = Path(source_run_root).resolve()
    source_manifest = source_root / "run" / "run-manifest.json"
    validate_source(source_manifest)
    previous = RunManifest.from_mapping(load(source_manifest))
    artifacts = {record.artifact_id: record for record in previous.artifacts}
    if len(artifacts) != len(previous.artifacts):
        raise ValueError("Source run repeats an artifact identifier")

    def old_artifact(identifier):
        record = artifacts.get(identifier)
        if record is None:
            raise ValueError(f"Source run lacks capture artifact: {identifier}")
        return source_manifest.parent / record.path, record

    selected_path, _ = old_artifact("production-inputs-v1")
    selected = load(selected_path)
    old_spec_path, _ = old_artifact("capture-selection-spec-v1")
    if any(binding(old_spec_path)[key] != binding(spec_path)[key] for key in ("bytes", "sha256")):
        raise ValueError("Capture selection changed since the source run")
    original = deepcopy(selected)
    if (original.get("capture_cue_count") != len(load_capture_spec(spec_path))
            or original.get("media_scope") != "mixed-footage"):
        raise ValueError("Source run does not have the complete requested capture selection")
    capture_ids = []
    for row in original["cues"]:
        capture = row.pop("capture_clip", None)
        if capture is not None:
            if (capture.get("claim_ids") != row["claim_ids"]
                    or capture.get("native_ai_causality_verified") is not False
                    or not capture.get("control_artifact_ids")):
                raise ValueError(f"Source capture binding is incomplete: {row['id']}")
            row["duration_seconds"] = capture["original_segment_duration_seconds"]
            capture_ids.extend([capture["raw_artifact_id"],
                                *capture["control_artifact_ids"],
                                capture["media_artifact_id"], capture["receipt_artifact_id"]])
    if len([row for row in selected["cues"] if "capture_clip" in row]) != original["capture_cue_count"]:
        raise ValueError("Source run capture count differs from selected rows")
    original["media_scope"] = inputs["media_scope"]
    original["actual_duration_seconds"] = inputs["actual_duration_seconds"]
    for key in ("capture_selection_artifact_id", "capture_cue_count", "director_artifact_id"):
        original.pop(key, None)
    if original != inputs:
        raise ValueError("Source captures were selected for different narration or visual inputs")

    preserve(spec_path, "capture-selection-spec-v1", "capture-selection-spec", "raw")
    for identifier in dict.fromkeys(capture_ids):
        path, record = old_artifact(identifier)
        preserve(path, identifier, record.role, record.collection)
    receipt = Path(root) / "capture-reuse-source.json"
    write_new(receipt, {"schema":"ck3-war-ai.capture-reuse-source.v1",
                        "source_run_id":previous.run_id,
                        "source_run_manifest":binding(source_manifest),
                        "source_selected_inputs":binding(selected_path),
                        "capture_selection":binding(spec_path),
                        "copied_artifact_ids":list(dict.fromkeys(capture_ids)),
                        "scope":"byte-verified-prepared-captures-only; failed source run unchanged; no human signoff"})
    preserve(receipt, "capture-reuse-source-v1", "capture-reuse-provenance", "raw")
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--capture-spec", type=Path, help="Existing GREEN capture bundles and cue selections; prepare and preserve continuous clips")
    parser.add_argument("--reuse-captures-from", type=Path,
                        help="Import already verified capture artifacts from a retained failed run into this new run")
    parser.add_argument("--v3-assets", type=Path, help="Hash-bound CASE-R/W original frame context manifest for V3")
    parser.add_argument("--full-film", action="store_true", help="Require all configured chapters and render the complete review film")
    args = parser.parse_args()
    args.project = args.project.resolve()
    args.inputs = args.inputs.resolve()
    root = args.run_root.resolve()
    root.mkdir(parents=True, exist_ok=False)
    log = root / "commands"
    manifest = root / "run" / "run-manifest.json"
    config_path = root / "selected-project.json"
    workdir = root / "build"
    calls = []

    def command(argv):
        command_root = log / f"{len(calls) + 1:03d}"
        result = run_command(CommandSpec.create(argv, label="war-film-production", cwd=args.project), audit_directory=command_root)
        calls.append(str(command_root))
        if result.returncode:
            raise RuntimeError(f"Production phase failed; retained {command_root}")
        return result.stdout

    def cli(*argv):
        return command([sys.executable, "-m", "xar_promo", *map(str, argv)])

    def validate():
        cli("validate", config_path, "--json")
        cli("validate", manifest, "--json")

    def preserve(path, artifact_id, role, collection="raw", *, check=True):
        cli("preserve", path, "--run-manifest", manifest, "--artifact-id", artifact_id,
            "--collection", collection, "--role", role)
        if check:
            validate()

    release = json.loads(command(["gh", "release", "view", "--repo", "XenoAmess/xar_promo_toolchain", "--json", "tagName,isDraft,isPrerelease,url"]))
    version = importlib.metadata.version("xar-promo-toolchain")
    if release["isDraft"] or release["isPrerelease"] or version != release["tagName"].removeprefix("v"):
        raise ValueError("Install the latest stable xar-promo before creating this run")
    for sub in [None, "start-run", "preserve", "validate", "plan", "build", "review"]:
        cli(*(([sub] if sub else []) + ["--help"]))
    inputs = load(args.inputs)
    rows = inputs["cues"]
    v3 = len(rows) == 45 and all(row["id"] == f"V3-{index:02d}" and row["shot_id"] == f"S3-{index:02d}"
                                   for index, row in enumerate(rows, 1))
    if any(str(row["id"]).startswith("V3-") for row in rows) and not v3:
        raise ValueError("V3 production requires all 45 bound cues in order")
    if v3 != bool(args.v3_assets):
        raise ValueError("V3 production requires --v3-assets; older cuts do not accept it")
    if args.reuse_captures_from and (not v3 or not args.capture_spec):
        raise ValueError("Capture reuse requires a V3 attempt and its exact capture spec")
    selected = {row["chapter_id"] for row in rows}
    config = load(args.project / "promo-project.json")
    if args.full_film:
        if selected != {chapter["id"] for chapter in config["chapters"]}:
            raise ValueError("A full film must contain every configured chapter")
        # 20–40 minutes is editorial guidance, not a newly imposed hard limit.
        if not all(math.isfinite(row["duration_seconds"]) and row["duration_seconds"] > 0 for row in rows):
            raise ValueError("A full film requires positive finite measured cue durations")
        inputs["full_film"] = True
    selected_inputs = root / "selected-production-inputs.json"
    config["chapters"] = [chapter for chapter in config["chapters"] if chapter["id"] in selected]
    if selected != {row["id"] for row in config["chapters"]}:
        raise ValueError("Unknown selected chapter")
    write_new(config_path, config)
    cli("validate", config_path, "--json")
    cli("start-run", config_path, "--run-id", args.run_id, "--run-directory", manifest.parent)
    validate()
    preserve(args.inputs, "narration-production-source-v1", "measured-narration-inputs")
    for row in rows:
        preserve(verify(row["audio"]), row["audio_artifact_id"], "narration-source")
    project_sources = [
        ("source-lock.json", "film-source-lock-v1", "source-lock"),
        ("longform/director-plan-v3.md", "film-director-v3", "director-plan"),
    ]
    if not v3:
        project_sources.extend([
            ("claims.json", "film-claims-v1", "claim-plan"),
            ("research-first-claim-ledger-20260923.json", "film-claim-ledger-v1", "claim-ledger"),
        ])
    for name, identifier, role in project_sources:
        preserve(args.project / name, identifier, role)
    for path in sorted((args.project / "integration/src/war_ai_promo").glob("*.py")):
        preserve(path, "producer-" + path.stem, "project-producer")
    if v3:
        ledger = args.project / "longform/v3/evidence-visual-ledger.json"
        if binding(ledger)["sha256"] != inputs["v3_evidence_ledger"]["sha256"]:
            raise ValueError("V3 bound narration and current evidence ledger differ")
        preserve(ledger, "v3-evidence-ledger-v1", "evidence-claim-and-visual-ledger")
        preserve(args.project / "longform/v3/visual-bindings-plan.json", "v3-visual-plan-v1", "editorial-visual-plan")
        frame_manifest = args.v3_assets.resolve()
        frames = load(frame_manifest)
        if frames.get("schema") != "ck3-war-ai.v3-context-frames.v1" or set(frames["assets"]) != {"CASE-R", "CASE-W"}:
            raise ValueError("V3 context manifest must bind exact CASE-R and CASE-W original frames")
        preserve(frame_manifest, "v3-frame-manifest-v1", "original-frame-manifest")
        frame_ids = {}
        for case_id, frame in frames["assets"].items():
            source = Path(frame["path"])
            actual = binding(source)
            if (frame.get("case_id") != case_id or frame.get("evidence_role") != "context-only-original-frame"
                    or any(frame.get(key) != actual[key] for key in ("bytes", "sha256"))):
                raise ValueError(f"V3 original frame binding changed: {case_id}")
            identifier = "v3-original-frame-" + case_id
            preserve(source, identifier, "original-ck3-context-frame")
            frame_ids[case_id] = identifier
        inputs["v3_visuals"] = {"ledger_artifact_id": "v3-evidence-ledger-v1",
                                "asset_manifest_artifact_id": "v3-frame-manifest-v1",
                                "frame_artifact_ids": frame_ids}
    if args.capture_spec:
        if args.reuse_captures_from:
            inputs = reuse_prepared_captures(inputs, args.capture_spec.resolve(),
                args.reuse_captures_from.resolve(), root,
                lambda path, identifier, role, collection: preserve(path, identifier, role, collection, check=False),
                lambda path: cli("validate", path, "--json"))
        else:
            inputs = prepare_captures(inputs, args.capture_spec.resolve(), root,
                lambda path, identifier, role, collection: preserve(path, identifier, role, collection, check=False),
                ffmpeg=os.environ.get("WAR_PROMO_FFMPEG", "ffmpeg"),
                ffprobe=os.environ.get("WAR_PROMO_FFPROBE", "ffprobe"))
        rows = inputs["cues"]
        validate()
    elif inputs.get("media_scope") != "teaching-graphics-radio-cut":
        raise ValueError("New mixed-footage attempts require --capture-spec")
    inputs["director_artifact_id"] = "film-director-v3"
    write_new(selected_inputs, inputs)
    preserve(selected_inputs, "production-inputs-v1", "measured-production-inputs")
    cli("plan", manifest, "--workdir", workdir, "--composer", "war_ai_promo.composer:compose")
    if workdir.exists():
        raise ValueError("Read-only plan unexpectedly created the build directory")
    validate()
    print("Native plan GREEN; building complete film" if args.full_film else "Native plan GREEN; building sample", flush=True)
    cli("build", manifest, "--workdir", workdir, "--composer", "war_ai_promo.composer:compose", "--offline-tts")
    validate()
    video = workdir / ("war-ai-full-film.mp4" if args.full_film else "war-ai-radio-cut.mp4")
    if args.full_film:
        chaptered = root / "war-ai-full-film-review.mp4"
        chapter_metadata = add_chapters(video, chaptered, rows, config, audit_directory=root / "chapter-mux-audit")
        preserve(chapter_metadata, "film-chapter-bookmarks-v1", "chapter-metadata", "derived")
        preserve(chaptered, "war-ai-full-film-review-v1", "deliverable", "derived")
        video = chaptered
    bound = root / "video.bound-probe.json"
    probe = probe_and_write_bound_media("ffprobe", video, output_path=bound, audit_directory=root / "probe")
    expected = sum(row["duration_seconds"] for row in rows)
    actual = probe.probe.require_duration()
    if abs(actual - expected) > max(.2, len(rows) / 30):
        raise ValueError(f"Actual duration {actual} differs from measured plan {expected}")
    if len(probe.probe.video_streams) != 1 or len(probe.probe.audio_streams) != 1:
        raise ValueError("Expected exactly one video and one audio stream")
    if (probe.probe.video_streams[0].width, probe.probe.video_streams[0].height) != (2560, 1440):
        raise ValueError("Wrong delivery dimensions")
    cursor = 0.0
    storyboard = []
    for index, row in enumerate(rows):
        end = cursor + row["duration_seconds"]
        if not storyboard or storyboard[-1]["id"] != row["chapter_id"]:
            storyboard.append({"id": row["chapter_id"], "start_seconds": round(cursor, 6),
                               "end_seconds": 0, "boundary_seconds": []})
        chapter = storyboard[-1]
        chapter["end_seconds"] = round(min(end, actual) if index == len(rows) - 1 else end, 6)
        # Review both states of the final cue in each shot. Actual chapters,
        # rather than individual speech cues, define chapter start/end frames.
        # This is a selected storyboard review, never a full-watch signoff.
        if index == len(rows) - 1 or rows[index + 1]["shot_id"] != row["shot_id"]:
            chapter["boundary_seconds"].append(round(cursor + row["duration_seconds"] / 2, 6))
        cursor = end
    story_path = root / "review-storyboard.json"
    write_new(story_path, {"chapters": storyboard})
    cli("review", video, "--storyboard", story_path, "--probe", bound,
        "--output-directory", root / "review", "--audit-directory", root / "review-audit",
        "--ffmpeg", "ffmpeg", "--plan-only")
    cli("review", video, "--storyboard", story_path, "--probe", bound,
        "--output-directory", root / "review", "--audit-directory", root / "review-audit", "--ffmpeg", "ffmpeg")
    for path, identifier, role in [(bound, "sample-bound-probe", "bound-media-probe"),
                                    (story_path, "sample-review-storyboard", "review-storyboard")]:
        preserve(path, identifier, role, "derived")
    # The native review report hashes each of its 106 frames. Keep the entire
    # review tree on disk, then preserve one byte-verified archive instead of
    # rewriting and validating a large RunManifest for every frame.
    review_archive = archive_capture_attempt(root / "review", root / "review-package-archive.zip")
    preserve(review_archive, "sample-review-bundle", "pending-review-material", "derived")
    write_new(root / "production-receipt.json", {"created_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "rendered-pending-human-review", "run": binding(manifest), "video": binding(video),
              "bound_probe": binding(bound), "actual_duration_seconds": actual, "toolchain": version,
              "latest_release": release, "selected_chapters": sorted(selected), "cue_count": len(rows),
              "provider": inputs["provider"], "media_scope": inputs["media_scope"], "music": "not-yet-added",
              "full_film_rendered": args.full_film, "human_signoff": "not-provided", "commands": calls})
    print(json.dumps({"video": str(video), "seconds": actual, "state": "pending-human-review"}), flush=True)


if __name__ == "__main__":
    main()

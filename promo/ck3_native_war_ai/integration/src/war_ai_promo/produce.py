"""Invoke the real xar-promo lifecycle for a fresh, retained film attempt."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import sys

from xar_promo.media import probe_and_write_bound_media
from xar_promo.process import CommandSpec, run_command

from .common import binding, load, verify, write_new
from .finalize import add_chapters


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
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

    def preserve(path, artifact_id, role, collection="raw"):
        cli("preserve", path, "--run-manifest", manifest, "--artifact-id", artifact_id,
            "--collection", collection, "--role", role)
        validate()

    release = json.loads(command(["gh", "release", "view", "--repo", "XenoAmess/xar_promo_toolchain", "--json", "tagName,isDraft,isPrerelease,url"]))
    version = importlib.metadata.version("xar-promo-toolchain")
    if release["isDraft"] or release["isPrerelease"] or version != release["tagName"].removeprefix("v"):
        raise ValueError("Install the latest stable xar-promo before creating this run")
    for sub in [None, "start-run", "preserve", "validate", "plan", "build", "review"]:
        cli(*(([sub] if sub else []) + ["--help"]))
    inputs = load(args.inputs)
    rows = inputs["cues"]
    selected = {row["chapter_id"] for row in rows}
    config = load(args.project / "promo-project.json")
    if args.full_film:
        if selected != {chapter["id"] for chapter in config["chapters"]}:
            raise ValueError("A full film must contain every configured chapter")
        if not 1200 <= sum(row["duration_seconds"] for row in rows) <= 2400:
            raise ValueError("The requested full film must be between 20 and 40 minutes")
        inputs["full_film"] = True
    selected_inputs = root / "selected-production-inputs.json"
    write_new(selected_inputs, inputs)
    config["chapters"] = [chapter for chapter in config["chapters"] if chapter["id"] in selected]
    if selected != {row["id"] for row in config["chapters"]}:
        raise ValueError("Unknown selected chapter")
    write_new(config_path, config)
    cli("validate", config_path, "--json")
    cli("start-run", config_path, "--run-id", args.run_id, "--run-directory", manifest.parent)
    validate()
    preserve(args.inputs, "narration-production-source-v1", "measured-narration-inputs")
    preserve(selected_inputs, "production-inputs-v1", "measured-production-inputs")
    for row in rows:
        preserve(verify(row["audio"]), row["audio_artifact_id"], "narration-source")
    for name, identifier, role in [
        ("claims.json", "film-claims-v1", "claim-plan"),
        ("source-lock.json", "film-source-lock-v1", "source-lock"),
        ("longform/director-plan.md", "film-director-v2", "director-plan"),
    ]:
        preserve(args.project / name, identifier, role)
    for path in sorted((args.project / "integration/src/war_ai_promo").glob("*.py")):
        preserve(path, "producer-" + path.stem, "project-producer")
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
    for index, path in enumerate(sorted((root / "review").rglob("*"))):
        if path.is_file():
            preserve(path, f"sample-review-{index:03d}", "pending-review-material", "derived")
    write_new(root / "production-receipt.json", {"created_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "rendered-pending-human-review", "run": binding(manifest), "video": binding(video),
              "bound_probe": binding(bound), "actual_duration_seconds": actual, "toolchain": version,
              "latest_release": release, "selected_chapters": sorted(selected), "cue_count": len(rows),
              "provider": inputs["provider"], "media_scope": inputs["media_scope"], "music": "not-yet-added",
              "full_film_rendered": args.full_film, "human_signoff": "not-provided", "commands": calls})
    print(json.dumps({"video": str(video), "seconds": actual, "state": "pending-human-review"}), flush=True)


if __name__ == "__main__":
    main()

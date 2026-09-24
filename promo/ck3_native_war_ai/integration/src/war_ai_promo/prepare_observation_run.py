"""Archive measured Episode 1 narration inputs in a fresh xar-promo run."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from .episode_one_observation import gameplay_overlay


EXPECTED_FOOTAGE_SHA256 = "1BF6FD2E3B35DF5E0B43F8EE7D595422E3BE959F156409A33829133B8F6D9A02"
EXPECTED_THEME_SHA256 = "FDA2464FB4B06CD9A2F0196E5C40CA311EB693EC263C996E4CCC24A6ADA8803F"


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--speech", type=Path, required=True)
    parser.add_argument("--production-inputs", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--toolchain-receipt", type=Path)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--timeline", type=Path, required=True)
    parser.add_argument("--footage", type=Path, required=True)
    parser.add_argument("--visibility-audit", type=Path, required=True)
    parser.add_argument("--theme", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    if not arguments.manifest.is_file():
        raise FileNotFoundError(arguments.manifest)
    if digest(arguments.footage) != EXPECTED_FOOTAGE_SHA256:
        raise ValueError("full-battle footage changed")
    if digest(arguments.theme) != EXPECTED_THEME_SHA256:
        raise ValueError("single series theme changed")
    production = arguments.production_inputs or arguments.speech / "production-inputs.json"
    inputs = json.loads(production.read_text(encoding="utf-8"))
    rows = inputs["cues"]
    provider = inputs["provider"]
    if len(rows) != 25 or provider not in {"edge", "index"}:
        raise ValueError("wrong Episode 1 narration cue set")
    if provider == "index":
        if arguments.reference is None or not arguments.reference.is_file():
            raise ValueError("IndexTTS reference WAV required")
        if digest(arguments.reference) != inputs["index_voice"]["reference"]["sha256"].upper():
            raise ValueError("IndexTTS reference changed")
    if not 1200 <= inputs["actual_duration_seconds"] <= 2400:
        raise ValueError("outside authorized 20–40 minutes")
    arguments.output.mkdir(parents=True, exist_ok=False)
    overlay = arguments.output / "gameplay-provenance-overlay.png"
    gameplay_overlay(overlay)
    archive = arguments.output / "speech-process-archive.zip"
    with ZipFile(archive, "x", compression=ZIP_DEFLATED, compresslevel=2) as bundle:
        for path in sorted(arguments.speech.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(arguments.speech).as_posix())
    repository = Path(__file__).resolve().parents[5]
    source_files = {
        "observation-composer-source": Path(__file__).with_name("episode_one_observation.py"),
        "observation-preparation-source": Path(__file__),
        "observation-timeline-source": Path(__file__).with_name("episode_one_full_timeline.py"),
        "observation-captions-source": Path(__file__).with_name("captions.py"),
        "observation-visuals-source": Path(__file__).with_name("visuals.py"),
        "observation-common-source": Path(__file__).with_name("common.py"),
        "observation-theme-mix-source": Path(__file__).with_name("theme_mix.py"),
        "observation-director-plan": repository / "promo/ck3_native_war_ai/episode-01-battle-win-probability/director-plan.md",
    }
    if provider == "index":
        source_files["index-narration-preparation-source"] = Path(__file__).with_name("prepare_episode_one_index_inputs.py")
        source_files["index-narration-synthesis-source"] = Path(__file__).with_name("index_revoice.py")
        source_files["index-film-verification-source"] = Path(__file__).with_name("verify_episode_one_index_film.py")
        source_files["index-review-contact-sheet-source"] = Path(__file__).with_name("review_contact_sheets.py")
        source_files["index-one-drive-delivery-source"] = Path(__file__).with_name("deliver_episode_one_index.py")
        source_files["index-one-drive-readback-source"] = Path(__file__).with_name("check_episode_one_onedrive.py")
    else:
        source_files["edge-narration-preparation-source"] = Path(__file__).with_name("prepare_narration.py")
    jobs: list[tuple[str, Path, str, str]] = [
        ("observation-production-inputs", production, "measured-narration-inputs", "application/json"),
        ("observation-film-script", arguments.script, "film-script", "application/json"),
        ("observation-shot-timeline", arguments.timeline, "shot-timeline", "application/json"),
        ("messina-full-battle-clean-footage", arguments.footage, "capture", "video/mp4"),
        ("messina-camera-visibility-audit", arguments.visibility_audit, "capture-audit", "application/json"),
        ("single-series-theme-master", arguments.theme, "audio-master", "audio/wav"),
        ("gameplay-provenance-overlay", overlay, "visual-provenance", "image/png"),
        (f"{provider}-speech-process-archive", archive, "process-archive", "application/zip"),
    ]
    if provider == "index":
        jobs.extend([
            ("index-voice-reference", arguments.reference, "authorized-voice-reference", "audio/wav"),
            ("index-synthesis-receipt", arguments.speech / "completed.json", "synthesis-receipt", "application/json"),
        ])
        if arguments.toolchain_receipt is None or not arguments.toolchain_receipt.is_file():
            raise ValueError("New IndexTTS run must bind latest formal xar-promo release")
        jobs.append(("index-toolchain-release-receipt", arguments.toolchain_receipt,
                     "toolchain-release", "application/json"))
    jobs.extend((identifier, path, "source", "text/plain")
                for identifier, path in source_files.items())
    for row in rows:
        identifier = row["audio_artifact_id"]
        extension, media_type = (".wav", "audio/wav") if provider == "index" else (".mp3", "audio/mpeg")
        jobs.append((identifier, arguments.speech / f"{row['id']}{extension}",
                     "prepared-narration", media_type))
    log_path = arguments.output / "preserve-command-history.jsonl"
    for identifier, source, role, media_type in jobs:
        if not source.is_file():
            raise FileNotFoundError(source)
        argv = [
            sys.executable, "-m", "xar_promo", "preserve",
            "--run-manifest", str(arguments.manifest),
            "--artifact-id", identifier,
            "--collection", "raw", "--role", role,
            "--media-type", media_type,
            str(source),
        ]
        result = subprocess.run(argv, capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
        with log_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps({
                "artifact_id": identifier, "argv": argv,
                "source_sha256": digest(source),
                "exit_code": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr,
            }, ensure_ascii=False) + "\n")
        if result.returncode != 0:
            raise RuntimeError(f"preserve failed for {identifier}: {result.stderr}")
        print(f"Preserved {identifier}", flush=True)
    print(json.dumps({
        "manifest": str(arguments.manifest), "artifacts": len(jobs),
        "duration_seconds": inputs["actual_duration_seconds"],
        "speech_archive_sha256": digest(archive),
        "command_history": str(log_path),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

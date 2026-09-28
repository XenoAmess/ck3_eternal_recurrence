"""Build six preserved Episode 2 reels, mix the series theme, and audit a review candidate.

Every render goes into a new external attempt. The output is a technical review
candidate, never a human approval or a published film.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import subprocess
import sys

from .episode_two_second_half import CHAPTER_IDS


COMPOSER = "war_ai_promo.episode_two_second_half:compose"
UNMIXED = "episode-02-second-half-unmixed.mp4"
FINAL = "episode-02-second-half-review-candidate.mp4"


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _binding(path: Path) -> dict:
    return {"bytes": path.stat().st_size, "sha256": _sha(path)}


def _new_json(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def _event(attempt: Path, phase: str, state: str, **details) -> None:
    with (attempt / "events.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps({"at_utc": datetime.now(timezone.utc).isoformat(),
                                 "phase": phase, "state": state, **details}, ensure_ascii=False) + "\n")


def _artifact(manifest_path: Path, run: dict, artifact_id: str) -> Path:
    rows = [row for row in run["artifacts"] if row["artifact_id"] == artifact_id]
    if len(rows) != 1:
        raise ValueError(f"Expected exactly one preserved artifact {artifact_id}")
    row = rows[0]
    path = (manifest_path.parent / row["path"]).resolve(strict=True)
    if _binding(path) != {"bytes": row["bytes"], "sha256": row["sha256"].upper()}:
        raise ValueError(f"Preserved bytes changed: {artifact_id}")
    return path


def _expect(path: Path, sha: str, count: int, label: str) -> None:
    if (not isinstance(sha, str) or len(sha) != 64 or type(count) is not int
            or count < 1 or _binding(path) != {"bytes": count, "sha256": sha.upper()}):
        raise ValueError(f"{label} lacks exact SHA-256/byte binding")


def _inputs(manifest_path: Path) -> tuple[dict, dict, Path, Path]:
    run = json.loads(manifest_path.read_text(encoding="utf-8"))
    if run.get("kind") != "xar_promo_run_manifest" or run.get("format_version") != 1:
        raise ValueError("Episode 2 requires a native xar-promo RunManifest")
    config = run["project_config"]
    snapshot = (manifest_path.parent / config["path"]).resolve(strict=True)
    _expect(snapshot, config["sha256"], config["bytes"], "ProjectConfig snapshot")
    document = json.loads(snapshot.read_text(encoding="utf-8"))
    if (document["project"]["id"] != "ck3-war-ai-battle-second-half"
            or [row["id"] for row in document["chapters"]] != list(CHAPTER_IDS)):
        raise ValueError("Run snapshot is not the six-chapter Episode 2 ProjectConfig")
    inputs_path = _artifact(manifest_path, run, "episode02-production-inputs-v1")
    inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
    if (inputs.get("schema") != "ck3-war-ai.episode02.production-inputs.v1"
            or inputs.get("human_signoff") != "not-provided"
            or inputs.get("project_config_sha256", "").upper() != _sha(snapshot)
            or inputs.get("project_config_bytes") != snapshot.stat().st_size
            or [row["id"] for row in inputs.get("chapters", [])] != list(CHAPTER_IDS)):
        raise ValueError("Production inputs do not bind this six-chapter run snapshot")
    music = _artifact(manifest_path, run, inputs["music_artifact_id"])
    _expect(music, inputs["music_sha256"], inputs["music_bytes"], "series theme")
    return run, inputs, snapshot, music


def _installed_wheel_digest() -> str:
    dist = importlib.metadata.distribution("xar-promo-toolchain")
    direct = json.loads(dist.read_text("direct_url.json") or "{}")
    archive = direct.get("archive_info", {})
    digest = archive.get("hashes", {}).get("sha256")
    if digest is None and archive.get("hash", "").startswith("sha256="):
        digest = archive["hash"][7:]
    if not digest or len(digest) != 64:
        raise ValueError("Selected interpreter has no verifiable official wheel SHA-256")
    return digest.upper()


def _command(attempt: Path, phase: str, argv: list[str], *, env: dict[str, str]) -> None:
    phase_dir = attempt / "commands" / phase
    phase_dir.mkdir(parents=True, exist_ok=False)
    _new_json(phase_dir / "argv.json", {"argv": argv, "cwd": str(attempt),
                                         "python": sys.executable})
    _event(attempt, phase, "started")
    with (phase_dir / "stdout.txt").open("xb") as stdout, (phase_dir / "stderr.txt").open("xb") as stderr:
        result = subprocess.run(argv, cwd=attempt, env=env, stdout=stdout,
                                stderr=stderr, check=False)
    _event(attempt, phase, "succeeded" if result.returncode == 0 else "failed",
           exit_code=result.returncode)
    if result.returncode:
        raise RuntimeError(f"{phase} failed with exit {result.returncode}; attempt retained at {attempt}")


def _probe(attempt: Path, phase: str, path: Path, env: dict[str, str]) -> dict:
    target = attempt / "probes" / f"{phase}.json"
    _command(attempt, f"probe-{phase}", [env["WAR_PROMO_FFPROBE"], "-v", "error",
             "-show_format", "-show_streams", "-show_chapters", "-of", "json",
             str(path)], env=env)
    stdout = attempt / "commands" / f"probe-{phase}" / "stdout.txt"
    data = json.loads(stdout.read_text(encoding="utf-8"))
    _new_json(target, data)
    return data


def _chapter_metadata(rows: list[dict]) -> tuple[str, int]:
    lines = [";FFMETADATA1\n"]
    cursor = 0
    for row in rows:
        duration = row["duration_seconds"]
        if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
            raise ValueError(f"Invalid chapter duration: {row['id']}")
        stop = cursor + round(duration * 1000)
        title = f"{row['id']} {row['title']}"
        if "\n" in title or "\r" in title:
            raise ValueError("Chapter title cannot contain a newline")
        for char in ("\\", "=", ";", "#"):
            title = title.replace(char, "\\" + char)
        lines.append(f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={cursor}\nEND={stop}\ntitle={title}\n")
        cursor = stop
    return "".join(lines), cursor


def _technical_gate(probe: dict, rows: list[dict], expected_ms: int) -> None:
    streams = probe["streams"]
    video = [stream for stream in streams if stream["codec_type"] == "video"]
    audio = [stream for stream in streams if stream["codec_type"] == "audio"]
    if (len(video) != 1 or len(audio) != 1 or video[0]["width"] != 2560
            or video[0]["height"] != 1440 or video[0]["r_frame_rate"] != "30/1"
            or audio[0]["codec_name"] != "aac" or int(audio[0]["sample_rate"]) != 48000
            or audio[0]["channels"] != 2):
        raise ValueError("Final MP4 does not have one 2560x1440/30 video and one 48 kHz stereo AAC stream")
    chapters = probe.get("chapters", [])
    if len(chapters) != len(CHAPTER_IDS):
        raise ValueError("Final MP4 does not have six chapters")
    cursor = 0
    for row, chapter in zip(rows, chapters):
        stop = cursor + round(row["duration_seconds"] * 1000)
        if (chapter.get("tags", {}).get("title") != f"{row['id']} {row['title']}"
                or abs(float(chapter["start_time"]) * 1000 - cursor) > 2
                or abs(float(chapter["end_time"]) * 1000 - stop) > 2):
            raise ValueError(f"Final chapter boundary differs: {row['id']}")
        cursor = stop
    if abs(float(probe["format"]["duration"]) * 1000 - expected_ms) > 150:
        raise ValueError("Final MP4 duration differs from measured chapters")


def assemble(manifest_path: Path, attempt: Path, *, selected_version: str,
             selected_wheel_sha256: str, music_gain_db: float = -17.0,
             synthetic_smoke: bool = False) -> dict:
    manifest_path = manifest_path.resolve(strict=True)
    attempt = attempt.resolve()
    if not attempt.is_absolute() or attempt.exists():
        raise ValueError("Attempt must be an absolute new directory")
    if not math.isfinite(music_gain_db) or not -120 <= music_gain_db <= 0:
        raise ValueError("Invalid fixed music gain")
    run, inputs, snapshot, music = _inputs(manifest_path)
    if (importlib.metadata.version("xar-promo-toolchain") != selected_version
            or _installed_wheel_digest() != selected_wheel_sha256.upper()):
        raise ValueError("Selected interpreter differs from the checked official wheel")
    src = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src) + os.pathsep + env.get("PYTHONPATH", "")
    env["WAR_PROMO_FFMPEG"] = env.get("WAR_PROMO_FFMPEG", "ffmpeg")
    env["WAR_PROMO_FFPROBE"] = env.get("WAR_PROMO_FFPROBE", "ffprobe")
    attempt.mkdir(parents=True, exist_ok=False)
    (attempt / "commands").mkdir()
    (attempt / "probes").mkdir()
    _new_json(attempt / "input-bindings.json", {
        "schema": "ck3-war-ai.episode02.assembly-input-bindings.v1",
        "run_id": run["run"]["id"], "manifest_at_start": _binding(manifest_path),
        "project_config_snapshot": {"path": str(snapshot), **_binding(snapshot)},
        "production_inputs": _binding(_artifact(manifest_path, run, "episode02-production-inputs-v1")),
        "music": {"artifact_id": inputs["music_artifact_id"], "path": str(music), **_binding(music)},
        "toolchain": {"version": selected_version, "wheel_sha256": selected_wheel_sha256.upper(),
                      "interpreter": sys.executable},
        "synthetic_smoke": synthetic_smoke,
    })
    _event(attempt, "assembly", "started", run_id=run["run"]["id"])
    cli = [sys.executable, "-m", "xar_promo"]
    _command(attempt, "validate", cli + ["validate", "--profile", "authoring",
                                        str(manifest_path)], env=env)
    _command(attempt, "plan", cli + ["plan", str(manifest_path), "--workdir",
                                    str(attempt / "build"), "--composer", COMPOSER], env=env)
    _command(attempt, "build", cli + ["build", str(manifest_path), "--workdir",
                                     str(attempt / "build"), "--composer", COMPOSER,
                                     "--offline-tts"], env=env)
    candidates = list((attempt / "build").rglob(UNMIXED))
    if len(candidates) != 1:
        raise ValueError(f"Expected one unmixed six-chapter film, got {len(candidates)}")
    unmixed = candidates[0]
    _probe(attempt, "unmixed", unmixed, env)
    mixed = attempt / "episode-02-theme-mixed-before-chapters.mp4"
    _command(attempt, "theme-mix", [sys.executable, "-m", "war_ai_promo.theme_mix",
             "--film", str(unmixed), "--music", str(music), "--output", str(mixed),
             "--work-directory", str(attempt / "theme-mix-work"),
             f"--music-gain-db={music_gain_db}"], env=env)
    metadata, expected_ms = _chapter_metadata(inputs["chapters"])
    chapter_path = attempt / "chapters.ffmeta"
    with chapter_path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(metadata)
    final = attempt / FINAL
    _command(attempt, "chapters", [env["WAR_PROMO_FFMPEG"], "-nostdin", "-hide_banner",
             "-loglevel", "error", "-n", "-i", str(mixed), "-f", "ffmetadata",
             "-i", str(chapter_path), "-map", "0:v:0", "-map", "0:a:0",
             "-map_chapters", "1", "-c", "copy", "-movflags", "+faststart",
             str(final)], env=env)
    probe = _probe(attempt, "final", final, env)
    _technical_gate(probe, inputs["chapters"], expected_ms)
    _command(attempt, "full-decode", [env["WAR_PROMO_FFMPEG"], "-nostdin", "-v", "error",
             "-xerror", "-i", str(final), "-f", "null", os.devnull], env=env)
    artifact_id = ("episode02-synthetic-technical-smoke" if synthetic_smoke
                   else "episode02-technical-review-candidate")
    _command(attempt, "preserve-final", cli + ["preserve", "--run-manifest",
             str(manifest_path), "--artifact-id", artifact_id, "--collection", "derived",
             "--role", "technical-review-candidate-unapproved", str(final)], env=env)
    receipt = {
        "schema": "ck3-war-ai.episode02.assembly-receipt.v1",
        "state": "SYNTHETIC_TECHNICAL_SMOKE" if synthetic_smoke else "TECHNICAL_CANDIDATE_UNREVIEWED",
        "human_signoff": "not-provided", "publication": "not-performed",
        "run_id": run["run"]["id"], "run_manifest": str(manifest_path),
        "run_manifest_after_build": _binding(manifest_path),
        "project_config_snapshot": _binding(snapshot),
        "unmixed": {"path": str(unmixed), **_binding(unmixed)},
        "music": {"path": str(music), **_binding(music), "gain_db": music_gain_db},
        "final": {"artifact_id": artifact_id, "path": str(final), **_binding(final),
                  "duration_seconds": float(probe["format"]["duration"])},
        "chapter_ids": list(CHAPTER_IDS), "chapter_count": len(probe["chapters"]),
        "full_decode": "passed", "technical_probe": str(attempt / "probes" / "final.json"),
        "toolchain_version": selected_version,
        "toolchain_wheel_sha256": selected_wheel_sha256.upper(),
    }
    _new_json(attempt / "assembly-receipt.json", receipt)
    _event(attempt, "assembly", "synthetic-smoke" if synthetic_smoke else "technical-candidate-unreviewed")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--attempt-directory", type=Path, required=True)
    parser.add_argument("--selected-version", required=True)
    parser.add_argument("--selected-wheel-sha256", required=True)
    parser.add_argument("--music-gain-db", type=float, default=-17.0)
    parser.add_argument("--synthetic-technical-smoke", action="store_true")
    args = parser.parse_args()
    result = assemble(args.run_manifest, args.attempt_directory,
                      selected_version=args.selected_version,
                      selected_wheel_sha256=args.selected_wheel_sha256,
                      music_gain_db=args.music_gain_db,
                      synthetic_smoke=args.synthetic_technical_smoke)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

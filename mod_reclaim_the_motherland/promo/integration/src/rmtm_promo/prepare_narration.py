"""Prepare immutable Edge TTS inputs and one exact 96-second narration master."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from xar_promo.tts import EdgeTtsProvider, TtsCache, TtsRequest


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _run(argv: list[str], audit_directory: Path) -> None:
    audit_directory.mkdir(parents=True, exist_ok=False)
    (audit_directory / "command.json").write_text(
        json.dumps({"argv": argv, "shell": False}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    completed = subprocess.run(argv, text=True, capture_output=True, check=False)
    (audit_directory / "stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (audit_directory / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
    (audit_directory / "result.json").write_text(
        json.dumps({"returncode": completed.returncode}, indent=2) + "\n",
        encoding="utf-8",
    )
    if completed.returncode:
        raise RuntimeError(f"command failed with exit code {completed.returncode}")


def prepare(policy_path: Path, attempt_directory: Path, ffmpeg: Path) -> Path:
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    if attempt_directory.exists():
        raise FileExistsError(f"attempt directory already exists: {attempt_directory}")
    attempt_directory.mkdir(parents=True)
    cache = TtsCache(attempt_directory / "tts-cache")
    provider = EdgeTtsProvider()
    voice = policy["narration"]
    rows: list[dict[str, object]] = []
    media_paths: list[Path] = []
    for section in policy["timeline"]["sections"]:
        text = section["narration"]
        if not text:
            continue
        request = TtsRequest(
            text=text,
            voice=voice["voice"],
            rate=voice["rate"],
            pitch=voice["pitch"],
            volume=voice["volume"],
            cache_salt="reclaim-promo-approved-script-v1",
        )
        entry = cache.get_or_create(request, provider, max_attempts=3)
        media_paths.append(entry.media_path.resolve())
        rows.append(
            {
                "section_id": section["id"],
                "start_seconds": float(section["start"]) + 0.35,
                "section_end_seconds": section["end"],
                "text": text,
                "fingerprint": entry.fingerprint,
                "media_path": str(entry.media_path.resolve()),
                "metadata_path": str(entry.metadata_path.resolve()),
                "media_bytes": entry.media_path.stat().st_size,
                "media_sha256": _sha256(entry.media_path),
                "cache_hit": entry.cache_hit,
            }
        )

    filter_rows: list[str] = []
    labels: list[str] = []
    for index, row in enumerate(rows):
        delay = round(float(row["start_seconds"]) * 1000)
        label = f"n{index}"
        filter_rows.append(
            f"[{index}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
            f"adelay={delay}|{delay},apad,atrim=duration=96[{label}]"
        )
        labels.append(f"[{label}]")
    filter_rows.append(
        "".join(labels)
        + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,"
        + "atrim=duration=96,asetpts=N/SR/TB[out]"
    )
    master = attempt_directory / "narration-master-a01.wav"
    partial = attempt_directory / "narration-master-a01.partial.wav"
    argv = [str(ffmpeg), "-nostdin", "-hide_banner", "-y"]
    for path in media_paths:
        argv.extend(["-i", str(path)])
    argv.extend(
        [
            "-filter_complex",
            ";".join(filter_rows),
            "-map",
            "[out]",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-c:a",
            "pcm_s24le",
            str(partial),
        ]
    )
    _run(argv, attempt_directory / "audit" / "narration-mix")
    partial.replace(master)
    manifest = {
        "format_version": 1,
        "kind": "reclaim-promo-narration-preparation",
        "voice": voice,
        "provider": {
            "id": provider.identity.provider_id,
            "version": provider.identity.tool_version,
        },
        "duration_seconds": 96,
        "master": {
            "path": str(master.resolve()),
            "bytes": master.stat().st_size,
            "sha256": _sha256(master),
        },
        "sections": rows,
    }
    (attempt_directory / "narration-preparation.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return master


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--attempt-directory", required=True, type=Path)
    parser.add_argument("--ffmpeg", required=True, type=Path)
    args = parser.parse_args()
    master = prepare(args.policy.resolve(), args.attempt_directory.resolve(), args.ffmpeg.resolve())
    print(master)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

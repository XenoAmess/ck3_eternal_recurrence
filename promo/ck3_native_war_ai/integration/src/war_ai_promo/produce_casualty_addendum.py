"""Preserve and build the eleven-cue casualty-chain addendum with xar-promo."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def run(argv: list[str], logs: Path, name: str) -> None:
    (logs / f"{name}.argv.json").write_text(json.dumps(argv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (logs / f"{name}.stdout").open("xb") as stdout, (logs / f"{name}.stderr").open("xb") as stderr:
        result = subprocess.run(argv, stdout=stdout, stderr=stderr, check=False)
    if result.returncode:
        raise RuntimeError(f"{name} failed ({result.returncode}): " +
                           (logs / f"{name}.stderr").read_text(encoding="utf-8", errors="replace")[-3000:])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--timeline", type=Path, required=True)
    parser.add_argument("--expected-toolchain-version", required=True)
    parser.add_argument("--wheel-sha256", required=True)
    parser.add_argument("--detail-only", action="store_true")
    args = parser.parse_args()
    attempt = args.attempt.resolve(strict=True)
    speech = attempt / "speech"
    manifest = attempt / "run" / "run-manifest.json"
    if not manifest.is_file() or not (speech / "production-inputs.json").is_file():
        raise FileNotFoundError("Run manifest or prepared narration is missing")
    if (attempt / "build").exists() or (attempt / "automation").exists():
        raise FileExistsError("This attempt was already produced; use a new attempt")
    logs = attempt / "automation"
    logs.mkdir()
    inputs = json.loads((speech / "production-inputs.json").read_text(encoding="utf-8"))
    rows = inputs["cues"]
    expected = ["C12"] if args.detail_only else [f"C{i:02d}" for i in range(1, 12)]
    if [row["id"] for row in rows] != expected:
        raise ValueError("Unexpected addendum cue set")
    cli = [sys.executable, "-m", "xar_promo"]
    version = subprocess.run(cli + ["--version"], capture_output=True, text=True, check=True).stdout.strip()
    if version.removeprefix("xar-promo ") != args.expected_toolchain_version:
        raise ValueError(f"Unexpected xar-promo version: {version}")
    if len(args.wheel_sha256) != 64:
        raise ValueError("Wheel SHA-256 must be 64 hexadecimal characters")
    int(args.wheel_sha256, 16)
    sources = [
        ("casualty-script", args.script.resolve(strict=True), "raw", "script"),
        ("casualty-timeline", args.timeline.resolve(strict=True), "raw", "timeline"),
        ("casualty-production-inputs", speech / "production-inputs.json", "derived", "production-inputs"),
    ]
    sources += [(row["audio_artifact_id"], speech / (row["id"] + ".mp3"), "raw", "audio") for row in rows]
    for index, (artifact_id, source, collection, role) in enumerate(sources):
        run(cli + ["preserve", "--run-manifest", str(manifest), "--artifact-id", artifact_id,
                   "--collection", collection, "--role", role, str(source)], logs, f"preserve-{index:02d}")
    run(cli + ["validate", "--profile", "authoring", str(manifest)], logs, "validate")
    run(cli + ["build", str(manifest), "--workdir", str(attempt / "build"),
               "--composer", "war_ai_promo.episode_one_casualty_addendum:compose",
               "--offline-tts"], logs, "build")
    candidates = list((attempt / "build").rglob("episode-01-casualty-addendum-unmixed.mp4"))
    if len(candidates) != 1:
        raise ValueError(f"Expected one addendum film, found {candidates}")
    receipt = {
        "schema": "ck3-war-ai-casualty-addendum-build.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "state": "built-awaiting-full-film-assembly",
        "toolchain_version": version,
        "toolchain_wheel_sha256": args.wheel_sha256.lower(),
        "interpreter": sys.executable,
        "source_run_manifest": str(manifest),
        "unmixed": str(candidates[0]),
        "unmixed_sha256": digest(candidates[0]),
        "cue_count": len(rows),
        "duration_seconds": inputs["actual_duration_seconds"],
        "human_signoff": "not-provided",
    }
    (attempt / "build-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()

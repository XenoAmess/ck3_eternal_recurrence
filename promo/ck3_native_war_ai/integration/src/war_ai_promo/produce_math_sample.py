"""Create the immutable EdgeTTS R0217 math pilot through xar-promo."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--gameplay", type=Path, required=True)
    parser.add_argument("--music", type=Path, required=True)
    args = parser.parse_args()
    attempt = args.attempt.resolve(strict=True)
    project = args.project.resolve(strict=True)
    source = project.parent.parent
    gameplay = args.gameplay.resolve(strict=True)
    music = args.music.resolve(strict=True)
    manifest = attempt / "run" / "run-manifest.json"
    if not manifest.is_file():
        raise FileNotFoundError(manifest)
    if any((attempt / name).exists() for name in ("speech", "build", "pilot-unmixed.mp4")):
        raise FileExistsError("Attempt has already started production; use a fresh attempt")
    env = os.environ.copy()
    src = Path(__file__).resolve().parents[1]
    env["PYTHONPATH"] = str(src) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    logs = attempt / "automation"
    logs.mkdir(exist_ok=True)

    def status(phase: str, **values) -> None:
        record = {"state": "running", "at_utc": datetime.now(timezone.utc).isoformat(),
                  "phase": phase, **values}
        (logs / "status.json").write_text(json.dumps(record, ensure_ascii=False,
                                                       indent=2) + "\n", encoding="utf-8")
        print(json.dumps(record, ensure_ascii=False), flush=True)

    def execute(label: str, argv: list[str]) -> None:
        (logs / f"{label}.argv.json").write_text(json.dumps(argv, ensure_ascii=False,
                                                            indent=2) + "\n", encoding="utf-8")
        with (logs / f"{label}.stdout").open("xb") as stdout, \
             (logs / f"{label}.stderr").open("xb") as stderr:
            result = subprocess.run(argv, env=env, cwd=source, stdout=stdout,
                                    stderr=stderr, check=False)
        (logs / f"{label}.result.json").write_text(json.dumps({
            "exit_code": result.returncode,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        }, indent=2) + "\n", encoding="utf-8")
        if result.returncode:
            tail = (logs / f"{label}.stderr").read_text(encoding="utf-8", errors="replace")[-2500:]
            raise RuntimeError(f"{label} failed ({result.returncode}): {tail}")

    python = sys.executable
    package = [python, "-m", "xar_promo"]
    status("01-edge-tts")
    execute("01-edge-tts", [python, "-m", "war_ai_promo.prepare_narration",
                            "--script", str(source / "script.json"),
                            "--timeline", str(source / "timeline.json"),
                            "--output", str(attempt / "speech"),
                            "--provider", "edge", "--voice", "zh-CN-XiaoxiaoNeural",
                            "--rate=-12%"])
    inputs = json.loads((attempt / "speech" / "production-inputs.json").read_text(encoding="utf-8"))
    if not 120 <= inputs["actual_duration_seconds"] <= 360:
        raise ValueError("Pilot duration outside 2–6 minutes")
    for row in inputs["cues"]:
        if len(row["visual_lines"]) != 3:
            raise ValueError(f"Expected three staged lines: {row['id']}")
    status("02-preserve", duration=inputs["actual_duration_seconds"])
    sources = [
        ("math-script", source / "script.json", "raw", "script"),
        ("math-timeline", source / "timeline.json", "raw", "timeline"),
        ("math-production-inputs", attempt / "speech" / "production-inputs.json", "derived", "production-inputs"),
        ("labelled-messina-context-source", gameplay, "raw", "capture"),
        ("single-series-theme", music, "raw", "music"),
    ]
    sources += [(row["audio_artifact_id"], attempt / "speech" / (row["id"] + ".mp3"),
                 "raw", "audio") for row in inputs["cues"]]
    for index, (artifact_id, path, collection, role) in enumerate(sources):
        execute(f"02-preserve-{index:02d}", package + ["preserve", "--run-manifest",
            str(manifest), "--artifact-id", artifact_id, "--collection", collection,
            "--role", role, str(path)])
    status("03-validate")
    execute("03-validate", package + ["validate", "--profile", "authoring", str(manifest)])
    status("04-build")
    execute("04-build", package + ["build", str(manifest), "--workdir",
            str(attempt / "build"), "--composer",
            "war_ai_promo.episode_one_math_sample:compose", "--offline-tts"])
    status("05-locate-build")
    candidates = list((attempt / "build").rglob("episode-01-math-pilot-unmixed.mp4"))
    if len(candidates) != 1:
        raise ValueError(f"Expected one unmixed film, got {candidates}")
    unmixed = candidates[0]
    status("06-theme-mix", unmixed=str(unmixed))
    output = attempt / "CK3-War-AI-Episode-1-R0217-Math-EdgeTTS-Pilot-20260925.mp4"
    execute("06-theme-mix", [python, "-m", "war_ai_promo.theme_mix",
             "--film", str(unmixed), "--music", str(music),
             "--output", str(output), "--work-directory", str(attempt / "theme-mix"),
             "--music-gain-db=-17"])
    status("07-decode")
    execute("07-decode", ["ffmpeg", "-nostdin", "-v", "error", "-xerror",
            "-i", str(output), "-f", "null", "NUL"])
    probe_path = attempt / "automation" / "output-probe.json"
    with probe_path.open("xb") as stream:
        subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                        "-of", "json", str(output)], stdout=stream, check=True)
    receipt = {"schema": "ck3-r0217-edge-math-pilot.v1",
               "state": "ready-for-onedrive-before-visual-review",
               "created_at_utc": datetime.now(timezone.utc).isoformat(),
               "toolchain_version": "0.2.1",
               "toolchain_wheel_sha256": "f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621",
               "provider": "edge-tts", "voice": "zh-CN-XiaoxiaoNeural", "rate": "-12%",
               "native_case": "R0217 one main-phase tick",
               "gameplay_case": "separate Messina replay",
               "run_manifest": str(manifest),
               "output": {"path": str(output), "bytes": output.stat().st_size,
                          "sha256": sha256(output)},
               "duration_seconds": inputs["actual_duration_seconds"],
               "theme": {"path": str(music), "sha256": sha256(music),
                         "gain_db": -17, "voice_gain_db": 0, "ducking": False},
               "visual_review": "pending-after-onedrive-upload",
               "human_signoff": "not-provided"}
    (attempt / "pilot-build-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False,
                                                                 indent=2) + "\n", encoding="utf-8")
    status("ready-for-onedrive-before-visual-review", output=str(output))


if __name__ == "__main__":
    main()

"""Prepare the approved Chinese narration with the installed XAR TTS provider.

Each invocation uses new output/run directories. Requests, response metadata,
partial audio, command output and successful media are retained for editing.
This prepares narration only; it does not render or approve a finished movie.
"""

from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata as metadata
import inspect
import json
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
from types import SimpleNamespace

import edge_tts
from xar_promo.media import ffprobe_command, parse_ffprobe_json
from xar_promo.tts import EdgeTtsProvider, TtsRequest


VOICE = "zh-CN-XiaoxiaoNeural"
RELEASE_REPOSITORY = "XenoAmess/xar_promo_toolchain"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.write("\n")


def run_command(argv: list[str], work: Path, label: str) -> subprocess.CompletedProcess[bytes]:
    started = now()
    result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    (work / f"{label}.stdout.txt").write_bytes(result.stdout)
    (work / f"{label}.stderr.txt").write_bytes(result.stderr)
    write_json(work / f"{label}.command.json", {
        "argv": argv,
        "cwd": str(Path.cwd()),
        "started_at": started,
        "completed_at": now(),
        "returncode": result.returncode,
    })
    if result.returncode:
        raise RuntimeError(f"{label} failed ({result.returncode}): {result.stderr.decode('utf-8', errors='replace')}")
    return result


class BoundaryCommunicate(edge_tts.Communicate):
    """Keep metadata from the same Edge request without a second synthesis."""

    def save_sync(self, audio_fname: str, metadata_fname: str | None = None) -> None:
        super().save_sync(
            audio_fname,
            metadata_fname or str(Path(audio_fname).with_suffix(".boundaries.jsonl")),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--director", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--report-directory", type=Path, required=True)
    args = parser.parse_args()
    director = args.director.resolve()
    config = args.config.resolve()
    work = args.work_dir.resolve()
    run_directory = args.run_directory.resolve()
    report_directory = args.report_directory.resolve()
    work.mkdir(parents=True, exist_ok=True)
    if (work / "narration").exists() or run_directory.exists() or report_directory.exists():
        raise RuntimeError("Use new narration, run and report directories; existing attempts are retained.")
    (work / "narration").mkdir()
    cli = [sys.executable, "-X", "utf8", "-m", "xar_promo"]
    release_result = run_command(
        ["gh", "api", f"repos/{RELEASE_REPOSITORY}/releases/latest"], work, "latest-release"
    )
    release = json.loads(release_result.stdout)
    wheels = [asset for asset in release["assets"] if asset["name"].endswith(".whl")]
    if release.get("draft") or release.get("prerelease") or len(wheels) != 1:
        raise RuntimeError("The latest official release has no unambiguous stable wheel.")
    wheel = wheels[0]
    distribution = metadata.distribution("xar-promo-toolchain")
    installed_version = distribution.version
    direct_url = json.loads(distribution.read_text("direct_url.json") or "{}")
    installed_sha = direct_url.get("archive_info", {}).get("hashes", {}).get("sha256")
    release_sha = wheel.get("digest", "").removeprefix("sha256:")
    if (
        release["tag_name"] != f"v{installed_version}"
        or not release_sha
        or installed_sha != release_sha
        or direct_url.get("url") != wheel["browser_download_url"]
    ):
        raise RuntimeError("Environment RED: install the latest formal wheel before creating a run.")
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("Environment RED: ffprobe is unavailable.")
    source_head = run_command(["git", "rev-parse", "HEAD"], work, "source-head").stdout.decode("utf-8").strip()
    framework = {
        "queried_at": now(),
        "release_repository": RELEASE_REPOSITORY,
        "release_id": release["id"],
        "release_tag": release["tag_name"],
        "release_url": release["html_url"],
        "wheel_url": wheel["browser_download_url"],
        "wheel_sha256": release_sha,
        "installed_direct_url": direct_url,
        "python_executable": sys.executable,
        "python_version": sys.version,
        "xar_promo_version": installed_version,
        "edge_tts_version": metadata.version("edge-tts"),
        "voice": VOICE,
        "settings": {"rate": "+0%", "pitch": "+0Hz", "volume": "+0%"},
        "boundary": "SentenceBoundary",
        "ffprobe": ffprobe,
        "source_head_at_input_read": source_head,
        "config_path": str(config),
        "config_sha256": sha(config),
        "director_path": str(director),
        "director_sha256": sha(director),
    }
    write_json(work / "framework-version.json", framework)
    for name, target in [("version", ["--version"]), ("top-help", ["--help"]),
                         ("start-run-help", ["start-run", "--help"]),
                         ("validate-help", ["validate", "--help"]),
                         ("preserve-help", ["preserve", "--help"])]:
        run_command(cli + target, work, name)
    run_command([ffprobe, "-version"], work, "ffprobe-version")
    with (work / "provider-source.txt").open("x", encoding="utf-8", newline="\n") as output:
        output.write(inspect.getsource(TtsRequest))
        output.write(inspect.getsource(EdgeTtsProvider))
        output.write(inspect.getsource(edge_tts.Communicate.save_sync))
        output.write(str(inspect.signature(edge_tts.Communicate)) + "\n")
    run_command(cli + ["validate", str(config), "--json"], work, "validate-config")
    run_command(cli + ["start-run", str(config), "--run-id", args.run_id,
                       "--run-directory", str(run_directory)], work, "start-run")
    run_manifest = run_directory / "run-manifest.json"
    preserve_index = 0

    def preserve(path: Path, artifact_id: str, role: str, *, collection: str = "raw") -> None:
        nonlocal preserve_index
        preserve_index += 1
        run_command(cli + ["preserve", str(path), "--run-manifest", str(run_manifest),
                           "--artifact-id", artifact_id, "--collection", collection,
                           "--role", role], work, f"preserve-{preserve_index:03d}")

    for path, artifact_id, role in [
        (director, "approved-director-json", "director"),
        (Path(__file__).resolve(), "narration-preparation-script", "script"),
        (work / "framework-version.json", "narration-framework-version", "framework-version"),
        (work / "latest-release.stdout.txt", "narration-latest-release", "release-query"),
        (work / "provider-source.txt", "narration-provider-source", "provider-source"),
    ]:
        preserve(path, artifact_id, role)
    payload = json.loads(director.read_text(encoding="utf-8-sig"))
    config_payload = json.loads(config.read_text(encoding="utf-8-sig"))
    cue_texts = {
        chapter["id"]: chapter["cues"][0]["narration"]["zh-CN"]
        for chapter in config_payload["chapters"]
    }
    scenes = payload["scenes"]
    if len(scenes) != 10 or any(cue_texts.get(scene["id"]) != scene["narration"] for scene in scenes):
        raise RuntimeError("The selected director and config must contain the same ten original narration texts.")
    provider = EdgeTtsProvider(
        module=SimpleNamespace(Communicate=BoundaryCommunicate),
        tool_version=metadata.version("edge-tts"),
    )
    results = []
    failure = None
    for scene in scenes:
        scene_id = scene["id"]
        scene_dir = work / "narration" / scene_id
        scene_dir.mkdir()
        request = TtsRequest(text=scene["narration"], voice=VOICE)
        request_path = scene_dir / "request.json"
        write_json(request_path, {
            "scene_id": scene_id,
            "request": request.cache_payload(),
            "provider": asdict(provider.identity),
            "boundary": "SentenceBoundary",
            "requested_at": now(),
        })
        text_path = scene_dir / "narration.zh-CN.txt"
        text_path.write_text(request.text, encoding="utf-8", newline="\n")
        audio_path = scene_dir / "narration.zh-CN.mp3"
        stdout_path = scene_dir / "tts.stdout.txt"
        stderr_path = scene_dir / "tts.stderr.txt"
        started = now()
        error = None
        try:
            with stdout_path.open("x", encoding="utf-8") as stdout, stderr_path.open("x", encoding="utf-8") as stderr:
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    provider.synthesize(request, audio_path)
            if not audio_path.is_file() or audio_path.stat().st_size == 0:
                raise RuntimeError("The TTS provider did not return audio bytes.")
            probe_result = run_command(
                [str(part) for part in ffprobe_command(Path(ffprobe), audio_path)],
                scene_dir, "ffprobe",
            )
            probe = parse_ffprobe_json(probe_result.stdout.decode("utf-8"))
            probe_raw = dict(probe.raw)
            duration = float(probe_raw["format"]["duration"])
            audio_streams = [stream for stream in probe_raw.get("streams", []) if stream.get("codec_type") == "audio"]
            if duration <= 0 or len(audio_streams) != 1 or audio_streams[0].get("codec_name") != "mp3":
                raise RuntimeError("The returned audio is not one positive-duration MP3 stream.")
            boundaries_path = audio_path.with_suffix(".boundaries.jsonl")
            boundaries = [json.loads(line) for line in boundaries_path.read_text(encoding="utf-8").splitlines() if line]
            if not boundaries or any(boundary.get("type") != "SentenceBoundary" for boundary in boundaries):
                raise RuntimeError("Expected retained Edge sentence boundaries from the same synthesis.")
            row = {
                "scene_id": scene_id,
                "title": scene["title"],
                "narration": request.text,
                "narration_utf8_sha256": hashlib.sha256(request.text.encode("utf-8")).hexdigest(),
                "status": "GREEN",
                "audio_path": str(audio_path),
                "audio_sha256": sha(audio_path),
                "audio_bytes": audio_path.stat().st_size,
                "duration_seconds": duration,
                "sample_rate": audio_streams[0].get("sample_rate"),
                "channels": audio_streams[0].get("channels"),
                "request_path": str(request_path),
                "request_sha256": sha(request_path),
                "boundaries_path": str(boundaries_path),
                "boundaries_sha256": sha(boundaries_path),
                "boundary_count": len(boundaries),
                "boundary_time_unit": "100-nanosecond ticks",
                "started_at": started,
                "completed_at": now(),
            }
            results.append(row)
            write_json(scene_dir / "result.json", row)
            print(f"{scene_id}: {duration:.3f}s, {len(boundaries)} sentence boundaries", flush=True)
        except Exception as exc:
            error = {
                "scene_id": scene_id,
                "status": "RED",
                "exception": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
                "started_at": started,
                "completed_at": now(),
                "partial_audio_path": str(audio_path) if audio_path.exists() else None,
                "partial_audio_bytes": audio_path.stat().st_size if audio_path.exists() else 0,
            }
            write_json(scene_dir / "failure.json", error)
            results.append(error)
            failure = error
        for path in sorted(scene_dir.iterdir()):
            role = "audio" if path.suffix == ".mp3" else "tts-boundaries" if path.name.endswith("boundaries.jsonl") else "tts-request" if path.name == "request.json" else "tts-evidence"
            preserve(path, f"{scene_id.lower()}-{path.name.replace('.', '-')}", role)
        if error:
            break
    report = {
        "format_version": 1,
        "kind": "superman_qiang_narration_preparation",
        "status": "GREEN" if not failure and len(results) == 10 else "RED",
        "completed_at": now(),
        "framework": framework,
        "run_manifest": str(run_manifest),
        "voice": VOICE,
        "settings": {"rate": "+0%", "pitch": "+0Hz", "volume": "+0%"},
        "successful_scenes": sum(row["status"] == "GREEN" for row in results),
        "planned_scenes": len(scenes),
        "total_audio_duration_seconds": sum(row.get("duration_seconds", 0) for row in results),
        "scenes": results,
        "remaining_scene_ids": [scene["id"] for scene in scenes if scene["id"] not in {row["scene_id"] for row in results}],
        "limitations": ["Narration preparation only; no rendered video or final human approval.",
                        "Durations are encoded MP3 durations, including provider padding.",
                        "Sentence boundaries are the provider's original metadata; use actual audio for final timing review."],
    }
    write_json(work / "narration-summary.json", report)
    preserve(work / "narration-summary.json", "narration-summary", "narration-summary", collection="derived")
    command_paths = sorted(path for path in work.iterdir() if path.is_file() and path.name.endswith((".stdout.txt", ".stderr.txt", ".command.json")))
    for index, path in enumerate(command_paths):
        preserve(path, f"narration-command-{index:03d}", "command-evidence")
    validate_result = run_command(cli + ["validate", str(run_manifest), "--json"], work, "validate-final-run")
    final_validation = json.loads(validate_result.stdout)
    report_directory.mkdir(parents=True)
    write_json(report_directory / "narration-summary.json", report)
    write_json(report_directory / "framework-version.json", framework)
    write_json(report_directory / "run-validation.json", final_validation)
    (report_directory / "README.md").write_text(
        "# 超人强旁白准备\n\n"
        f"状态：{report['status']}；声线 `{VOICE}`；Edge TTS {framework['edge_tts_version']}。\n\n"
        f"已生成 {report['successful_scenes']}/10 段，编码音频总时长 {report['total_audio_duration_seconds']:.3f} 秒。"
        "旁白逐字采用已批准 02m 导演稿，rate +0%、pitch +0Hz、volume +0%。\n\n"
        f"原始工作目录：`{work.as_posix()}`。请求、音频、句子时间标记、探测和命令日志均已保全进"
        f" `../../02m/runs/{args.run_id}/run-manifest.json` 的 content-addressed storage。\n\n"
        "[逐段音频、时长及 SHA-256](narration-summary.json)；"
        "[工具链与解释器版本](framework-version.json)；[原生 run 验证](run-validation.json)。\n\n"
        "这是旁白准备结果；尚无成片或成片人工签核。后续剪辑以真实音频时长安排字幕、呼吸和片尾。\n",
        encoding="utf-8", newline="\n",
    )
    print(json.dumps({"status": report["status"], "scenes": report["successful_scenes"],
                      "total_audio_duration_seconds": report["total_audio_duration_seconds"],
                      "run_manifest": str(run_manifest), "report": str(report_directory)}, ensure_ascii=False), flush=True)
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())

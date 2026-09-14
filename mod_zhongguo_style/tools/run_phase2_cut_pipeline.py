"""Run one phase-two promo cut through authoring, build, or post-candidate steps."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CUTS = {
    "character-led": {
        "project": "phase2-promo-character-project.json",
        "ledger": "phase2-authoring-character-claims.json",
        "artifact": "zhongguo-361-phase2-character-led-video",
        "audit_id": "character-led-automated-audit",
    },
    "institution-led": {
        "project": "phase2-promo-institution-project.json",
        "ledger": "phase2-authoring-institution-claims.json",
        "artifact": "zhongguo-361-phase2-institution-led-video",
        "audit_id": "institution-led-automated-audit",
    },
}


def run(command: list[str], *, cwd: Path, environment: dict[str, str]) -> None:
    subprocess.run(command, cwd=cwd, env=environment, check=True)


def output(command: list[str], *, cwd: Path) -> str:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def verify_toolchain(toolchain: Path) -> str:
    subprocess.run(["git", "-C", str(toolchain), "fetch", "origin"], check=True)
    dirty = output(["git", "-C", str(toolchain), "status", "--short"], cwd=toolchain)
    head = output(["git", "-C", str(toolchain), "rev-parse", "HEAD"], cwd=toolchain)
    origin = output(["git", "-C", str(toolchain), "rev-parse", "origin/main"], cwd=toolchain)
    if dirty:
        raise RuntimeError("promo tool checkout is dirty")
    if head != origin:
        raise RuntimeError("promo tool HEAD differs from origin/main; rebase it before running")
    return head


def file_sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def build(args: argparse.Namespace) -> None:
    metadata = CUTS[args.cut]
    repository = args.repository.resolve()
    toolchain = args.toolchain.resolve()
    work = args.work_dir.resolve()
    authoring = args.authoring_root.resolve() if args.authoring_root else Path(f"{work}-authoring")
    environment = os.environ.copy()
    environment["XAR_PROMO_SOURCE"] = str(toolchain)
    environment["PYTHONPATH"] = str(toolchain / "src")
    tool_head = verify_toolchain(toolchain)
    if args.expected_toolchain_head and tool_head != args.expected_toolchain_head:
        raise RuntimeError("promo tool HEAD differs from --expected-toolchain-head")
    python = str(args.python.resolve())
    intake = authoring / "footage-intake.json"
    project = authoring / metadata["project"]
    media = authoring / "media-preflight.json"
    run([
        python, str(repository / "tools/zhongguo_phase2_footage_intake.py"),
        "--capture-root", str(args.capture), "--output", str(intake),
    ], cwd=repository, environment=environment)
    run([
        python, str(repository / "mod_zhongguo_style/tools/promote_phase2_reviewed_authoring.py"),
        "--project-config", str(repository / "mod_zhongguo_style/promo" / metadata["project"]),
        "--authoring-ledger", str(repository / "mod_zhongguo_style/promo" / metadata["ledger"]),
        "--footage-intake-report", str(intake),
        "--source-review-receipt", str(args.source_review_receipt),
        "--output-project", str(project),
        "--output-receipt", str(authoring / "authoring-promotion-receipt.json"),
    ], cwd=repository, environment=environment)
    media_command = [
        python, str(repository / "mod_zhongguo_style/tools/preflight_phase2_media.py"),
        "--output", str(media), "--project-config", str(project),
        "--expected-toolchain-head", tool_head, "--capture-root", str(args.capture),
        "--planned-work-dir", str(work), "--planned-tts-cache", str(args.tts_cache),
    ]
    if args.planned_export_directory:
        media_command.extend(["--planned-export-dir", str(args.planned_export_directory)])
    run(media_command, cwd=repository, environment=environment)
    media_sha = file_sha256(media)
    run([
        python, str(repository / "mod_zhongguo_style/tools/prime_phase2_tts_cache.py"),
        "--cut", args.cut, "--project-config", str(project),
        "--media-preflight-report", str(media), "--expected-media-preflight-sha256", media_sha,
        "--tts-cache", str(args.tts_cache),
        "--output", str(authoring / "tts-cache-prime-receipt.json"),
        "--ffmpeg", args.ffmpeg, "--ffprobe", args.ffprobe,
    ], cwd=repository, environment=environment)
    common = [
        python, str(repository / "mod_zhongguo_style/tools/build_phase2_promo_video.py"),
        "--cut", args.cut, "--project-config", str(project),
        "--capture-root", str(args.capture), "--seed-preflight-report", str(args.seed_preflight),
        "--media-preflight-report", str(media), "--expected-media-preflight-sha256", media_sha,
        "--work-dir", str(work), "--tts-cache", str(args.tts_cache),
        "--ffmpeg", args.ffmpeg, "--ffprobe", args.ffprobe,
        "--run-id", f"phase2-{args.cut}-candidate",
    ]
    run([*common, "--validate-only"], cwd=repository, environment=environment)
    run(common, cwd=repository, environment=environment)


def post(args: argparse.Namespace) -> None:
    metadata = CUTS[args.cut]
    repository = args.repository.resolve()
    work = args.work_dir.resolve()
    authoring = Path(f"{work}-authoring")
    run_manifest = work / "candidate-run/run-manifest.json"
    post_root = work / "candidate-run/post-candidate"
    project = authoring / metadata["project"]
    command = [
        str(args.python.resolve()),
        str(repository / "mod_zhongguo_style/tools/materialize_phase2_post_candidate.py"),
        "--cut", args.cut, "--project-config", str(project),
        "--run-manifest", str(run_manifest), "--output-root", str(post_root),
        "--export-directory", str(args.export_directory),
    ]
    toolchain = args.toolchain.resolve()
    verify_toolchain(toolchain)
    environment = os.environ.copy()
    environment["XAR_PROMO_SOURCE"] = str(toolchain)
    environment["PYTHONPATH"] = str(toolchain / "src")
    run([*command, "--validate-only"], cwd=repository, environment=environment)
    run(command, cwd=repository, environment=environment)
    run([
        str(args.python.resolve()), "-m", "xar_promo.cli", "audit", str(run_manifest),
        "--subject-artifact-id", metadata["artifact"],
        "--evidence-bundle", str(post_root / "evidence-bundle.json"),
        "--report", str(post_root / "automated-audit.json"),
        "--report-artifact-id", metadata["audit_id"],
    ], cwd=repository, environment=environment)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--repository", type=Path, default=REPOSITORY_ROOT)
    result.add_argument("--python", type=Path, default=Path(sys.executable))
    subparsers = result.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--cut", choices=sorted(CUTS), required=True)
    build_parser.add_argument("--toolchain", type=Path, required=True)
    build_parser.add_argument("--capture", type=Path, required=True)
    build_parser.add_argument("--seed-preflight", type=Path, required=True)
    build_parser.add_argument("--tts-cache", type=Path, required=True)
    build_parser.add_argument("--work-dir", type=Path, required=True)
    build_parser.add_argument("--authoring-root", type=Path)
    build_parser.add_argument("--source-review-receipt", type=Path, required=True)
    build_parser.add_argument("--planned-export-directory", type=Path)
    build_parser.add_argument("--expected-toolchain-head")
    build_parser.add_argument("--ffmpeg", default="ffmpeg")
    build_parser.add_argument("--ffprobe", default="ffprobe")
    build_parser.set_defaults(handler=build)
    post_parser = subparsers.add_parser("post")
    post_parser.add_argument("--cut", choices=sorted(CUTS), required=True)
    post_parser.add_argument("--work-dir", type=Path, required=True)
    post_parser.add_argument("--export-directory", type=Path, required=True)
    post_parser.add_argument("--toolchain", type=Path, required=True)
    post_parser.set_defaults(handler=post)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    args.handler(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Run the phase-two validate-only sentinel preflight without a command shell."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", type=Path)
    args = parser.parse_args(argv)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence = (
        args.evidence_root.expanduser().resolve()
        if args.evidence_root
        else Path(tempfile.gettempdir()) / f"xar-phase2-preflight-{stamp}"
    )
    evidence.mkdir(parents=True, exist_ok=False)
    config = REPOSITORY_ROOT / "mod_zhongguo_style/promo/phase2-promo-project.json"
    config_sha_before = sha256(config)
    sentinels = {
        "capture-root": evidence / "capture-root-not-created",
        "work-dir": evidence / "work-dir-not-created",
        "tts-cache": evidence / "tts-cache-not-read",
        "ffmpeg": evidence / "ffmpeg-not-run.exe",
        "ffprobe": evidence / "ffprobe-not-run.exe",
        "zh-font-file": evidence / "zh-font-not-read.ttf",
        "en-font-file": evidence / "en-font-not-read.ttf",
    }
    command = [
        sys.executable,
        str(REPOSITORY_ROOT / "mod_zhongguo_style/tools/build_phase2_promo_video.py"),
        "--project-config", str(config),
        "--capture-root", str(sentinels["capture-root"]),
        "--work-dir", str(sentinels["work-dir"]),
        "--tts-cache", str(sentinels["tts-cache"]),
        "--ffmpeg", str(sentinels["ffmpeg"]),
        "--ffprobe", str(sentinels["ffprobe"]),
        "--zh-font-file", str(sentinels["zh-font-file"]),
        "--en-font-file", str(sentinels["en-font-file"]),
        "--run-id", f"phase2-preflight-{stamp}",
        "--validate-only",
    ]
    completed = subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    stdout_path = evidence / "stdout.txt"
    stderr_path = evidence / "stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")

    unexpected = [str(path) for path in sentinels.values() if path.exists()]
    config_sha_after = sha256(config)
    if unexpected:
        raise RuntimeError(f"validate-only created or touched: {unexpected}")
    if config_sha_after != config_sha_before:
        raise RuntimeError("project config changed during validate-only")
    if "Traceback" in completed.stderr:
        raise RuntimeError("unexpected Python traceback")

    result = {
        "schema_version": 1,
        "kind": "zhongguo-361-phase2-validate-only-preflight",
        "exit_code": completed.returncode,
        "config_sha256": config_sha_after,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "sentinels_absent": True,
    }
    (evidence / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"evidence_root": str(evidence), **result}, ensure_ascii=False))
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())

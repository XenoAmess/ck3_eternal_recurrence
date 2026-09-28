"""Hash-index a finished capture attempt and its source pair without editing it.

The output is a new external file. It does not certify clean spans, approve the
video, or mutate a xar-promo RunManifest. Preserve the index and key media in
the selected RunManifest with the installed xar-promo CLI afterwards.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any


def file_identity(path: Path) -> dict[str, Any]:
    before = path.stat()
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError(f"file changed during closure hash: {path}")
    return {"path": str(path.resolve()), "bytes": after.st_size,
            "sha256": h.hexdigest().upper()}


def collect(root: Path) -> list[dict[str, Any]]:
    if not root.is_dir():
        raise FileNotFoundError(root)
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"symlink inside capture assets: {path}")
        if path.is_file():
            rows.append({"relative_path": path.relative_to(root).as_posix(),
                         **file_identity(path)})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-root", type=Path, required=True)
    parser.add_argument("--offline-attempt", type=Path, required=True)
    parser.add_argument("--source-save", type=Path, required=True)
    parser.add_argument("--source-receipt", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--recorder-workdir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error("output must be new in an existing external closure directory")
    report = args.attempt_root / "ck3-output" / "capture-report.json"
    failure = args.attempt_root / "ck3-output" / "entry-failure.json"
    if not report.is_file() and not failure.is_file():
        parser.error("managed capture has not closed; wait for report or entry-failure")
    if args.recorder_workdir.parent.resolve() != args.attempt_root.resolve():
        parser.error("recorder workdir must be a child of this exact attempt")
    manifest = json.loads(args.run_manifest.read_text(encoding="utf-8"))
    if manifest.get("kind") != "xar_promo_run_manifest":
        parser.error("not a native xar-promo RunManifest")
    config_ref = manifest.get("project_config") or {}
    config_path = args.run_manifest.parent / config_ref.get("path", "")
    config = file_identity(config_path)
    if config["sha256"] != str(config_ref.get("sha256", "")).upper() or \
            config["bytes"] != config_ref.get("bytes"):
        parser.error("frozen ProjectConfig snapshot changed")
    capture_files = collect(args.attempt_root)
    offline_files = collect(args.offline_attempt)
    recorder_final = args.recorder_workdir / "recorder-final.json"
    recorder_intent = args.recorder_workdir / "recorder-intent.json"
    formal_recorder = None
    if recorder_final.is_file() and recorder_intent.is_file():
        formal_recorder = json.loads(recorder_final.read_text(encoding="utf-8"))
        intent = json.loads(recorder_intent.read_text(encoding="utf-8"))
        raw_path = Path(intent["raw_path"])
        if raw_path.is_symlink() or raw_path.resolve().parent != \
                (args.recorder_workdir / "raw").resolve():
            parser.error("formal recorder raw path escapes this recorder workdir")
        if formal_recorder.get("raw") != file_identity(raw_path):
            parser.error("formal recorder final does not bind its raw bytes")
    else:
        raw_path = None
    result = {"schema": "xar.war-promo.capture-asset-closure/v1",
              "indexed_at": datetime.now(timezone.utc).isoformat(),
              "result": "INDEXED_UNREVIEWED" if report.is_file() and formal_recorder and
                        formal_recorder.get("result") == "ENCODED_UNREVIEWED"
                        else "PARTIAL_PRESERVED",
              "clean_spans_certified": False, "human_review_completed": False,
              "formal_recorder_workdir": str(args.recorder_workdir.resolve()),
              "formal_recorder_final": file_identity(recorder_final) if recorder_final.is_file() else None,
              "formal_raw": file_identity(raw_path) if raw_path is not None else None,
              "run_manifest_at_index_time": file_identity(args.run_manifest),
              "project_config_snapshot": config,
              "source_save": file_identity(args.source_save),
              "source_receipt": file_identity(args.source_receipt),
              "attempt_root": str(args.attempt_root.resolve()),
              "attempt_files": capture_files,
              "offline_attempt_root": str(args.offline_attempt.resolve()),
              "offline_files": offline_files,
              "file_count": len(capture_files) + len(offline_files),
              "total_bytes": sum(row["bytes"] for row in capture_files + offline_files)}
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({"result": result["result"], "file_count": result["file_count"],
                      "total_bytes": result["total_bytes"], "output": str(args.output)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()

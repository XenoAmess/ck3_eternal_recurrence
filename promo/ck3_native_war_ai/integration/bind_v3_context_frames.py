"""Freeze two original CK3 frame excerpts for V3 context cards."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


def bind(path: Path, case: str) -> dict:
    if not path.is_file() or path.suffix.lower() != ".png":
        raise ValueError(f"Missing original PNG for {case}: {path}")
    with Image.open(path) as frame:
        if frame.size != (2560, 1440):
            raise ValueError(f"Unexpected original frame dimensions for {case}")
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"case_id": case, "path": path.resolve().as_posix(), "sha256": digest,
            "bytes": path.stat().st_size, "evidence_role": "context-only-original-frame"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-r", type=Path, required=True)
    parser.add_argument("--case-w", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    document = {"schema": "ck3-war-ai.v3-context-frames.v1",
                "scope": "Original CK3 map/HUD frames as context only; no synchronous AI decision proof",
                "assets": {"CASE-R": bind(args.case_r, "CASE-R"),
                           "CASE-W": bind(args.case_w, "CASE-W")}}
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(document, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({key: value["sha256"] for key, value in document["assets"].items()}))


if __name__ == "__main__":
    main()

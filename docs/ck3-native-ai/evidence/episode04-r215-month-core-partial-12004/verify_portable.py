#!/usr/bin/env python3
"""Verify the small R215 evidence copies by exact bytes and SHA-256."""
import hashlib
import json
import sys
from pathlib import Path


def need(ok, message):
    if not ok:
        raise ValueError(message)


def main() -> int:
    relative = Path("docs/ck3-native-ai/evidence/episode04-r215-month-core-partial-12004/index.json")
    bases = (base for parent in Path(__file__).resolve().parents for base in (parent, parent / "payload"))
    root = next(base for base in bases if (base / relative).is_file())
    index = json.loads((root / relative).read_text(encoding="utf-8"))
    need(index["schema"] == "xar.e04.r215-progress-evidence-index.v1", "schema differs")
    need(index["machine_id"] == "desktop-3fevhd2-1c74096080", "source machine differs")
    for row in index["copies"]:
        target = root / row["target"]
        body = target.read_bytes()
        need(len(body) == row["bytes"], "size differs: " + row["target"])
        need(hashlib.sha256(body).hexdigest() == row["sha256"], "hash differs: " + row["target"])
    print(json.dumps({"status": "PASS", "machine_id": index["machine_id"], "copies": len(index["copies"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

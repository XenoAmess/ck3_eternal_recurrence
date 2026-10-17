"""Verify copied R197 small originals without reading original machine paths."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True)
    parser.add_argument("--archive", required=True)
    args = parser.parse_args()
    index = json.loads(Path(args.index).read_text(encoding="utf-8"))
    archive = Path(args.archive).read_bytes()
    assert index["machine_id"] == "desktop-3fevhd2-1c74096080"
    assert len(archive) == index["archive"]["bytes"] and sha(archive) == index["archive"]["sha256"]
    with zipfile.ZipFile(args.archive) as z:
        assert set(z.namelist()) == {row["archive_member"] for row in index["entries"]}
        for row in index["entries"]:
            original = z.read(row["archive_member"])
            assert len(original) == row["bytes"] and sha(original) == row["sha256"]
        root = json.loads(z.read("01-root-unfreeze.json"))
        assert root["machine_id"] == index["machine_id"]
        assert root["source_head"] == index["source_head"]
        assert root["exit_reason"] == "timeout" and root["ck3_exit_code"] == 1
        assert root["cleanup_proven"] and not root["normal_exit_qualified"]
    print("PASS R197 small originals, exact hashes and abnormal-close boundary")


if __name__ == "__main__":
    main()

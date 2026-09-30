"""Retain native products and text/source records before removing listed outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile


class DigestReader:
    def __init__(self, stream):
        self.stream = stream
        self.digest = hashlib.sha256()

    def read(self, size=-1):
        chunk = self.stream.read(size)
        self.digest.update(chunk)
        return chunk


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--build-manifest", type=Path, required=True)
    parser.add_argument("--worktree-manifest", type=Path, required=True)
    args = parser.parse_args()
    destination = args.output.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    builds = json.loads(args.build_manifest.read_text(encoding="utf-8-sig"))
    worktrees = json.loads(args.worktree_manifest.read_text(encoding="utf-8-sig"))
    records = []
    suffixes = {".dll", ".pdb", ".txt", ".log", ".json", ".jsonl", ".ndjson",
                ".md", ".cpp", ".hpp", ".h", ".py", ".ps1", ".cmd", ".bat",
                ".cmake", ".yaml", ".yml", ".csv"}
    for kind, rows in (("build", builds), ("worktree", worktrees)):
        for row in rows:
            root = Path(row["path"])
            tracked = set()
            if kind == "worktree":
                data = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"])
                tracked = {os.fsdecode(p).replace("\\", "/") for p in data.split(b"\0") if p}
            selected = []
            for folder, dirs, names in os.walk(root):
                dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "pycache")]
                for name in names:
                    path = Path(folder) / name
                    relative = path.relative_to(root).as_posix()
                    if relative in tracked:
                        continue
                    if path.suffix.lower() in suffixes or (
                            path.suffix.lower() == ".exe" and path.name.startswith("xar_ck3_bridge")):
                        selected.append(path)
            archive = destination / f"{kind}-{root.name}.tar.gz"
            members = []
            with tarfile.open(archive, "w:gz", compresslevel=1) as writer:
                for path in sorted(selected):
                    info = tarfile.TarInfo(path.relative_to(root).as_posix())
                    stats = path.stat()
                    info.size = stats.st_size
                    info.mtime = stats.st_mtime
                    info.mode = stats.st_mode & 0o777
                    with path.open("rb") as source:
                        reader = DigestReader(source)
                        writer.addfile(info, reader)
                    members.append({"path": info.name, "size": info.size,
                                    "sha256": reader.digest.hexdigest()})
            expected = {m["path"]: m["sha256"] for m in members}
            with tarfile.open(archive, "r:gz") as reader:
                for member in reader:
                    with reader.extractfile(member) as content:
                        actual = hashlib.file_digest(content, "sha256").hexdigest()
                    if actual != expected[member.name]:
                        raise RuntimeError(f"Archive copy mismatch: {root} / {member.name}")
            with archive.open("rb") as stream:
                archive_sha = hashlib.file_digest(stream, "sha256").hexdigest()
            records.append({"kind": kind, "source": str(root), "source_head": row.get("head"),
                            "archive": str(archive), "archive_bytes": archive.stat().st_size,
                            "archive_sha256": archive_sha, "members": members,
                            "all_member_hashes_verified": True})
            if len(records) % 20 == 0:
                print(f"Retained {len(records)} directory archives", flush=True)
    index = destination.parent / "retained-materials.json"
    index.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"archives": len(records), "retained_files": sum(len(r["members"]) for r in records),
                      "compressed_bytes": sum(r["archive_bytes"] for r in records),
                      "all_member_hashes_verified": True}), flush=True)


if __name__ == "__main__":
    main()

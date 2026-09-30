"""Archive retired CK3 runtimes with deduplicated files, or restore their records."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil


BLOCK = 1024 * 1024
CACHE_DIRS = {"__pycache__", ".pytest_cache", "shadercache", "shadercachepdx"}
INTERMEDIATES = {".obj", ".o", ".lib", ".exp", ".ilk", ".pch", ".idb", ".tlog"}
PACKED = {".zip", ".7z", ".dds", ".png", ".jpg", ".jpeg", ".mp4", ".mkv", ".webm", ".ogg", ".pdf"}


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def exclusion(relative):
    if any(part.lower() in CACHE_DIRS for part in relative.parts[:-1]):
        return "regenerable cache"
    if relative.suffix.lower() in INTERMEDIATES:
        return "compiler intermediate"
    return None


def archive(args):
    rows = json.loads(args.candidates.read_text(encoding="utf-8-sig"))
    destination = args.output.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "objects").mkdir()
    (destination / "manifests").mkdir()
    objects = {}
    records = []
    for index, row in enumerate(rows, 1):
        root = Path(row["path"])
        members, skipped = [], []
        for entry in row["members"]:
            relative = Path(entry["path"])
            reason = exclusion(relative)
            if reason:
                skipped.append({**entry, "reason": reason})
                continue
            path = root / relative
            digest = sha256(path)
            if digest not in objects:
                packed = path.suffix.lower() in PACKED
                object_path = destination / "objects" / (digest + (".raw" if packed else ".gz"))
                copied = hashlib.sha256()
                size = 0
                opener = open if packed else gzip.open
                options = {} if packed else {"compresslevel": 1}
                with path.open("rb") as source, opener(object_path, "wb", **options) as target:
                    while chunk := source.read(BLOCK):
                        copied.update(chunk)
                        size += len(chunk)
                        target.write(chunk)
                if copied.hexdigest() != digest:
                    raise RuntimeError(f"Source changed while archiving: {path}")
                reader = open if packed else gzip.open
                with reader(object_path, "rb") as stream:
                    actual = hashlib.file_digest(stream, "sha256").hexdigest()
                if actual != digest:
                    raise RuntimeError(f"Archive copy mismatch: {path}")
                objects[digest] = {"path": object_path.relative_to(destination).as_posix(),
                                   "compression": "raw" if packed else "gzip", "size": size,
                                   "stored_bytes": object_path.stat().st_size}
            stored = objects[digest]
            if stored["size"] != entry["size"]:
                raise RuntimeError(f"Source changed since inventory: {path}")
            members.append({"path": relative.as_posix(), "size": stored["size"],
                            "sha256": digest, "object": stored["path"],
                            "compression": stored["compression"]})
        manifest = destination / "manifests" / f"{root.name}.json"
        write_json(manifest, {"source": str(root), "kind": row["kind"],
                              "members": members, "skipped": skipped})
        records.append({"source": str(root), "kind": row["kind"],
                        "archive": str(manifest), "archive_sha256": sha256(manifest),
                        "retained_files": len(members), "retained_bytes": sum(m["size"] for m in members),
                        "discarded_files": len(skipped), "discarded_bytes": sum(m["size"] for m in skipped),
                        "all_member_hashes_verified": True})
        if index % 5 == 0 or index == len(rows):
            print(json.dumps({"directories": index, "total": len(rows), "unique_objects": len(objects),
                              "stored_bytes": sum(o["stored_bytes"] for o in objects.values())}), flush=True)
    write_json(destination / "object-index.json", objects)
    write_json(destination.parent / "retained-materials.json", records)
    summary = {"directories": len(records), "retained_files": sum(r["retained_files"] for r in records),
               "retained_logical_bytes": sum(r["retained_bytes"] for r in records),
               "discarded_files": sum(r["discarded_files"] for r in records),
               "discarded_bytes": sum(r["discarded_bytes"] for r in records),
               "unique_objects": len(objects), "unique_original_bytes": sum(o["size"] for o in objects.values()),
               "stored_object_bytes": sum(o["stored_bytes"] for o in objects.values()),
               "all_member_hashes_verified": True}
    write_json(destination.parent / "archive-summary.json", summary)
    print(json.dumps(summary), flush=True)


def restore(args):
    record = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    archive_root = args.manifest.resolve().parent.parent
    target = args.destination.resolve()
    target.mkdir(parents=True, exist_ok=False)
    requested = set(args.relative_file or [])
    restored = []
    for member in record["members"]:
        if requested and member["path"] not in requested:
            continue
        path = target / member["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        opener = open if member["compression"] == "raw" else gzip.open
        with opener(archive_root / member["object"], "rb") as source, path.open("wb") as output:
            shutil.copyfileobj(source, output, BLOCK)
        if sha256(path) != member["sha256"]:
            raise RuntimeError(f"Restored copy mismatch: {path}")
        restored.append(member["path"])
    if requested - set(restored):
        raise ValueError(f"Files absent from manifest: {requested - set(restored)}")
    print(json.dumps({"destination": str(target), "restored_files": len(restored),
                      "all_restored_hashes_verified": True}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    archive_command = commands.add_parser("archive")
    archive_command.add_argument("--candidates", type=Path, required=True)
    archive_command.add_argument("--output", type=Path, required=True)
    restore_command = commands.add_parser("restore")
    restore_command.add_argument("--manifest", type=Path, required=True)
    restore_command.add_argument("--destination", type=Path, required=True)
    restore_command.add_argument("--relative-file", action="append")
    args = parser.parse_args()
    (archive if args.command == "archive" else restore)(args)


if __name__ == "__main__":
    main()

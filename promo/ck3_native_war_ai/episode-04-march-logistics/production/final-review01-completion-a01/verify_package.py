"""Verify relative text bytes only; never follow historical media locators.

Evidence: this verifies catalog integrity and local movie-subject agreements.
It does not decode media, verify PNG pixels, upload, or approve a film.
"""
from pathlib import Path, PurePosixPath
import hashlib
import json
import sys

MAX_SMALL = 1024 * 1024
TEXT_SUFFIXES = {".json", ".md", ".py", ".txt", ".patch"}
def require(condition, message):
    if not condition:
        raise ValueError(message)
def read_small(path):
    require(path.is_file() and not path.is_symlink(), f"Missing ordinary text file: {path}")
    require(path.stat().st_size <= MAX_SMALL, f"Large file forbidden: {path}")
    payload = path.read_bytes()
    payload.decode("utf-8-sig")
    return payload
def confined(root, relative):
    require(isinstance(relative, str) and "\\" not in relative and ":" not in relative, "Portable relative POSIX path required")
    relative_path = PurePosixPath(relative)
    require(not relative_path.is_absolute() and relative_path.parts and not any(p in {".", ".."} for p in relative_path.parts), "Path traversal forbidden")
    require(relative_path.as_posix() == relative, "Path must be normalized")
    require(relative_path.suffix.lower() in TEXT_SUFFIXES, "Only explicit text suffixes admitted")
    path = root.joinpath(*relative_path.parts)
    require(path.resolve().is_relative_to(root), "Resolved path escaped package")
    current = path
    while current != root:
        require(not current.is_symlink(), "Symlink path forbidden")
        current = current.parent
    return path
def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads(read_small(root / "manifest.json"))
    require(manifest["schema"] == "xar.e04.closed-producer-small-relative-manifest.v1", "Unexpected package manifest")
    require(manifest["large_media_included"] is False, "Media cannot enter this package")
    seen = set()
    total = 0
    for item in manifest["files"]:
        relative = item["relative"]
        require(relative not in seen, "Duplicate manifest path")
        seen.add(relative)
        payload = read_small(confined(root, relative))
        require(len(payload) == item["bytes"], f"Byte count mismatch: {relative}")
        require(hashlib.sha256(payload).hexdigest() == item["sha256"].lower(), f"SHA-256 mismatch: {relative}")
        total += len(payload)
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    require(actual == seen | {"manifest.json"}, "Unexpected or missing package files")
    subject = json.loads(read_small(root / "results/closed-movie-delivery.original.json"))["movie"]
    for relative, key in [("results/picture-bound-probe.original.json", "subject"), ("results/picture-receipt.original.json", "picture"), ("samples/INDEX.original.json", "movie"), ("pending-review/pending-review-package.original.json", "artifact")]:
        bound = json.loads(read_small(root / relative))[key]
        require(bound["bytes"] == subject["bytes"] and bound["sha256"].lower() == subject["sha256"].lower(), f"Movie subject disagreement: {relative}")
    template = json.loads(read_small(root / "pending-review/human-review-template.original.json"))
    require(template["state"] == "pending-human-review" and template["is_signoff"] is False and template["approval_granted"] is False, "Pending review boundary changed")
    require(template["human_response"]["decision"] is None, "No human decision is present")
    print(json.dumps({"state": "RELATIVE_TEXT_BYTES_AND_SUBJECT_BINDINGS_PASS", "files": len(seen), "bytes": total, "external_media_reads": 0, "processes_started": 0, "human_signoff": False}))
    return 0
if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError, UnicodeError) as error:
        print(json.dumps({"state": "RED", "error": str(error)}), file=sys.stderr)
        raise SystemExit(2)

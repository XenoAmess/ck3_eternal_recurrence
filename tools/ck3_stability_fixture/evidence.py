"""Permanent attempt evidence shared by pixel routing and closed-save inspection."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path


class NeedsOperator(RuntimeError):
    """No more automated input is justified by the available observation."""


def require(condition: object, message: str) -> None:
    if not condition:
        raise NeedsOperator(message)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_new(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def append(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps({"at_utc": now(), **value}, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def checked_file(reference: dict) -> Path:
    path = Path(reference["path"])
    require(sha256(path) == reference["sha256"].lower(), f"pinned file changed: {path}")
    return path

"""Installation identity and JSON helpers for disk-only CK3 update captures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def identify(root: Path) -> dict[str, object]:
    exe = root / "binaries/ck3.exe"
    image = exe.read_bytes()
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    optional = pe + 24
    launcher = root / "launcher/launcher-settings.json"
    settings = json.loads(launcher.read_text(encoding="utf-8-sig"))
    return {
        "root": str(root), "executable_sha256": hashlib.sha256(image).hexdigest(),
        "executable_size": len(image),
        "pe_timestamp": struct.unpack_from("<I", image, pe + 8)[0],
        "machine": hex(struct.unpack_from("<H", image, pe + 4)[0]),
        "preferred_image_base": hex(struct.unpack_from("<Q", image, optional + 24)[0]),
        "size_of_image": struct.unpack_from("<I", image, optional + 56)[0],
        "launcher_settings_sha256": digest(launcher),
        "launcher_identity": {k: settings.get(k) for k in (
            "gameId", "version", "rawVersion", "gameVersion", "displayVersion", "distPlatform")},
    }

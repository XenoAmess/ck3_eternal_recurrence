"""Disk-only CK3 installation selection shared by launch and acceptance tools."""

from __future__ import annotations

import json
import os
from pathlib import Path


CURRENT_STEAM_GAME_DIR = Path(r"Z:\SteamLibrary\steamapps\common\Crusader Kings III")
CURRENT_GAME_VERSION = "1.20.0.3"
CURRENT_EXECUTABLE_SHA256 = (
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"
)


def expanded_path(raw: str) -> Path:
    return Path(os.path.expandvars(raw)).expanduser().resolve()


def configured_game_dir(repo_root: Path) -> Path:
    """Prefer the installed Steam build; explicit old installations stay usable."""
    override = os.environ.get("XAR_CK3_GAME_DIR")
    if override:
        return expanded_path(override)
    if (CURRENT_STEAM_GAME_DIR / "binaries" / "ck3.exe").is_file():
        return CURRENT_STEAM_GAME_DIR.resolve()
    return (repo_root / "Crusader Kings III").resolve()


def configured_game_executable(repo_root: Path) -> Path:
    override = os.environ.get("XAR_CK3_EXE")
    if override:
        return expanded_path(override)
    return configured_game_dir(repo_root) / "binaries" / "ck3.exe"


def installed_game_version(executable: Path) -> str:
    """Read the configured executable's own launcher identity, without a process."""
    executable = executable.resolve()
    settings = executable.parent.parent / "launcher" / "launcher-settings.json"
    payload = json.loads(settings.read_text(encoding="utf-8-sig"))
    version = payload.get("rawVersion")
    if not isinstance(version, str) or not version:
        raise ValueError(f"launcher settings contain no rawVersion: {settings}")
    raw_executable = payload.get("exePath")
    if not isinstance(raw_executable, str) or not raw_executable:
        raise ValueError(f"launcher settings contain no exePath: {settings}")
    declared_executable = (settings.parent / raw_executable).resolve()
    if declared_executable != executable:
        raise ValueError(
            "launcher exePath does not match the configured CK3 executable: "
            f"{declared_executable} != {executable}"
        )
    return version

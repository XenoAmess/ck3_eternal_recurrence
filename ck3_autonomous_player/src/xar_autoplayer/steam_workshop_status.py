"""Profile-driven, read-only Steam and Workshop status observation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import re
from typing import Callable, Mapping


STEAM_WORKSHOP_STATUS_SCHEMA_V1 = "xar.ck3.steam-workshop-status/v1"
_NUMERIC_ID = re.compile(r"^[1-9][0-9]{0,19}$")
_PROCESS_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_HEX_SHA256 = re.compile(r"^[0-9A-Fa-f]{64}$")


@dataclass(frozen=True)
class WorkshopItemProfile:
    item_id: str
    display_name: str
    expected_manifest_id: str | None


@dataclass(frozen=True)
class SteamWorkshopProfile:
    steam_root: Path
    library_root: Path
    app_id: str
    expected_build_id: str
    executable_relative_path: Path
    expected_executable_sha256: str
    process_names: tuple[str, ...]
    workshop_items: tuple[WorkshopItemProfile, ...]


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _reject_unknown_keys(
    value: Mapping[str, object], allowed: set[str], label: str
) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValueError(f"{label} contains unknown keys: {unknown!r}")


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _absolute_path(value: object, label: str) -> Path:
    path = Path(_string(value, label))
    if not path.is_absolute():
        raise ValueError(f"{label} must be absolute")
    return path


def _relative_path(value: object, label: str) -> Path:
    path = Path(_string(value, label))
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"{label} must be a contained relative path")
    return path


def load_steam_workshop_profile(
    value: object,
    *,
    label: str = "steam",
) -> SteamWorkshopProfile:
    row = _mapping(value, label)
    _reject_unknown_keys(
        row,
        {"steam_root", "library_root", "app", "process_names", "workshop_items"},
        label,
    )
    app = _mapping(row.get("app"), f"{label}.app")
    _reject_unknown_keys(
        app,
        {
            "app_id",
            "expected_build_id",
            "executable_relative_path",
            "expected_executable_sha256",
        },
        f"{label}.app",
    )
    app_id = _string(app.get("app_id"), f"{label}.app.app_id")
    if not _NUMERIC_ID.fullmatch(app_id):
        raise ValueError(f"{label}.app.app_id must be a positive numeric ID")
    expected_build_id = _string(
        app.get("expected_build_id"), f"{label}.app.expected_build_id"
    )
    if not _NUMERIC_ID.fullmatch(expected_build_id):
        raise ValueError(
            f"{label}.app.expected_build_id must be a positive numeric ID"
        )
    expected_sha256 = _string(
        app.get("expected_executable_sha256"),
        f"{label}.app.expected_executable_sha256",
    )
    if not _HEX_SHA256.fullmatch(expected_sha256):
        raise ValueError(
            f"{label}.app.expected_executable_sha256 must be 64 hex characters"
        )
    raw_process_names = row.get(
        "process_names", ["steam.exe", "ck3.exe", "dowser.exe"]
    )
    if not isinstance(raw_process_names, list) or not raw_process_names:
        raise ValueError(f"{label}.process_names must be a non-empty array")
    process_names = tuple(
        _string(item, f"{label}.process_names[{index}]")
        for index, item in enumerate(raw_process_names)
    )
    if len(set(name.casefold() for name in process_names)) != len(process_names):
        raise ValueError(f"{label}.process_names must be unique")
    if any(not _PROCESS_NAME.fullmatch(name) for name in process_names):
        raise ValueError(f"{label}.process_names contains an invalid image name")
    raw_items = row.get("workshop_items")
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError(f"{label}.workshop_items must be a non-empty array")
    items: list[WorkshopItemProfile] = []
    for index, raw_item in enumerate(raw_items):
        item = _mapping(raw_item, f"{label}.workshop_items[{index}]")
        _reject_unknown_keys(
            item,
            {"item_id", "display_name", "expected_manifest_id"},
            f"{label}.workshop_items[{index}]",
        )
        item_id = _string(
            item.get("item_id"), f"{label}.workshop_items[{index}].item_id"
        )
        if not _NUMERIC_ID.fullmatch(item_id):
            raise ValueError(
                f"{label}.workshop_items[{index}].item_id must be numeric"
            )
        expected_manifest = item.get("expected_manifest_id")
        if expected_manifest is not None:
            expected_manifest = _string(
                expected_manifest,
                f"{label}.workshop_items[{index}].expected_manifest_id",
            )
            if not _NUMERIC_ID.fullmatch(expected_manifest):
                raise ValueError(
                    f"{label}.workshop_items[{index}].expected_manifest_id "
                    "must be numeric"
                )
        items.append(
            WorkshopItemProfile(
                item_id=item_id,
                display_name=_string(
                    item.get("display_name", item_id),
                    f"{label}.workshop_items[{index}].display_name",
                ),
                expected_manifest_id=expected_manifest,
            )
        )
    if len({item.item_id for item in items}) != len(items):
        raise ValueError(f"{label}.workshop_items item_id values must be unique")
    return SteamWorkshopProfile(
        steam_root=_absolute_path(row.get("steam_root"), f"{label}.steam_root"),
        library_root=_absolute_path(
            row.get("library_root"), f"{label}.library_root"
        ),
        app_id=app_id,
        expected_build_id=expected_build_id,
        executable_relative_path=_relative_path(
            app.get("executable_relative_path"),
            f"{label}.app.executable_relative_path",
        ),
        expected_executable_sha256=expected_sha256.lower(),
        process_names=process_names,
        workshop_items=tuple(items),
    )


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _parse_vdf(text: str) -> dict[str, object]:
    tokens = re.findall(r'"((?:\\.|[^"\\])*)"|([{}])', text)
    root: dict[str, object] = {}
    stack = [root]
    pending_key: str | None = None
    for quoted, brace in tokens:
        if brace == "{":
            if pending_key is None:
                raise ValueError("VDF object has no key")
            child: dict[str, object] = {}
            stack[-1][pending_key] = child
            stack.append(child)
            pending_key = None
        elif brace == "}":
            if pending_key is not None or len(stack) == 1:
                raise ValueError("malformed VDF object boundary")
            stack.pop()
        else:
            token = quoted.replace(r'\"', '"').replace(r"\\", "\\")
            if pending_key is None:
                pending_key = token
            else:
                stack[-1][pending_key] = token
                pending_key = None
    if pending_key is not None or len(stack) != 1:
        raise ValueError("incomplete VDF document")
    return root


def _object(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _offline_flags(text: str) -> list[str]:
    return sorted(set(re.findall(r'"WantsOfflineMode"\s+"([01])"', text)))


class SteamWorkshopStatusInspector:
    """Read only profile-allowlisted Steam/CK3/Workshop state."""

    def __init__(
        self,
        profile: SteamWorkshopProfile,
        *,
        process_pids: Callable[[str], list[int]],
    ) -> None:
        self.profile = profile
        self._process_pids = process_pids

    def query_v1(self) -> dict[str, object]:
        steam_exe = self.profile.steam_root / "steam.exe"
        loginusers = self.profile.steam_root / "config" / "loginusers.vdf"
        steamapps = self.profile.library_root / "steamapps"
        app_manifest = steamapps / f"appmanifest_{self.profile.app_id}.acf"
        workshop_manifest = (
            steamapps / "workshop" / f"appworkshop_{self.profile.app_id}.acf"
        )
        app_payload = _parse_vdf(_read_text(app_manifest)) if app_manifest.is_file() else {}
        app_state = _object(app_payload.get("AppState"))
        install_dir_name = app_state.get("installdir")
        install_dir = None
        executable = None
        if (
            isinstance(install_dir_name, str)
            and install_dir_name
            and Path(install_dir_name).name == install_dir_name
        ):
            install_dir = steamapps / "common" / install_dir_name
            executable = install_dir / self.profile.executable_relative_path
        observed_executable_sha256 = _sha256(executable) if executable else None
        build_id = app_state.get("buildid")
        login_flags = _offline_flags(_read_text(loginusers))

        workshop_payload = (
            _parse_vdf(_read_text(workshop_manifest))
            if workshop_manifest.is_file()
            else {}
        )
        app_workshop = _object(workshop_payload.get("AppWorkshop"))
        installed = _object(app_workshop.get("WorkshopItemsInstalled"))
        details = _object(app_workshop.get("WorkshopItemDetails"))
        content_root = steamapps / "workshop" / "content" / self.profile.app_id
        item_rows: list[dict[str, object]] = []
        for item in self.profile.workshop_items:
            installed_row = _object(installed.get(item.item_id))
            detail_row = _object(details.get(item.item_id))
            installed_manifest = installed_row.get("manifest")
            latest_manifest = detail_row.get("manifest")
            cache = content_root / item.item_id
            descriptor = cache / "descriptor.mod"
            item_rows.append(
                {
                    "item_id": item.item_id,
                    "display_name": item.display_name,
                    "expected_manifest_id": item.expected_manifest_id,
                    "installed_manifest_id": installed_manifest,
                    "latest_manifest_id": latest_manifest,
                    "cache": str(cache),
                    "cache_exists": cache.is_dir(),
                    "descriptor_exists": descriptor.is_file(),
                    "descriptor_sha256": _sha256(descriptor),
                    "installed_matches_latest": bool(
                        installed_manifest
                        and latest_manifest
                        and installed_manifest == latest_manifest
                        and cache.is_dir()
                    ),
                    "installed_matches_expected": (
                        installed_manifest == item.expected_manifest_id
                        if item.expected_manifest_id is not None
                        else None
                    ),
                }
            )
        return {
            "schema": STEAM_WORKSHOP_STATUS_SCHEMA_V1,
            "read_only": True,
            "caller_supplied_app_or_item": False,
            "steam": {
                "root": str(self.profile.steam_root),
                "executable_exists": steam_exe.is_file(),
                "loginusers_exists": loginusers.is_file(),
                "wants_offline_mode_values": login_flags,
                "offline_attested": login_flags == ["1"],
                "processes": {
                    name: self._process_pids(name)
                    for name in self.profile.process_names
                },
            },
            "app": {
                "app_id": self.profile.app_id,
                "manifest": str(app_manifest),
                "manifest_exists": app_manifest.is_file(),
                "manifest_sha256": _sha256(app_manifest),
                "state_flags": app_state.get("StateFlags"),
                "build_id": build_id,
                "expected_build_id": self.profile.expected_build_id,
                "build_matches_expected": build_id
                == self.profile.expected_build_id,
                "install_directory": str(install_dir) if install_dir else None,
                "executable": str(executable) if executable else None,
                "executable_exists": bool(executable and executable.is_file()),
                "executable_sha256": observed_executable_sha256,
                "expected_executable_sha256": (
                    self.profile.expected_executable_sha256
                ),
                "executable_matches_expected": observed_executable_sha256
                == self.profile.expected_executable_sha256,
            },
            "workshop": {
                "manifest": str(workshop_manifest),
                "manifest_exists": workshop_manifest.is_file(),
                "manifest_sha256": _sha256(workshop_manifest),
                "items": item_rows,
                "all_installed_match_latest": all(
                    row["installed_matches_latest"] for row in item_rows
                ),
                "all_pinned_expectations_match": all(
                    row["installed_matches_expected"] is not False
                    for row in item_rows
                ),
            },
        }

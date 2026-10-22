"""Typed saved-profile projection roles; verification never grants cold-load credit."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
from typing import Literal, Mapping, Protocol, TypedDict

SCHEMA: Literal["ck3-saved-campaign-profile-inventory-v2"] = "ck3-saved-campaign-profile-inventory-v2"
Role = Literal["formal_product", "case_fixture", "case_overlay"]
Mode = Literal["vanilla", "enabled"]


class ProfileDirectories(Protocol):
    @property
    def profile_dir(self) -> Path: ...

    @property
    def state_dir(self) -> Path: ...


class FilePinJSON(TypedDict):
    path: str
    bytes: int
    sha256: str


class ProjectionJSON(TypedDict):
    descriptor: str
    root_path: str
    source_role: Role


class InventoryJSON(TypedDict):
    schema: Literal["ck3-saved-campaign-profile-inventory-v2"]
    profile_mode: Mode
    profile_path: str
    enabled_mods: list[str]
    product_files: list[FilePinJSON]
    projections: list[ProjectionJSON]


def _object(value: object, fields: tuple[str, ...], label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError(label + " requires its exact closed fields")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(label + " requires string fields")
        result[key] = item
    return result


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(label + " requires nonempty text")
    return value


def _array(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(label + " requires a JSON array")
    return list(value)


def _path(value: object, label: str) -> Path:
    result = Path(_text(value, label))
    if not result.is_absolute():
        raise ValueError(label + " requires an absolute path")
    return result


def _role(value: object) -> Role:
    if type(value) is str:
        if value == "formal_product":
            return "formal_product"
        if value == "case_fixture":
            return "case_fixture"
        if value == "case_overlay":
            return "case_overlay"
    raise ValueError("Unknown saved profile projection role")


def _mode(value: object) -> Mode:
    if type(value) is str and value == "vanilla":
        return "vanilla"
    if type(value) is str and value == "enabled":
        return "enabled"
    raise ValueError("Explicit vanilla/enabled profile mode required")


def _key(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


@dataclass(frozen=True)
class FilePin:
    path: Path
    size: int
    sha256: str

    def to_json(self) -> FilePinJSON:
        return {"path": str(self.path), "bytes": self.size, "sha256": self.sha256}


@dataclass(frozen=True)
class Projection:
    descriptor: str
    root: Path
    role: Role

    def to_json(self) -> ProjectionJSON:
        return {"descriptor": self.descriptor, "root_path": str(self.root), "source_role": self.role}


@dataclass(frozen=True)
class Inventory:
    mode: Mode
    profile: Path
    enabled_mods: tuple[str, ...]
    files: tuple[FilePin, ...]
    projections: tuple[Projection, ...]

    def to_json(self) -> InventoryJSON:
        return {"schema": SCHEMA, "profile_mode": self.mode, "profile_path": str(self.profile),
            "enabled_mods": list(self.enabled_mods), "product_files": [row.to_json() for row in self.files],
            "projections": [row.to_json() for row in self.projections]}


def parse_file_pin(value: object) -> FilePin:
    item = _object(value, ("path", "bytes", "sha256"), "file pin")
    size = item["bytes"]
    if isinstance(size, bool) or not isinstance(size, int) or not 0 <= size <= 2**63 - 1:
        raise ValueError("File bytes must be an exact bounded integer")
    digest = _text(item["sha256"], "file SHA-256")
    if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValueError("Canonical lowercase SHA-256 required")
    return FilePin(_path(item["path"], "file pin path"), size, digest)


def parse_inventory(value: object) -> Inventory:
    """Validate the persisted JSON domain before constructing the typed model."""
    row = _object(value, ("schema", "profile_mode", "profile_path", "enabled_mods", "product_files", "projections"), "saved profile v2")
    if row["schema"] != SCHEMA:
        raise ValueError("Saved profile requires v2; legacy inventories are not aliases")
    mode = _mode(row["profile_mode"])
    profile = _path(row["profile_path"], "profile")
    raw_enabled = _array(row["enabled_mods"], "enabled_mods")
    raw_files = _array(row["product_files"], "product_files")
    raw_projections = _array(row["projections"], "projections")
    if mode == "vanilla" and (raw_enabled or raw_files or raw_projections):
        raise ValueError("Vanilla requires exactly empty enabled_mods/product_files/projections")
    enabled = tuple(_text(item, "enabled descriptor") for item in raw_enabled)
    if len(set(enabled)) != len(enabled):
        raise ValueError("Repeated enabled descriptor")
    files: list[FilePin] = []
    for raw in raw_files:
        files.append(parse_file_pin(raw))
    if len({_key(item.path) for item in files}) != len(files):
        raise ValueError("Repeated file pin identity")
    projections: list[Projection] = []
    for raw in raw_projections:
        item = _object(raw, ("descriptor", "root_path", "source_role"), "projection")
        projections.append(Projection(_text(item["descriptor"], "projection descriptor"),
            _path(item["root_path"], "projection root"), _role(item["source_role"])))
    descriptors = tuple(item.descriptor for item in projections)
    if len(set(descriptors)) != len(descriptors) or set(descriptors) != set(enabled):
        raise ValueError("Every enabled descriptor requires exactly one role projection")
    for index, projection in enumerate(projections):
        current = projection.root.resolve()
        for other in projections[:index]:
            previous = other.root.resolve()
            if current.is_relative_to(previous) or previous.is_relative_to(current):
                raise ValueError("Projection roots must not overlap role classifications")
    if mode == "vanilla":
        if enabled or files or projections:
            raise ValueError("Vanilla requires exactly empty enabled_mods/product_files/projections")
    elif not enabled or not files or not projections:
        raise ValueError("Enabled profile requires nonempty enabled_mods/product_files/projections")
    return Inventory(mode, profile, enabled, tuple(files), tuple(projections))


def descriptor_root(profile: Path, descriptor: str) -> Path:
    relative = Path(descriptor)
    raw = profile / relative
    path = raw.resolve()
    if relative.is_absolute() or not path.is_relative_to(profile.resolve()) or raw.is_symlink() or not path.is_file():
        raise ValueError("Enabled descriptor must be an ordinary file inside the prepared profile")
    matches = re.findall(r'(?m)^\s*path\s*=\s*"([^"\r\n]+)"\s*(?:#.*)?$', path.read_text(encoding="utf-8-sig"))
    if len(matches) != 1:
        raise ValueError("Descriptor must resolve exactly one product projection")
    raw_root = Path(matches[0])
    root = raw_root.resolve()
    if raw_root.is_symlink() or not root.is_dir():
        raise ValueError("Projection root must be an ordinary directory")
    return root


def build_inventory(*, profile: Path, mode: Mode, enabled_mods: object,
        product_files: object, roles: Mapping[str, Role]) -> Inventory:
    """Bind explicit producer roles to the actual copied descriptors.

    This constructs an inventory. Call verify_inventory at the consuming file
    boundary; neither function grants a cold-load or business qualification.
    """
    enabled = tuple(_text(value, "enabled descriptor") for value in _array(enabled_mods, "enabled_mods"))
    if set(roles) != set(enabled):
        raise ValueError("Producer must explicitly classify every enabled descriptor")
    projections = [Projection(name, descriptor_root(profile, name), _role(roles[name])).to_json() for name in enabled]
    return parse_inventory({"schema": SCHEMA, "profile_mode": mode, "profile_path": str(profile.resolve()),
        "enabled_mods": list(enabled), "product_files": product_files, "projections": projections})


def verify_inventory(inventory: Inventory, *, profile: Path, actual_enabled_mods: object) -> Inventory:
    """Read back every pinned file and exact enabled closure before role guards."""
    checked = parse_inventory(inventory.to_json())
    enabled = tuple(_text(value, "actual enabled descriptor") for value in _array(actual_enabled_mods, "actual enabled_mods"))
    if checked.profile.resolve() != profile.resolve() or checked.enabled_mods != enabled:
        raise ValueError("Inventory does not bind the actual prepared profile and enabled mods")
    seen: set[str] = set()
    for row in checked.files:
        raw_path = row.path
        path = raw_path.resolve()
        if raw_path.is_symlink() or not path.is_file():
            raise ValueError("Product inventory requires ordinary files")
        data = path.read_bytes()
        if len(data) != row.size or hashlib.sha256(data).hexdigest() != row.sha256:
            raise ValueError("Saved campaign inventory file changed: " + str(path))
        seen.add(_key(path))
    actual: set[str] = set()
    guarded: list[Path] = []
    for projection in checked.projections:
        root = descriptor_root(profile, projection.descriptor)
        if _key(root) != _key(projection.root):
            raise ValueError("Projection root differs from its actual enabled descriptor")
        actual.add(_key(profile / projection.descriptor))
        for path in root.rglob("*"):
            if path.is_symlink():
                raise ValueError("Product projection contains a symbolic link")
            if path.is_file():
                actual.add(_key(path))
                if projection.role != "formal_product" and path.suffix.casefold() == ".txt":
                    guarded.append(path)
    if actual != seen:
        raise ValueError("Inventory is not the complete exact enabled projection plus outer descriptors")
    for path in guarded:
        if "on_game_start_after_lobby" in path.read_text(encoding="utf-8-sig"):
            raise ValueError("Saved campaign fixture/overlay contains a cold-start registrar: " + str(path))
    return checked

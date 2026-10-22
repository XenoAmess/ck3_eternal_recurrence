"""Publish role-bound saved-profile inventories using the existing copy backend."""
from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
import sys
from typing import Literal, Mapping, NotRequired, Protocol, TypedDict, runtime_checkable

SDK_SOURCE = Path(__file__).resolve().parents[1] / "ck3_autonomous_player/src"
sys.path.insert(0, str(SDK_SOURCE))
from xar_autoplayer.saved_campaign_profile_inventory_v2 import FilePinJSON, Inventory, Mode, Role, build_inventory, parse_file_pin, parse_inventory

# The selected tools module and SDK contract must come from the same source
# tree. An already-imported package from another checkout is not a fallback.
if Path(inspect.getfile(Inventory)).resolve() != (SDK_SOURCE / "xar_autoplayer/saved_campaign_profile_inventory_v2.py").resolve():
    raise ValueError("Saved profile v2 contract imported from another source tree")

import ck3_mod_acceptance_prepare as legacy_copy


class MaterializedSavedProfile(TypedDict):
    state_dir: str
    profile: str
    product_inventory: FilePinJSON
    files: dict[str, FilePinJSON]
    product_file_count: int
    runtime_status: Literal["NOT_RUN"]
    fixture_mounted: Literal[False]
    vanilla_profile: NotRequired[Literal[True]]


@runtime_checkable
class _CopyBackend(Protocol):
    def __call__(self, context: object, product_dir: Path | None, plain_configuration: object) -> object: ...


def _mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(label + " requires an object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(label + " requires string fields")
        result[key] = item
    return result


def _path(value: object, label: str) -> Path:
    if not isinstance(value, (Path, str)) or not str(value):
        raise ValueError(label + " requires an explicit path")
    return Path(value).resolve()


def _write_inventory(path: Path, inventory: Inventory) -> FilePinJSON:
    checked = parse_inventory(inventory.to_json())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(checked.to_json(), stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    data = path.read_bytes()
    value: object = json.loads(data)
    if parse_inventory(value) != checked:
        raise ValueError("Published v2 inventory readback differs")
    return {"path": str(path.resolve()), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def write_saved_profile_inventory_v2(path: Path, *, profile: Path, mode: Mode, enabled_mods: object,
        product_files: object, roles: Mapping[str, Role]) -> FilePinJSON:
    """Publish one closed role-bound inventory for an existing exact copy."""
    inventory = build_inventory(profile=profile, mode=mode, enabled_mods=enabled_mods, product_files=product_files, roles=roles)
    return _write_inventory(path, inventory)


def materialize_saved_profile_v2(context: object, product_dir: Path | None, plain_configuration: object,
        *, source_role: Role | None) -> MaterializedSavedProfile:
    """Copy once through the shared backend, then publish explicit v2 roles.

    The old backend remains byte-stable for retained source contracts. Its v1
    inventory is not passed to a future host or used as a v2 compatibility alias.
    No profile verification here grants a cold-load or product qualification.
    """
    if product_dir is None:
        if source_role is not None:
            raise ValueError("Vanilla cannot declare a projection role")
    elif not isinstance(product_dir, Path) or source_role not in ("formal_product", "case_fixture", "case_overlay"):
        raise ValueError("An enabled source requires its explicit typed projection role")
    values = _mapping(context, "shared preparation context")
    output = _path(values.get("output"), "preparation output")
    state = _path(values.get("state_dir"), "prepared state")
    # This is the one legacy dynamic boundary. Validate the returned packet and
    # every persisted Pin before constructing the new cross-module return type.
    backend: object = legacy_copy.materialize_product_profile
    if not isinstance(backend, _CopyBackend):
        raise ValueError("Actual shared profile copy backend is unavailable")
    raw = backend(context, product_dir, plain_configuration)
    copied = _mapping(raw, "actual copied profile")
    profile = _path(copied.get("profile"), "actual copied profile")
    if _path(copied.get("state_dir"), "actual copied state") != state or profile != state / "profile":
        raise ValueError("Actual copied profile crossed its selected prepared state")
    inventory_pin = parse_file_pin(copied.get("product_inventory"))
    original_raw = inventory_pin.path.read_bytes()
    if len(original_raw) != inventory_pin.size or hashlib.sha256(original_raw).hexdigest() != inventory_pin.sha256:
        raise ValueError("Copy backend inventory changed before v2 publication")
    original_value: object = json.loads(original_raw)
    original = _mapping(original_value, "actual backend inventory")
    if set(original) != {"schema", "profile_path", "enabled_mods", "product_files"}:
        raise ValueError("Copy backend inventory fields differ")
    expected_schema = "ck3-saved-campaign-vanilla-profile-v1" if product_dir is None else "ck3-saved-campaign-product-only-profile-v1"
    if original["schema"] != expected_schema or _path(original["profile_path"], "backend profile") != profile:
        raise ValueError("Copy backend inventory does not bind its actual mode/profile")
    roles: dict[str, Role] = {}
    if source_role is not None:
        roles["mod/product.mod"] = source_role
    inventory = build_inventory(profile=profile, mode="vanilla" if product_dir is None else "enabled",
        enabled_mods=original["enabled_mods"], product_files=original["product_files"], roles=roles)
    files = {name: parse_file_pin(value).to_json() for name, value in _mapping(copied.get("files"), "actual copied file table").items()}
    destination = output / "saved-profile-inventory-v2.json"
    published = _write_inventory(destination, inventory)
    result: MaterializedSavedProfile = {"state_dir": str(state), "profile": str(profile),
        "product_inventory": published,
        "files": files, "product_file_count": len(inventory.files), "runtime_status": "NOT_RUN", "fixture_mounted": False}
    if product_dir is None:
        result["vanilla_profile"] = True
    return result

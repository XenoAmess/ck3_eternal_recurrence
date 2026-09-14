"""Stage the repository data bridge as an isolated profile companion mod.

The normal autonomous-player profile deliberately contains only the release
projection.  Live fixtures that need repository-only script definitions may
opt into this module after ``prepare_profile``.  The companion remains a
separate mod inside the disposable profile; no file is copied into the release
projection or either repository descriptor.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from .environment import (
    OUTER_DESCRIPTOR_REF,
    REPO_ROOT,
    EnvironmentSpec,
    ck3_processes,
    is_relative_to,
    parse_descriptor_target,
    sha256_file,
    snapshot_digest,
    tree_snapshot,
    verify_profile,
    write_bytes_atomic,
    write_json_atomic,
    write_outer_descriptor,
)
from .errors import AgentError


MOD_BRIDGE_SOURCE = REPO_ROOT / "ck3_autonomous_player" / "mod_bridge"
MOD_BRIDGE_TARGET_NAME = "xar-mcp-bridge"
MOD_BRIDGE_OUTER_NAME = "xar_mcp_bridge.mod"
MOD_BRIDGE_OUTER_REF = f"mod/{MOD_BRIDGE_OUTER_NAME}"
MOD_BRIDGE_RECEIPT_NAME = "xar-mod-bridge-companion.json"
MILITARY_WRAPPER_RELATIVE_PATH = Path(
    "common/script_values/xar_mcp_military_preparation_summary_v1.txt"
)
MILITARY_WRAPPERS = {
    "xar_mcp_military_current_strength_final": "current_military_strength",
    "xar_mcp_military_max_strength_final": "max_military_strength",
    "xar_mcp_military_number_of_knights_final": "number_of_knights",
    "xar_mcp_military_max_number_of_knights_final": "max_number_of_knights",
    "xar_mcp_military_maa_gold_expense_relative_final": (
        "character_men_at_arms_expense_gold_relative"
    ),
}
_LOADABLE_ROOTS = ("descriptor.mod", "common", "gui")


def _source_projection(source: Path) -> dict[str, dict[str, object]]:
    files: dict[str, dict[str, object]] = {}
    for name in _LOADABLE_ROOTS:
        root = source / name
        if root.is_file():
            paths = [root]
        elif root.is_dir():
            paths = sorted(path for path in root.rglob("*") if path.is_file())
        else:
            raise AgentError(f"mod_bridge loadable source is missing: {root}")
        for path in paths:
            if path.is_symlink():
                raise AgentError(f"mod_bridge loadable source is a symlink: {path}")
            relative = path.relative_to(source).as_posix()
            files[relative] = {
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
    return files


def _wrapper_proofs(wrapper: Path) -> dict[str, dict[str, object]]:
    text = wrapper.read_text(encoding="utf-8-sig")
    proofs: dict[str, dict[str, object]] = {}
    for key, expression in MILITARY_WRAPPERS.items():
        matches = re.findall(
            rf"(?ms)^\s*{re.escape(key)}\s*=\s*\{{\s*"
            rf"value\s*=\s*{re.escape(expression)}\s*\}}\s*$",
            text,
        )
        proofs[key] = {
            "expression": expression,
            "provider": MILITARY_WRAPPER_RELATIVE_PATH.as_posix(),
            "exact_definition_count": len(matches),
            "loadable": len(matches) == 1,
        }
    return proofs


def _render_receipt(
    spec: EnvironmentSpec,
    source: Path,
    target: Path,
    outer: Path,
    *,
    production_tree_sha256: str,
) -> dict[str, Any]:
    source_files = _source_projection(source)
    target_files = tree_snapshot(target)
    wrapper = target / MILITARY_WRAPPER_RELATIVE_PATH
    proofs = _wrapper_proofs(wrapper) if wrapper.is_file() else {}
    dlc_load_path = spec.profile_dir / "dlc_load.json"
    dlc_load = json.loads(dlc_load_path.read_text(encoding="utf-8-sig"))
    checks = {
        "production_projection_unchanged": (
            snapshot_digest(tree_snapshot(spec.production_dir))
            == production_tree_sha256
        ),
        "source_projection_matches_target": source_files == target_files,
        "enabled_playset_exact": dlc_load
        == {
            "enabled_mods": [OUTER_DESCRIPTOR_REF, MOD_BRIDGE_OUTER_REF],
            "disabled_dlcs": [],
        },
        "outer_descriptor_targets_companion": (
            outer.is_file() and parse_descriptor_target(outer) == target.resolve()
        ),
        "companion_inside_disposable_profile": is_relative_to(
            target.resolve(), spec.profile_dir.resolve()
        ),
        "five_military_wrappers_loadable": (
            len(proofs) == len(MILITARY_WRAPPERS)
            and all(item.get("loadable") is True for item in proofs.values())
        ),
    }
    return {
        "schema": "xar.ck3.autoplayer.mod_bridge_companion_profile_v1",
        "status": "green" if all(checks.values()) else "red",
        "profile": str(spec.profile_dir.resolve()),
        "source": str(source),
        "target": str(target),
        "outer_descriptor": str(outer),
        "enabled_mods": dlc_load.get("enabled_mods"),
        "production_tree_sha256_before_companion": production_tree_sha256,
        "production_tree_sha256_after_companion": snapshot_digest(
            tree_snapshot(spec.production_dir)
        ),
        "source_projection": source_files,
        "source_projection_sha256": snapshot_digest(source_files),
        "target_projection": target_files,
        "target_projection_sha256": snapshot_digest(target_files),
        "military_wrapper_file": {
            "path": str(wrapper),
            "sha256": sha256_file(wrapper) if wrapper.is_file() else None,
        },
        "military_wrapper_definitions": proofs,
        "checks": checks,
    }


def stage_mod_bridge_companion(
    spec: EnvironmentSpec, *, source: Path = MOD_BRIDGE_SOURCE
) -> dict[str, Any]:
    """Add one repository ``mod_bridge`` provider to a prepared fresh profile."""

    if ck3_processes():
        raise AgentError("refusing companion staging while ck3.exe is running")
    # Establish that the input is the normal signed production-only profile.
    manifest = verify_profile(spec)
    source = source.expanduser().resolve()
    source_files = _source_projection(source)
    inner = source / "descriptor.mod"
    inner_text = inner.read_text(encoding="utf-8-sig")
    if "remote_file_id" in inner_text or re.search(r"(?m)^\s*path\s*=", inner_text):
        raise AgentError("repository mod_bridge descriptor is not an inner descriptor")

    target = spec.profile_dir / "mod-content" / MOD_BRIDGE_TARGET_NAME
    outer = spec.profile_dir / "mod" / MOD_BRIDGE_OUTER_NAME
    receipt_path = spec.profile_dir / MOD_BRIDGE_RECEIPT_NAME
    for path in (target, outer, receipt_path):
        if path.exists():
            raise AgentError(f"companion target already exists: {path}")

    production_tree_sha256 = snapshot_digest(tree_snapshot(spec.production_dir))
    if production_tree_sha256 != manifest.get("mod", {}).get(
        "production_tree_sha256"
    ):
        raise AgentError("production projection changed before companion staging")

    target.mkdir(parents=True, exist_ok=False)
    shutil.copy2(inner, target / "descriptor.mod")
    for directory in ("common", "gui"):
        shutil.copytree(
            source / directory,
            target / directory,
            copy_function=shutil.copy2,
        )
    if tree_snapshot(target) != source_files:
        raise AgentError("mod_bridge companion copy differs from repository source")
    write_outer_descriptor(target / "descriptor.mod", outer, target)
    write_json_atomic(
        spec.profile_dir / "dlc_load.json",
        {
            "enabled_mods": [OUTER_DESCRIPTOR_REF, MOD_BRIDGE_OUTER_REF],
            "disabled_dlcs": [],
        },
    )
    inbox_source = source / "templates" / "xar_mcp_inbox.txt"
    if not inbox_source.is_file():
        raise AgentError(f"mod_bridge no-op inbox template is missing: {inbox_source}")
    write_bytes_atomic(
        spec.profile_dir / "run" / "xar_mcp_inbox.txt", inbox_source.read_bytes()
    )

    receipt = _render_receipt(
        spec,
        source,
        target,
        outer,
        production_tree_sha256=production_tree_sha256,
    )
    if receipt["status"] != "green":
        raise AgentError(f"mod_bridge companion staging is RED: {receipt['checks']!r}")
    write_json_atomic(receipt_path, receipt)
    return verify_mod_bridge_companion(spec, source=source)


def verify_mod_bridge_companion(
    spec: EnvironmentSpec, *, source: Path = MOD_BRIDGE_SOURCE
) -> dict[str, Any]:
    """Verify the two-mod disposable playset without accepting extra providers."""

    source = source.expanduser().resolve()
    receipt_path = spec.profile_dir / MOD_BRIDGE_RECEIPT_NAME
    if not receipt_path.is_file():
        raise AgentError(f"mod_bridge companion receipt is missing: {receipt_path}")
    recorded = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    target = spec.profile_dir / "mod-content" / MOD_BRIDGE_TARGET_NAME
    outer = spec.profile_dir / "mod" / MOD_BRIDGE_OUTER_NAME
    current = _render_receipt(
        spec,
        source,
        target,
        outer,
        production_tree_sha256=str(
            recorded.get("production_tree_sha256_before_companion", "")
        ),
    )
    if current.get("status") != "green":
        raise AgentError(f"mod_bridge companion preflight is RED: {current['checks']!r}")
    stable_keys = (
        "profile",
        "source",
        "target",
        "outer_descriptor",
        "enabled_mods",
        "production_tree_sha256_before_companion",
        "production_tree_sha256_after_companion",
        "source_projection_sha256",
        "target_projection_sha256",
        "military_wrapper_file",
        "military_wrapper_definitions",
        "checks",
    )
    if any(recorded.get(key) != current.get(key) for key in stable_keys):
        raise AgentError("mod_bridge companion differs from its staging receipt")
    current["receipt"] = str(receipt_path)
    current["receipt_sha256"] = sha256_file(receipt_path)
    return current

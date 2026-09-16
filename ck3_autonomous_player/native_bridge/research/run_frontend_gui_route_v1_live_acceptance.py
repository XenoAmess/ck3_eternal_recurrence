#!/usr/bin/env python3
"""Run the closed MCP CK3 frontend route acceptance.

This runner launches one managed, non-debug CK3 process at the main menu,
injects the exact bridge DLL, and uses the official MCP SDK to prove the
semantic route through ``coat_of_arms_designer``. Opt-in checks can collect a
detect/apply/native-Copy matrix, census the native custom-mode pattern tree, or
commit one design through the exact dynasty Finish button, reopen it, and
compare native Copy bytes. A hash-bound canonical preview can also be compared
to the full route-bound CK3 framebuffer through the managed MCP. It never sends
mouse or keyboard input and never uses OCR.
The opt-in Bookmarks model probe uses the same driver's private native pipe
after the official MCP NewGame/Bookmarks sequence; it never selects a ruler.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
from contextlib import ExitStack
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any
import uuid
import winreg

import numpy as np
from PIL import Image


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from mcp import Client  # noqa: E402

from xar_autoplayer.bridge.coat_of_arms_source_probe_contract import (  # noqa: E402
    COAT_OF_ARMS_SOURCE_V1_EXECUTABLE_SHA256,
    COAT_OF_ARMS_SOURCE_V1_GAME_VERSION,
    encode_coat_of_arms_source_v1,
    encode_coat_of_arms_source_transport_v2,
)
from xar_autoplayer.bridge.coat_of_arms_source_upload_v2 import (  # noqa: E402
    COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES,
)
from xar_autoplayer.bridge.frontend_gui_route_contract import (  # noqa: E402
    frontend_coat_of_arms_background_patterns_ready_v1,
    frontend_coat_of_arms_custom_mode_target_ready_v1,
    frontend_lobby_default_ruler_designer_ready_v1,
)
from xar_autoplayer.bridge.mcp_server import create_server  # noqa: E402
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.succession_transition_contract import (  # noqa: E402
    ORDINARY_CAMPAIGN_SUCCESSION,
    bind_succession_lifecycle_from_environment_v1,
)
from xar_autoplayer.environment import (  # noqa: E402
    ensure_state_path_safe,
    make_spec,
    verify_profile,
)
from xar_autoplayer.locking import (  # noqa: E402
    exclusive_launch_lock,
    exclusive_state_lock,
)
from xar_autoplayer.runtime import (  # noqa: E402
    NativeBridgeLaunchConfig,
    launch,
    stop_tracked,
    utc_now,
)


EXPECTED_CK3_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
QUERY_CAPABILITY = "game.command.query-frontend-gui-route-v1"
INSPECT_CAPABILITY = "game.command.inspect-frontend-gui-tree-v1"
ACTIVATE_NEW_GAME_CAPABILITY = "game.command.activate-frontend-new-game-v1"
ACTIVATE_PICK_ANY_CAPABILITY = (
    "game.command.activate-frontend-pick-any-character-v1"
)
ACTIVATE_SELECT_RANDOM_PLAYABLE_CAPABILITY = (
    "game.command.activate-frontend-select-random-playable-v1"
)
ACTIVATE_RULER_DESIGNER_CAPABILITY = (
    "game.command.activate-frontend-ruler-designer-v1"
)
ACTIVATE_COAT_OF_ARMS_DESIGNER_CAPABILITY = (
    "game.command.activate-frontend-coat-of-arms-designer-v1"
)
INSPECT_COAT_OF_ARMS_TREE_CAPABILITY = (
    "game.command.inspect-frontend-coat-of-arms-tree-v1"
)
INSPECT_COAT_OF_ARMS_PATTERN_GRID_CAPABILITY = (
    "game.command.inspect-frontend-coat-of-arms-pattern-grid-v1"
)
ACTIVATE_COAT_OF_ARMS_CUSTOM_MODE_CAPABILITY = (
    "game.command.activate-frontend-coat-of-arms-custom-mode-v1"
)
COMMIT_DYNASTY_COAT_OF_ARMS_CAPABILITY = (
    "game.command.commit-frontend-dynasty-coat-of-arms-v1"
)
PROBE_COAT_OF_ARMS_CAPABILITY = "game.command.probe-coat-of-arms-source-v1"
EXPORT_COAT_OF_ARMS_CAPABILITY = "game.command.export-coat-of-arms-source-v1"
QUERY_TOOL = "ck3_query_frontend_gui_route_v1"
BRIDGE_DIAGNOSTICS_TOOL = "ck3_get_bridge_diagnostics"
VFS_ASSET_PROJECTION_TOOL = "ck3_project_coat_of_arms_vfs_asset_winner_v1"
INSPECT_TOOL = "ck3_inspect_frontend_gui_tree_v1"
ACTIVATE_NEW_GAME_TOOL = "ck3_activate_frontend_new_game_v1"
ACTIVATE_PICK_ANY_TOOL = "ck3_activate_frontend_pick_any_character_v1"
ACTIVATE_PREPARE_CUSTOM_RULER_TOOL = (
    "ck3_activate_frontend_prepare_custom_ruler_v1"
)
ACTIVATE_RULER_DESIGNER_TOOL = "ck3_activate_frontend_ruler_designer_v1"
ACTIVATE_COAT_OF_ARMS_DESIGNER_TOOL = (
    "ck3_activate_frontend_coat_of_arms_designer_v1"
)
INSPECT_COAT_OF_ARMS_TREE_TOOL = (
    "ck3_inspect_frontend_coat_of_arms_tree_v1"
)
INSPECT_COAT_OF_ARMS_PATTERN_GRID_TOOL = (
    "ck3_inspect_frontend_coat_of_arms_pattern_grid_v1"
)
ACTIVATE_COAT_OF_ARMS_CUSTOM_MODE_TOOL = (
    "ck3_activate_frontend_coat_of_arms_custom_mode_v1"
)
COMMIT_DYNASTY_COAT_OF_ARMS_TOOL = (
    "ck3_commit_frontend_dynasty_coat_of_arms_v1"
)
SNAPSHOT_TOOL = "ck3_take_snapshot"
PROBE_COAT_OF_ARMS_TOOL = "ck3_probe_coat_of_arms_source_v1"
EXPORT_COAT_OF_ARMS_TOOL = "ck3_export_coat_of_arms_source_v1"
BEGIN_COAT_OF_ARMS_UPLOAD_TOOL = "ck3_begin_coat_of_arms_source_upload_v2"
APPEND_COAT_OF_ARMS_UPLOAD_TOOL = "ck3_append_coat_of_arms_source_chunk_v2"
COMMIT_COAT_OF_ARMS_UPLOAD_TOOL = "ck3_commit_coat_of_arms_source_upload_v2"
ABORT_COAT_OF_ARMS_UPLOAD_TOOL = "ck3_abort_coat_of_arms_source_upload_v2"
COMPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL = (
    "ck3_compare_frontend_coat_of_arms_framebuffer_v1"
)
CALIBRATE_COAT_OF_ARMS_FRAMEBUFFER_V3_TOOL = (
    "ck3_calibrate_frontend_coat_of_arms_framebuffer_v3"
)
COMPARE_COAT_OF_ARMS_FRAMEBUFFER_V3_TOOL = (
    "ck3_compare_frontend_coat_of_arms_framebuffer_v3"
)
CAPTURE_COAT_OF_ARMS_FRAMEBUFFER_TOOL = (
    "ck3_capture_frontend_coat_of_arms_framebuffer_v1"
)
PREPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL = (
    "ck3_prepare_frontend_coat_of_arms_framebuffer_v1"
)
FRAMEBUFFER_GATE_THRESHOLDS = {
    "maximum_locator_loss": 0.45,
    "minimum_distinct_margin": 0.005,
    "maximum_mean_absolute_error": 0.10,
    "maximum_color_mse": 0.03,
    "maximum_edge_loss": 0.16,
    "maximum_spatial_mean_absolute_error": 0.25,
}
COPY_REAPPLY_EQUIVALENCE_THRESHOLDS = {
    "maximum_locator_loss": 0.45,
    "minimum_distinct_margin": 0.005,
    "maximum_mean_absolute_error": 0.01,
    "maximum_color_mse": 0.001,
    "maximum_edge_loss": 0.02,
    "maximum_spatial_mean_absolute_error": 0.03,
}
SYNTAX_MATRIX = Path(__file__).with_name("coat_of_arms_syntax_matrix_v1.json")
_PROFILE_EXCLUDES = frozenset(
    {"crashes", "dumps", "exceptions", "logs", "save games", "last_save.ck3"}
)

PARENT_SEMANTICS_CASES = (
    {
        "id": "parent-only",
        "source": "coa = { parent = k_england }",
    },
    {
        "id": "literal-england",
        "source": (
            'coa = { pattern = "pattern_solid.dds" color1 = red color2 = white '
            'colored_emblem = { texture = "ce_wyvern.dds" color1 = white '
            'color2 = white color3 = red instance = { position = { 0.5 0.5 } '
            'scale = { 0.9 0.9 } } } }'
        ),
    },
    {
        "id": "parent-override-blue",
        "source": "coa = { parent = k_england color1 = blue }",
    },
    {
        "id": "literal-override-blue",
        "source": (
            'coa = { pattern = "pattern_solid.dds" color1 = blue color2 = white '
            'colored_emblem = { texture = "ce_wyvern.dds" color1 = white '
            'color2 = white color3 = red instance = { position = { 0.5 0.5 } '
            'scale = { 0.9 0.9 } } } }'
        ),
    },
    {
        "id": "parent-plus-child",
        "source": (
            'coa = { parent = k_england colored_emblem = { '
            'texture = "ce_block_02.dds" color1 = black color2 = black '
            'color3 = black instance = { position = { 0.5 0.5 } '
            'scale = { 0.25 0.25 } depth = 99 } } }'
        ),
    },
    {
        "id": "literal-plus-child",
        "source": (
            'coa = { pattern = "pattern_solid.dds" color1 = red color2 = white '
            'colored_emblem = { texture = "ce_wyvern.dds" color1 = white '
            'color2 = white color3 = red instance = { position = { 0.5 0.5 } '
            'scale = { 0.9 0.9 } depth = 0 } } colored_emblem = { '
            'texture = "ce_block_02.dds" color1 = black color2 = black '
            'color3 = black instance = { position = { 0.5 0.5 } '
            'scale = { 0.25 0.25 } depth = 99 } } }'
        ),
    },
    {
        "id": "unresolved-parent-control",
        "source": "coa = { parent = c_england }",
    },
)
PARENT_SEMANTICS_PAIRS = (
    ("parent-only", "literal-england"),
    ("parent-override-blue", "literal-override-blue"),
    ("parent-plus-child", "literal-plus-child"),
)
PARENT_SEMANTICS_DIAGNOSTIC_PAIRS = (
    ("parent-only", "unresolved-parent-control", True),
    ("parent-only", "parent-override-blue", True),
    ("parent-only", "parent-plus-child", False),
)
# Predeclared for r21 and later. Independent 8-bit captures may differ by one
# quantization level; anything larger, any alpha change, or a wider mean drift
# is treated as a real renderer difference.
PARENT_SEMANTICS_CAPTURE_NOISE_THRESHOLDS = {
    "maximum_channel_error": 1,
    "maximum_normalized_mean_absolute_error": 0.00001,
    "maximum_alpha_differing_pixels": 0,
}

VFS_WINNER_CASES = (
    {
        "id": "shared-conflict",
        "source": (
            'coa = { pattern = "pattern_xar_vfs_shared.dds" color1 = red '
            'color2 = white color3 = black }'
        ),
    },
    {
        "id": "load-order-0-reference",
        "source": (
            'coa = { pattern = "pattern_xar_vfs_first.dds" color1 = red '
            'color2 = white color3 = black }'
        ),
    },
    {
        "id": "load-order-1-reference",
        "source": (
            'coa = { pattern = "pattern_xar_vfs_second.dds" color1 = red '
            'color2 = white color3 = black }'
        ),
    },
)
# This is a predeclared hypothesis, not an assumption in the resolver.  The
# live matrix fails closed unless the conflicting path matches only the later
# enabled-mod reference within the independently fixed capture-noise bounds.
VFS_WINNER_DIAGNOSTIC_PAIRS = (
    ("shared-conflict", "load-order-0-reference", False),
    ("shared-conflict", "load-order-1-reference", True),
    ("load-order-0-reference", "load-order-1-reference", False),
)
VFS_EXTENDED_CASES = (
    {
        "id": "base-conflict",
        "source": (
            'coa = { pattern = "pattern_checkers_06.dds" color1 = red '
            'color2 = white color3 = black }'
        ),
    },
    {
        "id": "base-original-reference",
        "source": (
            'coa = { pattern = "pattern_xar_vfs_base_original.dds" color1 = red '
            'color2 = white color3 = black }'
        ),
    },
    {
        "id": "base-mod-reference",
        "source": (
            'coa = { pattern = "pattern_xar_vfs_base_mod.dds" color1 = red '
            'color2 = white color3 = black }'
        ),
    },
    {
        "id": "archive-conflict",
        "source": (
            'coa = { pattern = "pattern_xar_vfs_archive_shared.dds" color1 = red '
            'color2 = white color3 = black }'
        ),
    },
    {
        "id": "archive-directory-reference",
        "source": (
            'coa = { pattern = "pattern_xar_vfs_archive_directory.dds" color1 = red '
            'color2 = white color3 = black }'
        ),
    },
    {
        "id": "archive-later-reference",
        "source": (
            'coa = { pattern = "pattern_xar_vfs_archive_later.dds" color1 = red '
            'color2 = white color3 = black }'
        ),
    },
)
VFS_EXTENDED_DIAGNOSTIC_PAIRS = (
    ("base-conflict", "base-original-reference", False),
    ("base-conflict", "base-mod-reference", True),
    ("base-original-reference", "base-mod-reference", False),
    ("archive-conflict", "archive-directory-reference", False),
    ("archive-conflict", "archive-later-reference", True),
    ("archive-directory-reference", "archive-later-reference", False),
)
VFS_REPLACE_PATH_CASES = (
    {
        "id": "base-only",
        "source": (
            'coa = { pattern = "pattern_checkers_06.dds" color1 = red '
            'color2 = white color3 = black }'
        ),
    },
    {
        "id": "replaced-earlier-only",
        "source": (
            'coa = { pattern = "pattern_xar_vfs_replaced_earlier.dds" color1 = red '
            'color2 = white color3 = black }'
        ),
    },
    {
        "id": "missing-control",
        "source": (
            'coa = { pattern = "pattern_xar_vfs_missing_control.dds" color1 = red '
            'color2 = white color3 = black }'
        ),
    },
    {
        "id": "later-reference",
        "source": (
            'coa = { pattern = "pattern_xar_vfs_replace_later.dds" color1 = red '
            'color2 = white color3 = black }'
        ),
    },
)
VFS_REPLACE_PATH_DIAGNOSTIC_PAIRS = (
    ("base-only", "missing-control", True),
    ("base-only", "later-reference", False),
    ("replaced-earlier-only", "missing-control", False),
    ("replaced-earlier-only", "later-reference", False),
    ("missing-control", "later-reference", False),
)
VFS_MOUNT_ORDER_EXPECTED_FRAGMENTS = (
    "coa_vfs_replace_earlier",
    "coa_vfs_replace_later",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-profile", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-pipe", required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument(
        "--steam-loginusers",
        type=Path,
        help=(
            "Steam loginusers.vdf used for the offline-mode gate. When omitted, "
            "the runner resolves SteamPath from the current-user registry."
        ),
    )
    parser.add_argument("--timeout", type=float, default=360.0)
    parser.add_argument(
        "--bookmarks-read-only",
        action="store_true",
        help="stop at the native Bookmarks route and save its bounded GUI tree",
    )
    parser.add_argument(
        "--bookmarks-model-private",
        action="store_true",
        help="after MCP Bookmarks tree, capture one default-OFF private native selected-model frame without clicking",
    )
    parser.add_argument(
        "--bookmarks-select-start-private",
        action="store_true",
        help=(
            "controlled exact-build 1066 path: key-derived private typed "
            "selection, independent model requery, private StartGame, paused "
            "public campaign-root and paired checkpoint; public MCP tools stay OFF"
        ),
    )
    parser.add_argument(
        "--ordinary-campaign-xar-off-seed",
        action="store_true",
        help=(
            "use the already prepared state-dir xar_off profile and bind the "
            "paired fresh-1066 checkpoint as an ordinary no-pact campaign seed"
        ),
    )
    parser.add_argument(
        "--syntax-matrix",
        action="store_true",
        help="collect the checked-in CoA detect/apply/Copy matrix after routing",
    )
    parser.add_argument(
        "--custom-mode-census",
        action="store_true",
        help=(
            "enter native CoA custom mode and census the materialized "
            "background-pattern widget tree"
        ),
    )
    parser.add_argument(
        "--commit-roundtrip",
        action="store_true",
        help=(
            "apply one CoA, commit with native dynasty Finish, reopen, and "
            "compare native Copy bytes"
        ),
    )
    parser.add_argument(
        "--large-source",
        type=Path,
        help=(
            "apply one source larger than the v1 request bound through the "
            "chunked v2 MCP contract, then perform native Copy"
        ),
    )
    parser.add_argument(
        "--reference-preview",
        type=Path,
        help=(
            "hash-bind one canonical PNG and compare it to CK3 after the "
            "large source has been applied"
        ),
    )
    parser.add_argument(
        "--native-crop-output",
        type=Path,
        help="write the verified native framebuffer crop as an append-only PNG",
    )
    parser.add_argument(
        "--picture-corpus",
        type=Path,
        help=(
            "apply every picture-* case in one browser-evidence directory and "
            "compare each canonical preview in the same managed CK3 session"
        ),
    )
    parser.add_argument(
        "--single-reference-case",
        type=Path,
        help=(
            "apply one directory containing coat_of_arms.txt and "
            "canonical-preview-230.png through the same calibrated v3 "
            "native-pixel route as --picture-corpus"
        ),
    )
    parser.add_argument(
        "--picture-crop-dir",
        type=Path,
        help=(
            "write one verified native crop per --picture-corpus or "
            "--single-reference-case case"
        ),
    )
    parser.add_argument(
        "--parent-semantics-matrix",
        action="store_true",
        help=(
            "apply a bounded k_england parent/literal matrix and capture each "
            "native-UV surface through reference-free MCP"
        ),
    )
    parser.add_argument(
        "--parent-crop-dir",
        type=Path,
        help="write one hash-bound native crop per --parent-semantics-matrix case",
    )
    parser.add_argument(
        "--vfs-winner-matrix",
        action="store_true",
        help=(
            "apply the checked-in two-mod CoA VFS fixture and prove which "
            "load-order reference owns the conflicting DDS path"
        ),
    )
    parser.add_argument(
        "--vfs-crop-dir",
        type=Path,
        help="write one hash-bound native crop per --vfs-winner-matrix case",
    )
    parser.add_argument(
        "--vfs-extended-matrix",
        action="store_true",
        help=(
            "apply the checked-in base/mod plus directory/archive CoA VFS "
            "fixture and prove both conflicting DDS winners"
        ),
    )
    parser.add_argument(
        "--vfs-extended-crop-dir",
        type=Path,
        help="write one hash-bound native crop per --vfs-extended-matrix case",
    )
    parser.add_argument(
        "--vfs-replace-path-matrix",
        action="store_true",
        help=(
            "apply the checked-in later-mod replace_path fixture and compare "
            "base-only plus earlier-mod patterns to a missing control"
        ),
    )
    parser.add_argument(
        "--vfs-replace-path-crop-dir",
        type=Path,
        help="write one hash-bound native crop per --vfs-replace-path-matrix case",
    )
    parser.add_argument(
        "--vfs-mount-order-diagnostics",
        action="store_true",
        help=(
            "capture the default-OFF private VFS mount publisher table through "
            "the official read-only MCP diagnostics tool after reaching the CoA page"
        ),
    )
    parser.add_argument(
        "--vfs-mount-order-diagnostics-only",
        action="store_true",
        help=(
            "stop the managed run after the bounded startup mount-order MCP "
            "receipt; requires --vfs-mount-order-diagnostics"
        ),
    )
    parser.add_argument(
        "--vfs-asset-projection-path",
        action="append",
        default=[],
        help=(
            "project one direct coat-of-arms DDS winner through the live MCP "
            "mount receipt; repeatable and requires --vfs-mount-order-diagnostics"
        ),
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _git_head(repository: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repository, text=True
    ).strip()


def _copy_profile(source: Path, target: Path) -> dict[str, object]:
    source = source.resolve()
    target = target.resolve()
    if not source.is_dir():
        raise RuntimeError(f"source profile is missing: {source}")
    if target.exists():
        raise RuntimeError(f"target profile already exists: {target}")
    for path in source.rglob("*"):
        if path.is_symlink():
            raise RuntimeError(f"source profile contains a symlink: {path}")

    def ignore(directory: str, names: list[str]) -> set[str]:
        if Path(directory).resolve() == source:
            return set(names) & _PROFILE_EXCLUDES
        return set()

    shutil.copytree(source, target, copy_function=shutil.copy2, ignore=ignore)
    source_settings = source / "pdx_settings.txt"
    target_settings = target / "pdx_settings.txt"
    if not source_settings.is_file() or not target_settings.is_file():
        raise RuntimeError("profile clone lacks pdx_settings.txt")
    return {
        "source": str(source),
        "target": str(target),
        "pdx_settings_sha256": _sha256(target_settings),
        "source_settings_matched": _sha256(source_settings)
        == _sha256(target_settings),
    }


def _steam_offline(loginusers: Path) -> dict[str, object]:
    path = loginusers.resolve()
    text = path.read_text(encoding="utf-8-sig", errors="strict")
    matches = re.findall(r'"WantsOfflineMode"\s+"([01])"', text)
    result = {
        "path": str(path),
        "wants_offline_mode_values": matches,
        "offline": bool(matches) and all(value == "1" for value in matches),
    }
    if result["offline"] is not True:
        raise RuntimeError("Steam is not configured for offline mode")
    return result


def _resolve_steam_loginusers(explicit: Path | None) -> Path:
    if explicit is not None:
        path = explicit.resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Steam loginusers.vdf not found: {path}")
        return path

    registry_locations = (
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
    )
    checked: list[str] = []
    for hive, key_name, value_name in registry_locations:
        checked.append(key_name)
        try:
            with winreg.OpenKey(hive, key_name) as key:
                steam_root, _ = winreg.QueryValueEx(key, value_name)
        except OSError:
            continue
        candidate = Path(str(steam_root)) / "config" / "loginusers.vdf"
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(
        "Steam loginusers.vdf was not supplied and SteamPath discovery failed; "
        f"registry locations checked: {', '.join(checked)}"
    )


def _content_blocks(result: Any) -> list[object]:
    blocks: list[object] = []
    for block in getattr(result, "content", []):
        if hasattr(block, "model_dump"):
            blocks.append(block.model_dump(mode="json"))
        else:
            blocks.append(str(block))
    return blocks


async def _call(
    client: Client,
    name: str,
    arguments: dict[str, object] | None = None,
) -> dict[str, object]:
    arguments = {} if arguments is None else dict(arguments)
    started = time.monotonic()
    try:
        result = await client.call_tool(name, arguments)
        return {
            "tool": name,
            "arguments": arguments,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "is_error": bool(result.is_error),
            "structured_content": result.structured_content,
            "content": _content_blocks(result),
        }
    except BaseException as error:
        return {
            "tool": name,
            "arguments": arguments,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "is_error": True,
            "exception": f"{type(error).__name__}: {error}",
        }


def _structured(call: dict[str, object]) -> dict[str, object]:
    value = call.get("structured_content")
    return value if isinstance(value, dict) else {}


def _call_private_bookmarks_model(
    driver: NativeHeadlessGameplayDriver, timeout_seconds: float
) -> dict[str, object]:
    """One fixed read-only native-pipe ABI capture, outside public MCP tools."""
    started = time.monotonic()
    request_id = f"feudal-bm-model-{uuid.uuid4().hex[:12]}"
    step = "probe-frontend-bookmark-model-v1"
    if timeout_seconds <= 0:
        return {
            "tool": "private-native-bookmarks-model-v1",
            "elapsed_seconds": 0,
            "is_error": True,
            "error": "bounded sequence expired before private model submit",
            "submitted": False,
        }
    submitted = False
    try:
        driver.endpoint.send(
            {
                "type": "execute_step",
                "protocol_version": 1,
                "request_id": request_id,
                "step": step,
                "expected_revision": 0,
            }
        )
        submitted = True
        frame = driver.state.wait_for_command_result(
            request_id, min(timeout_seconds, 15.0)
        )
    except Exception as error:
        return {
            "tool": "private-native-bookmarks-model-v1",
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "is_error": True,
            "exception": f"{type(error).__name__}: {error}",
            "submitted": submitted,
        }
    if frame is None:
        return {
            "tool": "private-native-bookmarks-model-v1",
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "is_error": True,
            "error": "private native command_result timed out",
            "submitted": submitted,
            "timed_out": True,
        }
    result = frame.get("result")
    envelope_valid = (
        frame.get("type") == "command_result"
        and frame.get("request_id") == request_id
        and isinstance(result, dict)
        and result.get("step") == step
    )
    return {
        "tool": "private-native-bookmarks-model-v1",
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "is_error": frame.get("ok") is not True or not envelope_valid,
        "submitted": True,
        "envelope_valid": envelope_valid,
        "structured_content": result if envelope_valid else {},
        "raw_frame": frame,
    }


def _private_1066_candidate_index(model: object) -> int:
    """Use only this exact frame's selected Bookmark and native element keys."""
    if not isinstance(model, dict):
        raise ValueError("private 1066 model is not an object")
    keys = model.get("candidate_keys")
    index = model.get("supported_1066_candidate_index")
    count = model.get("bookmark_character_count")
    if (
        model.get("private_scope") != "exact-build-bookmarks-model-v1"
        or model.get("status") != "identity_ready"
        or model.get("candidate_identity_ready") is not True
        or model.get("setup_view_matches_bookmarks_root") is not True
        or model.get("verified_owner_route")
        not in {"gui_context_registry", "app_idler_chain"}
        or model.get("selected_bookmark_key")
        != "bm_1066_rags_to_riches"
        or model.get("supported_1066_government_key")
        != "feudal_government"
        or model.get("supported_1066_date_matches") is not True
        or model.get("selected_date_low_raw") != 0x032AEB08
        or not isinstance(keys, list)
        or not isinstance(count, int)
        or isinstance(count, bool)
        or len(keys) != count
        or len(keys) < 1
        or any(not isinstance(key, str) or not key for key in keys)
        or len(set(keys)) != len(keys)
        or not isinstance(index, int)
        or isinstance(index, bool)
        or not 0 <= index < count
        or keys[index]
        != "bookmark_rags_to_riches_petty_king_murchad"
    ):
        raise ValueError("current native 1066 feudal candidate identity is unproven")
    return index


def _call_private_frontend_action(
    driver: NativeHeadlessGameplayDriver,
    step: str,
    timeout_seconds: float,
) -> dict[str, object]:
    """Submit one fixed typed action; uncertain ACK is never retried here."""
    started = time.monotonic()
    request_id = f"feudal-bm-action-{uuid.uuid4().hex[:12]}"
    if timeout_seconds <= 0:
        return {
            "tool": "private-native-feudal-1066-action-v1",
            "step": step,
            "submitted": False,
            "is_error": True,
            "error": "bounded sequence expired before private action submit",
        }
    submitted = False
    try:
        driver.endpoint.send({
            "type": "execute_step",
            "protocol_version": 1,
            "request_id": request_id,
            "step": step,
            "expected_revision": 0,
        })
        submitted = True
        frame = driver.state.wait_for_command_result(
            request_id, min(timeout_seconds, 15.0)
        )
    except Exception as error:
        return {
            "tool": "private-native-feudal-1066-action-v1",
            "step": step,
            "submitted": submitted,
            "is_error": True,
            "exception": f"{type(error).__name__}: {error}",
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    if frame is None:
        return {
            "tool": "private-native-feudal-1066-action-v1",
            "step": step,
            "submitted": True,
            "is_error": True,
            "timed_out": True,
            "error": "submitted private action has no command_result",
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    result = frame.get("result")
    envelope_valid = (
        frame.get("type") == "command_result"
        and frame.get("request_id") == request_id
        and isinstance(result, dict)
        and result.get("step") == step
    )
    return {
        "tool": "private-native-feudal-1066-action-v1",
        "step": step,
        "submitted": True,
        "is_error": frame.get("ok") is not True or not envelope_valid,
        "envelope_valid": envelope_valid,
        "structured_content": result if envelope_valid else {},
        "raw_frame": frame,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def _controlled_private_feudal_start(
    driver: NativeHeadlessGameplayDriver,
    before_model: dict[str, object],
    timeout_seconds: float,
    *,
    expected_succession_lifecycle: dict[str, object] | None = None,
) -> dict[str, object]:
    """One private selection and StartGame, each followed by separate state."""
    deadline = time.monotonic() + timeout_seconds
    calls: list[dict[str, object]] = []
    flow: dict[str, object] = {
        "scope": "controlled-private-exact-build-1066",
        "public_query_action_advertised": False,
        "selector_submitted": False,
        "start_submitted": False,
        "ok": False,
        "calls": calls,
    }

    def stop(reason: str) -> dict[str, object]:
        flow["error"] = reason
        return flow

    try:
        target_index = _private_1066_candidate_index(before_model)
    except ValueError as error:
        return stop(str(error))
    selected_index = before_model.get("selected_character_index")
    if selected_index not in {-1, target_index}:
        return stop("another native Bookmark character is selected")
    flow["native_target_index_before"] = target_index
    flow["selected_index_before"] = selected_index
    if selected_index == -1:
        selector = _call_private_frontend_action(
            driver, "select-frontend-supported-1066-character-v1",
            max(0.0, deadline - time.monotonic()),
        )
        calls.append(selector)
        flow["selector_submitted"] = selector.get("submitted") is True
        selector_result = _structured(selector)
        if (
            selector.get("is_error") is not False
            or selector_result.get("accepted") is not True
            or selector_result.get("status")
            != "acknowledged_verification_pending"
        ):
            return stop("typed selection submitted or rejected without a verified next model; do not retry")
    after_call = _call_private_bookmarks_model(
        driver, max(0.0, deadline - time.monotonic())
    )
    calls.append(after_call)
    after_model = _structured(after_call)
    flow["next_native_model"] = after_model
    if after_call.get("is_error") is not False:
        return stop("independent post-selection native model unavailable")
    try:
        after_target_index = _private_1066_candidate_index(after_model)
    except ValueError as error:
        return stop(f"independent post-selection identity changed: {error}")
    if (
        after_model.get("selected_character_index") != after_target_index
        or after_model.get("selected_bookmark_key")
        != before_model.get("selected_bookmark_key")
        or after_model.get("selected_date_raw")
        != before_model.get("selected_date_raw")
        or after_model.get("supported_1066_government_key")
        != before_model.get("supported_1066_government_key")
    ):
        return stop("new native frame did not select the current key-matched role")
    flow["independent_selected_model_verified"] = True

    start = _call_private_frontend_action(
        driver, "activate-frontend-start-selected-bookmark-v1",
        max(0.0, deadline - time.monotonic()),
    )
    calls.append(start)
    flow["start_submitted"] = start.get("submitted") is True
    start_result = _structured(start)
    if (
        start.get("is_error") is not False
        or start_result.get("accepted") is not True
        or start_result.get("status") != "acknowledged_verification_pending"
    ):
        return stop("StartGame submitted or rejected without a paused map; do not retry")
    flow["start_acknowledgement"] = start_result

    paused_map: dict[str, object] | None = None
    last_error: str | None = None
    pause_submitted = False
    while time.monotonic() < deadline:
        try:
            observed = driver.take_snapshot()
        except Exception as error:
            last_error = f"{type(error).__name__}: {error}"
        else:
            played = observed.get("played_character")
            played_id = (
                played.get("character_id")
                if isinstance(played, dict)
                else None
            )
            if (
                isinstance(played_id, int)
                and not isinstance(played_id, bool)
                and played_id >= 1
            ):
                if observed.get("paused") is True:
                    paused_map = observed
                    break
                if not pause_submitted:
                    pause_submitted = True
                    try:
                        flow["typed_pause_map"] = driver.execute_step("pause-map")
                    except Exception as error:
                        last_error = f"typed pause-map: {type(error).__name__}: {error}"
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(0.25, remaining))
    if paused_map is None:
        flow["last_map_error"] = last_error
        return stop("StartGame submitted but independent paused player map was not observed")
    flow["independent_paused_map"] = paused_map

    # StartGame can publish the player/map snapshot before its application-main
    # load work returns through another SDL/Windows pump. A ready mailbox from
    # the previous pump is only submission permission, not a fresh executor
    # opportunity. Keep the same paused 1066 player binding and wait for one
    # later pump, as initial production native_auto_run readiness already does.
    first_played = paused_map.get("played_character")
    first_played_id = (
        first_played.get("character_id")
        if isinstance(first_played, dict)
        else None
    )
    first_diagnostics = paused_map.get("diagnostics")
    first_bridge_pid = (
        first_diagnostics.get("bridge_pid")
        if isinstance(first_diagnostics, dict)
        else None
    )
    first_connection_generation = (
        first_diagnostics.get("connection_generation")
        if isinstance(first_diagnostics, dict)
        else None
    )
    if (
        paused_map.get("map_ready") is not True
        or paused_map.get("date_raw") != after_model.get("selected_date_low_raw")
        or not isinstance(first_played_id, int)
        or isinstance(first_played_id, bool)
        or not isinstance(first_bridge_pid, int)
        or isinstance(first_bridge_pid, bool)
        or not isinstance(first_connection_generation, int)
        or isinstance(first_connection_generation, bool)
    ):
        return stop("independent paused 1066 player binding is incomplete")

    def pump_epoch(snapshot: dict[str, object]) -> int | None:
        diagnostics = snapshot.get("diagnostics")
        heartbeat = (
            diagnostics.get("last_heartbeat")
            if isinstance(diagnostics, dict)
            else None
        )
        mailbox = (
            heartbeat.get("main_thread_query_mailbox_v1")
            if isinstance(heartbeat, dict)
            else None
        )
        value = mailbox.get("pump_epochs") if isinstance(mailbox, dict) else None
        return (
            value
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0
            else None
        )

    current_key = (
        paused_map.get("snapshot_id"),
        paused_map.get("native_revision"),
    )
    baseline_epoch = pump_epoch(paused_map)
    last_epoch = baseline_epoch
    if baseline_epoch is None:
        return stop("application-main pump epoch is unknown after paused StartGame")
    post_ready_map: dict[str, object] | None = None
    while time.monotonic() < deadline:
        try:
            observed = driver.take_snapshot()
        except Exception as error:
            last_error = f"post-ready snapshot: {type(error).__name__}: {error}"
        else:
            observed_played = observed.get("played_character")
            observed_id = (
                observed_played.get("character_id")
                if isinstance(observed_played, dict)
                else None
            )
            observed_diagnostics = observed.get("diagnostics")
            if (
                observed.get("paused") is not True
                or observed.get("map_ready") is not True
                or observed.get("date_raw") != paused_map.get("date_raw")
                or observed_id != first_played_id
                or not isinstance(observed_diagnostics, dict)
                or observed_diagnostics.get("bridge_pid") != first_bridge_pid
                or observed_diagnostics.get("connection_generation")
                != first_connection_generation
            ):
                return stop("paused StartGame player binding changed before public query")
            last_epoch = pump_epoch(observed)
            if last_epoch is None:
                return stop("application-main pump epoch became unknown before public query")
            next_key = (
                observed.get("snapshot_id"),
                observed.get("native_revision"),
            )
            if next_key != current_key:
                current_key = next_key
                baseline_epoch = last_epoch
            elif last_epoch > baseline_epoch:
                post_ready_map = observed
                break
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(0.25, remaining))
    flow["post_ready_pump"] = {
        "baseline_epoch": baseline_epoch,
        "last_epoch": last_epoch,
        "initial_snapshot_id": paused_map.get("snapshot_id"),
        "initial_native_revision": paused_map.get("native_revision"),
        "last_error": last_error,
    }
    if post_ready_map is None:
        return stop("application-main pump did not advance on the stable paused 1066 player binding within the bounded window")
    paused_map = post_ready_map
    flow["post_ready_pump"].update(
        {
            "verified": True,
            "snapshot_id": paused_map.get("snapshot_id"),
            "native_revision": paused_map.get("native_revision"),
            "date_raw": paused_map.get("date_raw"),
            "player_character_id": first_played_id,
        }
    )

    try:
        root = driver._execute_campaign_root_context_v1_query(
            expected_revision=None
        )
    except Exception as error:
        return stop(f"public paused campaign-root query failed: {type(error).__name__}: {error}")
    flow["public_campaign_root"] = root
    played = paused_map.get("played_character")
    played_id = played.get("character_id") if isinstance(played, dict) else None
    government = root.get("government")
    if (
        paused_map.get("date_raw")
        != after_model.get("selected_date_low_raw")
        or root.get("date_raw") != paused_map.get("date_raw")
        or root.get("campaign_root_context_ready") is not True
        or root.get("queried_native_revision")
        != paused_map.get("native_revision")
        or root.get("player_character_id") != played_id
        or not isinstance(government, dict)
        or government.get("key") != "feudal_government"
    ):
        return stop("independent paused-map/public root does not prove 1066 feudal player")
    flow["independent_campaign_root_verified"] = True
    if expected_succession_lifecycle is not None:
        readiness = root.get("readiness")
        rule_tokens = root.get("selected_game_rule_tokens")
        if (
            not isinstance(readiness, dict)
            or readiness.get("selected_game_rule_tokens_ready") is not True
            or not isinstance(rule_tokens, list)
            or not all(isinstance(value, str) for value in rule_tokens)
            or "xar_off" not in rule_tokens
            or "xar_on" in rule_tokens
        ):
            return stop(
                "public campaign-root does not prove the selected xar_off rules"
            )
        flow["ordinary_xar_off_rules_verified"] = True

    try:
        checkpoint = driver.execute_step("save-checkpoint")
    except Exception as error:
        return stop(f"paired checkpoint failed: {type(error).__name__}: {error}")
    save_path = driver._checkpoint_path()
    driver_state_path = driver._native_driver_state_path()
    if (
        save_path is None
        or not save_path.is_file()
        or save_path.stat().st_size <= 0
        or not driver_state_path.is_file()
        or driver_state_path.stat().st_size <= 0
    ):
        return stop("paired game save/driver state did not materialize")
    if expected_succession_lifecycle is not None:
        checkpoint_metadata = (
            checkpoint.get("checkpoint")
            if isinstance(checkpoint, dict)
            else None
        )
        try:
            persisted_driver = json.loads(
                driver_state_path.read_text(encoding="utf-8-sig")
            )
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            return stop(
                "paired ordinary driver state is unreadable: "
                f"{type(error).__name__}: {error}"
            )
        persisted_checkpoint = (
            persisted_driver.get("last_checkpoint")
            if isinstance(persisted_driver, dict)
            else None
        )
        persisted_history = (
            persisted_driver.get("command_history")
            if isinstance(persisted_driver, dict)
            else None
        )
        history_index = (
            checkpoint_metadata.get("history_index")
            if isinstance(checkpoint_metadata, dict)
            else None
        )
        persisted_anchor = (
            persisted_history[history_index - 1]
            if (
                isinstance(persisted_history, list)
                and isinstance(history_index, int)
                and not isinstance(history_index, bool)
                and 1 <= history_index <= len(persisted_history)
                and isinstance(persisted_history[history_index - 1], dict)
            )
            else None
        )
        anchor_result = (
            persisted_anchor.get("result")
            if isinstance(persisted_anchor, dict)
            else None
        )
        anchor_checkpoint = (
            anchor_result.get("checkpoint")
            if isinstance(anchor_result, dict)
            else None
        )
        if not (
            isinstance(checkpoint_metadata, dict)
            and checkpoint_metadata.get("succession_lifecycle")
            == expected_succession_lifecycle
            and isinstance(persisted_driver, dict)
            and persisted_driver.get("succession_lifecycle")
            == expected_succession_lifecycle
            and isinstance(persisted_checkpoint, dict)
            and persisted_checkpoint.get("succession_lifecycle")
            == expected_succession_lifecycle
            and isinstance(persisted_anchor, dict)
            and persisted_anchor.get("command") == "save-checkpoint"
            and persisted_anchor.get("ok") is True
            and isinstance(anchor_checkpoint, dict)
            and anchor_checkpoint.get("succession_lifecycle")
            == expected_succession_lifecycle
        ):
            return stop(
                "paired checkpoint did not persist the ordinary lifecycle binding"
            )
        flow["succession_lifecycle"] = expected_succession_lifecycle
    flow["checkpoint_result"] = checkpoint
    flow["paired_checkpoint"] = {
        "game_save": str(save_path),
        "game_save_sha256": _sha256(save_path),
        "driver_state": str(driver_state_path),
        "driver_state_sha256": _sha256(driver_state_path),
    }
    flow["ok"] = True
    flow["status"] = "controlled_candidate_verified"
    return flow


def _source_structure(source: str) -> dict[str, int]:
    return {
        "logical_layers": len(
            re.findall(r"(?m)^\s*colored_emblem\s*=", source)
        ),
        "colored_emblem_blocks": len(
            re.findall(r"(?m)^\s*colored_emblem\s*=", source)
        ),
        "textured_emblem_blocks": len(
            re.findall(r"(?m)^\s*textured_emblem\s*=", source)
        ),
        "instances": len(re.findall(r"(?m)^\s*instance\s*=", source)),
        "utf8_bytes": len(source.encode("ascii")),
        "lines": len(source.splitlines()),
    }


def _source_size_contract(
    input_bytes: int,
    native_copy_bytes: object,
    *,
    require_v1_bound_exceeded: bool,
) -> tuple[dict[str, object], dict[str, bool]]:
    input_exceeds = input_bytes > 128 * 1024
    native_copy_exceeds = bool(
        isinstance(native_copy_bytes, int)
        and not isinstance(native_copy_bytes, bool)
        and native_copy_bytes > 128 * 1024
    )
    observations: dict[str, object] = {
        "requires_v1_bound_exceeded": require_v1_bound_exceeded,
        "v1_bound_bytes": 128 * 1024,
        "input_exceeds_v1_bound": input_exceeds,
        "native_copy_exceeds_v1_bound": native_copy_exceeds,
    }
    checks = {
        "input_size_contract": input_exceeds
        if require_v1_bound_exceeded
        else True,
        "native_copy_size_contract": native_copy_exceeds
        if require_v1_bound_exceeded
        else True,
    }
    return observations, checks


def _semantic_projection(source: str) -> dict[str, object]:
    flags = re.IGNORECASE | re.MULTILINE

    def text_values(pattern: str) -> list[str]:
        return [
            " ".join(value.split()).lower()
            for value in re.findall(pattern, source, flags)
        ]

    def numeric_values(pattern: str) -> list[list[float]]:
        return [
            [
                float(number)
                for number in re.findall(r"[-+]?[0-9]*\.?[0-9]+(?:e[-+]?[0-9]+)?", value)
            ]
            for value in re.findall(pattern, source, flags)
        ]

    def color_values() -> list[object]:
        values = text_values(
            r"\bcolor[123]\s*=\s*(rgb\s*\{[^}]*\}|hsv\s*\{[^}]*\}|"
            r'"[^"]+"|[a-z_][a-z0-9_]*)'
        )
        canonical: list[object] = []
        for value in values:
            match = re.fullmatch(r"rgb\s*\{([^}]*)\}", value)
            if match is None:
                canonical.append({"space": "text", "value": value})
                continue
            channels = [
                float(number)
                for number in re.findall(
                    r"[-+]?[0-9]*\.?[0-9]+(?:e[-+]?[0-9]+)?",
                    match.group(1),
                )
            ]
            if len(channels) != 3:
                canonical.append({"space": "text", "value": value})
                continue
            # CK3 accepts normalized rgb channels when every channel is in
            # [0, 1], but native Copy emits byte-domain channels. Comparing
            # both spellings in the unit interval preserves that semantics.
            normalized = (
                channels
                if all(0.0 <= channel <= 1.0 for channel in channels)
                else [channel / 255.0 for channel in channels]
            )
            canonical.append({"space": "rgb", "channels": normalized})
        return canonical

    return {
        "patterns": text_values(r'\bpattern\s*=\s*"([^"]+)"'),
        "textures": text_values(r'\btexture\s*=\s*"([^"]+)"'),
        "colors": color_values(),
        "masks": text_values(r"\bmask\s*=\s*\{([^}]*)\}"),
        "positions": numeric_values(r"\bposition\s*=\s*\{([^}]*)\}"),
        "scales": numeric_values(r"\bscale\s*=\s*\{([^}]*)\}"),
        "rotations": numeric_values(r"\brotation\s*=\s*([-+0-9.e]+)"),
        "depths": numeric_values(r"\bdepth\s*=\s*([-+0-9.e]+)"),
        "parents": text_values(
            r"\bparent\s*=\s*(\"[^\"]+\"|[a-z_][a-z0-9_]*)"
        ),
    }


def _semantic_projection_checks(
    expected: dict[str, object],
    actual: dict[str, object],
) -> dict[str, bool]:
    numeric_keys = {"positions", "scales", "rotations", "depths"}
    checks: dict[str, bool] = {}
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if key == "colors":
            checks[key] = bool(
                isinstance(expected_value, list)
                and isinstance(actual_value, list)
                and len(expected_value) == len(actual_value)
                and all(
                    isinstance(left, dict)
                    and isinstance(right, dict)
                    and left.get("space") == right.get("space")
                    and (
                        left.get("value") == right.get("value")
                        if left.get("space") == "text"
                        else isinstance(left.get("channels"), list)
                        and isinstance(right.get("channels"), list)
                        and len(left["channels"]) == len(right["channels"])
                        and all(
                            abs(float(a) - float(b)) <= 5.1e-7
                            for a, b in zip(
                                left["channels"], right["channels"]
                            )
                        )
                    )
                    for left, right in zip(expected_value, actual_value)
                )
            )
            continue
        if key == "rotations":
            expected_value = (
                [row for row in expected_value if row != [0.0]]
                if isinstance(expected_value, list)
                else expected_value
            )
            actual_value = (
                [row for row in actual_value if row != [0.0]]
                if isinstance(actual_value, list)
                else actual_value
            )
        if key not in numeric_keys:
            checks[key] = actual_value == expected_value
            continue
        checks[key] = bool(
            isinstance(expected_value, list)
            and isinstance(actual_value, list)
            and len(expected_value) == len(actual_value)
            and all(
                isinstance(expected_row, list)
                and isinstance(actual_row, list)
                and len(expected_row) == len(actual_row)
                and all(
                    abs(float(left) - float(right)) <= 5.1e-7
                    for left, right in zip(expected_row, actual_row)
                )
                for expected_row, actual_row in zip(
                    expected_value,
                    actual_value,
                )
            )
        )
    return checks


def _projection_summary(projection: dict[str, object]) -> dict[str, object]:
    wire = json.dumps(
        projection,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return {
        "sha256": hashlib.sha256(wire).hexdigest(),
        "field_counts": {
            key: len(value) if isinstance(value, list) else 0
            for key, value in projection.items()
        },
    }


def _load_large_source(
    path: Path,
) -> tuple[str, dict[str, object]]:
    resolved = path.resolve()
    raw = resolved.read_bytes()
    try:
        decoded = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise RuntimeError("large coat-of-arms source must be ASCII") from error
    encoded = encode_coat_of_arms_source_transport_v2(decoded)
    wire = encoded.source.encode("ascii")
    projection = _semantic_projection(encoded.source)
    return encoded.source, {
        "path": str(resolved),
        "raw_bytes": len(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "wire_bytes": len(wire),
        "wire_sha256": encoded.source_sha256,
        "line_endings_normalized": raw != wire,
        "structure": _source_structure(encoded.source),
        "semantic_projection": _projection_summary(projection),
    }


def _load_reference_preview(path: Path) -> tuple[str, dict[str, object]]:
    resolved = path.resolve()
    raw = resolved.read_bytes()
    if not raw:
        raise RuntimeError("reference preview is empty")
    digest = hashlib.sha256(raw).hexdigest().upper()
    return base64.b64encode(raw).decode("ascii"), {
        "path": str(resolved),
        "png_bytes": len(raw),
        "png_sha256": digest,
    }


def _load_picture_corpus(path: Path) -> list[dict[str, object]]:
    resolved = path.resolve()
    if not resolved.is_dir():
        raise RuntimeError(f"picture corpus directory is missing: {resolved}")
    case_directories = sorted(
        child
        for child in resolved.iterdir()
        if child.is_dir() and re.fullmatch(r"picture-[0-9]{2}", child.name)
    )
    if len(case_directories) != 7:
        raise RuntimeError(
            f"picture corpus must contain exactly seven cases, found {len(case_directories)}"
        )
    cases: list[dict[str, object]] = []
    for directory in case_directories:
        source, source_receipt = _load_large_source(
            directory / "coat_of_arms.txt"
        )
        preview, preview_receipt = _load_reference_preview(
            directory / "canonical-preview-230.png"
        )
        cases.append(
            {
                "id": directory.name,
                "source": source,
                "source_receipt": source_receipt,
                "preview_base64": preview,
                "preview_receipt": preview_receipt,
                "require_v1_bound_exceeded": True,
            }
        )
    return cases


def _load_single_reference_case(path: Path) -> dict[str, object]:
    resolved = path.resolve()
    if not resolved.is_dir():
        raise RuntimeError(f"single reference case directory is missing: {resolved}")
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", resolved.name) is None:
        raise RuntimeError(
            "single reference case directory name must be a safe 1-64 character id"
        )
    source, source_receipt = _load_large_source(resolved / "coat_of_arms.txt")
    preview, preview_receipt = _load_reference_preview(
        resolved / "canonical-preview-230.png"
    )
    return {
        "id": resolved.name,
        "source": source,
        "source_receipt": source_receipt,
        "preview_base64": preview,
        "preview_receipt": preview_receipt,
        "require_v1_bound_exceeded": False,
    }


def _framebuffer_gate(
    call: dict[str, object],
    *,
    thresholds: dict[str, float] | None = None,
) -> dict[str, object]:
    body = _structured(call)
    comparison = (
        body.get("comparison")
        if isinstance(body.get("comparison"), dict)
        else {}
    )
    best = (
        comparison.get("bestMatch")
        if isinstance(comparison.get("bestMatch"), dict)
        else {}
    )
    metrics = (
        comparison.get("metrics")
        if isinstance(comparison.get("metrics"), dict)
        else {}
    )
    spatial = metrics.get("spatialMeanAbsoluteError8x8")
    spatial_values = [
        float(value)
        for row in spatial
        if isinstance(row, list)
        for value in row
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ] if isinstance(spatial, list) else []
    worst_spatial = max(spatial_values) if spatial_values else None
    active_thresholds = thresholds or FRAMEBUFFER_GATE_THRESHOLDS
    calibrated_schema = body.get("schema") in {
        "ck3-coat-of-arms-framebuffer-comparison-v2",
        "ck3-coat-of-arms-framebuffer-comparison-v3",
    }
    is_v3 = body.get("schema") == "ck3-coat-of-arms-framebuffer-comparison-v3"
    calibration = body.get("calibration") if calibrated_schema else None
    checks = {
        "call_not_error": call.get("is_error") is False,
        "schema": body.get("schema") in {
            "ck3-coat-of-arms-framebuffer-comparison-v1",
            "ck3-coat-of-arms-framebuffer-comparison-v2",
            "ck3-coat-of-arms-framebuffer-comparison-v3",
        },
        "route_stable": body.get("routeStable") is True,
        "read_only_no_ocr_or_input": (
            body.get("readOnly") is True
            and body.get("usesOcr") is False
            and body.get("usesKeyboard") is False
            and body.get("usesMouse") is False
        ),
        "reference_independent_localization": bool(
            isinstance(calibration, dict)
            and calibration.get("referenceIndependent") is True
            and comparison.get("referenceUsedForLocalization") is False
            and (not is_v3 or comparison.get("referenceUsedForRegistration") is False)
            and (not is_v3 or calibration.get("uvRegistered") is True)
        ) if calibrated_schema else True,
        "locator_loss": True if calibrated_schema else (
            isinstance(best.get("locatorLoss"), (int, float))
            and not isinstance(best.get("locatorLoss"), bool)
            and best["locatorLoss"]
            <= active_thresholds["maximum_locator_loss"]
        ),
        "distinct_margin": True if calibrated_schema else (
            isinstance(best.get("distinctMargin"), (int, float))
            and not isinstance(best.get("distinctMargin"), bool)
            and best["distinctMargin"]
            >= active_thresholds["minimum_distinct_margin"]
        ),
        "mean_absolute_error": (
            isinstance(metrics.get("meanAbsoluteError"), (int, float))
            and not isinstance(metrics.get("meanAbsoluteError"), bool)
            and metrics["meanAbsoluteError"]
            <= active_thresholds["maximum_mean_absolute_error"]
        ),
        "color_mse": (
            isinstance(metrics.get("colorMse"), (int, float))
            and not isinstance(metrics.get("colorMse"), bool)
            and metrics["colorMse"]
            <= active_thresholds["maximum_color_mse"]
        ),
        "edge_loss": (
            isinstance(metrics.get("edgeLoss"), (int, float))
            and not isinstance(metrics.get("edgeLoss"), bool)
            and metrics["edgeLoss"]
            <= active_thresholds["maximum_edge_loss"]
        ),
        "worst_spatial_mean_absolute_error": (
            worst_spatial is not None
            and worst_spatial
            <= active_thresholds["maximum_spatial_mean_absolute_error"]
        ),
    }
    return {
        "ok": all(checks.values()),
        "thresholds": dict(active_thresholds),
        "worst_spatial_mean_absolute_error": worst_spatial,
        "checks": checks,
        "call": call,
    }


def _native_aligned_reference(
    call: dict[str, object],
) -> tuple[str, dict[str, object]]:
    body = _structured(call)
    comparison = body.get("comparison")
    best = (
        comparison.get("bestMatch")
        if isinstance(comparison, dict)
        and isinstance(comparison.get("bestMatch"), dict)
        else {}
    )
    encoded = best.get("alignedContentPngBase64")
    expected_sha256 = best.get("alignedContentPngSha256")
    if not isinstance(encoded, str) or not isinstance(expected_sha256, str):
        raise RuntimeError("native comparison lacks an aligned reference PNG")
    try:
        raw = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError) as error:
        raise RuntimeError("native aligned reference PNG is malformed") from error
    actual_sha256 = hashlib.sha256(raw).hexdigest().upper()
    if actual_sha256 != expected_sha256.upper():
        raise RuntimeError("native aligned reference PNG SHA-256 mismatch")
    return encoded, {
        "png_bytes": len(raw),
        "png_sha256": actual_sha256,
        "source": "original-native-apply",
    }


def _source_receipt_from_text(
    source: str, *, source_label: str
) -> dict[str, object]:
    payload = source.encode("ascii")
    digest = hashlib.sha256(payload).hexdigest()
    return {
        "path": source_label,
        "raw_bytes": len(payload),
        "raw_sha256": digest,
        "wire_bytes": len(payload),
        "wire_sha256": digest,
        "line_endings_normalized": False,
        "structure": _source_structure(source),
        "semantic_projection": _projection_summary(
            _semantic_projection(source)
        ),
    }


def _load_syntax_matrix(path: Path = SYNTAX_MATRIX) -> dict[str, object]:
    resolved = path.resolve()
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {
        "schema",
        "schema_version",
        "cases",
    }:
        raise RuntimeError("syntax matrix must contain exactly the v1 fields")
    if (
        payload.get("schema") != "ck3-coat-of-arms-syntax-matrix-v1"
        or payload.get("schema_version") != 1
        or isinstance(payload.get("schema_version"), bool)
        or not isinstance(payload.get("cases"), list)
        or not payload["cases"]
    ):
        raise RuntimeError("syntax matrix header is invalid")
    normalized: list[dict[str, str]] = []
    identifiers: set[str] = set()
    for index, value in enumerate(payload["cases"]):
        if not isinstance(value, dict) or set(value) != {
            "id",
            "purpose",
            "expected_detection",
            "apply_expectation",
            "source",
        }:
            raise RuntimeError(f"syntax matrix case {index} has invalid fields")
        identifier = value.get("id")
        purpose = value.get("purpose")
        detection = value.get("expected_detection")
        apply_expectation = value.get("apply_expectation")
        source = value.get("source")
        if (
            not isinstance(identifier, str)
            or not re.fullmatch(r"[a-z0-9_]+", identifier)
            or identifier in identifiers
        ):
            raise RuntimeError(f"syntax matrix case {index} has invalid id")
        if not isinstance(purpose, str) or not purpose:
            raise RuntimeError(f"syntax matrix case {identifier} lacks purpose")
        if detection not in {"detected", "not_detected"}:
            raise RuntimeError(
                f"syntax matrix case {identifier} has invalid detection expectation"
            )
        if apply_expectation not in {"required", "observe", "never"}:
            raise RuntimeError(
                f"syntax matrix case {identifier} has invalid apply expectation"
            )
        if detection == "not_detected" and apply_expectation != "never":
            raise RuntimeError(
                f"syntax matrix negative case {identifier} cannot request apply"
            )
        try:
            encoded_source = encode_coat_of_arms_source_v1(source)
        except ValueError as error:
            raise RuntimeError(
                f"syntax matrix case {identifier} source is invalid: {error}"
            ) from error
        identifiers.add(identifier)
        normalized.append(
            {
                "id": identifier,
                "purpose": purpose,
                "expected_detection": detection,
                "apply_expectation": apply_expectation,
                "source": encoded_source.source.replace("\r\n", "\n"),
            }
        )
    return {
        "schema": payload["schema"],
        "schema_version": 1,
        "path": str(resolved),
        "sha256": _sha256(resolved),
        "cases": normalized,
    }


def _schema_has_required_fields(
    schema: object, required: set[str]
) -> bool:
    required_value = (
        schema.get("required", []) if isinstance(schema, dict) else None
    )
    return bool(
        isinstance(schema, dict)
        and schema.get("additionalProperties") is False
        and isinstance(required_value, list)
        and set(required_value) == required
        and isinstance(schema.get("properties"), dict)
        and required <= set(schema["properties"])
    )


def _schema_is_zero_input(schema: object) -> bool:
    return bool(
        isinstance(schema, dict)
        and schema.get("type") == "object"
        and schema.get("properties") == {}
        and schema.get("required", []) == []
    )


def _is_nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


async def _collect_vfs_mount_order_diagnostics(
    client: Client,
    record: Any,
    settle_timeout_seconds: float = 60.0,
) -> dict[str, object]:
    """Poll a bounded private observer until fixture mounts settle or timeout."""

    settle_deadline = time.monotonic() + max(0.0, settle_timeout_seconds)
    poll_count = 0
    call: dict[str, object] = {}
    observer: object = None
    observer_kind = "missing"
    while True:
        call = await _call(client, BRIDGE_DIAGNOSTICS_TOOL)
        record(call)
        poll_count += 1
        body = _structured(call)
        diagnostics = body.get("diagnostics")
        private_observers = (
            diagnostics.get("private_observers")
            if isinstance(diagnostics, dict)
            else None
        )
        if not isinstance(private_observers, dict):
            private_observers = body.get("private_observers")
        observer = None
        observer_kind = "missing"
        if isinstance(private_observers, dict):
            observer = private_observers.get(
                "physfs_mounted_data_observer_v1"
            )
            if isinstance(observer, dict):
                observer_kind = "physfs_mounted_data_observer_v1"
            else:
                observer = private_observers.get(
                    "vfs_mount_lifecycle_observer_v1"
                )
                if isinstance(observer, dict):
                    observer_kind = "vfs_mount_lifecycle_observer_v1"
        candidate = observer if isinstance(observer, dict) else {}
        candidate_rows = candidate.get(
            "rows"
            if observer_kind == "physfs_mounted_data_observer_v1"
            else "publishers"
        )
        candidate_paths: list[str] = []
        if isinstance(candidate_rows, list):
            for row in candidate_rows:
                if not isinstance(row, dict):
                    continue
                path = row.get("path")
                preview = (
                    path
                    if isinstance(path, str)
                    else path.get("preview") if isinstance(path, dict) else None
                )
                if isinstance(preview, str):
                    candidate_paths.append(preview.casefold())
        fixtures_settled = all(
            any(fragment.casefold() in path for path in candidate_paths)
            for fragment in VFS_MOUNT_ORDER_EXPECTED_FRAGMENTS
        )
        if fixtures_settled or time.monotonic() >= settle_deadline:
            break
        await asyncio.sleep(2.0)

    observer = observer if isinstance(observer, dict) else {}
    caller_local = observer_kind == "physfs_mounted_data_observer_v1"
    published_rows = observer.get("rows" if caller_local else "publishers")
    rows = published_rows if isinstance(published_rows, list) else []
    slot_count = observer.get("row_count" if caller_local else "publisher_slot_count")

    ordinals: list[int] = []
    path_previews: list[str] = []
    rows_complete = True
    all_returns_seen = True
    for row in rows:
        if not isinstance(row, dict):
            rows_complete = False
            all_returns_seen = False
            continue
        ordinal = row.get("ordinal")
        if caller_local:
            preview = row.get("path")
            row_complete = (
                _is_nonnegative_int(ordinal)
                and ordinal != 0
                and _is_nonnegative_int(row.get("raw_result"))
                and isinstance(row.get("success"), bool)
                and isinstance(preview, str)
                and bool(preview)
            )
            return_seen = True
        else:
            entry_sequence = row.get("entry_sequence")
            return_sequence = row.get("return_sequence")
            path = row.get("path")
            preview = path.get("preview") if isinstance(path, dict) else None
            row_complete = (
                _is_nonnegative_int(ordinal)
                and ordinal != 0
                and _is_nonnegative_int(entry_sequence)
                and entry_sequence != 0
                and _is_nonnegative_int(return_sequence)
                and isinstance(row.get("return_seen"), bool)
                and isinstance(preview, str)
                and bool(preview)
                and isinstance(row.get("manager_before"), dict)
                and isinstance(row.get("manager_after"), dict)
            )
            return_seen = row.get("return_seen") is True
        if not row_complete:
            rows_complete = False
        if isinstance(ordinal, int) and not isinstance(ordinal, bool):
            ordinals.append(ordinal)
        if isinstance(preview, str):
            path_previews.append(preview)
        if not return_seen:
            all_returns_seen = False

    folded_paths = [value.casefold() for value in path_previews]
    expected_indices: dict[str, int | None] = {}
    for fragment in VFS_MOUNT_ORDER_EXPECTED_FRAGMENTS:
        folded_fragment = fragment.casefold()
        expected_indices[fragment] = next(
            (
                index
                for index, value in enumerate(folded_paths)
                if folded_fragment in value
            ),
            None,
        )
    expected_positions = list(expected_indices.values())
    expected_mounts_observed = all(
        isinstance(value, int) for value in expected_positions
    )
    expected_mount_order = bool(
        expected_mounts_observed
        and expected_positions == sorted(expected_positions)
        and len(set(expected_positions)) == len(expected_positions)
    )

    publisher_entry_count = observer.get(
        "call_count" if caller_local else "publisher_entry_count"
    )
    publisher_return_count = (
        publisher_entry_count
        if caller_local
        else observer.get("publisher_return_count")
    )
    publisher_success_count = observer.get(
        "success_count" if caller_local else "publisher_success_count"
    )
    publisher_failure_count = observer.get(
        "failure_count" if caller_local else "publisher_failure_count"
    )
    count_values_valid = all(
        _is_nonnegative_int(value)
        for value in (
            publisher_entry_count,
            publisher_return_count,
            publisher_success_count,
            publisher_failure_count,
        )
    )
    counts_coherent = bool(
        count_values_valid
        and publisher_entry_count >= len(rows)
        and publisher_return_count <= publisher_entry_count
        and publisher_success_count + publisher_failure_count
        == publisher_return_count
    )
    checks = {
        "call_not_error": call.get("is_error") is False,
        "observer_present": bool(observer),
        "private_read_only_not_public": (
            observer.get("private_build") is True
            and observer.get("read_only") is True
            and observer.get("public_capability") is False
        ),
        "installed_without_failure": (
            observer.get("installed") is True
            and observer.get("failure_flags") == 0
        ),
        "bounded_nonempty_snapshot": (
            _is_nonnegative_int(slot_count)
            and 0 < slot_count <= (128 if caller_local else 64)
            and slot_count == len(rows)
        ),
        "publisher_rows_complete": rows_complete and bool(rows),
        "publisher_ordinals_strictly_increasing": (
            len(ordinals) == len(rows)
            and all(
                previous < current
                for previous, current in zip(ordinals, ordinals[1:])
            )
        ),
        "publisher_returns_complete": all_returns_seen and bool(rows),
        "publisher_counts_coherent": counts_coherent,
        "fixture_mounts_observed": expected_mounts_observed,
        "fixture_mount_order_matches_dlc_load": expected_mount_order,
    }
    return {
        "ok": all(checks.values()),
        "scope": "bounded startup mount publisher order; no per-resource winner claim",
        "observer_kind": observer_kind,
        "poll_count": poll_count,
        "expected_fragments": list(VFS_MOUNT_ORDER_EXPECTED_FRAGMENTS),
        "expected_fragment_indices": expected_indices,
        "path_previews": path_previews,
        "checks": checks,
        "observer": observer,
        "call": call,
    }


async def _collect_vfs_asset_projections(
    client: Client,
    record: Any,
    game_directory: str,
    logical_paths: tuple[str, ...],
) -> dict[str, object]:
    """Call the public MCP projection once per predeclared direct DDS path."""

    projections: list[dict[str, object]] = []
    for logical_path in logical_paths:
        call = await _call(
            client,
            VFS_ASSET_PROJECTION_TOOL,
            {
                "game_directory": game_directory,
                "logical_path": logical_path,
            },
        )
        record(call)
        body = _structured(call)
        winner = body.get("winner")
        provenance = body.get("provenance")
        checks = {
            "mcp_call_succeeded": call.get("is_error") is False,
            "requested_path_preserved": body.get("logical_path") == logical_path,
            "direct_dds_winner_projected": (
                body.get("status") == "projected_direct_asset_winner"
                and isinstance(winner, dict)
                and isinstance(winner.get("asset_sha256"), str)
                and len(winner["asset_sha256"]) == 64
            ),
            "bounded_claim_scope_preserved": (
                isinstance(provenance, dict)
                and provenance.get("mount_order_observed") is True
                and provenance.get("source_bytes_observed") is True
                and provenance.get("engine_resolver_called") is False
                and provenance.get("resource_registration_observed") is False
                and provenance.get("replace_path_applied") is False
                and provenance.get("definition_merge_applied") is False
                and provenance.get("claim_scope")
                == "direct_dds_path_winner_projection_only"
            ),
        }
        projections.append(
            {
                "logical_path": logical_path,
                "call": call,
                "projection": body,
                "checks": checks,
                "ok": all(checks.values()),
            }
        )
    checks = {
        "paths_requested": bool(logical_paths),
        "paths_unique": len(logical_paths) == len(set(logical_paths)),
        "all_projections_passed": bool(projections)
        and all(value.get("ok") is True for value in projections),
    }
    return {
        "schema": "ck3-coat-of-arms-vfs-asset-projection-live-run-v1",
        "schema_version": 1,
        "game_directory": game_directory,
        "requested_paths": list(logical_paths),
        "projections": projections,
        "checks": checks,
        "ok": all(checks.values()),
    }


async def _collect_syntax_matrix(
    client: Client,
    matrix: dict[str, object],
    record: Any,
) -> dict[str, object]:
    capability_call = await _call(client, "ck3_get_capabilities")
    record(capability_call)
    capabilities = _structured(capability_call)
    snapshot_call: dict[str, object] | None = None
    if capability_call.get("is_error") is not False:
        return {
            "ok": False,
            "error": "post-route capabilities call failed",
            "capabilities_call": capability_call,
            "matrix": matrix,
            "cases": [],
        }
    if capabilities.get("snapshot") is True:
        snapshot_call = await _call(client, SNAPSHOT_TOOL)
        record(snapshot_call)
        snapshot = _structured(snapshot_call)
        revision = snapshot.get("revision")
        if (
            snapshot_call.get("is_error") is not False
            or isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 1
        ):
            return {
                "ok": False,
                "error": "post-route snapshot lacks a positive revision",
                "capabilities_call": capability_call,
                "snapshot_call": snapshot_call,
                "matrix": matrix,
                "cases": [],
            }
        binding_mode = "snapshot"
    elif capabilities.get("snapshot") is False:
        revision = 0
        binding_mode = "frontend"
    else:
        return {
            "ok": False,
            "error": "post-route capabilities lack a boolean snapshot state",
            "capabilities_call": capability_call,
            "matrix": matrix,
            "cases": [],
        }

    export_arguments = {"expected_revision": revision}
    before_export_call = await _call(
        client, EXPORT_COAT_OF_ARMS_TOOL, export_arguments
    )
    record(before_export_call)
    before_export = _structured(before_export_call)
    if (
        before_export_call.get("is_error") is not False
        or before_export.get("status") != "exported"
    ):
        return {
            "ok": False,
            "error": "initial native Copy/export failed",
            "binding_mode": binding_mode,
            "expected_revision": revision,
            "capabilities_call": capability_call,
            "snapshot_call": snapshot_call,
            "initial_export": before_export_call,
            "matrix": matrix,
            "cases": [],
        }

    cases: list[dict[str, object]] = []
    current_export = before_export
    matrix_cases = matrix.get("cases")
    assert isinstance(matrix_cases, list)
    for value in matrix_cases:
        assert isinstance(value, dict)
        source = value["source"]
        detect_call = await _call(
            client,
            PROBE_COAT_OF_ARMS_TOOL,
            {
                "source": source,
                "expected_revision": revision,
                "apply": False,
            },
        )
        record(detect_call)
        detection = _structured(detect_call)
        apply_call: dict[str, object] | None = None
        apply_result: dict[str, object] = {}
        if (
            detection.get("status") == "detected"
            and value["apply_expectation"] != "never"
        ):
            apply_call = await _call(
                client,
                PROBE_COAT_OF_ARMS_TOOL,
                {
                    "source": source,
                    "expected_revision": revision,
                    "apply": True,
                },
            )
            record(apply_call)
            apply_result = _structured(apply_call)
        after_export_call = await _call(
            client, EXPORT_COAT_OF_ARMS_TOOL, export_arguments
        )
        record(after_export_call)
        after_export = _structured(after_export_call)

        apply_expectation = value["apply_expectation"]
        if apply_expectation == "never":
            apply_evidence_complete = apply_call is None
        elif apply_expectation == "required":
            apply_evidence_complete = bool(
                apply_call is not None
                and apply_call.get("is_error") is False
                and apply_result.get("status") == "applied"
            )
        else:
            apply_evidence_complete = bool(
                apply_call is not None
                and apply_call.get("is_error") is False
                and apply_result.get("status") in {"applied", "apply_failed"}
            )
        expected_detection = value["expected_detection"]
        negative_state_unchanged = bool(
            expected_detection != "not_detected"
            or (
                isinstance(current_export.get("source_sha256"), str)
                and after_export.get("source_sha256")
                == current_export.get("source_sha256")
            )
        )
        checks = {
            "detect_call_not_error": detect_call.get("is_error") is False,
            "detection_matches_expectation": detection.get("status")
            == expected_detection,
            "apply_evidence_complete": apply_evidence_complete,
            "after_export_not_error": after_export_call.get("is_error")
            is False,
            "after_export_available": after_export.get("status") == "exported",
            "negative_state_unchanged": negative_state_unchanged,
        }
        cases.append(
            {
                "id": value["id"],
                "purpose": value["purpose"],
                "expected_detection": expected_detection,
                "apply_expectation": apply_expectation,
                "before_source_sha256": current_export.get("source_sha256"),
                "detect": detect_call,
                "apply": apply_call,
                "after_export": after_export_call,
                "checks": checks,
                "ok": all(checks.values()),
            }
        )
        if after_export.get("status") == "exported":
            current_export = after_export

    return {
        "ok": all(case.get("ok") is True for case in cases),
        "binding_mode": binding_mode,
        "expected_revision": revision,
        "capabilities_call": capability_call,
        "snapshot_call": snapshot_call,
        "initial_export": before_export_call,
        "matrix": matrix,
        "cases": cases,
    }


async def _collect_commit_roundtrip(
    client: Client,
    record: Any,
) -> dict[str, object]:
    source = (
        'coa={pattern="pattern_solid.dds" color1=rgb { 17 83 149 } '
        'color2=white color3=black colored_emblem={texture="ce_martlet.dds" '
        'color1=white mask={1} instance={position={0.37 0.61} '
        'scale={-0.42 0.58} rotation=-23 depth=1.01}}}'
    )
    capability_call = await _call(client, "ck3_get_capabilities")
    record(capability_call)
    capabilities = _structured(capability_call)
    snapshot_call: dict[str, object] | None = None
    if capability_call.get("is_error") is not False:
        return {"ok": False, "error": "commit capabilities call failed"}
    if capabilities.get("snapshot") is True:
        snapshot_call = await _call(client, SNAPSHOT_TOOL)
        record(snapshot_call)
        revision = _structured(snapshot_call).get("revision")
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
            return {"ok": False, "error": "commit snapshot lacks revision"}
        binding_mode = "snapshot"
    elif capabilities.get("snapshot") is False:
        revision = 0
        binding_mode = "frontend"
    else:
        return {"ok": False, "error": "commit capabilities lack snapshot state"}

    apply_call = await _call(
        client,
        PROBE_COAT_OF_ARMS_TOOL,
        {"source": source, "expected_revision": revision, "apply": True},
    )
    record(apply_call)
    before_export_call = await _call(
        client, EXPORT_COAT_OF_ARMS_TOOL, {"expected_revision": revision}
    )
    record(before_export_call)
    commit_call = await _call(client, COMMIT_DYNASTY_COAT_OF_ARMS_TOOL)
    record(commit_call)
    reopen_call = await _call(client, ACTIVATE_COAT_OF_ARMS_DESIGNER_TOOL)
    record(reopen_call)
    after_export_call = await _call(
        client, EXPORT_COAT_OF_ARMS_TOOL, {"expected_revision": revision}
    )
    record(after_export_call)

    applied = _structured(apply_call)
    before_export = _structured(before_export_call)
    committed = _structured(commit_call)
    reopened = _structured(reopen_call)
    after_export = _structured(after_export_call)
    before_sha = before_export.get("source_sha256")
    checks = {
        "apply_not_error": apply_call.get("is_error") is False,
        "applied": applied.get("status") == "applied",
        "before_exported": (
            before_export_call.get("is_error") is False
            and before_export.get("status") == "exported"
            and isinstance(before_sha, str)
            and len(before_sha) == 64
        ),
        "commit_not_error": commit_call.get("is_error") is False,
        "commit_verified": (
            committed.get("status") == "verified"
            and committed.get("action") == "commit_dynasty_coat_of_arms"
            and committed.get("postcondition_verified") is True
            and isinstance(committed.get("after"), dict)
            and committed["after"].get("route") == "ruler_designer"
        ),
        "commit_no_ocr_keyboard_mouse": (
            committed.get("uses_ocr") is False
            and committed.get("uses_keyboard") is False
            and committed.get("uses_mouse") is False
        ),
        "reopen_verified": (
            reopen_call.get("is_error") is False
            and reopened.get("status") == "verified"
            and isinstance(reopened.get("after"), dict)
            and reopened["after"].get("route") == "coat_of_arms_designer"
        ),
        "after_exported": (
            after_export_call.get("is_error") is False
            and after_export.get("status") == "exported"
        ),
        "native_copy_bytes_preserved_after_commit_reopen": (
            isinstance(before_sha, str)
            and after_export.get("source_sha256") == before_sha
            and after_export.get("source_bytes") == before_export.get("source_bytes")
            and after_export.get("source") == before_export.get("source")
        ),
    }
    return {
        "ok": all(checks.values()),
        "binding_mode": binding_mode,
        "expected_revision": revision,
        "source": source,
        "source_sha256": hashlib.sha256(source.encode("ascii")).hexdigest().upper(),
        "capabilities_call": capability_call,
        "snapshot_call": snapshot_call,
        "apply": apply_call,
        "before_commit_export": before_export_call,
        "commit": commit_call,
        "reopen": reopen_call,
        "after_reopen_export": after_export_call,
        "checks": checks,
    }


async def _collect_large_source_roundtrip(
    client: Client,
    source: str,
    receipt: dict[str, object],
    record: Any,
    *,
    require_v1_bound_exceeded: bool = True,
) -> dict[str, object]:
    capability_call = await _call(client, "ck3_get_capabilities")
    record(capability_call)
    capabilities = _structured(capability_call)
    snapshot_call: dict[str, object] | None = None
    if capability_call.get("is_error") is not False:
        return {"ok": False, "error": "large-source capabilities call failed"}
    if capabilities.get("snapshot") is True:
        snapshot_call = await _call(client, SNAPSHOT_TOOL)
        record(snapshot_call)
        revision = _structured(snapshot_call).get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 1
        ):
            return {"ok": False, "error": "large-source snapshot lacks revision"}
        binding_mode = "snapshot"
    elif capabilities.get("snapshot") is False:
        revision = 0
        binding_mode = "frontend"
    else:
        return {
            "ok": False,
            "error": "large-source capabilities lack snapshot state",
        }

    payload = source.encode("ascii")
    chunks = [
        payload[
            offset : offset + COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES
        ]
        for offset in range(
            0,
            len(payload),
            COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES,
        )
    ]
    source_sha256 = hashlib.sha256(payload).hexdigest()
    metadata = {
        "source_sha256": source_sha256,
        "expected_revision": revision,
        "apply": True,
        "expected_game_version": COAT_OF_ARMS_SOURCE_V1_GAME_VERSION,
        "expected_executable_sha256": (
            COAT_OF_ARMS_SOURCE_V1_EXECUTABLE_SHA256
        ),
    }
    chunk_receipts = [
        {
            "chunk_index": index,
            "chunk_bytes": len(chunk),
            "chunk_sha256": hashlib.sha256(chunk).hexdigest(),
        }
        for index, chunk in enumerate(chunks)
    ]
    begin_call = await _call(
        client,
        BEGIN_COAT_OF_ARMS_UPLOAD_TOOL,
        {
            "total_bytes": len(payload),
            "chunk_count": len(chunks),
            "chunk_encoding": "base64",
            **metadata,
        },
    )
    record(begin_call)
    begun = _structured(begin_call)
    append_calls: list[dict[str, object]] = []
    if begin_call.get("is_error") is False:
        for index, chunk in enumerate(chunks):
            item = await _call(
                client,
                APPEND_COAT_OF_ARMS_UPLOAD_TOOL,
                {
                    "upload_id": begun.get("upload_id"),
                    "generation": begun.get("generation"),
                    "chunk_index": index,
                    "chunk_count": len(chunks),
                    "chunk_encoding": "base64",
                    "chunk_bytes": len(chunk),
                    "chunk_sha256": hashlib.sha256(chunk).hexdigest(),
                    "chunk_base64": base64.b64encode(chunk).decode("ascii"),
                    **metadata,
                },
            )
            record(item)
            append_calls.append(item)
            if item.get("is_error") is not False:
                break

    all_chunks_sent = bool(
        len(append_calls) == len(chunks)
        and all(call.get("is_error") is False for call in append_calls)
    )
    commit_call: dict[str, object] | None = None
    export_call: dict[str, object] | None = None
    if all_chunks_sent:
        commit_call = await _call(
            client,
            COMMIT_COAT_OF_ARMS_UPLOAD_TOOL,
            {
                "upload_id": begun.get("upload_id"),
                "generation": begun.get("generation"),
                "chunk_count": len(chunks),
                **metadata,
            },
        )
        record(commit_call)
        if commit_call.get("is_error") is False:
            export_call = await _call(
                client,
                EXPORT_COAT_OF_ARMS_TOOL,
                {"expected_revision": revision},
            )
            record(export_call)

    committed = _structured(commit_call or {})
    native_result = (
        committed.get("result")
        if isinstance(committed.get("result"), dict)
        else {}
    )
    exported = _structured(export_call or {})
    exported_source = exported.get("source")
    input_projection = _semantic_projection(source)
    output_projection = (
        _semantic_projection(exported_source)
        if isinstance(exported_source, str)
        else {}
    )
    input_structure = _source_structure(source)
    output_structure = (
        _source_structure(exported_source)
        if isinstance(exported_source, str)
        else {}
    )
    semantic_checks = _semantic_projection_checks(
        input_projection,
        output_projection,
    )
    size_observations, size_checks = _source_size_contract(
        len(payload),
        exported.get("source_bytes"),
        require_v1_bound_exceeded=require_v1_bound_exceeded,
    )
    checks = {
        **size_checks,
        "begin_not_error": begin_call.get("is_error") is False,
        "begin_receiving": begun.get("status") == "receiving",
        "all_chunks_sent": all_chunks_sent,
        "last_chunk_ready": bool(
            append_calls
            and _structured(append_calls[-1]).get("status") == "ready"
        ),
        "commit_not_error": bool(
            commit_call is not None
            and commit_call.get("is_error") is False
        ),
        "commit_applied": bool(
            committed.get("status") == "committed"
            and native_result.get("status") == "applied"
            and native_result.get("detected") is True
            and native_result.get("applied") is True
        ),
        "commit_source_identity": bool(
            native_result.get("source_bytes") == len(payload)
            and native_result.get("source_sha256") == source_sha256
        ),
        "native_copy_exported": bool(
            export_call is not None
            and export_call.get("is_error") is False
            and exported.get("status") == "exported"
        ),
        "drawn_instance_count_preserved": bool(
            output_structure.get("instances") == input_structure["instances"]
        ),
        "logical_layer_count_preserved": bool(
            output_structure.get("logical_layers")
            == input_structure["logical_layers"]
        ),
        "colored_emblem_block_count_preserved": bool(
            output_structure.get("colored_emblem_blocks")
            == input_structure["colored_emblem_blocks"]
        ),
        "semantic_field_sequences_preserved": all(semantic_checks.values()),
    }
    return {
        "ok": all(checks.values()),
        "binding_mode": binding_mode,
        "expected_revision": revision,
        "input": receipt,
        "chunk_count": len(chunks),
        "chunks": chunk_receipts,
        "begin": begin_call,
        "append": append_calls,
        "commit": commit_call,
        "native_copy": export_call,
        "output_structure": output_structure,
        "output_semantic_projection": _projection_summary(output_projection),
        "semantic_checks": semantic_checks,
        "size_observations": size_observations,
        "checks": checks,
    }


async def _apply_calibration_source(
    client: Client,
    source: str,
    record: Any,
) -> dict[str, object]:
    capability_call = await _call(client, "ck3_get_capabilities")
    record(capability_call)
    capabilities = _structured(capability_call)
    snapshot_call: dict[str, object] | None = None
    if capability_call.get("is_error") is not False:
        return {"ok": False, "error": "calibration capabilities call failed"}
    if capabilities.get("snapshot") is True:
        snapshot_call = await _call(client, SNAPSHOT_TOOL)
        record(snapshot_call)
        revision = _structured(snapshot_call).get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 1
        ):
            return {"ok": False, "error": "calibration snapshot lacks revision"}
    elif capabilities.get("snapshot") is False:
        revision = 0
    else:
        return {"ok": False, "error": "calibration capabilities lack snapshot state"}
    call = await _call(
        client,
        PROBE_COAT_OF_ARMS_TOOL,
        {"source": source, "expected_revision": revision, "apply": True},
    )
    record(call)
    result = _structured(call)
    return {
        "ok": bool(
            call.get("is_error") is False
            and result.get("status") == "applied"
            and result.get("detected") is True
            and result.get("applied") is True
        ),
        "source_sha256": hashlib.sha256(source.encode("ascii")).hexdigest().upper(),
        "expected_revision": revision,
        "capabilities": capability_call,
        "snapshot": snapshot_call,
        "apply": call,
    }


async def _calibrate_picture_corpus_surface(
    client: Client,
    record: Any,
) -> dict[str, object]:
    calibration_id = "picture-corpus"
    red_source = (
        'coa={pattern="pattern_solid.dds" color1=rgb { 255 0 0 } '
        'color2=rgb { 255 0 0 } color3=rgb { 255 0 0 }}'
    )
    green_source = (
        'coa={pattern="pattern_solid.dds" color1=rgb { 0 255 0 } '
        'color2=rgb { 0 255 0 } color3=rgb { 0 255 0 }}'
    )
    black_source = (
        'coa={pattern="pattern_solid.dds" color1=rgb { 0 0 0 } '
        'color2=rgb { 0 0 0 } color3=rgb { 0 0 0 }}'
    )
    marker_blocks = []
    for depth, (x, y) in enumerate(
        (
            (0.30, 0.30),
            (0.50, 0.30),
            (0.70, 0.30),
            (0.30, 0.50),
            (0.50, 0.50),
            (0.70, 0.50),
            (0.30, 0.70),
            (0.50, 0.70),
            (0.70, 0.70),
        ),
        start=1,
    ):
        marker_blocks.append(
            'colored_emblem={texture="ce_block_02.dds" '
            'color1=rgb { 255 255 255 } color2=rgb { 255 255 255 } '
            'color3=rgb { 255 255 255 } instance={'
            f'position={{ {x:.2f} {y:.2f} }} scale={{ 0.05 0.05 }} '
            f'rotation=0 depth={depth}'
            '}}'
        )
    anchors_source = black_source[:-1] + " " + " ".join(marker_blocks) + "}"
    red = await _apply_calibration_source(client, red_source, record)
    if red.get("ok") is not True:
        return {"ok": False, "stage": "apply-red", "red": red}
    await asyncio.sleep(0.75)
    prepare_red = await _call(client, PREPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL)
    record(prepare_red)
    begin = await _call(
        client,
        CALIBRATE_COAT_OF_ARMS_FRAMEBUFFER_V3_TOOL,
        {"calibration_id": calibration_id, "phase": "begin"},
    )
    record(begin)
    green = await _apply_calibration_source(client, green_source, record)
    if green.get("ok") is not True:
        return {
            "ok": False,
            "stage": "apply-green",
            "red": red,
            "prepare_red": prepare_red,
            "begin": begin,
            "green": green,
        }
    await asyncio.sleep(0.75)
    prepare_green = await _call(client, PREPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL)
    record(prepare_green)
    surface_complete = await _call(
        client,
        CALIBRATE_COAT_OF_ARMS_FRAMEBUFFER_V3_TOOL,
        {"calibration_id": calibration_id, "phase": "surface_complete"},
    )
    record(surface_complete)
    surface_completed = _structured(surface_complete)
    black = await _apply_calibration_source(client, black_source, record)
    if black.get("ok") is not True:
        return {
            "ok": False,
            "stage": "apply-anchor-base",
            "red": red,
            "prepare_red": prepare_red,
            "begin": begin,
            "green": green,
            "prepare_green": prepare_green,
            "surface_complete": surface_complete,
            "black": black,
        }
    await asyncio.sleep(0.75)
    prepare_black = await _call(client, PREPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL)
    record(prepare_black)
    anchor_base = await _call(
        client,
        CALIBRATE_COAT_OF_ARMS_FRAMEBUFFER_V3_TOOL,
        {"calibration_id": calibration_id, "phase": "anchor_base"},
    )
    record(anchor_base)
    anchors = await _apply_calibration_source(client, anchors_source, record)
    if anchors.get("ok") is not True:
        return {
            "ok": False,
            "stage": "apply-anchors",
            "red": red,
            "begin": begin,
            "green": green,
            "surface_complete": surface_complete,
            "black": black,
            "anchor_base": anchor_base,
            "anchors": anchors,
        }
    await asyncio.sleep(0.75)
    prepare_anchors = await _call(client, PREPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL)
    record(prepare_anchors)
    anchors_complete = await _call(
        client,
        CALIBRATE_COAT_OF_ARMS_FRAMEBUFFER_V3_TOOL,
        {"calibration_id": calibration_id, "phase": "anchors_complete"},
    )
    record(anchors_complete)
    completed = _structured(anchors_complete)
    checks = {
        "red_applied": red.get("ok") is True,
        "begin_captured": bool(
            begin.get("is_error") is False
            and _structured(begin).get("nextPhase") == "surface_complete"
        ),
        "green_applied": green.get("ok") is True,
        "surface_complete_captured": bool(
            surface_complete.get("is_error") is False
            and surface_completed.get("readyForAnchorBase") is True
        ),
        "black_applied": black.get("ok") is True,
        "anchor_base_captured": bool(
            anchor_base.get("is_error") is False
            and _structured(anchor_base).get("nextPhase") == "anchors_complete"
        ),
        "anchors_applied": anchors.get("ok") is True,
        "anchors_complete_captured": bool(
            anchors_complete.get("is_error") is False
            and completed.get("readyForComparison") is True
            and completed.get("referenceIndependent") is True
            and completed.get("uvRegistered") is True
            and completed.get("calibrationId") == calibration_id
        ),
    }
    return {
        "ok": all(checks.values()),
        "calibration_id": calibration_id,
        "red": red,
        "prepare_red": prepare_red,
        "begin": begin,
        "green": green,
        "prepare_green": prepare_green,
        "surface_complete": surface_complete,
        "black": black,
        "prepare_black": prepare_black,
        "anchor_base": anchor_base,
        "anchors": anchors,
        "prepare_anchors": prepare_anchors,
        "anchors_complete": anchors_complete,
        "checks": checks,
    }


async def _collect_picture_corpus(
    client: Client,
    corpus: list[dict[str, object]],
    record: Any,
) -> dict[str, object]:
    calibration = await _calibrate_picture_corpus_surface(client, record)
    results: list[dict[str, object]] = []
    for value in corpus:
        identifier = value["id"]
        source = value["source"]
        source_receipt = value["source_receipt"]
        preview_base64 = value["preview_base64"]
        preview_receipt = value["preview_receipt"]
        require_v1_bound_exceeded = value.get(
            "require_v1_bound_exceeded", True
        )
        assert isinstance(identifier, str)
        assert isinstance(source, str)
        assert isinstance(source_receipt, dict)
        assert isinstance(preview_base64, str)
        assert isinstance(preview_receipt, dict)
        assert isinstance(require_v1_bound_exceeded, bool)
        roundtrip = await _collect_large_source_roundtrip(
            client,
            source,
            source_receipt,
            record,
            require_v1_bound_exceeded=require_v1_bound_exceeded,
        )
        roundtrip_checks = roundtrip.get("checks")
        framebuffer_ready = bool(
            isinstance(roundtrip_checks, dict)
            and all(
                roundtrip_checks.get(name) is True
                for name in (
                    "commit_applied",
                    "commit_source_identity",
                    "native_copy_exported",
                    "drawn_instance_count_preserved",
                    "logical_layer_count_preserved",
                    "colored_emblem_block_count_preserved",
                )
            )
        )
        if framebuffer_ready and calibration.get("ok") is True:
            await asyncio.sleep(0.75)
            preparation_call = await _call(
                client, PREPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL
            )
            record(preparation_call)
            framebuffer_call = await _call(
                client,
                COMPARE_COAT_OF_ARMS_FRAMEBUFFER_V3_TOOL,
                {
                    "calibration_id": calibration["calibration_id"],
                    "reference_png_base64": preview_base64,
                    "reference_png_sha256": preview_receipt["png_sha256"],
                },
            )
            record(framebuffer_call)
            framebuffer = _framebuffer_gate(framebuffer_call)
            framebuffer["preparation"] = preparation_call
        else:
            framebuffer = {
                "ok": False,
                "error": (
                    "large-source round-trip or reference-independent calibration "
                    "failed before framebuffer comparison"
                ),
            }
        exported = _structured(roundtrip.get("native_copy"))
        exported_source = exported.get("source")
        if (
            framebuffer.get("ok") is True
            and isinstance(exported_source, str)
            and exported_source
        ):
            try:
                native_reference, native_reference_receipt = (
                    _native_aligned_reference(framebuffer["call"])
                )
            except RuntimeError as error:
                copy_reapply = {
                    "ok": False,
                    "error": str(error),
                }
            else:
                reapply_roundtrip = await _collect_large_source_roundtrip(
                    client,
                    exported_source,
                    _source_receipt_from_text(
                        exported_source,
                        source_label=f"{identifier}:native-copy",
                    ),
                    record,
                    require_v1_bound_exceeded=require_v1_bound_exceeded,
                )
                reapply_checks = reapply_roundtrip.get("checks")
                reapply_ready = bool(
                    isinstance(reapply_checks, dict)
                    and all(
                        reapply_checks.get(name) is True
                        for name in (
                            "commit_applied",
                            "commit_source_identity",
                            "native_copy_exported",
                            "drawn_instance_count_preserved",
                            "logical_layer_count_preserved",
                            "colored_emblem_block_count_preserved",
                            "semantic_field_sequences_preserved",
                        )
                    )
                )
                if reapply_ready:
                    await asyncio.sleep(0.75)
                    reapply_preparation = await _call(
                        client, PREPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL
                    )
                    record(reapply_preparation)
                    reapply_framebuffer_call = await _call(
                        client,
                        COMPARE_COAT_OF_ARMS_FRAMEBUFFER_V3_TOOL,
                        {
                            "calibration_id": calibration["calibration_id"],
                            "reference_png_base64": native_reference,
                            "reference_png_sha256": native_reference_receipt[
                                "png_sha256"
                            ],
                        },
                    )
                    record(reapply_framebuffer_call)
                    reapply_framebuffer = _framebuffer_gate(
                        reapply_framebuffer_call,
                        thresholds=COPY_REAPPLY_EQUIVALENCE_THRESHOLDS,
                    )
                    reapply_framebuffer["preparation"] = reapply_preparation
                else:
                    reapply_framebuffer = {
                        "ok": False,
                        "error": (
                            "native Copy text did not complete a strict second "
                            "round-trip"
                        ),
                    }
                copy_reapply = {
                    "ok": bool(
                        reapply_roundtrip.get("ok") is True
                        and reapply_framebuffer.get("ok") is True
                    ),
                    "reference": native_reference_receipt,
                    "roundtrip": reapply_roundtrip,
                    "framebuffer": reapply_framebuffer,
                }
        else:
            copy_reapply = {
                "ok": False,
                "error": (
                    "original native framebuffer or Copy export was unavailable"
                ),
            }
        visual_ok = bool(
            framebuffer.get("ok") is True
            and copy_reapply.get("ok") is True
        )
        results.append(
            {
                "id": identifier,
                "source": source_receipt,
                "reference": preview_receipt,
                "roundtrip": roundtrip,
                "framebuffer_ready_after_native_apply": framebuffer_ready,
                "framebuffer": framebuffer,
                "copy_reapply": copy_reapply,
                "visual_ok": visual_ok,
                "ok": bool(
                    roundtrip.get("ok") is True
                    and visual_ok
                ),
            }
        )
    return {
        "schema": "ck3-coat-of-arms-picture-corpus-live-v2",
        "framebuffer_calibration": calibration,
        "case_count": len(results),
        "passed": sum(result["ok"] is True for result in results),
        "failed": sum(result["ok"] is not True for result in results),
        "strict_roundtrip_passed": sum(
            result["roundtrip"].get("ok") is True for result in results
        ),
        "native_pixel_passed": sum(
            result["framebuffer"].get("ok") is True for result in results
        ),
        "copy_reapply_passed": sum(
            result["copy_reapply"].get("ok") is True for result in results
        ),
        "visual_passed": sum(
            result["visual_ok"] is True for result in results
        ),
        "cases": results,
        "ok": bool(results) and all(result["ok"] is True for result in results),
    }


def _reference_free_capture_gate(call: dict[str, object]) -> dict[str, object]:
    body = _structured(call)
    capture = body.get("capture")
    if not isinstance(capture, dict):
        return {"ok": False, "error": "capture payload is missing"}
    encoded = capture.get("alignedContentPngBase64")
    expected_sha256 = capture.get("alignedContentPngSha256")
    if not isinstance(encoded, str) or not isinstance(expected_sha256, str):
        return {"ok": False, "error": "aligned capture payload is malformed"}
    try:
        raw = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError) as error:
        return {"ok": False, "error": f"capture base64 is malformed: {error}"}
    actual_sha256 = hashlib.sha256(raw).hexdigest().upper()
    checks = {
        "call_not_error": call.get("is_error") is False,
        "schema": body.get("schema")
        == "ck3-coat-of-arms-framebuffer-capture-v1",
        "route_stable": body.get("routeStable") is True,
        "read_only": body.get("readOnly") is True,
        "no_reference_accepted": capture.get("referenceImageAccepted") is False,
        "no_reference_localization": capture.get("referenceUsedForLocalization")
        is False,
        "no_reference_registration": capture.get("referenceUsedForRegistration")
        is False,
        "no_fixed_coordinates": capture.get("fixedScreenCoordinatesUsed") is False,
        "no_ocr": body.get("usesOcr") is False,
        "no_keyboard": body.get("usesKeyboard") is False,
        "no_mouse": body.get("usesMouse") is False,
        "capture_side": capture.get("captureSide") == 230,
        "hash_identity": actual_sha256 == expected_sha256,
    }
    return {
        "ok": all(checks.values()),
        "checks": checks,
        "png_bytes": len(raw),
        "png_sha256": actual_sha256,
        "call": call,
    }


def _capture_pair_metrics(
    first: dict[str, object], second: dict[str, object]
) -> dict[str, object]:
    def pixels(value: dict[str, object]) -> np.ndarray:
        body = _structured(value["call"])
        capture = body["capture"]
        raw = base64.b64decode(
            capture["alignedContentPngBase64"].encode("ascii"), validate=True
        )
        with Image.open(BytesIO(raw)) as image:
            return np.asarray(image.convert("RGBA"), dtype=np.uint8)

    first_pixels = pixels(first)
    second_pixels = pixels(second)
    if first_pixels.shape != second_pixels.shape:
        return {
            "comparable": False,
            "first_shape": list(first_pixels.shape),
            "second_shape": list(second_pixels.shape),
        }
    mask = np.logical_and(first_pixels[:, :, 3] > 0, second_pixels[:, :, 3] > 0)
    rgb_diff = np.abs(
        first_pixels[:, :, :3].astype(np.int16)
        - second_pixels[:, :, :3].astype(np.int16)
    )
    selected = rgb_diff[mask]
    if selected.size == 0:
        raise RuntimeError("parent semantics pair has no common visible pixels")
    differing = np.any(rgb_diff > 0, axis=2)
    return {
        "comparable": True,
        "side": int(first_pixels.shape[0]),
        "common_visible_pixels": int(np.count_nonzero(mask)),
        "differing_visible_pixels": int(np.count_nonzero(differing & mask)),
        "mean_absolute_error": float(np.mean(selected) / 255.0),
        "maximum_channel_error": int(np.max(selected)),
        "alpha_differing_pixels": int(
            np.count_nonzero(first_pixels[:, :, 3] != second_pixels[:, :, 3])
        ),
        "pixel_exact": bool(np.array_equal(first_pixels, second_pixels)),
    }


def _capture_pair_is_equivalent(metrics: dict[str, object]) -> bool:
    return bool(
        metrics.get("comparable") is True
        and isinstance(metrics.get("maximum_channel_error"), int)
        and metrics["maximum_channel_error"]
        <= PARENT_SEMANTICS_CAPTURE_NOISE_THRESHOLDS[
            "maximum_channel_error"
        ]
        and isinstance(metrics.get("mean_absolute_error"), (int, float))
        and not isinstance(metrics.get("mean_absolute_error"), bool)
        and metrics["mean_absolute_error"]
        <= PARENT_SEMANTICS_CAPTURE_NOISE_THRESHOLDS[
            "maximum_normalized_mean_absolute_error"
        ]
        and isinstance(metrics.get("alpha_differing_pixels"), int)
        and metrics["alpha_differing_pixels"]
        <= PARENT_SEMANTICS_CAPTURE_NOISE_THRESHOLDS[
            "maximum_alpha_differing_pixels"
        ]
    )


async def _collect_parent_semantics_matrix(
    client: Client,
    record: Any,
) -> dict[str, object]:
    calibration = await _calibrate_picture_corpus_surface(client, record)
    results: list[dict[str, object]] = []
    capture_by_id: dict[str, dict[str, object]] = {}
    for value in PARENT_SEMANTICS_CASES:
        identifier = value["id"]
        source = value["source"]
        assert isinstance(identifier, str)
        assert isinstance(source, str)
        applied = await _apply_calibration_source(client, source, record)
        export_call: dict[str, object] | None = None
        preparation_call: dict[str, object] | None = None
        capture_call: dict[str, object] | None = None
        capture: dict[str, object] = {
            "ok": False,
            "error": "source apply or calibration failed before capture",
        }
        if applied.get("ok") is True and calibration.get("ok") is True:
            snapshot_call = await _call(client, SNAPSHOT_TOOL)
            record(snapshot_call)
            revision = _structured(snapshot_call).get("revision")
            if isinstance(revision, int) and not isinstance(revision, bool):
                export_call = await _call(
                    client,
                    EXPORT_COAT_OF_ARMS_TOOL,
                    {"expected_revision": revision},
                )
                record(export_call)
            preparation_call = await _call(
                client, PREPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL
            )
            record(preparation_call)
            capture_call = await _call(
                client,
                CAPTURE_COAT_OF_ARMS_FRAMEBUFFER_TOOL,
                {
                    "calibration_id": calibration["calibration_id"],
                    "side": 230,
                },
            )
            record(capture_call)
            capture = _reference_free_capture_gate(capture_call)
        exported = _structured(export_call or {})
        exported_source = exported.get("source")
        checks = {
            "applied": applied.get("ok") is True,
            "native_copy_exported": bool(
                export_call is not None
                and export_call.get("is_error") is False
                and isinstance(exported_source, str)
                and exported_source
            ),
            "prepared": bool(
                preparation_call is not None
                and preparation_call.get("is_error") is False
                and _structured(preparation_call).get("routeStable") is True
            ),
            "reference_free_capture": capture.get("ok") is True,
        }
        result = {
            "id": identifier,
            "source": _source_receipt_from_text(
                source, source_label=f"parent-semantics:{identifier}"
            ),
            "apply": applied,
            "native_copy": export_call,
            "native_copy_semantic_projection": (
                _projection_summary(_semantic_projection(exported_source))
                if isinstance(exported_source, str)
                else None
            ),
            "preparation": preparation_call,
            "capture": capture,
            "checks": checks,
            "ok": all(checks.values()),
        }
        results.append(result)
        if capture.get("ok") is True:
            capture_by_id[identifier] = capture
    pair_metrics = []
    for first_id, second_id in PARENT_SEMANTICS_PAIRS:
        if first_id not in capture_by_id or second_id not in capture_by_id:
            metrics = {"comparable": False, "reason": "capture missing"}
        else:
            metrics = _capture_pair_metrics(
                capture_by_id[first_id], capture_by_id[second_id]
            )
        pair_metrics.append(
            {"first": first_id, "second": second_id, **metrics}
        )
    diagnostic_metrics = []
    for first_id, second_id, expected_equivalent in (
        PARENT_SEMANTICS_DIAGNOSTIC_PAIRS
    ):
        if first_id not in capture_by_id or second_id not in capture_by_id:
            metrics = {"comparable": False, "reason": "capture missing"}
        else:
            metrics = _capture_pair_metrics(
                capture_by_id[first_id], capture_by_id[second_id]
            )
        equivalent = _capture_pair_is_equivalent(metrics)
        diagnostic_metrics.append(
            {
                "first": first_id,
                "second": second_id,
                "expected_equivalent_within_capture_noise": expected_equivalent,
                "equivalent_within_capture_noise": equivalent,
                "gate_passed": equivalent is expected_equivalent,
                **metrics,
            }
        )
    return {
        "schema": "ck3-coat-of-arms-parent-semantics-matrix-v2",
        "case_count": len(results),
        "framebuffer_calibration": calibration,
        "capture_noise_thresholds": dict(
            PARENT_SEMANTICS_CAPTURE_NOISE_THRESHOLDS
        ),
        "cases": results,
        "pairs": pair_metrics,
        "diagnostic_pairs": diagnostic_metrics,
        "ok": bool(results)
        and calibration.get("ok") is True
        and all(result["ok"] is True for result in results)
        and all(pair.get("comparable") is True for pair in pair_metrics)
        and all(pair.get("gate_passed") is True for pair in diagnostic_metrics),
    }


async def _collect_vfs_winner_matrix(
    client: Client,
    record: Any,
    *,
    extended: bool = False,
    replace_path: bool = False,
) -> dict[str, object]:
    """Prove checked-in direct-DDS winners through native pixels."""

    if extended and replace_path:
        raise ValueError("extended and replace_path VFS matrices are mutually exclusive")
    cases = (
        VFS_REPLACE_PATH_CASES
        if replace_path
        else VFS_EXTENDED_CASES
        if extended
        else VFS_WINNER_CASES
    )
    diagnostic_pairs = (
        VFS_REPLACE_PATH_DIAGNOSTIC_PAIRS
        if replace_path
        else VFS_EXTENDED_DIAGNOSTIC_PAIRS
        if extended
        else VFS_WINNER_DIAGNOSTIC_PAIRS
    )
    calibration = await _calibrate_picture_corpus_surface(client, record)
    results: list[dict[str, object]] = []
    capture_by_id: dict[str, dict[str, object]] = {}
    for value in cases:
        identifier = value["id"]
        source = value["source"]
        assert isinstance(identifier, str)
        assert isinstance(source, str)
        applied = await _apply_calibration_source(client, source, record)
        export_call: dict[str, object] | None = None
        preparation_call: dict[str, object] | None = None
        capture_call: dict[str, object] | None = None
        capture: dict[str, object] = {
            "ok": False,
            "error": "source apply or calibration failed before capture",
        }
        if applied.get("ok") is True and calibration.get("ok") is True:
            snapshot_call = await _call(client, SNAPSHOT_TOOL)
            record(snapshot_call)
            revision = _structured(snapshot_call).get("revision")
            if isinstance(revision, int) and not isinstance(revision, bool):
                export_call = await _call(
                    client,
                    EXPORT_COAT_OF_ARMS_TOOL,
                    {"expected_revision": revision},
                )
                record(export_call)
            preparation_call = await _call(
                client, PREPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL
            )
            record(preparation_call)
            capture_call = await _call(
                client,
                CAPTURE_COAT_OF_ARMS_FRAMEBUFFER_TOOL,
                {
                    "calibration_id": calibration["calibration_id"],
                    "side": 230,
                },
            )
            record(capture_call)
            capture = _reference_free_capture_gate(capture_call)
        exported = _structured(export_call or {})
        exported_source = exported.get("source")
        checks = {
            "applied": applied.get("ok") is True,
            "native_copy_exported": bool(
                export_call is not None
                and export_call.get("is_error") is False
                and isinstance(exported_source, str)
                and exported_source
            ),
            "prepared": bool(
                preparation_call is not None
                and preparation_call.get("is_error") is False
                and _structured(preparation_call).get("routeStable") is True
            ),
            "reference_free_capture": capture.get("ok") is True,
        }
        result = {
            "id": identifier,
            "source": _source_receipt_from_text(
                source,
                source_label=(
                    f"vfs-replace-path:{identifier}"
                    if replace_path
                    else
                    f"vfs-extended:{identifier}"
                    if extended
                    else f"vfs-winner:{identifier}"
                ),
            ),
            "apply": applied,
            "native_copy": export_call,
            "native_copy_semantic_projection": (
                _projection_summary(_semantic_projection(exported_source))
                if isinstance(exported_source, str)
                else None
            ),
            "preparation": preparation_call,
            "capture": capture,
            "checks": checks,
            "ok": all(checks.values()),
        }
        results.append(result)
        if capture.get("ok") is True:
            capture_by_id[identifier] = capture

    diagnostic_metrics = []
    for first_id, second_id, expected_equivalent in diagnostic_pairs:
        if first_id not in capture_by_id or second_id not in capture_by_id:
            metrics = {"comparable": False, "reason": "capture missing"}
        else:
            metrics = _capture_pair_metrics(
                capture_by_id[first_id], capture_by_id[second_id]
            )
        equivalent = _capture_pair_is_equivalent(metrics)
        diagnostic_metrics.append(
            {
                "first": first_id,
                "second": second_id,
                "expected_equivalent_within_capture_noise": expected_equivalent,
                "equivalent_within_capture_noise": equivalent,
                "gate_passed": equivalent is expected_equivalent,
                **metrics,
            }
        )
    gate_passed = bool(diagnostic_metrics) and all(
        pair.get("gate_passed") is True for pair in diagnostic_metrics
    )
    result = {
        "schema": (
            "ck3-coat-of-arms-vfs-replace-path-matrix-v1"
            if replace_path
            else
            "ck3-coat-of-arms-vfs-extended-matrix-v1"
            if extended
            else "ck3-coat-of-arms-vfs-winner-matrix-v1"
        ),
        "case_count": len(results),
        "predeclared_hypothesis": (
            (
                "the base-game-only pattern behaves like a never-present missing control; "
                "the earlier enabled-mod pattern remains available and differs from both "
                "the missing control and the later replacement pattern"
            )
            if replace_path
            else (
                "an enabled directory mod owns a conflicting base-game DDS path; "
                "a later enabled archive mod owns a conflicting DDS path over an "
                "earlier directory mod"
            )
            if extended
            else (
                "enabled_mods load_order 1 owns a conflicting direct DDS path "
                "over load_order 0"
            )
        ),
        "framebuffer_calibration": calibration,
        "capture_noise_thresholds": dict(
            PARENT_SEMANTICS_CAPTURE_NOISE_THRESHOLDS
        ),
        "cases": results,
        "diagnostic_pairs": diagnostic_metrics,
        "ok": bool(results)
        and calibration.get("ok") is True
        and all(result["ok"] is True for result in results)
        and gate_passed,
    }
    if replace_path:
        result["inferred_replace_path_effect"] = (
            "base-game-directory-hidden-earlier-enabled-mod-preserved"
            if gate_passed
            else None
        )
    elif extended:
        result["inferred_winners"] = (
            {
                "base_vs_mod": "enabled-directory-mod",
                "directory_vs_archive": "later-enabled-archive-mod",
            }
            if gate_passed
            else None
        )
    else:
        result["inferred_winner_load_order"] = 1 if gate_passed else None
    return result


def _summarize_pattern_grid(inspection: object) -> dict[str, object]:
    """Summarize only the bounded subtree below vanilla patterns_scrollbox."""

    scrollbox_path = "0/3/0/2/1/1/2/0/0"
    widgets = inspection.get("widgets") if isinstance(inspection, dict) else None
    rows = [row for row in widgets if isinstance(row, dict)] if isinstance(
        widgets, list
    ) else []
    descendants = [
        row
        for row in rows
        if isinstance(row.get("child_path"), str)
        and row["child_path"].startswith(scrollbox_path + "/")
    ]
    direct_children = [
        row
        for row in descendants
        if "/" not in row["child_path"][len(scrollbox_path) + 1 :]
    ]
    named_counts: dict[str, int] = {}
    for row in descendants:
        name = row.get("runtime_name")
        if isinstance(name, str):
            named_counts[name] = named_counts.get(name, 0) + 1
    largest_children = sorted(
        descendants,
        key=lambda row: (-int(row.get("child_count", 0)), str(row["child_path"])),
    )[:32]
    return {
        "scrollbox_path": scrollbox_path,
        "inspection_widget_count": (
            inspection.get("widget_count") if isinstance(inspection, dict) else None
        ),
        "inspection_truncated": (
            inspection.get("truncated") if isinstance(inspection, dict) else None
        ),
        "descendant_count": len(descendants),
        "visible_descendant_count": sum(
            row.get("effective_visible") is True for row in descendants
        ),
        "enabled_descendant_count": sum(
            row.get("enabled") is True for row in descendants
        ),
        "direct_child_count": len(direct_children),
        "materialized": bool(descendants),
        "runtime_name_counts": dict(sorted(named_counts.items())),
        "direct_children": direct_children[:64],
        "largest_child_count_rows": largest_children,
    }


async def _collect_custom_mode_census(
    client: Client,
    record: Any,
) -> dict[str, object]:
    before_call = await _call(client, INSPECT_COAT_OF_ARMS_TREE_TOOL)
    record(before_call)
    before = _structured(before_call)
    activate_call = await _call(client, ACTIVATE_COAT_OF_ARMS_CUSTOM_MODE_TOOL)
    record(activate_call)
    activated = _structured(activate_call)
    after_call = await _call(client, INSPECT_COAT_OF_ARMS_TREE_TOOL)
    record(after_call)
    after = _structured(after_call)
    pattern_grid_call = await _call(
        client, INSPECT_COAT_OF_ARMS_PATTERN_GRID_TOOL
    )
    record(pattern_grid_call)
    pattern_grid = _structured(pattern_grid_call)
    after_route = (
        activated.get("after")
        if isinstance(activated.get("after"), dict)
        else {}
    )
    embedded_after = (
        activated.get("after_inspection")
        if isinstance(activated.get("after_inspection"), dict)
        else {}
    )
    checks = {
        "before_inspection_not_error": before_call.get("is_error") is False,
        "before_custom_mode_target_ready": (
            frontend_coat_of_arms_custom_mode_target_ready_v1(before)
        ),
        "activation_not_error": activate_call.get("is_error") is False,
        "activation_verified": (
            activated.get("status") == "verified"
            and activated.get("action") == "enter_coat_of_arms_custom_mode"
            and activated.get("postcondition_verified") is True
        ),
        "activation_no_ocr_keyboard_mouse": (
            activated.get("uses_ocr") is False
            and activated.get("uses_keyboard") is False
            and activated.get("uses_mouse") is False
        ),
        "route_remains_coat_of_arms_designer": (
            after_route.get("route") == "coat_of_arms_designer"
        ),
        "embedded_background_patterns_ready": (
            frontend_coat_of_arms_background_patterns_ready_v1(embedded_after)
        ),
        "separate_after_inspection_not_error": after_call.get("is_error") is False,
        "separate_background_patterns_ready": (
            frontend_coat_of_arms_background_patterns_ready_v1(after)
        ),
        "pattern_grid_census_recorded": (
            pattern_grid_call.get("is_error") is False
            and pattern_grid.get("scope_root_name")
            == "coat_of_arms_pattern_grid"
            and pattern_grid.get("direct_children_complete") is True
            and isinstance(pattern_grid.get("direct_child_count"), int)
            and pattern_grid.get("direct_child_count", 0) > 0
            and pattern_grid.get("read_only") is True
            and pattern_grid.get("uses_ocr") is False
            and pattern_grid.get("uses_keyboard") is False
            and pattern_grid.get("uses_mouse") is False
        ),
    }
    return {
        "ok": all(checks.values()),
        "before_inspection": before_call,
        "activation": activate_call,
        "after_inspection": after_call,
        "pattern_grid": pattern_grid_call,
        "checks": checks,
    }


async def _mcp_sequence(
    driver: NativeHeadlessGameplayDriver,
    timeout: float,
    syntax_matrix: dict[str, object] | None = None,
    custom_mode_census: bool = False,
    commit_roundtrip: bool = False,
    large_source: tuple[str, dict[str, object]] | None = None,
    reference_preview: tuple[str, dict[str, object]] | None = None,
    picture_corpus: list[dict[str, object]] | None = None,
    parent_semantics_matrix: bool = False,
    vfs_winner_matrix: bool = False,
    vfs_extended_matrix: bool = False,
    vfs_replace_path_matrix: bool = False,
    vfs_mount_order_diagnostics: bool = False,
    vfs_mount_order_diagnostics_only: bool = False,
    vfs_asset_projection_paths: tuple[str, ...] = (),
    game_directory: str | None = None,
    bookmarks_read_only: bool = False,
    bookmarks_model_private: bool = False,
    bookmarks_select_start_private: bool = False,
    expected_succession_lifecycle: dict[str, object] | None = None,
) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    calls: list[dict[str, object]] = []
    call_summary: dict[str, object] = {
        "total": 0,
        "omitted": 0,
        "last_call": None,
    }
    vfs_mount_order_result: dict[str, object] | None = None
    vfs_asset_projection_result: dict[str, object] | None = None

    def record(call: dict[str, object]) -> None:
        call_summary["total"] = int(call_summary["total"]) + 1
        call_summary["last_call"] = call
        if len(calls) < 32:
            calls.append(call)
        else:
            call_summary["omitted"] = int(call_summary["omitted"]) + 1

    def red(reason: str, **evidence: object) -> dict[str, object]:
        result = {
            "mcp_sdk": "official-python-client",
            "calls": calls,
            "call_summary": call_summary,
            "checks": {},
            "error": reason,
            "ok": False,
            **evidence,
        }
        if vfs_mount_order_diagnostics:
            result["vfs_mount_order_diagnostics"] = vfs_mount_order_result
        if vfs_asset_projection_paths:
            result["vfs_asset_projections"] = vfs_asset_projection_result
        return result

    async with Client(create_server(driver)) as client:
        listed = await client.list_tools()
        tools = {tool.name: tool for tool in listed.tools}
        route_required = (
            {QUERY_TOOL, INSPECT_TOOL, ACTIVATE_NEW_GAME_TOOL}
            if bookmarks_read_only
            else {
                QUERY_TOOL,
                INSPECT_TOOL,
                ACTIVATE_NEW_GAME_TOOL,
                ACTIVATE_PICK_ANY_TOOL,
                ACTIVATE_PREPARE_CUSTOM_RULER_TOOL,
                ACTIVATE_RULER_DESIGNER_TOOL,
                ACTIVATE_COAT_OF_ARMS_DESIGNER_TOOL,
                COMMIT_DYNASTY_COAT_OF_ARMS_TOOL,
            }
        )
        matrix_required = (
            {SNAPSHOT_TOOL, PROBE_COAT_OF_ARMS_TOOL, EXPORT_COAT_OF_ARMS_TOOL}
            if syntax_matrix is not None
            else set()
        )
        commit_required = (
            {
                SNAPSHOT_TOOL,
                PROBE_COAT_OF_ARMS_TOOL,
                EXPORT_COAT_OF_ARMS_TOOL,
                COMMIT_DYNASTY_COAT_OF_ARMS_TOOL,
            }
            if commit_roundtrip
            else set()
        )
        large_source_required = (
            {
                SNAPSHOT_TOOL,
                BEGIN_COAT_OF_ARMS_UPLOAD_TOOL,
                APPEND_COAT_OF_ARMS_UPLOAD_TOOL,
                COMMIT_COAT_OF_ARMS_UPLOAD_TOOL,
                ABORT_COAT_OF_ARMS_UPLOAD_TOOL,
                EXPORT_COAT_OF_ARMS_TOOL,
            }
            if large_source is not None or picture_corpus is not None
            else set()
        )
        framebuffer_required = (
            {
                PREPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL,
                *(
                    {
                        CALIBRATE_COAT_OF_ARMS_FRAMEBUFFER_V3_TOOL,
                        COMPARE_COAT_OF_ARMS_FRAMEBUFFER_V3_TOOL,
                    }
                    if picture_corpus is not None
                    else {COMPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL}
                ),
            }
            if reference_preview is not None or picture_corpus is not None
            else set()
        )
        parent_semantics_required = (
            {
                SNAPSHOT_TOOL,
                PROBE_COAT_OF_ARMS_TOOL,
                EXPORT_COAT_OF_ARMS_TOOL,
                PREPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL,
                CALIBRATE_COAT_OF_ARMS_FRAMEBUFFER_V3_TOOL,
                CAPTURE_COAT_OF_ARMS_FRAMEBUFFER_TOOL,
            }
            if parent_semantics_matrix or vfs_winner_matrix
            else set()
        )
        custom_mode_required = (
            {
                INSPECT_COAT_OF_ARMS_TREE_TOOL,
                INSPECT_COAT_OF_ARMS_PATTERN_GRID_TOOL,
                ACTIVATE_COAT_OF_ARMS_CUSTOM_MODE_TOOL,
            }
            if custom_mode_census
            else set()
        )
        diagnostics_required = (
            {BRIDGE_DIAGNOSTICS_TOOL}
            if vfs_mount_order_diagnostics
            else set()
        )
        projection_required = (
            {VFS_ASSET_PROJECTION_TOOL}
            if vfs_asset_projection_paths
            else set()
        )
        required = (
            route_required
            | matrix_required
            | commit_required
            | large_source_required
            | framebuffer_required
            | parent_semantics_required
            | custom_mode_required
            | diagnostics_required
            | projection_required
        )
        schemas = {
            name: tools[name].input_schema
            for name in sorted(required)
            if name in tools
        }
        if not required <= set(tools):
            return red(
                "frontend MCP tools are not registered",
                registered_tools=sorted(tools),
            )
        if any(
            schemas[name].get("required", []) != []
            or schemas[name].get("additionalProperties") is not False
            for name in route_required
        ):
            return red(
                "frontend MCP tools are not closed zero-input tools",
                tool_schemas=schemas,
            )

        if custom_mode_census and not all(
            _schema_is_zero_input(schemas.get(name))
            for name in custom_mode_required
        ):
            return red(
                "coat-of-arms custom-mode MCP tools are not closed zero-input tools",
                tool_schemas=schemas,
            )
        if vfs_mount_order_diagnostics and not _schema_is_zero_input(
            schemas.get(BRIDGE_DIAGNOSTICS_TOOL)
        ):
            return red(
                "bridge diagnostics MCP tool is not a closed zero-input tool",
                tool_schemas=schemas,
            )
        if vfs_asset_projection_paths and not _schema_has_required_fields(
            schemas.get(VFS_ASSET_PROJECTION_TOOL),
            {"game_directory", "logical_path"},
        ):
            return red(
                "VFS asset projection MCP tool has an unexpected schema",
                tool_schemas=schemas,
            )
        if (syntax_matrix is not None or commit_roundtrip) and not (
            _schema_is_zero_input(schemas.get(SNAPSHOT_TOOL))
            and _schema_has_required_fields(
                schemas.get(PROBE_COAT_OF_ARMS_TOOL),
                {"source", "expected_revision", "apply"},
            )
            and _schema_has_required_fields(
                schemas.get(EXPORT_COAT_OF_ARMS_TOOL), {"expected_revision"}
            )
        ):
            return red(
                "coat-of-arms matrix MCP tools do not have the expected v1 schemas",
                tool_schemas=schemas,
            )
        if (large_source is not None or picture_corpus is not None) and not (
            _schema_is_zero_input(schemas.get(SNAPSHOT_TOOL))
            and _schema_has_required_fields(
                schemas.get(BEGIN_COAT_OF_ARMS_UPLOAD_TOOL),
                {
                    "total_bytes",
                    "source_sha256",
                    "chunk_count",
                    "chunk_encoding",
                    "expected_revision",
                    "apply",
                    "expected_game_version",
                    "expected_executable_sha256",
                },
            )
            and _schema_has_required_fields(
                schemas.get(APPEND_COAT_OF_ARMS_UPLOAD_TOOL),
                {
                    "upload_id",
                    "generation",
                    "chunk_index",
                    "chunk_count",
                    "chunk_encoding",
                    "chunk_bytes",
                    "chunk_sha256",
                    "chunk_base64",
                    "source_sha256",
                    "expected_revision",
                    "apply",
                    "expected_game_version",
                    "expected_executable_sha256",
                },
            )
            and _schema_has_required_fields(
                schemas.get(COMMIT_COAT_OF_ARMS_UPLOAD_TOOL),
                {
                    "upload_id",
                    "generation",
                    "chunk_count",
                    "source_sha256",
                    "expected_revision",
                    "apply",
                    "expected_game_version",
                    "expected_executable_sha256",
                },
            )
            and _schema_has_required_fields(
                schemas.get(ABORT_COAT_OF_ARMS_UPLOAD_TOOL),
                {"upload_id", "generation"},
            )
            and _schema_has_required_fields(
                schemas.get(EXPORT_COAT_OF_ARMS_TOOL),
                {"expected_revision"},
            )
        ):
            return red(
                "large-source MCP tools do not have the expected closed schemas",
                tool_schemas=schemas,
            )
        if reference_preview is not None and not _schema_has_required_fields(
            schemas.get(COMPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL),
            {"reference_png_base64", "reference_png_sha256"},
        ):
            return red(
                "coat-of-arms framebuffer MCP tool does not have the expected schema",
                tool_schemas=schemas,
            )
        if picture_corpus is not None and not (
            _schema_has_required_fields(
                schemas.get(CALIBRATE_COAT_OF_ARMS_FRAMEBUFFER_V3_TOOL),
                {"calibration_id", "phase"},
            )
            and _schema_has_required_fields(
                schemas.get(COMPARE_COAT_OF_ARMS_FRAMEBUFFER_V3_TOOL),
                {
                    "calibration_id",
                    "reference_png_base64",
                    "reference_png_sha256",
                },
            )
        ):
            return red(
                "coat-of-arms calibrated framebuffer MCP tools have unexpected schemas",
                tool_schemas=schemas,
            )
        if (parent_semantics_matrix or vfs_winner_matrix) and not (
            _schema_is_zero_input(schemas.get(SNAPSHOT_TOOL))
            and _schema_has_required_fields(
                schemas.get(PROBE_COAT_OF_ARMS_TOOL),
                {"source", "expected_revision", "apply"},
            )
            and _schema_has_required_fields(
                schemas.get(EXPORT_COAT_OF_ARMS_TOOL), {"expected_revision"}
            )
            and _schema_is_zero_input(
                schemas.get(PREPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL)
            )
            and _schema_has_required_fields(
                schemas.get(CALIBRATE_COAT_OF_ARMS_FRAMEBUFFER_V3_TOOL),
                {"calibration_id", "phase"},
            )
            and _schema_has_required_fields(
                schemas.get(CAPTURE_COAT_OF_ARMS_FRAMEBUFFER_TOOL),
                {"calibration_id"},
            )
        ):
            return red(
                "reference-free CoA matrix MCP tools do not have the expected closed schemas",
                tool_schemas=schemas,
            )
        if (
            reference_preview is not None or picture_corpus is not None
        ) and not _schema_is_zero_input(
            schemas.get(PREPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL)
        ):
            return red(
                "coat-of-arms framebuffer preparation MCP tool is not zero-input",
                tool_schemas=schemas,
            )

        required_capabilities = (
            {QUERY_CAPABILITY, INSPECT_CAPABILITY, ACTIVATE_NEW_GAME_CAPABILITY}
            if bookmarks_read_only
            else {
                QUERY_CAPABILITY,
                INSPECT_CAPABILITY,
                ACTIVATE_NEW_GAME_CAPABILITY,
                ACTIVATE_PICK_ANY_CAPABILITY,
                ACTIVATE_SELECT_RANDOM_PLAYABLE_CAPABILITY,
                ACTIVATE_RULER_DESIGNER_CAPABILITY,
                ACTIVATE_COAT_OF_ARMS_DESIGNER_CAPABILITY,
                COMMIT_DYNASTY_COAT_OF_ARMS_CAPABILITY,
            }
        )
        if syntax_matrix is not None:
            required_capabilities |= {
                PROBE_COAT_OF_ARMS_CAPABILITY,
                EXPORT_COAT_OF_ARMS_CAPABILITY,
            }
        if commit_roundtrip:
            required_capabilities |= {
                PROBE_COAT_OF_ARMS_CAPABILITY,
                EXPORT_COAT_OF_ARMS_CAPABILITY,
                COMMIT_DYNASTY_COAT_OF_ARMS_CAPABILITY,
            }
        if large_source is not None or picture_corpus is not None:
            required_capabilities |= {
                PROBE_COAT_OF_ARMS_CAPABILITY,
                EXPORT_COAT_OF_ARMS_CAPABILITY,
            }
        if custom_mode_census:
            required_capabilities |= {
                INSPECT_COAT_OF_ARMS_TREE_CAPABILITY,
                INSPECT_COAT_OF_ARMS_PATTERN_GRID_CAPABILITY,
                ACTIVATE_COAT_OF_ARMS_CUSTOM_MODE_CAPABILITY,
            }

        capability_call: dict[str, object] | None = None
        while time.monotonic() < deadline:
            capability_call = await _call(client, "ck3_get_capabilities")
            record(capability_call)
            capability = _structured(capability_call)
            advertised = capability.get("bridge_capabilities")
            diagnostics = capability.get("diagnostics")
            hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
            hello_caps = hello.get("capabilities") if isinstance(hello, dict) else None
            if (
                capability_call.get("is_error") is False
                and isinstance(advertised, list)
                and isinstance(hello_caps, list)
                and required_capabilities <= set(advertised)
                and required_capabilities <= set(hello_caps)
            ):
                break
            await asyncio.sleep(0.25)
        else:
            return red(
                "native bridge did not advertise frontend MCP capabilities",
                tool_schemas=schemas,
                last_capability=_structured(capability_call or {}),
            )

        # Mount publication happens during cold startup, before the frontend
        # route is necessarily available. Capture the explicit diagnostics tool
        # as soon as the bridge contract is ready so a slow/failed route cannot
        # discard the bounded startup evidence.
        if vfs_mount_order_diagnostics:
            vfs_mount_order_result = await _collect_vfs_mount_order_diagnostics(
                client, record
            )
            if vfs_asset_projection_paths:
                if game_directory is None:
                    return red(
                        "VFS asset projection requires an explicit game directory"
                    )
                vfs_asset_projection_result = await _collect_vfs_asset_projections(
                    client,
                    record,
                    game_directory,
                    vfs_asset_projection_paths,
                )
            if vfs_mount_order_diagnostics_only:
                checks = {
                    "vfs_mount_order_diagnostics_complete": (
                        vfs_mount_order_result.get("ok") is True
                    ),
                    "vfs_asset_projections_complete": (
                        not vfs_asset_projection_paths
                        or (
                            isinstance(vfs_asset_projection_result, dict)
                            and vfs_asset_projection_result.get("ok") is True
                        )
                    ),
                }
                return {
                    "mcp_sdk": "official-python-client",
                    "calls": calls,
                    "call_summary": call_summary,
                    "tool_schemas": schemas,
                    "capabilities": _structured(capability_call or {}),
                    "vfs_mount_order_diagnostics": vfs_mount_order_result,
                    "vfs_asset_projections": vfs_asset_projection_result,
                    "diagnostics_only": True,
                    "checks": checks,
                    "ok": all(checks.values()),
                }

        before_call: dict[str, object] | None = None
        before: dict[str, object] = {}
        while time.monotonic() < deadline:
            before_call = await _call(client, QUERY_TOOL)
            record(before_call)
            before = _structured(before_call)
            if before_call.get("is_error") is False and before.get("route") == "main_menu":
                break
            await asyncio.sleep(0.25)
        else:
            return red(
                "main_menu route was not observed",
                tool_schemas=schemas,
                capabilities=_structured(capability_call or {}),
                last_route=before,
            )

        new_game_call = await _call(client, ACTIVATE_NEW_GAME_TOOL)
        record(new_game_call)
        new_game = _structured(new_game_call)
        after_new_game = (
            new_game.get("after")
            if isinstance(new_game.get("after"), dict)
            else {}
        )
        if (
            new_game_call.get("is_error") is not False
            or after_new_game.get("route") != "bookmarks"
        ):
            return red(
                "new-game MCP action did not reach bookmarks",
                tool_schemas=schemas,
                capabilities=_structured(capability_call or {}),
                before=before,
                new_game=new_game,
            )

        if bookmarks_read_only:
            inspection_call = await _call(client, INSPECT_TOOL)
            record(inspection_call)
            inspection = _structured(inspection_call)
            checks = {
                "new_game_to_bookmarks": after_new_game.get("route")
                == "bookmarks",
                "native_bookmarks_tree": (
                    inspection_call.get("is_error") is False
                    and inspection.get("status") == "available"
                    and inspection.get("scope_root_name")
                    == "frontend_bookmarks"
                    and inspection.get("root_available") is True
                    and isinstance(inspection.get("widgets"), list)
                ),
            }
            private_model_call: dict[str, object] | None = None
            private_model: dict[str, object] = {}
            private_start_flow: dict[str, object] | None = None
            if bookmarks_model_private:
                private_model_call = _call_private_bookmarks_model(
                    driver, max(0.0, deadline - time.monotonic())
                )
                record(private_model_call)
                private_model = _structured(private_model_call)
                checks["private_native_model_frame"] = (
                    private_model_call.get("is_error") is False
                    and private_model.get("private_scope")
                    == "exact-build-bookmarks-model-v1"
                    and private_model.get("status")
                    in {"identity_ready", "unavailable"}
                )
                checks["selected_1066_feudal_candidate"] = (
                    private_model.get("candidate_identity_ready") is True
                    and private_model.get("selected_bookmark_key")
                    == "bm_1066_rags_to_riches"
                    and private_model.get("supported_1066_government_key")
                    == "feudal_government"
                    and private_model.get("selected_date_low_raw")
                    == 0x032AEB08
                    and private_model.get("supported_1066_date_matches")
                    is True
                    and isinstance(
                        private_model.get("supported_1066_candidate_index"),
                        int,
                    )
                    and not isinstance(
                        private_model.get("supported_1066_candidate_index"),
                        bool,
                    )
                    and private_model["supported_1066_candidate_index"] >= 0
                )
                if bookmarks_select_start_private:
                    private_start_flow = _controlled_private_feudal_start(
                        driver, private_model,
                        max(0.0, deadline - time.monotonic()),
                        expected_succession_lifecycle=(
                            expected_succession_lifecycle
                        ),
                    )
                    checks["controlled_private_1066_start"] = (
                        private_start_flow.get("ok") is True
                    )
            if vfs_mount_order_diagnostics:
                checks["vfs_mount_order_diagnostics_complete"] = (
                    isinstance(vfs_mount_order_result, dict)
                    and vfs_mount_order_result.get("ok") is True
                )
            return {
                "mcp_sdk": "official-python-client",
                "calls": calls,
                "call_summary": call_summary,
                "checks": checks,
                "before": before,
                "new_game": new_game,
                "bookmarks_tree": inspection,
                "private_bookmarks_model_call": private_model_call,
                "private_bookmarks_model": private_model,
                "private_1066_start_flow": private_start_flow,
                "vfs_mount_order_diagnostics": vfs_mount_order_result,
                "tree_truncated": inspection.get("truncated"),
                "read_only_after_new_game": not bookmarks_select_start_private,
                "ok": all(checks.values()),
            }

        prepare_call = await _call(client, ACTIVATE_PREPARE_CUSTOM_RULER_TOOL)
        record(prepare_call)
        prepare = _structured(prepare_call)
        after_prepare = (
            prepare.get("after")
            if isinstance(prepare.get("after"), dict)
            else {}
        )
        if (
            prepare_call.get("is_error") is not False
            or after_prepare.get("route") != "lobby"
        ):
            return red(
                "custom-ruler preparation did not reach a ready lobby",
                tool_schemas=schemas,
                capabilities=_structured(capability_call or {}),
                before=before,
                new_game=new_game,
                prepare_custom_ruler=prepare,
            )

        ruler_designer_call = await _call(client, ACTIVATE_RULER_DESIGNER_TOOL)
        record(ruler_designer_call)
        ruler_designer = _structured(ruler_designer_call)
        inspection_call = await _call(client, INSPECT_TOOL)
        record(inspection_call)
        inspection = _structured(inspection_call)
        coat_of_arms_call = await _call(
            client, ACTIVATE_COAT_OF_ARMS_DESIGNER_TOOL
        )
        record(coat_of_arms_call)
        coat_of_arms = _structured(coat_of_arms_call)
        coat_of_arms_inspection_call = await _call(client, INSPECT_TOOL)
        record(coat_of_arms_inspection_call)
        coat_of_arms_inspection = _structured(coat_of_arms_inspection_call)
        after_ruler_designer = (
            ruler_designer.get("after")
            if isinstance(ruler_designer.get("after"), dict)
            else {}
        )
        checks = {
            "closed_zero_input_tools": set(route_required) <= set(schemas),
            "before_main_menu": before.get("route") == "main_menu",
            "new_game_not_error": new_game_call.get("is_error") is False,
            "new_game_verified": new_game.get("status") == "verified",
            "new_game_postcondition_verified": new_game.get(
                "postcondition_verified"
            )
            is True,
            "after_bookmarks": after_new_game.get("route") == "bookmarks",
            "new_game_no_ocr": new_game.get("uses_ocr") is False,
            "new_game_no_keyboard": new_game.get("uses_keyboard") is False,
            "new_game_no_mouse": new_game.get("uses_mouse") is False,
            "new_game_native_semantic_backend": new_game.get("input_backend")
            == "native_gui_semantic_activation",
            "prepare_not_error": prepare_call.get("is_error") is False,
            "prepare_verified": prepare.get("status") == "verified",
            "prepare_postcondition_verified": prepare.get(
                "postcondition_verified"
            )
            is True,
            "after_lobby": after_prepare.get("route") == "lobby",
            "lobby_designer_button_ready": (
                frontend_lobby_default_ruler_designer_ready_v1(
                    prepare.get("lobby_inspection")
                )
            ),
            "prepare_no_ocr": prepare.get("uses_ocr") is False,
            "prepare_no_keyboard": prepare.get("uses_keyboard") is False,
            "prepare_no_mouse": prepare.get("uses_mouse") is False,
            "prepare_native_semantic_backend": prepare.get("input_backend")
            == "native_gui_semantic_activation",
            "ruler_designer_not_error": ruler_designer_call.get("is_error")
            is False,
            "ruler_designer_verified": ruler_designer.get("status")
            == "verified",
            "ruler_designer_postcondition_verified": ruler_designer.get(
                "postcondition_verified"
            )
            is True,
            "after_ruler_designer": after_ruler_designer.get("route")
            == "ruler_designer",
            "ruler_designer_no_ocr": ruler_designer.get("uses_ocr") is False,
            "ruler_designer_no_keyboard": ruler_designer.get("uses_keyboard")
            is False,
            "ruler_designer_no_mouse": ruler_designer.get("uses_mouse") is False,
            "ruler_designer_native_semantic_backend": ruler_designer.get(
                "input_backend"
            )
            == "native_gui_semantic_activation",
            "tree_inspection_available": (
                inspection_call.get("is_error") is False
                and inspection.get("status") == "available"
                and inspection.get("read_only") is True
                and inspection.get("scope_root_name") == "ruler_designer"
            ),
            "coat_of_arms_not_error": coat_of_arms_call.get("is_error")
            is False,
            "coat_of_arms_verified": coat_of_arms.get("status") == "verified",
            "coat_of_arms_postcondition_verified": coat_of_arms.get(
                "postcondition_verified"
            )
            is True,
            "after_coat_of_arms_designer": (
                isinstance(coat_of_arms.get("after"), dict)
                and coat_of_arms["after"].get("route")
                == "coat_of_arms_designer"
            ),
            "coat_of_arms_no_ocr": coat_of_arms.get("uses_ocr") is False,
            "coat_of_arms_no_keyboard": coat_of_arms.get("uses_keyboard")
            is False,
            "coat_of_arms_no_mouse": coat_of_arms.get("uses_mouse") is False,
            "coat_of_arms_native_semantic_backend": coat_of_arms.get(
                "input_backend"
            )
            == "native_gui_semantic_activation",
            "coat_of_arms_tree_visible": (
                coat_of_arms_inspection_call.get("is_error") is False
                and coat_of_arms_inspection.get("status") == "available"
                and any(
                    isinstance(row, dict)
                    and row.get("runtime_name") == "coat_of_arms_page"
                    and row.get("child_path") == "0/2"
                    and row.get("effective_visible") is True
                    and row.get("enabled") is True
                    for row in coat_of_arms_inspection.get("widgets", [])
                )
            ),
        }
        matrix_result: dict[str, object] | None = None
        custom_mode_result: dict[str, object] | None = None
        if custom_mode_census:
            if all(checks.values()):
                custom_mode_result = await _collect_custom_mode_census(
                    client, record
                )
            else:
                custom_mode_result = {
                    "ok": False,
                    "error": "route checks failed before custom-mode census",
                }
            checks["custom_mode_census_evidence_complete"] = (
                custom_mode_result.get("ok") is True
            )
        if syntax_matrix is not None:
            if all(checks.values()):
                matrix_result = await _collect_syntax_matrix(
                    client, syntax_matrix, record
                )
            else:
                matrix_result = {
                    "ok": False,
                    "error": "route checks failed before syntax collection",
                    "matrix": syntax_matrix,
                    "cases": [],
                }
            checks["syntax_matrix_evidence_complete"] = (
                matrix_result.get("ok") is True
            )
        commit_result: dict[str, object] | None = None
        if commit_roundtrip:
            if all(checks.values()):
                commit_result = await _collect_commit_roundtrip(client, record)
            else:
                commit_result = {
                    "ok": False,
                    "error": "route checks failed before commit round-trip",
                }
            checks["commit_roundtrip_evidence_complete"] = (
                commit_result.get("ok") is True
            )
        large_source_result: dict[str, object] | None = None
        if large_source is not None:
            if all(checks.values()):
                large_source_result = await _collect_large_source_roundtrip(
                    client,
                    large_source[0],
                    large_source[1],
                    record,
                )
            else:
                large_source_result = {
                    "ok": False,
                    "error": "route checks failed before large-source round-trip",
                }
            checks["large_source_roundtrip_evidence_complete"] = (
                large_source_result.get("ok") is True
            )
        framebuffer_result: dict[str, object] | None = None
        if reference_preview is not None:
            if (
                all(checks.values())
                and large_source_result is not None
                and large_source_result.get("ok") is True
            ):
                await asyncio.sleep(0.75)
                preview_base64, preview_receipt = reference_preview
                preparation_call = await _call(
                    client, PREPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL
                )
                record(preparation_call)
                framebuffer_call = await _call(
                    client,
                    COMPARE_COAT_OF_ARMS_FRAMEBUFFER_TOOL,
                    {
                        "reference_png_base64": preview_base64,
                        "reference_png_sha256": preview_receipt["png_sha256"],
                    },
                )
                record(framebuffer_call)
                framebuffer_result = {
                    **_framebuffer_gate(framebuffer_call),
                    "reference": preview_receipt,
                    "preparation": preparation_call,
                }
                framebuffer_result["ok"] = bool(
                    framebuffer_result["ok"]
                    and preparation_call.get("is_error") is False
                    and _structured(preparation_call).get("routeStable") is True
                )
            else:
                framebuffer_result = {
                    "ok": False,
                    "error": "route or large-source checks failed before framebuffer comparison",
                    "reference": reference_preview[1],
                }
            checks["reference_framebuffer_evidence_complete"] = (
                framebuffer_result.get("ok") is True
            )
        corpus_result: dict[str, object] | None = None
        if picture_corpus is not None:
            if all(checks.values()):
                corpus_result = await _collect_picture_corpus(
                    client, picture_corpus, record
                )
            else:
                corpus_result = {
                    "ok": False,
                    "error": "route checks failed before picture-corpus comparison",
                    "case_count": len(picture_corpus),
                    "cases": [],
                }
            checks["picture_corpus_evidence_complete"] = (
                corpus_result.get("ok") is True
            )
        parent_semantics_result: dict[str, object] | None = None
        if parent_semantics_matrix:
            if all(checks.values()):
                parent_semantics_result = await _collect_parent_semantics_matrix(
                    client, record
                )
            else:
                parent_semantics_result = {
                    "ok": False,
                    "error": "route checks failed before parent semantics matrix",
                }
            checks["parent_semantics_evidence_complete"] = (
                parent_semantics_result.get("ok") is True
            )
        vfs_winner_result: dict[str, object] | None = None
        if vfs_winner_matrix:
            if all(checks.values()):
                vfs_winner_result = await _collect_vfs_winner_matrix(
                    client, record
                )
            else:
                vfs_winner_result = {
                    "ok": False,
                    "error": "route checks failed before VFS winner matrix",
                }
            checks["vfs_winner_evidence_complete"] = (
                vfs_winner_result.get("ok") is True
            )
        vfs_extended_result: dict[str, object] | None = None
        if vfs_extended_matrix:
            if all(checks.values()):
                vfs_extended_result = await _collect_vfs_winner_matrix(
                    client, record, extended=True
                )
            else:
                vfs_extended_result = {
                    "ok": False,
                    "error": "route checks failed before extended VFS matrix",
                }
            checks["vfs_extended_evidence_complete"] = (
                vfs_extended_result.get("ok") is True
            )
        vfs_replace_path_result: dict[str, object] | None = None
        if vfs_replace_path_matrix:
            if all(checks.values()):
                vfs_replace_path_result = await _collect_vfs_winner_matrix(
                    client, record, replace_path=True
                )
            else:
                vfs_replace_path_result = {
                    "ok": False,
                    "error": "route checks failed before replace_path VFS matrix",
                }
            checks["vfs_replace_path_evidence_complete"] = (
                vfs_replace_path_result.get("ok") is True
            )
        if vfs_mount_order_diagnostics:
            checks["vfs_mount_order_diagnostics_complete"] = (
                isinstance(vfs_mount_order_result, dict)
                and vfs_mount_order_result.get("ok") is True
            )
        if vfs_asset_projection_paths:
            checks["vfs_asset_projections_complete"] = (
                isinstance(vfs_asset_projection_result, dict)
                and vfs_asset_projection_result.get("ok") is True
            )
        return {
            "mcp_sdk": "official-python-client",
            "tool_schemas": schemas,
            "capabilities": _structured(capability_call or {}),
            "before": before,
            "new_game": new_game,
            "prepare_custom_ruler": prepare,
            "ruler_designer": ruler_designer,
            "tree_inspection_after_ruler_designer": inspection,
            "coat_of_arms_designer": coat_of_arms,
            "tree_inspection_after_coat_of_arms_designer": (
                coat_of_arms_inspection
            ),
            "custom_mode_census": custom_mode_result,
            "syntax_matrix": matrix_result,
            "commit_roundtrip": commit_result,
            "large_source_roundtrip": large_source_result,
            "reference_framebuffer": framebuffer_result,
            "picture_corpus": corpus_result,
            "parent_semantics_matrix": parent_semantics_result,
            "vfs_winner_matrix": vfs_winner_result,
            "vfs_extended_matrix": vfs_extended_result,
            "vfs_replace_path_matrix": vfs_replace_path_result,
            "vfs_mount_order_diagnostics": vfs_mount_order_result,
            "vfs_asset_projections": vfs_asset_projection_result,
            "calls": calls,
            "call_summary": call_summary,
            "checks": checks,
            "ok": all(checks.values()),
        }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _write_native_crop(
    path: Path, sequence: dict[str, object]
) -> dict[str, object]:
    framebuffer = sequence.get("reference_framebuffer")
    call = framebuffer.get("call") if isinstance(framebuffer, dict) else None
    if not isinstance(call, dict):
        raise RuntimeError("framebuffer result has no native crop call")
    return _write_native_crop_call(path, call)


def _write_native_crop_call(
    path: Path, call: dict[str, object]
) -> dict[str, object]:
    body = _structured(call) if isinstance(call, dict) else {}
    comparison = body.get("comparison")
    best = (
        comparison.get("bestMatch")
        if isinstance(comparison, dict)
        and isinstance(comparison.get("bestMatch"), dict)
        else {}
    )
    encoded = best.get("alignedContentPngBase64")
    expected_sha256 = best.get("alignedContentPngSha256")
    payload_kind = "aligned-content"
    if not isinstance(encoded, str) or not isinstance(expected_sha256, str):
        encoded = best.get("cropPngBase64")
        expected_sha256 = best.get("cropPngSha256")
        payload_kind = "outer-match"
    if not isinstance(encoded, str) or not isinstance(expected_sha256, str):
        raise RuntimeError("framebuffer result has no native crop payload")
    try:
        raw = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError) as error:
        raise RuntimeError("framebuffer crop base64 is malformed") from error
    actual_sha256 = hashlib.sha256(raw).hexdigest().upper()
    if actual_sha256 != expected_sha256:
        raise RuntimeError("framebuffer crop SHA-256 mismatch")
    resolved = path.resolve()
    temporary = resolved.with_name(resolved.name + ".tmp")
    if resolved.exists() or temporary.exists():
        raise RuntimeError(f"native crop output already exists: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_bytes(raw)
    temporary.replace(resolved)
    return {
        "path": str(resolved),
        "bytes": len(raw),
        "sha256": actual_sha256,
        "payload_kind": payload_kind,
    }


def _write_picture_corpus_crops(
    path: Path, sequence: dict[str, object]
) -> list[dict[str, object]]:
    corpus = sequence.get("picture_corpus")
    cases = corpus.get("cases") if isinstance(corpus, dict) else None
    if not isinstance(cases, list) or not cases:
        raise RuntimeError("picture corpus result has no cases")
    root = path.resolve()
    receipts: list[dict[str, object]] = []
    for value in cases:
        if not isinstance(value, dict) or not isinstance(value.get("id"), str):
            raise RuntimeError("picture corpus result has a malformed case")
        framebuffer = value.get("framebuffer")
        copy_reapply = value.get("copy_reapply")
        copy_framebuffer = (
            copy_reapply.get("framebuffer")
            if isinstance(copy_reapply, dict)
            else None
        )
        candidates = (
            (
                "original-apply",
                "native-crop.png",
                framebuffer.get("call")
                if isinstance(framebuffer, dict)
                else None,
            ),
            (
                "copy-reapplied",
                "native-copy-reapplied-crop.png",
                copy_framebuffer.get("call")
                if isinstance(copy_framebuffer, dict)
                else None,
            ),
        )
        for kind, filename, call in candidates:
            if not isinstance(call, dict):
                continue
            receipt = _write_native_crop_call(
                root / value["id"] / filename, call
            )
            receipts.append(
                {"id": value["id"], "kind": kind, **receipt}
            )
    if not receipts:
        raise RuntimeError("picture corpus produced no native crops")
    return receipts


def _write_reference_free_matrix_crops(
    path: Path,
    sequence: dict[str, object],
    *,
    matrix_key: str,
    label: str,
) -> list[dict[str, object]]:
    matrix = sequence.get(matrix_key)
    cases = matrix.get("cases") if isinstance(matrix, dict) else None
    if not isinstance(cases, list) or not cases:
        raise RuntimeError(f"{label} result has no cases")
    root = path.resolve()
    receipts: list[dict[str, object]] = []
    for value in cases:
        if not isinstance(value, dict) or not isinstance(value.get("id"), str):
            raise RuntimeError(f"{label} result has a malformed case")
        gated = value.get("capture")
        call = gated.get("call") if isinstance(gated, dict) else None
        body = _structured(call) if isinstance(call, dict) else {}
        capture = body.get("capture")
        if not isinstance(capture, dict):
            continue
        encoded = capture.get("alignedContentPngBase64")
        expected_sha256 = capture.get("alignedContentPngSha256")
        if not isinstance(encoded, str) or not isinstance(expected_sha256, str):
            continue
        raw = base64.b64decode(encoded.encode("ascii"), validate=True)
        actual_sha256 = hashlib.sha256(raw).hexdigest().upper()
        if actual_sha256 != expected_sha256:
            raise RuntimeError(f"{label} crop SHA-256 mismatch")
        output = root / f"{value['id']}.png"
        temporary = output.with_name(output.name + ".tmp")
        if output.exists() or temporary.exists():
            raise RuntimeError(f"{label} crop already exists: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_bytes(raw)
        temporary.replace(output)
        receipts.append(
            {
                "id": value["id"],
                "path": str(output),
                "bytes": len(raw),
                "sha256": actual_sha256,
                "payload_kind": "aligned-content-reference-free",
            }
        )
    if len(receipts) != len(cases):
        raise RuntimeError(f"{label} matrix did not produce every crop")
    return receipts


def _write_parent_semantics_crops(
    path: Path, sequence: dict[str, object]
) -> list[dict[str, object]]:
    return _write_reference_free_matrix_crops(
        path,
        sequence,
        matrix_key="parent_semantics_matrix",
        label="parent semantics",
    )


def _write_vfs_winner_crops(
    path: Path, sequence: dict[str, object]
) -> list[dict[str, object]]:
    return _write_reference_free_matrix_crops(
        path,
        sequence,
        matrix_key="vfs_winner_matrix",
        label="VFS winner",
    )


def _write_vfs_extended_crops(
    path: Path, sequence: dict[str, object]
) -> list[dict[str, object]]:
    return _write_reference_free_matrix_crops(
        path,
        sequence,
        matrix_key="vfs_extended_matrix",
        label="extended VFS",
    )


def _write_vfs_replace_path_crops(
    path: Path, sequence: dict[str, object]
) -> list[dict[str, object]]:
    return _write_reference_free_matrix_crops(
        path,
        sequence,
        matrix_key="vfs_replace_path_matrix",
        label="replace_path VFS",
    )


def _run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    started = time.monotonic()
    repository = Path(__file__).resolve().parents[3]
    steam_loginusers = _resolve_steam_loginusers(args.steam_loginusers)
    syntax_matrix = (
        _load_syntax_matrix() if getattr(args, "syntax_matrix", False) else None
    )
    commit_roundtrip = bool(getattr(args, "commit_roundtrip", False))
    custom_mode_census = bool(getattr(args, "custom_mode_census", False))
    bookmarks_read_only = bool(getattr(args, "bookmarks_read_only", False))
    bookmarks_model_private = bool(
        getattr(args, "bookmarks_model_private", False)
    )
    bookmarks_select_start_private = bool(
        getattr(args, "bookmarks_select_start_private", False)
    )
    ordinary_campaign_xar_off_seed = bool(
        getattr(args, "ordinary_campaign_xar_off_seed", False)
    )
    reference_preview = (
        _load_reference_preview(args.reference_preview)
        if getattr(args, "reference_preview", None) is not None
        else None
    )
    native_crop_output = getattr(args, "native_crop_output", None)
    picture_corpus = (
        _load_picture_corpus(args.picture_corpus)
        if getattr(args, "picture_corpus", None) is not None
        else None
    )
    single_reference_case = (
        _load_single_reference_case(args.single_reference_case)
        if getattr(args, "single_reference_case", None) is not None
        else None
    )
    if picture_corpus is not None and single_reference_case is not None:
        raise ValueError(
            "--picture-corpus cannot be combined with --single-reference-case"
        )
    reference_cases = (
        picture_corpus
        if picture_corpus is not None
        else [single_reference_case]
        if single_reference_case is not None
        else None
    )
    picture_crop_dir = getattr(args, "picture_crop_dir", None)
    parent_semantics_matrix = bool(
        getattr(args, "parent_semantics_matrix", False)
    )
    parent_crop_dir = getattr(args, "parent_crop_dir", None)
    vfs_winner_matrix = bool(getattr(args, "vfs_winner_matrix", False))
    vfs_crop_dir = getattr(args, "vfs_crop_dir", None)
    vfs_extended_matrix = bool(getattr(args, "vfs_extended_matrix", False))
    vfs_extended_crop_dir = getattr(args, "vfs_extended_crop_dir", None)
    vfs_replace_path_matrix = bool(
        getattr(args, "vfs_replace_path_matrix", False)
    )
    vfs_replace_path_crop_dir = getattr(args, "vfs_replace_path_crop_dir", None)
    vfs_mount_order_diagnostics = bool(
        getattr(args, "vfs_mount_order_diagnostics", False)
    )
    vfs_mount_order_diagnostics_only = bool(
        getattr(args, "vfs_mount_order_diagnostics_only", False)
    )
    vfs_asset_projection_paths = tuple(
        str(value) for value in getattr(args, "vfs_asset_projection_path", [])
    )
    if vfs_mount_order_diagnostics_only and not vfs_mount_order_diagnostics:
        raise ValueError(
            "--vfs-mount-order-diagnostics-only requires "
            "--vfs-mount-order-diagnostics"
        )
    if vfs_asset_projection_paths and not vfs_mount_order_diagnostics:
        raise ValueError(
            "--vfs-asset-projection-path requires "
            "--vfs-mount-order-diagnostics"
        )
    if len(vfs_asset_projection_paths) != len(set(vfs_asset_projection_paths)):
        raise ValueError("--vfs-asset-projection-path values must be unique")
    if reference_cases is not None and (
        getattr(args, "large_source", None) is not None
        or reference_preview is not None
    ):
        raise ValueError(
            "reference cases cannot be combined with --large-source or --reference-preview"
        )
    if (
        reference_preview is not None
        and getattr(args, "large_source", None) is None
    ):
        raise ValueError("--reference-preview requires --large-source")
    if native_crop_output is not None and reference_preview is None:
        raise ValueError("--native-crop-output requires --reference-preview")
    if picture_crop_dir is not None and reference_cases is None:
        raise ValueError(
            "--picture-crop-dir requires --picture-corpus or --single-reference-case"
        )
    if parent_crop_dir is not None and not parent_semantics_matrix:
        raise ValueError(
            "--parent-crop-dir requires --parent-semantics-matrix"
        )
    if vfs_crop_dir is not None and not vfs_winner_matrix:
        raise ValueError("--vfs-crop-dir requires --vfs-winner-matrix")
    if vfs_extended_crop_dir is not None and not vfs_extended_matrix:
        raise ValueError(
            "--vfs-extended-crop-dir requires --vfs-extended-matrix"
        )
    if vfs_replace_path_crop_dir is not None and not vfs_replace_path_matrix:
        raise ValueError(
            "--vfs-replace-path-crop-dir requires --vfs-replace-path-matrix"
        )
    if parent_semantics_matrix and (
        syntax_matrix is not None
        or custom_mode_census
        or commit_roundtrip
        or getattr(args, "large_source", None) is not None
        or reference_preview is not None
        or reference_cases is not None
        or vfs_winner_matrix
        or vfs_extended_matrix
        or vfs_replace_path_matrix
    ):
        raise ValueError(
            "--parent-semantics-matrix cannot be combined with other CoA matrices"
        )
    if vfs_winner_matrix and (
        syntax_matrix is not None
        or custom_mode_census
        or commit_roundtrip
        or getattr(args, "large_source", None) is not None
        or reference_preview is not None
        or reference_cases is not None
        or parent_semantics_matrix
        or vfs_extended_matrix
        or vfs_replace_path_matrix
    ):
        raise ValueError(
            "--vfs-winner-matrix cannot be combined with other CoA matrices"
        )
    if vfs_extended_matrix and (
        syntax_matrix is not None
        or custom_mode_census
        or commit_roundtrip
        or getattr(args, "large_source", None) is not None
        or reference_preview is not None
        or reference_cases is not None
        or parent_semantics_matrix
        or vfs_winner_matrix
        or vfs_replace_path_matrix
    ):
        raise ValueError(
            "--vfs-extended-matrix cannot be combined with other CoA matrices"
        )
    if vfs_replace_path_matrix and (
        syntax_matrix is not None
        or custom_mode_census
        or commit_roundtrip
        or getattr(args, "large_source", None) is not None
        or reference_preview is not None
        or reference_cases is not None
        or parent_semantics_matrix
        or vfs_winner_matrix
        or vfs_extended_matrix
    ):
        raise ValueError(
            "--vfs-replace-path-matrix cannot be combined with other CoA matrices"
        )
    if bookmarks_model_private and not bookmarks_read_only:
        raise ValueError("--bookmarks-model-private requires --bookmarks-read-only")
    if bookmarks_select_start_private and not (
        bookmarks_read_only and bookmarks_model_private
    ):
        raise ValueError(
            "--bookmarks-select-start-private requires both "
            "--bookmarks-read-only and --bookmarks-model-private"
        )
    if ordinary_campaign_xar_off_seed and not bookmarks_select_start_private:
        raise ValueError(
            "--ordinary-campaign-xar-off-seed requires "
            "--bookmarks-select-start-private"
        )
    if bookmarks_read_only and (
        syntax_matrix is not None
        or custom_mode_census
        or commit_roundtrip
        or getattr(args, "large_source", None) is not None
        or reference_preview is not None
        or picture_corpus is not None
        or parent_semantics_matrix
        or vfs_winner_matrix
        or vfs_extended_matrix
        or vfs_replace_path_matrix
        or vfs_mount_order_diagnostics
    ):
        raise ValueError("--bookmarks-read-only cannot run CoA actions")
    large_source = (
        _load_large_source(args.large_source)
        if getattr(args, "large_source", None) is not None
        else None
    )
    state_dir = args.state_dir.resolve()
    output = args.output.resolve()
    if ordinary_campaign_xar_off_seed:
        if not state_dir.is_dir():
            raise RuntimeError(
                "ordinary xar_off seed requires an existing prepared state directory: "
                f"{state_dir}"
            )
    elif state_dir.exists():
        raise RuntimeError(f"state directory already exists: {state_dir}")
    if output.exists() or output.with_name(output.name + ".tmp").exists():
        raise RuntimeError(f"artifact output already exists: {output}")
    ensure_state_path_safe(state_dir)
    if not ordinary_campaign_xar_off_seed:
        state_dir.mkdir(parents=True, exist_ok=False)

    report: dict[str, object] = {
        "schema": "ck3-frontend-gui-route-v1-live-acceptance",
        "schema_version": 1,
        "created_at": utc_now(),
        "repository_head": _git_head(repository),
        "open_kaishek": {
            "status": "not-applicable",
            "reason": "No frontend GUI or coat-of-arms domain exists in open_kaishek.",
        },
        "interaction_policy": {
            "mcp_only": not bookmarks_model_private,
            "mcp_baseline_private_native_read_only":
                bookmarks_model_private and not bookmarks_select_start_private,
            "controlled_private_native_selection_start":
                bookmarks_select_start_private,
            "uses_ocr": False,
            "uses_keyboard": False,
            "uses_mouse": False,
        },
        "syntax_matrix_requested": syntax_matrix is not None,
        "syntax_matrix_plan": syntax_matrix,
        "custom_mode_census_requested": custom_mode_census,
        "bookmarks_read_only_requested": bookmarks_read_only,
        "bookmarks_model_private_requested": bookmarks_model_private,
        "bookmarks_select_start_private_requested":
            bookmarks_select_start_private,
        "ordinary_campaign_xar_off_seed_requested": (
            ordinary_campaign_xar_off_seed
        ),
        "commit_roundtrip_requested": commit_roundtrip,
        "large_source_requested": large_source is not None,
        "large_source_plan": large_source[1] if large_source else None,
        "reference_preview_requested": reference_preview is not None,
        "reference_preview_plan": (
            reference_preview[1] if reference_preview else None
        ),
        "picture_corpus_requested": picture_corpus is not None,
        "single_reference_case_requested": single_reference_case is not None,
        "picture_corpus_plan": [
            {
                "id": value["id"],
                "source": value["source_receipt"],
                "reference": value["preview_receipt"],
            }
            for value in reference_cases or []
        ],
        "parent_semantics_matrix_requested": parent_semantics_matrix,
        "parent_semantics_plan": (
            [
                {
                    "id": value["id"],
                    "source": _source_receipt_from_text(
                        value["source"],
                        source_label=f"parent-semantics:{value['id']}",
                    ),
                }
                for value in PARENT_SEMANTICS_CASES
            ]
            if parent_semantics_matrix
            else None
        ),
        "vfs_winner_matrix_requested": vfs_winner_matrix,
        "vfs_winner_plan": (
            {
                "predeclared_hypothesis": (
                    "enabled_mods load_order 1 owns the conflicting direct DDS path"
                ),
                "cases": [
                    {
                        "id": value["id"],
                        "source": _source_receipt_from_text(
                            value["source"],
                            source_label=f"vfs-winner:{value['id']}",
                        ),
                    }
                    for value in VFS_WINNER_CASES
                ],
                "diagnostic_pairs": [list(value) for value in VFS_WINNER_DIAGNOSTIC_PAIRS],
                "capture_noise_thresholds": dict(
                    PARENT_SEMANTICS_CAPTURE_NOISE_THRESHOLDS
                ),
            }
            if vfs_winner_matrix
            else None
        ),
        "vfs_extended_matrix_requested": vfs_extended_matrix,
        "vfs_extended_plan": (
            {
                "predeclared_hypotheses": [
                    "enabled directory mod owns the conflicting base-game direct DDS path",
                    "later enabled archive mod owns the conflicting direct DDS path over the earlier directory mod",
                ],
                "cases": [
                    {
                        "id": value["id"],
                        "source": _source_receipt_from_text(
                            value["source"],
                            source_label=f"vfs-extended:{value['id']}",
                        ),
                    }
                    for value in VFS_EXTENDED_CASES
                ],
                "diagnostic_pairs": [
                    list(value) for value in VFS_EXTENDED_DIAGNOSTIC_PAIRS
                ],
                "capture_noise_thresholds": dict(
                    PARENT_SEMANTICS_CAPTURE_NOISE_THRESHOLDS
                ),
            }
            if vfs_extended_matrix
            else None
        ),
        "vfs_replace_path_matrix_requested": vfs_replace_path_matrix,
        "vfs_replace_path_plan": (
            {
                "predeclared_hypotheses": [
                    "the base-game-only pattern behaves like a never-present missing control",
                    "the earlier enabled-mod pattern remains available and differs from both "
                    "the missing control and the later replacement pattern",
                ],
                "cases": [
                    {
                        "id": value["id"],
                        "source": _source_receipt_from_text(
                            value["source"],
                            source_label=f"vfs-replace-path:{value['id']}",
                        ),
                    }
                    for value in VFS_REPLACE_PATH_CASES
                ],
                "diagnostic_pairs": [
                    list(value) for value in VFS_REPLACE_PATH_DIAGNOSTIC_PAIRS
                ],
                "capture_noise_thresholds": dict(
                    PARENT_SEMANTICS_CAPTURE_NOISE_THRESHOLDS
                ),
            }
            if vfs_replace_path_matrix
            else None
        ),
        "vfs_mount_order_diagnostics_requested": vfs_mount_order_diagnostics,
        "vfs_mount_order_diagnostics_only": vfs_mount_order_diagnostics_only,
        "vfs_asset_projection_paths": list(vfs_asset_projection_paths),
        "vfs_mount_order_diagnostics_plan": (
            {
                "transport": "official MCP ck3_get_bridge_diagnostics",
                "observer": "physfs_mounted_data_observer_v1",
                "bounded_publisher_slots": 128,
                "expected_fragments_in_order": list(
                    VFS_MOUNT_ORDER_EXPECTED_FRAGMENTS
                ),
                "evidence_boundary": (
                    "startup mount publisher order only; no per-resource winner claim"
                ),
            }
            if vfs_mount_order_diagnostics
            else None
        ),
        "vfs_asset_projection_plan": (
            {
                "transport": (
                    "official MCP "
                    "ck3_project_coat_of_arms_vfs_asset_winner_v1"
                ),
                "logical_paths": list(vfs_asset_projection_paths),
                "success_contract": (
                    "each direct DDS path has a hash-bound later-mount winner"
                ),
                "evidence_boundary": (
                    "projection from live mount receipt plus source bytes; "
                    "does not call CK3's internal resolver, observe resource "
                    "registration, or apply replace_path/definition merging"
                ),
            }
            if vfs_asset_projection_paths
            else None
        ),
    }
    handle = None
    driver: NativeHeadlessGameplayDriver | None = None
    primary_error: str | None = None
    cleanup: dict[str, object] | None = None
    slot_stack = ExitStack()
    shared_slot: dict[str, object] = {
        "mechanism": "exclusive_launch_lock + exclusive_state_lock",
        "launch_lock_acquired": False,
        "state_lock_acquired": False,
        "released": False,
    }
    report["shared_ck3_slot"] = shared_slot
    try:
        report["steam"] = _steam_offline(steam_loginusers)
        spec = make_spec(state_dir, args.game_dir.resolve())
        succession_lifecycle_binding: dict[str, object] | None = None
        if ordinary_campaign_xar_off_seed:
            source_profile = args.source_profile.resolve()
            if source_profile != spec.profile_dir.resolve():
                raise RuntimeError(
                    "ordinary xar_off seed must use state-dir/profile in place; "
                    f"received {source_profile}"
                )
            stale_driver_state = state_dir / "native-session" / "driver-state.json"
            checkpoint_path = spec.profile_dir / "save games" / "xar_checkpoint.ck3"
            if stale_driver_state.exists() or checkpoint_path.exists():
                raise RuntimeError(
                    "ordinary xar_off seed state already contains driver/checkpoint state"
                )
            try:
                prepared_environment = verify_profile(spec, xar_enabled="xar_off")
                succession_lifecycle_binding = (
                    bind_succession_lifecycle_from_environment_v1(
                        prepared_environment,
                        lifecycle=ORDINARY_CAMPAIGN_SUCCESSION,
                        ordinary_campaign_no_pact=True,
                    )
                )
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
                raise RuntimeError(
                    "ordinary seed state is not a verified frozen xar_off "
                    f"environment: {error}"
                ) from error
            report["profile"] = {
                "mode": "prepared-in-place",
                "source": str(source_profile),
                "target": str(spec.profile_dir.resolve()),
                "environment_sha256": prepared_environment.get(
                    "environment_sha256"
                ),
                "xar_enabled": "xar_off",
            }
            report["succession_lifecycle"] = succession_lifecycle_binding
        else:
            report["profile"] = _copy_profile(
                args.source_profile, spec.profile_dir
            )
        dll = args.bridge_dll.resolve()
        injector = args.bridge_injector.resolve()
        binary = {
            "ck3_exe": str(spec.game_exe),
            "ck3_exe_sha256": _sha256(spec.game_exe),
            "bridge_dll": str(dll),
            "bridge_dll_sha256": _sha256(dll),
            "bridge_injector": str(injector),
            "bridge_injector_sha256": _sha256(injector),
        }
        report["binary"] = binary
        if binary["ck3_exe_sha256"] != EXPECTED_CK3_SHA256:
            raise RuntimeError("CK3 executable SHA-256 differs from the exact-build pin")
        slot_stack.enter_context(exclusive_launch_lock(spec.game_exe))
        shared_slot["launch_lock_acquired"] = True
        slot_stack.enter_context(
            exclusive_state_lock(
                state_dir, "frontend-gui-route-v1-live-acceptance"
            )
        )
        shared_slot["state_lock_acquired"] = True
        config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=args.bridge_pipe,
            dll_path=dll,
            injector_path=injector,
        )
        driver_options: dict[str, object] = {}
        if succession_lifecycle_binding is not None:
            driver_options["succession_lifecycle_binding"] = (
                succession_lifecycle_binding
            )
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=state_dir,
            save_dir=spec.profile_dir / "save games",
            **driver_options,
        )
        handle = launch(
            spec,
            native_bridge=config,
            continue_last_save=False,
            verify_prepared_profile=ordinary_campaign_xar_off_seed,
            prepared_xar_enabled=(
                "xar_off" if ordinary_campaign_xar_off_seed else "xar_on"
            ),
        )
        report["managed_pid"] = int(handle.process.pid)
        sequence = asyncio.run(
            _mcp_sequence(
                driver,
                float(args.timeout),
                syntax_matrix=syntax_matrix,
                custom_mode_census=custom_mode_census,
                commit_roundtrip=commit_roundtrip,
                large_source=large_source,
                reference_preview=reference_preview,
                picture_corpus=reference_cases,
                parent_semantics_matrix=parent_semantics_matrix,
                vfs_winner_matrix=vfs_winner_matrix,
                vfs_extended_matrix=vfs_extended_matrix,
                vfs_replace_path_matrix=vfs_replace_path_matrix,
                vfs_mount_order_diagnostics=vfs_mount_order_diagnostics,
                vfs_mount_order_diagnostics_only=(
                    vfs_mount_order_diagnostics_only
                ),
                vfs_asset_projection_paths=vfs_asset_projection_paths,
                game_directory=str(args.game_dir.resolve()),
                bookmarks_read_only=bookmarks_read_only,
                bookmarks_model_private=bookmarks_model_private,
                bookmarks_select_start_private=bookmarks_select_start_private,
                expected_succession_lifecycle=succession_lifecycle_binding,
            )
        )
        report["sequence"] = sequence
        if native_crop_output is not None:
            try:
                report["native_crop"] = _write_native_crop(
                    native_crop_output, sequence
                )
            except RuntimeError as error:
                report["native_crop"] = {
                    "status": "unavailable",
                    "error": str(error),
                }
                if sequence.get("ok") is True:
                    raise
        if picture_crop_dir is not None:
            try:
                report["picture_corpus_native_crops"] = (
                    _write_picture_corpus_crops(picture_crop_dir, sequence)
                )
            except RuntimeError as error:
                report["picture_corpus_native_crops"] = {
                    "status": "unavailable",
                    "error": str(error),
                }
                corpus_result = sequence.get("picture_corpus")
                if (
                    isinstance(corpus_result, dict)
                    and corpus_result.get("cases")
                ):
                    raise
        if parent_crop_dir is not None:
            try:
                report["parent_semantics_native_crops"] = (
                    _write_parent_semantics_crops(parent_crop_dir, sequence)
                )
            except RuntimeError as error:
                report["parent_semantics_native_crops"] = {
                    "status": "unavailable",
                    "error": str(error),
                }
                matrix_result = sequence.get("parent_semantics_matrix")
                if (
                    isinstance(matrix_result, dict)
                    and matrix_result.get("cases")
                ):
                    raise
        if vfs_crop_dir is not None:
            try:
                report["vfs_winner_native_crops"] = _write_vfs_winner_crops(
                    vfs_crop_dir, sequence
                )
            except RuntimeError as error:
                report["vfs_winner_native_crops"] = {
                    "status": "unavailable",
                    "error": str(error),
                }
                matrix_result = sequence.get("vfs_winner_matrix")
                if (
                    isinstance(matrix_result, dict)
                    and matrix_result.get("cases")
                ):
                    raise
        if vfs_extended_crop_dir is not None:
            try:
                report["vfs_extended_native_crops"] = _write_vfs_extended_crops(
                    vfs_extended_crop_dir, sequence
                )
            except RuntimeError as error:
                report["vfs_extended_native_crops"] = {
                    "status": "unavailable",
                    "error": str(error),
                }
                matrix_result = sequence.get("vfs_extended_matrix")
                if (
                    isinstance(matrix_result, dict)
                    and matrix_result.get("cases")
                ):
                    raise
        if vfs_replace_path_crop_dir is not None:
            try:
                report["vfs_replace_path_native_crops"] = (
                    _write_vfs_replace_path_crops(
                        vfs_replace_path_crop_dir, sequence
                    )
                )
            except RuntimeError as error:
                report["vfs_replace_path_native_crops"] = {
                    "status": "unavailable",
                    "error": str(error),
                }
                matrix_result = sequence.get("vfs_replace_path_matrix")
                if (
                    isinstance(matrix_result, dict)
                    and matrix_result.get("cases")
                ):
                    raise
        if sequence.get("ok") is not True:
            raise RuntimeError("frontend MCP route sequence failed its checks")
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        if handle is not None:
            try:
                cleanup = stop_tracked(handle, require_running=False)
            except BaseException as error:
                cleanup = {
                    "ok": False,
                    "error": f"{type(error).__name__}: {error}",
                }
                if primary_error is None:
                    primary_error = cleanup["error"]
        if driver is not None:
            try:
                driver.close()
            except BaseException as error:
                if primary_error is None:
                    primary_error = f"driver close failed: {type(error).__name__}: {error}"
        try:
            slot_stack.close()
            if (
                shared_slot["launch_lock_acquired"] is True
                or shared_slot["state_lock_acquired"] is True
            ):
                shared_slot["released"] = True
        except BaseException as error:
            if primary_error is None:
                primary_error = (
                    f"shared CK3 slot release failed: {type(error).__name__}: {error}"
                )

    report["cleanup"] = cleanup
    report["error"] = primary_error
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    report["ok"] = bool(
        primary_error is None
        and isinstance(report.get("sequence"), dict)
        and report["sequence"].get("ok") is True
        and isinstance(cleanup, dict)
        and cleanup.get("cleanup_proven") is True
        and cleanup.get("tree_gone") is True
    )
    _write_json(output, report)
    return report, 0 if report["ok"] else 1


def main() -> int:
    args = _parser().parse_args()
    try:
        report, exit_code = _run(args)
    except BaseException as error:
        print(f"frontend GUI route acceptance setup failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

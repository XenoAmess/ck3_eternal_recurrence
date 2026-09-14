#!/usr/bin/env python3
"""Run the closed MCP-only CK3 frontend route acceptance.

This runner launches one managed, non-debug CK3 process at the main menu,
injects the exact bridge DLL, and uses the official MCP SDK to prove the
semantic route through ``coat_of_arms_designer``. Opt-in checks can collect a
detect/apply/native-Copy matrix or commit one design through the exact dynasty
Finish button, reopen it, and compare native Copy bytes. It never sends mouse
or keyboard input and never interprets pixels or OCR.
"""

from __future__ import annotations

import argparse
import asyncio
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from mcp import Client  # noqa: E402

from xar_autoplayer.bridge.coat_of_arms_source_probe_contract import (  # noqa: E402
    encode_coat_of_arms_source_v1,
)
from xar_autoplayer.bridge.frontend_gui_route_contract import (  # noqa: E402
    frontend_lobby_default_ruler_designer_ready_v1,
)
from xar_autoplayer.bridge.mcp_server import create_server  # noqa: E402
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.environment import ensure_state_path_safe, make_spec  # noqa: E402
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
COMMIT_DYNASTY_COAT_OF_ARMS_CAPABILITY = (
    "game.command.commit-frontend-dynasty-coat-of-arms-v1"
)
PROBE_COAT_OF_ARMS_CAPABILITY = "game.command.probe-coat-of-arms-source-v1"
EXPORT_COAT_OF_ARMS_CAPABILITY = "game.command.export-coat-of-arms-source-v1"
QUERY_TOOL = "ck3_query_frontend_gui_route_v1"
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
COMMIT_DYNASTY_COAT_OF_ARMS_TOOL = (
    "ck3_commit_frontend_dynasty_coat_of_arms_v1"
)
SNAPSHOT_TOOL = "ck3_take_snapshot"
PROBE_COAT_OF_ARMS_TOOL = "ck3_probe_coat_of_arms_source_v1"
EXPORT_COAT_OF_ARMS_TOOL = "ck3_export_coat_of_arms_source_v1"
SYNTAX_MATRIX = Path(__file__).with_name("coat_of_arms_syntax_matrix_v1.json")
_PROFILE_EXCLUDES = frozenset(
    {"crashes", "dumps", "exceptions", "logs", "save games", "last_save.ck3"}
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-profile", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-pipe", required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--steam-loginusers", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=360.0)
    parser.add_argument(
        "--syntax-matrix",
        action="store_true",
        help="collect the checked-in CoA detect/apply/Copy matrix after routing",
    )
    parser.add_argument(
        "--commit-roundtrip",
        action="store_true",
        help=(
            "apply one CoA, commit with native dynasty Finish, reopen, and "
            "compare native Copy bytes"
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


async def _mcp_sequence(
    driver: NativeHeadlessGameplayDriver,
    timeout: float,
    syntax_matrix: dict[str, object] | None = None,
    commit_roundtrip: bool = False,
) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    calls: list[dict[str, object]] = []
    call_summary: dict[str, object] = {
        "total": 0,
        "omitted": 0,
        "last_call": None,
    }

    def record(call: dict[str, object]) -> None:
        call_summary["total"] = int(call_summary["total"]) + 1
        call_summary["last_call"] = call
        if len(calls) < 32:
            calls.append(call)
        else:
            call_summary["omitted"] = int(call_summary["omitted"]) + 1

    def red(reason: str, **evidence: object) -> dict[str, object]:
        return {
            "mcp_sdk": "official-python-client",
            "calls": calls,
            "call_summary": call_summary,
            "checks": {},
            "error": reason,
            "ok": False,
            **evidence,
        }

    async with Client(create_server(driver)) as client:
        listed = await client.list_tools()
        tools = {tool.name: tool for tool in listed.tools}
        route_required = {
            QUERY_TOOL,
            INSPECT_TOOL,
            ACTIVATE_NEW_GAME_TOOL,
            ACTIVATE_PICK_ANY_TOOL,
            ACTIVATE_PREPARE_CUSTOM_RULER_TOOL,
            ACTIVATE_RULER_DESIGNER_TOOL,
            ACTIVATE_COAT_OF_ARMS_DESIGNER_TOOL,
            COMMIT_DYNASTY_COAT_OF_ARMS_TOOL,
        }
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
        required = route_required | matrix_required | commit_required
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

        required_capabilities = {
            QUERY_CAPABILITY,
            INSPECT_CAPABILITY,
            ACTIVATE_NEW_GAME_CAPABILITY,
            ACTIVATE_PICK_ANY_CAPABILITY,
            ACTIVATE_SELECT_RANDOM_PLAYABLE_CAPABILITY,
            ACTIVATE_RULER_DESIGNER_CAPABILITY,
            ACTIVATE_COAT_OF_ARMS_DESIGNER_CAPABILITY,
            COMMIT_DYNASTY_COAT_OF_ARMS_CAPABILITY,
        }
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
            "syntax_matrix": matrix_result,
            "commit_roundtrip": commit_result,
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


def _run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    started = time.monotonic()
    repository = Path(__file__).resolve().parents[3]
    syntax_matrix = (
        _load_syntax_matrix() if getattr(args, "syntax_matrix", False) else None
    )
    commit_roundtrip = bool(getattr(args, "commit_roundtrip", False))
    state_dir = args.state_dir.resolve()
    output = args.output.resolve()
    if state_dir.exists():
        raise RuntimeError(f"state directory already exists: {state_dir}")
    if output.exists() or output.with_name(output.name + ".tmp").exists():
        raise RuntimeError(f"artifact output already exists: {output}")
    ensure_state_path_safe(state_dir)
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
            "mcp_only": True,
            "uses_ocr": False,
            "uses_keyboard": False,
            "uses_mouse": False,
        },
        "syntax_matrix_requested": syntax_matrix is not None,
        "syntax_matrix_plan": syntax_matrix,
        "commit_roundtrip_requested": commit_roundtrip,
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
        report["steam"] = _steam_offline(args.steam_loginusers)
        report["profile"] = _copy_profile(
            args.source_profile, state_dir / "profile"
        )
        spec = make_spec(state_dir, args.game_dir.resolve())
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
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        handle = launch(
            spec,
            native_bridge=config,
            continue_last_save=False,
            verify_prepared_profile=False,
        )
        report["managed_pid"] = int(handle.process.pid)
        sequence = asyncio.run(
            _mcp_sequence(
                driver,
                float(args.timeout),
                syntax_matrix=syntax_matrix,
                commit_roundtrip=commit_roundtrip,
            )
        )
        report["sequence"] = sequence
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

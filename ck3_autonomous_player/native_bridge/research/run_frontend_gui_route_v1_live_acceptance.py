#!/usr/bin/env python3
"""Run the closed MCP-only CK3 frontend route acceptance.

This runner launches one managed, non-debug CK3 process at the main menu,
injects the exact bridge DLL, and uses the official MCP SDK to prove the
semantic route transition ``main_menu -> bookmarks -> lobby -> ruler_designer``.
It never sends mouse or keyboard input and never interprets pixels or OCR.
"""

from __future__ import annotations

import argparse
import asyncio
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

from xar_autoplayer.bridge.frontend_gui_route_contract import (  # noqa: E402
    frontend_lobby_default_ruler_designer_ready_v1,
)
from xar_autoplayer.bridge.mcp_server import create_server  # noqa: E402
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.environment import ensure_state_path_safe, make_spec  # noqa: E402
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
QUERY_TOOL = "ck3_query_frontend_gui_route_v1"
INSPECT_TOOL = "ck3_inspect_frontend_gui_tree_v1"
ACTIVATE_NEW_GAME_TOOL = "ck3_activate_frontend_new_game_v1"
ACTIVATE_PICK_ANY_TOOL = "ck3_activate_frontend_pick_any_character_v1"
ACTIVATE_PREPARE_CUSTOM_RULER_TOOL = (
    "ck3_activate_frontend_prepare_custom_ruler_v1"
)
ACTIVATE_RULER_DESIGNER_TOOL = "ck3_activate_frontend_ruler_designer_v1"
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


async def _call(client: Client, name: str) -> dict[str, object]:
    started = time.monotonic()
    try:
        result = await client.call_tool(name, {})
        return {
            "tool": name,
            "arguments": {},
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "is_error": bool(result.is_error),
            "structured_content": result.structured_content,
            "content": _content_blocks(result),
        }
    except BaseException as error:
        return {
            "tool": name,
            "arguments": {},
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "is_error": True,
            "exception": f"{type(error).__name__}: {error}",
        }


def _structured(call: dict[str, object]) -> dict[str, object]:
    value = call.get("structured_content")
    return value if isinstance(value, dict) else {}


async def _mcp_sequence(
    driver: NativeHeadlessGameplayDriver, timeout: float
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
        required = {
            QUERY_TOOL,
            INSPECT_TOOL,
            ACTIVATE_NEW_GAME_TOOL,
            ACTIVATE_PICK_ANY_TOOL,
            ACTIVATE_PREPARE_CUSTOM_RULER_TOOL,
            ACTIVATE_RULER_DESIGNER_TOOL,
        }
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
            schema.get("required", []) != []
            or schema.get("additionalProperties") is not False
            for schema in schemas.values()
        ):
            return red(
                "frontend MCP tools are not closed zero-input tools",
                tool_schemas=schemas,
            )

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
                and {
                    QUERY_CAPABILITY,
                    INSPECT_CAPABILITY,
                    ACTIVATE_NEW_GAME_CAPABILITY,
                    ACTIVATE_PICK_ANY_CAPABILITY,
                    ACTIVATE_SELECT_RANDOM_PLAYABLE_CAPABILITY,
                    ACTIVATE_RULER_DESIGNER_CAPABILITY,
                }
                <= set(advertised)
                and {
                    QUERY_CAPABILITY,
                    INSPECT_CAPABILITY,
                    ACTIVATE_NEW_GAME_CAPABILITY,
                    ACTIVATE_PICK_ANY_CAPABILITY,
                    ACTIVATE_SELECT_RANDOM_PLAYABLE_CAPABILITY,
                    ACTIVATE_RULER_DESIGNER_CAPABILITY,
                }
                <= set(hello_caps)
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
        after_ruler_designer = (
            ruler_designer.get("after")
            if isinstance(ruler_designer.get("after"), dict)
            else {}
        )
        checks = {
            "closed_zero_input_tools": set(schemas) == required,
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
        }
        return {
            "mcp_sdk": "official-python-client",
            "tool_schemas": schemas,
            "capabilities": _structured(capability_call or {}),
            "before": before,
            "new_game": new_game,
            "prepare_custom_ruler": prepare,
            "ruler_designer": ruler_designer,
            "tree_inspection_after_ruler_designer": inspection,
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
    }
    handle = None
    driver: NativeHeadlessGameplayDriver | None = None
    primary_error: str | None = None
    cleanup: dict[str, object] | None = None
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
        sequence = asyncio.run(_mcp_sequence(driver, float(args.timeout)))
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

#!/usr/bin/env python3
"""Run the closed MCP-only CK3 frontend route acceptance.

This runner launches one managed, non-debug CK3 process at the main menu,
injects the exact bridge DLL, and uses the official MCP SDK to prove the
semantic route transition ``main_menu -> bookmarks``.  It never sends mouse
or keyboard input and never interprets pixels or OCR.
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
ACTIVATE_CAPABILITY = "game.command.activate-frontend-new-game-v1"
QUERY_TOOL = "ck3_query_frontend_gui_route_v1"
ACTIVATE_TOOL = "ck3_activate_frontend_new_game_v1"
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
    async with Client(create_server(driver)) as client:
        listed = await client.list_tools()
        tools = {tool.name: tool for tool in listed.tools}
        required = {QUERY_TOOL, ACTIVATE_TOOL}
        schemas = {
            name: tools[name].input_schema
            for name in sorted(required)
            if name in tools
        }
        if not required <= set(tools):
            raise RuntimeError("frontend MCP tools are not registered")
        if any(
            schema.get("required", []) != []
            or schema.get("additionalProperties") is not False
            for schema in schemas.values()
        ):
            raise RuntimeError("frontend MCP tools are not closed zero-input tools")

        capability_call: dict[str, object] | None = None
        while time.monotonic() < deadline:
            capability_call = await _call(client, "ck3_get_capabilities")
            calls.append(capability_call)
            capability = _structured(capability_call)
            advertised = capability.get("bridge_capabilities")
            diagnostics = capability.get("diagnostics")
            hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
            hello_caps = hello.get("capabilities") if isinstance(hello, dict) else None
            if (
                capability_call.get("is_error") is False
                and isinstance(advertised, list)
                and isinstance(hello_caps, list)
                and {QUERY_CAPABILITY, ACTIVATE_CAPABILITY} <= set(advertised)
                and {QUERY_CAPABILITY, ACTIVATE_CAPABILITY} <= set(hello_caps)
            ):
                break
            await asyncio.sleep(0.25)
        else:
            raise RuntimeError("native bridge did not advertise frontend MCP capabilities")

        before_call: dict[str, object] | None = None
        before: dict[str, object] = {}
        while time.monotonic() < deadline:
            before_call = await _call(client, QUERY_TOOL)
            calls.append(before_call)
            before = _structured(before_call)
            if before_call.get("is_error") is False and before.get("route") == "main_menu":
                break
            await asyncio.sleep(0.25)
        else:
            raise RuntimeError(f"main_menu route was not observed: {before!r}")

        action_call = await _call(client, ACTIVATE_TOOL)
        calls.append(action_call)
        action = _structured(action_call)
        after = action.get("after") if isinstance(action.get("after"), dict) else {}
        checks = {
            "closed_zero_input_tools": set(schemas) == required,
            "before_main_menu": before.get("route") == "main_menu",
            "action_not_error": action_call.get("is_error") is False,
            "action_verified": action.get("status") == "verified",
            "postcondition_verified": action.get("postcondition_verified") is True,
            "after_bookmarks": after.get("route") == "bookmarks",
            "no_ocr": action.get("uses_ocr") is False,
            "no_keyboard": action.get("uses_keyboard") is False,
            "no_mouse": action.get("uses_mouse") is False,
            "native_semantic_backend": action.get("input_backend")
            == "native_gui_semantic_activation",
        }
        return {
            "mcp_sdk": "official-python-client",
            "tool_schemas": schemas,
            "capabilities": _structured(capability_call or {}),
            "before": before,
            "action": action,
            "calls": calls,
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

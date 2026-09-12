"""MCP server entry point.

The default workflow provider is read-only. Explicit UIA and native Steam tools
have real side effects and return their own receipts; they are separate from WAL orchestration.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from .engine import WorkshopService
from .providers import (
    FakeWorkshopProvider,
    PdxLauncherReadOnlyProvider,
    SteamworksReadOnlyProvider,
)
from .wal import OperationStore


def default_state_directory() -> Path:
    configured = os.environ.get("CK3_WORKSHOP_MCP_STATE_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "XenoAmess" / "ck3-workshop-mcp" / "operations"
    return Path.cwd() / ".ck3-workshop-mcp-state" / "operations"


def create_service(state_directory: Path, provider_name: str) -> WorkshopService:
    providers = {
        "pdx-readonly": PdxLauncherReadOnlyProvider,
        "steamworks-readonly": SteamworksReadOnlyProvider,
        "pdx-cdp": PdxLauncherReadOnlyProvider,
        "pdx-uia": PdxLauncherReadOnlyProvider,
        "steam-native": SteamworksReadOnlyProvider,
        "fake": FakeWorkshopProvider,
    }
    return WorkshopService(OperationStore(state_directory), providers[provider_name]())


def create_server(
    service: WorkshopService,
    *,
    cdp_url: str | None = None,
    enable_uia: bool = False,
    enable_native: bool = False,
):
    try:
        from mcp.server import MCPServer
        from mcp.types import ToolAnnotations
    except ImportError as error:
        raise RuntimeError("MCP mode requires: pip install 'mcp==2.0.0'") from error

    server = MCPServer(
        name="CK3 Workshop Publication",
        version="0.1.0",
        instructions=(
            "Read workshop://capabilities for the WAL workflow. Explicit workshop_ui_* and "
            "workshop_native_* tools operate outside that workflow and can have real external "
            "effects. Native publication saves a durable receipt; never retry uncertain creation "
            "with a fresh receipt. Steam online/offline restoration remains the caller's duty."
        ),
    )
    read_only = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
    local_write = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    )
    external_reversible = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    )
    irreversible = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    )

    @server.tool(annotations=read_only)
    def workshop_capabilities() -> dict[str, Any]:
        """Return provider support and hard workflow boundaries."""
        result = service.capabilities()
        result["direct_tools"] = {"uia": enable_uia, "native_steam": enable_native, "outside_wal_workflow": True}
        return result

    @server.tool(annotations=local_write)
    def workshop_plan_create(plan: dict[str, Any]) -> dict[str, Any]:
        """Persist one immutable, byte-hash-bound create or update plan."""

        return service.create_plan(plan)

    @server.tool(annotations=external_reversible)
    def workshop_begin_online_window(operation_id: str) -> dict[str, Any]:
        """Open an online window only after proving the account is not in game."""

        return service.begin_online_window(operation_id)

    @server.tool(annotations=external_reversible)
    def workshop_preflight(operation_id: str) -> dict[str, Any]:
        """Validate descriptors, hashes, ownership, account state, EULA and capabilities."""

        return service.preflight(operation_id)

    @server.tool(annotations=local_write)
    def workshop_issue_submit_token(
        operation_id: str,
        expected_plan_sha256: str,
        ttl_seconds: int = 300,
    ) -> dict[str, Any]:
        """Issue one short-lived token for the exact durable GREEN plan."""

        return service.issue_submit_token(
            operation_id, expected_plan_sha256, ttl_seconds=ttl_seconds
        )

    @server.tool(annotations=irreversible)
    def workshop_submit(
        operation_id: str,
        expected_plan_sha256: str,
        submit_token: str,
    ) -> dict[str, Any]:
        """Perform the sole irreversible create/update call; never automatically retry."""

        return service.submit(operation_id, expected_plan_sha256, submit_token)

    @server.tool(annotations=read_only)
    def workshop_operation_get(operation_id: str) -> dict[str, Any]:
        """Read the current operation view reconstructed from its WAL."""

        return service.operation(operation_id)

    @server.tool(annotations=read_only)
    def workshop_operation_events(operation_id: str) -> dict[str, Any]:
        """Read immutable WAL evidence for one operation."""

        return service.operation_events(operation_id)

    @server.tool(annotations=external_reversible)
    def workshop_restore_offline(operation_id: str) -> dict[str, Any]:
        """Run and verify the Steam-offline compensation explicitly."""

        return service.restore_offline(operation_id)

    @server.tool(annotations=external_reversible)
    def workshop_recover_offline_obligations() -> dict[str, Any]:
        """Restore offline mode for every durable, unfinished online window."""

        return service.recover_offline_obligations()

    if cdp_url is not None:

        @server.tool(annotations=read_only)
        def workshop_launcher_inspect() -> dict[str, Any]:
            """Inspect the configured PDX Launcher CDP endpoint without uploading."""

            from .launcher_cdp import inspect

            result = inspect(cdp_url)
            if not isinstance(result, dict):
                raise RuntimeError("launcher_cdp.inspect must return a JSON object")
            return result

        @server.tool(annotations=irreversible)
        def workshop_launcher_upload(plan: dict[str, Any]) -> dict[str, Any]:
            """Delegate one real Launcher upload to the configured CDP adapter."""

            from .launcher_cdp import upload

            result = upload(cdp_url, plan)
            if not isinstance(result, dict):
                raise RuntimeError("launcher_cdp.upload must return a JSON object")
            return result

    if enable_uia:

        @server.tool(annotations=read_only)
        def workshop_ui_inspect(hwnd: int = 0) -> dict[str, Any]:
            """List top-level windows or all semantic controls under one HWND."""

            from .launcher_uia import inspect

            return inspect(hwnd)

        @server.tool(annotations=irreversible)
        def workshop_ui_invoke(
            hwnd: int,
            name: str,
            control_type: str,
            automation_id: str = "",
        ) -> dict[str, Any]:
            """Invoke one UIA control by accessible identity without coordinates."""

            from .launcher_uia import invoke

            return invoke(hwnd, name, control_type, automation_id)

        @server.tool(annotations=external_reversible)
        def workshop_ui_set_text(
            hwnd: int,
            automation_id: str,
            text: str,
        ) -> dict[str, Any]:
            """Set exact Edit text through the UIA bridge and a temporary UTF-8 file."""

            from .launcher_uia import set_text

            return set_text(hwnd, automation_id, text)

        @server.tool(annotations=external_reversible)
        def workshop_ui_keys(hwnd: int, automation_id: str, sequence: str) -> dict[str, Any]:
            """Send navigation keys to one focused control after English layout verification."""
            from .launcher_uia import keys
            return keys(hwnd, automation_id, sequence)

    if enable_native:
        @server.tool(annotations=read_only)
        def workshop_native_symbols(dll_path: str) -> dict[str, Any]:
            """Read the local Steam DLL export table without loading or initializing it."""
            from .steam_native import symbols
            return symbols(dll_path)

        @server.tool(annotations=external_reversible)
        def workshop_native_probe(dll_path: str, app_id: int = 1158310) -> dict[str, Any]:
            """Initialize the existing Steam session and return user/app identity; no upload."""
            from .steam_native import probe
            return probe(dll_path, app_id)

        @server.tool(annotations=irreversible)
        def workshop_native_publish(dll_path: str, plan_file: str, receipt_file: str) -> dict[str, Any]:
            """Create/update one authorized Steam Workshop item using a durable native receipt."""
            from .steam_native import publish
            return publish(dll_path, plan_file, receipt_file)

    @server.resource("workshop://capabilities")
    def capabilities_resource() -> dict[str, Any]:
        return workshop_capabilities()

    @server.resource("workshop://operations/{operation_id}")
    def operation_resource(operation_id: str) -> dict[str, Any]:
        return service.operation(operation_id)

    @server.resource("workshop://operations/{operation_id}/events")
    def operation_events_resource(operation_id: str) -> dict[str, Any]:
        return service.operation_events(operation_id)

    return server


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="ck3-workshop-mcp")
    result.add_argument("--state-dir", type=Path, default=default_state_directory())
    result.add_argument(
        "--provider",
        choices=("pdx-readonly", "pdx-cdp", "pdx-uia", "steamworks-readonly", "steam-native", "fake"),
        default="pdx-readonly",
        help="select inert inspectors, explicit Launcher CDP/UIA tools, or the fake workflow provider",
    )
    result.add_argument(
        "--transport", choices=("stdio", "streamable-http"), default="stdio"
    )
    result.add_argument(
        "--cdp-url",
        help="PDX Launcher Chrome DevTools HTTP endpoint, e.g. http://127.0.0.1:9222",
    )
    result.add_argument("--host", default="127.0.0.1")
    result.add_argument("--port", type=int, default=8765)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    argument_parser = parser()
    args = argument_parser.parse_args(argv)
    if args.provider == "pdx-cdp" and not args.cdp_url:
        argument_parser.error("--provider pdx-cdp requires --cdp-url")
    if args.provider != "pdx-cdp" and args.cdp_url:
        argument_parser.error("--cdp-url is only valid with --provider pdx-cdp")
    service = create_service(args.state_dir, args.provider)
    server = create_server(
        service,
        cdp_url=args.cdp_url,
        enable_uia=args.provider == "pdx-uia",
        enable_native=args.provider == "steam-native",
    )
    can_restore = service.provider.capabilities().online_control
    if can_restore:
        service.recover_offline_obligations()
    try:
        if args.transport == "stdio":
            server.run(transport="stdio")
        else:
            server.run(
                transport="streamable-http",
                host=args.host,
                port=args.port,
                stateless_http=False,
                json_response=True,
            )
    finally:
        if can_restore:
            service.recover_offline_obligations()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

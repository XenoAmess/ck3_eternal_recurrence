"""Official MCP v2 server facade for replaceable CK3 gameplay drivers."""

from __future__ import annotations

import argparse
import importlib
import os
from pathlib import Path
from .driver import (
    DevelopmentReportDriver,
    GameplayBridgeDriver,
    HybridGameplayDriver,
)
from .mod_driver import load_data_mod_driver
from .native_driver import (
    ConfiguredHybridFallbackDriver,
    MinimizedRejectingVisualDriver,
    NativeHeadlessGameplayDriver,
    selected_pipe_name,
)
from .session_driver import DevelopmentSessionDriver
from .service import GameplayBridgeService


def _default_state_dir() -> Path:
    configured = os.environ.get("XAR_AUTOPLAYER_STATE_DIR")
    if configured:
        return Path(configured)
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise RuntimeError("LOCALAPPDATA or XAR_AUTOPLAYER_STATE_DIR is required")
    return Path(local) / "XarAutoplayer"


def load_driver(
    factory: str | None,
    *,
    userdir: str | os.PathLike[str] | None = None,
    state_dir: str | os.PathLike[str] | None = None,
    pipe_name: str | None = None,
) -> GameplayBridgeDriver:
    """Load a daemon driver without coupling MCP to a concrete game bridge."""
    def selected_state_dir() -> Path:
        return Path(state_dir) if state_dir else _default_state_dir()

    def selected_save_dir() -> Path:
        return selected_state_dir() / "profile" / "save games"

    if not factory or factory == "vision-report":
        return DevelopmentReportDriver(selected_state_dir())
    if factory == "vision-session":
        return DevelopmentSessionDriver(selected_state_dir())
    if factory == "mod":
        return load_data_mod_driver(userdir)
    if factory == "hybrid":
        return HybridGameplayDriver(
            load_data_mod_driver(userdir),
            DevelopmentSessionDriver(selected_state_dir()),
        )
    if factory == "native-headless":
        return NativeHeadlessGameplayDriver(
            selected_pipe_name(pipe_name), save_dir=selected_save_dir()
        )
    if factory == "hybrid-fallback":
        return ConfiguredHybridFallbackDriver(
            NativeHeadlessGameplayDriver(
                selected_pipe_name(pipe_name), save_dir=selected_save_dir()
            ),
            load_data_mod_driver(userdir),
            MinimizedRejectingVisualDriver(
                DevelopmentSessionDriver(selected_state_dir())
            ),
        )
    module_name, separator, attribute = factory.partition(":")
    if not separator or not module_name or not attribute:
        raise ValueError(
            "driver factory must be vision-report, vision-session, mod, "
            "hybrid, native-headless, hybrid-fallback, or module:callable"
        )
    candidate = getattr(importlib.import_module(module_name), attribute)
    if not callable(candidate):
        raise TypeError("driver factory is not callable")
    driver = candidate()
    if not isinstance(driver, GameplayBridgeDriver):
        raise TypeError("driver factory did not return a GameplayBridgeDriver")
    return driver


def create_server(driver: GameplayBridgeDriver):
    """Build the MCP server lazily so baseline vision installs need no SDK."""
    try:
        from mcp.server import MCPServer
    except ImportError as error:
        raise RuntimeError(
            "MCP mode requires the optional dependency: pip install 'mcp==2.0.0'"
        ) from error

    service = GameplayBridgeService(driver)
    server = MCPServer(
        name="Xar CK3 Gameplay Bridge",
        version="0.1.0",
        instructions=(
            "Control the current one-life CK3 episode through semantic steps. "
            "Use ck3_plan_turn unless a specific gameplay step is requested."
        ),
    )

    @server.tool()
    def ck3_get_capabilities() -> dict[str, object]:
        """List the current bridge backend and gameplay steps it implements."""
        return service.capabilities()

    @server.tool()
    def ck3_get_bridge_diagnostics() -> dict[str, object]:
        """Return live transport diagnostics without claiming CK3 game state."""
        diagnostics = getattr(driver, "diagnostics", None)
        if callable(diagnostics):
            return diagnostics()
        capabilities = service.capabilities()
        nested = capabilities.get("diagnostics")
        return nested if isinstance(nested, dict) else {
            "backend_id": capabilities.get("backend_id"),
            "connected": capabilities.get("connected"),
        }

    @server.tool()
    def ck3_take_snapshot() -> dict[str, object]:
        """Return the latest backend-neutral CK3 session snapshot."""
        return service.snapshot()

    @server.tool()
    def ck3_plan_turn() -> dict[str, object]:
        """Choose the next one-life gameplay step from the shared planner."""
        return service.plan_turn()

    @server.tool()
    def ck3_execute_step(
        step: str, expected_revision: int | None = None
    ) -> dict[str, object]:
        """Execute one semantic gameplay step through the selected backend."""
        return service.execute_step(step, expected_revision=expected_revision)

    @server.tool()
    def ck3_save_checkpoint(
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Create and materialize the fixed isolated CK3 checkpoint save."""
        return service.save_checkpoint(expected_revision=expected_revision)

    @server.tool()
    def ck3_select_event_option(
        option_number: int,
        event_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Select a 1-based option on the current CK3 event."""
        return service.select_event_option(
            option_number,
            event_instance_id=event_instance_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_resolve_active_event(
        event_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Choose and select the best enabled option on the current event."""
        return service.resolve_active_event(
            event_instance_id=event_instance_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_wait_for_change(
        after_revision: int, timeout_seconds: float = 10.0
    ) -> dict[str, object]:
        """Wait until CK3 publishes a newer semantic snapshot or timeout."""
        return service.wait_for_change(
            after_revision, timeout_seconds=timeout_seconds
        )

    @server.resource("ck3://capabilities")
    def ck3_capabilities_resource() -> dict[str, object]:
        return service.capabilities()

    @server.resource("ck3://state/current")
    def ck3_current_state_resource() -> dict[str, object]:
        return service.snapshot()

    return server


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="xar-ck3-mcp")
    result.add_argument(
        "--driver",
        default=os.environ.get("XAR_CK3_BRIDGE_DRIVER", "vision-report"),
        help=(
            "vision-report, vision-session, mod, hybrid, native-headless, "
            "hybrid-fallback, or a module:factory returning GameplayBridgeDriver"
        ),
    )
    result.add_argument(
        "--state-dir",
        default=os.environ.get("XAR_AUTOPLAYER_STATE_DIR"),
        help=(
            "XarAutoplayer state root; native checkpoints materialize under "
            "<state-dir>/profile/save games"
        ),
    )
    result.add_argument(
        "--userdir",
        default=os.environ.get("XAR_CK3_USERDIR"),
        help="active CK3 user directory used by --driver mod",
    )
    result.add_argument(
        "--pipe-name",
        default=os.environ.get("XAR_CK3_BRIDGE_PIPE"),
        help=(
            r"native bridge pipe (default: \\.\pipe\xar_ck3_bridge_mcp); "
            "also accepted through XAR_CK3_BRIDGE_PIPE"
        ),
    )
    result.add_argument(
        "--transport", choices=("stdio", "streamable-http"), default="stdio"
    )
    result.add_argument("--host", default="127.0.0.1")
    result.add_argument("--port", type=int, default=8765)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    driver = load_driver(
        args.driver,
        userdir=args.userdir,
        state_dir=args.state_dir,
        pipe_name=args.pipe_name,
    )
    server = create_server(driver)
    try:
        if args.transport == "stdio":
            server.run(transport="stdio")
        else:
            server.run(
                transport="streamable-http",
                host=args.host,
                port=args.port,
                stateless_http=True,
                json_response=True,
            )
    finally:
        close = getattr(driver, "close", None)
        if callable(close):
            close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

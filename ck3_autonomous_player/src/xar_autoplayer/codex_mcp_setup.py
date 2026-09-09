"""Per-user installer, Codex registration, and no-launch doctor for CK3 MCP.

This module deliberately owns no CK3 provider code.  It registers the existing
``ck3_autonomous_player/mcp_server.py`` stdio entry point and keeps every
Windows account on a distinct state directory, CK3 profile, and named pipe.
Nothing in this module starts or attaches to CK3.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Callable, Final, Sequence

from .vanilla_events import (
    DEFAULT_VANILLA_EVENT_ANALYSIS,
    DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
)
from .vanilla_events.registry import (
    VANILLA_EVENT_KNOWLEDGE_SCHEMA,
    VANILLA_EVENT_KNOWLEDGE_SCHEMA_VERSION,
)


MCP_SDK_VERSION: Final = "2.0.0"
LAYOUT_SCHEMA_VERSION: Final = 1
LAYOUT_MARKER_NAME: Final = "portable-mcp-layout-v1.json"
SET_PLAYED_CHARACTER_CAPABILITY: Final = (
    "game.command.set-played-character-v1-N"
)
SET_PLAYED_CHARACTER_TOOL: Final = "ck3_set_played_character_v1"
VANILLA_EVENT_KNOWLEDGE_TOOL: Final = (
    "ck3_query_vanilla_event_knowledge_v1"
)
VANILLA_EVENT_KNOWLEDGE_PROBE_KEY: Final = "health.1010"
EXACT_CK3_VERSION: Final = "1.19.0.6"
EXACT_CK3_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACKAGE_ROOT.parent
REPOSITORY_MCP_SERVER = PACKAGE_ROOT / "mcp_server.py"
REPOSITORY_AGENT = PACKAGE_ROOT / "agent.py"
SET_PLAYED_CHARACTER_CONTRACT = (
    PACKAGE_ROOT
    / "src"
    / "xar_autoplayer"
    / "bridge"
    / "set_played_character_contract.py"
)


class PortableMcpSetupError(RuntimeError):
    """A deterministic setup or doctor failure."""


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


CommandRunner = Callable[[Sequence[str]], CommandResult]


@dataclass(frozen=True)
class PortableMcpLayout:
    account: str
    account_slug: str
    server_name: str
    pipe_name: str
    base_dir: Path
    venv_dir: Path
    state_dir: Path
    userdir: Path
    codex_command: Path | None
    bootstrap_python: Path
    game_dir: Path
    bridge_dll: Path | None = None
    bridge_injector: Path | None = None

    @property
    def venv_python(self) -> Path:
        return self.venv_dir / "Scripts" / "python.exe"

    @property
    def marker_path(self) -> Path:
        return self.state_dir / LAYOUT_MARKER_NAME

    def marker_payload(self) -> dict[str, object]:
        return {
            "schema_version": LAYOUT_SCHEMA_VERSION,
            "kind": "xar_codex_mcp_portable_layout",
            "account": self.account,
            "account_slug": self.account_slug,
            "server_name": self.server_name,
            "pipe_name": self.pipe_name,
            "base_dir": str(self.base_dir),
            "venv_dir": str(self.venv_dir),
            "state_dir": str(self.state_dir),
            "userdir": str(self.userdir),
            "repository_mcp_server": str(REPOSITORY_MCP_SERVER),
            "launches_ck3": False,
        }


def safe_account_slug(value: str) -> str:
    """Return a stable component for paths, pipe names, and Codex names."""
    slug = re.sub(r"[^a-z0-9_.-]+", "-", value.strip().lower()).strip("-._")
    if not slug:
        raise PortableMcpSetupError("Windows account name has no portable characters")
    return slug


def current_windows_account() -> str:
    return os.environ.get("USERNAME") or getpass.getuser()


def _resolved(path: Path | str) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _optional_resolved(path: Path | str | None) -> Path | None:
    return None if path is None else _resolved(path)


def discover_codex_command(explicit: Path | str | None = None) -> Path | None:
    if explicit is not None:
        return _resolved(explicit)
    for name in ("codex.cmd", "codex.exe", "codex"):
        found = shutil.which(name)
        if found and Path(found).suffix.lower() != ".ps1":
            return _resolved(found)
    return None


def build_layout(
    *,
    account: str | None = None,
    local_app_data: Path | str | None = None,
    base_dir: Path | str | None = None,
    venv_dir: Path | str | None = None,
    state_dir: Path | str | None = None,
    userdir: Path | str | None = None,
    server_name: str | None = None,
    pipe_name: str | None = None,
    codex_command: Path | str | None = None,
    bootstrap_python: Path | str | None = None,
    game_dir: Path | str | None = None,
    bridge_dll: Path | str | None = None,
    bridge_injector: Path | str | None = None,
) -> PortableMcpLayout:
    selected_account = account or current_windows_account()
    slug = safe_account_slug(selected_account)
    local = local_app_data or os.environ.get("LOCALAPPDATA")
    if base_dir is None and not local:
        raise PortableMcpSetupError(
            "LOCALAPPDATA or --local-app-data is required for portable defaults"
        )
    selected_base = _resolved(
        base_dir
        or (Path(str(local)) / "XarAutoplayer" / "codex-mcp" / slug)
    )
    selected_state = _resolved(state_dir or selected_base / "state")
    selected_userdir = _resolved(userdir or selected_state / "profile")
    selected_venv = _resolved(venv_dir or selected_base / "venv")
    selected_game = _resolved(
        game_dir
        or os.environ.get("XAR_CK3_GAME_DIR")
        or (REPO_ROOT / "Crusader Kings III")
    )
    selected_bootstrap = _resolved(bootstrap_python or sys.executable)
    selected_codex = discover_codex_command(codex_command)
    layout = PortableMcpLayout(
        account=selected_account,
        account_slug=slug,
        server_name=server_name or f"xar-ck3-native-{slug}",
        pipe_name=pipe_name or rf"\\.\pipe\xar_ck3_bridge_mcp_{slug}",
        base_dir=selected_base,
        venv_dir=selected_venv,
        state_dir=selected_state,
        userdir=selected_userdir,
        codex_command=selected_codex,
        bootstrap_python=selected_bootstrap,
        game_dir=selected_game,
        bridge_dll=_optional_resolved(
            bridge_dll or os.environ.get("XAR_CK3_BRIDGE_DLL")
        ),
        bridge_injector=_optional_resolved(
            bridge_injector or os.environ.get("XAR_CK3_BRIDGE_INJECTOR")
        ),
    )
    validate_layout(layout)
    return layout


def validate_layout(layout: PortableMcpLayout) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", layout.server_name):
        raise PortableMcpSetupError(
            "server name may contain only letters, digits, dot, underscore, and dash"
        )
    if not re.fullmatch(r"\\\\\.\\pipe\\[A-Za-z0-9_.-]+", layout.pipe_name):
        raise PortableMcpSetupError(
            r"pipe name must be local and shaped like \\.\pipe\portable-name"
        )
    if layout.account_slug not in layout.server_name.lower():
        raise PortableMcpSetupError("server name must include the account slug")
    if layout.account_slug not in layout.pipe_name.lower():
        raise PortableMcpSetupError("pipe name must include the account slug")
    if layout.state_dir == layout.userdir:
        raise PortableMcpSetupError("state-dir and userdir must not be identical")
    try:
        layout.userdir.relative_to(layout.state_dir)
    except ValueError as error:
        raise PortableMcpSetupError(
            "userdir must be isolated beneath state-dir"
        ) from error
    if layout.venv_dir == layout.state_dir or layout.venv_dir == layout.userdir:
        raise PortableMcpSetupError("venv, state, and userdir must be distinct")


def mcp_server_arguments(layout: PortableMcpLayout) -> list[str]:
    return [
        str(layout.venv_python),
        str(REPOSITORY_MCP_SERVER),
        "--driver",
        "native-headless",
        "--state-dir",
        str(layout.state_dir),
        "--userdir",
        str(layout.userdir),
        "--pipe-name",
        layout.pipe_name,
        "--transport",
        "stdio",
    ]


def codex_add_command(layout: PortableMcpLayout) -> list[str]:
    if layout.codex_command is None:
        raise PortableMcpSetupError("Codex CLI was not found; pass --codex-command")
    return [
        str(layout.codex_command),
        "mcp",
        "add",
        layout.server_name,
        "--",
        *mcp_server_arguments(layout),
    ]


def native_session_command(layout: PortableMcpLayout) -> list[str] | None:
    if layout.bridge_dll is None or layout.bridge_injector is None:
        return None
    return [
        str(layout.venv_python),
        str(REPOSITORY_AGENT),
        "--state-dir",
        str(layout.state_dir),
        "--game-dir",
        str(layout.game_dir),
        "--bridge-mode",
        "native-headless",
        "--bridge-pipe",
        layout.pipe_name,
        "--bridge-dll",
        str(layout.bridge_dll),
        "--bridge-injector",
        str(layout.bridge_injector),
        "native-session",
        "--timeout",
        "21600",
    ]


def fresh_native_build_command(layout: PortableMcpLayout) -> list[str]:
    return [
        "powershell.exe",
        "-NoProfile",
        "-File",
        str(PACKAGE_ROOT / "native_bridge" / "tools" / "build_fresh.ps1"),
        "-BuildDir",
        str(layout.base_dir / "native-bridge-build"),
        "-Ck3ExecutablePath",
        str(layout.game_dir / "binaries" / "ck3.exe"),
    ]


def current_vanilla_event_knowledge_manifest() -> dict[str, object]:
    """Describe the current checkout's offline dataset, not a frozen ABI size."""

    return {
        "tool": VANILLA_EVENT_KNOWLEDGE_TOOL,
        "schema": VANILLA_EVENT_KNOWLEDGE_SCHEMA,
        "schema_version": VANILLA_EVENT_KNOWLEDGE_SCHEMA_VERSION,
        "exact_ck3_build": EXACT_CK3_VERSION,
        "probe_event_definition_key": VANILLA_EVENT_KNOWLEDGE_PROBE_KEY,
        "current_contract_count": len(
            DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS
        ),
        "current_analysis_count": len(DEFAULT_VANILLA_EVENT_ANALYSIS),
        "count_semantics": "current-revision-data-fact-not-abi",
        "requires_ck3": False,
    }


def offline_vanilla_event_knowledge_smoke_command(
    layout: PortableMcpLayout,
) -> list[str]:
    """Build one installed-runtime MCP list/call probe that never touches CK3."""

    source_root = str(PACKAGE_ROOT / "src")
    script = "\n".join((
        "import asyncio",
        "import json",
        "import sys",
        f"sys.path.insert(0, {source_root!r})",
        "from mcp import Client",
        "from xar_autoplayer.bridge.mcp_server import create_server",
        "from xar_autoplayer.vanilla_events import (",
        "    DEFAULT_VANILLA_EVENT_ANALYSIS,",
        "    DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,",
        ")",
        "",
        "class _OfflineDriver:",
        "    @staticmethod",
        "    def _unexpected(*args, **kwargs):",
        "        raise RuntimeError('offline knowledge smoke touched CK3')",
        "    capabilities = _unexpected",
        "    take_snapshot = _unexpected",
        "    execute_step = _unexpected",
        "    wait_for_change = _unexpected",
        "",
        "async def _main():",
        "    async with Client(create_server(_OfflineDriver())) as client:",
        "        listed = await client.list_tools()",
        "        names = {tool.name for tool in listed.tools}",
        f"        tool_name = {VANILLA_EVENT_KNOWLEDGE_TOOL!r}",
        f"        event_key = {VANILLA_EVENT_KNOWLEDGE_PROBE_KEY!r}",
        "        result = await client.call_tool(",
        "            tool_name,",
        "            {'event_definition_key': event_key},",
        "        )",
        "        payload = result.structured_content or {}",
        "        report = {",
        "            'tool_listed': tool_name in names,",
        "            'contract_count': len(",
        "                DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS",
        "            ),",
        "            'analysis_count': len(DEFAULT_VANILLA_EVENT_ANALYSIS),",
        "            'analysis_keyset_matches_contracts': (",
        "                set(DEFAULT_VANILLA_EVENT_ANALYSIS)",
        "                == set(DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS)",
        "            ),",
        "            'query_is_error': result.is_error,",
        "            'query_event_definition_key': payload.get(",
        "                'event_definition_key'",
        "            ),",
        "            'query_status': payload.get('status'),",
        "            'query_contract_non_null': payload.get('contract') is not None,",
        "            'query_analysis_non_null': payload.get('analysis') is not None,",
        "            'requires_ck3': False,",
        "        }",
        "        print(json.dumps(report, sort_keys=True))",
        "",
        "asyncio.run(_main())",
    ))
    return [str(layout.venv_python), "-c", script]


def render_plan(layout: PortableMcpLayout) -> dict[str, object]:
    return {
        "schema_version": LAYOUT_SCHEMA_VERSION,
        "kind": "xar_codex_mcp_portable_plan",
        "account": layout.account,
        "account_slug": layout.account_slug,
        "server_name": layout.server_name,
        "pipe_name": layout.pipe_name,
        "base_dir": str(layout.base_dir),
        "venv_dir": str(layout.venv_dir),
        "state_dir": str(layout.state_dir),
        "userdir": str(layout.userdir),
        "codex_command": (
            str(layout.codex_command) if layout.codex_command is not None else None
        ),
        "bootstrap_python": str(layout.bootstrap_python),
        "game_dir": str(layout.game_dir),
        "bridge_dll": (
            str(layout.bridge_dll) if layout.bridge_dll is not None else None
        ),
        "bridge_injector": (
            str(layout.bridge_injector)
            if layout.bridge_injector is not None
            else None
        ),
        "mcp_server": str(REPOSITORY_MCP_SERVER),
        "install_command": [
            str(layout.venv_python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            f"mcp=={MCP_SDK_VERSION}",
            "pywin32==312",
        ],
        "codex_add_command": (
            codex_add_command(layout) if layout.codex_command is not None else None
        ),
        "fresh_native_build_command": fresh_native_build_command(layout),
        "native_session_command": native_session_command(layout),
        "generic_rebind": {
            "tool": SET_PLAYED_CHARACTER_TOOL,
            "capability": SET_PLAYED_CHARACTER_CAPABILITY,
            "provider_reused": True,
            "exact_ck3_version": EXACT_CK3_VERSION,
            "exact_ck3_sha256": EXACT_CK3_SHA256,
        },
        "offline_vanilla_event_knowledge": (
            current_vanilla_event_knowledge_manifest()
        ),
        "ownership": {
            "run_setup_as_account": layout.account,
            "per_account_codex_config": True,
            "shared_pipe_or_state_forbidden": True,
        },
        "launches_ck3": False,
    }


def _run_command(command: Sequence[str]) -> CommandResult:
    completed = subprocess.run(
        list(command),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    return CommandResult(
        completed.returncode,
        completed.stdout,
        completed.stderr,
    )


def _require_current_account(layout: PortableMcpLayout) -> None:
    current = current_windows_account()
    if current.casefold() != layout.account.casefold():
        raise PortableMcpSetupError(
            f"apply commands must run as {layout.account!r}; current account is {current!r}"
        )


def _write_layout_marker(layout: PortableMcpLayout) -> None:
    layout.state_dir.mkdir(parents=True, exist_ok=True)
    layout.userdir.mkdir(parents=True, exist_ok=True)
    marker = layout.marker_path
    temporary = marker.with_suffix(marker.suffix + f".{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(layout.marker_payload(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, marker)


def install_runtime(
    layout: PortableMcpLayout,
    *,
    runner: CommandRunner = _run_command,
) -> dict[str, object]:
    """Create/update the selected account's venv; never build or launch CK3."""
    _require_current_account(layout)
    if os.name != "nt":
        raise PortableMcpSetupError("the native CK3 MCP runtime requires Windows")
    if not layout.bootstrap_python.is_file():
        raise PortableMcpSetupError(
            f"bootstrap Python does not exist: {layout.bootstrap_python}"
        )
    created = False
    if not layout.venv_python.is_file():
        if layout.venv_dir.exists() and any(layout.venv_dir.iterdir()):
            raise PortableMcpSetupError(
                f"venv directory exists but has no Python: {layout.venv_dir}"
            )
        layout.venv_dir.parent.mkdir(parents=True, exist_ok=True)
        result = runner(
            [str(layout.bootstrap_python), "-m", "venv", str(layout.venv_dir)]
        )
        if result.returncode != 0:
            raise PortableMcpSetupError(
                f"venv creation failed: {result.stderr or result.stdout}"
            )
        created = True
    install = runner(render_plan(layout)["install_command"])
    if install.returncode != 0:
        raise PortableMcpSetupError(
            f"MCP runtime installation failed: {install.stderr or install.stdout}"
        )
    _write_layout_marker(layout)
    return {
        "result": "installed",
        "venv_created": created,
        "venv_python": str(layout.venv_python),
        "layout_marker": str(layout.marker_path),
        "launches_ck3": False,
    }


def _codex_get_command(layout: PortableMcpLayout) -> list[str]:
    if layout.codex_command is None:
        raise PortableMcpSetupError("Codex CLI was not found; pass --codex-command")
    return [
        str(layout.codex_command),
        "mcp",
        "get",
        layout.server_name,
        "--json",
    ]


def _stdio_config(value: object) -> tuple[str | None, list[str] | None]:
    if not isinstance(value, dict):
        return None, None
    transport = value.get("transport")
    selected = transport if isinstance(transport, dict) else value
    command = selected.get("command")
    arguments = selected.get("args")
    if not isinstance(command, str):
        return None, None
    if not isinstance(arguments, list) or not all(
        isinstance(argument, str) for argument in arguments
    ):
        return None, None
    return command, arguments


def codex_config_matches(layout: PortableMcpLayout, value: object) -> bool:
    command, arguments = _stdio_config(value)
    expected = mcp_server_arguments(layout)
    if command is None or arguments is None:
        return False
    if os.path.normcase(os.path.normpath(command)) != os.path.normcase(
        os.path.normpath(expected[0])
    ):
        return False
    return arguments == expected[1:]


def register_codex_mcp(
    layout: PortableMcpLayout,
    *,
    replace: bool = False,
    runner: CommandRunner = _run_command,
) -> dict[str, object]:
    """Register the stdio command in this account's Codex config."""
    _require_current_account(layout)
    if not layout.venv_python.is_file():
        raise PortableMcpSetupError(
            f"per-user MCP Python is missing; run install first: {layout.venv_python}"
        )
    if layout.codex_command is None or not layout.codex_command.is_file():
        raise PortableMcpSetupError("Codex CLI was not found; pass --codex-command")
    existing = runner(_codex_get_command(layout))
    if existing.returncode == 0:
        try:
            payload = json.loads(existing.stdout)
        except json.JSONDecodeError as error:
            raise PortableMcpSetupError(
                "Codex returned malformed JSON for the existing MCP registration"
            ) from error
        if codex_config_matches(layout, payload):
            _write_layout_marker(layout)
            return {
                "result": "already_registered",
                "server_name": layout.server_name,
                "launches_ck3": False,
            }
        if not replace:
            raise PortableMcpSetupError(
                "Codex MCP name exists with a different command; rerun with --replace"
            )
        removed = runner(
            [str(layout.codex_command), "mcp", "remove", layout.server_name]
        )
        if removed.returncode != 0:
            raise PortableMcpSetupError(
                f"could not remove stale MCP registration: {removed.stderr or removed.stdout}"
            )
    added = runner(codex_add_command(layout))
    if added.returncode != 0:
        raise PortableMcpSetupError(
            f"Codex MCP registration failed: {added.stderr or added.stdout}"
        )
    confirmed = runner(_codex_get_command(layout))
    if confirmed.returncode != 0:
        raise PortableMcpSetupError(
            "Codex accepted the registration but could not read it back"
        )
    try:
        confirmed_payload = json.loads(confirmed.stdout)
    except json.JSONDecodeError as error:
        raise PortableMcpSetupError(
            "Codex registration readback was not valid JSON"
        ) from error
    if not codex_config_matches(layout, confirmed_payload):
        raise PortableMcpSetupError(
            "Codex registration readback did not match the requested stdio command"
        )
    _write_layout_marker(layout)
    return {
        "result": "registered",
        "server_name": layout.server_name,
        "layout_marker": str(layout.marker_path),
        "launches_ck3": False,
    }


def _check_marker(layout: PortableMcpLayout) -> tuple[bool, str]:
    if not layout.marker_path.is_file():
        return False, "layout marker is missing"
    try:
        value = json.loads(layout.marker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return False, f"layout marker is unreadable: {error}"
    if value != layout.marker_payload():
        return False, "layout marker belongs to another account or configuration"
    return True, "exact per-account layout marker"


def _check_rebind_source() -> tuple[bool, str]:
    try:
        mcp_text = REPOSITORY_MCP_SERVER.read_text(encoding="utf-8")
        public_text = (
            PACKAGE_ROOT
            / "src"
            / "xar_autoplayer"
            / "bridge"
            / "mcp_server.py"
        ).read_text(encoding="utf-8")
        contract_text = SET_PLAYED_CHARACTER_CONTRACT.read_text(encoding="utf-8")
    except OSError as error:
        return False, f"could not read repository MCP source: {error}"
    ready = (
        "xar_autoplayer.bridge.mcp_server import main" in mcp_text
        and f"def {SET_PLAYED_CHARACTER_TOOL}(" in public_text
        and SET_PLAYED_CHARACTER_CAPABILITY in contract_text
        and EXACT_CK3_VERSION in contract_text
        and EXACT_CK3_SHA256 in contract_text
    )
    return (
        ready,
        "existing typed provider is wired" if ready else "typed provider wiring drifted",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _check_python_runtime(
    layout: PortableMcpLayout,
    runner: CommandRunner,
) -> tuple[bool, str]:
    if not layout.venv_python.is_file():
        return False, "per-account venv Python is missing"
    probe = runner(
        [
            str(layout.venv_python),
            "-c",
            (
                "import importlib.metadata as m; "
                f"assert m.version('mcp') == '{MCP_SDK_VERSION}'"
            ),
        ]
    )
    if probe.returncode != 0:
        return False, "MCP SDK 2.0.0 import/version probe failed"
    help_probe = runner(
        [str(layout.venv_python), str(REPOSITORY_MCP_SERVER), "--help"]
    )
    if help_probe.returncode != 0:
        return False, "repository MCP server import/help probe failed"
    return True, "MCP SDK and repository server import are ready"


def _check_offline_vanilla_event_knowledge(
    layout: PortableMcpLayout,
    runner: CommandRunner,
) -> tuple[bool, str, dict[str, object]]:
    """List and call the read-only knowledge tool in the installed runtime."""

    expected = current_vanilla_event_knowledge_manifest()
    result = runner(offline_vanilla_event_knowledge_smoke_command(layout))
    if result.returncode != 0:
        payload: dict[str, object] = {
            "probe_error": (result.stderr or result.stdout).strip(),
            "requires_ck3": False,
        }
        return False, json.dumps(payload, sort_keys=True), payload
    try:
        output_lines = [line for line in result.stdout.splitlines() if line.strip()]
        value = json.loads(output_lines[-1])
    except (IndexError, json.JSONDecodeError) as error:
        payload = {
            "probe_error": f"malformed smoke JSON: {error}",
            "requires_ck3": False,
        }
        return False, json.dumps(payload, sort_keys=True), payload
    if not isinstance(value, dict):
        payload = {
            "probe_error": "smoke payload is not an object",
            "requires_ck3": False,
        }
        return False, json.dumps(payload, sort_keys=True), payload

    payload = dict(value)
    payload["expected_current_contract_count"] = expected[
        "current_contract_count"
    ]
    payload["expected_current_analysis_count"] = expected[
        "current_analysis_count"
    ]
    payload["count_semantics"] = expected["count_semantics"]
    passed = all((
        payload.get("tool_listed") is True,
        payload.get("contract_count") == expected["current_contract_count"],
        payload.get("analysis_count") == expected["current_analysis_count"],
        payload.get("analysis_keyset_matches_contracts") is True,
        payload.get("query_is_error") is False,
        payload.get("query_event_definition_key")
        == VANILLA_EVENT_KNOWLEDGE_PROBE_KEY,
        payload.get("query_status") == "available",
        payload.get("query_contract_non_null") is True,
        payload.get("query_analysis_non_null") is True,
        payload.get("requires_ck3") is False,
    ))
    return passed, json.dumps(payload, sort_keys=True), payload


def doctor(
    layout: PortableMcpLayout,
    *,
    require_native_assets: bool = False,
    runner: CommandRunner = _run_command,
) -> dict[str, object]:
    """Read configuration and files only; never create a pipe or launch CK3."""
    checks: dict[str, dict[str, object]] = {}

    def record(name: str, passed: bool, detail: str) -> None:
        checks[name] = {"passed": passed, "detail": detail}

    current = current_windows_account()
    record("windows", os.name == "nt", os.name)
    record(
        "current_account",
        current.casefold() == layout.account.casefold(),
        f"expected={layout.account}; current={current}",
    )
    marker_ok, marker_detail = _check_marker(layout)
    record("layout_marker", marker_ok, marker_detail)
    rebind_ok, rebind_detail = _check_rebind_source()
    record("generic_rebind_provider", rebind_ok, rebind_detail)
    python_ok, python_detail = _check_python_runtime(layout, runner)
    record("python_runtime", python_ok, python_detail)
    if python_ok:
        knowledge_ok, knowledge_detail, knowledge_payload = (
            _check_offline_vanilla_event_knowledge(layout, runner)
        )
    else:
        knowledge_ok = False
        knowledge_payload = {
            "probe_error": "python runtime prerequisite failed",
            "requires_ck3": False,
        }
        knowledge_detail = json.dumps(knowledge_payload, sort_keys=True)
    record(
        "offline_vanilla_event_knowledge",
        knowledge_ok,
        knowledge_detail,
    )
    codex_exists = (
        layout.codex_command is not None and layout.codex_command.is_file()
    )
    record(
        "codex_cli",
        codex_exists,
        str(layout.codex_command) if layout.codex_command is not None else "not found",
    )
    registered = False
    registration_detail = "Codex CLI unavailable"
    if codex_exists:
        result = runner(_codex_get_command(layout))
        if result.returncode == 0:
            try:
                registered = codex_config_matches(layout, json.loads(result.stdout))
                registration_detail = (
                    "exact stdio registration"
                    if registered
                    else "registration exists but does not match this account layout"
                )
            except json.JSONDecodeError:
                registration_detail = "Codex registration JSON is malformed"
        else:
            registration_detail = "server is not registered for this account"
    record("codex_registration", registered, registration_detail)

    game_exe = layout.game_dir / "binaries" / "ck3.exe"
    game_executable_match = False
    game_executable_detail = "missing"
    if game_exe.is_file():
        try:
            observed_sha256 = _sha256(game_exe)
            game_executable_match = observed_sha256 == EXACT_CK3_SHA256
            game_executable_detail = observed_sha256
        except OSError as error:
            game_executable_detail = f"unreadable: {error}"
    native_rows = {
        "game_executable_exact_build": game_executable_match,
        "bridge_dll": layout.bridge_dll is not None and layout.bridge_dll.is_file(),
        "bridge_injector": (
            layout.bridge_injector is not None
            and layout.bridge_injector.is_file()
        ),
    }
    native_ready = all(native_rows.values())
    record(
        "native_session_assets",
        native_ready,
        json.dumps(
            {
                **native_rows,
                "game_executable_sha256": game_executable_detail,
                "expected_game_executable_sha256": EXACT_CK3_SHA256,
            },
            sort_keys=True,
        ),
    )
    required = {
        "windows",
        "current_account",
        "layout_marker",
        "generic_rebind_provider",
        "python_runtime",
        "offline_vanilla_event_knowledge",
        "codex_cli",
        "codex_registration",
    }
    if require_native_assets:
        required.add("native_session_assets")
    failed = [
        name
        for name in sorted(required)
        if checks.get(name, {}).get("passed") is not True
    ]
    return {
        "schema_version": LAYOUT_SCHEMA_VERSION,
        "kind": "xar_codex_mcp_no_launch_doctor",
        "result": "GREEN" if not failed else "RED",
        "account": layout.account,
        "server_name": layout.server_name,
        "pipe_name": layout.pipe_name,
        "state_dir": str(layout.state_dir),
        "userdir": str(layout.userdir),
        "checks": checks,
        "failed_checks": failed,
        "registration_ready": all(
            checks[name]["passed"] is True
            for name in (
                "windows",
                "current_account",
                "generic_rebind_provider",
                "python_runtime",
                "offline_vanilla_event_knowledge",
                "codex_cli",
            )
        ),
        "registered_exact": registered,
        "native_session_assets_ready": native_ready,
        "native_assets_required": require_native_assets,
        "generic_rebind_tool": SET_PLAYED_CHARACTER_TOOL,
        "generic_rebind_capability": SET_PLAYED_CHARACTER_CAPABILITY,
        "offline_vanilla_event_knowledge": knowledge_payload,
        "launches_ck3": False,
    }


def _add_layout_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--account")
    parser.add_argument("--local-app-data", type=Path)
    parser.add_argument("--base-dir", type=Path)
    parser.add_argument("--venv-dir", type=Path)
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--userdir", type=Path)
    parser.add_argument("--server-name")
    parser.add_argument("--pipe-name")
    parser.add_argument("--codex-command", type=Path)
    parser.add_argument("--bootstrap-python", type=Path)
    parser.add_argument("--game-dir", type=Path)
    parser.add_argument("--bridge-dll", type=Path)
    parser.add_argument("--bridge-injector", type=Path)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="xar-codex-mcp-setup")
    _add_layout_arguments(result)
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("plan", help="print the per-account layout and commands")
    sub.add_parser("install", help="create/update the per-account Python runtime")
    register = sub.add_parser("register", help="register the existing stdio server")
    register.add_argument("--replace", action="store_true")
    setup = sub.add_parser("setup", help="install and register for this account")
    setup.add_argument("--replace", action="store_true")
    doctor_parser = sub.add_parser(
        "doctor", help="read-only registration/provider/runtime self-check"
    )
    doctor_parser.add_argument("--require-native-assets", action="store_true")
    return result


def _layout_from_args(args: argparse.Namespace) -> PortableMcpLayout:
    return build_layout(
        account=args.account,
        local_app_data=args.local_app_data,
        base_dir=args.base_dir,
        venv_dir=args.venv_dir,
        state_dir=args.state_dir,
        userdir=args.userdir,
        server_name=args.server_name,
        pipe_name=args.pipe_name,
        codex_command=args.codex_command,
        bootstrap_python=args.bootstrap_python,
        game_dir=args.game_dir,
        bridge_dll=args.bridge_dll,
        bridge_injector=args.bridge_injector,
    )


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        layout = _layout_from_args(args)
        if args.command == "plan":
            payload: object = render_plan(layout)
        elif args.command == "install":
            payload = install_runtime(layout)
        elif args.command == "register":
            payload = register_codex_mcp(layout, replace=args.replace)
        elif args.command == "setup":
            payload = {
                "schema_version": LAYOUT_SCHEMA_VERSION,
                "kind": "xar_codex_mcp_portable_setup",
                "install": install_runtime(layout),
                "registration": register_codex_mcp(
                    layout, replace=args.replace
                ),
                "doctor": doctor(layout),
                "launches_ck3": False,
            }
        else:
            payload = doctor(
                layout,
                require_native_assets=args.require_native_assets,
            )
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        if isinstance(payload, dict) and payload.get("result") == "RED":
            return 1
        if (
            args.command == "setup"
            and isinstance(payload, dict)
            and isinstance(payload.get("doctor"), dict)
            and payload["doctor"].get("result") == "RED"
        ):
            return 1
        return 0
    except PortableMcpSetupError as error:
        print(
            json.dumps(
                {
                    "schema_version": LAYOUT_SCHEMA_VERSION,
                    "kind": "xar_codex_mcp_portable_setup_error",
                    "result": "RED",
                    "error": str(error),
                    "launches_ck3": False,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

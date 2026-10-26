"""Type-check the maintained MCP query against its real dependency models."""
from __future__ import annotations

import ast
import os
from pathlib import Path
import sys
import tempfile

from mypy import api


def check_ingame_ui_query_types_v1() -> None:
    """Check the complete actual query, including its original decorator."""
    from xar_autoplayer.bridge import mcp_server

    source = Path(mcp_server.__file__).read_text(encoding="utf-8")
    module = ast.parse(source)
    factories = [node for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "create_server"]
    if len(factories) != 1:
        raise AssertionError("Expected one actual MCP service factory")
    queries = [node for node in factories[0].body
        if isinstance(node, ast.FunctionDef) and node.name == "ck3_query_ingame_ui_window_v1"]
    if len(queries) != 1 or not queries[0].decorator_list:
        raise AssertionError("Expected one complete decorated ingame UI query")
    imports = """from __future__ import annotations
from typing import Literal
from mcp.server import MCPServer
from xar_autoplayer.bridge.mcp_server import IngameUiRevisionV1
from xar_autoplayer.bridge.service import GameplayBridgeService

server: MCPServer
service: GameplayBridgeService
"""
    check_source = imports + ast.unparse(ast.Module(body=[queries[0]], type_ignores=[])) + "\n"
    with tempfile.TemporaryDirectory(prefix="title-query-types-") as task_dir:
        check_path = Path(task_dir) / "actual_ingame_ui_query.py"
        check_path.write_text(check_source, encoding="utf-8")
        stdout, stderr, status = api.run(["--strict", "--follow-imports=silent",
            "--follow-untyped-imports", "--no-incremental", "--cache-dir=" + os.devnull,
            "--python-executable=" + sys.executable, str(check_path)])
    if status != 0:
        raise AssertionError(stdout + stderr)

#!/usr/bin/env python3
"""Repository-local MCP entry point; package installation is not required."""

from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.bridge.mcp_server import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Repository-local portable Codex MCP setup entry point."""

from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.codex_mcp_setup import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())

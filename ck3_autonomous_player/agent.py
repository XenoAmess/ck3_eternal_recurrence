#!/usr/bin/env python3
"""Repository-local entry point; no installation is required."""

from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())


"""Explicit H3937 one-query CLI; default is read-only admission preflight."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from xar_autoplayer.h3937_single_query_once_enable import main

if __name__ == "__main__":
    raise SystemExit(main())

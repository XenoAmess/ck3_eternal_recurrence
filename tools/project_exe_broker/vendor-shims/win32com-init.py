"""Sealed broker-only COM package: no registry extensions or generated cache."""
from pathlib import Path
__path__ = [str(Path(__file__).resolve().parent)]
__gen_path__ = str(Path(__file__).resolve().parent / "gen_py")

"""Bind public case imports to the selected runtime's frozen SDK."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import os
from pathlib import Path
import sys


def _loaded_sdk_sources(package_root: Path) -> None:
    for name, module in tuple(sys.modules.items()):
        if name == "xar_autoplayer" or name.startswith("xar_autoplayer."):
            filename = getattr(module, "__file__", None)
            if not isinstance(filename, str) or not Path(filename).resolve().is_relative_to(package_root):
                raise ValueError("Public case SDK import escaped selected runtime: " + name)


@contextmanager
def case_sdk_imports(source_root: Path, environment: object) -> Iterator[Path | None]:
    """Keep lazy case imports in the same declared SDK as the host subprocess."""
    if not isinstance(environment, dict) or any(type(key) is not str for key in environment):
        raise ValueError("Selected runtime import environment must be an object")
    if "PYTHONPATH" not in environment:
        # Existing runtimes without a declared Python environment keep their
        # SDK-free case boundary; no SDK binding is asserted for them.
        yield None
        return
    value = environment["PYTHONPATH"]
    if not isinstance(value, str) or not value or any(not part for part in value.split(os.pathsep)):
        raise ValueError("Selected runtime PYTHONPATH must contain explicit paths")
    declared = tuple(Path(part).resolve() for part in value.split(os.pathsep))
    source = source_root.resolve()
    if (source / "ck3_autonomous_player/src/xar_autoplayer").is_dir():
        source = source / "ck3_autonomous_player/src"
    package = source / "xar_autoplayer"
    if not package.is_dir() or source not in declared:
        raise ValueError("Selected runtime PYTHONPATH does not bind its frozen SDK")
    _loaded_sdk_sources(package)
    prior = list(sys.path)
    try:
        sys.path.insert(0, str(source))
        yield source
    finally:
        try:
            _loaded_sdk_sources(package)
        finally:
            sys.path[:] = prior

"""Load exact b8 source increments without changing the shared repository."""
import hashlib
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys


def candidate_source(base, manifest, relative):
    row = next(row for row in manifest["files"] if row["path"] == relative)
    path = base / relative
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != row["base_sha256"]:
        raise ValueError("creation-once base source changed: " + relative)
    text = raw.decode("utf-8-sig")
    for item in row["replacements"]:
        if text.count(item["old"]) != 1:
            raise ValueError("creation-once source anchor changed: " + relative)
        text = text.replace(item["old"], item["new"], 1)
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != row["candidate_utf8_sha256"]:
        raise ValueError("creation-once candidate source changed: " + relative)
    return path, text, row


class Loader(importlib.abc.Loader):
    def __init__(self, path, text, row):
        self.path, self.text, self.row = path, text, row

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        module.__file__ = str(self.path)
        module.__candidate_hook_sha256__ = self.row["candidate_utf8_sha256"]
        exec(compile(self.text, str(self.path), "exec"), module.__dict__)


class Finder(importlib.abc.MetaPathFinder):
    def __init__(self, base, manifest):
        self.sources = {}
        for name in ("native_driver", "service", "mcp_server", "player_holy_site_creation_context_private_transport"):
            relative = "ck3_autonomous_player/src/xar_autoplayer/bridge/" + name + ".py"
            self.sources["xar_autoplayer.bridge." + name] = candidate_source(base, manifest, relative)

    def find_spec(self, fullname, path=None, target=None):
        if fullname not in self.sources:
            return None
        source, text, row = self.sources[fullname]
        return importlib.util.spec_from_loader(fullname, Loader(source, text, row), origin=str(source))


def install(base: Path, stage: Path):
    if any(name == "xar_autoplayer.bridge" or name.startswith("xar_autoplayer.bridge.") for name in sys.modules):
        raise RuntimeError("creation-once overlay needs a fresh interpreter")
    manifest = json.loads((stage / "tools/create-once-common-hooks-a01.json").read_text(encoding="utf-8"))
    sys.meta_path.insert(0, Finder(base, manifest))
    sys.path.insert(0, str(base / "ck3_autonomous_player/src"))
    import xar_autoplayer
    xar_autoplayer.__path__.insert(0, str(stage / "ck3_autonomous_player/src/xar_autoplayer"))
    bridge_base = base / "ck3_autonomous_player/src/xar_autoplayer/bridge"
    spec = importlib.util.spec_from_file_location("xar_autoplayer.bridge", bridge_base / "__init__.py",
        submodule_search_locations=[str(stage / "ck3_autonomous_player/src/xar_autoplayer/bridge"), str(bridge_base)])
    package = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = package
    xar_autoplayer.bridge = package
    spec.loader.exec_module(package)
    return manifest

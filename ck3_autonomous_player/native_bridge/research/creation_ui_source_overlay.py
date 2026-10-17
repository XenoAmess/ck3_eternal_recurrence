"""Load UI-only source changes against the frozen query-result source layer."""
from __future__ import annotations

import hashlib
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys


def query_source(base: Path, query: Path, relative: str) -> tuple[Path, str]:
    manifest_path = query / "tools/creation-context-common-hooks-a02.json"
    raw_manifest = manifest_path.read_bytes()
    if hashlib.sha256(raw_manifest).hexdigest() != "ece21c28c1543c371e82928250fed3aefde40cbb1459dbda2d5fae65c44a7190":
        raise RuntimeError("frozen query hooks changed before UI source reconstruction")
    manifest = json.loads(raw_manifest.decode("utf-8"))
    row = next((r for r in manifest["files"] if r["path"] == relative), None)
    path = base / relative
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    if row is None:
        return path, text
    if hashlib.sha256(text.encode("utf-8")).hexdigest() == row["candidate_utf8_sha256"]:
        return path, text  # The exact query result may already be integrated.
    if hashlib.sha256(raw).hexdigest() != row["base_sha256"]:
        raise RuntimeError(f"root is neither the frozen input nor exact query result: {relative}")
    for replacement in row["replacements"]:
        if text.count(replacement["old"]) != 1:
            raise RuntimeError(f"frozen query anchor changed: {relative}")
        text = text.replace(replacement["old"], replacement["new"], 1)
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != row["candidate_utf8_sha256"]:
        raise RuntimeError(f"query result could not be reconstructed exactly: {relative}")
    return path, text


def candidate_source(base: Path, query: Path, manifest: dict, relative: str):
    row = next(r for r in manifest["files"] if r["path"] == relative)
    path, text = query_source(base, query, relative)
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != row["query_result_utf8_sha256"]:
        raise RuntimeError(f"UI candidate crossed its frozen query-result base: {relative}")
    for replacement in row["replacements"]:
        if text.count(replacement["old"]) != 1:
            raise RuntimeError(f"UI candidate hook is not unique: {relative}")
        text = text.replace(replacement["old"], replacement["new"], 1)
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != row["candidate_utf8_sha256"]:
        raise RuntimeError(f"UI candidate source hash differs: {relative}")
    return path, text, row


class _Loader(importlib.abc.Loader):
    def __init__(self, path, text, row):
        self.path, self.text, self.row = path, text, row

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        module.__file__ = str(self.path)
        module.__candidate_hook_sha256__ = self.row["candidate_utf8_sha256"]
        module.__query_result_base_sha256__ = self.row["query_result_utf8_sha256"]
        exec(compile(self.text, str(self.path), "exec"), module.__dict__)


class _Finder(importlib.abc.MetaPathFinder):
    def __init__(self, base, query, manifest):
        self.sources = {}
        for name in ("native_driver", "service", "mcp_server", "ingame_ui_contract"):
            relative = f"ck3_autonomous_player/src/xar_autoplayer/bridge/{name}.py"
            self.sources[f"xar_autoplayer.bridge.{name}"] = candidate_source(base, query, manifest, relative)

    def find_spec(self, fullname, path=None, target=None):
        if fullname not in self.sources:
            return None
        source, text, row = self.sources[fullname]
        return importlib.util.spec_from_loader(fullname, _Loader(source, text, row), origin=str(source))


def install(base: Path, stage: Path, query: Path) -> dict:
    if any(name == "xar_autoplayer.bridge" or name.startswith("xar_autoplayer.bridge.") for name in sys.modules):
        raise RuntimeError("UI source overlay requires a fresh interpreter before bridge import")
    manifest = json.loads((stage / "tools/creation-ui-common-hooks-a01.json").read_text(encoding="utf-8"))
    closure = json.loads((query / "query-closure-a01.json").read_text(encoding="utf-8"))
    source = closure["new_production_source_current_fingerprint"]
    if hashlib.sha256(Path(source["path"]).read_bytes()).hexdigest() != source["sha256"]:
        raise RuntimeError("the qualified read-only query normalizer changed")
    sys.meta_path.insert(0, _Finder(base, query, manifest))
    sys.path.insert(0, str(base / "ck3_autonomous_player/src"))
    import xar_autoplayer
    xar_autoplayer.__path__[:0] = [str(stage / "ck3_autonomous_player/src/xar_autoplayer"),
                                  str(query / "ck3_autonomous_player/src/xar_autoplayer")]
    bridge_base = base / "ck3_autonomous_player/src/xar_autoplayer/bridge"
    spec = importlib.util.spec_from_file_location("xar_autoplayer.bridge", bridge_base / "__init__.py",
        submodule_search_locations=[str(stage / "ck3_autonomous_player/src/xar_autoplayer/bridge"),
                                    str(query / "ck3_autonomous_player/src/xar_autoplayer/bridge"), str(bridge_base)])
    package = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = package
    xar_autoplayer.bridge = package
    spec.loader.exec_module(package)
    return manifest

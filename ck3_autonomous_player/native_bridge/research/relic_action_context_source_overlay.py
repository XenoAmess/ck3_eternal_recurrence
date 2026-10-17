"""Load SHA-bound incremental candidate hooks before base bridge initialization."""
from __future__ import annotations

import hashlib
import importlib.abc
import importlib.util
import json
import linecache
import os
from pathlib import Path
import sys


def candidate_source(base: Path, manifest: dict, relative: str) -> tuple[Path, str, dict]:
    row = next(item for item in manifest['files'] if item['path'] == relative)
    source_path = base / relative
    raw = source_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != row['base_sha256']:
        raise RuntimeError(f'Common source changed; explicitly rebase incremental hooks: {relative}')
    text = raw.decode('utf-8-sig')
    for change in row['replacements']:
        if text.count(change['old']) != 1:
            raise RuntimeError(f'Common hook anchor differs: {relative}')
        text = text.replace(change['old'], change['new'], 1)
    if hashlib.sha256(text.encode('utf-8')).hexdigest() != row['candidate_utf8_sha256']:
        raise RuntimeError(f'Candidate source hash differs: {relative}')
    return source_path, text, row


class _CandidateLoader(importlib.abc.Loader):
    def __init__(self, path, text, row):
        self.path, self.text, self.row = path, text, row

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        module.__file__ = str(self.path)
        module.__candidate_hook_sha256__ = self.row['candidate_utf8_sha256']
        # Diagnostic tracebacks must display the candidate source actually run.
        # This changes only the process-local line cache, never the base file.
        linecache.cache[str(self.path)] = (len(self.text), None, self.text.splitlines(True), str(self.path))
        exec(compile(self.text, str(self.path), 'exec'), module.__dict__)


class _CandidateFinder(importlib.abc.MetaPathFinder):
    def __init__(self, base, manifest):
        self.sources = {}
        for name in ('native_driver', 'service', 'mcp_server'):
            relative = f'ck3_autonomous_player/src/xar_autoplayer/bridge/{name}.py'
            self.sources[f'xar_autoplayer.bridge.{name}'] = candidate_source(base, manifest, relative)

    def find_spec(self, fullname, path=None, target=None):
        if fullname not in self.sources:
            return None
        source_path, text, row = self.sources[fullname]
        return importlib.util.spec_from_loader(fullname, _CandidateLoader(source_path, text, row), origin=str(source_path))


def install(base: Path, stage: Path) -> dict:
    if any(name == 'xar_autoplayer.bridge' or name.startswith('xar_autoplayer.bridge.') for name in sys.modules):
        raise RuntimeError('External action-context overlay requires a fresh interpreter before bridge import')
    manifest_path = Path(os.environ.get('XAR_RELIC_ACTION_CONTEXT_COMMON_HOOK_MANIFEST',
                          str(stage / 'tools/relic-action-context-common-hooks-a01.json')))
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    sys.meta_path.insert(0, _CandidateFinder(base, manifest))
    sys.path.insert(0, str(base / 'ck3_autonomous_player/src'))
    import xar_autoplayer
    xar_autoplayer.__path__.insert(0, str(stage / 'ck3_autonomous_player/src/xar_autoplayer'))
    bridge_base = base / 'ck3_autonomous_player/src/xar_autoplayer/bridge'
    bridge_stage = stage / 'ck3_autonomous_player/src/xar_autoplayer/bridge'
    spec = importlib.util.spec_from_file_location('xar_autoplayer.bridge', bridge_base / '__init__.py',
                  submodule_search_locations=[str(bridge_stage), str(bridge_base)])
    package = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = package
    xar_autoplayer.bridge = package
    spec.loader.exec_module(package)
    return manifest

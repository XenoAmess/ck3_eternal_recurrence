"""Disk identity for an explicitly selected GUI-only runtime, without native ABI admission."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import re
import sys
from collections.abc import Mapping

from ck3_installation import installed_game_version


def identify_gui_game(repo: Path, game: Path, expected: Mapping[str, object],
                      *, steam_manifest: Path | None = None) -> dict[str, str]:
    """Match launcher, EXE and installed Steam build to the frozen GUI manifest."""
    executable = game.resolve() / 'binaries/ck3.exe'
    version = installed_game_version(executable)
    digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    expected_sha = expected.get('exe_sha256')
    expected_build = expected.get('steam_build_id')
    if (not isinstance(expected_sha, str) or re.fullmatch('[0-9a-fA-F]{64}', expected_sha) is None
            or version != expected.get('version') or digest != expected_sha.lower()
            or type(expected_build) not in (int, str) or re.fullmatch('[0-9]+', str(expected_build)) is None):
        raise ValueError('Installed game differs from the selected GUI metadata')
    manifest = (steam_manifest or game.resolve().parent.parent / 'appmanifest_1158310.acf').resolve()
    parser_path = repo.resolve() / 'ck3_autonomous_player/src/xar_autoplayer/steam_workshop_status.py'
    name = '_gui_steam_metadata_' + hashlib.sha256(str(parser_path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, parser_path)
    if spec is None or spec.loader is None:
        raise ValueError('Shared Steam manifest parser unavailable')
    parser = importlib.util.module_from_spec(spec)
    sys.modules[name] = parser
    try:
        spec.loader.exec_module(parser)
        app = parser._parse_vdf(manifest.read_text(encoding='utf-8-sig')).get('AppState')
    finally:
        sys.modules.pop(name, None)
    if (not isinstance(app, dict) or app.get('appid') != '1158310'
            or app.get('buildid') != str(expected_build) or app.get('StateFlags') != '4'):
        raise ValueError('Installed Steam build differs from the selected GUI metadata')
    return {'game_version': version, 'steam_build_id': str(expected_build), 'exe_sha256': digest}

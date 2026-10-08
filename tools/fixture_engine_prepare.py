"""Prepare-only primitives for exact-build external engine fixtures."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import os
import sys
import json
import re
import shutil
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def engine_identity(repo: Path, *, game_dir: Path | None = None,
                    steam_manifest: Path | None = None) -> dict[str, str]:
    """Identify preparation input from the one native build registry and Steam.

    This is exact engine metadata, not product, native ABI or GUI readiness.
    Optional paths let the shared entry select an installed game explicitly.
    """
    repo = repo.resolve()
    registry_path = repo / "ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py"
    module_name = "_fixture_native_build_identity_" + hashlib.sha256(str(registry_path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(module_name, registry_path)
    if spec is None or spec.loader is None:
        raise ValueError("native exact build registry is unavailable")
    registry = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = registry
    try:
        spec.loader.exec_module(registry)
    finally:
        sys.modules.pop(module_name, None)
    configured = os.environ.get("XAR_CK3_GAME_DIR")
    game = (game_dir or (Path(configured) if configured else repo / "Crusader Kings III")).resolve()
    exe_sha256 = digest(game / "binaries/ck3.exe")
    matches = [item for item in registry.NATIVE_BUILD_IDENTITIES
               if item.executable_sha256.lower() == exe_sha256 and item.game_version.startswith("1.20.")]
    if len(matches) != 1:
        raise ValueError("installed EXE differs from the native registry's exact CK3 1.20 builds")
    build = registry.require_exact_native_build(matches[0].game_version, exe_sha256)
    configured_manifest = os.environ.get("XAR_CK3_STEAM_MANIFEST")
    manifest = (steam_manifest or (Path(configured_manifest) if configured_manifest
                                  else game.parent.parent / "appmanifest_1158310.acf")).resolve()
    steam_build_id = "unknown"
    if manifest.is_file():
        parser_path = repo / "ck3_autonomous_player/src/xar_autoplayer/steam_workshop_status.py"
        parser_name = module_name + "_steam"
        parser_spec = importlib.util.spec_from_file_location(parser_name, parser_path)
        if parser_spec is None or parser_spec.loader is None:
            raise ValueError("shared Steam manifest parser is unavailable")
        parser = importlib.util.module_from_spec(parser_spec)
        sys.modules[parser_name] = parser
        try:
            parser_spec.loader.exec_module(parser)
        finally:
            sys.modules.pop(parser_name, None)
        app = parser._parse_vdf(manifest.read_text(encoding="utf-8-sig")).get("AppState", {})
        if not isinstance(app, dict) or app.get("appid") != "1158310":
            raise ValueError("Steam manifest is not CK3 app 1158310")
        value = app.get("buildid")
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]+", value):
            raise ValueError("Steam build id must be numeric")
        steam_build_id = value
    elif steam_manifest or configured_manifest:
        raise ValueError("explicit Steam manifest is unavailable")
    return {"game_version": build.game_version, "steam_build_id": steam_build_id,
            "exe_sha256": exe_sha256}


def checked_output(repo: Path, output: Path) -> tuple[Path, Path]:
    repo, output = repo.resolve(), output.resolve()
    if output == repo or repo in output.parents:
        raise ValueError("fixture output must be outside the repository")
    if output.exists() or output.with_suffix(".prepare.json").exists():
        raise ValueError("use a new output directory for every attempt")
    engine_identity(repo)
    return repo, output


def write_script(output: Path, relative: str, text: str) -> None:
    target = output / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8-sig", newline="\n")


def copy_files(source: Path, output: Path, files: list[Path]) -> None:
    for path in files:
        target = output / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"fixture anchor changed: {old[:100]!r}")
    return text.replace(old, new, 1)


def balanced_excerpt(source: str, marker: str) -> str:
    """Return one named braced excerpt; comments and quoted braces are ignored."""
    matches = list(re.finditer(marker, source, re.MULTILINE))
    if len(matches) != 1:
        raise ValueError(f"expected one excerpt: {marker!r}, found {len(matches)}")
    start = matches[0].start()
    brace = source.find("{", matches[0].start())
    quoted = escaped = comment = False
    depth = 0
    for index in range(brace, len(source)):
        char = source[index]
        if comment:
            if char == "\n":
                comment = False
            continue
        if escaped:
            escaped = False
        elif quoted and char == "\\":
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif not quoted and char == "#":
            comment = True
        elif not quoted and char == "{":
            depth += 1
        elif not quoted and char == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise ValueError("unterminated excerpt")


def decision_effect(repo: Path, product: str, relative: str, name: str) -> tuple[str, dict]:
    source = repo / product / relative
    raw = source.read_bytes()
    text = raw.decode("utf-8-sig").replace("\r\n", "\n")
    definition = balanced_excerpt(text, rf"^{re.escape(name)}\s*=\s*\{{")
    effect = balanced_excerpt(definition, r"^\teffect\s*=\s*\{")
    body = effect[effect.index("{") + 1:effect.rfind("}")].strip("\n\t ")
    return body, {"file":source.relative_to(repo).as_posix(), "file_sha256":hashlib.sha256(raw).hexdigest(),
                  "decision":name, "effect_sha256":hashlib.sha256(effect.encode("utf-8")).hexdigest()}


def required_markers(runner: Path) -> list[str]:
    parsed = ast.parse(runner.read_text(encoding="utf-8-sig"))
    for node in parsed.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "REQUIRED_MARKERS" for target in node.targets):
            value = ast.literal_eval(node.value)
            return list(value)
    raise ValueError("runner marker inventory is unavailable")


def finish_receipt(repo: Path, source: Path, output: Path, files: list[Path], receipt: dict) -> dict:
    receipt.update({
        **engine_identity(repo),
        "source_fixture":str(source), "prepared_fixture":str(output),
        "runtime_status":"NOT_RUN", "native_abi_loaded":False, "gui_callbacks_mounted":False,
        "source_file_sha256":{p.relative_to(source).as_posix():digest(p) for p in files},
        "prepared_file_sha256":{p.relative_to(output).as_posix():digest(p) for p in sorted(output.rglob("*")) if p.is_file()},
    })
    output.with_suffix(".prepare.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2) + "\n", encoding="utf-8")
    return receipt

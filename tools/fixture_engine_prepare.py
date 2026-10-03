"""Prepare-only primitives for exact-build external engine fixtures."""
from __future__ import annotations

import ast
import hashlib
import json
import re
import shutil
from pathlib import Path

REVIEWED_BUILDS = {
    "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d": (
        "1.20.0.2", "25588574",
    ),
    "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6": (
        "1.20.0.3", "25652598",
    ),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def engine_identity(repo: Path) -> dict[str, str]:
    """Select preparation metadata from the actual reviewed executable bytes.

    This identifies the fixture's engine input, not product or native readiness.
    The separate .3 ABI evidence is recorded in crozier-1.20.0.3-native-migration.
    """
    exe_sha256 = digest(repo / "Crusader Kings III/binaries/ck3.exe")
    try:
        version, build = REVIEWED_BUILDS[exe_sha256]
    except KeyError:
        raise ValueError("installed EXE differs from the reviewed CK3 1.20.0.2/1.20.0.3 builds") from None
    return {"game_version": version, "steam_build_id": build, "exe_sha256": exe_sha256}


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

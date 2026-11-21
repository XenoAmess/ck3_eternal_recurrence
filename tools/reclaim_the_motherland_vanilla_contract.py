"""Exact CK3 1.21.0.3 source contract; no Native/runtime qualification claim."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(os.environ.get("RMTM_CK3_GAME_ROOT", str(ROOT / "Crusader Kings III/game")))
CONTRACT_PATH = ROOT / "tools/reclaim_the_motherland_vanilla_1_21_0_3.json"
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
if (CONTRACT["game_version"], CONTRACT["steam_build_id"], CONTRACT["exe_sha256"]) != (
    "1.21.0.3", "26785313", "859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28"
):
    raise ValueError("RMTM vanilla contract targets a different exact build")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def extract_definition(source: str, name: str = "offer_vassalization_interaction") -> str:
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    matches = list(re.finditer(rf"^{re.escape(name)}\s*=\s*\{{", source, re.MULTILINE))
    if len(matches) != 1:
        raise ValueError(f"definition count for {name}: {len(matches)}, expected 1")
    start = matches[0].start()
    brace = source.find("{", start)
    depth = 0
    quoted = escaped = in_comment = False
    for index in range(brace, len(source)):
        char = source[index]
        if in_comment:
            if char == "\n":
                in_comment = False
            continue
        if escaped:
            escaped = False
        elif quoted and char == "\\":
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif not quoted and char == "#":
            in_comment = True
        elif not quoted and char == "{":
            depth += 1
        elif not quoted and char == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1] + "\n"
    raise ValueError(f"unterminated definition: {name}")


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"{label} anchor count is {count}, expected exactly 1")
    return source.replace(old, new, 1)


def assert_source_files(game: Path = GAME) -> None:
    for relative, expected in CONTRACT["files"].items():
        actual = sha256_bytes((game / relative).read_bytes())
        if actual != expected:
            raise ValueError(f"vanilla file changed: {relative}: {actual}; expected {expected}")
    assert_government_contract((game / CONTRACT["paths"]["government"]).read_text(encoding="utf-8-sig"))


def assert_government_contract(source: str) -> None:
    """Bind the actual primary government and the native ministry flag gate.

    All other government flags used by native Offer remain covered by the full
    seven-file hash contract. No old full-government equivalence is inferred.
    """
    item = CONTRACT["government_contract"]
    if item["key"] != "celestial_government" or item["required_flags"] != [
        "government_is_celestial", "government_uses_ministry_budget"
    ]:
        raise ValueError("RMTM requires the reviewed celestial/ministry government contract")
    body = extract_definition(source, item["key"])
    if sha256_bytes(body.encode("utf-8")) != item["normalized_text_sha256"]:
        raise ValueError("vanilla celestial government body changed")
    flags = re.findall(r"(?m)^\tflags\s*=\s*\{([^{}]*)\}", body)
    if len(flags) != 1:
        raise ValueError("celestial government requires one flat authored flags block")
    tokens = re.sub(r"#[^\n]*", "", flags[0]).split()
    if any(flag not in tokens for flag in item["required_flags"]):
        raise ValueError("celestial government lost the original ministry eligibility flags")


def definition(name: str, game: Path = GAME) -> str:
    item = CONTRACT["definitions"][name]
    raw = (game / item["file"]).read_bytes()
    expected_file = CONTRACT["files"][item["file"]]
    if sha256_bytes(raw) != expected_file:
        raise ValueError(f"vanilla source file changed: {item['file']}")
    body = extract_definition(raw.decode("utf-8-sig"), name)
    assert_definition(body, name)
    return body


def assert_definition(body: str, name: str) -> None:
    expected = CONTRACT["definitions"][name]["normalized_text_sha256"]
    actual = sha256_bytes(body.encode("utf-8"))
    if actual != expected:
        raise ValueError(f"vanilla {name} body changed: {actual}; expected {expected}")


def header(names: tuple[str, ...], note: str) -> str:
    rows = ["# GENERATED FILE. DO NOT EDIT.",
            f"# CK3 {CONTRACT['game_version']} / Steam build {CONTRACT['steam_build_id']} source projection."]
    for name in names:
        item = CONTRACT["definitions"][name]
        rows.append(f"# Vanilla {item['file']} SHA-256: {CONTRACT['files'][item['file']]}")
        rows.append(f"# Vanilla {name} SHA-256: {item['normalized_text_sha256']}")
    return "\n".join(rows) + f"\n# {note}\n\n"

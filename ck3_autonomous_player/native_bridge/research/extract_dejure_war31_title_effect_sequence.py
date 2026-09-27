"""Freeze only the stock de-jure CB victory title-effect script sequence.

This is a hash-bound text extractor, not a title-transfer simulator. In
particular it does not evaluate dynamic scopes or invoke setup/resolve effects.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
SCRIPT_SHA256 = "D8737A2205116118A5ECD6EFA576D316B3155730A3824DC4BD109A68B9D5B6EE"
SCRIPT_PATH = "game/common/casus_belli_types/00_dejure_war.txt"
REQUEST_ID = "WAR-INPUT-R0221-WAR31-20260927"


def _balanced_body(source: str, opening: int) -> tuple[str, int]:
    depth = 0
    for offset in range(opening, len(source)):
        if source[offset] == "{":
            depth += 1
        elif source[offset] == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1 : offset], offset
    raise ValueError("unbalanced stock script block")


def _unique_block(source: str, name: str) -> str:
    matches = list(re.finditer(rf"(?m)^\s*{re.escape(name)}\s*=\s*\{{", source))
    if len(matches) != 1:
        raise ValueError(f"expected one {name} block, found {len(matches)}")
    return _balanced_body(source, source.index("{", matches[0].start()))[0]


def _direct_statements(body: str) -> list[tuple[str, str, int]]:
    """Return direct children of one already-delimited Clausewitz block."""
    statements: list[tuple[str, str, int]] = []
    depth = 0
    offset = 0
    for line_number, line in enumerate(body.splitlines(keepends=True), 1):
        code = line.split("#", 1)[0]
        if depth == 0:
            match = re.match(r"\s*([A-Za-z_][\w:]*)\s*=\s*(\{|[^\s{}]+)", code)
            if match:
                key, value = match.groups()
                if value == "{":
                    value = _balanced_body(body, offset + match.start(2))[0]
                statements.append((key, value, line_number))
        depth += code.count("{") - code.count("}")
        if depth < 0:
            raise ValueError("unexpected closing brace in victory block")
        offset += len(line)
    if depth:
        raise ValueError("unterminated direct child in victory block")
    return statements


def _field(block: str, key: str, expected: str) -> None:
    values = re.findall(rf"(?m)^\s*{re.escape(key)}\s*=\s*([^#\r\n]+)", block)
    if [value.strip() for value in values] != [expected]:
        raise ValueError(f"unexpected {key} field: {values!r}")


def extract(game_dir: Path, request_path: Path) -> dict[str, object]:
    script_raw = (game_dir / SCRIPT_PATH).read_bytes()
    if hashlib.sha256(script_raw).hexdigest().upper() != SCRIPT_SHA256:
        raise ValueError("wrong stock build or changed de-jure CB script")
    if hashlib.sha256((game_dir / "binaries/ck3.exe").read_bytes()).hexdigest().upper() != EXE_SHA256:
        raise ValueError("CK3 executable differs from frozen 1.19.0.6 build")
    request_raw = request_path.read_bytes()
    request = json.loads(request_raw)
    frame = request["reproduction"]
    if (
        request["request_id"] != REQUEST_ID
        or request["source"]["ck3_exe_sha256"] != EXE_SHA256
        or frame["war_id"] != 16777231
        or frame["casus_belli_key"] != "individual_county_de_jure_cb"
        or frame["player_side"] != "defender"
        or not frame["player_is_primary_war_leader"]
        or frame["played_character_id"] != 29829
        or frame["primary_opponent_character_id"] != 30097
        or frame["targeted_title_ids"] != [2128]
    ):
        raise ValueError("R0221 does not match the frozen de-jure War 31 frame")

    cb = _unique_block(script_raw.decode("utf-8-sig"), frame["casus_belli_key"])
    victory = _unique_block(cb, "on_victory")
    statements = _direct_statements(victory)

    def one(key: str, predicate=lambda _: True) -> tuple[str, str, int]:
        matches = [row for row in statements if row[0] == key and predicate(row[1])]
        if len(matches) != 1:
            raise ValueError(f"expected one direct {key}, found {len(matches)}")
        return matches[0]

    create = one("create_title_and_vassal_change")
    target_loop = one("every_in_list", lambda value: "save_temporary_scope_as = target" in value)
    setup = one("setup_de_jure_cb")
    resolve = one("resolve_title_and_vassal_change")
    if not (create[2] < target_loop[2] < setup[2] < resolve[2]):
        raise ValueError("title-effect sequence or direct-child scope changed")
    for key, expected in (
        ("type", "conquest"), ("save_scope_as", "change"),
        ("add_claim_on_loss", "yes"),
    ):
        _field(create[1], key, expected)
    _field(target_loop[1], "list", "target_titles")
    _field(target_loop[1], "save_temporary_scope_as", "target")
    for key, expected in (
        ("attacker", "scope:attacker"), ("defender", "scope:defender"),
        ("change", "scope:change"), ("title", "scope:target"),
    ):
        _field(setup[1], key, expected)
    if resolve[1] != "scope:change":
        raise ValueError("resolved change scope differs from created change scope")
    if re.search(r"(?m)^\s*change_title_holder\s*=", victory):
        raise ValueError("unexpected explicit title-holder effect in on_victory")

    return {
        "schema": "xar.ck3.war31.dejure_title_effect_sequence.v1",
        "status": "STATIC_SCRIPT_SEQUENCE_ONLY",
        "exact_build": {"version": "1.19.0.6-steam23530548", "exe_sha256": EXE_SHA256},
        "script_path": SCRIPT_PATH,
        "script_sha256": SCRIPT_SHA256,
        "request_id": REQUEST_ID,
        "request_sha256": hashlib.sha256(request_raw).hexdigest().upper(),
        "war_id": frame["war_id"],
        "declared_target_title_ids_in_request": frame["targeted_title_ids"],
        "scripted_sequence": [
            {"step": "create_title_and_vassal_change", "type": "conquest",
             "saved_scope": "change", "add_claim_on_loss": True},
            {"step": "every_in_list", "list": "target_titles",
             "inner_effect": "save_temporary_scope_as", "saved_scope": "target"},
            {"step": "setup_de_jure_cb", "attacker": "scope:attacker",
             "defender": "scope:defender", "change": "scope:change", "title": "scope:target"},
            {"step": "resolve_title_and_vassal_change", "change": "scope:change"},
        ],
        "same_nesting_level_in_on_victory": True,
        "setup_is_outside_target_loop": True,
        "explicit_change_title_holder_in_on_victory": False,
        "unknown": [
            "Live target_titles list and scope:target referent when setup runs",
            "Runtime CTitleAndVassalChange object contents and native setup/resolve effects",
            "Final title holder, liege and vassal operations or persisted result",
        ],
        "ck3_launched": False,
        "effect_invoked": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(extract(args.game_dir, args.request), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

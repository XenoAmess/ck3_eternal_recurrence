"""Project paired CK3 save IDs to bounded human-readable battle labels.

Only saved identity fields and original simplified-Chinese localization are
used. Generated army-label rendering and full character titulature are not
claimed to be live UI strings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


IDENTITY_SIDECAR_SHA = "69B906918120294000C8BB821A1AEEFE43BD210FB14610E8EACC1B0CFC1BC210"
PAIRS = {
    11: ("3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953",
         "A82FDD3A57B84B8FC5E4A42EBD292013C45FAA5061D89F79D9E7A24E979A01C6"),
    21: ("E16B8EDE740F674973DE99036E6B0589E85B1866A5BBA8FD7C2E3D4B2DF7630A",
         "48F2EA80D7AF0DA5EA4DA3B34E965A481BD2FF201017E35F0F08711503089B61"),
}
ARMY_OWNERS = {16777221: 31549, 16777231: 32725, 27: 34320,
               22: 32231, 18: 29829}
PEOPLE = {31549: ("Ali", "阿里"), 32725: ("Tamim", "塔米姆"),
          34320: ("Ramadan", "拉马丹"), 32231: ("Munis", "穆尼斯"),
          29829: ("Robert", "罗贝尔")}
TITLE_ROWS = {2111: ("c_siracusa", 31549, "塞尔古塞"),
              2112: ("b_syracusa", 31549, "塞尔古塞"),
              2141: ("d_apulia", 29829, "阿普利亚")}
EXPECTED_ROSTERS = {11: ([16777221, 16777231, 27], [18]),
                    21: ([16777221, 16777231, 27, 22], [18])}
GAME_FILES = {
    "names_zh": "localization/simp_chinese/names/character_names_l_simp_chinese.yml",
    "nicknames_zh": "localization/simp_chinese/nicknames_l_simp_chinese.yml",
    "titles_zh": "localization/simp_chinese/titles_l_simp_chinese.yml",
    "landed_titles": "common/landed_titles/00_landed_titles.txt",
    "province_definition": "map_data/definition.csv",
}


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def blocks(path: Path) -> dict[tuple[int, int], list[dict]]:
    """Collect only selected exact-id blocks, with indentation and SHA intact."""
    wanted = {
        1: set(ARMY_OWNERS) | set(PEOPLE),
        2: {16777221, 16777218, *TITLE_ROWS},
    }
    starts = {b"\t" * depth + str(identity).encode() + b"={": (depth, identity)
              for depth, identities in wanted.items() for identity in identities}
    found: dict[tuple[int, int], list[dict]] = {}
    active: list[bytes] | None = None
    active_id: tuple[int, int] | None = None
    start_line = 0
    with path.open("rb") as stream:
        for line_no, raw in enumerate(stream, 1):
            stripped = raw.rstrip(b"\r\n")
            if active is None:
                active_id = starts.get(stripped)
                if active_id is not None:
                    active = [raw]
                    start_line = line_no
                continue
            active.append(raw)
            if stripped != b"\t" * active_id[0] + b"}":
                continue
            payload = b"".join(active)
            found.setdefault(active_id, []).append({
                "line_start": start_line, "line_end": line_no,
                "sha256": hashlib.sha256(payload).hexdigest().upper(),
                "raw": payload,
            })
            active = None
            active_id = None
    require(active is None, f"unterminated selected save block: {path}")
    return found


def select(found: dict, depth: int, identity: int, *markers: bytes) -> dict:
    hits = [block for block in found.get((depth, identity), [])
            if all(marker in block["raw"] for marker in markers)]
    require(len(hits) == 1, f"expected one ({depth},{identity}) with markers: {len(hits)}")
    return hits[0]


def exact_value(block: bytes, key: str, depth: int) -> str:
    pattern = rb"(?m)^" + b"\t" * depth + re.escape(key.encode()) + rb"=(?:\"([^\"]*)\"|([^\r\n]*))\r?$"
    matches = re.findall(pattern, block)
    require(len(matches) == 1, f"{key} at depth {depth} count {len(matches)}")
    return (matches[0][0] or matches[0][1]).decode("utf-8-sig")


def entry(block: dict) -> dict:
    return {key: block[key] for key in ("line_start", "line_end", "sha256")}


def roster(side: bytes) -> list[int]:
    match = re.search(rb"\t\t\t\tarmies=\{\r?\n\t\t\t\t\t([0-9 ]+)\r?\n\t\t\t\t\}", side)
    require(match is not None, "combat side armies unavailable")
    return [int(value) for value in match.group(1).split()]


def localization(lines: list[str], key: str, expected: str) -> int:
    pattern = re.compile(rf'^\s*{re.escape(key)}:(?:0)?\s*"{re.escape(expected)}"\s*$')
    hits = [number for number, line in enumerate(lines, 1) if pattern.fullmatch(line)]
    require(len(hits) == 1, f"original localization {key} mismatch")
    return hits[0]


def save_case(day: int, source: Path, melted: Path) -> dict:
    source_sha, melted_sha = PAIRS[day]
    require(digest(source) == source_sha, f"day {day} source-save SHA mismatch")
    require(digest(melted) == melted_sha, f"day {day} melted-save SHA mismatch")
    found = blocks(melted)
    units = {}
    people = {}
    for army_id, owner in ARMY_OWNERS.items():
        unit = select(found, 1, army_id, b"\t\ttype=army", f"\t\tarmy={army_id}".encode())
        require(int(exact_value(unit["raw"], "owner", 2)) == owner,
                f"day {day} ArmyID {army_id} owner changed")
        units[str(army_id)] = {"owner_character_id": owner, **entry(unit)}
    for character_id, (key, _) in PEOPLE.items():
        character = select(found, 1, character_id, f'\t\tfirst_name="{key}"'.encode())
        require(exact_value(character["raw"], "first_name", 2) == key,
                f"day {day} CharacterID {character_id} first_name changed")
        people[str(character_id)] = {"first_name_key": key, **entry(character)}
        if character_id in (31549, 29829):
            nickname_key, nickname_zh = (("nick_benavert", "贝纳韦尔特")
                                         if character_id == 31549 else ("nick_the_fox", "狐狸"))
            require(exact_value(character["raw"], "nickname", 2) == nickname_key
                    and exact_value(character["raw"], "nickname_text", 2) == nickname_zh,
                    f"day {day} CharacterID {character_id} nickname changed")
            people[str(character_id)].update({"nickname_key": nickname_key,
                                               "saved_nickname_text_zh": nickname_zh})
    title_rows = {}
    for title_id, (key, holder, dynamic_name) in TITLE_ROWS.items():
        title = select(found, 2, title_id, f'\t\t\tkey="{key}"'.encode())
        require(int(exact_value(title["raw"], "holder", 3)) == holder,
                f"day {day} title {key} holder changed")
        require(exact_value(title["raw"], "name", 4) == dynamic_name,
                f"day {day} title {key} dynamic name changed")
        title_rows[str(title_id)] = {"key": key, "holder_character_id": holder,
                                     "saved_dynamic_name_zh": dynamic_name, **entry(title)}
    army = select(found, 2, 16777221, b"\t\t\tunit=16777221", b"\t\t\tregiments={")
    require(b"\t\t\t\t87 88 89 90 91 92" in army["raw"]
            and exact_value(army["raw"], "commander", 3) == "31549"
            and exact_value(army["raw"], "id", 4) == "0"
            and exact_value(army["raw"], "province", 4) == "2638",
            f"day {day} ArmyID 16777221 regiment/commander/name seed changed")
    battle = select(found, 2, 16777218, b"\t\t\tphase=main",
                    b"\t\t\tcombat_results=16777218", b"\t\t\tprovince=2633")
    match = re.search(rb"\t\t\tattacker=\{(.*?)\t\t\t\}\r?\n\t\t\tdefender=\{(.*?)\t\t\t\}\r?\n\t\t\tphase=main", battle["raw"], re.S)
    require(match is not None, f"day {day} combat sides unavailable")
    attacker, defender = match.groups()
    attack_ids, defense_ids = roster(attacker), roster(defender)
    require((attack_ids, defense_ids) == EXPECTED_ROSTERS[day],
            f"day {day} CombatID 16777218 roster changed")
    require(exact_value(attacker, "leader", 4) == "31549"
            and exact_value(attacker, "commander", 4) == "34320"
            and exact_value(defender, "leader", 4) == "29829"
            and exact_value(defender, "commander", 4) == "29829",
            f"day {day} CombatID 16777218 leader/commander changed")
    result = select(found, 2, 16777218, b"\t\t\tlocation=2633",
                    b"\t\t\t\tmain_participant=31549",
                    b"\t\t\t\tmain_participant=29829")
    return {
        "source_day": day, "source_save_sha256": source_sha,
        "rakaly_melted_sha256": melted_sha,
        "units": units, "characters": people, "titles": title_rows,
        "regiment_87_army": {"army_id": 16777221, "commander_character_id": 31549,
                            "saved_name_seed": {"id": 0, "province_id": 2638},
                            **entry(army)},
        "combat": {"combat_id": 16777218, "province_id": 2633,
                   "attacker_army_ids": attack_ids, "attacker_leader_character_id": 31549,
                   "attacker_commander_character_id": 34320,
                   "defender_army_ids": defense_ids, "defender_leader_character_id": 29829,
                   "defender_commander_character_id": 29829,
                   **entry(battle)},
        "combat_result_main_participants": {"attacker": 31549, "defender": 29829,
                                            **entry(result)},
    }


def project(args: argparse.Namespace) -> dict:
    require(digest(args.identity_sidecar) == IDENTITY_SIDECAR_SHA,
            "prior paired-save identity sidecar SHA mismatch")
    cases = [save_case(day, getattr(args, f"day{day}_save"),
                       getattr(args, f"day{day}_melted")) for day in (11, 21)]
    sources = {key: args.game_root / relative for key, relative in GAME_FILES.items()}
    names = sources["names_zh"].read_text(encoding="utf-8-sig").splitlines()
    nicknames = sources["nicknames_zh"].read_text(encoding="utf-8-sig").splitlines()
    titles = sources["titles_zh"].read_text(encoding="utf-8-sig").splitlines()
    people = {str(identity): {"first_name_key": key, "first_name_zh": zh,
                              "localization_line": localization(names, key, zh)}
              for identity, (key, zh) in PEOPLE.items()}
    for identity, key, zh in ((31549, "nick_benavert", "贝纳韦尔特"),
                              (29829, "nick_the_fox", "狐狸")):
        people[str(identity)].update({"nickname_key": key, "nickname_zh": zh,
                                      "nickname_localization_line": localization(nicknames, key, zh)})
    title_base_names = {"c_siracusa": "锡拉库萨", "b_syracusa": "叙拉古",
                        "d_apulia": "阿普利亚"}
    title_localizations = {key: {"base_name_zh": value,
                                 "localization_line": localization(titles, key, value)}
                           for key, value in title_base_names.items()}
    landed = sources["landed_titles"].read_text(encoding="utf-8-sig").splitlines()
    seed_hits = [line for line, text in enumerate(landed, 1)
                 if text.strip() == "b_syracusa = {"
                 and line < len(landed) and landed[line].strip() == "province = 2638"]
    require(len(seed_hits) == 1, "ArmyID 16777221 name seed province-to-title map changed")
    definitions = sources["province_definition"].read_text(encoding="utf-8-sig").splitlines()
    definition_hits = [line for line, text in enumerate(definitions, 1)
                       if text.strip() == "2638;128;33;19;SYRACUSE;x;"]
    require(len(definition_hits) == 1, "ProvinceID 2638 definition changed")
    return {
        "schema": "ck3.episode01_paired_combat_human_names.v2",
        "paired_save_identity_sidecar_sha256": IDENTITY_SIDECAR_SHA,
        "cases": cases,
        "game_sources": {key: {"relative_path": relative, "sha256": digest(sources[key])}
                         for key, relative in GAME_FILES.items()},
        "first_names_zh": people,
        "title_base_localizations_zh": title_localizations,
        "army_16777221_name_seed_province": {"province_id": 2638,
            "definition_line": definition_hits[0], "landed_title_key": "b_syracusa",
            "landed_title_line": seed_hits[0]},
        "viewer_explanatory_labels_zh": {
            "attacker": "阿里（塞尔古塞领主）及塔米姆、拉马丹；第21日另有穆尼斯军",
            "defender": "罗贝尔（阿普利亚领主）",
        },
        "exact_generated_army_label_proven": False,
        "exact_full_character_ui_titulature_proven": False,
        "source_save_identity_not_same_frame_ui_readback": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identity-sidecar", type=Path, required=True)
    for day in (11, 21):
        parser.add_argument(f"--day{day}-save", type=Path, required=True)
        parser.add_argument(f"--day{day}-melted", type=Path, required=True)
    parser.add_argument("--game-root", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--check-sidecar", type=Path)
    args = parser.parse_args()
    value = project(args)
    if args.check_sidecar:
        require(json.loads(args.check_sidecar.read_text(encoding="utf-8")) == value,
                "human-name sidecar differs from projection")
        print(json.dumps({"ok": True, "sidecar_sha256": digest(args.check_sidecar)}))
    else:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()

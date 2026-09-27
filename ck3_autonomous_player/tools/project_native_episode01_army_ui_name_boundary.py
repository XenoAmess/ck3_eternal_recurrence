"""Audit army-name save seeds against original CK3 GUI and localization.

This deliberately does not render Army.GetNameNoTooltip from a save seed.
That callback's runtime branch and Province.GetNameNoTooltip are not frozen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


PRIOR_SIDECAR_SHA = "9D9385F55B3FAC7A74CDDA4D2A51C8DB1FCE2E96EEFE4727460B372E53D81D9A"
PAIRS = {
    11: ("3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953",
         "A82FDD3A57B84B8FC5E4A42EBD292013C45FAA5061D89F79D9E7A24E979A01C6"),
    21: ("E16B8EDE740F674973DE99036E6B0589E85B1866A5BBA8FD7C2E3D4B2DF7630A",
         "48F2EA80D7AF0DA5EA4DA3B34E965A481BD2FF201017E35F0F08711503089B61"),
}
ARMIES = {18: (2619, "b_trani", "特拉尼", "罗贝尔"),
          16777221: (2638, "b_syracusa", "叙拉古", "阿里"),
          22: (4598, "b_al-qasrayn", "卡塞林", "穆尼斯"),
          27: (2646, "b_malta", "马耳他", "拉马丹"),
          16777231: (4578, "b_mahdiya", "马赫迪耶", "塔米姆")}
GAME_FILES = {
    "army_window_gui": "gui/window_army.gui",
    "outliner_gui": "gui/hud_outliner.gui",
    "core_zh": "localization/simp_chinese/core_l_simp_chinese.yml",
    "titles_zh": "localization/simp_chinese/titles_l_simp_chinese.yml",
    "landed_titles": "common/landed_titles/00_landed_titles.txt",
    "province_definition": "map_data/definition.csv",
}
TEMPLATES = {
    "ARMY_NAME": "[PROVINCE.GetNameNoTooltip]第$NUM|O$军",
    "ARMY_NAME_RAIDER": "[PROVINCE.GetNameNoTooltip]第$NUM|O$劫掠队",
    "ARMY_NAME_BARTER": "[PROVINCE.GetNameNoTooltip]第$NUM|O$交易团",
    "ARMY_NAME_LANDLESS": "[CHARACTER.GetPrimaryTitle.GetNameNoTooltip]第$NUM|O$军",
    "GATHERING_ARMY_NAME": "在$LOCATION$集结军队",
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


def unique_line(lines: list[str], expected: str) -> int:
    hits = [number for number, line in enumerate(lines, 1) if line.strip() == expected]
    require(len(hits) == 1, f"expected one original line {expected!r}: {len(hits)}")
    return hits[0]


def saved_army_names(path: Path) -> dict[str, dict]:
    starts = {f"\t\t{army_id}={{".encode(): army_id for army_id in ARMIES}
    found: dict[int, list[dict]] = {army_id: [] for army_id in ARMIES}
    active: list[bytes] | None = None
    active_id: int | None = None
    line_start = 0
    with path.open("rb") as stream:
        for line_no, raw in enumerate(stream, 1):
            line = raw.rstrip(b"\r\n")
            if active is None:
                active_id = starts.get(line)
                if active_id is not None:
                    active = [raw]
                    line_start = line_no
                continue
            active.append(raw)
            if line != b"\t\t}":
                continue
            payload = b"".join(active)
            if (f"\t\t\tunit={active_id}".encode() in payload
                    and b"\t\t\tregiments={" in payload):
                found[active_id].append({"line_start": line_start, "line_end": line_no,
                                         "block_sha256": hashlib.sha256(payload).hexdigest().upper(),
                                         "raw": payload})
            active = None
            active_id = None
    require(active is None, f"unterminated selected army block: {path}")
    result = {}
    for army_id, (province, _, _, _) in ARMIES.items():
        hits = found[army_id]
        require(len(hits) == 1, f"ArmyID {army_id} composition block count {len(hits)}")
        block = hits[0]
        expected = f"\t\t\tname={{\n\t\t\t\tid=0\n\t\t\t\tprovince={province}\n\t\t\t}}".encode()
        normalized = block["raw"].replace(b"\r\n", b"\n")
        require(expected in normalized,
                f"ArmyID {army_id} save name seed no longer id=0/province={province}")
        result[str(army_id)] = {"save_name_id": 0, "seed_province_id": province,
                               "line_start": block["line_start"],
                               "line_end": block["line_end"],
                               "block_sha256": block["block_sha256"]}
    return result


def project(args: argparse.Namespace) -> dict:
    require(digest(args.prior_sidecar) == PRIOR_SIDECAR_SHA,
            "paired combat name sidecar SHA mismatch")
    prior = json.loads(args.prior_sidecar.read_text(encoding="utf-8"))
    require(prior["schema"] == "ck3.episode01_paired_combat_human_names.v2",
            "prior sidecar schema changed")
    cases = []
    for day in (11, 21):
        source = getattr(args, f"day{day}_save")
        melted = getattr(args, f"day{day}_melted")
        source_sha, melted_sha = PAIRS[day]
        require(digest(source) == source_sha and digest(melted) == melted_sha,
                f"day {day} paired source/melt SHA mismatch")
        seeds = saved_army_names(melted)
        previous = next(case for case in prior["cases"] if case["source_day"] == day)
        for army_id in ARMIES:
            require(str(army_id) in previous["units"],
                    f"day {day} prior combat owner map lost ArmyID {army_id}")
        cases.append({"source_day": day, "source_save_sha256": source_sha,
                      "rakaly_melted_sha256": melted_sha, "army_name_seeds": seeds,
                      "combat_army_ids": {side: previous["combat"][f"{side}_army_ids"]
                                           for side in ("attacker", "defender")}})
    sources = {key: args.game_root / relative for key, relative in GAME_FILES.items()}
    army_gui = sources["army_window_gui"].read_text(encoding="utf-8-sig").splitlines()
    outliner = sources["outliner_gui"].read_text(encoding="utf-8-sig").splitlines()
    core = sources["core_zh"].read_text(encoding="utf-8-sig").splitlines()
    title_loc = sources["titles_zh"].read_text(encoding="utf-8-sig").splitlines()
    landed = sources["landed_titles"].read_text(encoding="utf-8-sig").splitlines()
    definitions = sources["province_definition"].read_text(encoding="utf-8-sig").splitlines()
    window_getter_lines = [number for number, line in enumerate(army_gui, 1)
                           if line.strip() == 'text = "[Army.GetNameNoTooltip]"']
    require(window_getter_lines == [333, 462], "original army window getter locations changed")
    outliner_getter_line = unique_line(outliner, 'text = "[Army.GetNameNoTooltip]"')
    template_lines = {key: unique_line(core, f'{key}: "{value}"')
                      for key, value in TEMPLATES.items()}
    provinces = {}
    for army_id, (province, barony, base_zh, owner_zh) in ARMIES.items():
        definition_hits = [number for number, text in enumerate(definitions, 1)
                           if text.startswith(f"{province};")]
        require(len(definition_hits) == 1, f"ProvinceID {province} definition ambiguous")
        title_hits = [number for number, text in enumerate(landed, 1)
                      if text.strip() == f"{barony} = {{"
                      and number < len(landed)
                      and landed[number].strip() == f"province = {province}"]
        require(len(title_hits) == 1, f"ProvinceID {province} barony map ambiguous")
        loc_line = unique_line(title_loc, f'{barony}: "{base_zh}"')
        provinces[str(province)] = {"army_id": army_id, "saved_owner_short_name_zh": owner_zh,
                                    "landed_title_key": barony,
                                    "base_localization_zh": base_zh,
                                    "definition_line": definition_hits[0],
                                    "landed_title_line": title_hits[0],
                                    "base_localization_line": loc_line}
    return {
        "schema": "ck3.episode01_army_ui_name_boundary.v1",
        "paired_combat_names_sidecar_sha256": PRIOR_SIDECAR_SHA,
        "cases": cases,
        "game_sources": {key: {"relative_path": relative, "sha256": digest(sources[key])}
                         for key, relative in GAME_FILES.items()},
        "ui_getter_lines": {"army_window": window_getter_lines,
                            "outliner": outliner_getter_line},
        "localization_template_lines": template_lines,
        "seed_province_base_name_candidates": provinces,
        "exact_native_getter_branch_proven": False,
        "name_id_to_display_ordinal_proven": False,
        "province_runtime_display_name_proven": False,
        "exact_army_ui_titles_proven": False,
        "safe_explanatory_labels_zh": {str(army_id): f"{owner}的军队"
                                       for army_id, (_, _, _, owner) in ARMIES.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior-sidecar", type=Path, required=True)
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
                "army UI name boundary sidecar differs from source projection")
        print(json.dumps({"ok": True, "sidecar_sha256": digest(args.check_sidecar)}))
    else:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()

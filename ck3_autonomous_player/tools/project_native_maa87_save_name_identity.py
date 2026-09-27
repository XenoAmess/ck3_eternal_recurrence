"""Read-only source-save identity bridge for Messina RegimentID 87.

The paired saves identify the native MAA type; current-frame v3 stat inputs
still omit that key. This script never attributes a stat delta to modifiers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
RAKALY_SHA256 = "E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D"
PAIRS = {
    11: (
        "3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953",
        "A82FDD3A57B84B8FC5E4A42EBD292013C45FAA5061D89F79D9E7A24E979A01C6",
    ),
    21: (
        "E16B8EDE740F674973DE99036E6B0589E85B1866A5BBA8FD7C2E3D4B2DF7630A",
        "48F2EA80D7AF0DA5EA4DA3B34E965A481BD2FF201017E35F0F08711503089B61",
    ),
}
GAME_FILES = {
    "maa_definition": "common/men_at_arms_types/00_cultural_maa_types.txt",
    "province_definition": "map_data/definition.csv",
    "landed_titles": "common/landed_titles/00_landed_titles.txt",
    "maa_localization_zh": "localization/simp_chinese/regiment_l_simp_chinese.yml",
    "maa_localization_en": "localization/english/regiment_l_english.yml",
    "province_localization_zh": "localization/simp_chinese/titles_l_simp_chinese.yml",
    "province_localization_en": "localization/english/titles_l_english.yml",
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


def saved_regiment(path: Path) -> dict:
    """Find the unique 87 block carrying both type and army identity."""
    candidates = []
    active: list[tuple[int, bytes]] | None = None
    with path.open("rb") as stream:
        for line_number, line in enumerate(stream, 1):
            if active is None:
                if line.rstrip(b"\r\n") == b"\t\t87={":
                    active = [(line_number, line)]
                continue
            active.append((line_number, line))
            if line.rstrip(b"\r\n") != b"\t\t}":
                continue
            block = b"".join(raw for _, raw in active)
            if (b'\t\t\ttype="mubarizun"' in block
                    and b"\t\t\tarmy=16777221" in block):
                candidates.append({
                    "line_start": active[0][0],
                    "line_end": active[-1][0],
                    "type_key": "mubarizun",
                    "army_id": 16777221,
                    "block_sha256": hashlib.sha256(block).hexdigest().upper(),
                })
            active = None
    require(len(candidates) == 1, f"expected one saved RegimentID 87 block: {len(candidates)}")
    return candidates[0]


def localization(path: Path, key: str, expected: str) -> int:
    pattern = re.compile(rf"^\s*{re.escape(key)}:(?:0)?\s*\"{re.escape(expected)}\"\s*$")
    matches = [n for n, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1)
               if pattern.fullmatch(line)]
    require(len(matches) == 1, f"localization {key} mismatch: {path}")
    return matches[0]


def unique_line(path: Path, literal: str) -> int:
    matches = [n for n, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1)
               if line.strip() == literal]
    require(len(matches) == 1, f"expected one {literal!r} in {path}")
    return matches[0]


def project(args: argparse.Namespace) -> dict:
    require(digest(args.exe) == EXE_SHA256, "exact CK3 EXE SHA-256 mismatch")
    require(digest(args.rakaly_exe) == RAKALY_SHA256, "Rakaly 0.8.19 EXE SHA-256 mismatch")
    cases = []
    for day in (11, 21):
        source = getattr(args, f"day{day}_save")
        melted = getattr(args, f"day{day}_melted")
        source_sha, melted_sha = PAIRS[day]
        require(digest(source) == source_sha, f"day {day} immutable source save SHA-256 mismatch")
        require(digest(melted) == melted_sha, f"day {day} Rakaly melted text SHA-256 mismatch")
        cases.append({
            "source_day": day,
            "source_save": {"path": str(source), "sha256": source_sha},
            "rakaly_melted": {"path": str(melted), "sha256": melted_sha},
            "regiment_id": 87,
            **saved_regiment(melted),
        })

    files = {key: args.game_root / relative for key, relative in GAME_FILES.items()}
    maa = files["maa_definition"]
    maa_text = maa.read_text(encoding="utf-8-sig")
    match = re.search(
        r"(?m)^mubarizun\s*=\s*\{\s*type\s*=\s*heavy_infantry\s*"
        r"damage\s*=\s*45\s*toughness\s*=\s*25\s*"
        r"pursuit\s*=\s*0\s*screen\s*=\s*0",
        maa_text,
    )
    require(match is not None, "mubarizun base definition mismatch")
    maa_line = maa_text[:match.start()].count("\n") + 1
    province_line = unique_line(files["province_definition"], "2633;128;18;144;MESSINA;x;")
    landed = files["landed_titles"].read_text(encoding="utf-8-sig").splitlines()
    title_lines = [n for n, line in enumerate(landed, 1)
                   if line.strip() == "b_messina = {"
                   and n < len(landed) and landed[n].strip() == "province = 2633"]
    require(len(title_lines) == 1, "ProvinceID 2633 to b_messina binding mismatch")
    loc_lines = {
        "maa_zh": localization(files["maa_localization_zh"], "mubarizun", "穆巴里尊"),
        "maa_en": localization(files["maa_localization_en"], "mubarizun", "Mubarizun"),
        "province_zh": localization(files["province_localization_zh"], "b_messina", "墨西拿"),
        "province_en": localization(files["province_localization_en"], "b_messina", "Messina"),
    }
    return {
        "schema": "ck3.maa87_source_save_human_identity.v1",
        "game_build": "1.19.0.6",
        "exe_sha256": EXE_SHA256,
        "rakaly_version": "0.8.19",
        "rakaly_exe_sha256": RAKALY_SHA256,
        "source_cases": cases,
        "game_sources": {
            key: {"relative_path": GAME_FILES[key], "sha256": digest(path)}
            for key, path in files.items()
        },
        "maa_type": {"key": "mubarizun", "native_class_key": "heavy_infantry",
                     "base_damage": 45, "base_toughness": 25,
                     "definition_line": maa_line,
                     "localization_lines": {"zh": loc_lines["maa_zh"], "en": loc_lines["maa_en"]},
                     "name_zh": "穆巴里尊", "name_en": "Mubarizun"},
        "target_province": {"id": 2633, "definition_line": province_line,
                            "landed_title_key": "b_messina", "landed_title_line": title_lines[0],
                            "localization_lines": {"zh": loc_lines["province_zh"],
                                                   "en": loc_lines["province_en"]},
                            "name_zh": "墨西拿", "name_en": "Messina"},
        "v3_maa_type_key_filled": False,
        "same_frame_modifier_source_proven": False,
        "source_save_identity_only": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for day in (11, 21):
        parser.add_argument(f"--day{day}-save", type=Path, required=True)
        parser.add_argument(f"--day{day}-melted", type=Path, required=True)
    parser.add_argument("--rakaly-exe", type=Path, required=True)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--game-root", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--check-sidecar", type=Path)
    args = parser.parse_args()
    result = project(args)
    if args.check_sidecar:
        require(json.loads(args.check_sidecar.read_text(encoding="utf-8")) == result,
                "frozen sidecar differs from read-only projection")
        print(json.dumps({"ok": True, "sidecar_sha256": digest(args.check_sidecar)}))
    else:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()

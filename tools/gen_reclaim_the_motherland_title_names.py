#!/usr/bin/env python3
"""Generate the pinned vanilla Chinese realm-name copier for Later titles."""

from __future__ import annotations

import codecs
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT
    / "mod_reclaim_the_motherland"
    / "common"
    / "scripted_effects"
    / "rmtm_generated_title_name_effects.txt"
)
LOCALIZATION_ROOT = ROOT / "mod_reclaim_the_motherland" / "localization"
LANGUAGES = (
    "english",
    "french",
    "german",
    "japanese",
    "korean",
    "polish",
    "russian",
    "simp_chinese",
    "spanish",
)
VANILLA_SOURCE_SHA256 = "86574fb7ce246ef6d1b2741b211785d282ad39659e8771e0e5c714acdc001782"
TITLE_KEYS = (
    "dynn_title_ba", "dynn_title_bao", "dynn_title_bi", "dynn_title_bo",
    "dynn_title_cai", "dynn_title_cao", "dynn_title_chen", "dynn_title_cheng",
    "dynn_title_chu", "dynn_title_dai", "dynn_title_dao", "dynn_title_deng",
    "dynn_title_di", "dynn_title_dian", "dynn_title_e", "dynn_title_fu",
    "dynn_title_gan", "dynn_title_gui", "dynn_title_guo", "dynn_title_han",
    "dynn_title_han_henan", "dynn_title_han_korea", "dynn_title_he",
    "dynn_title_hua", "dynn_title_huai", "dynn_title_huang", "dynn_title_huo",
    "dynn_title_ji", "dynn_title_ji_hebei", "dynn_title_jiao", "dynn_title_jin",
    "dynn_title_jing", "dynn_title_ju", "dynn_title_jurchen_jin",
    "dynn_title_kang", "dynn_title_lai", "dynn_title_le", "dynn_title_li",
    "dynn_title_liang", "dynn_title_liang_west", "dynn_title_liao",
    "dynn_title_lu", "dynn_title_luo", "dynn_title_miao", "dynn_title_min",
    "dynn_title_nan", "dynn_title_ou", "dynn_title_peng", "dynn_title_qi",
    "dynn_title_qi_guannei", "dynn_title_qian", "dynn_title_qin",
    "dynn_title_qiong", "dynn_title_rui", "dynn_title_shang", "dynn_title_shen",
    "dynn_title_shu", "dynn_title_song", "dynn_title_sui", "dynn_title_tan",
    "dynn_title_tang", "dynn_title_teng", "dynn_title_wei", "dynn_title_wey",
    "dynn_title_wu", "dynn_title_xi", "dynn_title_xia", "dynn_title_xiang",
    "dynn_title_xing", "dynn_title_xu", "dynn_title_xu_shandong",
    "dynn_title_yan", "dynn_title_yang", "dynn_title_yin", "dynn_title_ying",
    "dynn_title_yong", "dynn_title_you", "dynn_title_yu", "dynn_title_yuan",
    "dynn_title_yuan_ferghana", "dynn_title_yue", "dynn_title_yue_2",
    "dynn_title_zhan", "dynn_title_zhao", "dynn_title_zhen",
    "dynn_title_zheng", "dynn_title_zhou", "dynn_title_zhuang_li",
    "dynn_title_zou",
)


def rendered_text() -> str:
    lines = [
        "# GENERATED FILE. Edit tools/gen_reclaim_the_motherland_title_names.py.",
        f"# Vanilla TGP scripted-effects SHA-256: {VANILLA_SOURCE_SHA256.upper()}",
        "# Character scope; h_china and scope:rmtm_restoration_hegemony_title exist.",
        "rmtm_freeze_restoration_hegemony_name_effect = {",
    ]
    for index, key in enumerate(TITLE_KEYS):
        branch = "if" if index == 0 else "else_if"
        lines.extend(
            (
                f"\t{branch} = {{",
                f"\t\tlimit = {{ title:h_china = {{ is_title_localization_key_used = {key} }} }}",
                "\t\tscope:rmtm_restoration_hegemony_title = {",
                f"\t\t\tset_title_name = rmtm_later_{key}",
                "\t\t}",
                "\t}",
            )
        )
    lines.extend(
        (
            "\telse = {",
            "\t\t# Preserve a literal player-authored title name when no pinned vanilla key matches.",
            "\t\ttitle:h_china = {",
            "\t\t\tmove_title_name_to = scope:rmtm_restoration_hegemony_title",
            "\t\t}",
            "\t\t# A literal player-authored name has no finite localization-key alias.",
            "\t\t# CK3's native prefix field is the only lossless dynamic representation.",
            "\t\tscope:rmtm_restoration_hegemony_title = {",
            "\t\t\tset_title_prefix = rmtm_restoration_title_prefix",
            "\t\t}",
            "\t}",
            "\ttitle:h_china = { reset_title_name = yes }",
            "}",
            "",
        )
    )
    return "\n".join(lines)


def rendered_bytes() -> bytes:
    return codecs.BOM_UTF8 + rendered_text().encode("utf-8")


def localization_output(language: str) -> Path:
    if language not in LANGUAGES:
        raise ValueError(f"unsupported language: {language}")
    return (
        LOCALIZATION_ROOT
        / language
        / f"rmtm_generated_title_names_l_{language}.yml"
    )


def rendered_localization_text(language: str) -> str:
    if language not in LANGUAGES:
        raise ValueError(f"unsupported language: {language}")
    lines = [
        f"l_{language}:",
    ]
    lines.extend(
        f' rmtm_later_{key}:0 "$rmtm_restoration_title_prefix$${key}$"'
        for key in TITLE_KEYS
    )
    lines.append("")
    return "\n".join(lines)


def rendered_localization_bytes(language: str) -> bytes:
    return codecs.BOM_UTF8 + rendered_localization_text(language).encode("utf-8")


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(rendered_bytes())
    for language in LANGUAGES:
        path = localization_output(language)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(rendered_localization_bytes(language))
    print(
        f"Wrote {OUTPUT} and {len(LANGUAGES)} localization projections "
        f"({len(TITLE_KEYS)} pinned vanilla title names)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Generate the first native content package from the authored catalogue.

This generator emits eight rite definitions, their fifteen core tenets and
Chinese/English localization. It never generates a faith override, history,
events, effects, triggers, decisions, or gameplay acceptance evidence.
"""

from __future__ import annotations

import argparse
import codecs
import json
from pathlib import Path

from content_data import (
    GAME_VERSION,
    MAIN_RITE_ID,
    PARENT_FAITH,
    PARENT_RELIGION,
    PRACTICES,
    RITES,
    SAMPLE_RITES,
    SAMPLE_TENETS,
    TENETS,
    validate_catalogue,
)

MOD_ROOT = Path(__file__).resolve().parents[1]
GENERATED_HEADER = "# GENERATED FILE — edit tools/content_data.py and rerun tools/gen_content.py."
TENET_DIVERGENCE_MULTIPLIER = "0.1"


def render_rites() -> str:
    lines = [
        GENERATED_HEADER,
        f"# CK3 {GAME_VERSION}; additive sample types only. No vanilla IDs are overridden.",
        "# Free chronology prototype. Native creation/conversion requires live verification.",
        "# convert=yes permits actual admission; product actions remain guarded player entries.",
        "",
    ]
    for rite in SAMPLE_RITES:
        color = " ".join(str(channel) for channel in rite.color)
        lines.extend([
            f"# {rite.code}: {rite.name_en}; kind={rite.kind}; era={rite.era}",
            f"{rite.script_id} = {{",
            f"\tname = {rite.script_id}",
            f"\tdesc = {rite.script_id}_desc",
            f"\tfaith = {PARENT_FAITH}",
            "\tcreate = yes",
            "\tconvert = yes",
            f"\tcolor = {{ {color} }}",
            f"\ticon = {rite.icon}",
            "\ttenets = {",
        ])
        tenets_by_code = {tenet.code: tenet for tenet in SAMPLE_TENETS}
        lines.extend(f"\t\t{tenets_by_code[code].script_id}" for code in rite.tenet_codes)
        lines.extend(["\t}", "}", ""])
    return "\n".join(lines)


def render_tenets() -> str:
    lines = [
        GENERATED_HEADER,
        f"# CK3 {GAME_VERSION}; additive sample tenets. No all-character modifiers.",
        "# Faith selection uses Faith scope. Personal selection has Character scope.",
        "# Faith can_pick has no unguarded is_ai check: its actor can be null.",
        "# Parameters are capability flags, not proof that practice events are connected.",
        "# Local divergence scaling is a prototype input; global defines are untouched.",
        "",
    ]
    for tenet in SAMPLE_TENETS:
        lines.extend([
            f"# {tenet.code}: {tenet.name_en}",
            f"{tenet.script_id} = {{",
            f"\ticon = {tenet.icon}",
            "\tvisible = yes",
            f"\tdivergence_multiplier = {TENET_DIVERGENCE_MULTIPLIER}",
            "\tpiety_cost = { value = faith_tenet_cost_low }",
            "\tis_shown = {",
            f"\t\treligion = religion:{PARENT_RELIGION}",
            "\t}",
            "\tcan_pick = {",
            f"\t\treligion = religion:{PARENT_RELIGION}",
            "\t}",
            "\tcan_pick_as_personal_tenet = {",
            "\t\tis_ai = no",
            f"\t\treligion = religion:{PARENT_RELIGION}",
            "\t}",
            "\tparameters = {",
            f"\t\t{tenet.parameter_id}",
            "\t}",
            "\tpersonal_tenet_parameters = {",
            f"\t\t{tenet.parameter_id}",
            "\t}",
            "}",
            "",
        ])
    return "\n".join(lines)


def _quote_localization(value: str) -> str:
    if any(char in value for char in ("\r", "\n", "\x00")):
        raise ValueError("Localization values must be single lines")
    return value.replace("\\", "\\\\").replace('"', '\\"')


def localization_entries(language: str) -> dict[str, str]:
    if language not in {"simp_chinese", "english"}:
        raise ValueError(f"Unsupported content language: {language}")
    zh = language == "simp_chinese"
    entries: dict[str, str] = {}

    def put(key: str, value: str) -> None:
        if key in entries:
            raise ValueError(f"Duplicate generated localization: {key}")
        entries[key] = value

    for rite in SAMPLE_RITES:
        name = rite.name_zh if zh else rite.name_en
        put(rite.script_id, name)
        put(f"{rite.script_id}_adj", name)
        put(f"{rite.script_id}_adherent", f"{name}之儒" if zh else f"Follower of {name}")
        put(f"{rite.script_id}_adherent_plural", f"{name}诸儒" if zh else f"Followers of {name}")
        put(f"{rite.script_id}_desc", rite.history_zh if zh else rite.history_en)

    for tenet in SAMPLE_TENETS:
        put(f"{tenet.script_id}_name", tenet.name_zh if zh else tenet.name_en)
        belief = tenet.belief_zh if zh else tenet.belief_en
        practice = tenet.practice_zh if zh else tenet.practice_en
        put(f"{tenet.script_id}_desc", f"{belief} {practice}")
        put(f"doctrine_parameter_{tenet.parameter_id}", practice)

    for practice in PRACTICES:
        put(f"{practice.script_id}_t", practice.title_zh if zh else practice.title_en)
        put(f"{practice.script_id}_desc", practice.desc_zh if zh else practice.desc_en)
        for option in practice.options:
            key = f"{practice.script_id}_{option.key}"
            put(key, option.label_zh if zh else option.label_en)
            put(f"{key}_tt", option.tooltip_zh if zh else option.tooltip_en)
    return entries


def render_localization(language: str) -> str:
    lines = [f"l_{language}:", f" {GENERATED_HEADER}"]
    for key, value in localization_entries(language).items():
        lines.append(f' {key}:0 "{_quote_localization(value)}"')
    return "\n".join(lines) + "\n"


def build_outputs() -> dict[str, bytes]:
    """Return deterministic UTF-8-BOM production text for this package only."""
    validate_catalogue()
    contents = {
        "common/religion/rite_types/lyd_rites.txt": render_rites(),
        "common/religion/tenet_types/lyd_tenets.txt": render_tenets(),
        "localization/simp_chinese/lyd_content_l_simp_chinese.yml": render_localization("simp_chinese"),
        "localization/english/lyd_content_l_english.yml": render_localization("english"),
    }
    return {name: codecs.BOM_UTF8 + text.encode("utf-8") for name, text in contents.items()}


def summary() -> dict[str, object]:
    return {
        "catalogue_rites": len(RITES),
        "catalogue_tenets": len(TENETS),
        "emitted_rites": len(SAMPLE_RITES),
        "emitted_tenets": len(SAMPLE_TENETS),
        "practice_inputs": len(PRACTICES),
        "parent_faith": PARENT_FAITH,
        "parent_religion": PARENT_RELIGION,
        "main_rite_id": MAIN_RITE_ID,
        "chronology_mode": "free",
        "live_acceptance": "not performed by content generator",
    }


def generate_content(output_dir: Path = MOD_ROOT, *, check: bool = False) -> list[str]:
    generated = build_outputs()
    mismatches = []
    for relative, expected in generated.items():
        target = output_dir / relative
        if check:
            if not target.is_file() or target.read_bytes() != expected:
                mismatches.append(relative)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(expected)
    if mismatches:
        raise ValueError("Generated content differs: " + ", ".join(mismatches))
    return list(generated)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check exact generated bytes without writing")
    parser.add_argument("--output", type=Path, default=MOD_ROOT, help="Mod output root (default: this mod)")
    args = parser.parse_args()
    try:
        paths = generate_content(args.output.resolve(), check=args.check)
    except ValueError as error:
        parser.exit(1, f"content generation failed: {error}\n")
    print(json.dumps({**summary(), "mode": "check" if args.check else "write", "files": paths}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

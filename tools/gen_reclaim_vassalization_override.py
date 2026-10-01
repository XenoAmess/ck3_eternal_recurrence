#!/usr/bin/env python3
"""Generate RMTM's private offer-vassalization path from exact CK3 1.20 sources."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import reclaim_the_motherland_vanilla_contract as native
from reclaim_the_motherland_vanilla_contract import extract_definition, replace_once, sha256_bytes

ROOT = native.ROOT
DEFAULT_GAME_SOURCE = native.GAME / native.CONTRACT["paths"]["interaction"]
OUTPUT = ROOT / "mod_reclaim_the_motherland/common/character_interactions/zz_rmtm_offer_vassalization.txt"
MODIFIERS_OUTPUT = ROOT / "mod_reclaim_the_motherland/common/scripted_modifiers/zz_rmtm_offer_vassalization_modifiers.txt"
DEFINITION = "offer_vassalization_interaction"
GENERAL = "offer_vassalization_interaction_ai_acceptance_general"
DIPLOMACY = "offer_vassalization_interaction_ai_acceptance_diplomacy"
PRIVATE_GENERAL = "rmtm_" + GENERAL
PRIVATE_DIPLOMACY = "rmtm_" + DIPLOMACY
SOURCE_SHA256 = native.CONTRACT["files"][native.CONTRACT["paths"]["interaction"]]
VANILLA_INTERACTION_SHA256 = native.CONTRACT["definitions"][DEFINITION]["normalized_text_sha256"]

HIGH_TIER_VANILLA = """\
\t\t\tNAND = {
\t\t\t\tscope:actor = {
\t\t\t\t\tgovernment_has_flag = government_is_celestial
\t\t\t\t\thighest_held_title_tier >= tier_hegemony
\t\t\t\t}
\t\t\t\tscope:recipient = {
\t\t\t\t\tgovernment_has_flag = government_is_celestial
\t\t\t\t}
\t\t\t}
"""
HIGH_TIER_RMTM = """\
\t\t\tOR = {
\t\t\t\tscope:actor = {
\t\t\t\t\trmtm_primary_title_is_restoration_hegemony_trigger = yes
\t\t\t\t}
""" + "\n".join("\t" + row for row in HIGH_TIER_VANILLA.splitlines()) + "\n\t\t\t}\n"

RECENT_WAR_VANILLA = "\tmodifier = { #I fought an independence war against you.\n"
RECENT_WAR_RMTM = """\
\tmodifier = { # Recently became independent from this Later Dynasty.
\t\tdesc = rmtm_offer_vassalization_recently_independent_tt
\t\ttrigger = {
\t\t\tscope:recipient = {
\t\t\t\tprimary_title = {
\t\t\t\t\texists = var:rmtm_recently_independent_from_restoration_hegemony
\t\t\t\t\tvar:rmtm_recently_independent_from_restoration_hegemony = {
\t\t\t\t\t\thas_variable = rmtm_restoration_hegemony
\t\t\t\t\t\tholder = scope:actor
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t}
\t\tadd = -50
\t}
""" + RECENT_WAR_VANILLA

NORMAL_RANK_VANILLA = """\
\t\t\tmultiply = {
\t\t\t\tvalue = scope:actor.highest_held_title_tier
\t\t\t\tsubtract = scope:recipient.highest_held_title_tier
\t\t\t\tsubtract = 1
\t\t\t}
"""
NORMAL_RANK_RMTM = """\
\t\t\tif = {
\t\t\t\tlimit = {
\t\t\t\t\tscope:actor = {
\t\t\t\t\t\tNOT = { rmtm_primary_title_is_restoration_hegemony_trigger = yes }
\t\t\t\t\t}
\t\t\t\t}
""" + "\n".join("\t" + row for row in NORMAL_RANK_VANILLA.splitlines()) + "\n\t\t\t}\n"

CELESTIAL_RANK_VANILLA = """\
\t\t\t\t\tscope:actor = {
\t\t\t\t\t\tgovernment_has_flag = government_is_celestial
\t\t\t\t\t}
\t\t\t\t\tscope:recipient = {
"""
CELESTIAL_RANK_RMTM = """\
\t\t\t\t\tscope:actor = {
\t\t\t\t\t\tgovernment_has_flag = government_is_celestial
\t\t\t\t\t\tNOT = { rmtm_primary_title_is_restoration_hegemony_trigger = yes }
\t\t\t\t\t}
\t\t\t\t\tscope:recipient = {
"""
HEGEMONY_VANILLA = "\t\t\tscope:actor = { highest_held_title_tier = tier_hegemony }\n"
HEGEMONY_RMTM = """\
\t\t\tscope:actor = {
\t\t\t\thighest_held_title_tier = tier_hegemony
\t\t\t\tNOT = { rmtm_primary_title_is_restoration_hegemony_trigger = yes }
\t\t\t}
"""
PROJECTIONS = (
    (HIGH_TIER_VANILLA, HIGH_TIER_RMTM, "high-tier refusal exemption"),
    (RECENT_WAR_VANILLA, RECENT_WAR_RMTM, "five-year independence modifier"),
    (NORMAL_RANK_VANILLA, NORMAL_RANK_RMTM, "fixed Later Dynasty rank bonus"),
    (CELESTIAL_RANK_VANILLA, CELESTIAL_RANK_RMTM, "celestial rank multiplier"),
    (HEGEMONY_VANILLA, HEGEMONY_RMTM, "generic hegemony bonus"),
)


def project(vanilla_interaction: str) -> str:
    native.assert_definition(vanilla_interaction, DEFINITION)
    return replace_once(vanilla_interaction, f"{GENERAL} = yes", f"{PRIVATE_GENERAL} = yes", "private general call")


def project_general(body: str) -> str:
    native.assert_definition(body, GENERAL)
    body = replace_once(body, f"{GENERAL} = {{", f"{PRIVATE_GENERAL} = {{", "general definition name")
    return replace_once(body, f"{DIPLOMACY} = yes", f"{PRIVATE_DIPLOMACY} = yes", "private diplomacy call")


def project_diplomacy(body: str) -> str:
    native.assert_definition(body, DIPLOMACY)
    body = replace_once(body, f"{DIPLOMACY} = {{", f"{PRIVATE_DIPLOMACY} = {{", "diplomacy definition name")
    for old, new, label in PROJECTIONS:
        body = replace_once(body, old, new, label)
    return body


def generated_payloads(source_path: Path = DEFAULT_GAME_SOURCE) -> dict[Path, bytes]:
    source_path = Path(source_path)
    # The seven-file contract also binds delegates, thresholds and government flags.
    game = source_path.parents[2]
    native.assert_source_files(game)
    interaction = project(native.definition(DEFINITION, game))
    general = project_general(native.definition(GENERAL, game))
    diplomacy = project_diplomacy(native.definition(DIPLOMACY, game))
    note = "Private offer path only; Later Dynasties use fixed +10 and lose celestial/hegemony perks; title-bound recent independence is -50."
    return {
        OUTPUT: b"\xef\xbb\xbf" + (native.header((DEFINITION,), "Only the general acceptance call is redirected.") + interaction).encode("utf-8"),
        MODIFIERS_OUTPUT: b"\xef\xbb\xbf" + (native.header((GENERAL, DIPLOMACY), note) + general + "\n" + diplomacy).encode("utf-8"),
    }


def rendered_bytes(source_path: Path = DEFAULT_GAME_SOURCE) -> bytes:
    return generated_payloads(source_path)[OUTPUT]


def validate_committed_projection(data: bytes, modifiers_data: bytes | None = None) -> list[str]:
    try:
        if not data.startswith(b"\xef\xbb\xbf"):
            raise ValueError("generated interaction override lacks UTF-8 BOM")
        body = extract_definition(data.decode("utf-8-sig"), DEFINITION)
        restored = replace_once(body, f"{PRIVATE_GENERAL} = yes", f"{GENERAL} = yes", "restore general call")
        native.assert_definition(restored, DEFINITION)
        if modifiers_data is None:
            modifiers_data = MODIFIERS_OUTPUT.read_bytes()
        if not modifiers_data.startswith(b"\xef\xbb\xbf"):
            raise ValueError("generated modifiers lack UTF-8 BOM")
        text = modifiers_data.decode("utf-8-sig")
        general = extract_definition(text, PRIVATE_GENERAL)
        general = replace_once(general, f"{PRIVATE_GENERAL} = {{", f"{GENERAL} = {{", "restore general name")
        general = replace_once(general, f"{PRIVATE_DIPLOMACY} = yes", f"{DIPLOMACY} = yes", "restore diplomacy call")
        native.assert_definition(general, GENERAL)
        diplomacy = extract_definition(text, PRIVATE_DIPLOMACY)
        for old, new, label in reversed(PROJECTIONS):
            diplomacy = replace_once(diplomacy, new, old, "restore " + label)
        diplomacy = replace_once(diplomacy, f"{PRIVATE_DIPLOMACY} = {{", f"{DIPLOMACY} = {{", "restore diplomacy name")
        native.assert_definition(diplomacy, DIPLOMACY)
    except (ValueError, OSError) as error:
        return [str(error)]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_GAME_SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--modifiers-output", type=Path, default=MODIFIERS_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payloads = generated_payloads(args.source)
    outputs = {OUTPUT: args.output, MODIFIERS_OUTPUT: args.modifiers_output}
    for path, expected in payloads.items():
        target = outputs[path]
        if args.check:
            if not target.is_file() or target.read_bytes() != expected:
                print(f"stale generated RMTM offer projection: {target}", file=sys.stderr)
                return 1
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(expected)
    print("RMTM PRIVATE VASSALIZATION PROJECTIONS OK" if args.check else "Wrote two RMTM private offer projections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate the narrow RMTM projection of vanilla offer-vassalization logic."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GAME_SOURCE = Path(
    r"C:\SteamLibrary\steamapps\common\Crusader Kings III\game\common"
    r"\character_interactions\00_character_interactions.txt"
)
OUTPUT = (
    ROOT
    / "mod_reclaim_the_motherland/common/character_interactions"
    / "zz_rmtm_offer_vassalization.txt"
)
SOURCE_SHA256 = "FDB0C52F8A3C0D03C0974D4F0916831B38BE47841C7DF1215FB44BDE0BB05D89"
VANILLA_INTERACTION_SHA256 = (
    "66713B5820CEAC2BF14810DE35D61B1B2737503D5720DC4843B0DAB060FE2E6B"
)
DEFINITION = "offer_vassalization_interaction"

HIGH_TIER_VANILLA = """\
\t\t\ttrigger = {
\t\t\t\tNAND = {
\t\t\t\t\tscope:actor = {
\t\t\t\t\t\tgovernment_has_flag = government_is_celestial
\t\t\t\t\t\thighest_held_title_tier >= tier_hegemony
\t\t\t\t\t}
\t\t\t\t\tscope:recipient = {
\t\t\t\t\t\tgovernment_has_flag = government_is_celestial
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tscope:recipient = { highest_held_title_tier >= tier_kingdom }
\t\t\t}
"""
HIGH_TIER_RMTM = """\
\t\t\ttrigger = {
\t\t\t\tOR = {
\t\t\t\t\tscope:actor = {
\t\t\t\t\t\trmtm_primary_title_is_restoration_hegemony_trigger = yes
\t\t\t\t\t}
\t\t\t\t\tNAND = {
\t\t\t\t\t\tscope:actor = {
\t\t\t\t\t\t\tgovernment_has_flag = government_is_celestial
\t\t\t\t\t\t\thighest_held_title_tier >= tier_hegemony
\t\t\t\t\t\t}
\t\t\t\t\t\tscope:recipient = {
\t\t\t\t\t\t\tgovernment_has_flag = government_is_celestial
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tscope:recipient = { highest_held_title_tier >= tier_kingdom }
\t\t\t}
"""

RECENT_WAR_VANILLA = """\
\t\t\tadd = -50
\t\t}
\t\tmodifier = { #I fought an independence war against you.
"""
RECENT_WAR_RMTM = """\
\t\t\tadd = -50
\t\t}
\t\tmodifier = { # Recently became independent from this Later Dynasty.
\t\t\tdesc = rmtm_offer_vassalization_recently_independent_tt
\t\t\ttrigger = {
\t\t\t\tscope:recipient = {
\t\t\t\t\tprimary_title = {
\t\t\t\t\t\texists = var:rmtm_recently_independent_from_restoration_hegemony
\t\t\t\t\t\tvar:rmtm_recently_independent_from_restoration_hegemony = {
\t\t\t\t\t\t\thas_variable = rmtm_restoration_hegemony
\t\t\t\t\t\t\tholder = scope:actor
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t\tadd = -50
\t\t}
\t\tmodifier = { #I fought an independence war against you.
"""

NORMAL_RANK_VANILLA = """\
\t\t\t\t\tOR = {
\t\t\t\t\t\tNOT = { government_has_flag = government_is_celestial }
\t\t\t\t\t\tscope:recipient = {
\t\t\t\t\t\t\tNOT = { government_has_flag = government_is_celestial }
\t\t\t\t\t\t}
\t\t\t\t\t}
"""
NORMAL_RANK_RMTM = """\
\t\t\t\t\tOR = {
\t\t\t\t\t\tNOT = { government_has_flag = government_is_celestial }
\t\t\t\t\t\trmtm_primary_title_is_restoration_hegemony_trigger = yes
\t\t\t\t\t\tscope:recipient = {
\t\t\t\t\t\t\tNOT = { government_has_flag = government_is_celestial }
\t\t\t\t\t\t}
\t\t\t\t\t}
"""

CELESTIAL_RANK_VANILLA = """\
\t\t\t\tscope:actor = {
\t\t\t\t\tgovernment_has_flag = government_is_celestial
\t\t\t\t\ttier_difference = {
"""
CELESTIAL_RANK_RMTM = """\
\t\t\t\tscope:actor = {
\t\t\t\t\tgovernment_has_flag = government_is_celestial
\t\t\t\t\tNOT = { rmtm_primary_title_is_restoration_hegemony_trigger = yes }
\t\t\t\t\ttier_difference = {
"""

HEGEMONY_VANILLA = """\
\t\t\ttrigger = {
\t\t\t\tscope:actor = { highest_held_title_tier = tier_hegemony }
\t\t\t}
"""
HEGEMONY_RMTM = """\
\t\t\ttrigger = {
\t\t\t\tscope:actor = {
\t\t\t\t\thighest_held_title_tier = tier_hegemony
\t\t\t\t\tNOT = { rmtm_primary_title_is_restoration_hegemony_trigger = yes }
\t\t\t\t}
\t\t\t}
"""

PROJECTIONS = (
    (HIGH_TIER_VANILLA, HIGH_TIER_RMTM, "high-tier refusal exemption"),
    (RECENT_WAR_VANILLA, RECENT_WAR_RMTM, "five-year independence modifier"),
    (NORMAL_RANK_VANILLA, NORMAL_RANK_RMTM, "normal rank bonus"),
    (CELESTIAL_RANK_VANILLA, CELESTIAL_RANK_RMTM, "celestial rank bonus"),
    (HEGEMONY_VANILLA, HEGEMONY_RMTM, "generic hegemony bonus"),
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def extract_definition(source: str, name: str = DEFINITION) -> str:
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    marker = f"{name} = {{"
    start = source.find(marker)
    if start < 0:
        raise ValueError(f"definition not found: {name}")
    brace = source.find("{", start)
    depth = 0
    quoted = False
    escaped = False
    in_comment = False
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
                return source[start : index + 1] + "\n"
    raise ValueError(f"unterminated definition: {name}")


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"{label} anchor count is {count}, expected exactly 1")
    return source.replace(old, new, 1)


def project(vanilla_interaction: str) -> str:
    digest = sha256_bytes(vanilla_interaction.encode("utf-8"))
    if digest != VANILLA_INTERACTION_SHA256:
        raise ValueError(
            f"vanilla interaction body SHA-256 changed: {digest}; "
            f"expected {VANILLA_INTERACTION_SHA256}"
        )
    result = vanilla_interaction
    for old, new, label in PROJECTIONS:
        result = replace_once(result, old, new, label)
    return result


def rendered_bytes(source_path: Path = DEFAULT_GAME_SOURCE) -> bytes:
    raw = Path(source_path).read_bytes()
    digest = sha256_bytes(raw)
    if digest != SOURCE_SHA256:
        raise ValueError(
            f"vanilla interaction file SHA-256 changed: {digest}; expected {SOURCE_SHA256}"
        )
    source = raw.decode("utf-8-sig")
    body = project(extract_definition(source))
    header = (
        "# GENERATED FILE. DO NOT EDIT.\n"
        f"# Vanilla file SHA-256: {SOURCE_SHA256}\n"
        f"# Vanilla {DEFINITION} SHA-256: {VANILLA_INTERACTION_SHA256}\n"
        "# Projection: Later Dynasties lose four h_china identity branches and "
        "their recent breakaways receive -50 for five years.\n\n"
    )
    return b"\xef\xbb\xbf" + (header + body).encode("utf-8")


def validate_committed_projection(data: bytes) -> list[str]:
    errors: list[str] = []
    if not data.startswith(b"\xef\xbb\xbf"):
        return ["generated interaction override lacks UTF-8 BOM"]
    value = data.decode("utf-8-sig")
    try:
        body = extract_definition(value)
    except ValueError as error:
        return [str(error)]
    restored = body
    for old, new, label in reversed(PROJECTIONS):
        count = restored.count(new)
        if count != 1:
            errors.append(f"generated {label} projection count is {count}, expected 1")
        else:
            restored = restored.replace(new, old, 1)
    digest = sha256_bytes(restored.encode("utf-8"))
    if digest != VANILLA_INTERACTION_SHA256:
        errors.append(
            f"restored vanilla interaction SHA-256 is {digest}, "
            f"expected {VANILLA_INTERACTION_SHA256}"
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_GAME_SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    expected = rendered_bytes(args.source)
    if args.check:
        if not args.output.is_file() or args.output.read_bytes() != expected:
            print(f"stale generated interaction override: {args.output}", file=sys.stderr)
            return 1
        print(f"RMTM VASSALIZATION OVERRIDE OK: {args.output}")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(expected)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

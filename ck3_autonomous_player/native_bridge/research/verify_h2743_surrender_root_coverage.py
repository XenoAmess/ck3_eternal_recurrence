"""Fail-closed source/root inventory for H2743 defender surrender.

This checks source identity and two required script roots. It deliberately does
not evaluate effects or certify an exit decision. No game process is touched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


GAME_FILES = {
    "cb": ("common/casus_belli_types/00_dejure_war.txt", "D8737A2205116118A5ECD6EFA576D316B3155730A3824DC4BD109A68B9D5B6EE"),
    "war_on_actions": ("common/on_action/war_on_actions.txt", "49AB57BF4A7C4EC3E6E3B430AB437C005C5084C43B838A57C8F55267E8F11B0F"),
    "truce_effects": ("common/scripted_effects/00_war_effects.txt", "A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D"),
    "truce_values": ("common/script_values/00_war_values.txt", "ED1CDB6E8BC887CF1FFFE010F1E9CA642DFD6DAF241E81F23E6B4736F7AFDF3B"),
    "fp2_effects": ("common/scripted_effects/03_dlc_fp2_scripted_effects.txt", "366469115EA2DED577B5DEB57DFD456340A1E2FA2D494DC2B20C36CB3FC5A710"),
    "ep3_effects": ("common/scripted_effects/07_dlc_ep3_scripted_effects.txt", "D2F5FE80E7BC000A749642CD26BDE1626DBEA7409C39314B8583547AE43DB43D"),
}

REQUIRED_ROOTS = frozenset({"cb_on_victory", "on_war_won_attacker"})
CB_EDGES = (
    "create_title_and_vassal_change", "setup_de_jure_cb",
    "resolve_title_and_vassal_change", "modify_all_participants_fame_values",
    "add_truce_attacker_victory_effect", "laamp_as_mercenary_payout_tooltip_effect",
    "mandala_war_victory_effects",
)
WAR_EDGES = (
    "fp2_contract_assistance_war_pay_effect", "war_task_contracts_completion_effect",
    "laamp_as_mercenary_payout_effect", "ep3_admin_war_aftermath_effect",
    "allies_progress_towards_friendship_effect",
    "mpo_save_potential_blood_brother_war_allies_effect",
)


class CoverageError(ValueError):
    pass


def extract_block(source: str, key: str) -> str:
    """Extract an exact-key script block, ignoring braces in comments/quotes."""
    match = re.search(r"(?m)^\s*" + re.escape(key) + r"\s*=\s*\{", source)
    if match is None:
        raise CoverageError(f"missing script block: {key}")
    start = source.index("{", match.start(), match.end())
    depth = 0
    quoted = False
    comment = False
    escaped = False
    for index in range(start, len(source)):
        char = source[index]
        if comment:
            if char == "\n":
                comment = False
            continue
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == "#":
            comment = True
        elif char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[match.start():index + 1]
    raise CoverageError(f"unterminated script block: {key}")


def require_edges(block: str, names: tuple[str, ...], label: str) -> None:
    for name in names:
        if not re.search(r"(?m)^\s*" + re.escape(name) + r"\s*=", block):
            raise CoverageError(f"{label} missing required edge: {name}")


def validate_claimed_roots(claimed_roots: set[str] | frozenset[str]) -> None:
    if claimed_roots != REQUIRED_ROOTS:
        raise CoverageError(
            "required root coverage mismatch: "
            f"missing={sorted(REQUIRED_ROOTS - claimed_roots)}, "
            f"unexpected={sorted(claimed_roots - REQUIRED_ROOTS)}"
        )


def verify(game_root: Path, claimed_roots: set[str] | frozenset[str]) -> dict:
    validate_claimed_roots(claimed_roots)
    sources = {}
    actual_hashes = {}
    for key, (relative, expected_hash) in GAME_FILES.items():
        source_bytes = (game_root / relative).read_bytes()
        actual_hash = hashlib.sha256(source_bytes).hexdigest().upper()
        if actual_hash != expected_hash:
            raise CoverageError(f"source SHA-256 mismatch: {relative}: {actual_hash}")
        sources[key] = source_bytes.decode("utf-8-sig")
        actual_hashes[relative] = actual_hash

    cb = extract_block(sources["cb"], "individual_county_de_jure_cb")
    cb_victory = extract_block(cb, "on_victory")
    war_won = extract_block(sources["war_on_actions"], "on_war_won_attacker")
    same_tick_effect = extract_block(war_won, "effect")
    fp2 = extract_block(sources["fp2_effects"], "fp2_contract_assistance_war_pay_effect")
    ep3 = extract_block(sources["ep3_effects"], "laamp_as_mercenary_payout_effect")
    truce_effect = extract_block(sources["truce_effects"], "add_truce_attacker_victory_effect")
    truce_call = extract_block(truce_effect, "add_truce_one_way")
    truce_days = extract_block(sources["truce_values"], "standard_truce_duration_days")
    require_edges(cb_victory, CB_EDGES, "CB on_victory")
    require_edges(same_tick_effect, WAR_EDGES, "on_war_won_attacker effect")
    require_edges(fp2, ("pay_short_term_gold",), "FP2 contract assistance")
    payment_positions = [match.start() for match in re.finditer(r"(?m)^\s*pay_short_term_gold\s*=", fp2)]
    tooltip_position = fp2.find("show_as_tooltip = {")
    if len(payment_positions) != 2 or not (payment_positions[0] < tooltip_position < payment_positions[1]):
        raise CoverageError("FP2 real payment / tooltip-only mirror placement changed")
    require_edges(ep3, ("trigger_event",), "EP3 mercenary payout")
    for statement in (
        "character = scope:defender", "days = standard_truce_duration_days",
        "war = root.war", "result = victory",
    ):
        if statement not in truce_call:
            raise CoverageError(f"attacker-victory truce call changed: {statement}")
    for statement in (
        "has_perk = flexible_truces_perk",
        "PARAMETER = truces_by_involved_or_interlopers_within_region_shorter",
        "PARAMETER = truces_by_involved_or_interlopers_within_region_longer",
        "government_has_flag = government_is_nomadic",
        "min = 730", "using_cb = fp2_border_raid", "multiply = 2",
    ):
        if statement not in truce_days:
            raise CoverageError(f"standard truce formula changed: {statement}")
    timing = sources["war_on_actions"]
    for statement in ("`effect` fires on THIS tick", "`events` fires on the NEXT tick", "war gets destroyed between this tick and the next"):
        if statement not in timing:
            raise CoverageError(f"missing on_action timing source statement: {statement}")
    return {
        "status": "known_script_roots_bound_only",
        "source_sha256": actual_hashes,
        "root_sha256": {
            "cb_on_victory": hashlib.sha256(cb_victory.encode()).hexdigest().upper(),
            "on_war_won_attacker": hashlib.sha256(war_won.encode()).hexdigest().upper(),
        },
        "required_roots": sorted(REQUIRED_ROOTS),
        "all_enabled_roots_known": False,
        "effect_projection_complete": False,
        "full_write_set_known": False,
        "actual_dlc_branches_observed": False,
        "signed_resource_delta_known": False,
        "title_vassal_delta_known": False,
        "directed_truce_days_known": False,
        "delayed_event_outcomes_known": False,
        "recommended_outcome": None,
        "action_literal": None,
        "unresolved": [
            "native setup_de_jure_cb and resolve_title_and_vassal_change data projection",
            "same-frame CB context, target scope, factor F, participants, and branch predicates",
            "native war-end dispatch order and all enabled DLC/mod on_action roots",
            "FP2 contract-assistance variables, contribution threshold and real gold transfer",
            "standard-truce short/long/border-raid predicates and native expiry persistence",
            "RNG, pending next-tick/delayed events, and post-destruction war context",
            "complete recipient write set and signed per-character/title/house delta",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, default=Path("C:/SteamLibrary/steamapps/common/Crusader Kings III/game"))
    parser.add_argument("--claimed-root", action="append", choices=sorted(REQUIRED_ROOTS))
    args = parser.parse_args()
    claimed = set(args.claimed_root) if args.claimed_root is not None else set(REQUIRED_ROOTS)
    try:
        result = verify(args.game_root, claimed)
    except (OSError, UnicodeError, CoverageError) as error:
        print(json.dumps({"status": "RED", "reason": str(error), "effect_projection_complete": False}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

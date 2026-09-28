"""Read-only, exact-build script envelope for the H2743 defender surrender.

This projection reports script components and missing live inputs. It never
evaluates a CK3 effect, launches the game, or supplies an action candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


GAME = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III")
ROOT = Path(__file__).resolve().parents[3]
FRAME = ROOT / "docs/autonomous-agent-progress/coordination/war-requests/evidence/WAR-ROBERT-H2743-EXIT-20260928.local-h2743-options.json"
EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
FRAME_SHA = "CAFA45C85F6F80BF71C155AB6D4C553D698CA33D47F82AC2FFC5B587FB0F137E"
SCRIPT_SHA = {
    "casus_belli_types/00_dejure_war.txt": "D8737A2205116118A5ECD6EFA576D316B3155730A3824DC4BD109A68B9D5B6EE",
    "scripted_effects/00_casus_belli_effects.txt": "9F7C77CC9342B1197B1C802A2D465E56F7521458B103DEC84F5EB7222E45F18C",
    "scripted_effects/00_war_effects.txt": "A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D",
    "script_values/00_war_values.txt": "ED1CDB6E8BC887CF1FFFE010F1E9CA642DFD6DAF241E81F23E6B4736F7AFDF3B",
    "scripted_effects/06_dlc_ce1_legitimacy_effects.txt": "DEE9D48221B49EF41490D04451ACD6DBFD4994A50EAD9D006F831F41A6247A83",
    "scripted_effects/07_dlc_ep3_scripted_effects.txt": "D2F5FE80E7BC000A749642CD26BDE1626DBEA7409C39314B8583547AE43DB43D",
    "scripted_effects/tgp_mandala_scripted_effects.txt": "10B2C2C0E317D66F13237069064BC98267EBC7D75928F1AAD4E15397D2383A1B",
}


def _block(source: str, name: str) -> str:
    starts = list(re.finditer(rf"(?m)^\s*{re.escape(name)}\s*=\s*\{{", source))
    if len(starts) != 1:
        raise ValueError(f"expected one {name} block, found {len(starts)}")
    opening = source.index("{", starts[0].start())
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1 : index]
    raise ValueError(f"unterminated {name} block")


def _read_exact(path: Path, sha: str) -> bytes:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != sha:
        raise ValueError(f"exact source SHA mismatch: {path.name}")
    return data


def _requires(text: str, *parts: str) -> None:
    for part in parts:
        if part not in text:
            raise ValueError(f"script structure changed: {part}")


def project(game_dir: Path = GAME, frame_path: Path = FRAME) -> dict[str, object]:
    _read_exact(game_dir / "binaries/ck3.exe", EXE_SHA)
    source = {
        name: _read_exact(game_dir / "game/common" / name, sha).decode("utf-8-sig")
        for name, sha in SCRIPT_SHA.items()
    }
    raw_frame = _read_exact(frame_path, FRAME_SHA)
    evidence = json.loads(raw_frame)
    frame = evidence["frame"]
    option = evidence["native_options"]["surrender"]
    if (
        frame["war_id"] != 16777231
        or frame["actor_character_id"] != 29829
        or frame["primary_opponent_character_id"] != 30097
        or frame["player_side"] != "defender"
        or frame["targeted_title_ids"] != [2128]
        or frame["casus_belli"]["canonical_key"] != "individual_county_de_jure_cb"
        or frame["casus_belli"]["database_index"] != 17
        or option["outcome"] != "attacker_victory"
        or not option["available"]
        or not option["native_validator_passed"]
        or not option["recipient_would_accept_now"]
        or option["terms_observable"]
    ):
        raise ValueError("H2743 frame is not the frozen available defender-surrender observation")

    cb = _block(source["casus_belli_types/00_dejure_war.txt"], "individual_county_de_jure_cb")
    victory = _block(cb, "on_victory")
    _requires(
        victory,
        "add_legitimacy_attacker_victory_effect = yes",
        "add_hook_from_temp_de_jure_liege_to_attacker = yes",
        "create_title_and_vassal_change = {",
        "setup_de_jure_cb = {",
        "resolve_title_and_vassal_change = scope:change",
        "FAME_BASE = scope:cb_prestige_factor",
        "WINNER_FAME_SCALE = 10",
        "LOSER_FAME_SCALE = -10",
        "IS_RELIGIOUS_WAR = no",
        "add_truce_attacker_victory_effect = yes",
        "laamp_as_mercenary_payout_tooltip_effect = yes",
        "mandala_war_victory_effects = yes",
    )
    fame = _block(source["scripted_effects/00_casus_belli_effects.txt"], "modify_all_participants_fame_values")
    _requires(fame, "add_prestige_experience = {", "max = @maximum_prestige_winner", "add_prestige = {", "min = @minimum_prestige_loser")
    _requires(source["scripted_effects/00_casus_belli_effects.txt"], "@maximum_prestige_winner = 1000", "@minimum_prestige_loser = -1000")
    _requires(source["scripted_effects/06_dlc_ce1_legitimacy_effects.txt"], "war_end_legitimacy_effect = {", "is_valid_for_legitimacy_change = yes", "add_legitimacy = {")
    _requires(source["scripted_effects/07_dlc_ep3_scripted_effects.txt"], "laamp_as_mercenary_payout_tooltip_effect = {", "pay_short_term_gold = {")
    _requires(source["scripted_effects/tgp_mandala_scripted_effects.txt"], "mandala_war_victory_effects = {", "has_realm_law_flag = piety_devotion_from_defensive_wars", "add_piety_experience = medium_piety_loss")
    truce_effect = _block(source["scripted_effects/00_war_effects.txt"], "add_truce_attacker_victory_effect")
    _requires(truce_effect, "add_truce_one_way = {", "character = scope:defender", "days = standard_truce_duration_days", "result = victory")
    truce_days = _block(source["script_values/00_war_values.txt"], "standard_truce_duration_days")
    _requires(truce_days, "value = 1825", "add = -450", "add = -900", "add = 900", "subtract = 730", "min = 730", "multiply = 2")

    return {
        "schema": "xar.ck3.h2743-exit-static-resource-envelope.v1",
        "status": "script_components_only_material_unavailable",
        "source": {"exe_sha256": EXE_SHA, "script_sha256": SCRIPT_SHA, "h2743_frame_sha256": FRAME_SHA},
        "frame": {"war_id": 16777231, "date_raw": frame["date_raw"], "snapshot_id": frame["snapshot_id_before_and_after"], "attacker": 30097, "defender": 29829, "target_title_ids": [2128]},
        "factor": {"name": "cb_prestige_factor", "actual_raw_q100000": None, "reason": "native_setup_factor_storage_and_same_frame_input_unproven"},
        "primary_direct_components": {
            "defender_prestige_currency": "max(-10 * F, -1000)",
            "attacker_prestige_experience": "min(10 * F, 1000)",
            "evaluated_raw_q100000": None,
        },
        "selected_conditional_effect_sources_not_exhaustive": [
            "war_end_legitimacy_effect: attacker legitimacy conditional on title tiers and legitimacy eligibility",
            "mandala_war_victory_effects: defender piety experience conditional on realm law",
            "laamp_as_mercenary_payout_tooltip_effect: participant and contract gold conditional on active contract state",
            "add_hook_from_temp_de_jure_liege_to_attacker: favor hook conditional on liege and can_add_hook",
        ],
        "other_effects_unresolved": [
            "show_pow_release_message_effect",
            "accolade_attacker_war_end_glory_gain_low_effect",
            "fp1_remember_recent_conquest_victory_effect",
            "global war-end effects outside this CB block",
        ],
        "truce": {
            "script_direction": {"owner": 30097, "toward": 29829},
            "days_expression": "(2 if B else 1) * max(730, 1825 - 450*FLEX - 900*SHORT + 900*LONG - 730*NOMAD_BOTH)",
            "evaluated_days": None,
            "expiry_date_raw": None,
        },
        "signed_total_resource_deltas": None,
        "resolved_title_vassal_operations": None,
        "comparison_ready": False,
        "material_complete": False,
        "recommended_outcome": None,
        "action_literal": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path, default=GAME)
    parser.add_argument("--frame", type=Path, default=FRAME)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(project(args.game_dir, args.frame), ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

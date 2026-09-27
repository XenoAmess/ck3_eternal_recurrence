#!/usr/bin/env python3
"""Hash-bound, read-only audit of one day-26 knight-kill random-list path.

The second draw is inferred from an exact-build instruction path and an
observed +2 local counter delta. It was not independently captured as a value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import pefile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.simulation.combat_core import DrawState, weighted_choice_index


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
SOURCE_SHA256 = "8BC27BC8420B31474DEDABDF00E004E5C2C910C4906406A15CE0D46144E809A8"
STOCK_EVENT_SHA256 = "E8F8E4978BB1AF130D74AA6ED72EE41F014B09C9F324608EBFB0E87D56A5EDB1"
SOURCE = (
    Path(__file__).resolve().parents[2]
    / "src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_day26_runtime_weights_v1.json"
)
FROZEN = Path(__file__).resolve().parent / "fixtures/knight_entry_dispatch_rng_11906.json"
SPANS = {
    "list_selection_0x2F087B1": (
        0x2F087B1, 0x78,
        "61591BDE1A95EA77AD39C2A25EF6A6D7DAEDE2FC4B671B161F45960EB3887D5A",
    ),
    "selected_entry_seed_0x3380C20": (
        0x3380C20, 0xC6,
        "3F8F371E4A828A662F317F6D9AB5633C933335B90CD7514F8B7D56257598427C",
    ),
    "selected_entry_virtual_call_0x3380CE6": (
        0x3380CE6, 0x1B,
        "18B0FCB3D0D20A13E402EEAE2F18091FFF3FB93C174C44AEDCBC7F9529FDFA2F",
    ),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require(condition: bool, description: str) -> None:
    if not condition:
        raise ValueError(description)


def project(exe: Path, source: Path = SOURCE) -> dict[str, object]:
    require(digest(exe.read_bytes()) == EXE_SHA256, "exact CK3 EXE differs")
    require(digest(source.read_bytes()) == SOURCE_SHA256, "day-26 evidence fixture differs")
    stock_event = exe.parent.parent / "game/common/combat_phase_events/00_knight_phase_events.txt"
    require(digest(stock_event.read_bytes()) == STOCK_EVENT_SHA256, "stock knight event source differs")
    stock_section = stock_event.read_text(encoding="utf-8-sig").split("knight_killed = {", 1)[1]
    stock_effect = stock_section.split("effect = {", 1)[1]
    previous = -1
    for token in (
        "random_side_knight = {",
        "knight_increase_prowess_chance_effect = yes",
        'key = "knight_killed_by_enemy"',
        "death_reason = death_battle",
        "killer = scope:enemy_knight",
    ):
        position = stock_effect.index(token)
        require(position > previous, f"stock knight effect order differs: {token}")
        previous = position
    image = pefile.PE(str(exe), fast_load=True)
    span_sha256 = {}
    for label, (rva, size, expected) in SPANS.items():
        actual = digest(image.get_data(rva, size))
        require(actual == expected, f"compiled code span differs: {label}")
        span_sha256[label] = actual

    evidence = json.loads(source.read_text(encoding="utf-8"))
    require(evidence["game_executable_sha256"] == EXE_SHA256, "source EXE identity differs")
    require(evidence["source_save_sha256"] == "C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B", "source save differs")
    require(evidence["native_event_load_index"] == 11, "different native event")
    require(evidence["native_selector_draw31"] == 1400813912, "different killer selector draw")
    require(evidence["native_selector_selected_character_id"] == 34120, "different killer")
    choice = evidence["native_choice"]
    require(choice["weights_native_int32"] == [40, 30, 15], "different runtime weights")
    require(choice["positive_weight_total"] == 85, "different positive weight sum")
    before = choice["child_counter_before"]
    require(before == 1462316485, "different list scope counter")
    selection_draw, after_selection = DrawState(before, 0).draw31()
    entry_seed_draw, after_entry_seed = after_selection.draw31()
    require(selection_draw == choice["selection_draw31"] == 51510340, "selection draw differs")
    require(after_entry_seed.counter == choice["child_counter_after"] == 1462316487, "entry seed counter differs")
    require(weighted_choice_index(tuple(choice["weights_native_int32"]), selection_draw) == choice["selected_source_order_index"] == 0, "selected entry differs")
    require(choice["selected_entry_identity_token"] == choice["entry_node_identity_tokens"][0], "selected entry identity differs")
    require(evidence["model_growth_transition"]["selected_branch"] == "no_op", "different growth branch")
    event = evidence["native_battle_event"]
    death = evidence["model_death_transition"]
    require(event["stable_key"] == "knight_killed_by_enemy", "different battle event")
    require(event["left_character_id"] == death["target_character_id"] == 33437, "victim differs")
    require(event["right_character_id"] == death["killer_character_id"] == 34120, "killer differs")
    require(death["reason"] == "death_battle" and death["applied"] is True, "death transition differs")
    require(evidence["complete_mutable_write_set_proven"] is False, "write-set boundary changed")
    require(evidence["whole_battle_win_probability_available"] is False, "probability boundary changed")
    return {
        "schema": "ck3.knight_entry_dispatch_rng_static.v1",
        "game_build": "1.19.0.6-steam23530548",
        "exe_sha256": EXE_SHA256,
        "source_fixture_sha256": SOURCE_SHA256,
        "stock_event_sha256": STOCK_EVENT_SHA256,
        "source_save_sha256": evidence["source_save_sha256"],
        "span_sha256": span_sha256,
        "observed": {
            "event_load_index": 11,
            "killer_selector_draw31": 1400813912,
            "killer_character_id": 34120,
            "list_local_counter_before": before,
            "list_selection_draw31": selection_draw,
            "list_weights": choice["weights_native_int32"],
            "selected_entry_index": 0,
            "list_local_counter_after": after_entry_seed.counter,
            "victim_character_id": 33437,
            "battle_event": "knight_killed_by_enemy",
        },
        "exact_build_conditional_inference": {
            "selected_entry_seed_draw31": entry_seed_draw,
            "seed_draw_is_directly_captured": False,
            "second_consumer": "0x3380C20-0x3380CFB selected-entry effect dispatcher",
            "seed_depends_on_selected_entry_node_hash": True,
            "derived_entry_child_counter_available": False,
        },
        "writeback_receipt_and_model_boundary": {
            "character_death_transition": death,
            "growth_branch": "no_op",
            "complete_mutable_write_set_proven": False,
            "whole_battle_win_probability_available": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exe", type=Path,
        default=Path("C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe"),
    )
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = project(args.exe, args.source)
    body = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.check:
        require(FROZEN.read_bytes() == body, "frozen projection differs")
    if args.output is not None:
        with args.output.open("xb") as stream:
            stream.write(body)
    else:
        print(body.decode("utf-8"), end="")


if __name__ == "__main__":
    main()

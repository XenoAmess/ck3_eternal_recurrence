"""Project the selected event's root effect-local RNG initialization.

This is exact-build static analysis tied to a native observed phase-fire seed.
It does not observe the compiled effect's later branch draws or winner sample.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import pefile

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
from xar_autoplayer.simulation.combat_core import DrawState, avalanche32  # noqa: E402
from xar_autoplayer.simulation.native_battle_case import (  # noqa: E402
    EPISODE01_PHASE_FIRE_DRAWS_SHA256,
    load_episode01_phase_fire_draw_projection,
)

EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
RVA = 0x337FE60
SLICE_BYTES = 0x60
MASK = 0xFFFFFFFF


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def project(exe: Path) -> dict[str, object]:
    source = load_episode01_phase_fire_draw_projection()
    if digest(exe) != EXE_SHA256:
        raise ValueError("CK3 executable does not match frozen exact build")
    pe = pefile.PE(str(exe), fast_load=True)
    binary = exe.read_bytes()
    offset = pe.get_offset_from_rva(RVA)
    code = binary[offset:offset + SLICE_BYTES]
    # 0x337FE70 reads the effect seed from context+0x10; the following
    # positive-seed branch zeroes salt and applies the same avalanche32.
    if (code[0x10:0x13] != bytes.fromhex("8B4210")
            or code[0x17:0x1E] != bytes.fromhex("C7410400000000")
            or code[0x1E:0x24] != bytes.fromhex("69C0B385D64A")):
        raise ValueError("effect-local seed initializer bytes changed")
    seed = source["target_effect_seed"]
    if not isinstance(seed, int) or not 0 <= seed < 0x80000000:
        raise ValueError("selected effect seed is outside positive native branch")
    counter = avalanche32((0x5EA6BA9F - seed * 0x4AD685B3) & MASK)
    first_draw, after = DrawState(counter, 0).draw31()
    return {
        "schema": "xar.ck3.episode01.effect-local-root-seed/v1",
        "game_build": "CK3 1.19.0.6",
        "ck3_exe_sha256": EXE_SHA256,
        "seed_initializer_rva": "0x337FE60",
        "seed_initializer_first_0x60_sha256": hashlib.sha256(code).hexdigest().upper(),
        "phase_fire_draw_projection_sha256": EPISODE01_PHASE_FIRE_DRAWS_SHA256,
        "observed_native_event_key": source["target_event_key"],
        "derived_effect_seed": seed,
        "derived_effect_local_root_counter": counter,
        "derived_effect_local_root_salt": 0,
        "first_draw_if_root_dispatch_consumes": first_draw,
        "root_counter_after_first_draw_if_consumed": after.counter,
        "root_first_draw_directly_observed": False,
        "effect_local_node_hashes_observed": False,
        "effect_local_winner_draw_observed": False,
        "full_effect_write_set_proven": False,
        "whole_battle_win_probability_available": False,
        "planner_usable": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = project(args.exe)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()

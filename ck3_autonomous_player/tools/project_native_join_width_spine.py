"""Verify bounded CK3 1.19.0.6 join-width production and phase-fire reads.

The report proves exact-build instructions, not width values in an unobserved
live reinforcement case. It never launches the game or calls native helpers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
CALLS = {
    0x2304255: 0x23CB840,
    0x2304261: 0x23CB840,
    0x2304272: 0x2305580,
    0x2309E92: 0x23CB840,
    0x2309EA1: 0x23CB840,
    0x2309F93: 0x23CB1D0,
    0x2309FAF: 0x23CB1D0,
}
INSTRUCTION_BYTES = {
    0x23040A0: "48895C24104889742418555741544156",  # 16 complete hook bytes
    0x23040B0: "4157",          # next instruction, not split by hook
    0x2304266: "4439A3C0060000",  # old base width > 0 gate; r12d=0
    0x2304277: "4438A3FC060000",  # branch merge after optional update
    0x2305590: "4C8B8900040000",  # side1 current total
    0x230559E: "4C0389B8000000",  # plus side0 current total
    0x230571B: "8913",            # candidate base write
    0x2305742: "8913",            # historical max base write
    0x2305812: "8997C4060000",    # raw final-width write
    0x2305824: "8987C4060000",    # minimum-clamped final-width write
    0x2309F7F: "448B87C4060000",  # side0 phase-fire width load
    0x2309F98: "448B87C4060000",  # side1 phase-fire width load
    0x23CB1D0: "4489442418",      # callee saves width argument
    0x23CB445: "4863842490000000", # callee consumes saved width
}


def _call_target(pe: pefile.PE, rva: int) -> int:
    code = pe.get_data(rva, 5)
    if len(code) != 5 or code[0] != 0xE8:
        raise ValueError(f"relative call missing at {rva:#x}")
    return rva + 5 + int.from_bytes(code[1:], "little", signed=True)


def project(exe: Path) -> dict:
    raw = exe.read_bytes()
    actual = hashlib.sha256(raw).hexdigest().upper()
    if actual != EXE_SHA256:
        raise ValueError(f"CK3 EXE differs from exact 1.19.0.6 build: {actual}")
    pe = pefile.PE(data=raw, fast_load=True)
    for site, target in CALLS.items():
        if _call_target(pe, site) != target:
            raise ValueError(f"join-width call target drifted at {site:#x}")
    for site, expected_hex in INSTRUCTION_BYTES.items():
        expected = bytes.fromhex(expected_hex)
        if pe.get_data(site, len(expected)) != expected:
            raise ValueError(f"join-width operand drifted at {site:#x}")
    return {
        "schema": "ck3.native_join_width_spine.v1",
        "game_build": "1.19.0.6", "exe_sha256": EXE_SHA256,
        "join_wrapper_rva": "0x23040A0",
        "side_refresh_rva": "0x23CB840",
        "side_refresh_calls_before_width_update": ["0x2304255", "0x2304261"],
        "width_update_gate_rva": "0x2304266",
        "width_update_call_rva": "0x2304272",
        "width_updater_rva": "0x2305580",
        "width_inputs": ["CCombat+0xB8 side0 current total Q100000",
                         "CCombat+0x400 side1 current total Q100000",
                         "CCombat+0x6B8 encounter Province terrain multiplier"],
        "base_width_field": "CCombat+0x6C0 int32",
        "final_width_field": "CCombat+0x6C4 int32",
        "main_tick_side_refresh_calls": ["0x2309E92", "0x2309EA1"],
        "main_tick_final_width_read_sites": ["0x2309F7F", "0x2309F98"],
        "phase_damage_callee_rva": "0x23CB1D0",
        "phase_damage_width_consume_rva": "0x23CB445",
        "live_case_width_values_sampled": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(project(args.exe), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

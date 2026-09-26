"""Project bounded CK3 1.19.0.6 AI builder/submit control-flow anchors.

This is a static exact-build check. It does not inspect or control a running
CK3 process and cannot identify which branch a previous live run took.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
GATE_RVA = 0x5762480
BYTES = {
    0x186B1C7: "66C743080000",  # clear result flags
    0x186B1D6: "C6430801",      # mark builder path handled
    0x186B27F: "741A",          # gate clear -> submit arm
    0x186B299: "EB30",          # gate set -> cleanup, no submit
    0x186B2EA: "C6430901",      # second result flag, not queue ACK
    0x1872362: "807C242800",    # outer dispatcher tests handled byte
    0x1872367: "0F8533030000",  # handled -> return cleanup
    0x18725B9: "7563",          # same global gate skips fallback submit
}
CALLS = {
    0x187235D: 0x186B190,  # outer dispatcher -> builder
    0x186B28D: 0xC7BA70,   # stack-local command scratch initializer
    0x186B2A7: 0xC7BA70,
    0x186B2C5: 0x973E00,   # builder command submit
    0x1872611: 0x973E00,   # outer fallback, only if builder unhandled
    0x973E41: 0x341D990,  # submit wrapper forwards to queue operation
}
GATE_TESTS = (0x186B278, 0x1871C51, 0x18725B2, 0x1872A31)


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
    for rva, expected_hex in BYTES.items():
        expected = bytes.fromhex(expected_hex)
        if pe.get_data(rva, len(expected)) != expected:
            raise ValueError(f"instruction bytes drifted at {rva:#x}")
    for rva, target in CALLS.items():
        if _call_target(pe, rva) != target:
            raise ValueError(f"call target drifted at {rva:#x}")
    for rva in GATE_TESTS:
        code = pe.get_data(rva, 7)
        if len(code) != 7 or code[:2] != b"\xF6\x05" or code[6] != 0xFD:
            raise ValueError(f"global bit test missing at {rva:#x}")
        target = rva + 7 + int.from_bytes(code[2:6], "little", signed=True)
        if target != GATE_RVA:
            raise ValueError(f"global bit test target drifted at {rva:#x}")
    return {
        "schema": "ck3.native_ai_builder_submit_gate.v1",
        "game_build": "1.19.0.6",
        "exe_sha256": EXE_SHA256,
        "builder_rva": "0x186B190",
        "outer_dispatcher_rva": "0x18721B0",
        "gate_global_rva": "0x5762480",
        "gate_mask": "0xFD",
        "gate_test_rvas": [f"0x{rva:X}" for rva in GATE_TESTS],
        "builder_submit_call_rva": "0x186B2C5",
        "builder_bypass_jump_rva": "0x186B299",
        "outer_handled_check_rva": "0x1872362",
        "outer_fallback_submit_call_rva": "0x1872611",
        "gate_semantic_name_confirmed": False,
        "live_065_branch_or_gate_value_observed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(project(args.exe), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

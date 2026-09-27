"""Pin the all-row Accolade source gate used by active side refresh."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile

from verify_active_advantage_refresh_inputs import (
    EXE_SHA256,
    verify_image as verify_refresh_inputs,
)


GATE_SPAN = (0x251C200, 0x251C271)
SITES = {
    "row_base": (0x251C20F, "488B5958"),
    "row_count": (0x251C216, "48634164"),
    "empty_rows_exit": (0x251C225, "741B"),
    "row_source_pointer": (0x251C227, "488B4B10"),
    "null_source_gate": (0x251C22B, "4885C9"),
    "null_source_exit": (0x251C22E, "7412"),
    "source_virtual_gate": (0x251C233, "FF10"),
    "virtual_result_test": (0x251C235, "84C0"),
    "invalid_source_exit": (0x251C237, "7409"),
    "next_row": (0x251C239, "4883C318"),
    "more_rows": (0x251C240, "75E5"),
    "ended_at_count": (0x251C257, "33C0"),
    "completed_rows_select": (0x251C25C, "480F44D8"),
    "gate_result_test": (0x251C260, "4885DB"),
    "gate_result_boolean": (0x251C268, "0F94C0"),
}


def verify_image(image: pefile.PE) -> dict[str, object]:
    verify_refresh_inputs(image)
    owners = [(int(row.struct.BeginAddress), int(row.struct.EndAddress))
              for row in image.DIRECTORY_ENTRY_EXCEPTION
              if int(row.struct.BeginAddress) <= GATE_SPAN[0]
              < int(row.struct.EndAddress)]
    if owners != [GATE_SPAN]:
        raise ValueError(f"accolade source gate owner differs: {owners}")
    anchors = {}
    for name, (rva, expected_hex) in SITES.items():
        expected = bytes.fromhex(expected_hex)
        if image.get_data(rva, len(expected)) != expected:
            raise ValueError(f"{name} differs at 0x{rva:X}")
        anchors[name] = {"rva": f"0x{rva:X}", "bytes_hex": expected_hex}
    if (0x251C225 + 2 + int.from_bytes(bytes.fromhex(SITES["empty_rows_exit"][1])[1:],
                                        "little", signed=True) != 0x251C242 or
        0x251C22E + 2 + int.from_bytes(bytes.fromhex(SITES["null_source_exit"][1])[1:],
                                        "little", signed=True) != 0x251C242 or
        0x251C237 + 2 + int.from_bytes(bytes.fromhex(SITES["invalid_source_exit"][1])[1:],
                                        "little", signed=True) != 0x251C242):
        raise ValueError("accolade source invalid-row exits differ")
    return {
        "schema": "ck3.native_active_accolade_all_row_gate.v1",
        "game_build": "1.19.0.6",
        "exe_sha256": EXE_SHA256,
        "gate_span": [f"0x{x:X}" for x in GATE_SPAN],
        "anchors": anchors,
        "proof_layer": "exact-build-instructions-pdata-and-branch-targets",
    }


def verify_exe(exe: Path) -> dict[str, object]:
    raw = exe.read_bytes()
    sha = hashlib.sha256(raw).hexdigest().upper()
    if sha != EXE_SHA256:
        raise ValueError(f"ck3.exe SHA mismatch: {sha}")
    return verify_image(pefile.PE(data=raw, fast_load=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--output", type=Path,
                        help="exclusively create a new exact-build fixture")
    args = parser.parse_args()
    result = verify_exe(args.exe)
    if args.expected is not None:
        expected = json.loads(args.expected.read_text(encoding="utf-8"))
        if result != expected:
            raise ValueError("accolade source gate fixture differs from exact EXE")
    body = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(body, end="")
    else:
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

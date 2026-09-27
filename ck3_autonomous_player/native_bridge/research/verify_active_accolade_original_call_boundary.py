"""Pin the original active-combat Accolade gate's call and detour boundaries."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile

from verify_active_accolade_source_gate import verify_image as verify_gate
from verify_active_advantage_refresh_inputs import EXE_SHA256


HOOKS = {
    "cache": (0x2308D50, 15, "48895C24184889742420574883EC20"),
    "refresh": (0x23CBCE0, 15, "48896C24104889742418574883EC20"),
    "append": (0x251B8F0, 16, "4889742410574883EC20488BF2488BF9"),
    "all_row_gate": (0x251C200, 15, "48895C24084889742410574883EC20"),
}
CALLS = {
    "cache_refresh_attacker": (0x2308D66, 0x23CBCE0, "E8752F0C00"),
    "cache_refresh_defender": (0x2308D72, 0x23CBCE0, "E8692F0C00"),
    "refresh_append": (0x23CBEA3, 0x251B8F0, "E848FA1400"),
    "append_gate": (0x251B900, 0x251C200, "E8FB080000"),
}
OWNER_SPANS = {
    "cache": (0x2308D50, 0x2308DE5),
    "refresh": (0x23CBCE0, 0x23CBD67),
    "append": (0x251B8F0, 0x251B90D),
    "all_row_gate": (0x251C200, 0x251C271),
}


def verify_image(image: pefile.PE) -> dict[str, object]:
    verify_gate(image)
    pdata = {
        (int(row.struct.BeginAddress), int(row.struct.EndAddress))
        for row in image.DIRECTORY_ENTRY_EXCEPTION
    }
    hooks = {}
    for name, (rva, length, expected_hex) in HOOKS.items():
        expected = bytes.fromhex(expected_hex)
        if len(expected) != length or image.get_data(rva, length) != expected:
            raise ValueError(f"{name} entry bytes differ at 0x{rva:X}")
        if OWNER_SPANS[name] not in pdata:
            owners = [span for span in pdata if span[0] <= rva < span[1]]
            raise ValueError(f"{name} .pdata owner differs: {owners}")
        hooks[name] = {
            "rva": f"0x{rva:X}",
            "whole_instruction_bytes": expected_hex,
            "length": length,
            "pdata_owner": [f"0x{x:X}" for x in OWNER_SPANS[name]],
        }
    calls = {}
    for name, (rva, target, expected_hex) in CALLS.items():
        expected = bytes.fromhex(expected_hex)
        actual = image.get_data(rva, len(expected))
        if actual != expected or len(actual) != 5 or actual[0] != 0xE8:
            raise ValueError(f"{name} call bytes differ at 0x{rva:X}")
        resolved = rva + 5 + int.from_bytes(actual[1:], "little", signed=True)
        if resolved != target:
            raise ValueError(f"{name} call target differs: 0x{resolved:X}")
        calls[name] = {
            "rva": f"0x{rva:X}",
            "return_rva": f"0x{rva + 5:X}",
            "target_rva": f"0x{target:X}",
            "bytes_hex": expected_hex,
        }
    return {
        "schema": "ck3.native_active_accolade_original_call_boundary.v1",
        "game_build": "1.19.0.6",
        "exe_sha256": EXE_SHA256,
        "hook_entries": hooks,
        "original_calls": calls,
        "observation_limit": (
            "all-row boolean is available at original gate return; the "
            "per-row failed virtual call index and caller RSI entry pointer "
            "are not returned by these function boundaries"
        ),
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
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify_exe(args.exe)
    if args.expected is not None:
        expected = json.loads(args.expected.read_text(encoding="utf-8"))
        if result != expected:
            raise ValueError("original-call boundary fixture differs")
    body = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(body, end="")
    else:
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

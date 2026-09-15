"""Verify the exact CK3 cost-helper source used by the read-only collector."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import pefile


HERE = Path(__file__).resolve().parent
ABI = HERE / "domain_construction_cost_gate_collector_v1_abi.json"


def verify(executable: Path) -> None:
    contract = json.loads(ABI.read_text(encoding="utf-8"))
    exact = contract["exact_build"]
    data = executable.read_bytes()
    expected_exe = exact["executable_sha256"]
    actual_exe = hashlib.sha256(data).hexdigest().upper()
    if actual_exe != expected_exe:
        raise RuntimeError(f"CK3 executable drift: {actual_exe} != {expected_exe}")
    image = pefile.PE(data=data, fast_load=True)

    def at(rva: int, size: int) -> bytes:
        offset = image.get_offset_from_rva(rva)
        return data[offset : offset + size]

    begin, end = (int(value, 16) for value in exact["cost_helper_span_rva"])
    actual_span = hashlib.sha256(at(begin, end - begin)).hexdigest().upper()
    if actual_span != exact["cost_helper_span_sha256"]:
        raise RuntimeError("exact cost-helper span drifted")
    source_bytes = {
        0x18D1802: bytes.fromhex("488BDA"),  # rbx <- resource balance
        0x18D180F: bytes.fromhex("488B7D7F"),  # rdi <- selected row
        0x18D185A: bytes.fromhex("0F1145BF"),  # cost at rbp-0x41
        0x18D18F3: bytes.fromhex(exact["cost_gate_bytes_to_next_instruction"]),
    }
    for rva, expected in source_bytes.items():
        if at(rva, len(expected)) != expected:
            raise RuntimeError(f"cost-gate register source drift at {rva:#x}")
    print("domain-construction-cost-gate-collector: GREEN_EXACT_BUILD")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path)
    arguments = parser.parse_args()
    executable = arguments.exe or os.environ.get("XAR_CK3_EXECUTABLE_PATH")
    if executable is None:
        parser.error("pass --exe or set XAR_CK3_EXECUTABLE_PATH")
    verify(Path(executable).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

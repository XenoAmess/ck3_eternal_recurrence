#!/usr/bin/env python3
"""Verify the frozen exact-build bytes used by pursuit modifier readback."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile


ABI = Path(__file__).with_name("combat_pursuit_modifier_readback_1_19_0_6_abi.json")


def verify(exe: Path) -> int:
    manifest = json.loads(ABI.read_text(encoding="utf-8"))
    data = exe.read_bytes()
    digest = hashlib.sha256(data).hexdigest().upper()
    if digest != manifest["exact_build"]["exe_sha256"]:
        raise ValueError("CK3 EXE SHA-256 differs from pursuit readback ABI")
    image = pefile.PE(data=data, fast_load=True)
    for address, hex_bytes in manifest["exact_instruction_bytes"].items():
        expected = bytes.fromhex(hex_bytes)
        offset = image.get_offset_from_rva(int(address, 16))
        if data[offset : offset + len(expected)] != expected:
            raise ValueError(f"pursuit readback instruction differs at {address}")
    print(f"GREEN pursuit modifier ABI {digest} {len(manifest['exact_instruction_bytes'])} anchors")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    return verify(parser.parse_args().exe)


if __name__ == "__main__":
    raise SystemExit(main())

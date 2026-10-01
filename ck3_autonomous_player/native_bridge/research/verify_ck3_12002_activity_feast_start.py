"""Verify the exact Crozier final Feast gate and original queue-accept branch."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import pefile

SHA = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
PREFIXES = {
    0x11B8670: "48895c24104889",
    0x11B88E8: "488d9100150000",
    0x11B8D90: "4055535657488dac2418f6ffff",
    0x11B8DA7: "e8a4f2ffff",
    0x11B8E73: "448d460e",
    0x11B8E85: "e866786302",
    0x11B94D9: "e8b2f8ffff",
    0x11B92C7: "e9c4faffff",
    0x11B92F3: "e878f3ffff",
    0x856050: "40534883ec20488b5118",
    0x297D080: "4883c120e907f9a7ff",
}

def verify(exe: Path) -> dict[str, object]:
    raw = exe.read_bytes()
    actual = hashlib.sha256(raw).hexdigest().upper()
    image = pefile.PE(data=raw, fast_load=True)
    failures = []
    if actual != SHA:
        failures.append("executable_sha256")
    if image.OPTIONAL_HEADER.ImageBase != 0x140000000:
        failures.append("image_base")
    for rva, hex_bytes in PREFIXES.items():
        expected = bytes.fromhex(hex_bytes)
        if image.get_data(rva, len(expected)) != expected:
            failures.append(f"code:0x{rva:X}")
    # The temporary Start command used by CanStart and Commit must match.
    for rva, expected in {0x476BAA0 + 6*8: 0x297D080}.items():
        target = struct.unpack("<Q", image.get_data(rva, 8))[0]
        if target != 0x140000000 + expected:
            failures.append(f"start_validator:0x{rva:X}")
    return {"schema": "xar.ck3_12002.feast_start_exact_abi.v1",
            "executable_sha256": actual, "verified": not failures,
            "mismatches": failures, "anchor_count": len(PREFIXES)+1}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.exe)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["verified"] else 1)

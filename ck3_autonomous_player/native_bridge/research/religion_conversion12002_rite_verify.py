"""Verify the exact read-only Rite preview ABI; never launches CK3."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from scan_anchors import PeImage

EXE_SHA256 = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
ANCHORS = [
    ("window paid command actor", 0x151697C, "8b057e52fc03"),
    ("window target Rite identity", 0x1516986, "8b81c8000000"),
    ("window payment flag", 0x1516990, "c644244801"),
    ("target Rite full Faith reference", 0x29A35A1, "8b86b8040000"),
    ("current Rite comes from Character+B4", 0x29A35AC, "448b97b4000000"),
    ("same Faith dispatch comparison", 0x29A35DE, "413b80b8040000"),
    ("same Faith null-reasons Rite gate", 0x29A3624, "e8d7003cff"),
    ("different Faith final rules gate", 0x29A365E, "e87dff3bff"),
    ("native payment flag branch", 0x29A36DE, "41807f2800"),
    ("native piety cost", 0x29A36EE, "e8ed060000"),
    ("whole piety to native fixed point", 0x29A3741, "4869cba0860100"),
    ("final rule and payment result", 0x29A38A8, "4022f7"),
    ("Rite rules target scope type42", 0x1D637C6, "c74424202a000000"),
    ("Rite rules instance field", 0x1D637ED, "488b88f00e0000"),
    ("Rite rules member offset", 0x1D637F4, "4881c110040000"),
    ("Rite rules null-reasons path", 0x1D6380F, "e81ca79c01"),
    ("Faith GetRites native getter", 0xB801B0, "488d4120c3"),
    ("Faith GetRites reflection caller", 0x244441E, "e88dbd73fe"),
    ("Rite association count offset", 0xFBD061, "8b700c"),
    ("Rite association data and stride4", 0xFBD0A5, "498b06488d0cb8"),
    ("Rite association identity resolver", 0xFBD0AC, "e80f67f4ff"),
    ("Rite association range stride4", 0xFBD210, "498d0c98"),
    ("Rite full generation comparison", 0xF037F5, "44394008"),
    ("native entry target identity", 0x14C2F5E, "418b8058020000"),
    ("native entry current Rite difference", 0x14C2F6A, "3982b4000000"),
]

def verify(executable: Path) -> dict:
    data = executable.read_bytes()
    digest = hashlib.sha256(data).hexdigest().upper()
    if digest != EXE_SHA256:
        raise ValueError("This ABI requires the frozen CK3 1.20.0.2 executable")
    image = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    rows = []
    for name, rva, expected in ANCHORS:
        size = len(bytes.fromhex(expected))
        offset = image.rva_to_offset(rva)
        actual = data[offset:offset + size]
        if actual.hex() != expected:
            raise ValueError(f"{name}: bytes changed at RVA {rva:#x}")
        instructions = list(decoder.disasm(actual, rva))
        if sum(instruction.size for instruction in instructions) != size:
            raise ValueError(f"{name}: incomplete instruction span at RVA {rva:#x}")
        rows.append({"name": name, "rva": hex(rva), "bytes": actual.hex(),
                     "instructions": [{"rva": hex(i.address), "mnemonic": i.mnemonic,
                                       "operands": i.op_str} for i in instructions]})
    slot = 0x4770370
    pointer = struct.unpack_from("<Q", data, image.rva_to_offset(slot))[0]
    if pointer != image.image_base + 0x29A34C0:
        raise ValueError("FaithAndRite primary vtable+0x30 is not the final validator")
    return {"schema": "xar.ck3_12002.religion_conversion_rite_abi.v1",
            "status": "GREEN", "evidence_level": "static-confirmed",
            "executable": str(executable), "executable_sha256": digest,
            "anchors": rows, "anchor_count": len(rows),
            "vtable": {"primary_rva": "0x4770340", "secondary_rva": "0x47703d8",
                       "validator_slot_rva": hex(slot), "validator_rva": "0x29a34c0"},
            "native_bindings": {"command_size": "0x30", "actor_id_offset": "0x20",
                "target_rite_id_offset": "0x24", "payment_flag_offset": "0x28",
                "rite_storage_slot_rva": "0x5d1e2f8", "faith_rites_getter_rva": "0xb801b0",
                "faith_rites_container_offset": "0x20", "rite_id_stride": 4,
                "container_data_offset": 0, "container_size_offset": 12},
            "boundary": "Read-only native validation and association list; no mutation or live evidence"}

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"GREEN {result['anchor_count']} exact instruction spans and final validator vtable")

if __name__ == "__main__":
    main()

"""Exact-build native formatted conversion reasons; no game operations."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from scan_anchors import PeImage

EXE_SHA256 = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
ANCHORS = [
    ("Blockers output argument retained", 0x1516B38, "488bda"),
    ("Native small string inline/pointer zero", 0x1516B40, "488932"),
    ("Native string size initially zero", 0x1516B43, "48897210"),
    ("Native string SSO capacity fifteen", 0x1516B47, "48c742180f000000"),
    ("Native inline text null terminator", 0x1516B4F, "408832"),
    ("Blockers command pays piety", 0x1516B91, "40886c2450"),
    ("Blockers direct paid final validator", 0x1516B9B, "e820c94801"),
    ("Blockers reflection local native string", 0x1516DDE, "488d542420"),
    ("Blockers reflection invokes formatter core", 0x1516DE3, "e838fdffff"),
    ("Blockers reflection publishes a copy", 0x1516DEF, "e89c2b36ff"),
    ("Blockers reflection points to owned buffer", 0x1516DF5, "488d4c2420"),
    ("Blockers reflection native string destructor", 0x1516DFA, "e851f233ff"),
    ("Native destructor reads capacity", 0x856056, "488b5118"),
    ("Native destructor heap threshold sixteen", 0x85605D, "4883fa10"),
    ("Native destructor loads native heap pointer", 0x856063, "488b09"),
    ("Native destructor large-allocation branch", 0x856069, "4881fa00100000"),
    ("Native destructor invokes runtime free", 0x85608A, "e8d5de9c03"),
    ("Native destructor resets size", 0x85608F, "48c7431000000000"),
    ("Native destructor resets inline capacity", 0x856097, "48c743180f000000"),
    ("Native destructor resets first character", 0x85609F, "c60300"),
    ("Final validator retains nonnull reason text", 0x29A34DE, "4c8bf2"),
    ("Native formatter intermediate constructor", 0x29A35FD, "e8de30e200"),
    ("Native formatter output text argument", 0x29A36AF, "4d8bc6"),
    ("Native formatter final reason text emission", 0x29A36BA, "e801a6db00"),
    ("Native piety reason string append", 0x29A4216, "e8b51deefd"),
    ("UI newline insertion output buffer", 0x1516C67, "488bcb"),
    ("UI newline insertion native method", 0x1516C6A, "e891a39d02"),
    ("Native insertion size read", 0x3EF1015, "4c8b4110"),
    ("Native insertion position bounds", 0x3EF101C, "4c3bc2"),
    ("Native insertion capacity read", 0x3EF1025, "4c8b4918"),
]

def verify(executable: Path) -> dict:
    data = executable.read_bytes()
    digest = hashlib.sha256(data).hexdigest().upper()
    if digest != EXE_SHA256:
        raise ValueError("Requires the exact frozen CK3 1.20.0.2 executable")
    image = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    evidence = []
    for name, rva, expected in ANCHORS:
        length = len(bytes.fromhex(expected))
        offset = image.rva_to_offset(rva)
        actual = data[offset:offset+length]
        if actual.hex() != expected:
            raise ValueError(f"Changed native ABI at {rva:#x}: {name}")
        decoded = list(decoder.disasm(actual, rva))
        if sum(instruction.size for instruction in decoded) != length:
            raise ValueError(f"Incomplete instruction span at {rva:#x}")
        evidence.append({"name": name, "rva": hex(rva), "bytes": actual.hex(),
                         "instructions": [{"rva": hex(i.address), "mnemonic": i.mnemonic,
                                           "operands": i.op_str} for i in decoded]})
    newline = data[image.rva_to_offset(0x448D028):image.rva_to_offset(0x448D028)+2]
    if newline != b"\n\0":
        raise ValueError("Blockers UI normalization literal changed")
    return {"schema": "xar.ck3_12002.religion_conversion_reasons_abi.v1",
            "status": "GREEN", "evidence_level": "static-confirmed",
            "executable": str(executable), "executable_sha256": digest,
            "anchor_count": len(evidence), "anchors": evidence,
            "native_string": {"size": "0x20", "inline_storage_size": 16,
                "size_offset": "0x10", "capacity_offset": "0x18",
                "initial_capacity": 15, "constructor": "1516B20 inline initialization",
                "native_destructor_rva": "0x856050"},
            "formatter": {"reflection_rva": "0x1516dd0", "core_rva": "0x1516b20",
                "native_validator_rva": "0x29a34c0", "reason_argument": "non-null owned native string",
                "payment_flag": 1, "newline_literal_rva": "0x448d028"},
            "boundary": "Read-only text formatter source; no GUI construction, submission or live proof"}

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(f"GREEN {result['anchor_count']} exact reason-lifetime instruction spans and UI newline literal")
if __name__ == "__main__":
    main()

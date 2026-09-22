"""Read exact-build MSVC vtable address points and RTTI, offline only.

This extracts bytes and names, not native function semantics or live readiness.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import pefile

EXE_SHA = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.exe.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXE_SHA:
        raise ValueError("exact EXE mismatch")
    pe = pefile.PE(data=raw, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    rows = []
    for rva, count in ((0x432BF18, 18), (0x432BFB0, 5)):
        col_rva = struct.unpack("<Q", pe.get_data(rva - 8, 8))[0] - base
        col_raw = pe.get_data(col_rva, 24)
        signature, offset, cd_offset, type_rva, hierarchy_rva, self_rva = struct.unpack("<6I", col_raw)
        name = pe.get_data(type_rva + 16, 512).split(b"\0", 1)[0].decode("ascii")
        entries = struct.unpack("<" + "Q" * count, pe.get_data(rva, count * 8))
        rows.append({"address_point_rva": hex(rva), "col_rva": hex(col_rva), "col_bytes": col_raw.hex(),
                     "col_signature": signature, "subobject_offset": offset, "constructor_displacement": cd_offset,
                     "type_descriptor_rva": hex(type_rva), "type_name": name,
                     "hierarchy_rva": hex(hierarchy_rva), "col_self_rva": hex(self_rva),
                     "slots": [{"offset": hex(i * 8), "slot_rva": hex(rva + i * 8),
                                "target_rva": hex(value - base)} for i, value in enumerate(entries)]})
    result = {"schema": "xar.war-film-retreat-vtables.v1", "proof_layer": "exact-build-RTTI-and-vtable-bytes",
              "exe": str(args.exe.resolve()), "exe_sha256": EXE_SHA, "image_base": hex(base),
              "argv": sys.argv, "live_execution_performed": False, "automatic_semantic_verification": False,
              "vtables": rows}
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

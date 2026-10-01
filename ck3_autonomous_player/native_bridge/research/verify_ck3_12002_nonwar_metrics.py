"""Offline exact-build verifier for campaign-root scalar metrics."""
from pathlib import Path
import argparse
import hashlib
import json
import re
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from scan_anchors import PeImage, occurrences

DEFAULT_EXE = Path("Z:/ck3_mod_rewrite/artifacts/migrations/2026-09-30/post-update-1.20.0.2/installation/binaries/ck3.exe")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--dump-rva", type=lambda value:int(value,0))
    parser.add_argument("--dump-size", type=lambda value:int(value,0), default=0x100)
    parser.add_argument("--find-bytes")
    parser.add_argument("--followed-displacement", type=lambda value:int(value,0))
    args = parser.parse_args()
    data = args.exe.read_bytes()
    pe = PeImage(data)
    if args.find_bytes:
        positions = occurrences(data, bytes.fromhex(args.find_bytes.replace("_", " ")))
        if args.followed_displacement is None:
            print([hex(pe.offset_to_rva(i)) for i in positions])
        else:
            cs = Cs(CS_ARCH_X86,CS_MODE_64)
            cs.detail=True
            from capstone.x86 import X86_OP_MEM
            for i in positions:
                rva=pe.offset_to_rva(i)
                ins=list(cs.disasm(data[i:i+0x40],rva))
                if any(op.type==X86_OP_MEM and op.mem.disp==args.followed_displacement for row in ins[1:] for op in row.operands):
                    print(hex(rva), [f"{x.address:#x} {x.mnemonic} {x.op_str}" for x in ins])
        return 0
    if args.dump_rva is not None:
        off = pe.rva_to_offset(args.dump_rva)
        for ins in Cs(CS_ARCH_X86, CS_MODE_64).disasm(data[off:off+args.dump_size], args.dump_rva):
            print(f"{ins.address:#010x} {ins.bytes.hex(' ').upper():45s} {ins.mnemonic} {ins.op_str}")
        return 0
    manifest = json.loads(Path(__file__).with_name("ck3_12002_nonwar_metrics_abi.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(data).hexdigest().upper() == manifest["build"]["sha256"]
    for row in manifest["code_spans"]:
        start, size = int(row["start_rva"], 0), int(row["size"], 0)
        offset = pe.rva_to_offset(start)
        assert hashlib.sha256(data[offset:offset+size]).hexdigest().upper() == row["sha256"], row["name"]
    for row in manifest["instruction_checks"] + manifest["literal_checks"]:
        off = pe.rva_to_offset(int(row["rva"],0))
        needle = bytes.fromhex(row["bytes"])
        assert data[off:off+len(needle)] == needle, row["name"]
    print(json.dumps(dict(status="GREEN", game_version="1.20.0.2", code_spans=len(manifest["code_spans"]), instruction_checks=len(manifest["instruction_checks"]), literal_checks=len(manifest["literal_checks"]), live_verified=False)))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

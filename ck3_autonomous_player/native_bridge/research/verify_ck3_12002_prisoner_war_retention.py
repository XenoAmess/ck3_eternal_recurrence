"""Verify the exact-build readonly generic PoW input reader against frozen files."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from scan_anchors import PeImage

HERE = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    manifest = json.loads((HERE / "ck3_12002_prisoner_war_retention_abi.json").read_text(encoding="utf-8"))
    data = args.exe.read_bytes()
    sha = hashlib.sha256(data).hexdigest().upper()
    failures = []
    if sha != manifest["build"]["sha256"] or len(data) != manifest["build"]["file_size"]:
        failures.append("unsupported executable")
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    for row in manifest["instruction_checks"]:
        rva = int(row["rva"], 0)
        offset = pe.rva_to_offset(rva)
        expected = bytes.fromhex(row["bytes"])
        actual = data[offset:offset + len(expected)]
        instruction = next(decoder.disasm(actual, rva), None)
        text = f"{instruction.mnemonic} {instruction.op_str}".rstrip() if instruction else None
        if actual != expected or text != row["instruction"]:
            failures.append(f"{row['name']} {rva:#x}: {text!r}")
    for relative, rows in manifest["source_constants"].items():
        source = (HERE.parent / relative).read_text(encoding="utf-8-sig")
        for name, expected in rows.items():
            found = re.search(rf"\b{re.escape(name)}\s*=\s*(0[xX][0-9A-Fa-f]+|\d+)\s*;", source)
            if not found or int(found.group(1), 0) != int(expected, 0):
                failures.append(f"source {relative}:{name} expected {expected}")
    stock = args.exe.parents[1] / manifest["stock_script"]["path"]
    stock_bytes = stock.read_bytes()
    if hashlib.sha256(stock_bytes).hexdigest().upper() != manifest["stock_script"]["sha256"]:
        failures.append("stock script SHA differs")
    lines = stock_bytes.decode("utf-8-sig").splitlines()
    body = "\n".join(lines[manifest["stock_script"]["start_line"] - 1:manifest["stock_script"]["end_line"]])
    for fragment in manifest["stock_script"]["required_fragments"]:
        if fragment not in body:
            failures.append(f"stock effect missing {fragment}")
    result = {"status": "RED" if failures else "GREEN", "readiness": "static-ready",
              "executable_sha256": sha, "instruction_count": len(manifest["instruction_checks"]),
              "source_constant_count": sum(len(v) for v in manifest["source_constants"].values()),
              "stock_effect_lines": [1650, 1699], "local_ck3_used": False,
              "live_verified": False, "failures": failures}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())

"""Verify the offline CK3 1.20.0.2 character/trait/XP migration ABI."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from capstone import CS_ARCH_X86, CS_MODE_64, Cs

from scan_anchors import PeImage, verify


HERE = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    manifest_path = HERE / "ck3_1_20_0_2_phase_character.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures = verify(args.exe, manifest_path)
    data = args.exe.read_bytes()
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    for row in manifest["instruction_checks"]:
        rva = int(row["rva"], 0)
        offset = pe.rva_to_offset(rva)
        expected = bytes.fromhex(row["bytes"])
        actual = data[offset:offset + len(expected)]
        instruction = next(decoder.disasm(actual, rva), None)
        text = (f"{instruction.mnemonic} {instruction.op_str}".rstrip()
                if instruction is not None else None)
        if actual != expected or text != row["instruction"]:
            failures.append(f"instruction {row['name']} at {rva:#x}: {text!r}")
    header = (HERE.parent / "include/xar_bridge/ck3_12002_phase_character.hpp").read_text(
        encoding="utf-8-sig")
    for name, expected in manifest["source_constants"].items():
        match = re.search(rf"\b{re.escape(name)}\s*=\s*(0[xX][0-9A-Fa-f]+|\d+)\s*;", header)
        if match is None or int(match.group(1), 0) != int(expected, 0):
            failures.append(f"source constant {name} does not match {expected}")
    root = HERE.parents[2]
    migration = manifest["trait_key_migration"]
    for path_key, hash_key in (("frozen_authority", "authority_sha256"),
                              ("frozen_traits", "traits_sha256")):
        path = root / migration[path_key]
        if hashlib.sha256(path.read_bytes()).hexdigest().upper() != migration[hash_key]:
            failures.append(f"frozen trait input differs: {migration[path_key]}")
    lookup = (root / migration["frozen_authority"]).read_text(encoding="utf-8-sig")
    if not re.search(r"(?m)^scholar\s*=\s*erudite\s*$", lookup):
        failures.append("native scholar = erudite conversion is missing")
    source = (HERE.parent / "src/ck3_12002_phase_character.cpp").read_text(
        encoding="utf-8-sig")
    match = re.search(r"kTraitOrGroupKeys\{(.*?)\};", source, re.S)
    keys = re.findall(r'"([a-z0-9_]+)"', match.group(1)) if match else []
    concrete = [("erudite" if key == "scholar" else key)
                for key in keys if key != "physique_good"]
    concrete.extend(("physique_good_1", "physique_good_2", "physique_good_3"))
    traits = (root / migration["frozen_traits"]).read_text(encoding="utf-8-sig")
    definitions = set(re.findall(r"(?m)^([a-z0-9_]+)\s*=\s*\{", traits))
    if (len(keys) != migration["wire_operand_count"] or
            len(concrete) != migration["concrete_native_definition_count"] or
            set(concrete) - definitions):
        failures.append("new-build concrete trait definitions do not cover the wire operands")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("PASS: exact_build=1 "
          f"unique_signatures={len(manifest['signature_anchors'])} "
          f"vtable_prefixes={len(manifest['vtable_prefixes'])} "
          f"instruction_checks={len(manifest['instruction_checks'])} "
          f"source_constants={len(manifest['source_constants'])} "
          f"concrete_trait_definitions={len(concrete)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

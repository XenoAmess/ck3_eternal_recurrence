#!/usr/bin/env python3
"""Verify the exact loaded CStaticModifier lookup chain from frozen PE bytes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from scan_anchors import PeImage
from verify_gift_opinion_receivers_v1 import murmur3_x86_32


def verify(exe: Path, manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    data = exe.read_bytes()
    image = PeImage(data)
    checks = []

    def check(name: str, passed: bool) -> None:
        checks.append({"name": name, "passed": passed})

    def at(rva: str | int, size: int) -> bytes:
        offset = image.rva_to_offset(int(rva, 0) if isinstance(rva, str) else rva)
        return data[offset:offset + size]

    build = manifest["build"]
    digest = hashlib.sha256(data).hexdigest().upper()
    check("exact_executable_identity", digest == build["sha256"]
          and len(data) == build["file_size"] and image.image_base == int(build["image_base"], 0))
    for row in manifest["native_spans"]:
        first, last = int(row["first_rva"], 0), int(row["end_rva"], 0)
        check("span:" + row["name"], hashlib.sha256(at(first, last - first)).hexdigest().upper() == row["sha256"])
    for row in manifest["semantic_instructions"]:
        wanted = bytes.fromhex(row["bytes"])
        check("instruction:" + row["name"], at(row["rva"], len(wanted)) == wanted)
    for row in manifest["direct_calls"]:
        site = int(row["site_rva"], 0)
        code = at(site, 5)
        check("call:" + row["name"], code[0] == 0xE8
              and site + 5 + struct.unpack_from("<i", code, 1)[0] == int(row["target_rva"], 0))
    for row in manifest["rip_relative_bindings"]:
        site = int(row["site_rva"], 0)
        code = at(site, 7)
        check("RIP:" + row["name"], code[:2] in {b"\x48\x8b", b"\x48\x8d", b"\x4c\x8b", b"\x4c\x8d"}
              and site + 7 + struct.unpack_from("<i", code, 3)[0] == int(row["target_rva"], 0))
    for row in manifest["rtti"]:
        td = int(row["type_descriptor_rva"], 0)
        col_rva = int(row["complete_object_locator_rva"], 0)
        vt = int(row["vtable_rva"], 0)
        name = row["type_name"].encode("ascii") + b"\0"
        col = struct.unpack("<6I", at(col_rva, 24))
        check("RTTI:" + row["name"], at(td + 16, len(name)) == name
              and col[0] == 1 and col[1] == row["object_offset"]
              and col[2] == row["constructor_displacement_offset"]
              and col[3] == td and col[5] == col_rva
              and struct.unpack("<Q", at(vt - 8, 8))[0] == image.image_base + col_rva)
    row = manifest["database_primary_vtable_prefix"]
    actual = struct.unpack("<5Q", at(row["rva"], 40))
    check("database_name_by_index_vslot_0x20", [value - image.image_base for value in actual]
          == [int(value, 0) for value in row["functions"]])
    for row in manifest["fixed_keys"]:
        check("fixed_key_hash:" + row["key"], murmur3_x86_32(row["key"].encode("ascii"))
              == int(row["stable_hash_u32"], 0))
    return {"schema": "xar.ck3_12002.loaded-static-modifier-definition.verification.v1",
            "result": "GREEN" if all(row["passed"] for row in checks) else "RED",
            "exact_executable_sha256": digest,
            "abi_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest().upper(),
            "checks": checks, "ck3_launched": False, "running_process_access": False,
            "paused_live": False, "fixture_executed": False,
            "readiness": manifest["readiness"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path,
                        default=Path("Z:/ck3_mod_rewrite/artifacts/migrations/2026-09-30/post-update-1.20.0.2/installation/binaries/ck3.exe"))
    parser.add_argument("--manifest", type=Path,
                        default=Path(__file__).with_suffix(".json"))
    parser.add_argument("--output", type=Path,
                        default=Path("Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/events12002/loaded-modifier-definitions/verification.json"))
    args = parser.parse_args()
    result = verify(args.exe, args.manifest)
    result["research_script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest().upper()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode("utf-8")
    args.output.write_bytes(payload)
    print(json.dumps({"result": result["result"], "checks": len(result["checks"]),
                      "failed_checks": [row["name"] for row in result["checks"] if not row["passed"]],
                      "artifact": str(args.output), "artifact_sha256": hashlib.sha256(payload).hexdigest().upper()}))
    return 0 if result["result"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())

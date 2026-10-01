"""Verify the frozen law CanEnact/cost/reason ABI from an executable file."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from scan_anchors import PeImage


def verify(exe: Path) -> dict[str, object]:
    manifest = json.loads(Path(__file__).with_name("ck3_12002_realm_law_final_terms_abi.json").read_text(encoding="utf-8"))
    data = exe.read_bytes()
    image = PeImage(data)
    checks: list[dict[str, object]] = []
    if hashlib.sha256(data).hexdigest().upper() != manifest["build"]["sha256"] or len(data) != manifest["build"]["file_size"]:
        raise ValueError("exact realm-law executable identity mismatch")
    for span in manifest["instruction_spans"]:
        rva, end = int(span["rva"], 0), int(span["end_rva"], 0)
        offset = image.rva_to_offset(rva)
        if hashlib.sha256(data[offset:offset + end - rva]).hexdigest() != span["sha256"]:
            raise ValueError("realm-law span mismatch: " + span["name"])
        checks.append({"kind": "instruction_span", "name": span["name"], "status": "PASS"})
    for call in manifest["relative_calls"]:
        site, wanted = int(call["site"], 0), int(call["target"], 0)
        offset = image.rva_to_offset(site)
        if data[offset] != 0xE8 or site + 5 + struct.unpack_from("<i", data, offset + 1)[0] != wanted:
            raise ValueError("realm-law call edge mismatch: " + call["site"])
        checks.append({"kind": "relative_call", **call, "status": "PASS"})
    for instruction in manifest["semantic_instructions"]:
        offset = image.rva_to_offset(int(instruction["rva"], 0))
        wanted = bytes.fromhex(instruction["bytes"])
        if data[offset:offset + len(wanted)] != wanted:
            raise ValueError("realm-law semantic instruction mismatch: " + instruction["rva"])
        checks.append({"kind": "semantic_instruction", **instruction, "status": "PASS"})
    return {"schema": "xar.ck3_12002_realm_law_final_terms_static_verification.v1", "status": "GREEN", "readiness": "static-ready", "exact_executable_sha256": manifest["build"]["sha256"], "checks": checks, "ck3_launched": False, "running_process_access": False, "paused_live": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "checks": len(result["checks"]), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

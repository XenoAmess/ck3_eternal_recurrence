"""Verify frozen LIFE native anchors. No running-process or desktop access."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from scan_anchors import PeImage


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    research = Path(__file__).resolve().parent
    actions = json.loads((research / "ck3_12002_lifestyle_actions_map.json").read_text(encoding="utf-8-sig"))
    state = json.loads((research / "ck3_12002_lifestyle_state_abi.json").read_text(encoding="utf-8-sig"))
    data = args.exe.read_bytes()
    sha = hashlib.sha256(data).hexdigest().upper()
    require(sha == actions["exact_build"]["sha256"], "unexpected exact executable SHA")
    require(len(data) == actions["exact_build"]["size_bytes"], "unexpected exact executable size")
    image = PeImage(data)
    image_base = int(actions["exact_build"]["image_base"], 0)
    rows: list[dict[str, object]] = []

    def region(name: str, record: dict[str, object]) -> None:
        rva = int(str(record["new_rva"]), 0)
        length = int(str(record["length"]), 0)
        offset = image.rva_to_offset(rva)
        digest = hashlib.sha256(data[offset:offset + length]).hexdigest()
        require(digest == record["sha256"], f"anchor mismatch: {name}")
        rows.append({"kind": "bounded_native_region", "name": name, "rva": hex(rva), "bytes": length, "status": "PASS"})

    for name, record in actions["functions"].items():
        region(name, record)
    for name, record in state["current_state_functions"].items():
        region(name, record)
    for record in actions["semantic_instruction_checks"] + state["semantic_instruction_checks"]:
        rva = int(record["rva"], 0)
        expected = bytes.fromhex(record["bytes"])
        offset = image.rva_to_offset(rva)
        require(data[offset:offset + len(expected)] == expected, f"semantic instruction mismatch at {hex(rva)}")
        rows.append({"kind": "semantic_instruction", "rva": hex(rva), "meaning": record["meaning"], "status": "PASS"})
    for kind, record in actions["command_vtables"].items():
        for slot_name, target_name in (("validator_slot_rva", "validator"), ("clone_slot_rva", "clone"), ("executor_slot_rva", "execute")):
            slot = int(record[slot_name], 0)
            offset = image.rva_to_offset(slot)
            observed, = struct.unpack_from("<Q", data, offset)
            expected = image_base + int(actions["functions"][f"{kind}_{target_name}"]["new_rva"], 0)
            require(observed == expected, f"vtable slot mismatch: {kind}/{slot_name}")
            rows.append({"kind": "native_vtable_slot", "name": f"{kind}/{slot_name}", "rva": hex(slot), "status": "PASS"})
    output = {"schema": "xar.ck3_12002_lifestyle_static_verification.v1", "status": "GREEN", "readiness": "static-ready", "exact_executable_sha256": sha, "checks": rows, "ck3_launched": False, "running_process_access": False, "paused_live": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "checks": len(rows), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

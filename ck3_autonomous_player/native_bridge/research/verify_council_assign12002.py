"""Verify the frozen-file CK3 1.20 council assignment native chain."""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path
from verify_council_assignment_action_1_19_0_6 import PeImage

def check(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)

def verify(exe: Path, manifest: Path) -> dict:
    contract = json.loads(manifest.read_text(encoding="utf-8"))
    blob = exe.read_bytes()
    sha = hashlib.sha256(blob).hexdigest().upper()
    check(sha == contract["build"]["sha256"], "frozen executable mismatch")
    check(len(blob) == contract["build"]["file_size"], "file size mismatch")
    image = PeImage(exe)
    runtime = image.runtime_functions()
    for span in contract["spans"]:
        code = image.read_rva(int(span["rva"], 0), span["size"])
        check(hashlib.sha256(code).hexdigest().upper() == span["sha256"], span["name"])
        if span["runtime_function"] is not None:
            check(tuple(span["runtime_function"]) in runtime, span["name"])
    for edge in contract["edges"]:
        rva = int(edge["rva"], 0)
        code = bytes.fromhex(edge["bytes"])
        check(image.read_rva(rva, len(code)) == code, edge["name"])
        check(rva + len(code) + struct.unpack_from("<i", code, 1)[0] == int(edge["target_rva"], 0), edge["name"])
    for edge in contract["vtable_edges"]:
        pointer = struct.unpack("<Q", image.read_rva(int(edge["rva"], 0), 8))[0]
        check(pointer == image.image_base + int(edge["target_rva"], 0), "command vtable")
    for source in contract["sources"]:
        blob = (exe.parent.parent / "game" / source["path"]).read_bytes()
        check(len(blob) == source["size"], source["path"])
        check(hashlib.sha256(blob).hexdigest().upper() == source["sha256"], source["path"])
    return {"status": "GREEN", "build": "1.20.0.2", "executable_sha256": sha,
            "spans": len(contract["spans"]), "edges": len(contract["edges"]),
            "vtable_edges": len(contract["vtable_edges"]), "sources": len(contract["sources"])}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("council_assign12002_abi.json"))
    args = parser.parse_args()
    try:
        result = verify(args.exe, args.manifest)
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"status": "RED", "reason": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

"""Verify frozen native feast guest sources without any process access."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scan_anchors import PeImage


def verify(executable: Path) -> dict[str, object]:
    manifest = json.loads(Path(__file__).with_name(
        "ck3_12002_feast_guests_abi.json").read_text(encoding="utf-8-sig"))
    raw = executable.read_bytes()
    image = PeImage(raw)
    sha = hashlib.sha256(raw).hexdigest().upper()
    checks: list[dict[str, object]] = []
    failures: list[str] = []
    if sha != manifest["exact_build"]["sha256"]:
        failures.append("executable_sha256")
    if len(raw) != manifest["exact_build"]["size_bytes"]:
        failures.append("executable_size")
    for name, region in manifest["functions"].items():
        rva = int(region["rva"], 0)
        offset = image.rva_to_offset(rva)
        actual = hashlib.sha256(raw[offset:offset + region["length"]]).hexdigest()
        matched = actual == region["sha256"]
        checks.append({"kind": "native_region", "name": name,
                       "rva": region["rva"], "matched": matched})
        if not matched:
            failures.append(name)
    for anchor in manifest["semantic_instructions"]:
        rva = int(anchor["rva"], 0)
        offset = image.rva_to_offset(rva)
        expected = bytes.fromhex(anchor["bytes"])
        matched = raw[offset:offset + len(expected)] == expected
        checks.append({"kind": "semantic_instruction", "name": anchor["name"],
                       "rva": anchor["rva"], "matched": matched})
        if not matched:
            failures.append(anchor["name"])
    return {"schema": "xar.ck3_12002_feast_guests_static_verification.v1",
            "status": "GREEN" if not failures else "RED",
            "readiness": "static-ready", "executable_sha256": sha,
            "checks": checks, "failures": failures,
            "ck3_launched": False, "running_process_access": False,
            "paused_live": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": len(result["checks"]),
                      "failures": result["failures"], "output": str(args.output)}))
    return 0 if result["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())

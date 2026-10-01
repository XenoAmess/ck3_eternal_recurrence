"""Read the frozen image and verify the Feast guest-rule migration anchors."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile


def verify(executable: Path) -> dict:
    manifest_path = Path(__file__).with_name("ck3_12002_feast_guest_rule_abi.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    data = executable.read_bytes()
    digest = hashlib.sha256(data).hexdigest().upper()
    if digest != manifest["executable_sha256"]:
        raise ValueError("Feast guest-rule verifier requires the frozen 1.20.0.2 image")
    image = pefile.PE(data=data, fast_load=True)
    checked = []
    for anchor in manifest["anchors"]:
        expected = bytes.fromhex(anchor["bytes"])
        offset = image.get_offset_from_rva(int(anchor["rva"], 16))
        if data[offset:offset + len(expected)] != expected:
            raise ValueError(f"Feast guest-rule anchor mismatch: {anchor['key']}")
        checked.append(anchor["key"])
    return {"schema": "xar.ck3.12002.feast-guest-rule-abi-verification.v1",
            "status": "static-ready", "executable_sha256": digest,
            "checked_anchors": checked, "local_ck3_contacted": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.exe)
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

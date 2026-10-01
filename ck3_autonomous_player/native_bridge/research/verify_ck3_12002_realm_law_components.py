"""Read-only exact-file proof for independent 1.20.0.2 law predicates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from verify_ck3_12002_realm_law_enact_mutation import PeImage, VerificationError


def verify(executable: Path, manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(executable.read_bytes()).hexdigest().upper()
    if digest != manifest["exe_sha256"]:
        raise VerificationError("realm-law components executable SHA mismatch")
    image = PeImage(executable)
    for span in manifest["instruction_and_data_spans"]:
        actual = hashlib.sha256(image.read_rva(int(span["rva"], 0),
                                               int(span["size"], 0))).hexdigest().upper()
        if actual != span["sha256"]:
            raise VerificationError(f"span mismatch: {span['name']}")
    for entry in manifest["native_tokens"]:
        token, pointer = struct.unpack("<QQ", image.read_rva(
            int(entry["registry_rva"], 0), 16))
        if token != int(entry["token"], 0) or pointer != image.image_base + int(
                entry["literal_rva"], 0):
            raise VerificationError(f"property registry mismatch: {entry['key']}")
    for entry in manifest["native_tokens"] + manifest["native_canonical_keys"]:
        expected = entry["key"].encode("ascii") + b"\0"
        if image.read_rva(int(entry["literal_rva"], 0), len(expected)) != expected:
            raise VerificationError(f"native key mismatch: {entry['key']}")
    return {"status": "GREEN", "contract": manifest["contract"],
            "game_version": manifest["game_version"], "exe_sha256": digest,
            "spans_verified": len(manifest["instruction_and_data_spans"]),
            "property_tokens_verified": len(manifest["native_tokens"]),
            "canonical_keys_verified": len(manifest["native_canonical_keys"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name(
        "ck3_12002_realm_law_components_abi.json"))
    arguments = parser.parse_args()
    try:
        result = verify(arguments.exe, arguments.manifest)
    except (OSError, ValueError, KeyError, VerificationError) as error:
        print(json.dumps({"status": "RED", "reason": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

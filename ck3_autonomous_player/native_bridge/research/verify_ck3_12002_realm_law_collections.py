"""Check the exact CK3 binary anchors used by the private active-law reader."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile


CONTRACT = Path(__file__).with_name("ck3_12002_realm_law_collections_abi.json")


def verify(executable: Path) -> list[str]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    data = executable.read_bytes()
    build = contract["build"]
    if len(data) != build["size"]:
        raise ValueError("exact executable size mismatch")
    if hashlib.sha256(data).hexdigest().upper() != build["sha256"]:
        raise ValueError("exact executable SHA-256 mismatch")
    pe = pefile.PE(data=data, fast_load=True)
    checked: list[str] = []
    for span in contract["instruction_spans"]:
        start, end = int(span["rva"], 16), int(span["end_rva"], 16)
        actual = pe.get_data(start, end - start)
        if len(actual) != end - start:
            raise ValueError(f"{span['name']}: instruction span missing")
        if hashlib.sha256(actual).hexdigest().upper() != span["sha256"]:
            raise ValueError(f"{span['name']}: instruction span changed")
        checked.append(span["name"])
    return checked


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    names = verify(args.exe)
    print(f"ck3_12002_realm_law_collections_abi: {len(names)}/{len(names)} GREEN")


if __name__ == "__main__":
    main()

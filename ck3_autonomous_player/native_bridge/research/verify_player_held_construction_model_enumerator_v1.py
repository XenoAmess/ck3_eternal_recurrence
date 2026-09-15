"""Check the private player-held model source against the frozen local CK3 EXE."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile


HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "player_held_construction_model_enumerator_v1_abi.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    arguments = parser.parse_args()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    image_path = arguments.exe.resolve()
    binary = image_path.read_bytes()
    observed_sha = hashlib.sha256(binary).hexdigest().upper()
    if observed_sha != contract["exe_sha256"]:
        raise ValueError(f"exact EXE SHA mismatch: {observed_sha}")
    image = pefile.PE(str(image_path), fast_load=True)
    for region in contract["exact_regions"]:
        start = int(region["start_rva"], 0)
        end = int(region["end_rva_exclusive"], 0)
        offset = image.get_offset_from_rva(start)
        observed = hashlib.sha256(binary[offset:offset + end - start]).hexdigest().upper()
        if observed != region["sha256"]:
            raise ValueError(f"{region['name']} SHA mismatch: {observed}")
    print("GREEN exact CK3 1.19.0.6 player-held model source regions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

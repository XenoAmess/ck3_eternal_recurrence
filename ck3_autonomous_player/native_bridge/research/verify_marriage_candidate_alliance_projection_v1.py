"""Check the frozen CK3 1.19.0.6 candidate-alliance source and call edges."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
from pathlib import Path

from verify_marriage_container_outcome_abi_v1 import PeImage, require


HERE = Path(__file__).resolve().parent
CONTRACT = (
    HERE / "fixtures" /
    "marriage_candidate_alliance_projection_v1_source_contract.json"
)


def default_executable() -> Path:
    configured = os.environ.get("CK3_EXE")
    return (Path(configured) if configured else
            HERE.parents[3] / "Crusader Kings III" / "binaries" / "ck3.exe")


def verify(executable: Path) -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    image = PeImage(executable)
    build = contract["exact_build"]
    require(len(image.data) == build["executable_size"], "EXE size drift")
    require(hashlib.sha256(image.data).hexdigest().upper() ==
            build["executable_sha256"], "EXE SHA-256 drift")
    for span in contract["native_spans"]:
        start = int(span["rva_start"], 0)
        end = int(span["rva_end_exclusive"], 0)
        require(hashlib.sha256(image.read_rva(start, end - start))
                .hexdigest().upper() == span["sha256"],
                f"{span['name']} drift")
    for edge in contract["direct_calls"]:
        site = int(edge["site"], 0)
        target = int(edge["target"], 0)
        call = image.read_rva(site, 5)
        require(call[0] == 0xE8 and
                site + 5 + struct.unpack_from("<i", call, 1)[0] == target,
                f"direct call drift at {edge['site']}")
    site = int(contract["matrilineal_option_load_site"], 0)
    load = image.read_rva(site, 6)
    require(load[:2] == b"\x8b\x15" and
            site + 6 + struct.unpack_from("<i", load, 2)[0] ==
            int(contract["matrilineal_option_id_slot"], 0),
            "matrilineal option slot drift")
    vector = contract["candidate_vector"]
    require(vector["header_size"] == 24 and
            vector["inline_owner_bytes"] == 104 and
            vector["inline_capacity"] == 3 and
            vector["row_stride"] == 32,
            "native candidate vector contract drift")
    print("marriage candidate alliance projection v1 " +
          ("normal" if __debug__ else "optimized") + " GREEN")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=default_executable())
    args = parser.parse_args()
    verify(args.exe.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Audit the exact G3 custom-dynasty CoA record in a CK3 1.19.0.6 save.

This is deliberately an exact-build evidence reader, not a general CK3 save parser.
It freezes the binary serialization observed for the R47 semantic source and proves
that the same record occurs in both the save metadata and serialized game state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_CK3_VERSION = b"1.19.0.6"
EXPECTED_SEMANTIC_FRAGMENT_SHA256 = (
    "8C0ABD44CCA61138E830FBDEA7007EDBCFEB5A59E5A45116C13DD7A0CCD786EA"
)

# Tokenized CK3 1.19.0.6 serialization of:
# pattern_solid.dds; rgb {17 83 149}; white; black; ce_martlet.dds;
# mask {1 0 0}; position {0.37 0.61}; scale {-0.42 0.58};
# depth 1.01; rotation -23.
EXPECTED_SEMANTIC_FRAGMENT = bytes.fromhex(
    "7061747465726e5f736f6c69642e646473"
    "39050100430203001400110000001400530000001400950000000400"
    "3a0501000f0005007768697465"
    "3b0501000f000500626c61636b"
    "3f0501000300390501000f0005007768697465"
    "9f0101000f000e0063655f6d6172746c65742e646473"
    "3d05010003000c00010000000c00000000000c00000000000400"
    "4205010003004c00010003000d00a470bd3e0d00f6281c3f0400"
    "5d00010003000d003d0ad7be0d00e17a143f0400"
    "430501000d00ae47813f"
    "560101000c00e9ffffff"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--expected-checkpoint-sha256", required=True)
    parser.add_argument("--expected-source-sha256", required=True)
    parser.add_argument("--output", type=Path)
    return parser


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _all_offsets(haystack: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    cursor = 0
    while True:
        offset = haystack.find(needle, cursor)
        if offset < 0:
            return offsets
        offsets.append(offset)
        cursor = offset + len(needle)


def audit(
    checkpoint: Path,
    expected_checkpoint_sha256: str,
    expected_source_sha256: str,
) -> dict[str, object]:
    path = checkpoint.resolve()
    raw = path.read_bytes()
    checkpoint_sha256 = _sha256_bytes(raw)
    expected_sha256 = expected_checkpoint_sha256.upper()
    source_sha256 = expected_source_sha256.upper()
    if len(source_sha256) != 64 or any(
        character not in "0123456789ABCDEF" for character in source_sha256
    ):
        raise ValueError("expected source SHA-256 must be 64 hexadecimal digits")
    fragment_sha256 = _sha256_bytes(EXPECTED_SEMANTIC_FRAGMENT)
    offsets = _all_offsets(raw, EXPECTED_SEMANTIC_FRAGMENT)
    checks = {
        "checkpoint_hash_exact": checkpoint_sha256 == expected_sha256,
        "save_format_exact": raw.startswith(b"SAV010"),
        "ck3_version_exact": EXPECTED_CK3_VERSION in raw[:128],
        "semantic_fragment_definition_exact": (
            fragment_sha256 == EXPECTED_SEMANTIC_FRAGMENT_SHA256
        ),
        "metadata_record_present": any(offset < 4096 for offset in offsets),
        "game_state_record_present": any(offset >= 4096 for offset in offsets),
    }
    ok = all(checks.values())
    return {
        "schema": "xar.ck3.coa-campaign-checkpoint-audit-v1",
        "schema_version": 1,
        "status": "GREEN" if ok else "RED",
        "ok": ok,
        "checkpoint": {
            "path": str(path),
            "bytes": len(raw),
            "sha256": checkpoint_sha256,
            "format_prefix_ascii": raw[:6].decode("ascii", errors="replace"),
            "ck3_version": EXPECTED_CK3_VERSION.decode("ascii"),
        },
        "semantic_source": {
            "source_sha256": source_sha256,
            "pattern": "pattern_solid.dds",
            "colors": ["rgb { 17 83 149 }", "white", "black"],
            "emblem": "ce_martlet.dds",
            "emblem_color": "white",
            "mask": [1, 0, 0],
            "position": [0.37, 0.61],
            "scale": [-0.42, 0.58],
            "depth": 1.01,
            "rotation": -23,
        },
        "binary_semantic_fragment": {
            "bytes": len(EXPECTED_SEMANTIC_FRAGMENT),
            "sha256": fragment_sha256,
            "occurrence_count": len(offsets),
            "offsets": offsets,
            "interpretation": (
                "exact-build tokenized record; first occurrence is save metadata "
                "and later occurrence is serialized game state"
            ),
        },
        "checks": checks,
        "limitations": [
            "This audit recognizes one frozen CK3 1.19.0.6 token sequence.",
            "It does not implement a general-purpose CK3 binary save parser.",
            "It does not prove an in-campaign editor can reopen ruler or title CoA.",
        ],
    }


def main() -> int:
    args = _parser().parse_args()
    report = audit(
        args.checkpoint,
        args.expected_checkpoint_sha256,
        args.expected_source_sha256,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_name(output.name + ".tmp")
        temporary.write_text(rendered, encoding="utf-8")
        temporary.replace(output)
    print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

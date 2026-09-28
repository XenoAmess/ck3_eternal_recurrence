#!/usr/bin/env python3
"""Read-only E2-05 a03 source and future d27 checkpoint admission.

This module neither starts CK3 nor sends native requests. A successful d27
check means only that the supplied immutable save and native receipt agree;
the separate strict offline character reader determines status in those bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from e2_05_a03_character_status import StatusUnknown, verify_checkpoint_receipt


D26 = 53146848
D27 = 53146872
ACTOR = 29829
SOURCE_SAVE_SHA = "C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B"
SOURCE_RECEIPT_SHA = "78931511D31E8400334D28DAD276F4CCDFBB342A901FC00B0BAFDCDEDA29584C"
CK3_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
OLD_DLL_SHA = "EB643577E0DE6214582A667B3C6C52DB712CA75E46374BECB9DB5C36204F67E7"
OLD_INJECTOR_SHA = "CE8A20C7B25A697058AB69B03629D6B7655BB2935AD147DF1E84895A826BF247"


class GateRed(ValueError):
    def __init__(self, message: str, *, source_ready: bool = False) -> None:
        super().__init__(message)
        self.source_ready = source_ready


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GateRed(message)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _pin(path: Path, expected_sha: str) -> dict[str, Any]:
    _require(path.is_file() and not path.is_symlink(),
             f"missing or linked file: {path}")
    _require(len(expected_sha) == 64 and all(c in "0123456789ABCDEF" for c in expected_sha),
             "expected SHA-256 must be an uppercase 64-hex pin")
    before = path.stat()
    observed = _sha(path)
    after = path.stat()
    _require((before.st_size, before.st_mtime_ns) ==
             (after.st_size, after.st_mtime_ns),
             f"file changed while hashing: {path}")
    _require(observed == expected_sha, f"SHA-256 mismatch: {path}")
    return {"path": str(path.resolve()), "bytes": after.st_size, "sha256": observed}


def _json(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(result, dict), f"JSON root must be an object: {path}")
    return result


def _receipt_matches(row: dict[str, Any], save: dict[str, Any], date: int) -> None:
    checked = verify_checkpoint_receipt(
        json.dumps(row).encode("utf-8"), expected_sha=save["sha256"],
        expected_date_raw=date, actor_id=ACTOR)
    _require(checked["checkpoint_size"] == save["bytes"],
             "native checkpoint size differs from immutable copy")


def source_gate(save_path: Path, receipt_path: Path, dll_path: Path,
                injector_path: Path, expected_dll_sha: str,
                expected_injector_sha: str) -> dict[str, Any]:
    save = _pin(save_path, SOURCE_SAVE_SHA)
    receipt = _pin(receipt_path, SOURCE_RECEIPT_SHA)
    _receipt_matches(_json(receipt_path), save, D26)
    dll = _pin(dll_path, expected_dll_sha)
    injector = _pin(injector_path, expected_injector_sha)
    if dll["sha256"] == OLD_DLL_SHA:
        raise GateRed("a02 DLL predates selector ring; a03 selector admission RED",
                      source_ready=True)
    return {"source_ready": True, "selector_abi_reviewed": False,
            "live_admission": False, "source_save": save, "source_receipt": receipt,
            "candidate_dll": dll, "candidate_injector": injector,
            "next_gate": "independent exact-build selector ABI and hash-bound helper review"}


def d27_checkpoint_gate(save_path: Path, expected_save_sha: str,
                        receipt_path: Path, expected_receipt_sha: str,
                        advance_path: Path, expected_advance_sha: str) -> dict[str, Any]:
    save = _pin(save_path, expected_save_sha)
    receipt = _pin(receipt_path, expected_receipt_sha)
    advance = _pin(advance_path, expected_advance_sha)
    _require(save["sha256"] != SOURCE_SAVE_SHA, "d26 source bytes are not a d27 save")
    _receipt_matches(_json(receipt_path), save, D27)
    step = _json(advance_path)
    values = step.get("post_values") or {}
    _require(step.get("mode") == "advance" and step.get("track") == "e2-05-d26" and
             step.get("result") == "ONE_DAY_ADVANCED_UNREVIEWED" and
             values.get("date_raw") == D27 and values.get("paused") is True and
             values.get("actor") == ACTOR and type(values.get("revision")) is int and
             isinstance(step.get("trace_finish"), dict) and
             isinstance(step.get("one_day"), dict),
             "advance trail does not prove one paused d27 frame and trace finish")
    return {"saved_day27_bytes_verified": True, "character_status_proven": False,
            "selector_numbers_proven": False, "live_admission": False,
            "day27_save": save, "day27_receipt": receipt,
            "advance_report": advance,
            "next_gate": "strict offline character reader with these independent save/receipt pins"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    source = sub.add_parser("source")
    source.add_argument("--save", type=Path, required=True)
    source.add_argument("--receipt", type=Path, required=True)
    source.add_argument("--dll", type=Path, required=True)
    source.add_argument("--injector", type=Path, required=True)
    source.add_argument("--expected-dll-sha256", required=True)
    source.add_argument("--expected-injector-sha256", required=True)
    post = sub.add_parser("d27")
    post.add_argument("--save", type=Path, required=True)
    post.add_argument("--expected-save-sha256", required=True)
    post.add_argument("--receipt", type=Path, required=True)
    post.add_argument("--expected-receipt-sha256", required=True)
    post.add_argument("--advance", type=Path, required=True)
    post.add_argument("--expected-advance-sha256", required=True)
    args = parser.parse_args()
    try:
        if args.mode == "source":
            result = source_gate(args.save, args.receipt, args.dll, args.injector,
                                 args.expected_dll_sha256, args.expected_injector_sha256)
        else:
            result = d27_checkpoint_gate(args.save, args.expected_save_sha256,
                                         args.receipt, args.expected_receipt_sha256,
                                         args.advance, args.expected_advance_sha256)
    except (GateRed, StatusUnknown, OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"source_ready": getattr(error, "source_ready", False),
                          "live_admission": False,
                          "status": "RED", "reason": str(error)}))
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

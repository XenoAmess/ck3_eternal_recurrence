#!/usr/bin/env python3
"""Verify WAR31 prestige's accumulated (fame) ledger in exact paired saves.

The historical material report already authenticated the two Rakaly melts.
This additive, read-only projection verifies that report and both text hashes
again, then parses only the two named character blocks.  It does not assign
the six-day net change to a particular same-frame writer.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re


MATERIAL_REPORT_SHA256 = "84154554437CE96FB751DC6DB23E65847CA974CD92917A2FCB32B12C3FC11634"
SCALE = 100_000
_DECIMAL = re.compile(rb"-?(?:0|[1-9][0-9]*)(?:\.[0-9]{1,5})?")


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest().upper()


def _fixed(raw: bytes) -> int:
    if _DECIMAL.fullmatch(raw) is None:
        raise ValueError("prestige ledger is not a CK3 decimal")
    try:
        value = Decimal(raw.decode("ascii")) * SCALE
    except (UnicodeDecodeError, InvalidOperation) as error:
        raise ValueError("prestige ledger decimal failed") from error
    if value != value.to_integral_value() or not -(2**63) <= value <= 2**63 - 1:
        raise ValueError("prestige ledger loses fixed-point precision")
    return int(value)


def read_prestige_ledger(
    melted: Path, *, character_id: int, line_start: int, line_end: int,
) -> dict[str, int]:
    """Read only one hashed melted-save character block, including fame."""

    if not 0 < character_id <= 2**31 - 1 or not 1 < line_start < line_end:
        raise ValueError("invalid character block locator")
    target_start = f"\t{character_id}={{".encode()
    in_prestige = False
    found_start = False
    found_end = False
    ledger: dict[str, int] = {}
    with melted.open("rb") as stream:
        for number, line in enumerate(stream, 1):
            if number < line_start:
                continue
            if number > line_end:
                break
            stripped = line.rstrip(b"\r\n")
            if number == line_start:
                if stripped != target_start:
                    raise ValueError("character block start drifted")
                found_start = True
            elif number == line_end:
                if stripped != b"\t}" or in_prestige:
                    raise ValueError("character block end drifted")
                found_end = True
            elif stripped == b"\t\t\tprestige={":
                if in_prestige or ledger:
                    raise ValueError("duplicate prestige block")
                in_prestige = True
            elif in_prestige and stripped == b"\t\t\t}":
                in_prestige = False
            elif in_prestige:
                for key in ("currency", "accumulated"):
                    prefix = f"\t\t\t\t{key}=".encode()
                    if stripped.startswith(prefix):
                        if key in ledger:
                            raise ValueError(f"duplicate prestige {key}")
                        ledger[key] = _fixed(stripped[len(prefix):])
    if not found_start or not found_end or set(ledger) != {"currency", "accumulated"}:
        raise ValueError("complete prestige ledger was not observed")
    return ledger


def project(material_report_path: Path) -> dict[str, object]:
    if digest(material_report_path) != MATERIAL_REPORT_SHA256:
        raise ValueError("WAR31 historical material report hash mismatch")
    report = json.loads(material_report_path.read_text(encoding="utf-8"))
    if report.get("schema") != "xar.ck3.war31.save-material.v1":
        raise ValueError("WAR31 historical material report schema mismatch")
    ledgers: dict[str, dict[str, dict[str, int]]] = {}
    sources: dict[str, dict[str, str]] = {}
    for stage in ("before", "after"):
        source = report["sources"][stage]
        melted = Path(source["melted_path"])
        if digest(melted) != source["melted_sha256"]:
            raise ValueError(f"{stage} melted save SHA-256 mismatch")
        sources[stage] = {
            "save_sha256": source["save_sha256"],
            "melted_sha256": source["melted_sha256"],
            "save_date": report[stage]["save_date"],
        }
        stage_ledgers = {}
        for character_id in (29829, 30097):
            row = report[stage]["characters"][str(character_id)]
            ledger = read_prestige_ledger(
                melted,
                character_id=character_id,
                line_start=row["line_start"],
                line_end=row["line_end"],
            )
            if ledger["currency"] != row["resources"]["prestige"]["raw"]:
                raise ValueError("prestige currency disagrees with existing report")
            stage_ledgers[str(character_id)] = ledger
        ledgers[stage] = stage_ledgers
    delta = {
        str(character_id): {
            key: ledgers["after"][str(character_id)][key]
            - ledgers["before"][str(character_id)][key]
            for key in ("currency", "accumulated")
        }
        for character_id in (29829, 30097)
    }
    return {
        "schema": "xar.ck3.war31.prestige-fame-save-delta.v1",
        "historical_material_report_sha256": MATERIAL_REPORT_SHA256,
        "sources": sources,
        "scale": SCALE,
        "ledgers": ledgers,
        "signed_delta_raw": delta,
        "same_native_frame_binding": False,
        "causal_attribution": "six_day_persisted_net_change_only",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--material-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = project(args.material_report)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

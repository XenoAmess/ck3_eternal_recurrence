#!/usr/bin/env python3
"""Read WAR31 title and character resources from exact-build CK3 saves.

This is an offline save projection. It does not claim a live native revision,
personal vassal relationship, or persisted truce without a separate observer.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile


GAME_VERSION = "1.19.0.6"
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
RAKALY_SHA256 = "E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D"
R0197_SAVE_SHA256 = "1AF4055F978AF60267FB3A0D8658224047CD6BFDA884C66886A13B74EE34A90A"
TARGET_TITLE_ID = 2128
CHARACTER_IDS = (29829, 30097)
SCALE = 100_000
_TITLE_START = re.compile(rb"\t\t([1-9][0-9]*)=\{\r?\n$")
_CHARACTER_START = re.compile(rb"\t([1-9][0-9]*)=\{\r?\n$")
_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]{1,5})?")
_DATE = re.compile(r"[0-9]{1,4}\.(?:[1-9]|1[0-2])\.(?:[1-9]|[12][0-9]|3[01])")


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest().upper()


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _int_field(raw: bytes, *, field: str) -> int:
    _require(raw.isdigit() and raw != b"0", f"{field} is not a positive ID")
    value = int(raw)
    _require(value <= 2**31 - 1, f"{field} exceeds signed int32")
    return value


def _fixed(raw: bytes, *, field: str) -> int:
    try:
        text = raw.decode("ascii")
        _require(_DECIMAL.fullmatch(text) is not None, f"{field} is not a save decimal")
        value = Decimal(text) * SCALE
    except (UnicodeDecodeError, InvalidOperation) as error:
        raise ValueError(f"{field} is not a save decimal") from error
    _require(value == value.to_integral_value(), f"{field} lost precision")
    number = int(value)
    _require(-(2**63) <= number <= 2**63 - 1, f"{field} exceeds int64")
    return number


def _record_field(record: dict, key: str, value: object, *, line: int) -> None:
    _require(key not in record, f"duplicate {key} in save at line {line}")
    record[key] = value


def project_melted(path: Path) -> dict[str, object]:
    """Stream only scoped title and living-character records from Rakaly text."""
    metadata: dict[str, str] = {}
    titles: dict[int, dict[str, object]] = {}
    characters: dict[int, dict[str, object]] = {}
    section: str | None = None
    in_title_table = False
    current_title: int | None = None
    current_character: int | None = None
    active_resource: str | None = None
    active_alive = False
    needed_character_ids = set(CHARACTER_IDS)
    with path.open("rb") as stream:
        header = stream.readline()
        _require(header.startswith(b"SAV") and header.rstrip(b"\r\n")[3:].isalnum(),
                 "Rakaly output is not a text SAV file")
        for line_number, line in enumerate(stream, 2):
            stripped = line.strip()
            if line in (b"meta_data={\n", b"meta_data={\r\n"):
                _require(section is None, "duplicate or nested meta_data")
                section = "meta_data"
                continue
            if line in (b"landed_titles={\n", b"landed_titles={\r\n"):
                _require(section is None, "duplicate or nested landed_titles")
                section = "landed_titles"
                continue
            if line in (b"living={\n", b"living={\r\n"):
                _require(section is None, "duplicate or nested living")
                section = "living"
                continue
            if section is not None and line in (b"}\n", b"}\r\n"):
                _require(current_title is None and current_character is None,
                         "unterminated scoped save record")
                section = None
                in_title_table = False
                continue
            if section == "meta_data":
                for key in (b"version", b"meta_date"):
                    prefix = b"\t" + key + b"="
                    if line.startswith(prefix):
                        value = stripped[len(key) + 1:].strip(b'"').decode("ascii")
                        _record_field(metadata, key.decode(), value, line=line_number)
                continue
            if section is None:
                if line.startswith(b"date="):
                    _record_field(metadata, "date", stripped[5:].decode("ascii"), line=line_number)
                continue
            if section == "landed_titles":
                if line in (b"\tlanded_titles={\n", b"\tlanded_titles={\r\n"):
                    _require(not in_title_table, "duplicate title table")
                    in_title_table = True
                    continue
                if in_title_table and line in (b"\t}\n", b"\t}\r\n"):
                    _require(current_title is None, "unterminated title")
                    in_title_table = False
                    continue
                if not in_title_table:
                    continue
                match = _TITLE_START.fullmatch(line)
                if match:
                    _require(current_title is None, "nested title record")
                    current_title = _int_field(match.group(1), field="title ID")
                    _require(current_title not in titles, "duplicate title ID")
                    titles[current_title] = {"line_start": line_number}
                    continue
                if current_title is None:
                    continue
                if line in (b"\t\t}\n", b"\t\t}\r\n"):
                    titles[current_title]["line_end"] = line_number
                    if current_title == TARGET_TITLE_ID:
                        holder_id = titles[current_title].get("holder")
                        if isinstance(holder_id, int):
                            needed_character_ids.add(holder_id)
                    current_title = None
                    continue
                if line.startswith(b"\t\t\t") and not line.startswith(b"\t\t\t\t"):
                    for key in (b"key", b"holder", b"de_facto_liege"):
                        prefix = b"\t\t\t" + key + b"="
                        if line.startswith(prefix):
                            raw = stripped[len(key) + 1:]
                            value = (raw.strip(b'"').decode("ascii") if key == b"key"
                                     else _int_field(raw, field=key.decode()))
                            _record_field(titles[current_title], key.decode(), value,
                                          line=line_number)
                continue
            if section == "living":
                match = _CHARACTER_START.fullmatch(line)
                if match:
                    _require(current_character is None, "nested living character")
                    character_id = _int_field(match.group(1), field="character ID")
                    current_character = character_id
                    if character_id in needed_character_ids:
                        _require(character_id not in characters, "duplicate character ID")
                        characters[character_id] = {"line_start": line_number}
                    continue
                if current_character is None:
                    continue
                if line in (b"\t}\n", b"\t}\r\n"):
                    if current_character in characters:
                        characters[current_character]["line_end"] = line_number
                    current_character = None
                    active_resource = None
                    active_alive = False
                    continue
                if current_character not in needed_character_ids:
                    continue
                record = characters[current_character]
                if line.startswith(b"\t\tfirst_name="):
                    _record_field(record, "first_name",
                                  stripped[len(b"first_name="):].strip(b'"').decode("utf-8"),
                                  line=line_number)
                elif line in (b"\t\talive_data={\n", b"\t\talive_data={\r\n"):
                    active_alive = True
                elif active_alive and line in (b"\t\t}\n", b"\t\t}\r\n"):
                    active_alive = False
                elif active_alive and line.startswith(b"\t\t\t"):
                    for resource in ("gold", "piety", "prestige"):
                        prefix = b"\t\t\t" + resource.encode() + b"={"
                        if stripped == prefix.strip():
                            _require(active_resource is None, "nested resource block")
                            _require(resource not in record, "duplicate resource block")
                            active_resource = resource
                            record[resource] = {}
                    if active_resource is not None:
                        if line in (b"\t\t\t}\n", b"\t\t\t}\r\n"):
                            active_resource = None
                        elif line.startswith(b"\t\t\t\t") and not line.startswith(b"\t\t\t\t\t"):
                            wanted = "value" if active_resource == "gold" else "currency"
                            prefix = b"\t\t\t\t" + wanted.encode() + b"="
                            if line.startswith(prefix):
                                _record_field(record[active_resource], "raw",
                                              _fixed(stripped[len(wanted) + 1:], field=active_resource),
                                              line=line_number)
    _require(section is None and current_title is None and current_character is None,
             "truncated scoped save")
    _require(metadata.get("version") == GAME_VERSION, "CK3 save version differs")
    _require(metadata.get("date") == metadata.get("meta_date") and
             _DATE.fullmatch(metadata.get("date", "")) is not None,
             "CK3 save date missing or inconsistent")
    _require(TARGET_TITLE_ID in titles, "target title 2128 absent")
    target = titles[TARGET_TITLE_ID]
    _require(isinstance(target.get("holder"), int), "target title holder absent")
    holder = target["holder"]
    liege_title = target.get("de_facto_liege")
    _require(liege_title is None or liege_title in titles,
             "target de facto liege title missing")
    if liege_title is not None:
        _require(isinstance(titles[liege_title].get("holder"), int),
                 "de facto liege title holder missing")
    children = [
        {"title_id": title_id, "holder_character_id": row.get("holder"),
         "key": row.get("key")}
        for title_id, row in titles.items()
        if row.get("de_facto_liege") == TARGET_TITLE_ID
    ]
    children.sort(key=lambda row: row["title_id"])
    for character_id in CHARACTER_IDS:
        _require(character_id in characters, f"character {character_id} absent")
        row = characters[character_id]
        for resource in ("gold", "piety", "prestige"):
            _require(isinstance(row.get(resource), dict) and
                     isinstance(row[resource].get("raw"), int),
                     f"character {character_id} {resource} absent")
    return {
        "save_version": metadata["version"],
        "save_date": metadata["date"],
        "target_title": {
            "title_id": TARGET_TITLE_ID,
            "key": target.get("key"),
            "holder_character_id": holder,
            "holder_first_name": characters.get(holder, {}).get("first_name"),
            "de_facto_liege_title_id": liege_title,
            "de_facto_liege_title_holder_character_id": (
                titles[liege_title]["holder"] if liege_title is not None else None
            ),
            "direct_de_facto_child_titles": children,
            "line_start": target["line_start"],
            "line_end": target["line_end"],
        },
        "characters": {
            str(character_id): {
                "character_id": character_id,
                "first_name": characters[character_id].get("first_name"),
                "resources": {
                    resource: {"raw": characters[character_id][resource]["raw"],
                               "scale": SCALE}
                    for resource in ("gold", "piety", "prestige")
                },
                "line_start": characters[character_id]["line_start"],
                "line_end": characters[character_id]["line_end"],
            }
            for character_id in CHARACTER_IDS
        },
        "holder_personal_liege": {"status": "unavailable", "reason": "title_de_facto_liege_is_not_a_personal_liege_read"},
        "holder_personal_vassals": {"status": "unavailable", "reason": "direct_child_titles_are_not_a_complete_personal_vassal_set"},
        "persisted_truce": {"status": "unavailable", "reason": "truce_save_schema_not_proven_for_war31"},
    }


def _verify_melt(source: Path, melted: Path, rakaly: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="ck3-war31-melt-") as directory:
        reproduced = Path(directory) / "melted.ck3"
        result = subprocess.run(
            [str(rakaly), "melt", str(source), "--format", "ck3", "-o", str(reproduced)],
            capture_output=True, text=True, check=False,
        )
        _require(result.returncode == 0 and reproduced.is_file(),
                 f"Rakaly melt failed: {result.stderr[-500:]}")
        _require(digest(reproduced) == digest(melted),
                 "melted text does not derive from source save")


def project_pair(before_save: Path, before_melted: Path, after_save: Path,
                 after_melted: Path, *, rakaly: Path, exe: Path) -> dict[str, object]:
    _require(digest(exe) == EXE_SHA256, "CK3 EXE SHA-256 mismatch")
    _require(digest(rakaly) == RAKALY_SHA256, "Rakaly 0.8.19 SHA-256 mismatch")
    _require(digest(before_save) == R0197_SAVE_SHA256,
             "before save is not the frozen R0197 checkpoint")
    _verify_melt(before_save, before_melted, rakaly)
    _verify_melt(after_save, after_melted, rakaly)
    before = project_melted(before_melted)
    after = project_melted(after_melted)
    _require(tuple(int(part) for part in after["save_date"].split(".")) >=
             tuple(int(part) for part in before["save_date"].split(".")),
             "after save predates before save")
    resource_deltas = {
        str(character_id): {
            resource: {
                "signed_delta_raw": (
                    after["characters"][str(character_id)]["resources"][resource]["raw"]
                    - before["characters"][str(character_id)]["resources"][resource]["raw"]
                ),
                "scale": SCALE,
            }
            for resource in ("gold", "piety", "prestige")
        }
        for character_id in CHARACTER_IDS
    }
    return {
        "schema": "xar.ck3.war31.save-material.v1",
        "game_version": GAME_VERSION,
        "exe_sha256": EXE_SHA256,
        "rakaly_sha256": RAKALY_SHA256,
        "sources": {
            stage: {
                "save_path": str(source), "save_sha256": digest(source),
                "melted_path": str(melted), "melted_sha256": digest(melted),
                "melt_verified": True,
            }
            for stage, source, melted in (
                ("before", before_save, before_melted),
                ("after", after_save, after_melted),
            )
        },
        "before": before,
        "after": after,
        "title_holder_changed": (
            before["target_title"]["holder_character_id"] !=
            after["target_title"]["holder_character_id"]
        ),
        "signed_resource_deltas": resource_deltas,
        "same_native_frame_binding": False,
        "personal_liege_vassals_observed": False,
        "persisted_truce_observed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before-save", required=True, type=Path)
    parser.add_argument("--before-melted", required=True, type=Path)
    parser.add_argument("--after-save", required=True, type=Path)
    parser.add_argument("--after-melted", required=True, type=Path)
    parser.add_argument("--rakaly-exe", required=True, type=Path)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = project_pair(args.before_save, args.before_melted,
                          args.after_save, args.after_melted,
                          rakaly=args.rakaly_exe, exe=args.exe)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output),
                      "title_holder_changed": report["title_holder_changed"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

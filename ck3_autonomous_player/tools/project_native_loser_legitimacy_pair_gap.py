#!/usr/bin/env python3
"""Audit frozen Messina legitimacy sources without attributing an effect.

The check-sidecar mode re-reads every referenced source.  The optional
verify-melt mode also re-runs exact Rakaly against each raw save in a temporary
directory and checks that the stored plaintext is its deterministic output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


RAKALY_SHA256 = "E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D"
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
ATTEMPTS = {
    "004": "episode01-full-edge-attempt-004",
    "021": "episode01-terminal-loss-live-attempt-021",
    "024": "episode01-denominator-live-attempt-024",
    "072": "episode01-winner-ai-reentry-v2-attempt-072",
    "074": "episode01-winner-ai-postsubmit-movement-attempt-074",
}
SAVE_CASES = {
    "004-day25": ("004", "trace-d25-immutable.ck3"),
    "004-day26": ("004", "trace-d26-immutable.ck3"),
    "004-day27": ("004", "trace-d27-immutable.ck3"),
    "004-seed": ("004", "ck3-state/profile/save games/xar_episode_seed.ck3"),
    "004-war-film-checkpoint": ("004", "ck3-state/profile/save games/war_film_checkpoint.ck3"),
    "072-war-film-checkpoint": ("072", "ck3-state/profile/save games/war_film_checkpoint.ck3"),
    **{f"{tag}-autosave": (tag, "ck3-state/profile/save games/autosave.ck3") for tag in ATTEMPTS},
}
RECEIPTS = {
    "004-d27": ("004", "trace-d27-after-snapshot.json"),
    "004-d32": ("004", "term-d32-snapshot.json"),
    "004-terminal": ("004", "term-d32-terminal.json"),
    "021-d32": ("021", "d32-snapshot.json"),
    "021-terminal": ("021", "d32-terminal.json"),
    "024-d32": ("024", "d32-snapshot.json"),
    "024-terminal": ("024", "d32-terminal.json"),
    "072-d25": ("072", "25-snapshot.json"),
    "072-d26": ("072", "26-snapshot.json"),
    "072-terminal": ("072", "26-winner-terminal-a.json"),
    "074-d25": ("074", "25-snapshot.json"),
    "074-d26": ("074", "26-snapshot.json"),
    "074-d27": ("074", "27-snapshot.json"),
    "074-terminal": ("074", "26-winner-terminal-a.json"),
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def parsed_save(path: Path) -> dict:
    dates: dict[str, str] = {}
    characters: dict[str, dict] = {}
    current: str | None = None
    record: dict | None = None
    with path.open("r", encoding="utf-8-sig", errors="strict") as stream:
        for line_no, line in enumerate(stream, 1):
            value = line.strip()
            if line_no < 1500 and value.startswith(("meta_date=", "date=")):
                key, date = value.split("=", 1)
                require(key not in dates, f"{path}: repeated {key}")
                dates[key] = date
            if current is None:
                if line.startswith("\t29829={") or line.startswith("\t31549={"):
                    current = line.split("=", 1)[0].strip()
                    require(current not in characters, f"{path}: repeated CharacterID {current}")
                    record = {"line_start": line_no}
                continue
            if line.startswith("\t}"):
                assert record is not None
                record["line_end"] = line_no
                characters[current] = record
                current = None
                record = None
                continue
            if value.startswith(("first_name=", "legitimacy=", "legitimacy_type=")):
                assert record is not None
                key, raw = value.split("=", 1)
                require(key not in record, f"{path}: repeated {current}.{key}")
                record[key] = {"line": line_no, "value": raw.strip('"')}
    require(dates.get("date") == dates.get("meta_date") and bool(dates.get("date")), f"{path}: save date missing/mismatched")
    require(set(characters) == {"29829", "31549"}, f"{path}: character identities missing")
    for character_id, name, legitimacy, kind in (
        ("29829", "Robert", "321", "duke_legitimacy"),
        ("31549", "Ali", "100", "count_legitimacy"),
    ):
        fields = characters[character_id]
        require(fields["first_name"]["value"] == name, f"{path}: CharacterID {character_id} name changed")
        require(fields["legitimacy"]["value"] == legitimacy, f"{path}: CharacterID {character_id} legitimacy changed")
        require(fields["legitimacy_type"]["value"] == kind, f"{path}: CharacterID {character_id} legitimacy type changed")
    return {"dates": dates, "characters": characters}


def any_legitimacy_key(obj: object) -> bool:
    if isinstance(obj, dict):
        return any("legitimacy" in str(key).casefold() or any_legitimacy_key(value) for key, value in obj.items())
    if isinstance(obj, list):
        return any(any_legitimacy_key(value) for value in obj)
    return False


def build(evidence_root: Path, melt_root: Path, rakaly_exe: Path, verify_melt: bool) -> dict:
    require(digest(rakaly_exe) == RAKALY_SHA256, "Rakaly 0.8.19 EXE SHA mismatch")
    inventory: dict[str, list[dict]] = {}
    for tag, name in ATTEMPTS.items():
        base = evidence_root / name
        saves = sorted((base / "ck3-state" / "profile").rglob("*.ck3"))
        require(bool(saves), f"attempt {tag}: no source saves")
        inventory[tag] = [{"relative_path": str(path.relative_to(base)).replace("\\", "/"),
                           "sha256": digest(path)} for path in saves]
    save_rows = {}
    for key, (tag, relative) in SAVE_CASES.items():
        source = evidence_root / ATTEMPTS[tag] / relative
        melted = melt_root / f"{key}-melted.ck3"
        source_sha = digest(source)
        melted_sha = digest(melted)
        if verify_melt:
            with tempfile.TemporaryDirectory(prefix="ck3-legitimacy-melt-") as directory:
                reproduced = Path(directory) / "melted.ck3"
                command = [str(rakaly_exe), "melt", str(source), "--format", "ck3", "-o", str(reproduced)]
                result = subprocess.run(command, capture_output=True, text=True, check=False)
                require(result.returncode == 0 and reproduced.is_file(), f"{key}: Rakaly melt failed: {result.stderr[-500:]}")
                require(digest(reproduced) == melted_sha, f"{key}: melted file does not derive from raw source")
        save_rows[key] = {
            "source_relative_path": f"{ATTEMPTS[tag]}/{relative}",
            "source_sha256": source_sha,
            "melted_file": melted.name,
            "melted_sha256": melted_sha,
            **parsed_save(melted),
        }
    known_source_hashes = {row["source_sha256"] for row in save_rows.values()}
    for tag, rows in inventory.items():
        require({row["sha256"] for row in rows}.issubset(known_source_hashes),
                f"attempt {tag}: profile has an unclassified save")
        lookup = {row["relative_path"]: row["sha256"] for row in rows}
        require(lookup["ck3-state/profile/last_save.ck3"] ==
                lookup["ck3-state/profile/save games/autosave.ck3"],
                f"attempt {tag}: last_save differs from classified autosave")
    receipt_rows = {}
    for key, (tag, filename) in RECEIPTS.items():
        relative = f"{ATTEMPTS[tag]}/ck3-output/interactive-requests-responses/{filename}"
        path = evidence_root / relative
        raw = path.read_bytes()
        envelope = json.loads(raw)
        require(envelope.get("result") == "CALL_COMPLETED", f"{key}: response failed")
        body = envelope.get("body")
        require(not any_legitimacy_key(body), f"{key}: legitimacy is available; revise audit")
        wars = body.get("active_wars", []) if isinstance(body, dict) else []
        war4 = next((war for war in wars if isinstance(war, dict) and war.get("war_id") == 4), None)
        receipt_rows[key] = {
            "relative_path": relative,
            "sha256": hashlib.sha256(raw).hexdigest().upper(),
            "at_utc": envelope.get("at"),
            "date_raw": body.get("date_raw") if isinstance(body, dict) else None,
            "played_character_id": (body.get("played_character") or {}).get("character_id") if isinstance(body, dict) else None,
            "war4_player_side": war4.get("player_side") if war4 else None,
            "war4_primary_opponent_character_id": war4.get("primary_opponent_character_id") if war4 else None,
            "legitimacy_key_found": False,
        }
    def calendar_tuple(date: str) -> tuple[int, int, int]:
        return tuple(int(part) for part in date.split("."))

    require(all(calendar_tuple(row["dates"]["date"]) < (1067, 1, 4)
                for row in save_rows.values()), "post-terminal source save found")
    require(all(row["dates"]["date"] == "1067.1.1" for key, row in save_rows.items() if key.endswith("autosave")), "post-terminal autosave found")
    require({receipt_rows[f"{tag}-d32"]["date_raw"] for tag in ("004", "021", "024")} == {53146992}, "old terminal dates differ")
    require({receipt_rows[f"{tag}-d26"]["date_raw"] for tag in ("072", "074")} == {53146992}, "new terminal dates differ")
    require(receipt_rows["074-d27"]["date_raw"] == 53147016, "074 next-day date differs")
    require(all(receipt_rows[f"{tag}-d32"]["played_character_id"] == 29829 for tag in ("004", "021", "024")), "old played identity differs")
    require(all(receipt_rows[f"{tag}-d26"]["played_character_id"] == 31549 for tag in ("072", "074")), "new played identity differs")
    return {
        "schema": "ck3.normal_result_loser_legitimacy_pair_gap.v2",
        "game_build": "1.19.0.6",
        "exe_sha256": EXE_SHA256,
        "rakaly_version": "0.8.19",
        "rakaly_exe_sha256": RAKALY_SHA256,
        "terminal_date_raw": 53146992,
        "loser_primary_character_id": 29829,
        "winner_primary_character_id": 31549,
        "source_save_inventory": inventory,
        "source_saves": save_rows,
        "formal_receipts": receipt_rows,
        "preterminal_loser_legitimacy": 321,
        "postterminal_same_character_legitimacy_available": False,
        "legitimacy_effect_attributed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--melt-root", required=True, type=Path)
    parser.add_argument("--rakaly-exe", required=True, type=Path)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--verify-melt", action="store_true")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--check-sidecar", type=Path)
    args = parser.parse_args()
    require(digest(args.exe) == EXE_SHA256, "CK3 EXE SHA mismatch")
    report = build(args.evidence_root, args.melt_root, args.rakaly_exe, args.verify_melt)
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    else:
        expected = json.loads(args.check_sidecar.read_text(encoding="utf-8"))
        require(report == expected, "sidecar differs from raw evidence")
    print(json.dumps({"status": "source_pair_gap_verified", "source_saves": len(report["source_saves"]),
                      "formal_receipts": len(report["formal_receipts"]),
                      "loser_character_id": 29829, "preterminal_legitimacy": 321,
                      "postterminal_legitimacy_available": False,
                      "effect_attributed": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

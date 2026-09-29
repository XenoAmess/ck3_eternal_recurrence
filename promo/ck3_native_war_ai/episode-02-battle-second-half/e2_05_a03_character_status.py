"""Strict, offline CK3 checkpoint life-status reader for one CharacterID.

This is a research candidate. It never starts CK3 or infers status from combat
events. A report describes only the supplied, hash-pinned saved state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


RAKALY_VERSION = "0.8.19"
RAKALY_SHA256 = "E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D"
CK3_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
TOKEN = re.compile(rb'\s+|\#[^\n]*|"(?:\\.|[^"\\])*"|[{}=]|[^\s{}=#"]+')
SHA256 = re.compile(r"[0-9A-Fa-f]{64}\Z")
SAVE_DATE = re.compile(rb"[0-9]{1,4}\.[0-9]{1,2}\.[0-9]{1,2}\Z")


class StatusUnknown(ValueError):
    """The saved state cannot prove the requested character status."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def read_regular(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise StatusUnknown(f"not a regular, non-symlink file: {path}")
    return path.read_bytes()


def pinned_sha(value: str) -> str:
    if not SHA256.fullmatch(value):
        raise StatusUnknown("expected SHA-256 must be 64 hex characters")
    return value.upper()


def _text(value: bytes) -> str:
    try:
        result = value.decode("utf-8")
        if result.startswith('"') and result.endswith('"'):
            result = json.loads(result)
        return result
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StatusUnknown("invalid text scalar") from exc


def parse_melted(data: bytes, character_id: int, expected_date: str) -> dict[str, object]:
    """Parse a unique direct child of the unique top-level living database.

    Braces, quotes, comments and assignment depth are scanned for the complete
    melted file. This deliberately refuses ambiguous or malformed structure.
    """
    if character_id <= 0:
        raise StatusUnknown("CharacterID must be positive")
    if not SAVE_DATE.fullmatch(expected_date.encode("ascii")):
        raise StatusUnknown("invalid expected save date")
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    stack: list[tuple[bytes | None, int]] = []
    pending_key: bytes | None = None
    previous: bytes | None = None
    cursor = 0
    date_values: list[bytes] = []
    date_assignments = 0
    living_assignments = 0
    target_assignments = 0
    living_count = 0
    target_count = 0
    target_start: int | None = None
    target_end: int | None = None
    status_blocks: list[tuple[bytes, int]] = []
    status_end: int | None = None
    status_shadow = False
    death_fields: dict[bytes, list[bytes]] = {key: [] for key in (b"date", b"reason", b"killer")}
    death_field_assignments: dict[bytes, int] = {key: 0 for key in death_fields}
    death_field_shadow = False
    target_name = str(character_id).encode("ascii")

    for match in TOKEN.finditer(data):
        if match.start() != cursor:
            raise StatusUnknown(f"invalid melted token at byte {cursor}")
        cursor = match.end()
        token = match.group()
        if token[:1].isspace() or token.startswith(b"#"):
            continue
        if token == b"=":
            if pending_key is not None or previous is None or previous in (b"=", b"{", b"}"):
                raise StatusUnknown("invalid assignment")
            pending_key = previous
            if not stack and pending_key == b"date":
                date_assignments += 1
            if not stack and pending_key == b"living":
                living_assignments += 1
            if len(stack) == 1 and stack[0][0] == b"living" and pending_key == target_name:
                target_assignments += 1
            if (target_start is not None and target_end is None
                    and pending_key in death_field_assignments
                    and len(stack) == 3 and stack[2][0] == b"dead_data"):
                death_field_assignments[pending_key] += 1
            previous = token
            continue
        if token == b"{":
            key = pending_key
            if key == b"living" and not stack:
                living_count += 1
            if len(stack) == 1 and stack[0][0] == b"living" and key == target_name:
                target_count += 1
                target_start = match.start()
            if target_start is not None and target_end is None:
                if len(stack) == 2 and stack[0][0] == b"living" and stack[1][0] == target_name:
                    if key in (b"alive_data", b"dead_data"):
                        status_blocks.append((key, match.start()))
                elif key in (b"alive_data", b"dead_data"):
                    status_shadow = True
                if key in death_fields and (
                    len(stack) < 3 or stack[2][0] != b"dead_data" or len(stack) != 3
                ):
                    death_field_shadow = True
            stack.append((key, match.start()))
            pending_key = None
            previous = token
            continue
        if token == b"}":
            if pending_key is not None or not stack:
                raise StatusUnknown("unbalanced or incomplete block")
            closed, _ = stack.pop()
            if (closed in (b"alive_data", b"dead_data") and len(stack) == 2
                    and stack[0][0] == b"living" and stack[1][0] == target_name):
                status_end = match.end()
            if closed == target_name and len(stack) == 1 and stack[0][0] == b"living":
                target_end = match.end()
            previous = token
            continue
        if pending_key is not None:
            key = pending_key
            if not stack and key == b"date":
                date_values.append(token)
            if target_start is not None and target_end is None:
                if key in (b"alive_data", b"dead_data"):
                    status_shadow = True  # life blocks must have a brace value
                if key in death_fields:
                    if len(stack) == 3 and stack[2][0] == b"dead_data":
                        death_fields[key].append(token)
                    else:
                        # The vanilla living focus has its own dated history.
                        # Exempt only that exact direct scalar, never a nested
                        # or misshapen death-field lookalike.
                        dated_living_focus = (
                            key == b"date" and bool(SAVE_DATE.fullmatch(token)) and
                            len(stack) == 4 and stack[0][0] == b"living" and
                            stack[1][0] == target_name and
                            stack[2][0] == b"alive_data" and stack[3][0] == b"focus"
                        )
                        if not dated_living_focus:
                            death_field_shadow = True
            pending_key = None
        previous = token

    if cursor != len(data) or stack or pending_key is not None:
        raise StatusUnknown("unbalanced, truncated or invalid melted text")
    if date_assignments != 1 or len(date_values) != 1 or date_values[0] != expected_date.encode("ascii"):
        raise StatusUnknown("melted top-level date is missing, duplicated or mismatched")
    if (living_assignments != 1 or living_count != 1 or target_assignments != 1
            or target_count != 1 or target_start is None or target_end is None):
        raise StatusUnknown("no unique CharacterID within a unique top-level living database")
    if status_shadow or len(status_blocks) != 1 or status_end is None:
        raise StatusUnknown("life blocks are missing, duplicated or nested-shadowed")
    kind, status_start = status_blocks[0]
    if kind == b"alive_data":
        if any(death_fields.values()) or death_field_shadow:
            raise StatusUnknown("alive character contains death-field shadow")
        status = "alive"
        death: dict[str, object] | None = None
    else:
        if (death_field_shadow or any(len(values) != 1 for values in death_fields.values())
                or any(count != 1 for count in death_field_assignments.values())):
            raise StatusUnknown("death fields are missing, duplicated or out of scope")
        date = death_fields[b"date"][0]
        if not SAVE_DATE.fullmatch(date):
            raise StatusUnknown("death date is malformed")
        reason = _text(death_fields[b"reason"][0])
        killer = _text(death_fields[b"killer"][0])
        if not reason or not killer.isdecimal() or int(killer) <= 0:
            raise StatusUnknown("death reason or killer is malformed")
        status = "dead"
        death = {"date": date.decode("ascii"), "reason": reason, "killer_character_id": int(killer)}
    return {
        "character_id": character_id,
        "save_date": expected_date,
        "life_status": status,
        "death": death,
        "character_block_sha256": digest(data[target_start:target_end]),
        "status_block_sha256": digest(data[status_start:status_end]),
        "scope": "unique top-level living / direct CharacterID / direct life block",
    }


def verify_checkpoint_receipt(receipt_bytes: bytes, *, expected_sha: str,
                              expected_date_raw: int, actor_id: int) -> dict[str, object]:
    try:
        receipt = json.loads(receipt_bytes)
        body = receipt["body"]
        checkpoint = body["checkpoint"]
        submission = body["submission"]
        hello = receipt["driver_state"]["hello"]
        size = checkpoint["size"]
        path = checkpoint["path"]
        bridge_version = hello["bridge_version"]
        if not (
            receipt["result"] == "CALL_COMPLETED"
            and body["step"] == "save-checkpoint"
            and body["accepted"] is True
            and checkpoint["status"] == "saved"
            and checkpoint["name"] == "xar_checkpoint.ck3"
            and checkpoint["sha256"].upper() == expected_sha
            and checkpoint["date_raw"] == expected_date_raw
            and submission["date_raw"] == expected_date_raw
            and checkpoint["episode_character_id"] == actor_id
            and hello["expected_ck3_sha256"].upper() == CK3_SHA256
            and hello["ck3_build_match"] is True
            and hello["game_adapter_id"] == "ck3-1.19.0.6-msvc-x64"
            and type(size) is int and size > 0
            and isinstance(path, str) and bool(path.strip())
            and bridge_version == "0.1.0"
        ):
            raise StatusUnknown("checkpoint receipt identity or state mismatch")
        return {"checkpoint_size": size, "checkpoint_path": path,
                "bridge_version": bridge_version,
                "game_adapter_id": hello["game_adapter_id"]}
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise StatusUnknown("checkpoint receipt is incomplete or inconsistent") from exc


def run(args: argparse.Namespace) -> dict[str, object]:
    save_sha = pinned_sha(args.expected_save_sha256)
    receipt_sha = pinned_sha(args.expected_receipt_sha256)
    rakaly_bytes = read_regular(args.rakaly_exe)
    if digest(rakaly_bytes) != RAKALY_SHA256:
        raise StatusUnknown("Rakaly executable SHA mismatch")
    version = subprocess.run([str(args.rakaly_exe), "--version"], capture_output=True, text=True,
                             check=False)
    if version.returncode != 0 or version.stdout.strip() != RAKALY_VERSION:
        raise StatusUnknown("Rakaly version mismatch")
    receipt_bytes = read_regular(args.checkpoint_receipt)
    if digest(receipt_bytes) != receipt_sha:
        raise StatusUnknown("checkpoint receipt SHA mismatch")
    source = read_regular(args.save)
    if digest(source) != save_sha:
        raise StatusUnknown("checkpoint source SHA mismatch")
    receipt_identity = verify_checkpoint_receipt(
        receipt_bytes, expected_sha=save_sha,
        expected_date_raw=args.expected_date_raw, actor_id=args.expected_actor_id)
    if len(source) != receipt_identity["checkpoint_size"]:
        raise StatusUnknown("checkpoint source size mismatch")
    if args.output_dir.exists():
        raise StatusUnknown("output directory already exists")
    args.output_dir.mkdir(parents=False)
    melted = args.output_dir / "melted.ck3"
    command = [str(args.rakaly_exe), "melt", str(args.save), "--unknown-key", "stringify",
               "--format", "ck3", "--out", str(melted)]
    result: subprocess.CompletedProcess[str] | None = None
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0 or not melted.is_file() or melted.is_symlink():
            raise StatusUnknown(f"Rakaly melt failed with exit {result.returncode}")
        melted_bytes = read_regular(melted)
        if digest(read_regular(args.save)) != save_sha:
            raise StatusUnknown("checkpoint source changed during melt")
        if digest(read_regular(args.checkpoint_receipt)) != receipt_sha:
            raise StatusUnknown("checkpoint receipt changed during melt")
        if digest(read_regular(args.rakaly_exe)) != RAKALY_SHA256:
            raise StatusUnknown("Rakaly executable changed during melt")
        parsed = parse_melted(melted_bytes, args.character_id, args.expected_save_date)
    except (StatusUnknown, OSError) as exc:
        failure = {
            "schema": "e2-05-a03-offline-character-status-failure-v1",
            "admission": False,
            "life_status": "UNKNOWN",
            "reason": str(exc),
            "source_save": str(args.save),
            "expected_source_save_sha256": save_sha,
            "checkpoint_receipt": str(args.checkpoint_receipt),
            "expected_checkpoint_receipt_sha256": receipt_sha,
            "rakaly_argv": command,
            "melted_file_exists": melted.is_file(),
            "melted_sha256": digest(read_regular(melted)) if melted.is_file() and not melted.is_symlink() else None,
            "rakaly_exit_code": result.returncode if result is not None else None,
            "rakaly_stdout": result.stdout if result is not None else None,
            "rakaly_stderr": result.stderr if result is not None else None,
        }
        with (args.output_dir / "failure.json").open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(failure, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        raise
    report = {
        "schema": "e2-05-a03-offline-character-status-v1",
        "admission": False,
        "status_proven_in_supplied_save": True,
        "run_day27_admission": False,
        "scope": "hash-pinned offline checkpoint only; no same-frame live target query",
        "source_save": str(args.save),
        "source_save_bytes": len(source),
        "source_save_sha256": save_sha,
        "checkpoint_receipt": str(args.checkpoint_receipt),
        "checkpoint_receipt_sha256": receipt_sha,
        "checkpoint_identity": receipt_identity,
        "expected_date_raw": args.expected_date_raw,
        "rakaly_exe": str(args.rakaly_exe),
        "rakaly_version": RAKALY_VERSION,
        "rakaly_exe_sha256": RAKALY_SHA256,
        "rakaly_argv": command,
        "rakaly_exit_code": result.returncode,
        "rakaly_stdout": result.stdout,
        "rakaly_stderr": result.stderr,
        "melted_save": str(melted),
        "melted_bytes": len(melted_bytes),
        "melted_sha256": digest(melted_bytes),
        "character": parsed,
    }
    with (args.output_dir / "report.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save", type=Path, required=True)
    parser.add_argument("--expected-save-sha256", required=True)
    parser.add_argument("--checkpoint-receipt", type=Path, required=True)
    parser.add_argument("--expected-receipt-sha256", required=True)
    parser.add_argument("--expected-date-raw", type=int, required=True)
    parser.add_argument("--expected-save-date", required=True)
    parser.add_argument("--expected-actor-id", type=int, required=True)
    parser.add_argument("--character-id", type=int, required=True)
    parser.add_argument("--rakaly-exe", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args)
    except (StatusUnknown, OSError) as exc:
        print(json.dumps({"admission": False, "life_status": "UNKNOWN", "reason": str(exc)}))
        return 2
    print(json.dumps({"admission": report["admission"], "status_proven_in_supplied_save":
                      report["status_proven_in_supplied_save"], "life_status":
                      report["character"]["life_status"], "report": str(args.output_dir / "report.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

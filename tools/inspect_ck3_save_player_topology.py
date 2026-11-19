#!/usr/bin/env python3
"""Inspect CK3 player records and celestial ruler topology offline.

The tool accepts any CK3 save plus a caller-supplied Rakaly executable, or an
already melted save for deterministic tests.  Its result is prelaunch input
evidence only; exact-build live MCP remains authoritative.
"""

from __future__ import annotations

import argparse
import codecs
from contextlib import contextmanager
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Iterator, Literal, NotRequired, Sequence, TextIO, TypedDict
import zipfile


SCHEMA_VERSION = 1
KIND = "ck3_save_player_topology_offline_v1"
TITLE_RANK = {"b": 1, "c": 2, "d": 3, "k": 4, "e": 5, "h": 6}


class SaveMemberIdentity(TypedDict):
    name: Literal["gamestate"]
    bytes: int
    compressed_bytes: int
    crc32: str


class SaveInputIdentity(TypedDict):
    format: Literal["plaintext", "native_zip_plaintext"]
    path: str
    bytes: int
    sha256: str
    content_bytes: int
    content_sha256: str
    member: NotRequired[SaveMemberIdentity]


class _CelestialCandidate(TypedDict):
    contract_id: int
    player_manager_character_id: int
    immediate_liege_character_id: int
    player_primary_title_tier: int
    player_primary_title_key: str
    player_government: str
    liege_primary_title_tier: int
    liege_primary_title_key: str
    liege_government: str
    direct_landed_vassal_count: int
    direct_landed_vassal_character_ids: list[int]


def _gamestate_member(archive: zipfile.ZipFile) -> zipfile.ZipInfo:
    members = archive.infolist()
    if len(members) != 1 or members[0].filename != "gamestate" or members[0].is_dir():
        raise ValueError("native save requires exactly one gamestate member")
    member = members[0]
    if member.flag_bits & 1:
        raise ValueError("encrypted native gamestate is unsupported")
    return member


def _check_native_prefix(prefix: bytes) -> None:
    prefix = prefix.removeprefix(codecs.BOM_UTF8).lstrip()
    if re.match(br"(?:SAV[0-9]{4}\s+)?meta_data\s*=\s*\{", prefix) is None:
        raise ValueError("native gamestate must be plaintext CK3 metadata")


@contextmanager
def _save_text(path: Path, *, native_zip: bool = False) -> Iterator[TextIO]:
    """Read a declared source; native mode never extracts or invokes Rakaly."""
    if not native_zip:
        with path.open("r", encoding="utf-8", errors="replace") as stream:
            yield stream
        return
    with zipfile.ZipFile(path) as archive:
        member = _gamestate_member(archive)
        with archive.open(member) as raw:
            with io.TextIOWrapper(raw, encoding="utf-8-sig", errors="strict") as stream:
                _check_native_prefix(stream.read(256).encode("utf-8"))
                stream.seek(0)
                yield stream


def _save_input_identity(path: Path, *, native_zip: bool = False) -> SaveInputIdentity:
    """Hash exact container/content bytes; native validation consumes CRC/UTF-8."""
    container_sha256 = _sha256(path).lower()
    digest = hashlib.sha256()
    size = 0
    member_identity: SaveMemberIdentity | None = None
    if native_zip:
        decoder = codecs.getincrementaldecoder("utf-8")(errors="strict")
        with zipfile.ZipFile(path) as archive:
            member = _gamestate_member(archive)
            member_identity = {"name": "gamestate", "bytes": member.file_size,
                               "compressed_bytes": member.compress_size, "crc32": f"{member.CRC:08x}"}
            with archive.open(member) as stream:
                prefix = stream.read(256)
                _check_native_prefix(prefix)
                digest.update(prefix)
                if "\x00" in decoder.decode(prefix):
                    raise ValueError("native gamestate contains binary NUL data")
                size += len(prefix)
                for chunk in iter(lambda: stream.read(65536), b""):
                    digest.update(chunk)
                    if "\x00" in decoder.decode(chunk):
                        raise ValueError("native gamestate contains binary NUL data")
                    size += len(chunk)
                decoder.decode(b"", final=True)
            if size != member.file_size:
                raise ValueError("native gamestate length differs from its ZIP member")
    else:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(65536), b""):
                digest.update(chunk)
                size += len(chunk)
    if _sha256(path).lower() != container_sha256:
        raise ValueError("save source changed while validating its content")
    result: SaveInputIdentity = {
        "format": "native_zip_plaintext" if native_zip else "plaintext",
        "path": str(path.resolve()), "bytes": path.stat().st_size,
        "sha256": container_sha256, "content_bytes": size,
        "content_sha256": digest.hexdigest(),
    }
    if member_identity is not None:
        result["member"] = member_identity
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _numeric_records(path: Path, *, native_zip: bool = False) -> Iterator[tuple[int, int, str]]:
    """Yield numeric records at the stable character/title/contract depths."""

    current_id: int | None = None
    level: int | None = None
    lines: list[str] = []
    with _save_text(path, native_zip=native_zip) as stream:
        for line in stream:
            if current_id is None:
                match = re.fullmatch(r"(\t{1,2})(\d+)=\{\s*\n?", line)
                if match is not None:
                    level = len(match.group(1))
                    current_id = int(match.group(2))
                    lines = [line]
                continue
            lines.append(line)
            assert level is not None
            if line == "\t" * level + "}\n":
                yield level, current_id, "".join(lines)
                current_id = None
                level = None
                lines = []


def _player_records(path: Path, *, native_zip: bool = False) -> tuple[list[dict[str, int]], list[int]]:
    played: list[dict[str, int]] = []
    current: list[int] = []
    block: list[str] | None = None
    kind: str | None = None
    depth = 0
    with _save_text(path, native_zip=native_zip) as stream:
        for line in stream:
            if block is None:
                stripped = line.strip()
                if line == "played_character={\n":
                    block, kind, depth = [line], "played", 1
                elif line == "currently_played_characters={\n":
                    block, kind, depth = [line], "current", 1
                elif stripped.startswith("currently_played_characters={") and stripped.endswith("}"):
                    current.extend(int(value) for value in re.findall(r"\d+", stripped))
                continue
            block.append(line)
            depth += line.count("{") - line.count("}")
            if depth != 0:
                continue
            text = "".join(block)
            if kind == "played":
                character = re.search(r"(?m)^\tcharacter=(\d+)$", text)
                player = re.search(r"(?m)^\tplayer=(\d+)$", text)
                if character is not None and player is not None:
                    played.append(
                        {
                            "character_id": int(character.group(1)),
                            "player_id": int(player.group(1)),
                        }
                    )
            else:
                current.extend(int(value) for value in re.findall(r"\d+", text))
            block = None
            kind = None
    return played, current


def inspect_melted(path: Path, *, requested_player: int | None = None,
                   native_zip: bool = False) -> dict[str, object]:
    meta_version: str | None = None
    meta_tier: int | None = None
    meta_players: int | None = None
    meta_portrait: int | None = None
    in_portrait = False
    with _save_text(path, native_zip=native_zip) as stream:
        for line in stream:
            stripped = line.strip()
            if stripped == "meta_main_portrait={":
                in_portrait = True
            elif in_portrait:
                match = re.fullmatch(r"id=(\d+)", stripped)
                if match is not None:
                    meta_portrait = int(match.group(1))
                    in_portrait = False
            if meta_version is None:
                match = re.fullmatch(r'version="([^"]+)"', stripped)
                if match is not None:
                    meta_version = match.group(1)
            match = re.fullmatch(r"meta_player_tier=(\d+)", stripped)
            if match is not None:
                meta_tier = int(match.group(1))
            match = re.fullmatch(r"meta_number_of_players=(\d+)", stripped)
            if match is not None:
                meta_players = int(match.group(1))
            if all(value is not None for value in (meta_version, meta_tier, meta_players, meta_portrait)):
                break

    contracts: list[tuple[int, int, int, str]] = []
    titles: list[tuple[int, str, int]] = []
    characters: dict[int, dict[str, object]] = {}
    for level, record_id, text in _numeric_records(path, native_zip=native_zip):
        if level == 2:
            vassal_match = re.search(r"(?m)^\t\t\tvassal=(\d+)$", text)
            liege_match = re.search(r"(?m)^\t\t\tliege=(\d+)$", text)
            group = re.search(r'(?m)^\t\t\tcontract_group="([^"]+)"$', text)
            if vassal_match is not None and liege_match is not None and group is not None:
                contracts.append(
                    (record_id, int(vassal_match.group(1)), int(liege_match.group(1)), group.group(1))
                )
            key_match = re.search(r'(?m)^\t\t\tkey="([bcdkeh]_[^"]+)"$', text)
            holder_match = re.search(r"(?m)^\t\t\tholder=(\d+)$", text)
            if key_match is not None and holder_match is not None:
                titles.append((record_id, key_match.group(1), int(holder_match.group(1))))
        elif (
            "\n\t\tfirst_name=" in text
            and "\n\t\talive_data={" in text
            and "\n\t\tlanded_data={" in text
        ):
            government = re.search(r'(?m)^\t\t\tgovernment="([^"]+)"$', text)
            characters[record_id] = {
                "government": government.group(1) if government is not None else None,
            }

    held: dict[int, list[tuple[int, str, int]]] = {}
    for title_id, key, holder in titles:
        held.setdefault(holder, []).append((TITLE_RANK[key[0]], key, title_id))
    celestial = [row for row in contracts if row[3] == "celestial_vassal"]
    landed_children: dict[int, list[int]] = {}
    for _, vassal, liege, _ in celestial:
        if vassal in characters:
            landed_children.setdefault(liege, []).append(vassal)

    candidates: list[_CelestialCandidate] = []
    for contract_id, vassal, liege, _ in celestial:
        vassal_character = characters.get(vassal)
        liege_character = characters.get(liege)
        vassal_title = max(held.get(vassal, [(0, "", 0)]))
        liege_title = max(held.get(liege, [(0, "", 0)]))
        if not (
            vassal_character is not None
            and liege_character is not None
            and vassal_title[0] >= 3
            and liege_title[0] >= 3
            and vassal_character.get("government") == "celestial_government"
            and liege_character.get("government") == "celestial_government"
        ):
            continue
        candidates.append(
            {
                "contract_id": contract_id,
                "player_manager_character_id": vassal,
                "immediate_liege_character_id": liege,
                "player_primary_title_tier": vassal_title[0],
                "player_primary_title_key": vassal_title[1],
                "player_government": "celestial_government",
                "liege_primary_title_tier": liege_title[0],
                "liege_primary_title_key": liege_title[1],
                "liege_government": "celestial_government",
                "direct_landed_vassal_count": len(landed_children.get(vassal, [])),
                "direct_landed_vassal_character_ids": sorted(
                    landed_children.get(vassal, [])
                ),
            }
        )
    candidates.sort(
        key=lambda row: (
            -row["direct_landed_vassal_count"],
            -row["player_primary_title_tier"],
            row["player_manager_character_id"],
        )
    )

    played, current = _player_records(path, native_zip=native_zip)
    player = requested_player if requested_player is not None else meta_portrait
    player_candidates = [
        row for row in candidates if row["player_manager_character_id"] == player
    ]
    single_player_ready = (
        isinstance(player, int)
        and player > 0
        and meta_players == 1
        and played == [{"character_id": player, "player_id": 1}]
        and current == [player]
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "result": "GREEN",
        "authority": "offline-prelaunch-only-live-exact-build-mcp-remains-authoritative",
        "game_version": meta_version,
        "meta_player_character_id": meta_portrait,
        "requested_player_character_id": player,
        "meta_player_tier": meta_tier,
        "meta_number_of_players": meta_players,
        "played_character_records": played,
        "currently_played_character_ids": current,
        "offline_single_player_ready": single_player_ready,
        "player_manager_candidates": player_candidates,
        "celestial_manager_candidate_count": len(candidates),
        "celestial_manager_candidates": candidates,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--save", type=Path)
    source.add_argument("--melted", type=Path)
    source.add_argument("--native-save", type=Path,
                        help="Read the native ZIP plaintext gamestate without extraction")
    parser.add_argument("--rakaly", type=Path)
    parser.add_argument("--player-character-id", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--keep-melted", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    temporary: tempfile.TemporaryDirectory[str] | None = None
    try:
        native_zip = args.native_save is not None
        native_identity: SaveInputIdentity | None = None
        if native_zip:
            if args.rakaly is not None or args.keep_melted is not None:
                raise ValueError("--native-save cannot use --rakaly or --keep-melted")
            melted = args.native_save.resolve()
            native_identity = _save_input_identity(melted, native_zip=True)
            source_record = dict(native_identity)
            rakaly_record = None
        elif args.melted is not None:
            melted = args.melted.resolve()
            if not melted.is_file():
                raise ValueError("melted input does not exist")
            source_record = None
            rakaly_record = None
        else:
            save = args.save.resolve()
            rakaly = args.rakaly.resolve() if args.rakaly is not None else None
            if not save.is_file() or rakaly is None or not rakaly.is_file():
                raise ValueError("--save requires an existing --rakaly executable")
            temporary = tempfile.TemporaryDirectory(prefix="ck3-save-topology-")
            melted = Path(temporary.name) / "source-melted.ck3"
            completed = subprocess.run(
                [str(rakaly), "melt", str(save), "-o", str(melted)],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0 or not melted.is_file():
                raise RuntimeError(
                    f"Rakaly melt failed ({completed.returncode}): {completed.stderr.strip()}"
                )
            source_record = {
                "path": str(save),
                "bytes": save.stat().st_size,
                "sha256": _sha256(save),
                "container_header": save.read_bytes()[:7].decode("ascii", errors="replace"),
            }
            rakaly_record = {
                "path": str(rakaly),
                "bytes": rakaly.stat().st_size,
                "sha256": _sha256(rakaly),
            }
        report = inspect_melted(
            melted, requested_player=args.player_character_id, native_zip=native_zip
        )
        report["source"] = source_record
        report["rakaly"] = rakaly_record
        if native_identity is not None:
            if _sha256(melted).lower() != native_identity["sha256"]:
                raise ValueError("native save changed while being inspected")
            report["melted_sha256"] = native_identity["content_sha256"].upper()
        else:
            report["melted_sha256"] = _sha256(melted)
        if args.keep_melted is not None:
            target = args.keep_melted.resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(melted.read_bytes())
            report["retained_melted_path"] = str(target)
        payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output is not None:
            output = args.output.resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(payload, encoding="utf-8")
        print(payload, end="")
        return 0
    finally:
        if temporary is not None:
            temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())

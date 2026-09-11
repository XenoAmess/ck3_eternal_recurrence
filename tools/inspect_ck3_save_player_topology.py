#!/usr/bin/env python3
"""Inspect CK3 player records and celestial ruler topology offline.

The tool accepts any CK3 save plus a caller-supplied Rakaly executable, or an
already melted save for deterministic tests.  Its result is prelaunch input
evidence only; exact-build live MCP remains authoritative.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Iterator, Sequence


SCHEMA_VERSION = 1
KIND = "ck3_save_player_topology_offline_v1"
TITLE_RANK = {"b": 1, "c": 2, "d": 3, "k": 4, "e": 5, "h": 6}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _numeric_records(path: Path) -> Iterator[tuple[int, int, str]]:
    """Yield numeric records at the stable character/title/contract depths."""

    current_id: int | None = None
    level: int | None = None
    lines: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if current_id is None:
                match = re.fullmatch(r"(\t{1,2})(\d+)=\{\s*\n?", line)
                if match is not None:
                    level = len(match.group(1))
                    current_id = int(match.group(2))
                    lines = [line]
                continue
            lines.append(line)
            if line == "\t" * int(level) + "}\n":
                yield int(level), current_id, "".join(lines)
                current_id = None
                level = None
                lines = []


def _player_records(path: Path) -> tuple[list[dict[str, int]], list[int]]:
    played: list[dict[str, int]] = []
    current: list[int] = []
    block: list[str] | None = None
    kind: str | None = None
    depth = 0
    with path.open("r", encoding="utf-8", errors="replace") as stream:
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


def inspect_melted(path: Path, *, requested_player: int | None = None) -> dict[str, object]:
    meta_version: str | None = None
    meta_tier: int | None = None
    meta_players: int | None = None
    meta_portrait: int | None = None
    in_portrait = False
    with path.open("r", encoding="utf-8", errors="replace") as stream:
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
    for level, record_id, text in _numeric_records(path):
        if level == 2:
            vassal = re.search(r"(?m)^\t\t\tvassal=(\d+)$", text)
            liege = re.search(r"(?m)^\t\t\tliege=(\d+)$", text)
            group = re.search(r'(?m)^\t\t\tcontract_group="([^"]+)"$', text)
            if vassal is not None and liege is not None and group is not None:
                contracts.append(
                    (record_id, int(vassal.group(1)), int(liege.group(1)), group.group(1))
                )
            key = re.search(r'(?m)^\t\t\tkey="([bcdkeh]_[^"]+)"$', text)
            holder = re.search(r"(?m)^\t\t\tholder=(\d+)$", text)
            if key is not None and holder is not None:
                titles.append((record_id, key.group(1), int(holder.group(1))))
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
    child_count: dict[int, int] = {}
    for _, vassal, liege, _ in celestial:
        if vassal in characters:
            child_count[liege] = child_count.get(liege, 0) + 1

    candidates: list[dict[str, object]] = []
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
                "player_government": vassal_character["government"],
                "liege_primary_title_tier": liege_title[0],
                "liege_primary_title_key": liege_title[1],
                "liege_government": liege_character["government"],
                "direct_landed_vassal_count": child_count.get(vassal, 0),
            }
        )
    candidates.sort(
        key=lambda row: (
            -int(row["direct_landed_vassal_count"]),
            -int(row["player_primary_title_tier"]),
            int(row["player_manager_character_id"]),
        )
    )

    played, current = _player_records(path)
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
    parser.add_argument("--rakaly", type=Path)
    parser.add_argument("--player-character-id", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--keep-melted", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    temporary: tempfile.TemporaryDirectory[str] | None = None
    try:
        if args.melted is not None:
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
            melted, requested_player=args.player_character_id
        )
        report["source"] = source_record
        report["rakaly"] = rakaly_record
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


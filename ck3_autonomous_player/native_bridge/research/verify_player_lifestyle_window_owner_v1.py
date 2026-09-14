#!/usr/bin/env python3
"""Verify the exact-build player lifestyle-window owner research contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
DEFAULT_REPO_ROOT = HERE.parents[2]
CONTRACT_PATH = HERE / "player_lifestyle_window_owner_v1_abi.json"
DOC_PATH = DEFAULT_REPO_ROOT / "docs" / "ck3-native-ai" / "lifestyle-focus-perk-ai.md"


def fail(message: str) -> None:
    raise RuntimeError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def parse_integer(value: str) -> int:
    return int(value, 0)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


class PeImage:
    """Minimal PE32+ RVA reader implemented with the Python standard library."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.data = path.read_bytes()
        require(self.data[:2] == b"MZ", f"not an MZ image: {path}")
        pe_offset = struct.unpack_from("<I", self.data, 0x3C)[0]
        require(
            self.data[pe_offset : pe_offset + 4] == b"PE\0\0",
            f"not a PE image: {path}",
        )
        coff = pe_offset + 4
        section_count = struct.unpack_from("<H", self.data, coff + 2)[0]
        optional_size = struct.unpack_from("<H", self.data, coff + 16)[0]
        optional = coff + 20
        require(
            struct.unpack_from("<H", self.data, optional)[0] == 0x20B,
            "expected a PE32+ image",
        )
        self.image_base = struct.unpack_from("<Q", self.data, optional + 24)[0]
        section_table = optional + optional_size
        self.sections: list[tuple[int, int, int, int]] = []
        for index in range(section_count):
            row = section_table + index * 40
            virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
                "<IIII", self.data, row + 8
            )
            self.sections.append(
                (virtual_address, max(virtual_size, raw_size), raw_offset, raw_size)
            )

    def at_rva(self, rva: int, length: int) -> bytes:
        require(length >= 0, "negative PE read length")
        for virtual_address, mapped_size, raw_offset, raw_size in self.sections:
            if virtual_address <= rva and rva + length <= virtual_address + mapped_size:
                delta = rva - virtual_address
                require(
                    delta + length <= raw_size,
                    f"RVA 0x{rva:X} extends into zero-fill data",
                )
                return self.data[raw_offset + delta : raw_offset + delta + length]
        fail(f"RVA 0x{rva:X}+0x{length:X} is outside mapped raw sections")
        return b""


def verify_asset(game_install: Path, asset: dict[str, Any]) -> None:
    path = game_install / asset["path"]
    require(path.is_file(), f"missing exact-build asset: {path}")
    data = path.read_bytes()
    require(len(data) == asset["bytes"], f"size drift: {asset['path']}")
    require(sha256(data) == asset["sha256"], f"SHA-256 drift: {asset['path']}")


def verify_tokens(path: Path, tokens: list[str]) -> None:
    text = path.read_text(encoding="utf-8-sig")
    for token in tokens:
        require(token in text, f"missing token {token!r} in {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--game-install", type=Path)
    parser.add_argument("--exe", type=Path)
    arguments = parser.parse_args()

    repo_root = arguments.repo_root.resolve()
    game_install = (
        arguments.game_install.resolve()
        if arguments.game_install
        else (repo_root / "Crusader Kings III").resolve()
    )
    exe_path = (
        arguments.exe.resolve()
        if arguments.exe
        else game_install / "binaries" / "ck3.exe"
    )
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    require(
        contract["contract"] == "player-lifestyle-window-owner-static-abi-v1",
        "unexpected contract identity",
    )
    require(contract["game_version"] == "1.19.0.6", "unexpected game version")
    require(contract["read_only"] is True, "contract must remain read-only")
    require(contract["live_validated"] is False, "research must not claim live status")
    require(contract["game_process_started"] is False, "research must not claim CK3 use")

    executable = contract["exact_build"]["executable"]
    require(exe_path.is_file(), f"missing exact executable: {exe_path}")
    exe_data = exe_path.read_bytes()
    require(len(exe_data) == executable["bytes"], "executable size drift")
    require(sha256(exe_data) == executable["sha256"], "executable SHA-256 drift")
    for asset in contract["exact_build"]["stock_sources"]:
        verify_asset(game_install, asset)

    image = PeImage(exe_path)
    require(image.image_base == 0x140000000, "unexpected CK3 image base")
    for region in contract["evidence_regions"]:
        start = parse_integer(region["start_rva"])
        end = parse_integer(region["end_rva"])
        length = parse_integer(region["length"])
        require(end - start == length, f"range arithmetic drift: {region['name']}")
        require(
            sha256(image.at_rva(start, length)) == region["sha256"],
            f"exact code range drift: {region['name']}",
        )

    rtti = contract["rtti"]
    type_descriptor = parse_integer(rtti["type_descriptor_rva"])
    decorated = rtti["decorated_name"].encode("ascii") + b"\0"
    require(
        image.at_rva(type_descriptor + 0x10, len(decorated)) == decorated,
        "CCharacterLifestyleWindow RTTI name drift",
    )
    for key, function_key in (
        ("primary_vtable_rva", "primary_vtable_function_rvas"),
        ("secondary_vtable_rva", "secondary_vtable_function_rvas"),
    ):
        expected = [parse_integer(value) for value in rtti[function_key]]
        table = image.at_rva(parse_integer(rtti[key]), len(expected) * 8)
        actual = [
            struct.unpack_from("<Q", table, index * 8)[0] - image.image_base
            for index in range(len(expected))
        ]
        require(actual == expected, f"vtable drift: {key}")

    owner = contract["owner_path"]
    expected_handler = [
        parse_integer(value)
        for value in owner["handler_primary_vtable_function_rvas"]
    ]
    handler_table = image.at_rva(
        parse_integer(owner["handler_primary_vtable_rva"]),
        len(expected_handler) * 8,
    )
    actual_handler = [
        struct.unpack_from("<Q", handler_table, index * 8)[0] - image.image_base
        for index in range(len(expected_handler))
    ]
    require(actual_handler == expected_handler, "CIngameInterfaceHandler vtable drift")

    for pointer_slot in contract["exact_pointer_slots"]:
        actual_target = (
            struct.unpack(
                "<Q",
                image.at_rva(parse_integer(pointer_slot["slot_rva"]), 8),
            )[0]
            - image.image_base
        )
        require(
            actual_target == parse_integer(pointer_slot["target_rva"]),
            f"function pointer target drift: {pointer_slot['name']}",
        )

    identity = contract["identity_gate"]
    initial = bytes.fromhex(identity["initial_bytes"])
    require(
        image.at_rva(parse_integer(identity["played_character_id_global_rva"]), len(initial))
        == initial,
        "played-character global initial bytes drift",
    )

    verify_tokens(
        game_install / "game/gui/hud.gui",
        ["OpenGameViewData( 'lifestyle', GetPlayer.GetID )"],
    )
    verify_tokens(
        game_install / "game/gui/window_character_lifestyle.gui",
        [
            "CharacterLifestyleWindow.GetCharacter",
            "CharacterLifestyleWindow.GetFocuses",
            "CharacterLifestyleWindow.GetPerkTrees",
            "CharacterLifestyleWindow.CanSelectFocus( FocusType.Self )",
            "CharacterLifestyleWindow.CanSelectPerk( Perk.Self )",
            "CharacterLifestyleWindow.CanSelectPerkIgnoreCost",
        ],
    )
    verify_tokens(
        game_install / "game/localization/english/gui/lifestyle_window_l_english.yml",
        [
            "CharacterLifestyleWindow.CanSelectPerkDesc",
            "CharacterLifestyleWindow.CanSelectFocusDesc",
        ],
    )
    verify_tokens(
        repo_root / "docs/ck3-native-ai/lifestyle-focus-perk-ai.md",
        [
            "G2-M4-LIFE3-WINDOW-OWNER-RESEARCH",
            "CIngameInterfaceHandler",
            "root = *(module + 0x570F7B8)",
            "handler + 0x1A8",
            "0xF48780",
            "0x132D4A0",
            "0x132D640",
            "lifestyle_window_unbound_or_stale",
            "unknown",
            "flowchart TD",
        ],
    )

    print(
        json.dumps(
            {
                "ok": True,
                "contract": contract["contract"],
                "game_version": contract["game_version"],
                "evidence_regions": len(contract["evidence_regions"]),
                "live_validated": contract["live_validated"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"RED: {error}", file=sys.stderr)
        raise SystemExit(1)

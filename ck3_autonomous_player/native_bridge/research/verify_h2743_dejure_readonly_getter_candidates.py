"""Verify exact-build disk/script anchors for two H2743 truce-input readers.

This never loads CK3, reads process memory, evaluates an effect, or computes an
H2743 truce duration. It only checks candidate sources for a future paused
reader of FLEX and NOMAD_BOTH.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from disasm_ck3_bounded_disk import IMAGE_BASE, read_rva, sections


REPO = Path(__file__).resolve().parents[3]
GAME = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III")
EXE = GAME / "binaries/ck3.exe"
EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
WAR_VALUES = GAME / "game/common/script_values/00_war_values.txt"
WAR_VALUES_SHA = "ED1CDB6E8BC887CF1FFFE010F1E9CA642DFD6DAF241E81F23E6B4736F7AFDF3B"
DEJURE_WAR = GAME / "game/common/casus_belli_types/00_dejure_war.txt"
DEJURE_WAR_SHA = "D8737A2205116118A5ECD6EFA576D316B3155730A3824DC4BD109A68B9D5B6EE"
LIFESTYLE_ABI = REPO / "ck3_autonomous_player/native_bridge/research/player_lifestyle_snapshot_v1_abi.json"
LIFESTYLE_SOURCE = REPO / "ck3_autonomous_player/native_bridge/src/player_lifestyle_snapshot_v1.cpp"
COMBAT_SOURCE = REPO / "ck3_autonomous_player/native_bridge/src/combat_v3.cpp"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def require_text(path: Path, pieces: tuple[str, ...]) -> str:
    value = path.read_text(encoding="utf-8-sig")
    for piece in pieces:
        if piece not in value:
            raise ValueError(f"missing exact source anchor in {path}: {piece}")
    return value


def verify() -> dict[str, object]:
    for path, digest in ((EXE, EXE_SHA), (WAR_VALUES, WAR_VALUES_SHA),
                         (DEJURE_WAR, DEJURE_WAR_SHA)):
        if sha256(path) != digest:
            raise ValueError(f"exact CK3 input changed: {path}")
    require_text(WAR_VALUES, (
        "standard_truce_duration_days = {", "has_perk = flexible_truces_perk",
        "government_is_nomadic", "using_cb = fp2_border_raid",
        "truces_by_involved_or_interlopers_within_region_shorter",
        "truces_by_involved_or_interlopers_within_region_longer",
    ))
    require_text(DEJURE_WAR, ("individual_county_de_jure_cb = {",
                              "add_truce_attacker_victory_effect = yes"))
    abi = json.loads(LIFESTYLE_ABI.read_text(encoding="utf-8"))
    if (abi["exact_build"]["executable_sha256"] != EXE_SHA
            or abi["native_current_state"]["unlocked_perks_span_getter_rva"] != "0x2669170"
            or abi["native_current_state"]["unlocked_perks_span_layout"] != {
                "data_offset": "0x0", "count_offset": "0xC",
                "row_stride_bytes": 8, "maximum_rows": 512}):
        raise ValueError("lifestyle exact-build span ABI changed")
    require_text(LIFESTYLE_SOURCE, (
        "environment.unlocked_perks(character)",
        "kPlayerLifestyleCharacterPerkStableKeyOffsetV1",
        "state.owned_perk_keys[index]",
    ))
    require_text(COMBAT_SOURCE, (
        "kCharacterGovernmentRva = 0x26165B0",
        "ResolveScriptIdentifier(module, \"government_is_nomadic\"",
        "definitions.government_is_nomadic_id",
        "static_cast<std::byte *>(government) + 0x48",
    ))
    anchors = {
        # Non-null character+0x1A8 takes the direct span path. The null/TLS
        # diagnostic branch must never be used by the proposed reader.
        0x2669174: bytes.fromhex("488B81A8010000"),
        0x266917B: bytes.fromhex("4885C07528"),
        0x26691A8: bytes.fromhex("4805200200004883C428C3"),
        # Alive landed CharacterGovernment returns *(landed+0x3F0). The
        # proposed reader copies this layout only after type/identity gates.
        0x26165E0: bytes.fromhex("488B83B80100004885C00F8581000000"),
        0x2616671: bytes.fromhex("488B80F00300004883C4205BC3"),
        # HasPerk's first native call goes to GetOwnedPerks; this binds the
        # perk span to its stock predicate, not to future script evaluation.
        0x2668EA9: bytes.fromhex("E8C2020000"),
    }
    with EXE.open("rb") as stream:
        image_base, mapped = sections(stream)
        if image_base != IMAGE_BASE:
            raise ValueError("unexpected CK3 PE image base")
        for rva, expected in anchors.items():
            if read_rva(stream, mapped, rva, len(expected)) != expected:
                raise ValueError(f"EXE candidate anchor changed at 0x{rva:X}")
    return {
        "schema": "xar.ck3.h2743-dejure-readonly-getter-candidates.v1",
        "status": "static_candidate_no_live_read",
        "exe_sha256": EXE_SHA,
        "script_sha256": {"00_war_values.txt": WAR_VALUES_SHA,
                           "00_dejure_war.txt": DEJURE_WAR_SHA},
        "source_sha256": {str(path.relative_to(REPO)): sha256(path)
                          for path in (LIFESTYLE_ABI, LIFESTYLE_SOURCE, COMBAT_SOURCE)},
        "disk_rva_anchors": {f"0x{rva:X}": expected.hex().upper()
                             for rva, expected in anchors.items()},
        "candidate_conditions": {
            "FLEX": "attacker owned-perk span contains flexible_truces_perk; requires full-generation attacker and double-read stable-key span",
            "NOMAD_BOTH": "both primary parties' government+0x48 validated identifier spans contain government_is_nomadic; requires alive-landed path or typed unavailable",
        },
        "unavailable_conditions": ["SHORT", "LONG", "BORDER_RAID_PAIR"],
        "evaluated_days": None,
        "persisted_expiry_date_raw": None,
        "gameplay_action_submitted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    receipt = verify()
    if args.output is not None:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(receipt, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

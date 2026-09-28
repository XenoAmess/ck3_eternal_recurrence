"""Verify exact CK3 disk anchors for a future H2743 clone-only passive observer.

This module never loads CK3 or calls setup, resolve, preview, or surrender. Its
output is a static hook candidate, never an observed term or action authority.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from disasm_ck3_bounded_disk import IMAGE_BASE, read_rva, sections


GAME = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III")
EXE = GAME / "binaries/ck3.exe"
DEJURE = GAME / "game/common/casus_belli_types/00_dejure_war.txt"
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
DEJURE_SHA256 = "D8737A2205116118A5ECD6EFA576D316B3155730A3824DC4BD109A68B9D5B6EE"

# These are complete instruction bytes, not patch lengths or evidence that a
# detour would preserve CK3 behavior. A future implementation must separately
# prove its relocation, register/flag preservation, rollback, and clone scope.
ANCHORS = {
    0x27A470E: "B812000000",        # context type tag 0x12
    0x27A471A: "668901",            # context+0 receives the tag
    0x27A4720: "48634208",          # source War+8 full ID
    0x27A472E: "4C8BF1",            # populated context pointer -> R14
    0x27A4731: "48894108",          # populated WarEffectContext+8
    0x2E9F445: "4C8BF2",            # setup execute keeps RDX context in R14
    0x2E9F5AF: "488D8E60020000",    # embedded title scope
    0x2E9F5B6: "E8F566AFFD",        # dynamic CLandedTitle resolver
    0x2E9F5BB: "4C8BE0",            # resolved pointer RAX -> R12
    0x995CD5: "66837C243005",      # resolver output type must be 5
    0x995CE7: "0F44442438",        # type 5 takes full component ID
    0x995D1E: "41394010",          # lookup compares full generation ID
    0x2E9F710: "48638540230000",    # dynamic container count
    0x2E9F717: "4869D0A0860100",    # count * 100000 -> RDX
    0x2E9F71E: "498B4E18",          # context variable wrapper
    0x2E9F722: "E899FBFFFF",        # factor writer call
    0x2E9F727: "80BE5802000000",  # first instruction after writer
    0x2E9F2D9: "8B1575C49402",      # writer loads factor identifier
    0x2E9F319: "E8B29D4B00",        # mutable identifier row writer
    0x3380492: "E869050000",        # loaded-effect entry dispatches 0x3380A00
    0x3380C66: "418901",            # generic dispatcher writes context counter
    0x3380CFB: "FF90B0000000",      # generic virtual node execute
    0x3380EE9: "E812FBFFFF",        # child iteration reenters dispatcher
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def verify(exe: Path = EXE, dejure: Path = DEJURE) -> dict[str, object]:
    if sha256(exe) != EXE_SHA256 or sha256(dejure) != DEJURE_SHA256:
        raise ValueError("CK3 EXE or de-jure script is not the exact audited build")
    script = dejure.read_text(encoding="utf-8-sig")
    for literal in (
        "individual_county_de_jure_cb = {",
        "setup_de_jure_cb = {",
        "title = scope:target",
        "resolve_title_and_vassal_change = scope:change",
    ):
        if literal not in script:
            raise ValueError(f"missing stock script anchor: {literal}")
    with exe.open("rb") as stream:
        image_base, mapped = sections(stream)
        if image_base != IMAGE_BASE:
            raise ValueError("CK3 PE image base changed")
        for rva, expected_hex in ANCHORS.items():
            expected = bytes.fromhex(expected_hex)
            if read_rva(stream, mapped, rva, len(expected)) != expected:
                raise ValueError(f"CK3 observer seam differs at RVA 0x{rva:X}")
    return {
        "schema": "xar.ck3.h2743-clone-observer-seams.v1",
        "status": "static_hook_candidate_only",
        "exe_sha256": EXE_SHA256,
        "dejure_script_sha256": DEJURE_SHA256,
        "disk_rva_anchors": {f"0x{rva:X}": value for rva, value in ANCHORS.items()},
        "candidate_only": {
            "war_context_id": "populate 0x27A470E/71A writes tag 0x12 and 0x27A4720/731 copies War+8 to context+8; prove the same context pointer reaches setup and resolve the actual War+CB before use",
            "runtime_target_title": "setup 0x2E9F5B6 returns CLandedTitle pointer; capture only on natural clone execution and validate full ID against title storage",
            "cb_prestige_factor_raw": "setup 0x2E9F717 computes dynamic count * 100000; pair pre/post 0x2E9F722 writer and verify identifier row before treating as produced",
            "generic_effect_dispatch": "0x3380492 calls 0x3380A00; 0x3380CFB is one virtual +0xB0 branch, with a nearby +0x30 branch at 0x3380D10, and 0x3380EE9 child recursion reenters the dispatcher; 0x3380C66 writes context state, so executed nodes alone cannot prove complete conditional coverage",
        },
        "unproven": [
            "detour relocation and rollback safety",
            "same WarEffectContext instance from populate to setup",
            "actual War object and active CB pointer/key at the same natural callback",
            "conditional effect tree coverage and signed resource causality",
            "full post-surrender title/vassal operation graph",
            "persisted directed truce and deterministic clone equivalence",
        ],
        "clone_executed": False,
        "native_effect_called": False,
        "material_complete": False,
        "recommended_outcome": None,
        "action_literal": None,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))

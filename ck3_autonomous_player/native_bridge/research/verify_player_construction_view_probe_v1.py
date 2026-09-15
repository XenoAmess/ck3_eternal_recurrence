"""Verify the exact-build player construction cache-probe source anchors."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re

import pefile


HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ck3-executable", type=Path)
    arguments = parser.parse_args()
    executable = arguments.ck3_executable
    if executable is None:
        env_path = os.environ.get("XAR_CK3_EXECUTABLE_PATH")
        if env_path is None:
            raise RuntimeError("set XAR_CK3_EXECUTABLE_PATH for the frozen EXE")
        executable = Path(env_path)

    contract = json.loads((HERE / "player_construction_view_probe_v1_abi.json").read_text(
        encoding="utf-8"))
    data = executable.read_bytes()
    assert sha256(data) == contract["exe_sha256"]
    gui = executable.parent.parent / "game/gui/window_county_view.gui"
    actual_gui_sha = sha256(gui.read_bytes())
    assert actual_gui_sha == contract["stock_gui_sha256"], (
        f"{gui}: {actual_gui_sha}")
    text = gui.read_text(encoding="utf-8-sig")
    for binding in contract["stock_gui_bindings"]:
        assert binding in text, binding

    image = pefile.PE(data=data, fast_load=True)
    for region in contract["exact_regions"]:
        start = int(region["start_rva"], 0)
        end = int(region["end_rva"], 0)
        offset = image.get_offset_from_rva(start)
        assert sha256(data[offset:offset + end - start]) == region["sha256"], (
            region["name"])

    header = (NATIVE / "src/player_construction_view_probe_v1.hpp").read_text(
        encoding="utf-8")
    source = (NATIVE / "src/player_construction_view_probe_v1.cpp").read_text(
        encoding="utf-8")
    process_source = (NATIVE / "src/player_construction_view_probe_v1_process.cpp").read_text(
        encoding="utf-8")
    mailbox_source = (NATIVE / "src/player_construction_view_probe_v1_mailbox.cpp").read_text(
        encoding="utf-8")
    for constant in ("0x40AF630U", "0x4131618U", "0xD0U", "0x118U",
                     "0x120U", "0x124U"):
        assert constant in source, constant
    assert "view_candidate_cache_empty" in header
    for anchor in ("kTitleMapIngameIdlerRootSlotRva",
                   "kTitleMapRuntimeDynamicCastRva",
                   "kTitleMapIngameIdlerTypeDescriptorRva"):
        assert anchor in process_source, anchor
    assert "advertised\\\":false" in mailbox_source
    assert contract["advertised"] is False
    transport = contract["private_transport"]
    assert transport["default"] == "OFF"
    assert transport["execute_step"] in (
        NATIVE / "src/player_construction_view_probe_v1_mailbox.hpp"
    ).read_text(encoding="utf-8")
    cmake = (NATIVE / "CMakeLists.txt").read_text(encoding="utf-8")
    option = re.escape(transport["cmake_option"])
    assert re.search(rf"option\(\s*{option}\s*\"[^\"]+\"\s*OFF\s*\)", cmake)
    for unit in ("player_construction_view_probe_v1.cpp",
                 "player_construction_view_probe_v1_process.cpp",
                 "player_construction_view_probe_v1_mailbox.cpp"):
        assert f"src/{unit}" in cmake, unit
    bridge = (NATIVE / "src/bridge.cpp").read_text(encoding="utf-8")
    assert f"#if defined({transport['cmake_option']})" in bridge
    assert "kPlayerConstructionViewProbePrivateStepV1" in bridge
    assert "ExecutePlayerConstructionViewProbeMailboxV1" in bridge
    assert 'response += ",\\\"private_probe\\\":"' in bridge
    print("player-construction-view-probe-source: GREEN_EXACT_BUILD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

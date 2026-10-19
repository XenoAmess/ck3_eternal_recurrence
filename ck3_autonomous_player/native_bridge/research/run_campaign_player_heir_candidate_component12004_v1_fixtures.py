"""Bounded source-only attachment DLLs; existing campaign-root query, no game.

Requires an exact storage card before creating the one named output child.
Reuses the already reviewed allocation guard and MSVC environment helper.
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import run_ck3_12004_player_heir_candidate_v1_fixtures as old

REPO, NATIVE = old.REPO, old.NATIVE
HARD_BYTES = old.HARD_BYTES
SOURCES = [
    "src/ck3_12004_player_heir_candidate_v1.cpp",
    "src/campaign_player_heir_candidate_component12004_v1.cpp",
    "src/campaign_player_heir_candidate_component12004_v1_serializer.cpp",
    "tests/campaign_player_heir_candidate_component12004_v1_fixture.cpp",
    "src/ck3_12004_abi_profile.cpp", "src/ck3_12004_family.cpp",
    "src/ck3_12002_family_value.cpp", "src/ck3_12002.cpp",
]
INPUTS = SOURCES + old.HEADERS + [
    "tests/ck3_12004_player_heir_candidate_v1_fixture.cpp",
    "include/xar_bridge/campaign_player_heir_candidate_component12004_v1.hpp",
    "cmake/campaign_player_heir_candidate_component12004_v1.cmake",
    "include/xar_bridge/campaign_root_context_v1.hpp",
    "src/bridge.cpp", "CMakeLists.txt",
    "research/run_ck3_12004_player_heir_candidate_v1_fixtures.py",
    "research/run_domain_construction_cost_legality_live_observer_v1_tests.py",
]


def machine() -> str:
    return subprocess.check_output([os.sys.executable, "-B",
        str(old.MACHINE_TOOL), "machine"], text=True).strip()


def plan(root: Path) -> dict:
    return {
        "schema": "xar.player-heir-campaign-attachment-mock-plan.v1",
        "machine_id": machine(), "observed_at_utc": old.utc(),
        "output_root": str(root.resolve()), "hard_limit_bytes": HARD_BYTES,
        "producer": old.pin(Path(__file__).resolve()),
        "source_pins": [old.pin(NATIVE / p) for p in dict.fromkeys(INPUTS)],
        "attempt": "one explicit create-only attempt, no automatic retry",
        "outputs": ["default-off/attachment.dll", "explicit-optin/attachment.dll",
            "{mode}/compile.log", "{mode}/*.obj,*.lib,*.exp,*.deps.json",
            "{mode}/wire.json", "{mode}/bridge_frame_fragment.hpp", "RESULT.json",
            "tmp/environment capture only"],
        "resource": "sequential BELOW_NORMAL/noMP; reused FileStandardInfo same-handle EOF/AllocationSize guard max(sumEOF,sumAllocation) hard16MiB; unknown stops own child",
        "cases": "attachment only, old29 not rerun; parent change/partial/mismatch, unknown, null/dead, known-none vs unavailable lineage, escaping, full signed32 IDs, default-off byte identity/zero reads",
        "boundary": "mock getter/Core/Family fixture + exact production ResultFrame fragment with base-root serializer stubs; no full Bridge/root-validator compile, CK3 image/process, GameRPC, Native29/prod DLL build/deploy, H or backup credit; executor/CMake source-reviewed only",
        "status": "PLAN_ONLY_NOT_EXECUTED",
    }


def run(plan_path: Path, card_path: Path, card_sha: str) -> dict:
    record = json.loads(plan_path.read_bytes())
    here = machine()
    if record["machine_id"] != here or old.pin(card_path)["sha256"] != card_sha:
        raise RuntimeError("machine/card identity mismatch")
    card = json.loads(card_path.read_bytes())
    admission = card["player_heir_fixture_admission"]
    root = Path(record["output_root"]).resolve()
    if (card["machine_id"] != here or
        Path(admission["output_root"]).resolve() != root or
        admission["plan_sha256"] != old.pin(plan_path)["sha256"] or
        admission["hard_limit_bytes"] != HARD_BYTES or
        admission["approved"] is not True):
        raise RuntimeError("exact storage admission mismatch")
    expiry = datetime.fromisoformat(admission["expires_at_utc"].replace("Z", "+00:00"))
    if expiry <= datetime.now(timezone.utc):
        raise RuntimeError("storage admission expired")
    if old.pin(Path(__file__).resolve()) != record["producer"]:
        raise RuntimeError("producer changed after plan")
    for row in record["source_pins"]:
        if old.pin(Path(row["path"])) != row:
            raise RuntimeError(f"input changed: {row['path']}")
    if root.exists():
        raise RuntimeError("preserve existing attempt; no implicit retry")
    root.mkdir()
    temporary = root / "tmp"
    temporary.mkdir()
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    from run_domain_construction_cost_legality_live_observer_v1_tests import (
        _visual_studio_environment,
    )
    env = _visual_studio_environment()
    compiler = shutil.which("cl.exe", path=env.get("PATH"))
    if not compiler:
        raise RuntimeError("MSVC unavailable")
    started = old.utc()
    bridge = (NATIVE / "src/bridge.cpp").read_text(encoding="utf-8")
    start = bridge.index("std::string CampaignRootContextResultFrame(")
    end = bridge.index("\nstd::string StewardDevelopCountyCandidatesResultFrame(", start)
    fragment = bridge[start:end]
    if len(fragment.encode()) > 4096:
        raise RuntimeError("bounded ResultFrame fragment unexpectedly grew")
    peak = dict(logical_bytes=0, allocated_bytes=0, guard_bytes=0)
    suites = []
    for mode, defines in (("default-off", []), ("explicit-optin", [
            "/DXAR_CK3_ENABLE_PLAYER_HEIR_CANDIDATE12004_V1=1",
            "/DXAR_CK3_ENABLE_CAMPAIGN_ROOT_PLAYER_HEIR_CANDIDATE12004_V1=1"])):
        out = root / mode
        out.mkdir()
        (out / "bridge_frame_fragment.hpp").write_text(fragment, encoding="utf-8", newline="\n")
        dll = out / "attachment.dll"
        command = [compiler, "/nologo", "/LD", "/std:c++20", "/W4", "/WX",
            "/permissive-", "/EHsc", "/DNOMINMAX", "/Od", "/MD", "/Gy",
            *defines, f"/I{NATIVE / 'include'}", f"/I{NATIVE / 'research'}",
            f"/I{NATIVE / 'src'}", f"/I{out}", *(str(NATIVE / p) for p in SOURCES),
            f"/Fe:{dll}", "/link", "/OPT:REF", "/INCREMENTAL:NO"]
        code, used = old.compile_dll(command, out, root, env)
        peak = {k: max(peak[k], used[k]) for k in peak}
        if code:
            raise RuntimeError(f"{mode} compile RED; original log retained: {out}")
        library = ctypes.CDLL(str(dll))
        buffer = ctypes.create_string_buffer(8192)
        entry = library.RunPlayerHeirCampaignAttachmentFixtures
        entry.argtypes = [ctypes.POINTER(ctypes.c_char), ctypes.c_size_t]
        entry.restype = ctypes.c_int
        if entry(buffer, len(buffer)):
            raise RuntimeError(buffer.value.decode("utf-8"))
        tested = json.loads(buffer.value)
        wire_entry = library.GetPlayerHeirCampaignAttachmentWire
        wire_entry.argtypes, wire_entry.restype = entry.argtypes, ctypes.c_int
        if wire_entry(buffer, len(buffer)):
            raise RuntimeError("wire fixture failed")
        frame = json.loads(buffer.value)
        assert set(frame) == {"type", "protocol_version", "request_id", "ok", "result"}
        assert frame["ok"] is True
        wire = frame["result"]
        assert set(wire) == {"step", "accepted", "status", "query_sequence",
                             "snapshot_revision", "campaign_root_context", "backend_id"}
        assert wire["query_sequence"] == 19
        component_root = wire["campaign_root_context"]
        if mode == "default-off":
            assert component_root == {"status": "available", "snapshot_revision": 77}
        else:
            c = component_root["player_heir_candidate_v1"]
            assert c["snapshot_revision"] == 77 and c["parent_frame_bound"] is True
            o = c["observation"]
            assert o["source_fixture"] is True and o["original_getter_source_bound"] is False
            assert o["candidate_character_id"] == -1845493758
            assert o["unavailable_reason"] is None
            assert o["before"] == o["after"] and len(o["before"]) == 8
            assert len(c) == 7 and len(o) == 15
        old.write_new(out / "wire.json", frame)
        suites.append({"mode": mode, "dll": old.pin(dll),
            "compile_log": old.pin(out / "compile.log"),
            "wire": old.pin(out / "wire.json"),
            "exact_ResultFrame_fragment": old.pin(out / "bridge_frame_fragment.hpp"),
            "fixture": tested})
    for row in record["source_pins"]:
        if old.pin(Path(row["path"])) != row:
            raise RuntimeError(f"input changed during fixture: {row['path']}")
    result = {
        "schema": "xar.player-heir-campaign-attachment-mock-result.v1",
        "machine_id": here, "started_at_utc": started, "ended_at_utc": old.utc(),
        "plan": old.pin(plan_path), "storage_card": old.pin(card_path),
        "status": "SOFTWARE_FIXTURES_PASS", "suites": suites,
        "peak_observed_usage": peak, "hard_limit_bytes": HARD_BYTES,
        "old29_suite_rerun": False, "production_bridge_compiled": False,
        "exact_production_ResultFrame_fragment_compiled": True,
        "base_root_serializers": "fixture stubs; original root validation not exercised",
        "Game_RPC_process_access": 0, "actual_H_credit": False,
    }
    old.write_new(root / "RESULT.json", result)
    if old.tree_usage(root)["guard_bytes"] > HARD_BYTES:
        raise RuntimeError("final hard limit exceeded; original result retained")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-output", type=Path)
    parser.add_argument("--build-root", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--storage-card", type=Path)
    parser.add_argument("--storage-card-sha256")
    args = parser.parse_args()
    if args.plan_output and args.build_root and not args.plan:
        old.write_new(args.plan_output, plan(args.build_root))
        print(json.dumps(old.pin(args.plan_output)))
    elif args.plan and args.storage_card and args.storage_card_sha256:
        print(json.dumps(run(args.plan, args.storage_card, args.storage_card_sha256)))
    else:
        parser.error("supply plan-output/build-root or pinned plan/card")

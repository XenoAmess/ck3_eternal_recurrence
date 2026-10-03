"""Focused production path self-liege regression; no SDK, game, pipe or window."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, sys
from run_ck3_12002_construction_serializer_tests import _environment

def run(root: Path, output: Path, expect_legacy_failure: bool) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    env = _environment(output)
    compiler = shutil.which("cl.exe", path=env["PATH"])
    bridge = root / "ck3_autonomous_player/native_bridge"
    sources = [bridge / "src" / name for name in (
        "ck3_12002_faction_alerts.cpp", "player_faction_alerts_v1.cpp",
        "player_faction_alerts_v1_serializer.cpp", "county_faction_final_12003.cpp",
        "faction_surrender_independent_liege_12003_wire_test.cpp")]
    binary = output / "faction-independent-liege.exe"
    result = {"status": "RED", "game_sdk_pipe_window_git_used": False,
              "scope": "production alerts reader -> actual C++ serializer -> Python normalizer",
              "expected_legacy_failure": expect_legacy_failure}
    try:
        compiled = subprocess.run([compiler, "/nologo", "/std:c++20", "/W4", "/WX",
            "/permissive-", "/EHsc", "/UNDEBUG", "/O2", f"/I{bridge / 'include'}",
            *(str(path) for path in sources), f"/Fe:{binary}"],
            cwd=output, env=env, capture_output=True, text=True, encoding="mbcs", errors="replace")
        (output / "compile.log").write_text(compiled.stdout + compiled.stderr, encoding="utf-8")
        compiled.check_returncode()
        produced = subprocess.run([str(binary)], cwd=output, env=env, capture_output=True)
        (output / "producer.jsonl").write_bytes(produced.stdout)
        produced.check_returncode()
        rows = [json.loads(row) for row in produced.stdout.splitlines()]
        assert len(rows) == 3
        sys.path.insert(0, str(root / "ck3_autonomous_player/src"))
        from xar_autoplayer.bridge.player_faction_alerts_contract import normalize_player_faction_alerts_v1
        for row in rows:
            assert normalize_player_faction_alerts_v1(row,
                expected_date_raw=row["date_raw"], expected_snapshot_revision=row["snapshot_revision"],
                expected_game_version=row["provenance"]["game_version"],
                expected_executable_sha256=row["provenance"]["executable_sha256"]) == row
        impacts = [row["targeting_factions"][0]["surrender_impact"] for row in rows]
        first, fallback, invalid = impacts
        assert fallback["status"] == "available" and fallback["county_loss_complete"] is True
        assert first["status"] == ("unavailable" if expect_legacy_failure else "available")
        if expect_legacy_failure:
            assert first["unavailable_reason"] == "surrender_title_collection_unavailable"
            assert first["seized_counties"] == [] and first["government_allows_state_faith"] is None
        else:
            assert first == fallback
            assert first["player_direct_title_loss_ids"] == [0x03000002, 0x03000003]
            assert len(first["member_counties"]) == 1 and len(first["seized_counties"]) == 2
            assert first["seized_counties"][0]["holder_character_id"] == 0x01000004
            assert first["seized_counties"][0]["top_liege_character_id"] == 0x01000001
            assert first["kingdoms"][0]["strict_majority_from_seized_counties"] is True
        assert invalid["status"] == "unavailable"
        assert invalid["unavailable_reason"] == "surrender_title_collection_unavailable"
        assert invalid["seized_counties"] == [] and invalid["ordinary_branch_title_sets_ready"] is False
        expected_predicate = None if expect_legacy_failure else False
        assert invalid["government_allows_state_faith"] is expected_predicate
        assert invalid["leader_at_war_with_target"] is expected_predicate
        result.update(status="EXPECTED_CAPABILITY_RED_REPRODUCED" if expect_legacy_failure else "GREEN",
            frames=3, compile_flags="/W4 /WX /O2",
            producer_sha256=hashlib.sha256(produced.stdout).hexdigest(),
            binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
            reader_sha256=hashlib.sha256(sources[0].read_bytes()).hexdigest())
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expect-legacy-failure", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.root.resolve(), args.output.resolve(), args.expect_legacy_failure)))

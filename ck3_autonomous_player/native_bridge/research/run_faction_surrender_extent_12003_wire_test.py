"""One offline production reader/serializer/Python round trip, no game or window."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, sys
from run_ck3_12002_construction_serializer_tests import _environment

def run(root: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    env = _environment(output)
    compiler = shutil.which("cl.exe", path=env["PATH"])
    bridge = root / "ck3_autonomous_player/native_bridge"
    sources = [bridge / "src" / name for name in (
        "ck3_12002_faction_alerts.cpp", "player_faction_alerts_v1.cpp",
        "player_faction_alerts_v1_serializer.cpp", "county_faction_final_12003.cpp",
        "faction_surrender_extent_12003_wire_test.cpp")]
    binary = output / "faction-surrender-extent.exe"
    result = {"status": "RED", "game_pipe_window_used": False,
              "scope": "production alerts reader -> actual C++ serializer -> Python normalizer"}
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
        assert len(rows) == 6
        sys.path.insert(0, str(root / "ck3_autonomous_player/src"))
        from xar_autoplayer.bridge.player_faction_alerts_contract import normalize_player_faction_alerts_v1
        for row in rows:
            normalized = normalize_player_faction_alerts_v1(row,
                expected_date_raw=row["date_raw"], expected_snapshot_revision=row["snapshot_revision"],
                expected_game_version=row["provenance"]["game_version"],
                expected_executable_sha256=row["provenance"]["executable_sha256"])
            assert normalized == row
        impacts = [row["targeting_factions"][0]["surrender_impact"] for row in rows]
        first = impacts[0]
        assert first["status"] == "available" and first["county_loss_complete"] is True
        assert len(first["member_counties"]) == 1 and len(first["seized_counties"]) == 2
        assert first["player_direct_title_loss_ids"] == [0x03000002, 0x03000003]
        assert first["seized_counties"][0]["holder_character_id"] == 0x01000004
        assert first["seized_counties"][0]["top_liege_character_id"] == 0x01000001
        assert first["kingdoms"][0]["strict_majority_from_seized_counties"] is True
        assert impacts[1]["kingdoms"][0]["strict_majority_from_seized_counties"] is False
        assert impacts[2]["government_allows_state_faith"] is True and impacts[2]["county_loss_complete"] is False
        assert impacts[3]["leader_at_war_with_target"] is True and impacts[3]["county_loss_complete"] is False
        assert impacts[4]["leader_at_war_with_target"] is False and impacts[4]["county_loss_complete"] is True
        assert impacts[5]["status"] == "unavailable" and impacts[5]["seized_counties"] == []
        assert all(impact["kingdom_outcome_complete"] is False for impact in impacts)
        result.update(status="GREEN", frames=6, compile_flags="/W4 /WX /O2",
            producer_sha256=hashlib.sha256(produced.stdout).hexdigest(),
            binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
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
    args = parser.parse_args()
    print(json.dumps(run(args.root.resolve(), args.output.resolve())))

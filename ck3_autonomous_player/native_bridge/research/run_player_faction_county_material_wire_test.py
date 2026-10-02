"""Compile the production county DTO serializer and consume its real JSON bytes.

This is an offline wire test; its values are examples, not live county results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from run_ck3_12002_construction_serializer_tests import _environment


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(root: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    environment = _environment(output)
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if compiler is None:
        raise RuntimeError("MSVC cl.exe is unavailable")
    bridge = root / "ck3_autonomous_player/native_bridge"
    sources = [bridge / "src" / name for name in (
        "player_faction_alerts_v1_serializer.cpp",
        "player_faction_county_material_v1_serializer_test.cpp",
    )]
    binary = output / "county-material-wire.exe"
    result = {"status": "RED", "scope": "offline production C++ to Python JSON wire",
              "game_sdk_pipe_window_used": False,
              "sources": {str(path.relative_to(root)): digest(path) for path in sources}}
    try:
        compiled = subprocess.run([
            compiler, "/nologo", "/std:c++20", "/W4", "/WX", "/permissive-",
            "/EHsc", "/UNDEBUG", "/O2", f"/I{bridge / 'include'}",
            *(str(path) for path in sources), f"/Fe:{binary}"],
            capture_output=True, text=True, encoding="mbcs", errors="replace",
            cwd=output, env=environment)
        (output / "compile.log").write_text(compiled.stdout + compiled.stderr,
                                            encoding="utf-8")
        compiled.check_returncode()
        produced = subprocess.run([str(binary)], capture_output=True, check=True,
                                  cwd=output, env=environment)
        (output / "producer.jsonl").write_bytes(produced.stdout)
        frames = [json.loads(line) for line in produced.stdout.splitlines() if line.strip()]
        assert len(frames) == 3
        sys.path.insert(0, str(root / "ck3_autonomous_player/src"))
        from xar_autoplayer.bridge.player_faction_alerts_contract import (
            normalize_player_faction_alerts_v1,
        )
        for frame in frames:
            normalized = normalize_player_faction_alerts_v1(
                frame, expected_date_raw=frame["date_raw"],
                expected_snapshot_revision=frame["snapshot_revision"],
                expected_game_version=frame["provenance"]["game_version"],
                expected_executable_sha256=frame["provenance"]["executable_sha256"],
            )
            assert normalized == frame
        counties = frames[0]["targeting_factions"][0]["county_member_observations"]
        assert counties[0]["county_opinion"] == {"raw": -37, "scale": 1}
        assert counties[0]["native_county_join_score"] == {"raw": -4_294_967_297, "scale": 100_000}
        assert counties[0]["can_add_county"] is False
        assert counties[0]["removal_queued"] is False
        assert counties[0]["native_leave_score_threshold"] == {"raw": -10, "scale": 1}
        assert counties[1]["county_opinion"] == {"raw": 0, "scale": 1}
        assert counties[1]["native_county_join_score"] == {"raw": 0, "scale": 100_000}
        assert counties[1]["native_leave_score_threshold"] == {"raw": 0, "scale": 1}
        partial = frames[1]["targeting_factions"][0]["county_member_observations"][0]
        assert partial["county_opinion"] is None
        assert partial["native_county_join_score"] is None
        assert partial["removal_queued"] is True
        assert partial["can_add_county"] is False
        assert partial["native_final_status"] == "unavailable"
        assert "county_member_observations" not in frames[2]["targeting_factions"][0]
        result.update(status="GREEN_OFFLINE_W4WX_PRODUCER_TO_PYTHON", frames=3,
                      compile_exit_code=compiled.returncode,
                      binary_sha256=digest(binary),
                      producer_sha256=digest(output / "producer.jsonl"))
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n",
                                            encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root.resolve(), args.output.resolve()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

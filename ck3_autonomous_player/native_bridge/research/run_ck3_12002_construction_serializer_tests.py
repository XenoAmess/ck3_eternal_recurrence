"""Exercise actual construction JSON production with offline DTOs only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _environment(build: Path) -> dict[str, str]:
    vswhere = Path(os.environ.get("ProgramFiles(x86)", "")) / (
        "Microsoft Visual Studio/Installer/vswhere.exe")
    installation = subprocess.run([
        str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property",
        "installationPath"], check=True, capture_output=True, text=True)
    vcvars = Path(installation.stdout.strip()) / "VC/Auxiliary/Build/vcvars64.bat"
    capture = build / "capture-msvc.cmd"
    capture.write_text(f'@call "{vcvars}" >nul\n@set\n', encoding="utf-8")
    output = subprocess.run([
        r"C:\Windows\System32\cmd.exe", "/d", "/c", str(capture)],
        check=True, capture_output=True, text=True, encoding="mbcs")
    environment = os.environ.copy()
    for line in output.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            environment[key.upper()] = value
    return environment


def _validate(rows: list[dict]) -> None:
    assert len(rows) == 2, "expected query-only and pending-ACK wire fixtures"
    for row in rows:
        assert row["game_version"] == "1.20.0.2"
        assert row["source_binding"] == "direct-world-building-manager"
        assert row["gui_cache_sampled"] is False
        assert row["status"] == "unavailable" and row["view_present"] is False
        assert row["holding_view_visibility"]["effective_visible"] is None
        assert row["executor_invocations"] == 0
        world = row["player_world_building_sources"]
        assert world["status"] == "source_available"
        assert world["player_character_id"] == 29829
        assert world["snapshot_revision"] == 3 and world["date_raw"] == 53168784
        assert world["native_final_legality_evaluated"] is True
        assert world["native_cost_evaluated"] is True
        sample = world["legal_samples"][0]
        assert sample["cost_raw_native"] == [15000000] + [0] * 9
        assert sample["cost_raw_slots"] == [15000000] + [0] * 7
    assert "private_action" not in rows[0]
    pending = rows[1]["private_action"]
    assert pending["status"] == "pending_receipt" and pending["applied"] is False
    assert pending["receiver_command_sequence"] == 7001
    assert pending["validator_calls"] == pending["materialize_calls"] == pending["receiver_calls"] == 1


def run(root: Path, build: Path) -> dict:
    build.mkdir(parents=True, exist_ok=True)
    environment = _environment(build)
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if compiler is None:
        raise RuntimeError("MSVC cl.exe is unavailable")
    bridge = root / "ck3_autonomous_player/native_bridge"
    sources = [bridge / "src" / name for name in (
        "ck3_12002_construction_serializer_test.cpp",
        "ck3_12002_construction_mailbox.cpp",
        "player_construction_view_probe_v1_mailbox.cpp",
        "ck3_12002_query_mailbox.cpp")]
    result = {"status": "RED", "ck3_started": False,
              "game_process_touched": False, "native_executors_called": False,
              "sources": {str(path.relative_to(root)): digest(path) for path in sources},
              "modes": {}, "fixture_scope": "offline DTOs through actual production serializer"}
    previous = None
    try:
        for mode, optimization in (("normal", "/Od"), ("optimized", "/O2")):
            binary = build / f"construction-serializer-12002-{mode}.exe"
            compiled = subprocess.run([
                compiler, "/nologo", "/std:c++20", "/W4", "/WX", "/permissive-",
                "/EHsc", "/UNDEBUG", optimization,
                f"/I{bridge / 'include'}", f"/I{bridge / 'src'}", f"/I{bridge / 'research'}",
                *(str(path) for path in sources), f"/Fe:{binary}"],
                capture_output=True, text=True, encoding="mbcs", errors="replace",
                cwd=build, env=environment)
            (build / f"compile-{mode}.log").write_text(
                compiled.stdout + compiled.stderr, encoding="utf-8")
            compiled.check_returncode()
            produced = subprocess.run([str(binary)], capture_output=True,
                                      check=True, cwd=build, env=environment)
            wire = produced.stdout.decode("utf-8")
            (build / f"fixtures-{mode}.jsonl").write_text(wire, encoding="utf-8")
            rows = [json.loads(line) for line in wire.splitlines() if line.strip()]
            for index, name in enumerate(("query-only", "pending-action")):
                target = build / f"{name}-{mode}.json"
                target.write_text(json.dumps(rows[index], indent=2) + "\n", encoding="utf-8")
            _validate(rows)
            if previous is not None:
                assert rows == previous, "optimized and normal serializer JSON differ"
            previous = rows
            result["modes"][mode] = {"status": "GREEN_W4WX", "exit_code": 0,
                                     "binary_sha256": digest(binary),
                                     "wire_sha256": digest(build / f"fixtures-{mode}.jsonl")}
            print(f"construction-serializer-12002-{mode}: GREEN_W4WX", flush=True)
        result["status"] = "GREEN_OFFLINE_PRODUCER"
        result["fixtures"] = {name: {"path": str(build / f"{name}-normal.json"),
                                     "sha256": digest(build / f"{name}-normal.json")}
                              for name in ("query-only", "pending-action")}
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        (build / "result.json").write_text(json.dumps(result, indent=2) + "\n",
                                           encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[3])
    parser.add_argument("--build-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root.resolve(), args.build_root.resolve()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

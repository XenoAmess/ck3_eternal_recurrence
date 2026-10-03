"""Strict focused .3 native producer -> serialized packets -> Python facades.

Only the new production fixture is executed. No CK3/SDK/desktop access.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_function(text, signature):
    start = text.index(signature)
    end = text.index("\n}", start) + 2
    return text[start:end]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-tree", type=Path,
                        default=Path(__file__).resolve().parents[3])
    parser.add_argument("--producer-tree", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_tree.resolve()
    producer = (args.producer_tree or source).resolve()
    native = source / "ck3_autonomous_player/native_bridge"
    changed_native = producer / "ck3_autonomous_player/native_bridge"
    own_native = Path(__file__).resolve().parents[1]
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    for relative in ("include/xar_bridge/ck3_12003_succession_modal.hpp",
                     "src/ck3_12003_succession_modal.cpp"):
        require((changed_native / relative).is_file(), "Missing actual .3 provider " + relative)

    bridge = (producer / "ck3_autonomous_player/native_bridge/src/bridge.cpp")
    if not bridge.is_file():
        bridge = native / "src/bridge.cpp"
    original_wire = bridge.read_text(encoding="utf-8-sig")
    signatures = ["std::string Number(", "void AppendJsonString(",
                  "std::string CurrentTimelineBlockerContextResultFrame(",
                  "std::string DeathSuccessionModalContinueResultFrame("]
    extracts = [extract_function(original_wire, signature) for signature in signatures]
    wire = out / "actual-bridge-timeline-serializer.cpp"
    wire.write_text(
        '#include "xar_bridge/current_timeline_blocker_context_v1.hpp"\n'
        '#include "xar_bridge/death_succession_modal_continue_v1.hpp"\n'
        '#include <array>\n#include <charconv>\n#include <cstdint>\n'
        '#include <string>\n#include <string_view>\n\n' + "\n\n".join(extracts) + "\n",
        encoding="utf-8")

    sys.path.insert(0, str(source / "tools"))
    from run_native_msvc import child_environment, initialize_msvc, visual_studio_installation
    env = child_environment(out)
    env, chain = initialize_msvc(visual_studio_installation(None, env), out, env)
    production_files = [
        native / "src/ck3_12002.cpp",
        changed_native / "src/ck3_12003_succession_modal.cpp",
        native / "src/current_timeline_blocker_context_v1.cpp",
        native / "src/death_succession_modal_continue_v1.cpp",
        native / "src/zhongguo_case_snapshot_v1.cpp",
        native / "src/zhongguo_scoreboard_state_v1.cpp",
    ]
    test = own_native / "src/current_timeline_blocker_12003_production_test.cpp"
    exe = out / "current_timeline_blocker_12003_production_test.exe"
    command = [chain["cl"], "/nologo", "/std:c++20", "/O2", "/MD", "/W4", "/WX",
               "/permissive-", "/EHsc", "/Gy", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
               "/DUNICODE", "/D_UNICODE", "/DXAR_CK3_SUCCESSION_FIXTURE_BRIDGE_WIRE",
               "/I" + str(changed_native / "include"), "/I" + str(native / "include"),
               *[str(path) for path in production_files], str(wire), str(test),
               "/Fe:" + str(exe), "/link", "/OPT:REF"]
    compiled = subprocess.run(command, cwd=out, env=env, capture_output=True)
    (out / "compile.log").write_bytes(compiled.stdout + compiled.stderr)
    receipt = {
        "schema": "xar.succession-modal-12003-focused-fixture/v1",
        "status": "RED" if compiled.returncode else "COMPILED",
        "source_tree": str(source), "producer_tree": str(producer),
        "source_reference": "Root frozen g44 / dafba6",
        "command": command, "compile_exit_code": compiled.returncode,
        "compiler_options": ["/O2", "/MD", "/W4", "/WX", "/Gy", "/std:c++20"],
        "production_files": [{"path": str(path), "sha256": digest(path)}
                             for path in production_files],
        "production_wire_source": {"path": str(bridge), "sha256": digest(bridge)},
        "production_wire_function_extracts": [
            {"signature": signature, "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest()}
            for signature, raw in zip(signatures, extracts)],
        "scope": "Actual .3 BindImage, native field/GUI readers and controller executor with fixture-owned mapped memory/callbacks; unchanged actual production serializers; existing transports/normalizer and newly registered facades",
        "sdk_calls": 0, "game_commands": 0, "window_inputs": 0, "shared_writes": 0,
        "git_mutations": 0, "natural_succession_credit": 0, "new_saved_days": 0,
        "old_fixture_matrix_rerun": False, "production_live": False,
    }
    result_path = out / "result.json"

    def record():
        result_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    if compiled.returncode:
        record()
        print((compiled.stdout + compiled.stderr).decode("mbcs", "replace"))
        return compiled.returncode
    executed = subprocess.run([str(exe), str(out)], cwd=out, env=env, capture_output=True)
    (out / "native.log").write_bytes(executed.stdout + executed.stderr)
    receipt.update(native_exit_code=executed.returncode,
                   status="NATIVE_GREEN" if executed.returncode == 0 else "RED")
    if executed.returncode:
        record()
        print((executed.stdout + executed.stderr).decode("utf-8", "replace"))
        return executed.returncode
    mcp_source = producer / "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py"
    consumer = own_native / "research/fixtures/consume_current_timeline_blocker_12003_native_packets.py"
    python_command = [sys.executable, "-B", "-O", str(consumer), str(source), str(out), str(mcp_source)]
    consumed = subprocess.run(python_command, cwd=out, env=env, capture_output=True)
    (out / "python.log").write_bytes(consumed.stdout + consumed.stderr)
    receipt.update(python_command=python_command, python_exit_code=consumed.returncode,
                   status="GREEN" if consumed.returncode == 0 else "RED")
    receipt["native_packets"] = [
        {"path": str(path), "sha256": digest(path)}
        for path in sorted(out.glob("*-native-command-result.json"))]
    receipt["test_file_pins"] = [{"path": str(path), "sha256": digest(path)}
                                for path in (test, consumer, Path(__file__).resolve())]
    record()
    print(json.dumps({"status": receipt["status"], "result": str(result_path),
                      "native_output": executed.stdout.decode("utf-8", "replace"),
                      "python_output": (consumed.stdout + consumed.stderr).decode("utf-8", "replace")},
                     ensure_ascii=False))
    return consumed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

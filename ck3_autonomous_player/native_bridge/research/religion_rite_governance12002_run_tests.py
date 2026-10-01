#!/usr/bin/env python3
"""Run combined Rite governance providers and the real owner-mailbox contract.

Only owned native-memory callbacks are exercised. This does not invoke CK3,
probe processes, open its pipe, install a desktop hook, or prove live readiness.
The component fixtures are deliberately excluded; their passed results are reused.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from test_government_runtime_adapter_12002_standalone import run_batch
from test_government_runtime_adapter_bridge_binder_v1_standalone import (
    visual_studio_developer_shell,
)


COMMON = (
    "ck3_12002.cpp",
    "ck3_12002_religion_context.cpp",
    "religion_rite_governance12002_state_rite.cpp",
    "religion_rite_governance12002_head.cpp",
    "religion_rite_governance12002_organization.cpp",
    "religion_rite_governance12002_context.cpp",
)
MAILBOX = (
    "main_thread_query_mailbox_v1.cpp",
    "ck3_12002_query_mailbox.cpp",
    "protocol.cpp",
    "religion_rite_governance12002_mailbox.cpp",
)
TESTS = (
    "religion_rite_governance12002_context_test.cpp",
    "religion_rite_governance12002_mailbox_test.cpp",
)
EXACT_SHA = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
WIRE_NAMES = (
    "distinct-zero.json", "legal-absent.json", "heads-unavailable.json",
    "components-unavailable.json",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_context(packet: dict, name: str) -> None:
    require(packet["schema"] == "ck3_12002_player_rite_governance_v1", "actual governance schema")
    require(packet["date_raw"] == 53175816 and packet["played_character_id"] == 0x03000004,
            "actual governance frame")
    if name == "components-unavailable.json":
        require(not packet["available"] and packet["frame_available"] and
                packet["observed_components"] == 0 and not packet["all_components_available"] and
                packet["unavailable_reason"] == "components_unavailable", "typed aggregate unavailable")
        return
    require(packet["available"] and packet["frame_available"], "observed aggregate")
    state, heads, counts = packet["state_rite"], packet["heads"], packet["organization"]
    if name == "distinct-zero.json":
        require(packet["observed_components"] == 3 and packet["all_components_available"], "three actual observations")
        require(state["actor_rite_id"] == 0 and state["actor_faith_main_rite_id"] == 0x8B00000C and
                state["player_primary_title"]["state_rite_id"] == 0x8C00000D and
                state["realm_primary_title"]["state_rite_id"] == 0x8D00000E, "four distinct Rite identities")
        require(heads["actor_rite_head_character_id"] == 0x85000005 and
                heads["faith_main_rite_head_character_id"] == 0x86000007 and
                heads["faith_religious_head_holder_character_id"] == 0x87000008 and
                heads["faith_religious_head_title_id"] == 0x90000003, "actual distinct head and title identities")
        require(counts["rite_id"] == 0 and counts["county_count"] == 0 and
                counts["character_follower_count"] == 0, "actual zero counts are not missing values")
    elif name == "legal-absent.json":
        require(packet["observed_components"] == 3 and state["actor_rite_id"] is None and
                heads["actor_rite_id"] is None and counts["rite_id"] is None and
                counts["county_count"] is None and counts["character_follower_count"] is None and
                state["realm_primary_title"]["title_id"] == 0x8F000002 and
                state["realm_primary_title"]["state_rite_id"] is None, "actual legal absence preserves identity scope")
    elif name == "heads-unavailable.json":
        require(packet["observed_components"] == 2 and not packet["all_components_available"] and
                state["available"] and counts["available"] and not heads["available"] and
                heads["unavailable_reason"] == "rite_head_unavailable" and
                state["realm_primary_title"]["state_rite_id"] == 0x8D00000E and
                counts["county_count"] == 0 and heads["actor_rite_head_character_id"] is None,
                "actual failed component does not hide independent observations")


def validate_wire(directory: Path, mailbox: bool) -> dict[str, str]:
    hashes = {}
    for name in WIRE_NAMES:
        path = directory / name
        packet = json.loads(path.read_text(encoding="utf-8"))
        if mailbox:
            require(packet["type"] == "command_result" and packet["protocol_version"] == 1 and
                    packet["request_id"] == 'governance"worker-fixture' and packet["ok"] is True,
                    "actual command_result envelope and escaped request ID")
            result = packet["result"]
            require(result["step"] == "query-player-rite-governance-v1" and result["accepted"] is True and
                    result["private_build"] is True and result["read_only"] is True and result["advertised"] is False and
                    result["game_version"] == "1.20.0.2" and result["executable_sha256"] == EXACT_SHA and
                    result["domain_key"] == "player_rite_governance_v1" and
                    result["backend_id"] == "ck3-1.20.0.2-native-player-rite-governance-v1" and
                    result["snapshot_revision"] == 701 and result["date_raw"] == 53175816,
                    "native metadata is present without consumer supplementation")
            require(result["status"] == ("unavailable" if name == "components-unavailable.json" else "observed"),
                    "actual command_result availability status")
            packet = result["player_rite_governance"]
            require(packet["capture_epoch"] != result["snapshot_revision"], "capture epoch is not worker revision")
        validate_context(packet, name)
        hashes[name] = sha(path)
    if mailbox:
        require(not (directory / "frame-changed.json").exists(), "changed owner frame has no success file")
        rejection = json.loads((directory / "frame-changed-rejection.json").read_text(encoding="utf-8"))
        require(rejection["success_wire_emitted"] is False and rejection["mailbox_reclaimed"] is True and
                bool(rejection["failure"]), "actual changed-frame runtime rejection")
    else:
        changed = json.loads((directory / "frame-changed.json").read_text(encoding="utf-8"))
        require(changed["available"] is False and changed["frame_available"] is False and
                changed["unavailable_reason"] == "state_changed" and changed["observed_components"] == 0,
                "changed provider frame discards available components")
    return hashes


def run_mode(root: Path, shell: Path, output: Path, mode: str) -> dict:
    native = root / "ck3_autonomous_player/native_bridge"
    output = output / mode
    output.mkdir(parents=True, exist_ok=True)
    compiler = [
        "cl.exe", "/nologo", "/std:c++20", "/EHsc", "/permissive-", "/Zc:__cplusplus",
        "/W4", "/WX", "/utf-8", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN", "/DUNICODE", "/D_UNICODE",
        f"/{mode}", "/DXAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1=1",
        "/DXAR_RITE_GOVERNANCE_STANDALONE_ADAPTER=1", f"/I{native / 'include'}",
    ]
    run_batch(command=compiler + ["/c", "/MP32"] + [str(native / "src" / name) for name in COMMON + MAILBOX],
              shell=shell, output=output, tag="common")
    results = []
    for name in TESTS:
        mailbox = "mailbox" in name
        tag = "mailbox" if mailbox else "context"
        executable = output / f"{tag}.exe"
        sources = COMMON + (MAILBOX if mailbox else ())
        run_batch(command=compiler + [str(native / "src" / name)] +
                  [str(output / Path(source).with_suffix(".obj")) for source in sources] +
                  ["User32.lib", f"/Fe:{executable}"], shell=shell, output=output, tag=tag)
        directory = output / f"{tag}-wire"
        directory.mkdir(exist_ok=True)
        completed = subprocess.run([str(executable), str(directory)], cwd=output,
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15)
        (output / f"{tag}.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
        require(completed.returncode == 0, f"{mode} {tag} fixture failed; see {output / f'{tag}.log'}")
        results.append({"fixture": name, "stdout": completed.stdout.strip(),
                        "executable_sha256": sha(executable), "actual_wire_sha256": validate_wire(directory, mailbox)})
    return {"mode": mode, "compile": "GREEN_W4_WX", "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    output = args.artifacts.resolve()
    require(output.drive.upper() == "Z:", "artifacts must reside on Z")
    output.mkdir(parents=True, exist_ok=True)
    temp = output / "temp"
    temp.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temp)
    root = Path(__file__).resolve().parents[3]
    shell = visual_studio_developer_shell()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run_mode, root, shell, output, mode) for mode in ("Od", "O2")]
        results = [future.result() for future in futures]
    sources = COMMON + MAILBOX + TESTS
    headers = (
        "religion_rite_governance12002_context.hpp", "religion_rite_governance12002_mailbox.hpp",
        "religion_rite_governance12002_state_rite.hpp", "religion_rite_governance12002_head.hpp",
        "religion_rite_governance12002_organization.hpp", "ck3_12002_religion_context.hpp",
        "ck3_12002_query_mailbox.hpp", "main_thread_query_mailbox_v1.hpp",
    )
    receipt = {
        "schema": "xar.religion_rite_governance12002_combined_runtime_fixture.v1",
        "status": "GREEN", "completed_at_utc": datetime.now(timezone.utc).isoformat(), "results": results,
        "source_sha256": {f"ck3_autonomous_player/native_bridge/src/{name}":
                          sha(root / "ck3_autonomous_player/native_bridge/src" / name) for name in sources},
        "header_sha256": {f"ck3_autonomous_player/native_bridge/include/xar_bridge/{name}":
                          sha(root / "ck3_autonomous_player/native_bridge/include/xar_bridge" / name) for name in headers},
        "test_script_sha256": sha(Path(__file__)),
        "actual_pipeline": "fixture-owned callbacks -> actual Core/component/aggregate reader -> worker TrySubmit -> owning ObservePumpDrain -> Wait/Reclaim -> native command_result serializer -> Python json decoder",
        "component_matrices_repeated": False, "dedicated_production_registration_tested": False,
        "mailbox_permit": "existing primary offline permitted_executor; central named registration pending",
        "native_adapter_unwrap": "standalone linker identity stand-in for bare fixture GameAdapter only",
        "ck3_launched": False, "ck3_process_queried": False, "ck3_pipe_opened": False,
        "desktop_accessed": False, "live_status": "not_run", "readiness": "static-ready",
    }
    (output / "result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "result": str(output / "result.json"),
                      "result_sha256": sha(output / "result.json"),
                      "fixtures": [row["stdout"] for result in results for row in result["results"]]}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error

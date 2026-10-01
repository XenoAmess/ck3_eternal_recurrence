"""Actual reform worker/owner mailbox/provider/command wire fixture; no CK3."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

from test_government_runtime_adapter_12002_standalone import run_batch
from test_government_runtime_adapter_bridge_binder_v1_standalone import visual_studio_developer_shell

NATIVE = Path(__file__).resolve().parent.parent
ROOT = NATIVE.parent.parent
SOURCES = (
    "ck3_12002.cpp", "ck3_12002_religion_context.cpp",
    "religion_reform12002_rite.cpp", "religion_reform12002_willingness.cpp",
    "religion_reform12002_window.cpp", "religion_reform12002_costs.cpp",
    "religion_reform12002_eligibility.cpp", "religion_reform12002_choices.cpp",
    "religion_doctrine12002_intrinsic.cpp", "religion_doctrine12002_choices.cpp",
    "religion_doctrine12002_tenet_rows.cpp", "religion_doctrine12002_selection.cpp",
    "religion_reform12002_query_runtime.cpp",
    "main_thread_query_mailbox_v1.cpp", "ck3_12002_query_mailbox.cpp",
    "protocol.cpp", "religion_reform12002_query_mailbox.cpp",
)
TEST = "religion_reform12002_query_mailbox_test.cpp"
HEADERS = (
    "ck3_12002.hpp", "ck3_12002_religion_context.hpp", "religion_reform12002_rite.hpp",
    "religion_reform12002_willingness.hpp", "religion_reform12002_window.hpp",
    "religion_reform12002_costs.hpp", "religion_reform12002_eligibility.hpp",
    "religion_reform12002_choices.hpp", "religion_reform12002_query_runtime.hpp",
    "religion_reform12002_query_mailbox.hpp", "main_thread_query_mailbox_v1.hpp",
    "ck3_12002_query_mailbox.hpp", "religion_doctrine12002_selection.hpp",
)
WIRE = (
    "visible-create.json", "visible-denied.json", "hidden-window.json", "absent-window.json",
    "cost-unavailable.json", "choices-unavailable.json", "context-unavailable.json",
    "query-unavailable.json", "doctrine-hidden-row.json", "empty-popup.json", "visible-zero-cost.json",
)
EXE_SHA = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
ACTOR = 0x03000004


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_wire(directory: Path) -> dict[str, str]:
    pins = {}
    for name in WIRE:
        path = directory / name
        packet = json.loads(path.read_text(encoding="utf-8"))
        require(packet["type"] == "command_result" and packet["protocol_version"] == 1 and
                packet["ok"] is True and packet["request_id"] == 'reform"mailbox-fixture',
                "actual complete protocol wire and escaped request ID")
        result = packet["result"]
        require(result["step"] == "query-player-religion-reform-context-v1" and
                result["domain_key"] == "player_religion_reform_context_v1" and
                result["backend_id"] == "ck3-1.20.0.2-native-player-religion-reform-context-v1" and
                result["accepted"] is True and result["private_build"] is True and
                result["read_only"] is True and result["advertised"] is False and
                result["game_version"] == "1.20.0.2" and result["executable_sha256"] == EXE_SHA and
                result["snapshot_revision"] == 701 and result["date_raw"] == 53175816,
                "actual caller serializer metadata")
        out = result["player_religion_reform_context"]
        require(out["schema"] == "ck3_12002_player_religion_reform_query_v1" and
                out["played_character_id"] == ACTOR and out["date_raw"] == 53175816 and
                out["capture_epoch"] != 701 and out["readiness"]["final_choice_legality_readiness"] is False,
                "actual assembly identity and honest choice legality")
        unavailable = name == "query-unavailable.json"
        require(out["available"] is not unavailable and
                result["status"] == ("unavailable" if unavailable else "observed"),
                "native read failure differs from observed false/absence")
        window = out["current_creation_window"]
        cost = out["current_draft_costs"]
        gate = out["current_draft_eligibility"]
        popup = out["current_popup_choices"]
        selection = out["current_doctrine_selection"]
        require(out["readiness"]["doctrine_final_selection_ready"] is selection["selection_ready"],
                "new final Doctrine readiness comes from actual observer")
        if not unavailable:
            require(out["current_rite_model"]["rite_id"] == 0x80000000 and
                    out["current_rite_model"]["faith_main_rite_id"] == 0x81000002 and
                    out["main_rite_unreformed"]["is_unreformed"] is True,
                    "actual actor Rite, Faith main Rite and full generation remain distinct")
        if name in ("visible-create.json", "visible-denied.json"):
            require(window["draft_observed"] and cost["piety_cost_raw"] == 9000000 and
                    cost["piety_missing_signed_raw"] == -2500000 and cost["has_enough_piety"] is True,
                    "visible current actual cost and signed surplus")
            require(gate["can_create_rite"] is (name == "visible-create.json") and
                    gate["can_edit_rite"] is (name == "visible-denied.json"),
                    "native final false is observed")
            require(len(popup["doctrines"]) == 1 and len(popup["tenets"]) == 1 and
                    popup["doctrines"][0]["native_observed_knowledge_button_gate"] is
                    (name == "visible-create.json"), "actual materialized popup row states")
            for row in popup["doctrines"] + popup["tenets"]:
                require(row["final_can_pick"] is None and row["final_choice_legality_readiness"] is False,
                        "partial popup helpers never imply final legal selection")
            require(selection["selection_ready"] is True and len(selection["rows"]) == 1 and
                    selection["selectable_doctrine_keys"] ==
                    (["doctrine_a"] if name == "visible-create.json" else []),
                    "actual final Doctrine selector observes allowed and native knowledge-denied states")
        elif name in ("hidden-window.json", "absent-window.json"):
            require(window["present"] is (name == "hidden-window.json") and
                    window["draft_observed"] is False and cost["piety_cost_raw"] is None and
                    gate["can_create_rite"] is None and popup["doctrines"] is None and popup["tenets"] is None,
                    "legitimate no current draft keeps all draft-only leaves null")
            require(selection["selection_ready"] is False, "no visible draft cannot imply final Doctrine selection")
        elif name == "cost-unavailable.json":
            require(cost["available"] is False and cost["piety_cost_raw"] is None and
                    cost["unavailable_reason"] == "native_quote_unavailable" and gate["available"] is True,
                    "failed native quote preserves independent actual final eligibility")
        elif name == "choices-unavailable.json":
            require(popup["available"] is False and popup["doctrines"] is None and
                    popup["unavailable_reason"] == "prophet_definition_unavailable" and cost["available"] is True,
                    "failed popup reader retains independently observed cost")
        elif name == "context-unavailable.json":
            require(out["current_context"]["available"] is False and
                    out["current_context"]["faith_fervor_raw"] is None and
                    out["current_rite_model"]["available"] is True,
                    "failed fixed point callback cannot invent zero or discard independent model")
        elif unavailable:
            require(out["unavailable_reason"] == "played_character_unavailable" and
                    cost["piety_cost_raw"] is None and popup["doctrines"] is None,
                    "whole query read callback failure has typed unavailability")
        elif name == "doctrine-hidden-row.json":
            require(selection["selection_ready"] is True and selection["selectable_doctrine_keys"] == [] and
                    selection["rows"][0]["native_should_display"] is False and
                    selection["rows"][0]["selection_blocker"] == "hidden_by_native_should_display",
                    "actual native ShouldDisplay excludes hidden materialized row")
        elif name == "empty-popup.json":
            require(popup["collection_readiness"] is True and popup["doctrines"] == [] and popup["tenets"] == [] and
                    selection["selection_ready"] is True and selection["rows"] == [] and
                    selection["selectable_doctrine_keys"] == [], "actual empty current popup is observed ready")
        elif name == "visible-zero-cost.json":
            require(cost["available"] is True and cost["piety_cost_raw"] == 0 and
                    cost["piety_missing_signed_raw"] == 0 and cost["has_enough_piety"] is True and
                    selection["selection_ready"] is True, "actual native zero quote survives complete result wire")
        require('"window":' not in path.read_text(encoding="utf-8"), "native pointer remains private")
        pins[name] = sha(path)
    require(not (directory / "frame-changed.json").exists(), "changed owner frame emits no successful wire")
    rejection = json.loads((directory / "frame-changed-rejection.json").read_text(encoding="utf-8"))
    require(rejection["success_wire_emitted"] is False and rejection["mailbox_reclaimed"] is True and
            bool(rejection["failure"]), "actual frame rejection preserves terminal reclamation")
    pins["frame-changed-rejection.json"] = sha(directory / "frame-changed-rejection.json")
    return pins


def run_mode(shell: Path, output: Path, mode: str) -> dict:
    directory = output / mode
    directory.mkdir(parents=True, exist_ok=True)
    compiler = ["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/utf-8",
                "/DNOMINMAX", f"/{mode}",
                "/DXAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1=1",
                "/DXAR_REFORM_MAILBOX_STANDALONE_ADAPTER=1", f"/I{NATIVE / 'include'}"]
    run_batch(command=compiler + ["/c", "/MP32"] + [str(NATIVE / "src" / name) for name in SOURCES],
              shell=shell, output=directory, tag="compile")
    executable = directory / "reform-query-mailbox.exe"
    run_batch(command=compiler + [str(NATIVE / "src" / TEST)] +
              [str(directory / Path(name).with_suffix(".obj")) for name in SOURCES] +
              ["User32.lib", f"/Fe:{executable}"], shell=shell, output=directory, tag="link")
    wires = directory / "wire"
    wires.mkdir(exist_ok=True)
    completed = subprocess.run([str(executable), str(wires)], cwd=directory, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=20)
    (directory / "run.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    require(completed.returncode == 0, f"{mode} actual mailbox fixture failed: {directory / 'run.log'}")
    return {"mode": mode, "compile": "GREEN_W4_WX", "stdout": completed.stdout.strip(),
            "executable_sha256": sha(executable), "actual_wire_sha256": validate_wire(wires)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    output = args.artifacts.resolve()
    output.mkdir(parents=True, exist_ok=True)
    temporary = output / "temp"
    temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    paths = [NATIVE / "src" / name for name in SOURCES + (TEST,)]
    paths += [NATIVE / "include/xar_bridge" / name for name in HEADERS]
    paths.append(Path(__file__).resolve())
    pins = {str(path.relative_to(ROOT)).replace("\\", "/"): sha(path) for path in paths}
    shell = visual_studio_developer_shell()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda mode: run_mode(shell, output, mode), ("Od", "O2")))
    require(pins == {str(path.relative_to(ROOT)).replace("\\", "/"): sha(path) for path in paths},
            "compiled source changed during new caller fixture")
    receipt = {
        "schema": "xar.ck3.religion-reform-query-mailbox-fixture/v1", "status": "GREEN",
        "time_utc": datetime.now(timezone.utc).isoformat(), "results": results, "source_sha256": pins,
        "actual_pipeline": "worker TrySubmit -> owning ObservePumpDrain -> actual core/component assembly -> Finish -> Wait/Reclaim -> complete native command_result -> Python JSON decoder",
        "old_component_matrices_repeated": False, "dedicated_production_registration_tested": False,
        "fixture_permit": "existing permitted_executor with exact typed callback; central dedicated named registration is separate",
        "ck3_accessed": False, "live_verified": False, "readiness": "static-ready library",
    }
    (output / "result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "result": str(output / "result.json"),
                      "result_sha256": sha(output / "result.json"), "fixtures": [r["stdout"] for r in results]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

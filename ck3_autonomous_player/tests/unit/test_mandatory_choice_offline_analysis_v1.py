from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.mandatory_choice_offline_analysis_v1 import (
    analyze_completed_incident, bound_backend_sha256,
    lookup_observed_ui_recovery, stable_source_key)


GAME_SHA = "a" * 64
BACKEND_SHA = "b" * 64


def test_backend_binding_uses_this_attempts_immutable_launch_pid(tmp_path):
    attempt = tmp_path / "attempt"
    state_dir = attempt / "state"
    state_dir.mkdir(parents=True)
    (attempt / "ROOT-ACTUAL-GAME-LAUNCH.json").write_text(
        json.dumps({"pid": 555, "dll_sha256": BACKEND_SHA.upper()}),
        encoding="utf-8")
    assert bound_backend_sha256(
        state_dir, {"diagnostics": {"bridge_pid": 555}}) == BACKEND_SHA
    assert bound_backend_sha256(
        state_dir, {"diagnostics": {"bridge_pid": 556}}) is None


def pair():
    frame = {"game_pid": 555, "connection_generation": 3,
             "actor_character_id": 31254, "episode_run_id": "episode-1",
             "date_raw": 53112345, "native_revision": 100}
    dto = {"window_id": "modal-kind-7", "window_instance_id": "0x12345678",
           "choices": [{"choice_id": "runtime-1", "label": "Proceed",
                        "role": "choice", "action_token": "nonce-token",
                        "bounds": {"left": 20, "top": 40, "width": 60, "height": 20}}],
           "stable_source_identity": {
               "game_exe_sha256": GAME_SHA, "native_adapter_id": "ck3-1.20.0.4",
               "root_runtime_name": "SomeModal", "root_type": "ModalView",
               "root_vtable_module_rva": "ck3.exe+0x1234",
               "choice_catalogue": [{"choice_id": "runtime-1",
                   "runtime_name": "PrimaryButton",
                   "widget_vtable_module_rva": "ck3.exe+0x5678",
                   "callback_identities": [{"vtable_module_rva": "ck3.exe+0x90",
                                            "function_module_rva": "ck3.exe+0xab"}]}]}}
    before = {"incident_id": "incident-1", "frame_binding": frame,
              "native_window": dto, "selection": {"choice_id": "runtime-1"}}
    post = {"verified": True, "old_window_id": "modal-kind-7",
            "old_instance": "0x12345678", "selected_choice_id": "runtime-1",
            "old_window_no_longer_blocking": True}
    after = {"incident_id": "incident-1",
             "original_blocking_window_advanced_verified": True,
             "action_receipt": {"accepted": True,
                                "mandatory_choice_postcondition": post}}
    return before, after


def progress(tmp_path, frame):
    path = tmp_path / "later-result.json"
    path.write_text(json.dumps({"semantic_frame": frame}), encoding="utf-8")
    return {"source_path": str(path),
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "json_pointer": ["semantic_frame"]}


def test_source_key_excludes_nonce_pointer_rect_and_includes_stable_widget_callback():
    before, _ = pair()
    original = stable_source_key(before["native_window"], backend_sha256=BACKEND_SHA)
    changed = copy.deepcopy(before["native_window"])
    changed["window_instance_id"] = "0xdeadbeef"
    changed["choices"][0]["action_token"] = "another-token"
    changed["choices"][0]["bounds"]["left"] = 900
    changed["choices"][0]["choice_id"] = "runtime-2"
    changed["stable_source_identity"]["choice_catalogue"][0]["choice_id"] = "runtime-2"
    assert stable_source_key(changed, backend_sha256=BACKEND_SHA)["source_key"] == original["source_key"]
    changed["stable_source_identity"]["choice_catalogue"][0]["callback_identities"][0]["function_module_rva"] = "ck3.exe+0xac"
    assert stable_source_key(changed, backend_sha256=BACKEND_SHA)["source_key"] != original["source_key"]
    assert stable_source_key(before["native_window"], backend_sha256=None) is None


def test_actual_native_source_identity_numeric_rvas_and_parallel_catalogue():
    before, _ = pair()
    dto = before["native_window"]
    source = dto.pop("stable_source_identity")
    source["backend_sha256"] = None
    source["root_vtable_module_rva"] = 0x1234
    source["choice_catalogue"] = [
        {"role": "modal_button_candidate", "runtime_name": "PrimaryButton",
         "widget_vtable_module_rva": 0x5678,
         "callback_identities": [{"vtable_module_rva": 0x90,
                                  "function_module_rva": 0xAB}]},
    ]
    dto["source_identity"] = source
    first = stable_source_key(dto, backend_sha256=BACKEND_SHA)
    assert first is not None
    later = copy.deepcopy(dto)
    later["window_instance_id"] = "0x99999999"
    later["choices"][0]["choice_id"] = "new-opaque-choice-id"
    later["choices"][0]["action_token"] = "new-token"
    later["choices"][0]["bounds"]["left"] = 123
    assert stable_source_key(later, backend_sha256=BACKEND_SHA)["source_key"] == first["source_key"]
    later["source_identity"]["choice_catalogue"][0]["callback_identities"][0][
        "function_module_rva"] = 0xAC
    assert stable_source_key(later, backend_sha256=BACKEND_SHA)["source_key"] != first["source_key"]


def test_only_old_window_gone_plus_later_same_game_date_progress_becomes_observed_ui(tmp_path):
    before, after = pair()
    later = {**before["frame_binding"], "date_raw": 53112346,
             "native_revision": 101}
    receipt = progress(tmp_path, later)
    known = analyze_completed_incident(before, after,
        backend_sha256=BACKEND_SHA, later_progress=receipt)
    assert known["status"] == "known_ui_recovery_observed"
    assert known["known_recovery_source"] == "observed-UI"
    assert known["business_effect_known"] is False
    assert known["semantic_optimal"] is False

    wrong = copy.deepcopy(after)
    wrong["action_receipt"]["mandatory_choice_postcondition"]["old_instance"] = "wrong"
    assert analyze_completed_incident(before, wrong,
        backend_sha256=BACKEND_SHA, later_progress=receipt)["status"] == "unresolved"
    no_date = progress(tmp_path, {**later, "date_raw": before["frame_binding"]["date_raw"]})
    assert analyze_completed_incident(before, after,
        backend_sha256=BACKEND_SHA, later_progress=no_date)["status"] == "unresolved"
    wrong_actor = progress(tmp_path, {**later, "actor_character_id": 999})
    assert analyze_completed_incident(before, after,
        backend_sha256=BACKEND_SHA, later_progress=wrong_actor)["status"] == "unresolved"
    altered = {**receipt, "source_sha256": "0" * 64}
    assert analyze_completed_incident(before, after,
        backend_sha256=BACKEND_SHA, later_progress=altered)["status"] == "unresolved"


def test_separate_worker_reads_completed_pairs_and_later_immutable_mcp_frame(tmp_path):
    script = Path(__file__).resolve().parents[2] / "offline_mandatory_choice_worker.py"
    spec = importlib.util.spec_from_file_location("mandatory_choice_worker_candidate", script)
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)
    attempt = tmp_path / "attempt"
    evidence = attempt / "state" / "evidence" / "unknown-mandatory-choices"
    evidence.mkdir(parents=True)
    (attempt / "ROOT-ACTUAL-GAME-LAUNCH.json").write_text(
        json.dumps({"pid": 555, "dll_sha256": BACKEND_SHA}), encoding="utf-8")
    before, after = pair()
    before.update(schema="xar.unknown-mandatory-choice-incident/v1",
                  captured_at_utc="2026-10-15T08:00:00+00:00")
    after.update(schema="xar.unknown-mandatory-choice-incident/v1",
                 captured_at_utc="2026-10-15T08:00:01+00:00")
    first = evidence / "incident-1.before.json"
    first.write_text(json.dumps(before), encoding="utf-8")
    after["before"] = {"sha256": hashlib.sha256(first.read_bytes()).hexdigest()}
    (evidence / "incident-1.after.json").write_text(json.dumps(after), encoding="utf-8")
    responses = attempt / "p01-responses"
    responses.mkdir()
    later = {**before["frame_binding"], "date_raw": 53112346,
             "native_revision": 101}
    later.pop("game_pid")
    (responses / "0002-1-result.json").write_text(json.dumps({
        "ended_at_utc": "2026-10-15T08:00:02+00:00",
        "result": {"is_error": False, "structured_content": later}}), encoding="utf-8")
    output = tmp_path / "review"
    records = worker.review_once(attempt, output)
    assert records[0]["status"] == "known_ui_recovery_observed"
    review = json.loads(Path(records[0]["review"]).read_text(encoding="utf-8"))
    assert review["known_recovery_source"] == "observed-UI"
    assert review["business_effect_known"] is False
    assert list((output / "known-ui-recovery").rglob("incident-1.json"))
    known = lookup_observed_ui_recovery(
        before["native_window"], backend_sha256=BACKEND_SHA, review_root=output)
    assert known["known_recovery_source"] == "observed-UI"
    assert known["business_effect_known"] is False
    mismatched = copy.deepcopy(before["native_window"])
    mismatched["stable_source_identity"]["choice_catalogue"][0][
        "callback_identities"][0]["function_module_rva"] = "ck3.exe+0xac"
    assert lookup_observed_ui_recovery(
        mismatched, backend_sha256=BACKEND_SHA, review_root=output) is None

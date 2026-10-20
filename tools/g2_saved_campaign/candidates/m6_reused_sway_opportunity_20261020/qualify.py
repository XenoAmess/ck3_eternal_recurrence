"""One bounded, synthetic qualification of the exact Source25 M6 delta."""
from __future__ import annotations

import copy
import ctypes
import difflib
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone

from transform import BASE_COMMIT, FORMAL, HELPER, SCHEDULE, pin, transform_sources

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
STORAGE = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01")
CARD = STORAGE / "G2-PARALLEL-SOURCE-QUALIFICATION1MiB0630-ADMITTED01.json"
CARD_SHA = "0d279e0bcc91159536b4e2c86a8079f24db195df9456a5c819d7a773ecdae1d4"
ARTIFACT = STORAGE / "G2-PARALLEL-QUALIFICATION0630-01/m6"
SDK = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/sdk-v20261019-candidate/src20")
LEDGER = REPO / "docs/ck3-native-ai/evidence/m6-sway-closed-ledger-2026-10-20.json"
SCHEDULE_EVIDENCE = REPO / "docs/ck3-native-ai/evidence/m6-sway-closed-schedule-2026-10-20.json"
MACHINE = "xenoamess-full-tower-eb9d2c1186"


def now():
    return datetime.now(timezone.utc).isoformat()


def load_module(name, data, path):
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader=None))
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(data, str(path), "exec"), module.__dict__)
    return module


def allocated(path):
    class Standard(ctypes.Structure):
        _fields_ = [("allocation", ctypes.c_longlong), ("length", ctypes.c_longlong),
                    ("links", ctypes.c_uint32), ("delete_pending", ctypes.c_ubyte),
                    ("directory", ctypes.c_ubyte)]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
        ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    kernel.CreateFileW.restype = ctypes.c_void_p
    kernel.GetFileInformationByHandleEx.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                                   ctypes.c_void_p, ctypes.c_uint32]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.CreateFileW(str(path), 0x80, 7, None, 3, 0, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        result = Standard()
        if not kernel.GetFileInformationByHandleEx(handle, 1, ctypes.byref(result), ctypes.sizeof(result)):
            raise ctypes.WinError(ctypes.get_last_error())
        return result.allocation
    finally:
        kernel.CloseHandle(handle)


def usage(root):
    # Only this explicitly assigned, finite lane is inspected; no other tree scan.
    files = [p for p in root.rglob("*") if p.is_file()] if root.exists() else []
    dirs = [root, *[p for p in root.rglob("*") if p.is_dir()]] if root.exists() else []
    return {"files": len(files), "logical_bytes": sum(p.stat().st_size for p in files),
            "file_allocated_bytes": sum(allocated(p) for p in files),
            "directory_overhead_conservative_bytes": 4096 * len(dirs),
            "conservative_total_bytes": sum(allocated(p) for p in files) + 4096 * len(dirs)}


def write_new(path, data):
    with path.open("xb") as stream:
        stream.write(data)


def main():
    started = now()
    monotonic_start = time.monotonic()
    card_bytes = CARD.read_bytes()
    assert hashlib.sha256(card_bytes).hexdigest() == CARD_SHA
    card = json.loads(card_bytes)
    assert card["machine_id"] == MACHINE
    assert datetime.now(timezone.utc) < datetime.fromisoformat(card["review_at_utc"])
    assert Path(card["lanes"]["m6"]["artifact_root"]).resolve() == ARTIFACT.resolve()
    assert not ARTIFACT.exists(), "create-only qualification attempt already exists"
    assert usage(HERE)["conservative_total_bytes"] + 16384 <= 65536
    ARTIFACT.mkdir(parents=True)
    source = {p: subprocess.run(["git", "show", f"{BASE_COMMIT}:{p}"], cwd=REPO,
                check=True, stdout=subprocess.PIPE).stdout for p in (SCHEDULE, FORMAL)}
    helper_bytes = (HERE / "reused_sway_opportunity_v1.py").read_bytes()
    output = transform_sources(source, helper_bytes)
    # Export is an observation only: these inputs must actually be Source25.
    for path, data in source.items():
        assert (SDK / path.split("src/", 1)[1]).read_bytes() == data
    differences = []
    for path, data in output.items():
        differences.extend(difflib.unified_diff(source.get(path, b"").decode().splitlines(True),
            data.decode().splitlines(True), fromfile="a/" + path, tofile="b/" + path))
    diff_bytes = "".join(differences).encode()
    write_new(HERE / "exact-source25.diff", diff_bytes)
    sys.path.insert(0, str(SDK))
    importlib.import_module("xar_autoplayer")
    helper = load_module("xar_autoplayer.reused_sway_opportunity_v1", helper_bytes, HELPER)
    formal = load_module("xar_autoplayer.sway_formal_consumer", output[FORMAL], FORMAL)
    scheduler = load_module("xar_autoplayer.ordinary_sway_schedule_v1", output[SCHEDULE], SCHEDULE)
    from xar_autoplayer.bridge.version_identity import CK3_12004
    from xar_autoplayer.bridge.active_scheme_sway_private_transport import _valid_active_sway_instances
    original_ledger = json.loads(LEDGER.read_bytes())
    original = original_ledger["resolved"]
    original_bytes = json.dumps(original_ledger, sort_keys=True)
    date = 53274960
    frame = {"snapshot_id": "synthetic:10", "revision": 20, "native_revision": 10,
        "date_raw": date, "paused": True, "map_ready": True,
        "episode_run_id": "synthetic-m6-new-independent-episode",
        "played_character": {"character_id": 40526, "alive": True},
        "active_context": {"active_event": None, "pending_character_interaction": None},
        "diagnostics": {"bridge_pid": 777, "connection_generation": 9}}
    root = {"status": "available", "player_character_id": 40526,
        "player_character_alive": True, "snapshot_revision": 10, "date_raw": date,
        "direct_landed_vassal_character_ids": [34973, 35899]}
    state = json.loads(SCHEDULE_EVIDENCE.read_bytes())
    state["frontier_membership"] = [34973, 35899]
    tests = []

    def check(name, operation):
        before = time.monotonic()
        try:
            operation()
            tests.append({"name": name, "status": "PASS", "seconds": time.monotonic() - before})
        except BaseException as error:
            tests.append({"name": name, "status": "FAIL", "error": repr(error),
                          "traceback": traceback.format_exc()})
            raise

    def equal(actual, expected):
        assert actual == expected, (actual, expected)

    def gap(resolved=original):
        return helper.reused_sway_observation_gap_v1(resolved, actor_character_id=40526, date_raw=date)

    def job(*, ledger=original_ledger, snapshot=frame, current_root=root, current_state=state, **kwargs):
        return scheduler.plan_ordinary_sway_schedule_v1(snapshot, selected_step=kwargs.pop("selected_step", "life-advance"),
            root=current_root, ledger=ledger, state=current_state, **kwargs)

    def quote(target=34973):
        return {"schema": "active-scheme-sway-private-read-v1", "snapshot_revision": 10,
            "capture_epoch": 10, "container_generation": 90, "date_raw": date,
            "actor_character_id": 40526, "target_character_id": target,
            "target_opinion_of_actor": 14, "active_scheme_count": 0, "active_sway_instances": [],
            "matching_sway_active": False, "native_complete_can_send": True, "native_legal_now": True,
            "queried_revision": 20, "queried_native_revision": 10,
            "exact_ck3_build": CK3_12004.game_version, "exe_sha256": CK3_12004.executable_sha256}

    try:
        check("existing_typed_native_input_has_complete_empty_inventory", lambda: equal(
            _valid_active_sway_instances(quote()), True))
        check("actual_closed_reuse_shape_recognized_without_terminal_credit", lambda: equal(
            gap()["instance_terminal_outcome_observed"], False))
        check("round_robin_reaches_new_target_after_reuse", lambda: equal(job()["target_character_id"], 35899))
        check("same_target_fresh_legal_empty_read_can_enter_new_uuid", lambda: equal(
            formal._same_target_followup(original, quote())["decision"], "repeat_selected_target"))
        check("quiet_observer_does_not_repeat_purged_instance_rpc", lambda: equal(
            job(active_observation_only=True)["job"], None))
        check("war_priority_preserved", lambda: equal(job(selected_step="war-existing-sentinel")["job"], None))
        check("same_frame_root_required", lambda: equal(job(current_root={**root, "date_raw": date - 24})["job"], None))
        check("existing_month_cadence_retained", lambda: equal(
            job(current_state={**state, "next_check_date_raw": date + 720})["job"], None))
        check("pending_is_never_rotated_or_replayed", lambda: equal(job(ledger={**original_ledger,
            "pending": {"actor_character_id": 40526, "target_character_id": 34973,
                        "action_id": "synthetic-old-pending"}})["job"], "reconcile_pending"))
        for name, changes in (
            ("plain_absence", {"storage_slot_reused": False}),
            ("unread_source", {"instance_source_observed": False}),
            ("present_instance", {"instance_present": True}),
            ("wrong_generation", {"scheme_instance_generation": 6}),
            ("wrong_build", {"exe_sha256": "0" * 64}),
            ("status_zero", {"native_status_observed": True, "native_status_raw": 0}),
        ):
            altered = copy.deepcopy(original)
            altered["latest_instance_observation"]["native_observation"].update(changes)
            check("reuse_proof_rejects_" + name, lambda altered=altered: equal(gap(altered), None))
        altered = copy.deepcopy(original)
        altered["latest_instance_observation"]["action_id"] = "synthetic-other-action"
        check("reuse_proof_rejects_other_original_action", lambda: equal(gap(altered), None))
        altered = copy.deepcopy(original)
        altered["latest_instance_observation"]["source_date_raw"] = date + 24
        check("reuse_proof_rejects_future_observation", lambda: equal(gap(altered), None))
        altered = copy.deepcopy(original)
        altered["terminal_intervention"]["instance_terminal_outcome_observed"] = True
        check("observed_terminal_keeps_original_lifecycle_policy", lambda: equal(gap(altered), None))
        altered = copy.deepcopy(original)
        altered["native_receipt"].update(scheme_instance_id=2, scheme_instance_generation=0)
        for container in (altered["latest_instance_observation"],
                          altered["latest_instance_observation"]["native_observation"]):
            container.update(scheme_instance_id=2, scheme_instance_generation=0)
        check("generation_zero_valid_reuse_supported", lambda: equal(gap(altered)["scheme_instance_generation"], 0))
        for name, changes in (
            ("occupied", {"active_scheme_count": 1}),
            ("boolean_count", {"active_scheme_count": False}),
            ("unknown_count", {"active_scheme_count": None}),
            ("missing_inventory", {"active_sway_instances": None}),
            ("nonempty_inventory", {"active_sway_instances": [{}]}),
            ("still_matching", {"matching_sway_active": True}),
            ("illegal", {"native_legal_now": False}),
            ("incomplete_cansend", {"native_complete_can_send": False}),
            ("wrong_current_build", {"exe_sha256": "0" * 64}),
            ("old_current_date", {"date_raw": 53274216}),
        ):
            altered_quote = {**quote(), **changes}
            check("fresh_read_rejects_" + name, lambda altered_quote=altered_quote: equal(
                helper.fresh_empty_sway_slot_after_reuse_v1(original, altered_quote), None))

        def integration(target):
            state_dir = ARTIFACT / ("same-target" if target == 34973 else "next-target")
            state_dir.mkdir()
            (state_dir / formal.LEDGER_FILE).write_text(json.dumps(original_ledger), encoding="utf-8")
            class Driver:
                allow_private_active_scheme_sway_action = True
                def __init__(self):
                    self.state_dir = state_dir
                    self.submits = self.receipts = self.reads = 0
                def take_snapshot(self):
                    return copy.deepcopy(frame)
                def submit_active_scheme_sway_private_v1(self, *, readback, action_id):
                    self.submits += 1
                    self.action_id = action_id
                    return {"stage": "submitted_verification_pending", "action_id": action_id}
                def query_active_scheme_sway_receipt_private_v1(self, **kwargs):
                    self.receipts += 1
                    binding = {"actor_character_id": 40526, "episode_run_id": frame["episode_run_id"],
                               "bridge_pid": 777, "connection_generation": 9, "date_raw": date}
                    return {"schema": "active-scheme-sway-formal-private-v1", "stage": "applied",
                        "postcondition_verified": True, "action_id": self.action_id,
                        "scheme_instance_id": 100663500, "scheme_instance_generation": 6,
                        "post_capture_epoch": 11, "post_date_raw": date,
                        "exact_ck3_build": CK3_12004.game_version, "exe_sha256": CK3_12004.executable_sha256,
                        formal.RECEIPT_SOURCE_KEY: {"schema": "xar.ck3.sway-receipt-source-frame.v1",
                                                  "before": binding, "after": binding}}
                def query_active_scheme_sway_target_private_v1(self, **kwargs):
                    self.reads += 1
                    return {**quote(target), "capture_epoch": 12, "active_scheme_count": 1,
                        "matching_sway_active": True, "native_complete_can_send": False, "native_legal_now": False,
                        "active_sway_instances": [{"scheme_instance_id": 100663500,
                            "scheme_instance_generation": 6, "target_character_id": target,
                            "progress": 0, "progress_goal": 355, "is_exposed": False, "is_frozen": False}]}
            driver = Driver()
            result = formal.consume_sway_private_once(driver, target_character_id=target,
                                                      snapshot=frame, readback=quote(target))
            equal(result["status"], "applied")
            equal((driver.submits, driver.receipts, driver.reads), (1, 1, 1))
            assert result["action_id"] != original["action_id"]
            assert "first_named_gain_intervention" not in result
            assert "terminal_intervention" not in result
            historical = result["previous_interventions"][-1]
            equal(historical, {k: v for k, v in original.items() if k != "previous_interventions"})
            equal(historical["terminal_intervention"]["instance_terminal_outcome_observed"], False)
            equal(historical["first_named_gain_intervention"]["scheme_sway_opinion"]["value"], 25)
            duplicate = formal.consume_sway_private_once(driver, target_character_id=target,
                snapshot=frame, readback=driver.query_active_scheme_sway_target_private_v1())
            equal(duplicate["status"], "already_applied")
            equal(driver.submits, 1)
            following = {**frame, "native_revision": 11, "date_raw": date + 24}
            consumed = formal.consume_sway_following_turn(state_dir, following)
            equal(consumed["next_turn_consumed"], True)
            equal(consumed["previous_interventions"][-1]["terminal_intervention"]["instance_terminal_outcome_observed"], False)

        check("same_target_full_formal_once_archive_and_following", lambda: integration(34973))
        check("different_target_full_formal_once_archive_and_following", lambda: integration(35899))
        check("read_only_scheduler_and_helper_never_mutate_historical_ledger", lambda: equal(
            json.dumps(original_ledger, sort_keys=True), original_bytes))
        status = "SOURCE_AND_SYNTHETIC_QUALIFICATION_PASS_RUNTIME_ADOPTION_PENDING"
    except BaseException:
        status = "SOURCE_OR_SYNTHETIC_QUALIFICATION_FAILED"
    report = {"schema": "xar.m6.reused-sway-opportunity-source-qualification/v1",
        "machine_id": MACHINE, "observed_at_utc": now(), "started_at_utc": started,
        "review_at_utc": card["review_at_utc"], "status": status, "base_commit": BASE_COMMIT,
        "source_inputs": {p: pin(data) for p, data in source.items()},
        "production_outputs": {p: pin(data) for p, data in output.items()},
        "diff": {"path": str(HERE / "exact-source25.diff"), **pin(diff_bytes)},
        "storage_card": {"path": str(CARD), **pin(card_bytes)},
        "historical_shape_basis": {"path": str(LEDGER), **pin(LEDGER.read_bytes()),
            "synthetic_endpoint_only": True, "new_live_credit": 0},
        "tests": tests, "passed": sum(t["status"] == "PASS" for t in tests),
        "failed": sum(t["status"] != "PASS" for t in tests),
        "wall_seconds": time.monotonic() - monotonic_start,
        "runtime_adopted": False, "G2_M6_complete": False, "G2_credit": "6/8 unchanged",
        "Game_Native_MCP_Task_desktop_actions": 0,
        "source_usage_before_report": usage(HERE), "artifact_usage_before_report": usage(ARTIFACT),
        "artifact_atomic_temporary_peak_extra_cap": 49152,
        "retention": {"category": "derived", "manual_review_at_utc": card["review_at_utc"],
            "policy_version": "1.0.0", "continue_retention_reason": "Source qualification and unresolved runtime-adoption review"}}
    raw = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode()
    write_new(ARTIFACT / "RESULT.json", raw)
    write_new(HERE / "SOURCE-QUALIFICATION.json", raw)
    source_usage, artifact_usage = usage(HERE), usage(ARTIFACT)
    assert source_usage["conservative_total_bytes"] <= 65536, source_usage
    assert artifact_usage["conservative_total_bytes"] + 49152 <= 196608, artifact_usage
    print(json.dumps({"status": status, "passed": report["passed"], "failed": report["failed"],
        "source_usage": source_usage, "artifact_usage": artifact_usage,
        "result": {"path": str(ARTIFACT / "RESULT.json"), **pin(raw)},
        "runtime_adopted": False}, ensure_ascii=False))
    return 0 if "PASS_RUNTIME" in status else 1


def correct_allocation_only():
    original_path = ARTIFACT / "RESULT.json"
    original_bytes = original_path.read_bytes()
    report = json.loads(original_bytes)
    assert report["status"] == "SOURCE_AND_SYNTHETIC_QUALIFICATION_PASS_RUNTIME_ADOPTION_PENDING"
    source_usage, artifact_usage = usage(HERE), usage(ARTIFACT)
    # One new correction leaf per lane, each bounded to a single 4 KiB cluster.
    assert source_usage["conservative_total_bytes"] + 4096 <= 65536, source_usage
    assert artifact_usage["conservative_total_bytes"] + 4096 + 49152 <= 196608, artifact_usage
    correction = {"schema": "xar.m6.reused-sway-allocation-correction/v1", "machine_id": MACHINE,
        "observed_at_utc": now(), "review_at_utc": report["review_at_utc"],
        "original_result": {"path": str(original_path), **pin(original_bytes)},
        "correction": "Original GetCompressedFileSizeW read returned logical length for plain files. File allocation here is actual FileStandardInfo.AllocationSize; directories retain 4096 B conservative overhead each.",
        "production_source_unchanged": True, "tests_rerun": 0,
        "source_usage_before_correction": source_usage, "artifact_usage_before_correction": artifact_usage,
        "source_after_correction_cap": source_usage["conservative_total_bytes"] + 4096,
        "artifact_after_correction_and_atomic_temp_cap": artifact_usage["conservative_total_bytes"] + 4096 + 49152,
        "qualifier_current": {"path": str(Path(__file__).resolve()), **pin(Path(__file__).read_bytes())}}
    raw = (json.dumps(correction, ensure_ascii=False, indent=2) + "\n").encode()
    assert len(raw) <= 4096
    write_new(ARTIFACT / "ALLOCATION-CORRECTION.json", raw)
    write_new(HERE / "ALLOCATION-CORRECTION.json", raw)
    print(json.dumps({"correction": {"path": str(ARTIFACT / "ALLOCATION-CORRECTION.json"), **pin(raw)},
        "source_actual": usage(HERE), "artifact_actual": usage(ARTIFACT), "tests_rerun": 0}))
    return 0


if __name__ == "__main__":
    sys.exit(correct_allocation_only() if sys.argv[1:] == ["--allocation-correction-only"] else main())

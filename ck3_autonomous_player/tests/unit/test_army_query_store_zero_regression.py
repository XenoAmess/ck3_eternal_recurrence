"""Real offline storage consumers: default-zero exports and bounded opt-in.

Native callbacks use the existing in-memory endpoint. No game, named pipe or
captured raw input is opened; positive-budget evidence is tiny synthetic data.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from test_native_bridge_driver import FakeEndpoint, _army, _army_strength, _hello, _snapshot
from xar_autoplayer.bridge import army_query_history_store as history_store
from xar_autoplayer.bridge.army_strengths_profile_contract import (
    OBSERVED_HISTORY_FULL_PROFILE,
    OBSERVED_PHASE_KEYS,
    ORDINARY_CORE_PROFILE,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver,
    load_native_driver_state_for_resume,
)


QUERY = "query-army-strengths-v1"
RAW_MARKER = "synthetic-diagnostic-never-export"


def _storage_payload(profile: str = ORDINARY_CORE_PROFILE) -> dict[str, object]:
    row = _army_strength(81, "player", [])
    if profile == OBSERVED_HISTORY_FULL_PROFILE:
        # Only the storage boundary consumes these synthetic journal values.
        row.update({key: {"records": [RAW_MARKER]} for key in OBSERVED_PHASE_KEYS})
    return {
        "step": QUERY,
        "accepted": True,
        "status": "available",
        "backend_id": "native-headless",
        "query_sequence": 7,
        "queried_snapshot_id": "native:40",
        "queried_revision": 2,
        "queried_native_revision": 40,
        "army_strengths_profile": profile,
        "army_observed_phase_coverage": (
            "exported_retained" if profile == OBSERVED_HISTORY_FULL_PROFILE
            else "not_requested"
        ),
        "army_strengths": [row],
        "diagnostic_payload": {"synthetic": RAW_MARKER * 32},
    }


def _make_driver(state_dir: Path, *, reply_metadata: bool = True):
    endpoint = FakeEndpoint(r"\\.\pipe\xar_army_zero_store_unit")
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name, endpoint=endpoint, state_dir=state_dir,
        command_timeout_seconds=0.1,
    )
    endpoint.publish(_hello("game.state.snapshot", "game.command." + QUERY))
    endpoint.publish(_snapshot(
        40, played_character={"character_id": 707, "alive": True},
        active_wars=[], player_armies=[_army(81, controllable=True)],
    ))
    before = driver.take_internal_semantic_snapshot()

    def answer(frame):
        if frame.get("type") != "execute_step":
            return
        assert frame["step"] == QUERY
        assert frame["army_strengths_profile"] == ORDINARY_CORE_PROFILE
        result = {
            "step": QUERY, "accepted": True, "status": "available",
            "query_sequence": 7, "army_strengths": [_army_strength(81, "player", [])],
        }
        if reply_metadata:
            result.update(
                army_strengths_profile=ORDINARY_CORE_PROFILE,
                army_observed_phase_coverage="not_requested",
            )
        endpoint.publish({
            "type": "command_result", "protocol_version": 1,
            "request_id": frame["request_id"], "ok": True, "result": result,
        })

    endpoint.send_hook = answer
    return driver, endpoint, before


@pytest.mark.parametrize("profile", [ORDINARY_CORE_PROFILE, OBSERVED_HISTORY_FULL_PROFILE])
def test_zero_budget_preserves_identity_without_exporting_diagnostics(tmp_path, monkeypatch, profile):
    evidence = tmp_path / "not-created"
    result = _storage_payload(profile)
    original = copy.deepcopy(result)

    def forbidden_export(*args, **kwargs):
        raise AssertionError("zero-budget recording must not encode or export a full result")

    monkeypatch.setattr(history_store, "write_json_exclusive", forbidden_export)
    summary = history_store.ArmyQueryHistoryStore(evidence, 0).record(result)
    assert not evidence.exists()
    assert list(tmp_path.iterdir()) == []
    assert result == original
    assert summary["accepted"] is True and summary["status"] == "available"
    assert summary["army_strengths_profile"] == profile
    assert summary["army_observed_phase_coverage"] == result["army_observed_phase_coverage"]
    assert summary["query_sequence"] == 7 and summary["army_count"] == 1
    assert summary["armies"][0]["current_soldiers"] == 1200
    assert summary["full_result_preserved"] is False
    assert "raw_result_reference" not in summary and "army_strengths" not in summary
    assert RAW_MARKER not in json.dumps(summary)
    assert len(json.dumps(summary).encode("utf-8")) < 2048


def test_default_driver_query_preserves_live_cache_and_durable_ledger(tmp_path, monkeypatch):
    driver, endpoint, before = _make_driver(tmp_path / "state")
    ledger = {"formal_ledger": {"pending_action_id": "unit-intent", "applied": [{"id": "unit-applied", "delta": 17}]}}
    try:
        assert driver.army_query_history_sidecar_limit_bytes == 0
        driver._record_command("unit-required-ledger", ok=True, result=ledger)
        ledger_row = copy.deepcopy(driver._command_history[-1])

        def forbidden_export(*args, **kwargs):
            raise AssertionError("default Driver must not export full Army diagnostics")

        monkeypatch.setattr(history_store, "write_json_exclusive", forbidden_export)
        result = driver.execute_step(QUERY, expected_revision=int(before["revision"]))
        assert result["army_strengths"][0]["regiment_count"] == 3
        assert result["army_strengths_profile"] == ORDINARY_CORE_PROFILE
        assert result["army_observed_phase_coverage"] == "not_requested"
        assert "history_summary_schema" not in result
        assert driver._command_history[-2] == ledger_row
        summary = driver._command_history[-1]["result"]
        assert summary["history_summary_schema"] == history_store.SUMMARY_SCHEMA
        assert summary["army_strengths_profile"] == ORDINARY_CORE_PROFILE
        assert summary["army_observed_phase_coverage"] == "not_requested"
        assert summary["full_result_preserved"] is False
        assert "raw_result_reference" not in summary and "army_strengths" not in summary
        assert not (driver._native_driver_state_path().parent / "army-query-history-results").exists()

        result["army_strengths"][0]["current_soldiers"] = -999
        public = driver.take_snapshot()
        assert public["army_strengths"][0]["current_soldiers"] == 1200
        public["army_strengths"][0]["current_soldiers"] = -888
        assert driver.take_snapshot()["army_strengths"][0]["current_soldiers"] == 1200

        driver._persist_driver_state()
        path = driver._native_driver_state_path()
        stored = json.loads(path.read_text(encoding="utf-8"))
        resumed = load_native_driver_state_for_resume(path, endpoint.pipe_name)
        assert stored["command_history"] == driver._command_history
        assert resumed["command_history"] == driver._command_history
        assert stored["command_history"][-2] == ledger_row
        assert stored["episode_character_id"] == 707
        assert stored["command_history"][-1]["result"] == summary
        assert "raw_result_reference" not in path.read_text(encoding="utf-8")
    finally:
        driver.close()


def test_legacy_reply_is_rejected_without_core_available_history(tmp_path):
    driver, endpoint, before = _make_driver(tmp_path / "state", reply_metadata=False)
    try:
        with pytest.raises(BridgeUnavailableError, match="malformed"):
            driver.execute_step(QUERY, expected_revision=int(before["revision"]))
        row = driver._command_history[-1]
        assert row["command"] == QUERY and row["ok"] is False
        assert "malformed" in row["error"]
        assert "result" not in row
        assert driver._army_strength_query is None
        assert not (driver._native_driver_state_path().parent / "army-query-history-results").exists()
        stored = json.loads(driver._native_driver_state_path().read_text(encoding="utf-8"))
        assert stored["command_history"][-1]["ok"] is False
    finally:
        driver.close()


def test_positive_quota_writes_one_tiny_result_and_restart_counts_it(tmp_path):
    evidence = tmp_path / "explicitly-admitted"
    result = _storage_payload(OBSERVED_HISTORY_FULL_PROFILE)
    summary = history_store.ArmyQueryHistoryStore(evidence, 64 * 1024).record(result)
    reference = summary["raw_result_reference"]
    path = Path(reference["path"])
    assert path.parent == evidence.resolve()
    assert json.loads(path.read_text(encoding="utf-8")) == result
    assert path.stat().st_size == reference["bytes"] < 64 * 1024
    assert summary["full_result_preserved"] is True
    assert reference["wire_bytes_preserved"] is False
    assert summary["army_strengths_profile"] == OBSERVED_HISTORY_FULL_PROFILE
    files = set(evidence.iterdir())
    exhausted = history_store.ArmyQueryHistoryStore(evidence, reference["bytes"]).record(result)
    assert set(evidence.iterdir()) == files
    assert exhausted["accepted"] is True and exhausted["status"] == "available"
    assert exhausted["full_result_preserved"] is False
    assert exhausted["unavailable_reason"] == "sidecar_budget_exhausted"
    assert "raw_result_reference" not in exhausted


def test_real_io_failure_stays_compact_without_reclassifying_native_result(tmp_path):
    obstruction = tmp_path / "not-a-directory"
    obstruction.write_bytes(b"owned synthetic obstruction")
    result = _storage_payload()
    summary = history_store.ArmyQueryHistoryStore(obstruction, 64 * 1024).record(result)
    assert list(tmp_path.iterdir()) == [obstruction]
    assert obstruction.read_bytes() == b"owned synthetic obstruction"
    assert summary["accepted"] is True and summary["status"] == "available"
    assert summary["full_result_preserved"] is False
    assert summary["unavailable_reason"] == "sidecar_io_error"
    assert "raw_result_reference" not in summary
    assert RAW_MARKER not in json.dumps(summary)


def test_re_recording_compact_history_creates_no_new_exports(tmp_path):
    store = history_store.ArmyQueryHistoryStore(tmp_path / "never-created", 0)
    summary = store.record(_storage_payload())
    repeated = store.record(summary)
    assert repeated == summary and repeated is not summary
    repeated["armies"][0]["current_soldiers"] = 0
    assert summary["armies"][0]["current_soldiers"] == 1200
    assert list(tmp_path.iterdir()) == []

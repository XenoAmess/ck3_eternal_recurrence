"""Real ledger IO/process recovery with synthetic Native envelopes; no CK3 access."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import types

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer import environment
from xar_autoplayer import sway_formal_consumer as consumer
from xar_autoplayer.bridge import active_scheme_sway_formal_private_transport as transport
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.version_identity import CK3_12004


class Driver:
    allow_private_active_scheme_sway_action = True

    def __init__(self, path, *, mode="fail_read", full_id=2):
        self.state_dir = Path(path)
        self.mode, self.full_id = mode, full_id
        self.after_epoch = 103
        self.submits = self.receipts = self.reads = 0
        self.sent = []
        self.frame = {
            "snapshot_id": "synthetic:10", "revision": 11, "native_revision": 10,
            "date_raw": 1000, "paused": True, "map_ready": True,
            "episode_run_id": "synthetic-original-episode", "episode_character_id": 7,
            "played_character": {"character_id": 7, "alive": True},
            "active_context": {"active_event": None, "pending_character_interaction": None},
            "diagnostics": {"bridge_pid": 100, "connection_generation": 5,
                "hello": {"expected_ck3_version": CK3_12004.game_version,
                          "expected_ck3_sha256": CK3_12004.executable_sha256}},
        }
        self.endpoint = types.SimpleNamespace(send=self.send)
        self.state = types.SimpleNamespace(wait_for_command_result=self.wait_result)

    def take_snapshot(self):
        return copy.deepcopy(self.frame)

    def readback(self, *, active=False, epoch=100):
        return {
            "schema": "active-scheme-sway-private-read-v1",
            "exact_ck3_build": CK3_12004.game_version,
            "exe_sha256": CK3_12004.executable_sha256,
            "queried_snapshot_id": self.frame["snapshot_id"],
            "queried_revision": self.frame["revision"],
            "queried_native_revision": self.frame["native_revision"],
            "snapshot_revision": self.frame["native_revision"],
            "post_snapshot_id": self.frame["snapshot_id"], "date_raw": self.frame["date_raw"],
            "capture_epoch": epoch, "container_generation": 1,
            "actor_character_id": self.frame["played_character"]["character_id"],
            "target_character_id": 9, "target_opinion_of_actor": -5,
            "active_scheme_count": int(active), "matching_sway_active": active,
            "native_complete_can_send": not active, "native_legal_now": not active,
            "active_sway_instances": ([{
                "scheme_instance_id": self.full_id,
                "scheme_instance_generation": self.full_id >> 24,
                "target_character_id": 9,
            }] if active else []),
        }

    def submit_active_scheme_sway_private_v1(self, *, readback, action_id):
        self.submits += 1
        return {"stage": "submitted_verification_pending", "action_id": action_id,
                "pre_capture_epoch": 101}

    def send(self, request):
        self.sent.append(copy.deepcopy(request))

    def wait_result(self, request_id, timeout):
        request = self.sent[-1]
        self.receipts += 1
        raw = {
            "schema": transport.SCHEMA, "stage": "applied", "action_id": request["action_id"],
            "post_capture_epoch": 102, "post_container_generation": 1, "post_date_raw": 1000,
            "scheme_instance_id": self.full_id, "scheme_instance_generation": self.full_id >> 24,
            "postcondition_verified": True,
        }
        return {"type": "command_result", "protocol_version": 1, "request_id": request_id,
            "ok": True, "result": {"step": request["step"], "accepted": True,
                "status": "applied", "private_build": True, "advertised": False,
                "active_scheme_sway_formal": raw, "backend_id": "native-headless"}}

    def query_active_scheme_sway_receipt_private_v1(self, **arguments):
        return transport.query_active_scheme_sway_receipt_private_v1(self, **arguments)

    def query_active_scheme_sway_target_private_v1(self, **arguments):
        self.reads += 1
        # Observe the actual canonical file before independent postcondition IO.
        saved = consumer.read_sway_ledger(self.state_dir)["pending"]
        assert saved["native_applied_receipt"]["scheme_instance_id"] == self.full_id
        assert transport.RECEIPT_SOURCE_KEY not in saved["native_applied_receipt"]
        if self.mode == "fail_read":
            raise BridgeUnavailableError("synthetic independent read unavailable")
        if self.mode == "exit":
            os._exit(23)
        return self.readback(active=True, epoch=self.after_epoch)


def start(driver):
    return consumer.consume_sway_private_once(
        driver, target_character_id=9, snapshot=driver.take_snapshot(), readback=driver.readback())


def restored(path, *, full_id=2):
    driver = Driver(path, mode="ok", full_id=full_id)
    driver.frame.update(snapshot_id="synthetic-cold:1", revision=2, native_revision=1, date_raw=1024)
    driver.frame["diagnostics"].update(bridge_pid=200, connection_generation=1)
    return driver


def recover(driver, read=None):
    return consumer.consume_sway_private_once(driver, target_character_id=9,
        snapshot=driver.take_snapshot(),
        readback=driver.readback(active=True, epoch=1) if read is None else read)


@pytest.mark.parametrize("full_id", [2, 0x01000002])
def test_receipt_and_source_are_in_real_file_before_independent_read(tmp_path, full_id):
    driver = Driver(tmp_path, full_id=full_id)
    result = start(driver)
    saved = consumer.read_sway_ledger(tmp_path)["pending"]
    assert result["status"] == "postcondition_pending"
    assert saved["native_applied_receipt"] == result["native_receipt"]
    assert saved["native_applied_receipt"]["scheme_instance_generation"] == full_id >> 24
    assert saved["native_receipt_source"]["before"]["bridge_pid"] == 100
    assert (driver.submits, driver.receipts, driver.reads) == (1, 1, 1)


def test_transport_sidecar_uses_only_existing_fields_and_never_native_request(tmp_path):
    driver = Driver(tmp_path)
    driver.frame.pop("episode_run_id")
    driver.frame["diagnostics"].pop("bridge_pid")
    driver.frame["diagnostics"].pop("connection_generation")
    result = driver.query_active_scheme_sway_receipt_private_v1(
        target_character_id=9, action_id="sway-synthetic", expected_revision=10, pre_capture_epoch=100)
    source = result[transport.RECEIPT_SOURCE_KEY]
    assert all("bridge_pid" not in source[name] and "episode_run_id" not in source[name]
               for name in ("before", "after"))
    assert set(driver.sent[0]) == {
        "type", "protocol_version", "request_id", "step", "expected_revision", "action_id"}


def test_new_session_retains_history_and_uses_fresh_exact_identity(tmp_path):
    first = Driver(tmp_path)
    start(first)
    old = consumer.read_sway_ledger(tmp_path)["pending"]
    driver = restored(tmp_path)
    result = recover(driver)
    assert result["status"] == "applied" and result["native_receipt"] is None
    assert result["retained_native_applied_receipt"] == old["native_applied_receipt"]
    assert result["retained_native_receipt_source"] == old["native_receipt_source"]
    source = result["recovered_instance_observation"]["source_read"]
    assert (source["capture_epoch"], source["date_raw"]) == (1, 1024)
    assert result["retained_native_applied_receipt"]["post_date_raw"] == 1000
    assert consumer._resolved_instance_identity(result)["scheme_instance_generation"] == 0
    assert (driver.submits, driver.receipts, driver.reads) == (0, 0, 0)
    assert consumer.read_sway_ledger(tmp_path)["pending"] is None


def test_exact_receipt_selects_its_row_when_target_has_another_instance(tmp_path):
    start(Driver(tmp_path))
    driver = restored(tmp_path)
    read = driver.readback(active=True, epoch=1)
    read["active_sway_instances"].append({"scheme_instance_id": 3,
        "scheme_instance_generation": 0, "target_character_id": 9})
    read["active_scheme_count"] = 2
    result = recover(driver, read)
    assert result["status"] == "applied"
    assert consumer._resolved_instance_identity(result)["scheme_instance_id"] == 2
    assert result["recovered_instance_observation"]["active_instance"]["scheme_instance_id"] == 2


def test_known_original_episode_cannot_recover_same_slot_in_another_episode(tmp_path):
    start(Driver(tmp_path))
    driver = restored(tmp_path)
    driver.frame["episode_run_id"] = "synthetic-other-episode"
    before = (tmp_path / consumer.LEDGER_FILE).read_bytes()
    result = recover(driver)
    assert result["status"] == "pending_recovery" and result["postcondition_verified"] is False
    assert (tmp_path / consumer.LEDGER_FILE).read_bytes() == before
    assert driver.submits == driver.receipts == 0


@pytest.mark.parametrize("change", ["id", "generation", "duplicate", "bool_generation"])
def test_same_target_different_instance_stays_pending_without_resubmit(tmp_path, change):
    start(Driver(tmp_path))
    driver = restored(tmp_path)
    read = driver.readback(active=True, epoch=1)
    row = read["active_sway_instances"][0]
    if change == "id":
        row["scheme_instance_id"] = 3
    elif change == "generation":
        row.update(scheme_instance_id=0x01000002, scheme_instance_generation=1)
    elif change == "bool_generation":
        row["scheme_instance_generation"] = False
    else:
        read["active_sway_instances"].append(dict(row))
    original = (tmp_path / consumer.LEDGER_FILE).read_bytes()
    result = recover(driver, read)
    assert result["status"] == "pending_recovery" and result["postcondition_verified"] is False
    assert (tmp_path / consumer.LEDGER_FILE).read_bytes() == original
    assert (driver.submits, driver.receipts, driver.reads) == (0, 0, 0)


@pytest.mark.parametrize("field,value", [
    ("action_id", "sway-other"), ("actor_character_id", 8), ("target_character_id", 10),
    ("exe_sha256", "0" * 64), ("exact_ck3_build", "1.20.0.3"),
])
def test_retained_original_receipt_identity_drift_cannot_apply(tmp_path, field, value):
    start(Driver(tmp_path))
    ledger = consumer.read_sway_ledger(tmp_path)
    ledger["pending"]["native_applied_receipt"][field] = value
    environment.write_json_atomic(tmp_path / consumer.LEDGER_FILE, ledger)
    result = recover(restored(tmp_path))
    assert result["status"] == "pending_recovery" and result["postcondition_verified"] is False


def test_source_sidecar_replace_failure_keeps_receipt_and_does_not_query(tmp_path, monkeypatch):
    replace = environment.os.replace

    def replace_with_source_failure(source, destination):
        payload = json.loads(Path(source).read_text(encoding="utf-8"))
        if "native_receipt_source" in (payload.get("pending") or {}):
            raise PermissionError("synthetic sidecar replace failure")
        return replace(source, destination)

    monkeypatch.setattr(environment.os, "replace", replace_with_source_failure)
    driver = Driver(tmp_path)
    with pytest.raises(PermissionError):
        start(driver)
    pending = consumer.read_sway_ledger(tmp_path)["pending"]
    assert pending["native_applied_receipt"]["scheme_instance_id"] == 2
    assert "native_receipt_source" not in pending
    assert (driver.submits, driver.receipts, driver.reads) == (1, 1, 0)


@pytest.mark.parametrize("drift", ["bridge_pid", "connection_generation", "episode_run_id", "missing"])
def test_session_drift_before_independent_read_never_compares_old_epochs(tmp_path, drift):
    driver = Driver(tmp_path, mode="ok")
    # Change session at the existing snapshot after receipt, before _read_now.
    snapshots = 0
    snapshot = driver.take_snapshot

    def session_snapshot():
        nonlocal snapshots
        snapshots += 1
        if snapshots == 5:
            driver.after_epoch = 1
            if drift == "missing":
                driver.frame["diagnostics"].pop("bridge_pid")
            elif drift == "episode_run_id":
                driver.frame[drift] = "synthetic-other-episode"
            else:
                driver.frame["diagnostics"][drift] += 1
        return snapshot()

    driver.take_snapshot = session_snapshot
    result = start(driver)
    # Missing/changed binding must not grant the original receipt current credit.
    if drift == "episode_run_id":
        assert result["status"] == "postcondition_pending"
        assert result["postcondition_verified"] is False
        assert consumer.read_sway_ledger(tmp_path)["pending"] is not None
        return
    assert result["status"] == "applied" and result["native_receipt"] is None
    assert result["retained_native_applied_receipt"]["post_capture_epoch"] == 102
    assert result["recovered_instance_observation"]["source_read"]["capture_epoch"] == 1
    assert (driver.submits, driver.receipts, driver.reads) == (1, 1, 1)


def _child(mode, path):
    driver = Driver(path, mode="exit")
    if mode == "write_before_source":
        original = consumer._write

        def write_then_exit(state_dir, ledger):
            original(state_dir, ledger)
            pending = ledger.get("pending") or {}
            if "native_applied_receipt" in pending and "native_receipt_source" not in pending:
                os._exit(24)

        consumer._write = write_then_exit
    if mode.startswith("write"):
        start(driver)
        raise AssertionError("child did not reach exit boundary")
    result = recover(restored(path))
    print(json.dumps(result, sort_keys=True))


@pytest.mark.parametrize("mode,exit_code", [("write", 23), ("write_before_source", 24)])
def test_receipt_survives_process_exit_and_fresh_process_recovery(tmp_path, mode, exit_code):
    command = [sys.executable, "-B", str(Path(__file__).resolve())]
    written = subprocess.run(command + [mode, str(tmp_path)], capture_output=True, text=True, timeout=30)
    assert written.returncode == exit_code, written.stderr
    original = consumer.read_sway_ledger(tmp_path)["pending"]
    assert original["native_applied_receipt"]["scheme_instance_generation"] == 0
    read = subprocess.run(command + ["recover", str(tmp_path)], capture_output=True, text=True, timeout=30)
    assert read.returncode == 0, read.stderr
    result = json.loads(read.stdout)
    assert result["native_receipt"] is None
    assert result["retained_native_applied_receipt"] == original["native_applied_receipt"]
    assert result["recovered_instance_observation"]["source_read"]["capture_epoch"] == 1
    if mode == "write_before_source":
        assert "retained_native_receipt_source" not in result


if __name__ == "__main__":
    _child(sys.argv[1], Path(sys.argv[2]))

"""Saved construction projection; transport envelopes and worker reset are synthetic.

These tests require only the installed SDK package and this adjacent JSON fixture.
They perform no Game/native/desktop calls and use pytest's temporary state directory.
"""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from xar_autoplayer import construction_formal_consumer as consumer
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
from xar_autoplayer.bridge.version_identity import CK3_12004


@pytest.fixture
def construction_observer(tmp_path, monkeypatch):
    fixture = json.loads((Path(__file__).parent / "fixtures" /
                          "construction_material_outside_projection.json").read_text(encoding="utf-8"))

    class Driver:
        state_dir = tmp_path

        def __init__(self):
            self.snapshot = deepcopy(fixture["frame"])
            self.records = []
            self.sends = []

        def take_snapshot(self):
            return deepcopy(self.snapshot)

        def _record_command(self, command, **result):
            self.records.append((command, result))

    driver = Driver()

    def send(unused, step, revision, request_id):
        driver.sends.append((step, revision, request_id))
        assert step == transport.QUERY_NATIVE
        world = deepcopy(fixture["material"]["world"])
        world.update(snapshot_revision=revision, date_raw=driver.snapshot["date_raw"])
        return {"step": step, "accepted": True, "private_probe": {
            "advertised": False, "snapshot_revision": revision,
            "date_raw": driver.snapshot["date_raw"],
            "proof_epoch": fixture["material"]["proof_epoch"],
            "player_world_building_sources": world}}

    monkeypatch.setattr(transport, "_identity", lambda unused: (249712, "20261015230508.297017+480"))
    monkeypatch.setattr(transport, "_send", send)
    monkeypatch.setattr(transport, "private_native_build_identity", lambda unused: CK3_12004)
    monkeypatch.setattr(transport, "private_native_provenance", lambda unused: {})
    monkeypatch.setattr(consumer, "private_native_build_identity", lambda unused: CK3_12004)
    subject = deepcopy(fixture["subject"])
    ledger = {"schema": "xar.ck3.construction_formal_pending_v1", "pending": None,
              "applied": subject, "applied_prior": []}
    consumer.write_construction_ledger(tmp_path, ledger)
    return driver, subject, ledger


def test_unobservable_applied_material_is_retained_and_monthly_watch_does_not_livelock(construction_observer):
    driver, subject, _ = construction_observer
    observation = transport.query_construction_receipt(
        driver, pending=deepcopy(subject), expected_revision=511)
    assert observation["status"] == "unavailable"
    assert observation["accepted"] is False
    assert observation["reason"] == "subject_outside_current_direct_holding_projection"
    assert observation["completion_status"] == "unobserved"
    assert observation["business_submission"] is False
    assert observation["native_submit_calls"] == 0
    assert observation["replay_allowed"] is False
    retained = consumer.read_construction_ledger(driver.state_dir)["applied"]
    preserved = deepcopy(retained)
    unavailable = preserved.pop("material_observation_unavailable_v1")
    assert unavailable["retry_not_before_date_raw"] == driver.snapshot["date_raw"] + 30 * 24
    assert preserved.pop("completion_last_check_date_raw") == driver.snapshot["date_raw"]
    original = deepcopy(subject)
    original.pop("completion_last_check_date_raw")
    assert preserved == original
    assert driver.records[-1][1]["ok"] is False
    assert driver.records[-1][1]["result"]["material_query"]["world"]["directly_held_barony_provinces"] == [
        {"barony_title_id": 2232, "province_id": 2619},
        {"barony_title_id": 2235, "province_id": 2617}]
    for _ in range(2):
        baseline = {"snapshot_id": "native:513", "revision": 511,
                    "plan": {"phase": "ordinary", "selected_step": "life-advance"}}
        following = consumer.plan_construction_private(
            driver, baseline, driver.snapshot, [], {"life-advance"})
        assert following["plan"]["selected_step"] == "life-advance"
        assert following["plan"]["phase"] == "ordinary"
    assert len(driver.sends) == 1
    # Worker counters restart while the Game process and historical material
    # remain the same; the new read-only lease must prevent another cold query.
    driver.snapshot.update(snapshot_id="native:3", native_revision=3, revision=1)
    transport.query_construction_receipt(driver, pending=retained, expected_revision=1)
    ledger = consumer.read_construction_ledger(driver.state_dir)
    assert ledger["applied"]["post_native_revision"] == subject["post_native_revision"]
    assert consumer.priority_construction_receipt(driver, ledger, driver.snapshot) is None
    assert consumer.construction_receipt_readback_scope_v1(ledger["applied"])["native_revision"] == 3
    assert len(driver.sends) == 2


def test_missing_unresolved_submit_keeps_pending_and_raises(construction_observer):
    driver, subject, ledger = construction_observer
    consumer.write_construction_ledger(driver.state_dir, {
        **ledger, "pending": deepcopy(subject), "applied": None})
    with pytest.raises(transport.BridgeUnavailableError, match="keep pending"):
        transport.query_construction_receipt(driver, pending=subject, expected_revision=511)
    assert consumer.read_construction_ledger(driver.state_dir)["pending"] == subject


@pytest.mark.parametrize("field,value", [
    ("business_submission", True), ("native_submit_calls", 1),
    ("action_request_id", "another-action"), ("read_only", False),
])
def test_untrusted_readback_lease_cannot_replace_material_scope(construction_observer, field, value):
    driver, subject, _ = construction_observer
    transport.query_construction_receipt(driver, pending=subject, expected_revision=511)
    retained = consumer.read_construction_ledger(driver.state_dir)["applied"]
    retained["material_observation_unavailable_v1"][field] = value
    scope = consumer.construction_receipt_readback_scope_v1(retained)
    assert scope["native_revision"] == subject["post_native_revision"]
    assert scope["date_raw"] == subject["post_date_raw"]

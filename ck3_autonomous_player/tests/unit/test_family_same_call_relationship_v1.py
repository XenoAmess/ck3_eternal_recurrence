"""Same-call relation reuse through real transport and consumers, with no files."""
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest

from test_family_marriage_formal_consumer import family_reads
from xar_autoplayer import current_first_heir_betrothal_formal_consumer as betrothal
from xar_autoplayer import family_marriage_formal_consumer as family
from xar_autoplayer.bridge import current_first_heir_relationship_private_transport as transport
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.version_identity import CK3_12004


def scene():
    return {"snapshot_id": "fixture:7", "revision": 7, "native_revision": 7,
            "date_raw": 53215920, "episode_run_id": "fixture-episode", "paused": True,
            "map_ready": True, "active_event": None, "pending_character_interaction": None,
            "active_wars": [], "played_character": {"character_id": 101, "alive": True},
            "diagnostics": {"bridge_pid": 55, "connection_generation": 2, "hello": {
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256}}}


class Driver:
    state_dir = Path("synthetic-family-state-not-opened")
    allow_private_current_first_heir_relationship_query = True
    allow_private_current_first_heir_betrothal_fulfillment = True

    def __init__(self):
        self.frame = scene()
        self.calls, self.requests = [], []
        self.reads = 0
        self.endpoint = self.state = self
        self.after_change = None
        self.strip_source = False
        self.legality, self.projection = family_reads()

    def take_internal_semantic_snapshot(self):
        self.reads += 1
        frame = deepcopy(self.frame)
        if self.reads % 3 == 0 and self.after_change is not None:
            self.after_change(frame)
        return frame

    def _execute_campaign_root_context_v1_query(self, *, expected_revision):
        return {"status": "available", "query_sequence": 1,
                "held_title_partition": [{"primary": True, "first_heir_character_id": 202}]}

    def send(self, request):
        assert request["step"] == transport.STEP  # No action is submitted.
        self.requests.append(request)

    def wait_for_command_result(self, request_id, timeout):
        return {"ok": True, "result": {
            "step": transport.STEP, "accepted": True, "private_build": True,
            "read_only": True, "advertised": False, "native_revision": 7,
            "subject_source": "public_campaign_root_primary_first_heir", "status": "available",
            "heir_character_id": 202, "unavailable_reason": None, "bilateral_verified": True,
            "betrothed_character_id": None, "primary_spouse_character_id": None,
            "spouse_character_ids": []}}

    def query_current_first_heir_relationship_private_v1(self, **kwargs):
        self.calls.append("relationship")
        result = transport.query_current_first_heir_relationship_private_v1(self, **kwargs)
        if self.strip_source:
            result.pop("source_frame", None)
        return result

    def query_observed_first_heir_marriage_legality_v1(self, **kwargs):
        self.calls.append("legality")
        return deepcopy(self.legality)

    def query_first_heir_candidate_alliance_projection_private_v1(self, **kwargs):
        self.calls.append("projection")
        assert len(kwargs["candidate_character_ids"]) == 5
        return deepcopy(self.projection)


def run_service(driver):
    owner = GameplayBridgeService(driver)
    empty = {"pending": None, "resolved": None}
    with patch.object(family, "read_family_marriage_ledger", return_value=empty), \
         patch.object(betrothal, "read_family_marriage_ledger", return_value=empty), \
         patch.object(betrothal, "_identity", return_value=(55, "created")), \
         patch.object(owner, "_ordinary_family_cooldown_eligible_v1", return_value=False), \
         patch.object(owner, "_skip_private_family_opportunity_during_cooldown_v1", return_value=None), \
         patch.object(owner, "_plan_private_family_education_v1", side_effect=lambda plan, *a, **k: plan):
        return owner._plan_private_family_opportunity_v1(
            {"snapshot_id": "fixture:7", "revision": 7,
             "plan": {"selected_step": "life-advance"}}, driver.frame)


def test_service_same_call_saves_one_read_without_reducing_five_candidate_policy():
    old, reused = Driver(), Driver()
    old.strip_source = True
    before, after = run_service(old), run_service(reused)
    assert old.calls == ["relationship", "relationship", "legality", "projection"]
    assert reused.calls == ["relationship", "legality", "projection"]
    assert (old.reads, reused.reads) == (6, 3)  # Only the original query bookends.
    for key in ("selected_step", "family_marriage_choice", "family_marriage_valued_choices",
                "family_marriage_legality", "family_marriage_private_diagnostic"):
        assert before["plan"][key] == after["plan"][key]
    assert len(after["plan"]["family_marriage_valued_choices"]) == 5
    assert len(reused.requests) == 1 and len(old.requests) == 2


def test_public_query_publication_retains_both_observed_wrappers():
    driver = Driver()
    driver.after_change = lambda frame: frame.update(snapshot_id="publication:8", revision=8)
    result = run_service(driver)
    source = result["plan"]["family_marriage_current_relationship"]["source_frame"]
    assert source["public_before"] == {"snapshot_id": "fixture:7", "revision": 7}
    assert source["public_after"] == {"snapshot_id": "publication:8", "revision": 8}
    assert source["native_frame"]["native_revision"] == 7
    assert driver.calls == ["relationship", "legality", "projection"]


@pytest.mark.parametrize("field", ["episode", "connection", "pid", "build", "missing", "regress"])
def test_transport_incomplete_or_conflicting_bookends_do_not_offer_reuse(field):
    driver = Driver()
    def change(frame):
        if field == "episode":
            frame["episode_run_id"] = "other"
        elif field == "connection":
            frame["diagnostics"]["connection_generation"] += 1
        elif field == "pid":
            frame["diagnostics"]["bridge_pid"] += 1
        elif field == "build":
            frame["diagnostics"]["hello"]["expected_ck3_sha256"] = "0" * 64
        elif field == "missing":
            frame["diagnostics"].pop("connection_generation")
        else:
            frame["revision"] = 6
    driver.after_change = change
    relation = driver.query_current_first_heir_relationship_private_v1(expected_native_revision=7)
    assert relation["status"] == "available" and "source_frame" not in relation
    assert driver.reads == 3 and len(driver.requests) == 1


@pytest.mark.parametrize("field", ["actor", "episode", "connection", "pid", "native", "date",
                                    "build", "public", "missing", "readonly", "advertised",
                                    "schema", "bilateral", "heir", "unavailable"])
def test_optional_relation_mismatch_falls_back_to_original_query(field):
    driver = Driver()
    relation = driver.query_current_first_heir_relationship_private_v1(expected_native_revision=7)
    native = relation["source_frame"]["native_frame"]
    keys = {"actor": "actor_character_id", "episode": "episode_run_id",
            "connection": "connection_generation", "pid": "bridge_pid",
            "native": "native_revision", "date": "date_raw"}
    if field in keys:
        native[keys[field]] = "different" if field == "episode" else native[keys[field]] + 1
    elif field == "build":
        relation["exe_sha256"] = "0" * 64
    elif field == "public":
        relation["source_frame"]["public_before"]["revision"] += 1
    elif field == "missing":
        relation.pop("source_frame")
    elif field == "readonly":
        relation["read_only"] = False
    elif field == "advertised":
        relation["advertised"] = True
    elif field == "schema":
        relation["schema"] = "other"
    elif field == "bilateral":
        relation["bilateral_verified"] = False
    elif field == "heir":
        relation["heir_character_id"] = True
    else:
        relation["status"] = "unavailable"
    checked = family._current_first_heir_relation(driver, driver.frame, relationship=relation)
    assert checked["heir_character_id"] == 202
    assert driver.calls == ["relationship", "relationship"]


def test_reuse_still_obeys_disabled_query_and_original_legality_identity_check():
    driver = Driver()
    driver.allow_private_current_first_heir_relationship_query = False
    assert family._current_first_heir_relation(driver, driver.frame, relationship={}) is None
    assert driver.calls == []
    driver.allow_private_current_first_heir_relationship_query = True
    driver.legality["observed_first_heir_character_id"] = 999
    with pytest.raises(ValueError, match="current first-heir relation and legal actor differ"):
        run_service(driver)
    assert driver.calls == ["relationship", "legality"]


def test_original_fetched_schema_failure_is_not_swallowed_as_optional_input():
    driver = Driver()
    with patch.object(driver, "query_current_first_heir_relationship_private_v1",
                      return_value={"schema": "bad"}) as query:
        with pytest.raises(ValueError, match="crossed the planning frame"):
            family._current_first_heir_relation(driver, driver.frame)
    query.assert_called_once_with(expected_native_revision=7)


def test_rejected_readonly_fallback_preserves_original_error_without_retry():
    driver = Driver()
    error = BridgeUnavailableError("original readonly rejection")
    with patch.object(driver, "query_current_first_heir_relationship_private_v1",
                      side_effect=error) as query:
        with pytest.raises(BridgeUnavailableError) as caught:
            family._current_first_heir_relation(driver, driver.frame,
                                               relationship={"status": "available"})
    assert caught.value is error
    query.assert_called_once_with(expected_native_revision=7)

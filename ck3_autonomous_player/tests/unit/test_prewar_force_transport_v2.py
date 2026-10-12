"""Real Driver/state/cache integration; only its native endpoint is synthetic."""
from copy import deepcopy
import threading

import pytest

from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.prewar_force_coalition_v2_transport import CAPABILITY, DOMAIN_KEY, STEP
from xar_autoplayer.bridge.version_identity import CK3_12004
from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot
from test_ordinary_prewar_force_admission_v2 import _evidence, SELECTED_FIELDS


def _harness(*, formal=True, bridge_version="0.1.0"):
    template, declaration, _, _ = _evidence()
    template = deepcopy(template)
    template.pop("prewar_force_coalition_coverage_v2_query")
    endpoint = FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
        command_timeout_seconds=.1)
    caps = ["game.state.snapshot", "game.state.declarable-wars",
            "game.command.query-declarable-wars", "game.command.declare-war-N"]
    if formal:
        caps.append(CAPABILITY)
    hello = _hello(*caps)
    hello.update(bridge_version=bridge_version, expected_ck3_version=CK3_12004.game_version,
                 expected_ck3_sha256=CK3_12004.executable_sha256)
    endpoint.publish(hello)
    endpoint.publish(_snapshot(40, played_character=deepcopy(template["played_character"]),
        date_raw=template["date_raw"]))

    def catalogue(request):
        assert request["step"] == "query-declarable-wars"
        endpoint.publish({"type": "command_result", "protocol_version": 1,
            "request_id": request["request_id"], "ok": True, "result": {
                "step": request["step"], "accepted": True, "status": "available",
                "query_sequence": 3, "declarable_wars": [deepcopy(declaration)]}})
    endpoint.send_hook = catalogue
    driver.execute_step("query-declarable-wars", expected_revision=driver.take_snapshot()["revision"])
    before = driver.take_internal_semantic_snapshot()
    rows, sequence = driver._declarable_wars_cache_for_snapshot(before,
        episode_run_id=before.get("episode_run_id"))
    assert sequence == 3 and len(rows) == 1
    declaration = rows[0]
    endpoint.frames.clear()
    endpoint.send_hook = None
    return driver, endpoint, before, declaration, template


def _response(request, before, declaration, *, ticket=13, lower=1500, partial=False):
    # Fixture source fields are independent of the command/domain being checked.
    # Identity and revision come from the actual Driver before frame, never vice versa.
    _, original, raw, _ = _evidence(lower=lower)
    assert {key: original[key] for key in SELECTED_FIELDS} == {
        key: declaration[key] for key in SELECTED_FIELDS}
    assert raw["actor_character_id"] == before["played_character"]["character_id"]
    raw.update(native_revision=before["native_revision"], public_revision=before["revision"],
        date_raw=before["date_raw"], actor_character_id=before["played_character"]["character_id"],
        ticket=ticket, query_sequence=ticket)
    if partial:
        # Contract 279–325/443–467: unknown enemy upper, complete participants.
        raw["owner_forces"][1].update(inventory_upper_soldiers=None, inventory_upper_ready=False,
            unavailable_reasons=["synthetic_enemy_inventory_unavailable"])
        raw.update(status="partial", enemy_upper_soldiers=None, enemy_force_coverage_complete=False,
            missing_required_domains=["enemy_current_inventory_upper"])
    return {"type": "command_result", "protocol_version": 1,
        "request_id": request["request_id"], "ok": True,
        "execution_receipt": {"ticket": ticket, "query_sequence": ticket, "capture_epoch": 17},
        "result": {"step": STEP, "accepted": True, "status": raw["status"],
            "private_build": False, "read_only": True, "advertised": True,
            "domain_key": DOMAIN_KEY, DOMAIN_KEY: raw}}


def _query(driver, before, declaration):
    return driver.query_prewar_force_coalition_coverage_v2(declaration["declaration_id"],
        expected_revision=before["revision"])


def test_formal_one_send_real_wait_uses_matched_top_receipt_without_private_optin():
    driver, endpoint, before, declaration, _ = _harness()
    assert driver.allow_private_prewar_force_coalition_query is False
    def answer(request):
        stray = _response(request, before, declaration, ticket=97)
        stray["request_id"] = "another-request"
        endpoint.publish(stray)
        endpoint.publish(_response(request, before, declaration))
    endpoint.send_hook = answer
    try:
        result = _query(driver, before, declaration)
        assert len(endpoint.frames) == 1
        sent = endpoint.frames[0]
        assert set(sent) == {"type", "protocol_version", "request_id", "step", "expected_revision",
            "expected_public_revision", "declaration_id", "selected_declaration"}
        assert sent["step"] == STEP and sent["expected_revision"] == before["native_revision"]
        assert sent["expected_public_revision"] == before["revision"]
        assert sent["selected_declaration"] == {key: declaration[key] for key in SELECTED_FIELDS}
        assert result["native_request_id"] == sent["request_id"]
        assert result["execution_receipt"] == {"ticket": 13, "query_sequence": 13, "capture_epoch": 17}
        assert result[DOMAIN_KEY]["ticket"] == 13
        assert driver.get_current_prewar_force_coalition_coverage_v2(
            declaration["declaration_id"], before)["native_request_id"] == sent["request_id"]
    finally:
        driver.close()


@pytest.mark.parametrize("corruption", ["receipt_missing", "receipt_bool", "receipt_sequence",
    "receipt_domain_disagrees", "selected_tuple", "wrong_frame"])
def test_wrong_receipt_declaration_or_frame_never_populates_real_cache(corruption):
    driver, endpoint, before, declaration, _ = _harness()
    def answer(request):
        frame = _response(request, before, declaration)
        if corruption == "receipt_missing":
            frame.pop("execution_receipt")
        elif corruption == "receipt_bool":
            frame["execution_receipt"]["ticket"] = True
        elif corruption == "receipt_sequence":
            frame["execution_receipt"]["query_sequence"] += 1
        elif corruption == "receipt_domain_disagrees":
            frame["execution_receipt"].update(ticket=14, query_sequence=14)
        elif corruption == "selected_tuple":
            frame["result"][DOMAIN_KEY]["selected_declaration"]["target_title_ids"] = [92]
        endpoint.publish(frame)
        if corruption == "wrong_frame":
            endpoint.publish(_snapshot(41, played_character=deepcopy(before["played_character"]),
                date_raw=before["date_raw"] + 1))
    endpoint.send_hook = answer
    try:
        with pytest.raises(BridgeUnavailableError):
            _query(driver, before, declaration)
        assert len(endpoint.frames) == 1
        assert driver._prewar_force_coalition_v2_query is None
        assert driver.get_current_prewar_force_coalition_coverage_v2(
            declaration["declaration_id"], driver.take_internal_semantic_snapshot()) is None
    finally:
        driver.close()


def test_real_cache_is_detached_from_caller_getter_and_snapshot_projection():
    driver, endpoint, before, declaration, _ = _harness()
    endpoint.send_hook = lambda request: endpoint.publish(_response(request, before, declaration))
    try:
        result = _query(driver, before, declaration)
        result[DOMAIN_KEY]["owner_forces"][0]["actor_lower_soldiers"] = 99999
        cached = driver.get_current_prewar_force_coalition_coverage_v2(declaration["declaration_id"], before)
        assert cached[DOMAIN_KEY]["owner_forces"][0]["actor_lower_soldiers"] == 1500
        cached["selected_declaration_source"]["target_title_ids"].append(999)
        projected = driver.take_snapshot()["prewar_force_coalition_coverage_v2_query"]
        assert projected["selected_declaration_source"]["target_title_ids"] == [91]
        projected[DOMAIN_KEY]["actor_lower_soldiers"] = 0
        assert driver.get_current_prewar_force_coalition_coverage_v2(
            declaration["declaration_id"], before)[DOMAIN_KEY]["actor_lower_soldiers"] == 1500
        assert len(endpoint.frames) == 1
    finally:
        driver.close()


def test_current_declaration_lease_change_invalidates_real_getter_cache():
    driver, endpoint, before, declaration, _ = _harness()
    endpoint.send_hook = lambda request: endpoint.publish(_response(request, before, declaration))
    try:
        _query(driver, before, declaration)
        with driver._driver_state_lock:
            driver._declaration_query_sequence += 1  # Synthetic catalogue source update only.
        assert driver.get_current_prewar_force_coalition_coverage_v2(declaration["declaration_id"], before) is None
        assert driver._prewar_force_coalition_v2_query is None
    finally:
        driver.close()


@pytest.mark.parametrize("newer_succeeds", [True, False])
def test_actual_concurrent_attempt_cas_rejects_old_late_answer(newer_succeeds):
    driver, endpoint, before, declaration, _ = _harness()
    old_entered, release_old = threading.Event(), threading.Event()
    errors = []
    def answer(request):
        ordinal = len(endpoint.frames)
        if ordinal == 1:
            old_entered.set()
            if not release_old.wait(3):
                raise AssertionError("test failed to release its old endpoint response")
            endpoint.publish(_response(request, before, declaration, ticket=13, lower=1500))
        elif newer_succeeds:
            endpoint.publish(_response(request, before, declaration, ticket=14, lower=2500))
        else:
            endpoint.publish({"type": "command_result", "protocol_version": 1,
                "request_id": request["request_id"], "ok": False, "error": "synthetic newer refusal"})
    endpoint.send_hook = answer
    def old_query():
        try:
            _query(driver, before, declaration)
        except Exception as error:
            errors.append(error)
    thread = threading.Thread(target=old_query, name="unit-old-prewar-v2")
    thread.start()
    try:
        try:
            assert old_entered.wait(1)
            if newer_succeeds:
                assert _query(driver, before, declaration)[DOMAIN_KEY]["actor_lower_soldiers"] == 2500
            else:
                with pytest.raises(BridgeUnavailableError, match="newer refusal"):
                    _query(driver, before, declaration)
        finally:
            release_old.set()
            thread.join(3)
        assert not thread.is_alive()
        assert len(errors) == 1 and isinstance(errors[0], BridgeUnavailableError)
        assert "superseded" in str(errors[0])
        current = driver.get_current_prewar_force_coalition_coverage_v2(declaration["declaration_id"], before)
        if newer_succeeds:
            assert current[DOMAIN_KEY]["actor_lower_soldiers"] == 2500
            assert current["execution_receipt"]["ticket"] == 14
        else:
            assert current is None and driver._prewar_force_coalition_v2_query is None
        assert len(endpoint.frames) == 2
    finally:
        release_old.set()
        driver.close()
        thread.join(3)


def test_no_formal_capability_sends_zero_native_query():
    driver, endpoint, before, declaration, _ = _harness(formal=False)
    try:
        with pytest.raises(UnsupportedStepError):
            _query(driver, before, declaration)
        assert endpoint.frames == [] and driver._prewar_force_coalition_v2_query is None
    finally:
        driver.close()

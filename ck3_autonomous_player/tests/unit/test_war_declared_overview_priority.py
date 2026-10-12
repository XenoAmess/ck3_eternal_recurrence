"""Real ordinary planner and Service popup arbitration, using endpoint-only observations."""
from copy import deepcopy

import pytest

from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_declared_overview_contract import QUERY_STEP, CLOSE_STEP
from xar_autoplayer.strategy import choose_one_life_turn
from test_war_declared_overview_transport import _harness, _reply
from test_prewar_force_transport_v2 import _response, STEP as FORCE_STEP
from test_service_prewar_prefetch_v2 import NativeFacade
from test_native_bridge_driver import _snapshot


class PopupNativeFacade(NativeFacade):
    """Only native endpoint world observations are fixture inputs."""
    def __init__(self, driver, endpoint, before, declaration, template, *, presence="visible", pending=False):
        super().__init__(driver, endpoint, before, declaration, template)
        self.presence, self.pending = presence, pending
        endpoint.send_hook = self.answer

    def answer(self, request):
        if request["step"] in {QUERY_STEP, CLOSE_STEP}:
            self.endpoint.publish(_reply(request, self.before, presence=self.presence,
                operation="query" if request["step"] == QUERY_STEP else "close",
                pending=self.pending and request["step"] == CLOSE_STEP))
        else:
            assert request["step"] == FORCE_STEP
            self.endpoint.publish(_response(request, self.before, self.declaration))

    def query_war_declared_overview_v1(self, *, expected_revision):
        return self.native.query_war_declared_overview_v1(expected_revision=expected_revision)

    def close_war_declared_overview_v1(self, *, expected_revision):
        return self.native.close_war_declared_overview_v1(expected_revision=expected_revision)

    def get_current_war_declared_overview_v1(self, snapshot=None):
        return self.native.get_current_war_declared_overview_v1(snapshot)

    def get_current_war_declared_overview_v1_query_attempt(self, snapshot=None):
        return self.native.get_current_war_declared_overview_v1_query_attempt(snapshot)


def _service(*, presence="visible", pending=False):
    driver, endpoint, before, declaration, template = _harness()
    facade = PopupNativeFacade(driver, endpoint, before, declaration, template,
        presence=presence, pending=pending)
    return GameplayBridgeService(facade), facade, driver, endpoint, before


def test_visible_popup_is_observed_once_and_outranks_ordinary_declaration_prefetch():
    service, facade, driver, endpoint, _ = _service()
    try:
        plan = service.plan_turn()["plan"]
        assert plan["selected_step"] == CLOSE_STEP
        assert plan["policy"] == "ordinary-war-declared-overview-v1"
        assert [request["step"] for request in endpoint.frames] == [QUERY_STEP]
        assert facade.query_calls == []
        again = service.plan_turn()["plan"]
        assert again["selected_step"] == CLOSE_STEP
        assert len(endpoint.frames) == 1
    finally:
        driver.close()


def test_actual_closed_dto_without_native_handled_alias_gets_only_verified_ui_credit():
    service, _, driver, endpoint, _ = _service()
    try:
        result = service.auto_turn()
        assert result["selected_step"] == CLOSE_STEP
        assert result["result"]["dispatch_invoked"] is True
        assert "invoked" not in result["result"]
        assert result["result"]["native_handled"] is False
        assert result["result"]["closure_verified"] is True
        assert result["status"] == "executed" and result["ui_action_credit"] is True
        assert [request["step"] for request in endpoint.frames] == [QUERY_STEP, CLOSE_STEP]
    finally:
        driver.close()


def test_pending_close_is_not_credited_or_resubmitted_by_next_ordinary_turn():
    service, _, driver, endpoint, _ = _service(pending=True)
    try:
        first = service.auto_turn()
        assert first["status"] == "pending" and first["ui_action_credit"] is False
        assert first["result"]["closure_verified"] is False
        second = service.auto_turn()
        assert second["status"] == "blocked"
        assert [request["step"] for request in endpoint.frames] == [QUERY_STEP, CLOSE_STEP, QUERY_STEP]
        assert driver.take_internal_semantic_snapshot()["war_declared_overview_v1_close_pending"] is not None
    finally:
        driver.close()


@pytest.mark.parametrize("presence", ["absent", "hidden"])
def test_independent_clear_query_resumes_full_prewar_planner(presence):
    service, facade, driver, endpoint, _ = _service(presence=presence)
    try:
        plan = service.plan_turn()["plan"]
        assert plan["decision"]["outcome"] == "DECLARE"
        assert plan["selected_step"].startswith("declare-war-")
        assert [request["step"] for request in endpoint.frames] == [QUERY_STEP, FORCE_STEP]
        assert len(facade.query_calls) == 1
    finally:
        driver.close()


@pytest.mark.parametrize("terminal", ["dead", "played_character_changed"])
def test_actual_terminal_frame_outranks_popup_query_and_close(terminal):
    service, facade, driver, endpoint, before = _service()
    try:
        played = deepcopy(before["played_character"])
        if terminal == "dead": played["alive"] = False
        else: played["character_id"] += 1
        endpoint.publish(_snapshot(41, played_character=played, date_raw=before["date_raw"]))
        # The synchronous fake publication is processed by the real state wait.
        current = driver.wait_for_change(before["revision"], timeout_seconds=.5)
        assert current is not None
        snapshot = facade.take_internal_semantic_snapshot()
        assert snapshot["one_life_terminal_reason"] is not None
        capabilities = facade.capabilities()
        plan = choose_one_life_turn(snapshot["history"], snapshot=snapshot,
            action_steps=capabilities["action_steps"], bridge_capabilities=capabilities["bridge_capabilities"])
        assert plan["terminal_reason"] is not None
        assert plan["selected_step"] not in {QUERY_STEP, CLOSE_STEP}
        service_plan = service.plan_turn()["plan"]
        assert service_plan["terminal_reason"] is not None
        assert service_plan["selected_step"] not in {QUERY_STEP, CLOSE_STEP}
        assert endpoint.frames == []
    finally:
        driver.close()

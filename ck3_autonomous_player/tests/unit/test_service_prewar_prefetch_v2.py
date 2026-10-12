"""Service dispatch and real planning; synthetic native facade supplies unit world inputs."""
from copy import deepcopy

import pytest

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.service import GameplayBridgeService
from test_prewar_force_transport_v2 import _harness, _response, DOMAIN_KEY


class NativeFacade:
    """Only the native/world boundary is simulated; coalition Driver remains real."""
    state_dir = None

    def __init__(self, driver, endpoint, before, declaration, template, *, partial=False, timeout=False):
        self.native, self.endpoint = driver, endpoint
        self.before, self.declaration, self.template = before, declaration, template
        self.partial, self.timeout = partial, timeout
        self.query_calls = []
        self.planning_views = 0
        endpoint.send_hook = lambda request: endpoint.publish(_response(request, before, declaration,
            partial=self.partial))

    def capabilities(self):
        value = deepcopy(self.native.capabilities())
        value["action_steps"] = list(dict.fromkeys([*value.get("action_steps", []), "life-advance"]))
        return value

    def take_internal_semantic_snapshot(self):
        actual = self.native.take_internal_semantic_snapshot()
        snapshot = deepcopy(actual)
        snapshot["history"] = [{"index": 1, "command": "save-checkpoint", "ok": True}]
        # These other observed-world domains are native facade fixture inputs.
        # Bind their existing canonical fixture metadata to the actual core frame.
        for key, actor_key in (("war_entry_assessments", "actor_character_id"),
                              ("campaign_root_context", "player_character_id")):
            domain = deepcopy(self.template[key])
            domain.update(snapshot_revision=actual["native_revision"], date_raw=actual["date_raw"])
            domain[actor_key] = actual["played_character"]["character_id"]
            snapshot[key] = domain
        return snapshot

    def take_snapshot(self):
        return self.take_internal_semantic_snapshot()

    def _with_internal_planning_view(self, snapshot, callback):
        self.planning_views += 1
        return self.native._with_internal_planning_view(snapshot, callback)

    def _declarable_wars_cache_for_snapshot(self, snapshot, *, episode_run_id):
        return self.native._declarable_wars_cache_for_snapshot(snapshot, episode_run_id=episode_run_id)

    def query_prewar_force_coalition_coverage_v2(self, declaration_id, *, expected_revision):
        self.query_calls.append((declaration_id, expected_revision))
        if self.timeout:
            raise BridgeUnavailableError("synthetic NativeFacade command_result timed out")
        return self.native.query_prewar_force_coalition_coverage_v2(declaration_id,
            expected_revision=expected_revision)


class TracedService(GameplayBridgeService):
    """Transparent call observer: all production planning and finish bodies run."""
    def __init__(self, driver):
        super().__init__(driver)
        self.query_permissions = []

    def _plan_turn_internal(self, *, allow_prewar_force_query=True):
        self.query_permissions.append(allow_prewar_force_query)
        return super()._plan_turn_internal(allow_prewar_force_query=allow_prewar_force_query)


def _service(*, formal=True, partial=False, timeout=False):
    driver, endpoint, before, declaration, template = _harness(formal=formal, bridge_version="0.1.0.4")
    facade = NativeFacade(driver, endpoint, before, declaration, template, partial=partial, timeout=timeout)
    return TracedService(facade), facade, driver, endpoint, before, declaration


def test_real_ordinary_service_prefetches_once_and_replans_with_query_disabled():
    service, facade, driver, endpoint, before, declaration = _service()
    try:
        result = service.plan_turn()
        assert facade.query_calls == [(declaration["declaration_id"], before["revision"])], result["plan"]
        assert service.query_permissions == [True, False], result["plan"]
        assert facade.planning_views == 2 and len(endpoint.frames) == 1
        assert result["plan"]["prewar_force_query"]["status"] == "available"
        assert result["plan"]["prewar_force_query"]["request_retried"] is False
        assert result["plan"]["decision"]["outcome"] == "DECLARE"
        assert driver.get_current_prewar_force_coalition_coverage_v2(
            declaration["declaration_id"], before)[DOMAIN_KEY]["status"] == "available"
    finally:
        driver.close()


def test_valid_partial_is_cached_but_never_declares_or_retries_same_frame():
    service, facade, driver, endpoint, before, declaration = _service(partial=True)
    try:
        result = service.plan_turn()
        assert service.query_permissions == [True, False]
        assert result["plan"]["prewar_force_query"]["status"] == "partial"
        assert result["plan"]["decision"]["outcome"] == "NO_DECLARE"
        cached = driver.get_current_prewar_force_coalition_coverage_v2(declaration["declaration_id"], before)
        assert cached[DOMAIN_KEY]["missing_required_domains"] == ["enemy_current_inventory_upper"]
        again = service.plan_turn()
        assert again["plan"]["required_prewar_force_coalition_query"] is None
        assert "prewar_force_query" not in again["plan"]
        assert again["plan"]["decision"]["outcome"] == "NO_DECLARE"
        assert len(facade.query_calls) == len(endpoint.frames) == 1
    finally:
        driver.close()


def test_facade_timeout_is_retained_and_same_frame_does_not_resend():
    service, facade, driver, endpoint, before, declaration = _service(timeout=True)
    try:
        result = service.plan_turn()
        assert service.query_permissions == [True]
        assert result["plan"]["prewar_force_query"]["status"] == "unavailable"
        assert "BridgeUnavailableError" in result["plan"]["prewar_force_query"]["reason"]
        assert result["plan"]["prewar_force_query"]["request_retried"] is False
        again = service.plan_turn()
        assert again["plan"]["prewar_force_query"]["same_frame_attempt_repeated"] is False
        assert len(facade.query_calls) == 1 and endpoint.frames == []
        assert driver.get_current_prewar_force_coalition_coverage_v2(declaration["declaration_id"], before) is None
    finally:
        driver.close()


def test_native_without_formal_capability_makes_no_prefetch_request():
    service, facade, driver, endpoint, _, _ = _service(formal=False)
    try:
        result = service.plan_turn()
        assert result["plan"]["prewar_force_query"]["status"] == "unsupported"
        assert facade.query_calls == [] and endpoint.frames == []
        assert service.query_permissions == [True]
    finally:
        driver.close()


def test_actual_missing_catalogue_has_typed_source_unavailable_and_zero_query():
    service, facade, driver, endpoint, before, declaration = _service()
    try:
        # Obtain a real current query intent before withdrawing the bottom source.
        from xar_autoplayer.strategy import choose_one_life_turn
        snapshot = facade.take_internal_semantic_snapshot()
        plan = choose_one_life_turn(snapshot["history"], snapshot=snapshot,
            action_steps=set(facade.capabilities()["action_steps"]))
        assert plan["required_prewar_force_coalition_query"]["declaration_id"] == declaration["declaration_id"], plan
        # Withdraw only synthetic source rows; the real lock/accessor/validator run.
        with driver._driver_state_lock:
            driver._declarable_wars = []
        result = service._finish_prewar_force_coalition_plan_v2({"plan": plan}, snapshot, allow_query=True)
        assert result["plan"]["prewar_force_query"]["status"] == "source_unavailable"
        assert facade.query_calls == [] and endpoint.frames == []
        assert service.query_permissions == []
    finally:
        driver.close()


@pytest.mark.parametrize("change", [{"expected_revision": True}, {"expected_revision": 0}, {"profile": "v1"}])
def test_malformed_prefetch_intent_is_rejected_before_native_query(change):
    service, facade, driver, endpoint, before, declaration = _service()
    try:
        required = {"profile": "v2", "declaration_id": declaration["declaration_id"],
            "expected_revision": before["revision"], **change}
        with pytest.raises(ValueError, match="intent"):
            service._finish_prewar_force_coalition_plan_v2({"plan": {
                "required_prewar_force_coalition_query": required}}, facade.take_snapshot(), allow_query=True)
        assert facade.query_calls == [] and endpoint.frames == []
    finally:
        driver.close()

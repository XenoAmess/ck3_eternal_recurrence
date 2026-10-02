"""Production nonwar consumers share one explicit, current root observation.

The committed Council SDK DTOs supply material fields; revision/endpoint seams
and the current-pair reply are deterministic offline fixtures. No game process,
pipe, SDK, native command or live qualification is used by these tests.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import threading
from types import SimpleNamespace

import pytest

from test_private_council_formal_consumer_v1 import ActualCouncilDriver, plan
from xar_autoplayer.bridge import current_first_heir_relationship_private_transport as relationship_transport
from xar_autoplayer.bridge.campaign_root_context_contract import (
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.succession_transition_contract import freeze_succession_expectation_v1
from xar_autoplayer.private_council_formal_consumer_v1 import (
    LEDGER_FILENAME,
    read_council_ledger,
    read_council_receipt_private,
    submit_council_private,
)


ROOT = Path(__file__).resolve().parents[2]


class _PlanningDriver(ActualCouncilDriver):
    """Real service/consumer/transport functions over retained native material."""

    allow_private_family_marriage_formal_trial = True
    allow_private_current_first_heir_betrothal_fulfillment = True
    allow_private_current_first_heir_relationship_query = True
    query_current_first_heir_relationship_private_v1 = (
        NativeHeadlessGameplayDriver.query_current_first_heir_relationship_private_v1
    )
    _with_internal_planning_view = NativeHeadlessGameplayDriver._with_internal_planning_view

    def __init__(self, state_dir: Path):
        super().__init__(state_dir)
        self.phase = "current"
        self.frame = copy.deepcopy(self.data["current_snapshot"])
        self.frame.update(
            backend_id="native-headless",
            episode_character_id=29829,
            one_life_terminal=False,
            one_life_terminal_reason=None,
            history=[],
        )
        provenance = self.data["current_root"]["campaign_root_context"]["provenance"]
        self.frame["diagnostics"] = {
            "bridge_pid": 4242,
            "connection_generation": 3,
            "hello": {
                "expected_ck3_version": provenance["game_version"],
                "expected_ck3_sha256": provenance["executable_sha256"],
            },
        }
        self._session_bridge_pid = 4242
        self._history_lock = threading.RLock()
        self._command_history = []
        self._rollback_war_failures = []
        self._root_query_sequence = 100
        self.endpoint = self
        self.state = SimpleNamespace(wait_for_command_result=self._relationship_reply)
        self.requests = []
        self.retained_bundles = []
        self.last_root_result = None
        # This native-negative fixture has actual signed cost fields and the
        # 14/14, threshold-16 hold. IDs are rebound only for the Council pair.
        self.pair_value = json.loads(
            (ROOT / "native_bridge/research/fixtures/ck3_12002_current_betrothal_negative.json")
            .read_text(encoding="utf-8-sig")
        )
        self.pair_value.update(
            actor_character_id=29829,
            heir_character_id=38822,
            partner_character_id=38718,
            recipient_character_id=32897,
        )

    def take_internal_semantic_snapshot(self):
        return copy.deepcopy(self.frame)

    def take_snapshot(self):
        return {**self.take_internal_semantic_snapshot(),
                "native_command_history": copy.deepcopy(self._command_history)}

    def capabilities(self):
        return {
            "action_steps": [QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP, "life-advance"],
            "bridge_capabilities": [QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY],
        }

    def _execute_campaign_root_context_v1_query(self, *, expected_revision):
        assert expected_revision == self.frame["revision"]
        self.root_calls += 1
        self._root_query_sequence += 1
        result = copy.deepcopy(self.data["current_root"])
        for key in ("scope", "build", "source", "binding"):
            result.pop(key)
        root = result["campaign_root_context"]
        root.update(snapshot_revision=self.frame["native_revision"],
                    date_raw=self.frame["date_raw"])
        result.update(
            snapshot_revision=self.frame["native_revision"],
            date_raw=self.frame["date_raw"],
            query_sequence=self._root_query_sequence,
            queried_snapshot_id=self.frame["snapshot_id"],
            queried_revision=self.frame["revision"],
            queried_native_revision=self.frame["native_revision"],
        )
        self.last_root_result = copy.deepcopy(result)
        return result

    def execute_step(self, step, *, expected_revision):
        assert step == QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP
        result = self._execute_campaign_root_context_v1_query(expected_revision=expected_revision)
        self._command_history.append({
            "index": len(self._command_history) + 1,
            "command": step,
            "ok": True,
            "result": copy.deepcopy(result),
        })
        return result

    def query_council_final_gates_private_v1(self, *, expected_revision):
        assert expected_revision == self.frame["revision"]
        self.query_calls += 1
        result = copy.deepcopy(self.data["current_query"])
        result["council_composition_candidates"]["snapshot"].update(
            snapshot_id=self.frame["snapshot_id"],
            public_revision=self.frame["revision"],
            native_revision=self.frame["native_revision"],
            date_raw=self.frame["date_raw"],
        )
        return result

    def retain_succession_expectation_v1(self, turn_bundle, *, expected_revision):
        assert turn_bundle["binding"]["revision"] == expected_revision == self.frame["revision"]
        self.frame["succession_expectation"] = freeze_succession_expectation_v1(
            turn_bundle,
            episode_run_id=self.frame["episode_run_id"],
            episode_character_id=self.frame["episode_character_id"],
        )
        self.retained_bundles.append(copy.deepcopy(turn_bundle))

    def reconcile_retained_succession_transition_v1(self, *_args, **_kwargs):
        raise AssertionError("a living fixture ruler must not reconcile succession")

    def send(self, request):
        assert request["step"] == relationship_transport.STEP
        assert request["expected_revision"] == self.frame["native_revision"]
        self.requests.append(copy.deepcopy(request))

    def _relationship_reply(self, request_id, _timeout_seconds):
        assert self.requests[-1]["request_id"] == request_id
        return {"ok": True, "result": {
            "step": relationship_transport.STEP,
            "accepted": True,
            "private_build": True,
            "read_only": True,
            "advertised": False,
            "native_revision": self.frame["native_revision"],
            "subject_source": "public_campaign_root_primary_first_heir",
            "heir_character_id": 38822,
            "status": "available",
            "unavailable_reason": None,
            "bilateral_verified": True,
            "betrothed_character_id": 38718,
            "primary_spouse_character_id": None,
            "spouse_character_ids": [],
            "betrothal_actionability": copy.deepcopy(self.pair_value),
        }}


def _apply_retained_council_assignment(state_dir: Path):
    """Create the ledger through existing consumers, never hand-author applied."""
    state_dir.mkdir()
    driver = ActualCouncilDriver(state_dir)
    planned = plan(driver)
    pending = submit_council_private(driver, plan=planned["plan"],
                                     expected_revision=planned["revision"])
    driver.phase = "post"
    result = read_council_receipt_private(
        driver, pending=pending, expected_revision=driver.take_snapshot()["revision"]
    )
    assert result["status"] == "applied"
    return driver


def test_real_nonwar_chain_reuses_root_and_preserves_material(tmp_path, monkeypatch):
    seed = tmp_path / "seed"
    _apply_retained_council_assignment(seed)
    ledger_bytes = (seed / LEDGER_FILENAME).read_bytes()
    drivers = []
    plans = []
    # Process identity and the driver/endpoint reads use offline fixtures;
    # service, policies, succession freezing, Council and relationship
    # transport execute their production functions.
    monkeypatch.setattr(
        "xar_autoplayer.bridge.domain_construction_private_transport_v1._process_identity",
        lambda _pid: {"creation_date": "fixture-process-4242"},
    )
    for label, reuse in (("baseline", False), ("shared", True)):
        state_dir = tmp_path / label
        state_dir.mkdir()
        (state_dir / LEDGER_FILENAME).write_bytes(ledger_bytes)
        driver = _PlanningDriver(state_dir)
        with monkeypatch.context() as context:
            if not reuse:
                context.setattr(relationship_transport, "_same_frame_campaign_root_result",
                                lambda _result, _snapshot: None)
            observed = GameplayBridgeService(driver).plan_nonwar_turn()
        drivers.append(driver)
        plans.append(observed)

    baseline, shared = drivers
    before, after = plans
    assert (baseline.root_calls, shared.root_calls) == (3, 1)
    # Root sharing must not replace the actual Council final gates or current
    # bilateral relationship/readiness query with a previous observation.
    assert (baseline.query_calls, shared.query_calls) == (1, 1)
    assert (len(baseline.requests), len(shared.requests)) == (1, 1)
    assert (baseline.submit_calls, shared.submit_calls) == (0, 0)
    assert baseline.retained_bundles == shared.retained_bundles
    assert before["plan"]["selected_step"] == after["plan"]["selected_step"] == "life-advance"
    for observed, driver in zip(plans, drivers):
        material = observed["plan"]
        assert material["council_decision"]["outcome"] == "NO_CHANGE"
        consumed = material["council_receipt_consumed"]
        assert consumed["next_turn_consumed"] is True
        assert consumed["next_turn_position"]["incumbent_character_id"] == 33433
        assert consumed["next_turn_position"]["task_key"] == "task_collect_taxes"
        assert material["current_betrothal_choice"]["status"] == "held"
        value = material["current_betrothal_relationship"]["betrothal_actionability"]
        assert (value["heir_adult_measure_raw"], value["partner_adult_measure_raw"]) == (14, 14)
        assert value["generic_costs"]["gold_raw"] == -20000
        assert read_council_ledger(driver.state_dir)["applied"]["next_turn_consumed"] is True

    before = copy.deepcopy(before)
    after = copy.deepcopy(after)
    assert before["plan"]["current_betrothal_relationship"].pop("root_query_sequence") == 103
    assert after["plan"]["current_betrothal_relationship"].pop("root_query_sequence") == 101
    assert before == after


@pytest.mark.parametrize("change", ["revision", "date"])
def test_relationship_discards_supplied_root_after_actual_frame_change(tmp_path, change):
    driver = _PlanningDriver(tmp_path)
    old = driver._execute_campaign_root_context_v1_query(expected_revision=driver.frame["revision"])
    if change == "revision":
        driver.frame["revision"] += 1
        driver.frame["native_revision"] += 1
        driver.frame["snapshot_id"] = f"native:{driver.frame['native_revision']}"
    else:
        driver.frame["date_raw"] += 24
    observed = driver.query_current_first_heir_relationship_private_v1(
        expected_native_revision=driver.frame["native_revision"],
        campaign_root_result=old,
    )
    assert driver.root_calls == 2
    assert len(driver.requests) == 1
    assert observed["root_query_sequence"] == 102
    assert observed["native_revision"] == driver.frame["native_revision"]
    assert driver.last_root_result["date_raw"] == driver.frame["date_raw"]


def test_public_root_and_direct_relationship_defaults_remain_fresh(tmp_path):
    driver = _PlanningDriver(tmp_path)
    service = GameplayBridgeService(driver)
    first = service.query_campaign_root_context_v1(expected_revision=driver.frame["revision"])
    second = service.query_campaign_root_context_v1(expected_revision=driver.frame["revision"])
    assert (first["query_sequence"], second["query_sequence"]) == (101, 102)
    first_pair = driver.query_current_first_heir_relationship_private_v1(
        expected_native_revision=driver.frame["native_revision"])
    second_pair = driver.query_current_first_heir_relationship_private_v1(
        expected_native_revision=driver.frame["native_revision"])
    assert (first_pair["root_query_sequence"], second_pair["root_query_sequence"]) == (103, 104)
    assert driver.root_calls == 4
    assert len(driver.requests) == 2


def test_assignment_receipt_still_observes_independent_post_action_root(tmp_path):
    driver = ActualCouncilDriver(tmp_path)
    planned = plan(driver)
    pending = submit_council_private(driver, plan=planned["plan"],
                                     expected_revision=planned["revision"])
    assert driver.root_calls == 0
    driver.phase = "post"
    result = read_council_receipt_private(
        driver, pending=pending, expected_revision=driver.take_snapshot()["revision"]
    )
    assert result["status"] == "applied"
    assert driver.root_calls == driver.receipt_calls == 1
    assert result["post_native_revision"] == driver.take_snapshot()["native_revision"]
    assert result["independent_position"]["incumbent_character_id"] == 33433
    assert result["independent_position"]["task_key"] == "task_collect_taxes"

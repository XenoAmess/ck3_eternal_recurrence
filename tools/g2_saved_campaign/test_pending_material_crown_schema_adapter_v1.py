"""Portable schema regressions through the complete original Crown consumer.

All game identities in the small DTO fixture are synthetic. The independent
consumer snapshot is test-only; production hosts pass their own original
consumer. These tests start no SDK process and claim no native qualification.
"""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from pending_material_crown_schema_adapter_v1 import (
    classify_pending_material_crown_schema_v1,
)

HERE = Path(__file__).parent
FIXTURE = HERE / "fixtures/crown_pending_material_prototype_v1.json"
CONSUMER = HERE / "fixtures/crown_original_consumer_snapshot_v1.py"
sys.path.insert(0, str(HERE.parents[1] / "ck3_autonomous_player/src"))


def material():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("original_crown_test_consumer", CONSUMER)
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    base = original.classify_governance_with_crown_base_v1
    initial, pid = data["initial_frame"], data["game_pid"]
    submit_credit, state = base(data["submit"], initial_frame=initial, game_pid=pid)
    assert submit_credit["submitted_pending"] is True
    return data, base, state


def hosted(body, base, state, initial, pid):
    result = classify_pending_material_crown_schema_v1(
        body, classify_original=base, state=state,
        initial_frame=initial, game_pid=pid)
    return base(body, state=state, initial_frame=initial, game_pid=pid) if result is None else result


def test_small_fixture_is_deidentified_and_consumer_preserves_its_original_ast():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert FIXTURE.stat().st_size <= 12 * 1024
    assert data["native_packet_synthetic"] is True
    assert data["runtime_qualification"] is False
    assert len(data["provenance"]["input_receipt_sha256"]) == 64
    raw = FIXTURE.read_text(encoding="utf-8")
    for private_identity in ("40695", "51028", "53381376", "e83386ea8e38419a962d3b6dc5231aa1",
                             "D:/", "D:\\", "xenoamess-full-tower"):
        assert private_identity not in raw
    tree = ast.parse(CONSUMER.read_text(encoding="utf-8"))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "classify_governance_with_crown_base_v1")
    expected = next(ast.literal_eval(node.value) for node in tree.body
                    if isinstance(node, ast.Assign)
                    and node.targets[0].id == "ORIGINAL_CONSUMER_AST_SHA256")
    assert hashlib.sha256(ast.dump(function, include_attributes=False).encode()).hexdigest() == expected


def test_missing_discriminator_reproduces_original_failure_then_full_consumer_verifies_material():
    data, base, state = material()
    body, initial, pid = data["receipt"], data["initial_frame"], data["game_pid"]
    original_body, original_state = copy.deepcopy(body), copy.deepcopy(state)
    with pytest.raises(ValueError, match="receipt original ID/target/source/frame mismatch"):
        base(body, state=state, initial_frame=initial, game_pid=pid)
    calls = []

    def complete_original(view, **kwargs):
        calls.append(view)
        assert view["result"] is body["result"]
        assert view["planning_source_frame"] is body["planning_source_frame"]
        assert view["plan"]["crown_pending_action"] is body["plan"]["crown_pending_action"]
        return base(view, **kwargs)

    credit, updated = classify_pending_material_crown_schema_v1(
        body, classify_original=complete_original, state=state,
        initial_frame=initial, game_pid=pid)
    assert len(calls) == 1
    assert calls[0]["plan"]["crown_cold_recovery"] is False
    assert credit["category"] == "crown_material_verified"
    assert credit["crown_material_verified"] is True
    assert credit["effective_law_key"] == "crown_authority_2"
    assert credit["action_request_id"] == "crown-formal-fixture-one"
    assert credit["replay_allowed"] is False
    assert updated["crown_pending"] is None
    provenance = credit["pending_material_crown_schema_adapter"]
    assert provenance["derived_validation_view_only"] is True
    assert provenance["original_plan_or_Native_receipt_changed"] is False
    assert provenance["paired_after_metrics_still_required"] is True
    assert body == original_body and state == original_state
    assert "crown_cold_recovery" not in body["plan"]


@pytest.mark.parametrize("case", [
    "untracked", "action_id", "pending_source", "pending_readback", "pending_budget",
    "receipt_request_id", "receipt_debit", "receipt_effective_law", "receipt_successor",
    "foreign_actor", "observed_native", "cold_recovery_true", "domain", "same_process_false",
])
def test_original_fourteen_guard_cases_reject_without_rewriting_the_receipt(case):
    data, base, state = material()
    body, initial, pid = data["receipt"], data["initial_frame"], data["game_pid"]
    plan, receipt = body["plan"], body["result"]
    if case == "untracked":
        state["crown_pending"] = None
    elif case == "action_id":
        plan["crown_pending_action"]["action_id"] = "crown-formal-foreign"
    elif case == "pending_source":
        plan["crown_pending_action"]["source_context"]["bridge_pid"] += 1
    elif case == "pending_readback":
        plan["crown_pending_action"]["readback"]["date_raw"] -= 24
    elif case == "pending_budget":
        plan["crown_pending_action"]["budgets"]["prestige"] -= 1
    elif case == "receipt_request_id":
        receipt["submitted_request_id"] = "crown-formal-foreign"
    elif case == "receipt_debit":
        receipt["charges"][0]["post_balance_raw"] += 1
    elif case == "receipt_effective_law":
        receipt["effective_law_key"] = "crown_authority_3"
    elif case == "receipt_successor":
        receipt["succession_verified"] = False
    elif case == "foreign_actor":
        body["planning_source_frame"]["actor_character_id"] += 1
    elif case == "observed_native":
        plan["pending_material"]["observed_native_revision"] -= 1
    elif case == "cold_recovery_true":
        plan["crown_cold_recovery"] = True
    elif case == "domain":
        plan["pending_material"]["domain"] = "construction"
    else:
        plan["pending_material"]["same_process"] = False
    before = copy.deepcopy(body)
    with pytest.raises(ValueError):
        hosted(body, base, state, initial, pid)
    assert body == before


@pytest.mark.parametrize("case", ["cold_receipt", "legacy_false", "different_step", "different_policy"])
def test_other_schemas_delegate_without_a_validation_projection_or_callback(case):
    data, _, state = material()
    body, initial, pid = data["receipt"], data["initial_frame"], data["game_pid"]
    if case == "cold_receipt":
        body["plan"]["pending_material"].update(status="cold_receipt", same_process=False)
    elif case == "legacy_false":
        body["plan"]["crown_cold_recovery"] = False
    elif case == "different_step":
        body["selected_step"] = "verify-construction-action-v1-private"
    else:
        body["plan"]["policy"] = "one-life-turn-v1"
    before = copy.deepcopy(body)

    def untouched(*args, **kwargs):
        raise AssertionError("original route belongs to the host; pure helper must decline")

    assert classify_pending_material_crown_schema_v1(
        body, classify_original=untouched, state=state,
        initial_frame=initial, game_pid=pid) is None
    assert body == before


def test_original_consumer_exceptions_propagate_without_credit():
    data, _, state = material()
    marker = ValueError("original complete consumer rejected its native proof")

    def original_reject(*args, **kwargs):
        raise marker

    with pytest.raises(ValueError) as caught:
        classify_pending_material_crown_schema_v1(
            data["receipt"], classify_original=original_reject, state=state,
            initial_frame=data["initial_frame"], game_pid=data["game_pid"])
    assert caught.value is marker


def test_independent_not_enacted_receipt_remains_nonmaterial_and_pending():
    data, base, state = material()
    body = data["receipt"]
    body["result"].update(
        status="failed", failure="effective_law_not_enacted", material_result=False,
        effective_law_key="crown_authority_1", effective_law_verified=False,
        resources_verified=False, succession_verified=False)
    body["result"]["charges"][0]["post_balance_raw"] = (
        body["result"]["charges"][0]["pre_balance_raw"])
    before = copy.deepcopy(state)
    credit, after = hosted(body, base, state, data["initial_frame"], data["game_pid"])
    assert credit["category"] == "crown_independent_not_enacted"
    assert credit["crown_material_verified"] is False
    assert credit["crown_receipt_nonmaterial"] is True
    assert credit["material_verified"] is False
    assert credit["original_action_still_pending"] is True
    assert credit["replay_allowed"] is False
    assert after["crown_pending"] == before["crown_pending"]

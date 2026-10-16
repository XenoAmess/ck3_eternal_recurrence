"""Synthetic Native packet through the production AST selection boundary."""
import ast
import builtins
import copy
import json
from pathlib import Path

import pytest


HERE = Path(__file__).parent
SOURCE = HERE / "war_results_scope_transition_classifier_v1.py"
FIXTURE = HERE / "fixtures/war_results_scope_pending_synthetic.json"


def classifier():
    nodes = [node for node in ast.parse(SOURCE.read_text(encoding="utf-8")).body
             if isinstance(node, ast.FunctionDef) and node.name.startswith("classify_")]
    original = builtins.__import__

    def no_sdk(name, *args, **kwargs):
        if name.startswith("xar_autoplayer"):
            raise AssertionError("queue classifier cannot import the application SDK")
        return original(name, *args, **kwargs)

    namespace = {"__builtins__": dict(vars(builtins), __import__=no_sdk)}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace["classify_war_results_scope_transition_pending_v1"]


def test_returned_callback_pending_has_zero_credit_and_requires_readback():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["native_packet_synthetic"] is True
    body = fixture["body"]
    observed = classifier()(body, initial_frame=body["planning_source_frame"], game_pid=249712)
    assert observed["typed_nonmaterial_observation"] is True
    assert observed["actual_elapsed_days"] == 0
    assert observed["ui_action_credit"] is False
    assert observed["replay_allowed"] is False
    assert observed["paired_after_metrics_still_required"] is True


@pytest.mark.parametrize("change", ["query", "exception", "ticket", "date"])
def test_wrong_operation_or_callback_or_owner_or_date_is_rejected(change):
    body = json.loads(FIXTURE.read_text(encoding="utf-8"))["body"]
    source = copy.deepcopy(body["planning_source_frame"])
    if change == "query":
        body["selected_step"] = "query-war-results-window-v1"
    elif change == "exception":
        body["result"]["dismiss_exception_code"] = 5
    elif change == "ticket":
        body["result"]["native_command_result"]["war_results_window_owner_receipt"]["completed_sequence"] = 999
    else:
        reason = body["result"]["unavailable_reason"]
        body["result"]["unavailable_reason"] = reason.replace(
            "end_date_raw=53339904", "end_date_raw=53339856")
    with pytest.raises(ValueError):
        classifier()(body, initial_frame=source, game_pid=249712)

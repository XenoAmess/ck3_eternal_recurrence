"""One new actual production whole-wire to private cause consumer compound."""

from copy import deepcopy
import json
import os
from pathlib import Path

from xar_autoplayer.bridge.active_scheme_sway_completion_execution_private_transport import normalize_active_scheme_sway_completion_execution_v1
from xar_autoplayer.bridge.active_scheme_sway_completion_termination_private_transport import normalize_active_scheme_sway_completion_termination_v1
from xar_autoplayer.bridge.sway_completion_causal_private_12004 import consume_sway_end_causal_12004


def test_new_native_wholewire_causal_consumer():
    path = os.environ.get("XAR_SWAY_CAUSAL_WHOLEWIRE_PACKET")
    if not path:
        import pytest
        pytest.skip("Root's new native whole-wire packet is required")
    packet = json.loads(Path(path).read_text(encoding="utf-8"))
    execution_envelope = packet["execution"]["result"]
    termination_envelope = packet["termination"]["result"]
    snapshot = {"played_character": {"character_id": 29829}}
    execution = normalize_active_scheme_sway_completion_execution_v1(
        execution_envelope["sway_completion_execution"], snapshot=snapshot,
        target_character_id=31900, scheme_instance_id=0x02000016)
    termination = normalize_active_scheme_sway_completion_termination_v1(
        termination_envelope["sway_completion_termination"], snapshot=snapshot,
        target_character_id=31900, scheme_instance_id=0x02000016)
    for read, envelope in ((execution, execution_envelope), (termination, termination_envelope)):
        read.update({key: envelope[key] for key in ("build_version", "executable_sha256")})
    causal = consume_sway_end_causal_12004(execution_read=execution, termination_read=termination)
    assert causal is not None and causal["cause_key"] == "authored_sway_complete_100_source"
    assert causal["end_original_invocation_id"] == 42 and causal["parent_toast_invocation_id"] == 41
    assert causal["material_effect_observed"] is False
    assert execution["records"][0]["stock_event"] is None
    assert execution["records"][0]["phase_result"] is None
    # These preserve valid independent records while removing only the joined
    # new input. They do not rerun the qualified21/22/27 native source fixtures.
    unmatched = deepcopy(termination)
    unmatched["records"][0]["cause_relation"] = None
    assert consume_sway_end_causal_12004(execution_read=execution, termination_read=unmatched) is None
    assert unmatched["records"][0]["native_terminal_state_observed"] is True
    other_parent = deepcopy(execution)
    other_parent["records"][0]["native_invocation"]["toast_invocation_id"] = 99
    assert consume_sway_end_causal_12004(execution_read=other_parent, termination_read=termination) is None
    reused = deepcopy(termination)
    reused["records"][0]["post_storage_slot_reused"] = True
    assert consume_sway_end_causal_12004(execution_read=execution, termination_read=reused) is None
    no_transition = deepcopy(termination)
    no_transition["records"][0]["native_terminal_transition_observed"] = False
    assert consume_sway_end_causal_12004(execution_read=execution, termination_read=no_transition) is None

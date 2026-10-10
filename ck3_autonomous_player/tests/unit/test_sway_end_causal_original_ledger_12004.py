"""Persist a current causal end under the actual older original Sway receipt.

The ledger is the unmodified saved6076 original. The terminal pair is a
declared synthetic, identity-only projection of a qualified .4 whole-wire
fixture. It is not a live terminal observation for that original instance.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from xar_autoplayer.bridge.sway_completion_causal_private_12004 import (
    consume_sway_end_causal_12004,
)
from xar_autoplayer.sway_end_causal_consumer_12004 import (
    record_sway_end_causal_observation,
)
from xar_autoplayer.sway_formal_consumer import read_sway_ledger


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "sway_causal_original_12004"
LEDGER_NAME = "active-scheme-sway-formal-private-v1.json"


def test_actual_original_sway_ledger_accepts_current_causal_end(tmp_path: Path) -> None:
    ledger_bytes = (FIXTURES / "saved6076-original-ledger.json").read_bytes()
    original = json.loads(ledger_bytes.decode("utf-8-sig"))
    pair = json.loads((FIXTURES / "identity-only-current4-causal-pair.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(ledger_bytes).hexdigest() == pair["original_ledger_sha256"]
    assert pair["native_runtime_observation"] is False
    resolved = original["resolved"]
    receipt = resolved["native_receipt"]
    assert "exact_ck3_build" not in resolved and "exe_sha256" not in resolved
    assert receipt["exact_ck3_build"] == "1.20.0.3"
    execution = pair["execution_read"]
    termination = pair["termination_read"]
    causal = consume_sway_end_causal_12004(
        execution_read=execution, termination_read=termination,
    )
    assert causal is not None
    assert causal["cause_key"] == "authored_sway_complete_100_source"
    assert (causal["actor_character_id"], causal["target_character_id"],
            causal["scheme_instance_id"], causal["scheme_instance_generation"]) == (
                29829, 34333, 134217986, 8)

    def state(name: str) -> Path:
        directory = tmp_path / name
        directory.mkdir()
        (directory / LEDGER_NAME).write_bytes(ledger_bytes)
        return directory

    current_state = state("current-query")
    observation = record_sway_end_causal_observation(
        current_state, execution_read=execution, termination_read=termination,
    )
    assert observation is not None
    assert observation["action_id"] == resolved["action_id"]
    assert observation["exact_ck3_build"] == "1.20.0.4"
    persisted = read_sway_ledger(current_state)
    assert persisted["pending"] == original["pending"]
    assert persisted["resolved"]["native_receipt"] == receipt
    assert persisted["resolved"]["material_intervention"] == resolved["material_intervention"]
    terminal = persisted["resolved"]["terminal_intervention"]
    assert terminal["terminal_cause_observed"] is True
    assert terminal["terminal_cause"] == "authored_sway_complete_100_source"
    assert terminal["next_turn_consumed"] is False
    assert read_sway_ledger(current_state)["resolved"]["end_causal_observation"] == observation

    # Preserve current .4 validation rather than admitting the old .3 origin
    # as the current capture's normalized build/SHA.
    historical_query = deepcopy(termination)
    historical_query.update(
        exact_ck3_build=receipt["exact_ck3_build"], exe_sha256=receipt["exe_sha256"],
    )
    historical_state = state("historical-query-aliases")
    assert record_sway_end_causal_observation(
        historical_state, execution_read=execution, termination_read=historical_query,
    ) is None
    assert (historical_state / LEDGER_NAME).read_bytes() == ledger_bytes

    foreign_state = state("foreign-original-target")
    foreign = deepcopy(original)
    foreign["resolved"]["target_character_id"] += 1
    foreign_path = foreign_state / LEDGER_NAME
    foreign_path.write_text(json.dumps(foreign), encoding="utf-8")
    foreign_bytes = foreign_path.read_bytes()
    assert record_sway_end_causal_observation(
        foreign_state, execution_read=execution, termination_read=termination,
    ) is None
    assert foreign_path.read_bytes() == foreign_bytes

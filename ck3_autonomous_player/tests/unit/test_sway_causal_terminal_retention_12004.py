"""Fresh offline regression for a consumed end surviving an unknown status1 read.

The fresh synthetic source frames pass the real causal writer and following
consumer before retention is tested. They claim no native/game observation.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest

from xar_autoplayer.bridge.version_identity import CK3_12003, CK3_12004
from xar_autoplayer.sway_end_causal_consumer_12004 import (
    record_sway_end_causal_observation,
    retain_sway_end_causal_terminal_12004,
)
from xar_autoplayer.sway_formal_consumer import (
    LEDGER_FILE, SCHEMA, consume_sway_following_turn, read_sway_ledger,
)
from xar_autoplayer.sway_lifecycle_consumer import (
    has_pending_sway_following_turn,
    record_sway_terminal_observation,
)


IDENTITY = {
    "action_id": "offline-m6e-new-retained-end",
    "actor_character_id": 0x05000031,
    "target_character_id": 0x06000041,
    "scheme_instance_id": 0x07000051,
    "scheme_instance_generation": 7,
    "exact_ck3_build": CK3_12004.game_version,
    "exe_sha256": CK3_12004.executable_sha256,
}
CAUSE = "authored_sway_complete_100_source"


def fresh_source_frames() -> tuple[dict[str, object], dict[str, object]]:
    ids = {key: IDENTITY[key] for key in (
        "actor_character_id", "target_character_id", "scheme_instance_id",
        "scheme_instance_generation")}
    common = {
        **ids,
        "available": True, "retention_gap": False,
        "build_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256,
        "exact_ck3_build": CK3_12004.game_version,
        "exe_sha256": CK3_12004.executable_sha256,
        "snapshot_revision": 91, "date_raw": 53290131,
    }
    stamp = {
        "observer_session_identity": 0x100032,
        "owner_thread_id": 73,
        "toast_invocation_id": 102,
        "branch_source_sequence": 91,
        "copied_scopes": {
            name: {"type": kind, "subtype": 0, "reserved": 0, "payload": identity}
            for name, kind, identity in (
                ("root", 4, IDENTITY["actor_character_id"]),
                ("owner", 4, IDENTITY["actor_character_id"]),
                ("target", 4, IDENTITY["target_character_id"]),
                ("scheme", 9, IDENTITY["scheme_instance_id"]),
            )
        },
    }
    execution = {
        **common, "schema": "xar.ck3.sway-completion-execution.v1",
        "records": [{
            **ids, "date_raw": common["date_raw"], "sequence": 91,
            "source_branch": CAUSE, "stock_event": None, "phase_result": None,
            "executing_input_observed": True, "exact_scope_join_ready": True,
            "message_enqueue_observed": False, "material_effect_observed": False,
            "native_terminal_state_observed": False, "native_invocation": stamp,
        }],
    }
    invocation = {
        "observer_session_identity": stamp["observer_session_identity"],
        "owner_thread_id": stamp["owner_thread_id"],
        "original_invocation_id": 103, "original_rva": 0x2D11B30,
        "incoming_return_address_observed": True, "caller_return_rva": 0x2D67C04,
        "original_forwarded_once": True, "original_returned": True,
        "pre_frame_observed": True, "pre_date_raw": common["date_raw"],
        "post_frame_observed": True, "post_date_raw": common["date_raw"],
    }
    relation = {
        **ids,
        "source_contract": "sway_child_end_causal_path_12004_v1",
        "source_contract_version": 1, "relationship_observed": True,
        "observer_session_identity": stamp["observer_session_identity"],
        "owner_thread_id": stamp["owner_thread_id"],
        "branch_source_sequence": stamp["branch_source_sequence"],
        "parent_toast_invocation_id": 102,
        "end_original_invocation_id": invocation["original_invocation_id"],
        "end_original_rva": invocation["original_rva"],
        "native_returns_observed": True, "native_returns_truncated": False,
        "native_return_rvas": [0x2D67C04, 0x3766146, 0x2CC93CC],
    }
    termination = {
        **common, "schema": "xar.ck3.sway-completion-termination.v1",
        "records": [{
            **ids, "date_raw": common["date_raw"], "sequence": 103,
            "source_class": "authored_end_scheme_false_execute", "input_root_scope_kind": 9,
            "pre_status": 0, "post_status": 1,
            "pre_owner": IDENTITY["actor_character_id"], "post_owner": IDENTITY["actor_character_id"],
            "executing_source_observed": True, "post_read_succeeded": True,
            "post_instance_present": True, "post_exact_instance_join_ready": True,
            "post_status_observed": True, "native_terminal_state_observed": True,
            "native_terminal_transition_observed": True, "post_storage_slot_reused": False,
            "native_invocation": invocation, "cause_relation": relation,
        }],
    }
    return execution, termination


def raw_unknown_read() -> dict[str, object]:
    return {
        **{key: value for key, value in IDENTITY.items() if key != "action_id"},
        "schema": "xar.ck3.sway_completion.v1",
        "available": True,
        "snapshot_revision": 901,
        "date_raw": 53290133,
        "instance_source_observed": True,
        "instance_present": True,
        "storage_slot_reused": False,
        "exact_instance_join_ready": True,
        "owner_matches_actor": True,
        "native_owner_raw": IDENTITY["actor_character_id"],
        "native_status_observed": True,
        "native_status_raw": 1,
        "native_status_key": "terminated_unattributed",
        "native_terminal_state_observed": True,
        "terminal_cause_observed": False,
        "terminal_cause": "unknown",
    }


def unknown_observation() -> dict[str, object]:
    native = raw_unknown_read()
    return {
        **IDENTITY,
        "source_native_revision": native["snapshot_revision"],
        "source_date_raw": native["date_raw"],
        "tracked_instance_active": False,
        "instance_terminal_outcome_observed": True,
        "native_status_key": native["native_status_key"],
        "terminal_cause_observed": False,
        "terminal_cause": "unknown",
        "native_observation": native,
        "next_turn_consumed": False,
    }


def set_current_identity(observation: dict[str, object], key: str, value: object) -> None:
    observation[key] = value
    if key != "action_id":
        observation["native_observation"][key] = value


class SwayCausalTerminalRetention12004Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._fixture_temp = tempfile.TemporaryDirectory(
            prefix="m6e-fresh-source-", dir=os.environ.get("XAR_M6E_TEMP_ROOT"))
        cls.addClassCleanup(cls._fixture_temp.cleanup)
        state = Path(cls._fixture_temp.name)
        ledger = {
            "schema": SCHEMA, "pending": None,
            "resolved": {
                **{key: value for key, value in IDENTITY.items()
                   if key not in ("scheme_instance_id", "scheme_instance_generation")},
                "postcondition_verified": True, "next_turn_consumed": False,
                "post_native_revision": 90, "post_date_raw": 53290130,
                "native_receipt": {
                    "scheme_instance_id": IDENTITY["scheme_instance_id"],
                    "scheme_instance_generation": IDENTITY["scheme_instance_generation"],
                },
            },
        }
        (state / LEDGER_FILE).write_text(json.dumps(ledger), encoding="utf-8")
        execution, termination = fresh_source_frames()
        proof = record_sway_end_causal_observation(
            state, execution_read=execution, termination_read=termination)
        if proof is None:
            raise AssertionError("fresh source frames failed the real causal writer")
        snapshot = {
            "paused": True, "map_ready": True,
            "played_character_id": IDENTITY["actor_character_id"],
            "played_character_alive": True,
            "revision": 801, "native_revision": 802, "date_raw": 53290132,
        }
        followed = consume_sway_following_turn(state, snapshot)
        if followed is None or followed["terminal_intervention"]["next_turn_consumed"] is not True:
            raise AssertionError("fresh proved terminal failed the real following-turn consumer")
        cls.admitted_ledger = read_sway_ledger(state)
        cls.retained = deepcopy(cls.admitted_ledger["resolved"]["terminal_intervention"])
        if cls.retained["causal_observation"] != proof:
            raise AssertionError("the real following consumer changed causal proof")

    def previous(self):
        return deepcopy(self.retained)

    def test_exact_same_instance_retains_consumption_following_and_entire_history(self):
        previous = self.previous()
        current = unknown_observation()
        before_previous, before_current = deepcopy(previous), deepcopy(current)

        result = retain_sway_end_causal_terminal_12004(previous, current)

        self.assertEqual(result, before_previous)
        self.assertIsNot(result, previous)
        self.assertEqual(previous, before_previous)
        self.assertEqual(current, before_current)
        self.assertTrue(result["next_turn_consumed"])
        self.assertEqual(result["following_native_revision"], 802)
        self.assertEqual(result["following_date_raw"], 53290132)
        self.assertEqual(result["causal_observation"], previous["causal_observation"])
        self.assertFalse(current["terminal_cause_observed"])
        self.assertEqual(current["terminal_cause"], "unknown")

    def test_actual_cold_ledger_hook_keeps_latest_raw_unknown_and_does_not_rearm(self):
        previous = self.previous()
        ledger = deepcopy(self.admitted_ledger)
        with tempfile.TemporaryDirectory(
                prefix="m6e-cause-retention-", dir=os.environ.get("XAR_M6E_TEMP_ROOT")) as directory:
            state = Path(directory)
            (state / LEDGER_FILE).write_text(json.dumps(ledger), encoding="utf-8")
            for step in range(2):
                native = raw_unknown_read()
                native["snapshot_revision"] += step
                native["date_raw"] += step
                raw_before = deepcopy(native)
                returned = record_sway_terminal_observation(state, completion_read=native)
                saved = read_sway_ledger(state)["resolved"]

                self.assertEqual(native, raw_before)
                self.assertIsNotNone(returned)
                self.assertFalse(returned["terminal_cause_observed"])
                self.assertEqual(returned["terminal_cause"], "unknown")
                self.assertEqual(saved["latest_instance_observation"], returned)
                self.assertEqual(saved["latest_instance_observation"]["native_observation"], raw_before)
                self.assertEqual(saved["terminal_intervention"], previous)
                self.assertEqual(saved["end_causal_observation"], previous["causal_observation"])
                self.assertFalse(has_pending_sway_following_turn(state))

    def test_current_purged_owner_sentinel_does_not_replace_the_same_retained_end(self):
        current = unknown_observation()
        current["native_observation"]["native_owner_raw"] = 0xFFFFFFFF
        current["native_observation"]["owner_matches_actor"] = False
        previous = self.previous()
        self.assertEqual(retain_sway_end_causal_terminal_12004(previous, current), previous)
        self.assertFalse(current["terminal_cause_observed"])

    def test_another_action_identity_build_or_reused_slot_gets_no_historical_attribution(self):
        mutations = {
            "new_action": lambda row: set_current_identity(row, "action_id", "offline-other-action"),
            "new_full_instance_same_slot": lambda row: set_current_identity(
                row, "scheme_instance_id", IDENTITY["scheme_instance_id"] + 0x01000000),
            "generation_changed": lambda row: set_current_identity(row, "scheme_instance_generation", 8),
            "actor_changed": lambda row: set_current_identity(row, "actor_character_id", 0x08000031),
            "target_changed": lambda row: set_current_identity(row, "target_character_id", 0x09000041),
            "wrong_build_pair": lambda row: (
                set_current_identity(row, "exact_ck3_build", CK3_12003.game_version),
                set_current_identity(row, "exe_sha256", CK3_12003.executable_sha256)),
            "wrong_sha_same_build": lambda row: set_current_identity(row, "exe_sha256", "0" * 64),
            "reused_slot": lambda row: row["native_observation"].update(storage_slot_reused=True),
            "absent_instance": lambda row: row["native_observation"].update(instance_present=False),
            "join_not_ready": lambda row: row["native_observation"].update(exact_instance_join_ready=False),
            "other_full_owner": lambda row: row["native_observation"].update(native_owner_raw=0x0A000031),
            "bool_instead_of_status": lambda row: row["native_observation"].update(native_status_raw=True),
        }
        for name, mutate in mutations.items():
            with self.subTest(case=name):
                previous, current = self.previous(), unknown_observation()
                mutate(current)
                before_previous, before_current = deepcopy(previous), deepcopy(current)
                result = retain_sway_end_causal_terminal_12004(previous, current)
                self.assertEqual(result, before_current)
                self.assertEqual(previous, before_previous)
                self.assertEqual(current, before_current)
                self.assertFalse(result["terminal_cause_observed"])
                self.assertEqual(result["terminal_cause"], "unknown")
                self.assertNotIn("causal_observation", result)

    def test_an_unproved_or_different_historical_cause_is_not_reused(self):
        for name in ("absent_proof", "different_actor_in_proof", "unobserved_transition"):
            with self.subTest(case=name):
                previous, current = self.previous(), unknown_observation()
                if name == "absent_proof":
                    previous.pop("causal_observation")
                elif name == "different_actor_in_proof":
                    previous["causal_observation"]["actor_character_id"] += 0x01000000
                else:
                    previous["causal_observation"]["native_terminal_transition_observed"] = False
                self.assertEqual(retain_sway_end_causal_terminal_12004(previous, current), current)


if __name__ == "__main__":
    unittest.main()

"""One configured Chancellor lifecycle with preserved actual Robert pre-inputs.

The internal snapshot and complete final-gates structuredContent below are
unchanged extracts from robert-v19-412-actual-01 (runtime source 41291bf2).
Only the default Steward-unavailable stub, ACK and future observations are
synthetic. This offline case never contacts the game, pipe or UI.
"""
from __future__ import annotations

import copy
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.council_assign_councillor_action_contract import (
    build_assign_councillor_request_v1,
)
from xar_autoplayer.bridge.council_composition_candidates_contract import (
    CHANCELLOR_POSITION_KEY, STEWARD_POSITION_KEY,
)
from xar_autoplayer.private_council_formal_consumer_v1 import (
    RECEIPT_STEP, SUBMIT_STEP, plan_council_private, read_council_ledger,
    read_council_receipt_private, select_council_candidate_v1,
    submit_council_private,
)

ACTUAL_INPUT_SHA256 = {'001-ck3_take_snapshot.json': 'aaf1054dcc09a51fe492e620d9ad8700e60f7444640f8136ef21e9b262d66f30',
 '002-ck3_query_campaign_root_context_v1.json': '8fe586ac1af4131295498ae3074c4268d99a4fa3489eb7cb99ee9090f2911a08',
 '004-ck3_query_council_final_gates_private_v1.json': 'a17e0c07d004cd60c0aaeaa1f57e888557ec186b91024305364b06d068f21713'}

ACTUAL_PRE_SNAPSHOT = {'snapshot_id': 'native:16',
 'revision': 2,
 'native_revision': 16,
 'date_raw': 53220624,
 'paused': True,
 'map_ready': True,
 'episode_run_id': 'native-29829-2bc2d599f7f9',
 'episode_character_id': 29829,
 'episode_identity_pending': False,
 'campaign_goal': {'format_version': 1,
                   'goal_key': 'dynasty_continuity',
                   'campaign_id': 'native-29829-2bc2d599f7f9',
                   'origin_character_id': 29829,
                   'current_character_id': 29829,
                   'progress': {'reconciled_successions': 0, 'last_succession': None}},
 'succession_lifecycle': {'schema': 'xar.ck3.succession-lifecycle-binding/v1',
                          'lifecycle': 'ordinary_campaign_succession',
                          'xar_enabled': 'xar_off',
                          'pact_contract': 'absent_by_fresh_campaign_xar_off_contract',
                          'source': 'prepared-environment-manifest',
                          'environment_sha256': 'd18d2e1f8d60cf6fdd8e505890493464863c4603d448b895b1b5641fb56f069f'},
 'active_event': None,
 'pending_character_interaction': None,
 'played_character': {'character_id': 29829, 'alive': True}}

ACTUAL_PRE_QUERY = {'schema': 'xar.ck3.council-application-main/v1',
 'step': 'private-query-council-final-gates-v1',
 'accepted': True,
 'status': 'available',
 'query_sequence': 29,
 'snapshot_revision': 16,
 'private': True,
 'advertised': False,
 'native_helper_invocations_delta': 0,
 'council_final_gates': {'schema': 'xar.ck3.private.council-final-gates/v1',
                         'status': 'available',
                         'unavailable_reason': 'none',
                         'candidate_count': 14,
                         'rows': [{'character_id': 30784,
                                   'native_collection_ordinal': 0,
                                   'final_gate_available': True,
                                   'candidate_already_councillor': False,
                                   'candidate_is_guest': False,
                                   'pending_character_interaction': False,
                                   'incumbent_fireability_evaluated': True,
                                   'incumbent_can_be_fired': True},
                                  {'character_id': 32023,
                                   'native_collection_ordinal': 1,
                                   'final_gate_available': True,
                                   'candidate_already_councillor': False,
                                   'candidate_is_guest': False,
                                   'pending_character_interaction': False,
                                   'incumbent_fireability_evaluated': True,
                                   'incumbent_can_be_fired': True},
                                  {'character_id': 32440,
                                   'native_collection_ordinal': 8,
                                   'final_gate_available': True,
                                   'candidate_already_councillor': False,
                                   'candidate_is_guest': False,
                                   'pending_character_interaction': False,
                                   'incumbent_fireability_evaluated': True,
                                   'incumbent_can_be_fired': True},
                                  {'character_id': 32716,
                                   'native_collection_ordinal': 7,
                                   'final_gate_available': True,
                                   'candidate_already_councillor': False,
                                   'candidate_is_guest': False,
                                   'pending_character_interaction': False,
                                   'incumbent_fireability_evaluated': True,
                                   'incumbent_can_be_fired': True},
                                  {'character_id': 33435,
                                   'native_collection_ordinal': 5,
                                   'final_gate_available': True,
                                   'candidate_already_councillor': True,
                                   'candidate_is_guest': False,
                                   'pending_character_interaction': False,
                                   'incumbent_fireability_evaluated': True,
                                   'incumbent_can_be_fired': True},
                                  {'character_id': 33437,
                                   'native_collection_ordinal': 2,
                                   'final_gate_available': True,
                                   'candidate_already_councillor': False,
                                   'candidate_is_guest': False,
                                   'pending_character_interaction': False,
                                   'incumbent_fireability_evaluated': True,
                                   'incumbent_can_be_fired': True},
                                  {'character_id': 34333,
                                   'native_collection_ordinal': 6,
                                   'final_gate_available': True,
                                   'candidate_already_councillor': True,
                                   'candidate_is_guest': False,
                                   'pending_character_interaction': False,
                                   'incumbent_fireability_evaluated': True,
                                   'incumbent_can_be_fired': True},
                                  {'character_id': 35637,
                                   'native_collection_ordinal': 3,
                                   'final_gate_available': True,
                                   'candidate_already_councillor': False,
                                   'candidate_is_guest': False,
                                   'pending_character_interaction': False,
                                   'incumbent_fireability_evaluated': True,
                                   'incumbent_can_be_fired': True},
                                  {'character_id': 36077,
                                   'native_collection_ordinal': 4,
                                   'final_gate_available': True,
                                   'candidate_already_councillor': False,
                                   'candidate_is_guest': False,
                                   'pending_character_interaction': False,
                                   'incumbent_fireability_evaluated': True,
                                   'incumbent_can_be_fired': True},
                                  {'character_id': 43696,
                                   'native_collection_ordinal': 12,
                                   'final_gate_available': True,
                                   'candidate_already_councillor': False,
                                   'candidate_is_guest': False,
                                   'pending_character_interaction': False,
                                   'incumbent_fireability_evaluated': True,
                                   'incumbent_can_be_fired': True},
                                  {'character_id': 43699,
                                   'native_collection_ordinal': 13,
                                   'final_gate_available': True,
                                   'candidate_already_councillor': False,
                                   'candidate_is_guest': False,
                                   'pending_character_interaction': False,
                                   'incumbent_fireability_evaluated': True,
                                   'incumbent_can_be_fired': True},
                                  {'character_id': 43700,
                                   'native_collection_ordinal': 11,
                                   'final_gate_available': True,
                                   'candidate_already_councillor': False,
                                   'candidate_is_guest': False,
                                   'pending_character_interaction': False,
                                   'incumbent_fireability_evaluated': True,
                                   'incumbent_can_be_fired': True},
                                  {'character_id': 43706,
                                   'native_collection_ordinal': 9,
                                   'final_gate_available': True,
                                   'candidate_already_councillor': True,
                                   'candidate_is_guest': False,
                                   'pending_character_interaction': False,
                                   'incumbent_fireability_evaluated': True,
                                   'incumbent_can_be_fired': True},
                                  {'character_id': 43712,
                                   'native_collection_ordinal': 10,
                                   'final_gate_available': True,
                                   'candidate_already_councillor': False,
                                   'candidate_is_guest': False,
                                   'pending_character_interaction': False,
                                   'incumbent_fireability_evaluated': True,
                                   'incumbent_can_be_fired': True}],
                         'council_composition_candidates': {'snapshot': {'snapshot_id': 'native:16',
                                                                         'public_revision': 16,
                                                                         'native_revision': 16,
                                                                         'date_raw': 53220624,
                                                                         'paused': True},
                                                            'owner_character_id': 29829,
                                                            'position': {'position_key': 'councillor_chancellor',
                                                                         'incumbent_character_id': 34867,
                                                                         'incumbent_main_skill': {'key': 'diplomacy',
                                                                                                  'value': 7},
                                                                         'vacant': False,
                                                                         'action_route': 'replace'},
                                                            'candidate_collection_complete': True,
                                                            'candidates': [{'character_id': 30784,
                                                                            'native_collection_ordinal': 0,
                                                                            'eligible': True,
                                                                            'eligibility_reason': 'native_candidate_provider_accepted',
                                                                            'main_skill': {'key': 'diplomacy',
                                                                                           'value': 7},
                                                                            'action_route': 'replace'},
                                                                           {'character_id': 32023,
                                                                            'native_collection_ordinal': 1,
                                                                            'eligible': True,
                                                                            'eligibility_reason': 'native_candidate_provider_accepted',
                                                                            'main_skill': {'key': 'diplomacy',
                                                                                           'value': 6},
                                                                            'action_route': 'replace'},
                                                                           {'character_id': 32440,
                                                                            'native_collection_ordinal': 8,
                                                                            'eligible': True,
                                                                            'eligibility_reason': 'native_candidate_provider_accepted',
                                                                            'main_skill': {'key': 'diplomacy',
                                                                                           'value': 4},
                                                                            'action_route': 'replace'},
                                                                           {'character_id': 32716,
                                                                            'native_collection_ordinal': 7,
                                                                            'eligible': True,
                                                                            'eligibility_reason': 'native_candidate_provider_accepted',
                                                                            'main_skill': {'key': 'diplomacy',
                                                                                           'value': 9},
                                                                            'action_route': 'replace'},
                                                                           {'character_id': 33435,
                                                                            'native_collection_ordinal': 5,
                                                                            'eligible': True,
                                                                            'eligibility_reason': 'native_candidate_provider_accepted',
                                                                            'main_skill': {'key': 'diplomacy',
                                                                                           'value': 8},
                                                                            'action_route': 'replace'},
                                                                           {'character_id': 33437,
                                                                            'native_collection_ordinal': 2,
                                                                            'eligible': True,
                                                                            'eligibility_reason': 'native_candidate_provider_accepted',
                                                                            'main_skill': {'key': 'diplomacy',
                                                                                           'value': 6},
                                                                            'action_route': 'replace'},
                                                                           {'character_id': 34333,
                                                                            'native_collection_ordinal': 6,
                                                                            'eligible': True,
                                                                            'eligibility_reason': 'native_candidate_provider_accepted',
                                                                            'main_skill': {'key': 'diplomacy',
                                                                                           'value': 5},
                                                                            'action_route': 'replace'},
                                                                           {'character_id': 35637,
                                                                            'native_collection_ordinal': 3,
                                                                            'eligible': True,
                                                                            'eligibility_reason': 'native_candidate_provider_accepted',
                                                                            'main_skill': {'key': 'diplomacy',
                                                                                           'value': 3},
                                                                            'action_route': 'replace'},
                                                                           {'character_id': 36077,
                                                                            'native_collection_ordinal': 4,
                                                                            'eligible': True,
                                                                            'eligibility_reason': 'native_candidate_provider_accepted',
                                                                            'main_skill': {'key': 'diplomacy',
                                                                                           'value': 7},
                                                                            'action_route': 'replace'},
                                                                           {'character_id': 43696,
                                                                            'native_collection_ordinal': 12,
                                                                            'eligible': True,
                                                                            'eligibility_reason': 'native_candidate_provider_accepted',
                                                                            'main_skill': {'key': 'diplomacy',
                                                                                           'value': 13},
                                                                            'action_route': 'replace'},
                                                                           {'character_id': 43699,
                                                                            'native_collection_ordinal': 13,
                                                                            'eligible': True,
                                                                            'eligibility_reason': 'native_candidate_provider_accepted',
                                                                            'main_skill': {'key': 'diplomacy',
                                                                                           'value': 1},
                                                                            'action_route': 'replace'},
                                                                           {'character_id': 43700,
                                                                            'native_collection_ordinal': 11,
                                                                            'eligible': True,
                                                                            'eligibility_reason': 'native_candidate_provider_accepted',
                                                                            'main_skill': {'key': 'diplomacy',
                                                                                           'value': 7},
                                                                            'action_route': 'replace'},
                                                                           {'character_id': 43706,
                                                                            'native_collection_ordinal': 9,
                                                                            'eligible': True,
                                                                            'eligibility_reason': 'native_candidate_provider_accepted',
                                                                            'main_skill': {'key': 'diplomacy',
                                                                                           'value': 8},
                                                                            'action_route': 'replace'},
                                                                           {'character_id': 43712,
                                                                            'native_collection_ordinal': 10,
                                                                            'eligible': True,
                                                                            'eligibility_reason': 'native_candidate_provider_accepted',
                                                                            'main_skill': {'key': 'diplomacy',
                                                                                           'value': 8},
                                                                            'action_route': 'replace'}],
                                                            'readiness': {'identity_ready': True,
                                                                          'candidate_collection_ready': True,
                                                                          'incumbent_ready': True,
                                                                          'incumbent_main_skill_ready': True,
                                                                          'candidate_legality_ready': True,
                                                                          'main_skill_ready': True,
                                                                          'action_route_ready': True,
                                                                          'same_frame_ready': True,
                                                                          'ready': True}}},
 'backend_id': 'native-headless',
 'native_step': 'private-query-council-final-gates-v1',
 'private_build': True,
 'read_only': True,
 'exact_build': {'game_version': '1.20.0.3',
                 'executable_sha256': '94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6'},
 'council_composition_candidates': {'snapshot': {'snapshot_id': 'native:16',
                                                 'public_revision': 16,
                                                 'native_revision': 16,
                                                 'date_raw': 53220624,
                                                 'paused': True},
                                    'owner_character_id': 29829,
                                    'position': {'position_key': 'councillor_chancellor',
                                                 'incumbent_character_id': 34867,
                                                 'incumbent_main_skill': {'key': 'diplomacy',
                                                                          'value': 7},
                                                 'vacant': False,
                                                 'action_route': 'replace'},
                                    'candidate_collection_complete': True,
                                    'candidates': [{'character_id': 30784,
                                                    'native_collection_ordinal': 0,
                                                    'eligible': True,
                                                    'eligibility_reason': 'native_candidate_provider_accepted',
                                                    'main_skill': {'key': 'diplomacy', 'value': 7},
                                                    'action_route': 'replace'},
                                                   {'character_id': 32023,
                                                    'native_collection_ordinal': 1,
                                                    'eligible': True,
                                                    'eligibility_reason': 'native_candidate_provider_accepted',
                                                    'main_skill': {'key': 'diplomacy', 'value': 6},
                                                    'action_route': 'replace'},
                                                   {'character_id': 32440,
                                                    'native_collection_ordinal': 8,
                                                    'eligible': True,
                                                    'eligibility_reason': 'native_candidate_provider_accepted',
                                                    'main_skill': {'key': 'diplomacy', 'value': 4},
                                                    'action_route': 'replace'},
                                                   {'character_id': 32716,
                                                    'native_collection_ordinal': 7,
                                                    'eligible': True,
                                                    'eligibility_reason': 'native_candidate_provider_accepted',
                                                    'main_skill': {'key': 'diplomacy', 'value': 9},
                                                    'action_route': 'replace'},
                                                   {'character_id': 33435,
                                                    'native_collection_ordinal': 5,
                                                    'eligible': True,
                                                    'eligibility_reason': 'native_candidate_provider_accepted',
                                                    'main_skill': {'key': 'diplomacy', 'value': 8},
                                                    'action_route': 'replace'},
                                                   {'character_id': 33437,
                                                    'native_collection_ordinal': 2,
                                                    'eligible': True,
                                                    'eligibility_reason': 'native_candidate_provider_accepted',
                                                    'main_skill': {'key': 'diplomacy', 'value': 6},
                                                    'action_route': 'replace'},
                                                   {'character_id': 34333,
                                                    'native_collection_ordinal': 6,
                                                    'eligible': True,
                                                    'eligibility_reason': 'native_candidate_provider_accepted',
                                                    'main_skill': {'key': 'diplomacy', 'value': 5},
                                                    'action_route': 'replace'},
                                                   {'character_id': 35637,
                                                    'native_collection_ordinal': 3,
                                                    'eligible': True,
                                                    'eligibility_reason': 'native_candidate_provider_accepted',
                                                    'main_skill': {'key': 'diplomacy', 'value': 3},
                                                    'action_route': 'replace'},
                                                   {'character_id': 36077,
                                                    'native_collection_ordinal': 4,
                                                    'eligible': True,
                                                    'eligibility_reason': 'native_candidate_provider_accepted',
                                                    'main_skill': {'key': 'diplomacy', 'value': 7},
                                                    'action_route': 'replace'},
                                                   {'character_id': 43696,
                                                    'native_collection_ordinal': 12,
                                                    'eligible': True,
                                                    'eligibility_reason': 'native_candidate_provider_accepted',
                                                    'main_skill': {'key': 'diplomacy', 'value': 13},
                                                    'action_route': 'replace'},
                                                   {'character_id': 43699,
                                                    'native_collection_ordinal': 13,
                                                    'eligible': True,
                                                    'eligibility_reason': 'native_candidate_provider_accepted',
                                                    'main_skill': {'key': 'diplomacy', 'value': 1},
                                                    'action_route': 'replace'},
                                                   {'character_id': 43700,
                                                    'native_collection_ordinal': 11,
                                                    'eligible': True,
                                                    'eligibility_reason': 'native_candidate_provider_accepted',
                                                    'main_skill': {'key': 'diplomacy', 'value': 7},
                                                    'action_route': 'replace'},
                                                   {'character_id': 43706,
                                                    'native_collection_ordinal': 9,
                                                    'eligible': True,
                                                    'eligibility_reason': 'native_candidate_provider_accepted',
                                                    'main_skill': {'key': 'diplomacy', 'value': 8},
                                                    'action_route': 'replace'},
                                                   {'character_id': 43712,
                                                    'native_collection_ordinal': 10,
                                                    'eligible': True,
                                                    'eligibility_reason': 'native_candidate_provider_accepted',
                                                    'main_skill': {'key': 'diplomacy', 'value': 8},
                                                    'action_route': 'replace'}],
                                    'readiness': {'identity_ready': True,
                                                  'candidate_collection_ready': True,
                                                  'incumbent_ready': True,
                                                  'incumbent_main_skill_ready': True,
                                                  'candidate_legality_ready': True,
                                                  'main_skill_ready': True,
                                                  'action_route_ready': True,
                                                  'same_frame_ready': True,
                                                  'ready': True}},
 'queried_snapshot_id': 'native:16',
 'queried_revision': 2,
 'queried_native_revision': 16,
 'source_frame': {'snapshot_id': 'native:16',
                  'revision': 2,
                  'native_revision': 16,
                  'date_raw': 53220624,
                  'player_character_id': 29829,
                  'paused': True}}

ACTUAL_PRE_POSITION = {'position_key': 'councillor_chancellor',
 'incumbent_character_id': 34867,
 'task_key': 'task_foreign_affairs',
 'task_type': 'general',
 'target': None,
 'frozen': False,
 'progress': {'kind': 'infinite', 'current': None, 'maximum': None}}


class ConfiguredChancellorDriver:
    """Actual pre-query; explicitly synthetic command and independent future reads."""

    allow_private_council_action = True

    def __init__(self, state_dir):
        self.state_dir = state_dir
        self.phase = "pre"
        self.roles = []
        self.submit_calls = 0
        self.receipt_calls = 0
        self.root_calls = 0
        self.native_ack = None

    def take_snapshot(self):
        value = copy.deepcopy(ACTUAL_PRE_SNAPSHOT)
        if self.phase != "pre":
            public, native = (3, 17) if self.phase == "post" else (4, 18)
            value.update(snapshot_id=f"native:{native}", revision=public, native_revision=native)
        return value

    take_internal_semantic_snapshot = take_snapshot

    def query_council_final_gates_private_v1(self, *, expected_revision,
                                          position_key=STEWARD_POSITION_KEY):
        snapshot = self.take_snapshot()
        assert expected_revision == snapshot["revision"]
        self.roles.append(position_key)
        if position_key == STEWARD_POSITION_KEY:
            # Only a default-routing probe; this is not an observed Steward DTO.
            return {"status": "unavailable", "unavailable_reason": "offline_steward_not_in_fixture"}
        assert position_key == CHANCELLOR_POSITION_KEY
        value = copy.deepcopy(ACTUAL_PRE_QUERY)
        if self.phase == "pre":
            return value
        # Synthetic independent future query: retain the active Chancellor task
        # and make the applied character the new incumbent with diplomacy 13.
        payload = value["council_composition_candidates"]
        payload["snapshot"].update(snapshot_id=snapshot["snapshot_id"],
            public_revision=snapshot["native_revision"], native_revision=snapshot["native_revision"])
        payload["position"].update(incumbent_character_id=43696,
                                  incumbent_main_skill={"key": "diplomacy", "value": 13})
        for gate in value["council_final_gates"]["rows"]:
            if gate["character_id"] == 43696:
                gate["candidate_already_councillor"] = True
        value.update(snapshot_revision=snapshot["native_revision"],
                     queried_snapshot_id=snapshot["snapshot_id"],
                     queried_revision=snapshot["revision"],
                     queried_native_revision=snapshot["native_revision"])
        return value

    def submit_council_assign_private_v1(self, *, query, candidate_character_id,
                                       expected_revision, action_request_id):
        assert self.phase == "pre"
        assert self.roles[-1] == CHANCELLOR_POSITION_KEY
        assert query == ACTUAL_PRE_QUERY
        assert expected_revision == 2 and candidate_character_id == 43696
        self.submit_calls += 1
        request = build_assign_councillor_request_v1(query["council_composition_candidates"],
            candidate_character_id=candidate_character_id, request_id=action_request_id)
        # This ACK models correlation and helper invocation; it is not live.
        self.native_ack = {
            "status": "native_helper_invoked_verification_pending", "failure": "none",
            "action_request_id": action_request_id,
            "pre_snapshot_id": request.expected_snapshot_id,
            "pre_public_revision": request.expected_public_revision,
            "pre_native_revision": request.expected_native_revision,
            "pre_date_raw": request.expected_date_raw,
            "owner_character_id": request.expected_owner_character_id,
            "position_key": request.position_key, "active_task_id": 333,
            "candidate_character_id": candidate_character_id,
            "had_incumbent": True, "previous_incumbent_character_id": 34867,
            "route": "replace_incumbent", "native_helper_invoked": True,
            "queue_acceptance_observed": False, "verification_pending": True,
            "native_reason_key": "",
        }
        return {"council_assign_councillor_ack": copy.deepcopy(self.native_ack),
                "action_request_id": action_request_id, "request": request.as_wire_fields()}

    def query_council_assign_receipt_private_v1(self, *, pending, expected_revision):
        assert self.phase == "post" and expected_revision == 3
        assert pending["council_assign_councillor_ack"] == self.native_ack
        self.receipt_calls += 1
        # Deliberately synthetic receipt, bound to the independent future frame.
        return {"council_assign_councillor_receipt": {
            "status": "applied", "rejected_action_failure": "none",
            "action_request_id": self.native_ack["action_request_id"],
            "post_snapshot_id": "native:17", "post_public_revision": 17,
            "post_native_revision": 17, "post_date_raw": ACTUAL_PRE_SNAPSHOT["date_raw"],
            "owner_character_id": 29829, "position_key": CHANCELLOR_POSITION_KEY,
            "incumbent_character_id": 43696, "incumbent_identity_round_trip": True,
            "postcondition_verified": True, "reason": "",
        }}

    def execute_step(self, step, *, expected_revision):
        assert self.phase != "pre" and step == "query-campaign-root-context-v1"
        snapshot = self.take_snapshot()
        assert expected_revision == snapshot["revision"]
        self.root_calls += 1
        # A separate synthetic root observation, never reconstructed from ACK.
        position = copy.deepcopy(ACTUAL_PRE_POSITION)
        position["incumbent_character_id"] = 43696
        return {"campaign_root_context": {
            "status": "available", "snapshot_revision": snapshot["native_revision"],
            "date_raw": snapshot["date_raw"], "player_character_id": 29829,
            "council": {"positions": [position]},
        }}


def _plan(driver, *, configured=True):
    snapshot = driver.take_snapshot()
    arguments = {"position_key": CHANCELLOR_POSITION_KEY} if configured else {}
    return plan_council_private(driver,
        {"revision": snapshot["revision"], "snapshot_id": snapshot["snapshot_id"],
         "plan": {"policy": "nonwar-dispatch", "selected_step": None}},
        snapshot, [], set(), **arguments)


def test_configured_actual_chancellor_plus_six_replace_pending_receipt_and_next(tmp_path):
    driver = ConfiguredChancellorDriver(tmp_path)
    default = _plan(driver, configured=False)["plan"]
    assert driver.roles == [STEWARD_POSITION_KEY]
    assert default["selected_step"] is None and driver.submit_calls == 0
    unconfigured = select_council_candidate_v1(ACTUAL_PRE_QUERY,
                                              position_key=CHANCELLOR_POSITION_KEY)
    assert unconfigured["outcome"] == "NO_CHANGE"
    assert unconfigured["reason_code"] == "occupied_chancellor_outside_action_coverage"

    planned = _plan(driver)
    choice = planned["plan"]
    assert choice["selected_step"] == SUBMIT_STEP
    assert choice["council_private_query"] == ACTUAL_PRE_QUERY
    assert driver.roles[-1] == CHANCELLOR_POSITION_KEY
    decision = choice["council_decision"]
    assert decision["position_key"] == CHANCELLOR_POSITION_KEY
    assert decision["outcome"] == "REPLACE_REQUIRED"
    assert decision["incumbent_character_id"] == 34867
    assert decision["incumbent_main_skill"] == {"key": "diplomacy", "value": 7}
    assert decision["selected_candidate"]["character_id"] == 43696
    assert decision["selected_candidate"]["main_skill"] == {"key": "diplomacy", "value": 13}
    assert decision["skill_gain"] == 6
    request = build_assign_councillor_request_v1(
        ACTUAL_PRE_QUERY["council_composition_candidates"],
        candidate_character_id=43696, request_id="configured-chancellor-replace")
    assert request.position_key == CHANCELLOR_POSITION_KEY
    assert request.expected_has_incumbent is True
    assert request.expected_incumbent_character_id == 34867
    assert request.expected_native_revision == request.expected_public_revision == 16
    assert planned["revision"] == 2  # Actual frontend revision stays distinct.

    pending = submit_council_private(driver, plan=choice, expected_revision=2)
    assert pending["stage"] == "receipt_pending"
    assert pending["request"]["position_key"] == CHANCELLOR_POSITION_KEY
    assert pending["action_ack"]["council_assign_councillor_ack"]["route"] == "replace_incumbent"
    assert read_council_ledger(tmp_path)["applied"] is None
    waiting = _plan(driver)["plan"]
    assert waiting["selected_step"] is None
    assert waiting["council_pending_action"] == pending
    assert driver.roles == [STEWARD_POSITION_KEY, CHANCELLOR_POSITION_KEY]
    with pytest.raises(ValueError, match="unresolved assignment"):
        submit_council_private(driver, plan=choice, expected_revision=2)
    assert driver.submit_calls == 1

    driver.phase = "post"
    ready = _plan(driver)["plan"]
    assert ready["selected_step"] == RECEIPT_STEP
    applied = read_council_receipt_private(driver,
        pending=ready["council_pending_action"], expected_revision=3)
    assert applied["status"] == "applied"
    assert applied["independent_position"]["position_key"] == CHANCELLOR_POSITION_KEY
    assert applied["independent_position"]["incumbent_character_id"] == 43696
    assert applied["independent_position"]["task_key"] == "task_foreign_affairs"
    assert applied["next_turn_consumed"] is False
    assert read_council_ledger(tmp_path)["pending"] is None

    driver.phase = "next"
    following = _plan(driver)["plan"]
    assert following["council_decision"]["outcome"] == "NO_CHANGE"
    consumed = following["council_receipt_consumed"]
    assert consumed["next_turn_consumed"] is True
    assert consumed["next_turn_native_revision"] == 18
    assert consumed["next_turn_position"]["position_key"] == CHANCELLOR_POSITION_KEY
    assert consumed["next_turn_position"]["incumbent_character_id"] == 43696
    assert consumed["next_turn_position"]["task_key"] == "task_foreign_affairs"
    assert read_council_ledger(tmp_path)["applied"]["next_turn_consumed"] is True
    assert driver.roles == [STEWARD_POSITION_KEY, CHANCELLOR_POSITION_KEY, CHANCELLOR_POSITION_KEY]
    assert (driver.submit_calls, driver.receipt_calls, driver.root_calls) == (1, 1, 2)

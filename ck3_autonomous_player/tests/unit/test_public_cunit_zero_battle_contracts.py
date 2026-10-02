from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge import actual_contact_contract as contact
from xar_autoplayer.bridge import active_combat_retreat_contract as retreat
from xar_autoplayer.bridge import battle_control_contract as control
from xar_autoplayer.bridge import battle_reinforcement_assignment_contract as reinforcement
from xar_autoplayer.bridge import battle_terminal_transition_contract as terminal
from xar_autoplayer.bridge import battle_transition_contract as transition
from xar_autoplayer.bridge import combat_contract as combat
from xar_autoplayer.bridge import combat_phase_contract as phase
from xar_autoplayer.bridge.public_unit_contract import (
    is_public_cunit_id, optional_public_cunit_id, public_cunit_id, public_cunit_ids,
)
from xar_autoplayer.simulation.candidate_source_proof import (
    candidate_source_sequence_sha256, normalize_candidate_source_proof,
    CANDIDATE_SOURCE_PROOF_POLICY,
)
from ck3_autonomous_player.tests.unit import test_actual_contact_scope_contract as contact_fixture
from ck3_autonomous_player.tests.unit import test_battle_control_snapshot_v1_bridge as control_fixture
from ck3_autonomous_player.tests.unit import test_battle_reinforcement_assignment_v1_bridge as reinforcement_fixture
from ck3_autonomous_player.tests.unit import test_battle_terminal_transition_v1_bridge as terminal_fixture
from ck3_autonomous_player.tests.unit import test_battle_transition_v1_bridge as transition_fixture
from ck3_autonomous_player.tests.unit import test_combat_phase_inputs_v3_production_contract as phase_fixture

_PUBLIC_KEYS = {
    "army_id", "subject_army_id", "source_army_id", "primary_source_army_id",
    "primary_army_id", "army_ids", "ordered_army_ids", "attacker_army_ids",
    "defender_army_ids", "opponent_army_ids", "province_unit_army_ids",
}
_INVALID = (True, False, -1, -(2**31), 2**31, "0", 0.0, None, [], {})


def _replace_public_id(value, prior: int, replacement):
    """Alter fixture CUnit identities without touching its native CArmy IDs."""
    if isinstance(value, dict):
        for key, member in value.items():
            is_native_knight_membership = key == "army_id" and "participant_army_membership_verified" in value
            if (key in _PUBLIC_KEYS or "public_cunit" in key) and not is_native_knight_membership:
                if isinstance(member, list):
                    value[key] = [replacement if type(item) is int and item == prior else item for item in member]
                elif type(member) is int and member == prior:
                    value[key] = replacement
            _replace_public_id(value[key], prior, replacement)
    elif isinstance(value, list):
        for member in value:
            _replace_public_id(member, prior, replacement)
    return value


class PublicCUnitZeroBattleContractsTests(unittest.TestCase):
    def test_public_domain_is_strict_and_optional_zero_is_present(self):
        for value in (0, 1, 83_886_341, 2**31 - 1):
            with self.subTest(value=value):
                self.assertTrue(is_public_cunit_id(value))
                self.assertEqual(public_cunit_id(value, "unit"), value)
                self.assertEqual(optional_public_cunit_id(value, "unit"), value)
        self.assertIsNone(optional_public_cunit_id(None, "unit"))
        for value in _INVALID:
            with self.subTest(invalid=value):
                self.assertFalse(is_public_cunit_id(value))
                with self.assertRaises(ValueError):
                    public_cunit_id(value, "unit")
                with self.assertRaises(ValueError):
                    public_cunit_ids([value], "units")
        self.assertEqual(public_cunit_ids([3, 0, 2], "units"), [3, 0, 2])
        with self.assertRaises(ValueError):
            public_cunit_ids([0, 0], "units")

    def test_builders_and_parsers_preserve_zero_and_upper_bound(self):
        cases = (
            (lambda value: contact.query_actual_contact_scope_step(value, 2585), contact.parse_query_actual_contact_scope_step, lambda value: (value, 2585)),
            (control.query_battle_control_snapshot_v1_step, control.parse_query_battle_control_snapshot_v1_step, lambda value: value),
            (reinforcement.query_battle_reinforcement_assignment_v1_step, reinforcement.parse_query_battle_reinforcement_assignment_v1_step, lambda value: value),
            (lambda value: terminal.query_battle_terminal_transition_v1_step(77, value, 3), terminal.parse_query_battle_terminal_transition_v1_step, lambda value: (77, value, 3)),
            (lambda value: retreat.preview_active_combat_retreat_v1_step(value, 2700), retreat.parse_preview_active_combat_retreat_v1_step, lambda value: (value, 2700)),
        )
        for builder, parser, expected in cases:
            for value in (0, 1, 2**31 - 1):
                with self.subTest(builder=builder, value=value):
                    self.assertEqual(parser(builder(value)), expected(value))
            for invalid in _INVALID:
                with self.subTest(builder=builder, invalid=invalid):
                    with self.assertRaises(ValueError):
                        builder(invalid)
        order = retreat.order_active_combat_retreat_v1_step(
            0, expected_snapshot_revision=7, expected_combat_id=77,
            expected_side_index=0, expected_scope="full_side",
            target_province_id=2700, candidate_token="A" * 32,
        )
        self.assertEqual(retreat.parse_order_active_combat_retreat_v1_step(order)["selected_public_cunit_id"], 0)
        for invalid in ("00", "01", "+0", "-0", "-1", "2147483648", "０", " 0"):
            self.assertIsNone(control.parse_query_battle_control_snapshot_v1_step("query-battle-control-snapshot-v1-" + invalid))

    def test_actual_contact_zero_subject_and_opponent_preserve_order(self):
        for old_id in (11, 31):
            frame = _replace_public_id(contact_fixture._scope(), old_id, 0)
            frame["province_unit_army_ids"].sort()
            self.assertEqual(contact.normalize_actual_contact_scope(
                frame, expected_subject_army_id=frame["subject_army_id"],
                expected_target_province_id=2585, expected_date_raw=53176104,
                expected_snapshot_revision=17), frame)
        frame = _replace_public_id(contact_fixture._scope(), 11, 0)
        for invalid in _INVALID:
            bad = copy.deepcopy(frame)
            bad["subject_army_id"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                contact.normalize_actual_contact_scope(bad, expected_subject_army_id=0,
                    expected_target_province_id=2585, expected_date_raw=53176104,
                    expected_snapshot_revision=17)
        for key in ("subject_native_carmy_id", "subject_owner_character_id", "target_province_id"):
            bad = copy.deepcopy(frame)
            bad[key] = 0
            with self.subTest(non_unit=key), self.assertRaises(ValueError):
                contact.normalize_actual_contact_scope(bad, expected_subject_army_id=0,
                    expected_target_province_id=2585, expected_date_raw=53176104,
                    expected_snapshot_revision=17)

    def test_battle_control_zero_identity_and_all_affected_bindings(self):
        frame = _replace_public_id(control_fixture._battle_frame(), control_fixture.SUBJECT, 0)
        self.assertEqual(control.normalize_battle_control_snapshot_v1(frame,
            expected_subject_public_cunit_id=0,
            expected_observed_date_raw=control_fixture.DATE_RAW,
            expected_snapshot_revision=control_fixture.NATIVE_REVISION), frame)
        for invalid in _INVALID:
            bad = copy.deepcopy(frame)
            bad["selected_public_cunit_id"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                control.normalize_battle_control_snapshot_v1(bad,
                    expected_subject_public_cunit_id=0,
                    expected_observed_date_raw=control_fixture.DATE_RAW,
                    expected_snapshot_revision=control_fixture.NATIVE_REVISION)
        bad = copy.deepcopy(frame)
        bad["subject_native_carmy_id"] = 0
        with self.assertRaises(ValueError):
            control.normalize_battle_control_snapshot_v1(bad, expected_subject_public_cunit_id=0,
                expected_observed_date_raw=control_fixture.DATE_RAW,
                expected_snapshot_revision=control_fixture.NATIVE_REVISION)

    def test_transition_and_terminal_lists_include_zero(self):
        frame = _replace_public_id(transition_fixture._frame(), transition_fixture.SUBJECT, 0)
        self.assertEqual(transition.normalize_battle_transition_v1(frame,
            expected_combat_id=frame["combat_id"],
            expected_observed_date_raw=frame["observed_date_raw"],
            expected_snapshot_revision=frame["snapshot_revision"]), frame)
        frame = _replace_public_id(terminal_fixture._normal_frame(), terminal_fixture.SUBJECT_CUNIT_ID, 0)
        self.assertEqual(terminal.normalize_battle_terminal_transition_v1(frame,
            expected_prior_combat_id=frame["prior_combat_id"],
            expected_subject_public_cunit_id=0,
            expected_after_terminal_sequence=terminal_fixture.CURSOR,
            expected_observed_date_raw=frame["observed_date_raw"],
            expected_snapshot_revision=frame["snapshot_revision"]), frame)

    def test_reinforcement_public_lists_change_without_native_identity(self):
        frame = _replace_public_id(reinforcement_fixture._frame(), reinforcement_fixture.SUBJECT, 0)
        self.assertEqual(reinforcement.normalize_battle_reinforcement_assignment_v1(frame,
            expected_selected_public_cunit_id=0,
            expected_observed_date_raw=frame["observed_date_raw"],
            expected_snapshot_revision=frame["snapshot_revision"]), frame)
        for key in ("selected_native_carmy_id", "coordinator_id"):
            bad = copy.deepcopy(frame)
            bad[key] = 0
            with self.subTest(non_unit=key), self.assertRaises(ValueError):
                reinforcement.normalize_battle_reinforcement_assignment_v1(bad,
                    expected_selected_public_cunit_id=0,
                    expected_observed_date_raw=frame["observed_date_raw"],
                    expected_snapshot_revision=frame["snapshot_revision"])

    def test_combat_request_zero_in_either_side_but_not_other_id_domains(self):
        for attackers, defenders in (([0, 12], [22]), ([12], [0, 22])):
            expected = (900, 800, attackers, defenders)
            self.assertEqual(combat.normalize_combat_simulation_request(*expected), expected)
            self.assertEqual(combat.parse_query_combat_simulation_inputs_step(
                combat.query_combat_simulation_inputs_step(*expected)), expected)
            self.assertEqual(phase.parse_query_combat_simulation_inputs_v3_step(
                phase.query_combat_simulation_inputs_v3_step(*expected)), expected)
        for invalid in _INVALID:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                combat.normalize_combat_simulation_request(900, 800, [invalid], [22])
        for args in ((0, 800, [0], [22]), (900, 0, [0], [22]), (900, 800, [0], [0])):
            with self.subTest(args=args), self.assertRaises(ValueError):
                combat.normalize_combat_simulation_request(*args)

    def test_production_combat_phase_zero_round_trip(self):
        payload, scope = phase_fixture._production_payload()
        first = payload["base_inputs"]["scenario"]["attacker_army_ids"][0]
        _replace_public_id(payload, first, 0)
        _replace_public_id(scope, first, 0)
        # The fixture now describes a different, precisely bound source sequence.
        # Recompute its claimed digest; production still verifies it independently.
        for side in payload["phase_event_inputs"]["raw"]["sides"]:
            proof = side["candidate_source_proof"]
            proof["sequence_sha256"] = candidate_source_sequence_sha256(
                side["side_index"], proof["ordered_sources"]
            )
        normalized = phase_fixture._normalize(payload, scope)
        self.assertEqual(normalized["base_inputs"]["scenario"]["attacker_army_ids"][0], 0)
        self.assertEqual(normalized["base_inputs"]["armies"][0]["army_id"], 0)
        proof = normalized["phase_event_inputs"]["raw"]["sides"][0]["candidate_source_proof"]
        self.assertEqual(proof["ordered_sources"][0]["source_army_id"], 0)
        self.assertEqual(proof["sequence_sha256"], candidate_source_sequence_sha256(0, proof["ordered_sources"]))
        self.assertGreater(normalized["base_inputs"]["armies"][0]["native_carmy_id"], 0)
        for invalid in _INVALID:
            bad = copy.deepcopy(payload)
            bad["base_inputs"]["armies"][0]["army_id"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                phase_fixture._normalize(bad, scope)

    def test_candidate_source_zero_requires_exact_sha_and_positive_character(self):
        rows = [{"role": "commander", "source_army_id": 0, "source_regiment_id": None, "character_id": 42}]
        proof = {"policy": CANDIDATE_SOURCE_PROOF_POLICY,
            "source_vector_equivalence": True, "ordered_sources": rows,
            "sequence_sha256": candidate_source_sequence_sha256(0, rows)}
        self.assertEqual(normalize_candidate_source_proof(proof, side_index=0), proof)
        for key, invalid in (("source_army_id", value) for value in _INVALID):
            bad = copy.deepcopy(proof)
            bad["ordered_sources"][0][key] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                normalize_candidate_source_proof(bad, side_index=0)
        bad = copy.deepcopy(proof)
        bad["ordered_sources"][0]["character_id"] = 0
        with self.assertRaises(ValueError):
            normalize_candidate_source_proof(bad, side_index=0)
        bad = copy.deepcopy(proof)
        bad["sequence_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            normalize_candidate_source_proof(bad, side_index=0)


if __name__ == "__main__":
    unittest.main()

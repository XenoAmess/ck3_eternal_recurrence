"""Synthetic DTOs only: no Native provider, saved game or real H qualified.

The normal-source flags below model a future owner-validated response; this
test cannot establish its provenance. Actual native fixture flags are tested
separately and must never receive scoring credit.
"""
from dataclasses import replace
import unittest

from xar_autoplayer.player_heir_fixed_dynasty_projection_v1 import (
    BoundPlayerHeirCandidateV1, CandidateCoreFrameV1, CandidateLineageV1,
    CandidateQueryBindingV1, EXACT_EXE_SHA256, FixedDynastyAnchorV1,
    GETTER_SOURCE_CLOSURE_SHA256, NativePlayerHeirCandidateV1, SOURCE_KIND,
    ROBERT_V20261019_T0_ANCHOR,
    project_fixed_dynasty_candidate_v1,
)


def fixture():
    anchor = ROBERT_V20261019_T0_ANCHOR
    binding = CandidateQueryBindingV1(
        machine_id="synthetic-projection-fixture", game_birth="134368602545256920",
        bridge_pid=123, connection_generation=2,
        executable_sha256=EXACT_EXE_SHA256, native_provider_sha256="a" * 64,
        owner_source_epoch="b" * 64, query_id="synthetic-query-1",
        snapshot_id="native:2", revision=3, native_revision=2, capture_epoch=7,
        date_raw=53186880, actor_character_id=40526,
        episode_run_id="synthetic-successor-episode",
        goal_campaign_id=anchor.goal_campaign_id, origin_character_id=anchor.origin_character_id,
        baseline_save_sha256=anchor.baseline_save_sha256,
        baseline_summary_sha256=anchor.baseline_summary_sha256)
    core = CandidateCoreFrameV1(binding.date_raw, True, 3, 0, True, True, binding.actor_character_id, True)
    observation = NativePlayerHeirCandidateV1(
        available=True, unavailable_reason=None, source_fixture=False,
        original_getter_source_bound=True, before=core, after=core,
        getter_observed=True, candidate_present=True, actor_character_id=binding.actor_character_id,
        candidate_character_id=67890, candidate_alive=True, identity_and_frame_stable=True,
        lineage_available=True, candidate_lineage=CandidateLineageV1(900, 174),
        lineage_unavailable_reason=None)
    captured = BoundPlayerHeirCandidateV1(binding, observation, SOURCE_KIND, GETTER_SOURCE_CLOSURE_SHA256)
    return dict(anchor=anchor, captured=captured, current=binding, current_core=core)


def with_observation(case, **changes):
    return {**case, "captured": replace(case["captured"],
        observation=replace(case["captured"].observation, **changes))}


class FixedDynastyProjectionTests(unittest.TestCase):
    def assert_unknown(self, result):
        self.assertIsNone(result.k)
        self.assertIsNone(result.b)
        self.assertEqual(result.H_interval, (0, 100))
        self.assertFalse(result.positive_same_dynasty_legal_witness)
        self.assertFalse(result.complete_backup_domain)

    def test_single_cadet_house_witness_has_interval_and_preserves_T0(self):
        case = fixture()
        result = project_fixed_dynasty_candidate_v1(**case)
        self.assertEqual(result.k, 1)
        self.assertIsNone(result.b)
        self.assertEqual(result.H_interval, (70, 100))
        self.assertTrue(result.candidate_same_fixed_dynasty)
        self.assertFalse(result.complete_backup_domain)
        # Current actor/episode differ from founder/T0. No owner-dynasty or age
        # input is used: a native-legal minor or cadet is not penalized again.
        self.assertNotEqual(case["current"].episode_run_id, case["anchor"].baseline_episode_run_id)
        self.assertNotEqual(case["current"].actor_character_id, case["anchor"].origin_character_id)
        self.assertEqual(case["anchor"].founding_dynasty_id_raw, 174)

    def test_mismatching_selected_dynasty_never_proves_k_zero(self):
        for house, dynasty in ((900, 175), (900, 0x010000AE), (-1, -1), (900, -1)):
            case = with_observation(fixture(), candidate_lineage=CandidateLineageV1(house, dynasty))
            with self.subTest(house=house, dynasty=dynasty):
                result = project_fixed_dynasty_candidate_v1(**case)
                self.assert_unknown(result)
                self.assertIs(result.candidate_same_fixed_dynasty, False)

    def test_unavailable_lineage_is_distinct_from_known_none(self):
        case = with_observation(fixture(), lineage_available=False,
            candidate_lineage=CandidateLineageV1(-1, -1), lineage_unavailable_reason="reader_failed")
        result = project_fixed_dynasty_candidate_v1(**case)
        self.assert_unknown(result)
        self.assertIsNone(result.candidate_same_fixed_dynasty)
        self.assertEqual(result.reason, "candidate_lineage_unavailable")

    def test_null_dead_stale_invalid_self_or_unbound_never_gains_score(self):
        for changes in (
            {"candidate_present": False, "candidate_character_id": -1},
            {"candidate_alive": False}, {"candidate_character_id": -1},
            {"candidate_character_id": 40526}, {"candidate_character_id": True},
            {"candidate_character_id": 2**31}, {"identity_and_frame_stable": False},
            {"getter_observed": False}, {"original_getter_source_bound": False},
            {"available": False, "unavailable_reason": "source_unavailable"},
            {"unavailable_reason": "contradictory_source_error"},
            {"lineage_unavailable_reason": "contradictory_lineage_error"},
            {"actor_character_id": -1}, {"candidate_alive": 1},
        ):
            with self.subTest(changes=changes):
                self.assert_unknown(project_fixed_dynasty_candidate_v1(**with_observation(fixture(), **changes)))

    def test_full_signed_generation_ids_preserved_without_slot_mask(self):
        case = fixture()
        actor, heir, house, dynasty = (0x81000001 - 2**32, 0x92000002 - 2**32,
            0xE1000001 - 2**32, 0xF1000001 - 2**32)
        # Separate synthetic baseline, not a rewrite of the actual D0=174 pin.
        anchor = replace(case["anchor"], founding_dynasty_id_raw=dynasty,
            baseline_save_sha256="d" * 64, baseline_summary_sha256="e" * 64)
        binding = replace(case["current"], actor_character_id=actor,
            baseline_save_sha256=anchor.baseline_save_sha256,
            baseline_summary_sha256=anchor.baseline_summary_sha256)
        core = replace(case["current_core"], played_character_id=actor)
        obs = replace(case["captured"].observation, before=core, after=core,
            actor_character_id=actor, candidate_character_id=heir,
            candidate_lineage=CandidateLineageV1(house, dynasty))
        case.update(anchor=anchor, current=binding, current_core=core,
            captured=replace(case["captured"], binding=binding, observation=obs))
        result = project_fixed_dynasty_candidate_v1(**case)
        self.assertEqual(result.k, 1)
        self.assertEqual(result.candidate_character_id, heir)
        self.assertEqual(result.fixed_dynasty_id_raw, dynasty)
        different_generation = replace(obs, candidate_lineage=CandidateLineageV1(house, 1))
        result = project_fixed_dynasty_candidate_v1(**{**case,
            "captured": replace(case["captured"], observation=different_generation)})
        self.assert_unknown(result)
        self.assertIs(result.candidate_same_fixed_dynasty, False)

    def test_every_changed_query_identity_is_stale_even_on_same_native_date(self):
        changes = dict(machine_id="other-machine", game_birth="other-birth", bridge_pid=124,
            connection_generation=3, native_provider_sha256="c" * 64, owner_source_epoch="d" * 64,
            query_id="query-2", snapshot_id="native:3", revision=4, native_revision=3,
            capture_epoch=8, date_raw=53186881, actor_character_id=40527,
            episode_run_id="other-episode", goal_campaign_id="other-campaign", origin_character_id=31255,
            baseline_save_sha256="e" * 64, baseline_summary_sha256="f" * 64)
        for key, value in changes.items():
            case = fixture(); case["current"] = replace(case["current"], **{key: value})
            with self.subTest(key=key):
                self.assert_unknown(project_fixed_dynasty_candidate_v1(**case))

    def test_core_bookends_are_independent_of_claimed_stable_flag(self):
        changes = dict(date_raw=53186881, paused=False, speed=4, local_player_id=1,
            map_ready=False, has_played_character=False, played_character_id=40527,
            played_character_alive=False)
        for key, value in changes.items():
            case = fixture(); different = replace(case["current_core"], **{key: value})
            for endpoint in ("before", "after"):
                with self.subTest(key=key, endpoint=endpoint):
                    self.assert_unknown(project_fixed_dynasty_candidate_v1(
                        **with_observation(case, **{endpoint: different})))

    def test_title_heirs_cache_rosters_and_native_mock_source_are_not_witnesses(self):
        for source in ("primary_title_first_heir", "LandState+3A0", "exclude_selector_loop"):
            case = fixture(); case["captured"] = replace(case["captured"], source_kind=source)
            with self.subTest(source=source):
                self.assert_unknown(project_fixed_dynasty_candidate_v1(**case))
        self.assert_unknown(project_fixed_dynasty_candidate_v1(
            **with_observation(fixture(), source_fixture=True)))
        # Repeated exact observations and duplicate candidates cannot increase b.
        for _ in range(3):
            result = project_fixed_dynasty_candidate_v1(**fixture())
            self.assertIsNone(result.b)
            self.assertEqual(result.H_interval, (70, 100))

    def test_anchor_and_source_pins_must_join_original_campaign(self):
        for changes in (
            {"goal_campaign_id": "robert-first30-v20261019"},
            {"origin_character_id": 40526}, {"baseline_save_sha256": "f" * 64},
            {"baseline_summary_sha256": "f" * 64}, {"t0_date_raw": 53186881},
            {"founding_dynasty_id_raw": -1},
            {"founding_dynasty_id_raw": 175},
        ):
            case = fixture(); case["anchor"] = replace(case["anchor"], **changes)
            with self.subTest(changes=changes):
                self.assert_unknown(project_fixed_dynasty_candidate_v1(**case))
        case = fixture(); case["captured"] = replace(case["captured"], getter_source_closure_sha256="0" * 64)
        self.assert_unknown(project_fixed_dynasty_candidate_v1(**case))
        case = fixture(); bad = replace(case["current"], executable_sha256="f" * 64)
        case.update(current=bad, captured=replace(case["captured"], binding=bad))
        self.assert_unknown(project_fixed_dynasty_candidate_v1(**case))

    def test_inconsistent_or_malformed_lineage_and_json_are_not_trusted(self):
        for lineage in (CandidateLineageV1(-1, 174), CandidateLineageV1(True, 174),
                CandidateLineageV1(900, 2**31), {"house_id": 900, "dynasty_id": 174}):
            with self.subTest(lineage=lineage):
                self.assert_unknown(project_fixed_dynasty_candidate_v1(
                    **with_observation(fixture(), candidate_lineage=lineage)))
        case = fixture(); case["captured"] = {"native_qualified": True, "dynasty_id": 174}
        self.assert_unknown(project_fixed_dynasty_candidate_v1(**case))


if __name__ == "__main__":
    unittest.main()

"""SYNTHETIC pure-Python DTOs only: no native fixture, live or business qualification.

The explicit synthetic legacy envelopes exercise real existing normalizers.
No game, pipe endpoint, native build, callback or action is run by this test.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import unittest

REPO = Path(__file__).resolve().parents[3]
BASE = Path(os.environ.get("XAR_RELIC_RECOGNITION_BASE_SOURCE_ROOT", str(REPO))).resolve()
sys.path.insert(0, str(BASE / "ck3_autonomous_player/src"))
import xar_autoplayer

if REPO.resolve() != BASE:
    if any(name == "xar_autoplayer.bridge" or name.startswith("xar_autoplayer.bridge.") for name in sys.modules):
        raise RuntimeError("synthetic external source-overlay tests require a fresh Python process")
    bridge_base = BASE / "ck3_autonomous_player/src/xar_autoplayer/bridge"
    bridge_candidate = REPO / "ck3_autonomous_player/src/xar_autoplayer/bridge"
    spec = importlib.util.spec_from_file_location("xar_autoplayer.bridge", bridge_base / "__init__.py",
        submodule_search_locations=[str(bridge_candidate), str(bridge_base)])
    package = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = package
    xar_autoplayer.bridge = package
    spec.loader.exec_module(package)

from xar_autoplayer.bridge.holy_site_relic_recognition_matrix import (
    LIMITS, normalize_holy_site_relic_recognition_matrix_v1 as normalize,
)
from xar_autoplayer.bridge.player_holy_site_relic_context_private_transport import normalize_player_holy_site_relic_context_v1 as normalize_context
from xar_autoplayer.bridge.player_holy_site_relic_action_context_private_transport import (
    normalize_player_holy_site_relic_action_context_v1 as normalize_action,
    relic_action_preview_canonical_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12004

SITE, ACTOR, DATE, EPOCH = 32, 15893, 51394920, 211


def parent():
    return {"available": True, "capture_epoch": EPOCH, "played_character_id": ACTOR,
            "date_raw": DATE, "evaluation_context": {"native_getter_calls": 10000}}


def matrix(*, associated=None, player=6, holder=7, slots=None, candidates=None, requested=None):
    """Synthetic recognized booleans alternate; no CK3 semantics are inferred."""
    associated = [5, 6, 5] if associated is None else associated
    slots = [100, None, 101, 100] if slots is None else slots
    candidates = [102, 100] if candidates is None else candidates
    faith_ids = list(dict.fromkeys(item for item in [*associated, player, holder] if item is not None))
    artifact_ids = list(dict.fromkeys(item for item in [*slots, *candidates, requested] if item is not None))
    return {"schema": "ck3_12004_holy_site_relic_recognition_matrix_v1", "available": True,
        "complete": True, "source_arrays_stable": True, "evaluation_atomic": False,
        "benefits_observed": False, "world_cache_written": False, "read_only": True,
        "holy_site_id": SITE, "capture_epoch": EPOCH, "played_character_id": ACTOR, "date_raw": DATE,
        "faith_sources": {"associated_available": True, "associated_faith_ids": associated,
            "player_faith_id": player, "county_holder_faith_id": holder},
        "artifact_sources": {"slots_available": True, "slot_artifact_ids": slots,
            "window_candidates_available": True, "window_candidate_artifact_ids": candidates,
            "requested_action_artifact_id": requested},
        "faiths": [{"faith_id": item, "source_associated": item in associated, "source_player": item == player,
            "source_county_holder": item == holder, "object_resolved": True, "unavailable_reason": None} for item in faith_ids],
        "artifacts": [{"artifact_id": item, "slot_indices": [i for i, raw in enumerate(slots) if raw == item],
            "candidate_indices": [i for i, raw in enumerate(candidates) if raw == item], "source_action_request": item == requested,
            "object_resolved": True, "unavailable_reason": None} for item in artifact_ids],
        "cells": [{"artifact_id": artifact, "faith_id": faith, "available": True,
            "value": bool((ai + fi) % 2), "unavailable_reason": None}
            for ai, artifact in enumerate(artifact_ids) for fi, faith in enumerate(faith_ids)],
        "faith_deduplication": "first_seen_full_id_associated_player_county_holder",
        "artifact_deduplication": "first_seen_full_id_slots_window_candidates_action_request",
        "native_getter_calls": len(faith_ids) * len(artifact_ids), "max_native_getter_calls": 256,
        "limits": dict(LIMITS), "unavailable_reason": None}


def invalidate(value, *, reason="synthetic_source_drift", stable=False):
    value.update(available=False, complete=False, source_arrays_stable=stable, unavailable_reason=reason)
    for cell in value["cells"]:
        cell.update(available=False, value=None, unavailable_reason=reason)
    return value


def overflow(value):
    value.update(available=False, complete=False, native_getter_calls=0,
        faiths=[], artifacts=[], cells=[], unavailable_reason="synthetic_evaluation_cap_exceeded")
    return value


class MatrixSyntheticTests(unittest.TestCase):
    def accepted(self, value, *, requested=None, owner=None):
        original = deepcopy(value)
        result = normalize(value, parent=owner or parent(), holy_site_id=SITE, requested_action_artifact_id=requested)
        self.assertEqual(value, original)
        self.assertEqual(result, value)
        return result

    def rejected(self, value, *, requested=None, owner=None):
        original = deepcopy(value)
        with self.assertRaises(ValueError):
            normalize(value, parent=owner or parent(), holy_site_id=SITE, requested_action_artifact_id=requested)
        self.assertEqual(value, original)

    def test_raw_duplicates_first_seen_rows_indices_and_observed_false_are_preserved(self):
        value = matrix()
        result = self.accepted(value)
        self.assertEqual([row["faith_id"] for row in result["faiths"]], [5, 6, 7])
        self.assertEqual(result["artifacts"][0]["slot_indices"], [0, 3])
        self.assertEqual(result["cells"][0]["value"], False)
        self.assertTrue(result["cells"][0]["available"])
        result["faith_sources"]["associated_faith_ids"].append(99)
        self.assertNotEqual(result, value)

    def test_request_is_only_the_actual_existing_action_argument(self):
        self.accepted(matrix(requested=237), requested=237)
        self.rejected(matrix(requested=237))
        self.rejected(matrix(requested=237), requested=238)

    def test_parent_identity_crosses_and_full_reference_generation_are_rejected(self):
        for key, value in (("holy_site_id", SITE + 1), ("capture_epoch", EPOCH + 1),
                ("played_character_id", ACTOR + 1), ("date_raw", DATE + 1)):
            altered = matrix()
            altered[key] = value
            with self.subTest(key=key):
                self.rejected(altered)
        value = matrix(associated=[5, 0x10000005], player=5, holder=0x10000005)
        self.accepted(value)
        value["faiths"][1]["faith_id"] = 5
        self.rejected(value)

    def test_unknown_schema_extra_semantics_and_forged_boundaries_are_rejected(self):
        changes = (("schema", "other"), ("evaluation_atomic", True), ("benefits_observed", True),
            ("world_cache_written", True), ("read_only", False), ("available", 1),
            ("faith_deduplication", "sorted"), ("artifact_deduplication", "sorted"),
            ("per_faith_active", False), ("beneficiaries", []))
        for field, value in changes:
            altered = matrix()
            altered[field] = value
            with self.subTest(field=field):
                self.rejected(altered)

    def test_only_unavailable_parent_accepts_explicit_null_extension(self):
        self.assertIsNone(normalize(None, parent={**parent(), "available": False}, holy_site_id=SITE))
        self.rejected(None)
        self.rejected(matrix(), owner={**parent(), "available": False})

    def test_complete_requires_known_player_and_holder_even_if_associated_known(self):
        for field in ("player", "holder"):
            value = matrix(**{field: None})
            with self.subTest(field=field):
                self.rejected(value)
                value.update(complete=False, unavailable_reason="synthetic_" + field + "_faith_unavailable")
                self.accepted(value)

    def test_unresolved_faith_cells_remain_null_and_partial_reason_is_preserved(self):
        value = matrix()
        value.update(complete=False, unavailable_reason="synthetic_recognition_cell_unavailable")
        value["faiths"][1].update(object_resolved=False, unavailable_reason="synthetic_stale_faith_generation")
        for cell in value["cells"]:
            if cell["faith_id"] == 6:
                cell.update(available=False, value=None, unavailable_reason="synthetic_stale_faith_generation")
        self.accepted(value)
        value["complete"] = True
        self.rejected(value)
        value["complete"] = False
        next(cell for cell in value["cells"] if cell["faith_id"] == 6)["value"] = False
        self.rejected(value)

    def test_unresolved_artifact_may_not_expose_an_observed_cell(self):
        value = matrix()
        value.update(complete=False, unavailable_reason="synthetic_artifact_unresolved")
        value["artifacts"][0].update(object_resolved=False, unavailable_reason="synthetic_stale_artifact_generation")
        self.rejected(value)
        for cell in value["cells"]:
            if cell["artifact_id"] == 100:
                cell.update(available=False, value=None, unavailable_reason="synthetic_stale_artifact_generation")
        self.accepted(value)

    def test_drift_invalidates_every_cell_and_allows_empty_cell_array(self):
        value = invalidate(matrix())
        self.accepted(value)
        value["cells"][0].update(available=True, value=False, unavailable_reason=None)
        self.rejected(value)
        value["cells"] = []
        self.accepted(value)

    def test_false_unavailability_does_not_become_an_observed_negative(self):
        value = invalidate(matrix())
        value["cells"][0]["value"] = False
        self.rejected(value)
        value["cells"][0]["value"] = None
        value["cells"][0]["unavailable_reason"] = None
        self.rejected(value)

    def test_raw_unavailable_sources_are_null_and_prevent_complete(self):
        for source_name, flag, ids in (("faith_sources", "associated_available", "associated_faith_ids"),
                ("artifact_sources", "slots_available", "slot_artifact_ids"),
                ("artifact_sources", "window_candidates_available", "window_candidate_artifact_ids")):
            value = matrix(associated=[], slots=[], candidates=[])
            value[source_name][flag] = False
            value[source_name][ids] = None
            value.update(complete=False, unavailable_reason="synthetic_source_unavailable")
            with self.subTest(source=ids):
                self.accepted(value)
                value[source_name][ids] = []
                self.rejected(value)

    def test_every_evaluation_cap_preserves_raw_sources_but_clears_dedup_rows(self):
        examples = (matrix(associated=list(range(65)), player=0, holder=0, slots=[1], candidates=[]),
            matrix(slots=[100] * 65, candidates=[]), matrix(slots=[], candidates=[100] * 65),
            matrix(slots=list(range(64)), candidates=[64]),
            matrix(associated=list(range(17)), player=0, holder=0, slots=list(range(16)), candidates=[]))
        for original in examples:
            with self.subTest(faiths=len(original["faiths"]), artifacts=len(original["artifacts"])):
                value = overflow(deepcopy(original))
                self.accepted(value)
                self.assertEqual(value["faith_sources"], original["faith_sources"])
                self.assertEqual(value["artifact_sources"], original["artifact_sources"])
                value["native_getter_calls"] = 1
                self.rejected(value)

    def test_raw_array_bound_is_4096_not_a_dedup_truncation(self):
        self.accepted(matrix(associated=[6] * 4096, player=6, holder=6, slots=[0], candidates=[]))
        self.rejected(matrix(associated=[6] * 4097, player=6, holder=6, slots=[0], candidates=[]))

    def test_cartesian_product_exactly_256_is_observed_and_257plus_is_not(self):
        self.accepted(matrix(associated=list(range(16)), player=0, holder=0, slots=list(range(16)), candidates=[]))
        self.rejected(matrix(associated=list(range(17)), player=0, holder=0, slots=list(range(16)), candidates=[]))

    def test_first_seen_orders_flags_indices_and_grid_are_exact(self):
        mutations = (
            lambda value: value["faiths"].reverse(), lambda value: value["artifacts"].reverse(),
            lambda value: value["cells"].reverse(), lambda value: value["faiths"][0].update(source_player=True),
            lambda value: value["artifacts"][0].update(slot_indices=[3, 0]),
            lambda value: value["artifacts"][0].update(candidate_indices=[]),
            lambda value: value["cells"][0].update(faith_id=999),
            lambda value: value["cells"].append(deepcopy(value["cells"][0])),
        )
        for mutate in mutations:
            value = matrix()
            mutate(value)
            with self.subTest(mutate=mutate):
                self.rejected(value)

    def test_bool_ids_unused_id_nonbool_values_and_counter_lies_are_rejected(self):
        mutations = (
            lambda value: value["faith_sources"].update(player_faith_id=True),
            lambda value: value["artifact_sources"]["slot_artifact_ids"].__setitem__(0, 0xFFFFFFFF),
            lambda value: value["cells"][0].update(value=0),
            lambda value: value.update(native_getter_calls=True), lambda value: value.update(native_getter_calls=257),
            lambda value: value.update(native_getter_calls=0), lambda value: value.update(native_getter_calls=10),
            lambda value: value["limits"].update(slots=65),
        )
        for mutate in mutations:
            value = matrix()
            mutate(value)
            with self.subTest(mutate=mutate):
                self.rejected(value)
        self.accepted(matrix(), owner={**parent(), "evaluation_context": {"native_getter_calls": 0}})

    def test_empty_artifact_grid_is_not_an_invented_negative(self):
        value = matrix(associated=[], slots=[], candidates=[])
        self.accepted(value)
        self.assertEqual(value["cells"], [])
        self.assertEqual(value["native_getter_calls"], 0)


def unknown(**values):
    return {"available": False, "unavailable_reason": "synthetic_unobserved", **values}


def observed(**values):
    return {"available": True, "unavailable_reason": None, **values}


def frame():
    return {"played_character": {"character_id": ACTOR}, "date_raw": DATE,
        "diagnostics": {"hello": {"expected_ck3_version": CK3_12004.game_version,
        "expected_ck3_sha256": CK3_12004.executable_sha256}}}


def common(schema):
    return {"schema": schema, "game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256,
        "available": True, "unavailable_reason": None, "capture_epoch": EPOCH, "played_character_id": ACTOR,
        "date_raw": DATE, "requested_holy_site_id": SITE, "read_only": True}


def legacy_context():
    result = common("ck3_12004_player_holy_site_relic_context_v1")
    result.update(player_rite_id=15, player_faith_id=6, holy_site_id=SITE,
        beneficiaries_observed=False, beneficiaries=None, can_enshrine_observed=False, can_enshrine=None,
        window_candidates_observed=False, associated_faith_ids_available=True, associated_faith_ids=[5, 6, 5],
        cached_world_state=unknown(is_active=None, total_active_artifact_rarity=None, refresh_time_known=False, world_effects_applied_observed=False),
        county_context=unknown(barony_title_id=None, county_title_id=None, county_holder_id=None,
            county_holder_rite_id=None, county_holder_faith_id=None),
        inventory=observed(artifact_ids=[], slots=[], artifact_objects=[]),
        current_relic_evaluation=unknown(method="original_native_rarity_producer", active_artifact_rarity_sum=None,
            is_active=None, cache_evaluation_disagreement=None, inventory_artifact_count_raw=None, county_holder_faith_associated=None),
        evaluation_context={"native_getter_calls": 10000, "getter_backend": "unavailable",
            "owner_thread_requirement": "existing_religion_owner_callback", "gameplay_command_submitted": False,
            "world_cache_written": False, "script_evaluation_allocates_and_uses_tls": True,
            "script_rng_effects_verified": False, "script_rng_effects": "unknown"})
    return result


def legacy_permissions(artifact):
    result = common("ck3_12004_player_holy_site_relic_permissions_v1")
    result.update(available=False, unavailable_reason="synthetic_unobserved", player_faith_id=6, holy_site_id=SITE,
        requested_artifact_id=artifact, loaded_source_pins_verified=False, action_ready=False,
        beneficiaries_observed=False, beneficiaries=None,
        evaluation_context={"native_getter_calls": 10000, "getter_backend": "unavailable",
            "owner_thread_requirement": "existing_religion_owner_callback", "gameplay_command_submitted": False,
            "world_cache_written": False, "window_selection_written": False, "window_candidate_cache_written": False,
            "script_evaluation_allocates_and_uses_tls": True, "inventory_getter_may_initialize_static_context": True,
            "script_rng_effects_verified": False, "script_rng_effects": "unknown"},
        site_inventory_slots=unknown(slots=None),
        window_context=unknown(root_present=None, selected_holy_site_id=None, selected_artifact_id=None,
            slot_mode="unknown", selected_slot_index=None, selected_slot_artifact_id=None,
            cached_candidates=unknown(artifact_ids=None, refresh_time_known=False, producer_invoked=False)),
        player_inventory=unknown(artifact_ids=None, native_character_owner_id=None, native_holy_site_owner_id=None, owner_matches_player=None),
        current_candidates=unknown(artifact_ids=None, evaluations=None,
            method="original_native_candidate_predicate_over_current_player_inventory", producer_invoked=False),
        artifact_permissions=unknown(object_resolved=False, artifact_id=artifact, native_holy_site_owner_id=None,
            rarity_level=None, player_inventory_contains_reference=None, can_enshrine=unknown(value=None),
            can_remove=unknown(value=None), slot_context="current_holy_site_window"),
        current_buttons=unknown(selected_artifact_id=None, context_matches_requested_artifact=None,
            can_enshrine=unknown(value=None), can_remove=unknown(value=None)))
    return result


def ownership(artifact):
    return unknown(object_resolved=False, artifact_id=artifact, character_owner_id=None, holy_site_owner_id=None,
        rarity_level=None, character_owner_matches_player=None, holy_site_owner_matches_requested=None,
        player_owned_reference_member=None, player_equipped_slot_member=unknown(value=None), site_equipped_slot_member=unknown(value=None))


def legacy_action(artifact=237):
    result = common("ck3_12004_player_holy_site_relic_action_context_v1")
    result.update(requested_artifact_id=artifact, loaded_source_pins_verified=False,
        permissions=legacy_permissions(artifact), artifact_ownership=ownership(artifact),
        destination=unknown(action_kind="unknown", selected_slot_index=None, explicit_slot_type_compatible=None,
            original_picker_called=False, effective_slot_index=None, replacing_artifact_id=None, replacing_artifact=ownership(None),
            method="source_bound_explicit_slot_branch_then_original_native_picker",
            effective_slot_script_permission_independently_observed=False),
        selected_artifact_matches_request=False, selected_action_effect_description=unknown(text=None),
        enshrine_disabled_tooltip=unknown(text=None), remove_disabled_tooltip=unknown(text=None),
        preview_identity_available=False, preview_identity_sha256=None,
        evaluation_context={"getter_backend": "unavailable", "native_getter_calls": 10000,
            "owner_thread_requirement": "existing_religion_owner_callback", "gameplay_command_submitted": False,
            "window_selection_written": False, "world_cache_written": False,
            "original_effect_description_evaluates_script_context": True, "script_rng_effects_verified": False, "script_rng_effects": "unknown"},
        action_ready=False, business_outcome_observed=False, beneficiaries_observed=False, beneficiaries=None)
    return result


class ExistingNormalizerSyntheticTests(unittest.TestCase):
    def test_legacy_packets_with_no_extension_remain_exactly_unchanged(self):
        for value, normalizer, args in ((legacy_context(), normalize_context, {}), (legacy_action(), normalize_action, {"artifact_id": 237})):
            with self.subTest(normalizer=normalizer.__name__):
                before = deepcopy(value)
                actual = normalizer(value, snapshot=frame(), holy_site_id=SITE, **args)
                self.assertEqual(actual, before)
                self.assertEqual(value, before)
                self.assertNotIn("recognition_matrix", actual)

    def test_both_existing_normalizers_attach_only_the_optional_field(self):
        for value, normalizer, args, extra in ((legacy_context(), normalize_context, {}, matrix()),
                (legacy_action(), normalize_action, {"artifact_id": 237}, matrix(requested=237))):
            with self.subTest(normalizer=normalizer.__name__):
                value["recognition_matrix"] = extra
                before = deepcopy(value)
                actual = normalizer(value, snapshot=frame(), holy_site_id=SITE, **args)
                self.assertEqual(actual, before)
                self.assertEqual(value, before)
                value["recognition_matrix"]["capture_epoch"] += 1
                with self.assertRaises(ValueError):
                    normalizer(value, snapshot=frame(), holy_site_id=SITE, **args)

    def test_explicit_null_compatibility_and_unknown_action_fields(self):
        for value, normalizer, args in ((legacy_context(), normalize_context, {}), (legacy_action(), normalize_action, {"artifact_id": 237})):
            value.update(available=False, unavailable_reason="synthetic_site_unavailable", recognition_matrix=None)
            self.assertIsNone(normalizer(value, snapshot=frame(), holy_site_id=SITE, **args)["recognition_matrix"])
        value = legacy_action()
        value["unrelated_new_field"] = None
        with self.assertRaises(ValueError):
            normalize_action(value, snapshot=frame(), holy_site_id=SITE, artifact_id=237)

    def test_legacy_preview_canonical_and_hash_do_not_include_matrix(self):
        value = legacy_action()
        canonical = relic_action_preview_canonical_v1(value)
        digest = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        value["recognition_matrix"] = matrix(requested=237)
        self.assertEqual(relic_action_preview_canonical_v1(value), canonical)
        value["recognition_matrix"] = invalidate(matrix(requested=237))
        self.assertEqual(hashlib.sha256(relic_action_preview_canonical_v1(value).encode('utf-8')).hexdigest(), digest)
        relative = 'ck3_autonomous_player/src/xar_autoplayer/bridge/player_holy_site_relic_action_context_private_transport.py'
        def canonical_node(path):
            return next(node for node in ast.parse(path.read_text(encoding='utf-8-sig')).body
                if isinstance(node, ast.FunctionDef) and node.name == 'relic_action_preview_canonical_v1')
        self.assertEqual(ast.dump(canonical_node(BASE / relative), include_attributes=False),
                         ast.dump(canonical_node(REPO / relative), include_attributes=False))


if __name__ == '__main__':
    unittest.main()

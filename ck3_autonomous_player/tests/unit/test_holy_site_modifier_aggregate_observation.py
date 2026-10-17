"""SYNTHETIC pure-Python aggregate DTO tests; no native build or live qualification.

Imports shared synthetic legacy context construction only. It never runs the
older recognition-matrix suite, native fixtures, engine functions or MCP I/O.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_holy_site_relic_recognition_matrix import (
    ACTOR, DATE, EPOCH, SITE, frame, legacy_context, matrix,
    normalize_context, parent,
)
from xar_autoplayer.bridge.holy_site_modifier_aggregate_observation import (
    LIMITS, normalize_holy_site_modifier_aggregate_v1 as normalize,
)


def aggregate(*, holder=419, faith_keys=None, local_keys=None):
    """Synthetic keys intentionally have no claimed property names or effects."""
    faith_keys = [7, 7, 0xFFFF, 9] if faith_keys is None else faith_keys
    local_keys = [9, 4] if local_keys is None else local_keys
    keys = list(dict.fromkeys(key for key in [*faith_keys, *local_keys] if key != 0xFFFF))
    ids = list(dict.fromkeys(item for item in (ACTOR, holder) if item is not None))
    blocks = [{"kind": kind, "available": True, "count_raw": len(rows), "entries": [
        {"key_raw_u16": key, "definition_raw_q64": (-100000, 0, 10, 2**63 - 1)[index % 4], "property_name": None}
        for index, key in enumerate(rows)], "unavailable_reason": None}
        for kind, rows in (("faith_fixed", faith_keys), ("local_fixed", local_keys))]
    recipients = [{"character_id": identity, "source_player": identity == ACTOR,
        "source_county_holder": identity == holder, "rite_id": 15, "faith_id": 50,
        "available": True, "owned_aggregate_observed": True, "values": [
            {"key_raw_u16": key, "available": True, "aggregate_raw_q64": (0, -(2**63), 2**63 - 1)[index % 3],
             "unavailable_reason": None} for index, key in enumerate(keys)], "unavailable_reason": None} for identity in ids]
    return {"schema": "ck3_12004_holy_site_modifier_aggregate_v1", "available": True,
        "complete": holder is not None, "source_arrays_stable": True, "capture_epoch": EPOCH,
        "date_raw": DATE, "played_character_id": ACTOR, "holy_site_id": SITE,
        "county_holder_character_id": holder, "definition_blocks": blocks, "recipients": recipients,
        "read_only": True, "native_functions_called": False, "evaluation_atomic": False,
        "names_bound": False, "site_attribution_observed": False, "scaled_effects_observed": False,
        "limits": dict(LIMITS), "unavailable_reason": None if holder is not None else "synthetic_county_holder_unavailable"}


def unknown_recipient(value, *, index=0, owned=False, reason="actual_owned_character_aggregate_unavailable"):
    value.update(complete=False, unavailable_reason="synthetic_partial_recipient")
    row = value["recipients"][index]
    row.update(available=False, owned_aggregate_observed=owned, unavailable_reason=reason)
    for entry in row["values"]:
        entry.update(available=False, aggregate_raw_q64=None, unavailable_reason=reason)
    return value


def invalidate(value, *, reason="modifier_aggregate_sources_changed_during_copy"):
    value.update(available=False, complete=False, source_arrays_stable=False, unavailable_reason=reason)
    for block in value["definition_blocks"]:
        block.update(available=False, entries=[], unavailable_reason=reason)
    for row in value["recipients"]:
        row.update(available=False, owned_aggregate_observed=False, values=[], unavailable_reason=reason)
    return value


class AggregateSyntheticTests(unittest.TestCase):
    def accepted(self, value, *, owner=None):
        original = deepcopy(value)
        actual = normalize(value, parent=owner or parent(), holy_site_id=SITE)
        self.assertEqual(actual, original)
        self.assertEqual(value, original)
        return actual

    def rejected(self, value, *, owner=None):
        original = deepcopy(value)
        with self.assertRaises(ValueError):
            normalize(value, parent=owner or parent(), holy_site_id=SITE)
        self.assertEqual(value, original)

    def test_original_definition_duplicates_sentinel_signed_raw_and_union_grid(self):
        value = aggregate()
        actual = self.accepted(value)
        self.assertEqual([row["key_raw_u16"] for row in actual["definition_blocks"][0]["entries"]], [7, 7, 0xFFFF, 9])
        self.assertEqual([row["key_raw_u16"] for row in actual["recipients"][0]["values"]], [7, 9, 4])
        self.assertEqual(actual["recipients"][0]["values"][0]["aggregate_raw_q64"], 0)
        actual["definition_blocks"][0]["entries"].clear()
        self.assertNotEqual(value, actual)

    def test_player_then_actual_holder_and_same_full_reference_dedup(self):
        value = aggregate(holder=ACTOR)
        self.accepted(value)
        self.assertEqual(len(value["recipients"]), 1)
        self.assertTrue(value["recipients"][0]["source_player"])
        self.assertTrue(value["recipients"][0]["source_county_holder"])
        self.accepted(aggregate(holder=0x10000001))
        value = aggregate()
        value["recipients"].reverse()
        self.rejected(value)

    def test_missing_county_holder_stays_partial_even_if_player_owned(self):
        value = aggregate(holder=None)
        self.accepted(value)
        value.update(complete=True, unavailable_reason=None)
        self.rejected(value)

    def test_owned_key_copy_failure_keeps_owned_fact_but_all_values_unknown(self):
        value = unknown_recipient(aggregate(), owned=True, reason="actual_owned_character_aggregate_key_unavailable")
        self.accepted(value)
        self.assertTrue(value["recipients"][0]["owned_aggregate_observed"])
        value["recipients"][0]["values"][0].update(available=True, aggregate_raw_q64=0, unavailable_reason=None)
        self.rejected(value)

    def test_default_fallback_cannot_claim_owned_cache_or_observed_zero(self):
        value = unknown_recipient(aggregate())
        self.accepted(value)
        value["recipients"][0]["owned_aggregate_observed"] = True
        self.rejected(value)
        value["recipients"][0]["owned_aggregate_observed"] = False
        value["recipients"][0]["values"][0]["aggregate_raw_q64"] = 0
        self.rejected(value)

    def test_unavailable_value_cannot_mix_with_an_available_recipient(self):
        value = aggregate()
        value["recipients"][0]["values"][0].update(available=False, aggregate_raw_q64=None, unavailable_reason="synthetic_copy_failure")
        self.rejected(value)

    def test_drift_clears_both_blocks_and_all_recipient_value_and_owned_claims(self):
        value = invalidate(aggregate())
        self.accepted(value)
        value["recipients"][0]["values"] = [{"key_raw_u16": 7, "available": False,
            "aggregate_raw_q64": None, "unavailable_reason": "synthetic_drift"}]
        self.rejected(value)
        value["recipients"][0]["values"] = []
        value["recipients"][0]["owned_aggregate_observed"] = True
        self.rejected(value)

    def test_partial_fixed_pc_failure_invalidates_all_other_blocks_before_totals(self):
        value = aggregate()
        value["definition_blocks"][1].update(available=False, entries=[], unavailable_reason="synthetic_pc_unread")
        self.rejected(value)
        value = invalidate(aggregate())
        value["definition_blocks"][1]["count_raw"] = None
        self.accepted(value)

    def test_pc_entry_cap_and_negative_count_remain_explicit_raw_diagnostics(self):
        for count in (33, -1, 2**31 - 1):
            value = aggregate()
            value["definition_blocks"][0]["count_raw"] = count
            with self.subTest(count=count):
                self.rejected(value)
                invalidate(value, reason="modifier_aggregate_fixed_pc_unavailable_or_over_limit")
                self.accepted(value)
                self.assertEqual(value["definition_blocks"][0]["count_raw"], count)

    def test_exact_32_each_and_64_unique_keys_are_retained_without_names(self):
        value = aggregate(faith_keys=list(range(32)), local_keys=list(range(32, 64)))
        self.accepted(value)
        self.assertEqual(len(value["recipients"][0]["values"]), 64)
        value = aggregate(faith_keys=list(range(33)), local_keys=[])
        self.rejected(value)

    def test_initial_failure_keeps_two_block_kinds_and_may_have_no_recipients(self):
        value = invalidate(aggregate(), reason="modifier_aggregate_current_player_context_unavailable")
        value["recipients"] = []
        for block in value["definition_blocks"]:
            block["count_raw"] = None
        self.accepted(value)
        value["definition_blocks"].pop()
        self.rejected(value)

    def test_empty_or_all_sentinel_pc_still_needs_actual_owned_recipients(self):
        self.accepted(aggregate(faith_keys=[], local_keys=[]))
        self.accepted(aggregate(faith_keys=[0xFFFF], local_keys=[0xFFFF]))
        self.accepted(unknown_recipient(aggregate(faith_keys=[], local_keys=[])))

    def test_changed_site_frame_actor_holder_provenance_or_key_grid_is_rejected(self):
        mutations = (
            lambda value: value.update(holy_site_id=SITE + 1), lambda value: value.update(capture_epoch=EPOCH + 1),
            lambda value: value.update(date_raw=DATE + 1), lambda value: value.update(played_character_id=ACTOR + 1),
            lambda value: value["recipients"][1].update(character_id=420),
            lambda value: value["recipients"][0].update(source_county_holder=True),
            lambda value: value["recipients"][0]["values"].reverse(),
            lambda value: value["recipients"][0]["values"][0].update(key_raw_u16=0xFFFF),
        )
        for mutate in mutations:
            value = aggregate()
            mutate(value)
            with self.subTest(mutate=mutate):
                self.rejected(value)

    def test_property_name_effects_attribution_native_calls_and_new_semantics_are_rejected(self):
        for key in ("names_bound", "site_attribution_observed", "scaled_effects_observed", "native_functions_called", "evaluation_atomic"):
            value = aggregate()
            value[key] = True
            with self.subTest(key=key):
                self.rejected(value)
        value = aggregate()
        value["definition_blocks"][0]["entries"][0]["property_name"] = "diplomacy"
        self.rejected(value)
        value = aggregate()
        value["beneficiaries"] = []
        self.rejected(value)

    def test_bool_ids_counts_keys_and_out_of_range_q64_are_rejected(self):
        mutations = (
            lambda value: value.update(available=1), lambda value: value.update(county_holder_character_id=True),
            lambda value: value["definition_blocks"][0].update(count_raw=True),
            lambda value: value["definition_blocks"][0]["entries"][0].update(key_raw_u16=True),
            lambda value: value["definition_blocks"][0]["entries"][0].update(key_raw_u16=65536),
            lambda value: value["definition_blocks"][0]["entries"][0].update(definition_raw_q64=2**63),
            lambda value: value["recipients"][0]["values"][0].update(aggregate_raw_q64=-(2**63) - 1),
            lambda value: value["recipients"][0].update(rite_id=0xFFFFFFFF),
            lambda value: value["limits"].update(unique_keys=65),
        )
        for mutate in mutations:
            value = aggregate()
            mutate(value)
            with self.subTest(mutate=mutate):
                self.rejected(value)

    def test_incomplete_shape_or_missing_reason_cannot_become_available(self):
        value = aggregate()
        value["definition_blocks"][0]["count_raw"] = 1
        self.rejected(value)
        value = unknown_recipient(aggregate())
        value["recipients"][0]["unavailable_reason"] = None
        self.rejected(value)
        value = aggregate()
        value.update(complete=True, unavailable_reason="synthetic_partial")
        self.rejected(value)


class ExistingContextSyntheticTests(unittest.TestCase):
    def test_legacy_absent_extension_remains_byte_equivalent_structure(self):
        value = legacy_context()
        self.assertEqual(normalize_context(value, snapshot=frame(), holy_site_id=SITE), value)
        self.assertNotIn("modifier_aggregate_observation", value)

    def test_present_aggregate_attaches_without_changing_existing_context_fields(self):
        value = legacy_context()
        value["modifier_aggregate_observation"] = aggregate()
        before = deepcopy(value)
        self.assertEqual(normalize_context(value, snapshot=frame(), holy_site_id=SITE), before)
        self.assertEqual(value, before)
        value["modifier_aggregate_observation"]["date_raw"] += 1
        with self.assertRaises(ValueError):
            normalize_context(value, snapshot=frame(), holy_site_id=SITE)

    def test_aggregate_and_recognition_are_independent_optional_observations(self):
        value = legacy_context()
        value.update(recognition_matrix=matrix(), modifier_aggregate_observation=aggregate())
        before = deepcopy(value)
        self.assertEqual(normalize_context(value, snapshot=frame(), holy_site_id=SITE), before)
        self.assertFalse(value["modifier_aggregate_observation"]["site_attribution_observed"])
        self.assertFalse(value["recognition_matrix"]["benefits_observed"])

    def test_explicit_null_only_with_unavailable_parent_and_legacy_absence_remains_absent(self):
        value = legacy_context()
        value["modifier_aggregate_observation"] = None
        with self.assertRaises(ValueError):
            normalize_context(value, snapshot=frame(), holy_site_id=SITE)
        value.update(available=False, unavailable_reason="synthetic_site_unavailable")
        self.assertIsNone(normalize_context(value, snapshot=frame(), holy_site_id=SITE)["modifier_aggregate_observation"])
        del value["modifier_aggregate_observation"]
        self.assertNotIn("modifier_aggregate_observation", normalize_context(value, snapshot=frame(), holy_site_id=SITE))


if __name__ == '__main__':
    unittest.main()

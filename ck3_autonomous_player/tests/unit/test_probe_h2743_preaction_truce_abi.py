"""Disk-only H2743 truce ABI projection and false poststate gates."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "native_bridge" / "research"))

from probe_h2743_preaction_truce_abi import project_probe


ABI = (ROOT / "native_bridge" / "research" /
       "g2_actual_truce_expiry_v1_abi.json")


def frozen_abi() -> dict:
    return json.loads(ABI.read_text(encoding="utf-8"))


class H2743PreactionTruceAbiProbeTests(unittest.TestCase):
    def test_exact_frozen_abi_keeps_both_expiry_fields_unknown(self) -> None:
        result = project_probe(frozen_abi())
        self.assertEqual(result["status"], "static_abi_candidate_only")
        self.assertEqual((result["owner_character_id"],
                          result["toward_character_id"]), (30097, 29829))
        self.assertEqual(result["target_frame_claim"], {
            "snapshot_id": "native:3", "public_revision": 4,
            "native_revision": 3, "date_raw": 53217264,
            "connection_generation": 1,
        })
        self.assertEqual(result["read_only_native_call_rvas"], {
            "has_truce": "0x26631E0",
            "get_truce_end_date": "0x2663250",
            "relation_lookup": "0x2610840",
        })
        self.assertEqual(result["forbidden_query_call_rvas"], {
            "relation_get_or_create": "0x26108F0",
            "caddtruce_duration_evaluator": "0x3373000",
        })
        for key in ("preaction_existing_truce_expiry_date_raw",
                    "post_surrender_actual_expiry_date_raw",
                    "script_candidate_days", "recommended_outcome", "action_literal"):
            self.assertIsNone(result[key], key)
        self.assertFalse(result["exe_bytes_authenticated_here"])
        self.assertFalse(result["checkpoint_bytes_authenticated_here"])
        self.assertFalse(result["native_call_edges_authenticated_here"])
        self.assertFalse(result["effect_projection_complete"])
        self.assertFalse(result["material_complete"])

    def test_direction_and_unobserved_values_cannot_be_relabelled(self) -> None:
        bad_options = (
            {"owner_character_id": 29829, "toward_character_id": 30097},
            {"owner_character_id": 30097, "toward_character_id": 30097},
            {"claimed_existing_expiry_date_raw": 53219000},
            {"claimed_post_surrender_expiry_date_raw": 53219000},
            {"claimed_post_surrender_expiry_date_raw": 0},
        )
        for options in bad_options:
            with self.subTest(options=options), self.assertRaises(ValueError):
                project_probe(frozen_abi(), **options)

    def test_wrong_exe_or_bounded_native_range_rejected(self) -> None:
        mutations = (
            lambda x: x["build"].update(executable_sha256="0" * 64),
            lambda x: x["native_ranges"]["get_truce_end_date"].update(
                sha256="0" * 64),
            lambda x: x["native_ranges"]["caddtruce_normal"].update(
                begin_rva="0x2EDAD21"),
            lambda x: x["bindings"].update(
                read_only_relation_lookup_rva="0x26108F0"),
        )
        for mutate in mutations:
            value = deepcopy(frozen_abi())
            mutate(value)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                project_probe(value)

    def test_played_owner_reader_cannot_masquerade_as_arbitrary_owner(self) -> None:
        mutations = (
            lambda x: x["candidate"].update(owner_arbitrary_selection=True),
            lambda x: x["candidate"].update(owner_binding="arbitrary character"),
            lambda x: x["source_sha256"].update(
                {"src/raiktor_actual_truce_expiry_v1.cpp": "0" * 64}),
            lambda x: x.update(default_enabled=True),
        )
        for mutate in mutations:
            value = deepcopy(frozen_abi())
            mutate(value)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                project_probe(value)

    def test_temporal_boundary_or_status_drift_rejected(self) -> None:
        mutations = (
            lambda x: x["temporal_split"].update(before_application="observed"),
            lambda x: x["temporal_split"].update(after_application="predicted"),
            lambda x: x.update(status="live-ready"),
            lambda x: x.update(read_only=False),
        )
        for mutate in mutations:
            value = deepcopy(frozen_abi())
            mutate(value)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                project_probe(value)


if __name__ == "__main__":
    unittest.main()

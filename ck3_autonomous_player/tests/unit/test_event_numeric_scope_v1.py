from __future__ import annotations

import copy
import unittest

from xar_autoplayer.bridge.event_window_context_contract import (
    _EVENT_PROVENANCE_BY_BACKEND,
    _event_scope,
    normalize_current_event_window_context_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002, CK3_12003
from test_event_window_context_v1_bridge import (
    DATE_RAW, EVENT_ID, NATIVE_REVISION, _frame,
)


def numeric_scope(raw: str, decimal: str, integer: str | None) -> dict:
    return {
        "status": "available", "raw_type_index": 1, "type_key": "value",
        "subtype": 0,
        "typed_identity": {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        },
        "numeric_value": {
            "raw_fixed_point": raw, "scale": 100000,
            "decimal_value": decimal, "integer_value": integer,
        },
    }


class EventNumericScopeContractTests(unittest.TestCase):
    def check_scope(self, scope):
        _event_scope(scope, "numeric fixture", allow_numeric_value=True)

    def test_exact_signed_fixedpoint_and_fractional_null_integer(self):
        for raw, decimal, integer in (
            ("0", "0", "0"), ("12300000", "123", "123"),
            ("-100000", "-1", "-1"), ("-1", "-0.00001", None),
            ("100001", "1.00001", None),
            ("-9223372036854775808", "-92233720368547.75808", None),
            ("9223372036854775807", "92233720368547.75807", None),
        ):
            with self.subTest(raw=raw):
                self.check_scope(numeric_scope(raw, decimal, integer))

    def test_missing_native_field_is_not_numeric_zero(self):
        scope = numeric_scope("0", "0", "0")
        del scope["numeric_value"]
        self.check_scope(scope)
        self.assertNotIn("numeric_value", scope)
        scope["numeric_value"] = None
        with self.assertRaises(ValueError):
            self.check_scope(scope)

    def test_kind_key_subtype_and_build_are_strict(self):
        for field, value in (("raw_type_index", 4), ("type_key", "character"),
                             ("subtype", 1)):
            with self.subTest(field=field):
                scope = numeric_scope("0", "0", "0")
                scope[field] = value
                with self.assertRaises(ValueError):
                    self.check_scope(scope)
        with self.assertRaises(ValueError):
            _event_scope(numeric_scope("0", "0", "0"), "legacy fixture")

    def test_noncanonical_or_out_of_range_raw_rejected(self):
        for raw in (0, True, "", "+0", "-0", "00", " 0", "1.0",
                    "9223372036854775808", "-9223372036854775809"):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    self.check_scope(numeric_scope(raw, "0", "0"))

    def test_closed_fields_and_exact_derived_projection(self):
        mutations = (
            ("scale", 1), ("scale", True), ("raw_fixed_point", None),
            ("decimal_value", "0.0"), ("decimal_value", 0),
            ("integer_value", None), ("integer_value", 0),
            ("expected_serial", "0"),
        )
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                scope = numeric_scope("0", "0", "0")
                scope["numeric_value"][key] = value
                with self.assertRaises(ValueError):
                    self.check_scope(scope)
        fractional = numeric_scope("100001", "1.00001", "1")
        with self.assertRaises(ValueError):
            self.check_scope(fractional)
        scope = numeric_scope("0", "0", "0")
        del scope["numeric_value"]["scale"]
        with self.assertRaises(ValueError):
            self.check_scope(scope)

    def test_numeric_value_never_claims_object_identity(self):
        scope = numeric_scope("0", "0", "0")
        scope["typed_identity"] = {
            "status": "available", "kind": "character", "character_id": 42,
        }
        with self.assertRaises(ValueError):
            self.check_scope(scope)

    def patch3_frame(self):
        frame = _frame()
        frame["provenance"] = copy.deepcopy(
            _EVENT_PROVENANCE_BY_BACKEND[CK3_12003.backend_id("event-window-v1")]
        )
        for option in frame["options"]:
            option["effect_indicators"]["coverage"] = (
                "played-character-event-icon-indicators-1.20.0.3-v1"
            )
        frame["saved_scopes"] = [{
            "name": "lyd_i3b_event_serial", "name_identifier": 15696,
            "scope": numeric_scope("12300000", "123", "123"),
        }]
        return frame

    def normalize(self, frame):
        return normalize_current_event_window_context_v1(
            frame, expected_event_instance_id=EVENT_ID,
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )

    def test_full_frame_preserves_detached_numeric_leaf(self):
        frame = self.patch3_frame()
        result = self.normalize(frame)
        self.assertEqual(result["saved_scopes"], frame["saved_scopes"])
        frame["saved_scopes"][0]["scope"]["numeric_value"]["raw_fixed_point"] = "0"
        self.assertEqual(result["saved_scopes"][0]["scope"]["numeric_value"]["raw_fixed_point"], "12300000")

    def test_full_frame_rejects_duplicate_stale_and_wrong_build(self):
        frame = self.patch3_frame()
        duplicate = copy.deepcopy(frame)
        duplicate["saved_scopes"].append(copy.deepcopy(duplicate["saved_scopes"][0]))
        stale = copy.deepcopy(frame)
        stale["snapshot_revision"] += 1
        legacy = copy.deepcopy(frame)
        legacy["provenance"] = copy.deepcopy(
            _EVENT_PROVENANCE_BY_BACKEND[CK3_12002.backend_id("event-window-v1")]
        )
        for bad in (duplicate, stale, legacy):
            with self.subTest(frame=bad):
                with self.assertRaises(ValueError):
                    self.normalize(bad)

    def test_legacy_patch3_receipt_retains_unknown(self):
        frame = self.patch3_frame()
        del frame["saved_scopes"][0]["scope"]["numeric_value"]
        result = self.normalize(frame)
        self.assertNotIn("numeric_value", result["saved_scopes"][0]["scope"])


if __name__ == "__main__":
    unittest.main()

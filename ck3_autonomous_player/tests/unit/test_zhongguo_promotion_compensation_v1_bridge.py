from __future__ import annotations

import json
from pathlib import Path
import unittest

import jsonschema
import pytest

from xar_autoplayer.bridge.zhongguo_promotion_compensation_postcondition_contract import (
    QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY,
    ZhongguoPromotionCompensationQueryV1,
    bind_promotion_compensation_event_snapshots_v1,
    normalize_native_zhongguo_promotion_compensation_v1,
    parse_query_zhongguo_promotion_compensation_v1_step,
    query_zhongguo_promotion_compensation_v1_step,
)


ROOT = Path(__file__).resolve().parents[3]


def _typed(value: int | bool) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def _identity() -> dict[str, object]:
    return {
        "owner_character_id": _typed(147),
        "subject_character_id": _typed(361),
        "cycle_serial": _typed(9),
        "case_serial": _typed(14),
        "revision": _typed(3),
    }


def _native_frame() -> dict[str, object]:
    readiness = {
        key: True
        for key in (
            "player_owner_binding_ready",
            "portfolio_subject_binding_ready",
            "source_identity_ready",
            "result_identity_ready",
            "frozen_case_identity_ready",
            "promotion_choice_receipt_ready",
            "compensation_receipt_posted",
            "same_case_identity_ready",
            "revision_binding_ready",
            "receipt_serials_ready",
            "same_frame_ready",
            "ready",
        )
    }
    return {
        "schema_version": 1,
        "status": "available",
        "capability": QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY,
        "source_backend_id": (
            "ck3-1.19.0.6-native-zhongguo-promotion-compensation-"
            "postcondition-v1"
        ),
        "request_nonce": "promo.14",
        "snapshot_revision": 51,
        "date_raw": 800,
        "paused": True,
        "player_character_id": 147,
        "subject_character_id": 361,
        "promotion_compensation": {
            "source_identity": _identity(),
            "result_identity": _identity(),
            "frozen_case": {"identity": _identity(), "frozen": True},
            "promotion_choice": {
                "identity": _identity(),
                "option_number": _typed(2),
                "receipt_serial": _typed(14),
                "active": _typed(True),
                "consumed": _typed(True),
            },
            "compensation_receipt": {
                "identity": _identity(),
                "operation_id": _typed(82),
                "option_number": _typed(2),
                "receipt_serial": _typed(14),
                "active": _typed(True),
                "consumed": _typed(True),
                "posted": _typed(True),
            },
        },
        "readiness": readiness,
        "unavailable_reason": None,
    }


def test_step_round_trip_and_malformed_prefix_fail_closed() -> None:
    step = query_zhongguo_promotion_compensation_v1_step(147, "promo.14")
    assert parse_query_zhongguo_promotion_compensation_v1_step(step) == (
        ZhongguoPromotionCompensationQueryV1(147, "promo.14")
    )
    assert parse_query_zhongguo_promotion_compensation_v1_step(
        step + "-extra"
    ) is None


def test_native_frame_normalizes_and_satisfies_json_schema() -> None:
    frame = _native_frame()
    query = ZhongguoPromotionCompensationQueryV1(147, "promo.14")
    normalized = normalize_native_zhongguo_promotion_compensation_v1(
        frame,
        expected_query=query,
        expected_snapshot_revision=51,
        expected_date_raw=800,
        expected_player_character_id=147,
    )
    schema = json.loads(
        (
            ROOT
            / "ck3_autonomous_player/schemas/zhongguo-promotion-"
            "compensation-postcondition-v1.schema.json"
        ).read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator(schema).validate(normalized)


def test_facade_binds_source_result_and_connection_generation() -> None:
    business = {
        **_native_frame(),
        "source_backend_id": "native-headless",
        "binding": {
            "connection_generation": 7,
            "snapshot_id": "result-51",
            "revision": 19,
            "native_revision": 51,
            "player_character_id": 147,
        },
    }
    source = {
        "binding": {
            "connection_generation": 7,
            "snapshot_id": "source-50",
            "revision": 18,
            "native_revision": 50,
        }
    }
    result = {
        "binding": {
            "connection_generation": 7,
            "snapshot_id": "result-51",
            "revision": 19,
            "native_revision": 51,
        }
    }
    bound = bind_promotion_compensation_event_snapshots_v1(
        business, source, result
    )
    assert bound["binding"]["source_snapshot_id"] == "source-50"
    assert bound["binding"]["result_native_revision"] == 51
    drifted = {"binding": {**result["binding"], "connection_generation": 8}}
    with pytest.raises(ValueError, match="generation drifted"):
        bind_promotion_compensation_event_snapshots_v1(
            business, source, drifted
        )


def test_default_adapter_does_not_advertise_before_paused_live() -> None:
    adapter = (
        ROOT
        / "ck3_autonomous_player/native_bridge/src/ck3_11906_adapter.cpp"
    ).read_text(encoding="utf-8")
    assert QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY not in adapter


class OptimizedContractTests(unittest.TestCase):
    """Keep the same boundary executable under ``python -O``."""

    def test_step_and_native_schema(self) -> None:
        step = query_zhongguo_promotion_compensation_v1_step(
            147, "promo.14"
        )
        self.assertEqual(
            parse_query_zhongguo_promotion_compensation_v1_step(step),
            ZhongguoPromotionCompensationQueryV1(147, "promo.14"),
        )
        frame = _native_frame()
        normalized = normalize_native_zhongguo_promotion_compensation_v1(
            frame,
            expected_query=ZhongguoPromotionCompensationQueryV1(
                147, "promo.14"
            ),
            expected_snapshot_revision=51,
            expected_date_raw=800,
            expected_player_character_id=147,
        )
        schema = json.loads(
            (
                ROOT
                / "ck3_autonomous_player/schemas/zhongguo-promotion-"
                "compensation-postcondition-v1.schema.json"
            ).read_text(encoding="utf-8")
        )
        jsonschema.Draft202012Validator(schema).validate(normalized)

    def test_facade_generation_and_default_off(self) -> None:
        business = {
            **_native_frame(),
            "binding": {
                "connection_generation": 7,
                "snapshot_id": "result-51",
                "revision": 19,
                "native_revision": 51,
                "player_character_id": 147,
            },
        }
        source = {
            "binding": {
                "connection_generation": 7,
                "snapshot_id": "source-50",
                "revision": 18,
                "native_revision": 50,
            }
        }
        result = {
            "binding": {
                "connection_generation": 7,
                "snapshot_id": "result-51",
                "revision": 19,
                "native_revision": 51,
            }
        }
        bound = bind_promotion_compensation_event_snapshots_v1(
            business, source, result
        )
        self.assertEqual(bound["binding"]["source_snapshot_id"], "source-50")
        adapter = (
            ROOT
            / "ck3_autonomous_player/native_bridge/src/ck3_11906_adapter.cpp"
        ).read_text(encoding="utf-8")
        self.assertNotIn(
            QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY, adapter
        )


if __name__ == "__main__":
    unittest.main()

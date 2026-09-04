from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "ck3_autonomous_player" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from xar_autoplayer.bridge.zhongguo_career_hc_workforce_postcondition_contract import (  # noqa: E402
    QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_CAPABILITY,
    ZHONGGUO_CAREER_HC_WORKFORCE_V1_BACKEND_ID,
    ZHONGGUO_CAREER_HC_WORKFORCE_V1_CASE_KIND,
    ZhongguoCareerHcWorkforceQueryV1,
    normalize_native_zhongguo_career_hc_workforce_v1,
    parse_query_zhongguo_career_hc_workforce_v1_step,
    query_zhongguo_career_hc_workforce_v1_step,
)


def typed(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def frame() -> dict[str, object]:
    identity = {
        "owner_character_id": typed(101),
        "subject_character_id": typed(202),
        "cycle_serial": typed(7),
        "case_serial": typed(7009),
    }
    return {
        "schema_version": 1,
        "status": "available",
        "capability": QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_CAPABILITY,
        "case_kind": ZHONGGUO_CAREER_HC_WORKFORCE_V1_CASE_KIND,
        "source_backend_id": ZHONGGUO_CAREER_HC_WORKFORCE_V1_BACKEND_ID,
        "request_nonce": "b6.route-b.post",
        "snapshot_revision": 88,
        "date_raw": 123456,
        "paused": True,
        "player_character_id": 202,
        "subject_character_id": 202,
        "requested_owner_character_id": 101,
        "m360_identity": copy.deepcopy(identity),
        "m360_receipt": {
            **copy.deepcopy(identity),
            "state": typed(4),
            "choice": typed(2),
            "provider_observed": True,
        },
        "career_hc_partition": {
            "authorized": typed(8),
            "available": typed(2),
            "reserved": typed(1),
            "occupied": typed(3),
            "frozen": typed(1),
            "reclaimed": typed(1),
            "conserved": typed(True),
            "provider_observed": True,
        },
        "route_b_cost": {
            "manager_cost_total": typed(0),
            "provider_observed": True,
        },
        "readiness": {
            "player_subject_binding_ready": True,
            "owner_binding_ready": True,
            "m360_identity_ready": True,
            "m360_route_b_receipt_ready": True,
            "career_hc_partition_ready": True,
            "career_hc_conservation_ready": True,
            "route_b_manager_cost_zero_ready": True,
            "same_frame_ready": True,
            "ready": True,
        },
        "unavailable_reason": None,
    }


def normalize(value: object) -> dict[str, object]:
    return normalize_native_zhongguo_career_hc_workforce_v1(
        value,
        expected_query=ZhongguoCareerHcWorkforceQueryV1(101, "b6.route-b.post"),
        expected_snapshot_revision=88,
        expected_date_raw=123456,
        expected_player_character_id=202,
    )


class CareerHcWorkforcePostconditionContractTests(unittest.TestCase):
    def test_query_step_round_trip_is_closed(self) -> None:
        step = query_zhongguo_career_hc_workforce_v1_step(
            101, "b6.route-b.post"
        )
        self.assertEqual(
            parse_query_zhongguo_career_hc_workforce_v1_step(step),
            ZhongguoCareerHcWorkforceQueryV1(101, "b6.route-b.post"),
        )
        self.assertIsNone(
            parse_query_zhongguo_career_hc_workforce_v1_step(step + "-extra")
        )
        with self.assertRaises(ValueError):
            query_zhongguo_career_hc_workforce_v1_step(101, "bad nonce")

    def test_available_frame_requires_provider_observed_route_b_and_hc(self) -> None:
        result = normalize(frame())
        self.assertEqual(result["status"], "available")
        self.assertTrue(result["m360_receipt"]["provider_observed"])
        self.assertTrue(result["career_hc_partition"]["provider_observed"])

    def test_wrong_case_identity_is_rejected(self) -> None:
        value = frame()
        value["m360_receipt"]["case_serial"] = typed(7010)
        with self.assertRaisesRegex(ValueError, "identity and receipt disagree"):
            normalize(value)

    def test_ack_shaped_or_unobserved_receipt_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly the v1 fields"):
            normalize({"accepted": True, "status": "submitted"})
        value = frame()
        value["m360_receipt"]["provider_observed"] = False
        with self.assertRaisesRegex(ValueError, "not fully provider observed"):
            normalize(value)

    def test_non_route_b_receipt_is_rejected(self) -> None:
        value = frame()
        value["m360_receipt"]["choice"] = typed(1)
        with self.assertRaisesRegex(ValueError, "requested route-B"):
            normalize(value)

    def test_hc_conservation_or_nonzero_cost_is_rejected(self) -> None:
        value = frame()
        value["career_hc_partition"]["available"] = typed(1)
        with self.assertRaisesRegex(ValueError, "conservation is not GREEN"):
            normalize(value)
        value = frame()
        value["route_b_cost"]["manager_cost_total"] = typed(1)
        with self.assertRaisesRegex(ValueError, "conservation is not GREEN"):
            normalize(value)

    def test_source_contract_keeps_native_wiring_and_live_evidence_pending(self) -> None:
        path = (
            ROOT
            / "ck3_autonomous_player"
            / "native_bridge"
            / "research"
            / "fixtures"
            / "zhongguo_career_hc_workforce_postcondition_v1_source_contract.json"
        )
        contract = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            contract["readiness"], "static_and_fixture_ready_live_pending"
        )
        self.assertEqual(contract["integration"]["native_provider_wiring"], "pending")
        self.assertFalse(contract["integration"]["formal_runner_registry_modified"])


if __name__ == "__main__":
    unittest.main()

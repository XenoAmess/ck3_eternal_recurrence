from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUTOPLAYER_SRC = ROOT / "ck3_autonomous_player" / "src"
for item in (ROOT / "tools", AUTOPLAYER_SRC):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

from preflight_zg361_phase2_hc_workforce_b6 import run_preflight  # noqa: E402
from xar_autoplayer.bridge.zhongguo_career_hc_workforce_postcondition_contract import (  # noqa: E402
    QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_CAPABILITY,
)
from zg361_phase2_hc_workforce_b6_action_cell import (  # noqa: E402
    B6CareerHcWorkforceActionCellError,
    run_b6_career_hc_workforce_gameplay_action_cell,
)


def typed(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def provider_frame() -> dict[str, object]:
    identity = {
        "owner_character_id": typed(101),
        "subject_character_id": typed(202),
        "cycle_serial": typed(7),
        "case_serial": typed(7009),
    }
    return {
        "status": "available",
        "unavailable_reason": None,
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
        "readiness": {"ready": True},
    }


def ack() -> dict[str, object]:
    return {
        "result": "ACKED",
        "business_receipt_claimed": False,
        "binding": {
            "route": "B",
            "option_number": 2,
            "owner_character_id": 101,
            "subject_character_id": 202,
            "date_raw": 123456,
        },
    }


class FakeSubjectService:
    def __init__(
        self,
        response: dict[str, object] | None = None,
        *,
        capability: bool = True,
        date_raw: int = 123456,
    ) -> None:
        self.response = copy.deepcopy(response or provider_frame())
        self.capability = capability
        self.date_raw = date_raw
        self.queries: list[tuple[str, int, int]] = []

    def capabilities(self) -> dict[str, object]:
        return {
            "bridge_capabilities": (
                [QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_CAPABILITY]
                if self.capability
                else []
            )
        }

    def snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": "b6-subject-post",
            "revision": 88,
            "native_revision": 87,
            "date_raw": self.date_raw,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 202},
        }

    def query_zhongguo_career_hc_workforce_postcondition_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        self.queries.append((request_nonce, expected_revision, owner_character_id))
        return copy.deepcopy(self.response)


def action_executor(_service: object, *, route: str) -> dict[str, object]:
    if route != "B":
        raise AssertionError("B6 must select only route B")
    return ack()


class CareerHcWorkforceB6ActionCellTests(unittest.TestCase):
    def test_green_requires_action_then_subject_provider_result(self) -> None:
        subject = FakeSubjectService()
        result = run_b6_career_hc_workforce_gameplay_action_cell(
            object(),
            subject_service_factory=lambda _binding: subject,
            action_executor=action_executor,
        )
        self.assertEqual(result["result"], "GREEN")
        self.assertTrue(result["gameplay_action_executed"])
        self.assertTrue(result["provider_postcondition_observed"])
        self.assertFalse(result["action_ack_is_business_postcondition"])
        self.assertFalse(result["fixture_evidence_is_live"])
        self.assertEqual(
            subject.queries,
            [("zg361.p2.hc-workforce.b6.post", 88, 101)],
        )

    def test_ack_without_subject_provider_is_red(self) -> None:
        with self.assertRaises(B6CareerHcWorkforceActionCellError) as caught:
            run_b6_career_hc_workforce_gameplay_action_cell(
                object(),
                subject_service_factory=None,
                action_executor=action_executor,
            )
        self.assertEqual(caught.exception.reason_code, "subject_provider_session_required")
        self.assertFalse(caught.exception.evidence["provider_postcondition_observed"])

    def test_unadvertised_provider_is_red(self) -> None:
        with self.assertRaises(B6CareerHcWorkforceActionCellError) as caught:
            run_b6_career_hc_workforce_gameplay_action_cell(
                object(),
                subject_service_factory=lambda _binding: FakeSubjectService(
                    capability=False
                ),
                action_executor=action_executor,
            )
        self.assertEqual(
            caught.exception.reason_code, "career_hc_workforce_provider_unavailable"
        )

    def test_wrong_case_identity_is_red(self) -> None:
        response = provider_frame()
        response["m360_receipt"]["case_serial"] = typed(7010)
        with self.assertRaises(B6CareerHcWorkforceActionCellError) as caught:
            run_b6_career_hc_workforce_gameplay_action_cell(
                object(),
                subject_service_factory=lambda _binding: FakeSubjectService(response),
                action_executor=action_executor,
            )
        self.assertEqual(
            caught.exception.reason_code,
            "career_hc_workforce_postcondition_not_green",
        )

    def test_unconserved_partition_or_nonzero_route_cost_is_red(self) -> None:
        for mutate in (
            lambda value: value["career_hc_partition"].__setitem__(
                "available", typed(1)
            ),
            lambda value: value["route_b_cost"].__setitem__(
                "manager_cost_total", typed(1)
            ),
        ):
            response = provider_frame()
            mutate(response)
            with self.subTest(response=response):
                with self.assertRaises(B6CareerHcWorkforceActionCellError):
                    run_b6_career_hc_workforce_gameplay_action_cell(
                        object(),
                        subject_service_factory=lambda _binding, response=response: (
                            FakeSubjectService(response)
                        ),
                        action_executor=action_executor,
                    )

    def test_unobserved_receipt_is_red(self) -> None:
        response = provider_frame()
        response["m360_receipt"]["provider_observed"] = False
        with self.assertRaises(B6CareerHcWorkforceActionCellError):
            run_b6_career_hc_workforce_gameplay_action_cell(
                object(),
                subject_service_factory=lambda _binding: FakeSubjectService(response),
                action_executor=action_executor,
            )

    def test_subject_rebind_must_not_advance_date(self) -> None:
        with self.assertRaises(B6CareerHcWorkforceActionCellError) as caught:
            run_b6_career_hc_workforce_gameplay_action_cell(
                object(),
                subject_service_factory=lambda _binding: FakeSubjectService(
                    date_raw=123457
                ),
                action_executor=action_executor,
            )
        self.assertEqual(caught.exception.reason_code, "subject_provider_binding_drifted")

    def test_no_launch_preflight_is_green_but_live_pending(self) -> None:
        result = run_preflight()
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(result["readiness"], "static-ready-live-pending")
        self.assertFalse(result["ck3_started"])
        self.assertFalse(result["provider_live_result_claimed"])
        self.assertEqual(
            result["career_hc_effect_shards"]["maximum_effects_per_file"], 10
        )


if __name__ == "__main__":
    unittest.main()

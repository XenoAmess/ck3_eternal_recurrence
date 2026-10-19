"""Offline orchestration checks; fakes do not claim current Native acceptance."""
from copy import deepcopy
import json
import unittest

from test_campaign_score_existing_inputs_v1 import cash_inputs, root_inputs
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.campaign_score_cadence_v1 import date_to_raw
from xar_autoplayer.campaign_score_monthly_met_v1 import collect_monthly_met_candidate_v1


ANCHOR = {"campaign_id": "synthetic-post-auto", "founder_character_id": 12345,
          "founding_house_id": 174, "founding_dynasty_id": 174}


def inputs():
    snapshot, _, root = root_inputs()
    snapshot.update(snapshot_id="synthetic-post-auto-month-001", revision=635,
                    native_revision=737, date_raw=date_to_raw("1066.10.15"))
    snapshot["active_wars"] = []
    root["binding"].update({key: snapshot[key] for key in (
        "snapshot_id", "revision", "native_revision", "date_raw")})
    root["binding"]["expected_revision"] = snapshot["revision"]
    root["campaign_root_context"].update(snapshot_revision=snapshot["native_revision"],
                                         date_raw=snapshot["date_raw"])
    _, _, cash = cash_inputs()
    actor = snapshot["played_character"]["character_id"]
    cash.update(played_character_id=actor, snapshot_revision=snapshot["native_revision"],
                date_raw=snapshot["date_raw"], queried_snapshot_id=snapshot["snapshot_id"],
                queried_revision=snapshot["revision"], queried_native_revision=snapshot["native_revision"],
                current_treasury=deepcopy(snapshot["played_character_gold"]))
    for row in cash["military_expenses"].values():
        row.update(owner_character_id=actor, resource_id=str(actor))
    return snapshot, cash, root


class FakeDriver:
    def __init__(self, frames, cash):
        self.frames, self.cash = list(frames), cash
        self.read_count, self.calls = 0, []

    def take_internal_semantic_snapshot(self):
        self.read_count += 1
        value = self.frames.pop(0) if len(self.frames) > 1 else self.frames[0]
        if isinstance(value, Exception):
            raise value
        return deepcopy(value)

    def query_war_cash_current_resources_private_v1(self, *, expected_revision):
        self.calls.append(("cash", expected_revision))
        if isinstance(self.cash, Exception):
            raise self.cash
        return deepcopy(self.cash)


class FakeService:
    _observed_planning_source_frame = staticmethod(GameplayBridgeService._observed_planning_source_frame)

    def __init__(self, frames, cash, root):
        self.driver, self.root = FakeDriver(frames, cash), root

    def query_campaign_root_context_v1(self, *, expected_revision):
        self.driver.calls.append(("realm", expected_revision))
        return deepcopy(self.root)


def collect(service):
    return collect_monthly_met_candidate_v1(service, start_date="1066.9.15",
        machine_id="synthetic-software-test", campaign_anchor=ANCHOR)


class MonthlyMetCollectorTests(unittest.TestCase):
    def test_fresh_month_point_collects_four_rates_and_domain_in_bounded_bundle(self):
        snapshot, cash, root = inputs()
        service = FakeService([snapshot], cash, root)
        current, sample = collect(service)
        self.assertEqual(service.driver.calls, [("cash", 635), ("realm", 635)])
        self.assertEqual(service.driver.read_count, 3)
        self.assertEqual(current, snapshot)
        self.assertEqual(sample["month_index"], 1)
        self.assertEqual(sample["frame"]["revision"], 635)
        self.assertEqual(sample["campaign_anchor"], ANCHOR)
        self.assertEqual(sample["raw_metrics"]["gross_income"]["value"], "9.93374")
        self.assertEqual(sample["raw_metrics"]["total_expenses"]["value"], "0.236")
        self.assertEqual(sample["raw_metrics"]["military_current"]["value"], "0.111")
        self.assertEqual(sample["raw_metrics"]["military_all_raised"]["value"], "4.101")
        self.assertEqual(sample["existing_realm_diagnostics"]["domain"]["value"]["size"], 6)
        collection = sample["monthly_collection"]
        self.assertEqual(collection["mode"], "paused_readonly_bundle")
        self.assertFalse(collection["same_native_capture"])
        self.assertEqual(collection["native_capture_epochs"], {"cash": None, "realm": None})
        self.assertTrue(collection["closing_frame_verified"])
        self.assertEqual(collection["readonly_query_invocations"], 2)
        self.assertIsNone(sample["new_RPC_calls"])
        self.assertEqual(sample["new_SAVE_exports"], 0)
        for key in ("due_commitments", "P_quality", "Q_realm", "K_dynasty", "continuation_legal"):
            self.assertIsNone(sample["raw_metrics"][key]["value"])
        self.assertLess(len(json.dumps(sample).encode()), 32 * 1024)

    def test_non_slot_or_unpaused_MET_keeps_one_read_and_zero_queries(self):
        for mutation in ("date", "paused"):
            with self.subTest(mutation=mutation):
                snapshot, cash, root = inputs()
                snapshot.update({"date_raw": snapshot["date_raw"] + 24} if mutation == "date" else {"paused": False})
                service = FakeService([snapshot], cash, root)
                current, sample = collect(service)
                self.assertEqual(current, snapshot)
                self.assertIsNone(sample)
                self.assertEqual(service.driver.read_count, 1)
                self.assertEqual(service.driver.calls, [])

    def test_absent_methods_leave_unknown_without_query_or_blocking(self):
        snapshot, cash, root = inputs()
        service = FakeService([snapshot], cash, root)
        service.driver.query_war_cash_current_resources_private_v1 = None
        service.query_campaign_root_context_v1 = None
        _, sample = collect(service)
        self.assertEqual(service.driver.calls, [])
        self.assertEqual(service.driver.read_count, 1)
        self.assertIsNone(sample["raw_metrics"]["gross_income"]["value"])
        self.assertEqual(sample["new_RPC_calls"], 0)
        self.assertEqual(sample["existing_realm_diagnostics"]["status"], "unavailable")

    def test_known_cash_permission_refusal_can_still_read_existing_public_root(self):
        snapshot, _, root = inputs()
        service = FakeService([snapshot], UnsupportedStepError("private observation disabled"), root)
        _, sample = collect(service)
        self.assertEqual([row[0] for row in service.driver.calls], ["cash", "realm"])
        self.assertIsNone(sample["raw_metrics"]["gross_income"]["value"])
        self.assertEqual(sample["existing_realm_diagnostics"]["status"], "available")
        self.assertEqual(sample["monthly_collection"]["queries"]["cash"]["status"], "unsupported")

    def test_frame_drift_after_cash_cannot_relabel_old_packet_or_submit_root(self):
        for field in ("revision", "connection_generation"):
            with self.subTest(field=field):
                snapshot, cash, root = inputs()
                changed = deepcopy(snapshot)
                target = changed if field == "revision" else changed["diagnostics"]
                target[field] += 1
                service = FakeService([snapshot, changed], cash, root)
                current, sample = collect(service)
                self.assertEqual(current, changed)
                self.assertEqual([row[0] for row in service.driver.calls], ["cash"])
                self.assertIsNone(sample["raw_metrics"]["gross_income"]["value"])
                self.assertFalse(sample["monthly_collection"]["closing_frame_verified"])
                self.assertIn(field, sample["existing_input_gaps"]["cash"])

    def test_unknown_inflight_result_stops_bundle_without_retry_despite_stable_SEM(self):
        snapshot, _, root = inputs()
        service = FakeService([snapshot], BridgeUnavailableError("command_result timed out; inflight unknown"), root)
        _, sample = collect(service)
        self.assertEqual([row[0] for row in service.driver.calls], ["cash"])
        self.assertEqual(sample["monthly_collection"]["retry_count"], 0)
        self.assertEqual(sample["monthly_collection"]["queries"]["realm"]["status"], "not_invoked")
        self.assertIsNone(sample["raw_metrics"]["gross_income"]["value"])

    def test_closing_SEM_unavailable_cannot_promote_cash_or_submit_root(self):
        snapshot, cash, root = inputs()
        service = FakeService([snapshot, BridgeUnavailableError("semantic frame unavailable")], cash, root)
        current, sample = collect(service)
        self.assertEqual(current, snapshot)
        self.assertEqual([row[0] for row in service.driver.calls], ["cash"])
        self.assertIsNone(sample["raw_metrics"]["gross_income"]["value"])
        self.assertIsNone(sample["monthly_collection"]["closing_frame"])
        self.assertIn("closing_frame", sample["existing_input_gaps"])


if __name__ == "__main__":
    unittest.main()

"""Round-trip actual new LAW4/LAW8 mailbox outputs through typed Python calls."""

from __future__ import annotations

import unittest

from test_ck3_12002_sway_law_transport_wire import (
    FixtureDriver, envelope, paused_frame,
)
from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.realm_law_formal_private_transport import (
    query_realm_law_crown_action_private_v1,
    query_realm_law_crown_receipt_private_v1,
    submit_realm_law_crown_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002


def wire(name: str) -> dict[str, object]:
    return envelope(f"ck3_12002_realm_law_action/wire-law-crown-{name}.json")


def query_frame() -> dict[str, object]:
    observation = wire("query")["observation"]
    return paused_frame({
        "snapshot_revision": observation["snapshot_revision"],
        "date_raw": observation["date_raw"],
        "actor_character_id": observation["player_character_id"],
    })


def receipt_frame(receipt: dict[str, object]) -> dict[str, object]:
    observation = wire("query")["observation"]
    return paused_frame({
        "snapshot_revision": receipt["post_public_revision"],
        "date_raw": receipt["post_date_raw"],
        "actor_character_id": observation["player_character_id"],
    })


class LawDriver(FixtureDriver):
    allow_private_realm_law_action = True


class RealmLawFormal12002WireTest(unittest.TestCase):
    def query(self) -> dict[str, object]:
        snapshot = query_frame()
        return query_realm_law_crown_action_private_v1(
            LawDriver(wire("query"), snapshot), expected_revision=snapshot["revision"],
        )

    def test_actual_observation_and_explicit_budget_submit_preserve_the_native_ack(self) -> None:
        readback = self.query()
        observation = wire("query")["observation"]
        self.assertEqual({key: readback[key] for key in observation}, observation)
        self.assertEqual(readback["exact_ck3_build"], CK3_12002.game_version)
        self.assertEqual(readback["exe_sha256"], CK3_12002.executable_sha256)
        native_ack = wire("submit-pending")["ack"]
        budgets = {charge["currency_key"]: charge["cost_raw"] for charge in native_ack["charges"]}
        driver = LawDriver(wire("submit-pending"), query_frame())
        actual = submit_realm_law_crown_private_v1(
            driver, readback=readback, law_key=native_ack["requested_law_key"],
            budgets=budgets, action_id=native_ack["submitted_request_id"],
        )
        self.assertEqual({key: actual[key] for key in native_ack}, native_ack)
        self.assertEqual(actual["status"], "submitted_verification_pending")
        self.assertFalse(actual["material_result"])
        request = driver.sent[0]
        self.assertNotEqual(request["request_id"], request["submitted_request_id"])
        self.assertEqual(request["expected_proof_epoch"], observation["proof_epoch"])
        self.assertEqual(request["budget_prestige_raw"], 20000000)

    def test_independent_receipts_keep_unchanged_failure_separate_from_verified_enactment(self) -> None:
        for name, material in (("receipt-unchanged", False), ("receipt-enacted", True)):
            with self.subTest(name=name):
                reply = wire(name)
                receipt = reply["receipt"]
                snapshot = receipt_frame(receipt)
                actual = query_realm_law_crown_receipt_private_v1(
                    LawDriver(reply, snapshot), expected_revision=snapshot["revision"],
                    submitted_request_id=receipt["submitted_request_id"],
                )
                self.assertEqual({key: actual[key] for key in receipt}, receipt)
                self.assertIs(actual["material_result"], material)
                self.assertEqual(actual["status"], reply["status"])
                if material:
                    charge = actual["charges"][0]
                    self.assertEqual(charge["pre_balance_raw"] - charge["post_balance_raw"], charge["cost_raw"])
                    self.assertTrue(actual["effective_law_verified"])
                    self.assertTrue(actual["resources_verified"])
                    self.assertTrue(actual["succession_verified"])
                else:
                    self.assertEqual(actual["failure"], "effective_law_not_enacted")

    def test_actual_native_final_recheck_denial_remains_a_nonmaterial_rejection(self) -> None:
        readback = self.query()
        reply = wire("submit-native-denied")
        ack = reply["ack"]
        actual = submit_realm_law_crown_private_v1(
            LawDriver(reply, query_frame()), readback=readback,
            law_key=ack["requested_law_key"], budgets={"prestige": 20000000},
            action_id=ack["submitted_request_id"],
        )
        self.assertEqual({key: actual[key] for key in ack}, ack)
        self.assertEqual(actual["status"], "rejected_before_submit")
        self.assertEqual(actual["failure"], "final_legality_denied")
        self.assertFalse(actual["material_result"])

    def test_explicit_private_flag_is_required_before_sending_a_query(self) -> None:
        snapshot = query_frame()
        driver = LawDriver(wire("query"), snapshot)
        driver.allow_private_realm_law_action = False
        with self.assertRaises(UnsupportedStepError):
            query_realm_law_crown_action_private_v1(driver, expected_revision=snapshot["revision"])
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()

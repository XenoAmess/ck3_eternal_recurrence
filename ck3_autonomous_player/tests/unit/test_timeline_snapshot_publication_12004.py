"""Source-route and real decoder regression for RMTM R15's partial frame.

This is not a compiled native producer or a live qualification. Only the packet
endpoint is synthetic in the decoder replay; no CK3 process or queue is used.
"""

from pathlib import Path
import re
import unittest

from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


BRIDGE = (Path(__file__).resolve().parents[2] /
          "native_bridge/src/bridge.cpp").read_text(encoding="utf-8-sig")


class TimelineSnapshotPublication12004Tests(unittest.TestCase):
    def test_both_noop_routes_exclude_exact_12004_core_observation(self):
        for kind, status in (("Pause", "already_paused"),
                             ("Resume", "already_running")):
            with self.subTest(kind=kind):
                condition = re.findall(
                    rf"result == xar::game::{kind}SubmitResult::{status} &&"
                    r"\s*(!xar::game::IsReviewedCrozierAdapter\(game\)"
                    r"\s*&&\s*!xar::game::IsCk3_12004Descriptor\(game.descriptor\(\)\))"
                    r"\s*\? &command_observation\s*: nullptr", BRIDGE)
                self.assertEqual(len(condition), 1)
                # Evaluate this exact production predicate, not an independent
                # replacement route. .2/.3 and other legacy behavior is kept.
                expression = condition[0].replace(
                    "xar::game::IsReviewedCrozierAdapter(game)", "reviewed"
                ).replace(
                    "xar::game::IsCk3_12004Descriptor(game.descriptor())", "actual4"
                ).replace("&&", " and ").replace("!", "not ").strip()
                expression = " ".join(expression.split())
                for reviewed, actual4, use_observation in (
                    (False, True, False), (True, False, False),
                    (False, False, True),
                ):
                    self.assertEqual(eval(expression, {"__builtins__": {}},
                                          {"reviewed": reviewed, "actual4": actual4}),
                                     use_observation)

    def test_null_observation_uses_existing_complete_snapshot_reader(self):
        route = re.search(
            r"if \(observed_snapshot != nullptr\) \{\s*"
            r"snapshot = \*observed_snapshot;\s*"
            r"\} else if \(!xar::game::ReadSnapshot\(bindings, snapshot\)\) \{"
            r"(?P<failure>.*?)\n  \}\n  if \(mailbox_lifetime != nullptr\)",
            BRIDGE, re.DOTALL)
        self.assertIsNotNone(route)
        failure = re.sub(r"//[^\n]*", "", route.group("failure"))
        # A failed full read may refresh payment identity from a fresh narrow
        # reader. It must still return before complete-frame publication.
        self.assertRegex(failure, r"#if defined\(XAR_ENABLE_WAR_PAYMENT_PASSIVE_12004\)")
        self.assertRegex(
            failure,
            r"PaymentIdentityCoreContext12004 identity_context\{\s*&bindings,\s*"
            r"g_war_payment_connection_12004\.load\(std::memory_order_acquire\),revision\};")
        self.assertRegex(
            failure,
            r"RefreshWarPaymentIdentityAfterSnapshotUnavailable12004\(\s*"
            r"g_war_payment_window_12004,&ReadPaymentIdentityCoreFrame12004,&identity_context\);")
        self.assertRegex(
            failure,
            r'#endif\s*record\("read_failed", revision, 0\);\s*return true;\s*\Z')
        self.assertNotRegex(
            failure,
            r"ObserveWarPaymentWindowFrame12004|PaymentFrame12004|mailbox_lifetime|snapshot\s*=")

    def test_core_only_stress_stays_rejected_and_complete_frame_is_accepted(self):
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint)
        endpoint.publish(_hello("game.state.snapshot"))
        actor = {"character_id": 34422, "alive": True, "stress_points": 7,
                 "betrothed_id": None, "primary_spouse_id": 808,
                 "spouse_ids": [808]}
        endpoint.publish(_snapshot(12, date_raw=53144352, played_character=actor))
        before = driver.take_internal_semantic_snapshot()
        self.assertEqual(before["native_revision"], 12)
        self.assertEqual(before["diagnostics"]["rejected_state_snapshot_count"], 0)

        # The captured failing payload's sentinel is not a lawful stress value.
        partial = dict(actor, stress_points=-1, primary_spouse_id=None, spouse_ids=[])
        endpoint.publish(_snapshot(13, date_raw=53144352, played_character=partial))
        rejected = driver.take_internal_semantic_snapshot()
        self.assertEqual(rejected["native_revision"], 12)
        self.assertEqual(rejected["diagnostics"]["rejected_state_snapshot_count"], 1)
        self.assertEqual(rejected["diagnostics"]["last_rejected_state_snapshot"]["error"],
                         "native played_character stress_points is malformed")

        endpoint.publish(_snapshot(14, date_raw=53144352, played_character=actor))
        complete = driver.take_internal_semantic_snapshot()
        self.assertEqual(complete["native_revision"], 14)
        self.assertEqual(complete["played_character"]["stress_points"], 7)
        self.assertEqual(complete["played_character"]["spouse_ids"], [808])
        self.assertEqual(complete["diagnostics"]["rejected_state_snapshot_count"], 1)


if __name__ == "__main__":
    unittest.main()

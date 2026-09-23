"""R0211 exact heartbeat regression for the battle-control submit gate."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.application_main_pump_readiness import (
    PumpReadinessError,
    exact_build_pump_gate_required,
    wait_for_verified_pump,
)


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "combat_r0211_capabilities.json"
# Git's repository-wide LF projection of the frozen R0211 CRLF response.
FIXTURE_SHA256 = "DD08DF9B6A2C7FA5EC115093B1198D5FC1695881A9E7097A4345FB1BC42CBA50"
DATE_RAW = 53179128


def real_capabilities() -> dict[str, object]:
    data = FIXTURE.read_bytes()
    assert hashlib.sha256(data).hexdigest().upper() == FIXTURE_SHA256
    return json.loads(data)


class ApplicationMainPumpReadinessTests(unittest.TestCase):
    def test_real_fixture_has_only_public_verified_counter(self) -> None:
        capabilities = real_capabilities()
        self.assertTrue(exact_build_pump_gate_required(capabilities))
        mailbox = capabilities["diagnostics"]["last_heartbeat"]["main_thread_query_mailbox_v1"]
        self.assertEqual(mailbox["pump_epochs"], 4414)
        self.assertEqual(mailbox["owner_verified_pump_epochs"], 4414)
        self.assertTrue(mailbox["paused_main_thread_observed"])
        self.assertNotIn("paused_owner_verified_pump_epochs", mailbox)

    def test_real_heartbeat_without_new_pump_expires_at_40_seconds(self) -> None:
        baseline = real_capabilities()
        elapsed = [0.0]
        calls = [0]

        def read() -> dict[str, object]:
            calls[0] += 1
            return baseline

        def sleep(_seconds: float) -> None:
            elapsed[0] += 10.0

        with self.assertRaises(PumpReadinessError) as raised:
            wait_for_verified_pump(
                read, baseline, DATE_RAW, timeout_seconds=40,
                clock=lambda: elapsed[0], sleep=sleep,
            )
        self.assertEqual(raised.exception.code, "no_fresh_pump")
        self.assertEqual((raised.exception.start_epoch, raised.exception.last_epoch), (4414, 4414))
        self.assertEqual(calls[0], 4)

    def test_real_heartbeat_new_verified_pump_is_ready(self) -> None:
        baseline = real_capabilities()
        advanced = copy.deepcopy(baseline)
        mailbox = advanced["diagnostics"]["last_heartbeat"]["main_thread_query_mailbox_v1"]
        mailbox["pump_epochs"] = 4415
        mailbox["owner_verified_pump_epochs"] = 4415
        elapsed = [0.0]
        calls = [0]

        def read() -> dict[str, object]:
            calls[0] += 1
            return baseline if calls[0] == 1 else advanced

        def sleep(_seconds: float) -> None:
            elapsed[0] += 1.0

        result = wait_for_verified_pump(
            read, baseline, DATE_RAW, timeout_seconds=40,
            clock=lambda: elapsed[0], sleep=sleep,
        )
        self.assertIs(result, advanced)
        self.assertEqual(calls[0], 2)

    def test_owner_or_paused_date_change_fails_before_query(self) -> None:
        baseline = real_capabilities()
        changed = copy.deepcopy(baseline)
        mailbox = changed["diagnostics"]["last_heartbeat"]["main_thread_query_mailbox_v1"]
        mailbox["owner_tid"] += 1
        with self.assertRaises(PumpReadinessError) as raised:
            wait_for_verified_pump(lambda: changed, baseline, DATE_RAW)
        self.assertEqual(raised.exception.code, "owner_or_paused_frame_changed")

        changed = copy.deepcopy(baseline)
        changed["diagnostics"]["last_heartbeat"]["main_thread_query_mailbox_v1"]["date_raw"] += 1
        with self.assertRaises(PumpReadinessError) as raised:
            wait_for_verified_pump(lambda: changed, baseline, DATE_RAW)
        self.assertEqual(raised.exception.code, "owner_or_paused_frame_changed")


if __name__ == "__main__":
    unittest.main()

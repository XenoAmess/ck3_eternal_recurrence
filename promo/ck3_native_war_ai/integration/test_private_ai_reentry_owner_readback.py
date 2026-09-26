"""Offline contract for the one-owner private passive readback; no CK3 launch."""

import asyncio
import json
from pathlib import Path
import tempfile
import threading
import unittest

from capture_session import (
    AI_REENTRY_CAPABILITY,
    AI_REENTRY_STEP,
    private_ai_reentry_readback,
    service_requests,
)


class FakeDriver:
    def __init__(self):
        self.paused = True
        self.revision = 12
        self.advertise = True
        self.calls = []
        self.result = {
            "step": AI_REENTRY_STEP,
            "accepted": True,
            "schema_version": 1,
            "observer": {"installed": True, "records": []},
        }

    def take_snapshot(self):
        return {"paused": self.paused, "revision": self.revision}

    def capabilities(self):
        return {"bridge_capabilities": [AI_REENTRY_CAPABILITY] if self.advertise else [],
                "action_steps": []}

    def _execute_primitive_step(self, step, **kwargs):
        self.calls.append((step, kwargs))
        return self.result


class PrivateAiReentryOwnerReadbackTests(unittest.TestCase):
    def setUp(self):
        self.driver = FakeDriver()
        self.request = {
            "action": "private_ai_terminal_reentry",
            "step": AI_REENTRY_STEP,
            "expected_revision": 12,
        }

    def test_exact_step_uses_owner_driver_and_private_capability(self):
        result = private_ai_reentry_readback(self.request, driver=self.driver)
        self.assertEqual(result, self.driver.result)
        self.assertEqual(self.driver.calls, [(AI_REENTRY_STEP, {
            "expected_revision": 12,
            "required_capability": AI_REENTRY_CAPABILITY,
            "timeout_seconds": 90,
        })])
        self.assertNotIn(AI_REENTRY_STEP, self.driver.capabilities()["action_steps"])

    def test_denies_unadvertised_stale_unpaused_or_broad_request(self):
        for request in (
            {**self.request, "step": "move-army-16777231-to-2639"},
            {**self.request, "extra": True},
            {**self.request, "expected_revision": True},
        ):
            with self.assertRaises(RuntimeError):
                private_ai_reentry_readback(request, driver=self.driver)
        self.driver.paused = False
        with self.assertRaisesRegex(RuntimeError, "stable paused"):
            private_ai_reentry_readback(self.request, driver=self.driver)
        self.driver.paused = True
        self.driver.revision = 13
        with self.assertRaisesRegex(RuntimeError, "stable paused"):
            private_ai_reentry_readback(self.request, driver=self.driver)
        self.driver.revision = 12
        self.driver.advertise = False
        with self.assertRaisesRegex(RuntimeError, "not advertised"):
            private_ai_reentry_readback(self.request, driver=self.driver)
        self.assertEqual(self.driver.calls, [])

    def test_service_uses_existing_call_slot_and_denies_without_opt_in(self):
        with tempfile.TemporaryDirectory() as temp:
            async def drive(enabled):
                directory = Path(temp) / ("enabled" if enabled else "disabled") / "interactive-requests"
                directory.parent.mkdir()

                async def submit_later():
                    while not directory.is_dir():
                        await asyncio.sleep(0.01)
                    source = directory.parent / "incoming.json"
                    source.write_text(json.dumps(self.request), encoding="utf-8")
                    source.replace(directory / "001.json")

                async def unused_call(*_args, **_kwargs):
                    raise AssertionError("private readback must not use MCP action route")

                await asyncio.gather(
                    service_requests(
                        directory, call=unused_call, stopped=threading.Event(),
                        seconds=1.0, state_reader=lambda: {},
                        private_ai_reentry_call=(
                            lambda request: private_ai_reentry_readback(
                                request, driver=self.driver)) if enabled else None,
                    ),
                    submit_later(),
                )
                return json.loads((directory.parent /
                                   "interactive-requests-responses/001.json").read_text(encoding="utf-8"))

            denied = asyncio.run(drive(False))
            self.assertEqual(denied["result"], "RED")
            self.assertEqual(self.driver.calls, [])
            accepted = asyncio.run(drive(True))
            self.assertEqual(accepted["result"], "CALL_COMPLETED")
            self.assertEqual(accepted["body"], self.driver.result)
            self.assertEqual(len(self.driver.calls), 1)


if __name__ == "__main__":
    unittest.main()

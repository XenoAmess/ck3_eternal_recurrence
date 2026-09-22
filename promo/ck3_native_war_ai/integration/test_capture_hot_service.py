"""Offline checks of the same-owner service; these never launch CK3."""
import asyncio
import json
from pathlib import Path
import tempfile
import threading
import unittest

from capture_session import service_requests


class HotServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_failed_call_keeps_owner_available_and_never_retries_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            requests = Path(temp) / "requests"
            calls = []
            owner = object()
            owners = []

            async def call(name, arguments):
                calls.append((name, arguments))
                owners.append(owner)
                if name == "ck3_activate_frontend_start_1066_bookmark_character_v1":
                    raise RuntimeError("postcondition unavailable")
                return {"map_ready": True, "paused": True}

            async def producer():
                while not requests.exists():
                    await asyncio.sleep(0.01)
                rows = [
                    {"action": "mcp", "tool": "ck3_activate_frontend_start_1066_bookmark_character_v1"},
                    {"action": "mcp", "tool": "ck3_take_snapshot"},
                    {"action": "finish"},
                ]
                for i, row in enumerate(rows):
                    path = requests / f"{i:03}.pending"
                    path.write_text(json.dumps(row), encoding="utf-8")
                    path.rename(path.with_suffix(".json"))

            await asyncio.gather(
                service_requests(requests, call=call, stopped=threading.Event(), seconds=3,
                                 state_reader=lambda: {"bridge_pid": 123}), producer())
            self.assertEqual(len(calls), 2)
            self.assertTrue(all(item is owner for item in owners))
            responses = Path(temp) / "requests-responses"
            self.assertEqual(json.loads((responses / "000.json").read_text())["result"], "RED")
            self.assertEqual(json.loads((responses / "001.json").read_text())["body"]["map_ready"], True)
            self.assertEqual(json.loads((responses / "002.json").read_text())["result"], "SERVICE_FINISHED")
            self.assertEqual(len(list(requests.glob("*.json"))), 3)

    async def test_stopped_owner_does_not_execute_requests(self):
        with tempfile.TemporaryDirectory() as temp:
            stopped = threading.Event()
            stopped.set()

            async def call(*args):
                self.fail("Stopped service must not call MCP")

            await service_requests(Path(temp) / "requests", call=call, stopped=stopped,
                                   seconds=1, state_reader=lambda: {})
            ended = json.loads((Path(temp) / "requests-responses/service-ended.json").read_text())
            self.assertEqual(ended["reason"], "owner_stopped")


if __name__ == "__main__":
    unittest.main()

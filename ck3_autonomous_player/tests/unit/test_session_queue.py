from __future__ import annotations

import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.session_queue import (  # noqa: E402
    PersistentSessionQueue,
    StdinLinePump,
    command_from_payload,
    expected_revision_error,
)


def publish_atomic(path: Path, payload: object) -> None:
    temporary = path.with_suffix(path.suffix + ".publishing")
    temporary.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(temporary, path)


class SessionQueueTests(unittest.TestCase):
    def test_claims_atomic_step_request_and_writes_terminal_response(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            queue = PersistentSessionQueue(Path(temporary) / "run")
            request_path = queue.inbox_dir / "turn-0001.json"
            publishing_path = request_path.with_suffix(".json.publishing")
            publishing_path.write_text(
                json.dumps(
                    {
                        "request_id": "turn-0001",
                        "command": "step",
                        "step": {"name": "auto-run", "turns": 6},
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(queue.poll(), [])
            os.replace(publishing_path, request_path)
            requests = queue.poll()

            self.assertEqual(len(requests), 1)
            self.assertEqual(requests[0].request_id, "turn-0001")
            self.assertEqual(requests[0].command, "auto-run 6")
            response_path = queue.respond(
                requests[0],
                ok=True,
                result={"selected_step": "life-advance"},
            )
            response = json.loads(response_path.read_text(encoding="utf-8"))
            self.assertEqual(
                response,
                {
                    "protocol_version": 1,
                    "request_id": "turn-0001",
                    "ok": True,
                    "result": {"selected_step": "life-advance"},
                    "error": None,
                },
            )
            self.assertEqual(queue.poll(), [])

    def test_existing_outbox_prevents_replay_after_queue_reopens(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            first = PersistentSessionQueue(run_dir)
            publish_atomic(
                first.inbox_dir / "same-id.json",
                {"request_id": "same-id", "command": "auto-turn"},
            )
            request = first.poll()[0]
            first.respond(request, ok=True, result={"turn": 1})

            reopened = PersistentSessionQueue(run_dir)
            self.assertEqual(reopened.poll(), [])

    def test_bad_request_gets_claimed_without_becoming_a_command(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            queue = PersistentSessionQueue(Path(temporary) / "run")
            publish_atomic(
                queue.inbox_dir / "filename-id.json",
                {"request_id": "different-id", "command": "status"},
            )

            request = queue.poll()[0]

            self.assertIsNone(request.command)
            self.assertIn("must match", request.error or "")
            response_path = queue.respond(
                request,
                ok=False,
                error=request.error,
            )
            response = json.loads(response_path.read_text(encoding="utf-8"))
            self.assertFalse(response["ok"])
            self.assertIsNone(response["result"])

    def test_command_payload_preserves_existing_stdin_command_language(self) -> None:
        self.assertEqual(command_from_payload({"command": "status"}), "status")
        self.assertEqual(
            command_from_payload({"command": "auto-turn"}),
            "auto-turn",
        )
        self.assertEqual(
            command_from_payload({"command": "step", "step": "war-status"}),
            "war-status",
        )
        self.assertEqual(
            command_from_payload({"command": "auto-run", "turns": 3}),
            "auto-run 3",
        )

    def test_expected_revision_is_rechecked_by_session_consumer(self) -> None:
        self.assertIsNone(
            expected_revision_error({"command": "auto-turn"}, current_revision=8)
        )
        self.assertIsNone(
            expected_revision_error(
                {"command": "auto-turn", "expected_revision": 8},
                current_revision=8,
            )
        )
        self.assertEqual(
            expected_revision_error(
                {"command": "auto-turn", "expected_revision": 7},
                current_revision=8,
            ),
            "development session revision mismatch: expected 7, current 8",
        )
        self.assertEqual(
            expected_revision_error(
                {"command": "auto-turn", "expected_revision": True},
                current_revision=8,
            ),
            "expected_revision must be a non-negative integer",
        )

    def test_descriptor_exposes_discovery_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            queue = PersistentSessionQueue(
                Path(temporary) / "run",
                supported_commands=("status", "auto-turn", "stop"),
                action_steps=("auto-turn",),
            )
            descriptor = queue.descriptor()
            self.assertEqual(descriptor["protocol_version"], 1)
            self.assertEqual(Path(str(descriptor["bridge_dir"])), queue.bridge_dir)
            self.assertEqual(Path(str(descriptor["inbox_dir"])), queue.inbox_dir)
            self.assertEqual(Path(str(descriptor["outbox_dir"])), queue.outbox_dir)
            self.assertEqual(
                descriptor["supported_commands"],
                ["status", "auto-turn", "stop"],
            )
            self.assertEqual(descriptor["action_steps"], ["auto-turn"])


class StdinLinePumpTests(unittest.TestCase):
    def test_blocking_read_is_decoupled_from_main_thread_command_poll(self) -> None:
        pump = StdinLinePump(io.StringIO("status\nauto-turn\n"))
        pump.start()
        deadline = time.monotonic() + 2
        lines: list[str] = []
        eof = False
        while time.monotonic() < deadline and not eof:
            batch = pump.poll()
            lines.extend(batch.lines)
            eof = batch.eof
            if not eof:
                time.sleep(0.005)

        self.assertTrue(eof)
        self.assertEqual(lines, ["status\n", "auto-turn\n"])


if __name__ == "__main__":
    unittest.main()

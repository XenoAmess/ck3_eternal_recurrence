#!/usr/bin/env python3

from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

import codex_task_bus as bus


def invoke(*arguments: str) -> dict[str, object]:
    output = io.StringIO()
    with redirect_stdout(output):
        bus.main(list(arguments))
    return json.loads(output.getvalue())


class TaskBusTests(unittest.TestCase):
    def test_install_copies_executable_and_documentation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = invoke("--bus-dir", raw, "install")
            self.assertTrue(Path(result["installed"]).is_file())
            self.assertTrue(Path(result["documentation"]).is_file())

    def test_status_notification_and_incremental_ack(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            common = ("--bus-dir", str(root))
            invoke(*common, "register", "--task", "alpha", "--summary", "build")
            invoke(*common, "register", "--task", "beta", "--summary", "review")
            invoke(
                *common,
                "notify",
                "--task",
                "alpha",
                "--to",
                "beta",
                "--level",
                "action",
                "--message",
                "origin/master advanced",
            )

            first = invoke(*common, "poll", "--task", "beta", "--ack")
            self.assertEqual(
                [event["kind"] for event in first["events"]],
                ["registered", "notification"],
            )
            self.assertEqual(first["events"][-1]["message"], "origin/master advanced")
            second = invoke(*common, "poll", "--task", "beta", "--ack")
            self.assertEqual(second["events"], [])

            invoke(
                *common,
                "notify",
                "--task",
                "alpha",
                "--to",
                "*",
                "--message",
                "broadcast",
            )
            broadcast = invoke(*common, "poll", "--task", "beta")
            self.assertEqual(broadcast["events"][0]["to"], ["*"])

            listing = invoke(*common, "list")
            self.assertEqual({task["task_id"] for task in listing["tasks"]}, {"alpha", "beta"})

    def test_done_clears_stale_next_step_and_resources(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            common = ("--bus-dir", raw)
            invoke(
                *common,
                "register",
                "--task",
                "alpha",
                "--summary",
                "build",
                "--next-step",
                "upload",
                "--resource",
                "CK3",
            )

            completed = invoke(
                *common,
                "status",
                "--task",
                "alpha",
                "--state",
                "done",
                "--summary",
                "published",
            )

            self.assertEqual(completed["task"]["state"], "done")
            self.assertEqual(completed["task"]["next_step"], "")
            self.assertEqual(completed["task"]["resources"], [])
            self.assertEqual(completed["event"]["kind"], "completed")


if __name__ == "__main__":
    unittest.main()

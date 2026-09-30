"""Harmless temporary-bus contracts for the video CK3 launch fence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest

from screen_bus_lease import ScreenLeaseKeeper, checked_owner, renew_once


REPO = Path(__file__).resolve().parents[3]
HEAD = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                      capture_output=True, text=True, check=True).stdout.strip()
TASK = "ck3-video-screen-fixture"
FAKE_CLI = '''import argparse
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
p = argparse.ArgumentParser()
p.add_argument('--bus-dir', type=Path, required=True)
p.add_argument('--expected-cli-sha256', required=True)
p.add_argument('command')
p.add_argument('--task')
p.add_argument('--expected-sequence', type=int)
p.add_argument('--repo')
p.add_argument('--stale-after')
a = p.parse_args()
path = a.bus_dir / 'fixture.json'
task = json.loads(path.read_text(encoding='utf-8'))
if a.command == 'list':
    print(json.dumps({'schema': 'codex.task_bus.v1', 'ok': True, 'tasks': [task]}))
elif a.command == 'heartbeat':
    if task['last_sequence'] != a.expected_sequence or task['task_id'] != a.task:
        print(json.dumps({'schema': 'codex.task_bus.v1', 'ok': False, 'code': 'CAS_CONFLICT'}))
        sys.exit(3)
    task['last_sequence'] += 1
    task['updated_at_utc'] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(task), encoding='utf-8')
    print(json.dumps({'schema': 'codex.task_bus.v1', 'ok': True, 'task': task,
                      'event': {'kind': 'heartbeat', 'task_id': a.task,
                                'sequence': task['last_sequence'], 'event_id': 'fixture'}}))
else:
    sys.exit(4)
'''


def task_row(*, sequence: int = 11, resources: list[str] | None = None,
             age_seconds: int = 0) -> dict:
    return {
        "schema": "codex.task_bus.v1", "task_id": TASK, "state": "running",
        "resources": ["ck3-screen:acquired"] if resources is None else resources,
        "last_sequence": sequence, "repo": str(REPO.resolve()),
        "git": {"head": HEAD, "dirty_entries": 0},
        "updated_at_utc": (datetime.now(timezone.utc) - timedelta(seconds=age_seconds)).isoformat(),
        "stale": age_seconds > 600,
    }


class ScreenBusLeaseTests(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory(prefix="video-screen-fixture-")
        root = Path(temporary.name)
        source = root / "source_bus.py"
        installed = root / "bus" / "bin" / "codex_task_bus.py"
        installed.parent.mkdir(parents=True)
        source.write_text(FAKE_CLI, encoding="utf-8")
        installed.write_bytes(source.read_bytes())
        (root / "bus" / "fixture.json").write_text(json.dumps(task_row()), encoding="utf-8")
        return temporary, source, root / "bus", hashlib.sha256(source.read_bytes()).hexdigest().upper()

    def test_cas_admission_and_unique_owner_readback(self):
        temporary, source, bus, sha = self.fixture()
        with temporary:
            row = renew_once(source=source, bus_dir=bus, expected_sha=sha,
                             task_id=TASK, expected_sequence=11, repo=REPO)
            self.assertEqual(row["sequence"], 12)
            self.assertEqual(json.loads((bus / "fixture.json").read_text())["last_sequence"], 12)
            with self.assertRaisesRegex(RuntimeError, "bus CAS/readback failed|exact running CAS owner"):
                renew_once(source=source, bus_dir=bus, expected_sha=sha,
                           task_id=TASK, expected_sequence=11, repo=REPO)

    def test_missing_or_changed_cli_stops_before_heartbeat(self):
        temporary, source, bus, sha = self.fixture()
        with temporary:
            (bus / "bin" / "codex_task_bus.py").write_text(FAKE_CLI + "# changed\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "bytes differ"):
                renew_once(source=source, bus_dir=bus, expected_sha=sha,
                           task_id=TASK, expected_sequence=11, repo=REPO)
            self.assertEqual(json.loads((bus / "fixture.json").read_text())["last_sequence"], 11)

    def test_stale_wrong_repo_and_nonunique_owner_stop(self):
        row = task_row(age_seconds=601)
        with self.assertRaisesRegex(RuntimeError, "stale"):
            checked_owner([row], TASK, 11, REPO, HEAD)
        row = task_row()
        row["repo"] = str(REPO.parent)
        with self.assertRaisesRegex(RuntimeError, "another checkout"):
            checked_owner([row], TASK, 11, REPO, HEAD)
        other = task_row()
        other["task_id"] = "other-screen-task"
        with self.assertRaisesRegex(RuntimeError, "claimed by another task"):
            checked_owner([task_row(), other], TASK, 11, REPO, HEAD)

    def test_keeper_preserves_red_and_requests_abort_on_conflict(self):
        temporary, source, bus, sha = self.fixture()
        with temporary:
            abort = threading.Event()
            keeper = ScreenLeaseKeeper(source=source, bus_dir=bus, expected_sha=sha,
                                       task_id=TASK, sequence=10, repo=REPO,
                                       journal=bus / "keeper.jsonl", abort=abort,
                                       interval_seconds=30)
            keeper.start()
            with self.assertRaises(RuntimeError):
                keeper.refresh()
            keeper.stop()
            self.assertTrue(abort.is_set())
            self.assertIsNotNone(keeper.failure)
            lines = (bus / "keeper.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(json.loads(lines[-1])["result"], "LOST_OR_UNCERTAIN_STOP")


if __name__ == "__main__":
    unittest.main()

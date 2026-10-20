"""Pure resume parsing contracts; no files, RPC, or game processes."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
from typing import Literal, NotRequired, TypedDict
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge.native_driver import (
    load_native_driver_state_for_resume_payload as consume,
)

PIPE = "synthetic-driver-resume-type-contract"
FixtureKind = Literal["legacy_unbound", "old_checkpoint", "ordinary_checkpoint"]
KINDS: tuple[FixtureKind, ...] = (
    "legacy_unbound", "old_checkpoint", "ordinary_checkpoint",
)


class HistoryRow(TypedDict):
    index: object  # Deliberately includes malformed boundary inputs.
    command: str
    ok: bool
    result: dict[str, object]


class ResumePayload(TypedDict):
    format_version: object
    pipe_name: str
    bridge_pid: int
    episode_character_id: int | None
    episode_run_id: str | None
    command_history: list[HistoryRow]
    last_checkpoint: dict[str, object] | None
    rollback_war_failure: None
    managed_restore_transaction: None
    succession_expectation: None
    campaign_goal: None
    succession_lifecycle: NotRequired[dict[str, object]]
    rollback_war_failures: NotRequired[list[dict[str, object]]]


def snapshot(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


def fixture(version: int, kind: FixtureKind) -> ResumePayload:
    checkpoint: dict[str, object] = {
        "name": "xar_checkpoint.ck3", "size": 123, "sha256": "a" * 64,
        "date_raw": 53274624, "history_index": 3,
        "episode_character_id": 40526, "episode_run_id": "synthetic-40526",
    }
    saved = deepcopy(checkpoint)
    rows: list[HistoryRow] = [
        {"index": 1, "command": "status", "ok": True, "result": {}},
        {"index": 2, "command": "status", "ok": True, "result": {}},
        {"index": 3, "command": "save-checkpoint", "ok": True,
         "result": {"step": "save-checkpoint", "checkpoint": saved}},
    ]
    value: ResumePayload = {
        "format_version": version, "pipe_name": PIPE, "bridge_pid": 4242,
        "episode_character_id": 40526, "episode_run_id": "synthetic-40526",
        "command_history": rows, "last_checkpoint": checkpoint,
        "rollback_war_failure": None, "managed_restore_transaction": None,
        "succession_expectation": None, "campaign_goal": None,
    }
    if kind == "legacy_unbound":
        value["episode_character_id"] = None
        value["episode_run_id"] = None
        value["command_history"] = []
        value["last_checkpoint"] = None
    elif kind == "ordinary_checkpoint":
        binding: dict[str, object] = {
            "schema": "xar.ck3.succession-lifecycle-binding/v1",
            "lifecycle": "ordinary_campaign_succession", "xar_enabled": "xar_off",
            "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
            "source": "synthetic-type-contract", "environment_sha256": "b" * 64,
        }
        value["succession_lifecycle"] = deepcopy(binding)
        value["rollback_war_failures"] = []
        checkpoint["succession_lifecycle"] = deepcopy(binding)
        saved["succession_lifecycle"] = deepcopy(binding)
    return value


class DriverResumeTypeContractTests(unittest.TestCase):
    def test_v1_v2_legacy_and_ordinary_full_and_thin(self) -> None:
        for version in (1, 2):
            for kind in KINDS:
                for include_history in (False, True):
                    with self.subTest(version=version, kind=kind, history=include_history):
                        value = fixture(version, kind)
                        before = snapshot(value)
                        result = consume(value, PIPE, include_command_history=include_history)
                        if result is None:
                            self.fail("legal resume payload was rejected")
                        self.assertIs(type(result["format_version"]), int)
                        self.assertEqual(result["format_version"], version)
                        self.assertEqual("command_history" in result, include_history)
                        self.assertIs(result["succession_lifecycle_migration_required"],
                                      kind != "ordinary_checkpoint")
                        self.assertEqual(snapshot(value), before)

    def test_numeric_version_lookalikes_return_none(self) -> None:
        for bad in (True, 1.0, 2.0):
            for include_history in (False, True):
                with self.subTest(bad=bad, bad_type=type(bad).__name__, history=include_history):
                    value = fixture(2, "old_checkpoint")
                    value["format_version"] = bad
                    before = snapshot(value)
                    self.assertIsNone(consume(value, PIPE, include_command_history=include_history))
                    self.assertEqual(snapshot(value), before)

    def test_numeric_history_index_lookalikes_raise(self) -> None:
        bad_indices: tuple[tuple[int, object], ...] = (
            (0, True), (0, 1.0), (1, 2.0), (2, 3.0),
        )
        for version in (1, 2):
            for offset, bad in bad_indices:
                for include_history in (False, True):
                    with self.subTest(version=version, row=offset + 1, bad=bad,
                                      bad_type=type(bad).__name__, history=include_history):
                        value = fixture(version, "old_checkpoint")
                        value["command_history"][offset]["index"] = bad
                        before = snapshot(value)
                        with self.assertRaisesRegex(ValueError, "^driver state command history is malformed$"):
                            consume(value, PIPE, include_command_history=include_history)
                        self.assertEqual(snapshot(value), before)


if __name__ == "__main__":
    unittest.main()

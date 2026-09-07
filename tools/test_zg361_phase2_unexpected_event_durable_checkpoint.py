#!/usr/bin/env python3
"""CK3-free tests for unexpected-event durable checkpoint capture."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from zg361_phase2_unexpected_event_durable_checkpoint import (  # noqa: E402
    attempt_unexpected_event_durable_checkpoint,
)


PID = 361250
GENERATION = 4
PLAYER = 32904
DATE_RAW = 53206512
INSTANCE = 206
KEY = "ep3_emperor_yearly.2211"


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "native:276",
        "revision": 43,
        "native_revision": 276,
        "date_raw": DATE_RAW,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": PLAYER},
        "diagnostics": {
            "connected": True,
            "bridge_pid": PID,
            "connection_generation": GENERATION,
        },
        # R250 exposed four authored options in the snapshot while the
        # current-event context rendered native indices 1/2/3.  Durable
        # capture binds the snapshot-side count; route selection validates
        # the separate native-index projection in its own exact contract.
        "active_event": {"instance_id": INSTANCE, "option_count": 4},
    }


def _unexpected_event() -> dict[str, object]:
    snapshot = _snapshot()
    event = {
        "snapshot_id": snapshot["snapshot_id"],
        "revision": snapshot["revision"],
        "native_revision": snapshot["native_revision"],
        "date_raw": DATE_RAW,
        "player_character_id": PLAYER,
        "connection_generation": GENERATION,
        "event_instance_id": INSTANCE,
        "event_option_count": 4,
    }
    return {
        "event_definition_key": KEY,
        "snapshot": snapshot,
        "event": event,
        "query": {
            "status": "available",
            "current_event_window_context": {"event_definition_key": KEY},
            "binding": {
                "snapshot_id": event["snapshot_id"],
                "revision": event["revision"],
                "native_revision": event["native_revision"],
                "event_instance_id": INSTANCE,
            },
        },
    }


class FakeService:
    def __init__(self, state_dir: Path, *, drift_after_save: bool = False) -> None:
        self.state_dir = state_dir
        self.current = _snapshot()
        self.drift_after_save = drift_after_save
        self.save_calls = 0
        self.expected_revisions: list[int] = []

    def capabilities(self) -> dict[str, object]:
        return {
            "mode": "native-headless",
            "backend_id": "native-headless",
            "visual_fallback": False,
            "bridge_capabilities": ["game.command.save-checkpoint"],
            "action_steps": ["save-checkpoint"],
            "checkpoint_materialization": {"configured": True},
            "diagnostics": copy.deepcopy(self.current["diagnostics"]),
        }

    def snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.current)

    def save_checkpoint(self, *, expected_revision: int) -> dict[str, object]:
        self.save_calls += 1
        self.expected_revisions.append(expected_revision)
        path = self.state_dir / "profile" / "save games" / "xar_checkpoint.ck3"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = b"durable-unexpected-event-checkpoint"
        path.write_bytes(payload)
        if self.drift_after_save:
            self.current["active_event"] = {"instance_id": INSTANCE + 1, "option_count": 1}
        return {
            "accepted": True,
            "status": "submitted",
            "checkpoint": {
                "status": "saved",
                "path": str(path.resolve()),
                "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "date_raw": DATE_RAW,
                "episode_character_id": PLAYER,
                "episode_run_id": "native-32904-unit",
                "history_index": 17,
                "strategy": "native-autosave-command-v1",
            },
            "materialization": {"available": True},
        }


class UnexpectedEventDurableCheckpointTests(unittest.TestCase):
    def test_exact_paused_modal_materializes_durable_recovery_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "state"
            artifact = root / "artifacts" / "checkpoint.json"
            service = FakeService(state)
            result = attempt_unexpected_event_durable_checkpoint(
                service,
                state_dir=state,
                unexpected_event=_unexpected_event(),
                artifact_path=artifact,
            )

            self.assertEqual(result["result"], "GREEN")
            self.assertTrue(result["durable_recovery_ready"])
            self.assertTrue(result["live_retention_may_continue"])
            self.assertEqual(service.save_calls, 1)
            self.assertEqual(service.expected_revisions, [43])
            self.assertEqual(result["pre_save_binding"], result["post_save_binding"])
            self.assertTrue(Path(result["recovery_input"]["source_save"]).is_file())
            persisted = json.loads(artifact.read_text(encoding="utf-8-sig"))
            self.assertEqual(persisted["result"], "GREEN")
            self.assertTrue(persisted["durable_recovery_ready"])

    def test_source_frame_drift_fails_before_save_but_keeps_live_retention(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = FakeService(root / "state")
            service.current["date_raw"] = DATE_RAW + 24
            result = attempt_unexpected_event_durable_checkpoint(
                service,
                state_dir=root / "state",
                unexpected_event=_unexpected_event(),
                artifact_path=root / "artifact.json",
            )

        self.assertEqual(result["result"], "RED")
        self.assertFalse(result["durable_recovery_ready"])
        self.assertTrue(result["live_retention_may_continue"])
        self.assertEqual(service.save_calls, 0)
        self.assertIn("changed before", result["failure_reason"])

    def test_post_save_modal_drift_does_not_claim_durable_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = FakeService(root / "state", drift_after_save=True)
            result = attempt_unexpected_event_durable_checkpoint(
                service,
                state_dir=root / "state",
                unexpected_event=_unexpected_event(),
                artifact_path=root / "artifact.json",
            )

        self.assertEqual(result["result"], "RED")
        self.assertFalse(result["durable_recovery_ready"])
        self.assertTrue(result["live_retention_may_continue"])
        self.assertEqual(service.save_calls, 1)
        self.assertIn("changed while", result["failure_reason"])


if __name__ == "__main__":
    unittest.main()

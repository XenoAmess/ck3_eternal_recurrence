from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.war_cash_pending_ledger_v1 import (
    _append,
    ledger_path,
    observe_recorded_war_cash_pending_v1,
    open_war_cash_scope_v1,
    record_war_cash_ack_v1,
    reserve_war_cash_action_v1,
    resolve_war_cash_action_v1,
)


WAR_ID = 16777231
EPISODE = "native-29829-2bc2d599f7f9"
SHA = "A" * 64
FRAME = {
    "played_character_id": 29829,
    "native_revision": 3,
    "date_raw": 53217624,
    "snapshot_id": "native:3",
    "revision": 4,
    "episode_run_id": EPISODE,
}
ACTION = {
    "selected_step": "move-army:17->392",
    "command_kind": "move_army",
    "typed_arguments": {"army_id": 17, "target_province_id": 392},
    "route_sha256": "B" * 64,
}


def action_sha(action: dict[str, object] = ACTION) -> str:
    payload = json.dumps(action, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def quote(action: dict[str, object] = ACTION, raw: int = 125_000) -> dict[str, object]:
    return {
        "source_frame": dict(FRAME), "war_id": WAR_ID,
        "priced_action": action, "raw": raw, "scale": 100_000,
        "price_source_kind": "native_exact_q100000",
        "price_evidence_sha256": SHA,
    }


class WarCashPendingLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.state_dir = Path(self.temporary.name)

    def observe(self, frame: dict[str, object] = FRAME) -> dict[str, object]:
        return observe_recorded_war_cash_pending_v1(
            self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID,
            current_frame=frame,
        )

    def open_and_reserve(self) -> None:
        open_war_cash_scope_v1(
            self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID,
            owner_id="Robert-driver", source_checkpoint_sha256=SHA,
        )
        reserve_war_cash_action_v1(
            self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID,
            request_id="request-1", quote=quote(),
            source_checkpoint_sha256=SHA, current_frame=FRAME,
        )

    def test_absent_scope_is_unknown_and_never_formal_zero(self) -> None:
        seen = self.observe()
        self.assertEqual(seen["status"], "uninitialized_unknown")
        self.assertIsNone(seen["recorded_unresolved_quote_sum_raw"])
        self.assertIsNone(seen["pending_war_cash_raw"])
        self.assertFalse(seen["formal_cash_receipt_eligible"])

    def test_unresolved_quote_survives_reopen_and_ack(self) -> None:
        self.open_and_reserve()
        record_war_cash_ack_v1(
            self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID,
            request_id="request-1", priced_action=ACTION,
        )
        seen = self.observe()  # New reader; no in-memory driver state.
        self.assertEqual(seen["recorded_unresolved_quote_sum_raw"], 125_000)
        self.assertEqual(seen["unresolved_request_ids"], ["request-1"])
        self.assertIsNone(seen["pending_war_cash_raw"])
        self.assertFalse(seen["formal_cash_receipt_eligible"])
        with self.assertRaisesRegex(ValueError, "unique owned scope"):
            reserve_war_cash_action_v1(
                self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID,
                request_id="request-1", quote=quote(),
                source_checkpoint_sha256=SHA, current_frame=FRAME,
            )

    def test_independent_postcondition_closes_record_but_not_coverage(self) -> None:
        self.open_and_reserve()
        resolve_war_cash_action_v1(
            self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID,
            request_id="request-1", independent_receipt={
                "request_id": "request-1", "action_sha256": action_sha(),
                "episode_run_id": EPISODE, "war_id": WAR_ID,
                "postcondition_verified": True, "status": "charged",
                "charged_raw": 125_000, "source_sha256": SHA,
                "post_frame": {**FRAME, "revision": 5},
            },
        )
        seen = self.observe()
        self.assertEqual(seen["recorded_unresolved_quote_sum_raw"], 0)
        self.assertEqual(seen["unresolved_request_ids"], [])
        self.assertIsNone(seen["pending_war_cash_raw"])
        self.assertFalse(seen["formal_cash_receipt_eligible"])

    def test_wrong_action_or_price_does_not_mutate_journal(self) -> None:
        self.open_and_reserve()
        path = ledger_path(self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID)
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, "unresolved priced action"):
            record_war_cash_ack_v1(
                self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID,
                request_id="request-1",
                priced_action={**ACTION, "route_sha256": "C" * 64},
            )
        with self.assertRaisesRegex(ValueError, "independent receipt"):
            resolve_war_cash_action_v1(
                self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID,
                request_id="request-1", independent_receipt={
                    "request_id": "request-1", "action_sha256": action_sha(),
                    "episode_run_id": EPISODE, "war_id": WAR_ID,
                    "postcondition_verified": True, "status": "charged",
                    "charged_raw": 125_001, "source_sha256": SHA,
                    "post_frame": FRAME,
                },
            )
        self.assertEqual(path.read_bytes(), before)

    def test_unproved_zero_and_wrong_scope_fail_closed(self) -> None:
        open_war_cash_scope_v1(
            self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID,
            owner_id="Robert-driver", source_checkpoint_sha256=SHA,
        )
        with self.assertRaisesRegex(ValueError, "proved-zero"):
            reserve_war_cash_action_v1(
                self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID,
                request_id="request-1", quote=quote(raw=0),
                source_checkpoint_sha256=SHA, current_frame=FRAME,
            )
        with self.assertRaisesRegex(ValueError, "same-episode"):
            reserve_war_cash_action_v1(
                self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID,
                request_id="request-1", quote={**quote(), "war_id": WAR_ID + 1},
                source_checkpoint_sha256=SHA, current_frame=FRAME,
            )

    def test_stale_price_frame_is_rejected_before_reservation(self) -> None:
        open_war_cash_scope_v1(
            self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID,
            owner_id="Robert-driver", source_checkpoint_sha256=SHA,
        )
        path = ledger_path(self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID)
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, "current paused frame"):
            reserve_war_cash_action_v1(
                self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID,
                request_id="request-1", quote=quote(),
                source_checkpoint_sha256=SHA,
                current_frame={**FRAME, "revision": FRAME["revision"] + 1},
            )
        self.assertEqual(path.read_bytes(), before)

    def test_restore_before_quote_requires_requery(self) -> None:
        self.open_and_reserve()
        seen = self.observe({**FRAME, "date_raw": FRAME["date_raw"] - 1})
        self.assertEqual(seen["status"], "restore_before_quoted_frame_requires_requery")
        self.assertIsNone(seen["recorded_unresolved_quote_sum_raw"])

    def test_partial_tail_and_hash_change_fail_closed(self) -> None:
        self.open_and_reserve()
        path = ledger_path(self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID)
        original = path.read_bytes()
        path.write_bytes(original + b'{"partial":')
        with self.assertRaisesRegex(ValueError, "incomplete final record"):
            self.observe()
        path.write_bytes(original.replace(b'"raw":125000', b'"raw":125001'))
        with self.assertRaisesRegex(ValueError, "hash chain changed"):
            self.observe()

    def test_stale_writer_cannot_append_after_other_writer(self) -> None:
        self.open_and_reserve()
        path = ledger_path(self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID)
        stale_sha = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])["sha256"]
        record_war_cash_ack_v1(
            self.state_dir, episode_run_id=EPISODE, war_id=WAR_ID,
            request_id="request-1", priced_action=ACTION,
        )
        current = path.read_bytes()
        with self.assertRaisesRegex(ValueError, "changed before append"):
            _append(path, {"kind": "stale"}, expected_sha256=stale_sha)
        self.assertEqual(path.read_bytes(), current)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3

from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from zg361_phase2_cross_cycle_endgame_action_cell import (  # noqa: E402
    EndgameResultBinding,
    PRODUCTION_SUBJECT_TRANSITION_MODE,
)
from zg361_phase2_cross_cycle_endgame_production_subject import (  # noqa: E402
    EXACT_EXE_SHA256,
    EXACT_GAME_VERSION,
    PRODUCTION_SUBJECT_CHECKPOINT_KIND,
    ProductionSubjectCheckpointError,
    bind_product_subject_checkpoint_session,
)


OWNER = 29037
SUBJECT = 29038
DATE_RAW = 9010
RESULT_SHA = "A" * 64
LINEAGE = "phase2-endgame-production-subject-lineage"


class SubjectService:
    def __init__(self, *, player: int = SUBJECT, active_event: object = None) -> None:
        self.player = player
        self.active_event = active_event

    def snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": "product-subject:1",
            "revision": 31,
            "native_revision": 131,
            "date_raw": DATE_RAW,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": self.player},
            "active_event": self.active_event,
        }


def result_binding() -> EndgameResultBinding:
    return EndgameResultBinding(
        owner_character_id=OWNER,
        subject_character_id=SUBJECT,
        result_event_instance_id=3611,
        result_revision=15,
        result_native_revision=115,
        result_date_raw=DATE_RAW,
        result_checkpoint_sha256=RESULT_SHA,
        save_lineage_id=LINEAGE,
    )


def receipt(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    return {
        "schema_version": 1,
        "kind": PRODUCTION_SUBJECT_CHECKPOINT_KIND,
        "result": "GREEN",
        "transition_mode": PRODUCTION_SUBJECT_TRANSITION_MODE,
        "game_version": EXACT_GAME_VERSION,
        "game_exe_sha256": EXACT_EXE_SHA256,
        "parent_result_checkpoint_sha256": RESULT_SHA,
        "save_lineage_id": LINEAGE,
        "source_event_definition_key": "zg361we.361",
        "owner_character_id": OWNER,
        "subject_character_id": SUBJECT,
        "player_character_id": SUBJECT,
        "date_raw": DATE_RAW,
        "path": str(path.resolve()),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest().upper(),
        "product_only": True,
        "official_ui_switch_observed": True,
        "fixture_used": False,
        "typed_event_fixture_used": False,
        "business_state_fixture_used": False,
        "console_used": False,
        "generic_character_rebind_used": False,
    }


class ProductionSubjectCheckpointTests(unittest.TestCase):
    def test_materialized_product_checkpoint_binds_subject_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "subject.ck3"
            path.write_bytes(b"real-product-subject-checkpoint")
            session = bind_product_subject_checkpoint_session(
                SubjectService(), result_binding(), receipt(path)
            )
        transition = session.transition_receipt
        self.assertEqual(
            transition["transition_mode"], PRODUCTION_SUBJECT_TRANSITION_MODE
        )
        self.assertTrue(transition["checkpoint_restore_observed"])
        self.assertTrue(transition["product_only"])
        self.assertFalse(transition["typed_event_fixture_used"])
        self.assertFalse(transition["generic_character_rebind_used"])
        self.assertEqual(transition["from_player_character_id"], OWNER)
        self.assertEqual(transition["to_player_character_id"], SUBJECT)

    def test_wrong_checkpoint_hash_is_typed_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "subject.ck3"
            path.write_bytes(b"real-product-subject-checkpoint")
            candidate = receipt(path)
            candidate["sha256"] = "F" * 64
            with self.assertRaises(ProductionSubjectCheckpointError) as caught:
                bind_product_subject_checkpoint_session(
                    SubjectService(), result_binding(), candidate
                )
        self.assertEqual(
            caught.exception.reason_code, "subject_checkpoint_contract_invalid"
        )

    def test_owner_or_active_event_frame_cannot_bind_as_subject(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "subject.ck3"
            path.write_bytes(b"real-product-subject-checkpoint")
            candidate = receipt(path)
            for service in (
                SubjectService(player=OWNER),
                SubjectService(active_event={"instance_id": 999}),
            ):
                with self.subTest(service=service):
                    with self.assertRaises(
                        ProductionSubjectCheckpointError
                    ) as caught:
                        bind_product_subject_checkpoint_session(
                            service, result_binding(), candidate
                        )
                    self.assertEqual(
                        caught.exception.reason_code,
                        "played_subject_checkpoint_not_observed",
                    )


if __name__ == "__main__":
    unittest.main()

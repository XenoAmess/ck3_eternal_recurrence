#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from preflight_zg361_phase2_cross_cycle_endgame_rebind import (  # noqa: E402
    build_preflight,
)
from zg361_phase2_cross_cycle_endgame_action_cell import (  # noqa: E402
    CrossCycleEndgameCellError,
)
from zg361_phase2_cross_cycle_endgame_live_seam import (  # noqa: E402
    ActivatedResultSession,
    CrossCycleEndgameLiveSeamError,
    EXACT_EXE_SHA256,
    EXACT_GAME_VERSION,
    TRANSITION_EVENT,
    TRANSITION_FIXTURE_ID,
    run_exact_build_cross_cycle_endgame_seam,
)


OWNER = 29037
SUBJECT = 29038
CYCLE = 16
CASE = 16056
SOURCE_DATE = 9000
RESULT_DATE = SOURCE_DATE + 240
LINEAGE = "cross-cycle-live-seam-unit-lineage"


def available(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def character_scope(character_id: int) -> dict[str, object]:
    return {
        "status": "available",
        "typed_identity": {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        },
    }


def identity_group(state: int | None = None) -> dict[str, object]:
    result = {
        "owner_character_id": available(OWNER),
        "subject_character_id": available(SUBJECT),
        "cycle_serial": available(CYCLE),
        "case_serial": available(CASE),
    }
    if state is not None:
        result["state"] = available(state)
    return result


class FakeExactEndgameService:
    def __init__(
        self,
        checkpoint_path: Path,
        *,
        unexpected_progress_event: bool = False,
        provider_ready: bool = True,
    ) -> None:
        self.checkpoint_path = checkpoint_path.resolve()
        self.unexpected_progress_event = unexpected_progress_event
        self.provider_ready = provider_ready
        self.stage = "source"
        self.player = OWNER
        self.event_id: int | None = 3561
        self.revision = 10
        self.native_revision = 110
        self.date_raw = SOURCE_DATE
        self.paused = True
        self.speed = 1
        self.steps: list[str] = []
        self.selections: list[tuple[str, int]] = []
        self.provider_queries = 0

    def capabilities(self) -> dict[str, object]:
        return {"bridge_capabilities": []}

    def snapshot(self) -> dict[str, object]:
        if self.stage == "progressing" and self.paused is False:
            self.date_raw = RESULT_DATE
            self.revision += 1
            self.native_revision += 1
            self.paused = True
            self.stage = "unexpected" if self.unexpected_progress_event else "m360"
            self.event_id = 8881 if self.unexpected_progress_event else 3601
        return {
            "snapshot_id": f"{self.stage}:{self.player}:{self.revision}",
            "revision": self.revision,
            "native_revision": self.native_revision,
            "date_raw": self.date_raw,
            "paused": self.paused,
            "map_ready": True,
            "speed": self.speed,
            "played_character": {"character_id": self.player},
            "active_event": (
                {"instance_id": self.event_id, "option_count": 1 if self.stage == "fixture" else 3}
                if self.event_id is not None
                else None
            ),
        }

    def _event_key(self) -> str:
        return {
            "source": "zg361we.356",
            "m360": "zg361we.360",
            "m361": "zg361we.361",
            "m361_reloaded": "zg361we.361",
            "fixture": TRANSITION_EVENT,
            "unexpected": "zg361other.999",
        }[self.stage]

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        if event_instance_id != self.event_id or expected_revision != self.revision:
            raise AssertionError("event query escaped its fake frame")
        key = self._event_key()
        fixture = key == TRANSITION_EVENT
        saved = [
            {
                "name": (
                    "zga_phase2_endgame_owner" if fixture else "zg361_we_al_owner"
                ),
                "scope": character_scope(OWNER),
            },
            {
                "name": (
                    "zga_phase2_endgame_subject" if fixture else "zg361_we_al_subject"
                ),
                "scope": character_scope(SUBJECT),
            },
        ]
        if not fixture:
            saved.extend(
                [
                    {"name": "zg361_we_al_cycle", "scope": {}},
                    {"name": "zg361_we_al_case", "scope": {}},
                ]
            )
        count = 1 if fixture else 3
        context = {
            "status": "available",
            "event_definition_key": key,
            "current_event_instance_id": event_instance_id,
            "snapshot_revision": self.native_revision,
            "date_raw": self.date_raw,
            "root_scope": character_scope(self.player),
            "saved_scopes": saved,
            "options": [
                {
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                }
                for index in range(count)
            ],
            "readiness": {
                "event_definition_identity_ready": True,
                "root_scope_ready": True,
                "saved_scopes_ready": True,
                "option_presentation_ready": True,
            },
        }
        return {"status": "available", "current_event_window_context": context}

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        if event_instance_id != self.event_id or expected_revision != self.revision:
            raise AssertionError("selection escaped its fake frame")
        self.selections.append((self.stage, option_number))
        self.revision += 1
        self.native_revision += 1
        if self.stage == "source" and option_number == 1:
            self.stage = "progressing"
            self.event_id = None
        elif self.stage == "m360" and option_number == 3:
            self.stage = "m361"
            self.event_id = 3611
        elif self.stage == "m361_reloaded" and option_number == 1:
            self.stage = "fixture"
            self.event_id = 9361
        elif self.stage == "fixture" and option_number == 1:
            self.stage = "subject"
            self.player = SUBJECT
            self.event_id = None
        else:
            raise AssertionError(f"unexpected fake selection {self.stage}/{option_number}")
        return {"accepted": True, "status": "submitted"}

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        if expected_revision != self.revision:
            raise AssertionError("timeline command escaped its revision")
        self.steps.append(step)
        self.revision += 1
        self.native_revision += 1
        if step == "set-speed-1":
            self.speed = 1
        elif step == "resume-map":
            self.paused = False
        elif step == "pause-map":
            self.paused = True
        else:
            raise AssertionError(f"unexpected step {step}")
        return {"accepted": True, "status": "submitted", "step": step}

    def save_checkpoint(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        if self.stage != "m361" or expected_revision != self.revision:
            raise AssertionError("checkpoint was not saved on visible M361")
        size = self.checkpoint_path.stat().st_size
        sha = hashlib.sha256(self.checkpoint_path.read_bytes()).hexdigest().upper()
        return {
            "accepted": True,
            "status": "submitted",
            "checkpoint": {
                "status": "saved",
                "path": str(self.checkpoint_path),
                "size": size,
                "sha256": sha,
            },
        }

    def query_zhongguo_workforce_collective_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        self.provider_queries += 1
        if self.stage != "subject":
            raise AssertionError("provider was queried before the typed transition")
        snapshot = self.snapshot()
        if expected_revision != snapshot["revision"] or owner_character_id != OWNER:
            raise AssertionError("provider query binding drifted")
        if not self.provider_ready:
            return {"status": "unavailable", "readiness": {"ready": False}}
        return {
            "status": "available",
            "player_character_id": SUBJECT,
            "subject_character_id": SUBJECT,
            "requested_owner_character_id": OWNER,
            "binding": {
                "snapshot_id": snapshot["snapshot_id"],
                "revision": snapshot["revision"],
                "native_revision": snapshot["native_revision"],
                "date_raw": snapshot["date_raw"],
                "player_character_id": SUBJECT,
                "subject_character_id": SUBJECT,
                "owner_character_id": OWNER,
            },
            "al_case": identity_group(5),
            "m360_receipt": {**identity_group(4), "choice": available(3)},
            "route_c_debt": {
                **identity_group(4),
                "open": available(True),
                "consumed": available(False),
                "due_cycle_serial": available(CYCLE + 1),
            },
            "charter_gate": {
                "status": "consumed",
                **identity_group(5),
                "evidence_count": available(3),
                "evidence_ready": available(False),
                "evidence_consumed": available(True),
                "prepared_charter_id": available(36101),
                "adopted_cycle_serial": available(CYCLE),
                "effective_cycle_serial": available(CYCLE + 1),
            },
            "readiness": {"ready": True},
        }


def source_restore() -> dict[str, object]:
    return {
        "result": "GREEN",
        "span_id": "phase2_cross_cycle_endgame",
        "handler": "capture_cross_cycle_endgame",
        "checkpoint": {
            "bytes": 1024,
            "sha256": "B" * 64,
            "save_lineage_id": LINEAGE,
        },
        "expected": {
            "event_definition_key": "zg361we.356",
            "owner_character_id": OWNER,
            "player_character_id": OWNER,
            "date_raw": SOURCE_DATE,
        },
        "restore_receipt": {
            "result": "GREEN",
            "provider_observed": True,
            "checkpoint_sha256": "B" * 64,
            "save_lineage_id": LINEAGE,
            "event_definition_key": "zg361we.356",
            "owner_character_id": OWNER,
            "player_character_id": OWNER,
            "date_raw": SOURCE_DATE,
            "fixture_used": False,
            "console_used": False,
            "generic_character_rebind_used": False,
        },
    }


def build_identity() -> dict[str, object]:
    return {
        "game_version": EXACT_GAME_VERSION,
        "game_exe_sha256": EXACT_EXE_SHA256,
    }


class CrossCycleEndgameLiveSeamTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.checkpoint = Path(self.temp.name) / "endgame-result.ck3"
        self.checkpoint.write_bytes(b"real-checkpoint-fixture-bytes")

    def _activation(
        self,
        service: FakeExactEndgameService,
        *,
        owner: int = OWNER,
        generic: bool = False,
    ):
        def activate(result: object) -> ActivatedResultSession:
            service.stage = "m361_reloaded"
            service.player = OWNER
            service.event_id = 3612
            service.revision += 1
            service.native_revision += 1
            return ActivatedResultSession(
                service,
                {
                    "result": "GREEN",
                    "provider_observed": True,
                    "action_ack_only": False,
                    "transition_fixture_id": TRANSITION_FIXTURE_ID,
                    "typed_event_fixture_used": True,
                    "business_state_fixture_used": False,
                    "console_used": False,
                    "generic_character_rebind_used": generic,
                    "checkpoint_sha256": result.result_checkpoint_sha256,
                    "save_lineage_id": result.save_lineage_id,
                    "event_definition_key": "zg361we.361",
                    "owner_character_id": owner,
                    "subject_character_id": SUBJECT,
                    "player_character_id": OWNER,
                    "date_raw": RESULT_DATE,
                    "game_version": EXACT_GAME_VERSION,
                    "game_exe_sha256": EXACT_EXE_SHA256,
                },
            )

        return activate

    def test_green_uses_real_route_c_typed_transition_and_provider(self) -> None:
        service = FakeExactEndgameService(self.checkpoint)
        result = run_exact_build_cross_cycle_endgame_seam(
            service,
            source_checkpoint_restore=source_restore(),
            build_identity=build_identity(),
            activate_result_session=self._activation(service),
            timeout_s=1,
            poll_interval_s=0,
        )
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(result["readiness"], "static-ready-live-pending")
        self.assertTrue(result["provider_observed_postcondition"])
        self.assertFalse(result["action_ack_is_business_postcondition"])
        self.assertEqual(
            service.selections,
            [("source", 1), ("m360", 3), ("m361_reloaded", 1), ("fixture", 1)],
        )
        self.assertEqual(service.steps, ["resume-map"])
        self.assertEqual(service.player, SUBJECT)
        self.assertEqual(service.provider_queries, 1)
        transition = result["subject_transition_receipt"]
        self.assertTrue(transition["typed_event_fixture_used"])
        self.assertFalse(transition["generic_character_rebind_used"])

    def test_exact_build_drift_is_typed_red_before_action(self) -> None:
        service = FakeExactEndgameService(self.checkpoint)
        identity = build_identity()
        identity["game_version"] = "1.19.0.7"
        with self.assertRaises(CrossCycleEndgameLiveSeamError) as caught:
            run_exact_build_cross_cycle_endgame_seam(
                service,
                source_checkpoint_restore=source_restore(),
                build_identity=identity,
                activate_result_session=self._activation(service),
                timeout_s=1,
                poll_interval_s=0,
            )
        self.assertEqual(caught.exception.reason_code, "exact_build_mismatch")
        self.assertEqual(service.selections, [])

    def test_unexpected_progress_event_is_typed_red(self) -> None:
        service = FakeExactEndgameService(
            self.checkpoint, unexpected_progress_event=True
        )
        with self.assertRaises(CrossCycleEndgameLiveSeamError) as caught:
            run_exact_build_cross_cycle_endgame_seam(
                service,
                source_checkpoint_restore=source_restore(),
                build_identity=build_identity(),
                activate_result_session=self._activation(service),
                timeout_s=1,
                poll_interval_s=0,
            )
        self.assertEqual(caught.exception.reason_code, "unexpected_owner_event")

    def test_wrong_restore_owner_is_typed_red(self) -> None:
        service = FakeExactEndgameService(self.checkpoint)
        with self.assertRaises(CrossCycleEndgameLiveSeamError) as caught:
            run_exact_build_cross_cycle_endgame_seam(
                service,
                source_checkpoint_restore=source_restore(),
                build_identity=build_identity(),
                activate_result_session=self._activation(service, owner=OWNER + 9),
                timeout_s=1,
                poll_interval_s=0,
            )
        self.assertEqual(caught.exception.reason_code, "result_restore_owner_mismatch")
        self.assertEqual(service.provider_queries, 0)

    def test_generic_restore_rebind_is_typed_red(self) -> None:
        service = FakeExactEndgameService(self.checkpoint)
        with self.assertRaises(CrossCycleEndgameLiveSeamError) as caught:
            run_exact_build_cross_cycle_endgame_seam(
                service,
                source_checkpoint_restore=source_restore(),
                build_identity=build_identity(),
                activate_result_session=self._activation(service, generic=True),
                timeout_s=1,
                poll_interval_s=0,
            )
        self.assertEqual(caught.exception.reason_code, "generic_character_rebind_forbidden")
        self.assertEqual(service.provider_queries, 0)

    def test_ack_and_event_visibility_without_provider_never_green(self) -> None:
        service = FakeExactEndgameService(self.checkpoint, provider_ready=False)
        with self.assertRaises(CrossCycleEndgameCellError) as caught:
            run_exact_build_cross_cycle_endgame_seam(
                service,
                source_checkpoint_restore=source_restore(),
                build_identity=build_identity(),
                activate_result_session=self._activation(service),
                timeout_s=1,
                poll_interval_s=0,
            )
        self.assertEqual(caught.exception.reason_code, "workforce_provider_unavailable")
        self.assertEqual(service.provider_queries, 1)

    def test_no_launch_preflight_is_green_and_live_pending(self) -> None:
        report = build_preflight()
        self.assertEqual(report["result"], "GREEN")
        self.assertEqual(report["readiness"], "static-ready-live-pending")
        self.assertFalse(report["no_launch_boundary"]["ck3_started"])
        self.assertFalse(report["live_gate"]["ready"])
        self.assertTrue(all(report["checks"].values()))


if __name__ == "__main__":
    unittest.main()

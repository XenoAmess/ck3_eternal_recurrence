from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_zhongguo_scoreboard_action_contract import (  # noqa: E402
    CONNECTION_GENERATION,
    ENTRY,
    NATIVE_REVISION,
    PLAYER,
    PUBLIC_REVISION,
    TAB,
    _frame,
    _post,
    _set_visible,
)
from xar_autoplayer.bridge.zhongguo_scoreboard_action_batch import (  # noqa: E402
    run_zhongguo_scoreboard_action_batch,
)
from xar_autoplayer.bridge.zhongguo_scoreboard_action_contract import (  # noqa: E402
    ScoreboardActionRejected,
    acknowledged_zhongguo_scoreboard_action_v1,
    build_zhongguo_scoreboard_action_v1_request,
    plan_zhongguo_scoreboard_action_v1,
)


class _BatchService:
    def __init__(self) -> None:
        self.state = _frame(open_tab=None, entry_tab="received")
        self.semantic_serial = 2
        self.fail_semantic_action: str | None = None
        self.entry = "received"
        self.bridge_pid = 4100
        self.connection_generation = CONNECTION_GENERATION
        self.player = PLAYER
        self.date_raw = int(self.state["date_raw"])
        self.provider_session = str(self.state["provider_session_id"])

    def snapshot(self) -> dict[str, object]:
        return {
            "paused": True,
            "map_ready": True,
            "revision": PUBLIC_REVISION,
            "native_revision": NATIVE_REVISION,
            "date_raw": self.date_raw,
            "played_character": {"character_id": self.player},
            "diagnostics": {
                "bridge_pid": self.bridge_pid,
                "connection_generation": self.connection_generation,
            },
        }

    def prepare(self, surface_id: str) -> dict[str, object]:
        previous_pid = self.bridge_pid
        previous_generation = self.connection_generation
        self.bridge_pid += 1
        self.connection_generation += 1
        self.provider_session = f"{self.connection_generation:032X}"
        entry = "managed" if surface_id == "managed-capable" else "received"
        self.entry = entry
        self.state = _frame(open_tab=None, entry_tab=entry)
        self.state["observation_sequence"] = 10 + self.semantic_serial
        self.state["observed_state_revision"] = 5 + self.semantic_serial
        self.state["semantic_fingerprint_v1"] = (
            f"{self.semantic_serial:064X}"
        )
        self.state["provider_session_id"] = self.provider_session
        if surface_id == "managed-capable":
            managed = self.state["acl"]["managed"]
            managed["surface_available"] = True
            managed["current_player_can_assess_others"] = True
        self.semantic_serial += 1
        return {
            "surface_id": surface_id,
            "status": "ready",
            "evidence_class": "real_ck3",
            "state_origin": "product-checkpoint",
            "transition_kind": "canonical-checkpoint-clean-restart",
            "restore_materialized": True,
            "provider_observed": True,
            "checkpoint_sha256": "A" * 64,
            "checkpoint_bytes": 1024,
            "save_lineage_id": "phase2-product-lineage",
            "lifecycle": {
                "lifecycle_intent": "restore",
                "previous_pid": previous_pid,
                "pid": self.bridge_pid,
                "previous_connection_generation": previous_generation,
                "connection_generation": self.connection_generation,
            },
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
            "generic_character_rebind_used": False,
        }

    def query_zhongguo_scoreboard_state_v1(
        self, request_nonce: str, *, expected_revision: int
    ) -> dict[str, object]:
        if expected_revision != PUBLIC_REVISION:
            raise AssertionError("batch changed the paused public revision")
        frame = copy.deepcopy(self.state)
        frame["request_nonce"] = request_nonce
        frame["binding"] = {
            "request_nonce": request_nonce,
            "snapshot_id": "native:77",
            "revision": PUBLIC_REVISION,
            "native_revision": NATIVE_REVISION,
            "connection_generation": self.connection_generation,
            "date_raw": frame["date_raw"],
            "paused": True,
            "player_character_id": self.player,
            "expected_revision": PUBLIC_REVISION,
        }
        frame["source"] = {
            "connection_generation": self.connection_generation,
            "revision": PUBLIC_REVISION,
        }
        return frame

    def activate_zhongguo_scoreboard_v1(
        self,
        request_nonce: str,
        action: str,
        **arguments: object,
    ) -> dict[str, object]:
        request = build_zhongguo_scoreboard_action_v1_request(
            request_nonce=request_nonce,
            action=action,
            **arguments,
        )
        try:
            plan = plan_zhongguo_scoreboard_action_v1(
                request,
                source_state=self.state,
                observed_revision=PUBLIC_REVISION,
                observed_connection_generation=self.connection_generation,
            )
        except ScoreboardActionRejected as error:
            return {
                "accepted": False,
                "status": "unavailable",
                "rejection_reason": error.reason,
                "action_ack": None,
                "production_capability_advertised": False,
            }

        ack = acknowledged_zhongguo_scoreboard_action_v1(plan)
        expected = plan["expected_postcondition"]
        post = _post(self.state, active_tab=expected["active_tab"])
        if expected["active_tab"] is None:
            for tab, identity in TAB.items():
                _set_visible(post, identity, False)
            for tab, identity in ENTRY.items():
                _set_visible(post, identity, tab == self.entry)
        else:
            for identity in TAB.values():
                _set_visible(post, identity, True)
            for identity in ENTRY.values():
                _set_visible(post, identity, False)
        self.semantic_serial += 1
        post["semantic_fingerprint_v1"] = f"{self.semantic_serial:064X}"
        if action == self.fail_semantic_action:
            post["semantic_fingerprint_v1"] = self.state[
                "semantic_fingerprint_v1"
            ]
            self.fail_semantic_action = None
        self.state = post
        return {
            "accepted": True,
            "status": "acknowledged_verification_pending",
            "rejection_reason": None,
            "action_ack": ack,
            "production_capability_advertised": False,
        }


class ZhongguoScoreboardActionBatchTests(unittest.TestCase):
    def test_missing_surface_provider_returns_explicit_red_without_actions(
        self,
    ) -> None:
        service = _BatchService()
        evidence = run_zhongguo_scoreboard_action_batch(
            service,
            prepare_surface=lambda surface_id: {
                "surface_id": surface_id,
                "status": "unavailable",
                "failure_reason": "real_surface_provider_missing",
            },
        )
        self.assertEqual(evidence["result"], "RED")
        self.assertEqual(
            evidence["failure_reason"], "real_surface_provider_missing"
        )
        self.assertEqual(evidence["action_matrix"]["managed-capable"], [])
        self.assertFalse(evidence["promotion_eligible"])

    def test_full_candidate_matrix_verifies_even_while_advertisement_is_false(
        self,
    ) -> None:
        service = _BatchService()
        evidence = run_zhongguo_scoreboard_action_batch(
            service, prepare_surface=service.prepare
        )

        self.assertEqual(evidence["result"], "RED")
        self.assertTrue(evidence["candidate_batch_complete"])
        self.assertTrue(evidence["all_postconditions_verified"])
        self.assertTrue(evidence["all_expected_acl_denials_verified"])
        self.assertTrue(
            evidence["per_surface_single_session_binding_verified"]
        )
        self.assertTrue(evidence["cross_surface_clean_restart_verified"])
        self.assertFalse(evidence["global_single_session_required"])
        self.assertEqual(
            evidence["binding_policy"],
            "per-surface-single-session-with-canonical-clean-restart",
        )
        self.assertFalse(evidence["production_capability_advertised"])
        self.assertFalse(evidence["promotion_eligible"])
        self.assertEqual(
            evidence["failure_reason"],
            "production_capability_not_advertised",
        )

        matrix = evidence["action_matrix"]
        self.assertEqual(set(matrix), {"managed-capable", "received-only"})
        self.assertEqual(len(matrix["managed-capable"]), 6)
        self.assertEqual(len(matrix["received-only"]), 6)
        accepted = [
            row
            for rows in matrix.values()
            for row in rows
            if row["expected_outcome"] == "accepted"
        ]
        self.assertEqual(len(accepted), 11)
        self.assertTrue(all(row["verified_pass"] for row in accepted))
        self.assertTrue(
            all(isinstance(row["verified_postcondition"], dict) for row in accepted)
        )
        denied = next(
            row
            for row in matrix["received-only"]
            if row["expected_outcome"] == "managed_acl_denied"
        )
        self.assertTrue(denied["expected_outcome_verified"])
        self.assertIsNone(denied["verified_postcondition"])

        surfaces = evidence["surface_matrix"]
        self.assertTrue(surfaces["managed-capable"]["reopen_verified"])
        self.assertTrue(surfaces["received-only"]["reopen_verified"])
        self.assertEqual(
            surfaces["managed-capable"]["reopen_composition"],
            {
                "strategy": "close-query-open-query",
                "close_matrix_index": 5,
                "open_matrix_index": 6,
            },
        )

    def test_semantic_noop_keeps_batch_incomplete_and_fail_closed(self) -> None:
        service = _BatchService()
        service.fail_semantic_action = "switch-system"
        evidence = run_zhongguo_scoreboard_action_batch(
            service, prepare_surface=service.prepare
        )
        self.assertEqual(evidence["result"], "RED")
        self.assertFalse(evidence["candidate_batch_complete"])
        self.assertFalse(evidence["all_postconditions_verified"])
        self.assertFalse(evidence["promotion_eligible"])
        self.assertEqual(
            evidence["failure_reason"], "scoreboard_candidate_batch_incomplete"
        )

    def test_provider_session_change_inside_one_surface_is_rejected(
        self,
    ) -> None:
        service = _BatchService()
        original_activate = service.activate_zhongguo_scoreboard_v1

        def activate(
            request_nonce: str, action: str, **arguments: object
        ) -> dict[str, object]:
            result = original_activate(request_nonce, action, **arguments)
            if action == "switch-system":
                service.state["provider_session_id"] = "F" * 32
            return result

        service.activate_zhongguo_scoreboard_v1 = activate  # type: ignore[method-assign]

        evidence = run_zhongguo_scoreboard_action_batch(
            service, prepare_surface=service.prepare
        )
        self.assertEqual(evidence["result"], "RED")
        self.assertFalse(
            evidence["per_surface_single_session_binding_verified"]
        )
        self.assertFalse(evidence["candidate_batch_complete"])
        self.assertFalse(evidence["promotion_eligible"])

    def test_cross_surface_pid_change_requires_typed_clean_restart(self) -> None:
        service = _BatchService()

        def prepare(surface_id: str) -> dict[str, object]:
            receipt = service.prepare(surface_id)
            if surface_id == "received-only":
                receipt["transition_kind"] = "same-session"
            return receipt

        evidence = run_zhongguo_scoreboard_action_batch(
            service, prepare_surface=prepare
        )
        self.assertEqual(evidence["result"], "RED")
        self.assertFalse(evidence["cross_surface_clean_restart_verified"])
        self.assertFalse(evidence["candidate_batch_complete"])

    def test_cross_pid_is_never_labeled_global_single_session(self) -> None:
        service = _BatchService()
        evidence = run_zhongguo_scoreboard_action_batch(
            service, prepare_surface=service.prepare
        )
        managed = evidence["surface_matrix"]["managed-capable"]
        received = evidence["surface_matrix"]["received-only"]
        self.assertNotEqual(
            managed["prepared_binding"]["bridge_pid"],
            received["prepared_binding"]["bridge_pid"],
        )
        self.assertTrue(
            managed["per_surface_single_session_binding_verified"]
        )
        self.assertTrue(
            received["per_surface_single_session_binding_verified"]
        )
        self.assertNotIn("single_session_binding_verified", evidence)


if __name__ == "__main__":
    unittest.main()

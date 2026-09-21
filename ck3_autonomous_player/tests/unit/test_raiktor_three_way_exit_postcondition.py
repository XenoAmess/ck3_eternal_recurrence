from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


from xar_autoplayer.simulation.raiktor_three_way_exit_action_gate import (  # noqa: E402
    provide_raiktor_three_way_exit_action_gate,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_postcondition import (  # noqa: E402
    POSTWAR_EVIDENCE_SCHEMA,
    PROVIDER_SCHEMA,
    ThreeWayExitPostconditionError,
    provide_raiktor_three_way_exit_postcondition,
)
from test_raiktor_three_way_exit_action_gate import _capabilities  # noqa: E402
from test_raiktor_three_way_exit_recommendation import _provide  # noqa: E402
from test_raiktor_white_peace_narrow_projection_provider import (  # noqa: E402
    _snapshot,
)


def _authorized(route: str) -> dict[str, object]:
    if route == "continue":
        recommendation = _provide(production_live=True)
        literal = "resume-map"
    elif route == "white_peace":
        recommendation = _provide(
            production_live=True, allow_white_favor=True
        )
        literal = "offer-white-peace-50331699"
    elif route == "surrender":
        recommendation = _provide(
            production_live=True, opponent_penalty=100_000_000
        )
        literal = "surrender-war-50331699"
    else:  # pragma: no cover
        raise AssertionError(route)
    result = provide_raiktor_three_way_exit_action_gate(
        recommendation, _snapshot(), _capabilities(literal)
    )
    assert result["action_ready"] is True
    return result


def _post(
    gate: dict[str, object], *, route: str, restored: bool = False
) -> dict[str, object]:
    authorization = gate["authorization"]
    frame = authorization["frame"]
    expectations = authorization["postcondition_plan"]["expectations"]
    if route == "continue":
        gold_raw = 35_000_000
        prestige_raw = 12_345_678
        wars = deepcopy(_snapshot()["active_wars"])
        date_raw = frame["date_raw"] + 24
    else:
        resources = expectations["resources"]
        gold_raw = resources["gold"]["post_raw"]
        prestige_raw = resources["prestige"]["post_raw"]
        wars = []
        date_raw = frame["date_raw"]
    return {
        "snapshot_id": "restored-native:3" if restored else "fixture-native:92",
        "revision": 3 if restored else 92,
        "native_revision": 2 if restored else 8,
        "date_raw": date_raw,
        "paused": True,
        "active_event": None,
        "episode_run_id": frame["episode_id"],
        "diagnostics": {
            "bridge_pid": 62_001 if restored else frame["ck3_pid"],
            "connection_generation": 1 if restored else 12,
        },
        "played_character": {
            "character_id": expectations["played_character_id"],
            "alive": True,
        },
        "played_character_gold": {"raw": gold_raw, "scale": 100_000},
        "played_character_prestige": {
            "raw": prestige_raw,
            "scale": 100_000,
        },
        "active_wars": wars,
    }


def _action_result(
    gate: dict[str, object], post: dict[str, object], *, nested: bool = True
) -> dict[str, object]:
    authorization = gate["authorization"]
    action = authorization["action"]
    frame = authorization["frame"]
    result = {
        "step": action["literal"],
        "accepted": True,
        "status": "submitted",
        "backend_id": "native-headless",
    }
    if nested and action["semantic_action"] != "continue":
        typed_outcome = (
            "attacker_defeat"
            if action["semantic_action"] == "surrender"
            else action["semantic_action"]
        )
        result["war_termination_result"] = {
            "status": "applied",
            "war_id": action["war_id"],
            "outcome": typed_outcome,
            "episode_run_id": frame["episode_id"],
            "starting_snapshot_id": frame["snapshot_id"],
            "observed_snapshot_id": post["snapshot_id"],
            "command_acknowledged": True,
            "war_id_absent_after_ack": True,
        }
    return result


def _postwar(
    gate: dict[str, object], post: dict[str, object]
) -> dict[str, object]:
    authorization = gate["authorization"]
    expectations = authorization["postcondition_plan"]["expectations"]
    truce = expectations["truce"]
    return {
        "schema": POSTWAR_EVIDENCE_SCHEMA,
        "authorization_sha256": authorization["authorization_sha256"],
        "war_id": expectations["war_id"],
        "post_snapshot_id": post["snapshot_id"],
        "source_specific_loss": {
            "war_id": expectations["war_id"],
            "status": "destroyed",
            "source_specific_attribution_ready": True,
            "frozen_generation_count": 6,
            "post_termination_soldiers": 0,
            "source_set_sha256": "A" * 64,
            "evidence_sha256": "B" * 64,
        },
        "truce": {
            "source": "persisted_native_truce_row",
            "formula_derived": False,
            "from_character_id": truce["owner_character_id"],
            "to_character_id": truce["toward_character_id"],
            "evaluated_days": truce["evaluated_days"],
            "queried_at_date_raw": post["date_raw"],
            "expiry_date_raw": post["date_raw"] + truce["evaluated_days"] * 24,
            "evidence_sha256": "C" * 64,
        },
    }


def _checkpoint_restore(
    gate: dict[str, object], post: dict[str, object]
) -> dict[str, object]:
    restored = _post(gate, route=gate["authorization"]["action"]["semantic_action"], restored=True)
    checkpoint = {
        "status": "saved",
        "name": "xar_checkpoint.ck3",
        "size": 128,
        "sha256": "D" * 64,
        "date_raw": post["date_raw"],
        "episode_run_id": post["episode_run_id"],
        "episode_character_id": post["played_character"]["character_id"],
    }
    return {
        "save_result": {
            "step": "save-checkpoint",
            "accepted": True,
            "status": "submitted",
            "backend_id": "native-headless",
            "checkpoint": checkpoint,
            "materialization": {"available": True},
        },
        "restore_result": {
            "step": "restore-checkpoint",
            "accepted": True,
            "status": "restored",
            "backend_id": "native-headless",
            "source": "native-session-lifecycle-queue",
            "map_ready": True,
            "restored_date_raw": post["date_raw"],
            "checkpoint": {
                "status": "restored",
                "sha256": checkpoint["sha256"],
                "date_raw": post["date_raw"],
                "saved_date_raw": post["date_raw"],
            },
            "lifecycle": {
                "previous_pid": post["diagnostics"]["bridge_pid"],
                "pid": restored["diagnostics"]["bridge_pid"],
                "previous_connection_generation": post["diagnostics"][
                    "connection_generation"
                ],
                "connection_generation": restored["diagnostics"][
                    "connection_generation"
                ],
            },
            "paused": True,
            "snapshot_id": restored["snapshot_id"],
            "revision": restored["revision"],
        },
        "restored_snapshot": restored,
    }


def _termination_inputs(route: str = "white_peace") -> dict[str, object]:
    gate = _authorized(route)
    post = _post(gate, route=route)
    return {
        "action_gate_value": gate,
        "action_result_value": _action_result(gate, post),
        "post_snapshot_value": post,
        "postwar_evidence_value": _postwar(gate, post),
        "checkpoint_restore_value": _checkpoint_restore(gate, post),
    }


class RaiktorThreeWayExitPostconditionTests(unittest.TestCase):
    def test_white_peace_six_checks_close_gen034(self) -> None:
        result = provide_raiktor_three_way_exit_postcondition(
            **_termination_inputs()
        )

        self.assertEqual(result["schema"], PROVIDER_SCHEMA)
        self.assertEqual(result["status"], "verified")
        self.assertTrue(result["action_submitted"])
        self.assertTrue(result["postcondition_verified"])
        self.assertTrue(result["checkpoint_cold_restore_verified"])
        self.assertTrue(result["gen034_closed"])
        self.assertTrue(
            all(result["postcondition_receipt"]["checks"].values())
        )

    def test_surrender_accepts_existing_simple_native_ack_shape(self) -> None:
        inputs = _termination_inputs("surrender")
        inputs["action_result_value"].pop("war_termination_result")

        result = provide_raiktor_three_way_exit_postcondition(**inputs)

        self.assertEqual(result["route"], "surrender")
        self.assertTrue(result["gen034_closed"])

    def test_surrender_maps_native_attacker_defeat_to_semantic_action(self) -> None:
        inputs = _termination_inputs("surrender")
        termination = inputs["action_result_value"]["war_termination_result"]
        self.assertEqual(termination["outcome"], "attacker_defeat")

        result = provide_raiktor_three_way_exit_postcondition(**inputs)

        self.assertTrue(result["gen034_closed"])
        termination["outcome"] = "surrender"
        rejected = provide_raiktor_three_way_exit_postcondition(**inputs)
        self.assertFalse(rejected["gen034_closed"])
        self.assertIn(
            "postcondition_failed:authorized_action_submitted",
            rejected["blockers"],
        )

    def test_async_white_peace_submission_binds_earlier_pending_observation(self) -> None:
        inputs = _termination_inputs()
        termination = inputs["action_result_value"]["war_termination_result"]
        termination["status"] = "submitted_pending"
        termination["observed_snapshot_id"] = "native:pending-offer"
        termination["war_id_absent_after_ack"] = False

        result = provide_raiktor_three_way_exit_postcondition(**inputs)
        self.assertTrue(result["gen034_closed"])
        self.assertTrue(
            result["postcondition_receipt"]["checks"]["authorized_action_submitted"]
        )

        termination["war_id_absent_after_ack"] = True
        rejected = provide_raiktor_three_way_exit_postcondition(**inputs)
        self.assertFalse(rejected["gen034_closed"])
        self.assertIn(
            "postcondition_failed:authorized_action_submitted",
            rejected["blockers"],
        )

    def test_ack_without_observations_remains_evidence_required(self) -> None:
        gate = _authorized("white_peace")
        result = provide_raiktor_three_way_exit_postcondition(
            gate,
            {
                "step": "offer-white-peace-50331699",
                "accepted": True,
                "status": "submitted",
                "backend_id": "native-headless",
            },
            None,
        )

        self.assertEqual(result["status"], "evidence_required")
        self.assertFalse(result["action_submitted"])
        self.assertFalse(result["postcondition_verified"])
        self.assertFalse(result["gen034_closed"])
        self.assertEqual(
            result["blockers"],
            [
                "post_snapshot_unavailable",
                "postwar_evidence_unavailable",
                "checkpoint_restore_evidence_unavailable",
            ],
        )

    def test_each_material_drift_retains_a_named_red(self) -> None:
        cases = {
            "war": lambda value: value["post_snapshot_value"][
                "active_wars"
            ].append({"war_id": 50_331_699}),
            "gold": lambda value: value["post_snapshot_value"][
                "played_character_gold"
            ].update({"raw": 34_999_999}),
            "prestige": lambda value: value["post_snapshot_value"][
                "played_character_prestige"
            ].update({"raw": 8_845_677}),
            "truce": lambda value: value["postwar_evidence_value"][
                "truce"
            ].update({"to_character_id": 99}),
            "loss": lambda value: value["postwar_evidence_value"][
                "source_specific_loss"
            ].update({"status": "still_alive"}),
            "restore": lambda value: value["checkpoint_restore_value"][
                "restore_result"
            ]["lifecycle"].update(
                {
                    "pid": value["post_snapshot_value"]["diagnostics"][
                        "bridge_pid"
                    ]
                }
            ),
        }
        expected = {
            "war": "old_full_generation_war_id_absent",
            "gold": "gold_matches_frozen_terms",
            "prestige": "attacker_prestige_matches_frozen_terms",
            "truce": "directional_truce_days_and_expiry_observed",
            "loss": "source_specific_war_bound_regiments_absent",
            "restore": "postwar_checkpoint_cold_restore_rebinds_identity",
        }
        for label, mutate in cases.items():
            with self.subTest(label=label):
                inputs = _termination_inputs()
                mutate(inputs)
                result = provide_raiktor_three_way_exit_postcondition(**inputs)
                self.assertEqual(result["status"], "red")
                self.assertFalse(result["gen034_closed"])
                self.assertIn(
                    f"postcondition_failed:{expected[label]}",
                    result["blockers"],
                )

    def test_continue_verifies_successor_but_cannot_close_gen034(self) -> None:
        gate = _authorized("continue")
        post = _post(gate, route="continue")
        result = provide_raiktor_three_way_exit_postcondition(
            gate, _action_result(gate, post), post
        )

        self.assertEqual(result["status"], "verified")
        self.assertTrue(result["postcondition_verified"])
        self.assertFalse(result["checkpoint_cold_restore_verified"])
        self.assertFalse(result["gen034_closed"])

    def test_tampered_authorization_hash_is_rejected(self) -> None:
        inputs = _termination_inputs()
        inputs["action_gate_value"]["authorization"]["action"][
            "war_id"
        ] += 1

        with self.assertRaisesRegex(
            ThreeWayExitPostconditionError, "hash drifted"
        ):
            provide_raiktor_three_way_exit_postcondition(**inputs)


if __name__ == "__main__":
    unittest.main()

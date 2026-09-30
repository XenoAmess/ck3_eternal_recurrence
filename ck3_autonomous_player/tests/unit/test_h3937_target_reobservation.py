"""Exercise the actual target collector's handoff after two observed queries."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer import h3937_target_readonly_queries as target
from xar_autoplayer.errors import AgentError


def frame():
    def army(army_id, owner, province, controllable):
        return {"army_id": army_id, "owner_character_id": owner,
                "current_province_id": province,
                "move_target_province_id": None, "move_target_observable": False,
                "route_province_ids": [], "route_read_status": "complete_empty",
                "route_source_count": 0, "army_state": "regular", "army_state_code": 1,
                "in_combat": False, "retreating": False, "controllable": controllable}
    subject = army(target.ARMY_ID, 29829, target.TARGET_PROVINCE_ID, True)
    return {"snapshot_id": "native:3", "revision": 4, "native_revision": 3,
            "date_raw": target.EXPECTED_DATE_RAW, "paused": True, "map_ready": True,
            "episode_run_id": target.EXPECTED_EPISODE_RUN_ID,
            "episode_character_id": 29829, "played_character": {"character_id": 29829},
            "active_wars": [{"war_id": 16777231, "player_side": "defender",
                             "allied_armies": [copy.deepcopy(subject)],
                             "enemy_armies": [army(50331920, 30400, 2599, False),
                                              army(83886484, 30401, 2598, False)]}],
            "player_armies": [subject], "active_event": None,
            "pending_character_interaction": None, "route_contact_horizon_supported": True,
            "native_command_history": [{"command": "query-province-local-siege-v1-2610", "ok": True},
                                       {"command": "query-route-contact-horizon", "ok": True}],
            "diagnostics": {"connection_generation": 1, "heartbeat_sequence": 1544}}


class Service:
    def __init__(self, observed):
        self.observed, self.calls = observed, []
    def snapshot(self):
        return copy.deepcopy(self.observed)
    def execute_step(self, step, *, expected_revision):
        self.calls.append((step, expected_revision))
        raise AgentError("native gameplay step failed: state_changed")


class TargetReobservationTests(unittest.TestCase):
    def invoke(self, old, observed):
        scope = target._complete_published_scope(old)
        self.assertIsNotNone(scope)
        combined = {"observed": True, "frames": [copy.deepcopy(old) for _ in range(3)],
                    "envelopes": [{"accepted": True}, {"accepted": True}],
                    "steps": ["query-province-local-siege-v1-2610", "query-route-contact-horizon"],
                    "scope": scope}
        service = Service(observed)
        with patch.object(target, "H3937_TARGET_LIVE_AUTHORIZED", True), \
             patch.object(target, "collect_h3937_combined_reads_in_session", return_value=combined):
            result = target.collect_h3937_target_reads_in_session(service)
        return result, service

    def test_diagnostic_refresh_reaches_third_query_and_retains_native_rejection(self):
        old = frame()
        refreshed = copy.deepcopy(old)
        refreshed["diagnostics"]["heartbeat_sequence"] += 1
        refreshed["diagnostics"]["last_snapshot_publish_diagnostic"] = {"elapsed_seconds": 0.4}
        self.assertNotEqual(refreshed, old)
        result, service = self.invoke(old, refreshed)
        self.assertTrue(result["checks"]["combined_final_snapshot_reobserved"])
        self.assertEqual(service.calls, [(target.QUERY_ARMY_STRENGTHS_STEP, 4)])
        self.assertEqual(result["query_attempts"], 3)
        self.assertEqual(result["error"], "AgentError: native gameplay step failed: state_changed")
        self.assertFalse(result["observed"])
        self.assertEqual(result["gameplay_actions"], 0)

    def test_actual_semantic_revision_membership_or_history_drift_stops_before_query(self):
        mutations = {
            "native_revision": lambda f: f.update(native_revision=4),
            "local_revision": lambda f: f.update(revision=5),
            "snapshot_id": lambda f: f.update(snapshot_id="native:4"),
            "date": lambda f: f.update(date_raw=target.EXPECTED_DATE_RAW + 1),
            "pause": lambda f: f.update(paused=False),
            "map": lambda f: f.update(map_ready=False),
            "episode": lambda f: f.update(episode_run_id="other-episode"),
            "generation": lambda f: f["diagnostics"].update(connection_generation=2),
            "actor": lambda f: f["played_character"].update(character_id=30000),
            "target_membership": lambda f: f["active_wars"][0]["enemy_armies"].pop(),
            "subject_route": lambda f: f["player_armies"][0].update(current_province_id=2599),
            "history": lambda f: f["native_command_history"].append({"command": "unexpected", "ok": True}),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                old, observed = frame(), frame()
                mutate(observed)
                result, service = self.invoke(old, observed)
                self.assertFalse(result["checks"]["combined_final_snapshot_reobserved"])
                self.assertEqual(service.calls, [])
                self.assertEqual(result["query_attempts"], 2)
                self.assertIn("combined final frame changed", result["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

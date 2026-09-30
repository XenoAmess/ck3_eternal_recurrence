"""No-screen negative tests for the frozen A05 terminal frame proof."""

from __future__ import annotations

from copy import deepcopy
import unittest

from verify_e2_09_a05_fact_receipt import verify_terminal_frame


DATE = 53146992


def good_pair() -> tuple[dict, dict]:
    post = {"result": "CALL_COMPLETED", "body": {
        "date_raw": DATE, "paused": True, "revision": 19,
        "native_revision": 18, "snapshot_id": "native:18",
    }}
    writer = {"result": "CALL_COMPLETED", "body": {
        "accepted": True, "status": "available",
        "battle_terminal_transition_ready": True,
        "snapshot_revision": 18, "queried_revision": 19,
        "queried_native_revision": 18, "queried_snapshot_id": "native:18",
        "source": {"date_raw": DATE, "paused": True, "revision": 19,
                   "native_revision": 18, "snapshot_id": "native:18"},
        "battle_terminal_transition": {
            "status": "available", "snapshot_revision": 18,
            "observed_date_raw": DATE, "prior_combat_id": 16777218,
            "subject_public_cunit_id": 18,
            "terminal_journal": {"event_status": "observed"},
            "prior": {"combat_id": 16777218, "terminal_kind": "normal_result",
                      "battle_warscore": {"war_id": 4}},
            "removal": {"prior_combat_strictly_resolves": False,
                        "prior_province_contains_prior_combat_id": False},
            "subject": {"exists": True, "native_carmy_id": 18,
                        "combat_backlink_id": None, "active_combat_id": None},
            "successor": {"state": "subject_retreating"},
        },
    }}
    return writer, post


class TerminalFrameTest(unittest.TestCase):
    def test_bound_terminal_closure(self) -> None:
        writer, post = good_pair()
        verify_terminal_frame(writer, post, DATE)

    def test_rejects_unbound_or_nonterminal_receipts(self) -> None:
        mutations = {
            "rejected_query": lambda w, p: w["body"].update(accepted=False),
            "source_date": lambda w, p: w["body"]["source"].update(date_raw=DATE + 24),
            "source_pause": lambda w, p: w["body"]["source"].update(paused=False),
            "native_revision": lambda w, p: w["body"].update(queried_native_revision=17),
            "snapshot_id": lambda w, p: w["body"].update(queried_snapshot_id="native:17"),
            "post_snapshot": lambda w, p: p["body"].update(snapshot_id="native:19"),
            "wrapper_revision": lambda w, p: w["body"].update(queried_revision=20),
            "old_combat_live": lambda w, p: w["body"]["battle_terminal_transition"]
            ["removal"].update(prior_combat_strictly_resolves=True),
            "army_in_combat": lambda w, p: w["body"]["battle_terminal_transition"]
            ["subject"].update(active_combat_id=16777218),
            "wrong_war": lambda w, p: w["body"]["battle_terminal_transition"]
            ["prior"]["battle_warscore"].update(war_id=5),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                writer, post = map(deepcopy, good_pair())
                mutate(writer, post)
                with self.assertRaises(ValueError):
                    verify_terminal_frame(writer, post, DATE)


if __name__ == "__main__":
    unittest.main()

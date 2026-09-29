from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.physical_army_inventory_v1 import (  # noqa: E402
    validate_native_physical_inventory_mailbox_v1,
    validate_physical_army_inventory_shape_v1,
)


DATE = 53_219_928
WAR = 16_777_231
SUBJECT = 83_886_367
ENEMY = 50_331_920


def receipt() -> dict:
    return {
        "status": "complete", "source_build": "CK3 1.19.0.6",
        "snapshot_id": "native:7", "revision": 8, "native_revision": 7,
        "episode_run_id": "native-29829-2bc2d599f7f9",
        "connection_generation": 3, "date_raw": DATE,
        "war_id": WAR, "subject_army_id": SUBJECT,
        "storage_capacity": 4, "slots_scanned": 4, "empty_slots": 2,
        "canonical_units": 2, "invalid_id_slots": 0,
        "noncanonical_slots": 0, "unresolved_slots": 0,
        "player_army_ids": [SUBJECT], "allied_army_ids": [SUBJECT],
        "hostile_army_ids": [ENEMY],
        "contact_hostile_army_ids": [ENEMY],
        "retreating_hostile_army_ids": [],
        "units": [
            {"army_id": SUBJECT, "owner_character_id": 29_829,
             "current_province_id": 2610, "war_side": "allied",
             "route_read_status": "complete_empty", "retreating": False,
             "route_source_count": 0, "route_province_ids": [],
             "army_state_code": 1, "in_combat": False,
             "controllable": True},
            {"army_id": ENEMY, "owner_character_id": 30_097,
             "current_province_id": 2629, "war_side": "hostile",
             "route_read_status": "complete_nonempty", "retreating": False,
             "route_source_count": 1, "route_province_ids": [2610],
             "army_state_code": 1, "in_combat": False,
             "controllable": False},
        ],
    }


def check(data: dict, *, published: list[int] | None = None,
          players: list[int] | None = None,
          allies: list[int] | None = None,
          request: list[int] | None = None,
          result: list[int] | None = None):
    return validate_physical_army_inventory_shape_v1(
        data, expected_date_raw=DATE, expected_war_id=WAR,
        expected_subject_army_id=SUBJECT,
        expected_snapshot_id="native:7", expected_revision=8,
        expected_native_revision=7,
        expected_episode_run_id="native-29829-2bc2d599f7f9",
        expected_connection_generation=3,
        published_player_ids=[SUBJECT] if players is None else players,
        published_allied_ids=[SUBJECT] if allies is None else allies,
        published_enemy_ids=[ENEMY] if published is None else published,
        contact_request_ids=[ENEMY] if request is None else request,
        contact_result_ids=[ENEMY] if result is None else result,
    )


def mailbox_fixture() -> tuple[dict, dict, dict]:
    native = receipt()
    for key in ("snapshot_id", "revision", "episode_run_id", "connection_generation"):
        del native[key]
    native.update({
        "query_sequence": 9, "mailbox_pump_epoch": 11,
        "mailbox_thread_id": 5, "mailbox_date_raw": DATE,
        "mailbox_paused": True, "same_source_across_route": True,
    })
    snapshot = {
        "map_ready": True, "paused": True, "snapshot_id": "native:7", "revision": 8,
        "native_revision": 7, "episode_run_id": "native-29829-2bc2d599f7f9",
        "date_raw": DATE, "diagnostics": {"connection_generation": 3},
        "episode_character_id": 29_829, "active_event": None,
        "pending_character_interaction": None,
        "route_contact_horizon_supported": True,
        "played_character": {"character_id": 29_829},
        "player_armies": [{"army_id": SUBJECT,
                            "owner_character_id": 29_829,
                            "controllable": True}],
        "active_wars": [{"war_id": WAR,
                         "allied_armies": [{"army_id": SUBJECT}],
                         "enemy_armies": [{"army_id": ENEMY}]}],
    }
    horizon = {"hostile_army_ids": [ENEMY]}
    return native, snapshot, horizon


def check_mailbox(native: dict, snapshot: dict, horizon: dict,
                  *, current: dict | None = None):
    return validate_native_physical_inventory_mailbox_v1(
        native, starting=snapshot,
        current=snapshot if current is None else current,
        horizon=horizon, query_sequence=9, subject_army_id=SUBJECT,
        requested_hostiles=(ENEMY,),
    )


class PhysicalInventoryShapeTests(unittest.TestCase):
    def test_main_thread_mailbox_candidate_is_still_read_only(self) -> None:
        native, snapshot, horizon = mailbox_fixture()
        checked = check_mailbox(native, snapshot, horizon)
        self.assertTrue(checked.valid)
        self.assertEqual(checked.reason, "shape_valid_only")
        self.assertFalse(checked.date_or_action_authorized)

    def test_mailbox_rejects_missing_slot_wrong_frame_and_wrong_source(self) -> None:
        native, snapshot, horizon = mailbox_fixture()
        for key, value in (
            ("slots_scanned", 3), ("unresolved_slots", 1),
            ("mailbox_pump_epoch", 0), ("mailbox_date_raw", DATE + 24),
            ("native_revision", 6), ("same_source_across_route", False),
            ("query_sequence", 10),
        ):
            with self.subTest(key=key):
                changed = copy.deepcopy(native)
                changed[key] = value
                self.assertFalse(check_mailbox(changed, snapshot, horizon).valid)
        changed_snapshot = copy.deepcopy(snapshot)
        changed_snapshot["diagnostics"]["connection_generation"] = 4
        self.assertFalse(check_mailbox(native, snapshot, horizon,
                                       current=changed_snapshot).valid)
        changed_snapshot = copy.deepcopy(snapshot)
        changed_snapshot["revision"] = 9
        self.assertFalse(check_mailbox(native, snapshot, horizon,
                                       current=changed_snapshot).valid)
        changed_snapshot = copy.deepcopy(snapshot)
        changed_snapshot["played_character"]["character_id"] = 29_830
        self.assertEqual(check_mailbox(native, snapshot, horizon,
                                       current=changed_snapshot).reason,
                         "public_frame_changed")
        changed_snapshot = copy.deepcopy(snapshot)
        changed_snapshot["map_ready"] = False
        self.assertFalse(check_mailbox(native, snapshot, horizon,
                                       current=changed_snapshot).valid)
        for key, value in (
            ("active_event", {"instance_id": 7}),
            ("pending_character_interaction", {"interaction_id": 9}),
            ("route_contact_horizon_supported", False),
        ):
            with self.subTest(key=key):
                changed_snapshot = copy.deepcopy(snapshot)
                changed_snapshot[key] = value
                self.assertFalse(check_mailbox(native, snapshot, horizon,
                                               current=changed_snapshot).valid)
        wrong_actor = copy.deepcopy(snapshot)
        wrong_actor["played_character"]["character_id"] = 29_830
        wrong_actor["player_armies"][0]["owner_character_id"] = 29_830
        self.assertEqual(check_mailbox(native, wrong_actor, horizon).reason,
                         "h3937_actor_binding_mismatch")
        wrong_episode = copy.deepcopy(snapshot)
        wrong_episode["episode_run_id"] = "native-other"
        self.assertEqual(check_mailbox(native, wrong_episode, horizon).reason,
                         "h3937_episode_or_subject_mismatch")
        wrong_war = copy.deepcopy(snapshot)
        wrong_war["active_wars"][0]["war_id"] = WAR + 1
        self.assertEqual(check_mailbox(native, wrong_war, horizon).reason,
                         "h3937_war_mismatch")

    def test_mailbox_rejects_retreat_and_ambiguous_war(self) -> None:
        native, snapshot, horizon = mailbox_fixture()
        native["units"][1]["retreating"] = True
        native["contact_hostile_army_ids"] = []
        native["retreating_hostile_army_ids"] = [ENEMY]
        self.assertFalse(check_mailbox(native, snapshot, horizon).valid)
        native, snapshot, horizon = mailbox_fixture()
        snapshot["active_wars"].append(copy.deepcopy(snapshot["active_wars"][0]))
        self.assertEqual(check_mailbox(native, snapshot, horizon).reason,
                         "war_scope_ambiguous")

    def test_good_shape_still_cannot_authorize_gameplay(self) -> None:
        observed = check(receipt())
        self.assertTrue(observed.valid)
        self.assertFalse(observed.date_or_action_authorized)
        self.assertEqual(observed.reason, "shape_valid_only")

    def test_missing_header_and_partial_never_mean_empty(self) -> None:
        for mutation in ({"status": "partial"}, {"storage_capacity": 0},
                         {"slots_scanned": 3}, {"unresolved_slots": 1},
                         {"invalid_id_slots": 1}, {"noncanonical_slots": 1}):
            with self.subTest(mutation=mutation):
                data = receipt()
                data.update(mutation)
                self.assertFalse(check(data).valid)

    def test_identity_and_generation_must_match(self) -> None:
        for key, value in (("source_build", "CK3 1.19.0.5"),
                           ("snapshot_id", "native:6"),
                           ("revision", 7), ("native_revision", 6),
                           ("episode_run_id", "old"),
                           ("connection_generation", 2),
                           ("date_raw", DATE + 24), ("war_id", WAR + 1),
                           ("subject_army_id", SUBJECT + 1)):
            with self.subTest(key=key):
                data = receipt()
                data[key] = value
                self.assertFalse(check(data).valid)

    def test_physical_and_query_sets_are_distinct_checks(self) -> None:
        data = receipt()
        self.assertFalse(check(data, players=[]).valid)
        self.assertFalse(check(data, allies=[]).valid)
        self.assertFalse(check(data, published=[ENEMY + 1]).valid)
        self.assertFalse(check(data, request=[ENEMY + 1]).valid)
        self.assertFalse(check(data, result=[ENEMY + 1]).valid)
        data["hostile_army_ids"] = []
        self.assertFalse(check(data).valid)

    def test_retreating_hostile_is_not_silently_excluded(self) -> None:
        data = receipt()
        data["units"][1]["retreating"] = True
        data["contact_hostile_army_ids"] = []
        data["retreating_hostile_army_ids"] = [ENEMY]
        self.assertEqual(check(data, request=[], result=[]).reason,
                         "retreating_hostile_risk_unproven")

    def test_invalid_route_owner_side_and_duplicate_row(self) -> None:
        for key, value in (("route_read_status", "target_only"),
                           ("route_read_status", ["complete_empty"]),
                           ("route_source_count", 2),
                           ("route_province_ids", [0]),
                           ("owner_character_id", None),
                           ("war_side", "unknown"),
                           ("war_side", ["hostile"]),
                           ("army_state_code", 6),
                           ("in_combat", True)):
            data = receipt()
            data["units"][1][key] = value
            self.assertFalse(check(data).valid)
        data = receipt()
        data["units"].append(copy.deepcopy(data["units"][1]))
        data["canonical_units"] = 3
        data["empty_slots"] = 1
        self.assertFalse(check(data).valid)


if __name__ == "__main__":
    unittest.main()

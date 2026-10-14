from pathlib import Path

import pytest

from xar_autoplayer.bridge.war_hotspot_camera import (
    LandedProvinceIndex,
    follow_war_hotspot,
    select_war_hotspot,
)


def test_title_index_and_observed_hotspot_priority(tmp_path: Path) -> None:
    title_dir = tmp_path / "game" / "common" / "landed_titles"
    title_dir.mkdir(parents=True)
    (title_dir / "00_landed_titles.txt").write_text(
        """e_test = { d_test = { c_messina = {
            b_messina = { province = 2633 color = { 1 2 3 } }
            b_cefalu = { province = 2634 }
        } c_siracusa = { b_syracuse = { province = 2638 } } } }
        """,
        encoding="utf-8",
    )
    index = LandedProvinceIndex.from_game_dir(tmp_path)
    assert index.barony_by_province[2633] == "b_messina"
    snapshot = {
        "revision": 110,
        "active_wars": [
            {
                "war_id": 4,
                "allied_armies": [
                    {
                        "army_id": 18,
                        "in_combat": True,
                        "current_province_id": 2633,
                        "move_target_province_id": 2638,
                        "controllable": True,
                    }
                ],
                "war_objective_province_ids": [2638],
            }
        ],
    }
    assert select_war_hotspot(snapshot, index) == {
        "reason": "battle", "priority": 0, "war_id": 4, "army_id": 18,
        "province_id": 2633, "title_key": "b_messina", "county_key": "c_messina",
    }

    class Service:
        def center_map_on_landed_title_v1(self, title_key: str, *, expected_revision: int) -> dict:
            assert (title_key, expected_revision) == ("b_messina", 110)
            return {
                "status": "centered", "title": {"key": "b_messina"},
                "camera_center": {"postcondition_verified": True},
            }

    parks = []

    def park() -> dict:
        parks.append("before_native_camera")
        return {"status": "parked", "parked_screen_xy": [512, 560]}

    followed = follow_war_hotspot(Service(), snapshot, index, park_cursor=park)
    assert followed["status"] == "centered"
    assert parks == ["before_native_camera"]
    assert followed["cursor_park"]["status"] == "parked"


def test_sea_does_not_displace_land_objective(tmp_path: Path) -> None:
    title_dir = tmp_path / "game" / "common" / "landed_titles"
    title_dir.mkdir(parents=True)
    (title_dir / "00_landed_titles.txt").write_text(
        "c_siracusa = { b_syracuse = { province = 2638 } }",
        encoding="utf-8",
    )
    index = LandedProvinceIndex.from_game_dir(tmp_path)
    hotspot = select_war_hotspot(
        {"active_wars": [{
            "war_id": 4,
            "allied_armies": [{"army_id": 18, "in_combat": False,
                               "current_province_id": 8653, "controllable": True}],
            "war_objective_province_ids": [2638],
        }]},
        index,
    )
    assert hotspot is not None
    assert hotspot["province_id"] == 2638
    assert hotspot["title_key"] == "b_syracuse"


def test_moving_army_follows_observed_position_not_distant_destination(tmp_path: Path) -> None:
    title_dir = tmp_path / "game" / "common" / "landed_titles"
    title_dir.mkdir(parents=True)
    (title_dir / "00_landed_titles.txt").write_text(
        "c_one = { b_current = { province = 10 } } "
        "c_two = { b_target = { province = 20 } }",
        encoding="utf-8",
    )
    snapshot = {"active_wars": [{
        "war_id": 1,
        "allied_armies": [{"army_id": 5, "controllable": True,
                           "current_province_id": 10,
                           "move_target_province_id": 20}],
        "war_objective_province_ids": [20],
    }]}
    index = LandedProvinceIndex.from_game_dir(tmp_path)
    land_hotspot = select_war_hotspot(snapshot, index)
    assert land_hotspot is not None
    assert (land_hotspot["reason"], land_hotspot["province_id"]) == (
        "moving_player_army", 10
    )
    snapshot["active_wars"][0]["allied_armies"][0]["current_province_id"] = 8653
    sea_hotspot = select_war_hotspot(snapshot, index)
    assert sea_hotspot is not None
    assert (sea_hotspot["reason"], sea_hotspot["province_id"]) == (
        "army_destination", 20
    )


def test_controlled_battle_outranks_other_allied_battle(tmp_path: Path) -> None:
    title_dir = tmp_path / "game" / "common" / "landed_titles"
    title_dir.mkdir(parents=True)
    (title_dir / "00_landed_titles.txt").write_text(
        "c_one = { b_one = { province = 10 } } "
        "c_two = { b_two = { province = 20 } }",
        encoding="utf-8",
    )
    index = LandedProvinceIndex.from_game_dir(tmp_path)
    hotspot = select_war_hotspot({"active_wars": [{
        "war_id": 1,
        "allied_armies": [
            {"army_id": 1, "in_combat": True, "controllable": False,
             "current_province_id": 10},
            {"army_id": 20, "in_combat": True, "controllable": True,
             "current_province_id": 20},
        ],
    }]}, index)
    assert hotspot is not None
    assert hotspot["province_id"] == 20
    assert hotspot["priority"] == 0


def test_camera_requires_verified_native_result(tmp_path: Path) -> None:
    title_dir = tmp_path / "game" / "common" / "landed_titles"
    title_dir.mkdir(parents=True)
    (title_dir / "00_landed_titles.txt").write_text(
        "c_test = { b_test = { province = 12 } }", encoding="utf-8"
    )
    index = LandedProvinceIndex.from_game_dir(tmp_path)

    class Service:
        def center_map_on_landed_title_v1(self, *_args: object, **_kwargs: object) -> dict:
            return {"status": "centered", "title": {"key": "b_test"},
                    "camera_center": {"postcondition_verified": False}}

    with pytest.raises(ValueError, match="verified native postcondition"):
        follow_war_hotspot(
            Service(), {"revision": 1, "active_wars": [{"war_id": 1,
                "war_objective_province_ids": [12]}]}, index
        )
    with pytest.raises(ValueError, match="cursor was not parked"):
        follow_war_hotspot(
            Service(), {"revision": 1, "active_wars": [{"war_id": 1,
                "war_objective_province_ids": [12]}]}, index,
            park_cursor=lambda: {"status": "ck3_not_foreground"},
        )


def test_minimized_ck3_skips_pointer_move_but_keeps_native_postcondition(
    tmp_path: Path,
) -> None:
    title_dir = tmp_path / "game" / "common" / "landed_titles"
    title_dir.mkdir(parents=True)
    (title_dir / "00_landed_titles.txt").write_text(
        "c_test = { b_test = { province = 12 } }", encoding="utf-8"
    )
    index = LandedProvinceIndex.from_game_dir(tmp_path)
    calls = []

    class Service:
        def center_map_on_landed_title_v1(
            self, title_key: str, *, expected_revision: int
        ) -> dict:
            calls.append((title_key, expected_revision))
            return {"status": "centered", "title": {"key": title_key},
                    "camera_center": {"postcondition_verified": True}}

    followed = follow_war_hotspot(
        Service(),
        {"revision": 4, "active_wars": [{
            "war_id": 1, "war_objective_province_ids": [12]}]},
        index,
        park_cursor=lambda: {"status": "skipped_minimized", "ck3_pid": 321},
    )
    assert calls == [("b_test", 4)]
    assert followed["status"] == "centered"
    assert followed["cursor_park"]["status"] == "skipped_minimized"


def test_automatic_follow_reuses_only_an_exact_paused_frame() -> None:
    import copy
    from types import SimpleNamespace
    index = LandedProvinceIndex({10: "b_one", 20: "b_two"}, {}, ())
    snapshot = {"paused": True, "map_ready": True, "snapshot_id": "native:7",
        "revision": 4, "native_revision": 7, "date_raw": 1000, "episode_run_id": "episode",
        "played_character": {"character_id": 8, "alive": True},
        "diagnostics": {"bridge_pid": 99, "connection_generation": 3},
        "active_wars": [{"war_id": 1, "allied_armies": [
            {"army_id": 5, "controllable": True, "current_province_id": 10}]}]}
    calls, parks = [], []
    def center(title_key, *, expected_revision):
        calls.append((title_key, expected_revision))
        return {"status": "already_centered", "title": {"key": title_key},
                "camera_center": {"postcondition_verified": True}}
    service = SimpleNamespace(center_map_on_landed_title_v1=center)
    def park():
        parks.append(1)
        return {"status": "skipped_other_virtual_desktop"}
    first = follow_war_hotspot(service, snapshot, index, park_cursor=park, reuse_same_frame=True)
    second = follow_war_hotspot(service, copy.deepcopy(snapshot), index, park_cursor=park, reuse_same_frame=True)
    assert first["status"] == "already_centered"
    assert second["status"] == "reused_same_frame_anchor"
    assert second["native_command_submitted"] is False
    assert second["camera_receipt"] == first["camera_receipt"]
    assert second["camera_receipt_source"] == "previous_same_frame"
    assert second["camera_receipt"] is not first["camera_receipt"]
    assert calls == [("b_one", 4)] and parks == [1]
    # Explicit presentation requests always issue a new native read.
    follow_war_hotspot(service, snapshot, index)
    assert len(calls) == 2

    changes = [
        {"revision": 5}, {"native_revision": 8}, {"date_raw": 1024},
        {"snapshot_id": "native:8"}, {"episode_run_id": "next-episode"},
        {"played_character": {"character_id": 9, "alive": True}},
        {"diagnostics": {"bridge_pid": 100, "connection_generation": 3}},
        {"diagnostics": {"bridge_pid": 99, "connection_generation": 4}},
    ]
    for change in changes:
        service._war_hotspot_camera_anchor = None
        follow_war_hotspot(service, snapshot, index, reuse_same_frame=True)
        before = len(calls)
        follow_war_hotspot(service, {**snapshot, **change}, index, reuse_same_frame=True)
        assert len(calls) == before + 1
    moved = copy.deepcopy(snapshot)
    moved["active_wars"][0]["allied_armies"][0]["current_province_id"] = 20
    follow_war_hotspot(service, moved, index, reuse_same_frame=True)
    assert calls[-1][0] == "b_two"


def test_failed_camera_postcondition_is_never_reused() -> None:
    from types import SimpleNamespace
    calls = []
    def center(*args, **kwargs):
        calls.append(1)
        return {"status": "centered", "title": {"key": "b_one"},
                "camera_center": {"postcondition_verified": False}}
    service = SimpleNamespace(center_map_on_landed_title_v1=center)
    snapshot = {"revision": 1, "active_wars": [
        {"allied_armies": [{"army_id": 1, "controllable": True, "current_province_id": 10}]}]}
    for _ in range(2):
        with pytest.raises(ValueError, match="postcondition"):
            follow_war_hotspot(service, snapshot, LandedProvinceIndex({10: "b_one"}, {}, ()),
                               reuse_same_frame=True)
    assert calls == [1, 1]

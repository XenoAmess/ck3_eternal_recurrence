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

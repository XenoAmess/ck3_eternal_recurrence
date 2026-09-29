"""No-screen admission and same-frame negative cases for the d06 operator."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from e2_04_d06_knight_live import (
    ACTOR, ARMY, CHARACTER, COMBAT, DATE, PROVINCE, REGIMENT, WAR,
    control_case, knight_case, snapshot_case, verify_no_launch, verify_session,
)


PREFLIGHT = Path("D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d06-knight-preflight-20260929-a02")
OLD_CONTROL = Path("D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d06-v3-live-20260929-a08-a02/ck3-output/interactive-requests-responses/a08-d06-cold-control.json")


def frame() -> dict:
    return {"date_raw": DATE, "paused": True,
            "played_character": {"character_id": ACTOR},
            "revision": 5, "native_revision": 3, "snapshot_id": "native:3",
            "active_wars": [{"war_id": WAR, "allied_armies": [
                {"army_id": ARMY, "army_state": "combat", "current_province_id": PROVINCE,
                 "controllable": True, "in_combat": True}]}]}


def control() -> dict:
    return {"accepted": True, "status": "available", "queried_revision": 5,
            "queried_native_revision": 3, "queried_snapshot_id": "native:3",
            "snapshot_revision": 3,
            "source": {"revision": 5, "native_revision": 3, "snapshot_id": "native:3",
                       "paused": True, "date_raw": DATE},
            "battle_control_snapshot": {
                "status": "available", "battle_control_ready": True,
                "snapshot_revision": 3, "observed_date_raw": DATE,
                "subject_public_cunit_id": ARMY, "subject_native_carmy_id": ARMY,
                "selected_owner_character_id": ACTOR, "combat_id": COMBAT,
                "combat_province_id": PROVINCE,
                "defender": {"men_at_arms_entries": [{"regiment_id": REGIMENT,
                                                      "damage_raw": 15000000}]}}}


def knight() -> dict:
    return {"accepted": True, "status": "available", "queried_revision": 5,
            "queried_native_revision": 3, "queried_snapshot_id": "native:3",
            "snapshot_revision": 3,
            "source": {"revision": 5, "native_revision": 3, "snapshot_id": "native:3"},
            "current_battle_knight": {
                "schema": "current-battle-knight-v1", "observed_date_raw": DATE,
                "combat_id": COMBAT, "province_id": PROVINCE,
                "subject_public_cunit_id": ARMY, "native_carmy_id": ARMY,
                "character_id": CHARACTER, "regiment_id": REGIMENT,
                "paired_generation_ids_verified": True, "double_sample_stable": True,
                "province_evaluation_fresh": True, "scale": 100000,
                "current_effective_prowess": 11, "knight_effectiveness_raw": 500000,
                "province_evaluated_damage_raw": 11000000,
                "province_evaluated_toughness_raw": 2200000,
                "stored_combat_entry_damage_raw": 15000000,
                "stored_combat_entry_toughness_raw": 3000000}}


class D06KnightOperatorTest(unittest.TestCase):
    def test_real_ready_no_launch_and_red_a01(self) -> None:
        if not PREFLIGHT.is_dir():
            self.skipTest("external a02 no-launch not mounted")
        bound = verify_no_launch(PREFLIGHT)
        self.assertEqual(bound["preflight"]["sha256"],
                         "EACE028F6AD8ACBEF29004FFF833722F82DF3E383C9814BFB6C1467C49C76488")
        with self.assertRaisesRegex(ValueError, "a01 no-launch was RED"):
            verify_no_launch(PREFLIGHT.with_name("episode02-e2-04-d06-knight-preflight-20260929-a01"))

    def test_snapshot_requires_one_paused_d06_army_and_frame(self) -> None:
        self.assertEqual(snapshot_case(frame())["native_revision"], 3)
        for mutation in (lambda x: x.update(paused=False),
                         lambda x: x.update(snapshot_id="native:4"),
                         lambda x: x["active_wars"].append(copy.deepcopy(x["active_wars"][0])),
                         lambda x: x["active_wars"][0]["allied_armies"][0].update(in_combat=False)):
            changed = frame()
            mutation(changed)
            with self.assertRaises(ValueError):
                snapshot_case(changed)

    def test_control_requires_unique_regiment_and_exact_frame(self) -> None:
        f = snapshot_case(frame())
        self.assertEqual(control_case(control(), f)["combat_id"], COMBAT)
        duplicate = control()
        duplicate["battle_control_snapshot"]["defender"]["men_at_arms_entries"].append(
            {"regiment_id": REGIMENT})
        with self.assertRaisesRegex(ValueError, "unique"):
            control_case(duplicate, f)
        stale = control()
        stale["queried_revision"] = 4
        with self.assertRaisesRegex(ValueError, "same frame"):
            control_case(stale, f)

    def test_old_control_only_checks_parser_shape(self) -> None:
        if not OLD_CONTROL.is_file():
            self.skipTest("archived a08 d06 control not mounted")
        response = json.loads(OLD_CONTROL.read_text(encoding="utf-8"))
        body = response["body"]
        source = body["source"]
        old_frame = {"revision": source["revision"],
                     "native_revision": source["native_revision"],
                     "snapshot_id": source["snapshot_id"]}
        parsed = control_case(body, old_frame)
        self.assertEqual(parsed["regiment_61_stored_entry"]["regiment_id"], 61)

    def test_current_values_distinguish_fresh_from_stored(self) -> None:
        f = snapshot_case(frame())
        values = knight_case(knight(), f)
        self.assertEqual(values["province_evaluated_damage_raw"], 11000000)
        self.assertEqual(values["stored_combat_entry_damage_raw"], 15000000)
        for mutation in (lambda x: x["current_battle_knight"].update(character_id=12),
                         lambda x: x["current_battle_knight"].update(province_evaluation_fresh=False),
                         lambda x: x.update(queried_native_revision=4),
                         lambda x: x["current_battle_knight"].update(current_effective_prowess=True)):
            changed = knight()
            mutation(changed)
            with self.assertRaises(ValueError):
                knight_case(changed, f)

    def test_cleanup_binding_does_not_require_gui_observation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            live = root / "episode02-e2-04-d06-knight-live-20260929-test"
            output = live / "ck3-output"
            output.mkdir(parents=True)
            (output / "interactive-requests").mkdir()
            (output / "interactive-requests-responses").mkdir()
            offline = root / "episode02-e2-04-d06-knight-offline-20260929-test" / "steam-offline-reviewed.json"
            offline.parent.mkdir()
            offline.write_text("{}", encoding="utf-8")
            script = root / "capture_session.py"
            script.write_text("capture", encoding="utf-8")
            no_launch = root / "episode02-e2-04-d06-knight-preflight-20260929-test"
            no_launch.mkdir()
            (no_launch / "run-argv.json").write_text(
                json.dumps({"argv": ["python", str(script)]}), encoding="utf-8")
            (output / "preflight.json").write_text(json.dumps({"result": "READY_FOR_BOUNDED_LIVE_ATTEMPT"}), encoding="utf-8")
            (output / "native-start-readback.json").write_text(
                json.dumps({"postcondition_verified": True}), encoding="utf-8")
            (output / "command.json").write_text(json.dumps({
                "argv": [str(script), "--steam-offline-receipt", str(offline), "--capture"]}),
                encoding="utf-8")
            from e2_04_d06_knight_live import identity
            prior = {"capture_script_sha256": identity(script)["sha256"]}
            with patch("e2_04_d06_knight_live.verify_no_launch", return_value=prior), \
                    patch("e2_04_d06_knight_live.verify_preflight"), \
                    patch("e2_04_d06_knight_live.bound_source"):
                self.assertEqual(verify_session(output, no_launch, require_gui=False)["gui"],
                                 "not_a_cleanup_prerequisite")
                with self.assertRaises(FileNotFoundError):
                    verify_session(output, no_launch)


if __name__ == "__main__":
    unittest.main()

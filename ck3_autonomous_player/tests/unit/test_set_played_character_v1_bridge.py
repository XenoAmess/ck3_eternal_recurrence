from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.mcp_server import _ck3_set_played_character_v1
from xar_autoplayer.bridge.native_driver import _action_steps
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.set_played_character_contract import (
    SET_PLAYED_CHARACTER_V1_CAPABILITY,
    set_played_character_v1_step,
    validate_character_id,
)


class _Driver:
    def __init__(self) -> None:
        self.snapshot = {
            "snapshot_id": "fixture:7",
            "revision": 7,
            "native_revision": 17,
            "date_raw": 53_246_712,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 32_904, "alive": True},
        }
        self.calls: list[tuple[int, int]] = []

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "set-player-fixture",
            "source": "fixture",
            "snapshot": True,
            "wait_for_change": True,
            "action_steps": [],
            "bridge_capabilities": [SET_PLAYED_CHARACTER_V1_CAPABILITY],
        }

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshot)

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        raise AssertionError("generic rebind must use its typed driver method")

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        return self.take_snapshot()

    def set_player_character_v1(
        self, character_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        self.calls.append((character_id, expected_revision))
        prior = self.snapshot["played_character"]["character_id"]
        self.snapshot["revision"] = expected_revision + 1
        self.snapshot["snapshot_id"] = f"fixture:{expected_revision + 1}"
        self.snapshot["played_character"] = {
            "character_id": character_id,
            "alive": True,
        }
        return {
            "schema_version": 1,
            "step": set_played_character_v1_step(character_id),
            "accepted": True,
            "status": "switched",
            "from_character_id": prior,
            "to_character_id": character_id,
            "before_revision": expected_revision,
            "after_revision": expected_revision + 1,
            "native_revision": 18,
            "date_raw": self.snapshot["date_raw"],
            "paused": True,
            "map_ready": True,
            "postcondition_verified": True,
            "backend_id": "native-headless",
        }


class SetPlayedCharacterV1Tests(unittest.TestCase):
    def test_character_id_contract_and_step_are_canonical(self) -> None:
        self.assertEqual(validate_character_id(30_938), 30_938)
        self.assertEqual(
            set_played_character_v1_step(30_938),
            "set-played-character-v1-30938",
        )
        for invalid in (None, True, 0, -1, 2**31):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    validate_character_id(invalid)

    def test_operator_rebind_never_enters_planner_steps(self) -> None:
        self.assertEqual(
            _action_steps([SET_PLAYED_CHARACTER_V1_CAPABILITY]), []
        )

    def test_service_and_mcp_facade_delegate_typed_rebind(self) -> None:
        driver = _Driver()
        service = GameplayBridgeService(driver)
        result = _ck3_set_played_character_v1(service, 30_938, 7)
        self.assertEqual(driver.calls, [(30_938, 7)])
        self.assertEqual(result["from_character_id"], 32_904)
        self.assertEqual(result["to_character_id"], 30_938)
        self.assertIs(result["postcondition_verified"], True)


if __name__ == "__main__":
    unittest.main()

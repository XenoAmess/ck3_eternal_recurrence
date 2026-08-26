from __future__ import annotations

import importlib.util
from pathlib import Path
import json
import tempfile
from types import SimpleNamespace
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "native_bridge"
    / "research"
    / "run_owner_subset_retreat_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_owner_subset_retreat_live_acceptance", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


def _frame(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "status": "available",
        "battle_control_ready": True,
        "selected_public_cunit_id": HARNESS.OWNER_SUBSET_CUNIT_ID,
        "selected_native_carmy_id": HARNESS.OWNER_SUBSET_NATIVE_CARMY_ID,
        "selected_owner_character_id": HARNESS.OWNER_SUBSET_CHARACTER_ID,
        "side_index": HARNESS.EXPECTED_SIDE_INDEX,
        "side_scope": "owner_subset",
        "affected_public_cunit_ids_in_stored_order": [
            HARNESS.OWNER_SUBSET_CUNIT_ID
        ],
        "unaffected_same_side_public_cunit_ids_in_stored_order": [
            HARNESS.UNCONTROLLED_ALLY_CUNIT_ID
        ],
        "battle_control_snapshot": {"combat_id": HARNESS.COMBAT_ID},
    }
    value.update(overrides)
    return value


class OwnerSubsetRetreatLiveAcceptanceTests(unittest.TestCase):
    def test_every_fresh_stage_uses_the_exact_continue_slot_name(self) -> None:
        self.assertEqual(HARNESS.CONTINUE_SAVE_NAME, "autosave.ck3")
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(source.count("save_name=CONTINUE_SAVE_NAME"), 4)

    def test_seed_inbox_uses_guarded_exact_player_switch_effect(self) -> None:
        effect = HARNESS._seed_switch_effect()
        self.assertIn(
            f"NOT = {{ global_var:{HARNESS.SEED_GUARD_VARIABLE} = 1 }}",
            effect,
        )
        self.assertIn(
            f"province:{HARNESS.TARGET_CHARACTER_ANCHOR_PROVINCE_ID} = {{",
            effect,
        )
        self.assertIn("province_owner = {", effect)
        self.assertIn(
            "save_temporary_scope_as = xar_fixture_owner_subset_target",
            effect,
        )
        self.assertIn(
            "set_player_character = scope:xar_fixture_owner_subset_target",
            effect,
        )
        self.assertIn(HARNESS.SEED_SWITCH_MARKER, effect)
        self.assertNotIn("ExecuteConsoleCommand", effect)
        self.assertNotIn("play 36108", effect)
        self.assertNotIn("character:36108", effect)

    def test_seed_target_anchor_requires_exact_war_opponent_and_province(self) -> None:
        snapshot = {
            "active_wars": [
                {
                    "war_id": 16_777_290,
                    "player_side": "attacker",
                    "primary_opponent_character_id": (
                        HARNESS.OWNER_SUBSET_CHARACTER_ID
                    ),
                    "enemy_primary_default_raise_province_id": (
                        HARNESS.TARGET_CHARACTER_ANCHOR_PROVINCE_ID
                    ),
                }
            ]
        }
        self.assertTrue(HARNESS._validate_seed_target_anchor(snapshot))
        snapshot["active_wars"][0]["primary_opponent_character_id"] = 1
        self.assertFalse(HARNESS._validate_seed_target_anchor(snapshot))

    def test_seed_clear_effect_removes_guard_and_marks_completion(self) -> None:
        effect = HARNESS._seed_clear_effect()
        self.assertIn(
            f"exists = global_var:{HARNESS.SEED_GUARD_VARIABLE}", effect
        )
        self.assertIn(
            f"remove_global_variable = {HARNESS.SEED_GUARD_VARIABLE}",
            effect,
        )
        self.assertIn(HARNESS.SEED_CLEAR_MARKER, effect)

    def test_seed_inbox_atomic_writer_preserves_bom_and_exact_noop(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-owner-inbox-") as temporary:
            inbox = Path(temporary) / "run" / "xar_mcp_inbox.txt"
            identity = HARNESS._write_seed_inbox(
                inbox, HARNESS.SEED_NOOP_INBOX
            )
            self.assertTrue(identity["utf8_bom"])
            self.assertTrue(inbox.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertEqual(
                inbox.read_text(encoding="utf-8-sig"),
                HARNESS.SEED_NOOP_INBOX,
            )
            self.assertEqual(list(inbox.parent.glob(".xar_mcp_inbox.*.tmp")), [])

    def test_seed_bridge_stages_existing_mod_bridge_as_second_mod(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-owner-bridge-") as temporary:
            profile = Path(temporary) / "profile"
            (profile / "mod").mkdir(parents=True)
            (profile / "mod-content").mkdir(parents=True)
            evidence = HARNESS._install_seed_bridge(
                SimpleNamespace(profile_dir=profile)
            )
            self.assertEqual(
                evidence["enabled_mods"],
                ["mod/xar_autoplayer.mod", "mod/xar_mcp_bridge.mod"],
            )
            target = Path(evidence["target"])
            self.assertEqual(
                (target / "gui" / "xar_mcp_bridge.gui").read_bytes(),
                (
                    HARNESS.MOD_BRIDGE_SOURCE
                    / "gui"
                    / "xar_mcp_bridge.gui"
                ).read_bytes(),
            )
            self.assertEqual(
                (profile / "run" / "xar_mcp_inbox.txt").read_text(
                    encoding="utf-8-sig"
                ),
                HARNESS.SEED_NOOP_INBOX,
            )
            self.assertEqual(
                json.loads((profile / "dlc_load.json").read_text()),
                {
                    "enabled_mods": [
                        "mod/xar_autoplayer.mod",
                        "mod/xar_mcp_bridge.mod",
                    ],
                    "disabled_dlcs": [],
                },
            )

    def test_exact_owner_subset_frame_is_accepted(self) -> None:
        self.assertTrue(HARNESS._validate_owner_subset_frame(_frame()))

    def test_wrong_scope_identity_or_order_is_rejected(self) -> None:
        for overrides in (
            {"side_scope": "full_side"},
            {"selected_owner_character_id": 29_829},
            {"selected_native_carmy_id": 345},
            {
                "affected_public_cunit_ids_in_stored_order": [
                    HARNESS.UNCONTROLLED_ALLY_CUNIT_ID
                ]
            },
            {
                "unaffected_same_side_public_cunit_ids_in_stored_order": [
                    HARNESS.OWNER_SUBSET_CUNIT_ID
                ]
            },
        ):
            with self.subTest(overrides=overrides):
                self.assertFalse(
                    HARNESS._validate_owner_subset_frame(_frame(**overrides))
                )

    def test_played_character_id_is_strict(self) -> None:
        self.assertEqual(
            HARNESS._played_character_id(
                {
                    "played_character": {
                        "character_id": HARNESS.OWNER_SUBSET_CHARACTER_ID
                    }
                }
            ),
            HARNESS.OWNER_SUBSET_CHARACTER_ID,
        )
        self.assertIsNone(
            HARNESS._played_character_id(
                {"played_character": {"character_id": True}}
            )
        )

    def test_expected_sha256_is_canonicalized(self) -> None:
        self.assertEqual(
            HARNESS._expected_sha256("ab" * 32), ("AB" * 32)
        )
        with self.assertRaises(ValueError):
            HARNESS._expected_sha256("not-a-hash")

    def test_day15_advance_frame_freezes_both_defender_owners(self) -> None:
        frame = {
            "status": "available",
            "battle_control_ready": True,
            "selected_public_cunit_id": HARNESS.ORIGINAL_ATTACKER_CUNIT_ID,
            "side_index": 0,
            "side_scope": "full_side",
            "battle_control_snapshot": {
                "combat_id": HARNESS.COMBAT_ID,
                "phase": "main",
                "phase_day": 12,
                "attacker": {
                    "ordered_armies": [
                        {
                            "public_cunit_id": (
                                HARNESS.ORIGINAL_ATTACKER_CUNIT_ID
                            )
                        }
                    ]
                },
                "defender": {
                    "ordered_armies": [
                        {"public_cunit_id": HARNESS.OWNER_SUBSET_CUNIT_ID},
                        {
                            "public_cunit_id": (
                                HARNESS.UNCONTROLLED_ALLY_CUNIT_ID
                            )
                        },
                    ]
                },
            },
        }
        self.assertTrue(HARNESS._validate_advance_frame(frame))
        frame["battle_control_snapshot"]["defender"]["ordered_armies"].reverse()
        self.assertFalse(HARNESS._validate_advance_frame(frame))


if __name__ == "__main__":
    unittest.main()

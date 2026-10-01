"""Patch source selection retains historical migrations and deferred domains."""

from pathlib import Path
import sys
import unittest
import importlib.util
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.vanilla_events import query_vanilla_event_knowledge_v1
from xar_autoplayer.vanilla_events.builds import SUPPORTED_CK3_EXE_SHA256
from xar_autoplayer.vanilla_events.source_index import load_vanilla_event_source_index


class PatchVanillaRegistryTests(unittest.TestCase):
    def test_reviewed_patch_policy_replays_preserve_choices_without_live_claims(self):
        root = Path(__file__).resolve().parents[3]
        spec = importlib.util.spec_from_file_location("patch_event_replay", root / "tools/replay_vanilla_event_research.py")
        replay = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(replay)
        fixtures = json.loads((root / "ck3_autonomous_player/tests/fixtures/vanilla_event_migration_12002_replay.json").read_text())
        for row in fixtures["cases"]:
            with self.subTest(case=row.get("id", row["expected_native_option_index"])):
                encoded = json.dumps(row["bundle"]).replace("1.20.0.2", "1.20.0.3").replace(
                    SUPPORTED_CK3_EXE_SHA256["1.20.0.2"], SUPPORTED_CK3_EXE_SHA256["1.20.0.3"])
                report = replay.replay_bytes(encoded.encode("utf-8"))
                self.assertEqual(report["policy"]["status"], "recommended")
                self.assertEqual(report["policy"]["ck3_build"], "1.20.0.3")
                self.assertEqual(report["policy"]["selected_native_option_index"], row["expected_native_option_index"])
                self.assertFalse(report["new_live_evidence"])
                self.assertEqual(report["gameplay_commands_submitted"], 0)

    def test_patch_dataset_and_epidemic_dependency_are_independent(self):
        old = query_vanilla_event_knowledge_v1("epidemic_events.1100", "1.20.0.2")
        new = query_vanilla_event_knowledge_v1("epidemic_events.1100", "1.20.0.3")
        self.assertEqual((old["status"], new["status"]), ("available", "available"))
        self.assertEqual(old["contract"], new["contract"])
        self.assertEqual(old["analysis"]["exact_build"]["game_version"], "1.20.0.2")
        self.assertEqual(new["analysis"]["exact_build"], {
            "game_version": "1.20.0.3", "steam_build_id": 25652598,
            "ck3_executable_sha256": SUPPORTED_CK3_EXE_SHA256["1.20.0.3"],
        })
        self.assertNotEqual(old["analysis"]["source_sha256"]["common/scripted_effects/pam_effects.txt"],
                            new["analysis"]["source_sha256"]["common/scripted_effects/pam_effects.txt"])
        self.assertFalse(new["analysis"]["migration_1_20_0_3"]["new_live_evidence"])
        source = load_vanilla_event_source_index(build="1.20.0.3")
        self.assertEqual(source["ck3_exe_sha256"], SUPPORTED_CK3_EXE_SHA256["1.20.0.3"])
        self.assertEqual(len(source["events"]), 192)

    def test_deferred_events_remain_unavailable_on_both_patch_builds(self):
        for build in ("1.20.0.2", "1.20.0.3"):
            for key in ("fervor.1002", "court_chaplain_task.0313", "great_holy_war.0011"):
                with self.subTest(build=build, key=key):
                    result = query_vanilla_event_knowledge_v1(key, build)
                    self.assertEqual(result["unavailable_reason"], "event_domain_owner_deferred")


if __name__ == "__main__":
    unittest.main()

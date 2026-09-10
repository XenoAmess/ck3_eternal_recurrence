from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import zg361_phase2_legacy_seed_migration_job as migration


def source_bytes(player: int = 33596113) -> bytes:
    return (f'''SAV0102
save_game_version=15
version="1.18.3.1"
meta_date=1164.3.29
meta_player_name="Legacy ruler"
meta_title_name="Legacy duchy"
meta_player_tier=4
meta_government=celestial_government
ironman=no
meta_main_portrait={{
 id={player}
 }}
meta_heir_portrait={{
 }}
'''.encode() + b"PK\x03\x04legacy-payload")


def make_plan(root: Path, player: int = 33596113) -> dict[str, object]:
    source = root / "legacy.ck3"
    source.write_bytes(source_bytes(player))
    executable = root / "ck3.exe"
    executable.write_bytes(b"exact-game-build")
    bridge = root / "bridge.dll"
    bridge.write_bytes(b"bridge")
    injector = root / "injector.exe"
    injector.write_bytes(b"injector")
    product = root / "product"
    product.mkdir()
    manifest = root / "product.json"
    manifest.write_text("{}", encoding="utf-8")
    return migration.build_no_launch_plan(
        source_save=source, expected_source_sha256=migration.sha256_file(source),
        target_executable=executable, expected_target_executable_sha256=migration.sha256_file(executable),
        bridge_dll=bridge, bridge_injector=injector,
        product_projection=product, product_manifest=manifest,
    )


class FakeService:
    def __init__(self, root: Path, plan: dict[str, object]) -> None:
        self.save_calls = []
        self.saved_path = root / "current-exact.ck3"
        self.saved_path.write_bytes(b"SAV0101current-save")
        target = plan["target"]
        self.snapshot_value = {
            "revision": 7, "date_raw": 53300000, "paused": True, "map_ready": True,
            "active_event": None,
            "played_character": {"character_id": target["required_player_character_id"], "alive": True},
            "diagnostics": {"bridge_pid": 999, "connection_generation": 1, "hello": {
                "ck3_build_match": True, "expected_ck3_version": target["game_version"],
                "expected_ck3_sha256": target["executable_sha256"],
                "game_adapter_id": target["required_adapter_id"], "game_adapter_status": "ready",
                "pid": 999, "connection_generation": 1,
                "capabilities": ["game.command.save-checkpoint"],
            }},
        }

    def snapshot(self):
        return copy.deepcopy(self.snapshot_value)

    def capabilities(self):
        return {}

    def save_checkpoint(self, *, expected_revision):
        self.save_calls.append(expected_revision)
        return {"accepted": True, "checkpoint": {
            "status": "saved", "path": str(self.saved_path), "size": self.saved_path.stat().st_size,
            "sha256": migration.sha256_file(self.saved_path), "date_raw": 53300000,
            "episode_character_id": self.snapshot_value["played_character"]["character_id"],
        }}


class LegacySeedMigrationTests(unittest.TestCase):
    def test_plan_derives_identity_from_hash_bound_source_without_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            plan = make_plan(Path(temporary), player=123456)
        self.assertEqual(plan["target"]["required_player_character_id"], 123456)
        self.assertEqual(plan["migration_round"]["playset"], "no-custom-mods")
        self.assertFalse(plan["launch_attempted"])
        self.assertFalse(plan["ck3_control_attempted"])

    def test_native_resave_receipt_preserves_scope_and_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = make_plan(root)
            service = FakeService(root, plan)
            receipt = migration.migrate_already_bound(service, plan, root / "receipt.json")
            self.assertEqual(service.save_calls, [7])
            self.assertEqual(receipt["checkpoint"]["header"], "SAV0101")
            self.assertEqual(receipt["binding"]["player_character_id"], 33596113)
            self.assertEqual(receipt["source_sha256"], migration.sha256_file(root / "legacy.ck3"))
            self.assertFalse(receipt["product_seed_ready"])
            self.assertEqual(receipt["before_snapshot"]["date_raw"], receipt["after_snapshot"]["date_raw"])

    def test_active_event_preserves_session_without_saving(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = make_plan(root)
            service = FakeService(root, plan)
            service.snapshot_value["active_event"] = {"instance_id": 1}
            with self.assertRaises(migration.MigrationError) as raised:
                migration.migrate_already_bound(service, plan, root / "receipt.json")
            self.assertEqual(service.save_calls, [])
            self.assertFalse(raised.exception.evidence["checks"]["no_active_event"])
            self.assertFalse((root / "receipt.json").exists())

    def test_materialization_mounts_no_custom_mod_and_preserves_source_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = make_plan(root)
            startup = root / "startup"
            (startup / "shadercache").mkdir(parents=True)
            (startup / "shadercache/cache.bin").write_bytes(b"cache")
            bound = {"plan": plan, "state_directory": root / "state",
                     "game_directory": root, "startup_template_profile": startup}
            runner = SimpleNamespace(
                project_particle2_startup_shader_bundle=mock.Mock(return_value={"result": "GREEN"}),
                terminal=SimpleNamespace(render_settings=lambda: "settings-fixture"),
            )
            materialization = migration.materialize_migration_profile(bound, runner)
            profile = root / "state/profile"
            self.assertEqual(json.loads((profile / "dlc_load.json").read_text()),
                             {"enabled_mods": [], "disabled_dlcs": []})
            self.assertFalse((profile / "mod-content").exists())
            self.assertFalse(materialization["custom_mods_loaded"])
            self.assertEqual(materialization["source_materialization"][0]["sha256"], plan["source"]["sha256"])

    def test_cleanup_green_preserves_failed_migration_result(self):
        job = migration.LegacySeedMigrationJob(Path("unused.json"))
        job.migration_result = "RED"
        job.failure_reason = "migration failed"
        job.state = "MIGRATION_RED_NO_LIVE_PROCESS"
        with mock.patch.object(migration.operator, "ck3_pids", return_value=[]):
            status = job.perform_cleanup()
        self.assertEqual(status["migration_result"], "RED")
        self.assertEqual(status["cleanup_result"], "GREEN")
        self.assertEqual(status["result"], "RED")
        self.assertFalse(status["product_seed_ready"])

    def test_successful_worker_runs_managed_cleanup_after_migration(self):
        job = migration.LegacySeedMigrationJob(Path("unused.json"))
        bound = {"kind": "test-bound"}
        with mock.patch.object(migration, "validate_operator_activation", return_value=bound), \
             mock.patch.object(job, "_execute") as execute, \
             mock.patch.object(job, "perform_cleanup") as cleanup, \
             mock.patch.object(migration.operator, "ck3_pids", return_value=[]), \
             mock.patch("builtins.print"):
            job._run()
        execute.assert_called_once_with(bound)
        cleanup.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()

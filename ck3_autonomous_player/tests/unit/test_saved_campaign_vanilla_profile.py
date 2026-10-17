"""Saved inputs are copied only after an explicit frozen profile inventory."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

PACKAGE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE / "src"))
SPEC = importlib.util.spec_from_file_location("vanilla_saved_host_tests",
    PACKAGE / "native_bridge/research/run_ck3_12002_mcp_live.py")
HOST = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOST)
VANILLA = "ck3-saved-campaign-vanilla-profile-v1"
PRODUCT = "ck3-saved-campaign-product-only-profile-v1"


class SavedVanillaProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profile = self.root / "state/profile"
        self.profile.mkdir(parents=True)
        self.source = self.root / "checkpoint.ck3"
        self.source.write_bytes(b"immutable checkpoint input")
        self.inventory_path = self.root / "inventory.json"
        self.inventory = {"schema": VANILLA, "profile_path": str(self.profile),
            "enabled_mods": [], "product_files": []}
        self.enabled_mods = []
        self.args = SimpleNamespace(saved_campaign_save=self.source,
            saved_campaign_save_bytes=self.source.stat().st_size,
            saved_campaign_save_sha256=hashlib.sha256(self.source.read_bytes()).hexdigest(),
            saved_campaign_player_id=15893, saved_campaign_date_raw=51394920,
            saved_campaign_product_inventory=self.inventory_path)
        self.spec = SimpleNamespace(profile_dir=self.profile, state_dir=self.profile.parent)

    def prepare(self):
        (self.profile / "dlc_load.json").write_text(json.dumps({"enabled_mods": self.enabled_mods}), encoding="utf-8")
        self.inventory_path.write_text(json.dumps(self.inventory), encoding="utf-8")
        return HOST.prepare_saved_campaign(self.args, self.spec)

    def test_explicit_empty_vanilla_inventory_copies_exact_input(self):
        receipt = self.prepare()
        self.assertEqual(Path(receipt["copied_save_path"]).read_bytes(), self.source.read_bytes())
        self.assertEqual(receipt["status"], "IMMUTABLE_SAVE_COPIED_TO_FRESH_VANILLA_PROFILE")
        self.assertEqual(receipt["profile_inventory_schema"], VANILLA)
        self.assertFalse(receipt["source_game_state_claimed"])
        self.assertFalse(receipt["product_acceptance_proven"])

    def test_product_schema_cannot_masquerade_as_empty_vanilla(self):
        self.inventory["schema"] = PRODUCT
        with self.assertRaisesRegex(ValueError, "requires nonempty"):
            self.prepare()
        self.assertFalse((self.profile / "save games").exists())

    def test_vanilla_schema_requires_both_lists_exactly_empty(self):
        for key in ("enabled_mods", "product_files"):
            with self.subTest(key=key):
                self.inventory[key] = ["unadmitted"]
                self.enabled_mods = self.inventory["enabled_mods"]
                with self.assertRaisesRegex(ValueError, "exactly empty"):
                    self.prepare()
                self.inventory[key] = []
                self.enabled_mods = []
        self.assertFalse((self.profile / "save games").exists())

    def test_vanilla_keeps_profile_and_actual_enabled_mod_binding(self):
        for change in ("profile", "enabled", "unknown"):
            with self.subTest(change=change):
                original = dict(self.inventory)
                if change == "profile":
                    self.inventory["profile_path"] = str(self.root / "another-profile")
                elif change == "enabled":
                    self.enabled_mods = ["mod/fixture.mod"]
                else:
                    self.inventory["schema"] = "unqualified-empty-profile"
                with self.assertRaisesRegex(ValueError, "does not bind"):
                    self.prepare()
                self.inventory = original
                self.enabled_mods = []

    def product(self, *, registrar=False):
        product = self.root / "frozen-product"
        product.mkdir()
        script = product / "events.txt"
        script.write_text("on_game_start_after_lobby = {}" if registrar else "namespace = test", encoding="utf-8")
        descriptor = self.profile / "mod/test.mod"
        descriptor.parent.mkdir()
        descriptor.write_text('path="' + product.as_posix() + '"\n', encoding="utf-8")
        self.enabled_mods = ["mod/test.mod"]
        self.inventory.update(schema=PRODUCT, enabled_mods=list(self.enabled_mods),
            product_files=[{"path":str(path), "bytes":path.stat().st_size,
                "sha256":hashlib.sha256(path.read_bytes()).hexdigest()} for path in (descriptor, script)])
        return script

    def test_original_product_projection_still_admitted(self):
        self.product()
        self.assertEqual(self.prepare()["status"], "IMMUTABLE_SAVE_COPIED_TO_FRESH_PRODUCT_ONLY_PROFILE")

    def test_product_hash_and_cold_registrar_guards_are_preserved(self):
        script = self.product(registrar=True)
        with self.assertRaisesRegex(ValueError, "cold-start registrar"):
            self.prepare()
        script.write_text("mutated", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "file changed"):
            self.prepare()
        self.assertFalse((self.profile / "save games").exists())

    def test_vanilla_does_not_relax_exact_save_hash_or_freshness(self):
        self.args.saved_campaign_save_sha256 = "0" * 64
        with self.assertRaisesRegex(ValueError, "input bytes/SHA"):
            self.prepare()
        with self.assertRaisesRegex(ValueError, "fresh profile"):
            self.prepare()


if __name__ == "__main__":
    unittest.main()

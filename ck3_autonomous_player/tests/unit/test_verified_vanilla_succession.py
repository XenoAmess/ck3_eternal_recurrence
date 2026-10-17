"""Portable fixture-only absent-mod evidence tests; no runtime assertions."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from xar_autoplayer.bridge import succession_transition_contract as module


def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


class VanillaSuccession(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="vanilla-fixture-")
        root = Path(self.temp.name); profile = root / "profile"; (profile / "logs").mkdir(parents=True)
        dlc = profile / "dlc_load.json"; dlc.write_text('{"enabled_mods": [], "disabled_dlcs": []}')
        log = root / "REVIEWED-STARTUP-SNAPSHOT.txt"; log.write_text("Fixture explicit loaded mod list: []\n")
        self.manifest = {"rules": {"profile": []}, "environment_sha256": "a" * 64,
            "profile_dir": str(profile), "load_profile": {"enabled_mods": [], "dlc_load_sha256": pin(dlc)["sha256"]},
            "verified_mod_absence": {"schema": "xar.verified-xar-mod-absence/v1",
                "status": "ACTUAL_PROFILE_AND_STARTUP_LOG_VERIFIED", "reviewer": "/root",
                "enabled_mods_known": True, "loaded_mods_known": True, "startup_log_reviewed": True,
                "enabled_mods": [], "loaded_mods": [], "environment_sha256": "a" * 64,
                "game_pid": 1, "game_creation_filetime": 2, "profile_dir": str(profile),
                "profile_enabled_mods": pin(dlc), "startup_log_snapshot": pin(log),
                "startup_log_original_path": str(profile / "logs/setup.log")}}

    def tearDown(self):
        self.temp.cleanup()

    def bind(self, value, **kwargs):
        return module.bind_succession_lifecycle_from_environment_v1(value,
            lifecycle=module.ORDINARY_CAMPAIGN_SUCCESSION, ordinary_campaign_no_pact=True, **kwargs)

    def test_known_empty_evidence_binds_normalizes_and_legacy_off_unchanged(self):
        result = self.bind(self.manifest)
        self.assertIsNone(result["xar_enabled"])
        self.assertEqual(result["source"], "absent_by_verified_xar_mod_not_loaded")
        self.assertEqual(module.normalize_succession_lifecycle_binding_v1(result), result)
        legacy = {"rules": {"profile": [{"rule": "xar_enabled", "setting": "xar_off"}]}, "environment_sha256": "b" * 64}
        self.assertEqual(self.bind(legacy)["pact_contract"], "absent_by_fresh_campaign_xar_off_contract")

    def test_missing_unknown_or_nonempty_are_not_off(self):
        mutations = [lambda v: v.pop("verified_mod_absence"),
            lambda v: v["load_profile"].pop("enabled_mods"),
            lambda v: v["load_profile"].update(enabled_mods=["mod/xar.mod"]),
            lambda v: v["verified_mod_absence"].update(loaded_mods_known=False),
            lambda v: v["verified_mod_absence"].update(loaded_mods=["xar"]),
            lambda v: v["verified_mod_absence"].update(startup_log_reviewed=False),
            lambda v: v["verified_mod_absence"].update(environment_sha256="c" * 64),
            lambda v: v["rules"].update(profile=[{"rule": "xar_enabled", "setting": "xar_on"}])]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                value = copy.deepcopy(self.manifest); mutation(value)
                with self.assertRaises(ValueError): self.bind(value)

    def test_tampered_log_or_profile_pin_and_missing_no_pact_reject(self):
        for key in ("profile_enabled_mods", "startup_log_snapshot"):
            value = copy.deepcopy(self.manifest); value["verified_mod_absence"][key]["sha256"] = "f" * 64
            with self.assertRaises(ValueError): self.bind(value)
        with self.assertRaises(ValueError):
            module.bind_succession_lifecycle_from_environment_v1(self.manifest,
                lifecycle=module.ORDINARY_CAMPAIGN_SUCCESSION, ordinary_campaign_no_pact=False)
        with self.assertRaises(ValueError):
            module.bind_succession_lifecycle_from_environment_v1(self.manifest,
                lifecycle=module.ROGUE_ONE_LIFE, ordinary_campaign_no_pact=False)

    def test_foreign_profile_unreviewed_or_unbound_identity_rejects(self):
        mutations = {
            "profile": lambda v: v["verified_mod_absence"].update(profile_dir=str(Path(v["profile_dir"]).parent)),
            "log_origin": lambda v: v["verified_mod_absence"].update(startup_log_original_path=str(Path(v["profile_dir"]) / "not-the-log.txt")),
            "reviewer": lambda v: v["verified_mod_absence"].update(reviewer="unknown"),
            "missing_pid": lambda v: v["verified_mod_absence"].pop("game_pid"),
            "boolean_pid": lambda v: v["verified_mod_absence"].update(game_pid=True),
            "missing_birth": lambda v: v["verified_mod_absence"].pop("game_creation_filetime"),
            "boolean_birth": lambda v: v["verified_mod_absence"].update(game_creation_filetime=True),
            "unknown_enabled": lambda v: v["verified_mod_absence"].update(enabled_mods_known=False),
            "missing_digest": lambda v: v.pop("environment_sha256"),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                value = copy.deepcopy(self.manifest)
                mutate(value)
                with self.assertRaises(ValueError):
                    self.bind(value)


if __name__ == "__main__":
    unittest.main()

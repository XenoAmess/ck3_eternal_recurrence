from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.steam_workshop_status import (  # noqa: E402
    SteamWorkshopStatusInspector,
    load_steam_workshop_profile,
)


class SteamWorkshopStatusTests(unittest.TestCase):
    def _fixture(self, root: Path):
        steam = root / "steam"
        library = root / "library"
        (steam / "config").mkdir(parents=True)
        (steam / "steam.exe").write_bytes(b"steam")
        (steam / "config" / "loginusers.vdf").write_text(
            '"users" { "42" { "WantsOfflineMode" "1" } }',
            encoding="utf-8",
        )
        steamapps = library / "steamapps"
        executable = steamapps / "common" / "CK3" / "binaries" / "ck3.exe"
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"fixture-executable")
        (steamapps / "appmanifest_1158310.acf").write_text(
            '"AppState" { "appid" "1158310" "buildid" "23530548" '
            '"StateFlags" "4" "installdir" "CK3" }',
            encoding="utf-8",
        )
        workshop = steamapps / "workshop"
        cache = workshop / "content" / "1158310" / "3784706360"
        cache.mkdir(parents=True)
        (cache / "descriptor.mod").write_bytes(b"name=fixture\n")
        (workshop / "appworkshop_1158310.acf").write_text(
            '"AppWorkshop" { "WorkshopItemsInstalled" { "3784706360" '
            '{ "manifest" "999" } } "WorkshopItemDetails" { "3784706360" '
            '{ "manifest" "999" } } }',
            encoding="utf-8",
        )
        payload = {
            "steam_root": str(steam),
            "library_root": str(library),
            "app": {
                "app_id": "1158310",
                "expected_build_id": "23530548",
                "executable_relative_path": "binaries/ck3.exe",
                "expected_executable_sha256": hashlib.sha256(
                    executable.read_bytes()
                ).hexdigest(),
            },
            "process_names": ["steam.exe", "ck3.exe", "dowser.exe"],
            "workshop_items": [
                {
                    "item_id": "3784706360",
                    "display_name": "Fixture",
                    "expected_manifest_id": "999",
                }
            ],
        }
        return load_steam_workshop_profile(payload)

    def test_status_is_profile_driven_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = self._fixture(Path(temporary))
            result = SteamWorkshopStatusInspector(
                profile,
                process_pids=lambda name: [7] if name == "steam.exe" else [],
            ).query_v1()

            self.assertTrue(result["read_only"])
            self.assertFalse(result["caller_supplied_app_or_item"])
            self.assertTrue(result["steam"]["offline_attested"])
            self.assertEqual(result["steam"]["processes"]["steam.exe"], [7])
            self.assertTrue(result["app"]["build_matches_expected"])
            self.assertTrue(result["app"]["executable_matches_expected"])
            self.assertEqual(len(result["app"]["manifest_sha256"]), 64)
            self.assertTrue(result["workshop"]["all_installed_match_latest"])
            self.assertTrue(result["workshop"]["all_pinned_expectations_match"])
            self.assertEqual(
                len(result["workshop"]["manifest_sha256"]), 64
            )
            item = result["workshop"]["items"][0]
            self.assertTrue(item["descriptor_exists"])
            self.assertEqual(item["installed_manifest_id"], "999")

    def test_profile_rejects_arbitrary_relative_escape_and_duplicate_item(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = self._fixture(Path(temporary))
            payload = {
                "steam_root": str(profile.steam_root),
                "library_root": str(profile.library_root),
                "app": {
                    "app_id": profile.app_id,
                    "expected_build_id": profile.expected_build_id,
                    "executable_relative_path": "../outside.exe",
                    "expected_executable_sha256": profile.expected_executable_sha256,
                },
                "workshop_items": [
                    {"item_id": "1", "display_name": "A"},
                ],
            }
            with self.assertRaisesRegex(ValueError, "contained relative path"):
                load_steam_workshop_profile(payload)
            payload["app"]["executable_relative_path"] = "binaries/ck3.exe"
            payload["workshop_items"].append(
                {"item_id": "1", "display_name": "B"}
            )
            with self.assertRaisesRegex(ValueError, "must be unique"):
                load_steam_workshop_profile(payload)

    def test_profile_rejects_unreviewed_or_credential_like_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile = self._fixture(Path(temporary))
            payload = {
                "steam_root": str(profile.steam_root),
                "library_root": str(profile.library_root),
                "app": {
                    "app_id": profile.app_id,
                    "expected_build_id": profile.expected_build_id,
                    "executable_relative_path": "binaries/ck3.exe",
                    "expected_executable_sha256": (
                        profile.expected_executable_sha256
                    ),
                },
                "workshop_items": [
                    {"item_id": "1", "display_name": "A"},
                ],
                "password": "must-not-be-accepted",
            }
            with self.assertRaisesRegex(ValueError, "unknown keys"):
                load_steam_workshop_profile(payload)


if __name__ == "__main__":
    unittest.main()

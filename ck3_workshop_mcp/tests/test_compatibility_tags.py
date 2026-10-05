from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ck3_workshop_mcp.compatibility_tags import (
    CK3_WORKSHOP_VERSION_TAGS,
    compatibility_tag_from_descriptor,
    compatibility_tags_for_staging,
)


class CompatibilityTagsTests(unittest.TestCase):
    def test_numeric_and_wildcard_descriptor_versions_use_confirmed_minor(self):
        for version in ("1.20", "1.20.0", "1.20.0.3", "1.20.*", "1.20.*.*"):
            with self.subTest(version=version):
                self.assertEqual(
                    "1.20 'Crozier'",
                    compatibility_tag_from_descriptor(f'supported_version="{version}"\n'),
                )

    def test_old_versions_replaced_other_tags_preserved_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            staging = Path(directory)
            descriptor = staging / "descriptor.mod"
            raw = b'name="Fixture"\nsupported_version="1.20.0.3"\n'
            descriptor.write_bytes(raw)
            tags = ("Gameplay", "1.19 'Khans of the Steppe'", "Balance", "1.20", "Events", "1.20 mod features")
            expected = ("Gameplay", "Balance", "Events", "1.20 mod features", "1.20 'Crozier'")
            actual = compatibility_tags_for_staging(staging, tags)
            self.assertEqual(expected, actual)
            self.assertEqual(expected, compatibility_tags_for_staging(staging, actual))
            self.assertEqual(raw, descriptor.read_bytes())

    def test_staging_descriptor_is_authority_over_supplied_version_tag(self):
        with tempfile.TemporaryDirectory() as directory:
            staging = Path(directory)
            (staging / "descriptor.mod").write_text('supported_version="1.20.0.3"\n', encoding="utf-8")
            self.assertEqual(
                ("Gameplay", "1.20 'Crozier'"),
                compatibility_tags_for_staging(staging, ["Gameplay", "1.21 'Unconfirmed'"]),
            )

    def test_unknown_minor_fails_without_fabricating_label(self):
        for version in ("1.21.0", "2.0"):
            with self.subTest(version=version), self.assertRaisesRegex(ValueError, "no confirmed"):
                compatibility_tag_from_descriptor(f'supported_version="{version}"\n')

    def test_pre120_descriptor_returns_no_automatic_tag(self):
        for version in ("1.18.0.2", "1.19.0.6", "1.19.*"):
            with self.subTest(version=version):
                self.assertIsNone(compatibility_tag_from_descriptor(f'supported_version="{version}"\n'))

    def test_pre120_staging_preserves_all_original_tags(self):
        with tempfile.TemporaryDirectory() as directory:
            staging = Path(directory)
            raw = b'supported_version="1.19.0.6"\n'
            (staging / "descriptor.mod").write_bytes(raw)
            tags = ("Gameplay", "1.18 'Prior fixture'", "Balance", "1.19")
            self.assertEqual(tags, compatibility_tags_for_staging(staging, tags))
            self.assertEqual(raw, (staging / "descriptor.mod").read_bytes())

    def test_future_confirmed_registry_entry_automatically_replaces_old_minor(self):
        with tempfile.TemporaryDirectory() as directory:
            staging = Path(directory)
            (staging / "descriptor.mod").write_text('supported_version="1.21.0.1"\n', encoding="utf-8")
            # Synthetic registry entry tests extensibility; it is not a real
            # public version label and never leaves this patched test scope.
            with patch.dict(CK3_WORKSHOP_VERSION_TAGS, {"1.21": "1.21 'Confirmed test fixture'"}):
                self.assertEqual(
                    ("Gameplay", "1.21 'Confirmed test fixture'"),
                    compatibility_tags_for_staging(staging, ["Gameplay", "1.20 'Crozier'"]),
                )
            self.assertNotIn("1.21", CK3_WORKSHOP_VERSION_TAGS)

    def test_missing_duplicate_or_malformed_version_fails(self):
        for text in (
            '# supported_version="1.20.0.3"\n',
            'supported_version="1.20"\nsupported_version="1.20"\n',
            'supported_version="1.20"\nsupported_version="1.21" trailing junk\n',
            'supported_version="Crozier"\n',
            'supported_version="1.20.0.3.4"\n',
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                compatibility_tag_from_descriptor(text)

    def test_BOM_spacing_comments_and_CRLF_are_supported(self):
        self.assertEqual(
            "1.20 'Crozier'",
            compatibility_tag_from_descriptor('\ufeff# old supported_version="1.19"\r\n  supported_version = "1.20.0.3" # release\r\n'),
        )

    def test_invalid_tags_and_missing_staging_descriptor_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            for tags in ("Gameplay", [""], [None], {"Gameplay"}):
                with self.subTest(tags=tags), self.assertRaises(ValueError):
                    compatibility_tags_for_staging(directory, tags)
            with self.assertRaises(FileNotFoundError):
                compatibility_tags_for_staging(directory, ["Gameplay"])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Unit tests for public Steam Workshop publication verification."""

from __future__ import annotations

import unittest
import json
import tempfile
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import verify_workshop_publication as verify


TITLE = "Tributary Expansion Directives — 驱策朝贡国"
DESCRIPTION = "English\n\n中文"
NOTES = "Initial release.\n\n- One\n- Two"


def item_api(title: str = TITLE, description: str = DESCRIPTION) -> dict[str, object]:
    return {
        "response": {
            "publishedfiledetails": [
                {
                    "title": title,
                    "description": description,
                    "time_updated": 123,
                    "file_size": 456,
                }
            ]
        }
    }


class VerifyWorkshopPublicationTests(unittest.TestCase):
    def test_cli_timeout_default_and_explicit_longer_value_reach_both_fetches(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            description, notes = root / "description", root / "notes"
            description.write_text(DESCRIPTION, encoding="utf-8")
            notes.write_text(NOTES, encoding="utf-8")
            for index, extra in enumerate(([], ["--timeout", "2200"])):
                expected = 1800 if not extra else 2200
                with patch.object(verify, "fetch_public_item", return_value=json.dumps(item_api()).encode()) as item, \
                     patch.object(verify, "fetch_changelog", return_value=b'<p id="987">Initial release.<br><br>- One<br>- Two</p>') as changelog, \
                     redirect_stdout(StringIO()):
                    result = verify.main(["--item-id", "3182367229", "--title", TITLE,
                        "--description", str(description), "--change-notes", str(notes),
                        "--output", str(root / str(index)), *extra])
                self.assertEqual(result, 0)
                item.assert_called_once_with("3182367229", expected)
                changelog.assert_called_once_with("3182367229", expected)

    def test_exact_metadata_and_html_decoding(self) -> None:
        raw = '<p id="987">Initial release.<br><br>- One<br/>- Two</p>'
        result = verify.verify_payloads(
            item_api=item_api(),
            changelog_html=raw,
            expected_title=TITLE,
            expected_description=DESCRIPTION + "\n",
            expected_change_notes=NOTES + "\n",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["changelog_entry_id"], "987")
        self.assertEqual(result["change_notes_lines"], 4)
        self.assertEqual(
            result["change_notes_sha256"], result["expected_change_notes_sha256"]
        )

    def test_partial_or_different_notes_fail(self) -> None:
        raw = '<p id="987">Initial release.</p>'
        result = verify.verify_payloads(
            item_api=item_api(),
            changelog_html=raw,
            expected_title=TITLE,
            expected_description=DESCRIPTION,
            expected_change_notes=NOTES,
        )
        self.assertFalse(result["ok"])
        self.assertFalse(result["change_notes_exact"])

    def test_wrong_title_or_description_fail(self) -> None:
        raw = '<p id="987">Initial release.<br><br>- One<br>- Two</p>'
        result = verify.verify_payloads(
            item_api=item_api(title="Wrong", description="Wrong"),
            changelog_html=raw,
            expected_title=TITLE,
            expected_description=DESCRIPTION,
            expected_change_notes=NOTES,
        )
        self.assertFalse(result["ok"])
        self.assertFalse(result["title_exact"])
        self.assertFalse(result["description_exact"])

    def test_malformed_api_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unexpected shape"):
            verify.verify_payloads(
                item_api={},
                changelog_html="",
                expected_title=TITLE,
                expected_description=DESCRIPTION,
                expected_change_notes=NOTES,
            )


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Unit tests for public Steam Workshop publication verification."""

from __future__ import annotations

import unittest

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

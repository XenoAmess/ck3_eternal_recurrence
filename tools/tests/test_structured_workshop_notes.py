"""Necessary local-only regression Source using byte-exact captured public inputs.

No fetch and no old-verifier execution. A mutation is test DATA, never new public
evidence or a replacement for any original failed report.
"""
from pathlib import Path
import hashlib
import json
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify_structured_workshop_notes as verifier


FIXTURES = Path(__file__).parent / "fixtures" / "structured-workshop-notes"
PINS = {
    "public-changelog-original.html": (62449, "2ef6f3265310113366c88f5a93b5aadf234f10f7a53f0c8c6cda5d5f799e67c8"),
    "expected-change-notes-original.txt": (3307, "1655b358cec20068d00c8bbbf151685b413738e45d679b2cf19ef572ba28ba8a"),
    "item-api-original.raw": (8764, "f7633b0daf270fc2d42a9900e4cd6b435b8f4d88b4956597097c9bda22b8f7b4"),
}
ENTRY = re.compile(r'(<p id="1795491643">)(.*?)(</p>)', re.DOTALL)


def captured(name):
    raw = (FIXTURES / name).read_bytes()
    length, digest = PINS[name]
    if len(raw) != length or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("original portable public capture changed")
    return raw.decode("utf-8")


def edit_entry(page, function):
    matches = list(ENTRY.finditer(page))
    if len(matches) != 1:
        raise ValueError("test requires the one original observed entry")
    match = matches[0]
    return page[:match.start(2)] + function(match[2]) + page[match.end(2):]


class StructuredWorkshopNotesTest(unittest.TestCase):
    def setUp(self):
        self.page = captured("public-changelog-original.html")
        self.notes = captured("expected-change-notes-original.txt")
        self.api = json.loads(captured("item-api-original.raw"))

    def verify(self, *, page=None, notes=None):
        return verifier.verify_structured_notes(
            expected_change_notes=self.notes if notes is None else notes,
            changelog_html=self.page if page is None else page,
            item_api=self.api, item_id="3798404599")

    def test_complete_original_capture_matches_one_entry_and_full_format_tree(self):
        result = self.verify()
        self.assertTrue(result["ok"])
        self.assertEqual("1795491643", result["changelog_entry_id"])
        self.assertEqual(1, result["complete_semantic_match_count"])
        self.assertEqual(result["expected_full_semantic_sha256"], result["public_full_semantic_sha256"])
        counts = result["expected_structure_counts"]
        self.assertEqual((1, 1, 8, 2), tuple(counts[key] for key in ("heading1", "list", "item", "bold")))

    def test_text_spaces_and_inline_paragraph_breaks_are_all_significant(self):
        mutations = [
            lambda body: body.replace("Follows current vanilla vassalization", "Followz current vanilla vassalization", 1),
            lambda body: body.replace("current vanilla vassalization", "current  vanilla vassalization", 1),
            lambda body: body.replace("<br>Follows current vanilla", "Follows current vanilla", 1),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                changed = edit_entry(self.page, mutation)
                self.assertNotEqual(self.page, changed)
                self.assertFalse(self.verify(page=changed)["ok"])

    def test_missing_list_item_is_not_a_full_match(self):
        def remove_first(body):
            changed, count = re.subn(r"<li>.*?</li>", "", body, count=1, flags=re.DOTALL)
            self.assertEqual(1, count)
            return changed
        self.assertFalse(self.verify(page=edit_entry(self.page, remove_first))["ok"])

    def test_lost_bold_is_rejected_even_when_all_its_text_remains(self):
        changed = edit_entry(self.page, lambda body: body.replace("<b>", "", 1).replace("</b>", "", 1))
        self.assertFalse(self.verify(page=changed)["ok"])

    def test_lost_heading_is_rejected_without_dropping_heading_text(self):
        changed = edit_entry(self.page, lambda body: body.replace('<div class="bb_h1">', "", 1).replace("</div>", "", 1))
        self.assertFalse(self.verify(page=changed)["ok"])

    def test_lost_list_structure_is_rejected_with_every_item_word_retained(self):
        def flatten(body):
            return body.replace('<ul class="bb_ul">', "").replace("</ul>", "").replace("<li>", "").replace("</li>", "")
        self.assertFalse(self.verify(page=edit_entry(self.page, flatten))["ok"])

    def test_multiple_complete_matches_and_duplicate_entry_ids_are_refused(self):
        original = ENTRY.search(self.page).group(0)
        for duplicate in (original, original.replace('id="1795491643"', 'id="1795491644"', 1)):
            with self.subTest(same_id=duplicate == original):
                with self.assertRaises(ValueError):
                    self.verify(page=self.page + duplicate)

    def test_only_the_verified_block_lf_adjustments_are_allowed(self):
        changed_notes = self.notes.replace("[/h1]\n\n", "[/h1]\n\n\n", 1)
        self.assertNotEqual(self.notes, changed_notes)
        self.assertFalse(self.verify(notes=changed_notes)["ok"])
        doubled = edit_entry(self.page, lambda body: body.replace("</div><br>", "</div><br><br>", 1))
        self.assertFalse(self.verify(page=doubled)["ok"])
        extra_space = edit_entry(self.page, lambda body: body + " ")
        self.assertFalse(self.verify(page=extra_space)["ok"])
        decorated = edit_entry(self.page, lambda body: body.replace("<b>", '<b style="display:none">', 1))
        self.assertFalse(self.verify(page=decorated)["ok"])
        with self.assertRaises(ValueError):
            self.verify(notes="[i]unsupported format[/i]")


if __name__ == "__main__":
    unittest.main()

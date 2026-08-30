#!/usr/bin/env python3
"""Offline tests for the strict ZhongGuo 361 Workshop description gate."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


TOOLS_DIRECTORY = Path(__file__).resolve().parent
if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import validate_workshop_description as gate  # noqa: E402


COMMIT_A = "1" * 40
COMMIT_B = "2" * 40


def _description(
    *,
    commit: str = COMMIT_A,
    names: tuple[str, ...] | None = None,
) -> bytes:
    inventory = names or tuple(sorted(gate.EXPECTED_MEDIA_INVENTORY))
    lines = ["[h1]ZhongGuo 361[/h1]"]
    for name in inventory:
        lines.append(
            "[img]https://raw.githubusercontent.com/"
            "XenoAmess/ck3_eternal_recurrence/"
            f"{commit}/mod_zhongguo_style/workshop/media/{name}[/img]"
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def _write_inventory(directory: Path, names: set[str] | None = None) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in names or set(gate.EXPECTED_MEDIA_INVENTORY):
        (directory / name).write_bytes(b"fixture")


class WorkshopDescriptionGateTests(unittest.TestCase):
    def _validate(self, root: Path, data: bytes) -> gate.ValidationResult:
        description = root / "description.bbcode"
        description.write_bytes(data)
        media = root / "media"
        _write_inventory(media)
        return gate.validate_description(description, media)

    def test_accepts_sub_8000_byte_eight_image_single_commit_release(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self._validate(Path(temporary), _description())
        self.assertTrue(result.ok, result.errors)
        self.assertLess(result.byte_count, gate.MAX_DESCRIPTION_BYTES)
        self.assertEqual(8, result.image_count)
        self.assertEqual(COMMIT_A, result.commit_sha)
        self.assertEqual(
            tuple(sorted(gate.EXPECTED_MEDIA_INVENTORY)),
            result.media_inventory,
        )

    def test_rejects_description_at_exact_8000_byte_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data = _description()
            data += b"x" * (gate.MAX_DESCRIPTION_BYTES - len(data))
            self.assertEqual(gate.MAX_DESCRIPTION_BYTES, len(data))
            result = self._validate(Path(temporary), data)
        self.assertFalse(result.ok)
        self.assertTrue(any("below 8000" in error for error in result.errors))

    def test_rejects_lf_text_that_exceeds_limit_after_form_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data = _description()
            added_lines = 120
            padding = gate.MAX_DESCRIPTION_BYTES - 10 - len(data) - added_lines
            self.assertGreaterEqual(padding, 0)
            data += (b"x" * padding) + (b"\n" * added_lines)
            self.assertLess(len(data), gate.MAX_DESCRIPTION_BYTES)
            result = self._validate(Path(temporary), data)
        self.assertGreaterEqual(result.submitted_byte_count, gate.MAX_DESCRIPTION_BYTES)
        self.assertTrue(any("CRLF form projection" in error for error in result.errors))

    def test_rejects_invalid_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self._validate(Path(temporary), _description() + b"\xff")
        self.assertFalse(result.ok)
        self.assertTrue(any("not valid UTF-8" in error for error in result.errors))

    def test_rejects_six_images_without_blocking_main_static_validator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            names = tuple(sorted(gate.EXPECTED_MEDIA_INVENTORY))[:6]
            result = self._validate(Path(temporary), _description(names=names))
        self.assertFalse(result.ok)
        self.assertTrue(any("exactly 8" in error for error in result.errors))
        self.assertTrue(any("description image inventory mismatch" in error for error in result.errors))

    def test_rejects_mixed_or_non_commit_raw_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data = _description().replace(COMMIT_A.encode(), COMMIT_B.encode(), 1)
            data += (
                "https://raw.githubusercontent.com/XenoAmess/"
                "ck3_eternal_recurrence/main/README.md\n"
            ).encode("utf-8")
            result = self._validate(Path(temporary), data)
        self.assertFalse(result.ok)
        self.assertTrue(any("40-character" in error for error in result.errors))
        self.assertTrue(any("one identical" in error for error in result.errors))

    def test_rejects_wrong_referenced_and_tracked_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            names = list(sorted(gate.EXPECTED_MEDIA_INVENTORY))
            names[-1] = "08_wrong.jpg"
            description = root / "description.bbcode"
            description.write_bytes(_description(names=tuple(names)))
            media = root / "media"
            tracked = set(gate.EXPECTED_MEDIA_INVENTORY)
            tracked.remove("08_policy_361_charter.jpg")
            tracked.add("08_wrong.jpg")
            _write_inventory(media, tracked)
            result = gate.validate_description(description, media)
        self.assertFalse(result.ok)
        self.assertTrue(any("description image inventory mismatch" in error for error in result.errors))
        self.assertTrue(any("tracked Workshop media inventory mismatch" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()

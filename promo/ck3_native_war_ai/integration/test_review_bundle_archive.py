"""The native review package survives one bounded preservation artifact."""
from pathlib import Path
import tempfile
import unittest
import zipfile

from war_ai_promo.produce import archive_capture_attempt


class ReviewBundleArchiveTests(unittest.TestCase):
    def test_exact_review_tree_survives_bundle_and_existing_archive_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            review = root / "review"
            frames = review / "frames"
            frames.mkdir(parents=True)
            originals = {
                "review-package.json": b'{"state":"pending-human-review","approval_granted":false}',
                "review-template.json": b'{"is_signoff":false}',
                "frames/frame-000001.png": b"\x89PNG\r\n\x1a\nfirst-frame",
                "frames/frame-000106.png": b"\x89PNG\r\n\x1a\nfinal-frame",
            }
            for name, content in originals.items():
                path = review / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

            archive = root / "review-package-archive.zip"
            self.assertEqual(archive_capture_attempt(review, archive), archive)
            with zipfile.ZipFile(archive) as package:
                self.assertIsNone(package.testzip())
                self.assertEqual(package.namelist(), sorted(originals))
                self.assertEqual({name: package.read(name) for name in package.namelist()}, originals)
            self.assertEqual(archive_capture_attempt(review, root / "second.zip").read_bytes(),
                             archive.read_bytes())
            with self.assertRaises(FileExistsError):
                archive_capture_attempt(review, archive)
            self.assertEqual({name: (review / name).read_bytes() for name in originals}, originals)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Offline contracts for deterministic ZhongGuo Workshop media projections."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw


TOOLS_DIRECTORY = Path(__file__).resolve().parent
if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import compose_workshop_media as media  # noqa: E402
import prepare_promo_release_manifest as prepare  # noqa: E402
import test_prepare_promo_release_manifest as promo_fixture  # noqa: E402


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_test_capture(path: Path, mechanism_id: int) -> None:
    image = Image.new(
        "RGB",
        media.EXPECTED_SIZE,
        (30 + mechanism_id % 120, 50, 80),
    )
    draw = ImageDraw.Draw(image)
    draw.rectangle((420, 280, 1609, 874), outline=(240, 210, 120), width=12)
    draw.rectangle((500, 360, 1500, 780), fill=(60, 70, 90))
    draw.text((560, 420), f"TEST POLICY #{mechanism_id:03d}", fill="white")
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")


def _make_green_capture(root: Path, *, result: str = "GREEN") -> Path:
    capture = promo_fixture._make_capture(root, result=result)
    policy_images = []
    for mechanism_id in (1, 361):
        path = capture / "cell" / f"12_policy_{mechanism_id:03d}_event.png"
        _write_test_capture(path, mechanism_id)
        policy_images.append(path)
    promo_fixture._refresh_index_records(capture, *policy_images)
    return capture


class WorkshopMediaTests(unittest.TestCase):
    def test_base_projections_require_strict_23_person_live_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "legacy-base-capture"
            output = root / "projected"
            _write_json(
                artifacts / "report.json",
                {
                    "result": "GREEN",
                    "cell": {
                        "result": "GREEN",
                        "fixture_markers": [
                            "ZGA: DATA bootstrap_cohort_n 23",
                            "ZGA: DATA bootstrap_pending_375_n 7",
                            "ZGA: DATA bootstrap_pending_35_n 16",
                            "ZGA: DATA bootstrap_pending_325_n 0",
                        ]
                    },
                },
            )

            with self.assertRaisesRegex(
                ValueError, "strict 23-person 7/14/2 live marker"
            ):
                media.render(artifacts, output, check=False)
            self.assertFalse(output.exists())

            _write_json(
                artifacts / "report.json",
                {
                    "result": "GREEN",
                    "cell": {
                        "result": "GREEN",
                        "fixture_markers": [
                            "timestamp and engine context: "
                            + media.STRICT_BASE_CAPTURE_MARKER
                        ]
                    },
                },
            )
            media.require_strict_base_capture_marker(artifacts)

    def test_red_report_cannot_supply_base_media_even_with_strict_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary) / "red-base-capture"
            for label, root_result, cell_result, message in (
                ("root", "RED", "GREEN", "root report must be GREEN"),
                ("cell", "GREEN", "RED", "cell report must be GREEN"),
            ):
                with self.subTest(report=label):
                    _write_json(
                        artifacts / "report.json",
                        {
                            "result": root_result,
                            "cell": {
                                "result": cell_result,
                                "fixture_markers": [
                                    media.STRICT_BASE_CAPTURE_MARKER
                                ],
                            },
                        },
                    )
                    with self.assertRaisesRegex(ValueError, message):
                        media.require_strict_base_capture_marker(artifacts)

    def test_policy_recipes_are_exactly_release_slots_seven_and_eight(self) -> None:
        self.assertEqual(
            [1, 361],
            [recipe.mechanism_id for recipe in media.POLICY_CARD_RECIPES],
        )
        self.assertEqual(
            [
                "07_policy_001_kpi_evidence.jpg",
                "08_policy_361_charter.jpg",
            ],
            [recipe.output for recipe in media.POLICY_CARD_RECIPES],
        )
        self.assertTrue(
            all(recipe.crop == (420, 280, 1610, 875) for recipe in media.POLICY_CARD_RECIPES)
        )
        with self.assertRaisesRegex(ValueError, "requires a policy-card lock"):
            media.selected_projections(None, policy_cards_only=True)

        release_lock = json.loads(
            media.DEFAULT_POLICY_LOCK.read_text(encoding="utf-8")
        )
        self.assertEqual(
            media.DEFAULT_ARTIFACTS.resolve(),
            Path(release_lock["artifact_root"]).resolve(),
        )
        release_projections = media.selected_projections(media.DEFAULT_POLICY_LOCK)
        self.assertEqual(8, len(release_projections))
        self.assertEqual(
            media.EXPECTED_RELEASE_MEDIA_INVENTORY,
            tuple(projection.output for projection in release_projections),
        )

    def test_green_capture_lock_renders_two_deterministic_sub_2mb_jpegs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capture = _make_green_capture(root / "green-capture")
            lock = root / "release" / "media-policy-lock.json"
            payload = media.create_policy_lock(capture, lock)
            projections = media.load_policy_lock(lock, artifact_root=capture)

            self.assertEqual("GREEN", payload["result"])
            self.assertEqual([1, 361], payload["policy_ids"])
            self.assertEqual(2, len(projections))
            self.assertTrue(
                all(0 < row["bytes"] < media.MAX_BYTES for row in payload["projections"])
            )
            self.assertEqual(8, len(media.PROJECTIONS + projections))
            self.assertEqual(
                projections,
                media.selected_projections(
                    lock, artifact_root=capture, policy_cards_only=True
                ),
            )

            output = root / "projected"
            first = media.render(
                capture, output, check=False, projections=projections
            )
            checked = media.render(
                capture, output, check=True, projections=projections
            )
            tracked = media.verify_tracked_outputs(
                output, projections=projections
            )
            self.assertEqual(first, checked)
            self.assertEqual(first, tracked)
            self.assertTrue(all(row["bytes"] < media.MAX_BYTES for row in tracked))

            # Same provenance is idempotent; a different lock may not overwrite it.
            self.assertEqual(payload, media.create_policy_lock(capture, lock))
            changed = json.loads(lock.read_text(encoding="utf-8"))
            changed["report_sha256"] = "0" * 64
            lock.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                media.create_policy_lock(capture, lock)

    def test_red_capture_cannot_create_a_policy_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capture = _make_green_capture(root / "red-capture", result="RED")
            lock = root / "release" / "media-policy-lock.json"
            with self.assertRaisesRegex(ValueError, "not a valid GREEN capture"):
                media.create_policy_lock(capture, lock)
            self.assertFalse(lock.exists())

    def test_policy_lock_is_bound_to_one_artifact_and_exact_recipes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capture = _make_green_capture(root / "green-capture")
            lock = root / "release" / "media-policy-lock.json"
            media.create_policy_lock(capture, lock)
            with self.assertRaisesRegex(ValueError, "different capture artifact"):
                media.load_policy_lock(lock, artifact_root=root / "other-capture")

            payload = json.loads(lock.read_text(encoding="utf-8"))
            payload["projections"][0]["output"] = "07_not_the_release_slot.jpg"
            bad = root / "bad-lock.json"
            _write_json(bad, payload)
            with self.assertRaisesRegex(ValueError, "output mismatch"):
                media.load_policy_lock(bad)

            payload = json.loads(lock.read_text(encoding="utf-8"))
            payload["report_sha256"] = "0" * 64
            bad_provenance = root / "bad-provenance-lock.json"
            _write_json(bad_provenance, payload)
            with self.assertRaisesRegex(ValueError, "no longer matches"):
                media.load_policy_lock(
                    bad_provenance, artifact_root=capture
                )


if __name__ == "__main__":
    unittest.main()

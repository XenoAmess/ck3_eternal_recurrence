"""One pure boundary test; no media, provider, installed game or machine paths."""
import json
from pathlib import Path
import sys
import unittest
from dataclasses import FrozenInstanceError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from faith_power_promo import full_episode as common
PROFILE_PATH = ROOT / 'profiles/episode01-v5-3240s-1440p30-v1.json'


class Episode01V5ProfileTests(unittest.TestCase):
    def test_v5_duration_is_explicit_immutable_and_quality_preserving(self):
        profile = common.V5_REORDER_PROFILE
        expected = json.loads(PROFILE_PATH.read_text(encoding='utf-8'))
        self.assertEqual(profile.to_mapping(), expected)
        self.assertEqual((common.DEFAULT_PROFILE.max_seconds,
                          common.PADDING_PROFILE.max_seconds), (1860, 2101))
        self.assertEqual(common.render_profile({}, lambda value: value), common.DEFAULT_PROFILE)
        with self.assertRaises(FrozenInstanceError):
            profile.max_seconds = 4000
        budget = common.peak_budget(3240, 168, profile=profile)
        self.assertEqual(budget['peak_new_bytes'], 4_491_531_768)
        self.assertEqual((budget['video_maxrate_bps'], budget['video_bufsize_bits'],
                          budget['audio_bitrate_bps'], budget['geometry']),
                         (3_000_000, 3_000_000, 192_000, [2560, 1440, 30]))
        for seconds, count, selected in [(2101 + 1 / 30, 168, common.PADDING_PROFILE),
                                          (3240 + 1 / 30, 168, profile),
                                          (3240, 169, profile)]:
            with self.subTest(seconds=seconds, count=count):
                with self.assertRaises(ValueError):
                    common.peak_budget(seconds, count, profile=selected)
        with self.assertRaises(ValueError):
            common.peak_budget(3240)  # No profile means the legacy limit.
        reference = {'render_profile': common.pin(PROFILE_PATH)}
        self.assertEqual(common.render_profile(reference, common.Inputs({}).bound), profile)


if __name__ == '__main__':
    unittest.main()

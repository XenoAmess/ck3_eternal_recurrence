"""Pure timeline regressions. Synthetic PCM only; never invokes a media tool."""
import ast
import hashlib
import math
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


def contract(source):
    tree = ast.parse(source)
    names = {'music_window_metrics', 'music_presence'}
    tree.body = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name in names]
    namespace = {'Path': Path, 'hashlib': hashlib, 'math': math,
                 'subprocess': subprocess, 'now': lambda: 'synthetic-fixture',
                 'pin': lambda path: {'fixture_only': True, 'path': str(path)},
                 'write': lambda path, value: Path(path)}
    exec(compile(tree, '<pure-music-contract>', 'exec'), namespace)
    return SimpleNamespace(**namespace)


COMMON = None  # Candidate runner supplies source in RAM; repository CI uses below.


class Episode01MusicTimelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(__file__).resolve().parents[1] / 'src/faith_power_promo/full_episode.py'
        cls.common = COMMON or contract(source.read_text(encoding='utf-8'))

    @staticmethod
    def dry(t):
        import numpy as np
        return .08 * np.sin(2 * np.pi * 197.3 * t) + .03 * np.cos(2 * np.pi * 353.7 * t)

    @staticmethod
    def theme(t):
        import numpy as np
        return .04 * np.sin(2 * np.pi * 89.3 * t) + .02 * np.cos(2 * np.pi * 127.7 * t)

    def test_dry_reference_offset_cannot_be_corrected_by_shifting_final(self):
        import numpy as np
        t = 30 + np.arange(32000) / 8000
        # AAC1024/48k is170+2/3 samples at8k: use the actual fractional time.
        delta = 1024 / 48000
        self.assertAlmostEqual(delta * 8000, 170 + 2 / 3)
        expected = self.theme(t) * 10 ** (-17 / 20)
        actual = self.dry(t) + expected
        wrong_dry = self.dry(t + delta)
        metrics = self.common.music_window_metrics
        self.assertTrue(metrics(actual, self.dry(t), expected)['passed'])
        self.assertFalse(metrics(actual, wrong_dry, expected)['passed'])
        # Moving final to match the bad dry clock also moves music away from t.
        shifted_final = self.dry(t + delta) + self.theme(t + delta) * 10 ** (-17 / 20)
        self.assertFalse(metrics(shifted_final, wrong_dry, expected)['passed'])

    def test_five_windows_use_absolute_dry_timestamp_without_fitted_final_shift(self):
        import numpy as np
        commands = []
        duration = 120.
        source_duration = 1000.

        def fake_run(argv, **kwargs):
            commands.append(argv)
            self.assertEqual(kwargs, {'capture_output': True, 'timeout': 30})
            start = float(argv[argv.index('-ss') + 1])
            seconds = float(argv[argv.index('-t') + 1])
            self.assertEqual(seconds, 4.)
            path = argv[argv.index('-i') + 1]
            t = start + np.arange(round(seconds * 8000)) / 8000
            if path == 'dry.ffconcat':
                self.assertIn('-seek_timestamp', argv)
                self.assertEqual(argv[argv.index('-seek_timestamp') + 1], '1')
                self.assertLess(argv.index('-seek_timestamp'), argv.index('-i'))
                samples = self.dry(t)
            elif path == 'theme.wav':
                self.assertNotIn('-seek_timestamp', argv)
                samples = self.theme(t)
            else:
                self.assertEqual(path, 'final.mp4')
                self.assertNotIn('-seek_timestamp', argv)
                fade = np.minimum(np.clip(t / 2, 0, 1), np.clip((duration - t) / 8, 0, 1))
                samples = self.dry(t) + self.theme(t) * 10 ** (-17 / 20) * fade
            return SimpleNamespace(returncode=0, stdout=samples.astype('<f4').tobytes(), stderr=b'')

        reports = {}

        def capture_write(path, value):
            reports[Path(path).name] = value
            return Path(path)

        with tempfile.TemporaryDirectory(prefix='faith-pure-clock-') as directory:
            with patch.object(self.common.subprocess, 'run', side_effect=fake_run):
                function = self.common.music_presence
                with patch.dict(function.__globals__, {'write': capture_write}):
                    function('never-executed-ffmpeg', {'path': 'final.mp4'}, 'dry.ffconcat',
                             {'file': {'path': 'theme.wav'}}, source_duration,
                             duration, directory, 'synthetic-fixture-machine')
        report = reports['music-presence.json']
        self.assertEqual(len(commands), 15)
        self.assertEqual(report['global_lag_samples_at_8000Hz'], 0)
        self.assertIsNone(report['lag_calibrated_once_at_seconds'])
        self.assertEqual(report['lag_search_limit_samples'], 0)
        self.assertTrue(report['passed'])
        self.assertEqual(report['thresholds'], {'correlation_above': .90,
                         'gain_open_interval': [.85, 1.15],
                         'error_RMS_over_music_RMS_below': .5, 'music_RMS_above': 1e-6})
        for i in range(0, 15, 3):
            starts = [cmd[cmd.index('-ss') + 1] for cmd in commands[i:i + 3]]
            self.assertEqual(len(set(starts)), 1)


if __name__ == '__main__':
    unittest.main()

"""Focused RAM-only new-Game display qualification, no temporary directory."""
import contextlib
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import prepare_c23_display_capture_amendment_v1 as new
from tools.g2_saved_campaign import test_new_game_recording_owner_v1 as original_fixture

T = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
OUTPUT = T.parent.parent / 'p51-fresh1066-v20261019-prepare01/c23-display-source100'
MACHINE = 'xenoamess-full-tower-eb9d2c1186'


def planned():
    return new.plan(T, T, OUTPUT, generation='C23', machine_id=MACHINE)


class Qualification(unittest.TestCase):
    def test_complete_graph_pause_inverse_and_five_source_pins(self):
        values, raw, review = planned()
        self.assertEqual(len(values), 18)
        self.assertEqual(sum(map(len, values.values())), 278733)
        self.assertEqual(review['actual_capture']['bytes'], 73689)
        self.assertEqual(review['actual_capture']['sha256'], new.PAUSED_SHA)
        owner = values['presentation-c23/start_new_game_display.py']
        self.assertEqual(len(owner), 11355)
        self.assertEqual(hashlib.sha256(owner).hexdigest(), '56b649988bda143426a6eca518ed72f0025f0f5ae5df3e8df6e8f236636c96dd')
        pins = review['external_import_source_pins']
        self.assertEqual(set(pins), {'root_decision_text_api_c23', 'root_p37c23_overlay_relay',
            'root_p37c23_compact_decision_feed', 'root_continuous_segment_auto_c23', 'p51_decision_text_shutdown_c23'})
        for name, ref in pins.items():
            data = values[name + '.py']
            self.assertEqual(ref, new.pin(data, T / (name + '.py')))
        self.assertFalse(review['runtime_admitted'])
        self.assertFalse(review['actual_new_Game_or_publisher_identity_invented'])
        self.assertIn('full-hold canonical', review['canonical_storage_rule'])
        self.assertEqual(hashlib.sha256((new.HERE/'prepare_new_game_recording_owner_v1.py').read_bytes()).hexdigest(),new.LEGACY_SHA)
        self.assertFalse(OUTPUT.exists())

    def test_actual_original_owner_lifecycle_with_new_capture_and_no_scratch(self):
        # Reuse the original generated-owner lifecycle; all files and child
        # calls are already RAM mocks. Replace its empty temp-dir wrapper too.
        ram_path = ROOT / '_runtime/C23-DISPLAY-QUALIFICATION-NOT-MATERIALIZED'
        self.assertFalse(ram_path.exists())
        with patch.object(original_fixture, 'plan', new.plan), patch.object(
                original_fixture.tempfile, 'TemporaryDirectory', lambda **kw: contextlib.nullcontext(str(ram_path))):
            original_fixture.OwnerTests().test_actual_generated_owner_uses_only_patched_worker_and_retains_new_publisher()
        self.assertFalse(ram_path.exists())

    def test_changed_source_and_existing_namespace_are_rejected(self):
        real_read = Path.read_bytes
        target = new.HERE.parent / 'ck3_obs_capture.py'
        def corrupt(path):
            raw = real_read(path)
            return raw + b'\n' if path == target else raw
        with patch.object(Path, 'read_bytes', corrupt), self.assertRaisesRegex(ValueError, 'mutable-replace helper'):
            planned()
        real_exists = Path.exists
        collision = T / 'root_decision_text_api_c23.py'
        with patch.object(Path, 'exists', lambda p: True if p == collision else real_exists(p)), self.assertRaisesRegex(ValueError, 'namespace'):
            planned()


if __name__ == '__main__':
    unittest.main(verbosity=2)

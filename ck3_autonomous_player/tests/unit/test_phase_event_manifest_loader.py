from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from xar_autoplayer.simulation.phase_event_manifest import (
    STOCK_PHASE_EVENT_MANIFEST_SHA256,
    PhaseEventEvaluatorUnavailable,
    PhaseEventManifestError,
    load_stock_phase_event_manifest,
)


MANIFEST_PATH = (
    Path(__file__).parents[2]
    / "src"
    / "xar_autoplayer"
    / "simulation"
    / "data"
    / "ck3_1_19_0_6_stock_combat_phase_events.json"
)


class FrozenPhaseEventManifestLoaderTests(unittest.TestCase):
    def test_exact_manifest_is_immutable_and_cannot_enable_fidelity(self) -> None:
        manifest = load_stock_phase_event_manifest()
        self.assertEqual(
            manifest.canonical_manifest_sha256,
            STOCK_PHASE_EVENT_MANIFEST_SHA256,
        )
        self.assertEqual(len(manifest.event_rows), 13)
        self.assertEqual(
            tuple(row.event_type for row in manifest.event_rows),
            ("commander",) * 4 + ("knight",) * 9,
        )
        self.assertFalse(manifest.fidelity_gate)
        with self.assertRaises(PhaseEventEvaluatorUnavailable):
            manifest.require_evaluator_ready()
        with self.assertRaises(TypeError):
            manifest.event_rows[0].validity_ast["op"] = "const_bool"  # type: ignore[index]

    def test_any_manifest_mutation_fails_the_frozen_hash(self) -> None:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        payload["event_rows"][0]["base_weight"] += 1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(PhaseEventManifestError, "canonical hash"):
                load_stock_phase_event_manifest(path)


if __name__ == "__main__":
    unittest.main()

"""Real public adapter entry without the host subprocess's xar_autoplayer path."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from ck3_mod_acceptance import Selection
from ck3_mod_acceptance_client import CaseClient

ADAPTER_PATH = ROOT / "tools/ck3_mod_acceptance_cases/faith_e02_d1_readonly_adapter.py"


def snapshot(actor=31254, date=53144328, revision=5):
    return {"source": "injected-dll-named-pipe", "backend_id": "native-headless",
        "episode_projection": "native_campaign", "snapshot_id": "synthetic:" + str(revision),
        "revision": revision, "native_revision": revision - 1, "date_raw": date,
        "played_character": {"character_id": actor, "alive": True, "source": "native"},
        "paused": True, "map_ready": True, "active_event": None, "episode_run_id": None,
        "diagnostics": {"bridge_pid": 1234, "connection_generation": 4, "hello": {
            "pid": 1234, "connection_generation": 4, "expected_ck3_version": "1.20.0.4",
            "expected_ck3_sha256": "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518",
            "ck3_build_match": True, "game_adapter_id": "ck3-1.20.0.4-msvc-x64"}}}


class PublicClientStub(CaseClient):
    """Use the real public frame validator; replace only external queue/process IO."""
    operator_reviewer = "isolated-entry-reviewer"

    def __init__(self, frames):
        self.frames = list(frames)
        self.manifest = {"game": {"version": "1.20.0.4",
            "exe_sha256": "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"}}
        self._binding = None
        self.holds = 0
        self.checkpoints = []

    def snapshot(self):
        return self.validate_frame(deepcopy(self.frames.pop(0)))

    def checkpoint(self, key, value):
        self.checkpoints.append(key)

    def root_checkpoint(self, key, value, reserve):
        self.holds += 1
        return {"run_id": "isolated-entry", "reviewer": self.operator_reviewer, "status": "complete"}


class PublicAdapterEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        # Reproduce the actual parent environment, not the test suite's usual
        # global src insertion. Each test owns this isolated module/path scope.
        old_path = list(sys.path)
        old_modules = {name: mod for name, mod in sys.modules.items()
                       if name == "xar_autoplayer" or name.startswith("xar_autoplayer.")}
        for name in old_modules:
            sys.modules.pop(name)
        sys.path[:] = [p for p in sys.path if not (Path(p or ".") / "xar_autoplayer").is_dir()]
        self.addCleanup(self.restore, old_path, old_modules)
        self.assertNotIn("xar_autoplayer", sys.modules)
        selection = Selection.__new__(Selection)
        selection.locations = {"repo_root": ROOT}
        selection.adapter_path = ADAPTER_PATH
        self.adapter = selection.load_adapter()

    @staticmethod
    def restore(old_path, old_modules):
        for name in tuple(sys.modules):
            if name == "xar_autoplayer" or name.startswith("xar_autoplayer."):
                sys.modules.pop(name)
        sys.modules.update(old_modules)
        sys.path[:] = old_path

    def context(self, source=None):
        a = self.adapter
        saved = {"save": "not-read-original-D1.ck3", "bytes": a.SAVE_BYTES,
                 "sha256": a.SAVE_SHA256, "player_id": 31254, "date_raw": 53144328}
        c = {"schema": "faith-engine-e02-d1-readonly-case-v1", "product": a.PRODUCT,
            "case": a.CASE, "machine_id": "4-8e1c2f1861", "saved_input": saved,
            "historical_identity_expectation": {
                "kind": "historical_expectation_not_fresh_observation",
                "source": {"path": "history.py", "bytes": 42, "sha256": "a" * 64},
                "player_id": 31254, "date_raw": 53144328},
            "profile": {"enabled_mods": [], "product_files": []}, "scope": dict(a.SCOPE)}
        return {"product": a.PRODUCT, "case": a.CASE, "case_contract": c,
            "case_spec": {"required_mcp_tools": sorted(a.REQUIRED_TOOLS),
                "opt_in_read_only_mcp_tools": sorted(a.READONLY_TOOLS),
                **{name: False for name in a.ACTION_OPT_INS}},
            "shared_source_root": str(ROOT if source is None else source),
            "run_id": "isolated-entry", "output": str(self.output)}

    def identity(self):
        return json.loads((self.output / "faith-e02-d1-first-native-identity.json").read_text(encoding="utf-8"))

    def test_real_load_adapter_run_case_without_host_import_path(self):
        client = PublicClientStub([snapshot(date=53144352), snapshot(date=53144352, revision=6)])
        result = self.adapter.run_case(self.context(), client)
        actual = self.identity()
        self.assertTrue(actual["fresh_identity_validated"])
        self.assertEqual(actual["scene_binding"]["date_raw"], 53144352)
        self.assertEqual(client.holds, 1)
        self.assertFalse(result["business_pass"])
        refs = actual["opening_binding_sources"]
        self.assertEqual(Path(refs["opening_contract"]["path"]),
            (ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_decisions_open_contract.py").resolve())
        self.assertFalse(any((Path(p or ".") / "xar_autoplayer").is_dir() for p in sys.path))

    def test_selected_package_src_layout_also_works(self):
        source = ROOT / "ck3_autonomous_player/src"
        result = self.adapter.run_case(self.context(source), PublicClientStub([snapshot(), snapshot(revision=6)]))
        self.assertTrue(result["research_holder_completed"])
        self.assertFalse(result["case_contract_qualified"])

    def test_selected_source_absent_preserves_first_snapshot_and_never_holds(self):
        client = PublicClientStub([snapshot()])
        with self.assertRaisesRegex(ValueError, "shared binding source is absent"):
            self.adapter.run_case(self.context(self.output / "missing-source"), client)
        self.assertFalse(self.identity()["fresh_identity_validated"])
        self.assertEqual(self.identity()["actual_snapshot"]["played_character"]["character_id"], 31254)
        self.assertEqual(client.holds, 0)

    def test_cached_foreign_contract_is_rejected_without_fallback(self):
        foreign = types.ModuleType("xar_autoplayer.bridge.ingame_decisions_open_contract")
        foreign.__file__ = str(self.output / "foreign.py")
        foreign.opening_binding = lambda value: self.fail("foreign binding must never run")
        sys.modules[foreign.__name__] = foreign
        client = PublicClientStub([snapshot()])
        with self.assertRaisesRegex(ValueError, "escaped the selected shared source"):
            self.adapter.run_case(self.context(), client)
        self.assertFalse(self.identity()["fresh_identity_validated"])
        self.assertEqual(client.holds, 0)

    def test_import_failure_preserves_first_snapshot_instead_of_losing_receipt(self):
        client = PublicClientStub([snapshot()])
        with patch.object(self.adapter.importlib, "import_module", side_effect=ImportError("synthetic unavailable dependency")):
            with self.assertRaisesRegex(ImportError, "synthetic unavailable dependency"):
                self.adapter.run_case(self.context(), client)
        self.assertFalse(self.identity()["fresh_identity_validated"])
        self.assertIn("synthetic unavailable dependency", self.identity()["rejection_reason"])
        self.assertEqual(client.holds, 0)

    def test_actor_mismatch_preserved_before_hold_with_selected_reader(self):
        client = PublicClientStub([snapshot(actor=98765)])
        with self.assertRaisesRegex(ValueError, "actual native player"):
            self.adapter.run_case(self.context(), client)
        self.assertFalse(self.identity()["fresh_identity_validated"])
        self.assertEqual(self.identity()["actual_snapshot"]["played_character"]["character_id"], 98765)
        self.assertEqual(client.holds, 0)

    def test_after_date_drift_remains_rejected_and_never_produces_holder_success(self):
        client = PublicClientStub([snapshot(), snapshot(date=53144329, revision=6)])
        with self.assertRaisesRegex(ValueError, "changed date_raw"):
            self.adapter.run_case(self.context(), client)
        self.assertTrue(self.identity()["fresh_identity_validated"])
        self.assertEqual(client.holds, 1)
        self.assertFalse((self.output / "faith-e02-d1-readonly-holder-result.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)

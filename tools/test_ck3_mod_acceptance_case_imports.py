"""Actual public CLI run without ambient SDK paths; no game or host executes."""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from ck3_mod_acceptance_case_imports import case_sdk_imports


class CaseImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prior_path = list(sys.path)
        self.cached = {name: sys.modules.pop(name) for name in tuple(sys.modules)
                       if name == "xar_autoplayer" or name.startswith("xar_autoplayer.")}
        self.temporary = tempfile.TemporaryDirectory(prefix="case-import-")
        self.source = Path(self.temporary.name) / "sdk"
        (self.source / "xar_autoplayer").mkdir(parents=True)
        (self.source / "xar_autoplayer/__init__.py").write_text("FROZEN = True\n", encoding="utf-8")

    def tearDown(self) -> None:
        for name in tuple(sys.modules):
            if name == "xar_autoplayer" or name.startswith("xar_autoplayer."):
                del sys.modules[name]
        sys.modules.update(self.cached)
        sys.path[:] = self.prior_path
        self.temporary.cleanup()

    def test_selected_sdk_is_bound_and_path_restored_on_exception(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "case failure"):
            with case_sdk_imports(self.source, {"PYTHONPATH": str(self.source)}):
                module = importlib.import_module("xar_autoplayer")
                self.assertEqual(Path(str(module.__file__)).parent, self.source / "xar_autoplayer")
                raise RuntimeError("case failure")
        self.assertEqual(sys.path, self.prior_path)

    def test_cached_foreign_sdk_is_rejected_before_case(self) -> None:
        foreign = ModuleType("xar_autoplayer")
        foreign.__file__ = str(Path(self.temporary.name) / "foreign/xar_autoplayer/__init__.py")
        sys.modules["xar_autoplayer"] = foreign
        with self.assertRaisesRegex(ValueError, "escaped selected runtime"):
            with case_sdk_imports(self.source, {"PYTHONPATH": str(self.source)}):
                self.fail("foreign SDK must never reach the case")
        self.assertEqual(sys.path, self.prior_path)

    def test_wrong_missing_and_empty_environment_paths_are_rejected(self) -> None:
        for environment in ({"PYTHONPATH": None}, {"PYTHONPATH": True}, {"PYTHONPATH": ""},
                            {"PYTHONPATH": str(self.source) + os.pathsep},
                            {"PYTHONPATH": str(self.source.parent)}):
            with self.subTest(environment=environment), self.assertRaises(ValueError):
                with case_sdk_imports(self.source, environment):
                    self.fail("invalid frozen SDK declaration")

    def test_existing_sdk_free_environment_does_not_claim_a_binding(self) -> None:
        with case_sdk_imports(self.source.parent, {}) as selected:
            self.assertIsNone(selected)
        self.assertEqual(sys.path, self.prior_path)

    def test_public_cli_run_imports_original_lazy_consumers_without_pythonpath(self) -> None:
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        completed = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(Path(__file__).resolve()),
                                    "--cli-fixture"], cwd=self.temporary.name, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   encoding="utf-8", timeout=60, check=False)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        value = json.loads(completed.stdout)
        self.assertTrue(value["case_result"]["original_observations_imported"])
        self.assertTrue(value["case_result"]["original_native_day_imported"])
        self.assertEqual(value["launcher_exit_code"], 0)
        self.assertFalse(value["case_result"]["game_started"])


def cli_fixture() -> int:
    """Test-only owned launcher/client; execute real Selection/preflight/run/CLI."""
    from unittest.mock import patch
    sys.path.insert(0, str(ROOT / "tools"))
    sys.path.insert(0, str(ROOT))
    if importlib.util.find_spec("xar_autoplayer") is not None:
        raise RuntimeError("CLI fixture accidentally received an ambient SDK")
    from test_ck3_mod_acceptance import SharedEntryTests
    import ck3_mod_acceptance as entry
    import ck3_mod_acceptance_client as client_module
    fixture = SharedEntryTests(methodName="test_run_delegates_existing_launcher_without_executing_host")
    fixture.setUp()
    try:
        source = fixture.locations["source"]
        bridge = source / "xar_autoplayer/bridge"
        bridge.mkdir(parents=True)
        (source / "xar_autoplayer/__init__.py").write_text("", encoding="utf-8")
        (bridge / "__init__.py").write_text("", encoding="utf-8")
        for name in ("player_pilgrimage_traits.py", "campaign_interaction_boundary_v1.py"):
            (bridge / name).write_bytes((ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge" / name).read_bytes())
        fixture.manifest["entry_environment"] = {"PYTHONPATH_parts": [{"path_key": "source_root"}]}
        fixture.write(fixture.manifest_path, fixture.manifest)
        fixture.runtime["manifest"] = entry.pin(fixture.manifest_path)
        fixture.write(fixture.runtime_path, fixture.runtime)
        adapter = fixture.root / "cases/lazy_adapter.py"
        adapter.parent.mkdir()
        adapter.write_text('''from pathlib import Path
def prepare_case(context: dict[str, object]) -> dict[str, object]:
    return {}
def verify_case(context: dict[str, object]) -> dict[str, object]:
    return {}
def run_case(context: dict[str, object], client: object) -> dict[str, object]:
    from tools.ck3_mod_acceptance_cases import faith_e02_pilgrimage_observations as observations
    from ck3_mod_acceptance_native_day import pending_instance
    from xar_autoplayer.bridge import player_pilgrimage_traits as traits
    assert observations.normalize_player_pilgrimage_traits_v1(None, current_context={}) is None
    assert pending_instance(None) is None
    assert Path(traits.__file__).resolve().is_relative_to(Path(str(context['shared_source_root'])).resolve())
    return {'original_observations_imported': True, 'original_native_day_imported': True, 'game_started': False}
''', encoding="utf-8")
        contract = adapter.with_suffix(".json")
        fixture.write(contract, {})
        fixture.products["product_inventory"] = str(fixture.files["inventory"])
        fixture.products["products"]["xqol"]["cases"][0]["adapter"] = {"path": str(adapter), "config": str(contract)}
        fixture.write(fixture.products_path, fixture.products)
        context, _, _, value = fixture.context()
        value["reviewer"] = "synthetic-cli-reviewer"
        fixture.write(context, value)

        class OwnedClient:
            def __init__(self, selection: object) -> None:
                self.output = fixture.root / "case-output"
                self.output.mkdir()
                self._handle: object | None = object()

            def wait_hold(self) -> None:
                return None

            def retain_held_process(self, wait: bool = False) -> bool:
                return False

            def normal_close(self, reason: str) -> dict[str, object]:
                return {"normal_close_qualified": True, "synthetic_owned_client": True, "game_started": False}

            def close_handle(self) -> None:
                return None

        with patch.object(client_module, "CaseClient", OwnedClient):
            code = entry.main(["run", "--runtime", str(fixture.runtime_path), "--products", str(fixture.products_path),
                               "--product", "xqol", "--case", "core", "--run-context", str(context)])
            if type(code) is not int:
                raise TypeError("public CLI must return its actual integer exit code")
            return code
    finally:
        fixture.doCleanups()


if __name__ == "__main__":
    if sys.argv[1:] == ["--cli-fixture"]:
        raise SystemExit(cli_fixture())
    unittest.main(verbosity=2)

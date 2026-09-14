from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from xar_autoplayer.companion_profile import (  # noqa: E402
    MILITARY_WRAPPER_RELATIVE_PATH,
    MOD_BRIDGE_OUTER_REF,
    _wrapper_proofs,
    stage_mod_bridge_companion,
    verify_mod_bridge_companion,
)
from xar_autoplayer.environment import (  # noqa: E402
    OUTER_DESCRIPTOR_REF,
    EnvironmentSpec,
    snapshot_digest,
    tree_snapshot,
)
from xar_autoplayer.errors import AgentError  # noqa: E402


RUNNER_PATH = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_military_preparation_summary_private_probe_live.py"
)
RUNNER_SPEC = importlib.util.spec_from_file_location("military_live_runner", RUNNER_PATH)
assert RUNNER_SPEC is not None and RUNNER_SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(RUNNER_SPEC)
RUNNER_SPEC.loader.exec_module(RUNNER)

BOOTSTRAP_PATH = ROOT.parent / "tools" / "run_g2_military_preparation_probe.py"
BOOTSTRAP_SPEC = importlib.util.spec_from_file_location(
    "military_runtime_bootstrap", BOOTSTRAP_PATH
)
assert BOOTSTRAP_SPEC is not None and BOOTSTRAP_SPEC.loader is not None
BOOTSTRAP = importlib.util.module_from_spec(BOOTSTRAP_SPEC)
BOOTSTRAP_SPEC.loader.exec_module(BOOTSTRAP)


WRAPPER_TEXT = """xar_mcp_military_current_strength_final = {
 value = current_military_strength
}
xar_mcp_military_max_strength_final = {
 value = max_military_strength
}
xar_mcp_military_number_of_knights_final = {
 value = number_of_knights
}
xar_mcp_military_max_number_of_knights_final = {
 value = max_number_of_knights
}
xar_mcp_military_maa_gold_expense_relative_final = {
 value = character_men_at_arms_expense_gold_relative
}
"""


class CompanionProfileTests(unittest.TestCase):
    def test_repository_provider_has_exactly_five_loadable_wrappers(self) -> None:
        proofs = _wrapper_proofs(ROOT / "mod_bridge" / MILITARY_WRAPPER_RELATIVE_PATH)
        self.assertEqual(len(proofs), 5)
        self.assertTrue(all(proof["loadable"] for proof in proofs.values()))

    def _fixture(self, root: Path) -> tuple[EnvironmentSpec, Path, str]:
        state = root / "state"
        game = root / "game"
        spec = EnvironmentSpec(state.resolve(), game.resolve())
        spec.production_dir.mkdir(parents=True)
        (spec.production_dir / "descriptor.mod").write_text(
            'name="production"\n', encoding="utf-8"
        )
        (spec.production_dir / "content.txt").write_text("sentinel\n", encoding="utf-8")
        production_hash = snapshot_digest(tree_snapshot(spec.production_dir))
        mod = spec.profile_dir / "mod"
        mod.mkdir(parents=True)
        (mod / "xar_autoplayer.mod").write_text(
            f'path="{spec.production_dir.as_posix()}"\n', encoding="utf-8"
        )
        (spec.profile_dir / "dlc_load.json").write_text(
            json.dumps({"enabled_mods": [OUTER_DESCRIPTOR_REF], "disabled_dlcs": []}),
            encoding="utf-8",
        )

        source = root / "source-mod-bridge"
        (source / MILITARY_WRAPPER_RELATIVE_PATH.parent).mkdir(parents=True)
        (source / "gui").mkdir(parents=True)
        (source / "templates").mkdir(parents=True)
        (source / "descriptor.mod").write_text(
            'name="fixture companion"\n', encoding="utf-8"
        )
        (source / MILITARY_WRAPPER_RELATIVE_PATH).write_text(
            WRAPPER_TEXT, encoding="utf-8"
        )
        (source / "gui" / "fixture.gui").write_text("guiTypes = {}\n", encoding="utf-8")
        (source / "templates" / "xar_mcp_inbox.txt").write_text(
            "# fixture no-op\n", encoding="utf-8"
        )
        return spec, source, production_hash

    def test_stages_separate_companion_and_proves_all_five_wrappers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            spec, source, production_hash = self._fixture(Path(temporary))
            with mock.patch(
                "xar_autoplayer.companion_profile.ck3_processes", return_value=[]
            ), mock.patch(
                "xar_autoplayer.companion_profile.verify_profile",
                return_value={"mod": {"production_tree_sha256": production_hash}},
            ):
                result = stage_mod_bridge_companion(spec, source=source)

            self.assertEqual(result["status"], "green")
            self.assertEqual(
                result["enabled_mods"], [OUTER_DESCRIPTOR_REF, MOD_BRIDGE_OUTER_REF]
            )
            self.assertEqual(len(result["military_wrapper_definitions"]), 5)
            self.assertTrue(
                all(
                    proof["loadable"]
                    for proof in result["military_wrapper_definitions"].values()
                )
            )
            self.assertEqual(
                snapshot_digest(tree_snapshot(spec.production_dir)), production_hash
            )
            self.assertEqual(
                (spec.profile_dir / "mod-content" / "xar-mcp-bridge" / MILITARY_WRAPPER_RELATIVE_PATH).read_bytes(),
                (source / MILITARY_WRAPPER_RELATIVE_PATH).read_bytes(),
            )

    def test_preflight_rejects_wrapper_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            spec, source, production_hash = self._fixture(Path(temporary))
            with mock.patch(
                "xar_autoplayer.companion_profile.ck3_processes", return_value=[]
            ), mock.patch(
                "xar_autoplayer.companion_profile.verify_profile",
                return_value={"mod": {"production_tree_sha256": production_hash}},
            ):
                stage_mod_bridge_companion(spec, source=source)
            target = (
                spec.profile_dir
                / "mod-content"
                / "xar-mcp-bridge"
                / MILITARY_WRAPPER_RELATIVE_PATH
            )
            target.write_bytes(target.read_bytes() + b"# drift\n")
            with self.assertRaisesRegex(AgentError, "preflight is RED"):
                verify_mod_bridge_companion(spec, source=source)


class RawProbePersistenceTests(unittest.TestCase):
    def test_next_live_plan_is_fixed_to_r686(self) -> None:
        plan = json.loads(
            (
                ROOT
                / "native_bridge"
                / "research"
                / "fixtures"
                / "military_preparation_r686_live_plan.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(plan["round"]["old"], "R685")
        self.assertEqual(plan["round"]["new"], "R686")
        self.assertFalse(plan["runtime"]["arbitrary_path_python_fallback"])
        self.assertIn(
            "persist raw-probe.json before semantic validation",
            plan["evidence_order"],
        )

    def test_unavailable_result_is_persisted_before_validation_raises(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "raw-probe.json"
            probe = {
                "result_published": True,
                "result": {"status": "unavailable", "failure_flags": 512},
            }

            def reject(_probe: dict[str, object]) -> dict[str, object]:
                raise RuntimeError("status mismatch")

            with self.assertRaisesRegex(RuntimeError, "status mismatch"):
                RUNNER.persist_then_validate(
                    output,
                    diagnostics={"connected": True},
                    probe=probe,
                    binding={"played_character_id": 29829},
                    validator=reject,
                )
            persisted = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(persisted["result"]["status"], "unavailable")
            self.assertEqual(persisted["result"]["failure_flags"], 512)
            self.assertFalse(persisted["semantic_validation_started"])


class RuntimeBootstrapTests(unittest.TestCase):
    def test_runtime_resolution_uses_workspace_config_and_never_sys_executable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "portable-workspace"
            runtime = workspace / "tools" / ".venv" / "Scripts" / "python.exe"
            runtime.parent.mkdir(parents=True)
            runtime.write_bytes(b"fixture")
            with mock.patch.object(
                BOOTSTRAP.subprocess,
                "run",
                return_value=subprocess.CompletedProcess([], 0, "", ""),
            ):
                source, selected = BOOTSTRAP.resolve_runtime_python(
                    requested=None,
                    workspace_root=workspace,
                    repo_root=root / "clone",
                    environment={},
                )
            self.assertEqual(source, "workspace-root")
            self.assertEqual(selected, runtime.resolve())
            self.assertNotEqual(selected, Path(sys.executable).resolve())

    def test_runtime_resolution_fails_when_no_explicit_project_runtime_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(RuntimeError, "no explicit XAR project Python"):
                BOOTSTRAP.resolve_runtime_python(
                    requested=None,
                    workspace_root=None,
                    repo_root=root,
                    environment={},
                )


if __name__ == "__main__":
    unittest.main()

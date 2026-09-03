from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[3]
SCRIPT = (
    REPO / "ck3_autonomous_player" / "native_bridge" / "research"
    / "verify_raiktor_generic_war_bound_normal_desktop.py"
)
SPEC = importlib.util.spec_from_file_location("normal_desktop_preflight", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GenericWarBoundNormalDesktopPreflightTest(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[Path, Path, Path, Path]:
        runner = root / "runner.py"
        runner.write_text(
            'terms_live._run(\n'
            'query_war_termination_terms_step(war_id)\n'
            'query_war_termination_terms_step(war_id)\n'
            '"no_mutation_commands"\n', encoding="utf-8")
        manifest = root / "manifest.json"
        manifest.write_text("{}\n", encoding="utf-8")
        runtime = root / "runtime.py"
        runtime.write_text(
            "startup = win32process.STARTUPINFO()\n"
            "creation_flags = win32process.CREATE_SUSPENDED\n"
            "win32process.CreateProcess(command, startup)\n",
            encoding="utf-8",
        )
        report = root / "verify.json"
        report.write_text(json.dumps({
            "ok": True,
            "status": "ready-to-run",
            "ck3_started": False,
            "profile_prepared": False,
            "attempt_dir": str(root / "absent-attempt"),
            "checks": {"all": True},
            "identities": {
                "runner_sha256": MODULE._sha256(runner),
                "manifest_sha256": MODULE._sha256(manifest),
            },
        }), encoding="utf-8")
        return report, runner, manifest, runtime

    def test_default_desktop_is_ready_without_launch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report, runner, manifest, runtime = self._fixture(Path(temporary))
            value = MODULE.audit(
                base_verify_report=report, runner=runner, manifest=manifest,
                runtime=runtime, desktop_name="Default", process_rows=[])
        self.assertTrue(value["ok"])
        self.assertEqual(value["status"], "ready-to-run-on-normal-desktop")
        self.assertFalse(value["launch_attempted"])

    def test_sandbox_desktop_preserves_candidate_but_is_ineligible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report, runner, manifest, runtime = self._fixture(Path(temporary))
            value = MODULE.audit(
                base_verify_report=report, runner=runner, manifest=manifest,
                runtime=runtime, desktop_name="CodexSandboxDesktop-123",
                process_rows=[])
        self.assertFalse(value["ok"])
        self.assertTrue(value["normal_desktop_direct_execution_supported"])
        self.assertEqual(
            value["status"], "candidate-ready-current-desktop-ineligible")


if __name__ == "__main__":
    unittest.main()

"""Real product CLI regressions; no installed game or live acceptance is claimed."""
from __future__ import annotations

import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
SUPPORT = SOURCE.parent / "tools"


class DeJureConquestStaticContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="djc-product-cli-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.product = self.root / "mod_de_jure_conquest"
        metadata = runpy.run_path(str(SOURCE / "tools/product.py"))
        runtime = metadata.get("RUNTIME_FILES")
        if not isinstance(runtime, frozenset) or not all(isinstance(x, str) for x in runtime):
            raise TypeError("actual product runtime inventory is not a string frozenset")
        for relative in runtime:
            source = SOURCE / relative
            target = self.product / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for name in ("product.py", "validate_static.py", "build_release.py", "gen_acceptance_fixture.py", "verify_fixture_log.py"):
            target = self.product / "tools" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / "tools" / name, target)

    def command(self, tool: str, *args: str) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(SUPPORT)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run([sys.executable, "-B", "-X", "utf8", str(self.product / "tools" / tool), *args],
                              cwd=self.root, env=environment, capture_output=True, text=True, encoding="utf-8", check=False)

    def test_full_runtime_and_nine_language_release_validation(self) -> None:
        result = self.command("validate_static.py", "--no-installed-game", "--release-localization")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertIsInstance(report, dict)
        self.assertEqual(report["runtime_allowlist_count"], 16)
        self.assertEqual(report["checked_runtime_file_count"], 16)
        self.assertEqual(report["live"], "NOT_RUN")
        self.assertEqual(report["errors"], [])

    def test_real_cb_source_rejects_AI_fee_and_war_identity_regressions(self) -> None:
        cb = self.product / "common/casus_belli_types/duchy_de_jure_greatwar.txt"
        original = cb.read_bytes()
        for before, after, expected in (
            (b"\tai = no", b"\tai = yes", "ai must equal no"),
            (b"\t\t\tvalue = 200", b"\t\t\tvalue = 201", "value must equal 200"),
            (b"djc_join_de_jure_defenders = { WAR = root.war }", b"djc_join_de_jure_defenders = { WAR = scope:attacker }", "WAR must equal root.war"),
        ):
            with self.subTest(expected=expected):
                self.assertEqual(original.count(before), 1)
                cb.write_bytes(original.replace(before, after, 1))
                result = self.command("validate_static.py", "--no-installed-game", "--release-localization")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(expected, result.stdout)
                cb.write_bytes(original)
        self.assertEqual(self.command("validate_static.py", "--no-installed-game", "--release-localization").returncode, 0)

    def test_upstream_and_foreign_Workshop_ids_reject_before_git_or_output(self) -> None:
        for item in ("3600021457", "3809999999", "0", "true"):
            with self.subTest(item=item):
                target = self.root / ("forbidden-" + item)
                result = self.command("build_release.py", "--output", str(target), "--workshop-item-id", item)
                self.assertEqual(result.returncode, 1)
                self.assertIn("maintained Workshop item must be 3812510217", result.stderr)
                self.assertFalse(target.exists())
                self.assertNotIn("not a git repository", result.stderr)

    def test_wrong_entry_shapes_fail_closed_without_traceback(self) -> None:
        cb = self.product / "common/casus_belli_types/duchy_de_jure_greatwar.txt"
        original = cb.read_bytes()
        cb.write_bytes(original.replace(b"allowed_for_character = {", b"allowed_for_character = no\n unused_original_allowed_block = {", 1))
        result = self.command("validate_static.py", "--no-installed-game")
        self.assertEqual(result.returncode, 1)
        self.assertIn("allowed_for_character must be a block", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_original_matrix_emitter_keeps_72_unique_markers_and_121_fixture(self) -> None:
        target = self.root / "actual-emitted-fixture"
        result = self.command("gen_acceptance_fixture.py", "--output", str(target))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('supported_version="1.21.*"', (target / "descriptor.mod").read_text())
        contract = json.loads((target / "fixture-contract.json").read_text())
        self.assertEqual(len(contract["markers"]), 72)
        self.assertEqual(len(set(contract["markers"])), 72)
        self.assertEqual(contract["player_history_id"], 1128)
        self.assertTrue(contract["claims_excluded"])

    def test_release_localization_rejects_missing_original_foreign_key(self) -> None:
        localization = self.product / "localization/french/greatwar_l_french.yml"
        rows = localization.read_text(encoding="utf-8-sig").splitlines(keepends=True)
        localization.write_text("".join(rows[:-1]), encoding="utf-8-sig")
        result = self.command("validate_static.py", "--no-installed-game", "--release-localization")
        self.assertEqual(result.returncode, 1)
        self.assertIn("release localization keys differ: french", result.stdout)


if __name__ == "__main__":
    unittest.main()

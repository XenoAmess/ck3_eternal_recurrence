from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


AUTOPLAYER_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = AUTOPLAYER_ROOT.parent
SCRIPT = (
    AUTOPLAYER_ROOT
    / "native_bridge"
    / "research"
    / "prepare_g2_source_specific_operator_profile.py"
)
sys.path.insert(0, str(AUTOPLAYER_ROOT / "src"))

SPEC = importlib.util.spec_from_file_location("g2_operator_profile", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

from xar_autoplayer.operator_mcp import load_operator_profile  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class G2OperatorProfileTests(unittest.TestCase):
    def _fixture(self, root: Path) -> dict[str, Path]:
        repo = root / "portable-clone"
        repo.mkdir()
        runtime = root / "runtime-bundle"
        runtime.mkdir()
        deployment = root / "operator-deployment"
        deployment.mkdir()
        python = runtime / "python.exe"
        python.write_bytes(b"python-fixture")
        settings = runtime / "profile" / "pdx_settings.txt"
        settings.parent.mkdir()
        settings.write_bytes(b"settings-fixture")
        shadercache = settings.parent / "shadercache"
        shadercache.mkdir()
        (shadercache / "warm.bin").write_bytes(b"warm")

        dependencies: dict[str, Path] = {}
        paths: dict[str, str] = {}
        hashes: dict[str, str] = {}
        for name in sorted(MODULE._REQUIRED_DEPENDENCIES):
            if name in MODULE._RUNTIME_DEPENDENCIES:
                path = runtime / f"{name}.bin"
                paths[name] = f"C:\\old-machine\\{name}.bin"
            else:
                path = repo / "deps" / f"{name}.py"
                paths[name] = path.relative_to(repo).as_posix()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"{name}-fixture".encode("ascii"))
            dependencies[name] = path
            hashes[name] = _sha256(path)

        manifest = repo / "g2-manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema": MODULE.MANIFEST_SCHEMA,
                    "status": "static-ready-live-command-default-off",
                    "default_off": True,
                    "live_executed": False,
                    "paths": paths,
                    "sha256": hashes,
                    "live_admission": {"expected_war_id": 50331699},
                }
            ),
            encoding="utf-8",
        )
        return {
            "repo": repo,
            "runtime": runtime,
            "deployment": deployment,
            "python": python,
            "settings": settings,
            "shadercache": shadercache,
            "manifest": manifest,
            **dependencies,
        }

    def _build(self, fixture: dict[str, Path]) -> dict[str, object]:
        return MODULE.build_profile(
            target_id="portable-operator",
            display_name="Portable operator",
            token_user="TARGET\\operator",
            desktop="WinSta0\\Default",
            machine="TARGET-HOST",
            endpoint_host="127.0.0.1",
            endpoint_port=8768,
            advertised_url="http://127.0.0.1:8768/mcp",
            state_directory=fixture["deployment"] / "state",
            repository_root=fixture["repo"],
            python_executable=fixture["python"],
            manifest_path=fixture["manifest"],
            preflight_output=fixture["deployment"] / "preflight.json",
            profile_settings_template=fixture["settings"],
            game_executable=fixture["game_executable"],
            bookmark_events=fixture["bookmark_events"],
            capture_executable=fixture["capture_executable"],
            bridge_dll=fixture["bridge_dll"],
            bridge_injector=fixture["bridge_injector"],
        )

    def test_profile_is_portable_hash_bound_and_no_launch_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self._fixture(Path(temporary))
            payload = self._build(fixture)
            output = fixture["deployment"] / "profile.json"
            receipt = MODULE.write_profile(output, payload)
            loaded = load_operator_profile(output)

            self.assertEqual(
                receipt["status"], "READY_TO_DEPLOY_G2_NO_LAUNCH_OPERATOR_PROFILE"
            )
            self.assertFalse(receipt["ck3_launch_or_control_available"])
            self.assertEqual(loaded.target_id, "portable-operator")
            self.assertEqual(list(loaded.jobs), [MODULE.JOB_NAME])
            job = loaded.jobs[MODULE.JOB_NAME]
            self.assertEqual(job.exclusive_process_names, ())
            self.assertEqual(job.controls, {})
            self.assertEqual(job.command[-1], "--verify-only")
            self.assertNotIn("--authorize-private-live", job.command)
            self.assertNotIn("--artifact-dir", job.command)
            self.assertNotIn("--userdir", job.command)
            self.assertIn(str(fixture["capture_executable"].resolve()), job.command)
            self.assertNotIn(
                "xenoa", json.dumps(payload["target"], ensure_ascii=False).lower()
            )
            self.assertNotRegex(output.read_text(encoding="utf-8"), r"R\d+")
            file_rows = [row for row in job.required_paths if row.kind == "file"]
            self.assertTrue(file_rows)
            self.assertTrue(all(row.size is not None and row.sha256 for row in file_rows))
            self.assertIn(
                fixture["shadercache"].resolve(),
                [row.path for row in job.required_paths if row.kind == "directory"],
            )

    def test_manifest_hash_drift_is_rejected_before_profile_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self._fixture(Path(temporary))
            fixture["bridge_dll"].write_bytes(b"drift")
            with self.assertRaisesRegex(
                MODULE.ProfilePreparationError,
                "manifest dependency drifted: bridge_dll",
            ):
                self._build(fixture)

    def test_existing_preflight_output_and_profile_are_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = self._fixture(Path(temporary))
            preflight = fixture["deployment"] / "preflight.json"
            preflight.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(
                MODULE.ProfilePreparationError, "preflight-output already exists"
            ):
                self._build(fixture)

            preflight.unlink()
            profile = self._build(fixture)
            output = fixture["deployment"] / "profile.json"
            output.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(
                MODULE.ProfilePreparationError, "profile-output already exists"
            ):
                MODULE.write_profile(output, profile)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()

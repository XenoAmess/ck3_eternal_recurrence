from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

from tools import build_g2_preview_package as builder


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class G2PreviewPackageBuilderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "source-repo"
        self.repo.mkdir()
        required = {
            "ck3_autonomous_player/agent.py": b"print('agent')\n",
            "ck3_autonomous_player/pyproject.toml": b"[project]\nname='test'\n",
            "ck3_autonomous_player/src/xar_autoplayer/cli.py": b"# cli\n",
            "ck3_autonomous_player/native_bridge/research/"
            "run_campaign_root_context_live_acceptance.py": b"# eligibility\n",
            "tools/build_release.py": b"# release\n",
            "tools/requirements-static.txt": b"\n",
            "tools/g2_preview_operator.py": b"# operator\n",
            "tools/g2_preview_eligibility.py": b"# eligibility\n",
            "tools/build_g2_preview_package.py": b"# builder\n",
            "XenoAmess_s_Eternal_Recurrence/descriptor.mod": b'version="1"\n',
        }
        for relative, data in required.items():
            path = self.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.git("init", "-b", "master")
        self.git("config", "user.name", "Preview Test")
        self.git("config", "user.email", "preview@example.invalid")
        self.git("add", ".")
        self.git("commit", "-m", "fixture")
        self.commit = self.git("rev-parse", "HEAD").strip()

        self.inputs = self.root / "inputs"
        self.inputs.mkdir()
        self.checkpoint = self.write("checkpoint.ck3", b"checkpoint-r802")
        self.driver = self.write("driver-state.json", b'{"history":293}\n')
        self.dll = self.write("xar_ck3_bridge.dll", b"native-dll")
        self.injector = self.write("xar_ck3_bridge_injector.exe", b"injector")
        self.dlc = self.write("dlc_load.json", b'{"enabled_mods":[]}\n')
        self.production_manifest = self.write(
            "xar-production.manifest.json", b'{"format_version":2}\n'
        )
        self.evidence = self.write(
            "R802-postwar-cold-restore-seal.json", b'{"status":"GREEN"}\n'
        )
        self.production = self.inputs / "production"
        (self.production / "common").mkdir(parents=True)
        (self.production / "common" / "sample.txt").write_bytes(b"production")
        (self.production / "descriptor.mod").write_bytes(b'version="1"\n')
        production_snapshot = builder.snapshot(self.production)

        self.python = self.write("python.exe", b"python")
        self.game = self.root / "game"
        (self.game / "binaries").mkdir(parents=True)
        self.game_exe = self.game / "binaries" / "ck3.exe"
        self.game_exe.write_bytes(b"ck3-exact-build")
        self.no_launch_state = self.root / "no-launch-state"
        self.stage = self.root / "stage"
        self.spec = {
            "schema": builder.SPEC_SCHEMA,
            "output": {
                "stage_dir": str(self.stage),
                "zip_name": "g2-preview-ordinary-test-r802.zip",
            },
            "source": {
                "repo": str(self.repo),
                "commit": self.commit,
                "canonical_remote_url": (
                    "https://github.com/XenoAmess/ck3_eternal_recurrence.git"
                ),
            },
            "ck3": {
                "exact_build": "1.19.0.6",
                "exe_sha256": builder.sha256(self.game_exe),
                "exe_included": False,
            },
            "native": {
                "source_commit": "8" * 40,
                "relation": "test mixed-source relation",
                "dll": self.artifact(self.dll),
                "injector": self.artifact(self.injector),
            },
            "sample_resume": {
                "checkpoint": self.artifact(self.checkpoint),
                "driver_state": self.artifact(self.driver),
                "date_raw": 53150976,
                "history_index": 293,
                "episode_character_id": 31853,
                "episode_run_id": "native-31853-test",
                "pipe": r"\\.\pipe\xar-g2-preview-test",
                "expected_active_context": {
                    "war_ids": [],
                    "army_ids": [],
                    "active_event": None,
                    "pending_character_interaction": None,
                },
                "goal": {
                    "kind": "postwar_continuation",
                    "old_war_id": 5,
                    "rule": "old war consumed; never reoffer",
                },
            },
            "lifecycle": {
                "xar_enabled": "xar_off",
                "succession_lifecycle": "ordinary_campaign_succession",
                "ordinary_campaign_no_pact": True,
                "government": "feudal_government",
            },
            "content": {
                "dlc_load": self.artifact(self.dlc),
                "production_manifest": self.artifact(self.production_manifest),
                "production_tree": {
                    "path": str(self.production),
                    "file_count": len(production_snapshot),
                    "tree_sha256": builder.snapshot_digest(production_snapshot),
                },
                "enabled_mods_in_order": ["mod/xar_autoplayer.mod"],
                "disabled_dlcs": [],
                "installed_dlc_descriptors": 29,
                "dlc_entitlement_verified": False,
            },
            "bounds": {
                "formal_turns": 20,
                "timeout_seconds": 810,
                "session_ceiling_seconds": 900,
                "readiness_timeout_seconds": 720,
            },
            "evidence": [
                {
                    "source": str(self.evidence),
                    "dest": "evidence/R802-postwar-cold-restore-seal.json",
                    "sha256": builder.sha256(self.evidence),
                    "role": "cold_restore",
                }
            ],
            "release": {
                "candidate_status": builder.PENDING_STATUS,
                "g2_authoritative": "1/8",
                "supported_boundary": [
                    "Exact-build standard-feudal R802 postwar continuation."
                ],
                "unsupported_boundary": [
                    "Arbitrary saves, full campaign, and second seed are not qualified."
                ],
            },
            "preview_action": {
                "kind": "postwar_continuation",
                "required": "fresh package qualification",
            },
            "build_host": {
                "python": str(self.python),
                "game_dir": str(self.game),
                "no_launch_state_dir": str(self.no_launch_state),
            },
        }
        self.spec_path = self.root / "build-spec.json"
        builder.write_json(self.spec_path, self.spec)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *arguments: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(self.repo), *arguments], text=True
        ).strip()

    def write(self, name: str, data: bytes) -> Path:
        path = self.inputs / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    @staticmethod
    def artifact(path: Path) -> dict[str, str]:
        return {"path": str(path), "sha256": builder.sha256(path)}

    def write_no_launch_evidence(self, *, launched: bool = False) -> None:
        save = self.no_launch_state / "profile" / "save games" / "xar_checkpoint.ck3"
        state_driver = self.no_launch_state / "native-session" / "driver-state.json"
        environment = self.no_launch_state / "profile" / "xar-autoplayer-environment.json"
        save.parent.mkdir(parents=True, exist_ok=True)
        state_driver.parent.mkdir(parents=True, exist_ok=True)
        save.write_bytes(self.checkpoint.read_bytes())
        state_driver.write_bytes(b'{"rebound":true}\n')
        environment.write_bytes(b'{"environment":"test"}\n')
        receipt = {
            "schema": builder.REBIND_SCHEMA,
            "status": "rebound",
            "ok": True,
            "ck3_launch_attempted": launched,
            "desktop_interaction": False,
            "pipe_name": self.spec["sample_resume"]["pipe"],
            "process_inventory": {"processes": []},
            "environment": {
                "source_sha256": "a" * 64,
                "target_sha256": builder.sha256(environment),
            },
            "driver_state": {
                "source_sha256": builder.sha256(self.driver),
                "target_sha256": builder.sha256(state_driver),
            },
            "save": {
                "bytes_unchanged": True,
                "target": {"sha256": builder.sha256(save)},
            },
            "no_launch_preflight_expectations": {
                "expected_character_id": 31853,
                "expected_episode_run_id": "native-31853-test",
                "xar_enabled": "xar_off",
                "succession_lifecycle": "ordinary_campaign_succession",
                "ordinary_campaign_no_pact": True,
            },
        }
        builder.write_json(
            self.no_launch_state / "ordinary-seed-rebind-v1.json", receipt
        )
        preflight = self.no_launch_state / "preflights" / "fixture" / "report.json"
        builder.write_json(
            preflight,
            {
                "format_version": 1,
                "kind": "ck3_native_one_generation_preflight",
                "pipe": self.spec["sample_resume"]["pipe"],
                "status": "ready",
                "ok": True,
                "ck3_launch_attempted": launched,
                "process_inventory": {"processes": []},
                "profile": {
                    "agent_runtime_revision": self.commit,
                    "production_tree_sha256": self.spec["content"][
                        "production_tree"
                    ]["tree_sha256"],
                },
            },
        )

    def test_parameterized_stage_finalize_and_deterministic_assembly(self) -> None:
        staged = builder.stage(self.spec_path)
        self.assertEqual(
            staged["status"], "SEALED_INPUTS_WAITING_NO_LAUNCH_FINALIZATION"
        )
        self.write_no_launch_evidence()
        validation = builder.finalize_no_launch(self.spec_path)
        self.assertEqual(validation["status"], "GREEN_NO_LAUNCH_ONLY")
        first = builder.assemble(self.spec_path)
        first_bytes = Path(first["zip_path"]).read_bytes()
        second = builder.assemble(self.spec_path)
        self.assertEqual(first["zip_sha256"], second["zip_sha256"])
        self.assertEqual(first_bytes, Path(second["zip_path"]).read_bytes())
        self.assertEqual(first["zip_crc_test"], "GREEN")

        with zipfile.ZipFile(first["zip_path"]) as archive:
            self.assertIsNone(archive.testzip())
            names = archive.namelist()
            self.assertEqual(len(names), len(set(names)))
            self.assertNotIn("ck3.exe", {Path(name).name.casefold() for name in names})
            manifest = json.loads(archive.read("candidate-manifest.json"))
            template = json.loads(archive.read("operator-manifest.template.json"))
        self.assertEqual(manifest["source"]["agent_commit"], self.commit)
        self.assertEqual(manifest["sample_resume"]["history_index"], 293)
        self.assertEqual(manifest["sample_resume"]["saved_date_raw"], 53150976)
        self.assertEqual(
            manifest["expected_active_context"],
            {
                "war_ids": [],
                "army_ids": [],
                "active_event": None,
                "pending_character_interaction": None,
            },
        )
        self.assertEqual(template["source_repo"], "<ABSOLUTE_EXTRACTED_PACKAGE_ROOT>\\repo")
        self.assertNotIn("R783", json.dumps(manifest))
        self.assertNotIn("53145000", json.dumps(manifest))

    def test_contract_rejects_partial_lifecycle_and_invalid_bounds(self) -> None:
        partial = copy.deepcopy(self.spec)
        partial["lifecycle"].pop("ordinary_campaign_no_pact")
        with self.assertRaisesRegex(ValueError, "lifecycle must equal"):
            builder.validate_spec(partial)
        invalid = copy.deepcopy(self.spec)
        invalid["bounds"]["timeout_seconds"] = 720
        with self.assertRaisesRegex(ValueError, "must exceed"):
            builder.validate_spec(invalid)
        context = copy.deepcopy(self.spec)
        context["sample_resume"]["expected_active_context"]["war_ids"] = [5, 5]
        with self.assertRaisesRegex(ValueError, "unique positive"):
            builder.validate_spec(context)

    def test_stage_rejects_existing_target_and_input_hash_drift(self) -> None:
        self.stage.mkdir()
        with self.assertRaises(FileExistsError):
            builder.stage(self.spec_path)
        self.stage.rmdir()
        changed = copy.deepcopy(self.spec)
        changed["native"]["dll"]["sha256"] = "0" * 64
        builder.write_json(self.spec_path, changed)
        with self.assertRaisesRegex(ValueError, "hash differs"):
            builder.stage(self.spec_path)

    def test_finalize_rejects_any_ck3_launch(self) -> None:
        builder.stage(self.spec_path)
        self.write_no_launch_evidence(launched=True)
        with self.assertRaisesRegex(ValueError, "no-launch finalization checks failed"):
            builder.finalize_no_launch(self.spec_path)


if __name__ == "__main__":
    unittest.main()

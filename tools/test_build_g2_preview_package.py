from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
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
            ".gitignore": b"__pycache__/\n",
            "ck3_autonomous_player/agent.py": b"print('agent')\n",
            "ck3_autonomous_player/pyproject.toml": b"[project]\nname='test'\n",
            "ck3_autonomous_player/src/xar_autoplayer/cli.py": b"# cli\n",
            "ck3_autonomous_player/native_bridge/research/"
            "run_campaign_root_context_live_acceptance.py": b"# eligibility\n",
            "tools/build_release.py": b"# release\n",
            "tools/requirements-static.txt": b"\n",
            "tools/g2_preview_operator.py": b"# operator\n",
            "tools/g2_preview_eligibility.py": b"# eligibility\n",
            "tools/ck3_live_run_id.py": (
                Path(builder.__file__).with_name("ck3_live_run_id.py").read_bytes()
            ),
            "tools/build_g2_preview_package.py": b"# builder\n",
            "XenoAmess_s_Eternal_Recurrence/descriptor.mod": b'version="1"\n',
            "artifacts/tracked-contract.json": b'{"tracked":true}\n',
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
        self.dll = self.write(
            "xar_ck3_bridge.dll",
            b"native-dll\x00"
            + b"\x00".join(builder.REQUIRED_ORDINARY_SUCCESSION_NATIVE_STEPS),
        )
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
        environment_digest = "e" * 64
        builder.write_json(
            environment,
            {
                "environment": "test",
                "environment_sha256": environment_digest,
            },
        )
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
                "target_sha256": environment_digest,
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
                    "environment_sha256": environment_digest,
                    "production_tree_sha256": self.spec["content"][
                        "production_tree"
                    ]["tree_sha256"],
                },
            },
        )

    def test_quickstart_allocates_separately_for_each_live_launch(self) -> None:
        guide = builder.quickstart(self.spec)
        allocate = "ck3_live_run_id.py allocate --mod eternal-recurrence"
        self.assertEqual(guide.count(allocate), 2)
        prepare = guide.index("g2_preview_operator.py prepare-state")
        preflight = guide.index("g2_preview_eligibility.py --manifest")
        first_allocation = guide.index(allocate)
        live_eligibility = guide.index(
            "g2_preview_eligibility.py --manifest", preflight + 1
        )
        second_allocation = guide.index(allocate, first_allocation + 1)
        formal = guide.index("g2_preview_operator.py run --manifest")
        self.assertLess(prepare, preflight)
        self.assertLess(preflight, first_allocation)
        self.assertIn("--preflight-only", guide[preflight:first_allocation])
        self.assertLess(first_allocation, live_eligibility)
        self.assertLess(live_eligibility, second_allocation)
        self.assertLess(second_allocation, formal)
        self.assertIn("eligibility command **starts CK3**", guide)
        self.assertIn(
            "same persistent ledger", " ".join(guide.split()).replace("**", "")
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
            self.assertIn("repo/tools/ck3_live_run_id.py", names)
            manifest = json.loads(archive.read("candidate-manifest.json"))
            template = json.loads(archive.read("operator-manifest.template.json"))
            quickstart = archive.read("QUICKSTART.md").decode("utf-8")
        self.assertEqual(manifest["source"]["agent_commit"], self.commit)
        self.assertEqual(
            manifest["source"]["run_id_allocator_entry"],
            "repo/tools/ck3_live_run_id.py",
        )
        self.assertEqual(
            manifest["formal_entry"]["allocate_run_id"],
            "repo/tools/ck3_live_run_id.py allocate",
        )
        self.assertEqual(
            manifest["formal_entry"]["record_run_status"],
            "repo/tools/ck3_live_run_id.py status",
        )
        self.assertIn("included in this package", quickstart)
        self.assertIn("non-`C:`", quickstart)
        self.assertIn("%XAR_PREVIEW_ROOT%\\live-run-ids-v1", quickstart)
        self.assertIn("never initialize a blank ledger", quickstart)
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

        extracted = self.root / "fresh-extraction"
        with zipfile.ZipFile(first["zip_path"]) as archive:
            archive.extractall(extracted)
        allocator = extracted / "repo" / "tools" / "ck3_live_run_id.py"
        allocator_state = self.root / "portable-live-run-ids"
        allocated = json.loads(
            subprocess.check_output(
                [
                    sys.executable,
                    str(allocator),
                    "allocate",
                    "--mod",
                    "eternal-recurrence",
                    "--state-root",
                    str(allocator_state),
                    "--machine-id",
                    "preview-portable-test",
                ],
                text=True,
            )
        )
        self.assertEqual(
            allocated["run_id"],
            "preview-portable-test--eternal-recurrence--R0001",
        )
        recorded = json.loads(
            subprocess.check_output(
                [
                    sys.executable,
                    str(allocator),
                    "status",
                    "--run-id",
                    allocated["run_id"],
                    "--mod",
                    "eternal-recurrence",
                    "--machine-id",
                    "preview-portable-test",
                    "--status",
                    "completed-green",
                    "--reason",
                    "fresh-extraction no-launch packaging test",
                    "--state-root",
                    str(allocator_state),
                ],
                text=True,
            )
        )
        self.assertEqual(recorded["run_id"], allocated["run_id"])
        self.assertEqual(recorded["status"], "completed-green")
        migrated_state = self.root / "migrated-live-run-ids"
        shutil.copytree(allocator_state, migrated_state)
        continued = json.loads(
            subprocess.check_output(
                [
                    sys.executable,
                    str(allocator),
                    "allocate",
                    "--mod",
                    "eternal-recurrence",
                    "--state-root",
                    str(migrated_state),
                    "--machine-id",
                    "preview-portable-test",
                ],
                text=True,
            )
        )
        self.assertEqual(
            continued["run_id"],
            "preview-portable-test--eternal-recurrence--R0002",
        )
        original_counter = json.loads(
            (
                allocator_state
                / "preview-portable-test"
                / "eternal-recurrence"
                / "counter.json"
            ).read_text(encoding="utf-8")
        )
        migrated_counter = json.loads(
            (
                migrated_state
                / "preview-portable-test"
                / "eternal-recurrence"
                / "counter.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(original_counter["last_sequence"], 1)
        self.assertEqual(migrated_counter["last_sequence"], 2)
        self.assertTrue(
            (
                allocator_state
                / "preview-portable-test"
                / "eternal-recurrence"
                / "statuses.jsonl"
            ).is_file()
        )
        self.assertEqual(
            subprocess.check_output(
                ["git", "-C", str(extracted / "repo"), "rev-parse", "HEAD"],
                text=True,
            ).strip(),
            self.commit,
        )
        runtime_cache = (
            extracted
            / "repo"
            / "ck3_autonomous_player"
            / "src"
            / "xar_autoplayer"
            / "__pycache__"
            / "runtime.cpython-313.pyc"
        )
        runtime_cache.parent.mkdir(parents=True)
        runtime_cache.write_bytes(b"runtime cache")
        self.assertEqual(
            subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(extracted / "repo"),
                    "status",
                    "--porcelain=v1",
                    "--untracked-files=all",
                ],
                text=True,
            ),
            "",
        )

        equivalent_repo = self.root / "equivalent-source-repo"
        subprocess.run(
            ["git", "clone", "--no-local", "-q", str(self.repo), str(equivalent_repo)],
            check=True,
        )
        equivalent = copy.deepcopy(self.spec)
        equivalent["source"]["repo"] = str(equivalent_repo)
        equivalent["output"]["stage_dir"] = str(self.root / "equivalent-stage")
        equivalent_path = self.root / "equivalent-build-spec.json"
        builder.write_json(equivalent_path, equivalent)
        builder.stage(equivalent_path)
        builder.finalize_no_launch(equivalent_path)
        equivalent_download = builder.assemble(equivalent_path)
        self.assertEqual(first["zip_sha256"], equivalent_download["zip_sha256"])
        self.assertEqual(
            first_bytes, Path(equivalent_download["zip_path"]).read_bytes()
        )

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

    def test_stage_rejects_native_without_ordinary_succession_steps(self) -> None:
        self.dll.write_bytes(b"native-dll-without-private-succession-route")
        changed = copy.deepcopy(self.spec)
        changed["native"]["dll"]["sha256"] = builder.sha256(self.dll)
        builder.write_json(self.spec_path, changed)
        with self.assertRaisesRegex(
            ValueError,
            "native.dll lacks ordinary succession private steps",
        ) as failure:
            builder.stage(self.spec_path)
        self.assertIn("query-current-timeline-blocker-context-v1", str(failure.exception))
        self.assertIn("continue-death-succession-modal-v1", str(failure.exception))

    def test_finalize_rejects_any_ck3_launch(self) -> None:
        builder.stage(self.spec_path)
        self.write_no_launch_evidence(launched=True)
        with self.assertRaisesRegex(ValueError, "no-launch finalization checks failed"):
            builder.finalize_no_launch(self.spec_path)

    def test_promotion_binds_exact_zip_and_cold_restore_chain(self) -> None:
        builder.stage(self.spec_path)
        self.write_no_launch_evidence()
        builder.finalize_no_launch(self.spec_path)
        download = builder.assemble(self.spec_path)
        zip_path = Path(download["zip_path"])
        zip_before = zip_path.read_bytes()
        qualification_root = self.root / "qualification"
        qualification_root.mkdir()

        def evidence_file(name: str, payload: dict[str, object]) -> dict[str, str]:
            path = qualification_root / name
            builder.write_json(path, payload)
            return {"path": name, "sha256": builder.sha256(path)}

        final_checkpoint = qualification_root / "final-checkpoint.ck3"
        final_driver = qualification_root / "final-driver.json"
        final_checkpoint.write_bytes(b"cold-final-checkpoint")
        final_driver.write_bytes(b'{"cold":"final"}\n')
        formal_checkpoint = "1" * 64
        formal_driver = "2" * 64
        cold_checkpoint = builder.sha256(final_checkpoint)
        cold_driver = builder.sha256(final_driver)
        rounds: dict[str, object] = {}
        round_specs = (
            (
                "eligibility",
                "R803",
                {"ok": True, "status": "GREEN_READ_ONLY", "checks": {"all": True}},
                None,
            ),
            (
                "formal_stop",
                "R804",
                {
                    "ok": False,
                    "status": "operator_stop_checkpointed",
                    "outcome": "operator_stopped",
                },
                {
                    "ok": True,
                    "status": "completed",
                    "formal_exit_code": 0,
                    "checkpoint_sha256_after": formal_checkpoint,
                    "driver_state_sha256_after": formal_driver,
                },
            ),
            (
                "cold_restore",
                "R805",
                {"ok": True, "status": "turn_limit"},
                {
                    "ok": True,
                    "status": "completed",
                    "formal_exit_code": 0,
                    "checkpoint_sha256_before": formal_checkpoint,
                    "driver_state_sha256_before": formal_driver,
                    "checkpoint_sha256_after": cold_checkpoint,
                    "driver_state_sha256_after": cold_driver,
                },
            ),
        )
        for role, round_id, report, receipt in round_specs:
            row: dict[str, object] = {
                "round_id": round_id,
                "report": evidence_file(f"{round_id}-report.json", report),
                "closed_ledger": evidence_file(
                    f"{round_id}-closed.json",
                    {
                        "round_id": round_id,
                        "package_zip_sha256": download["zip_sha256"],
                        "source_commit": self.commit,
                        "cleanup": {"ok": True, "tree_gone": True},
                    },
                ),
            }
            if receipt is not None:
                row["operator_receipt"] = evidence_file(
                    f"{round_id}-receipt.json", receipt
                )
            rounds[role] = row
        qualification = {
            "schema": builder.QUALIFICATION_SCHEMA,
            "package_zip_sha256": download["zip_sha256"],
            "source_commit": self.commit,
            "native_source_commit": "8" * 40,
            "gates": {gate: True for gate in builder.PROMOTION_GATES},
            "rounds": rounds,
            "chain": {
                "formal_checkpoint_after_sha256": formal_checkpoint,
                "formal_driver_after_sha256": formal_driver,
                "cold_checkpoint_before_sha256": formal_checkpoint,
                "cold_driver_before_sha256": formal_driver,
                "cold_checkpoint_after_sha256": cold_checkpoint,
                "cold_driver_after_sha256": cold_driver,
                "formal_process_id": 100,
                "cold_process_id": 200,
                "final_checkpoint": self.artifact(final_checkpoint),
                "final_driver_state": self.artifact(final_driver),
            },
            "output": {"qualification_receipt": "live-qualification.json"},
        }
        qualification_path = qualification_root / "qualification-input.json"
        builder.write_json(qualification_path, qualification)
        promoted = builder.promote(self.spec_path, qualification_path)
        self.assertEqual(promoted["status"], "GO_RUNNABLE_PREVIEW")
        self.assertEqual(zip_before, zip_path.read_bytes())
        receipt = builder.read_json(Path(promoted["qualification_receipt"]))
        self.assertEqual(receipt["immutable_package"]["zip"]["zip_sha256"], download["zip_sha256"])
        self.assertEqual(receipt["g2_authoritative"]["status"], "1/8")
        external_download = builder.read_json(self.stage / "download-manifest.json")
        self.assertEqual(external_download["status"], "GO_RUNNABLE_PREVIEW")


if __name__ == "__main__":
    unittest.main()

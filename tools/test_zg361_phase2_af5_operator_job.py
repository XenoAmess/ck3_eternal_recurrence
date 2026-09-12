from __future__ import annotations

import importlib.util
import json
import tempfile
from types import SimpleNamespace
from pathlib import Path
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


job = load("af5_operator_job_tested", HERE / "zg361_phase2_af5_operator_job.py")


class Af5OperatorJobTests(unittest.TestCase):
    def test_nested_bootstrap_paths_are_explicitly_serialized(self) -> None:
        value = {
            "target": Path(r"Z:\candidate\mod"),
            "nested": [
                {"checkpoint": Path(r"Z:\candidate\save.ck3")},
                (Path(r"Z:\candidate\manifest.json"),),
            ],
        }
        converted = job.bootstrap_evidence_json_value(value)
        self.assertEqual(converted["target"], r"Z:\candidate\mod")
        self.assertEqual(
            converted["nested"],
            [
                {"checkpoint": r"Z:\candidate\save.ck3"},
                [r"Z:\candidate\manifest.json"],
            ],
        )
        json.dumps(converted)

    def test_bootstrap_serializer_rejects_unexpected_types(self) -> None:
        with self.assertRaisesRegex(TypeError, "unsupported bootstrap evidence type"):
            job.bootstrap_evidence_json_value({"bad": object()})

    def test_presets_use_explicit_hash_bound_vanilla_path(self) -> None:
        observed: list[Path] = []

        class Acceptance:
            @staticmethod
            def declared_vanilla_rule_defaults(path):
                observed.append(path)
                return [("rule_a", "setting_a"), ("rule_b", "setting_b")]

        explicit = Path(r"Z:\ck3\game\common\game_rules\00_game_rules.txt")
        rendered = job.render_presets_from_explicit_vanilla(Acceptance, explicit)
        self.assertEqual(observed, [explicit])
        self.assertIn("setting_a setting_b zg361_on zg361_freq_yearly zg361_ratio_strict", rendered)

    def test_no_launch_preflight_is_inert(self) -> None:
        with mock.patch.object(job, "ck3_pids", return_value=[]):
            result = job.no_launch_preflight()
        self.assertEqual(result["result"], "GREEN")
        self.assertFalse(result["launch_requested"])
        self.assertFalse(result["cleanup_requested"])
        self.assertEqual(
            result["controls"],
            ["status", "run-af5", "retry-policy", "retry-af5", "cleanup"],
        )

    def test_standard_retry_policy_rejects_without_retained_red(self) -> None:
        instance = job.Af5OperatorJob(Path("activation.json"))
        with mock.patch.object(job, "ck3_pids", return_value=[]):
            response = instance.retry_policy()
        self.assertFalse(response["accepted"])
        self.assertEqual(response["control"], "retry-policy")
        self.assertEqual(response["job_retry_control"], "retry-af5")
        policy = response["retry_policy"]
        self.assertEqual(policy["kind"], "xar_pre_input_retry_policy_v1")
        self.assertEqual(policy["reason_code"], "NO_ELIGIBLE_RETAINED_FAILURE")
        self.assertTrue(policy["prior_attempt_immutable"])
        self.assertFalse(policy["game_deadline_may_expand"])

    def test_failure_evidence_is_preserved_without_running_or_reselecting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary) / "artifacts"
            instance = job.Af5OperatorJob(Path(temporary) / "activation.json")
            instance.bound = {"artifact_directory": artifacts}
            instance.stage = "source_result"
            payload = {
                "selection_ack": {"accepted": True},
                "after_selection": {"revision": 5, "active_event": None},
                "checkpoint": Path(temporary) / "source.ck3",
            }
            error = job.Af5JobError("result event did not arrive", payload)
            with mock.patch.object(job, "ck3_pids", return_value=[]):
                instance._record_failure(error)
                result = instance.status()
            saved = job.read_object(artifacts / "af5-red.json")
            self.assertEqual(saved["failure_stage"], "source_result")
            self.assertEqual(saved["evidence"]["after_selection"]["revision"], 5)
            self.assertTrue(saved["evidence"]["selection_ack"]["accepted"])
            self.assertEqual(saved["evidence"]["checkpoint"], str(payload["checkpoint"]))
            self.assertEqual(result["product_result"], "RED")
            self.assertEqual(result["cleanup_result"], "PENDING")

    def test_cleanup_success_does_not_turn_product_failure_green(self) -> None:
        instance = job.Af5OperatorJob(Path("unused-activation.json"))
        with mock.patch.object(job, "ck3_pids", return_value=[]):
            instance._record_failure(job.Af5JobError("business failed"))
            status = instance.perform_cleanup()
        self.assertEqual(status["state"], "CLEANED")
        self.assertEqual(status["cleanup_result"], "GREEN")
        self.assertEqual(status["product_result"], "RED")
        self.assertEqual(status["result"], "RED")
        self.assertEqual(instance.exit_code(), 1)

    def test_green_product_still_requires_green_cleanup_for_successful_exit(self) -> None:
        instance = job.Af5OperatorJob(Path("unused-activation.json"))
        instance.product_result = "GREEN"
        instance.state = "AF5_GREEN_PARKED"
        self.assertEqual(instance.exit_code(), 1)
        with mock.patch.object(job, "ck3_pids", return_value=[]):
            status = instance.perform_cleanup()
        self.assertEqual(status["product_result"], "GREEN")
        self.assertEqual(status["cleanup_result"], "GREEN")
        self.assertEqual(instance.exit_code(), 0)

    def test_no_launch_cleanup_does_not_claim_product_success(self) -> None:
        instance = job.Af5OperatorJob(Path("unused-activation.json"))
        with mock.patch.object(job, "ck3_pids", return_value=[]):
            status = instance.perform_cleanup()
        self.assertEqual(status["product_result"], "PENDING")
        self.assertEqual(status["result"], "PENDING")
        self.assertEqual(status["cleanup_result"], "GREEN")

    def test_verified_terminal_is_saved_through_shared_checkpoint_service(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            activation, _ = make_activation(root)
            instance = job.Af5OperatorJob(activation)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            bound = {
                "round": "R402", "artifact_directory": artifacts,
                "expected_hashes": {"product_tree_sha256": "A" * 64, "code_commit": "a" * 40},
                "repository_root": root,
                "checkpoint": root / "checkpoint.ck3", "bridge_dll": root / "bridge.dll",
            }
            instance.bound = bound
            instance.binding = {"bridge_pid": 123, "connection_generation": 1}
            checkpoint = {"status": "saved", "path": str(root / "checkpoint.ck3"), "size": 7, "sha256": "B" * 64}
            instance.service = mock.Mock()
            instance.service.snapshot.return_value = {"revision": 17, "paused": True}
            instance.service.save_checkpoint.return_value = {"accepted": True, "checkpoint": checkpoint}
            archive = {"path": str(artifacts / "af5-terminal.ck3"), "bytes": 7, "sha256": "B" * 64}
            instance.runner = mock.Mock()
            instance.runner._phase2_archive_checkpoint.return_value = archive
            action = mock.Mock(return_value={
                "result": "GREEN", "provider_observed": True,
                "terminal_postcondition_verified": True,
                "action_ack_is_business_postcondition": False,
            })
            advance = mock.Mock()
            module = SimpleNamespace(run_af5_terminal_action_cell=action, advance_to_af5=advance)
            with mock.patch.object(job.importlib, "import_module", return_value=module):
                instance._execute_action(bound)
            action.assert_called_once_with(instance.service, advance_to_af5=advance, request_nonce="R402.af5.terminal")
            instance.service.save_checkpoint.assert_called_once_with(expected_revision=17)
            instance.runner._phase2_archive_checkpoint.assert_called_once_with(
                checkpoint, artifacts / "af5-terminal.ck3", save_lineage_id="R402.af5.terminal",
            )
            self.assertEqual(instance.product_result, "GREEN")
            self.assertEqual(job.read_object(artifacts / "af5-terminal-checkpoint.json")["checkpoint"], archive)
            self.assertTrue((artifacts / "af5-terminal-green.json").is_file())

    def test_checkpoint_failure_retains_already_verified_product_result(self) -> None:
        instance = job.Af5OperatorJob(Path("unused-activation.json"))
        instance.af5_evidence = {"result": "GREEN", "provider_observed": True}
        instance.product_result = "GREEN"
        instance.stage = "terminal_checkpoint"
        with mock.patch.object(job, "ck3_pids", return_value=[]):
            instance._record_failure(job.Af5JobError("save failed"))
            status = instance.perform_cleanup()
        self.assertEqual(status["product_result"], "GREEN")
        self.assertEqual(status["result"], "RED")
        self.assertEqual(status["cleanup_result"], "GREEN")
        self.assertEqual(instance.exit_code(), 1)

    def test_hot_retry_reuses_service_without_materialization_or_launch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            activation, payload = make_activation(root)
            identity = {"head": payload["expected_hashes"]["code_commit"], "tracked_dirty": False}
            with mock.patch.object(job, "git_identity", return_value=identity):
                original = job.validate_activation(activation, process_probe=lambda: [], require_empty_slot=False)
            artifacts = original["artifact_directory"]
            artifacts.mkdir()
            job.write_object(artifacts / "af5-red.json", {"result": "RED", "evidence": {"selected_option_number": None}})
            repaired = {**original, "repository_root": root / "repaired-frozen"}
            repaired["expected_hashes"] = {**original["expected_hashes"], "code_commit": "b" * 40}
            instance = job.Af5OperatorJob(activation)
            instance.bound = original
            instance.binding = {"bridge_pid": 123, "connection_generation": 1}
            service = mock.Mock()
            service.snapshot.return_value = {"paused": True, "date_raw": 999,
                "played_character": {"id": 5}, "active_event": {"instance_id": 7},
                "diagnostics": {"connected": True, "bridge_pid": 123, "connection_generation": 1}}
            instance.service = service
            instance.stage = "af5_terminal_action"
            instance.state = "AF5_RED_PARKED"
            with mock.patch.object(job, "validate_activation", return_value=repaired), \
                 mock.patch.object(job, "ck3_pids", return_value=[123]), \
                 mock.patch.object(instance, "_reload_action_modules") as reload_action, \
                 mock.patch.object(instance, "_execute") as cold_setup, \
                 mock.patch.object(instance, "_execute_action") as action, \
                 mock.patch("builtins.print"):
                instance._run_retry()
            cold_setup.assert_not_called()
            reload_action.assert_called_once_with(repaired["repository_root"])
            action.assert_called_once_with(repaired)
            self.assertIs(instance.service, service)
            self.assertTrue((artifacts / "af5-red-attempt-01.json").is_file())
            self.assertTrue((artifacts / "af5-retry-attempt-02.json").is_file())

    def test_activation_binds_supplied_execution_commit_and_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            activation, payload = make_activation(Path(temporary))
            identity = {"head": payload["expected_hashes"]["code_commit"], "tracked_dirty": False}
            with mock.patch.object(job, "git_identity", return_value=identity) as probe:
                bound = job.validate_activation(activation, process_probe=lambda: [], require_empty_slot=True)
            self.assertEqual(bound["expected_hashes"], payload["expected_hashes"])
            probe.assert_called_once_with(Path(payload["repository_root"]))
            self.assertFalse(Path(payload["state_directory"]).exists())
            self.assertFalse(Path(payload["artifact_directory"]).exists())
            with mock.patch.object(job, "git_identity", return_value={"head": "b" * 40, "tracked_dirty": False}):
                with self.assertRaisesRegex(job.Af5JobError, "repository identity differs"):
                    job.validate_activation(activation, process_probe=lambda: [], require_empty_slot=True)

    def test_activation_rejects_changed_checkpoint_before_launch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            activation, payload = make_activation(Path(temporary))
            Path(payload["checkpoint"]["path"]).write_bytes(b"changed checkpoint")
            identity = {"head": payload["expected_hashes"]["code_commit"], "tracked_dirty": False}
            with mock.patch.object(job, "git_identity", return_value=identity):
                with self.assertRaisesRegex(job.Af5JobError, "checkpoint hash/size binding differs"):
                    job.validate_activation(activation, process_probe=lambda: [], require_empty_slot=True)
            self.assertFalse(Path(payload["state_directory"]).exists())
            self.assertFalse(Path(payload["artifact_directory"]).exists())


def make_activation(root: Path) -> tuple[Path, dict[str, object]]:
    def make_file(relative: str, contents: bytes = b"fixture") -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
        return path

    repository = root / "frozen-execution"
    for relative in (
        "tools/run_zhongguo_acceptance.py", "tools/run_acceptance.py",
        "tools/zg361_phase2_af5_action_cell.py",
        "ck3_autonomous_player/src/xar_autoplayer/native_session.py",
    ):
        make_file("frozen-execution/" + relative)
    game_exe = make_file("game/binaries/ck3.exe")
    rules = make_file("game/game/common/game_rules/00_game_rules.txt")
    make_file("startup/pdx_settings.txt")
    (root / "startup/shadercache").mkdir()
    (root / "product").mkdir()
    checkpoint = make_file("checkpoint.ck3")
    bridge = make_file("bridge.dll")
    injector = make_file("injector.exe")
    cleanup = make_file("cleanup.json", json.dumps({
        "result": "GREEN", "scope": "phase2_managed_native_session_cleanup",
    }).encode())
    product_sha = "A" * 64
    projection = make_file("projection.json", json.dumps({
        "schema_version": 1, "kind": "zg361_phase2_product_projection",
        "source_tree_sha256": product_sha,
    }).encode())
    payload = {
        "schema_version": 1,
        "kind": job.KIND,
        "rounds": {"frontend_warmup": "R401", "gameplay": "R402"},
        "repository_root": str(repository),
        "game_directory": str(root / "game"),
        "product_root": str(root / "product"),
        "startup_template_profile": str(root / "startup"),
        "checkpoint": job.file_record(checkpoint),
        "product_projection_manifest": job.file_record(projection),
        "bridge_dll": job.file_record(bridge),
        "bridge_injector": job.file_record(injector),
        "prior_cleanup": job.file_record(cleanup),
        "vanilla_game_rules": job.file_record(rules),
        "state_directory": str(root / "live-state"),
        "artifact_directory": str(root / "live-artifacts"),
        "bridge_pipe": r"\\.\pipe\xar_ck3_bridge_zg361_" + "a" * 32,
        "warmup_bridge_pipe": r"\\.\pipe\xar_ck3_bridge_zg361_" + "b" * 32,
        "expected_hashes": {
            "code_commit": "a" * 40,
            "product_tree_sha256": product_sha,
            "checkpoint_sha256": job.sha256(checkpoint),
            "projection_manifest_sha256": job.sha256(projection),
            "bridge_dll_sha256": job.sha256(bridge),
            "game_exe_sha256": job.sha256(game_exe),
            "vanilla_game_rules_sha256": job.sha256(rules),
        },
    }
    activation = root / "activation.json"
    job.write_object(activation, payload)
    return activation, payload


if __name__ == "__main__":
    unittest.main()

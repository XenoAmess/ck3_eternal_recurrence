from contextlib import nullcontext
import importlib.metadata
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from xar_autoplayer import environment as environment
from xar_autoplayer import cli
from xar_autoplayer.errors import AgentError


class NativeOnlyProfileDependencyTests(unittest.TestCase):
    def test_native_profile_records_required_core_packages_without_claiming_cuda(self):
        def versions(name):
            if name not in environment.NATIVE_HEADLESS_RUNTIME_DISTRIBUTIONS:
                raise importlib.metadata.PackageNotFoundError(name)
            return "fixture-native-version"
        with patch.object(environment.importlib.metadata, "version", side_effect=versions):
            result = environment.agent_runtime_fingerprint(runtime_dependency_profile="native-only")
        self.assertEqual(result["runtime_dependency_profile"], "native-only")
        self.assertEqual(result["disabled_capabilities"], ["visual_ocr", "hybrid_fallback"])
        self.assertEqual(set(result["distributions"]), set(environment.NATIVE_HEADLESS_RUNTIME_DISTRIBUTIONS))
        self.assertFalse(any(name.startswith("nvidia-") for name in result["distributions"]))
        self.assertNotIn("rapidocr-onnxruntime", result["distributions"])
        self.assertNotIn("onnxruntime-gpu", result["distributions"])
        self.assertEqual(result["distributions"], {
            name: "fixture-native-version"
            for name in environment.NATIVE_HEADLESS_RUNTIME_DISTRIBUTIONS
        })

    def test_full_default_keeps_existing_distribution_contract_and_shape(self):
        with patch.object(environment.importlib.metadata, "version", return_value="fixture-version"):
            result = environment.agent_runtime_fingerprint()
        self.assertEqual(set(result["distributions"]), set(environment.RUNTIME_DISTRIBUTIONS))
        self.assertNotIn("runtime_dependency_profile", result)
        self.assertNotIn("disabled_capabilities", result)
        self.assertEqual(environment.recorded_runtime_dependency_profile(result), "full")

    def test_missing_required_native_package_still_fails(self):
        original = importlib.metadata.version
        def versions(name):
            if name == "pydantic":
                raise importlib.metadata.PackageNotFoundError(name)
            return original(name)
        with patch.object(environment.importlib.metadata, "version", side_effect=versions):
            with self.assertRaisesRegex(AgentError, "missing: pydantic"):
                environment.agent_runtime_fingerprint(runtime_dependency_profile="native-only")

    def test_unknown_dependency_profile_is_rejected(self):
        with self.assertRaisesRegex(AgentError, "unsupported runtime dependency profile"):
            environment.agent_runtime_fingerprint(runtime_dependency_profile="skip-all")
        with self.assertRaisesRegex(AgentError, "unsupported runtime dependency profile"):
            environment.recorded_runtime_dependency_profile({"runtime_dependency_profile": "skip-all"})

    def test_cli_requires_an_explicit_native_only_prepare_selection(self):
        self.assertEqual(cli.parser().parse_args(["prepare-profile"]).runtime_dependency_profile, "full")
        self.assertIsNone(cli.parser().parse_args(["verify-profile"]).runtime_dependency_profile)
        self.assertEqual(cli.parser().parse_args([
            "prepare-profile", "--runtime-dependency-profile", "native-only",
        ]).runtime_dependency_profile, "native-only")

    def test_prepare_passes_explicit_profile_to_original_locked_producer(self):
        with tempfile.TemporaryDirectory() as temporary:
            spec = environment.make_spec(Path(temporary) / "state", Path(temporary) / "game")
            with (patch.object(environment, "ensure_state_path_safe"),
                  patch.object(environment, "exclusive_state_lock", return_value=nullcontext()),
                  patch.object(environment, "ck3_processes", return_value=[]),
                  patch.object(environment, "_prepare_profile_locked", return_value={"fixture": True}) as producer):
                result = environment.prepare_profile(spec, xar_enabled="xar_off", runtime_dependency_profile="native-only")
            self.assertEqual(result, {"fixture": True})
            producer.assert_called_once_with(spec, xar_enabled="xar_off", display_mode="fullscreen", runtime_dependency_profile="native-only")

    def test_verifier_uses_recorded_profile_and_rejects_explicit_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            spec = environment.make_spec(Path(temporary) / "state", Path(temporary) / "game")
            spec.profile_dir.mkdir(parents=True)
            manifest = {
                "state_dir": str(spec.state_dir.resolve()),
                "profile_dir": str(spec.profile_dir.resolve()),
                "display": environment.display_contract("fullscreen"),
                "agent_runtime": {"sha256": "fixture-runtime", "runtime_dependency_profile": "native-only"},
            }
            manifest["environment_sha256"] = environment._contract_digest(manifest)
            spec.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with (patch.object(environment, "ensure_state_path_safe"),
                  patch.object(environment, "agent_runtime_fingerprint", return_value={"sha256": "fixture-runtime"}) as fingerprint,
                  patch.object(environment, "launcher_identity", side_effect=RuntimeError("fixture stopped after dependency validation"))):
                with self.assertRaisesRegex(RuntimeError, "after dependency validation"):
                    environment.verify_profile(spec)
                fingerprint.assert_called_once_with(runtime_dependency_profile="native-only")
                fingerprint.reset_mock()
                with self.assertRaisesRegex(AgentError, "runtime dependency profile differs"):
                    environment.verify_profile(spec, runtime_dependency_profile="full")
                fingerprint.assert_not_called()


if __name__ == "__main__":
    unittest.main()

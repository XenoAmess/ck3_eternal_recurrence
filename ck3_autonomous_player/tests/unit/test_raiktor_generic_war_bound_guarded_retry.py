from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "native_bridge"
    / "research"
    / "verify_raiktor_generic_war_bound_guarded_retry.py"
)
SPEC = importlib.util.spec_from_file_location(
    "verify_raiktor_generic_war_bound_guarded_retry", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


QUERY = {
    "terms_query_count": 2,
    "allowed_gameplay_commands": [
        "query-war-termination-terms-v1-50331699",
        "query-war-termination-terms-v1-50331699",
    ],
    "mutation_commands": [],
    "strict_equal_layers": ["child", "aggregate", "session", "cache"],
    "paused": True,
}
READINESS = {
    "generic_war_bound_current_ready": True,
    "source_specific_war_bound_ready": False,
    "pre_soldiers_ready": False,
    "proven_soldier_loss_ready": False,
    "action_terms_ready": False,
    "automatic_surrender_ready": False,
}


class GuardedRetryVerifyOnlyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source_root = self.root / "source"
        self.native = self.source_root / "ck3_autonomous_player/native_bridge"
        (self.native / "src").mkdir(parents=True)
        (self.native / "research").mkdir(parents=True)
        self.build = self.root / "build"
        self.build.mkdir()
        self.contract = self.root / "contract.json"
        self.manifest = self.root / "manifest.json"
        self.dll = self.root / "xar_ck3_bridge.dll"
        self.injector = self.root / "xar_bridge_injector.exe"
        self.runner = self.native / "research/run_war_termination_terms_live_acceptance.py"
        self.attempt = self.root / "attempt"
        self.contract.write_text(
            json.dumps(
                {
                    "frozen_unguarded_bridge_dll_sha256": "0" * 64,
                    "query_contract": QUERY,
                    "readiness_boundary": READINESS,
                }
            ),
            encoding="utf-8",
        )
        self.manifest.write_text(
            json.dumps(
                {"query_contract": QUERY, "readiness_boundary": READINESS}
            ),
            encoding="utf-8",
        )
        self.dll.write_bytes(b"guarded current dll")
        self.injector.write_bytes(b"injector")
        self.runner.write_text(
            'parser.add_argument("--bridge-dll")\nNativeBridgeLaunchConfig\n',
            encoding="utf-8",
        )
        self._write_ready_source()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_ready_source(self) -> None:
        (self.native / "CMakeLists.txt").write_text(
            """
option(
  XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1
  "Install the existing exact-build startup containment chain"
  OFF
)
if(XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=1
  )
endif()
""",
            encoding="utf-8",
        )
        (self.native / "src/bridge.cpp").write_text(
            """
#if defined(XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1)
constexpr bool kStartupFailureContainmentEnabledV1 = true;
#else
constexpr bool kStartupFailureContainmentEnabledV1 = false;
#endif
constexpr bool kStartupParticle2StageRecorderEnabledV1 = false;
static_assert(!(kStartupFailureContainmentEnabledV1 &&
                kStartupParticle2StageRecorderEnabledV1));
InstallStartupParticle2NullGuardV1();
InstallStartupParticle2ConsumerGuardV1();
InstallStartupDx11RenderContextDrawGuardV1();
InstallStartupLocalizeCurrentRootGuardV1();
""",
            encoding="utf-8",
        )
        (self.build / "CMakeCache.txt").write_text(
            "XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1:BOOL=ON\n"
            "XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1:BOOL=OFF\n",
            encoding="utf-8",
        )

    def _verify(self) -> dict[str, object]:
        return VERIFY.verify(
            contract_path=self.contract,
            source_root=self.source_root,
            build_dir=self.build,
            base_manifest_path=self.manifest,
            bridge_dll=self.dll,
            bridge_injector=self.injector,
            runner_path=self.runner,
            attempt_dir=self.attempt,
            inventory_provider=lambda: [],
        )

    def test_proposed_default_off_option_with_guarded_cache_is_ready(self) -> None:
        result = self._verify()
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "READY_TO_FREEZE")
        self.assertEqual(result["no_launch_boundary"]["query_count"], 0)
        self.assertFalse(result["no_launch_boundary"]["ck3_started"])
        identities = result["identities"]
        for key in (
            "cmake_sha256",
            "bridge_source_sha256",
            "cmake_cache_sha256",
            "runner_sha256",
            "bridge_dll_sha256",
            "bridge_injector_sha256",
        ):
            self.assertRegex(identities[key], r"^[0-9A-F]{64}$")

    def test_current_hard_disabled_source_is_blocked(self) -> None:
        bridge = self.native / "src/bridge.cpp"
        bridge.write_text(
            bridge.read_text(encoding="utf-8").replace(
                "#if defined(XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1)\n"
                "constexpr bool kStartupFailureContainmentEnabledV1 = true;\n"
                "#else\nconstexpr bool kStartupFailureContainmentEnabledV1 = false;\n#endif",
                "constexpr bool kStartupFailureContainmentEnabledV1 = false;",
            ),
            encoding="utf-8",
        )
        result = self._verify()
        self.assertFalse(result["ok"])
        self.assertFalse(result["checks"]["containment_constant_macro_bound"])

    def test_stage_recorder_on_is_rejected(self) -> None:
        cache = self.build / "CMakeCache.txt"
        cache.write_text(
            cache.read_text(encoding="utf-8").replace(
                "XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1:BOOL=OFF",
                "XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1:BOOL=ON",
            ),
            encoding="utf-8",
        )
        result = self._verify()
        self.assertFalse(result["checks"]["stage_recorder_cache_off"])
        self.assertFalse(result["ok"])

    def test_query_or_identity_or_mutation_drift_is_rejected(self) -> None:
        for key, value in (
            ("terms_query_count", 1),
            ("mutation_commands", ["accept-war-terms"]),
            ("strict_equal_layers", ["child", "aggregate"]),
        ):
            with self.subTest(key=key):
                manifest = {"query_contract": dict(QUERY), "readiness_boundary": READINESS}
                manifest["query_contract"][key] = value
                self.manifest.write_text(json.dumps(manifest), encoding="utf-8")
                self.assertFalse(self._verify()["ok"])

    def test_runner_has_exactly_one_bridge_slot(self) -> None:
        self.runner.write_text(
            'parser.add_argument("--bridge-dll")\n'
            'parser.add_argument("--bridge-dll")\nNativeBridgeLaunchConfig\n',
            encoding="utf-8",
        )
        result = self._verify()
        self.assertFalse(result["checks"]["one_bridge_dll_argument"])

    def test_wrapper_runner_delegates_the_single_bridge_slot(self) -> None:
        self.runner.write_text(
            "parser = terms_live._parser()\nterms_live._run(\n",
            encoding="utf-8",
        )
        result = self._verify()
        self.assertTrue(result["checks"]["one_bridge_dll_argument"])
        self.assertTrue(
            result["checks"]["prepare_startup_export_used_by_injector_path"]
        )

    def test_running_ck3_or_existing_attempt_blocks_freeze(self) -> None:
        result = VERIFY.verify(
            contract_path=self.contract,
            source_root=self.source_root,
            build_dir=self.build,
            base_manifest_path=self.manifest,
            bridge_dll=self.dll,
            bridge_injector=self.injector,
            runner_path=self.runner,
            attempt_dir=self.attempt,
            inventory_provider=lambda: [{"name": "ck3.exe", "pid": 42}],
        )
        self.assertFalse(result["checks"]["exclusive_ck3_inventory_empty"])
        self.attempt.mkdir()
        result = self._verify()
        self.assertFalse(result["checks"]["attempt_dir_absent"])

    def test_verifier_contains_no_ck3_launch_primitive(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in (
            "Start-Process",
            "NativeBridgeLaunchConfig(",
            "native_session(",
            "subprocess.Popen(",
            "os.startfile(",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("CreateToolhelp32Snapshot", source)


if __name__ == "__main__":
    unittest.main()

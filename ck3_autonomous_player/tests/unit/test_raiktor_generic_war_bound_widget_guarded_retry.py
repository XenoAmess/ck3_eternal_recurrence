from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "native_bridge/research/verify_raiktor_generic_war_bound_widget_guarded_retry.py"
)
SPEC = importlib.util.spec_from_file_location("_widget_guard_verify", SCRIPT)
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


class WidgetGuardedRetryVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.native = self.source / "ck3_autonomous_player/native_bridge"
        (self.native / "src").mkdir(parents=True)
        (self.native / "research/fixtures").mkdir(parents=True)
        self.build = self.root / "build"
        self.build.mkdir()
        self.contract = self.root / "contract.json"
        self.manifest = self.root / "manifest.json"
        self.dll = self.root / "bridge.dll"
        self.injector = self.root / "injector.exe"
        self.runner = self.root / "runner.py"
        self.attempt = self.root / "never-created-attempt"
        self.dll.write_bytes(b"fifth guard dll")
        self.injector.write_bytes(b"injector")
        self.runner.write_text(
            'parser.add_argument("--bridge-dll")\nNativeBridgeLaunchConfig\n',
            encoding="utf-8",
        )
        self.contract.write_text(
            json.dumps(
                {
                    "frozen_previous_four_guard_bridge_dll_sha256": "0" * 64,
                    "query_contract": QUERY,
                    "readiness_boundary": READINESS,
                }
            ),
            encoding="utf-8",
        )
        self.manifest.write_text(
            json.dumps({"query_contract": QUERY, "readiness_boundary": READINESS}),
            encoding="utf-8",
        )
        (
            self.native
            / "research/fixtures/startup_widget_null_flag_call_guard_v1_source_contract.json"
        ).write_text(
            json.dumps(
                {
                    "guard_semantics": {
                        "global_callee_patch": False,
                        "default_enabled": False,
                        "continue_rva": "0xAF4EED",
                    }
                }
            ),
            encoding="utf-8",
        )
        self._write_sources(widget_default="OFF")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_sources(self, *, widget_default: str) -> None:
        (self.native / "CMakeLists.txt").write_text(
            f'''option(
  XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1
  "Install the existing exact-build startup containment chain"
  OFF
)
option(
  XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1
  "Skip only the proven null-RDI startup widget flag call on the exact build"
  {widget_default}
)
if(XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=1
  )
endif()
if(XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=1
    XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1=1
  )
endif()
''',
            encoding="utf-8",
        )
        (self.native / "src/bridge.cpp").write_text(
            '''#if defined(XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1)
constexpr bool kStartupFailureContainmentEnabledV1 = true;
#else
constexpr bool kStartupFailureContainmentEnabledV1 = false;
#endif
#if defined(XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1)
constexpr bool kStartupWidgetNullFlagCallGuardEnabledV1 = true;
#else
constexpr bool kStartupWidgetNullFlagCallGuardEnabledV1 = false;
#endif
constexpr bool kStartupParticle2StageRecorderEnabledV1 = false;
static_assert(!(kStartupFailureContainmentEnabledV1 &&
                kStartupParticle2StageRecorderEnabledV1));
static_assert(!kStartupWidgetNullFlagCallGuardEnabledV1 ||
              kStartupFailureContainmentEnabledV1);
InstallStartupParticle2NullGuardV1();
InstallStartupParticle2ConsumerGuardV1();
InstallStartupDx11RenderContextDrawGuardV1();
InstallStartupLocalizeCurrentRootGuardV1();
InstallStartupWidgetNullFlagCallGuardV1();
''',
            encoding="utf-8",
        )
        (self.build / "CMakeCache.txt").write_text(
            "XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1:BOOL=ON\n"
            "XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1:BOOL=ON\n"
            "XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1:BOOL=OFF\n",
            encoding="utf-8",
        )

    def _verify(self) -> dict[str, object]:
        return VERIFY.verify(
            contract_path=self.contract,
            source_root=self.source,
            build_dir=self.build,
            base_manifest_path=self.manifest,
            bridge_dll=self.dll,
            bridge_injector=self.injector,
            runner_path=self.runner,
            attempt_dir=self.attempt,
            inventory_provider=lambda: [],
        )

    def test_ready_candidate_is_no_launch_and_five_guard_bound(self) -> None:
        result = self._verify()
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "READY_TO_FREEZE")
        self.assertFalse(result["no_launch_boundary"]["ck3_started"])
        self.assertEqual(
            result["configuration"]["guard_install_order"][-1],
            "InstallStartupWidgetNullFlagCallGuardV1",
        )

    def test_widget_option_default_on_is_blocked(self) -> None:
        self._write_sources(widget_default="ON")
        result = self._verify()
        self.assertFalse(result["ok"])
        self.assertFalse(result["checks"]["widget_guard_option_default_off"])


if __name__ == "__main__":
    unittest.main()

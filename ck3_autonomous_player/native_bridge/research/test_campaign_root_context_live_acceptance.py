from __future__ import annotations

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import run_campaign_root_context_live_acceptance as acceptance


class CampaignRootContextLiveAcceptanceTest(unittest.TestCase):
    def _run_until_readiness(
        self,
        *,
        prepared_xar_enabled: str | None,
        succession_lifecycle_binding: dict[str, object] | None = None,
        binding_capable: bool = True,
    ) -> tuple[mock.Mock, object, dict[str, object]]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            game_exe = root / "game" / "binaries" / "ck3.exe"
            dll = root / "bridge.dll"
            injector = root / "injector.exe"
            for path in (game_exe, dll, injector):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"fixture")
            spec = SimpleNamespace(
                game_exe=game_exe,
                state_dir=root / "state",
                profile_dir=root / "profile",
            )
            config = SimpleNamespace(
                pipe_name=r"\\.\pipe\campaign-root-test",
                dll_path=dll,
                injector_path=injector,
            )
            driver = (
                mock.Mock()
                if binding_capable
                else SimpleNamespace(close=mock.Mock())
            )
            native_session = mock.Mock(return_value={})
            kwargs = {
                "stage": "unit",
                "spec": spec,
                "config": config,
                "cold_start_checkpoint": True,
                "save_checkpoint": False,
                "timeout": 1.0,
                "readiness_timeout": 1.0,
            }
            if prepared_xar_enabled is not None:
                kwargs["prepared_xar_enabled"] = prepared_xar_enabled
            if succession_lifecycle_binding is not None:
                kwargs["succession_lifecycle_binding"] = (
                    succession_lifecycle_binding
                )
            with (
                mock.patch.object(
                    acceptance, "native_session", native_session
                ),
                mock.patch.object(
                    acceptance,
                    "NativeHeadlessGameplayDriver",
                    return_value=driver,
                ),
                mock.patch.object(acceptance, "GameplayBridgeService"),
                mock.patch.object(
                    acceptance,
                    "_wait_for_readiness",
                    side_effect=RuntimeError("bounded unit stop"),
                ),
                mock.patch.object(
                    acceptance, "_cleanup_report", return_value={"ok": True}
                ),
                mock.patch.object(
                    acceptance, "_compact_session_report", return_value={}
                ),
                mock.patch.object(
                    acceptance, "_sha256_file", return_value="0" * 64
                ),
            ):
                report = acceptance._run_live_stage(**kwargs)
            return native_session, driver, report

    def test_live_stage_binds_exact_ordinary_profile(self) -> None:
        binding = {
            "schema": "xar.ck3.succession-lifecycle-binding/v1",
            "lifecycle": "ordinary_campaign_succession",
            "xar_enabled": "xar_off",
            "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
            "source": "prepared-environment-manifest",
            "environment_sha256": "e" * 64,
        }
        native_session, driver, _report = self._run_until_readiness(
            prepared_xar_enabled="xar_off",
            succession_lifecycle_binding=binding,
        )
        driver.bind_succession_lifecycle_v1.assert_called_once_with(binding)
        self.assertEqual(
            native_session.call_args.kwargs["prepared_xar_enabled"],
            "xar_off",
        )

    def test_live_stage_keeps_legacy_default(self) -> None:
        native_session, _driver, report = self._run_until_readiness(
            prepared_xar_enabled=None,
            binding_capable=False,
        )
        self.assertEqual(
            native_session.call_args.kwargs["prepared_xar_enabled"],
            "xar_on",
        )
        self.assertNotIn("binding-capable driver", str(report["error"]))

    def test_nonlegacy_binding_requires_binding_capable_driver(self) -> None:
        binding = {
            "schema": "xar.ck3.succession-lifecycle-binding/v1",
            "lifecycle": "ordinary_campaign_succession",
            "xar_enabled": "xar_off",
            "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
            "source": "prepared-environment-manifest",
            "environment_sha256": "e" * 64,
        }
        native_session, _driver, report = self._run_until_readiness(
            prepared_xar_enabled="xar_off",
            succession_lifecycle_binding=binding,
            binding_capable=False,
        )
        native_session.assert_not_called()
        self.assertFalse(report["ok"])
        self.assertIn("binding-capable driver", str(report["error"]))


if __name__ == "__main__":
    unittest.main()

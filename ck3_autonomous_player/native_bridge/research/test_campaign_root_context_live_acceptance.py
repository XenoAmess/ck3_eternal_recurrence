from __future__ import annotations

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import run_campaign_root_context_live_acceptance as acceptance


class CampaignRootContextLiveAcceptanceTest(unittest.TestCase):
    def _run_until_readiness(
        self, *, prepared_xar_enabled: str | None
    ) -> mock.Mock:
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
            driver = mock.Mock()
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
                acceptance._run_live_stage(**kwargs)
            return native_session

    def test_live_stage_forwards_ordinary_prepared_rule(self) -> None:
        native_session = self._run_until_readiness(
            prepared_xar_enabled="xar_off"
        )
        self.assertEqual(
            native_session.call_args.kwargs["prepared_xar_enabled"],
            "xar_off",
        )

    def test_live_stage_keeps_legacy_default(self) -> None:
        native_session = self._run_until_readiness(
            prepared_xar_enabled=None
        )
        self.assertEqual(
            native_session.call_args.kwargs["prepared_xar_enabled"],
            "xar_on",
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import run_campaign_root_context_live_acceptance as acceptance


class CampaignRootContextLiveAcceptanceTest(unittest.TestCase):
    @staticmethod
    def _manifest(xar_enabled: str, digest: str = "e" * 64) -> dict[str, object]:
        return {
            "game": {"executable_sha256": "c" * 64},
            "mod": {"production_tree_sha256": "d" * 64},
            "dlc": {"installed_descriptors_sha256": "f" * 64},
            "load_profile": {
                "enabled_mods": ["mod/xar.mod"],
                "disabled_dlcs": [],
            },
            "rules": {
                "profile": [{"rule": "xar_enabled", "setting": xar_enabled}]
            },
            "environment_sha256": digest,
        }

    def test_ordinary_source_binding_requires_matching_frozen_xar_off(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory)
            (profile / acceptance.PROFILE_MANIFEST_NAME).write_text(
                json.dumps(self._manifest("xar_off")), encoding="utf-8"
            )
            binding = acceptance._source_lifecycle_binding(
                profile,
                ordinary_campaign_no_pact=True,
                expected_environment_sha256="E" * 64,
            )
            self.assertEqual(binding["lifecycle"], "ordinary_campaign_succession")
            self.assertEqual(binding["xar_enabled"], "xar_off")
            self.assertEqual(binding["environment_sha256"], "e" * 64)
            with self.assertRaisesRegex(
                acceptance.AgentError, "environment SHA differs"
            ):
                acceptance._source_lifecycle_binding(
                    profile,
                    ordinary_campaign_no_pact=True,
                    expected_environment_sha256="f" * 64,
                )
            with self.assertRaisesRegex(
                acceptance.AgentError, "requires --expected-source-environment"
            ):
                acceptance._source_lifecycle_binding(
                    profile,
                    ordinary_campaign_no_pact=True,
                    expected_environment_sha256=None,
                )
            (profile / acceptance.PROFILE_MANIFEST_NAME).write_text(
                json.dumps(self._manifest("xar_on")), encoding="utf-8"
            )
            with self.assertRaisesRegex(
                acceptance.AgentError, "requires frozen xar_off"
            ):
                acceptance._source_lifecycle_binding(
                    profile,
                    ordinary_campaign_no_pact=True,
                    expected_environment_sha256="e" * 64,
                )

    def test_legacy_source_default_rejects_accidental_ordinary_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory)
            self.assertIsNone(
                acceptance._source_lifecycle_binding(
                    profile,
                    ordinary_campaign_no_pact=False,
                    expected_environment_sha256=None,
                )
            )
            with self.assertRaisesRegex(
                acceptance.AgentError, "requires --ordinary-campaign-no-pact"
            ):
                acceptance._source_lifecycle_binding(
                    profile,
                    ordinary_campaign_no_pact=False,
                    expected_environment_sha256="e" * 64,
                )

    def test_ordinary_clone_prepares_and_verifies_xar_off_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "source"
            profile.mkdir()
            save = profile / "source.ck3"
            save.write_bytes(b"ordinary fixture")
            target = root / "stage-a"
            spec = SimpleNamespace(state_dir=target, profile_dir=target / "profile")
            manifest = self._manifest("xar_off", "a" * 64)
            with (
                mock.patch.object(acceptance, "_copy_source_profile"),
                mock.patch.object(acceptance, "make_spec", return_value=spec),
                mock.patch.object(
                    acceptance, "prepare_profile", return_value=manifest
                ) as prepare,
                mock.patch.object(
                    acceptance,
                    "verify_profile",
                    return_value={"environment_sha256": "a" * 64},
                ) as verify,
            ):
                _spec, clone = acceptance._prepare_stage_clone(
                    source_profile=profile,
                    target_state_dir=target,
                    game_dir=root / "game",
                    source_save=save,
                    stage="stage-a",
                    ordinary_campaign_no_pact=True,
                )
            prepare.assert_called_once_with(spec, xar_enabled="xar_off")
            verify.assert_called_once_with(spec, xar_enabled="xar_off")
            self.assertTrue(clone["ok"])
            self.assertEqual(
                clone["succession_lifecycle_binding"]["environment_sha256"],
                "a" * 64,
            )
            self.assertEqual(
                clone["ordinary_profile_inputs"]["production_tree_sha256"],
                "d" * 64,
            )

    def test_runner_keeps_checkpoint_origin_binding_across_cold_stage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "source"
            profile.mkdir()
            (profile / acceptance.PROFILE_MANIFEST_NAME).write_text(
                json.dumps(self._manifest("xar_off")), encoding="utf-8"
            )
            save = profile / "xar_checkpoint.ck3"
            save.write_bytes(b"ordinary fixture")
            dll = root / "bridge.dll"
            injector = root / "injector.exe"
            dll.write_bytes(b"fixture")
            injector.write_bytes(b"fixture")
            args = acceptance._parser().parse_args(
                [
                    "--source-profile", str(profile),
                    "--source-save", str(save),
                    "--expected-source-save-sha256", acceptance._sha256_file(save),
                    "--ordinary-campaign-no-pact",
                    "--expected-source-environment-sha256", "e" * 64,
                    "--state-dir", str(root / "disposable"),
                    "--game-dir", str(root / "game"),
                    "--bridge-pipe", r"\\.\pipe\campaign-root-test",
                    "--bridge-dll", str(dll),
                    "--bridge-injector", str(injector),
                    "--output", str(root / "artifact.json"),
                ]
            )
            first = acceptance.bind_succession_lifecycle_from_environment_v1(
                self._manifest("xar_off", "a" * 64),
                lifecycle=acceptance.ORDINARY_CAMPAIGN_SUCCESSION,
                ordinary_campaign_no_pact=True,
            )
            second = acceptance.bind_succession_lifecycle_from_environment_v1(
                self._manifest("xar_off", "b" * 64),
                lifecycle=acceptance.ORDINARY_CAMPAIGN_SUCCESSION,
                ordinary_campaign_no_pact=True,
            )
            inputs = {
                "game_exe_sha256": "c" * 64,
                "production_tree_sha256": "d" * 64,
                "installed_dlc_descriptors_sha256": "f" * 64,
                "rules_profile": self._manifest("xar_off")["rules"]["profile"],
                "enabled_mods": ["mod/xar.mod"],
                "disabled_dlcs": [],
            }
            source_sha256 = acceptance._sha256_file(save)
            clones = [
                (
                    SimpleNamespace(),
                    {
                        "succession_lifecycle_binding": first,
                        "ordinary_profile_inputs": inputs,
                        "source_save_sha256": source_sha256,
                    },
                ),
                (
                    SimpleNamespace(),
                    {
                        "succession_lifecycle_binding": second,
                        "ordinary_profile_inputs": inputs,
                        "source_save_sha256": source_sha256,
                    },
                ),
            ]
            with (
                mock.patch.object(acceptance, "_prepare_disposable_root"),
                mock.patch.object(
                    acceptance, "_prepare_stage_clone", side_effect=clones
                ) as prepare,
                mock.patch.object(
                    acceptance,
                    "_run_live_stage",
                    side_effect=[{"ok": True}, {"ok": True}],
                ) as live,
                mock.patch.object(
                    acceptance, "_transfer_checkpoint_bundle",
                    return_value={"ok": True},
                ),
                mock.patch.object(
                    acceptance, "_cross_stage_proof", return_value={"ok": True}
                ),
            ):
                payload, status = acceptance._run(args)
            self.assertEqual(status, 0)
            self.assertTrue(payload["ok"])
            self.assertEqual(
                payload["source_lifecycle_binding"]["environment_sha256"],
                "e" * 64,
            )
            self.assertEqual(payload["policy"]["prepared_xar_enabled"], "xar_off")
            self.assertTrue(payload["policy"]["ordinary_campaign_no_pact"])
            self.assertEqual(prepare.call_count, 2)
            self.assertTrue(
                all(
                    call.kwargs["ordinary_campaign_no_pact"] is True
                    for call in prepare.call_args_list
                )
            )
            self.assertEqual(
                [call.kwargs["succession_lifecycle_binding"] for call in live.call_args_list],
                [first, first],
            )
            self.assertEqual(payload["cold_restore_lifecycle_binding"], first)
            self.assertTrue(
                all(
                    call.kwargs["prepared_xar_enabled"] == "xar_off"
                    for call in live.call_args_list
                )
            )

    def test_ordinary_cold_restore_rejects_semantic_drift(self) -> None:
        first_binding = acceptance.bind_succession_lifecycle_from_environment_v1(
            self._manifest("xar_off", "a" * 64),
            lifecycle=acceptance.ORDINARY_CAMPAIGN_SUCCESSION,
            ordinary_campaign_no_pact=True,
        )
        second_binding = acceptance.bind_succession_lifecycle_from_environment_v1(
            self._manifest("xar_off", "b" * 64),
            lifecycle=acceptance.ORDINARY_CAMPAIGN_SUCCESSION,
            ordinary_campaign_no_pact=True,
        )
        first = {
            "succession_lifecycle_binding": first_binding,
            "ordinary_profile_inputs": {"production_tree_sha256": "c" * 64},
            "source_save_sha256": "d" * 64,
        }
        second = {
            "succession_lifecycle_binding": second_binding,
            "ordinary_profile_inputs": {"production_tree_sha256": "c" * 64},
            "source_save_sha256": "d" * 64,
        }
        self.assertEqual(
            acceptance._ordinary_cold_restore_binding(first, second),
            first_binding,
        )
        with self.assertRaisesRegex(acceptance.AgentError, "profile inputs differ"):
            acceptance._ordinary_cold_restore_binding(
                first,
                {
                    **second,
                    "ordinary_profile_inputs": {
                        "production_tree_sha256": "e" * 64
                    },
                },
            )
        with self.assertRaisesRegex(acceptance.AgentError, "source save differs"):
            acceptance._ordinary_cold_restore_binding(
                first, {**second, "source_save_sha256": "e" * 64}
            )
        with self.assertRaisesRegex(acceptance.AgentError, "semantics differ"):
            acceptance._ordinary_cold_restore_binding(
                first,
                {
                    **second,
                    "succession_lifecycle_binding": {
                        **second_binding,
                        "xar_enabled": "xar_on",
                    },
                },
            )

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

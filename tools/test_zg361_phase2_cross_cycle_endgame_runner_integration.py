#!/usr/bin/env python3

from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from types import SimpleNamespace
from unittest import mock


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


def _install_optional_desktop_import_stubs() -> None:
    attributes = {
        "pyautogui": (
            "FAILSAFE",
            "press",
            "hotkey",
            "moveTo",
            "click",
            "mouseDown",
            "mouseUp",
            "size",
        ),
        "numpy": (),
        "cv2": (),
        "win32api": ("GetKeyboardLayoutList",),
        "win32con": (),
        "win32gui": ("GetForegroundWindow", "GetWindowText"),
        "win32process": ("GetWindowThreadProcessId",),
    }
    for name, names in attributes.items():
        if importlib.util.find_spec(name) is None:
            module = types.ModuleType(name)
            for attribute in names:
                setattr(module, attribute, None)
            sys.modules[name] = module


_install_optional_desktop_import_stubs()

import run_zhongguo_acceptance as runner  # noqa: E402
from zhongguo_phase2_promo_producer import (  # noqa: E402
    Phase2PromoCaptureContext,
    canonical_phase2_capture_contract,
)


class CrossCycleEndgameRunnerIntegrationTests(unittest.TestCase):
    def test_formal_registry_assigns_endgame_to_exact_cell_driver(self) -> None:
        context = Phase2PromoCaptureContext(
            stream=object(),
            artifacts=Path("artifacts"),
            recorder=object(),
            title_navigation_service=object(),
            tracked_ck3_pid=1,
            native_bridge=object(),
            preflight_bridge_identity={},
            contract=canonical_phase2_capture_contract(),
        )
        sequenced = runner._make_default_phase2_promo_span_driver(context)
        owners = sequenced.delegate._owners
        owner = owners[runner.ENDGAME_HANDLER]
        self.assertIsInstance(
            owner, runner._Phase2CrossCycleEndgameSpanDriver
        )
        self.assertNotIsInstance(owner, runner.Phase2VisualHandlerAdapter)
        self.assertEqual(
            set(sequenced.available_handlers()),
            {item.handler for item in runner.PHASE2_CAPTURE_SCENARIOS},
        )

    def test_typed_fixture_enable_disable_is_bounded_to_isolated_userdir(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            userdir = root / "userdir"
            artifacts = root / "artifacts"
            (userdir / "mod").mkdir(parents=True)
            artifacts.mkdir()
            enabled = ["mod/zg361_acceptance.mod"]
            (userdir / "dlc_load.json").write_text(
                json.dumps({"enabled_mods": enabled, "disabled_dlcs": []}),
                encoding="utf-8",
            )
            install = runner.install_phase2_endgame_rebind_fixture(
                userdir, {"enabled_mods": enabled}, artifacts
            )
            self.assertEqual(install["result"], "GREEN")
            self.assertEqual(
                install["transition_fixture_id"],
                runner.PHASE2_ENDGAME_REBIND_FIXTURE_ID,
            )
            self.assertFalse(install["business_state_fixture_used"])
            target = Path(str(install["target"]))
            outer = Path(str(install["outer_descriptor"]))
            self.assertTrue(target.is_dir())
            self.assertTrue(outer.is_file())
            self.assertTrue(target.is_relative_to(userdir.resolve()))
            self.assertTrue(outer.is_relative_to(userdir.resolve()))

            disabled = runner.disable_phase2_endgame_rebind_fixture(
                userdir, install, artifacts
            )
            self.assertEqual(disabled["result"], "GREEN")
            self.assertFalse(disabled["fixture_enabled_for_next_restart"])
            self.assertTrue(disabled["fixture_bytes_left_dormant"])
            load = json.loads(
                (userdir / "dlc_load.json").read_text(encoding="utf-8-sig")
            )
            self.assertEqual(load["enabled_mods"], enabled)

    def test_formal_handler_consumes_registered_source_and_provider_cell(self) -> None:
        source_restore = {
            "result": "GREEN",
            "handler": runner.ENDGAME_HANDLER,
            "checkpoint": {"save_lineage_id": "seed-lineage"},
        }

        class SourceChoreography:
            def take_registered_source_restore(self, handler):
                self.handler = handler
                return source_restore

        class Service:
            def __init__(self):
                self.snapshots = iter(
                    (
                        {
                            "snapshot_id": "source",
                            "revision": 1,
                            "native_revision": 11,
                            "date_raw": 100,
                            "paused": True,
                            "map_ready": True,
                            "played_character": {"character_id": 10},
                            "active_event": {"instance_id": 1, "option_count": 3},
                            "diagnostics": {
                                "bridge_pid": 5001,
                                "connection_generation": 7,
                            },
                        },
                        {
                            "snapshot_id": "result",
                            "revision": 9,
                            "native_revision": 19,
                            "date_raw": 200,
                            "paused": True,
                            "map_ready": True,
                            "played_character": {"character_id": 10},
                            "active_event": {"instance_id": 9, "option_count": 3},
                            "diagnostics": {
                                "bridge_pid": 5003,
                                "connection_generation": 9,
                            },
                        },
                    )
                )

            def snapshot(self):
                return next(self.snapshots)

        result_binding = SimpleNamespace(
            owner_character_id=10,
            subject_character_id=20,
            result_date_raw=200,
            result_checkpoint_sha256="A" * 64,
            save_lineage_id="seed-lineage",
        )

        def seam(_service, **kwargs):
            self.assertIs(kwargs["source_checkpoint_restore"], source_restore)
            activation = kwargs["activate_result_session"](result_binding)
            self.assertIsInstance(activation, runner.ActivatedResultSession)
            self.assertEqual(
                activation.restore_receipt["checkpoint_sha256"], "A" * 64
            )
            return {
                "result": "GREEN",
                "provider_observed_postcondition": True,
                "action_ack_is_business_postcondition": False,
            }

        source = SourceChoreography()
        service = Service()
        driver = runner._Phase2CrossCycleEndgameSpanDriver(
            service, source_choreography=source
        )
        scenario = next(
            item
            for item in runner.PHASE2_CAPTURE_SCENARIOS
            if item.handler == runner.ENDGAME_HANDLER
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            context = Phase2PromoCaptureContext(
                stream=object(),
                artifacts=root,
                recorder=object(),
                title_navigation_service=service,
                tracked_ck3_pid=5001,
                native_bridge=object(),
                preflight_bridge_identity={},
                contract=canonical_phase2_capture_contract(),
                seed_contract={
                    "runtime": {
                        "game_version": runner.ENDGAME_EXACT_GAME_VERSION,
                        "executable_sha256": runner.ENDGAME_EXACT_EXE_SHA256,
                    }
                },
                isolated_userdir=root / "userdir",
                runtime_bootstrap={"enabled_mods": ["mod/product.mod"]},
            )
            with (
                mock.patch.object(
                    runner,
                    "run_exact_build_cross_cycle_endgame_seam",
                    side_effect=seam,
                ),
                mock.patch.object(
                    runner,
                    "install_phase2_endgame_rebind_fixture",
                    return_value={
                        "result": "GREEN",
                        "enabled_mods_before": ["mod/product.mod"],
                        "enabled_mods_after": ["mod/product.mod", "mod/fixture.mod"],
                    },
                ),
                mock.patch.object(
                    runner,
                    "disable_phase2_endgame_rebind_fixture",
                    return_value={"result": "GREEN"},
                ),
                mock.patch.object(
                    runner,
                    "_restore_phase2_endgame_result_checkpoint",
                    return_value={"result": "GREEN"},
                ) as restores,
                mock.patch.object(
                    runner,
                    "_phase2_promo_visible_scenario_surface",
                    return_value={"event_definition_key": "zg361we.361"},
                ),
            ):
                evidence = driver.run_span(scenario, context, {})

        self.assertEqual(source.handler, runner.ENDGAME_HANDLER)
        self.assertEqual(restores.call_count, 2)
        self.assertEqual(evidence["result"], "GREEN")
        self.assertTrue(evidence["postcondition_green"])
        self.assertEqual(
            evidence["source_checkpoint_origin"],
            "registered_real_ck3_read_only",
        )
        self.assertEqual(
            evidence["managed_session_transition"]["restore_count"], 2
        )


if __name__ == "__main__":
    unittest.main()

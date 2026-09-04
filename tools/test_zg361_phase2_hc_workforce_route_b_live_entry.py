#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

import run_zhongguo_acceptance as runner
from zg361_phase2_hc_workforce_route_b_checkpoint import RouteBCaseIdentity
from zg361_phase2_hc_workforce_route_b_checkpoint_registry import (
    RegisteredRouteBCheckpoint,
)


OWNER = 32904
SUBJECT = 29037
DATE = 53146920
SOURCE_COMMIT = "c" * 40
CHECKPOINT_SHA = "a" * 64


class RestoreService:
    def __init__(self) -> None:
        self.restore_calls: list[dict[str, object]] = []
        self.capability_calls = 0

    def capabilities(self) -> dict[str, object]:
        self.capability_calls += 1
        return {"bridge_capabilities": [runner.CAREER_CAPABILITY]}

    def hc_workforce_route_b_checkpoint_restore_available_v1(self) -> bool:
        return True

    def restore_hc_workforce_route_b_checkpoint_v1(
        self, **kwargs: object
    ) -> dict[str, object]:
        self.restore_calls.append(dict(kwargs))
        return {
            "result": "GREEN",
            "provider_observed": True,
            "fixture_used": True,
            "checkpoint_sha256": CHECKPOINT_SHA.upper(),
        }


class Provider:
    def __init__(self, entry: RegisteredRouteBCheckpoint) -> None:
        self.entry = entry
        self.projections: list[object] = []

    def preflight(
        self, *, current_projection_binding: object
    ) -> dict[str, object]:
        self.projections.append(current_projection_binding)
        return {"result": "GREEN"}

    def checkpoint(
        self, *, current_projection_binding: object
    ) -> RegisteredRouteBCheckpoint:
        self.projections.append(current_projection_binding)
        return self.entry


class RouteBLiveEntryTests(unittest.TestCase):
    def test_focused_capability_profile_excludes_unrelated_domains_and_b6(self) -> None:
        required_bridge = {
            runner.PHASE2_REQUIRED_BRIDGE_CAPABILITIES[label]
            for label in (
                runner.PHASE2_HC_WORKFORCE_ROUTE_B_REQUIRED_BRIDGE_CAPABILITY_LABELS
            )
        }
        required_steps = {
            runner.PHASE2_REQUIRED_ACTION_STEPS[label]
            for label in (
                runner.PHASE2_HC_WORKFORCE_ROUTE_B_REQUIRED_ACTION_STEP_LABELS
            )
        }

        class Service:
            def capabilities(self) -> dict[str, object]:
                result = {
                    "mode": runner.NATIVE_BRIDGE_MODE,
                    "backend_id": runner.NATIVE_BRIDGE_MODE,
                    "visual_fallback": False,
                    "snapshot": True,
                    "wait_for_change": True,
                    "bridge_capabilities": sorted(required_bridge),
                    "action_steps": sorted(required_steps),
                    "diagnostics": {
                        "connected": True,
                        "bridge_pid": 7711,
                        "connection_generation": 4,
                    },
                    "checkpoint_materialization": {"configured": True},
                    "native_session_control": {"configured": True},
                }
                for label in (
                    runner.PHASE2_HC_WORKFORCE_ROUTE_B_REQUIRED_QUERY_FLAG_LABELS
                ):
                    result[runner.PHASE2_REQUIRED_QUERY_FLAGS[label]] = True
                return result

        with tempfile.TemporaryDirectory() as temporary:
            report = runner.phase2_runtime_capability_preflight(
                Service(),
                Path(temporary),
                tracked_ck3_pid=7711,
                managed_restore_supervisor=True,
                focused_hc_workforce_route_b=True,
            )
        self.assertEqual("GREEN", report["result"])
        self.assertTrue(report["focused_hc_workforce_route_b"])
        self.assertNotIn(
            "manager_subordinate_selector",
            report["required_bridge_capabilities"],
        )
        self.assertNotIn(
            runner.CAREER_CAPABILITY,
            report["required_bridge_capabilities"].values(),
        )

    def run_scenario(
        self, *, enable_career: bool
    ) -> tuple[dict[str, object], list[object]]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkpoint = root / "route-b.ck3"
            checkpoint.write_bytes(b"route-b")
            identity = RouteBCaseIdentity(OWNER, SUBJECT, 16, 16056)
            capture = {
                "result": "GREEN",
                "checkpoint": {"sha256": CHECKPOINT_SHA},
            }
            projection = {"source_git_commit": SOURCE_COMMIT}
            entry = RegisteredRouteBCheckpoint(
                seed_lineage_id="seed-lineage",
                checkpoint_path=checkpoint,
                checkpoint_bytes=checkpoint.stat().st_size,
                checkpoint_sha256=CHECKPOINT_SHA,
                date_raw=DATE,
                owner_character_id=OWNER,
                subject_character_id=SUBJECT,
                case_identity=identity,
                projection_binding=projection,
                checkpoint_capture=capture,
                sealed_postconditions={"result": "GREEN"},
            )
            provider = Provider(entry)
            service = RestoreService()
            hooks: list[object] = []

            def run_postconditions(
                _service: object, **kwargs: object
            ) -> dict[str, object]:
                hook = kwargs["career_hc_hook"]
                hooks.append(hook)
                if enable_career:
                    career = {
                        "status": "observed",
                        "provider_observed": True,
                    }
                else:
                    career = hook(
                        object(),
                        expected_revision=30,
                        expected_date_raw=DATE,
                        identity=identity,
                    )
                return {
                    "result": "GREEN",
                    "action_ack_is_business_postcondition": False,
                    "career_hc_provider": career,
                }

            with mock.patch.object(
                runner,
                "install_phase2_workforce_action_fixture",
                return_value={"result": "GREEN"},
            ), mock.patch.object(
                runner,
                "bind_current_cumulative_projection",
                return_value=projection,
            ), mock.patch.object(
                runner,
                "RouteBCheckpointRegistryProvider",
                return_value=provider,
            ), mock.patch.object(
                runner,
                "wait_for_phase2_exact_event",
                return_value={"result": "GREEN"},
            ), mock.patch.object(
                runner,
                "run_route_b_and_collect_postconditions",
                side_effect=run_postconditions,
            ), mock.patch.object(
                runner,
                "restore_route_b_pre_action_checkpoint",
                return_value={
                    "result": "GREEN",
                    "checkpoint_sha256": CHECKPOINT_SHA,
                },
            ), mock.patch.object(
                runner,
                "_phase2_seed_lineage_id",
                return_value="seed-lineage",
            ):
                result = runner.run_phase2_hc_workforce_route_b_registry_scenario(
                    service,
                    root / "artifacts",
                    userdir=root / "profile",
                    bootstrap={},
                    seed_contract={},
                    registry={},
                    source_git_commit=SOURCE_COMMIT,
                    enable_career_hc_provider=enable_career,
                )
            return result, hooks

    def test_career_provider_is_default_off_even_if_advertised(self) -> None:
        result, hooks = self.run_scenario(enable_career=False)
        self.assertEqual("GREEN", result["result"])
        self.assertTrue(result["career_hc_provider_default_off"])
        self.assertEqual(2, len(hooks))
        for postconditions in (
            result["first_postconditions"],
            result["replay_postconditions"],
        ):
            career = postconditions["career_hc_provider"]
            self.assertEqual("not_available", career["status"])
            self.assertEqual(
                "career_hc_live_gate_default_off", career["reason"]
            )
            self.assertFalse(career["provider_observed"])

    def test_explicit_career_gate_selects_typed_provider_hook(self) -> None:
        result, hooks = self.run_scenario(enable_career=True)
        self.assertEqual("GREEN", result["result"])
        self.assertFalse(result["career_hc_provider_default_off"])
        self.assertEqual(
            [runner.query_career_hc_if_available] * 2,
            hooks,
        )

    def test_main_requires_registry_before_resolving_bridge_or_launch(self) -> None:
        with mock.patch.object(
            runner, "resolve_native_bridge_config"
        ) as resolve_bridge:
            with self.assertRaises(runner.acceptance.RunnerError) as raised:
                runner.main(phase2_hc_workforce_route_b_live=True)
        self.assertIn("requires exactly one strict", str(raised.exception))
        resolve_bridge.assert_not_called()


if __name__ == "__main__":
    unittest.main()

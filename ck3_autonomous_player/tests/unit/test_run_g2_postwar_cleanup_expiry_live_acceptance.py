"""Focused checks for the private G2 cleanup/expiry short-path runner."""

from __future__ import annotations

from contextlib import redirect_stderr
import importlib.util
import io
from pathlib import Path
import asyncio
import sys
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_g2_postwar_cleanup_expiry_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_g2_postwar_cleanup_expiry_live_acceptance", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import guard
    raise RuntimeError(f"cannot load runner: {SCRIPT}")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def _binding(*, war_present: bool) -> dict[str, object]:
    return {
        "snapshot_id": "native:4",
        "revision": 5,
        "native_revision": 4,
        "date_raw": 53_223_936,
        "paused": True,
        "episode_run_id": "episode",
        "connection_generation": 1,
        "ck3_pid": 1234,
        "character_id": 29_829,
        "active_wars": ([{"war_id": 50_331_699}] if war_present else []),
    }


class G2PostwarCleanupExpiryLiveAcceptanceTests(unittest.TestCase):
    def test_private_surrender_uses_advertised_capability_without_public_action(self) -> None:
        capabilities = {
            RUNNER.QUERY_WAR_TERMINATION_TERMS_CAPABILITY,
            RUNNER.QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_CAPABILITY,
            RUNNER.QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_CAPABILITY,
            RUNNER.SURRENDER_CAPABILITY,
        }
        pre_sequence = {
            "ok": True,
            "before_snapshot": {
                "is_error": False,
                "structured_content": {"snapshot_id": "native:3"},
            },
            "second_query": {
                "is_error": False,
                "structured_content": {"war_termination_terms": {}},
            },
            "capabilities": {
                "is_error": False,
                "structured_content": {
                    "bridge_capabilities": sorted(capabilities),
                    "action_steps": [],
                },
            },
            "public_revision": 4,
        }
        calls: list[tuple[str, int | None, str | None]] = []

        class Driver:
            def _execute_primitive_step(
                self,
                step: str,
                *,
                expected_revision: int | None = None,
                required_capability: str | None = None,
            ) -> dict[str, object]:
                calls.append((step, expected_revision, required_capability))
                return {
                    "step": step,
                    "accepted": True,
                    "status": "submitted",
                    "backend_id": "native-headless",
                }

        class Client:
            def __init__(self, _server: object) -> None:
                pass

            async def __aenter__(self) -> "Client":
                return self

            async def __aexit__(self, *_args: object) -> None:
                return None

        receipt = {
            "ticket_validation": {"ok": True},
            "boundaries": {
                "source_specific_attribution_ready": False,
                "public_readiness_promoted": False,
                "action_readiness_promoted": False,
                "decision_ready": False,
                "automatic_surrender_ready": False,
                "gen034_closed": False,
            },
        }

        async def run() -> dict[str, object]:
            with (
                mock.patch.object(
                    RUNNER.base,
                    "_run_mcp_sequence",
                    mock.AsyncMock(return_value=pre_sequence),
                ),
                mock.patch.object(
                    RUNNER.base, "create_server", return_value=object()
                ),
                mock.patch.object(
                    RUNNER.adapter,
                    "_normalize_pre",
                    return_value=({"revision": 4}, {}, {}),
                ),
                mock.patch.object(
                    RUNNER,
                    "_wait_for_stable_postwar",
                    mock.AsyncMock(return_value=({"snapshot_id": "native:5"}, [])),
                ),
                mock.patch.object(
                    RUNNER.adapter,
                    "collect_after_surrender",
                    mock.AsyncMock(return_value=receipt),
                ),
                mock.patch.dict(sys.modules, {"mcp": SimpleNamespace(Client=Client)}),
            ):
                return await RUNNER._run_private_sequence(
                    Driver(),
                    war_id=50_331_699,
                    expected_character_id=29_829,
                    expected_date_raw=53_223_936,
                    ticket={"opponent_character_id": 36_769},
                    postwar_timeout=1.0,
                )

        result = asyncio.run(run())
        self.assertTrue(result["ok"])
        self.assertEqual(
            calls,
            [
                (
                    "surrender-war-50331699",
                    4,
                    RUNNER.SURRENDER_CAPABILITY,
                )
            ],
        )

    def test_private_live_is_default_off_before_process_inventory(self) -> None:
        arguments = [
            "--attempt-dir", "future",
            "--source-checkpoint", "checkpoint",
            "--source-driver-state", "driver",
            "--expected-checkpoint-sha256", "0" * 64,
            "--expected-driver-state-sha256", "0" * 64,
            "--game-dir", "game",
            "--bridge-dll", "bridge.dll",
            "--bridge-injector", "injector.exe",
            "--war-id", "50331699",
            "--expected-character-id", "29829",
            "--expected-date-raw", "53223936",
            "--retention-manifest", "retention.json",
            "--expected-retention-manifest-sha256", "0" * 64,
            "--expected-retention-ticket-id", "ticket",
            "--expected-bridge-dll-sha256", "0" * 64,
            "--expected-bridge-injector-sha256", "0" * 64,
        ]
        with mock.patch.object(RUNNER, "_process_inventory") as inventory:
            with redirect_stderr(io.StringIO()):
                self.assertEqual(RUNNER.main(arguments), 2)
        inventory.assert_not_called()

    def test_war_absence_is_only_postwar_admission(self) -> None:
        pre = _binding(war_present=True)
        pre["snapshot_id"] = "native:3"
        pre["revision"] = 4
        pre["native_revision"] = 3
        post = _binding(war_present=False)
        self.assertTrue(
            RUNNER._same_postwar_candidate(pre, post, 50_331_699)
        )
        self.assertFalse(
            RUNNER._same_postwar_candidate(
                pre, _binding(war_present=True), 50_331_699
            )
        )
        self.assertNotIn("cleanup", post)
        self.assertNotIn("destroyed", post)

    def test_source_keeps_exact_reader_and_no_promotion_boundaries(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("adapter.collect_after_surrender", source)
        self.assertIn(
            "cleanup_destroyed_must_come_from_exact_store_reader", source
        )
        self.assertIn("war_id_absence_is_admission_only", source)
        for boundary in (
            "public_readiness_promoted",
            "action_readiness_promoted",
            "automatic_surrender_ready",
            "gen034_closed",
        ):
            self.assertIn(boundary, source)


if __name__ == "__main__":
    unittest.main()

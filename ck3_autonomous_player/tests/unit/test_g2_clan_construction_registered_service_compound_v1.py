"""Registered normal-service Clan construction, with explicit outer I/O seams.

Reuse the retained native-shaped construction/cash replies and normal CLI fixture.
The real CLI, registered MCP, Service, production transports and durable ledger run.
Native execution, process identity and the baseline chooser remain synthetic; this
does not qualify a government, seed, real checkpoint or any actual game outcome.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
from pathlib import Path
import sys
from typing import Literal
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).resolve().parent)]

from mcp import Client
from mcp.server import MCPServer

from test_construction_monthly_budget_v1 import cash_fixture
from test_g2_normal_construction_cli_service_compound_v1 import (
    NormalConstructionFixtureDriver,
)
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_cash_private_transport_v1 import CURRENT_STEP
from xar_autoplayer.construction_formal_consumer import (
    RECEIPT_STEP,
    SUBMIT_STEP,
    read_construction_ledger,
)

Government = Literal["feudal_government", "clan_government", "tribal_government"]
CashMode = Literal["available", "missing_net", "wrong_actor"]


def _record(value: object) -> dict[str, object]:
    """Narrow native-shaped/MCP dynamic fixture data at the test boundary."""
    if not isinstance(value, dict):
        raise AssertionError(f"Expected object, got {type(value).__name__}")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise AssertionError("Fixture object has a non-string key")
        result[key] = item
    return result


class _RegisteredClanDriver:
    """Only the outer reply source varies; all cash consumption is production."""

    def __init__(self, state_dir: Path, government: Government, cash_mode: CashMode) -> None:
        self._fixture: object = NormalConstructionFixtureDriver(state_dir)
        self.state_dir = state_dir
        self.snapshot = self.current_frame(3)
        self.requests: list[dict[str, object]] = []
        self.endpoint = self
        self.state = self
        self.command_timeout_seconds = 2.0
        self.allow_private_construction_formal_trial = False
        self.cash_mode: CashMode = cash_mode
        original = _record(self._fixture_call("take_snapshot"))
        history = original["native_command_history"]
        if not isinstance(history, list) or not history:
            raise AssertionError("Retained fixture has no root producer row")
        result = _record(_record(history[0])["result"])
        root = _record(result["campaign_root_context"])
        root["government"] = {
            "key": government,
            "flags": [{
                "feudal_government": "government_is_feudal",
                "clan_government": "government_is_clan",
                "tribal_government": "government_is_tribal",
            }[government]],
        }
        self.recorded: list[tuple[str, dict[str, object]]] = [("query-campaign-root-context-v1", {
            **result, "campaign_root_context": root,
        })]

    def __getattr__(self, name: str) -> object:
        result: object = getattr(self._fixture, name)
        return result

    def _fixture_call(self, name: str, *args: object, **options: object) -> object:
        # The retained fixture predates typing. Its dynamic interface is local
        # to this boundary; structured replies are validated by _record before
        # reaching the actual production parsers.
        method = getattr(self._fixture, name)
        if not callable(method):
            raise AssertionError(f"Fixture member is not callable: {name}")
        result: object = method(*args, **options)
        return result

    def _sync_fixture(self) -> None:
        for name in ("state_dir", "snapshot", "requests", "recorded"):
            setattr(self._fixture, name, getattr(self, name))

    def current_frame(self, revision: int) -> dict[str, object]:
        return _record(self._fixture_call("current_frame", revision))

    def take_snapshot(self) -> dict[str, object]:
        self._sync_fixture()
        return _record(self._fixture_call("take_snapshot"))

    def send(self, request: dict[str, object]) -> None:
        self.requests.append(request)

    def _record_command(self, step: str, *, ok: bool, result: dict[str, object]) -> None:
        self._sync_fixture()
        self._fixture_call("_record_command", step, ok=ok, result=result)

    def wait_for_change(self, after_revision: int, *, timeout_seconds: float) -> dict[str, object]:
        raise BridgeUnavailableError("Controlled fixture has no later native frame")

    def query_construction_cash_outcome_private_v1(
        self, *, expected_revision: int, reserve_gold_raw: int,
        existing_commitment_gold_raw: int, horizon_months: int,
    ) -> dict[str, object]:
        return _record(NativeHeadlessGameplayDriver.query_construction_cash_outcome_private_v1(
            self, expected_revision=expected_revision, reserve_gold_raw=reserve_gold_raw,
            existing_commitment_gold_raw=existing_commitment_gold_raw,
            horizon_months=horizon_months,
        ))

    def query_war_cash_current_resources_private_v1(
        self, *, expected_revision: int, payment_sampling: str | None = None,
        payment_window_contract: str | None = None,
    ) -> dict[str, object]:
        return _record(NativeHeadlessGameplayDriver.query_war_cash_current_resources_private_v1(
            self, expected_revision=expected_revision, payment_sampling=payment_sampling,
            payment_window_contract=payment_window_contract,
        ))

    def take_internal_semantic_snapshot(self) -> dict[str, object]:
        return _record(self.take_snapshot())

    def wait_for_command_result(
        self, request_id: str, timeout: float,
    ) -> dict[str, object] | None:
        request = self.requests[-1]
        if request["step"] != CURRENT_STEP:
            self._sync_fixture()
            result = self._fixture_call("wait_for_command_result", request_id, timeout)
            return None if result is None else _record(result)
        gold = _record(self.snapshot["played_character_gold"])["raw"]
        if type(gold) is not int:
            raise AssertionError("Fixture gold must be an exact integer")
        cash = _record(cash_fixture(
            gold=gold, gross=450_000, expenses=380_000,
            current=200_000, all_raised=500_000,
        ))
        cash.update(snapshot_revision=self.snapshot["native_revision"],
                    date_raw=self.snapshot["date_raw"])
        if self.cash_mode == "missing_net":
            cash.update(status="partial", player_monthly_net_income=None,
                        monthly_net_income_unavailable_reason="fixture_net_missing")
            readiness = _record(cash["readiness"])
            readiness["monthly_net_income_ready"] = False
            cash["readiness"] = readiness
        elif self.cash_mode == "wrong_actor":
            cash["played_character_id"] = 33441
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True,
            "result": {
                "step": CURRENT_STEP, "accepted": True, "status": "available",
                "private_build": True, "read_only": True, "advertised": False,
                "backend_id": "native-headless", "war_cash_current_resources": cash,
            },
        }


def _configured_server(
    directory: Path, government: Government, cash_mode: CashMode = "available",
    *, enabled: bool = True,
) -> tuple[MCPServer, _RegisteredClanDriver]:
    directory.mkdir(parents=True, exist_ok=False)
    driver = _RegisteredClanDriver(directory, government, cash_mode)
    captured: list[MCPServer] = []

    def load_fixture(driver_name: str, **options: object) -> _RegisteredClanDriver:
        if driver_name != "native-headless" or options.get("state_dir") != directory:
            raise AssertionError("CLI selected a different fixture source")
        return driver

    def capture_run(server: MCPServer, **options: object) -> None:
        if options != {"transport": "stdio"}:
            raise AssertionError("Unexpected MCP transport")
        if driver.allow_private_construction_formal_trial is not enabled:
            raise AssertionError("CLI did not consume construction opt-in")
        captured.append(server)

    argv = ["--driver", "native-headless", "--transport", "stdio",
            "--state-dir", str(directory)]
    if enabled:
        argv.append("--allow-private-construction-formal-trial")
    with patch.object(mcp_server, "load_driver", side_effect=load_fixture) as factory, \
            patch.object(MCPServer, "run", new=capture_run):
        assert mcp_server.main(argv) == 0
    assert factory.call_count == 1 and len(captured) == 1
    return captured[0], driver


def _actions(driver: _RegisteredClanDriver) -> int:
    return sum(row["step"] == transport.ACTION_NATIVE for row in driver.requests)


def test_registered_clan_and_feudal_submit_material_ledger_and_following(tmp_path: Path) -> None:
    """Close the registered path missing from the earlier Clan selector compound."""
    baseline = {"policy": "normal-baseline-fixture", "phase": "life_advance",
                "selected_step": "life-advance"}
    before = deepcopy(baseline)

    async def exercise() -> None:
        candidates: list[dict[str, object]] = []
        governments: tuple[Government, ...] = ("feudal_government", "clan_government")
        for government in governments:
            server, driver = _configured_server(tmp_path / government, government)
            async with Client(server) as client:
                observed = await client.call_tool("ck3_plan_turn", {})
                assert not observed.is_error, observed.content
                selected = _record(_record(observed.structured_content)["plan"])
                assert selected["selected_step"] == SUBMIT_STEP
                quote = _record(selected["construction_private_query"])
                candidate = _record(quote["candidate"])
                candidates.append(candidate)
                assert candidate["stock_gold_cost_raw"] == 15_000_000
                assert _record(quote["world"])["native_final_legality_evaluated"] is True
                if government == "clan_government":
                    budget = _record(quote["construction_monthly_budget"])
                    current = _record(_record(budget["scenarios"])["current"])
                    assert current["net_monthly_gold_raw"] == 70_000
                    assert current["cash_after_construction_and_commitments_raw"] == 35_000_000
                    assert budget["reserve_gold_raw"] == 20_000_000
                    assert current["scenario_floor_ready"] is True
                    assert "pre_cash_v2" in quote
                assert _actions(driver) == 0

                submitted = await client.call_tool("ck3_auto_turn", {})
                assert not submitted.is_error, submitted.content
                receipt = _record(submitted.structured_content)
                assert receipt["selected_step"] == SUBMIT_STEP
                assert _record(receipt["result"])["status"] == "submitted_verification_pending"
                pending = _record(read_construction_ledger(driver.state_dir)["pending"])
                assert pending["pre_native_revision"] == 3
                action_id = pending["action_request_id"]
                assert _actions(driver) == 1

                # No new native frame yet: another ordinary plan must keep
                # verification pending, without claiming material or resending.
                pending_plan = await client.call_tool("ck3_plan_turn", {})
                assert not pending_plan.is_error, pending_plan.content
                waiting = _record(_record(pending_plan.structured_content)["plan"])
                assert waiting["selected_step"] is None
                retained_pending = _record(read_construction_ledger(driver.state_dir)["pending"])
                assert retained_pending["action_request_id"] == action_id
                assert "construction_receipt_consumed" not in waiting
                assert _actions(driver) == 1

                # A separate later native-shaped reply supplies the independent
                # active construction tuple and wallet; ACK alone did not.
                driver.snapshot = driver.current_frame(4)
                applied = await client.call_tool("ck3_auto_turn", {})
                assert not applied.is_error, applied.content
                receipt = _record(applied.structured_content)
                assert receipt["selected_step"] == RECEIPT_STEP
                material = _record(receipt["result"])
                assert material["postcondition_verified"] is True
                assert material["post_player_gold_raw"] == 35_000_000
                assert material["action_request_id"] == action_id
                assert _record(material["candidate"]) == candidate
                assert read_construction_ledger(driver.state_dir)["pending"] is None

                # Create a new fixture consumer against the same actual small
                # JSON ledger. This checks persistence, not a real Game restore.
                recovered_server, recovered = _configured_server(
                    tmp_path / (government + "-reader"), government,
                )
                recovered.state_dir = driver.state_dir
                recovered.snapshot = recovered.current_frame(4)
                async with Client(recovered_server) as next_client:
                    following = await next_client.call_tool("ck3_plan_turn", {})
                    assert not following.is_error, following.content
                    planned = _record(_record(following.structured_content)["plan"])
                    assert planned["selected_step"] == "life-advance"
                    consumed = _record(planned["construction_receipt_consumed"])
                    assert consumed["action_request_id"] == action_id
                    assert _actions(recovered) == 0
                assert _actions(driver) == 1
        assert candidates[0] == candidates[1]

    with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline), \
            patch.object(GameplayBridgeService, "plan_nonwar_turn", side_effect=AssertionError("normal route required")), \
            patch.object(GameplayBridgeService, "auto_nonwar_turn", side_effect=AssertionError("normal executor required")), \
            patch.object(transport, "_identity", return_value=(881, "fixture-construction12004")), \
            patch("xar_autoplayer.bridge.service.construction_process_identity", return_value=(881, "fixture-construction12004")):
        asyncio.run(exercise())
    assert baseline == before


def test_registered_clan_missing_cash_and_unsupported_scenes_keep_ordinary_plan(tmp_path: Path) -> None:
    baseline = {"policy": "normal-baseline-fixture", "phase": "life_advance",
                "selected_step": "life-advance"}
    cases: tuple[tuple[str, Government, CashMode, bool, int], ...] = (
        ("clan-net-missing", "clan_government", "missing_net", True, 1),
        ("clan-cash-wrong-actor", "clan_government", "wrong_actor", True, 1),
        ("clan-default-off", "clan_government", "available", False, 0),
        ("tribal-preserved-outside-scene", "tribal_government", "available", True, 0),
    )

    async def exercise() -> None:
        for name, government, cash_mode, enabled, expected_queries in cases:
            server, driver = _configured_server(
                tmp_path / name, government, cash_mode, enabled=enabled,
            )
            async with Client(server) as client:
                observed = await client.call_tool("ck3_plan_turn", {})
                assert not observed.is_error, observed.content
                planned = _record(_record(observed.structured_content)["plan"])
                assert planned["selected_step"] == "life-advance"
                assert _actions(driver) == 0
                assert len(driver.requests) == expected_queries
                if enabled and government == "clan_government":
                    assert planned["phase"] == "construction_clan_observation_deferred"
                    assert "reason" in planned

    with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline), \
            patch.object(GameplayBridgeService, "plan_nonwar_turn", side_effect=AssertionError("normal route required")), \
            patch.object(transport, "_identity", return_value=(881, "fixture-construction12004")), \
            patch("xar_autoplayer.bridge.service.construction_process_identity", return_value=(881, "fixture-construction12004")):
        asyncio.run(exercise())

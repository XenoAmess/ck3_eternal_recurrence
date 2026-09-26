from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_entry_contract import (
    EXECUTABLE_SHA256,
    QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY,
)
from xar_autoplayer.strategy import choose_one_life_turn


STEP = "query-war-entry-assessments-v1-1-808"
OTHER_STEP = "query-war-entry-assessments-v1-1-42"


def _declaration(target: int) -> dict[str, object]:
    return {
        "declaration_id": f"{target}-17-0",
        "target_character_id": target,
        "casus_belli_index": 17,
        "casus_belli_key": "county_conquest_cb",
        "configuration_index": 0,
        "claimant_character_id": -1,
        "target_title_ids": [91],
        "source": "native",
    }


def _active_war(opponent: int) -> dict[str, object]:
    return {
        "war_id": 33_554_473,
        "player_side": "attacker",
        "primary_opponent_character_id": opponent,
        "player_is_primary_war_leader": True,
        "enemy_primary_default_raise_province_id": None,
        "targeted_title_ids": [91],
        "war_objective_province_ids": [],
        "objective_province_states": [],
        "player_relative_war_score": 0,
        "allied_armies": [],
        "enemy_armies": [],
    }


def _row(target: int, *, effective_target: int | None = None) -> dict[str, object]:
    return {
        "target_character_id": target,
        "effective_target_character_id": effective_target or target,
        "distance_raw": 2_500_000,
        "actor_power_base_raw": 55_223,
        "actor_network_contribution_raw": 44_777,
        "actor_power_total_raw": 100_000,
        "target_power_base_raw": 58_468,
        "target_network_contribution_raw": 21_532,
        "target_pre_adjustment_total_raw": 80_000,
        "target_adjustment_delta_raw": 5_000,
        "target_power_total_raw": 85_000,
        "actual_power_ratio_raw": 85_000,
        "target_ai_context_actor_entry_raw": 0,
        "actor_ai_context_target_entry_raw": 1,
        "native_flags_raw": 3,
    }


def _payload(
    targets: list[int] | None = None, *, snapshot_revision: int = 5
) -> dict[str, object]:
    selected = targets or [808]
    return {
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": snapshot_revision,
        "date_raw": 53_171_400,
        "actor_character_id": 29_829,
        "requested_target_character_ids": list(selected),
        "assessments": [_row(target) for target in selected],
        "readiness": {
            "actor_identity_ready": True,
            "targets_declarable_ready": True,
            "effective_targets_ready": True,
            "ai_context_ready": True,
            "native_output_ready": True,
            "network_decomposition_ready": True,
            "same_frame_ready": True,
            "ready": True,
        },
        "provenance": {
            "game_version": "1.19.0.6",
            "executable_sha256": EXECUTABLE_SHA256,
            "assessment_rva": "0x1878A00",
            "network_collector_rva": "0x1879850",
            "power_leaf": "CCharacter+0x1B8->+0x308",
            "fixed_point_scale": 100_000,
        },
    }


def _result(*, targets: list[int] | None = None) -> dict[str, object]:
    selected = targets or [808]
    return {
        "step": (
            "query-war-entry-assessments-v1-"
            + str(len(selected))
            + "-"
            + "-".join(str(target) for target in selected)
        ),
        "accepted": True,
        "status": "available",
        "query_sequence": 41,
        "war_entry_assessments": _payload(selected),
    }


def _r759_like_entry_snapshot(target: int = 909) -> dict[str, object]:
    declaration = _declaration(target)
    declaration.update(
        {
            "declaration_id": f"{target}-17--1",
            "casus_belli_key": "individual_county_de_jure_cb",
            "configuration_index": -1,
            "target_title_ids": [777],
        }
    )
    assessment = _row(target)
    assessment.update(
        {
            "distance_raw": 0,
            "actor_power_base_raw": 2_400_000_000,
            "actor_network_contribution_raw": 0,
            "actor_power_total_raw": 2_400_000_000,
            "target_power_base_raw": 1_500_000_000,
            "target_network_contribution_raw": 0,
            "target_pre_adjustment_total_raw": 1_500_000_000,
            "target_adjustment_delta_raw": 0,
            "target_power_total_raw": 1_500_000_000,
            "actual_power_ratio_raw": 62_500,
        }
    )
    payload = _payload([target])
    payload["assessments"] = [assessment]
    return {
        "snapshot_id": "native:5",
        "revision": 6,
        "native_revision": 5,
        "date_raw": 53_171_400,
        "played_character": {"character_id": 29_829, "alive": True},
        "active_wars": [],
        "player_armies": [],
        "declarable_wars": [declaration],
        "war_entry_assessments": payload,
        "campaign_root_context": {
            "schema_version": 1,
            "status": "available",
            "snapshot_revision": 5,
            "date_raw": 53_171_400,
            "player_character_id": 29_829,
            "player_monthly_gold_income": {"raw": 400_000, "scale": 100_000},
            "player_domain_size": 2,
            "player_domain_limit": 5,
            "player_targeting_faction_count": 0,
            "government": {
                "key": "feudal_government",
                "flags": ["government_is_feudal", "government_is_settled"],
                "native_flag_count": 2,
            },
            "readiness": {"ready": True},
        },
    }


def _player_claim(
    target: int,
    *,
    title: int,
    claimant: int = 29_829,
) -> dict[str, object]:
    return {
        "declaration_id": f"{target}-11-0",
        "target_character_id": target,
        "casus_belli_index": 11,
        "casus_belli_key": "claim_cb",
        "configuration_index": 0,
        "claimant_character_id": claimant,
        "target_title_ids": [title],
        "source": "native",
    }


def _claim_power_payload(
    target: int,
    *,
    target_base: int,
    target_network: int = 0,
    target_adjustment: int = 0,
    actor_base: int = 100_000,
    actor_network: int = 0,
) -> dict[str, object]:
    actor_total = actor_base + actor_network
    target_pre_adjustment = target_base + target_network
    target_total = target_pre_adjustment + target_adjustment
    row = _row(target)
    row.update(
        {
            "distance_raw": 0,
            "actor_power_base_raw": actor_base,
            "actor_network_contribution_raw": actor_network,
            "actor_power_total_raw": actor_total,
            "target_power_base_raw": target_base,
            "target_network_contribution_raw": target_network,
            "target_pre_adjustment_total_raw": target_pre_adjustment,
            "target_adjustment_delta_raw": target_adjustment,
            "target_power_total_raw": target_total,
            "actual_power_ratio_raw": (
                target_total * 100_000 // actor_total if actor_total else 0
            ),
        }
    )
    payload = _payload([target])
    payload["assessments"] = [row]
    return payload


def _claim_campaign_root(
    targets: list[tuple[int, int, str]],
) -> dict[str, object]:
    contexts = []
    for target, title, tier in sorted(targets):
        tier_raw = 2 if tier == "county" else 3
        contexts.append(
            {
                "character_id": target,
                "relationship_role": "adjacent_external_province_holder",
                "primary_title": {
                    "title_id": title,
                    "tier_raw": tier_raw,
                    "tier_key": tier,
                },
                "capital_province_id": title + 10_000,
                "immediate_liege_character_id": None,
                "top_liege_character_id": target,
                "independent": True,
            }
        )
    return {
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": 5,
        "date_raw": 53_171_400,
        "player_character_id": 29_829,
        "player_monthly_gold_income": {"raw": 400_000, "scale": 100_000},
        "player_domain_size": 2,
        "player_domain_limit": 5,
        "player_targeting_faction_count": 0,
        "primary_title": {"title_id": 700, "tier_raw": 3, "tier_key": "duchy"},
        "independent": True,
        "adjacent_external_province_holder_character_ids": sorted(
            target for target, _title, _tier in targets
        ),
        "related_character_contexts": contexts,
        "government": {
            "key": "feudal_government",
            "flags": ["government_is_feudal", "government_is_settled"],
            "native_flag_count": 2,
        },
        "readiness": {
            "ready": True,
            "adjacent_external_province_holders_ready": True,
            "related_character_contexts_ready": True,
        },
    }


def _claim_snapshot_and_history(
    declarations: list[dict[str, object]],
    payloads: list[dict[str, object]],
    *,
    target_contexts: list[tuple[int, int, str]],
    active_wars: list[dict[str, object]] | None = None,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    snapshot = {
        "snapshot_id": "native:5",
        "revision": 6,
        "native_revision": 5,
        "date_raw": 53_171_400,
        "played_character": {"character_id": 29_829, "alive": True},
        "active_wars": active_wars or [],
        "player_armies": [],
        "declarable_wars": declarations,
        "campaign_root_context": _claim_campaign_root(target_contexts),
    }
    history = [{"index": 1, "command": "save-checkpoint", "ok": True}]
    if payloads:
        snapshot["war_entry_assessments"] = payloads[-1]
        for index, payload in enumerate(payloads[:-1], start=2):
            target = payload["requested_target_character_ids"][0]
            history.append(
                {
                    "index": index,
                    "command": f"query-war-entry-assessments-v1-1-{target}",
                    "ok": True,
                    "result": {"war_entry_assessments": payload},
                }
            )
    return snapshot, history


def _semantic_snapshot(
    revision: int = 5,
    *,
    active_wars: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "type": "state_snapshot",
        "protocol_version": 1,
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "state": {
            "phase": "map_hud",
            "date": "1066.9.15",
            "date_raw": 53_171_400,
            "speed": 1,
            "paused": True,
            "map_ready": True,
            "history": [],
            "active_event": None,
            "pending_character_interaction": None,
            "played_character": {"character_id": 29_829, "alive": True},
            "one_life_settlement": None,
            "active_wars": active_wars or [],
            "player_armies": [],
        },
    }


class _FakeEndpoint:
    def __init__(self) -> None:
        self.pipe_name = r"\\.\pipe\xar_war_entry_fixture"
        self.frames: list[dict[str, object]] = []
        self.on_frame = None
        self.send_hook = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame

    def publish(self, frame: dict[str, object]) -> None:
        assert self.on_frame is not None
        self.on_frame(frame)

    def send(self, frame: dict[str, object]) -> None:
        self.frames.append(frame)
        if self.send_hook is not None:
            self.send_hook(frame)

    def close(self) -> None:
        return None

    def transport_error(self) -> str | None:
        return None


def _native_driver(
    *,
    declarations: list[dict[str, object]] | None = None,
    active_wars: list[dict[str, object]] | None = None,
) -> tuple[NativeHeadlessGameplayDriver, _FakeEndpoint]:
    endpoint = _FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name,
        endpoint=endpoint,
        command_timeout_seconds=0.1,
    )
    endpoint.publish(
        {
            "type": "hello",
            "protocol_version": 1,
            "bridge_version": "0.1.0",
            "pid": 4545,
            "session_generation": 0,
            "game_version": "1.19.0.6",
            "executable_sha256": EXECUTABLE_SHA256,
            "capabilities": [
                "game.state.snapshot",
                QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY,
            ],
        }
    )
    endpoint.publish(_semantic_snapshot(active_wars=active_wars))
    snapshot = driver.take_snapshot()
    driver._declarable_wars = (
        [_declaration(808), _declaration(42)]
        if declarations is None
        else declarations
    )
    driver._declaration_query_sequence = 1
    diagnostics = snapshot["diagnostics"]
    assert isinstance(diagnostics, dict)
    driver._declaration_query_binding = {
        "native_revision": snapshot["native_revision"],
        "snapshot_id": snapshot["snapshot_id"],
        "revision": snapshot["revision"],
        "connection_generation": diagnostics["connection_generation"],
        "episode_run_id": snapshot["episode_run_id"],
    }
    return driver, endpoint


def _answer(endpoint: _FakeEndpoint) -> None:
    def answer(frame: dict[str, object]) -> None:
        if frame.get("type") != "execute_step":
            return
        endpoint.publish(
            {
                "type": "command_result",
                "protocol_version": 1,
                "request_id": frame["request_id"],
                "ok": True,
                "result": _result(),
            }
        )

    endpoint.send_hook = answer


class WarEntryNativeDriverTests(unittest.TestCase):
    def test_paused_query_is_scope_checked_and_cached_on_exact_frame(self) -> None:
        driver, endpoint = _native_driver()
        _answer(endpoint)
        capabilities = driver.capabilities()
        self.assertTrue(capabilities["war_entry_assessments_query_supported"])
        self.assertIn(STEP, capabilities["action_steps"])
        self.assertIn(OTHER_STEP, capabilities["action_steps"])
        self.assertNotIn(
            "query-war-entry-assessments-v1-2-808-42",
            capabilities["action_steps"],
        )
        self.assertNotIn(
            "query-war-entry-assessments-v1-N",
            capabilities["action_steps"],
        )

        revision = int(driver.take_snapshot()["revision"])
        result = driver.execute_step(STEP, expected_revision=revision)

        self.assertEqual(result["status"], "available")
        self.assertEqual(
            result["war_entry_assessments"]["assessments"][0][
                "actual_power_ratio_raw"
            ],
            85_000,
        )
        cached = driver.take_snapshot()
        self.assertEqual(cached["war_entry_assessments_status"], "available")
        self.assertEqual(
            cached["war_entry_assessments"]["requested_target_character_ids"],
            [808],
        )

        frozen = copy.deepcopy(driver._war_entry_assessments_query)
        assert isinstance(frozen, dict)
        for field, replacement in {
            "native_revision": 99,
            "snapshot_id": "native:99",
            "revision": 99,
            "connection_generation": 99,
            "episode_run_id": "other",
            "target_character_ids": [42],
        }.items():
            with self.subTest(field=field):
                candidate = copy.deepcopy(frozen)
                candidate["cache_binding"][field] = replacement
                driver._war_entry_assessments_query = candidate
                self.assertIsNone(driver.take_snapshot()["war_entry_assessments"])
        driver._war_entry_assessments_query = frozen
        endpoint.publish(_semantic_snapshot(6))
        self.assertIsNone(driver.take_snapshot()["war_entry_assessments"])

    def test_active_war_opponent_is_advertised_and_queryable(self) -> None:
        driver, endpoint = _native_driver(
            declarations=[], active_wars=[_active_war(808)]
        )
        _answer(endpoint)

        self.assertIn(STEP, driver.capabilities()["action_steps"])
        revision = int(driver.take_snapshot()["revision"])
        result = driver.execute_step(STEP, expected_revision=revision)

        self.assertEqual(result["status"], "available")
        self.assertEqual(
            result["war_entry_assessments"]["requested_target_character_ids"],
            [808],
        )
        self.assertEqual(
            result["target_scopes"],
            [{"target_character_id": 808, "sources": ["active_war_primary_opponent"]}],
        )

    def test_two_independent_active_war_reads_bind_to_one_paused_frame(self) -> None:
        driver, endpoint = _native_driver(
            declarations=[], active_wars=[_active_war(808)]
        )
        sequence = 40

        def answer(frame: dict[str, object]) -> None:
            nonlocal sequence
            if frame.get("type") != "execute_step":
                return
            sequence += 1
            result = _result()
            result["query_sequence"] = sequence
            endpoint.publish({
                "type": "command_result", "protocol_version": 1,
                "request_id": frame["request_id"], "ok": True,
                "result": result,
            })

        endpoint.send_hook = answer
        revision = int(driver.take_snapshot()["revision"])
        driver.execute_step(STEP, expected_revision=revision)
        self.assertEqual(
            len(driver.take_snapshot()["war_entry_assessments_two_read_trace_v1"]), 1
        )
        driver.execute_step(STEP, expected_revision=revision)
        trace = driver.take_snapshot()["war_entry_assessments_two_read_trace_v1"]
        self.assertEqual([row["query"]["query_sequence"] for row in trace], [41, 42])
        self.assertEqual(trace[0]["after_snapshot"], trace[1]["before_snapshot"])
        self.assertEqual(trace[1]["query"]["target_scopes"], [
            {"target_character_id": 808, "sources": ["active_war_primary_opponent"]}
        ])
        endpoint.publish(_semantic_snapshot(6, active_wars=[_active_war(808)]))
        self.assertEqual(
            driver.take_snapshot()["war_entry_assessments_two_read_trace_v1"], []
        )

    def test_out_of_scope_target_is_rejected_before_pipe_send(self) -> None:
        driver, endpoint = _native_driver()
        before = len(endpoint.frames)
        with self.assertRaisesRegex(BridgeUnavailableError, "outside current"):
            driver.execute_step(
                "query-war-entry-assessments-v1-1-43",
                expected_revision=int(driver.take_snapshot()["revision"]),
            )
        self.assertEqual(len(endpoint.frames), before)

    def test_multi_target_literal_is_rejected_before_pipe_send(self) -> None:
        driver, endpoint = _native_driver()
        before = len(endpoint.frames)
        with self.assertRaisesRegex(
            UnsupportedStepError, "non-production-bounded"
        ):
            driver.execute_step(
                "query-war-entry-assessments-v1-2-808-42",
                expected_revision=int(driver.take_snapshot()["revision"]),
            )
        self.assertEqual(len(endpoint.frames), before)

    def test_result_target_or_native_revision_drift_is_rejected(self) -> None:
        for mutation in ("target", "revision"):
            driver, endpoint = _native_driver()

            def answer(frame: dict[str, object], *, mutation=mutation) -> None:
                if frame.get("type") != "execute_step":
                    return
                result = _result()
                if mutation == "target":
                    result["war_entry_assessments"]["assessments"][0][
                        "target_character_id"
                    ] = 42
                else:
                    result["war_entry_assessments"]["snapshot_revision"] = 6
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": True,
                        "result": result,
                    }
                )

            endpoint.send_hook = answer
            with self.subTest(mutation=mutation):
                with self.assertRaises(BridgeUnavailableError):
                    driver.execute_step(
                        STEP,
                        expected_revision=int(driver.take_snapshot()["revision"]),
                    )


class _ServiceDriver:
    def __init__(
        self, *, advertise: bool = True, active_war_only: bool = False
    ) -> None:
        self.advertise = advertise
        self.active_war_only = active_war_only
        self.execute_count = 0
        self.snapshot_count = 0

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "war-entry-fixture",
            "source": "fixture",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [STEP, OTHER_STEP],
            "bridge_capabilities": (
                [QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY]
                if self.advertise
                else []
            ),
        }

    def take_snapshot(self) -> dict[str, object]:
        self.snapshot_count += 1
        return {
            "format_version": 1,
            "snapshot_id": "war-entry:17",
            "revision": 17,
            "native_revision": 5,
            "date_raw": 53_171_400,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 29_829, "alive": True},
            "declarable_wars": (
                []
                if self.active_war_only
                else [_declaration(808), _declaration(42)]
            ),
            "active_wars": (
                [_active_war(808)] if self.active_war_only else []
            ),
            "episode_run_id": "native-29829-test",
            "backend_id": "war-entry-fixture",
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        self.execute_count += 1
        if step != STEP or expected_revision != 17:
            raise AssertionError("service changed the target order or revision")
        return {**_result(), "backend_id": "war-entry-fixture"}

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("war-entry assessment must not advance time")


class WarEntryServiceAndStrategyTests(unittest.TestCase):
    def test_service_requires_native_capability_and_same_revision(self) -> None:
        unavailable = _ServiceDriver(advertise=False)
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(unavailable).query_war_entry_assessments(
                [808], expected_revision=17
            )
        self.assertEqual(unavailable.execute_count, 0)

        result = GameplayBridgeService(
            _ServiceDriver()
        ).query_war_entry_assessments([808], expected_revision=17)
        self.assertEqual(result["queried_revision"], 17)
        self.assertEqual(result["queried_native_revision"], 5)
        self.assertEqual(result["target_character_ids"], [808])
        self.assertEqual(
            result["target_scopes"],
            [{"target_character_id": 808, "sources": ["declarable_war"]}],
        )
        self.assertNotIn("win_probability", result)

    def test_service_accepts_active_war_opponent_scope(self) -> None:
        result = GameplayBridgeService(
            _ServiceDriver(active_war_only=True)
        ).query_war_entry_assessments([808], expected_revision=17)

        self.assertEqual(
            result["target_scopes"],
            [
                {
                    "target_character_id": 808,
                    "sources": ["active_war_primary_opponent"],
                }
            ],
        )

    def test_service_rejects_multiple_targets_before_snapshot_or_driver(self) -> None:
        driver = _ServiceDriver()
        with self.assertRaisesRegex(ValueError, "exactly 1"):
            GameplayBridgeService(driver).query_war_entry_assessments(
                [808, 42], expected_revision=17
            )
        self.assertEqual(driver.snapshot_count, 0)
        self.assertEqual(driver.execute_count, 0)

    def test_strategy_queries_power_before_life_advance_but_never_declares(self) -> None:
        declaration = _declaration(808)
        plan = choose_one_life_turn(
            [{"index": 1, "command": "save-checkpoint", "ok": True}],
            snapshot={
                "active_wars": [],
                "player_armies": [],
                "declarable_wars": [declaration],
            },
            action_steps={
                "query-declarable-wars",
                "query-war-entry-assessments-v1-1-808",
                "declare-war-808-17-0",
                "life-advance",
            },
        )
        self.assertEqual(plan["phase"], "native_war_entry_assessment")
        self.assertEqual(
            plan["selected_step"],
            "query-war-entry-assessments-v1-1-808",
        )

        snapshot = {
            "active_wars": [],
            "player_armies": [],
            "declarable_wars": [declaration],
            "war_entry_assessments": _payload([808]),
        }
        deferred = choose_one_life_turn(
            [{"index": 1, "command": "save-checkpoint", "ok": True}],
            snapshot=snapshot,
            action_steps={
                "query-war-entry-assessments-v1-1-808",
                "declare-war-808-17-0",
                "life-advance",
            },
        )
        self.assertEqual(deferred["phase"], "native_war_entry_no_declare")
        self.assertEqual(deferred["selected_step"], "life-advance")
        self.assertEqual(deferred["decision"]["outcome"], "NO_DECLARE")
        self.assertFalse(
            deferred["decision"]["automatic_declaration_enabled"]
        )
        self.assertTrue(
            deferred["decision"]["native_power_assessment_consumed"]
        )
        self.assertIsNone(deferred["decision"]["eu_lower_raw"])
        self.assertEqual(deferred["war_entry_assessment"], _row(808))
        eu = deferred["war_entry_expected_utility"]
        self.assertEqual(eu["status"], "native_power_component_ready")
        self.assertTrue(eu["native_power_component_ready"])
        self.assertEqual(
            eu["native_power_component"][
                "conservative_self_power_margin_raw"
            ],
            55_223 - 85_000,
        )
        self.assertEqual(
            eu["native_power_component"]["actual_power_ratio_raw"],
            85_000,
        )
        self.assertIsNone(eu["eu_lower_raw"])
        self.assertIn("combat_forecast", eu["missing_components"])
        self.assertFalse(eu["automatic_declaration_enabled"])

    def test_feudal_de_jure_overmatch_remains_a_forecast_candidate(self) -> None:
        snapshot = _r759_like_entry_snapshot(target=909)
        plan = choose_one_life_turn(
            [{"index": 1, "command": "save-checkpoint", "ok": True}],
            snapshot=snapshot,
            action_steps={
                "query-declarable-wars",
                "query-war-entry-assessments-v1-1-909",
                "declare-war-909-17--1",
                "life-advance",
            },
        )

        self.assertEqual(plan["phase"], "native_war_entry_forecast_required")
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["decision"]["outcome"], "NO_DECLARE")
        self.assertFalse(plan["decision"]["automatic_declaration_enabled"])
        self.assertEqual(
            plan["decision"]["policy"],
            "feudal-single-county-de-jure-forecast-candidate-v1",
        )
        self.assertEqual(plan["declaration"]["target_title_ids"], [777])
        self.assertEqual(plan["war_entry_candidate"]["native_actual_power_ratio_raw"], 62_500)
        self.assertEqual(plan["war_entry_candidate"]["typed_declaration_step"], "declare-war-909-17--1")
        self.assertTrue(plan["war_entry_candidate"]["typed_declaration_available"])
        self.assertIsNone(plan["war_entry_expected_utility"]["eu_lower_raw"])
        self.assertTrue(plan["prewar_forecast_admission_available"])
        self.assertFalse(plan["prewar_forecast_admission"]["admitted"])
        self.assertIn(
            "game.command.query-prewar-combat-simulation-inputs-v3-N",
            plan["required_capabilities"],
        )
        self.assertNotIn(
            "game.command.query-combat-simulation-inputs-v3-N",
            plan["required_capabilities"],
        )
        self.assertIn("game.forecast.combat-monte-carlo-v1", plan["required_capabilities"])

    def test_feudal_de_jure_below_old_overmatch_still_enters_forecast(self) -> None:
        snapshot = _r759_like_entry_snapshot(target=909)
        assessment = snapshot["war_entry_assessments"]["assessments"][0]
        assessment["target_power_base_raw"] = 1_800_000_000
        assessment["target_pre_adjustment_total_raw"] = 1_800_000_000
        assessment["target_power_total_raw"] = 1_800_000_000
        assessment["actual_power_ratio_raw"] = 75_000
        plan = choose_one_life_turn(
            [{"index": 1, "command": "save-checkpoint", "ok": True}],
            snapshot=snapshot,
            action_steps={"declare-war-909-17--1", "life-advance"},
        )
        self.assertEqual(plan["phase"], "native_war_entry_forecast_required")
        self.assertEqual(plan["declaration"]["declaration_id"], "909-17--1")
        self.assertEqual(plan["war_entry_candidate"]["native_actual_power_ratio_raw"], 75_000)
        self.assertEqual(plan["decision"]["outcome"], "NO_DECLARE")
        self.assertEqual(plan["selected_step"], "life-advance")

    def test_general_native_declaration_uses_decisive_aggregate_battle_prior(self) -> None:
        snapshot = _r759_like_entry_snapshot(target=909)
        snapshot["declarable_wars"] = [_declaration(909)]
        snapshot["campaign_root_context"]["independent"] = True
        assessment = snapshot["war_entry_assessments"]["assessments"][0]
        assessment.update({
            "target_power_base_raw": 600_000_000,
            "target_pre_adjustment_total_raw": 600_000_000,
            "target_power_total_raw": 600_000_000,
            "actual_power_ratio_raw": 25_000,
        })
        plan = choose_one_life_turn(
            [{"index": 1, "command": "save-checkpoint", "ok": True}],
            snapshot=snapshot,
            action_steps={"declare-war-909-17-0", "life-advance"},
        )
        self.assertEqual(plan["phase"], "native_war_declaration")
        self.assertEqual(plan["selected_step"], "declare-war-909-17-0")
        self.assertEqual(plan["decision"]["policy"], "general-native-war-entry-battle-prior-v1")
        self.assertTrue(plan["prewar_forecast_admission"]["admitted"])
        self.assertFalse(plan["prewar_battle_forecast"]["calibrated_probability"])

    def test_de_jure_candidate_scope_stays_observable_without_declaration(self) -> None:
        cases = {
            "power_ratio": lambda snapshot: snapshot[
                "war_entry_assessments"
            ]["assessments"][0].update({"actual_power_ratio_raw": 66_668}),
            "actor_network": lambda snapshot: snapshot[
                "war_entry_assessments"
            ]["assessments"][0].update(
                {
                    "actor_network_contribution_raw": 1,
                    "actor_power_total_raw": 2_400_000_001,
                }
            ),
            "target_adjustment": lambda snapshot: snapshot[
                "war_entry_assessments"
            ]["assessments"][0].update(
                {
                    "target_adjustment_delta_raw": -1,
                    "target_power_total_raw": 1_499_999_999,
                }
            ),
            "government": lambda snapshot: snapshot[
                "campaign_root_context"
            ]["government"].update(
                {"key": "tribal_government", "flags": ["government_is_tribal"]}
            ),
            "faction": lambda snapshot: snapshot[
                "campaign_root_context"
            ].update({"player_targeting_faction_count": 1}),
            "stale_root": lambda snapshot: snapshot[
                "campaign_root_context"
            ].update({"snapshot_revision": 4}),
            "other_cb": lambda snapshot: snapshot["declarable_wars"][0].update(
                {"casus_belli_key": "claim_cb"}
            ),
            "active_war": lambda snapshot: snapshot.update(
                {"active_wars": [_active_war(808)]}
            ),
        }
        for name, mutate in cases.items():
            snapshot = _r759_like_entry_snapshot()
            mutate(snapshot)
            with self.subTest(name=name):
                plan = choose_one_life_turn(
                    [{"index": 1, "command": "save-checkpoint", "ok": True}],
                    snapshot=snapshot,
                    action_steps={
                        "query-declarable-wars",
                        "query-war-entry-assessments-v1-1-909",
                        "declare-war-909-17--1",
                        "life-advance",
                    },
                )
                self.assertNotEqual(plan["phase"], "native_war_declaration")
                if name == "power_ratio":
                    self.assertEqual(plan["phase"], "native_war_entry_forecast_required")
                    self.assertEqual(plan["war_entry_candidate"]["native_actual_power_ratio_raw"], 66_668)
                elif name != "active_war":
                    self.assertEqual(
                        plan["phase"], "native_war_entry_no_declare"
                    )
                if name != "active_war":
                    self.assertEqual(plan["selected_step"], "life-advance")
                    self.assertEqual(plan["decision"]["outcome"], "NO_DECLARE")

    def test_strategy_uses_same_frame_power_and_network_risk_to_rank_targets(self) -> None:
        risky = _payload([42])
        safe = _payload([808])
        safe_row = safe["assessments"][0]
        safe_row.update(
            {
                "actor_power_base_raw": 90_000,
                "actor_network_contribution_raw": 10_000,
                "actor_power_total_raw": 100_000,
                "target_power_base_raw": 45_000,
                "target_network_contribution_raw": 5_000,
                "target_pre_adjustment_total_raw": 50_000,
                "target_adjustment_delta_raw": 10_000,
                "target_power_total_raw": 60_000,
                "actual_power_ratio_raw": 60_000,
            }
        )
        snapshot = {
            "active_wars": [],
            "player_armies": [],
            "declarable_wars": [_declaration(42), _declaration(808)],
            "war_entry_assessments": safe,
            "native_revision": 5,
            "date_raw": 53_171_400,
            "played_character": {"character_id": 29_829, "alive": True},
        }
        commands = [
            {"index": 1, "command": "save-checkpoint", "ok": True},
            {
                "index": 2,
                "command": OTHER_STEP,
                "ok": True,
                "result": {"war_entry_assessments": risky},
            },
        ]
        plan = choose_one_life_turn(
            commands,
            snapshot=snapshot,
            action_steps={
                STEP,
                OTHER_STEP,
                "declare-war-42-17-0",
                "declare-war-808-17-0",
            },
        )

        # The old CB/title/target-id heuristic would choose 42.  Exact native
        # power instead makes the self-sufficient 808 target the lower-risk
        # diagnostic candidate, while declaration remains disabled.
        self.assertEqual(plan["declaration"]["target_character_id"], 808)
        self.assertEqual(plan["war_entry_assessment"], safe_row)
        component = plan["war_entry_expected_utility"][
            "native_power_component"
        ]
        self.assertEqual(component["conservative_self_power_margin_raw"], 30_000)
        self.assertEqual(component["actor_network_dependency_raw"], 10_000)
        self.assertEqual(component["target_network_support_raw"], 5_000)
        self.assertIsNone(plan["selected_step"])

    def test_strategy_queries_an_alternative_after_native_self_power_deficit(self) -> None:
        plan = choose_one_life_turn(
            [{"index": 1, "command": "save-checkpoint", "ok": True}],
            snapshot={
                "active_wars": [],
                "player_armies": [],
                "declarable_wars": [_declaration(42), _declaration(808)],
                "war_entry_assessments": _payload([42]),
                "native_revision": 5,
                "date_raw": 53_171_400,
                "played_character": {
                    "character_id": 29_829,
                    "alive": True,
                },
            },
            action_steps={STEP, OTHER_STEP},
        )

        self.assertEqual(
            plan["phase"], "native_war_entry_assessment_alternative"
        )
        self.assertEqual(plan["selected_step"], STEP)
        self.assertEqual(
            plan["rejected_power_declaration"]["target_character_id"], 42
        )
        self.assertEqual(
            plan["rejected_war_entry_expected_utility"][
                "native_power_component"
            ]["conservative_self_power_margin_raw"],
            55_223 - 85_000,
        )

    def test_player_claim_selector_compares_all_county_targets_and_ignores_religious_cb(
        self,
    ) -> None:
        claims = [
            _player_claim(31_050, title=2_132),
            _player_claim(31_549, title=2_111),
            _player_claim(33_422, title=2_102),
            _player_claim(33_621, title=2_115),
        ]
        religious = _declaration(33_621)
        religious.update(
            {
                "declaration_id": "33621-40--1",
                "casus_belli_index": 40,
                "casus_belli_key": "minor_religious_war",
                "configuration_index": -1,
                "claimant_character_id": -1,
                "target_title_ids": [2_115],
            }
        )
        snapshot, history = _claim_snapshot_and_history(
            [*claims, religious],
            [
                _claim_power_payload(31_050, target_base=18_719),
                _claim_power_payload(
                    31_549, target_base=20_000, target_network=25_422
                ),
                _claim_power_payload(33_422, target_base=34_172),
                _claim_power_payload(33_621, target_base=27_791),
            ],
            target_contexts=[
                (31_050, 2_132, "duchy"),
                (31_549, 2_111, "county"),
                (33_422, 2_102, "county"),
                (33_621, 2_115, "county"),
            ],
        )

        plan = choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps={
                *(f"declare-war-{row['declaration_id']}" for row in claims),
                "declare-war-33621-40--1",
                "life-advance",
            },
        )

        self.assertEqual(plan["phase"], "native_war_declaration")
        self.assertEqual(plan["selected_step"], "declare-war-33621-11-0")
        self.assertEqual(plan["declaration"]["target_character_id"], 33_621)
        self.assertEqual(plan["declaration"]["casus_belli_key"], "claim_cb")
        self.assertEqual(plan["decision"]["claimant_character_id"], 29_829)
        self.assertEqual(plan["decision"]["outcome"], "DECLARE")
        self.assertTrue(plan["prewar_forecast_admission"]["admitted"])
        self.assertFalse(plan["prewar_battle_forecast"]["calibrated_probability"])
        self.assertEqual(
            plan["decision"]["policy"],
            "feudal-adjacent-independent-county-player-claim-forecast-candidate-v1",
        )

    def test_player_claim_selector_includes_target_network_in_diagnostic_total(
        self,
    ) -> None:
        claim = _player_claim(808, title=91)
        snapshot, history = _claim_snapshot_and_history(
            [claim],
            [
                _claim_power_payload(
                    808,
                    target_base=30_000,
                    target_network=20_000,
                )
            ],
            target_contexts=[(808, 91, "county")],
        )

        plan = choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps={"declare-war-808-11-0", "life-advance"},
        )

        self.assertEqual(plan["phase"], "native_war_entry_forecast_required")
        self.assertEqual(
            plan["war_entry_assessment"][
                "target_network_contribution_raw"
            ],
            20_000,
        )
        self.assertEqual(
            plan["war_entry_assessment"]["target_power_total_raw"], 50_000
        )
        self.assertEqual(plan["decision"]["outcome"], "NO_DECLARE")

    def test_player_claim_below_two_to_one_still_enters_forecast(self) -> None:
        claim = _player_claim(808, title=91)
        snapshot, history = _claim_snapshot_and_history(
            [claim],
            [_claim_power_payload(808, target_base=80_000)],
            target_contexts=[(808, 91, "county")],
        )
        plan = choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps={"declare-war-808-11-0", "life-advance"},
        )
        self.assertEqual(plan["phase"], "native_war_entry_forecast_required")
        self.assertEqual(plan["declaration"]["declaration_id"], "808-11-0")
        self.assertEqual(plan["war_entry_candidate"]["native_actual_power_ratio_raw"], 80_000)
        self.assertEqual(plan["decision"]["outcome"], "NO_DECLARE")
        self.assertEqual(plan["selected_step"], "life-advance")
        without_advance = choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps={"declare-war-808-11-0"},
        )
        self.assertEqual(without_advance["phase"], "native_war_entry_forecast_required")
        self.assertIsNone(without_advance["selected_step"])
        self.assertEqual(without_advance["decision"]["outcome"], "NO_DECLARE")

    def test_player_claim_selector_rejects_zero_total_and_nonplayer_claims(
        self,
    ) -> None:
        cases = (
            (
                "zero_total",
                _player_claim(808, title=91),
                _claim_power_payload(808, target_base=0),
            ),
            (
                "nonplayer_claimant",
                _player_claim(808, title=91, claimant=42),
                _claim_power_payload(808, target_base=20_000),
            ),
        )
        for name, claim, payload in cases:
            snapshot, history = _claim_snapshot_and_history(
                [claim],
                [payload],
                target_contexts=[(808, 91, "county")],
            )
            with self.subTest(name=name):
                plan = choose_one_life_turn(
                    history,
                    snapshot=snapshot,
                    action_steps={"declare-war-808-11-0", "life-advance"},
                )
                self.assertNotEqual(plan["phase"], "native_war_declaration")
                self.assertNotEqual(plan["selected_step"], "declare-war-808-11-0")

    def test_player_claim_selector_queries_every_candidate_before_action(self) -> None:
        first = _player_claim(808, title=91)
        second = _player_claim(909, title=92)
        snapshot, history = _claim_snapshot_and_history(
            [first, second],
            [_claim_power_payload(808, target_base=20_000)],
            target_contexts=[(808, 91, "county"), (909, 92, "county")],
        )
        query_step = "query-war-entry-assessments-v1-1-909"

        query = choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps={
                query_step,
                "declare-war-808-11-0",
                "declare-war-909-11-0",
                "life-advance",
            },
        )
        self.assertEqual(query["phase"], "native_player_claim_power_assessment")
        self.assertEqual(query["selected_step"], query_step)

        no_query = choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps={
                "declare-war-808-11-0",
                "declare-war-909-11-0",
                "life-advance",
            },
        )
        self.assertEqual(
            no_query["phase"], "native_player_claim_evidence_required"
        )
        self.assertEqual(no_query["decision"]["outcome"], "NO_DECLARE")
        self.assertEqual(no_query["selected_step"], "life-advance")

    def test_player_claim_selector_requires_peace_and_complete_scope(self) -> None:
        claim = _player_claim(808, title=91)
        snapshot, history = _claim_snapshot_and_history(
            [claim],
            [_claim_power_payload(808, target_base=20_000)],
            target_contexts=[(808, 91, "county")],
            active_wars=[_active_war(42)],
        )
        plan = choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps={"declare-war-808-11-0", "life-advance"},
        )
        self.assertNotEqual(plan["phase"], "native_war_declaration")

        snapshot["active_wars"] = []
        snapshot.pop("campaign_root_context")
        query = choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps={
                "query-campaign-root-context-v1",
                "declare-war-808-11-0",
                "life-advance",
            },
        )
        self.assertEqual(query["phase"], "native_player_claim_scope_assessment")
        self.assertEqual(query["selected_step"], "query-campaign-root-context-v1")

    def test_strategy_does_not_rank_with_a_stale_history_assessment(self) -> None:
        stale = _payload([42], snapshot_revision=4)
        current = _payload([808], snapshot_revision=5)
        plan = choose_one_life_turn(
            [
                {"index": 1, "command": "save-checkpoint", "ok": True},
                {
                    "index": 2,
                    "command": OTHER_STEP,
                    "ok": True,
                    "result": {"war_entry_assessments": stale},
                },
            ],
            snapshot={
                "active_wars": [],
                "player_armies": [],
                "declarable_wars": [_declaration(42), _declaration(808)],
                "war_entry_assessments": current,
                "native_revision": 5,
                "date_raw": 53_171_400,
                "played_character": {
                    "character_id": 29_829,
                    "alive": True,
                },
            },
            action_steps={STEP},
        )

        self.assertEqual(plan["declaration"]["target_character_id"], 808)
        self.assertEqual(plan["war_entry_assessment"], _row(808))


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class WarEntryMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_and_calls_war_entry_tool(self) -> None:
        from mcp import Client

        driver = _ServiceDriver()
        server = create_server(driver)
        async with Client(server) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            self.assertIn("ck3_query_war_entry_assessments", names)
            result = await client.call_tool(
                "ck3_query_war_entry_assessments",
                {
                    "target_character_ids": [808],
                    "expected_revision": 17,
                },
            )
            rejected = await client.call_tool(
                "ck3_query_war_entry_assessments",
                {
                    "target_character_ids": [808, 42],
                    "expected_revision": 17,
                },
            )

        self.assertFalse(result.is_error)
        payload = result.structured_content
        self.assertEqual(payload["status"], "available")
        self.assertEqual(payload["target_character_ids"], [808])
        self.assertNotIn("win_probability", payload)
        self.assertTrue(rejected.is_error)
        self.assertEqual(driver.execute_count, 1)
        self.assertEqual(driver.snapshot_count, 2)


if __name__ == "__main__":
    unittest.main()

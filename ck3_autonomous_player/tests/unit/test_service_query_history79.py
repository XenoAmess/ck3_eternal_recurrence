"""Four focused groups for the root/bundle history-export callsite change.

The frozen recipe supplies old and new service classes. No existing test module
is imported, and the native boundary is a small in-memory reply transport.
"""
from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path
import tempfile
import threading
import textwrap
import unittest

from xar_autoplayer.bridge.campaign_root_context_contract import (
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
    _PROVENANCE_BY_BUILD,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver

OLD_SERVICE = None
NEW_SERVICE = None
TEMP_ROOT: Path | None = None
CHECKS: list[dict[str, object]] = []
GROUP_OBSERVATIONS: dict[str, object] = {}
REVISION = 41
NATIVE_REVISION = 2**63 + 17
DATE_RAW = 53_182_008
PLAYER_ID = 12_345
SNAPSHOT_ID = "service-history79:41"
STEP = QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP


def configure_service_sources(old_service: type, new_service: type, temp_root: Path) -> None:
    global OLD_SERVICE, NEW_SERVICE, TEMP_ROOT
    OLD_SERVICE, NEW_SERVICE = old_service, new_service
    TEMP_ROOT = temp_root


def _frame() -> dict[str, object]:
    title = {"title_id": 67_890, "tier_raw": 2, "tier_key": "county"}
    readiness = {key: True for key in (
        "player_identity_ready", "player_monthly_gold_income_ready",
        "player_health_ready", "player_domain_ready", "player_targeting_factions_ready",
        "primary_title_ready", "primary_title_succession_ready", "held_title_partition_ready",
        "capital_ready", "lieges_ready", "direct_landed_vassals_ready",
        "adjacent_external_province_holders_ready", "related_character_contexts_ready",
        "government_ready", "selected_game_rule_tokens_ready", "same_frame_ready", "ready",
    )}
    readiness["council_ready"] = False
    return {
        "schema_version": 1, "status": "available",
        "snapshot_revision": NATIVE_REVISION, "date_raw": DATE_RAW,
        "local_player_id": 0, "player_character_id": PLAYER_ID,
        "player_character_alive": True,
        "player_monthly_gold_income": {"raw": 570_772, "scale": 100_000},
        "player_health": {"raw": 275_000, "scale": 100_000},
        "player_domain_size": 1, "player_domain_limit": 7,
        "player_targeting_faction_count": 0,
        "council": {
            "status": "unavailable", "coverage_key": "standard_landed_non_nomadic_core_v1",
            "owner_character_id": PLAYER_ID, "positions": [],
            "auxiliary_vacancies_complete": False,
            "unavailable_reason": "actual4_council_position_key_source_unavailable",
        },
        "primary_title": title,
        "primary_title_succession_character_ids": [98_765],
        "held_title_partition": [{"title": copy.deepcopy(title), "first_heir_character_id": 98_765,
                                  "capital_province_id": 42, "primary": True}],
        "capital_province_id": 42, "immediate_liege_character_id": None,
        "top_liege_character_id": PLAYER_ID, "independent": True,
        "direct_landed_vassal_character_ids": [],
        "adjacent_external_province_holder_character_ids": [],
        "related_character_contexts": [],
        "government": {"key": "feudal_government", "flags": ["government_is_feudal", "government_is_settled"],
                       "native_flag_count": 2},
        "selected_game_rule_tokens": ["normal_difficulty"],
        "native_selected_game_rule_token_count": 1,
        "readiness": readiness, "unavailable_reason": None,
        "provenance": copy.deepcopy(_PROVENANCE_BY_BUILD["1.20.0.4"]),
    }


def _snapshot() -> dict[str, object]:
    provenance = _PROVENANCE_BY_BUILD["1.20.0.4"]
    return {
        "format_version": 1, "snapshot_id": SNAPSHOT_ID,
        "revision": REVISION, "native_revision": NATIVE_REVISION,
        "source": "named-pipe", "backend_id": "native-headless",
        "date_raw": DATE_RAW, "paused": True, "episode_run_id": "native-service-history79",
        "played_character": {"character_id": PLAYER_ID, "alive": True, "stress_points": 120},
        "played_character_gold": {"raw": 2_500_000, "scale": 100_000},
        "active_event": None, "pending_character_interaction": None, "active_wars": [],
        "diagnostics": {"hello": {"expected_ck3_version": provenance["game_version"],
                                    "expected_ck3_sha256": provenance["executable_sha256"]}},
    }


def _reply() -> dict[str, object]:
    frame = _frame()
    mirrored = {key: copy.deepcopy(value) for key, value in frame.items()
                if key not in {"status", "snapshot_revision"}}
    return {
        "step": STEP, "accepted": True, "status": "available", "query_sequence": 9,
        "snapshot_revision": NATIVE_REVISION, "campaign_root_context": frame,
        "backend_id": "native-headless", **mirrored,
        "campaign_root_context_ready": True, "queried_snapshot_id": SNAPSHOT_ID,
        "queried_revision": REVISION, "queried_native_revision": NATIVE_REVISION,
    }


def _history_rows() -> list[dict[str, object]]:
    return [{
        "index": index, "command": "future-opaque-query", "ok": True,
        "future_extension": {"duplicates": [7, 7, -1], "qword": 2**64 - 1,
                             "nested": [None, False, {"untouched": "原样"}]},
    } for index in range(1, 4)]


class OpaqueHistory(list):
    def __init__(self, *, forbid_copy: bool = False) -> None:
        super().__init__(_history_rows())
        self.forbid_copy = forbid_copy
        self.copy_attempts = 0

    def __deepcopy__(self, memo: dict[int, object]) -> list[object]:
        self.copy_attempts += 1
        if self.forbid_copy:
            raise AssertionError("opaque native history deepcopy is forbidden")
        result: list[object] = []
        memo[id(self)] = result
        result.extend(copy.deepcopy(row, memo) for row in self)
        return result


class FakeNativeTransport:
    def __init__(self) -> None:
        self.requests: list[dict[str, object]] = []

    def execute_step(self, step: str, *, expected_revision: int | None) -> dict[str, object]:
        self.requests.append({"step": step, "expected_revision": expected_revision})
        if step != STEP or expected_revision != REVISION:
            raise AssertionError("service changed the native RPC/revision binding")
        return _reply()


class SmallNativeDriver(NativeHeadlessGameplayDriver):
    """Use real snapshot/history-export methods with an in-memory native frame."""
    def __init__(self, *, poison_history: bool = False, drift_on_read: int | None = None) -> None:
        self._driver_state_lock = threading.RLock()
        self._history_lock = threading.RLock()
        self._rollback_war_failures = []
        self._command_history = OpaqueHistory(forbid_copy=poison_history)
        self.transport = FakeNativeTransport()
        self.semantic_frames: list[dict[str, object]] = []
        self.drift_on_read = drift_on_read
        self.raw_driver = {
            "format_version": 2, "pipe_name": "synthetic-service-history79",
            "bridge_pid": 123, "episode_character_id": PLAYER_ID,
            "episode_run_id": "native-service-history79", "last_checkpoint": None,
            "command_history": self._command_history, "rollback_war_failure": None,
            "rollback_war_failures": [], "managed_restore_transaction": None,
            "succession_expectation": None, "succession_lifecycle": None,
            "campaign_goal": None,
            "unknown_driver_extension": {"exact_order": ["third", "first", "third"], "raw_bits": "ffffffffffffffff"},
        }

    def capabilities(self) -> dict[str, object]:
        return {"action_steps": [STEP], "bridge_capabilities": [QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY]}

    def take_internal_semantic_snapshot(self) -> dict[str, object]:
        frame = _snapshot()
        if self.drift_on_read == len(self.semantic_frames) + 1:
            frame["native_revision"] = NATIVE_REVISION + 1
        self.semantic_frames.append(frame)
        return frame

    def execute_step(self, step: str, *, expected_revision: int | None = None) -> dict[str, object]:
        return self.transport.execute_step(step, expected_revision=expected_revision)


class ServiceQueryHistory79Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if OLD_SERVICE is not None and NEW_SERVICE is not None:
            return
        from xar_autoplayer.bridge import service as current_module

        current = current_module.GameplayBridgeService

        def prior_method(name: str, expected_calls: int):
            source = textwrap.dedent(inspect.getsource(getattr(current, name)))
            optimized_call = "self.snapshot(include_native_command_history=False)"
            if source.count(optimized_call) != expected_calls:
                raise AssertionError("service history79 control requires its exact three callsites")
            namespace = vars(current_module).copy()
            exec(compile(source.replace(optimized_call, "self.snapshot()"),
                         "service_history79_previous_calls", "exec"), namespace)
            return namespace[name]

        class PreviousCallService(current):
            pass

        PreviousCallService.query_campaign_root_context_v1 = prior_method("query_campaign_root_context_v1", 2)
        PreviousCallService.query_turn_bundle_v1 = prior_method("query_turn_bundle_v1", 1)
        temporary = tempfile.TemporaryDirectory(prefix="service-history79-unit-")
        cls.addClassCleanup(temporary.cleanup)
        configure_service_sources(PreviousCallService, current, Path(temporary.name))

    def check(self, name: str, condition: bool) -> None:
        self.assertTrue(condition, name)
        CHECKS.append({"group": self._testMethodName, "name": name, "passed": True})

    def equal(self, name: str, left: object, right: object) -> None:
        self.assertEqual(left, right, name)
        CHECKS.append({"group": self._testMethodName, "name": name, "passed": True})

    def query(self, service_type: type, method: str, *, poison: bool = False,
              drift_on_read: int | None = None) -> tuple[dict[str, object], SmallNativeDriver]:
        driver = SmallNativeDriver(poison_history=poison, drift_on_read=drift_on_read)
        result = getattr(service_type(driver), method)(expected_revision=REVISION)
        return result, driver

    def test_01_root_output_rpc_revision_and_independent_boundaries(self) -> None:
        old, old_driver = self.query(OLD_SERVICE, "query_campaign_root_context_v1")
        new, new_driver = self.query(NEW_SERVICE, "query_campaign_root_context_v1")
        self.equal("exact root output", new, old)
        self.equal("root is available", new["status"], "available")
        self.equal("root native RPCs", new_driver.transport.requests, old_driver.transport.requests)
        self.equal("one root RPC with original revision", new_driver.transport.requests,
                   [{"step": STEP, "expected_revision": REVISION}])
        self.equal("public revision unchanged", new["binding"]["revision"], REVISION)
        self.equal("high-bit native revision unchanged", new["binding"]["native_revision"], NATIVE_REVISION)
        self.equal("old root before/after reads", len(old_driver.semantic_frames), 2)
        self.equal("new root before/after reads", len(new_driver.semantic_frames), 2)
        self.check("root reads are independent", new_driver.semantic_frames[0] is not new_driver.semantic_frames[1])
        self.equal("old history clones calibrate both boundaries", old_driver._command_history.copy_attempts, 2)
        self.equal("new root history clones", new_driver._command_history.copy_attempts, 0)
        errors = []
        for service_type in (OLD_SERVICE, NEW_SERVICE):
            driver = SmallNativeDriver(drift_on_read=2)
            with self.assertRaises(BridgeUnavailableError) as caught:
                service_type(driver).query_campaign_root_context_v1(expected_revision=REVISION)
            errors.append(str(caught.exception))
            self.equal("drift retains two reads", len(driver.semantic_frames), 2)
            self.equal("drift retains one RPC", driver.transport.requests, [{"step": STEP, "expected_revision": REVISION}])
        self.equal("same root drift rejection", errors, ["campaign-root query crossed a snapshot revision"] * 2)
        GROUP_OBSERVATIONS["root"] = {"rpc": new_driver.transport.requests, "semantic_reads": 2,
                                      "old_history_clones": 2, "new_history_clones": 0,
                                      "native_revision": NATIVE_REVISION, "result": new}

    def test_02_bundle_output_rpc_revision_and_three_reads(self) -> None:
        old, old_driver = self.query(OLD_SERVICE, "query_turn_bundle_v1")
        new, new_driver = self.query(NEW_SERVICE, "query_turn_bundle_v1")
        self.equal("exact bundle output", new, old)
        self.equal("bundle schema", new["schema"], "xar.ck3.turn-bundle/v1")
        self.equal("existing council gap stays partial", new["status"], "partial")
        self.equal("bundle native RPCs", new_driver.transport.requests, old_driver.transport.requests)
        self.equal("one bundle RPC with original revision", new_driver.transport.requests,
                   [{"step": STEP, "expected_revision": REVISION}])
        self.equal("bundle revision unchanged", new["binding"]["revision"], REVISION)
        self.equal("bundle native revision unchanged", new["binding"]["native_revision"], NATIVE_REVISION)
        self.equal("old bundle reads", len(old_driver.semantic_frames), 3)
        self.equal("new bundle reads", len(new_driver.semantic_frames), 3)
        self.equal("all bundle reads remain independent", len({id(frame) for frame in new_driver.semantic_frames}), 3)
        self.equal("old bundle history clones", old_driver._command_history.copy_attempts, 3)
        self.equal("new bundle history clones", new_driver._command_history.copy_attempts, 0)
        GROUP_OBSERVATIONS["bundle"] = {"rpc": new_driver.transport.requests, "semantic_reads": 3,
                                        "old_history_clones": 3, "new_history_clones": 0, "result": new}

    def test_03_complete_driver_opaque_history_and_file_bytes_unchanged(self) -> None:
        for service_type in (OLD_SERVICE, NEW_SERVICE):
            driver = SmallNativeDriver()
            state_before = json.dumps(driver.raw_driver, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            history_identity = id(driver.raw_driver["command_history"])
            opaque_identity = id(driver.raw_driver["unknown_driver_extension"])
            row_identities = [id(row) for row in driver._command_history]
            with tempfile.TemporaryDirectory(prefix="service-history79-", dir=TEMP_ROOT) as directory:
                state_path = Path(directory) / "driver-state.synthetic.json"
                state_path.write_bytes(state_before)
                service = service_type(driver)
                for method in ("query_campaign_root_context_v1", "query_turn_bundle_v1"):
                    getattr(service, method)(expected_revision=REVISION)
                    self.equal("complete Driver object serialized unchanged",
                               json.dumps(driver.raw_driver, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), state_before)
                    self.equal("complete synthetic file bytes unchanged", state_path.read_bytes(), state_before)
                    self.equal("owned history identity preserved", id(driver.raw_driver["command_history"]), history_identity)
                    self.equal("opaque Driver extension identity preserved", id(driver.raw_driver["unknown_driver_extension"]), opaque_identity)
                    self.equal("opaque row identities/order preserved", [id(row) for row in driver._command_history], row_identities)
            self.equal("complete history remains three rows", len(driver._command_history), 3)
        GROUP_OBSERVATIONS["raw_driver"] = {"old_and_new_immutable": True, "synthetic_only": True,
                                           "complete_rows": 3, "opaque_extensions_preserved": True}

    def test_04_poison_history_calibration_and_existing_false_path(self) -> None:
        calibrated = SmallNativeDriver(poison_history=True)
        with self.assertRaisesRegex(AssertionError, "opaque native history deepcopy is forbidden"):
            OLD_SERVICE(calibrated).query_campaign_root_context_v1(expected_revision=REVISION)
        self.equal("poison rejects actual baseline history clone", calibrated._command_history.copy_attempts, 1)
        self.equal("poison calibration occurs before RPC", calibrated.transport.requests, [])
        for method, expected_reads in (("query_campaign_root_context_v1", 2), ("query_turn_bundle_v1", 3)):
            result, driver = self.query(NEW_SERVICE, method, poison=True)
            self.equal("optimized poison history remains untouched", driver._command_history.copy_attempts, 0)
            self.equal("optimized route still reads every boundary", len(driver.semantic_frames), expected_reads)
            self.equal("optimized route still issues exactly one RPC", driver.transport.requests,
                       [{"step": STEP, "expected_revision": REVISION}])
            self.equal("optimized poison result unchanged", result,
                       GROUP_OBSERVATIONS["root" if expected_reads == 2 else "bundle"]["result"])
        GROUP_OBSERVATIONS["poison_history"] = {"baseline_clone_rejected": True, "optimized_clone_attempts": 0,
                                               "root_reads": 2, "bundle_reads": 3,
                                               "native_false_path": "inherited NativeHeadlessGameplayDriver.take_snapshot_without_native_command_history -> take_snapshot(False)"}

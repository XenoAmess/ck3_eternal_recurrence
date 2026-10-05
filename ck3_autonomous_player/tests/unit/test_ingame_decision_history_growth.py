"""Production Confirm/history/persistence and official SDK growth regression.

The source outcome, history recorder, snapshot exporter, claim writer, profile
verifier and MCP SDK run unchanged. Only the native observations/dispatch and
machine guard are deterministic in-memory fixtures; no live endpoint is used.
Artifacts are create-only in the selected external test directory.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest

from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.ingame_decisions_open_contract import EXE_SHA256, opening_binding
from xar_autoplayer.bridge.service import GameplayBridgeService
from test_ingame_decision_outcomes import OutcomeDriver, outcome_ack, KEY, EVENT_KEY, STEP


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def history_depth(value, depth=0):
    if isinstance(value, dict):
        return max([depth if isinstance(value.get("native_command_history"), list)
                    and value["native_command_history"] else 0]
                   + [history_depth(item, depth + 1) for item in value.values()])
    if isinstance(value, list):
        return max([0] + [history_depth(item, depth + 1) for item in value])
    return 0


def artifact_directory(label):
    parent = os.environ.get("XAR_HISTORY_GROWTH_TEST_ARTIFACTS")
    if parent:
        Path(parent).mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=label + "-", dir=parent))


def preserve(path, value):
    with path.open("xb") as stream:
        stream.write(encoded(value) + b"\n")


class NoIOEndpoint:
    def start(self, on_frame, on_disconnect):
        self.on_frame, self.on_disconnect = on_frame, on_disconnect
    def send(self, frame):
        raise RuntimeError("Growth fixture cannot send to a game or pipe")
    def close(self):
        pass
    def transport_error(self):
        return None


class GrowthDriver(NativeHeadlessGameplayDriver):
    """Use the actual driver-owned transcript, exporter and atomic persistence."""
    capabilities = OutcomeDriver.capabilities
    _execute_primitive_step = OutcomeDriver._execute_primitive_step
    query_ingame_decision_item_v1 = OutcomeDriver.query_ingame_decision_item_v1
    query_current_event_window_context_v1 = OutcomeDriver.query_current_event_window_context_v1
    inspect_gui_window_tree_v1 = OutcomeDriver.inspect_gui_window_tree_v1

    def __init__(self, directory, outcome):
        super().__init__(endpoint=NoIOEndpoint(), state_dir=directory,
                         episode_projection="native_campaign")
        OutcomeDriver.__init__(self, directory, outcome)
        self.frame["episode_projection"] = "native_campaign"
        self.frame["diagnostics"]["bridge_pid"] = 12700
        self.frame["diagnostics"]["hello"]["game_adapter_status"] = "ready"
        self._session_bridge_pid = 12700
        self._episode_character_id = self.frame["played_character"]["character_id"]
        self._episode_run_id = self.frame["episode_run_id"]
        self.original_files = {}

    def take_internal_semantic_snapshot(self):
        return deepcopy(self.frame)

    def prepare(self):
        self.frame["active_event"] = None
        self.selected = True
        self.native_ack = outcome_ack(opening_binding(self.frame), self.outcome)


class GrowthTests(unittest.TestCase):
    def run_rounds(self, outcome, rounds, *, legacy_ending=False):
        folder = artifact_directory(("legacy" if legacy_ending else "candidate") + "-" + outcome)
        driver = GrowthDriver(folder, outcome)
        if legacy_ending:
            # Restore precisely the old ending exporter while keeping every
            # other production function identical, for the measured control.
            driver.take_snapshot_without_native_command_history = driver.take_snapshot
        metrics = []
        prefix = []
        for number in range(1, rounds + 1):
            driver.prepare()
            started = time.perf_counter()
            result = driver.confirm_ingame_decision_outcome_v1(KEY, outcome,
                expected_event_definition_key=EVENT_KEY if outcome == "event_window" else None,
                expected_revision=driver.frame["revision"])
            snapshot = driver.take_snapshot()
            persisted = json.loads(driver._native_driver_state_path().read_text(encoding="utf-8"))
            self.assertEqual(snapshot["native_command_history"][:-1], prefix)
            self.assertEqual(persisted["command_history"], snapshot["native_command_history"])
            self.assertEqual(snapshot["native_command_history"][-1],
                             {"index": number, "command": STEP, "ok": True, "result": result})
            self.assertEqual(len(driver.submissions), number)
            self.assertIsNone(driver._driver_state_error)
            if not legacy_ending:
                ending = result["snapshot_after"]
                self.assertEqual(ending["native_command_history"], [])
                self.assertEqual(ending["native_command_history_export"],
                                 {"mode": "omitted", "total_count": number - 1, "included_count": 0})
                self.assertEqual(ending["diagnostics"], driver.frame["diagnostics"])
                semantic = {key: value for key, value in ending.items()
                            if key not in {"native_command_history", "native_command_history_export",
                                           "native_rollback_war_failure", "native_rollback_war_failures"}}
                self.assertEqual(semantic, driver.take_internal_semantic_snapshot())
                self.assertEqual(history_depth(snapshot), 0)
                self.assertIs(result["business_effects_verified"], False)
                self.assertIs(result["full_product_acceptance_credit"], False)
                for field in ("owner_thread_verified", "frame_verified", "source_abi_pins_verified",
                              "action_abi_pins_verified", "receiver_qualified", "native_call_completed"):
                    self.assertIs(result["native_ack"][field], True)
            claim = Path(result["action_claim_path"])
            sidecars = [claim, claim.with_suffix(".result.json"), claim.with_suffix(".verified.json")]
            for path in sidecars:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                driver.original_files.setdefault(str(path), digest)
                self.assertEqual(driver.original_files[str(path)], digest)
            preserve(folder / f"round-{number:03d}.result.json", result)
            metrics.append({"round": number, "result_bytes": len(encoded(result)),
                "snapshot_bytes": len(encoded(snapshot)),
                "driver_state_bytes": driver._native_driver_state_path().stat().st_size,
                "history_count": len(snapshot["native_command_history"]),
                "populated_history_max_depth": history_depth(snapshot),
                "elapsed_seconds": time.perf_counter() - started})
            prefix = deepcopy(snapshot["native_command_history"])
        for path, digest in driver.original_files.items():
            self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(), digest)
        preserve(folder / "sidecar-sha256.json", driver.original_files)
        preserve(folder / "growth.json", {"mode": "legacy" if legacy_ending else "candidate",
            "outcome": outcome, "rounds": metrics, "native_io": "NOT_RUN"})
        return metrics

    def test_64_closed_confirms_keep_all_history_and_proof_with_linear_bytes(self):
        metrics = self.run_rounds("decision_closed", 64)
        self.assertLess(max(row["result_bytes"] for row in metrics), metrics[0]["result_bytes"] * 1.02)
        self.assertLess(metrics[63]["driver_state_bytes"], metrics[7]["driver_state_bytes"] * 8.02)
        self.assertLess(metrics[63]["snapshot_bytes"], metrics[7]["snapshot_bytes"] * 8.02)

    def test_64_event_confirms_keep_full_actual_event_state_and_linear_bytes(self):
        metrics = self.run_rounds("event_window", 64)
        self.assertLess(max(row["result_bytes"] for row in metrics), metrics[0]["result_bytes"] * 1.02)
        self.assertLess(metrics[63]["driver_state_bytes"], metrics[7]["driver_state_bytes"] * 8.02)

    def test_same_production_recorder_reproduces_old_exponential_ending(self):
        metrics = self.run_rounds("decision_closed", 8, legacy_ending=True)
        self.assertGreater(metrics[-1]["result_bytes"], metrics[-2]["result_bytes"] * 1.8)
        self.assertGreater(metrics[-1]["driver_state_bytes"], metrics[0]["driver_state_bytes"] * 100)
        self.assertGreater(metrics[-1]["populated_history_max_depth"], 20)


class OfficialSDKGrowthTests(unittest.IsolatedAsyncioTestCase):
    async def test_32_profile_confirms_preserve_native_receipts_and_official_sdk_fields(self):
        from mcp import Client
        import ck3_native_profile_mcp as native
        folder = artifact_directory("official-sdk")
        driver = GrowthDriver(folder / "native-state", "decision_closed")
        driver.directory.mkdir()
        profile = {"guard": {"target": {"pid": 12700, "executable_sha256": EXE_SHA256}},
            "game_version": "1.20.0.3", "profile_sha256": "1" * 64,
            "evidence_directory": str(folder / "native-receipts")}
        service = native.NativeProfileService(profile, backend=SimpleNamespace(poll=lambda _: {}))
        service.guard = lambda: {"game_pid": 12700, "fixture": "in-memory-only"}
        service.driver = driver
        service._attach_result = {"status": "attached_snapshot_verified"}
        service._gameplay = GameplayBridgeService(driver)
        metrics, previous_history, originals = [], [], {}
        async with Client(native.create_server(service), cache=None) as client:
            inventory = (await client.list_tools()).model_dump(mode="json", by_alias=True, exclude_none=False)
            preserve(folder / "tools.json", inventory)
            for number in range(1, 33):
                driver.prepare()
                started = time.perf_counter()
                sdk = await client.call_tool("ck3_confirm_profile_decision_outcome_v1", {
                    "decision_key": KEY, "expected_outcome": "decision_closed",
                    "expected_revision": driver.frame["revision"]}, read_timeout_seconds=60)
                self.assertFalse(sdk.is_error, str(sdk))
                payload = sdk.model_dump(mode="json", by_alias=True, exclude_none=False)
                data = sdk.structured_content
                self.assertEqual(data["status"], "native_gameplay_postcondition_verified")
                self.assertEqual(data["snapshot_before"]["native_command_history"], previous_history)
                history = data["snapshot_after"]["native_command_history"]
                self.assertEqual(history[:-1], previous_history)
                self.assertEqual(len(history), number)
                self.assertEqual(data["result"]["snapshot_after"]["native_command_history"], [])
                self.assertEqual(data["result"]["snapshot_after"]["diagnostics"], driver.frame["diagnostics"])
                self.assertEqual(json.loads(sdk.content[0].text), data)
                receipt = Path(data["receipt_path"])
                self.assertEqual(json.loads(receipt.read_text(encoding="utf-8")), data)
                originals[str(receipt)] = hashlib.sha256(receipt.read_bytes()).hexdigest()
                preserve(folder / f"round-{number:03d}.sdk-result.json", payload)
                metrics.append({"round": number, "sdk_bytes": len(encoded(payload)),
                    "receipt_bytes": receipt.stat().st_size, "history_count": number,
                    "elapsed_seconds": time.perf_counter() - started})
                previous_history = deepcopy(history)
        for path, digest in originals.items():
            self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(), digest)
        preserve(folder / "receipt-sha256.json", originals)
        preserve(folder / "growth.json", {"rounds": metrics, "client": "official mcp.Client(cache=None)",
            "transport": "in-memory server; real process/pipe/UI NOT_RUN"})
        self.assertLess(metrics[31]["sdk_bytes"], metrics[7]["sdk_bytes"] * 4.1)
        self.assertLess(metrics[31]["elapsed_seconds"], 60)


if __name__ == "__main__":
    unittest.main()

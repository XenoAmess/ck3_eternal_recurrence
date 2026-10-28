"""Synthetic opening proof and durable one-claim regressions; never use a game endpoint."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
import hashlib
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.ingame_decisions_open_contract import (
    CAPABILITY, EXE_SHA256, STEP, opening_binding, normalize_sdk_open_result,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


def snapshot():
    return {"revision": 1, "native_revision": 7, "snapshot_id": "synthetic-paused-7",
            "episode_run_id": "synthetic-opener-episode", "paused": True, "map_ready": True,
            "date_raw": 1234, "played_character": {"character_id": 7001, "alive": True},
            "diagnostics": {"connection_generation": 1, "pid": 99999,
                            "hello": {"pid": 12700, "ck3_build_match": True,
                                      "game_adapter_id": "ck3-1.20.0.3-msvc-x64",
                                      "expected_ck3_version": "1.20.0.3",
                                      "expected_ck3_sha256": EXE_SHA256}}}


def pending_native_ack():
    return {"schema": "ck3-ingame-decisions-open-v1", "step": STEP, "game_version": "1.20.0.3",
            "executable_sha256": EXE_SHA256, "native_revision": 7,
            "connection_generation": 1, "game_pid": 12700, "played_character_id": 7001,
            "date_raw": 1234, "owner_thread_verified": True, "frame_verified": True,
            "source_abi_pins_verified": True, "gui_owner_binding_verified": True,
            "native_after_read": True, "before_visible": False, "dispatch_invoked": True,
            "topbar_tree_complete": True, "receiver_qualified": True,
            "native_after_visible": False, "native_after_tree_complete": False,
            "postcondition_verified": False, "verification_pending": True}


def decisions_tree(visible: bool) -> dict[str, object]:
    return {"schema": "ck3-native-gui-window-tree-inspection-v1", "window_kind": "decisions",
            "accepted": True, "status": "available", "read_only": True, "widget_count": 1,
            "scope_root_name": "decisions_view", "root_available": True, "truncated": False,
            "widgets": [{"child_path": "", "runtime_name": "decisions_view", "effective_visible": visible}]}


class SyntheticDriver:
    open_ingame_decisions_v1 = NativeHeadlessGameplayDriver.open_ingame_decisions_v1

    def __init__(self, state_directory, *, frame=None, ack=None, action_error=None):
        self.frame = deepcopy(snapshot() if frame is None else frame)
        self.ack = deepcopy(pending_native_ack() if ack is None else ack)
        self.state_directory = Path(state_directory)
        self.action_error = action_error
        self.submissions = []
        self.queries = []
        self.records = []
        self.visible = False

    def take_snapshot(self): return deepcopy(self.frame)
    def capabilities(self): return {"bridge_capabilities": [CAPABILITY]}
    def _native_driver_state_path(self): return self.state_directory / "synthetic-state.json"
    def _record_command(self, *args, **kwargs): self.records.append((args, kwargs))

    def _execute_primitive_step(self, step, **kwargs):
        self.submissions.append((step, kwargs))
        if self.action_error is not None:
            raise self.action_error
        self.visible = True
        return deepcopy(self.ack)

    def inspect_gui_window_tree_v1(self, kind):
        self.queries.append(kind)
        return decisions_tree(self.visible)


class DecisionsOpeningProofTests(unittest.TestCase):
    def state_directory(self):
        parent = os.environ.get("XAR_WHITE_DECISIONS_TEST_ARTIFACTS")
        if parent:
            Path(parent).mkdir(parents=True, exist_ok=True)
        # Preserve synthetic claims for inspection; no old runtime/state path is used.
        return Path(tempfile.mkdtemp(prefix="synthetic-claim-", dir=parent))

    def test_invalid_actual_binding_rejects_before_claim_or_submission(self):
        for invalid in ("hash", "dead", "revision", "missing_game_pid"):
            with self.subTest(invalid=invalid):
                frame = snapshot()
                if invalid == "hash": frame["diagnostics"]["hello"]["expected_ck3_sha256"] = "0" * 64
                if invalid == "dead": frame["played_character"]["alive"] = False
                if invalid == "revision": frame["native_revision"] = True
                if invalid == "missing_game_pid": del frame["diagnostics"]["hello"]["pid"]
                driver = SyntheticDriver(self.state_directory(), frame=frame)
                with self.assertRaises(BridgeUnavailableError): driver.open_ingame_decisions_v1()
                self.assertEqual(driver.submissions, [])
                self.assertEqual(driver.queries, [])
                self.assertFalse((driver.state_directory / "ingame-decisions-opener-actions").exists())

    def test_invalid_native_proof_consumes_one_claim_and_cannot_be_retried(self):
        for invalid in ("game_pid", "gui_owner_binding_verified", "native_after_read"):
            with self.subTest(invalid=invalid):
                ack = pending_native_ack()
                ack[invalid] = 99999 if invalid == "game_pid" else False
                driver = SyntheticDriver(self.state_directory(), ack=ack)
                with self.assertRaises(ValueError): driver.open_ingame_decisions_v1()
                self.assertEqual(len(driver.submissions), 1)
                self.assertEqual(driver.queries, ["decisions"])
                with self.assertRaisesRegex(BridgeUnavailableError, "already claimed"):
                    driver.open_ingame_decisions_v1()
                self.assertEqual(len(driver.submissions), 1)

    def test_lost_ack_is_not_queried_or_resubmitted_even_after_reconnect(self):
        directory = self.state_directory()
        driver = SyntheticDriver(directory, action_error=TimeoutError("synthetic lost ACK"))
        with self.assertRaises(TimeoutError): driver.open_ingame_decisions_v1()
        self.assertEqual(len(driver.submissions), 1)

        self.assertEqual(driver.queries, ["decisions"])
        claim_files = list((directory / "ingame-decisions-opener-actions").glob("*.claim.json"))
        self.assertEqual(len(claim_files), 1)
        claim = json.loads(claim_files[0].read_text(encoding="utf-8"))
        self.assertEqual(claim["status"], "claimed_result_unknown_no_retry")
        self.assertEqual(claim["request_id"], driver.submissions[0][1]["protocol_request_id"])
        self.assertEqual(list(claim_files[0].parent.glob("*.result.json")), [])
        reconnect_frame = snapshot()
        reconnect_frame["diagnostics"]["connection_generation"] = 2
        reconnected = SyntheticDriver(directory, frame=reconnect_frame)
        with self.assertRaisesRegex(BridgeUnavailableError, "already claimed"):
            reconnected.open_ingame_decisions_v1()
        self.assertEqual(reconnected.submissions, [])

    def test_pending_ack_needs_independent_current_visible_root(self):
        driver = SyntheticDriver(self.state_directory())
        result = driver.open_ingame_decisions_v1(expected_revision=1)
        self.assertEqual(len(driver.submissions), 1)
        self.assertEqual(driver.queries, ["decisions", "decisions"])
        self.assertFalse(result["native_ack"]["postcondition_verified"])
        self.assertTrue(result["postcondition_verified"])
        self.assertFalse(result["verification_pending"])
        self.assertEqual(result["later_decisions_tree"]["scope_root_name"], "decisions_view")
        self.assertEqual(driver.submissions[0][1]["request_fields"]["expected_game_pid"], 12700)
        observed = driver.open_ingame_decisions_v1()
        self.assertEqual(observed["proof_kind"], "current_visibility")
        self.assertIsNone(observed["native_ack"])
        self.assertEqual(len(driver.submissions), 1)

    def legacy_visible_claim(self, directory: Path) -> Path:
        """Write the actual v1 shape: observed visible, no GUI dispatch."""
        binding = opening_binding(snapshot())
        identity = {"game_pid": binding["game_pid"], "actor_id": binding["played_character_id"],
                    "episode_run_id": binding["episode_run_id"], "decision_key": "", "action": "open",
                    "public_revision": 1}
        parent = directory / "ingame-decisions-opener-actions"
        parent.mkdir()
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        claim = parent / (key + ".claim.json")
        request = "decisions-" + "a" * 32
        ack = pending_native_ack()
        ack.update(before_visible=True, dispatch_invoked=False, native_after_visible=True,
                   native_after_tree_complete=True, postcondition_verified=True, verification_pending=False)
        result = {**ack, "native_ack": ack, "status": "verified_visible",
                  "postcondition_verified": True, "verification_pending": False,
                  "action_request_id": request, "action_claim_path": str(claim),
                  "episode_run_id": binding["episode_run_id"], "queried_revision": 1,
                  "later_decisions_tree": decisions_tree(True),
                  "uses_mouse": False, "uses_keyboard": False, "uses_ocr": False}
        for path, value in (
            (claim, {"schema": "ck3-ingame-decisions-once-claim-v1", "request_id": request,
                     "binding": binding, "action_identity": identity, "status": "claimed_result_unknown_no_retry"}),
            (claim.with_suffix(".result.json"), {"request_id": request, "raw": ack}),
            (claim.with_suffix(".verified.json"), {"schema": "ck3-ingame-decision-action-independent-verification-v1",
                                                   "request_id": request, "result": result})):
            path.write_text(json.dumps(value), encoding="utf-8")
        return claim

    def test_real_no_dispatch_legacy_success_then_same_frame_visible_is_read_only(self) -> None:
        directory = self.state_directory()
        claim = self.legacy_visible_claim(directory)
        original = claim.read_bytes()
        driver = SyntheticDriver(directory)
        driver.visible = True
        result = driver.open_ingame_decisions_v1(expected_revision=1)
        self.assertEqual(result["proof_kind"], "current_visibility")
        self.assertTrue(result["read_only"])
        self.assertIsNone(result["native_ack"])
        self.assertIsNone(result["action_request_id"])
        self.assertEqual(driver.submissions, [])
        self.assertEqual(claim.read_bytes(), original)
        self.assertEqual(len(list(claim.parent.glob("*.claim.json"))), 1)

    def test_verified_legacy_hidden_reopens_once_without_revision_or_date_change(self) -> None:
        directory = self.state_directory()
        claim = self.legacy_visible_claim(directory)
        original = claim.read_bytes()
        driver = SyntheticDriver(directory)
        first = driver.open_ingame_decisions_v1(expected_revision=1)
        self.assertEqual(first["proof_kind"], "native_open")
        new = json.loads(Path(first["action_claim_path"]).read_text(encoding="utf-8"))
        self.assertEqual(new["parent_request_id"], "decisions-" + "a" * 32)
        self.assertEqual(new["parent"]["claim"]["path"], str(claim))
        driver.open_ingame_decisions_v1(expected_revision=1)
        self.assertEqual(len(driver.submissions), 1)
        driver.visible = False
        second = driver.open_ingame_decisions_v1(expected_revision=1)
        self.assertNotEqual(second["action_claim_path"], first["action_claim_path"])
        self.assertEqual(len(driver.submissions), 2)
        self.assertEqual(claim.read_bytes(), original)

    def test_fresh_visible_without_history_creates_no_action_claim(self) -> None:
        driver = SyntheticDriver(self.state_directory())
        driver.visible = True
        result = driver.open_ingame_decisions_v1()
        self.assertEqual(result["status"], "observed_visible_read_only")
        self.assertEqual(driver.submissions, [])
        self.assertEqual(list((driver.state_directory / "ingame-decisions-opener-actions").glob("*.claim.json")), [])

    def test_unknown_blocks_even_current_visible_at_new_revision_and_reconnect(self) -> None:
        driver = SyntheticDriver(self.state_directory(), action_error=TimeoutError("unknown"))
        with self.assertRaises(TimeoutError): driver.open_ingame_decisions_v1()
        driver.frame.update(revision=10, native_revision=17)
        driver.frame["diagnostics"]["connection_generation"] = 2
        driver.visible, driver.action_error = True, None
        count = len(driver.queries)
        with self.assertRaisesRegex(BridgeUnavailableError, "unresolved"):
            driver.open_ingame_decisions_v1(expected_revision=10)
        self.assertEqual(len(driver.queries), count)
        self.assertEqual(len(driver.submissions), 1)

    def test_incomplete_or_false_like_hidden_census_never_creates_claim(self) -> None:
        from copy import deepcopy
        for mutation in (
            lambda t: t.update(root_available=False), lambda t: t.update(truncated=True),
            lambda t: t.update(widget_count=True), lambda t: t.update(widget_count=2),
            lambda t: t.update(widgets=[]), lambda t: t.update(scope_root_name="foreign"),
            lambda t: t["widgets"][0].update(effective_visible=0),
            lambda t: t.update(widgets=t["widgets"] * 2, widget_count=2),
            lambda t: t.pop("read_only")):
            driver = SyntheticDriver(self.state_directory())
            tree = deepcopy(decisions_tree(False))
            mutation(tree)
            driver.inspect_gui_window_tree_v1 = lambda kind: deepcopy(tree)
            with self.assertRaises(BridgeUnavailableError): driver.open_ingame_decisions_v1()
            self.assertEqual(driver.submissions, [])
            self.assertEqual(list((driver.state_directory / "ingame-decisions-opener-actions").glob("*.claim.json")), [])

    def test_visible_result_contract_rejects_missing_wrong_and_bool_fields(self) -> None:
        driver = SyntheticDriver(self.state_directory())
        driver.visible = True
        result = dict(driver.open_ingame_decisions_v1())
        for field, bad in (("native_revision", True), ("queried_revision", 1.0),
                           ("native_ack", {}), ("dispatch_invoked", 0),
                           ("proof_kind", "cached_ack"), ("episode_run_id", False)):
            row = {**result, field: bad}
            with self.assertRaises(ValueError): normalize_sdk_open_result(row)
        for field in ("native_ack", "postcondition_verified", "proof_kind"):
            row = dict(result); row.pop(field)
            with self.assertRaises(ValueError): normalize_sdk_open_result(row)
        self.assertEqual(normalize_sdk_open_result(json.loads(json.dumps(result))), result)

    def test_tampered_verified_parent_is_not_reopened(self) -> None:
        directory = self.state_directory()
        claim = self.legacy_visible_claim(directory)
        path = claim.with_suffix(".verified.json")
        value = json.loads(path.read_text(encoding="utf-8"))
        value["result"]["native_ack"]["owner_thread_verified"] = False
        path.write_text(json.dumps(value), encoding="utf-8")
        driver = SyntheticDriver(directory)
        with self.assertRaises(BridgeUnavailableError): driver.open_ingame_decisions_v1()
        self.assertEqual(driver.submissions, [])

    def test_reopen_continues_in_independent_python_process(self) -> None:
        directory = self.state_directory()
        self.legacy_visible_claim(directory)
        code = ("import json,sys; from test_ingame_decisions_open_contract import SyntheticDriver; "
                "d=SyntheticDriver(sys.argv[1]); r=d.open_ingame_decisions_v1(expected_revision=1); "
                "print(json.dumps({'kind':r['proof_kind'],'calls':len(d.submissions)}))")
        for _ in range(2):
            child = subprocess.run([sys.executable, "-B", "-X", "utf8", "-c", code, str(directory)],
                                   capture_output=True, text=True, encoding="utf-8", timeout=30, check=False)
            self.assertEqual(child.returncode, 0, child.stderr)
            self.assertEqual(json.loads(child.stdout), {"kind": "native_open", "calls": 1})
        self.assertEqual(len(list((directory / "ingame-decisions-opener-actions").glob("*.claim.json"))), 3)

    def test_same_parent_race_creates_only_one_native_dispatch(self) -> None:
        directory = self.state_directory()
        self.legacy_visible_claim(directory)
        barrier = threading.Barrier(2)
        class Racing(SyntheticDriver):
            def inspect_gui_window_tree_v1(self, kind):
                if not self.submissions: barrier.wait(timeout=10)
                return super().inspect_gui_window_tree_v1(kind)
        drivers = [Racing(directory), Racing(directory)]
        def invoke(driver):
            try:
                driver.open_ingame_decisions_v1()
                return "ok"
            except BridgeUnavailableError:
                return "rejected"
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(invoke, drivers))
        self.assertEqual(sorted(outcomes), ["ok", "rejected"])
        self.assertEqual(sum(len(d.submissions) for d in drivers), 1)

    def test_service_revalidates_current_visibility_and_native_action_branches(self) -> None:
        from xar_autoplayer.bridge.service import GameplayBridgeService
        driver = SyntheticDriver(self.state_directory())
        service = GameplayBridgeService(driver)
        native = service.open_ingame_decisions_v1(expected_revision=1)
        self.assertEqual(native["proof_kind"], "native_open")
        current = service.open_ingame_decisions_v1(expected_revision=1)
        self.assertEqual(current["proof_kind"], "current_visibility")
        driver.open_ingame_decisions_v1 = lambda **kwargs: {**current, "native_ack": native["native_ack"]}
        with self.assertRaises(BridgeUnavailableError):
            service.open_ingame_decisions_v1(expected_revision=1)
        self.assertEqual(len(driver.submissions), 1)

    def test_registered_mcp_serializes_both_exact_sdk_branches(self) -> None:
        import asyncio
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server
        driver = SyntheticDriver(self.state_directory())
        async def exercise() -> None:
            async with Client(create_server(driver)) as client:
                first = await client.call_tool("ck3_open_ingame_decisions_v1", {"expected_revision": 1})
                self.assertFalse(first.is_error)
                self.assertEqual(first.structured_content["proof_kind"], "native_open")
                second = await client.call_tool("ck3_open_ingame_decisions_v1", {"expected_revision": 1})
                self.assertFalse(second.is_error)
                self.assertEqual(second.structured_content["proof_kind"], "current_visibility")
                self.assertIsNone(second.structured_content["native_ack"])
                invalid = await client.call_tool("ck3_open_ingame_decisions_v1", {"expected_revision": True})
                self.assertTrue(invalid.is_error)
        asyncio.run(exercise())
        self.assertEqual(len(driver.submissions), 1)

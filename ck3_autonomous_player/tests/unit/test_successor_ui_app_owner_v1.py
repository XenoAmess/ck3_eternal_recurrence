"""Registered MCP -> real Service/dispatcher -> synthetic driver -> real Queue.

All frames, OS identities and native results are synthetic. No Game is opened,
queried or changed, and none of these tests awards runtime succession credit.
"""
from copy import deepcopy
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from mcp import Client
from test_verified_successor_ui_service_v1 import SourceDriver, goal
from test_successor_ui_pending_ledger_v1 import verification
from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge import successor_ui_app_owner_v1 as app
from xar_autoplayer import successor_ui_pending_ledger_v1 as journal
from xar_autoplayer.strategy import continue_ordinary_campaign_goal_v1
from xar_autoplayer.vanilla_events.unhandled_fallback import plan_unhandled_event_fallback_v1

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("_m7_app_owner_queue", ROOT / "tools/g2_saved_campaign/m7_ordinary_successor_queue.py")
queue_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue_module)

class Driver(SourceDriver):
    def __init__(self, root):
        super().__init__()
        self.state_dir = Path(root)
        self.allow_private_death_succession_modal_continue = True
        self.allow_private_current_timeline_blocker_query = True
        self._succession_lifecycle = {
            "schema": "xar.ck3.succession-lifecycle-binding/v1", "lifecycle": "ordinary_campaign_succession",
            "xar_enabled": "xar_off", "pact_contract": "synthetic-no-pact", "source": "synthetic",
            "environment_sha256": "a" * 64}
        self.frame["succession_lifecycle"] = deepcopy(self._succession_lifecycle)
        self.frame["active_event"].update(option_count=1, options=[{"option_number": 1, "enabled": True}])
        self.post = deepcopy(self.frame)
        self.continues = self.saves = self.ordinary = self.snapshot_reads = self.cap_reads = 0
        self.continue_dispatch_attempts = 0
        self.continue_failure_mode = None
        self.order = []
        self.fail_persist = self.bad_goal = self.bad_post = False
        self.result = verification(self)["result"]
        self.result.update({key: self.frame[key] for key in ("snapshot_id", "revision", "date_raw")})
        self.result["reconciliation"]["predecessor_binding"] = deepcopy(self.proof["predecessor_binding"])
        self.result["succession_lifecycle"] = deepcopy(self._succession_lifecycle)
        self.result["original_extra"] = {"opaque": [1, 2, "keep original complete receipt"]}
        self.frame.update(episode_run_id="synthetic-predecessor", episode_character_id=19,
                          one_life_terminal=True, one_life_terminal_reason="played_character_changed")
        self.frame["campaign_goal"] = goal(19)
        self.frame["campaign_goal"]["progress"]["reconciled_successions"] = 0
        self.post["campaign_goal"] = continue_ordinary_campaign_goal_v1(self.frame["campaign_goal"], self.result["reconciliation"])

    def take_snapshot(self):
        self.snapshot_reads += 1
        return deepcopy(self.frame)

    take_snapshot_without_native_command_history = take_snapshot

    def capabilities(self):
        self.cap_reads += 1
        return {"backend_id": "synthetic-private", "action_steps": [app.STEP, "select-event-option-1", "save-checkpoint", "unpause"],
                "diagnostics": deepcopy(self.frame["diagnostics"]),
                "native_session_control": {"episode_binding_state": "active_natural_successor" if self.continues else "terminal",
                    "driver_state_restore_kind": "natural_succession" if self.continues else None}}

    def execute_step(self, step, *, expected_revision):
        if expected_revision != self.frame["revision"]:
            raise ValueError("synthetic stale revision")
        self.order.append("execute:" + step)
        if step == app.STEP:
            self.continue_dispatch_attempts += 1
            self.assert_intent()
            if self.continue_failure_mode == "before_apply":
                raise BridgeUnavailableError("synthetic original Continue throw before apply")
            self.continues += 1
            self.frame = deepcopy(self.post)
            if self.continue_failure_mode == "after_apply_unknown":
                raise BridgeUnavailableError("synthetic original Continue unknown after apply")
            result = deepcopy(self.result)
            if self.bad_goal:
                self.frame["campaign_goal"]["progress"]["reconciled_successions"] += 1
            if self.bad_post:
                self.frame["native_revision"] += 1
            if self.fail_persist:
                result["driver_state_persistence_diagnostic"] = {"status": "failed", "error": "synthetic disk failure"}
            return result
        if step == "select-event-option-1":
            assert self.event["root_scope"]["typed_identity"]["character_id"] == 19
            self.event_finished()
            return {"step": step, "accepted": True, "status": "completed", "event_selection": {
                "status": "event_instance_advanced", "postcondition_verified": True,
                "old_event_instance_id": 47, "new_event_instance_id": None, "selected_native_option_index": 0}}
        if step == "save-checkpoint":
            self.saves += 1
            return {"step": step, "accepted": True, "checkpoint": {"status": "saved",
                "date_raw": self.frame["date_raw"], "episode_run_id": self.frame["episode_run_id"],
                "episode_character_id": self.frame["episode_character_id"],
                "succession_lifecycle": self.frame["succession_lifecycle"]}}
        self.ordinary += 1
        return {"step": step, "accepted": True, "status": "completed"}

    def assert_intent(self):
        value = json.loads((self.state_dir / journal.FILE).read_text(encoding="utf-8"))
        assert value["status"] == "handoff_unverified"
        self.order.append("preintent-observed-before-driver")

    def continue_death_succession_modal_private_v1(self, **arguments):
        intents = list(self.state_dir.glob("successor-ui-close-*.json"))
        assert len(intents) == 1
        assert json.loads(intents[0].read_text(encoding="utf-8"))["status"] == "UNKNOWN"
        self.order.append("close-intent-observed-before-driver")
        return super().continue_death_succession_modal_private_v1(**arguments)

def planned(service):
    driver = service.driver
    frame = deepcopy(driver.frame)
    if frame.get("one_life_terminal") is True:
        plan = {"selected_step": app.STEP, "phase": "synthetic-natural-terminal"}
    elif frame.get("active_event") is not None:
        context = deepcopy(driver.event)
        context.update(snapshot_revision=frame["native_revision"], date_raw=frame["date_raw"])
        plan = plan_unhandled_event_fallback_v1(snapshot=frame, event_context=context,
            event_summary=frame["active_event"], registry_decision={"status": "uncovered"},
            action_steps=["select-event-option-1"])
    else:
        plan = {"selected_step": "unpause", "phase": "synthetic-ordinary"}
    return {"snapshot_id": frame["snapshot_id"], "revision": frame["revision"], "plan": plan,
            "planning_source_frame": service._observed_planning_source_frame(frame)}

class RegisteredQueue:
    """The real synchronous Queue consumer calls the registered MCP Client."""
    def __init__(self, client, loop, root):
        self.client, self.loop, self.root, self.number = client, loop, Path(root), 0

    def call(self, name, arguments, kind):
        response = asyncio.run_coroutine_threadsafe(self.client.call_tool(name, arguments), self.loop).result(timeout=8)
        if response.is_error:
            raise ValueError(str(response))
        payload = response.structured_content
        self.number += 1
        path = self.root / (f"{self.number:03}-{kind}.json")
        path.write_text(json.dumps(payload), encoding="utf-8")
        return payload, path

    def thin(self, kind, payload):
        path = self.root / (kind + ".json")
        path.write_text(json.dumps(payload), encoding="utf-8")

class AppOwnerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="successor-app-software-")
        self.root = Path(self.temp.name)
        self.driver = Driver(self.root)
        self.patches = [patch.object(app, "_machine_id", return_value="synthetic-App-machine"),
                        patch.object(app, "_game_identity", side_effect=lambda snapshot: {
                            "pid": snapshot["diagnostics"]["bridge_pid"], "creation_date": "synthetic-original-birth",
                            "executable": "synthetic/ck3.exe"}),
                        patch.object(GameplayBridgeService, "plan_turn", planned)]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    async def call(self, client, name, args=None, *, error=False):
        response = await client.call_tool(name, args or {})
        self.assertEqual(response.is_error, error, str(response))
        return response.structured_content

    async def test_same_app_full_continue_old_root_unknown_event_close_save_and_following_turn(self):
        def display(candidate):
            self.driver.order.append("display-ack:" + candidate["selected_step"])
            if candidate["selected_step"] == app.STEP:
                if self.driver.continues == 0:
                    self.assertFalse((self.root / journal.FILE).exists())
                else:
                    self.assertEqual(json.loads((self.root / journal.FILE).read_text(encoding="utf-8"))["status"], "resolved")
            elif candidate["selected_step"] == "continue-death-succession-modal-v1":
                self.assertEqual(list(self.root.glob("successor-ui-close-*.json")), [])
        server = mcp_server.create_server(self.driver, before_auto_turn_submit=display)
        async with Client(server) as client:
            turns = []
            queue = RegisteredQueue(client, asyncio.get_running_loop(), self.root)
            predecessor = {"episode_character_id": 19, "episode_run_id": "synthetic-predecessor"}
            _, _, transition = await asyncio.to_thread(queue_module.continue_successor, queue, predecessor, turns)
            self.assertEqual(self.driver.order[:3], ["display-ack:" + app.STEP, "execute:" + app.STEP,
                                                   "preintent-observed-before-driver"])
            self.assertTrue(transition["successor_ui_pending"])
            self.assertEqual((self.driver.continues, self.driver.closes, self.driver.saves), (1, 0, 0))
            await self.call(client, "ck3_save_checkpoint", {"expected_revision": self.driver.frame["revision"]}, error=True)

            server_owner = self.driver._successor_ui_pending_ledger_v1
            original_display = server_owner.path.read_text(encoding="utf-8")
            self.assertIn('"status": "pending"', original_display)
            event = await self.call(client, "ck3_auto_turn")
            self.assertEqual(event["selected_step"], "select-event-option-1")
            self.assertTrue(event["unhandled_event_fallback_evidence"]["event_instance_advanced_verified"])
            captured = json.loads(next((self.root / "evidence/unhandled-events").glob("*.before.json")).read_text(encoding="utf-8"))
            self.assertEqual(captured["window_context"]["root_scope"]["typed_identity"]["character_id"], 19)
            _, _, saved = await asyncio.to_thread(queue_module.checkpoint_if_clear, queue, transition)
            self.assertIsNotNone(saved)
            self.assertIs(self.driver._successor_ui_pending_ledger_v1, server_owner)
            self.assertEqual((self.driver.continues, self.driver.closes, self.driver.saves), (1, 1, 1))
            self.assertLess(self.driver.order.index("display-ack:continue-death-succession-modal-v1"),
                            self.driver.order.index("close-intent-observed-before-driver"))
            self.assertEqual(self.driver.frame["campaign_goal"]["progress"]["reconciled_successions"], 1)
            counts = self.driver.snapshot_reads, self.driver.cap_reads
            following = await self.call(client, "ck3_auto_turn")
            self.assertEqual(following["selected_step"], "unpause")
            self.assertEqual((self.driver.snapshot_reads, self.driver.cap_reads), counts)

            previous = self.driver.frame["episode_character_id"]
            old_episode = self.driver.frame["episode_run_id"]
            self.driver.frame["played_character"]["character_id"] = 29
            self.driver.frame.update(one_life_terminal=True, one_life_terminal_reason="played_character_changed")
            self.driver.post = deepcopy(self.driver.frame)
            self.driver.post.update(episode_character_id=29, episode_run_id="synthetic-second-successor",
                                    one_life_terminal=False, one_life_terminal_reason=None)
            reconciliation = deepcopy(self.driver.result["reconciliation"])
            reconciliation.update(predecessor_character_id=previous, actual_successor_character_id=29,
                successor_binding={key: self.driver.frame[key] for key in ("snapshot_id", "revision", "native_revision", "date_raw")})
            reconciliation["predecessor_binding"] = {"episode_character_id": previous, "episode_run_id": old_episode}
            self.driver.result.update(predecessor_character_id=previous, successor_character_id=29,
                source_episode_run_id=old_episode, episode_run_id="synthetic-second-successor", reconciliation=reconciliation)
            self.driver.result.update({key: self.driver.frame[key] for key in ("snapshot_id", "revision", "date_raw")})
            self.driver.post["campaign_goal"] = continue_ordinary_campaign_goal_v1(
                self.driver.frame["campaign_goal"], reconciliation)
            second = await self.call(client, "ck3_auto_turn")
            self.assertEqual(second["successor_ui_obligation_v1"]["status"], "pending")
            cleared = await self.call(client, "ck3_resume_successor_ui_v1")
            self.assertFalse(cleared["pending"])
            await self.call(client, "ck3_save_checkpoint", {"expected_revision": self.driver.frame["revision"]})
            self.assertIs(self.driver._successor_ui_pending_ledger_v1, server_owner)
            self.assertEqual((self.driver.continues, self.driver.closes, self.driver.saves), (2, 1, 2))
            self.assertEqual(self.driver.frame["campaign_goal"]["origin_character_id"], 19)
            self.assertEqual(self.driver.frame["campaign_goal"]["progress"]["reconciled_successions"], 2)

    async def test_completed_logical_response_and_auto_close_are_consumed_by_real_queue_without_replay(self):
        terminal = deepcopy(self.driver.frame)
        async with Client(mcp_server.create_server(self.driver)) as client:
            turn = await self.call(client, "ck3_auto_turn")
            queue = RegisteredQueue(client, asyncio.get_running_loop(), self.root)
            transitions = []
            _, _, transition = await asyncio.to_thread(queue_module.consume_completed, queue, turn,
                self.root / "original-auto.json", terminal, self.root / "independent-terminal.json", transitions)
            await self.call(client, "ck3_auto_turn")
            resumed = await self.call(client, "ck3_auto_turn")
            self.assertEqual(resumed["status"], "successor_ui_resumed")
            self.assertTrue(queue_module.completed_ui_resume(resumed))
            self.assertFalse(queue_module.completed_continuation(resumed))
            await asyncio.to_thread(queue_module.consume_completed_ui_resume, queue, resumed,
                self.root / "original-ui-auto.json", transition)
            _, _, saved = await asyncio.to_thread(queue_module.checkpoint_if_clear, queue, transition)
            self.assertIsNotNone(saved)
            self.assertEqual((self.driver.continues, self.driver.closes, self.driver.saves), (1, 1, 1))
            credit = json.loads((self.root / "m7-auto-ui-result.json").read_text(encoding="utf-8"))
            self.assertEqual((credit["new_natural_succession_credit"], credit["ordinary_cycle_credit"]), (0, 0))

    async def test_packaged_identity_matches_canonical_and_isolated_app_bootstraps_without_repo_tools(self):
        generator_spec = importlib.util.spec_from_file_location("_machine_package_generator", ROOT / "tools/gen_ck3_live_run_identity_package.py")
        generator = importlib.util.module_from_spec(generator_spec)
        generator_spec.loader.exec_module(generator)
        self.assertEqual(generator.render(), generator.TARGET.read_text(encoding="utf-8"))
        code = '''import asyncio,sys,tempfile
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from mcp import Client
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.successor_ui_app_owner_v1 import _machine_id
from xar_autoplayer.successor_ui_pending_ledger_v1 import owner_source_epoch_v1
assert _machine_id() == 'synthetic-isolated-app'
assert len(owner_source_epoch_v1()) == 64
assert 'tools.ck3_live_run_id' not in sys.modules
class Driver:
    allow_private_death_succession_modal_continue = True
    allow_private_current_timeline_blocker_query = True
    _succession_lifecycle = {'lifecycle':'ordinary_campaign_succession'}
    def capabilities(self): return {'backend_id':'synthetic-isolated'}
async def run():
    with tempfile.TemporaryDirectory(prefix='isolated-app-software-') as root:
        driver=Driver(); driver.state_dir=Path(root)
        async with Client(create_server(driver)) as client:
            assert 'ck3_resume_successor_ui_v1' in {v.name for v in (await client.list_tools()).tools}
            result=await client.call_tool('ck3_get_capabilities',{})
            assert not result.is_error
asyncio.run(run())
print('ISOLATED_PACKAGE_APP_BOOTSTRAP_OK_NO_GAME_NO_REPO_TOOLS')
'''
        env = dict(os.environ, XAR_CK3_MACHINE_ID="synthetic-isolated-app", PYTHONDONTWRITEBYTECODE="1")
        result = await asyncio.to_thread(subprocess.run,
            [sys.executable, "-I", "-B", "-X", "utf8", "-c", code, str(ROOT / "ck3_autonomous_player/src")],
            cwd=self.root, env=env, capture_output=True, text=True, encoding="utf-8", timeout=20,
            creationflags=getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ISOLATED_PACKAGE_APP_BOOTSTRAP_OK", result.stdout)

    async def test_external_interception_and_intent_failure_never_execute_continue(self):
        async with Client(mcp_server.create_server(self.driver, before_auto_turn_submit=lambda _: {"reason": "synthetic intercept"})) as client:
            result = await self.call(client, "ck3_auto_turn")
            self.assertEqual(result["status"], "intercepted")
        self.assertFalse((self.root / journal.FILE).exists())
        async with Client(mcp_server.create_server(self.driver)) as client:
            with patch.object(journal.SuccessorUIPendingLedger, "_write", side_effect=OSError("synthetic fsync/readback failed")):
                await self.call(client, "ck3_auto_turn", error=True)
        self.assertEqual(self.driver.continues, 0)

    async def test_interaction_and_close_display_interception_defer_without_new_game_or_close(self):
        block_close = [True]
        def display(candidate):
            if candidate["selected_step"] == "continue-death-succession-modal-v1" and block_close[0]:
                return {"reason": "synthetic presentation intercept"}
        async with Client(mcp_server.create_server(self.driver, before_auto_turn_submit=display)) as client:
            await self.call(client, "ck3_auto_turn")
            await self.call(client, "ck3_auto_turn")
            self.driver.frame["pending_character_interaction"] = {"instance_id": 79}
            deferred = await self.call(client, "ck3_resume_successor_ui_v1")
            self.assertTrue(deferred["player_decision_pending"])
            self.assertEqual(self.driver.closes, 0)
            self.driver.frame["pending_character_interaction"] = None
            intercepted = await self.call(client, "ck3_auto_turn")
            self.assertEqual(intercepted["status"], "successor_ui_pending")
            self.assertEqual(list(self.root.glob("successor-ui-close-*.json")), [])
            block_close[0] = False
            applied = await self.call(client, "ck3_auto_turn")
            self.assertEqual(applied["status"], "successor_ui_resumed")
            self.assertEqual((self.driver.continues, self.driver.closes), (1, 1))

    async def test_mixed_pre_frame_and_missing_pre_goal_reject_before_intent(self):
        original = deepcopy(self.driver.frame)
        for kind in ("frame", "goal"):
            self.driver.frame = deepcopy(original)
            if kind == "goal":
                self.driver.frame.pop("campaign_goal")
            def stale(service):
                result = planned(service)
                if kind == "frame":
                    result["planning_source_frame"]["connection_generation"] += 1
                return result
            with patch.object(GameplayBridgeService, "plan_turn", stale):
                async with Client(mcp_server.create_server(self.driver)) as client:
                    await self.call(client, "ck3_auto_turn", error=True)
            self.assertFalse((self.root / journal.FILE).exists())
        self.assertEqual(self.driver.continues, 0)

    async def test_post_goal_retention_and_original_persistence_failures_keep_original_and_once_lock(self):
        for kind in ("bad_post", "bad_goal", "fail_persist", "retain"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(prefix="successor-failure-software-") as temp:
                self.driver = Driver(temp)
                if kind != "retain":
                    setattr(self.driver, kind, True)
                guard = patch.object(journal.SuccessorUIPendingLedger, "retain", side_effect=OSError("synthetic retain failed"))
                with guard if kind == "retain" else patch.dict({}, {}):
                    async with Client(mcp_server.create_server(self.driver)) as client:
                        response = await self.call(client, "ck3_auto_turn", error=True)
                        diagnostics = response["diagnostics"]
                        key = "natural_succession_driver_state_persistence_v1" if kind == "fail_persist" else "successor_ui_obligation_v1"
                        original = diagnostics[key]["original_turn"]["result"]
                        self.assertEqual(original["original_extra"], self.driver.result["original_extra"])
                        self.assertTrue(original["accepted"])
                        await self.call(client, "ck3_auto_turn", error=True)
                self.assertEqual(self.driver.continues, 1)
                self.assertEqual(json.loads((Path(temp) / journal.FILE).read_text(encoding="utf-8"))["status"], "handoff_unverified")

    async def test_same_game_new_connection_rebind_unknown_close_and_none_open_remain_safe(self):
        async with Client(mcp_server.create_server(self.driver)) as client:
            await self.call(client, "ck3_auto_turn")
            await self.call(client, "ck3_resume_successor_ui_v1")

        self.driver.frame["diagnostics"]["connection_generation"] += 1
        self.driver.frame["revision"] = 1
        self.driver.frame["native_revision"] += 1
        self.driver.context["snapshot_revision"] = self.driver.frame["native_revision"]
        self.driver.frame["snapshot_id"] = "synthetic:new-connection"
        async with Client(mcp_server.create_server(self.driver)) as client:
            deferred = await self.call(client, "ck3_resume_successor_ui_v1")
            self.assertTrue(deferred["pending"])
            await self.call(client, "ck3_auto_turn")

            self.driver.context["identity"] = "none"
            unresolved = await self.call(client, "ck3_auto_turn")
            self.assertEqual(unresolved["status"], "successor_ui_pending")
            self.assertEqual(self.driver.closes, 0)
            await self.call(client, "ck3_save_checkpoint", error=True)
            self.driver.context["identity"] = "death_succession_modal"
            self.driver.ack_only = True
            await self.call(client, "ck3_auto_turn", error=True)
            await self.call(client, "ck3_auto_turn", error=True)
        self.assertEqual((self.driver.continues, self.driver.closes, self.driver.saves), (1, 1, 0))

    async def test_same_game_rebuilt_app_and_real_queue_finish_old_root_event_close_and_save(self):
        transitions = []
        async with Client(mcp_server.create_server(self.driver)) as client:
            queue = RegisteredQueue(client, asyncio.get_running_loop(), self.root)
            _, _, transition = await asyncio.to_thread(queue_module.continue_successor, queue,
                {"episode_character_id": 19, "episode_run_id": "synthetic-predecessor"}, transitions)
        original_binding = deepcopy(transition["successor_episode_binding"])
        self.driver.frame["diagnostics"]["connection_generation"] += 1
        self.driver.frame["revision"] = 1
        self.driver.frame["native_revision"] += 1
        self.driver.context["snapshot_revision"] = self.driver.frame["native_revision"]
        self.driver.frame["snapshot_id"] = "synthetic:reconnected-App"
        async with Client(mcp_server.create_server(self.driver)) as client:
            queue = RegisteredQueue(client, asyncio.get_running_loop(), self.root)
            await asyncio.to_thread(queue_module.resume_successor_ui, queue, deepcopy(self.driver.frame), transition)
            self.assertEqual(transition["successor_episode_binding"], original_binding)
            await self.call(client, "ck3_auto_turn")
            _, _, saved = await asyncio.to_thread(queue_module.checkpoint_if_clear, queue, transition)
            self.assertIsNotNone(saved)
            self.assertEqual((self.driver.continues, self.driver.closes, self.driver.saves), (1, 1, 1))
            self.assertEqual(self.driver.frame["campaign_goal"]["progress"]["reconciled_successions"], 1)

    async def test_foreign_birth_and_unadopted_driver_cannot_clear_pending(self):
        async with Client(mcp_server.create_server(self.driver)) as client:
            await self.call(client, "ck3_auto_turn")
        with patch.object(app, "_game_identity", return_value={"pid": 123, "creation_date": "foreign-birth", "executable": "synthetic/ck3.exe"}):
            async with Client(mcp_server.create_server(self.driver)) as client:
                await self.call(client, "ck3_resume_successor_ui_v1", error=True)
        self.driver.allow_private_death_succession_modal_continue = False
        with self.assertRaisesRegex(ValueError, "qualified ordinary App owner"):
            mcp_server.create_server(self.driver)

    async def test_true_terminal_has_no_forced_successor_or_new_game(self):
        self.driver.frame["played_character"]["alive"] = False
        self.driver.frame["one_life_terminal_reason"] = "played_character_dead"
        def terminal(service):
            return {"snapshot_id": service.driver.frame["snapshot_id"], "revision": service.driver.frame["revision"],
                    "plan": {"phase": "terminal_complete", "selected_step": None}}
        with patch.object(GameplayBridgeService, "plan_turn", terminal):
            async with Client(mcp_server.create_server(self.driver)) as client:
                result = await self.call(client, "ck3_auto_turn")
        self.assertEqual(result["status"], "terminal")
        self.assertFalse((self.root / journal.FILE).exists())
        self.assertEqual((self.driver.continues, self.driver.closes, self.driver.saves), (0, 0, 0))

    async def test_original_driver_exception_cannot_rearm_generic_or_AUTO_continue(self):
        for mode, applied in (("before_apply", 0), ("after_apply_unknown", 1)):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(prefix="successor-dispatch-once-") as temp:
                self.driver = Driver(temp)
                self.driver.continue_failure_mode = mode
                async with Client(mcp_server.create_server(self.driver)) as client:
                    first = await client.call_tool("ck3_auto_turn", {})
                    self.assertTrue(first.is_error)
                    self.assertIn("synthetic original Continue", str(first))
                    self.assertEqual((self.driver.continue_dispatch_attempts, self.driver.continues), (1, applied))
                    self.driver.continue_failure_mode = None
                    for tool in ("ck3_execute_step", "ck3_auto_turn", "ck3_execute_step"):
                        arguments = ({"step": app.STEP, "expected_revision": self.driver.frame["revision"]}
                                     if tool == "ck3_execute_step" else {})
                        response = await client.call_tool(tool, arguments)
                        self.assertEqual((self.driver.continue_dispatch_attempts, self.driver.continues), (1, applied))
                        self.assertTrue(response.is_error)
                    retained = json.loads((Path(temp) / journal.FILE).read_text(encoding="utf-8"))
                    self.assertEqual(retained["status"], "handoff_unverified")
                    self.assertFalse(retained["action_replay_authorized"])

if __name__ == "__main__":
    unittest.main()

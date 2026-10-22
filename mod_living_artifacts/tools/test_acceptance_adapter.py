"""Offline producer/consumer and once-only control tests; no live qualification."""
from __future__ import annotations

import json
import copy
from pathlib import Path
import re
import shutil
import tempfile
import sys
import unittest

import acceptance_adapter as adapter
from acceptance_contract import ArtifactSample, Object, array, exact_getter_integer, field, integer, json_value, mapping, object_value, pin, read, write_once
import prepare_fixture
from living_artifacts_core import render_core_localization
from inventory_gui_contract import REFUSAL
from checkpoint_callback import checked_pin
from test_core_generation import Script
from test_inventory_gui_contract import response_fixture
from startup_actor_binding import StartupActorBinding
from ck3_mod_acceptance_client import CaseClient
from native_interruption_contract import completed_interruption_response
from test_native_interruption_contract import PublicCheckpointPort, RootCheckpointConsumer

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'ck3_autonomous_player/src'))


def sample_line(*, equipped: bool = True) -> str:
    # Authored legacy-parser boundary only. R2 proved the removed hidden logger
    # cannot generate this line; these rows never qualify a real game getter.
    return (f"XALW_SAMPLE_V1;seq=2.00000;owner=29829;artifact=16777217;equipped={int(equipped)};"
            "game_day=1000.00000;month=12800.00000;level=2.00000;xp=0.00000;pending=0.00000;"
            "growth=1.00000;last_month=12800.00000;resonance=25.00000;durability=100.00000")


class UnitPort:
    """Authored public-boundary rows to exercise control logic, never SDK evidence."""

    def __init__(self, output: Path) -> None:
        self.output = output
        self.state = output / "state"
        self.manifest: object = {"machine_id": "unit-machine", "game": {"version": "1.20.0.4", "exe_sha256": "a" * 64}}
        self.frozen: object = {"run_id": "unit-run"}
        self.operator_reviewer = "unit-root"
        self.calls: list[str] = []
        self.frame: Object = {
            "paused": True, "map_ready": True, "source": "injected-dll-named-pipe", "backend_id": "native-headless",
            "episode_projection": "native_campaign", "revision": 1, "native_revision": 1, "date_raw": 24000,
            "played_character": {"character_id": 29829, "alive": True, "source": "native"},
            "active_event": None, "pending_character_interaction": None,
            "diagnostics": {"bridge_pid": 123, "connection_generation": 1, "pipe_name": "unit-pipe",
                            "hello": {"pid": 123, "connection_generation": 1, "ck3_build_match": True,
                                      "expected_ck3_version": "1.20.0.4", "expected_ck3_sha256": "a" * 64}},
            "managed_campaign_run_binding": {"run_id": "unit-run", "bridge_pipe": "unit-pipe"},
        }

    def snapshot(self, allow_actor_change: bool = False, require_event_free: bool = True) -> object:
        raise AssertionError("Not part of this unit's action-only seam")

    def execute_plan(self, steps: list[Object], name: str, timeout: int | float | None = None, reserve: int = 90) -> object:
        tool = steps[0]["tool"]
        if not isinstance(tool, str):
            raise AssertionError("Tool must be explicit")
        self.calls.append(tool)
        result: Object
        if tool == adapter.WINDOW:
            result = {"available": True, "current": {"available": True, "native_visible": True, "effective_visible": True}}
        elif tool == adapter.ITEM:
            result = {"available": True, "read_only": True, "loaded_source_pins_verified": True, "personally_owned": True,
                      "inventory_artifact": True, "requested_artifact_id": 16777217, "played_character_id": 29829,
                      "date_raw": 24000, "native_equipped_observed": True, "equipped": False, "equipped_slot_index": None,
                      "inventory_view_available": True, "inventory_view_visible": True,
                      "effective_slot_index": 0, "replacing_artifact_id": None, "can_equip_in_effective_slot": True, "can_unequip": False}
        elif tool == adapter.EQUIP:
            result = {"once_intent_consumed": True, "intent_sequence": 1,
                      "desired_inventory_state_observed": True}  # Deliberately dishonest ACK flag is never credited.
        elif tool == adapter.EQUIP_POST:
            result = {"desired_inventory_state_observed": False}
        else:
            raise AssertionError("Unexpected unit request: " + tool)
        row: Object = {"ok": True, "result": result, "after_snapshot": self.frame}
        write_once(self.output / (name + ".actual-results.json"), {"rows": [row], "unit_test_data": True})
        return [row]

    def advance_day(self, days: int = 1, timeout: float = 300, allow_event_boundary: bool = False,
                    allow_actor_change: bool = False) -> object:
        raise AssertionError("No simulated days in this unit test")

    def guard(self, reserve: int = 90) -> object:
        return {"unit_test": True}

    def log_bytes(self, name: str = "debug.log", maximum: int = 64 * 1024 * 1024) -> bytes:
        raise AssertionError("No authored log can stand in for a live logger in this unit")

    def checkpoint(self, name: str, value: object) -> object:
        return write_once(self.output / (name + ".json"), value)

    def root_checkpoint(self, name: str, request: Object, reserve: int = 90) -> object:
        raise AssertionError("No reviewer in this unit")


class GuiPort(UnitPort):
    """Authored refusal/GUI/readback rows; no desktop or native commands."""

    def __init__(self, output: Path, *, error: str = REFUSAL, callback_status: str = "completed",
                 actual_visible: bool = True) -> None:
        super().__init__(output)
        self.frozen = {"run_id": "unit-run", "source_root": str(Path(__file__).resolve().parents[2])}
        self.error = error
        self.callback_status = callback_status
        self.actual_visible = actual_visible
        self.visible = False
        self.gui_requests: list[Object] = []
        self.snapshot_count = 0

    def snapshot(self, allow_actor_change: bool = False, require_event_free: bool = True) -> object:
        self.snapshot_count += 1
        write_once(self.output / f"case-snapshot-{self.snapshot_count:04d}.actual-results.json",
                   {"rows": [{"ok": True, "result": self.frame}], "unit_test_data": True})
        return self.frame

    def execute_plan(self, steps: list[Object], name: str, timeout: int | float | None = None, reserve: int = 90) -> object:
        tool = steps[0]["tool"]
        if tool == adapter.OPEN:
            self.calls.append(adapter.OPEN)
            refusal: Object = {"ok": False, "error": self.error}  # Actual guard refusal has neither result nor after_snapshot.
            write_once(self.output / (name + ".actual-results.json"), {"rows": [refusal], "unit_test_data": True})
            return [refusal]
        actual = super().execute_plan(steps, name, timeout, reserve)
        if tool == adapter.ITEM:
            row = mapping(array(actual, "authored rows")[0], "authored row")
            item = mapping(row["result"], "authored item")
            item["inventory_view_visible"] = self.visible
            amended: Object = {"ok": True, "result": json_value(item), "after_snapshot": self.frame}
            # Preserve exactly the authored boundary returned to Session.call.
            (self.output / (name + ".actual-results.json")).write_text(
                json.dumps({"rows": [amended], "unit_test_data": True}), encoding="utf-8")
            return [amended]
        return actual

    def root_checkpoint(self, name: str, request: Object, reserve: int = 90) -> object:
        self.gui_requests.append(request)
        root = self.output / name
        root.mkdir()
        response, _, _ = response_fixture(root, pid=123, generation="1", actor=29829, date_raw=24000,
            target="16777217", refusal=checked_pin(request["original_native_refusal"], "authored native refusal"))
        if self.callback_status == "completed":
            self.visible = self.actual_visible
        else:
            response.update(status=self.callback_status, submitted=self.callback_status == "outcome_unknown", reason="Authored GUI boundary")
            for key in ("mapping_receipt", "source_screenshot", "after_screenshot"):
                response[key] = None
        return response


class NotificationPort(GuiPort):
    def __init__(self,output: Path,*,keep_original: bool=False) -> None:
        super().__init__(output)
        self.keep_original=keep_original
        self.native_requests: list[str]=[]

    def advance_day(self,days: int=1,timeout: float=300,allow_event_boundary: bool=False,
                    allow_actor_change: bool=False) -> object:
        self.calls.append("actual-host-advance-interface")
        self.frame["date_raw"]=24024
        self.frame["pending_character_interaction"]={"instance_id":33554443}
        return {"result":{"after":self.frame}}

    def root_checkpoint(self,name: str,request: Object,reserve: int=90) -> object:
        if request.get("schema")!="living-artifacts-native-interruption-request-v1" or request.get("existing_specialist_policy_priority") is not True:
            raise AssertionError("Actual native interruption policy contract required")
        self.native_requests.append(name)
        if not self.keep_original:
            self.frame["pending_character_interaction"]=None
        response = completed_interruption_response(request, reviewer=self.operator_reviewer)
        write_once(self.output / (name + '-root-result.json'), object_value(response))
        public: RootCheckpointConsumer = PublicCheckpointPort(self.output)
        return public.root_checkpoint(name, request, reserve=reserve)


class NativePublicPort(CaseClient):
    """Actual public route, snapshot validation and projection; authored transport only."""
    def __init__(self,output: Path,before: Object,*,early: bool) -> None:
        self.output=output;self._seq=0;self._binding=None
        self.manifest={"game":{"version":"1.20.0.4","exe_sha256":"a"*64}}
        self.current=copy.deepcopy(before);self.early=early;self.dispatches=0
        self.report={"readiness":before,"steps":[],"capabilities":{
            "action_steps":["life-advance-one-day"],"bridge_capabilities":[
                "game.command.research-arm-tactical-daily-sentinel-v1-N",
                "game.command.research-query-tactical-daily-sentinel-v1",
                "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N",
                "game.command.query-current-event-window-context-v1"]}}

    def guard(self,reserve: int=90,*,failure_shutdown: bool=False) -> dict[str,object]:
        return self.report

    def execute_plan(self,steps: list[dict[str,object]],name: str,timeout: float | None=None,
                     reserve: int=90) -> list[object]:
        pending: Object={"instance_id":33554443,"sender_character_id":31408,
                        "auto_accept_notification":False,"source":"native"}
        if steps[0].get("tool")=="ck3_take_snapshot":
            if self.early and self._seq==2:self.current["pending_character_interaction"]=pending
            return [{"ok":True,"result":copy.deepcopy(self.current)}]
        self.dispatches+=1
        start=integer(self.current["date_raw"],"authored start")
        self.current["date_raw"]=start+24;self.current["revision"]=2;self.current["native_revision"]=2
        self.current["pending_character_interaction"]=pending
        return [{"id":name,"ok":True,"error":None,"after_snapshot":copy.deepcopy(self.current),"result":{
            "step":"life-advance-one-day","source":"native-composite","backend_id":"native-headless",
            "starting_date_raw":start,"ending_date_raw":start+24,"paused":True,"requested_horizon_days":1,
            "active_event":None,"pending_character_interaction":pending,"ordinary_events":[],"actions":[],
            "progress_status":"postcondition","event_resolution":"none"}}]


class NativeRouteNotificationPort(NotificationPort):
    def __init__(self,output: Path,*,early: bool) -> None:
        super().__init__(output);self.native=NativePublicPort(output,self.frame,early=early)

    def advance_day(self,days: int=1,timeout: float=300,allow_event_boundary: bool=False,
                    allow_actor_change: bool=False) -> object:
        # Synchronize the initial public snapshot sequence with the real outer
        # saved-source consumer; the next actual public snapshot gets a new name.
        self.native._seq=self.snapshot_count
        row=self.native.advance_day(days,timeout,allow_event_boundary,allow_actor_change)
        self.snapshot_count=self.native._seq
        self.frame=object_value(field(field(row,"result"),"after"))
        return row


class AcceptanceContractTests(unittest.TestCase):
    def test_actual_public_native_day_reaches_product_interruption_consumer(self) -> None:
        for early in (True,False):
            with self.subTest(early=early),tempfile.TemporaryDirectory() as temporary:
                port=NativeRouteNotificationPort(Path(temporary),early=early)
                session=adapter.Session({"run_id":"unit-run"},port,adapter.Contract(72,420,60,(),()))
                session.startup_actor=StartupActorBinding(29829,123,"1",24000,25,"a"*64,"b"*64)
                session.snapshot();session.advance_one()
                self.assertEqual(port.native.dispatches,0 if early else 1)
                self.assertEqual(session.days,0 if early else 1)
                self.assertEqual(port.native_requests,["xalw-native-interruption-0001"])
                self.assertIsNone(mapping(session.last_frame,"actual consumed frame")["pending_character_interaction"])

    def test_pending_notification_is_handled_before_any_later_business_call(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            port=NotificationPort(Path(temporary))
            session=adapter.Session({"run_id":"unit-run"},port,adapter.Contract(72,420,60,(),()))
            session.startup_actor=StartupActorBinding(29829,123,"1",24000,25,"a"*64,"b"*64)
            session.snapshot();session.advance_one()
            self.assertEqual(session.days,1)
            self.assertEqual(port.native_requests,["xalw-native-interruption-0001"])
            self.assertIsNone(mapping(session.last_frame,"retained frame")["pending_character_interaction"])
            self.assertEqual(port.calls,["actual-host-advance-interface"])

    def test_root_absence_flag_cannot_replay_an_unchanged_native_window(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            port=NotificationPort(Path(temporary),keep_original=True)
            session=adapter.Session({"run_id":"unit-run"},port,adapter.Contract(72,420,60,(),()))
            session.startup_actor=StartupActorBinding(29829,123,"1",24000,25,"a"*64,"b"*64)
            session.snapshot()
            with self.assertRaisesRegex(ValueError,"never replay"):
                session.advance_one()
            self.assertEqual(port.native_requests,["xalw-native-interruption-0001"])

    def test_localization_rejects_script_scope_prefix_and_keeps_named_object_methods(self) -> None:
        for language in ("simp_chinese", "english"):
            entries = render_core_localization("simp_chinese" if language == "simp_chinese" else "english")
            self.assertFalse(any("[scope:" in body for body in entries.values()))
            self.assertIn("xalw_artifact.MakeScope.Var('xalw_level')", entries["xalw.10.desc"])
        self.assertNotIn("[scope:", prepare_fixture.render_observer_effects())

    def test_legacy_parser_authored_fields_are_closed(self) -> None:
        sample = ArtifactSample.parse(sample_line())
        self.assertEqual((sample.owner_id, sample.artifact_id, sample.level, sample.xp, sample.growth_sequence), ("29829", "16777217", 2, 0, 1))
        self.assertEqual(ArtifactSample.parse(sample_line(equipped=False)).equipped, False)

    def test_getter_fraction_cannot_be_rounded_into_a_passing_integer(self) -> None:
        with self.assertRaisesRegex(ValueError, "noninteger"):
            ArtifactSample.parse(sample_line().replace("level=2.00000", "level=2.00001"))
        self.assertEqual(exact_getter_integer("1,280.00000", "grouped native integer"), 1280)
        with self.assertRaises(ValueError):
            exact_getter_integer("12,80.00000", "malformed grouping")

    def test_missing_wrong_duplicate_or_unexpanded_fields_are_rejected(self) -> None:
        for changed in (sample_line().replace("pending=0.00000;", ""), sample_line().replace("growth=", "growth_sequence="),
                        sample_line() + ";level=2.00000", sample_line().replace("owner=29829", "owner=[scope:owner.GetID]")):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                ArtifactSample.parse(changed)

    def test_identity_keeps_decimal_strings_across_json_roundtrip(self) -> None:
        sample = ArtifactSample.parse(sample_line().replace("artifact=16777217", "artifact=18446744073709551614"))
        payload = sample.to_json()
        self.assertEqual(json.loads(json.dumps(payload))["artifact_id"], "18446744073709551614")
        self.assertEqual(json_value(("first", "second")), ["first", "second"])
        with self.assertRaisesRegex(ValueError, "safe range"):
            json_value(2**53)

    def test_read_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "wrong.json"
            path.write_text('{"schema_version":1,"schema_version":2}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                read(path)

    def test_actual_input_rarities_and_references_are_not_inferred_from_role(self) -> None:
        rows = [f"XALW_INPUT_V1;role={role};owner=29829;artifact={number};rarity={rarity}"
                for number, role, rarity in ((1, "target", "masterwork"), (2, "common", "common"), (3, "masterwork", "masterwork"),
                                             (4, "famed", "famed"), (5, "illustrious", "illustrious"))]
        self.assertEqual(adapter._inputs("\n".join(rows).encode())["illustrious"], ("29829", "5"))
        with self.assertRaisesRegex(ValueError, "rarity"):
            adapter._inputs("\n".join(rows).replace("artifact=5;rarity=illustrious", "artifact=5;rarity=famed").encode())
        with self.assertRaisesRegex(ValueError, "distinct"):
            adapter._inputs("\n".join(rows).replace("artifact=5", "artifact=4").encode())

    def test_fixture_has_initial_inputs_and_no_periodic_or_dynamic_logger(self) -> None:
        script = Script(prepare_fixture.render_observer_effects())
        observer = script.named("xalw_fixture_initialize_effect")
        self.assertFalse(any(block.key == "xalw_fixture_observe_effect" for block in script.blocks))
        self.assertNotIn("[", script.text)
        self.assertNotIn("trigger_event", script.text)
        self.assertNotIn("change_variable", script.text)
        self.assertFalse(any(scalar.key in {"xalw_feed_material_effect", "xalw_settle_xp_effect", "destroy_artifact", "equip_artifact_to_owner_replace"}
                             for block in (observer, *script.blocks) for scalar in script.scalars(block)
                             if observer.opening < scalar.start < observer.end))

    def test_unknown_original_equipment_ack_is_not_replayed_or_credited(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            port = UnitPort(Path(temporary))
            session = adapter.Session({"run_id": "unit-run"}, port, adapter.Contract(72, 420, 60, (), ()))
            # This action-only seam supplies an explicitly authored binding;
            # separate startup tests exercise real frontend/root proof parsing.
            session.startup_actor = StartupActorBinding(29829, 123, "1", 24000, 25, "a" * 64, "b" * 64)
            with self.assertRaisesRegex(adapter.CaseBlocked, "unknown"):
                session.equip("16777217", True)
            self.assertEqual(port.calls.count(adapter.EQUIP), 1)
            self.assertEqual(port.calls.count(adapter.EQUIP_POST), 3)
            self.assertTrue(session.original_action_unknown)
            self.assertNotIn(adapter.WINDOW, port.calls)
            self.assertNotIn(adapter.OPEN, port.calls)

    def test_exact_pre_intent_refusal_uses_gui_once_and_independent_item_readback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            port = GuiPort(Path(temporary))
            session = adapter.Session({"run_id": "unit-run"}, port, adapter.Contract(72, 420, 60, (), ()))
            session.startup_actor = StartupActorBinding(29829, 123, "1", 24000, 25, "a" * 64, "b" * 64)
            session.open_inventory("16777217")
            self.assertEqual(port.calls, [adapter.ITEM, adapter.OPEN, adapter.ITEM])
            self.assertEqual((len(port.gui_requests), port.snapshot_count), (1, 1))
            self.assertFalse(session.original_action_unknown)
            self.assertIs(port.gui_requests[0]["original_open_intent_not_admitted"], True)
            session.open_inventory("16777217")
            self.assertEqual(port.calls.count(adapter.OPEN), 1)
            self.assertEqual(len(port.gui_requests), 1)
            self.assertNotIn(adapter.WINDOW, port.calls)

    def test_unknown_native_error_never_authorizes_gui_or_second_open(self) -> None:
        for error in ("Original native dispatch outcome unavailable", "Another failure mentioning " + REFUSAL,
                      "RuntimeError: Inventory opening requires the existing actual managed-source inventory"):
            with self.subTest(error=error), tempfile.TemporaryDirectory() as temporary:
                port = GuiPort(Path(temporary), error=error)
                session = adapter.Session({"run_id": "unit-run"}, port, adapter.Contract(72, 420, 60, (), ()))
                session.startup_actor = StartupActorBinding(29829, 123, "1", 24000, 25, "a" * 64, "b" * 64)
                with self.assertRaises(adapter.CaseCallUnavailable):
                    session.open_inventory("16777217")
                with self.assertRaisesRegex(adapter.CaseBlocked, "unknown"):
                    session.open_inventory("16777217")
                self.assertEqual(port.calls, [adapter.ITEM, adapter.OPEN])
                self.assertEqual(port.gui_requests, [])
                self.assertTrue(session.original_action_unknown)

    def test_gui_unknown_is_preserved_and_completed_callback_requires_native_visibility(self) -> None:
        for status, visible in (("outcome_unknown", False), ("completed", False)):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as temporary:
                port = GuiPort(Path(temporary), callback_status=status, actual_visible=visible)
                session = adapter.Session({"run_id": "unit-run"}, port, adapter.Contract(72, 420, 60, (), ()))
                session.startup_actor = StartupActorBinding(29829, 123, "1", 24000, 25, "a" * 64, "b" * 64)
                with self.assertRaises((adapter.CaseBlocked, ValueError)):
                    session.open_inventory("16777217")
                with self.assertRaisesRegex(adapter.CaseBlocked, "unknown"):
                    session.open_inventory("16777217")
                self.assertEqual((port.calls.count(adapter.OPEN), len(port.gui_requests)), (1, 1))
                self.assertTrue(session.original_action_unknown)

    def test_every_declared_optional_action_is_explicit(self) -> None:
        config = read(Path(__file__).with_name("core_continuous.contract.json"))
        spec: Object = {"required_mcp_tools": list(adapter.REQUIRED_TOOLS), "opt_in_read_only_mcp_tools": [adapter.ITEM],
                        **adapter.REQUIRED_OPT_INS}
        context: Object = {"product": "living-artifacts", "case": "core_continuous", "case_contract": config, "case_spec": spec}
        self.assertEqual(adapter.validate_contract(context).maximum_days, 72)
        spec["opt_in_player_artifact_personal_use_actions"] = False
        with self.assertRaisesRegex(ValueError, "opt-in"):
            adapter.validate_contract(context)

    def test_frozen_emitter_reaches_runtime_copy_and_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / "emitted"
            fixture = prepare_fixture.emit_fixture(original)
            context: Object = {"state_dir": str(root / "allocated"),
                "case_contract": read(Path(__file__).with_name("core_continuous.contract.json")),
                "case_inputs": {"post_start": {"government_key": "feudal_government", "primary_title_tier_key": "duchy", "independent": True}}}
            adapter._write_fixture_contract(original, adapter._bound_config(context), fixture)
            copied = root / "allocated/profile/mod-content/fixture"
            shutil.copytree(original, copied)
            self.assertTrue(adapter._prepared_sources(context, root / "allocated"))
            script = copied / "common/scripted_effects/xalw_fixture_observer.txt"
            script.write_bytes(script.read_bytes() + b"\n# changed after preparation\n")
            with self.assertRaisesRegex(ValueError, "runtime fixture differs"):
                adapter._prepared_sources(context, root / "allocated")

    def test_pins_reject_equal_but_wrong_json_types(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "one-byte.txt"
            source.write_bytes(b"a")
            reference = pin(source)
            for value in (True, 1.0):
                wrong: dict[str, object] = dict(reference)
                wrong["bytes"] = value
                with self.subTest(value=value), self.assertRaisesRegex(ValueError, "bool/float"):
                    adapter._checked_pin(wrong, "unit source", source)


if __name__ == "__main__":
    unittest.main()

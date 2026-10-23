"""Authored CK3 boundary drives real Session, Save producer and saved consumers.

These inputs and health values are offline regression fixtures, never live proof.
"""
from __future__ import annotations

from datetime import date, timedelta
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
for directory in (REPO / "tools", REPO / "ck3_autonomous_player/src", Path(__file__).resolve().parent):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import acceptance_adapter as core
from acceptance_contract import Object, array, field, integer, mapping, object_value, pin, read, text, write_once
from ck3_mod_acceptance_native_day import STEP, project_native_day
from startup_actor_binding import StartupActorBinding
from test_checkpoint_artifacts import AUTHORED_ARTIFACTS, AuthoredArtifact, authored_checkpoint_text
from test_core_generation import Script
from test_npc_saved_observer import variable
from test_preview_acceptance_adapter import context_fixture as preview_context
from test_suppression_timer_acceptance_adapter import TimerPort
import curse_representative_acceptance_adapter as curse
import prepare_curse_fixture as emitter
from prepare_npc_fixture import SourceBinding
from test_threshold_acceptance_adapter import qualify_zero_gold_context


def context_fixture(root: Path, *, qualified_zero_gold: bool = True, wrong_zero_exe: bool = False) -> Object:
    context = preview_context(root)
    if qualified_zero_gold:
        qualify_zero_gold_context(context, game=("1.20.0.4", "a" * 64) if wrong_zero_exe else None)
    context["case"] = curse.CASE
    context["case_contract"] = read(curse.TOOLS / curse.CONTRACT_NAME)
    context["case_spec"] = read(curse.TOOLS / "curse_representative.registry_stanza.json")
    context["state_dir"] = str(root / "curse-state")
    context["output"] = str(root / "curse-prepared")
    Path(str(context["output"])).mkdir()
    source = write_once(root / "authored-vanilla-boundary.json", {"authored_not_game_qualification": True})
    with patch.object(emitter, "qualify_fixture_sources", return_value={"authored-only": source}), patch.object(emitter, "current_machine_id", return_value="unit-machine"):
        prepared = curse.prepare_case(context)
    if prepared["runtime_status"] != "NOT_RUN":
        raise AssertionError("Initial inputs cannot qualify business")
    context["output"] = str(root / "curse-output")
    Path(str(context["output"])).mkdir()
    return context


class CursePort(TimerPort):
    def __init__(self, context: Object, *, fault: str | None = None) -> None:
        super().__init__(context, fault=fault)
        self.level, self.xp, self.growth = 1, 0, 0
        # Read the real prepared producer output; this authored boundary does
        # not prove CK3's gold effects or grant live initial-state qualification.
        emitted = Script((self.state / "profile/mod-content/fixture/common/scripted_effects/xalw_curse_inputs.txt").read_text(encoding="utf-8-sig"))
        initial = emitted.named("xalw_curse_initialize_effect")
        debit, credit = emitted.scalar(initial, "remove_short_term_gold"), emitted.scalar(initial, "add_gold")
        if debit.value != "gold" or credit.value != "20" or debit.start >= credit.start or emitted.descendants(initial, "add_gold"):
            raise AssertionError("Prepared initial wallet must clear current gold with the native positive debit before adding 20")
        self.gold, self.prestige, self.stress = int(credit.value), 1000, 20
        if fault == "wrong_initial_wallet":
            self.gold = 276  # R18's retained native and first Save input failure.
        self.equipped_id: int | None = None
        self.payment: int | None = None
        self.equip_count = 0

    def frame(self) -> Object:
        result = super().frame()
        if self.gold == 0 and self.fault == "missing_gold_nonzero_native":
            result["played_character_gold"] = {"raw": 1, "scale": 100000}
        return result

    def saved_text(self) -> str:
        items = (*AUTHORED_ARTIFACTS, AuthoredArtifact("17", "★Appetite Input", "masterwork"), AuthoredArtifact("18", "Raw Discovery Candidate", "common"))
        source = authored_checkpoint_text(items)
        calendar = date(1066, 9, 15) + timedelta(days=self.day)
        source = source.replace("date=1066.9.15", f"date={calendar.year}.{calendar.month}.{calendar.day}")
        source = source.replace(variable("xalw_xp_in_level", "value", "9200000"), variable("xalw_xp_in_level", "value", "0"), 1)
        if self.day >= 16:
            source = source.replace(variable("xalw_last_settled_month", "value", "1280100000"), variable("xalw_last_settled_month", "value", "1280200000"), 1)
        for identity, curse_id in ((12, 1), (17, 2)):
            values = variable("xalw_schema_version", "value", "200000") + variable("xalw_kind", "flag", flag="living")
            values += variable("xalw_curse_1", "value", str(curse_id * 100000)) + variable("xalw_curse_rank_1", "value", "300000")
            if identity == 17:
                for key, amount in (("level", 1), ("xp_in_level", 8 if self.day >= 16 else 0), ("growth_sequence", 0)):
                    values += variable("xalw_" + key, "value", str(amount * 100000))
            anchor = f'\t\t{identity}={{\n'
            source = source.replace(anchor, anchor + '\t\t\tvariables={ data={ ' + values + ' } }\n', 1)
            # Merge rather than duplicate the existing selected variable block.
            start = source.index(anchor)
            old = source.index('\t\t\tvariables={ data={ ', start + len(anchor) + len('\t\t\tvariables={ data={ ' + values + ' } }\n'))
            end = source.index(' } }\n', old) + len(' } }\n')
            previous = source[old:end]
            source = source[:old] + source[end:]
            source = source.replace('variables={ data={ ' + values, 'variables={ data={ ' + previous[len('\t\t\tvariables={ data={ '):-len(' } }\n')] + values, 1)
        if self.fault != "missing_modifier":
            source = source.replace('\t\t12={\n', '\t\t12={\n\t\t\tmodifiers={ xalw_content_blood_1_3_modifier }\n', 1)
        candidate_kind = "living" if self.fault == "reroll" and self.day >= 17 else "ordinary"
        candidate = variable("xalw_schema_version", "value", "200000") + variable("xalw_kind", "flag", flag=candidate_kind)
        source = source.replace('\t\t18={\n', '\t\t18={\n\t\t\tvariables={ data={ ' + candidate + ' } }\n', 1)
        source = source.replace('\t\t\tvariables={ data={  } }\n\t\t}\n', '\t\t}\n')
        refs = variable("xalw_curse_fixture_appetite", "artifact", "17") + variable("xalw_curse_fixture_candidate", "artifact", "18")
        if self.payment is not None:
            refs += variable("xalw_content_appetite_quote", "value", "5000000") + variable("xalw_content_payment", "value", str(self.payment * 100000))
            refs += variable("xalw_content_month_done", "value", "1280200000")
        source = source.replace(variable("xalw_fixture_target", "artifact", "12"), refs + variable("xalw_fixture_target", "artifact", "12"), 1)
        gold = "" if self.gold == 0 else f'\t\t\tgold={{ value={self.gold} }}\n'
        if self.gold == 0:
            invalid_gold = {"null_gold": "gold=null", "empty_gold": "gold={}",
                "duplicate_gold": "gold={ value=0 } gold={ value=0 }"}.get(self.fault or "")
            if invalid_gold is not None:
                gold = "\t\t\t" + invalid_gold + "\n"
        prestige = "" if self.gold == 0 and self.fault == "missing_zero_prestige" else f'\t\t\tprestige={{ currency={self.prestige} accumulated=1000 }}\n'
        source = source.replace('\t\talive_data={\n', f'\t\talive_data={{\n{gold}{prestige}\t\t\tstress={self.stress}\n', 1)
        return source

    def execute_plan(self, steps: list[Object], name: str, timeout: int | float | None = None, reserve: int = 90) -> object:
        step = steps[0]
        tool = str(step["tool"])
        args = mapping(step["args"], "authored args")
        if tool == "ck3_query_campaign_root_context_v1":
            raw = 500000 - (110000 if self.fault == "wrong_health" else 120000) if self.equipped_id == 12 else 500000
            result: Object = {"status": "unavailable", "campaign_root_context_ready": False} if self.fault == "health_unavailable" else {
                "status": "available", "accepted": True, "campaign_root_context_ready": True, "campaign_root_context": {
                    "player_character_id": 91, "date_raw": 53144328 + self.day * 24, "snapshot_revision": 2,
                    "readiness": {"player_health_ready": True, "same_frame_ready": True, "ready": True}, "player_health": {"raw": raw, "scale": True if self.fault == "bad_health_scale" else 100000},
                    "provenance": {"game_version": text(field(field(self.manifest, "game"), "version"), "authored game version"),
                        "executable_sha256": text(field(field(self.manifest, "game"), "exe_sha256"), "authored game EXE SHA"), "character_health_rva": "0x28C64E0"}}}
        elif tool == core.ITEM:
            identity = integer(args["artifact_id"], "authored item", 0)
            equipped = self.equipped_id == identity
            result = {"available": True, "read_only": True, "loaded_source_pins_verified": True, "personally_owned": True, "inventory_artifact": True,
                "requested_artifact_id": identity, "played_character_id": 91, "date_raw": 53144328 + self.day * 24, "native_equipped_observed": True,
                "equipped": equipped, "equipped_slot_index": 0 if equipped else None, "effective_slot_index": 0, "replacing_artifact_id": None,
                "can_equip_in_effective_slot": True, "can_unequip": True, "inventory_view_available": True, "inventory_view_visible": self.inventory_visible,
                "owned_ids": [12, 13, 14, 15, 16, 17, 18]}
        elif tool == core.EQUIP:
            self.equip_count += 1
            self.equipped_id = integer(args["artifact_id"], "authored item", 0) if args["desired_equipped"] is True else None
            if self.fault == "same_day_charge" and self.equip_count == 5:
                self.stress += 1
            result = {"once_intent_consumed": True, "intent_sequence": self.equip_count}
        elif tool == "ck3_select_event_option" and self.event == "xalw.10":
            self.show(None)
            result = {"submitted": True}
        else:
            return super().execute_plan(steps, name, timeout, reserve)
        self.tools.append(tool)
        row: Object = object_value({"ok": True, "plan": step, "result": result, "after_snapshot": self.frame()})
        if tool == core.EQUIP and self.fault == "unknown_equip":
            row = {"ok": False, "plan": step, "error": "Authored unknown original equipment result", "after_snapshot": self.frame()}
        write_once(self.output / (name + ".actual-results.json"), {"rows": [row]})
        return [row]

    def advance_day(self, days: int = 1, timeout: float = 300, allow_event_boundary: bool = False, allow_actor_change: bool = False) -> object:
        if days != 1 or not allow_event_boundary or allow_actor_change:
            raise AssertionError("Use the unchanged shared natural-day policy")
        before = object_value(self.snapshot(require_event_free=False))
        self.day += 1
        if self.day == 16:
            self.payment, self.gold = 20, -30 if self.fault == "negative_wallet" else 0
            self.stress += 28  # Actual adjusted stress is not assumed to equal 40.
        if self.day == 17:
            if self.fault == "daily_repeat":
                self.payment = 0
                self.stress += 28
            else:
                self.gold += 3  # Legitimate world income must not fail non-reentry.
                self.stress -= 1
        after = self.frame()
        name = f"case-natural-day-{self.day:04d}"
        raw: Object = object_value({"id": name, "ok": True, "error": None,
            "plan": {"id": name, "tool": "ck3_execute_step", "args": {"step": STEP}}, "after_snapshot": after,
            "result": {"starting_date_raw": field(before, "date_raw"), "ending_date_raw": field(after, "date_raw"), "step": STEP,
                "source": "native-composite", "backend_id": "native-headless", "paused": True, "requested_horizon_days": 1,
                "active_event": None, "pending_character_interaction": None, "ordinary_events": [], "progress_status": "completed", "event_resolution": "not_needed", "actions": []}})
        write_once(self.output / (name + ".actual-results.json"), {"rows": [raw]})
        projected = project_native_day(mapping(raw, "authored day"), mapping(before, "authored before"), allow_event_boundary=True)
        write_once(self.output / (name + ".native-day-projection.json"), {"raw_public_row_path": str(self.output / (name + ".actual-results.json")), "projection_source": "actual-life-advance-one-day", "row": projected})
        return projected


def run_fixture(root: Path, *, fault: str | None = None) -> tuple[Object, Object, CursePort]:
    context = context_fixture(root, qualified_zero_gold=fault != "unknown_zero_source", wrong_zero_exe=fault == "wrong_zero_exe")
    port = CursePort(context, fault=fault)
    binding = StartupActorBinding(91, 124, "9", 53144328, 12801, "a" * 64, "b" * 64)
    with patch.object(StartupActorBinding, "parse", return_value=binding):
        result = curse.run_case(context, port)
    return context, result, port


class CurseRepresentativeTests(unittest.TestCase):

    def test_r20_exact_refusal_actual_producers_and_final_audit_rejects_unknown_or_broken_gui(self) -> None:
        import hashlib
        import threshold_acceptance_adapter as historical
        fixtures = Path(__file__).resolve().parent / "fixtures"
        provenance = read(fixtures / "r20-inventory-refusal.provenance.json")
        for name, raw in mapping(provenance["sources"], "retained R20 sources").items():
            data = (fixtures / name).read_bytes()
            self.assertEqual((len(data), hashlib.sha256(data).hexdigest()), (field(raw, "bytes"), field(raw, "sha256")))
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary), fault="inventory_refusal")
            self.assertEqual(result["status"], "PASS", result.get("error"))
            self.assertEqual((port.saves, port.day, port.equip_count, port.tools.count(core.OPEN)), (7, 17, 5, 1))
            self.assertEqual(curse.verify_case(context), result)
            journal = read(Path(str(field(result["journal"], "path"))))
            self.assertEqual(curse.evaluate(context, manifest=port.manifest, reviewer="unit-root", journal=json.loads(json.dumps(journal))),
                field(array(result["checks"], "checks")[0], "observed"))
            callback = next(port.output.glob("inventory-gui-open-*-root-result.json"))
            original = callback.read_bytes()
            completed = read(callback)
            for changed in ({**completed, "reviewer": "another-reviewer"}, {**completed, "date_raw": True},
                    {**completed, "status": "outcome_unknown", "reason": "Unknown original click", "mapping_receipt": None,
                     "source_screenshot": None, "after_screenshot": None}, {**completed, "mapping_receipt": None}):
                callback.write_text(json.dumps(changed), encoding="utf-8")
                with self.subTest(callback=changed), self.assertRaises(ValueError):
                    curse.evaluate(context, manifest=port.manifest, reviewer="unit-root", journal=journal)
            callback.write_bytes(original)
            request = next(port.output.glob("inventory-gui-open-*-awaiting.json"))
            original_request = request.read_bytes()
            requested = read(request)
            for changed in ({**requested, "original_open_intent_not_admitted": False}, {**requested, "target_artifact_id": "17"},
                    {**requested, "reserve_seconds": True}, {**requested, "refusal_source": requested["original_native_refusal"]}):
                request.write_text(json.dumps(changed), encoding="utf-8")
                with self.subTest(request=changed), self.assertRaises(ValueError):
                    curse.evaluate(context, manifest=port.manifest, reviewer="unit-root", journal=journal)
            request.write_bytes(original_request)
            native = next(q for q in port.output.glob("xalw-core-*.actual-results.json") if field(array(read(q)["rows"], "rows")[0], "ok") is False)
            original_native = native.read_bytes()
            refused = object_value(array(read(native)["rows"], "row")[0])
            for changed in ({**refused, "error": "Another native failure"}, {**refused, "result": None}, {**refused, "after_snapshot": None}):
                native.write_text(json.dumps({"rows": [changed]}), encoding="utf-8")
                altered = {**journal, "native_records": historical._native_files(port.output)}
                with self.subTest(native=changed), self.assertRaises(ValueError):
                    curse.evaluate(context, manifest=port.manifest, reviewer="unit-root", journal=altered)
            native.write_bytes(original_native)
            sequence = int(native.name.split(".", 1)[0].rsplit("-", 1)[1])
            post = port.output / f"xalw-core-{sequence + 1:04d}.actual-results.json"
            original_post = post.read_bytes()
            post_row = object_value(array(read(post)["rows"], "post ITEM")[0])
            item, snapshot = object_value(post_row["result"]), object_value(post_row["after_snapshot"])
            for changed in ({**post_row, "result": {**item, "inventory_view_visible": False}},
                    {**post_row, "result": {**item, "equipped": True}},
                    {**post_row, "result": {**item, "loaded_source_pins_verified": False}},
                    {**post_row, "after_snapshot": {**snapshot, "date_raw": 53144352}}):
                post.write_text(json.dumps({"rows": [changed]}), encoding="utf-8")
                altered = {**journal, "native_records": historical._native_files(port.output)}
                with self.subTest(post=changed), self.assertRaises(ValueError):
                    curse.evaluate(context, manifest=port.manifest, reviewer="unit-root", journal=altered)
            post.write_bytes(original_post)
            self.assertEqual(curse.verify_case(context), result)

    def test_real_zero_wallet_consumers_reject_bad_fields_nonzero_and_wrong_executable(self) -> None:
        for fault in ("null_gold", "empty_gold", "duplicate_gold", "missing_zero_prestige", "missing_gold_nonzero_native", "wrong_zero_exe"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                context, result, port = run_fixture(Path(temporary), fault=fault)
                self.assertEqual(result["status"], "BLOCKED", result.get("error"))
                self.assertEqual((port.saves, port.day), (5, 16))
                self.assertEqual(curse.verify_case(context), result)

    def test_unknown_zero_wallet_source_blocks_actual_consumer_before_save_six(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary), fault="unknown_zero_source")
            self.assertEqual(result["status"], "BLOCKED", result.get("error"))
            self.assertEqual((port.saves, port.day), (5, 16))
            self.assertIn("qualified exact CK3 source", str(result["error"]))
            self.assertEqual(curse.verify_case(context), result)

    def test_real_prepare_session_seven_save_producers_all_consumers_and_retained_verify(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary))
            self.assertEqual(result["status"], "PASS", result.get("error"))
            self.assertEqual((port.saves, port.day, port.equip_count), (7, 17, 5))
            self.assertEqual(curse.verify_case(context), result)
            observed = field(array(result["checks"], "checks")[0], "observed")
            self.assertEqual(field(observed, "next_day_wallet_change_raw_decimal"), "300000")
            self.assertEqual(field(observed, "next_day_stress_change"), -1)
            self.assertFalse(result["business_pass"])
            self.assertFalse(result["product_release_pass"])
            charged = read(port.output / "curse-checkpoint-05.json")
            charged_base = field(field(charged, "projection"), "base")
            self.assertEqual(field(field(charged_base, "saved_vitals"), "gold_raw_decimal"), "0")
            self.assertEqual(field(field(charged_base, "native_vitals"), "gold_raw_decimal"), "0")
            melted = Path(str(field(field(field(field(charged, "base"), "response"), "melted_save"), "path")))
            self.assertNotIn("gold={", melted.read_text(encoding="utf-8"))
            base = object_value(field(charged, "base"))
            response = object_value(field(base, "response"))
            for changed in (
                {**base, "response": {**response, "date_raw": 53144328}},
                {**base, "response": {**response, "melted_save": pin(melted.with_name("original.ck3"))}},
            ):
                with self.subTest(base=changed), self.assertRaises(ValueError):
                    curse.consume_observation({**charged, "base": changed}, context=context, manifest=port.manifest, reviewer="unit-root")
            item = read(Path(str(field(field(base, "item_native"), "path"))))
            row = object_value(array(item["rows"], "native rows")[0])
            snapshot = object_value(row["after_snapshot"])
            snapshot["played_character_gold"] = {"raw": 1, "scale": 100000}
            inconsistent = write_once(port.output / "authored-inconsistent-item.json",
                {"rows": [{**row, "after_snapshot": snapshot}]})
            with self.assertRaisesRegex(ValueError, "Independent native paused vitals differ"):
                curse.consume_observation({**charged, "base": {**base, "item_native": inconsistent}},
                    context=context, manifest=port.manifest, reviewer="unit-root")
            deployed = read(port.state / "profile/mod-content/fixture/_case_contract.json")
            sources = mapping(deployed["caller_sources"], "real prepared caller sources")
            for name in ("prepare_curse_fixture.py", "curse_representative_acceptance_adapter.py"):
                self.assertEqual(sources[name], pin(curse.TOOLS / name))

    def test_r18_initial_wallet_failure_is_retained_before_any_equipment_or_day(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary), fault="wrong_initial_wallet")
            self.assertEqual(result["status"], "BLOCKED", result.get("error"))
            self.assertEqual((port.saves, port.equip_count, port.day), (1, 0, 0))
            self.assertNotIn(core.EQUIP, port.tools)
            self.assertTrue((port.output / "curse-checkpoint-01.json").is_file())
            self.assertIn("saved Q100000=27600000, native Q100000=27600000", str(result["error"]))
            self.assertEqual([field(check, "status") for check in array(result["checks"], "checks")], ["BLOCKED"] * 5)
            self.assertFalse(result["case_contract_qualified"])
            self.assertFalse(result["gui_contract_qualified"])
            self.assertEqual(curse.verify_case(context), result)

    def test_native_health_unavailable_keeps_other_four_checks_and_no_fake_health(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary), fault="health_unavailable")
            self.assertEqual(result["status"], "BLOCKED", result.get("error"))
            self.assertEqual([field(check, "status") for check in array(result["checks"], "checks")], ["BLOCKED", "PASS", "PASS", "PASS", "PASS"])
            self.assertEqual((port.saves, port.day), (7, 17))
            self.assertEqual(curse.verify_case(context), result)

    def test_missing_modifier_wrong_health_shortage_recharge_and_candidate_reroll_cannot_pass(self) -> None:
        for fault in ("missing_modifier", "wrong_health", "negative_wallet", "same_day_charge", "daily_repeat", "reroll"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                context, result, _ = run_fixture(Path(temporary), fault=fault)
                self.assertEqual(result["status"], "FAIL", result.get("error"))
                self.assertEqual(curse.verify_case(context), result)

    def test_health_fixed_point_bool_is_rejected_at_real_consumer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            _, result, port = run_fixture(Path(temporary), fault="bad_health_scale")
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual((port.day, port.equip_count), (0, 0))

    def test_unknown_equipment_never_replays_or_advances(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary), fault="unknown_equip")
            self.assertEqual(result["status"], "BLOCKED")
            self.assertTrue(result["original_action_unknown"])
            self.assertEqual((port.saves, port.equip_count, port.day), (1, 1, 0))
            self.assertEqual(curse.verify_case(context), result)

    def test_closed_contract_types_source_deployment_and_persisted_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary))
            self.assertEqual(result["status"], "PASS", result.get("error"))
            curse.validate_contract(json.loads(json.dumps(context)))
            original = mapping(context["case_contract"], "contract")
            for changed in ({**original, "maximum_natural_days": True}, {**original, "maximum_checkpoints": 7.0}, {**original, "extra": None}, {key: value for key, value in original.items() if key != "schema_version"}):
                with self.assertRaises(ValueError):
                    curse.validate_contract({**context, "case_contract": changed})
            checkpoint = read(port.output / "curse-checkpoint-01.json")
            for mutation in ({**checkpoint, "projection": {}}, {key: value for key, value in checkpoint.items() if key != "candidate_native"}):
                with self.assertRaises(ValueError):
                    curse.consume_observation(mutation, context=context, manifest=port.manifest, reviewer="unit-root")
            loaded = port.state / "profile/mod-content/fixture/common/scripted_effects/xalw_curse_inputs.txt"
            loaded.write_text(loaded.read_text(encoding="utf-8-sig") + "\n# drift\n", encoding="utf-8-sig")
            with self.assertRaises(ValueError):
                curse.verify_case(context)

    def test_initial_script_has_only_inputs_refresh_and_one_production_owner_handoff(self) -> None:
        source = emitter.render_initial_inputs()
        self.assertEqual(source.count("xalw_refresh_artifact_effect = yes"), 2)
        self.assertEqual(source.count("xalw_discover_owner_effect = yes"), 1)
        initial = Script(source)
        owner = initial.named("xalw_curse_initialize_effect")
        debit, credit = initial.scalar(owner, "remove_short_term_gold"), initial.scalar(owner, "add_gold")
        self.assertEqual((debit.value, credit.value), ("gold", "20"))
        self.assertLess(debit.start, credit.start)
        self.assertFalse(initial.descendants(owner, "add_gold"))
        for forbidden in ("xalw_content_monthly_effect", "xalw_owner_monthly_effect", "xalw_content_payment", "xalw_content_month_done", "remove_variable", "equip_artifact", "destroy_artifact", "PASS"):
            self.assertNotIn(forbidden, source)

    def test_real_source_qualifier_rejects_script_and_executable_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            game = root / "game"
            needed = {"common/scripted_effects/00_ep1_artifact_creation_effects.txt", "common/on_action/game_start.txt",
                "common/on_action/inventory_on_actions.txt", "common/artifacts/types/00_types.txt", "common/modifiers/00_artifact_modifiers.txt"}
            bindings: list[SourceBinding] = []
            for relative in sorted(needed):
                path = game / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("authored vanilla boundary: " + relative, encoding="utf-8")
                bindings.append(SourceBinding(relative, pin(path)["sha256"]))
            executable = root / "binaries/ck3.exe"
            executable.parent.mkdir()
            executable.write_bytes(b"authored executable boundary")
            with patch.object(emitter, "GAME_SOURCES", tuple(bindings)), patch.object(emitter, "EXPECTED_EXE_SHA", pin(executable)["sha256"]):
                self.assertEqual(set(emitter.qualify_fixture_sources(game)), needed | {"binaries/ck3.exe"})
                executable.write_bytes(b"changed executable")
                with self.assertRaises(ValueError):
                    emitter.qualify_fixture_sources(game)
                executable.write_bytes(b"authored executable boundary")
                (game / bindings[0].relative).write_text("drift", encoding="utf-8")
                with self.assertRaises(ValueError):
                    emitter.qualify_fixture_sources(game)

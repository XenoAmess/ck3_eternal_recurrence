"""Authored game boundary; real preparation, Session, producers and consumers.

The authored calendar/native state is never live CK3 evidence. Actual shared
day projection and real Root producer/file-validation paths run in these tests.
"""
from __future__ import annotations

from datetime import date, timedelta
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import acceptance_adapter as core
from acceptance_contract import Frame, Object, Pin, array, field, integer, mapping, object_value, pin, read, write_once
from ck3_mod_acceptance_native_day import STEP, project_native_day
from management_event_contract import source_option_index
from startup_actor_binding import StartupActorBinding
from test_checkpoint_artifacts import AUTHORED_ARTIFACTS, authored_checkpoint_text
from test_npc_saved_observer import variable
from test_preview_acceptance_adapter import context_fixture as preview_context
from test_threshold_acceptance_adapter import ThresholdPort, qualify_zero_gold_context
from cold_persistence_observer import compare_persistence, consume_checkpoint
from checkpoint_callback import checked_pin
from prepare_fixture import InitialFeedingImprint
import suppression_timer_acceptance_adapter as timer
import threshold_acceptance_adapter as historical


def context_fixture(root: Path, *, qualified_zero_gold: bool = False) -> Object:
    context = preview_context(root)
    if qualified_zero_gold:
        qualify_zero_gold_context(context)
    context["case"] = timer.CASE
    context["case_contract"] = read(timer.TOOLS / timer.CONTRACT_NAME)
    context["case_spec"] = read(timer.TOOLS / "suppression_timer.registry.json")
    context["state_dir"] = str(root / "timer-state")
    context["output"] = str(root / "timer-prepared")
    Path(str(context["output"])).mkdir()
    prepared = timer.prepare_case(context)
    if field(prepared, "runtime_status") != "NOT_RUN":
        raise AssertionError("Preparation cannot grant game qualification")
    context["output"] = str(root / "timer-output")
    Path(str(context["output"])).mkdir()
    return context


class TimerPort(ThresholdPort):
    def __init__(self, context: Object, *, fault: str | None = None) -> None:
        super().__init__(context, inventory_refusal=fault == "inventory_refusal")
        self.level, self.xp, self.growth = 1, 92, 0
        self.chain, self.timer_sequence = 0, 0
        self.fault = fault
        if fault == "zero_wallet":
            self.gold = 70
        self.suppression_intents = 0
        self.renewal_intents = 0
        # CursePort reuses this authored transport with its own initial fixture.
        # Only the timer contract declares this persistence seed.
        self.initial_imprint = (InitialFeedingImprint.parse(field(field(context, "case_contract"), "initial_feeding_imprint"))
            if field(context, "case") == timer.CASE else None)

    def saved_text(self) -> str:
        source = authored_checkpoint_text(AUTHORED_ARTIFACTS)
        actual_date = date(1066, 9, 15) + timedelta(days=self.day)
        source = source.replace("date=1066.9.15", f"date={actual_date.year}.{actual_date.month}.{actual_date.day}")
        for key, old, new in (("level", 1, self.level), ("xp_in_level", 92, self.xp), ("growth_sequence", 0, self.growth),
                ("last_settled_month", 12801, actual_date.year * 12 + actual_date.month)):
            source = source.replace(variable("xalw_" + key, "value", str(old * 100000)), variable("xalw_" + key, "value", str(new * 100000)))
        values = variable("xalw_suppression_chain", "value", str(self.chain * 100000))
        values += " " + variable("xalw_unsuppressed_equipped_months", "value", "100000" if self.growth else "0")
        if self.timer_sequence:
            values += " " + variable("xalw_suppression_timer_sequence", "value", str(self.timer_sequence * 100000))
        if self.deadline is not None:
            values += " " + variable("xalw_growth_suppressed_until", "value", str(self.deadline * 100000))
        if self.initial_imprint is not None and self.day < self.initial_imprint.days:
            if self.day == 0 and self.fault == "wrong_initial_imprint_type":
                values += " " + variable("xalw_feeding_imprint", "value", "100000")
            elif self.day == 0 and self.fault == "wrong_initial_imprint_flag":
                values += " " + variable("xalw_feeding_imprint", "flag", flag="weapon")
            elif not (self.day == 0 and self.fault == "missing_initial_imprint" or
                    self.renewal_intents == 1 and self.fault == "missing_renewed_imprint"):
                values += " " + variable("xalw_feeding_imprint", "flag", flag=self.initial_imprint.flag)
        source = source.replace(variable("xalw_level", "value", str(self.level * 100000)), values + " " + variable("xalw_level", "value", str(self.level * 100000)), 1)
        source = source.replace(variable("xalw_fixture_target", "artifact", "12"), variable("xalw_fixture_initial_day", "value", "10000000") + " " + variable("xalw_fixture_target", "artifact", "12"), 1)
        gold = "" if self.fault == "zero_wallet" and self.gold == 0 else f"\t\t\tgold={{ value={self.gold} }}\n"
        source = source.replace("\t\talive_data={\n", f"\t\talive_data={{\n{gold}\t\t\tprestige={{ currency={self.prestige} accumulated=1000 }}\n\t\t\tstress={self.stress}\n", 1)
        return source

    def execute_plan(self, steps: list[Object], name: str, timeout: int | float | None = None, reserve: int = 90) -> object:
        step = steps[0]
        if step["tool"] != "ck3_select_event_option" or self.event != "xalw.10":
            return super().execute_plan(steps, name, timeout, reserve)
        args = mapping(step["args"], "authored intent")
        option = integer(args["option_number"], "native source option", 1)
        if option == source_option_index("xalw.10", "xalw.10.suppress") + 1:
            self.suppression_intents += 1
            self.chain, self.timer_sequence, self.deadline = 1, 1, 190
            self.gold -= 24 if self.fault == "wrong_cost" else 25
        elif option == source_option_index("xalw.10", "xalw.10.renew") + 1:
            self.renewal_intents += 1
            if self.deadline is None:
                raise AssertionError("Authored renewal needs its actual initial timer")
            self.deadline = 250 if self.fault == "renew_from_today" else self.deadline + 90
            self.chain = 2
            if self.fault == "new_sequence":
                self.timer_sequence = 2
            self.gold -= 45
        else:
            raise AssertionError("Only ordinary suppression and renewal belong to this scenario")
        self.prestige -= 50
        self.stress += 6
        self.show(None)
        self.tools.append("ck3_select_event_option")
        row: Object = object_value({"ok": True, "plan": step, "result": {"submitted": True}, "after_snapshot": self.frame()})
        if self.fault == "unknown_suppression" and self.suppression_intents == 1:
            row = object_value({"ok": False, "plan": step, "error": "authored unknown original suppression", "after_snapshot": self.frame()})
        write_once(self.output / (name + ".actual-results.json"), {"rows": [row]})
        return [row]

    def advance_day(self, days: int = 1, timeout: float = 300, allow_event_boundary: bool = False, allow_actor_change: bool = False) -> object:
        if days != 1 or not allow_event_boundary or allow_actor_change:
            raise AssertionError("Use the unchanged shared Session single-day policy")
        before = object_value(self.snapshot(require_event_free=False))
        self.day += 1
        if self.day == 90 and self.fault == "old_timer_clears":
            self.deadline = None
        if self.day == 180 and self.fault != "late_expiry":
            self.deadline = None
        if self.day == 198 and self.fault != "no_growth":
            self.level, self.xp, self.growth = 2, 0, 1
        if self.day == 16 and self.fault == "growth_leak":
            self.xp += 1
        after = self.frame()
        name = f"case-natural-day-{self.day:04d}"
        raw: Object = object_value({"id": name, "ok": True, "error": None,
            "plan": {"id": name, "tool": "ck3_execute_step", "args": {"step": STEP}}, "after_snapshot": after,
            "result": {"starting_date_raw": field(before, "date_raw"), "ending_date_raw": field(after, "date_raw"), "step": STEP,
                "source": "native-composite", "backend_id": "native-headless", "paused": True, "requested_horizon_days": 1,
                "active_event": None, "pending_character_interaction": None, "ordinary_events": [], "progress_status": "completed",
                "event_resolution": "not_needed", "actions": []}})
        write_once(self.output / (name + ".actual-results.json"), {"rows": [raw]})
        projected = project_native_day(mapping(raw, "authored native day"), mapping(before, "authored before"), allow_event_boundary=True)
        write_once(self.output / (name + ".native-day-projection.json"), {"raw_public_row_path": str(self.output / (name + ".actual-results.json")),
            "projection_source": "actual-life-advance-one-day", "row": projected})
        return projected


def run_fixture(root: Path, *, fault: str | None = None) -> tuple[Object, Object, TimerPort]:
    context = context_fixture(root, qualified_zero_gold=fault == "zero_wallet")
    port = TimerPort(context, fault=fault)
    binding = StartupActorBinding(91, 124, "9", 53144328, 12801, "a" * 64, "b" * 64)
    with patch.object(StartupActorBinding, "parse", return_value=binding):
        result = timer.run_case(context, port)
    return context, result, port


def authored_q64_snapshots(value: object) -> object:
    """Authored raw ABI boundary only; never alter real game evidence."""
    if isinstance(value, dict):
        result = {key: authored_q64_snapshots(item) for key, item in mapping(value, "authored raw JSON").items()}
        if "diagnostics" in result and "date_raw" in result:
            result["authored_native_FILETIME"] = 18446744073709551614
        return result
    if isinstance(value, list):
        return [authored_q64_snapshots(item) for item in value]
    return value


class SuppressionTimerTests(unittest.TestCase):
    def test_r20_exact_refusal_actual_session_and_retained_timer_consumers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary), fault="inventory_refusal")
            self.assertEqual(result["status"], "PASS", result.get("error"))
            self.assertEqual((port.saves, port.day, port.tools.count(core.OPEN)), (7, 198, 1))
            self.assertEqual(timer.verify_case(context), result)
            observed = field(array(result["checks"], "checks")[0], "observed")
            self.assertGreater(len(array(field(observed, "inventory_gui_evidence"), "GUI evidence")), 0)

    def test_real_timer_producer_zero_omission_and_retained_evaluate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary), fault="zero_wallet")
            self.assertEqual(result["status"], "PASS", result.get("error"))
            self.assertEqual((port.saves, port.day, port.gold), (7, 198, 0))
            self.assertEqual(timer.verify_case(context), result)

    def test_real_prepare_session_seven_producers_all_saved_consumers_and_retained_verify(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary))
            self.assertEqual(result["status"], "PASS", result.get("error"))
            self.assertEqual((port.saves, port.day, port.suppression_intents, port.renewal_intents), (7, 198, 1, 1))
            self.assertLess(integer(result["actual_public_calls_budgeted"], "calls"), 1200)
            self.assertEqual(timer.verify_case(context), result)
            self.assertFalse(result["business_pass"])
            self.assertFalse(result["product_release_pass"])
            observed = field(array(result["checks"], "checks")[0], "observed")
            self.assertEqual((field(observed, "original_deadline"), field(observed, "renewed_deadline")), (190, 280))
            self.assertEqual(field(observed, "actual_natural_hours"), 198 * 24)
            journal = read(Path(str(field(result["journal"], "path"))))
            renewed_ref = checked_pin(array(journal["checkpoints"], "checkpoint refs")[3], "renewed timer checkpoint")
            renewed = read(Path(renewed_ref["path"]))
            saves: list[Pin] = []
            for raw in mapping(journal["native_records"], "native closure").values():
                reference = checked_pin(raw, "original native record")
                native = array(field(read(Path(reference["path"])), "rows"), "native rows")[0]
                if field(field(native, "plan"), "tool") == "ck3_save_checkpoint":
                    checkpoint = field(field(native, "result"), "checkpoint")
                    if field(checkpoint, "sha256") == field(renewed["source_save"], "sha256"):
                        saves.append(reference)
            self.assertEqual(len(saves), 1)
            actual = consume_checkpoint(renewed, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root", manifest=port.manifest,
                save_native=saves[0], item_native=renewed["item_native"])
            imprint = actual.artifact.variables["xalw_feeding_imprint"]
            self.assertEqual((imprint.kind, imprint.raw_identity, imprint.flag), ("flag", None, "primary_armament"))
            self.assertEqual(actual.sample.level, 1)
            self.assertEqual(actual.sample.xp, 92)
            # Authored cold boundary, not another game Save: the real timer
            # producer/consumer source now contains all requested cold features.
            after = replace(actual, run_id="authored-cold-run", load_save={**actual.load_save, "path": str(port.output / "authored-cold-save.ck3")})
            self.assertTrue(all(check["status"] == "PASS" for check in compare_persistence(actual, after)))
            first = read(Path(str(field(array(journal["checkpoints"], "checkpoints")[0], "path"))))
            for mutation in ({**first, "machine_id": "other"}, {**first, "projection": {}}, {key: value for key, value in first.items() if key != "response"}):
                with self.assertRaises(ValueError):
                    historical.consume_observation(mutation, context=context, manifest=port.manifest, reviewer="unit-root")
            # Independent raw-consumer regression. Save callbacks above retain
            # their original sources; this re-authored native-only input cannot
            # be promoted to the earlier retained whole-case qualification.
            paths = (*port.output.glob("case-snapshot-*.actual-results.json"), *port.output.glob("case-natural-day-*.json"))
            for path in paths:
                value: object = json.loads(path.read_text(encoding="utf-8"))
                path.write_text(json.dumps(authored_q64_snapshots(value)), encoding="utf-8")
            initial_frame = Frame(3, 2, 53144328, 91, 124, "9")
            final_frame = Frame.parse(port.frame(), run_id="unit-run", machine_id="unit-machine", manifest=port.manifest)
            self.assertEqual(timer._audit_natural(mapping(timer._natural_files(port.output), "native-only authored closure"), context=context,
                manifest=port.manifest, first=initial_frame, final=final_frame), 198 * 24)
            self.assertFalse(timer._same_native({"q": 18446744073709551614}, {"q": 18446744073709551615}))

    def test_wrong_cost_renewal_origin_sequence_old_event_expiry_and_growth_cannot_pass(self) -> None:
        for fault in ("wrong_cost", "renew_from_today", "new_sequence", "old_timer_clears", "late_expiry", "no_growth", "growth_leak"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                context, result, _ = run_fixture(Path(temporary), fault=fault)
                self.assertEqual(result["status"], "FAIL", result.get("error"))
                self.assertEqual(timer.verify_case(context), result)

    def test_unknown_suppression_is_not_repeated_or_followed_by_days(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary), fault="unknown_suppression")
            self.assertEqual(result["status"], "BLOCKED")
            self.assertTrue(result["original_action_unknown"])
            self.assertEqual((port.day, port.suppression_intents, port.renewal_intents), (0, 1, 0))
            self.assertEqual(timer.verify_case(context), result)

    def test_resources_are_observed_initial_inputs_not_synthesized_payment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context = context_fixture(Path(temporary))
            port = TimerPort(context)
            port.gold = 20
            binding = StartupActorBinding(91, 124, "9", 53144328, 12801, "a" * 64, "b" * 64)
            with patch.object(StartupActorBinding, "parse", return_value=binding):
                result = timer.run_case(context, port)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual((port.saves, port.day, port.suppression_intents), (1, 0, 0))
            self.assertEqual(timer.verify_case(context), result)

    def test_actual_fixture_imprint_is_required_before_payment_and_at_renewed_source(self) -> None:
        for fault in ("missing_initial_imprint", "wrong_initial_imprint_type", "wrong_initial_imprint_flag", "missing_renewed_imprint"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                context, result, port = run_fixture(Path(temporary), fault=fault)
                self.assertEqual(result["status"], "BLOCKED", result.get("error"))
                self.assertIn("fixture imprint", str(result.get("error")))
                self.assertFalse(result["original_action_unknown"])
                self.assertEqual(timer.verify_case(context), result)
                if fault == "missing_renewed_imprint":
                    self.assertEqual((port.saves, port.day, port.suppression_intents, port.renewal_intents), (4, 60, 1, 1))
                else:
                    self.assertEqual((port.saves, port.day, port.suppression_intents, port.renewal_intents), (1, 0, 0, 0))
                    self.assertNotIn(core.EQUIP, port.tools)
                self.assertEqual(len(array(result["checks"], "original timer checks")), len(timer.CHECKS))

    def test_contract_fields_types_registry_and_json_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context = context_fixture(Path(temporary))
            self.assertEqual(timer.verify_case(context)["status"], "NOT_RUN")
            timer.validate_contract(json.loads(json.dumps(context)))
            config = mapping(context["case_contract"], "contract")
            for changed in ({**config, "schema_version": True}, {**config, "maximum_checkpoints": 7.0},
                    {**config, "maximum_natural_days": 212.0}, {key: value for key, value in config.items() if key != "maximum_checkpoints"}, {**config, "unknown": None}):
                with self.assertRaises(ValueError):
                    timer.validate_contract({**context, "case_contract": changed})
            spec = mapping(context["case_spec"], "registry")
            with self.assertRaises(ValueError):
                timer.validate_contract({**context, "case_spec": {**spec, "required_mcp_tools": []}})
            manifest = read(Path(str(context["state_dir"])) / "profile/mod-content/fixture/_case_contract.json")
            originals = mapping(field(manifest, "fixture_emission"), "emission")
            fixture_source = Path(str(field(field(field(originals, "files"), "common/scripted_effects/xalw_fixture_observer.txt"), "path")))
            initial = fixture_source.read_text(encoding="utf-8-sig")
            self.assertNotIn("xalw_growth_suppressed_until", initial)
            self.assertNotIn("xalw_suppress_effect", initial)
            self.assertNotIn("add_gold", initial)
            self.assertIn("name = xalw_feeding_imprint value = flag:primary_armament days = 90", initial)
            self.assertNotIn("xalw_feed_material_effect", initial)
            self.assertEqual(field(manifest["config"], "initial_feeding_imprint"),
                InitialFeedingImprint.parse(field(config, "initial_feeding_imprint")).to_json())
            self.assertFalse(field(field(manifest["config"], "initial_feeding_imprint"), "feeding_action_credit"))
            loaded = Path(str(context["state_dir"])) / "profile/mod-content/fixture/common/scripted_effects/xalw_fixture_observer.txt"
            loaded.write_bytes(loaded.read_bytes().replace(b"days = 90", b"days = 89"))
            with self.assertRaises(ValueError):
                timer.prepared_sources(context, Path(str(context["state_dir"])))

    def test_retained_deployment_natural_receipts_and_false_equal_projection_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary))
            self.assertEqual(result["status"], "PASS", result.get("error"))
            journal = read(Path(str(field(result["journal"], "path"))))
            with self.assertRaisesRegex(ValueError, "closure"):
                timer.evaluate(context, manifest=port.manifest, reviewer="unit-root", journal={**journal, "natural_records": {}})
            checkpoints = array(journal["checkpoints"], "checkpoint refs")
            first = read(Path(str(field(checkpoints[0], "path"))))
            projected = mapping(first["projection"], "actual projection")
            sample = mapping(projected["sample"], "sample")
            changed = {**first, "projection": {**projected, "sample": {**sample, "level": True}}}
            with self.assertRaisesRegex(ValueError, "projection"):
                historical.consume_observation(changed, context=context, manifest=port.manifest, reviewer="unit-root")
            loaded = port.state / "profile/mod-content/product/extra.txt"
            loaded.write_text("unqualified extra", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "closure"):
                timer.verify_case(context)
            loaded.unlink()
            native = mapping(journal["natural_records"], "natural closure")
            first_key = next(key for key in native if key.endswith(".actual-results.json"))
            Path(str(field(native[first_key], "path"))).write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                timer.verify_case(context)

    def test_public_selection_cold_imports_standalone_adapter_without_registry_mutation(self) -> None:
        script = "from pathlib import Path\nfrom ck3_mod_acceptance import Selection\ns=object.__new__(Selection)\ns.adapter_path=Path(" + repr(str(timer.TOOLS / "suppression_timer_acceptance_adapter.py")) + ")\ns.locations={'repo_root':Path(" + repr(str(timer.TOOLS.parents[1])) + ")}\ns.runtime_environment={}\ns.manifest_path_key=lambda row:Path('.')\ns.manifest={'source_root':{}}\nm=s.load_adapter()\nassert callable(m.prepare_case) and callable(m.run_case) and callable(m.verify_case)\n"
        completed = subprocess.run([sys.executable, "-B", "-X", "utf8", "-c", script], cwd=timer.TOOLS.parents[1], capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "PYTHONPATH": str(timer.TOOLS.parents[1] / "tools")})
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()

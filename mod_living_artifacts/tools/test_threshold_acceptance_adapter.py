"""Authored native state drives actual Session, Save producer and both consumers.

No authored state here is game evidence. Non-10 actual stress deltas deliberately
exercise the narrower paid-stress scope rather than a hardcoded adjustment formula.
"""
from __future__ import annotations

from dataclasses import replace
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Protocol, runtime_checkable
import unittest
from unittest.mock import patch

import acceptance_adapter as core
from acceptance_contract import Frame, Object, array, field, integer, mapping, object_value, pin, read, write_once
from checkpoint_artifacts import inspect_inputs
from checkpoint_callback import checked_pin, verify_readback
from management_event_contract import source_option_index
import prepare_threshold_fixture as emitter
from startup_actor_binding import StartupActorBinding
from test_checkpoint_artifacts import AUTHORED_ARTIFACTS, authored_checkpoint_text
from test_npc_acceptance_adapter import public_round_trip
from test_npc_saved_observer import variable
from test_preview_acceptance_adapter import PreviewPort, context_fixture as preview_context
import threshold_acceptance_adapter as threshold
import ck3_mod_acceptance as public_entry


@runtime_checkable
class PublicSelection(Protocol):
    def prepare(self, inputs_path: Path, output: Path) -> object: ...
    def adapter_context(self, output: Path | None = None, inputs: object = None) -> object: ...
    def verify(self) -> object: ...
    def describe(self) -> object: ...


@runtime_checkable
class PublicSelectionFactory(Protocol):
    def __call__(self, runtime_path: Path, products_path: Path, product_key: str, case_id: str,
                 context_path: Path | None = None, prepared_path: Path | None = None) -> PublicSelection: ...


def public_selection(runtime: Path, products: Path, context: Path | None = None, prepared: Path | None = None) -> PublicSelection:
    factory: object = public_entry.Selection
    if not isinstance(factory, PublicSelectionFactory):
        raise AssertionError("Actual shared Selection factory required")
    return factory(runtime, products, "living-artifacts", emitter.CASE, context, prepared)


def public_pipeline(root: Path, *, unknown_train: bool = False) -> tuple[PublicSelection, Object, ThresholdPort, list[str], Path]:
    """Actual public preparation/Session/retained verifier, authored native/close seams."""
    root.mkdir()
    provider = root / "provider"
    provider.mkdir()
    base = preview_context(provider)
    repo = Path(__file__).resolve().parents[2]
    source_root = Path(str(base["shared_source_root"]))
    paths: dict[str, Path] = {"source_root": source_root}
    for name in ("host", "source_index", "native_source_index", "dll", "injector"):
        path = root / (name + ".never-executed")
        path.write_text("Authored source-only public verification input\n", encoding="utf-8")
        paths[name] = path
    manifest = object_value(read(Path(str(field(field(base, "runtime_manifest"), "path")))))
    manifest.update(schema=public_entry.MANIFEST_SCHEMA, source_root={"path_key": "source_root"},
        host={"path_key": "host", "bytes": paths["host"].stat().st_size, "sha256": pin(paths["host"])["sha256"]},
        source_index={"path_key": "source_index", "bytes": paths["source_index"].stat().st_size, "sha256": pin(paths["source_index"])["sha256"]},
        native_source_index={"path_key": "native_source_index", "bytes": paths["native_source_index"].stat().st_size, "sha256": pin(paths["native_source_index"])["sha256"]},
        native={name: {"path_key": name, "bytes": paths[name].stat().st_size, "sha256": pin(paths[name])["sha256"]} for name in ("dll", "injector")})
    manifest_pin = write_once(root / "public-manifest.json", manifest)
    runtime_path = root / "runtime.json"
    write_once(runtime_path, {"schema": public_entry.RUNTIME_SCHEMA, "manifest": manifest_pin, "python": sys.executable,
        "repo_root": str(repo), "game_dir": base["game_dir"], "userdir_root": str(root / "profiles"),
        "artifacts_root": str(root / "live"), "paths": {name: str(path) for name, path in paths.items()}})
    registry = object_value(read(repo / "tools/ck3_mod_acceptance_products.json"))
    product = object_value(field(field(registry, "products"), "living-artifacts"))
    case = object_value(read(emitter.TOOLS / "threshold_suppression.registry.json"))
    case["adapter"] = {"path": str(emitter.TOOLS / "threshold_acceptance_adapter.py"), "config": str(emitter.TOOLS / emitter.CONTRACT_NAME)}
    product["cases"] = [case]
    registry["products"] = {"living-artifacts": product}
    products_path = root / "products.json"
    write_once(products_path, registry)
    state = root / "public-state"
    inputs_path = root / "inputs.json"
    write_once(inputs_path, {"state_dir": str(state), "case_inputs": base["case_inputs"]})
    prepared = root / "public-prepared"
    public_selection(runtime_path, products_path).prepare(inputs_path, prepared)
    prepared_path = prepared / "prepared-case.json"
    run = root / "live/unit-run"
    output = run / "case-output"
    output.mkdir(parents=True)
    context_path = run / "context.json"
    context = object_value({"schema": public_entry.CONTEXT_SCHEMA, "run_id": "unit-run", "run_dir": str(run),
        "product": "living-artifacts", "case": emitter.CASE, "prepared_case": pin(prepared_path),
        "case_inputs": base["case_inputs"], "reviewer": "unit-root"})
    write_once(context_path, context)
    # The actual constructor builds the original argv; no run/allocator/host is called.
    selected = public_selection(runtime_path, products_path, context_path, prepared_path)
    described = selected.describe()
    original_argv = field(described, "host_argv")
    required = [manifest_pin, pin(prepared_path), *[pin(path) for name, path in paths.items() if name != "source_root"]]
    required.extend(pin(path) for path in (runtime_path, products_path, emitter.TOOLS / "threshold_acceptance_adapter.py", emitter.TOOLS / emitter.CONTRACT_NAME))
    for path in prepared.rglob("*"):
        if path.is_file():
            required.append(pin(path))
    files = {reference["path"]: {"bytes": reference["bytes"], "sha256": reference["sha256"]} for reference in required}
    frozen = write_once(run / "frozen-argv.json", {"run_id": "unit-run", "argv": original_argv, "runtime_environment": {},
        "runtime_manifest": manifest_pin, "source_root": str(source_root), "files": files})
    context["frozen_argv"] = object_value(frozen)
    context_path.write_text(json.dumps(context), encoding="utf-8")
    selected = public_selection(runtime_path, products_path, context_path, prepared_path)
    actual_context = object_value(selected.adapter_context())
    port = ThresholdPort(actual_context, unknown_train=unknown_train)
    binding = StartupActorBinding(91, 124, "9", 53144328, 12801, "a" * 64, "b" * 64)
    with patch.object(StartupActorBinding, "parse", return_value=binding):
        result = object_value(threshold.run_case(actual_context, port))
    write_once(output / "normal-close-result.json", {"normal_close_qualified": True, "authored_close_boundary_only": True})
    args = ["verify", "--runtime", str(runtime_path), "--products", str(products_path), "--product", "living-artifacts",
        "--case", emitter.CASE, "--prepared-case", str(prepared_path), "--run-context", str(context_path)]
    return selected, result, port, args, output


def public_verify_output(arguments: list[str]) -> tuple[int, Object]:
    stream = io.StringIO()
    with redirect_stdout(stream):
        code = public_entry.main(arguments)
    return code, object_value(json.loads(stream.getvalue()))


def legacy_public_pipeline_worker(root: Path) -> None:
    """Fresh-process consumer of the byte-pinned historical producer fixture."""
    check = unittest.TestCase()
    selected, produced, port, arguments, output = public_pipeline(root / "known")
    result_path = output / threshold.RESULT_NAME
    original_bytes = result_path.read_bytes()
    original = pin(result_path)
    check.assertEqual(produced["schema"], "living-artifacts-threshold-case-result-v1")
    check.assertNotIn("gui_contract_qualified", produced)
    check.assertEqual((port.saves, port.day), (7, 47))
    verified = object_value(selected.verify())
    check.assertTrue(verified["case_acceptance_pass"])
    qualification = public_entry.parse_legacy_threshold_gui_qualification_v1(verified["legacy_gui_qualification"])
    check.assertEqual(public_entry.parse_legacy_threshold_gui_qualification_v1(json.loads(json.dumps(qualification))), qualification)
    check.assertEqual(qualification["retained_result"], original)
    check.assertEqual(public_verify_output(arguments)[0], 0)
    check.assertEqual(pin(result_path), original)
    for changed in ({**produced, "schema": "living-artifacts-threshold-case-result-v2"},
                    {**produced, "gui_contract_qualified": False}, {**produced, "actual_natural_days": 47.0},
                    {**produced, "case_contract_qualified": 1}, {**produced, "unexpected": True},
                    {name: value for name, value in produced.items() if name != "journal"}):
        result_path.write_text(json.dumps(changed), encoding="utf-8")
        check.assertEqual(public_verify_output(arguments)[0], 2)
    result_path.write_bytes(original_bytes)
    check.assertEqual(pin(result_path), original)
    close_path = output / "normal-close-result.json"
    close_bytes = close_path.read_bytes()
    close_path.write_text(json.dumps({"normal_close_qualified": False}), encoding="utf-8")
    failed_close = public_verify_output(arguments)
    check.assertEqual(failed_close[0], 2)
    check.assertNotIn("legacy_gui_qualification", failed_close[1])
    close_path.write_bytes(close_bytes)
    _, blocked, _, blocked_args, _ = public_pipeline(root / "unknown-action", unknown_train=True)
    check.assertTrue(blocked["original_action_unknown"])
    check.assertEqual(public_verify_output(blocked_args)[0], 2)
    # A semantically identical but unknown producer is a new source, not v1 credit.
    source_path = emitter.TOOLS / "threshold_acceptance_adapter.py"
    with source_path.open("ab") as stream:
        stream.write(b"\n# Authored unknown producer identity.\n")
    _, _, _, unknown_args, _ = public_pipeline(root / "unknown-source")
    unknown_source = public_verify_output(unknown_args)
    check.assertEqual(unknown_source[0], 2)
    check.assertIn("Unsupported legacy threshold producer identity", str(unknown_source[1]))
    print(json.dumps({"known_legacy_cli_exit": 0, "wrong_version_shape_type_false_cli_exit": 2,
        "failed_close_cli_exit": 2, "unknown_action_cli_exit": 2, "unknown_source_cli_exit": 2,
        "legacy_producer_saves": port.saves, "legacy_producer_natural_days": port.day, "old_result_unchanged": True,
        "qualification": qualification}))


def qualify_zero_gold_context(context: Object, *, game: tuple[str, str] | None = None) -> None:
    """Authored known-version boundaries, never a claim of an actual CK3 run."""
    version, digest = threshold.ZERO_GOLD_GAME if game is None else game
    reference = field(context, "runtime_manifest")
    path = Path(str(field(reference, "path")))
    manifest = object_value(read(path))
    game_record: Object = {"version": version, "exe_sha256": digest}
    manifest["game"] = game_record
    path.write_text(json.dumps(manifest), encoding="utf-8")
    context["runtime_manifest"], context["shared_game"] = object_value(pin(path)), game_record
    engine = Path(str(context["shared_source_root"])) / "tools/fixture_engine_prepare.py"
    engine.write_text(engine.read_text(encoding="utf-8").replace("unit-version", version).replace("a" * 64, digest), encoding="utf-8")


def context_fixture(root: Path, *, qualified_zero_gold: bool = False) -> Object:
    # Reuse authored shared-provider configuration; threshold still runs its own
    # actual preparation and copied-profile/source-closure verification.
    context = preview_context(root)
    if qualified_zero_gold:
        qualify_zero_gold_context(context)
    context["case"] = emitter.CASE
    context["case_contract"] = read(emitter.TOOLS / emitter.CONTRACT_NAME)
    context["case_spec"] = read(emitter.TOOLS / "threshold_suppression.registry.json")
    context["state_dir"] = str(root / "threshold-state")
    context["output"] = str(root / "threshold-prepared")
    Path(str(context["output"])).mkdir()
    prepared = threshold.prepare_case(context)
    if field(prepared, "runtime_status") != "NOT_RUN":
        raise AssertionError("Initial source preparation cannot claim runtime PASS")
    context["output"] = str(root / "threshold-case-output")
    Path(str(context["output"])).mkdir()
    return context


class ThresholdPort(PreviewPort):
    def __init__(self, context: Object, *, bad_growth: bool = False, charge: int = 75,
                 monthly_leak: bool = False, reset_on_equip: bool = False, missing_stress: bool = False,
                 unknown_train: bool = False, no_curse: bool = False, wrong_timer: bool = False,
                  zero_wallet: bool = False, inventory_refusal: bool = False) -> None:
        super().__init__(context)
        self.level, self.xp, self.growth = 10, 992, 0
        self.gold, self.prestige, self.stress = 1000, 1000, 20
        self.zero_wallet = zero_wallet
        if zero_wallet:
            self.gold = 75
        self.trained, self.suppressed = False, False
        self.deadline: int | None = None
        self.charge = charge
        self.bad_growth, self.monthly_leak, self.reset_on_equip = bad_growth, monthly_leak, reset_on_equip
        self.missing_stress, self.unknown_train, self.no_curse, self.wrong_timer = missing_stress, unknown_train, no_curse, wrong_timer
        self.train_intents = 0
        self.inventory_visible = not inventory_refusal
        if inventory_refusal:
            from inventory_gui_contract import GUARD_RELATIVE
            shared = Path(str(context["shared_source_root"]))
            guard = shared / GUARD_RELATIVE
            guard.parent.mkdir(parents=True)
            shutil.copyfile(Path(__file__).resolve().parents[2] / GUARD_RELATIVE, guard)
            self.frozen = {"run_id": "unit-run", "source_root": str(shared)}

    def root_checkpoint(self, name: str, request: Object, reserve: int = 90) -> object:
        if request["schema"] != "living-artifacts-inventory-gui-open-request-v1":
            return super().root_checkpoint(name, request, reserve)
        from test_inventory_gui_contract import response_fixture
        from inventory_gui_contract import InventoryOpenResponse
        fixtures = Path(__file__).resolve().parent / "fixtures"
        retained = read(fixtures / "r20-inventory-open-root-result.json")
        if set(retained) != set(InventoryOpenResponse.__required_keys__) or retained["status"] != "completed":
            raise AssertionError("Retained R20 completed callback shape changed")
        write_once(self.output / (name + "-awaiting.json"), {**request, "original_hold_deadline": 1800000000,
            "reserve_seconds": reserve, "operator_reviewer": self.operator_reviewer})
        images = self.output / (name + "-authored-geometry")
        images.mkdir()
        response, _, _ = response_fixture(images, date_raw=53144328 + self.day * 24,
            target=str(request["target_artifact_id"]), refusal=checked_pin(request["original_native_refusal"], "original refusal"))
        write_once(self.output / (name + "-root-result.json"), response)
        self.inventory_visible = True
        return response

    def frame(self) -> Object:
        result = super().frame()
        hello = mapping(field(field(result, "diagnostics"), "hello"), "authored hello")
        hello["expected_ck3_version"] = field(field(self.manifest, "game"), "version")
        hello["expected_ck3_sha256"] = field(field(self.manifest, "game"), "exe_sha256")
        actor = mapping(result["played_character"], "authored actor")
        if not self.missing_stress:
            actor["stress_points"] = self.stress
        result["played_character"] = object_value(actor)
        diagnostics = mapping(result["diagnostics"], "authored diagnostics")
        diagnostics["hello"] = object_value(hello)
        result["diagnostics"] = object_value(diagnostics)
        result["played_character_gold"] = {"raw": self.gold * 100000, "scale": 100000}
        result["played_character_prestige"] = {"raw": self.prestige * 100000, "scale": 100000}
        return result

    def saved_text(self) -> str:
        source = authored_checkpoint_text(AUTHORED_ARTIFACTS)
        dates = {0: "1066.9.15", 16: "1066.10.1", 47: "1066.11.1"}
        source = source.replace("date=1066.9.15", "date=" + dates[self.day])
        for key, old, new in (("level", 1, self.level), ("xp_in_level", 92, self.xp), ("growth_sequence", 0, self.growth),
                              ("last_settled_month", 12801, 12801 if self.day == 0 else 12802 if self.day == 16 else 12803)):
            source = source.replace(variable("xalw_" + key, "value", str(old * 100000)), variable("xalw_" + key, "value", str(new * 100000)))
        target_values = variable("xalw_suppression_chain", "value", "100000" if self.suppressed else "0") + " " + variable("xalw_curse_1", "value", "100000") + " " + variable("xalw_curse_rank_1", "value", "200000")
        if self.deadline is not None:
            target_values += " " + variable("xalw_growth_suppressed_until", "value", str(self.deadline * 100000)) + " " + variable("xalw_suppression_timer_sequence", "value", "100000")
        source = source.replace(variable("xalw_level", "value", str(self.level * 100000)), target_values + " " + variable("xalw_level", "value", str(self.level * 100000)), 1)
        player_values = variable("xalw_fixture_initial_day", "value", "10000000")
        if self.trained:
            player_values += " " + variable("xalw_training_cooldown", "boolean", "1")
        source = source.replace(variable("xalw_fixture_target", "artifact", "12"), player_values + " " + variable("xalw_fixture_target", "artifact", "12"), 1)
        vitals = "" if self.zero_wallet and self.gold == 0 else f"gold={{ value={self.gold} }}\n\t\t\t"
        vitals += f"prestige={{ currency={self.prestige} accumulated=1000 }}\n"
        if not self.missing_stress:
            vitals += f"\t\t\tstress={self.stress}\n"
        source = source.replace("\t\talive_data={\n", "\t\talive_data={\n\t\t\t" + vitals, 1)
        if self.day:
            modifiers = f"xalw_hunger_{2 if self.suppressed else 1}_modifier"
            if not self.no_curse:
                modifiers += " xalw_content_blood_1_2_modifier"
            source = source.replace('\t\t12={\n', '\t\t12={\n\t\t\tmodifiers={ ' + modifiers + ' }\n', 1)
        return source

    def execute_plan(self, steps: list[Object], name: str, timeout: int | float | None = None, reserve: int = 90) -> object:
        step = steps[0]
        tool = str(step["tool"])
        args = mapping(step["args"], "authored arguments")
        if tool == core.OPEN:
            retained = read(Path(__file__).resolve().parent / "fixtures/r20-inventory-refusal.actual-results.json")
            original = object_value(array(retained["rows"], "retained R20 refusal")[0])
            original["id"], original["plan"] = name, step
            write_once(self.output / (name + ".actual-results.json"), {"rows": [original]})
            self.tools.append(tool)
            return [original]
        if tool == "ck3_save_checkpoint":
            self.tools.append(tool)
            self.saves += 1
            source = self.state / "profile/save games/live.ck3"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(self.saved_text(), encoding="utf-8")
            saved = pin(source)
            result: Object = object_value({"checkpoint": {"status": "saved", "path": saved["path"], "size": saved["bytes"], "sha256": saved["sha256"],
                "date_raw": 53144328 + self.day * 24}, "materialization": {"available": True}})
        elif tool == core.ITEM:
            self.tools.append(tool)
            result = object_value({"available": True, "read_only": True, "loaded_source_pins_verified": True, "personally_owned": True, "inventory_artifact": True,
                "requested_artifact_id": args["artifact_id"], "played_character_id": 91, "date_raw": 53144328 + self.day * 24, "native_equipped_observed": True,
                "equipped": self.equipped, "equipped_slot_index": 0 if self.equipped else None, "effective_slot_index": 0, "replacing_artifact_id": None,
                "can_equip_in_effective_slot": True, "can_unequip": True, "inventory_view_available": True, "inventory_view_visible": self.inventory_visible,
                "owned_ids": [12, 13, 14, 15, 16]})
        elif tool == "ck3_select_event_option" and self.event == "xalw.10":
            self.tools.append(tool)
            option = integer(args["option_number"], "authored source option", 1)
            if option == source_option_index("xalw.10", "xalw.10.train") + 1:
                self.train_intents += 1
                self.trained, self.xp = True, 25
                self.prestige -= 50
                self.stress += 7
            elif option == source_option_index("xalw.10", "xalw.10.suppress") + 1:
                self.suppressed = True
                self.gold -= self.charge
                self.prestige -= 50
                self.stress += 6
                self.deadline = 207 if self.wrong_timer else 206
            else:
                raise AssertionError("Scenario must only choose actual train/suppress")
            self.show(None)
            if self.unknown_train and self.train_intents == 1 and not self.suppressed:
                rows = [object_value({"ok": False, "error": "authored unknown original selection", "plan": step, "after_snapshot": self.frame()})]
                write_once(self.output / (name + ".actual-results.json"), {"rows": rows})
                return rows
            result = {"submitted": True}
        else:
            if tool == core.EQUIP and self.reset_on_equip and self.suppressed:
                self.deadline = None
            return super().execute_plan(steps, name, timeout, reserve)
        rows = [object_value({"ok": True, "plan": step, "result": result, "after_snapshot": self.frame()})]
        write_once(self.output / (name + ".actual-results.json"), {"rows": rows})
        return rows

    def advance_day(self, days: int = 1, timeout: float = 300, allow_event_boundary: bool = False, allow_actor_change: bool = False) -> object:
        if days != 1:
            raise AssertionError("Only ordinary one-day Session progression is permitted")
        self.day += 1
        if self.day == 16 and not self.bad_growth:
            self.level, self.xp, self.growth = 11, 0, 1
        if self.day == 47 and self.monthly_leak:
            self.xp += 8
        return {"result": {"after": self.frame()}}


def run_fixture(root: Path, **faults: bool | int) -> tuple[Object, Object, ThresholdPort]:
    context = context_fixture(root, qualified_zero_gold=bool(faults.get("zero_wallet", False)))
    port = ThresholdPort(context, bad_growth=bool(faults.get("bad_growth", False)), charge=int(faults.get("charge", 75)),
        monthly_leak=bool(faults.get("monthly_leak", False)), reset_on_equip=bool(faults.get("reset_on_equip", False)),
        missing_stress=bool(faults.get("missing_stress", False)), unknown_train=bool(faults.get("unknown_train", False)),
        no_curse=bool(faults.get("no_curse", False)), wrong_timer=bool(faults.get("wrong_timer", False)),
        zero_wallet=bool(faults.get("zero_wallet", False)), inventory_refusal=bool(faults.get("inventory_refusal", False)))
    binding = StartupActorBinding(91, 124, "9", 53144328, 12801, "a" * 64, "b" * 64)
    with patch.object(StartupActorBinding, "parse", return_value=binding):
        result = threshold.run_case(context, port)
    return context, result, port


class ThresholdAcceptanceTests(unittest.TestCase):
    def test_r20_exact_refusal_actual_session_and_retained_threshold_consumers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary), inventory_refusal=True)
            self.assertEqual(result["status"], "PASS", result.get("error"))
            self.assertEqual((port.saves, port.day, port.tools.count(core.OPEN)), (7, 47, 1))
            self.assertEqual(threshold.verify_case(context), result)

    def test_r19_retained_zero_wallet_fragment_requires_exact_source_and_native_corroboration(self) -> None:
        fixture = emitter.TOOLS / "fixtures/r19-zero-gold-living-31254.ck3.txt"
        self.assertEqual((fixture.stat().st_size, pin(fixture)["sha256"]),
            (9516, "157449d69de163bf05c3acafe745bfaa8de83900488ab7a291911a2dd3dbc3c6"))
        provenance = read(fixture.with_suffix(".provenance.json"))
        self.assertEqual(field(provenance, "machine_id"), "pc-20260924rtuf-f11af23c08")
        self.assertEqual(field(field(provenance, "fragment"), "sha256"), pin(fixture)["sha256"])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            melted = root / "selected-actor.ck3"
            original = "living={\n" + fixture.read_text(encoding="utf-8") + "}\n"
            melted.write_text(original, encoding="utf-8")
            version, digest = threshold.ZERO_GOLD_GAME
            source = threshold.SavedVitalsSource(pin(melted), Frame(42, 41, 53144712, 31254, 6576, "1"),
                31254, 53144712, threshold.Vitals("0", "220000000", 45), version, digest)
            with self.assertRaisesRegex(ValueError, "corroboration"):
                threshold.saved_vitals(melted, "31254")
            observed = threshold.saved_vitals(melted, "31254", source=source)
            self.assertEqual(observed, source.native)
            self.assertEqual(threshold.Vitals.parse(json.loads(json.dumps(observed.to_json()))), observed)
            other = root / "another-source.ck3"
            other.write_text(original, encoding="utf-8")
            wrong_sources = (
                replace(source, game_version="unknown"), replace(source, exe_sha256="a" * 64),
                replace(source, native=threshold.Vitals("1", "220000000", 45)),
                replace(source, native=threshold.Vitals("0", "220000000", True)),
                replace(source, readback_actor_id=91), replace(source, readback_date_raw=53144736),
                replace(source, frame=replace(source.frame, player_id=91)),
                replace(source, melted_save=pin(other)),
                replace(source, melted_save={**pin(melted), "sha256": "a" * 64}),
            )
            for wrong in wrong_sources:
                with self.subTest(source=wrong), self.assertRaises(ValueError):
                    threshold.saved_vitals(melted, "31254", source=wrong)
            for gold in ("gold=null", "gold={}", "gold={ value=0 value=0 }", "gold={ value=0 } gold={ value=0 }", "gold={ value=nan }"):
                changed = original.replace("\t\talive_data={\n", "\t\talive_data={\n\t\t\t" + gold + "\n", 1)
                melted.write_text(changed, encoding="utf-8")
                with self.subTest(gold=gold), self.assertRaises(ValueError):
                    threshold.saved_vitals(melted, "31254", source=replace(source, melted_save=pin(melted)))
            no_prestige = original.replace("\t\t\tprestige={", "\t\t\tnot_prestige={", 1)
            self.assertNotEqual(no_prestige, original)
            melted.write_text(no_prestige, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "prestige"):
                threshold.saved_vitals(melted, "31254", source=replace(source, melted_save=pin(melted)))

    def test_real_threshold_producer_zero_omission_roundtrip_and_retained_evaluate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary), zero_wallet=True)
            self.assertEqual(result["status"], "PASS", result.get("error"))
            self.assertEqual((port.saves, port.day, port.gold), (7, 47, 0))
            self.assertEqual(threshold.verify_case(context), result)

    def test_legacy_derivation_is_not_a_missing_gui_default_for_other_cases(self) -> None:
        unused = Path("unused-legacy-verification-source")
        for result in (
            {"schema": "living-artifacts-core-case-result-v2", "product": "living-artifacts", "case": "core_continuous", "gui_contract_qualified": False},
            {"schema": "living-artifacts-npc-case-result-v1", "product": "living-artifacts", "case": "npc_continuous", "gui_contract_qualified": False},
            {"schema": "unknown", "product": "living-artifacts", "case": emitter.CASE},
            {"schema": "living-artifacts-threshold-case-result-v1", "product": "another-product", "case": emitter.CASE},
            {"schema": "living-artifacts-threshold-case-result-v1", "product": "living-artifacts", "case": emitter.CASE, "gui_contract_qualified": False},
        ):
            with self.subTest(result=result):
                self.assertIsNone(public_entry._legacy_threshold_gui_qualification_v1(result,
                    loaded_adapter_source=None, adapter_path=unused, contract_path=unused, prepared_path=None,
                    context_path=unused, runtime_path=unused, products_path=unused, manifest_path=unused,
                    required_pins=[], expected_argv=[], expected_environment={}, normal_close_path=unused))

    def test_actual_v2_producer_public_selection_and_cli_exit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            selected, result, port, arguments, output = public_pipeline(Path(temporary) / "v2")
            original = pin(output / threshold.RESULT_NAME)
            self.assertEqual(result["schema"], "living-artifacts-threshold-case-result-v2")
            self.assertTrue(result["gui_contract_qualified"])
            self.assertEqual((port.saves, port.day), (7, 47))
            verified = object_value(selected.verify())
            self.assertTrue(verified["case_acceptance_pass"])
            self.assertTrue(verified["qualified_boundary_pass"])
            self.assertNotIn("legacy_gui_qualification", verified)
            self.assertFalse(verified["business_pass"])
            self.assertEqual(public_verify_output(arguments)[0], 0)
            self.assertEqual(pin(output / threshold.RESULT_NAME), original)
            for changed in ({**result, "gui_contract_qualified": False}, {**result, "gui_contract_qualified": 1},
                            {**result, "gui_contract_qualified": None}, {**result, "schema": "living-artifacts-threshold-case-result-v1"},
                            {name: value for name, value in result.items() if name != "gui_contract_qualified"}):
                (output / threshold.RESULT_NAME).write_text(json.dumps(changed), encoding="utf-8")
                self.assertEqual(public_verify_output(arguments)[0], 2)

    def test_actual_frozen_v1_producer_legacy_public_verification_fresh_process(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "historical-source/mod_living_artifacts/tools"
            source.mkdir(parents=True)
            for original in emitter.TOOLS.iterdir():
                if original.is_file() and (original.suffix == ".json" or original.suffix == ".py" and not original.name.startswith("test_")):
                    shutil.copyfile(original, source / original.name)
            fixture = emitter.TOOLS / "fixtures/threshold-result-v1-adapter.py.txt"
            historical = fixture.read_bytes()
            self.assertEqual((len(historical), pin(fixture)["sha256"]), public_entry.LEGACY_THRESHOLD_ADAPTER_V1)
            (source / "threshold_acceptance_adapter.py").write_bytes(historical)
            repo = Path(__file__).resolve().parents[2]
            environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": os.pathsep.join(map(str, (
                source, repo / "tools", emitter.TOOLS, repo, repo / "ck3_autonomous_player/src")))}
            completed = subprocess.run([sys.executable, "-B", "-X", "utf8", "-c",
                "from pathlib import Path; from test_threshold_acceptance_adapter import legacy_public_pipeline_worker; "
                "legacy_public_pipeline_worker(Path(" + repr(str(root)) + "))"], cwd=repo, env=environment,
                capture_output=True, text=True, encoding="utf-8", timeout=180)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            # The real Root checkpoint transport emits its retained request paths
            # before the worker's final structured result.
            summary = object_value(json.loads(completed.stdout.splitlines()[-1]))
            self.assertEqual((summary["legacy_producer_saves"], summary["legacy_producer_natural_days"]), (7, 47))
            self.assertTrue(summary["old_result_unchanged"])
            qualification = public_entry.parse_legacy_threshold_gui_qualification_v1(summary["qualification"])
            for changed in ({**qualification, "gui_contract_qualified": 1}, {**qualification, "original_adapter_recomputed": False},
                            {**qualification, "original_result_modified": True}, {**qualification, "schema": "unknown"},
                            {**qualification, "extra": True}, {**qualification, "reverified_check_ids": []},
                            {**qualification, "producer_adapter": {**qualification["producer_adapter"], "bytes": True}},
                            {name: value for name, value in qualification.items() if name != "normal_close"}):
                with self.subTest(changed=changed), self.assertRaises(ValueError):
                    public_entry.parse_legacy_threshold_gui_qualification_v1(changed)

    def test_initial_fixture_has_no_tested_terminal_effect_or_success_counter(self) -> None:
        source = emitter.render_initial_inputs()
        for forbidden in ("xalw_settle_xp_effect", "xalw_refresh_artifact_effect", "xalw_train_effect", "xalw_suppress_effect", "xalw_begin_suppression_timer_effect", "xalw_growth_suppressed_until", "PASS", "trigger_event"):
            self.assertNotIn(forbidden, source)
        self.assertIn("xalw_xp_in_level value = 992", source)
        self.assertIn("xalw_curse_rank_1 value = 2", source)
        self.assertIn("add_stress = 20", source)
        with tempfile.TemporaryDirectory() as temporary:
            emitted = emitter.emit_fixture(Path(temporary) / "initial-inputs")
            self.assertFalse(emitted["game_started"])
            self.assertEqual(emitted["business_acceptance"], "NOT_ASSESSED")
            for reference in emitted["files"].values():
                self.assertEqual(pin(Path(reference["path"])), reference)

    def test_real_prepare_session_seven_producers_public_consumers_and_retained_verify(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary))
            self.assertEqual(result["status"], "PASS", result.get("error"))
            self.assertEqual((port.saves, port.day, port.train_intents), (7, 47, 1))
            self.assertLess(integer(result["actual_public_calls_budgeted"], "calls"), 480)
            self.assertEqual(threshold.verify_case(context), result)
            self.assertFalse(result["business_pass"])
            self.assertFalse(result["product_release_pass"])
            stress_checks = [check for check in array(result["checks"], "checks") if field(check, "case_id") in ("TRAIN-ACTUAL-STRESS", "SUPPRESS-ACTUAL-STRESS")]
            self.assertEqual([field(field(check, "observed"), "actual_stress_delta_points") for check in stress_checks], [7, 6])

    def test_actual_save_producer_public_consumer_and_both_saved_readers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            # Real producer -> actual CaseClient.root_checkpoint -> unique shared
            # verifier -> original inspector and new historical-vitals consumer.
            context = context_fixture(root)
            port = ThresholdPort(context)
            response, frame, source = public_round_trip(root, port.saved_text())
            inputs, _ = verify_readback(response, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root", frame=frame, source_save=source)
            self.assertEqual(inspect_inputs(Path(str(field(field(response, "melted_save"), "path"))), player_id=91), inputs)
            vitals = threshold.saved_vitals(Path(str(field(field(response, "melted_save"), "path"))), "91")
            self.assertEqual(threshold.Vitals.parse(json.loads(json.dumps(vitals.to_json()))), vitals)
            self.assertEqual(vitals, threshold.Vitals("100000000", "100000000", 20))

    def test_wrong_cost_growth_monthly_leak_timer_curse_and_equipment_reset_fail_independently(self) -> None:
        for fault, value in (("charge", 74), ("bad_growth", True), ("monthly_leak", True), ("wrong_timer", True), ("no_curse", True), ("reset_on_equip", True)):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                _, result, port = run_fixture(Path(temporary), **{fault: value})
                self.assertNotEqual(result["status"], "PASS", result.get("error"))
                if fault == "bad_growth":
                    self.assertEqual(port.train_intents, 0)

    def test_missing_saved_stress_does_not_invent_zero_or_block_other_completed_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary), missing_stress=True)
            self.assertEqual(result["status"], "BLOCKED", result.get("error"))
            self.assertEqual((port.saves, port.day), (7, 47))
            statuses = {str(field(check, "case_id")): field(check, "status") for check in array(result["checks"], "checks")}
            self.assertEqual(statuses["TRAIN-ACTUAL-STRESS"], "BLOCKED")
            self.assertEqual(statuses["SUPPRESS-ACTUAL-STRESS"], "BLOCKED")
            self.assertEqual(statuses["THRESHOLD-AUTOMATIC-11"], "PASS")
            self.assertEqual(statuses["SUPPRESS-MONTHLY-PAUSE"], "PASS")
            self.assertEqual(threshold.verify_case(context), result)

    def test_unknown_original_training_is_not_replayed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary), unknown_train=True)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertTrue(result["original_action_unknown"])
            self.assertEqual(port.train_intents, 1)
            self.assertFalse(port.suppressed)
            self.assertEqual(port.day, 16)
            self.assertEqual(threshold.verify_case(context), result)

    def test_vitals_runtime_rejects_wrong_types_missing_and_unknown_fields_and_preserves_q64(self) -> None:
        raw = threshold.Vitals(str(2**63 - 1), str(-(2**63)), 20).to_json()
        self.assertEqual(threshold.Vitals.parse(json.loads(json.dumps(raw))).to_json(), raw)
        for key, value in (("gold_raw_decimal", 2**63 - 1), ("gold_raw_decimal", "01"), ("prestige_raw_decimal", "-0"),
                           ("scale", True), ("scale", 100000.0), ("stress_points", True), ("stress_points", 20.0)):
            mutated: dict[str, object] = dict(raw)
            mutated[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                threshold.Vitals.parse(mutated)
        for mutation in ({key: value for key, value in raw.items() if key != "stress_points"}, {**raw, "extra": None}):
            with self.assertRaises(ValueError):
                threshold.Vitals.parse(mutation)

    def test_real_retained_verifier_rejects_source_closure_projection_scene_and_extra_action_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary))
            self.assertEqual(result["status"], "PASS", result.get("error"))
            journal = read(Path(str(field(result["journal"], "path"))))
            refs = array(journal["checkpoints"], "checkpoint refs")
            record = read(Path(str(field(refs[0], "path"))))
            for mutation in ({**record, "machine_id": "other-machine"}, {**record, "projection": {}}, {key: value for key, value in record.items() if key != "response"}):
                with self.assertRaises(ValueError):
                    threshold.consume_observation(mutation, context=context, manifest=port.manifest, reviewer="unit-root")
            native = mapping(journal["native_records"], "native closure")
            with self.assertRaisesRegex(ValueError, "closure"):
                threshold.evaluate(context, manifest=port.manifest, reviewer="unit-root", journal={**journal, "native_records": {}})
            first_key = next(iter(native))
            Path(str(field(native[first_key], "path"))).write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                threshold.verify_case(context)

    def test_canonical_contract_rejects_bool_float_missing_and_other_case(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context = context_fixture(Path(temporary))
            config = mapping(context["case_contract"], "contract")
            for mutated in ({**config, "schema_version": True}, {**config, "maximum_natural_days": 47.0},
                            {key: value for key, value in config.items() if key != "maximum_checkpoints"}):
                with self.assertRaises(ValueError):
                    threshold.validate_contract({**context, "case_contract": mutated})
            with self.assertRaises(ValueError):
                threshold.validate_contract({**context, "case": "npc_continuous"})


if __name__ == "__main__":
    unittest.main()

"""Authored native/screens/tool seams exercise real producers and consumers.

These offline fixtures are never screenshots, saves or acceptance from CK3.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "tools") not in sys.path:
    sys.path.insert(0, str(REPO / "tools"))

import acceptance_adapter as core
from acceptance_contract import Frame, Object, Pin, array, field, integer, mapping, object_value, pin, read, write_once
from living_artifacts_model import FEEDING_XP
from living_artifacts_core import render_core_effects
from inventory_gui_contract import REFUSAL
from management_event_contract import source_option_index
import preview_acceptance_adapter as preview
from startup_actor_binding import StartupActorBinding
from test_checkpoint_artifacts import AUTHORED_ARTIFACTS, authored_checkpoint_text
from test_inventory_gui_contract import png, response_fixture as inventory_response
from test_management_contracts import displayed_option, event_fixture
from test_native_interruption_contract import PublicCheckpointPort, RootCheckpointConsumer
from test_npc_acceptance_adapter import AuthoredCasePort
from test_npc_saved_observer import variable
from checkpoint_producer import stamp

TOOLS = Path(__file__).resolve().parent


def context_fixture(root: Path) -> Object:
    product, output, state = root / "formal", root / "prepared", root / "state"
    output.mkdir()
    (product / "common/scripted_effects").mkdir(parents=True)
    (product / "descriptor.mod").write_text('name="Authored offline pipeline"\n', encoding="utf-8")
    (product / "common/scripted_effects/core.txt").write_text(render_core_effects(), encoding="utf-8")
    engine = root / "shared/tools/fixture_engine_prepare.py"
    engine.parent.mkdir(parents=True)
    engine.write_text("def engine_identity(repo, *, game_dir, steam_manifest=None):\n return {'game_version':'unit-version','exe_sha256':'" + "a" * 64 + "'}\n", encoding="utf-8")
    plain: dict[str, Pin] = {}
    for index, name in enumerate(("pdx_settings.txt", "tutorial.txt", "presets.txt", "player/game_rules/presets.txt")):
        source = root / f"plain-{index}.txt"
        source.write_text("authored configuration\n", encoding="utf-8")
        plain[name] = pin(source)
    manifest = write_once(root / "runtime-manifest.json", {"machine_id": "unit-machine", "game": {"version": "unit-version", "exe_sha256": "a" * 64}})
    registry = read(REPO / "tools/ck3_mod_acceptance_products.json")
    selected = field(field(registry, "products"), "living-artifacts")
    case_spec = next(item for item in array(field(selected, "cases"), "cases") if field(item, "id") == "feeding_preview")
    context = object_value({"product": "living-artifacts", "case": "feeding_preview", "run_id": "unit-run", "state_dir": str(state), "output": str(output),
        "game_dir": str(root / "game"), "shared_source_root": str(engine.parents[1]), "shared_game": {"version": "unit-version", "exe_sha256": "a" * 64},
        "case_contract": read(TOOLS / preview.CONTRACT_NAME), "runtime_manifest": manifest,
        "case_spec": case_spec,
        "case_inputs": {"product_dir": str(product), "plain_configuration": plain}})
    result = preview.prepare_case(context)
    if field(result, "runtime_status") != "NOT_RUN":
        raise AssertionError("Preparation cannot claim runtime qualification")
    context["output"] = str(root / "case-output")
    Path(str(context["output"])).mkdir()
    return context


def authored_save(feeds: int) -> str:
    """Grammar fixture consumed by real strict saved-state reader."""
    remaining = tuple(FEEDING_XP)[feeds:]
    source = authored_checkpoint_text(tuple(item for item in AUTHORED_ARTIFACTS if item.reference == "12" or item.rarity in remaining))
    level, xp, growth = 1, 92, 0
    for amount in tuple(FEEDING_XP.values())[:feeds]:
        xp += amount
        while xp >= 100 * level:
            xp -= 100 * level; level += 1; growth += 1
    for key, old, new in (("level", 1, level), ("xp_in_level", 92, xp), ("growth_sequence", 0, growth)):
        source = source.replace(variable("xalw_" + key, "value", str(old * 100000)), variable("xalw_" + key, "value", str(new * 100000)))
    return source.replace('{ flag="xalw_level"', variable("xalw_diet", "flag", flag="armor") + ' { flag="xalw_level"', 1)


class PreviewPort(AuthoredCasePort):
    """Only CK3/native/pixels are authored; Session and file pipeline are real."""
    def __init__(self, context: Object, *, wrong_preview: bool = False, keep_material: bool = False,
                 error_log: bytes = b"", cancel_consumes: bool = False, drift_after_review: bool = False,
                 review_delay: timedelta = timedelta(0)) -> None:
        super().__init__(context)
        self.feeds = 0
        self.equipped = False
        self.event: str | None = None
        self.instance = 80
        self.reviews = 0
        self.wrong_preview, self.keep_material = wrong_preview, keep_material
        self.cancel_consumes, self.drift_after_review = cancel_consumes, drift_after_review
        self.canceled_consumed = False
        self.review_delay = review_delay
        logs = self.state / "profile/logs"
        logs.mkdir(exist_ok=True)
        (logs / "error.log").write_bytes(error_log)

    def frame(self) -> Object:
        frame = super().frame()
        frame["active_event"] = None if self.event is None else {"instance_id": self.instance}
        return frame

    def show(self, event: str | None) -> None:
        self.event = event
        self.instance += 1

    def execute_plan(self, steps: list[Object], name: str, timeout: int | float | None = None, reserve: int = 90) -> object:
        step = steps[0]
        tool = str(step["tool"])
        args = mapping(step["args"], "authored native args")
        self.tools.append(tool)
        result: Object
        if tool == "ck3_save_checkpoint":
            self.saves += 1
            source = self.state / "profile/save games/live.ck3"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(authored_save(self.feeds), encoding="utf-8")
            saved = pin(source)
            result = object_value({"checkpoint": {"status": "saved", "path": saved["path"], "size": saved["bytes"], "sha256": saved["sha256"],
                "date_raw": 53144328}, "materialization": {"available": True}})
        elif tool == core.ITEM:
            consumed = 0 if self.keep_material else self.feeds
            owned = [int(item.reference) for item in AUTHORED_ARTIFACTS if item.reference == "12" or item.rarity in tuple(FEEDING_XP)[consumed:]]
            if self.canceled_consumed and 13 in owned:
                owned.remove(13)
            result = object_value({"available": True, "read_only": True, "loaded_source_pins_verified": True, "personally_owned": True, "inventory_artifact": True,
                "requested_artifact_id": args["artifact_id"], "played_character_id": 91, "date_raw": 53144328, "native_equipped_observed": True,
                "equipped": self.equipped, "equipped_slot_index": 0 if self.equipped else None, "effective_slot_index": 0, "replacing_artifact_id": None,
                "can_equip_in_effective_slot": True, "can_unequip": True, "inventory_view_available": True, "inventory_view_visible": True, "owned_ids": owned})
        elif tool == core.EQUIP:
            self.equipped = args["desired_equipped"] is True
            result = {"once_intent_consumed": True, "intent_sequence": 1}
        elif tool == core.EQUIP_POST:
            result = {"desired_inventory_state_observed": True}
        elif tool == core.DECISIONS_OPEN:
            result = {"schema": "ck3-ingame-decisions-open-v1", "postcondition_verified": True, "verification_pending": False}
        elif tool == core.DECISION_SELECT:
            result = {"schema": "ck3-ingame-decision-item-action-v1", "action": "select", "decision_key": "xalw_manage_decision", "postcondition_verified": True}
        elif tool == core.DECISION_CONFIRM:
            self.show("xalw.12")
            result = {"schema": "ck3-ingame-decision-outcome-confirm-v1", "postcondition_verified": True, "verification_pending": False, "expected_event_definition_key": "xalw.12"}
        elif tool == "ck3_query_current_event_window_context_v1":
            if self.event is None:
                raise AssertionError("No authored native event")
            frame = Frame.parse(self.frame(), run_id="unit-run", machine_id="unit-machine", manifest=self.manifest)
            result, _ = event_fixture(event=self.event, instance=self.instance, frame=frame,
                options=[displayed_option(index, index) for index in range(10 if self.event == "xalw.10" else 2)])
        elif tool == "ck3_select_event_option":
            if self.event == "xalw.11":
                if args["option_number"] == 1:
                    self.feeds += 1
                elif self.cancel_consumes:
                    self.canceled_consumed = True
                self.show("xalw.10")
            elif self.event == "xalw.12":
                self.show("xalw.10")
            else:
                self.show(None if args["option_number"] == source_option_index("xalw.10", "xalw.10.close") + 1 else "xalw.11")
            result = {"submitted": True}
        else:
            raise AssertionError("Unexpected authored tool " + tool)
        rows = [object_value({"ok": True, "plan": step, "result": result, "after_snapshot": self.frame()})]
        write_once(self.output / (name + ".actual-results.json"), {"rows": rows})
        return rows

    def root_checkpoint(self, name: str, request: Object, reserve: int = 90) -> object:
        if request["schema"] != "living-artifacts-feeding-preview-request-v1":
            return super().root_checkpoint(name, request, reserve)
        public: RootCheckpointConsumer = ReviewRoot(self.output, name, self)
        actual = public.root_checkpoint(name, request, reserve)
        if self.drift_after_review:
            self.show("xalw.11")
        return actual

    def produce_review(self, name: str, awaiting: Path) -> None:
        request = read(awaiting)
        self.reviews += 1
        screenshot = self.output / (name + ".png")
        png(screenshot, 64, 48)
        captured = datetime.now(timezone.utc) + self.review_delay
        capture = write_once(self.output / (name + ".capture.json"), {"machine_id": "unit-machine", "observed_at_utc": captured.isoformat(),
            "image": {**pin(screenshot), "width": 64, "height": 48}, "desktop": {"width": 64, "height": 48}, "foreground": {"pid": 124}, "gameplay_pass_claimed": False})
        reviewed = max(captured, datetime.now(timezone.utc))
        with patch.object(preview, "utc_now", return_value=reviewed.isoformat()):
            response = preview.produce_preview_review(awaiting, manifest=self.manifest, reviewer="unit-root", reviewed_at_utc=reviewed.isoformat(), screenshot=screenshot, capture=Path(capture["path"]),
                displayed_base_xp=integer(request["expected_base_xp"], "expected authored base"),
                displayed_preview_xp=0 if self.wrong_preview else integer(request["expected_preview_xp"], "expected authored preview"), displayed_material_name="Authored material", direct_reviewed=True)
        write_once(self.output / (name + "-root-result.json"), response)

    def log_bytes(self, name: str = "debug.log", maximum: int = 64 * 1024 * 1024) -> bytes:
        return (self.state / "profile/logs" / name).read_bytes()

    def advance_day(self, days: int = 1, timeout: float = 300, allow_event_boundary: bool = False, allow_actor_change: bool = False) -> object:
        raise AssertionError("Preview scenario cannot advance a natural day")


class InventoryFailurePort(PreviewPort):
    """Actual failure/continuation orchestration; only the game boundary is authored."""
    def __init__(self, context: Object) -> None:
        super().__init__(context)
        self.live = self.output.parent
        self._seq = 0
        self.frozen = {"run_id": "unit-run", "lease_anchor": str(REPO), "source_root": str(REPO)}
        self.inventory_visible = False
        self.hold = datetime.now(timezone.utc).timestamp() + 7200
        self.host_steps: list[Object] = []

    def read_report(self, allow_error: bool = False) -> object:
        return {"hold_until_utc_estimated": self.hold, "steps": self.host_steps}

    def snapshot(self, allow_actor_change: bool = False, require_event_free: bool = True) -> object:
        self.snapshots += 1
        self._seq += 1
        name = f"case-snapshot-{self._seq:04d}"
        rows = array(self.execute_plan([{"id": name, "tool": "ck3_take_snapshot", "args": {}}], name), "authored snapshot")
        return field(rows[0], "result")

    def execute_plan(self, steps: list[Object], name: str, timeout: int | float | None = None, reserve: int = 90) -> object:
        if any(field(row, "id") == name for row in self.host_steps):
            raise AssertionError("A consumed global control ID was replayed")
        step = steps[0]
        tool = str(step["tool"])
        if tool == "ck3_take_snapshot":
            rows: object = [{"ok": True, "plan": step, "result": self.frame(), "after_snapshot": self.frame()}]
            write_once(self.output / (name + ".actual-results.json"), {"rows": rows})
        elif tool == core.OPEN:
            self.tools.append(tool)
            rows = [{"ok": False, "error": REFUSAL, "plan": step, "after_snapshot": self.frame()}]
            write_once(self.output / (name + ".actual-results.json"), {"rows": rows})
        else:
            rows = super().execute_plan(steps, name, timeout, reserve)
            if tool == core.ITEM:
                row = mapping(array(rows, "authored native rows")[0], "authored ITEM")
                result = mapping(row["result"], "authored ITEM result")
                result["inventory_view_visible"] = self.inventory_visible
                row["result"] = object_value(result)
                rows = [row]
                (self.output / (name + ".actual-results.json")).write_text(json.dumps({"rows": rows}), encoding="utf-8")
        host_row = object_value(array(rows, "authored controls")[0])
        host_row["id"], host_row["finished_at"] = name, datetime.now(timezone.utc).isoformat()
        self.host_steps.append(host_row)
        return rows

    def root_checkpoint(self, name: str, request: Object, reserve: int = 90) -> object:
        if request["schema"] != "living-artifacts-inventory-gui-open-request-v1":
            return super().root_checkpoint(name, request, reserve)
        write_once(self.output / (name + "-awaiting.json"), {**request, "original_hold_deadline": self.hold})
        evidence = self.output / "authored-wrong-navigation"
        evidence.mkdir()
        response, _, _ = inventory_response(evidence, date_raw=53144328, refusal=pin(Path(str(field(request["original_native_refusal"], "path")))))
        write_once(self.output / (name + "-root-result.json"), response)
        return response


class ReviewRoot(PublicCheckpointPort):
    """Actual public awaiting file drives the actual Root preview producer."""
    def __init__(self, output: Path, name: str, port: PreviewPort) -> None:
        super().__init__(output)
        self.name, self.port, self.produced = name, port, False

    def guard(self, reserve: int = 90, *, failure_shutdown: bool = False) -> dict[str, object]:
        awaiting = self.output / (self.name + "-awaiting.json")
        if awaiting.is_file() and not self.produced:
            self.produced = True
            self.port.produce_review(self.name, awaiting)
        return {"authored_native_pixels_not_runtime_evidence": True}


def run_fixture(root: Path, *, wrong_preview: bool = False, keep_material: bool = False, error_log: bytes = b"",
                cancel_consumes: bool = False, drift_after_review: bool = False, review_delay: timedelta = timedelta(0)) -> tuple[Object, Object, PreviewPort]:
    context = context_fixture(root)
    port = PreviewPort(context, wrong_preview=wrong_preview, keep_material=keep_material, error_log=error_log,
        cancel_consumes=cancel_consumes, drift_after_review=drift_after_review, review_delay=review_delay)
    binding = StartupActorBinding(91, 124, "9", 53144328, 12801, "a" * 64, "b" * 64)
    with patch.object(StartupActorBinding, "parse", return_value=binding):
        result = preview.run_case(context, port)
    return context, result, port


class PreviewAcceptanceTests(unittest.TestCase):
    def test_real_inventory_postcondition_failure_continues_same_sequence_with_only_four_more_saves(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context = context_fixture(Path(temporary))
            port = InventoryFailurePort(context)
            binding = StartupActorBinding(91, 124, "9", 53144328, 12801, "a" * 64, "b" * 64)
            with patch.object(StartupActorBinding, "parse", return_value=binding):
                original = preview.run_case(context, port)
            self.assertEqual(original["status"], "BLOCKED", original.get("error"))
            self.assertEqual(original["error"], "ValueError: Independent current ITEM did not confirm GUI inventory visibility")
            self.assertEqual((original["actual_public_calls_budgeted"], port.saves, port.snapshots), (7, 1, 2))
            predecessor = port.output
            retained = pin(predecessor / preview.RESULT_NAME)
            port.inventory_visible = True
            port.execute_plan([{"id": "corrected-inventory-readonly", "tool": core.ITEM, "args": {"artifact_id": 12}}], "corrected-inventory-readonly")
            correction = write_once(predecessor / "corrected-item.json", {"rows": [port.host_steps[-1]]})
            port.output = predecessor.parent / "case-continuation-a01"
            port.output.mkdir()
            port._seq = 0
            context = {**context, "output": str(port.output)}
            with patch.object(StartupActorBinding, "parse", return_value=binding):
                result = preview.resume_inventory_open_failure(context, port, predecessor_output=predecessor,
                    corrected_item=correction, original_source_tools=TOOLS)
            self.assertEqual(result["status"], "PASS", result.get("error"))
            self.assertEqual((port.saves, port.reviews, result["actual_saved_observations"], result["inherited_public_calls"]), (5, 5, 5, 8))
            self.assertEqual(pin(predecessor / preview.RESULT_NAME), retained)
            self.assertFalse(result["original_public_case_PASS"])
            self.assertTrue((port.output / "xalw-core-0006.actual-results.json").is_file())
            self.assertTrue((port.output / "case-snapshot-0003.actual-results.json").is_file())
            self.assertFalse((port.output / "checkpoint-readback-01-awaiting.json").exists())
            journal = read(Path(str(field(result["journal"], "path"))))
            self.assertEqual(preview.evaluate(context, manifest=port.manifest, reviewer="unit-root", journal=journal), result["observed"])
            self.assertEqual(array(journal["checkpoints"], "checkpoints")[0], pin(predecessor / "preview-checkpoint-01.json"))

    def test_inventory_continuation_rejects_wrong_current_scene_before_any_new_action(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context = context_fixture(Path(temporary))
            port = InventoryFailurePort(context)
            binding = StartupActorBinding(91, 124, "9", 53144328, 12801, "a" * 64, "b" * 64)
            with patch.object(StartupActorBinding, "parse", return_value=binding):
                original = preview.run_case(context, port)
            self.assertEqual(original["actual_public_calls_budgeted"], 7)
            predecessor = port.output
            port.inventory_visible = True
            port.execute_plan([{"id": "corrected-inventory-readonly", "tool": core.ITEM, "args": {"artifact_id": 12}}], "corrected-inventory-readonly")
            wrong = mapping(port.host_steps[-1], "authored wrong native")
            after = mapping(wrong["after_snapshot"], "authored wrong scene")
            after["date_raw"] = 53144352
            wrong["after_snapshot"] = object_value(after)
            correction = write_once(predecessor / "wrong-corrected-item.json", {"rows": [wrong]})
            port.output = predecessor.parent / "case-continuation-a01"
            port.output.mkdir()
            port._seq = 0
            with self.assertRaisesRegex(ValueError, "Correction crossed"):
                preview.resume_inventory_open_failure({**context, "output": str(port.output)}, port,
                    predecessor_output=predecessor, corrected_item=correction, original_source_tools=TOOLS)
            self.assertEqual((port.saves, port.reviews), (1, 0))

    def test_registered_public_adapter_loads_in_independent_python_without_product_pythonpath(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths: dict[str, str] = {}
            for name in ("host", "source_index", "native_source_index", "dll", "injector"):
                source = root / (name + ".py" if name == "host" else name + ".json")
                source.write_text("# authored never execute\n" if name == "host" else "{}", encoding="utf-8")
                paths[name] = str(source)
            source_root = root / "source"; source_root.mkdir()
            paths["source_root"] = str(source_root)
            manifest = write_once(root / "manifest.json", {"schema": "ck3-mod-acceptance-shared-runtime-v1", "source_root": {"path_key": "source_root"},
                "host": {"path_key": "host", "bytes": Path(paths["host"]).stat().st_size, "sha256": pin(Path(paths["host"]))["sha256"]},
                "source_index": {"path_key": "source_index", "bytes": 2, "sha256": pin(Path(paths["source_index"]))["sha256"]},
                "native_source_index": {"path_key": "native_source_index", "bytes": 2, "sha256": pin(Path(paths["native_source_index"]))["sha256"]},
                "native": {name: {"path_key": name, "bytes": 2, "sha256": pin(Path(paths[name]))["sha256"]} for name in ("dll", "injector")},
                "game": {"version": "unit-version", "exe_sha256": "a" * 64}, "capabilities": {}})
            runtime = write_once(root / "runtime.json", {"schema": "ck3-mod-acceptance-runtime-v1", "manifest": manifest, "python": sys.executable,
                "repo_root": str(REPO), "game_dir": str(root / "game"), "userdir_root": str(root / "userdir"), "artifacts_root": str(root / "artifacts"), "paths": paths})
            script = root / "cold_import.py"
            script.write_text("import sys\nfrom pathlib import Path\nsys.path[:0]=[str(Path(sys.argv[1])/'tools'),str(Path(sys.argv[1])/'ck3_autonomous_player/src')]\n"
                "from ck3_mod_acceptance import Selection\ns=Selection(Path(sys.argv[2]),Path(sys.argv[1])/'tools/ck3_mod_acceptance_products.json','living-artifacts','feeding_preview')\n"
                "m=s.load_adapter()\nc=m.validate_contract(s.adapter_context())\nassert c.maximum_checkpoints==5 and c.transport.maximum_days==0\n"
                "assert m.__name__=='ck3_mod_acceptance_cases.preview_acceptance_adapter'\nprint('ACTUAL_PREVIEW_PUBLIC_COLD_IMPORT_OK')\n", encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(script), str(REPO), runtime["path"]], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("ACTUAL_PREVIEW_PUBLIC_COLD_IMPORT_OK", result.stdout)

    def test_actual_prepare_session_five_save_producers_public_png_reviews_and_verify(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary))
            self.assertEqual(result["status"], "PASS", result.get("error"))
            self.assertEqual((port.saves, port.reviews, port.day), (5, 5, 0))
            self.assertEqual(preview.verify_case(context), result)
            self.assertFalse(result["business_pass"])
            self.assertFalse(result["product_release_pass"])
            self.assertNotIn("ck3_advance_day", port.tools)
            self.assertTrue(all(field(check, "status") == "PASS" for check in array(result["checks"], "checks")))

    def test_wrong_ui_zero_and_real_material_still_owned_cannot_pass(self) -> None:
        for options in ({"wrong_preview": True}, {"keep_material": True}, {"cancel_consumes": True}, {"drift_after_review": True}):
            with self.subTest(options=options), tempfile.TemporaryDirectory() as temporary:
                _, result, port = run_fixture(Path(temporary), wrong_preview=options.get("wrong_preview", False),
                    keep_material=options.get("keep_material", False), cancel_consumes=options.get("cancel_consumes", False),
                    drift_after_review=options.get("drift_after_review", False))
                self.assertNotEqual(result["status"], "PASS")
                self.assertFalse(result["case_contract_qualified"])
                if options.get("drift_after_review"):
                    self.assertEqual(port.feeds, 0)
                if options.get("cancel_consumes") or options.get("wrong_preview"):
                    self.assertEqual(port.feeds, 0)
                if options.get("keep_material"):
                    self.assertEqual(port.feeds, 1)

    def test_complete_log_scan_catches_tail_error_while_static_warnings_remain_separate(self) -> None:
        static = b"[19:00:00][E][jomini_effect.cpp:1146]: Variable 'xalw_fixture_target' is set but is never used.\n"
        raw = static * 1000 + b"[19:00:01][E] Script system error! (while building tooltip/description)\n Error: xalw_suppression_timer_sequence not set\n"
        scan = preview.scan_error_log(raw)
        self.assertEqual((scan["record_count"], scan["static_diagnostic_count"], scan["mod_runtime_error_count"]), (1001, 1000, 1))
        with tempfile.TemporaryDirectory() as temporary:
            _, result, _ = run_fixture(Path(temporary), error_log=raw)
            self.assertEqual(result["status"], "FAIL", result.get("error"))

    def test_request_response_closed_fields_types_scenes_pixels_and_capture_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary))
            self.assertEqual(result["status"], "PASS", result.get("error"))
            envelope = read(port.output / "preview-review-01.json")
            request, response = envelope["request"], mapping(envelope["response"], "response")
            wrong: tuple[tuple[str, object], ...] = (("event_instance_id", True), ("date_raw", 53144328.0), ("displayed_preview_xp", 80.0),
                ("business_pass", 0), ("run_id", "other"), ("reviewer", "other"), ("displayed_preview_xp", 0), ("direct_reviewed", 1))
            for key, value in wrong:
                with self.subTest(key=key, value=value), self.assertRaises((ValueError, core.CaseFailed)):
                    preview.parse_review({**response, key: value}, request=request, manifest=port.manifest, reviewer="unit-root")
            for key in response:
                with self.subTest(missing=key), self.assertRaises(ValueError):
                    preview.parse_review({name: value for name, value in response.items() if name != key}, request=request, manifest=port.manifest, reviewer="unit-root")
            with self.assertRaises(ValueError):
                preview.parse_review({**response, "extra": True}, request=request, manifest=port.manifest, reviewer="unit-root")
            screenshot = Path(str(field(response["screenshot"], "path")))
            screenshot.write_bytes(screenshot.read_bytes() + b"tamper")
            with self.assertRaises(ValueError):
                preview.verify_case(context)

    def test_producer_consumes_actual_root_envelope_and_rejects_stale_or_foreign_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            _, result, port = run_fixture(Path(temporary))
            self.assertEqual(result["status"], "PASS", result.get("error"))
            first = read(port.output / "preview-review-01.json")
            second = read(port.output / "preview-review-02.json")
            response = mapping(first["response"], "original response")
            request_path = Path(str(field(response["root_request"], "path")))
            root_request = read(request_path)
            screenshot = Path(str(field(response["screenshot"], "path")))
            capture = Path(str(field(response["capture"], "path")))
            wrong: tuple[dict[str, object], ...] = ({"reserve_seconds": 180.0}, {"operator_reviewer": "other"},
                {"original_hold_deadline": False}, {"original_hold_deadline": 1.0}, {"extra": True})
            for index, changes in enumerate(wrong):
                changed = port.output / f"changed-{index}-awaiting.json"
                write_once(changed, {**root_request, **changes})
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    preview.produce_preview_review(changed, manifest=port.manifest, reviewer="unit-root", reviewed_at_utc=datetime.now(timezone.utc).isoformat(), screenshot=screenshot, capture=capture,
                        displayed_base_xp=80, displayed_preview_xp=80, displayed_material_name="Authored material", direct_reviewed=True)
            with self.assertRaises(ValueError):
                preview.produce_preview_review(request_path, manifest=port.manifest, reviewer="unit-root", reviewed_at_utc=datetime.now(timezone.utc).isoformat(), screenshot=screenshot, capture=capture,
                    displayed_base_xp=80, displayed_preview_xp=80, displayed_material_name="Authored material", direct_reviewed=False)
            later_request = Path(str(field(field(second["response"], "root_request"), "path")))
            with self.assertRaisesRegex(ValueError, "chronology"):
                preview.produce_preview_review(later_request, manifest=port.manifest, reviewer="unit-root", reviewed_at_utc=datetime.now(timezone.utc).isoformat(), screenshot=screenshot, capture=capture,
                    displayed_base_xp=80, displayed_preview_xp=80, displayed_material_name="Authored material", direct_reviewed=True)
            original_capture = read(capture)
            capture_changes: tuple[Object, ...] = ({"machine_id": "other"}, {"foreground": {"pid": 125}}, {"desktop": {"width": 64.0, "height": 48}})
            for index, change in enumerate(capture_changes):
                changed_capture = write_once(port.output / f"foreign-capture-{index}.json", {**original_capture, **change})
                with self.subTest(change=change), self.assertRaises(ValueError):
                    preview.produce_preview_review(request_path, manifest=port.manifest, reviewer="unit-root", reviewed_at_utc=datetime.now(timezone.utc).isoformat(), screenshot=screenshot, capture=Path(changed_capture["path"]),
                        displayed_base_xp=80, displayed_preview_xp=80, displayed_material_name="Authored material", direct_reviewed=True)
            # R11: a timely direct-review operation was written back much later.
            # Keep the real earlier time; neither wire nor consumer changes.
            reviewed = str(response["reviewed_at_utc"])
            reviewed_time = datetime.fromisoformat(reviewed.replace("Z", "+00:00"))
            delayed = reviewed_time + timedelta(seconds=240)
            with patch.object(preview, "utc_now", return_value=delayed.isoformat()):
                actual = preview.produce_preview_review(request_path, manifest=port.manifest, reviewer="unit-root", reviewed_at_utc=reviewed,
                    screenshot=screenshot, capture=capture, displayed_base_xp=80, displayed_preview_xp=80, displayed_material_name="Authored material", direct_reviewed=True)
                self.assertEqual(actual["reviewed_at_utc"], reviewed)
                self.assertEqual(preview.parse_review(actual, request=first["request"], manifest=port.manifest, reviewer="unit-root"), actual)
                for invalid in ((delayed + timedelta(seconds=1)).isoformat(), "", "not-a-date",
                        (datetime.fromisoformat(str(original_capture["observed_at_utc"]).replace("Z", "+00:00")) - timedelta(seconds=1)).isoformat()):
                    with self.subTest(invalid_review_time=invalid), self.assertRaises(ValueError):
                        preview.produce_preview_review(request_path, manifest=port.manifest, reviewer="unit-root", reviewed_at_utc=invalid, screenshot=screenshot,
                            capture=capture, displayed_base_xp=80, displayed_preview_xp=80, displayed_material_name="Authored material", direct_reviewed=True)
                near_close = port.output / "near-close-awaiting.json"
                write_once(near_close, {**root_request, "original_hold_deadline": delayed.timestamp() + 100})
                with self.assertRaisesRegex(ValueError, "reserve"):
                    preview.produce_preview_review(near_close, manifest=port.manifest, reviewer="unit-root", reviewed_at_utc=reviewed, screenshot=screenshot,
                        capture=capture, displayed_base_xp=80, displayed_preview_xp=80, displayed_material_name="Authored material", direct_reviewed=True)

    def test_r11_actual_request02_age_preserves_same_event_and_real_hold_boundaries(self) -> None:
        # Only these observed times are historical R11 facts. The following
        # native/pixel/payment state is authored; it grants no R11 retry or PASS.
        timing = read(TOOLS / "fixtures/r11_preview_request02_timing.json")
        self.assertEqual(timing["machine_id"], "pc-20260924rtuf-f11af23c08")
        self.assertEqual(timing["requested_at_utc"], "2026-10-22T15:38:44.256059+00:00")
        self.assertEqual(timing["captured_at_utc"], "2026-10-22T15:42:13.442942+00:00")
        self.assertIsNone(timing["actual_reviewed_at_utc"])
        self.assertFalse(timing["retroactive_gameplay_credit"])
        delay = stamp(timing["captured_at_utc"]) - stamp(timing["requested_at_utc"])
        self.assertEqual(delay, timedelta(seconds=209, microseconds=186883))
        self.assertGreater(delay.total_seconds(), 180)
        for drift in (False, True):
            with self.subTest(event_drift=drift), tempfile.TemporaryDirectory() as temporary:
                context, result, port = run_fixture(Path(temporary), review_delay=delay, drift_after_review=drift)
                if drift:
                    self.assertEqual(result["status"], "BLOCKED")
                    self.assertEqual(port.feeds, 0)
                else:
                    self.assertEqual(result["status"], "PASS", result.get("error"))
                    self.assertEqual((port.reviews, port.saves, port.feeds, port.day), (5, 5, 4, 0))
                self.assertEqual(preview.verify_case(context), result)
        # Use exact original request/capture timestamps in a new authored
        # producer input. A separately authored review time stays explicit.
        with tempfile.TemporaryDirectory() as temporary:
            _, result, port = run_fixture(Path(temporary))
            self.assertEqual(result["status"], "PASS", result.get("error"))
            envelope = read(port.output / "preview-review-01.json")
            response = mapping(envelope["response"], "response")
            original = read(Path(str(field(response["root_request"], "path"))))
            awaiting = port.output / "r11-timing-authored-awaiting.json"
            write_once(awaiting, {**original, "requested_at_utc": timing["requested_at_utc"], "original_hold_deadline": timing["original_hold_deadline"]})
            old_capture = read(Path(str(field(response["capture"], "path"))))
            capture = write_once(port.output / "r11-timing-authored-capture.json", {**old_capture, "observed_at_utc": timing["captured_at_utc"]})
            authored_review = stamp(timing["captured_at_utc"]) + timedelta(seconds=1)
            producing = authored_review + timedelta(minutes=4)
            with patch.object(preview, "utc_now", return_value=producing.isoformat()):
                reviewed = preview.produce_preview_review(awaiting, manifest=port.manifest, reviewer="unit-root", reviewed_at_utc=authored_review.isoformat(),
                    screenshot=Path(str(field(response["screenshot"], "path"))), capture=Path(capture["path"]), displayed_base_xp=80,
                    displayed_preview_xp=80, displayed_material_name="Authored material", direct_reviewed=True)
                request = {key: read(awaiting)[key] for key in preview.PreviewRequest.__required_keys__}
                self.assertEqual(preview.parse_review(reviewed, request=request, manifest=port.manifest, reviewer="unit-root"), reviewed)

    def test_saved_projection_rejects_false_equal_numbers_and_pass_needs_journal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary))
            self.assertEqual(result["status"], "PASS", result.get("error"))
            journal = read(Path(str(field(result["journal"], "path"))))
            checkpoints = array(journal["checkpoints"], "saved checkpoints")
            first = read(Path(str(field(checkpoints[0], "path"))))
            changed = {**first, "sample": {**mapping(first["sample"], "sample"), "level": True}}
            changed_ref = write_once(port.output / "false-equal-sample.json", changed)
            with self.assertRaisesRegex(ValueError, "projection"):
                preview.evaluate(context, manifest=port.manifest, reviewer="unit-root", journal={**journal, "checkpoints": [changed_ref, *checkpoints[1:]]})
            checks = [{**mapping(check, "check"), "evidence": []} for check in array(result["checks"], "checks")]
            (port.output / preview.RESULT_NAME).write_text(json.dumps({**result, "checks": checks}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "evidence journal"):
                preview.verify_case(context)

    def test_whole_deployment_closure_and_retained_result_cannot_be_relabelled_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, result, port = run_fixture(Path(temporary))
            self.assertEqual(result["status"], "PASS", result.get("error"))
            loaded = port.state / "profile/mod-content/product/extra.txt"
            loaded.write_text("extra unqualified input", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "closure"):
                preview.verify_case(context)
            loaded.unlink()
            path = port.output / preview.RESULT_NAME
            changed = {**result, "actual_saved_observations": 4}
            path.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaises(ValueError):
                preview.verify_case(context)

    def test_not_run_contract_false_equal_caps_and_missing_tool_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context = context_fixture(Path(temporary))
            self.assertEqual(preview.verify_case(context)["status"], "NOT_RUN")
            for key, wrong in (("schema_version", True), ("maximum_natural_days", False), ("maximum_checkpoints", 5.0), ("maximum_direct_reviews", 5.0)):
                contract = mapping(context["case_contract"], "contract")
                with self.subTest(key=key), self.assertRaises(ValueError):
                    preview.validate_contract({**context, "case_contract": {**contract, key: wrong}})
            spec = mapping(context["case_spec"], "spec")
            with self.assertRaises(ValueError):
                preview.validate_contract({**context, "case_spec": {**spec, "required_mcp_tools": []}})


if __name__ == "__main__":
    unittest.main()

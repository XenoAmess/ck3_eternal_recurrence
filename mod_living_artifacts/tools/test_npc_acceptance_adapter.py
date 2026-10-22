"""Authored external-tool/native fixtures drive real public producers/consumers."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Protocol, runtime_checkable
import unittest
from unittest.mock import patch

import acceptance_adapter as core
from acceptance_contract import Frame, Object, Pin, array, field, integer, object_value, pin, read, write_once
from checkpoint_callback import verify_readback
import checkpoint_producer as producer
from checkpoint_producer import Identity, ProcessOutcome, ProducerSpec, StoragePins
from living_artifacts_core import render_core_effects
import npc_acceptance_adapter as npc
from npc_saved_observer import HEALTHY_ROLES, NpcInitialBaseline, NpcSavedObservation, observe_npc_saved
import prepare_npc_fixture as emitter
from startup_actor_binding import StartupActorBinding
from test_checkpoint_artifacts import AUTHORED_ARTIFACTS, authored_checkpoint_text
from test_native_interruption_contract import PublicCheckpointPort, RootCheckpointConsumer
from test_npc_saved_observer import ITEMS, authored_save, r9_excerpt_text, variable


REPO = Path(__file__).resolve().parents[2]


def combined_save(*, day: int = 0, markers: bool = True, remove_material: bool = True,
                  initially_equipped: bool = False) -> str:
    """Actual parsers consume authored records; these are never CK3 observations."""
    dates = {0: "1066.9.15", 1: "1066.9.16", 16: "1066.10.1", 47: "1066.11.1"}
    items = ITEMS if day == 0 or not remove_material else tuple(item for item in ITEMS if item.kind != "common")
    source = authored_save(items=items, equipped=day > 0 or initially_equipped, date=dates[day])
    source = source.replace('variables={ data={ ', 'variables={ data={ ' + variable("xalw_fixture_target", "artifact", "12") + " " +
        variable("xalw_npc_fixture_missing_fragile", "boolean", "1") + " ", 1)
    base = variable("xalw_level", "value", "100000")
    source = source.replace(base, base + " " + variable("xalw_xp_in_level", "value") + " " +
        variable("xalw_pending_xp", "value") + " " + variable("xalw_growth_sequence", "value"))
    if day:
        if markers:
            source = source.replace(variable("xalw_imaginary_equipped_flag", "boolean", "1"),
                variable("xalw_imaginary_equipped_flag", "boolean", "1") + " " + variable("xalw_training_cooldown", "boolean", "1"))
        xp = 0 if day == 1 else 8 if day == 16 else 16
        for item in ITEMS:
            if item.kind != "target":
                continue
            start = source.index("\t\t" + item.identity + "={\n")
            end = source.index("\n\t\t}\n", start)
            block = source[start:end].replace(base, variable("xalw_level", "value", "200000"))
            block = block.replace(variable("xalw_xp_in_level", "value"), variable("xalw_xp_in_level", "value", str(xp * 100000)))
            block = block.replace(variable("xalw_growth_sequence", "value"), variable("xalw_growth_sequence", "value", "100000"))
            if markers:
                block = block.replace('variables={ data={ ', 'variables={ data={ ' + variable("xalw_feeding_imprint", "flag", flag="primary_armament") + " ", 1)
            source = source[:start] + block + source[end:]
    core_text = authored_checkpoint_text(AUTHORED_ARTIFACTS)
    core_artifacts = core_text.split('artifacts={\n\tartifacts={\n', 1)[1].rsplit('\t}\n}\n', 1)[0]
    return source.replace('artifacts={\n\tartifacts={\n', 'artifacts={\n\tartifacts={\n' + core_artifacts, 1)


def authored_tool(argv: tuple[str, ...], *, output: Path, timeout: int, maximum_melted: int, maximum_log: int) -> ProcessOutcome:
    """The only stand-in external transformation; retain the requested argv exactly."""
    if argv[1] != "melt" or argv[3:8] != ("--format", "ck3", "--unknown-key", "error", "-o"):
        raise AssertionError("Actual producer changed strict argv")
    shutil.copyfile(argv[2], argv[8])
    (output / "stdout.log").write_bytes(b"")
    (output / "stderr.log").write_bytes(b"")
    return ProcessOutcome(99, 0, "exited", None, datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat())


class ProducingRoot(PublicCheckpointPort):
    """Real Root file consumer triggers the real producer from its actual request."""
    def __init__(self, output: Path, name: str, manifest: Pin) -> None:
        super().__init__(output)
        self.name = name
        self.manifest_pin = manifest
        self.produced = False

    def guard(self, reserve: int = 90, *, failure_shutdown: bool = False) -> dict[str, object]:
        awaiting = self.output / (self.name + "-awaiting.json")
        if awaiting.is_file() and not self.produced:
            self.produced = True
            request = read(awaiting)
            identity = Identity("unit-run", "unit-machine", "unit-root", integer(field(request, "pid"), "PID", 1),
                str(field(request, "connection_generation")), integer(field(request, "actor_character_id"), "actor", 1),
                integer(field(request, "date_raw"), "date", 1))
            proof = write_once(self.output / (self.name + "-authored-external-provider.json"), {"authored_external_environment": True})
            storage = StoragePins(policy=proof, machine_profile=proof, asset_ledger=proof, reservation=proof, inspection=proof)
            spec = ProducerSpec(identity, pin(awaiting), self.manifest_pin, proof, proof, proof, storage,
                self.output / (self.name + "-producer"), 1024 * 1024, 65536, 2)
            spec_pin = write_once(self.output / (self.name + "-spec.json"), spec.to_json())
            with patch.object(producer, "actual_machine", return_value="unit-machine"), \
                 patch.object(producer, "validate_official_tool", return_value=(proof,)), \
                 patch.object(producer, "storage_admission", return_value={"authored_provider": True}), \
                 patch.object(producer, "execute_melter", side_effect=authored_tool):
                producer.produce_readback(Path(spec_pin["path"]))
        return {"authored_offline_transport": True}


def public_round_trip(root: Path, content: str, *, name: str = "checkpoint-readback-01", player_id: int = 91) -> tuple[object, Frame, Pin]:
    raw = root / "live.ck3"
    raw.write_text(content, encoding="utf-8")
    frame = Frame(3, 2, 53144328, player_id, 124, "9")
    manifest = write_once(root / "manifest.json", {"machine_id": "unit-machine", "game": {"version": "unit-version", "exe_sha256": "a" * 64}})
    snapshot = {"paused": True, "map_ready": True, "source": "injected-dll-named-pipe", "backend_id": "native-headless",
        "episode_projection": "native_campaign", "revision": 3, "native_revision": 2, "date_raw": frame.date_raw,
        "played_character": {"character_id": frame.player_id, "alive": True, "source": "native"},
        "managed_campaign_run_binding": {"run_id": "unit-run", "bridge_pipe": "unit-pipe"},
        "diagnostics": {"bridge_pid": 124, "connection_generation": 9, "pipe_name": "unit-pipe", "hello": {
            "pid": 124, "connection_generation": 9, "ck3_build_match": True, "expected_ck3_version": "unit-version", "expected_ck3_sha256": "a" * 64}}}
    native = write_once(root / "authored-original-native.json", {"rows": [{"ok": True, "plan": {"tool": "ck3_take_snapshot"}, "result": snapshot}]})
    request: Object = object_value({"schema": "living-artifacts-checkpoint-readback-request-v1", "run_id": "unit-run", "machine_id": "unit-machine",
        "pid": frame.pid, "connection_generation": frame.generation_decimal, "actor_character_id": frame.player_id, "date_raw": frame.date_raw,
        "actual_source_save": pin(raw), "expected_target_id": None, "required_response_schema": "living-artifacts-checkpoint-readback-v1",
        "required_unknown_token_policy": "error", "original_native_frame_record": native, "observation_number": 1,
        "storage_policy": "docs/storage-retention-policy.json", "business_pass": False})
    public: RootCheckpointConsumer = ProducingRoot(root, name, manifest)
    actual = public.root_checkpoint(name, request, reserve=180)
    return actual, frame, pin(raw)


def prepared_fixture(root: Path) -> Object:
    state, output, game = root / "state", root / "prepared", root / "game"
    output.mkdir()
    product = root / "formal"
    (product / "common/scripted_effects").mkdir(parents=True)
    (product / "descriptor.mod").write_text('name="Authored pipeline product"\n', encoding="utf-8")
    (product / "common/scripted_effects/core.txt").write_text(render_core_effects(), encoding="utf-8")
    engine = root / "shared-source/tools/fixture_engine_prepare.py"
    engine.parent.mkdir(parents=True)
    engine.write_text("def engine_identity(repo, *, game_dir, steam_manifest=None):\n return {'game_version':'unit-version','exe_sha256':'" + "a" * 64 + "'}\n", encoding="utf-8")
    plain: dict[str, Pin] = {}
    for index, name in enumerate(("pdx_settings.txt", "tutorial.txt", "presets.txt", "player/game_rules/presets.txt")):
        path = root / f"plain-{index}.txt"
        path.write_text("authored configuration\n", encoding="utf-8")
        plain[name] = pin(path)
    registry = read(REPO / "tools/ck3_mod_acceptance_products.json")
    product_spec = field(field(registry, "products"), "living-artifacts")
    case_spec = next(item for item in array(field(product_spec, "cases"), "cases") if field(item, "id") == "npc_continuous")
    manifest = write_once(root / "runtime-manifest.json", {"machine_id": "unit-machine", "game": {"version": "unit-version", "exe_sha256": "a" * 64}})
    context = object_value({"product": "living-artifacts", "case": "npc_continuous", "run_id": "unit-run", "state_dir": str(state), "output": str(output),
        "game_dir": str(game), "shared_source_root": str(engine.parents[1]), "shared_game": {"version": "unit-version", "exe_sha256": "a" * 64},
        "case_contract": read(TOOLS / "npc_continuous.contract.json"), "case_spec": case_spec, "runtime_manifest": manifest,
        "case_inputs": {"product_dir": str(product), "plain_configuration": plain}})
    source = write_once(root / "authored-source-provider.json", {"authored_sources_not_game_qualification": True})
    qualified = {binding.relative: source for binding in emitter.SOURCES}
    qualified.update({"binaries/ck3.exe": source, "product/prepare_npc_fixture.py": source, "product/living_artifacts_core.py": source, "product/living_artifacts_model.py": source})
    with patch.object(emitter, "qualify_sources", return_value=qualified), patch.object(emitter, "current_machine_id", return_value="unit-machine"):
        prepared = npc.prepare_case(context)
    if field(prepared, "runtime_status") != "NOT_RUN":
        raise AssertionError("Static preparation must not claim a live result")
    context["output"] = str(root / "case-output")
    Path(str(context["output"])).mkdir()
    return context


TOOLS = Path(__file__).resolve().parent


class AuthoredCasePort:
    """Shared Session consumes authored native frames, never a live backend."""
    def __init__(self, context: Object) -> None:
        self.output = Path(str(context["output"]))
        self.state = Path(str(context["state_dir"]))
        self.manifest_pin = object_value(field(context, "runtime_manifest"))
        self.manifest: object = read(Path(str(self.manifest_pin["path"])))
        self.frozen: object = {"run_id": "unit-run"}
        self.operator_reviewer = "unit-root"
        self.day = 0
        self.snapshots = 0
        self.saves = 0
        self.tools: list[str] = []

    def frame(self) -> Object:
        return object_value({"paused": True, "map_ready": True, "source": "injected-dll-named-pipe", "backend_id": "native-headless",
            "episode_projection": "native_campaign", "revision": 3 + self.day, "native_revision": 2 + self.day, "date_raw": 53144328 + self.day * 24,
            "played_character": {"character_id": 91, "alive": True, "source": "native"}, "active_event": None, "pending_character_interaction": None,
            "managed_campaign_run_binding": {"run_id": "unit-run", "bridge_pipe": "unit-pipe"},
            "diagnostics": {"bridge_pid": 124, "connection_generation": 9, "pipe_name": "unit-pipe", "hello": {
                "pid": 124, "connection_generation": 9, "ck3_build_match": True, "expected_ck3_version": "unit-version", "expected_ck3_sha256": "a" * 64}}})

    def guard(self, reserve: int = 90) -> object:
        return {"authored_guard": True}

    def snapshot(self, allow_actor_change: bool = False, require_event_free: bool = True) -> object:
        self.snapshots += 1
        result = self.frame()
        write_once(self.output / f"case-snapshot-{self.snapshots:04d}.actual-results.json", {"rows": [{"ok": True, "plan": {"tool": "ck3_take_snapshot"}, "result": result}]})
        return result

    def execute_plan(self, steps: list[Object], name: str, timeout: int | float | None = None, reserve: int = 90) -> object:
        if len(steps) != 1 or steps[0]["tool"] != "ck3_save_checkpoint":
            raise AssertionError("NPC scenario must not submit AI actions")
        self.tools.append("ck3_save_checkpoint")
        self.saves += 1
        source = self.state / "profile/save games/live.ck3"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(combined_save(day=self.day), encoding="utf-8")
        saved = pin(source)
        result = object_value({"checkpoint": {"status": "saved", "path": saved["path"], "size": saved["bytes"], "sha256": saved["sha256"],
            "date_raw": 53144328 + self.day * 24}, "materialization": {"available": True}})
        rows: list[Object] = [object_value({"id": name, "ok": True, "plan": steps[0], "result": result, "after_snapshot": self.frame()})]
        write_once(self.output / (name + ".actual-results.json"), {"rows": rows})
        return rows

    def advance_day(self, days: int = 1, timeout: float = 300, allow_event_boundary: bool = False, allow_actor_change: bool = False) -> object:
        if days != 1:
            raise AssertionError("Only real shared one-day interface belongs to this seam")
        self.day += 1
        return {"result": {"after": self.frame()}}

    def root_checkpoint(self, name: str, request: Object, reserve: int = 90) -> object:
        public: RootCheckpointConsumer = ProducingRoot(self.output, name, pin(Path(str(self.manifest_pin["path"]))))
        return public.root_checkpoint(name, request, reserve)

    def log_bytes(self, name: str = "debug.log", maximum: int = 64 * 1024 * 1024) -> bytes:
        return b""

    def checkpoint(self, name: str, value: object) -> object:
        return write_once(self.output / (name + ".json"), value)


class NpcReadbackIntegrationTests(unittest.TestCase):
    def test_r9_actual_reference_excerpt_through_producer_public_root_and_both_npc_consumers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            actual, frame, original = public_round_trip(Path(temporary), r9_excerpt_text(), player_id=31254)
            observed, verified = npc.consume_npc_readback(actual, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root",
                frame=frame, source_save=original, spec=emitter.NpcFixtureSpec(0))
            self.assertTrue(observed.initial_inputs_complete)
            self.assertEqual(tuple(role.owner_id for role in observed.roles), ("37243", "46974", "38570"))
            self.assertEqual(NpcSavedObservation.parse(json.loads(json.dumps(observed.to_json()))), observed)
            bound = npc.candidates(Path(verified.melted_save["path"]), "31254")
            self.assertEqual(tuple((item.role, item.status, item.owner_id) for item in bound), (
                ("landed", "bound", "37243"), ("baron", "bound", "46974"), ("courtier", "bound", "38570"), ("fragile", "bound", "43621")))
            self.assertTrue(all(item.raw_reference is not None and item.raw_reference.kind == "char" for item in bound))
            invalid = Path(temporary) / "authored-invalid-alias.ck3"
            invalid.write_text(r9_excerpt_text().replace("type=char", "type=character", 1), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Exact saved char"):
                npc.candidates(invalid, "31254")

    def test_real_producer_public_file_and_both_actual_consumers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            response, frame, source = public_round_trip(root, combined_save())
            player, refs = verify_readback(response, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root", frame=frame, source_save=source)
            observed, files = npc.consume_npc_readback(response, run_id="unit-run", machine_id="unit-machine", reviewer="unit-root", frame=frame,
                source_save=source, spec=emitter.NpcFixtureSpec(0))
            self.assertEqual(player.target_id, "12")
            self.assertTrue(observed.initial_inputs_complete)
            self.assertEqual(refs, files.evidence)
            self.assertEqual(files.source_save["sha256"], source["sha256"])
            self.assertEqual(len(observed.roles), 3)

    def test_wrong_identity_missing_fields_and_false_equal_types_fail_both_consumers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            response, frame, source = public_round_trip(Path(temporary), combined_save())
            row = object_value(response)
            mutations = ({**row, "pid": 124.0}, {**row, "schema_version": True}, {**row, "machine_id": "other"},
                {key: value for key, value in row.items() if key != "melter"})
            for invalid in mutations:
                for consumer in (verify_readback, npc.consume_npc_readback):
                    with self.subTest(consumer=consumer.__name__, invalid=invalid):
                        arguments: dict[str, object] = {"run_id": "unit-run", "machine_id": "unit-machine", "reviewer": "unit-root", "frame": frame, "source_save": source}
                        if consumer is npc.consume_npc_readback:
                            arguments["spec"] = emitter.NpcFixtureSpec(0)
                        self.assertRaises(ValueError, consumer, invalid, **arguments)

    def test_material_disappearance_alone_never_becomes_feeding_or_training(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initial_path = root / "initial.ck3"
            initial_path.write_text(combined_save(), encoding="utf-8")
            initial = observe_npc_saved(initial_path, player_id="91", machine_id="unit-machine", spec=emitter.NpcFixtureSpec(0))
            baseline = NpcInitialBaseline(initial)
            later: list[NpcSavedObservation] = []
            for day in (1, 16, 47):
                path = root / f"post-{day}.ck3"
                path.write_text(combined_save(day=day, markers=False), encoding="utf-8")
                later.append(observe_npc_saved(path, player_id="91", machine_id="unit-machine", spec=emitter.NpcFixtureSpec(0), phase="post", baseline=baseline))
            refs = [pin(initial_path)]
            checks = npc.evaluate(initial, tuple(later), npc.candidates(initial_path, "91"), refs=refs, production_sources=tuple(refs))
            by_id = {check["case_id"]: check for check in checks}
            for role in HEALTHY_ROLES:
                self.assertEqual(by_id["NPC-EQUIP-" + role]["status"], "PASS")
                self.assertEqual(by_id["NPC-GROW-" + role]["status"], "PASS")
                self.assertEqual(by_id["NPC-FEED-" + role]["status"], "BLOCKED")
                self.assertEqual(by_id["NPC-TRAIN-" + role]["status"], "BLOCKED")
            self.assertEqual(by_id["NPC-BIND-fragile"]["status"], "BLOCKED")

    def test_monthly_growth_cannot_be_replaced_by_day_one_cultivation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initial_path = root / "initial.ck3"; initial_path.write_text(combined_save(), encoding="utf-8")
            initial = observe_npc_saved(initial_path, player_id="91", machine_id="unit-machine", spec=emitter.NpcFixtureSpec(0))
            baseline = NpcInitialBaseline(initial)
            later: list[NpcSavedObservation] = []
            for day in (1, 16, 47):
                path = root / f"post-{day}.ck3"
                content = combined_save(day=day)
                if day == 47:
                    content = content.replace("identity=1600000", "identity=800000")
                path.write_text(content, encoding="utf-8")
                later.append(observe_npc_saved(path, player_id="91", machine_id="unit-machine", spec=emitter.NpcFixtureSpec(0), phase="post", baseline=baseline))
            refs = [pin(initial_path)]
            checks = npc.evaluate(initial, tuple(later), npc.candidates(initial_path, "91"), refs=refs, production_sources=tuple(refs))
            for check in checks:
                if check["case_id"].startswith("NPC-GROW-"):
                    self.assertEqual(check["status"], "BLOCKED")


class NpcPreparationTests(unittest.TestCase):
    def test_real_emitter_shared_prepare_source_table_and_loaded_deployment_closure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context = prepared_fixture(Path(temporary))
            state = Path(str(context["state_dir"]))
            refs = npc.prepared_sources(context, state)
            self.assertGreater(len(refs), 10)
            actual = read(state / "preparation.json")
            self.assertEqual(field(actual, "schema"), "ck3-mod-acceptance-profile-startup-evidence-v1")
            copied = state / "profile/mod-content/fixture/common/scripted_effects/xalw_npc_fixture_inputs.txt"
            self.assertTrue(copied.is_file())
            self.assertIn("xalw_npc_fixture_owner_fragile", copied.read_text(encoding="utf-8-sig"))
            self.assertNotIn("queue_item_001", copied.read_text(encoding="utf-8-sig"))
            self.assertTrue(npc.action_sources(state / "profile/mod-content/product"))

    def test_actual_closure_rejects_extra_or_modified_fixture_product_outer_and_source_table(self) -> None:
        cases = ("fixture", "product", "outer", "source-table")
        for kind in cases:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                context = prepared_fixture(Path(temporary))
                state = Path(str(context["state_dir"]))
                if kind == "fixture":
                    (state / "profile/mod-content/fixture/extra.txt").write_text("unlisted", encoding="utf-8")
                elif kind == "product":
                    (state / "profile/mod-content/product/common/scripted_effects/core.txt").write_text("changed", encoding="utf-8")
                elif kind == "outer":
                    (state / "profile/mod/product.mod").write_text('path="elsewhere"', encoding="utf-8")
                else:
                    target = state / "profile/mod-content/fixture/_case_contract.json"
                    value = read(target)
                    emission = object_value(field(value, "fixture_emission"))
                    emission["source_bindings"] = {}
                    value["fixture_emission"] = emission
                    target.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaises(ValueError):
                    npc.prepared_sources(context, state)

    def test_exclusive_action_writer_check_rejects_additional_marker_writer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context = prepared_fixture(Path(temporary))
            product = Path(str(context["state_dir"])) / "profile/mod-content/product"
            npc.action_sources(product)
            (product / "common/scripted_effects/extra.txt").write_text('cheat = { set_variable = { name = xalw_feeding_imprint value = flag:primary_armament } }', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exclusive"):
                npc.action_sources(product)

    def test_unique_marker_moved_outside_success_branch_cannot_qualify_feeding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context = prepared_fixture(Path(temporary))
            product = Path(str(context["state_dir"])) / "profile/mod-content/product"
            path = product / "common/scripted_effects/core.txt"
            source = path.read_text(encoding="utf-8")
            writer = "set_variable = { name = xalw_feeding_imprint value = var:xalw_pending_feed_imprint days = 90 }"
            self.assertEqual(source.count(writer), 1)
            source = source.replace(writer, "# original writer moved", 1)
            source = source.replace("xalw_feed_material_effect = {", "xalw_feed_material_effect = {\n" + writer, 1)
            path.write_text(source, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "post-destruction"):
                npc.action_sources(product)

    def test_full_shared_session_four_producers_natural_days_and_actual_verify_reprojection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context = prepared_fixture(Path(temporary))
            port = AuthoredCasePort(context)
            # Startup source proof has its own existing full native/source tests.
            startup = StartupActorBinding(91, 124, "9", 53144328, 25, "a" * 64, "b" * 64)
            with patch.object(StartupActorBinding, "parse", return_value=startup):
                result = npc.run_case(context, port)
            self.assertEqual((port.day, port.saves), (47, 4))
            self.assertEqual(port.tools, ["ck3_save_checkpoint"] * 4)
            checks = {str(field(item, "case_id")): field(item, "status") for item in array(result["checks"], "checks")}
            for role in HEALTHY_ROLES:
                for action in ("BIND", "EQUIP", "GROW", "TRAIN", "FEED"):
                    self.assertEqual(checks["NPC-" + action + "-" + role], "PASS")
            self.assertEqual(checks["NPC-BIND-fragile"], "BLOCKED")
            first = read(port.output / "npc-observer-checkpoint-01.json")
            original = object_value(field(first, "source_save"))
            self.assertNotEqual(pin(Path(str(original["path"])))['sha256'], original["sha256"])
            verified = npc.verify_case(context)
            self.assertEqual(verified, result)
            self.assertIs(verified["business_pass"], False)
            self.assertIs(verified["current_native_npc_equipment"], False)
            result_path = port.output / npc.RESULT_NAME
            original_result = result_path.read_text(encoding="utf-8")
            for key, value in (("machine_id", "other-machine"), ("actual_saved_observations", 3), ("actual_natural_days", True),
                    ("actual_public_calls_budgeted", 321), ("normal_close_pending", False), ("unknown_field", True)):
                with self.subTest(forged_result=key):
                    changed = object_value(json.loads(original_result))
                    changed[key] = value
                    result_path.write_text(json.dumps(changed), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        npc.verify_case(context)
            for key, check_value in (("evidence", []), ("evidence_scope", "native_current"), ("reason", "invented")):
                with self.subTest(forged_check=key):
                    changed = object_value(json.loads(original_result))
                    rows = array(changed["checks"], "checks")
                    rows[0] = {**object_value(rows[0]), key: check_value}
                    changed["checks"] = object_value({"rows": rows})["rows"]
                    result_path.write_text(json.dumps(changed), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        npc.verify_case(context)
            result_path.write_text(original_result, encoding="utf-8")
            forged = dict(result)
            altered = array(forged["checks"], "checks")
            altered[3] = {**object_value(altered[3]), "status": "PASS", "reason": None}
            forged["checks"] = object_value({"rows": altered})["rows"]
            (port.output / npc.RESULT_NAME).write_text(json.dumps(forged), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "action claim"):
                npc.verify_case(context)

    def test_initially_equipped_target_cannot_receive_new_equipment_credit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "initial.ck3"
            source.write_text(combined_save(initially_equipped=True), encoding="utf-8")
            initial = observe_npc_saved(source, player_id="91", machine_id="unit-machine", spec=emitter.NpcFixtureSpec(0))
            baseline = NpcInitialBaseline(initial)
            after = root / "after.ck3"
            after.write_text(combined_save(day=47), encoding="utf-8")
            later = observe_npc_saved(after, player_id="91", machine_id="unit-machine", spec=emitter.NpcFixtureSpec(0), phase="post", baseline=baseline)
            for check in npc.evaluate(initial, (later,), npc.candidates(source, "91"), refs=[pin(source)], production_sources=(pin(source),)):
                if check["case_id"].startswith("NPC-EQUIP-"):
                    self.assertEqual(check["status"], "BLOCKED")

    def test_public_registration_loads_in_fresh_python_process_without_product_pythonpath(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths: dict[str, str] = {}
            for key in ("host", "source_index", "native_source_index", "dll", "injector"):
                source = root / (key + ".py" if key == "host" else key + ".json")
                source.write_text("# authored host; never execute\n" if key == "host" else "{}", encoding="utf-8")
                paths[key] = str(source)
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
                "from ck3_mod_acceptance import Selection\ns=Selection(Path(sys.argv[2]),Path(sys.argv[1])/'tools/ck3_mod_acceptance_products.json','living-artifacts','npc_continuous')\n"
                "m=s.load_adapter()\nc=m.validate_contract(s.adapter_context())\nassert c.maximum_checkpoints==4\nassert m.__name__=='ck3_mod_acceptance_cases.npc_acceptance_adapter'\nprint('ACTUAL_PUBLIC_COLD_IMPORT_OK')\n", encoding="utf-8")
            completed = subprocess.run([sys.executable, "-B", "-X", "utf8", str(script), str(REPO), runtime["path"]], capture_output=True, text=True, timeout=30)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("ACTUAL_PUBLIC_COLD_IMPORT_OK", completed.stdout)


if __name__ == "__main__":
    unittest.main()

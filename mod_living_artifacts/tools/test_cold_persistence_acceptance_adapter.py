"""Authored saved/readback boundaries through actual consumers; no native credit."""
from __future__ import annotations

from dataclasses import replace
import argparse
import asyncio
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parents[1]
for directory in (REPO, REPO / "tools", REPO / "ck3_autonomous_player/src"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import cold_persistence_acceptance_adapter as adapter
from acceptance_adapter import ITEM
from acceptance_contract import Frame, Object, Pin, array, field, json_value, mapping, object_value, pin, read, write_once
from checkpoint_callback import CheckpointSample, verify_readback
from checkpoint_artifacts import SavedVariable
from cold_persistence_observer import ObservedCheckpoint, compare_persistence, consume_checkpoint
from independent_mod_release import build
from product import spec
from test_checkpoint_artifacts import authored_survivors
from test_checkpoint_callback import callback_fixture
from test_saved_campaign_actor_binding import EXE_SHA, RestoreClient, actual_restore, cold_frame
from test_saved_campaign_profile_inventory_v2 import ProfileSpec, actual_host_preparer
from test_native_interruption_contract import RootCheckpointConsumer
from test_npc_acceptance_adapter import ProducingRoot


def observed_fixture(root: Path, run: str, *, features: bool = True, preserved_copy: bool = False) -> tuple[ObservedCheckpoint, Object, Pin, Pin, Pin]:
    root.mkdir(parents=True)
    response, _, source = callback_fixture(root, artifacts=authored_survivors(()))
    melted_path = Path(text_value(field(field(response, "melted_save"), "path")))
    if features:
        raw = melted_path.read_text(encoding="utf-8")
        marker = '{ flag="xalw_level"'
        extra = ('{ flag="xalw_growth_suppressed_until" data={ type=value identity=12354600000 } } '
            '{ flag="xalw_suppression_timer_sequence" data={ type=value identity=200000 } } '
            '{ flag="xalw_feeding_imprint" data={ type=flag flag=primary_armament } } ')
        melted_path.write_text(raw.replace(marker, extra + marker, 1), encoding="utf-8")
    request = read(root / "request.json")
    request["run_id"] = run
    request_ref = write_once(root / "request-current.json", request)
    process = read(root / "process.json")
    process["run_id"] = run
    process["request"] = json_value(request_ref)
    process["melted"] = json_value(pin(melted_path))
    if preserved_copy:
        retained_raw = root / "retained-original.ck3"
        retained_raw.write_bytes(Path(source["path"]).read_bytes())
        response["source_save"] = json_value(pin(retained_raw))
        process["raw"] = json_value(pin(retained_raw))
        command = read(root / "command.json")
        argv = array(command["argv"], "authored strict argv")
        argv[2] = str(retained_raw.resolve())
        command["argv"] = json_value(argv)
        command_ref = write_once(root / "command-preserved.json", command)
        response["command"] = json_value(command_ref)
        process["command"] = json_value(command_ref)
    process_ref = write_once(root / "process-current.json", process)
    response["run_id"] = run
    response["melted_save"] = json_value(pin(melted_path))
    response["process_receipt"] = json_value(process_ref)
    manifest: Object = {"machine_id": "unit-machine", "game": {"version": "1.20.0.4", "exe_sha256": EXE_SHA}}
    snapshot = cold_frame(epoch=4, run_id=run)
    frame_ref = write_once(root / "case-snapshot-01.actual-results.json", {"rows": [{"plan": {"tool": "ck3_take_snapshot"},
        "ok": True, "error": None, "result": snapshot, "after_snapshot": snapshot}]})
    request["original_native_frame_record"] = json_value(frame_ref)
    request["expected_target_id"] = None
    process["request"] = json_value(write_once(root / "request-final.json", request))
    response["process_receipt"] = json_value(write_once(root / "process-final.json", process))
    save_payload: Object = {"rows": [{"plan": {"tool": "ck3_save_checkpoint"}, "ok": True, "error": None,
        "result": {"checkpoint": {"status": "saved", "path": source["path"], "size": source["bytes"], "sha256": source["sha256"], "date_raw": 123456},
            "materialization": {"available": True}}, "after_snapshot": snapshot}]}
    save_ref = write_once(root / "save.actual-results.json", save_payload)
    item_payload: Object = {"rows": [{"plan": {"tool": "ck3_query_player_artifact_personal_use_v1"},
        "ok": True, "error": None, "result": {"available": True, "read_only": True, "loaded_source_pins_verified": True,
            "personally_owned": True, "inventory_artifact": True, "equipped": True, "requested_artifact_id": 12,
            "played_character_id": 91, "date_raw": 123456, "owned_ids": [12]}, "after_snapshot": snapshot}]}
    item_ref = write_once(root / "item.actual-results.json", item_payload)
    frame = Frame.parse(snapshot, run_id=run, machine_id="unit-machine", manifest=manifest)
    inputs, _ = verify_readback(response, run_id=run, machine_id="unit-machine", reviewer="unit-root", frame=frame,
        source_save=source, expected_material_rarities=())
    sample = CheckpointSample.from_saved(inputs.artifacts[0], inputs, native_equipped=True)
    record: Object = {"schema_version": 2, "run_id": run, "machine_id": "unit-machine", "observed_at_utc": "2000-01-01T00:00:00Z",
        "native_date_raw": 123456, "sample": sample.to_json(), "saved_inputs": inputs.to_json(), "readback_response": response,
        "original_native_frame_record": json_value(frame_ref), "expected_material_rarities": [], "current_native_artifact_variable_query": False}
    observation_ref = write_once(root / "observer-checkpoint-07.json", record)
    actual = consume_checkpoint(read(Path(observation_ref["path"])), run_id=run, machine_id="unit-machine", reviewer="unit-root",
        manifest=manifest, save_native=save_ref, item_native=item_ref)
    return actual, manifest, observation_ref, save_ref, item_ref


def text_value(value: object) -> str:
    if not isinstance(value, str):
        raise AssertionError("Authored string required")
    return value


def compound_context(root: Path) -> tuple[dict[str, object], ObservedCheckpoint, dict[str, object], Object]:
    before, manifest, observation, save_ref, item_ref = observed_fixture(root / "old-live", "original-run")
    runtime = write_once(root / "runtime-manifest.json", manifest)
    frozen_source = write_once(root / "old-live/frozen-argv.json", {"run_id": "original-run", "runtime_manifest": runtime})
    source_context = write_once(root / "old-context.json", {"schema": "ck3-mod-acceptance-run-context-v1", "product": "living-artifacts",
        "run_id": "original-run", "run_dir": str(root / "old-live"), "frozen_argv": frozen_source})
    revision = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    staging, formal, _, _ = build(spec(), root / "formal", revision)
    config: dict[str, Pin] = {}
    for index, name in enumerate(("pdx_settings.txt", "tutorial.txt", "presets.txt", "player/game_rules/presets.txt")):
        path = root / "config" / str(index)
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(b"authored configuration")
        config[name] = pin(path)
    context: dict[str, object] = {"product": "living-artifacts", "case": adapter.CASE, "run_id": None,
        "case_contract": read(TOOLS / adapter.CONTRACT_NAME), "case_spec": read(TOOLS / adapter.REGISTRY_NAME), "runtime_manifest": runtime,
        "state_dir": str(root / "new-state"), "output": str(root / "prepared"),
        "case_inputs": {"product_dir": str(staging), "formal_manifest": pin(formal), "plain_configuration": config,
            "source_run_context": source_context, "source_runtime_manifest": runtime, "source_checkpoint_observation": observation,
            "source_save_native_record": save_ref, "source_item_native_record": item_ref},
        "saved_campaign": {"save": before.load_save["path"], "bytes": before.load_save["bytes"], "sha256": before.load_save["sha256"], "player_id": 91, "date_raw": 123456},
        "shared_source_root": str(REPO), "_selected_engine": (object(), {"game_version": "1.20.0.4", "exe_sha256": EXE_SHA})}
    prepared = adapter.prepare_case(context)
    seed = field(field(prepared, "startup"), "saved_campaign")
    args = argparse.Namespace(saved_campaign_save=Path(text_value(field(seed, "save"))), saved_campaign_save_bytes=field(seed, "bytes"),
        saved_campaign_save_sha256=field(seed, "sha256"), saved_campaign_player_id=91, saved_campaign_date_raw=123456,
        saved_campaign_product_inventory=Path(text_value(field(seed, "product_inventory"))))
    copied = mapping(actual_host_preparer()(args, ProfileSpec(root / "new-state/profile", root / "new-state")), "actual copied save")
    report: dict[str, object] = {"pipe": "unit-pipe", "saved_campaign_input": copied,
        "saved_campaign_launch": {"status": "ACTUAL_SINGLE_CLI_RESTORE_LAUNCHED", "argv_admitted": True,
            "continue_last_save": False, "load_save_name": "restored_campaign", "ck3_pid": 124,
            "command": ["AUTHORED-TEST-NO-PROCESS", "-loadsave=restored_campaign"]}}

    def write() -> None:
        return None

    async def restore() -> object:
        return await actual_restore()(RestoreClient("unit-run"), {key: copied[key] for key in ("source_path", "bytes", "sha256", "actor_character_id", "date_raw")},
            report=report, write=write, timeout=3.0, managed_done=None, poll_interval=0.001)

    asyncio.run(restore())
    live = root / "unit-run"
    frozen: Object = {"run_id": "unit-run", "argv": ["host", "--state-dir", str(root / "new-state"),
        "--saved-campaign-save", text_value(field(seed, "save")), "--saved-campaign-save-bytes", str(field(seed, "bytes")),
        "--saved-campaign-save-sha256", text_value(field(seed, "sha256")), "--saved-campaign-player-id", "91",
        "--saved-campaign-date-raw", "123456", "--saved-campaign-product-inventory", text_value(field(seed, "product_inventory"))]}
    write_once(live / "native-report.json", report)
    write_once(live / "frozen-argv.json", frozen)
    context.update(run_id="unit-run", run_dir=str(live), output=str(live / "case-output"), saved_campaign=seed, operator_reviewer="unit-root")
    (live / "case-output").mkdir()
    return context, before, report, frozen


class ColdPort:
    """Authored native side; actual Session, public Root, producer and parsers."""
    def __init__(self, context: object, source: ObservedCheckpoint, report: object, frozen: object, *, changed_sequence: bool = False) -> None:
        self.output = Path(text_value(field(context, "output")))
        self.state = Path(text_value(field(context, "state_dir")))
        self.manifest_pin = pin(Path(text_value(field(field(context, "runtime_manifest"), "path"))))
        self.manifest: object = read(Path(self.manifest_pin["path"]))
        self.frozen = frozen
        self.operator_reviewer = "unit-root"
        self.report = report
        self.snapshots = 0
        self.saves = 0
        self.tools: list[str] = []
        self.content = Path(text_value(field(field(source.response, "melted_save"), "path"))).read_text(encoding="utf-8")
        if changed_sequence:
            self.content = self.content.replace('flag="xalw_suppression_timer_sequence" data={ type=value identity=200000',
                'flag="xalw_suppression_timer_sequence" data={ type=value identity=300000', 1)

    def guard(self, reserve: int = 90) -> object:
        return self.report

    def snapshot(self, allow_actor_change: bool = False, require_event_free: bool = True) -> object:
        self.snapshots += 1
        snapshot = cold_frame(epoch=4, run_id="unit-run")
        write_once(self.output / f"case-snapshot-{self.snapshots:04d}.actual-results.json", {"rows": [
            {"plan": {"tool": "ck3_take_snapshot"}, "ok": True, "error": None, "result": snapshot}]})
        return snapshot

    def execute_plan(self, steps: list[Object], name: str, timeout: int | float | None = None, reserve: int = 90) -> object:
        step = steps[0]
        tool = text_value(step["tool"])
        self.tools.append(tool)
        if tool == "ck3_save_checkpoint":
            self.saves += 1
            source = self.state / "profile/save games/authored-new-cold.ck3"
            source.write_text(self.content, encoding="utf-8")
            saved = pin(source)
            result: Object = object_value({"checkpoint": {"status": "saved", "path": saved["path"], "size": saved["bytes"],
                "sha256": saved["sha256"], "date_raw": 123456}, "materialization": {"available": True}})
        elif tool == ITEM:
            result = {"available": True, "read_only": True, "loaded_source_pins_verified": True, "personally_owned": True,
                "inventory_artifact": True, "equipped": True, "requested_artifact_id": 12, "played_character_id": 91,
                "date_raw": 123456, "owned_ids": [12]}
        else:
            raise AssertionError("Cold case cannot perform this action: " + tool)
        rows = [object_value({"plan": step, "ok": True, "error": None, "result": result, "after_snapshot": cold_frame(epoch=4, run_id="unit-run")})]
        write_once(self.output / (name + ".actual-results.json"), {"rows": rows})
        return rows

    def root_checkpoint(self, name: str, request: Object, reserve: int = 90) -> object:
        public: RootCheckpointConsumer = ProducingRoot(self.output, name, self.manifest_pin)
        return public.root_checkpoint(name, request, reserve)

    def advance_day(self, days: int = 1, timeout: float = 300, allow_event_boundary: bool = False, allow_actor_change: bool = False) -> object:
        raise AssertionError("Cold case cannot advance game days")

    def log_bytes(self, name: str = "debug.log", maximum: int = 64 * 1024 * 1024) -> bytes:
        return b""

    def checkpoint(self, name: str, value: object) -> object:
        return write_once(self.output / (name + ".json"), value)


class ColdPersistenceTests(unittest.TestCase):
    def test_retained_original_copy_stays_valid_after_native_save_slot_is_reused(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            actual, manifest, observation, save_ref, item_ref = observed_fixture(Path(temporary) / "old", "original-run", preserved_copy=True)
            source_row = read(Path(save_ref["path"]))
            rows = array(source_row["rows"], "authored Save rows")
            original_path = Path(text_value(field(field(field(rows[0], "result"), "checkpoint"), "path")))
            original_path.write_bytes(b"later actual Save reused the original slot")
            reparsed = consume_checkpoint(read(Path(observation["path"])), run_id="original-run", machine_id="unit-machine", reviewer="unit-root",
                manifest=manifest, save_native=save_ref, item_native=item_ref)
            self.assertEqual(reparsed.inputs, actual.inputs)
            self.assertEqual(reparsed.load_save, actual.load_save)
    def test_actual_prepare_host_restore_session_public_producer_consumers_and_verify(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, source, report, frozen = compound_context(Path(temporary))
            port = ColdPort(context, source, report, frozen)
            result = adapter.run_case(context, port)
            self.assertEqual(result["status"], "PASS", result.get("error"))
            self.assertEqual(port.saves, 1)
            self.assertEqual(port.tools, ["ck3_save_checkpoint", ITEM])
            self.assertEqual(adapter.verify_case(context), result)
            self.assertFalse(result["business_pass"])
            self.assertFalse(result["product_release_pass"])
            self.assertEqual(field(read(port.output / "cold-checkpoint-01.json"), "schema"), "living-artifacts-cold-checkpoint-v1")
            empty = port.output / "unrelated-empty.json"
            empty.write_bytes(b"")
            retained = read(port.output / adapter.RESULT_NAME)
            evidence = array(retained["evidence"], "authored retained evidence")
            evidence.append(pin(empty))
            retained["evidence"] = json_value(evidence)
            (port.output / adapter.RESULT_NAME).write_text(json.dumps(retained), encoding="utf-8")
            with self.assertRaises(ValueError):
                adapter.verify_case(context)

    def test_real_produced_drift_is_fail_and_retained_status_or_restore_tamper_cannot_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            context, source, report, frozen = compound_context(Path(temporary))
            port = ColdPort(context, source, report, frozen, changed_sequence=True)
            result = adapter.run_case(context, port)
            self.assertEqual(result["status"], "FAIL", result.get("error"))
            self.assertEqual(adapter.verify_case(context), result)
            result_path = port.output / adapter.RESULT_NAME
            retained = read(result_path)
            retained["status"] = "PASS"
            result_path.write_text(json.dumps(retained), encoding="utf-8")
            with self.assertRaises(ValueError):
                adapter.verify_case(context)
    def test_source_and_new_saved_callbacks_reach_all_real_consumers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            before, _, _, _, _ = observed_fixture(root / "before", "original-run")
            after, _, _, _, _ = observed_fixture(root / "after", "new-cold-run")
            checks = compare_persistence(before, after)
            self.assertEqual(tuple(check["case_id"] for check in checks), adapter.CHECKS)
            self.assertTrue(all(check["status"] == "PASS" for check in checks))
            self.assertEqual(before.artifact.variables["xalw_suppression_timer_sequence"].integer_value("sequence"), 2)
            self.assertEqual(before.artifact.variables["xalw_feeding_imprint"].flag, "primary_armament")

    def test_missing_source_features_are_blocked_not_false_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            before, _, _, _, _ = observed_fixture(root / "before", "original-run", features=False)
            after, _, _, _, _ = observed_fixture(root / "after", "new-cold-run", features=False)
            checks = compare_persistence(before, after)
            self.assertEqual([row["case_id"] for row in checks if row["status"] == "BLOCKED"], list(adapter.CHECKS[2:5]))

    def test_identically_invalid_source_feature_values_cannot_qualify(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            before, _, _, _, _ = observed_fixture(root / "before", "original-run")
            after, _, _, _, _ = observed_fixture(root / "after", "new-cold-run")
            invalid = (
                ("xalw_growth_suppressed_until", 2, SavedVariable("value", None, None)),
                ("xalw_growth_suppressed_until", 2, SavedVariable("flag", None, "123546")),
                ("xalw_suppression_timer_sequence", 3, SavedVariable("value", "-100000", None)),
                ("xalw_suppression_timer_sequence", 3, SavedVariable("value", "150000", None)),
                ("xalw_feeding_imprint", 4, SavedVariable(None, None, "primary_armament")),
                ("xalw_feeding_imprint", 4, SavedVariable("flag", "1", "primary_armament")),
                ("xalw_feeding_imprint", 4, SavedVariable("flag", None, "weapon")),
            )
            for name, index, value in invalid:
                def changed(checkpoint: ObservedCheckpoint) -> ObservedCheckpoint:
                    variables = {**checkpoint.artifact.variables, name: value}
                    artifact = replace(checkpoint.artifact, variables=variables)
                    return replace(checkpoint, inputs=replace(checkpoint.inputs, artifacts=(artifact,)))
                with self.subTest(name=name, value=value):
                    checks = compare_persistence(changed(before), changed(after))
                    self.assertEqual(checks[index]["status"], "BLOCKED")

    def test_changed_growth_deadline_sequence_imprint_and_materials_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            before, _, _, _, _ = observed_fixture(root / "before", "original-run")
            after, _, _, _, _ = observed_fixture(root / "after", "new-cold-run")
            changed_sample = replace(after.sample, xp=after.sample.xp + 1)
            self.assertEqual(compare_persistence(before, replace(after, sample=changed_sample))[0]["status"], "FAIL")
            for name, check in (("xalw_growth_suppressed_until", 2), ("xalw_suppression_timer_sequence", 3), ("xalw_feeding_imprint", 4)):
                variables = dict(after.artifact.variables)
                del variables[name]
                artifact = replace(after.artifact, variables=variables)
                inputs = replace(after.inputs, artifacts=(artifact,))
                changed = replace(after, inputs=inputs)
                with self.subTest(name=name):
                    self.assertEqual(compare_persistence(before, changed)[check]["status"], "FAIL")
            with self.assertRaises(ValueError):
                compare_persistence(before, replace(after, run_id=before.run_id))

    def test_real_native_save_identity_and_strict_receipts_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            actual, manifest, observation, save_ref, item_ref = observed_fixture(Path(temporary) / "old", "original-run")
            row = read(Path(observation["path"]))
            changed = read(Path(save_ref["path"]))
            rows = field(changed, "rows")
            if not isinstance(rows, list):
                raise AssertionError("Authored Save rows absent")
            target = field(field(rows[0], "result"), "checkpoint")
            if not isinstance(target, dict):
                raise AssertionError("Authored checkpoint absent")
            target["size"] = True
            bad_ref = write_once(Path(temporary) / "bad-save.json", changed)
            with self.assertRaises(ValueError):
                consume_checkpoint(row, run_id="original-run", machine_id="unit-machine", reviewer="unit-root", manifest=manifest,
                    save_native=bad_ref, item_native=item_ref)
            Path(actual.load_save["path"]).write_bytes(b"changed source")
            with self.assertRaises(ValueError):
                consume_checkpoint(row, run_id="original-run", machine_id="unit-machine", reviewer="unit-root", manifest=manifest,
                    save_native=save_ref, item_native=item_ref)

    def test_actual_adapter_prepare_formal_v2_and_host_copy_without_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            before, manifest, observation, save_ref, item_ref = observed_fixture(root / "old-live", "original-run")
            runtime = write_once(root / "runtime-manifest.json", manifest)
            frozen = write_once(root / "old-live/frozen-argv.json", {"run_id": "original-run", "runtime_manifest": runtime})
            source_context = write_once(root / "old-context.json", {"schema": "ck3-mod-acceptance-run-context-v1", "product": "living-artifacts",
                "run_id": "original-run", "run_dir": str(root / "old-live"), "frozen_argv": frozen})
            revision = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
            staging, formal, _, _ = build(spec(), root / "formal", revision)
            config: dict[str, Pin] = {}
            for index, name in enumerate(("pdx_settings.txt", "tutorial.txt", "presets.txt", "player/game_rules/presets.txt")):
                path = root / "config" / str(index)
                path.parent.mkdir(exist_ok=True)
                path.write_bytes(b"authored configuration")
                config[name] = pin(path)
            context: dict[str, object] = {"product": "living-artifacts", "case": adapter.CASE, "run_id": None,
                "case_contract": read(TOOLS / adapter.CONTRACT_NAME), "case_spec": read(TOOLS / adapter.REGISTRY_NAME), "runtime_manifest": runtime,
                "state_dir": str(root / "new-state"), "output": str(root / "prepared"),
                "case_inputs": {"product_dir": str(staging), "formal_manifest": pin(formal), "plain_configuration": config,
                    "source_run_context": source_context, "source_runtime_manifest": runtime, "source_checkpoint_observation": observation,
                    "source_save_native_record": save_ref, "source_item_native_record": item_ref},
                "saved_campaign": {"save": before.load_save["path"], "bytes": before.load_save["bytes"], "sha256": before.load_save["sha256"],
                    "player_id": 91, "date_raw": 123456},
                "shared_source_root": str(REPO), "_selected_engine": (object(), {"game_version": "1.20.0.4", "exe_sha256": EXE_SHA})}
            prepared = adapter.prepare_case(context)
            startup = field(prepared, "startup")
            self.assertEqual(field(startup, "mode"), "saved_campaign")
            self.assertFalse(prepared["fixture_mounted"])
            self.assertFalse((root / "new-state/profile/mod-content/fixture").exists())
            seed = field(startup, "saved_campaign")
            import argparse
            args = argparse.Namespace(saved_campaign_save=Path(text_value(field(seed, "save"))), saved_campaign_save_bytes=field(seed, "bytes"),
                saved_campaign_save_sha256=field(seed, "sha256"), saved_campaign_player_id=91, saved_campaign_date_raw=123456,
                saved_campaign_product_inventory=Path(text_value(field(seed, "product_inventory"))))
            copied = actual_host_preparer()(args, ProfileSpec(root / "new-state/profile", root / "new-state"))
            self.assertFalse(field(copied, "source_game_state_claimed"))
            self.assertEqual((root / "new-state/profile/save games/restored_campaign.ck3").read_bytes(), Path(before.load_save["path"]).read_bytes())
            self.assertEqual(adapter.verify_case({**context, "run_id": "new-run", "output": str(root / "not-run")})["status"], "NOT_RUN")


if __name__ == "__main__":
    unittest.main()

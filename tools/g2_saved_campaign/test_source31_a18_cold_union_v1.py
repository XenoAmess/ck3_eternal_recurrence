"""Portable A18 DTO and projection regressions using actual repository functions.

All manifests, refs and identities are synthetic model inputs. Paths named by
producer constants are compared as protocol values, never opened. This suite
does not qualify a cold graph, native DLL, actual ledger, Task, Steam or game.
"""
from __future__ import annotations

import ast
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from enum import IntEnum
import hashlib
import inspect
import json
from pathlib import Path
import sys
from typing import TypedDict
import unittest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import prepare_source31_a18_cold_union_v1 as main
import prepare_source31_a18_owner_metadata_v1 as owner

Doc = dict[str, object]
NOW = datetime(2026, 10, 21, 1, 45, tzinfo=timezone.utc)
PLAN_REFS = (
    "full_storage_ref", "live_storage_ref", "steam_native_state_ref",
    "union_producer", "stage_producer", "sdk_base_ref", "canonical_anchor_ref",
    "native_binding_ref", "closure_ref", "current_driver_review_ref", "ledger_ref",
    "current_next_ref", "runtime_adapter_ref", "runtime_extension_ref",
)
OWNER_REFS = (
    "cold_graph_plan", "cold_graph_quote", "full_storage_ref", "live_storage_ref",
    "actual_game", "sdk_freeze", "business_anchor", "mod_absence",
)
SDK = (
    "xar_autoplayer/bridge/native_driver.py",
    "xar_autoplayer/bridge/cached_native_clock_summary_v1.py",
    "xar_autoplayer/bridge/tactical_clock_diagnostics_v1.py",
    "xar_autoplayer/bridge/exact_clock_failure_diagnostic_v1.py",
    "xar_autoplayer/bridge/player_lifestyle_private_transport_v1.py",
    "xar_autoplayer/successor_ui_pending_ledger_v1.py",
)
PREFIX = "ck3_autonomous_player/src/"


class Number(IntEnum):
    ONE = 1


def doc(value: object) -> Doc:
    return main.record(value)


def exact_ref(name: str) -> main.ExactRef:
    return {"path": str((HERE / "RAM-not-created" / name).resolve()),
            "bytes": 1, "sha256": "a" * 64}


def plan_input() -> Doc:
    result: Doc = {
        "schema": "xar.Source31-A18-complete-cold-input/v1",
        "machine_id": main.MACHINE, "execution_owner": "Root",
        "root_direct_execution_release": True, "observed_at_utc": NOW.isoformat(),
        "attempt_nonce": "a" * 32, "task_nonce": "b" * 32,
        "screen_admission_path": str(main.SCREEN),
    }
    for name in PLAN_REFS:
        result[name] = exact_ref(name)
    return result


def admission_input() -> Doc:
    return {
        "schema": "xar.Source31-A18-runtime-prepare-admission/v1",
        "machine_id": "portable-model-machine", "owner": "Root",
        "status": "ADMITTED", "root_direct_execution_release": True,
        "canonical_capacity_review_passed": True, "runtime_hard_bytes": 3145728,
        "plan": exact_ref("plan"), "quote": exact_ref("quote"),
        "full_storage_ref": exact_ref("full"),
        "capacity": {"D_free_floor_bytes": 2**53 - 1, "Z_free_floor_bytes": 1},
    }


def owner_input() -> Doc:
    value: Doc = {
        "schema": "xar.C23-A18-cold-owner-metadata-input/v1",
        "machine_id": owner.MACHINE, "execution_owner": "Root",
        "root_direct_execution_release": True, "observed_at_utc": NOW.isoformat(),
        "runtime_root": str(owner.TARGET),
        "recording": {name: exact_ref(name) for name in (
            "request", "job", "started", "first_frame_admission", "publisher_started")},
    }
    for name in OWNER_REFS:
        value[name] = exact_ref(name)
    return value


class MetadataFixture(TypedDict):
    base: Doc
    anchor: Doc
    parent: Doc
    parent_anchor_ref: main.ExactRef
    parent_base_ref: main.ExactRef


def metadata_fixture() -> MetadataFixture:
    # Match the actual writer's five-field SDKRow and CanonicalPatchRow domains.
    before: list[object] = []
    names = [name for name in SDK if name != SDK[1]]
    names += ["unchanged/" + str(i).zfill(4) + ".py" for i in range(1460)]
    for name in names:
        before.append({"relative": name, "bytes": 1, "sha256": "a" * 64,
                       "git_blob_sha1": "a" * 40, "git_mode": "100644"})
    after = deepcopy(before)
    for i, value in enumerate(after):
        row = doc(value)
        if row["relative"] in SDK:
            row.update(bytes=2, sha256="b" * 64, git_blob_sha1="b" * 40)
        after[i] = row
    after.append({"relative": SDK[1], "bytes": 2, "sha256": "b" * 64,
                  "git_blob_sha1": "b" * 40, "git_mode": "100644"})
    old = {main.text(doc(value)["relative"]): doc(value) for value in before}
    current = {main.text(doc(value)["relative"]): doc(value) for value in after}
    public: list[object] = [
        {"relative": name, "pin": {"bytes": 2, "sha256": "b" * 64}}
        for name in SDK[1:5]]
    # Execute the real writer's pure return projection, without mocking its I/O guards.
    tree = ast.parse((HERE / "write_source31_canonical_ref_v1.py").read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "canonical_patch_rows_v1")
    returned = next(node for node in function.body if isinstance(node, ast.Return))
    if returned.value is None:
        raise AssertionError("real canonical writer projection required")
    pins = {name: {"bytes": 2, "sha256": "b" * 64} for name in SDK}
    scope: Doc = {"SDK": SDK, "PREFIX": PREFIX, "PUBLIC": SDK[1:5],
        "POST_PINS": pins, "PUBLIC_PINS": pins, "plan": {"public_source_commit": "d" * 40},
        "before": {name: {"bytes": row["bytes"], "sha256": row["sha256"]}
                   for name, row in old.items()}, "__builtins__": {}}
    canonical: object = eval(compile(ast.Expression(returned.value),
        "<actual Source31 canonical-row producer projection>", "eval"), scope)
    packed = json.dumps(after, ensure_ascii=False, sort_keys=True,
                        separators=(",", ":"), allow_nan=False).encode()
    parent_anchor, parent_base = exact_ref("parent-anchor"), exact_ref("parent-base")
    parent: Doc = {
        "schema": "root.ck3.final-sdk-freeze/v1", "machine_id": main.MACHINE,
        "status": "FINAL_SOURCE_FROZEN", "runtime_admitted": False,
        "business_source_commit": main.SOURCE30_COMMIT, "files": before,
        "source_file_count": 1465, "source_bytes": 1465,
    }
    base: Doc = {
        "schema": "root.ck3.final-sdk-freeze/v1", "machine_id": main.MACHINE,
        "status": "FINAL_SOURCE_FROZEN", "runtime_admitted": False,
        "files": after, "source_file_count": 1466, "business_source_commit": "c" * 40,
        "source31_canonical_anchor": exact_ref("source31-anchor"),
    }
    anchor: Doc = {
        "schema": "xar.source31.canonical-git-anchor/v1", "machine_id": main.MACHINE,
        "status": "CANONICAL_REF_CREATED_NOT_DEPLOYED", "parent": main.SOURCE30_COMMIT,
        "actual_Source30_anchor": parent_anchor, "actual_Source30_BASE": parent_base,
        "commit": "c" * 40, "output_pins": [current[name] for name in SDK],
        "canonical_patch_rows": canonical, "public_source_commit": "d" * 40,
        "public_inputs": public, "source_file_count": 1466, "source_bytes": 1472,
        "complete_rows_JSON": {"bytes": len(packed),
                               "sha256": hashlib.sha256(packed).hexdigest()},
    }
    return {"base": base, "anchor": anchor, "parent": parent,
            "parent_anchor_ref": parent_anchor, "parent_base_ref": parent_base}


def validate_metadata(fixture: MetadataFixture) -> Doc:
    return main.source31_metadata_v1(
        fixture["base"], fixture["anchor"], fixture["parent"],
        fixture["parent_anchor_ref"], fixture["parent_base_ref"],
        machine_id=main.MACHINE)


def native_basis_node() -> ast.Expr:
    text = inspect.getsource(owner.validate_source31_owner_basis_v1)
    matches = [node for node in ast.walk(ast.parse(text))
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name) and node.value.func.id == "need"
        and len(node.value.args) == 2 and isinstance(node.value.args[1], ast.Constant)
        and node.value.args[1].value == "Source31 Native32 observer basis"]
    if len(matches) != 1:
        raise AssertionError("actual owner Native32 consumer seam changed")
    return matches[0]


def native_basis(binding: Doc) -> None:
    # Execute only the installed schema/refs guard; never the DLL qualifier.
    scope: Doc = {"binding": binding, "MACHINE": owner.MACHINE,
                  "base_ref": exact_ref("source31-base"),
                  "anchor_ref": exact_ref("source31-anchor"),
                  "need": owner.need, "parse_ref": owner.parse_ref}
    exec(compile(ast.Module(body=[native_basis_node()], type_ignores=[]),
                 "<actual A18 Native32 owner consumer>", "exec"), scope)


class PlanTests(unittest.TestCase):
    def test_real_encoder_parser_roundtrip_and_exact_fields(self) -> None:
        value = plan_input()
        original = deepcopy(value)
        parsed = main.parse_plan(json.loads(main.enc(value)))
        self.assertEqual(set(parsed), set(main.PlanV1.__annotations__))
        self.assertEqual(dict(parsed), value)
        self.assertEqual(value, original)

    def test_plan_missing_null_wrong_fields_and_release_types(self) -> None:
        for key in plan_input():
            for missing in (False, True):
                value = plan_input()
                if missing:
                    del value[key]
                else:
                    value[key] = None
                with self.subTest(field=key, missing=missing), self.assertRaises(ValueError):
                    main.parse_plan(value)
        for wrong in (False, 1, 1.0, Number.ONE):
            value = plan_input()
            value["root_direct_execution_release"] = wrong
            with self.subTest(release=wrong), self.assertRaises(ValueError):
                main.parse_plan(value)
        for key in ("task_sequence", "at_utc", "unknown"):
            value = plan_input()
            value[key] = 1
            with self.assertRaises(ValueError):
                main.parse_plan(value)

    def test_plan_refs_nonce_timezone_and_screen_drift(self) -> None:
        bad: object
        for name in PLAN_REFS:
            for bad in (True, 1.0, Number.ONE, None, 0, 2**53):
                value = plan_input()
                ref = doc(value[name])
                ref["bytes"] = bad
                value[name] = ref
                with self.subTest(ref=name, bytes=bad), self.assertRaises(ValueError):
                    main.parse_plan(value)
        for key, bad in (("task_nonce", "a" * 32), ("attempt_nonce", "G" * 32),
                         ("observed_at_utc", "2026-10-21T01:45:00"),
                         ("screen_admission_path", "."), ("schema", "Source29")):
            value = plan_input()
            value[key] = bad
            with self.subTest(field=key), self.assertRaises(ValueError):
                main.parse_plan(value)

    def test_named_history_view_changes_only_current_sequence(self) -> None:
        value: Doc = {"next_sequence": 10569, "unknown_native_request": 10565,
                      "historical": {"next_sequence": 10569}, "saved_cycles": 4753}
        original = deepcopy(value)
        result = main.history_view_v1(json.loads(main.enc(value)))
        self.assertEqual(result, {**value, "next_sequence": 10552})
        self.assertEqual(value, original)
        for bad in (10552, 10569.0, True, "10569", None, Number.ONE):
            with self.subTest(sequence=bad), self.assertRaises(ValueError):
                main.history_view_v1({"next_sequence": bad})
        with self.assertRaises(ValueError):
            main.history_view_v1({})


class RuntimeAdmissionTests(unittest.TestCase):
    def parse(self, value: object) -> main.RuntimeAdmissionV1:
        return main.parse_runtime_admission_v1(
            value, expected_machine_id="portable-model-machine")

    def test_new_core_roundtrip_and_original_receipt_not_mutated(self) -> None:
        value = admission_input()
        original = deepcopy(value)
        parsed = self.parse(json.loads(main.enc(value)))
        self.assertEqual(set(parsed), set(main.RuntimeAdmissionV1.__annotations__))
        self.assertEqual(dict(parsed), value)
        self.assertEqual(value, original)

    def test_every_required_field_missing_or_null_fails(self) -> None:
        for key in admission_input():
            for missing in (False, True):
                value = admission_input()
                if missing:
                    del value[key]
                else:
                    value[key] = None
                with self.subTest(field=key, missing=missing), self.assertRaises(ValueError):
                    self.parse(value)

    def test_capacity_safe_ids_and_review_are_exact_types(self) -> None:
        for field in ("runtime_hard_bytes", "D_free_floor_bytes", "Z_free_floor_bytes"):
            for bad in (None, True, 1.0, Number.ONE, 0, -1, 2**53, "1"):
                value = admission_input()
                if field == "runtime_hard_bytes":
                    value[field] = bad
                else:
                    capacity = doc(value["capacity"])
                    capacity[field] = bad
                    value["capacity"] = capacity
                with self.subTest(field=field, value=bad), self.assertRaises(ValueError):
                    self.parse(value)
        for field in ("root_direct_execution_release", "canonical_capacity_review_passed"):
            for bad in (False, 1, 1.0, None):
                value = admission_input()
                value[field] = bad
                with self.subTest(field=field, value=bad), self.assertRaises(ValueError):
                    self.parse(value)

    def test_foreign_machine_old_schema_and_aliases_do_not_migrate_silently(self) -> None:
        for field, bad in (("schema", "xar.Source29-A17-runtime-prepare-admission/v1"),
                           ("machine_id", "foreign"), ("owner", "other"),
                           ("status", "PREPARED"), ("hard_bytes", 3145728)):
            value = admission_input()
            value[field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.parse(value)
        for alias in ("D_conservative_floor_bytes", "Z_conservative_floor_bytes"):
            value = admission_input()
            capacity = doc(value["capacity"])
            capacity[alias] = 1
            value["capacity"] = capacity
            with self.subTest(alias=alias), self.assertRaises(ValueError):
                self.parse(value)
        for key in ("plan", "quote", "full_storage_ref"):
            value = admission_input()
            ref = doc(value[key])
            ref["path"] = "relative.json"
            value[key] = ref
            with self.subTest(ref=key), self.assertRaises(ValueError):
                self.parse(value)


class Source31MetadataTests(unittest.TestCase):
    def test_actual_metadata_consumer_accepts_writer_shape_and_roundtrip(self) -> None:
        self.assertEqual(set(SDK), main.SDK31_CHANGED)
        fixture = metadata_fixture()
        original = deepcopy(fixture)
        self.assertEqual(validate_metadata(fixture), fixture["anchor"])
        encoded = json.loads(main.enc(fixture))
        self.assertEqual(validate_metadata(encoded), fixture["anchor"])
        self.assertEqual(fixture, original)

    def test_complete_rows_numeric_aliases_and_extra_fields_are_rejected(self) -> None:
        baseline = metadata_fixture()
        size = doc(baseline["anchor"]["complete_rows_JSON"])["bytes"]
        if type(size) is not int:
            self.fail("fixture integer digest byte count")
        for bad in (float(size), True, None, str(size)):
            fixture = deepcopy(baseline)
            digest = doc(fixture["anchor"]["complete_rows_JSON"])
            digest["bytes"] = bad
            fixture["anchor"]["complete_rows_JSON"] = digest
            with self.subTest(bytes=bad), self.assertRaises((ValueError, RuntimeError)):
                validate_metadata(fixture)
        fixture = deepcopy(baseline)
        digest = doc(fixture["anchor"]["complete_rows_JSON"])
        digest["unexpected"] = None
        fixture["anchor"]["complete_rows_JSON"] = digest
        with self.assertRaises((ValueError, RuntimeError)):
            validate_metadata(fixture)

    def test_duplicate_parent_and_null_canonical_rows_do_not_get_collapsed(self) -> None:
        fixture = metadata_fixture()
        rows = main.sequence(fixture["parent"]["files"])
        rows.append(deepcopy(rows[0]))
        with self.assertRaises((ValueError, RuntimeError)):
            validate_metadata(fixture)
        fixture = metadata_fixture()
        fixture["anchor"]["canonical_patch_rows"] = [None] * 6
        with self.assertRaises((ValueError, RuntimeError)):
            validate_metadata(fixture)

    def test_sdk_and_canonical_pin_types_and_sources_are_exact(self) -> None:
        bad: object
        baseline = metadata_fixture()
        for field, bad in (("bytes", True), ("bytes", 1.0),
                           ("git_mode", 100644), ("git_blob_sha1", "bad")):
            fixture = deepcopy(baseline)
            rows = main.sequence(fixture["parent"]["files"])
            row = doc(rows[0])
            row[field] = bad
            rows[0] = row
            with self.subTest(field=field, bad=bad), self.assertRaises((ValueError, RuntimeError)):
                validate_metadata(fixture)
        for bad in (None, True, 2.0):
            fixture = deepcopy(baseline)
            patches = main.sequence(fixture["anchor"]["canonical_patch_rows"])
            row = doc(patches[0])
            pin = doc(row["output_pin"])
            pin["bytes"] = bad
            row["output_pin"] = pin
            patches[0] = row
            with self.subTest(output_bytes=bad), self.assertRaises((ValueError, RuntimeError)):
                validate_metadata(fixture)
        for field, bad in (("parent", "f" * 40), ("machine_id", "foreign"),
                           ("source_file_count", 1466.0)):
            fixture = deepcopy(baseline)
            fixture["anchor"][field] = bad
            with self.subTest(field=field), self.assertRaises((ValueError, RuntimeError)):
                validate_metadata(fixture)


class OwnerTests(unittest.TestCase):
    def test_owner_serializer_parser_roundtrip_and_recording_refs(self) -> None:
        value = owner_input()
        original = deepcopy(value)
        parsed = owner.parse_owner_inputs_v1(
            json.loads(owner.encode(value)), at_utc=NOW)
        self.assertEqual(dict(parsed), value)
        self.assertEqual(value, original)

    def test_owner_missing_null_refs_time_and_release_are_rejected(self) -> None:
        for key in owner_input():
            for missing in (False, True):
                value = owner_input()
                if missing:
                    del value[key]
                else:
                    value[key] = None
                with self.subTest(field=key, missing=missing), self.assertRaises(ValueError):
                    owner.parse_owner_inputs_v1(value, at_utc=NOW)
        for bad in (True, 1.0, Number.ONE, None, 0):
            value = owner_input()
            ref = doc(value["sdk_freeze"])
            ref["bytes"] = bad
            value["sdk_freeze"] = ref
            with self.subTest(bytes=bad), self.assertRaises(ValueError):
                owner.parse_owner_inputs_v1(value, at_utc=NOW)
        for observed in ((NOW - timedelta(seconds=601)).isoformat(),
                         (NOW + timedelta(seconds=1)).isoformat(),
                         NOW.replace(tzinfo=None).isoformat()):
            value = owner_input()
            value["observed_at_utc"] = observed
            with self.subTest(time=observed), self.assertRaises(ValueError):
                owner.parse_owner_inputs_v1(value, at_utc=NOW)
        value = owner_input()
        recording = doc(value["recording"])
        recording["task_sequence"] = 1
        value["recording"] = recording
        with self.assertRaises(ValueError):
            owner.parse_owner_inputs_v1(value, at_utc=NOW)

    def test_real_owner_native32_v2_consumer_and_old_schema_refusal(self) -> None:
        binding: Doc = {
            "schema": "xar.native32.source31-production-observer-binding/v2",
            "machine_id": owner.MACHINE,
            "status": "COLD_SOURCE_BOUND_NOT_RUNTIME_ADMITTED",
            "sdk_base_ref": exact_ref("source31-base"),
            "sdk_anchor_ref": exact_ref("source31-anchor"),
        }
        native_basis(binding)
        native_basis(doc(json.loads(owner.encode(binding))))
        for bad in ("xar.native32.production-observer-binding/v1",
                    None, True, 1.0, "future"):
            changed = deepcopy(binding)
            changed["schema"] = bad
            with self.subTest(schema=bad), self.assertRaises(ValueError):
                native_basis(changed)
        for bad in (True, 1.0):
            changed = deepcopy(binding)
            ref = doc(changed["sdk_base_ref"])
            ref["bytes"] = bad
            changed["sdk_base_ref"] = ref
            with self.assertRaises(ValueError):
                native_basis(changed)

    def test_native_decimal_identity_and_opaque_file_id_stay_distinct(self) -> None:
        identity = {"volume_serial": str(2**64 - 1), "file_id": "a" * 32}
        self.assertEqual(owner.parse_file_identity_v1(
            json.loads(owner.encode(identity))), identity)
        for bad in (True, 1.0, Number.ONE, str(2**64), "01", "0x10", None):
            value: Doc = {**identity, "volume_serial": bad}
            with self.subTest(volume=bad), self.assertRaises(ValueError):
                owner.parse_file_identity_v1(value)
        for bad in (True, 1.0, "123", "A" * 32, "g" * 32, None):
            value = {**identity, "file_id": bad}
            with self.subTest(file_id=bad), self.assertRaises(ValueError):
                owner.parse_file_identity_v1(value)

    def test_real_legacy_projection_keeps_every_nonmigration_guard(self) -> None:
        raw = (HERE / "prepare_c23_a05_union_v1.py").read_bytes()
        self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), owner.LEGACY_PIN)
        original = next(node for node in ast.parse(raw).body
            if isinstance(node, ast.FunctionDef) and node.name == "cold_owner")
        projected = owner.project_legacy_owner_v1(raw)
        compile(projected, "<real A18 owner projection>", "exec")
        function = ast.parse(projected).body[0]
        if not isinstance(function, ast.FunctionDef):
            self.fail("one projected function")
        kept: list[ast.stmt] = []
        inserted: list[str] = []
        for node in function.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) \
                    and isinstance(node.value.func, ast.Name) \
                    and node.value.func.id == "metadata_source":
                inserted.append("metadata_source")
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) \
                    and isinstance(node.value.func, ast.Name) \
                    and node.value.func.id == "metadata_scope":
                inserted.append("metadata_scope")
            else:
                kept.append(node)
        self.assertCountEqual(inserted, ["metadata_source", "metadata_scope"])
        function.body = kept
        source = ast.parse(inspect.getsource(owner.project_legacy_owner_v1))
        maps = [node.value for node in ast.walk(source) if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "replacements"
                        for target in node.targets)]
        self.assertEqual(len(maps), 1)
        value: object = eval(compile(ast.Expression(maps[0]), "<actual literal migration>", "eval"),
                             {"FREEZE_NAME": owner.FREEZE_NAME, "__builtins__": {}})
        reverse: dict[str, str] = {}
        for old, new in doc(value).items():
            if type(new) is not str:
                self.fail("literal migration text value")
            reverse[new] = old

        class Reverse(ast.NodeTransformer):
            def visit_Constant(self, node: ast.Constant) -> ast.AST:
                if type(node.value) is str and node.value in reverse:
                    return ast.copy_location(ast.Constant(reverse[node.value]), node)
                return node

        restored = Reverse().visit(function)
        self.assertEqual(ast.dump(restored, include_attributes=False),
                         ast.dump(original, include_attributes=False))
        for changed in (b"", raw[:-1], raw + b" "):
            with self.subTest(bytes=len(changed)), self.assertRaises(ValueError):
                owner.project_legacy_owner_v1(changed)


if __name__ == "__main__":
    unittest.main()

"""Portable keyed pins and versioned background source protocol regressions.

Fixtures bind real repository sources; no Steam, process, lease or game action.
Historical source identities below are metadata, never executed substitutes.
"""
from __future__ import annotations

import ast
from copy import deepcopy
from enum import IntEnum
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ck3_mod_acceptance_background_refusal as refusal
import ck3_mod_acceptance_launcher as launcher
from ck3_mod_acceptance_keeper import check_pin
from ck3_mod_acceptance_background_types import (
    CONTROL_QUEUE_MODULE_ORDER_V1, FilePin, JsonObject, file_pin, json_object,
    json_value, keyed_file_pin,
)
from ck3_mod_acceptance_launcher_protocol_v1 import (
    CURRENT_CLOSURE_SCHEMA_V1, LEGACY_CLOSURE_SCHEMA_V1,
    LAUNCHER_PROTOCOL_SHA256, build_launcher_protocol_v1,
    verify_closure_protocol_v1,
)


def real_protocol_seams(row: JsonObject) -> None:
    """Run the installed producer and reader's actual narrow protocol nodes."""
    text = Path(refusal.__file__).read_text(encoding="utf-8-sig")
    module = ast.parse(text)
    producer = next(node for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "build_bundle")
    consumer = next(node for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "_validate_supervisor_refusal_impl")
    writes = [node for node in producer.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Name) and target.value.id == "row"
            and isinstance(target.slice, ast.Constant)
            and target.slice.value == "launcher_protocol" for target in node.targets)]
    checks = [node for node in producer.body if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "verify_closure_protocol_v1"]
    reads: list[ast.stmt] = [node for node in consumer.body if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "verify_closure_protocol_v1"]
    if (len(writes), len(checks), len(reads)) != (1, 1, 1):
        raise AssertionError("installed producer/reader protocol seams changed")
    scope: dict[str, object] = {
        "row": row, "json_object": json_object,
        "build_launcher_protocol_v1": build_launcher_protocol_v1,
        "verify_closure_protocol_v1": verify_closure_protocol_v1,
    }
    exec(compile(ast.Module(body=[writes[0], checks[0]], type_ignores=[]),
                 "<actual closure producer protocol seam>", "exec"), scope)
    source_pins = [file_pin(row["launcher_source"]), file_pin(row["steam_gate_source"])]
    pin_nodes: list[ast.stmt] = [node for node in consumer.body
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name)
            and target.id in {"gate_ref", "source_ref"} for target in node.targets)]
    if len(pin_nodes) != 2:
        raise AssertionError("installed keyed consumer pin seams changed")
    scope["bundle"] = json.loads(json.dumps(row))
    scope["launcher"] = Path(source_pins[0]["path"])
    scope["keyed_file_pin"] = keyed_file_pin
    for explicit in (False, True):
        keyed_rows: JsonObject = {}
        for ref in source_pins:
            keyed_rows[ref["path"]] = json_object(ref) if explicit else {
                "bytes": ref["bytes"], "sha256": ref["sha256"]}
        scope["freeze"] = json.loads(json.dumps({"files": keyed_rows}))
        exec(compile(ast.Module(body=reads + pin_nodes, type_ignores=[]),
                     "<actual closure reader keyed protocol seams>", "exec"), scope)
        if (file_pin(scope["source_ref"]) != source_pins[0]
                or file_pin(scope["gate_ref"]) != source_pins[1]):
            raise AssertionError("actual consumer lost selected source pins")


class Number(IntEnum):
    ONE = 1


def source_pin(path: Path) -> FilePin:
    raw = path.read_bytes()
    return FilePin(path=str(path.resolve()), bytes=len(raw),
                   sha256=hashlib.sha256(raw).hexdigest())


class KeyedFilePinTests(unittest.TestCase):
    temporary: tempfile.TemporaryDirectory[str]
    root: Path
    host: Path

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="keyed-file-pin-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.host = self.root / "nonexecuted-host.py"
        self.host.write_bytes(b"# nonexecuted fixture input\n")

    def write(self, name: str, value: object) -> Path:
        path = self.root / name
        path.write_text(json.dumps(value, allow_nan=False), encoding="utf-8")
        return path

    def rows(self) -> JsonObject:
        paths = [self.host, Path(launcher.__file__).with_name(
            "ck3_mod_acceptance_runtime_inputs.py").resolve()]
        paths += [Path(launcher.__file__).with_name(name + ".py").resolve()
                  for name in CONTROL_QUEUE_MODULE_ORDER_V1]
        return {str(path): json_object(source_pin(path)) for path in paths}

    def freeze(self, rows: JsonObject) -> None:
        frozen: JsonObject = {
            "run_id": "synthetic-keyed-pins",
            "argv": ["unused", str(self.host), "--agent-source-root", "unused"],
            "files": rows,
            "launch_requires_fresh_owned_cas_and_background_offline": True,
            "previous_session_closed": True,
            "previous_screen_released": True,
            "runtime_manifest": json_object(source_pin(self.host)),
        }
        path = self.write("frozen-argv.json", frozen)
        self.write("ready-context.json", {
            "run_id": frozen["run_id"], "run_dir": str(self.root),
            "frozen_argv": source_pin(path),
        })

    def test_keyed_and_explicit_forms_roundtrip_without_mutation(self) -> None:
        full = source_pin(self.host)
        keyed: JsonObject = {"bytes": full["bytes"], "sha256": full["sha256"]}
        for value in (keyed, json_object(full)):
            before = deepcopy(value)
            decoded = keyed_file_pin(str(self.host), value)
            self.assertEqual(decoded, full)
            self.assertEqual(keyed_file_pin(str(self.host),
                json.loads(json.dumps(value))), full)
            self.assertEqual(value, before)

    def test_keys_and_rows_are_not_coerced(self) -> None:
        full = source_pin(self.host)
        keys: tuple[object, ...] = (
            None, True, 1, 1.0, self.host, "", "relative.py",
            str(self.host) + chr(0),
        )
        for key in keys:
            with self.subTest(key=repr(key)), self.assertRaises(ValueError):
                keyed_file_pin(key, full)
        row: object
        for row in (None, [], True, 1, "pin"):
            with self.subTest(row=row), self.assertRaises(ValueError):
                keyed_file_pin(str(self.host), row)

    def test_missing_wrong_extra_fields_and_numeric_aliases_are_rejected(self) -> None:
        good: dict[str, object] = dict(source_pin(self.host))
        cases: list[dict[str, object]] = []
        for key in ("bytes", "sha256"):
            row = dict(good)
            del row[key]
            cases.append(row)
        for key, values in (
            ("path", (None, True, 1, 1.0, "", "another.py", self.host)),
            ("bytes", (None, True, 1.0, Number.ONE, -1, "1")),
            ("sha256", (None, True, 1, "", "a" * 63, "G" * 64, "A" * 64)),
        ):
            for value in values:
                row = dict(good)
                row[key] = value
                cases.append(row)
        cases += [{**good, "byte_count": good["bytes"]},
                  {"path": good["path"], "byte_count": good["bytes"],
                   "sha256": good["sha256"]}]
        for row in cases:
            with self.subTest(row=repr(row)), self.assertRaises(ValueError):
                keyed_file_pin(str(self.host), row)

    def test_real_launcher_accepts_both_persisted_pin_forms(self) -> None:
        for explicit in (False, True):
            with self.subTest(explicit=explicit):
                rows = self.rows()
                if not explicit:
                    rows = {key: {field: value for field, value in
                        json_object(row).items() if field != "path"}
                        for key, row in rows.items()}
                self.freeze(json_object(json.loads(json.dumps(rows))))
                frozen, _ = launcher.frozen_run(self.root)
                self.assertEqual(frozen["run_id"], "synthetic-keyed-pins")

    def test_all_four_launcher_seams_reject_before_target_pin_or_load(self) -> None:
        helper = Path(launcher.__file__).with_name(
            "ck3_mod_acceptance_queue.py").resolve()
        runtime = Path(launcher.__file__).with_name(
            "ck3_mod_acceptance_runtime_inputs.py").resolve()
        cases = (
            ("launch-all", self.host, True, "launch"),
            ("fixed-helper", helper, False, "launch"),
            ("host", self.host, False, "launch"),
            ("running-input", runtime, True, "running"),
        )
        original_check = check_pin
        for label, target, all_pins, phase in cases:
            for wrong in ("another.py", None, True, 1.0):
                with self.subTest(seam=label, wrong=wrong):
                    rows = self.rows()
                    row = json_object(rows[str(target)])
                    row["path"] = json_value(wrong)
                    rows[str(target)] = row
                    self.freeze(rows)
                    checked: list[str] = []

                    def observe(value: object) -> None:
                        checked.append(file_pin(value)["path"])
                        original_check(value)

                    with patch.object(launcher, "check_pin", observe), \
                         patch("importlib.util.spec_from_file_location",
                               side_effect=AssertionError("no runtime dispatch")):
                        with self.assertRaises(ValueError):
                            launcher.frozen_run(self.root, all_pins=all_pins,
                                                input_phase=phase)
                    self.assertNotIn(str(target), checked)
                    self.assertIn(str(self.root / "frozen-argv.json"), checked)


class LauncherProtocolTests(unittest.TestCase):
    def pins(self) -> tuple[FilePin, FilePin, FilePin]:
        current = source_pin(Path(launcher.__file__).resolve())
        gate = source_pin(Path(launcher.__file__).with_name(
            "ck3_mod_acceptance_steam_gate.py").resolve())
        legacy = FilePin(path=current["path"], bytes=16572,
                         sha256=LAUNCHER_PROTOCOL_SHA256)
        return current, gate, legacy

    def bundle(self, schema: str, source: FilePin, gate: FilePin) -> JsonObject:
        return {"schema": schema, "launcher_source": json_object(source),
                "steam_gate_source": json_object(gate)}

    def test_new_producer_descriptor_consumes_json_roundtrip(self) -> None:
        current, gate, _ = self.pins()
        descriptor = build_launcher_protocol_v1(current, gate)
        self.assertEqual(descriptor["version"], "background-keyed-pins-v2")
        row = self.bundle(CURRENT_CLOSURE_SCHEMA_V1, current, gate)
        real_protocol_seams(row)
        self.assertEqual(row["launcher_protocol"], descriptor)
        self.assertEqual(verify_closure_protocol_v1(row), descriptor)
        self.assertEqual(verify_closure_protocol_v1(
            json.loads(json.dumps(row))), descriptor)

    def test_historical_wire_is_preserved_and_cannot_claim_new_source(self) -> None:
        current, gate, legacy = self.pins()
        row = self.bundle(LEGACY_CLOSURE_SCHEMA_V1, legacy, gate)
        self.assertEqual(verify_closure_protocol_v1(row)["version"],
                         "background-offline-v1")
        self.assertEqual(verify_closure_protocol_v1(
            json.loads(json.dumps(row)))["version"], "background-offline-v1")
        row["launcher_source"] = json_object(current)
        with self.assertRaises(ValueError):
            verify_closure_protocol_v1(row)
        row["launcher_source"] = json_object(legacy)
        row["launcher_protocol"] = None
        with self.assertRaises(ValueError):
            verify_closure_protocol_v1(row)

    def test_versioned_metadata_is_required_exact_and_nonnullable(self) -> None:
        current, gate, _ = self.pins()
        row = self.bundle(CURRENT_CLOSURE_SCHEMA_V1, current, gate)
        with self.assertRaises(ValueError):
            verify_closure_protocol_v1(row)
        descriptor = build_launcher_protocol_v1(current, gate)
        bad: tuple[object, ...] = (
            None, True, [], {}, "background-keyed-pins-v2",
            {"schema": descriptor["schema"]},
            {"schema": descriptor["schema"], "version": None},
            {"schema": descriptor["schema"], "version": "future-v3"},
            {"schema": descriptor["schema"], "version": "background-offline-v1"},
            {**descriptor, "launcherVersion": descriptor["version"]},
        )
        for value in bad:
            changed = dict(row)
            changed["launcher_protocol"] = json_value(value)
            with self.subTest(value=value), self.assertRaises(ValueError):
                verify_closure_protocol_v1(changed)

    def test_crossed_or_numeric_source_identities_are_refused(self) -> None:
        current, gate, _ = self.pins()
        row = self.bundle(CURRENT_CLOSURE_SCHEMA_V1, current, gate)
        row["launcher_protocol"] = json_object(build_launcher_protocol_v1(current, gate))
        for field in ("launcher_source", "steam_gate_source"):
            for key, bad in (("bytes", True), ("bytes", 1.0),
                             ("bytes", Number.ONE), ("sha256", "0" * 64)):
                changed = deepcopy(row)
                ref = json_object(changed[field])
                ref[key] = json_value(bad) if not isinstance(bad, Number) else bad
                changed[field] = ref
                with self.subTest(field=field, key=key, value=bad), \
                     self.assertRaises(ValueError):
                    verify_closure_protocol_v1(changed)


if __name__ == "__main__":
    unittest.main()

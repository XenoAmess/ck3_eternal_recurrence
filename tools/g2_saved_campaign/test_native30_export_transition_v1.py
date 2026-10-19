"""Synthetic receipts and private memory FS only; no Native/Git/Task calls."""
import ast
import copy
from datetime import datetime, timezone
import hashlib
import io
import json
import ntpath
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from g2_saved_campaign import native29_to30_export_contract_v1 as contract
from g2_saved_campaign import native30_export_adapter_v1 as adapter_module
from g2_saved_campaign import export_native30_immutable_sdk_views_v1 as producer

MACHINE = "synthetic-receipt-machine-not-a-runtime"
NOW = datetime(2026, 10, 20, tzinfo=timezone.utc)


def document(name, value):
    raw = (json.dumps(value, sort_keys=True) + "\n").encode()
    return contract.parse_document_v1(raw, {"path": "Z:/synthetic/" + name + ".json",
        "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})


def corpus(mutate=None):
    """All bytes below are invented test data, including purported PASS rows."""
    machine = {"machine_id": MACHINE}
    old = document("native29", {**machine, "native_build_label": "native29-synthetic",
        "native_dll_sha256": "1" * 64})
    base = document("base", {**machine, "status": "FINAL_SOURCE_FROZEN", **old.value,
        "git_head": "d" * 40, "business_source_commit": "a" * 40,
        "source_root": "Z:/base", "files": [], "source_file_count": 0, "source_bytes": 0})
    target = document("native30", {**machine, "native_build_label": contract.NATIVE30_BUILD_LABEL,
        "native_dll_sha256": "2" * 64})
    fixtures = [{"target": name, "artifact": name + ".exe"} for name in contract.FIXTURE_TARGETS]
    fixtures[-2]["args"] = ["--idle-presentation-only"]
    fixtures[-1]["args"] = ["--machine-id", "$MACHINE_ID", "--observed-at-utc", "$OBSERVED_UTC"]
    fixtures[-1]["postcheck"] = "tools/check_native_layout_report_v1.py"
    plan = document("plan", {**machine, "schema": "native30-wholeclean-plan-v1",
        "fixtures": fixtures, "dll_artifact": "bridge.dll"})
    freeze = document("freeze", {"commit": "e" * 40, "files": [
        {"path": "native/source.cpp", "bytes": 3, "sha256": "4" * 64, "git_blob": "f" * 40}]})
    delivery = document("delivery", {"DLL": {"path": "Z:/build/bridge.dll", "bytes": 1234,
        "sha256": "2" * 64}, "source_commit": "e" * 40, "source_freeze": freeze.reference, "deployed": False})
    phases = []
    for index, fixture in enumerate(fixtures):
        argv = ["Z:/build/" + fixture["artifact"]] + [arg.replace("$MACHINE_ID", MACHINE)
            .replace("$OBSERVED_UTC", "2026-10-19T09:59:59Z") for arg in fixture.get("args", [])]
        phases.append({"argv": argv, "returncode": 0,
            "owned_active_after": 0, "pid": 100 + index,
            "start_utc": "2026-10-19T10:00:00Z", "end_utc": "2026-10-19T10:00:01Z",
            "log": {"path": "Z:/logs/phase" + str(index) + ".log", "bytes": 7, "sha256": "5" * 64}})
    phases.append({**phases[-1], "argv": ["Z:/python.exe", "-B",
        "Z:/source/tools/check_native_layout_report_v1.py", phases[-1]["log"]["path"]]})
    result_value = {**machine, "schema": "native30-wholeclean-result-v1",
        "status": "BUILT_FIXTURES_PASS_NOT_DEPLOYED", "phases": phases, "Game_calls": 0,
        "DLL_loaded": False, "start_utc": "2026-10-19T09:00:00Z",
        "end_utc": "2026-10-19T11:00:00Z", "plan": plan.reference}
    if mutate is not None:
        mutate(result_value)
    result = document("result", result_value)
    image = {"sha256": "7" * 64, "bytes": 987, "version": "1.20.0.4", "architecture": "x64"}
    binding = {**machine, "schema": "xar.ck3.native-executable-binding/v1", "game_executable": image,
        "wire_contract": {"protocol_version": 1, "campaign_root_envelope_fields": list(contract.ROOT_FIELDS)},
        "native_layout_id": "ck3-1.20.0.4"}
    base_binding = document("base-binding", {**binding, "native_pin": old.reference})
    target_binding = document("target-binding", {**binding, "native_pin": target.reference,
        "source_freeze": freeze.reference})
    evidence = {"target_native_pin": target, "build_result": result, "production_delivery": delivery,
        "source_freeze": freeze, "build_plan": plan, "base_exe_binding": base_binding,
        "target_exe_binding": target_binding}
    compat = document("compat", {**machine, "schema": "xar.ck3.native29-to30-compatibility/v1",
        **{name: evidence[name].reference for name in ("base_exe_binding", "target_exe_binding",
            "build_result", "production_delivery", "source_freeze")}})
    evidence["compatibility"] = compat
    args = SimpleNamespace(machine_id=MACHINE, business_source_repo="Z:/repo",
        runtime_source_repo="Z:/host", business_source_commit="c" * 40, runtime_source_commit="d" * 40,
        base_freeze=base.path, base_freeze_sha256=base.sha256, native_pin=old.path,
        native_pin_sha256=old.sha256, capacity_card="Z:/synthetic/card.json", capacity_card_sha256="",
        source_destination="Z:/new-source", reference_destination="Z:/new-reference",
        output_root="Z:/new-output", sdk_generation="source-fixture-not-adopted")
    card = document("card", {**machine, "schema": contract.CARD_SCHEMA, "status": "ADMITTED",
        "review_at_utc": "2100-01-01T00:00:00Z", "base_freeze_sha256": base.sha256,
        "native_pin_sha256": old.sha256, "business_source_commit": args.business_source_commit,
        "runtime_source_commit": args.runtime_source_commit, "sdk_generation": args.sdk_generation,
        "base_source_root": "Z:\\base", "source_destination": "Z:\\new-source",
        "reference_destination": "Z:\\new-reference", "output_root": "Z:\\new-output",
        "approved_output_roots": ["Z:/"], "metadata_reserve_bytes": 1024**2,
        "filesystem_metadata_reserve_bytes": 65536, "new_allocation_limit_bytes": 2 * 1024**2,
        "disk_reserve_bytes": 0, "native_transition": {"schema": contract.TRANSITION_SCHEMA,
            "from_generation": 29, "to_generation": 30, "target_native_build_label": target.value["native_build_label"],
            "source_commit": "e" * 40, **{name: doc.reference for name, doc in evidence.items()}}})
    args.capacity_card_sha256 = card.sha256
    return base, old, evidence, card, args


def qualify(values, fixture=False):
    base, old, evidence, card, _args = values
    return contract.validate_native_transition_v1(base_freeze=base, base_native_pin=old,
        evidence=evidence, capacity=card, machine_id=MACHINE, source_fixture=fixture, now=NOW)


class MemoryPath:
    """Private test FS facade. No method touches a physical output path."""
    def __init__(self, fs, path):
        self.fs, self.path = fs, ntpath.normpath(str(path))
    def __str__(self): return self.path
    def __repr__(self): return "MemoryPath(" + repr(self.path) + ")"
    def __hash__(self): return hash(self.path)
    def __eq__(self, other): return isinstance(other, MemoryPath) and self.path == other.path
    def __truediv__(self, tail): return MemoryPath(self.fs, ntpath.join(self.path, str(tail)))
    def is_relative_to(self, other):
        return self.path == other.path or self.path.startswith(other.path.rstrip("\\") + "\\")
    def exists(self): return self.path in self.fs.dirs or self.path in self.fs.files
    def is_dir(self): return self.path in self.fs.dirs
    @property
    def parent(self): return MemoryPath(self.fs, ntpath.dirname(self.path))
    def mkdir(self, parents=False, exist_ok=False):
        if not exist_ok and self.exists(): raise FileExistsError(self.path)
        self.fs.dirs.add(self.path); self.fs.operations.append(("mkdir", self.path))
    def open(self, mode):
        if mode != "xb" or self.exists(): raise ValueError("memory create-only required")
        fs, path = self.fs, self.path
        class Buffer(io.BytesIO):
            def close(inner):
                fs.files[path] = inner.getvalue()
                fs.operations.append(("write", path))
                super().close()
        return Buffer()


class MemoryFS:
    def __init__(self, adapter, values):
        self.dirs = {"Z:\\", "Z:\\base"}; self.files = {}; self.operations = []; self.json = {}
        self.raw = b"synthetic SDK leaf; not a native artifact\n"
        self.blob = hashlib.sha1(b"blob " + str(len(self.raw)).encode() + b"\0" + self.raw).hexdigest()
        base, old, evidence, card, args = values
        lookup = {doc.path: doc for doc in (base, old, card)}
        ns = adapter.namespace
        ns["current_machine_id"] = lambda: MACHINE
        ns["no_reparse"] = lambda path: MemoryPath(self, path)
        ns["existing_parent"] = lambda path: MemoryPath(self, "Z:/")
        ns["ntfs_identity"] = self.identity
        ns["shutil"] = SimpleNamespace(disk_usage=lambda path: SimpleNamespace(free=100 * 1024**2))
        ns["tree"] = lambda repo, rev: {} if rev == "a" * 40 else {
            "xar_autoplayer/tiny.py": {"bytes": len(self.raw), "git_blob_sha1": self.blob, "git_mode": "100644"}}
        def git(repo, *argv):
            if argv == ("status", "--porcelain"): return b""
            if argv == ("rev-parse", "HEAD"): return b"d" * 40
            if argv[0] == "rev-parse": return argv[1].split("^")[0].encode()
            if argv[:2] == ("cat-file", "blob") and argv[2] == self.blob: return self.raw
            raise AssertionError("unexpected synthetic Git lookup: " + repr(argv))
        ns["git"] = git  # private function namespace only, no actual Git execution
        ns["read_json_pin"] = lambda path, sha: (lookup[str(path)].value, lookup[str(path)].reference)
        ns["hash_file"] = lambda path, size: (hashlib.sha256(self.files[str(path)]).hexdigest(), self.blob)
        def create_json(path, value):
            raw = (json.dumps(value, indent=2) + "\n").encode()
            with path.open("xb") as stream: stream.write(raw)
            self.json[ntpath.basename(str(path))] = copy.deepcopy(value)
            return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        ns["create_json"] = create_json
    def identity(self, path):
        name = str(path); raw = self.files.get(name, b"")
        return {"directory": name in self.dirs, "bytes": len(raw), "volume_serial": 1,
            "file_id": name, "cluster_bytes": 4096, "allocation_bytes": ((len(raw) + 4095) // 4096) * 4096}


class NativeTransitionTests(unittest.TestCase):
    def test_positive_pure_metadata_keeps_both_sources_and_fixture_is_unadmitted(self):
        values = corpus(); before = values[0].raw, values[1].raw, values[3].raw
        transition = qualify(values, fixture=True)
        self.assertTrue(transition.source_fixture)
        self.assertEqual(transition.target_native["native_build_label"], contract.NATIVE30_BUILD_LABEL)
        self.assertEqual(transition.manifest_metadata["base_native_build_label"], "native29-synthetic")
        self.assertFalse(transition.manifest_metadata["runtime_admitted"])
        self.assertEqual(before, (values[0].raw, values[1].raw, values[3].raw))
        with self.assertRaisesRegex(ValueError, "synthetic"):
            adapter_module.FrozenExporterAdapterV1().prepare(values[4], {}, transition)

    def test_FAILED_zero_fixtures_running_missing_or_bad_phase_never_qualifies(self):
        changes = [lambda r: r.update(status="FAILED", phases=[]), lambda r: r.update(status="RUNNING"),
            lambda r: r["phases"].pop(0), lambda r: r["phases"].append(copy.deepcopy(r["phases"][0])),
            lambda r: r["phases"][0].update(returncode=1),
            lambda r: r["phases"][0].update(returncode=False),
            lambda r: r["phases"][0].update(owned_active_after=1),
            lambda r: r["phases"].pop(), lambda r: r.update(DLL_loaded=True),
            lambda r: r["phases"][7]["argv"].append("--foreign"),
            lambda r: r["phases"][8]["argv"].__setitem__(2, "foreign-machine"),
            lambda r: r.update(Game_calls=False)]
        for index, mutate in enumerate(changes):
            with self.subTest(index=index), self.assertRaises(ValueError): qualify(corpus(mutate))

    def test_wrong_binding_or_admission_rejected(self):
        for field in ("base_machine", "target_machine", "target_label", "oldcard", "expired", "exe", "wire", "source", "fixture"):
            with self.subTest(field=field):
                base, old, evidence, card, args = corpus()
                if field == "base_machine":
                    base = document("base", {**base.value, "machine_id": "foreign"})
                elif field == "oldcard":
                    card = document("card", {**card.value, "native_pin_sha256": "9" * 64})
                elif field == "expired":
                    card = document("card", {**card.value, "review_at_utc": "2020-01-01T00:00:00Z"})
                else:
                    name = "target_native_pin" if field in ("target_machine", "target_label", "fixture") else "target_exe_binding"
                    value = evidence[name].value
                    if field == "target_machine": value["machine_id"] = "foreign"
                    if field == "target_label": value["native_build_label"] = "native30-placeholder"
                    if field == "fixture": value["source_fixture"] = True
                    if field == "exe": value["game_executable"]["sha256"] = "8" * 64
                    if field == "wire": value["wire_contract"]["protocol_version"] = 2
                    if field == "source": value["source_freeze"]["sha256"] = "8" * 64
                    evidence[name] = document(name, value)
                # Re-pin descendants/admission so the intended guard, not a
                # stale top-level SHA, is what refuses this test input.
                compat = evidence["compatibility"].value
                for name in ("base_exe_binding", "target_exe_binding", "build_result", "production_delivery", "source_freeze"):
                    compat[name] = evidence[name].reference
                evidence["compatibility"] = document("compat", compat)
                card_value = card.value
                if field != "oldcard": card_value["native_pin_sha256"] = old.sha256
                card_value["base_freeze_sha256"] = base.sha256
                card_value["native_transition"].update({name: doc.reference for name, doc in evidence.items()})
                card_value["native_transition"]["target_native_build_label"] = evidence["target_native_pin"].value["native_build_label"]
                card = document("card", card_value)
                expected = {"base_machine": "foreign", "target_machine": "foreign",
                    "target_label": "non-placeholder", "oldcard": "old card/native", "expired": "expired",
                    "exe": "cross-EXE/build", "wire": "wire/layout", "source": "backlink", "fixture": "synthetic"}[field]
                with self.assertRaisesRegex(ValueError, expected): qualify((base, old, evidence, card, args))

    def test_original_validator_and_complete_core_with_private_memory_facade(self):
        values = corpus(); args = values[4]
        adapter = adapter_module.FrozenExporterAdapterV1(); fs = MemoryFS(adapter, values)
        before_validate = adapter.original_validate.__code__
        context = adapter.validate_base(args)
        original_native = copy.deepcopy(context["native"])
        # Well-formed purported production envelope is still entirely synthetic
        # test input. All export IO/Git/NTFS are injected private memory facades.
        transition = qualify(values)
        ready = adapter.prepare(args, context, transition)
        self.assertEqual(fs.operations, [])
        result = adapter.export(args, ready)
        self.assertIs(before_validate, adapter.original_validate.__code__)
        self.assertEqual(context["native"], original_native)
        self.assertEqual(adapter.seam_counts, {"native": 2, "attempt": 1, "manifest": 1, "complete": 1})
        self.assertEqual(result["status"], "SOURCE_READY_NOT_LOADED")
        for name in ("SOURCE-FREEZE.json", "REFERENCE-FREEZE.json"):
            manifest = fs.json[name]
            self.assertEqual(manifest["native_build_label"], contract.NATIVE30_BUILD_LABEL)
            self.assertEqual(manifest["base_freeze"], values[0].reference)
            self.assertEqual(manifest["native_transition"]["base_native_pin"], values[1].reference)
            self.assertFalse(manifest["runtime_admitted"])
        self.assertEqual(len(fs.files), 6)  # 2 leaves + ATTEMPT + 2 manifests + COMPLETE
        with self.assertRaisesRegex(ValueError, "once-only"): adapter.export(args, ready)

    def test_original_native29_guard_is_not_replaced_by_new_target(self):
        values = corpus(); adapter = adapter_module.FrozenExporterAdapterV1(); fs = MemoryFS(adapter, values)
        native30 = values[2]["target_native_pin"]
        original_read = adapter.namespace["read_json_pin"]
        adapter.namespace["read_json_pin"] = lambda path, sha: (
            (native30.value, native30.reference) if str(path) == values[1].path else original_read(path, sha))
        with self.assertRaisesRegex(ValueError, "Host/native base binding differs"):
            adapter.validate_base(values[4])
        self.assertEqual(fs.operations, [])

    def test_root_metadata_description_crosses_pin_card_and_result_without_qualification_credit(self):
        description = "Native30 continuous hotspot tracking and idle realm overview"
        values = corpus()
        self.assertEqual(values[2]["target_native_pin"].value["native_build_label"], description)
        self.assertEqual(values[3].value["native_transition"]["target_native_build_label"], description)
        transition = qualify(values, fixture=True)
        self.assertEqual(transition.target_native["native_build_label"], description)
        self.assertTrue(transition.source_fixture)
        self.assertFalse(transition.manifest_metadata["actual_loaded_provider_issued"])
        cases = [("native30-synthetic", None, False), (description + " ", None, False),
                 ("Native30 placeholder", None, False), ("Native30 fixture", None, False),
                 (description, "different card description", False), (description, None, True)]
        for label, card_label, synthetic in cases:
            with self.subTest(label=label, card_label=card_label, synthetic=synthetic):
                base, old, evidence, card, args = corpus()
                target = evidence["target_native_pin"].value
                target.update(native_build_label=label)
                if synthetic: target["source_fixture"] = True
                evidence["target_native_pin"] = document("target", target)
                admitted = card.value
                admitted["native_transition"].update({name: doc.reference for name, doc in evidence.items()})
                admitted["native_transition"]["target_native_build_label"] = label if card_label is None else card_label
                card = document("card", admitted)
                with self.assertRaises(ValueError): qualify((base, old, evidence, card, args))

    def test_context_mutation_or_foreign_ready_rejects_before_mkdir(self):
        for kind in ("context", "args", "foreign"):
            with self.subTest(kind=kind):
                values = corpus(); adapter = adapter_module.FrozenExporterAdapterV1(); fs = MemoryFS(adapter, values)
                context = adapter.validate_base(values[4]); ready = adapter.prepare(values[4], context, qualify(values))
                if kind == "context": context["native"]["native_build_label"] = "mutated"
                if kind == "args": values[4].sdk_generation = "mutated"
                if kind == "foreign": ready.adapter = object()
                with self.assertRaises(ValueError): adapter.export(values[4], ready)
                self.assertEqual(fs.operations, [])

    def test_duplicate_json_wrong_pin_and_original_source_tamper_rejected(self):
        raw = b'{"status":"PASS","status":"FAILED"}'
        with self.assertRaisesRegex(ValueError, "duplicate"):
            contract.parse_document_v1(raw, {"path": "Z:/fake.json", "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        with self.assertRaisesRegex(ValueError, "bytes differ"):
            contract.parse_document_v1(b"{}", {"path": "Z:/fake.json", "bytes": 2, "sha256": "0" * 64})
        _path, raw = adapter_module._code_source()
        with self.assertRaisesRegex(ValueError, "exporter bytes changed"):
            adapter_module._require_frozen_bytes_v1(raw[:-1] + b"!")
        tree = ast.parse(raw); node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "export_views")
        node.body[0] = ast.parse("context = {} ").body[0]
        with self.assertRaisesRegex(ValueError, "pre-output validation"):
            adapter_module._transform_export(node)

    def test_public_entry_disabled_and_failed_qualification_precedes_adapter(self):
        self.assertEqual(producer.export_native30_views_v1(None)["status"], "DISABLED")
        # Qualification loader is reusable without enabling output creation.
        values = corpus(lambda value: value.update(status="FAILED", phases=[]))
        with self.assertRaises(ValueError): qualify(values)
        docs = {doc.path: doc for doc in (values[0], values[1], values[3], *values[2].values())}
        class InputPath:
            def __init__(self, path): self.path = str(path)
            def resolve(self, strict=False): return self
            def __str__(self): return self.path
            def stat(self): return SimpleNamespace(st_size=len(docs[self.path].raw))
        with mock.patch.object(producer, "Path", InputPath), mock.patch.object(producer,
                "_read_document", side_effect=lambda ref: docs[ref["path"]]), mock.patch.object(
                producer, "FrozenExporterAdapterV1", side_effect=AssertionError("must not instantiate before qualification")):
            with self.assertRaisesRegex(ValueError, "closed successful actual Native build"):
                producer.export_native30_views_v1(values[4], execute=True)

    def test_adapter_namespaces_are_isolated_and_original_validator_is_unchanged(self):
        first, second = adapter_module.FrozenExporterAdapterV1(), adapter_module.FrozenExporterAdapterV1()
        self.assertIsNot(first.namespace, second.namespace)
        self.assertIsNot(first.original_validate, second.original_validate)
        self.assertEqual(first.original_validate.__code__.co_code, second.original_validate.__code__.co_code)
        actual = second.namespace["git"]
        first.namespace["git"] = lambda *args: (_ for _ in ()).throw(AssertionError("first private test only"))
        self.assertIs(second.namespace["git"], actual)
        self.assertIs(second.namespace["validate_inputs"], second.original_validate)
        _path, raw = adapter_module._code_source()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), adapter_module.OLD_SHA256)


if __name__ == "__main__":
    unittest.main()

"""Portable regression of the real A14 producer and Source28 proof consumer."""
from __future__ import annotations

import ast
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import IntEnum
import hashlib
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
from types import FunctionType, ModuleType
from typing import ClassVar, Literal, Protocol, TypedDict, cast
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
PRODUCER = ROOT / "tools/g2_saved_campaign/prepare_source28_a14_rich_native31_union_v1.py"
CONSUMER = ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/succession_transition_contract.py"


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("string keys required")
        result[key] = item
    return result


def _roundtrip(value: object) -> dict[str, object]:
    decoded: object = json.loads(json.dumps(value))
    return _object(decoded)


def _select(path: Path, names: set[str]) -> dict[str, object]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    selected: list[ast.stmt] = []
    found: set[str] = set()
    for node in tree.body:
        name = node.name if isinstance(node, (ast.FunctionDef, ast.ClassDef)) else None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            name = target.id if isinstance(target, ast.Name) else None
        if name in names:
            selected.append(node)
            found.add(name)
    if found != names:
        raise AssertionError(f"real source symbols missing: {names - found}")
    scope: dict[str, object] = {
        "ast": ast, "hashlib": hashlib, "json": json, "Mapping": Mapping,
        "Literal": Literal, "TypedDict": TypedDict, "Callable": Callable,
        "Protocol": Protocol, "ModuleType": ModuleType, "cast": cast,
        "Doc": dict[str, object], "Path": Path,
    }
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), scope)
    return scope


def _function(scope: dict[str, object], name: str) -> FunctionType:
    value = scope[name]
    if not isinstance(value, FunctionType):
        raise AssertionError(f"actual Python function required: {name}")
    return value


@dataclass(frozen=True)
class _Stat:
    st_size: int


class _MemoryPath:
    files: ClassVar[dict[str, bytes]] = {}
    reads: ClassVar[list[str]] = []

    def __init__(self, value: str | _MemoryPath) -> None:
        self.key = str(PurePosixPath(str(value)))

    def __str__(self) -> str:
        return self.key

    @property
    def name(self) -> str:
        return PurePosixPath(self.key).name

    @property
    def parent(self) -> _MemoryPath:
        return _MemoryPath(str(PurePosixPath(self.key).parent))

    def with_name(self, name: str) -> _MemoryPath:
        return _MemoryPath(str(PurePosixPath(self.key).with_name(name)))

    def __truediv__(self, child: str) -> _MemoryPath:
        return _MemoryPath(str(PurePosixPath(self.key) / child))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _MemoryPath) and self.key == other.key

    def resolve(self, strict: bool = False) -> _MemoryPath:
        if strict and self.key not in self.files:
            raise FileNotFoundError(self.key)
        return self

    def is_absolute(self) -> bool:
        return PurePosixPath(self.key).is_absolute()

    def is_relative_to(self, parent: _MemoryPath) -> bool:
        return PurePosixPath(self.key).is_relative_to(PurePosixPath(parent.key))

    def is_file(self) -> bool:
        return self.key in self.files

    def stat(self) -> _Stat:
        return _Stat(len(self.files[self.key]))

    def read_bytes(self) -> bytes:
        self.reads.append(self.key)
        return self.files[self.key]

    def open(self, mode: str) -> BytesIO:
        if mode != "rb":
            raise AssertionError("read-only memory fixture")
        return BytesIO(self.read_bytes())


class _EnumInt(IntEnum):
    ONE = 1


class ModAbsenceBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = _select(PRODUCER, {
            "_one", "MOD_CLEAN_LEGACY14", "MOD_CLEAN_RUNTIME14",
            "patch_mod_absence_binding_v1", "ModAbsenceIdentityV1",
            "build_mod_absence_identity_v1",
        })
        legacy = self.api["MOD_CLEAN_LEGACY14"]
        if not isinstance(legacy, str):
            raise AssertionError("actual legacy literal required")
        self.legacy = legacy.encode()
        # These casts follow symbol selection and the actual FunctionDef check;
        # source functions remain the implementation under test.
        self.transform = cast(Callable[[bytes], bytes],
                              _function(self.api, "patch_mod_absence_binding_v1"))
        self.identity = cast(Callable[[Mapping[str, object]], object],
                             _function(self.api, "build_mod_absence_identity_v1"))
        consumer = _select(CONSUMER, {"verify_xar_mod_absence_evidence_v1"})
        self.verify = cast(Callable[[object], bool],
                           _function(consumer, "verify_xar_mod_absence_evidence_v1"))
        launch: dict[str, object] = {"pid": 4242, "creation_filetime": 2**60 + 7}
        self.launch: object = launch
        mods = b'{"enabled_mods":[]}'
        _MemoryPath.files = {"/profile/dlc_load.json": mods, "/evidence/startup.log": b"reviewed"}
        _MemoryPath.reads = []
        self.manifest: dict[str, object] = {
            "profile_dir": "/profile", "environment_sha256": "a" * 64,
            "load_profile": {"enabled_mods": [], "dlc_load_sha256": hashlib.sha256(mods).hexdigest()},
        }
        self.proof = {
            **_object(self.identity(launch)),
            "status": "ACTUAL_PROFILE_AND_STARTUP_LOG_VERIFIED", "reviewer": "/root",
            "enabled_mods_known": True, "loaded_mods_known": True,
            "startup_log_reviewed": True, "enabled_mods": [], "loaded_mods": [],
            "environment_sha256": "a" * 64, "profile_dir": "/profile",
            "profile_enabled_mods": self._ref("/profile/dlc_load.json"),
            "startup_log_snapshot": self._ref("/evidence/startup.log"),
            "startup_log_original_path": "/profile/logs/game.log",
        }
        self.proof_path = "/run/admitted-proof.json"
        self._write(self.proof_path, self.proof)
        self.admission: object = {"mod_absence": self._ref(self.proof_path)}
        # This obsolete basename is deliberately hostile. It must never be read.
        self.old_path = "/run/ROOT-CLEAN-CAMPAIGN-MOD-ABSENCE-ACTUAL-C23.json"
        self._write(self.old_path, {"game_creation_filetime": "wrong-old-proof"})

    def _write(self, path: str, value: object) -> None:
        _MemoryPath.files[path] = json.dumps(value).encode()

    def _ref(self, path: str) -> dict[str, object]:
        raw = _MemoryPath.files[path]
        return {"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

    def _consume(self, manifest: dict[str, object], **kwargs: object) -> object:
        self.assertEqual(kwargs, {"marker": "kept"})
        self.assertTrue(self.verify(manifest))
        return manifest

    def _bind(self) -> dict[str, object]:
        self._write("/run/ROOT-ACTUAL-GAME-LAUNCH-C23.json", self.launch)
        self._write("/run/ROOT-P37C23-COLD-RESUME-ADMISSION.json", self.admission)
        scope: dict[str, object] = {
            "Path": _MemoryPath, "N": _MemoryPath("/run"), "json": json,
            "original_bind_lifecycle": self._consume,
        }
        exec(compile(self.transform(self.legacy), "actual-A14-patched-entry", "exec"), scope)
        bind = cast(Callable[..., object], _function(scope, "bind_clean_lifecycle"))
        with patch("pathlib.Path", _MemoryPath):
            result = bind(self.manifest, marker="kept")
        return _object(result)

    def test_exact_admitted_reference_roundtrip_reaches_real_consumer(self) -> None:
        self.launch = _roundtrip(self.launch)
        self.proof = _roundtrip(self.proof)
        self._write(self.proof_path, self.proof)
        self.admission = _roundtrip({"mod_absence": self._ref(self.proof_path)})
        result = self._bind()
        proof = _object(result["verified_mod_absence"])
        self.assertIs(type(proof["game_creation_filetime"]), int)
        self.assertEqual(proof["game_creation_filetime"], 2**60 + 7)
        self.assertIn(self.proof_path, _MemoryPath.reads)
        self.assertNotIn(self.old_path, _MemoryPath.reads)

    def test_transform_rejects_wrong_duplicate_and_already_patched_source(self) -> None:
        for raw in (self.legacy.replace(b"def ", b"def changed_", 1),
                    self.legacy + b"\n" + self.legacy,
                    self.transform(self.legacy), b"x" * 1048577):
            with self.subTest(length=len(raw)), self.assertRaises(ValueError):
                self.transform(raw)

    def test_identity_exact_int_and_bounds(self) -> None:
        for key in ("pid", "creation_filetime"):
            for bad in (True, False, 1.0, "1", None, _EnumInt.ONE, 0, -1):
                with self.subTest(key=key, value=repr(bad)), self.assertRaises(ValueError):
                    self.identity({**_object(self.launch), key: bad})
            missing = _object(self.launch)
            del missing[key]
            with self.assertRaises(ValueError):
                self.identity(missing)
        for key, bad in (("pid", 2**32), ("creation_filetime", 2**64)):
            with self.assertRaises(ValueError):
                self.identity({**_object(self.launch), key: bad})

    def test_launch_json_shape_fields_and_types(self) -> None:
        good = _object(self.launch)
        bad: object
        for bad in (None, [], "launch", {}, {"process_id": 4242},
                    {"pid": 4242}, {"creation_filetime": 2**60 + 7}):
            self._write("/run/ROOT-ACTUAL-GAME-LAUNCH-C23.json", bad)
            # Bypass only the fixture writer; execute the real embedded helper.
            self.launch = bad
            with self.subTest(shape=repr(bad)), self.assertRaises(ValueError):
                self._bind()
        for key in good:
            for bad in (True, 4242.0 if key == "pid" else float(2**60), "4242"):
                self.launch = {**good, key: bad}
                with self.subTest(key=key, value=bad), self.assertRaises(ValueError):
                    self._bind()
        self.launch = good

    def test_proof_generation_types_and_consumer_contract(self) -> None:
        good = dict(self.proof)
        for key in ("game_pid", "game_creation_filetime"):
            for bad in (True, 4242.0 if key == "game_pid" else float(2**60), str(good[key]), None, 999):
                self._write(self.proof_path, {**good, key: bad})
                self.admission = {"mod_absence": self._ref(self.proof_path)}
                with self.subTest(key=key, value=bad), self.assertRaises(ValueError):
                    self._bind()
        for key in ("status", "profile_enabled_mods", "startup_log_snapshot"):
            bad_proof = dict(good)
            del bad_proof[key]
            self._write(self.proof_path, bad_proof)
            self.admission = {"mod_absence": self._ref(self.proof_path)}
            with self.subTest(missing=key), self.assertRaises(ValueError):
                self._bind()

    def test_admission_and_reference_shape_integrity(self) -> None:
        good_ref = self._ref(self.proof_path)
        bad_refs: list[object] = [None, [], "ref", {}, {**good_ref, "bytes": True},
            {**good_ref, "bytes": float(len(_MemoryPath.files[self.proof_path]))},
            {**good_ref, "path": "relative.json"}, {**good_ref, "sha256": "0" * 64},
            {**good_ref, "extra": 1}]
        for key in good_ref:
            value = dict(good_ref)
            del value[key]
            bad_refs.append(value)
        for reference in bad_refs:
            self.admission = {"mod_absence": reference}
            with self.subTest(reference=repr(reference)), self.assertRaises(ValueError):
                self._bind()

    def test_json_nonobjects_missing_and_explicit_null_stay_distinct(self) -> None:
        bad: object
        for bad in (None, [], "proof"):
            self._write(self.proof_path, bad)
            self.admission = {"mod_absence": self._ref(self.proof_path)}
            with self.subTest(proof=repr(bad)), self.assertRaises(ValueError):
                self._bind()
        for bad in (None, [], "admission", {}, {"mod_absence": None}, {"wrong_field": {}}):
            self.admission = bad
            with self.subTest(admission=repr(bad)), self.assertRaises(ValueError):
                self._bind()

    def test_real_consumer_requires_legacy_integer_identity(self) -> None:
        for key in ("game_pid", "game_creation_filetime"):
            for bad in (True, 1.0, "1", None, _EnumInt.ONE):
                manifest = {**self.manifest, "verified_mod_absence": {**self.proof, key: bad}}
                with self.subTest(key=key, value=repr(bad)), patch("pathlib.Path", _MemoryPath):
                    with self.assertRaises(ValueError):
                        self.verify(manifest)

    def _recording_case(self) -> tuple[dict[str, object], dict[str, dict[str, object]],
            Callable[[object, int], dict[str, object]], list[dict[str, object]]]:
        sid = "00000000-0000-4000-8000-000000000001"
        root = "/run/recordings/" + sid
        refs = {n: {"path": root + "/" + n + ".json"}
                for n in ("binding", "request", "job", "started", "first", "publisher")}
        game: dict[str, object] = {"pid": 1, "creation_filetime": 1}
        binding: dict[str, object] = {
            "schema": "xar.C23-actual-cold-recording-binding/v1", "machine_id": "portable",
            "status": "ACTUAL_NEW_RECORDING_READY", "Game_pid": 1,
            "Game_creation_filetime": 1, "session_id": sid, **refs,
            "first_frame_admission": refs["first"], "publisher_started": refs["publisher"]}
        request: dict[str, object] = {"worker_pid": 1, "worker_creation_filetime": 1,
            "receipt_root": root, "session_id": sid}
        job: dict[str, object] = {"pid": 1, "game_creation_filetime": 1,
            "receipt_root": root, "session_id": sid, "decision_text_publisher_receipt": refs["publisher"]}
        started: dict[str, object] = {"game_pid": 1, "game_creation_filetime": 1, "state": "recording"}
        first: dict[str, object] = {"game_pid": 1, "game_creation_filetime": 1,
            "recorder_session_id": sid, "status": "GREEN", "machine_id": "portable",
            "recording_job_root": root, "publisher_started": refs["publisher"]}
        records = dict(zip(refs, (binding, request, job, started, first, {})))
        admission: dict[str, object] = {"new_Game": game, "recording_binding": refs["binding"],
                                      "queue_source": {"path": "/run/queue.py"}}
        def checked(reference: object, limit: int) -> dict[str, object]:
            self.assertGreater(limit, 0)
            path = _object(reference)["path"]
            if not isinstance(path, str):
                raise ValueError("fixture reference")
            return records[PurePosixPath(path).stem]
        return admission, records, checked, [game, binding, request, job, started, first]

    def _recording_globals(self) -> dict[str, object]:
        def require(ok: bool, message: str) -> None:
            if not ok:
                raise ValueError(message)
        return {"Path": _MemoryPath, "MACHINE": "portable",
            "OLD_GAME": {"pid": 0, "creation_filetime": 0}, "require": require,
            "Callable": Callable, "Mapping": Mapping}

    def test_real_recording_contract_identity_matrix_and_roundtrip(self) -> None:
        scope = _select(PRODUCER, {"_one", "RECORDING_LEGACY14", "RECORDING_IDENTITY14",
                                    "patch_recording_identity_v1"})
        old, new = scope["RECORDING_LEGACY14"], scope["RECORDING_IDENTITY14"]
        if not isinstance(old, str) or not isinstance(new, str):
            raise AssertionError("actual recording source literals required")
        source = (ROOT / "tools/g2_saved_campaign/c23_source_abort_checkpoint_inputs_v1.py").read_text(encoding="utf-8-sig")
        node = next(n for n in ast.parse(source).body
                    if isinstance(n, ast.FunctionDef) and n.name == "current_recording_inputs_v1")
        self.assertEqual(old, ast.get_source_segment(source, node))
        admission, records, checked, carriers = self._recording_case()
        runtime = self._recording_globals()
        patcher = cast(Callable[[bytes], bytes], _function(scope, "patch_recording_identity_v1"))
        changed = patcher((old + "\n").encode())
        self.assertIn(new.strip(), changed.decode())
        with self.assertRaises(ValueError):
            patcher(changed)
        exec(compile(changed, "actual-A14-recording", "exec"), runtime)
        call = cast(Callable[[object, Callable[[object, int], dict[str, object]]], object],
                    _function(runtime, "current_recording_inputs_v1"))
        call(admission, checked)
        original_records = dict(records)
        for name, record in records.items():
            records[name] = _roundtrip(record)
        call(_roundtrip(admission), checked)
        # Restore shared carrier objects after testing the JSON representation.
        records.clear()
        records.update(original_records)
        for carrier, keys in zip(carriers, (("pid", "creation_filetime"),
                ("Game_pid", "Game_creation_filetime"),
                ("worker_pid", "worker_creation_filetime"), ("pid", "game_creation_filetime"),
                ("game_pid", "game_creation_filetime"), ("game_pid", "game_creation_filetime"))):
            for index, key in enumerate(keys):
                for bad in (True, 1.0, _EnumInt.ONE, None, 0, -1, 2**(32 if index == 0 else 64)):
                    carrier[key] = bad
                    before = repr((admission, records))
                    with self.subTest(field=key, value=repr(bad)), self.assertRaises(ValueError):
                        call(admission, checked)
                    self.assertEqual(before, repr((admission, records)))
                del carrier[key]
                with self.assertRaises(ValueError):
                    call(admission, checked)
                carrier["wrong_field"] = 1
                with self.assertRaises(ValueError):
                    call(admission, checked)
                del carrier["wrong_field"]
                carrier[key] = 1

    def _loader_api(self) -> dict[str, object]:
        path = ROOT / "tools/g2_saved_campaign/prepare_source28_a14_cold_union_v1.py"
        result = _select(path, {"need", "text", "one", "Dynamic",
            "patch_recording_bootstrap_loader_v1", "patch_recording_metadata_loader_v1"})
        result["Path"] = _MemoryPath
        return result

    def _assert_recording_installed(self, module: ModuleType) -> None:
        admission, records, checked, carriers = self._recording_case()
        vars(module).update(self._recording_globals())
        call = cast(Callable[[object, Callable[[object, int], dict[str, object]]], object],
                    _function(vars(module), "current_recording_inputs_v1"))
        call(admission, checked)
        for carrier, key in zip(carriers, ("pid", "Game_pid", "worker_pid", "pid", "game_pid", "game_pid")):
            carrier[key] = 1.0
            with self.subTest(loader=module.__name__, field=key), self.assertRaises(ValueError):
                call(admission, checked)
            carrier[key] = 1

    def test_actual_metadata_loader_three_arguments_target_and_same_module(self) -> None:
        api = self._loader_api()
        literal = _select(PRODUCER, {"RECORDING_LEGACY14", "RECORDING_IDENTITY14"})
        old, new = literal["RECORDING_LEGACY14"], literal["RECORDING_IDENTITY14"]
        if not isinstance(old, str) or not isinstance(new, str):
            raise AssertionError("recording literals")
        target, foreign = ModuleType("target"), ModuleType("foreign")
        exec(old, vars(target))
        exec(old, vars(foreign))
        previous = vars(foreign)["current_recording_inputs_v1"]
        calls: list[tuple[object, object, object]] = []
        path = _MemoryPath("/run/root_c23_a03_source_abort_checkpoint_inputs.py")
        def load(p: object, digest: object, name: object) -> object:
            calls.append((p, digest, name))
            if digest != "verified":
                raise ValueError("original hash rejection")
            return target if p == path else foreign
        scope: dict[str, object] = {"_load": load}
        install = cast(Callable[[dict[str, object], object, str], None],
                       _function(api, "patch_recording_metadata_loader_v1"))
        install(scope, _MemoryPath("/run"), new)
        wrapped = cast(Callable[[object, object, object], object], _function(scope, "_load"))
        self.assertIs(wrapped(path, "verified", "name"), target)
        self.assertEqual(calls[-1], (path, "verified", "name"))
        self._assert_recording_installed(target)
        self.assertIs(wrapped(_MemoryPath("/elsewhere/helper.py"), "verified", "other"), foreign)
        self.assertIs(vars(foreign)["current_recording_inputs_v1"], previous)
        with self.assertRaisesRegex(ValueError, "original hash rejection"):
            wrapped(path, "wrong", "name")

    def test_actual_bootstrap_guard_precedes_recording_overlay(self) -> None:
        api = self._loader_api()
        literal = _select(PRODUCER, {"RECORDING_LEGACY14", "RECORDING_IDENTITY14"})
        old, new = literal["RECORDING_LEGACY14"], literal["RECORDING_IDENTITY14"]
        if not isinstance(old, str) or not isinstance(new, str):
            raise AssertionError("recording literals")
        source = (ROOT / "tools/g2_saved_campaign/prepare_c23_a10_union_v1.py").read_text(encoding="utf-8-sig")
        embedded = next(n.value for n in ast.walk(ast.parse(source))
                        if isinstance(n, ast.Constant) and isinstance(n.value, str)
                        and "def _a10_helper():" in n.value)
        tree = ast.parse(embedded)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_a10_helper")
        fragment = ast.get_source_segment(embedded, node)
        if fragment is None:
            raise AssertionError("actual bootstrap fragment")
        patcher = cast(Callable[[bytes, str], bytes],
                       _function(api, "patch_recording_bootstrap_loader_v1"))
        changed = patcher(fragment.encode(), new)
        with self.assertRaises(ValueError):
            patcher((fragment + "\n" + fragment).encode(), new)
        expected = next(n.value for n in ast.walk(node)
                        if isinstance(n, ast.Constant) and isinstance(n.value, str) and len(n.value) == 64)
        raw = (old + "\n").encode().ljust(17637, b" ")
        path = "/run/root_c23_a03_source_abort_checkpoint_inputs.py"
        _MemoryPath.files[path] = raw
        env: dict[str, object] = {"Path": _MemoryPath, "__file__": "/run/bootstrap.py",
            "require": self._recording_globals()["require"], "hashlib": hashlib}
        exec(changed, env)
        loader = cast(Callable[[], object], _function(env, "_a10_helper"))
        # This synthetic source has no historical SHA authority.
        with self.assertRaises(ValueError):
            loader()
        @dataclass(frozen=True)
        class Digest:
            def hexdigest(self) -> str:
                return expected
        class FixtureHash:
            def sha256(self, value: bytes) -> Digest:
                if value != raw:
                    raise AssertionError("only the synthetic control-flow fixture")
                return Digest()
        env["hashlib"] = FixtureHash()
        result = loader()
        if not isinstance(result, ModuleType):
            raise AssertionError("actual loader module")
        self._assert_recording_installed(result)
        _MemoryPath.files[path] = raw[:-1]
        with self.assertRaises(ValueError):
            loader()


if __name__ == "__main__":
    unittest.main()

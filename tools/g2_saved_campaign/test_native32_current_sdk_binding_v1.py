"""Offline producer -> real historical validator -> current SDK reader fixtures.

The SDK objects and native endpoint below are explicit host fakes. These tests
grant no LoadedProvider, runtime, Game, performance or drain qualification.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import types
from typing import Protocol, runtime_checkable
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools.g2_saved_campaign.current_saved_basis_v1 import (
    ExactRefV1, JsonObject, json_object, json_value, need, parse_json, record,
)
from tools.g2_saved_campaign import prepare_native32_current_sdk_binding_v1 as composer

ROOT: Path
MACHINE = "synthetic-native32-current-sdk-fixture"
OLD_COMMIT = "1" * 40
NEW_COMMIT = "2" * 40
DELTA = (
    "xar_autoplayer/bridge/native_driver.py", "xar_autoplayer/bridge/mcp_server.py",
    "xar_autoplayer/bridge/route_window_clock_v1.py",
    "xar_autoplayer/successor_ui_pending_ledger_v1.py",
    "xar_autoplayer/ordinary_sway_schedule_v1.py",
    "xar_autoplayer/bridge/ordinary_sway_service_v1.py",
    "xar_autoplayer/sway_formal_consumer.py",
    "xar_autoplayer/bridge/war_stationary_sway_opportunity_v1.py",
)
NEW = frozenset((DELTA[2], DELTA[7]))


def encoded(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def ref(path: Path) -> JsonObject:
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": sha(raw)}


def exact(value: object) -> ExactRefV1:
    row = record(value)
    return ExactRefV1(str(row["path"]), int(str(row["bytes"])), str(row["sha256"]))


def pin(path: Path, *, raw: bytes = b"x", size: int | None = None,
        digest: str | None = None) -> JsonObject:
    return {"path": str(path), "bytes": len(raw) if size is None else size,
            "sha256": sha(raw) if digest is None else digest,
            "device": "1", "file_id": "2", "mtime_ns": "3"}


def row(name: str, raw: bytes) -> JsonObject:
    return {"relative": name, "bytes": len(raw), "sha256": sha(raw),
            "git_blob_sha1": hashlib.sha1(raw).hexdigest(), "git_mode": "100644"}


@runtime_checkable
class RuntimeApiV1(Protocol):
    def qualify_native32_binding_v1(self, value: object, *, machine_id: str) -> object: ...
    def _qualify_native32_historical_binding_v2(self, value: object, *, machine_id: str) -> object: ...
    def read_native32_once_v1(self, owner: object, driver: object, *,
        binding_value: object, machine_id: str, request_id: str,
        selection: object, timeout_seconds: float = 2.0) -> dict[str, object]: ...
    def AllNativeObservedHistoryV1(self) -> object: ...


@runtime_checkable
class ExtensionApiV1(Protocol):
    def validate_native32_mcp_result_v1(self, value: object, *, actual_game: object,
        binding_value: object, machine_id: str) -> dict[str, object]: ...


@dataclass
class HostState:
    generation: int = 1
    birth: str = "134370291327133940"

    def diagnostics(self) -> dict[str, object]:
        return {"connected": True, "connection_generation": self.generation,
                "hello": {"pid": 42, "connection_generation": self.generation}}

    def wait_for_command_result(self, request_id: str, timeout: float) -> dict[str, object]:
        return {"type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True, "result": {
            "step": "observe-time-command-journal-v1", "accepted": True,
            "status": "passive_observation_only", "drain_fence": False,
            "observer_schema": "xar.ck3.time-command-observer32/v1",
            "lifetime_coverage": "observed_clone_and_primary_delete_slots_only",
            "scalar_samples_are_snapshots": False, "query_is_tail": True,
            "retirement_diagnostics": "bounded_recent_addresses_only",
            "payload_samples": "entry_observation_not_return_readback",
            "qpc_frequency": "10000000", "snapshot_qpc": "100",
            "process_id": 42, "process_birth": self.birth, "image_base": "4096",
            "attached": 1, "readable": 1, "newest": "0", "oldest_retained": "1",
            "returned_count": 0, "first_returned": "1", "coverage_gaps": 0,
            "lost": "0", "live_registry": 0, "events": []}}


@dataclass
class HostEndpoint:
    pipe_name: str
    sent: list[dict[str, object]]

    def send(self, packet: dict[str, object]) -> None:
        self.sent.append(packet)


@dataclass
class HostDriver:
    state: HostState
    endpoint: HostEndpoint
    pipe_name: str
    _player_heir_candidate_owner_v1: object = None


@dataclass
class HostOwner:
    driver: HostDriver
    machine: str
    epoch: str = "fixture-epoch"
    _player_heir_loaded_provider_v1: object = None
    _player_heir_loaded_custody_v1: object = None


class FixtureObject:
    pass


class FixtureProvider(FixtureObject):
    pass


class FixtureCustody(FixtureObject):
    pass


class FixtureOrigin(FixtureObject):
    pass


N37_EXTERNAL_GUARD_SOURCE = "def _check_c23_external_imports(root, policy):\n    pins=policy.get('entry_source_pins')\n    require(isinstance(pins,(list,tuple)) and 0<len(pins)<=64, 'bounded complete source closure required')\n    paths=[]\n    for row in pins:\n        require(isinstance(row,(list,tuple)) and len(row)==2 and isinstance(row[0],str)\n            and Path(row[0]).is_absolute() and isinstance(row[1],str) and len(row[1])==64,\n            'exact complete source path/SHA required')\n        path=Path(row[0]).resolve(strict=True);paths.append(str(path))\n        with path.open('rb') as stream:raw=stream.read(1048577)\n        require(len(raw)<=1048576 and hashlib.sha256(raw).hexdigest()==row[1], 'complete source closure changed')\n    require(len(paths)==len(set(paths)), 'duplicate complete source path')\n    refs=policy.get('external_import_source_pins')\n    require(isinstance(refs,dict) and set(refs)==set(_C23_EXTERNAL_IMPORT_PINS), 'all frozen external algorithms must be explicitly pinned')\n    entries={str(Path(p).resolve(strict=True)):h for p,h in policy['entry_source_pins']}\n    for name,(size,digest) in _C23_EXTERNAL_IMPORT_PINS.items():\n        ref=refs[name];path=(root/(name+'.py')).resolve(strict=True)\n        require(Path(ref['path']).resolve(strict=True)==path and ref.get('bytes')==size\n            and ref.get('sha256')==digest and entries.get(str(path))==digest, 'external import pin differs: '+name)\n        with path.open('rb') as stream:raw=stream.read(1048577)\n        require(len(raw)==size and hashlib.sha256(raw).hexdigest()==digest, 'external algorithm changed: '+name)\n        module=sys.modules.get(name)\n        require(module is None or Path(module.__file__).resolve(strict=True)==path, 'foreign cached external algorithm: '+name)"
N37_EXTERNAL_GUARD_SHA256 = '8129e1cb5e5ef8f55907f3056570bda1da706872a0e6a964b8214a67e33c13c9'

ROOT_ENV = "XAR_NATIVE32_CURRENT_SDK_FIXTURE_ROOT"


def configured_fixture_root_v1() -> Path:
    value = os.environ.get(ROOT_ENV)
    if value is None:
        raise ValueError("explicit budgeted fixture root required: " + ROOT_ENV)
    root = Path(value)
    if not root.is_absolute() or root == Path(root.anchor):
        raise ValueError("absolute dedicated fixture root required")
    return root


@dataclass(frozen=True, slots=True)
class Native32CurrentSdkConsumerFixtureV1:
    entry_bytes: bytes
    queue_bytes: bytes
    outer_bytes: bytes
    bundle: composer.Native32CurrentSdkBundleV1
    external_payloads: dict[str, bytes]


def portable_consumer_fixture_v1(
    bundle: composer.Native32CurrentSdkBundleV1 | None = None,
) -> Native32CurrentSdkConsumerFixtureV1:
    """RAM source fixtures; this builder never creates a directory or provider."""
    if bundle is None:
        frozen = REPO / "tools/g2_saved_campaign/candidates/native32_runtime_journal_adapter_20261021"
        placeholder = ExactRefV1(str(REPO / "fixture-reference-never-written.json"), 1, "0" * 64)
        bundle = composer.compose_native32_current_sdk_binding_v1(
            (frozen / composer.READER_NAME).read_bytes(),
            (frozen / composer.EXTENSION_NAME).read_bytes(),
            historical_binding_ref=placeholder, current_sdk_base_ref=placeholder,
            current_sdk_anchor_ref=placeholder, machine_id=MACHINE)
    payloads = {f"external_fixture_{i}.py": f"# algorithm {i}\n".encode()
                for i in range(24)}
    original_pins = {name[:-3]: (len(raw), sha(raw)) for name, raw in payloads.items()}
    original_pins["observer_journal_runtime_v1"] = composer.HISTORICAL_READER_PIN
    original_pins["native32_mcp_extension_v1"] = composer.HISTORICAL_EXTENSION_PIN
    payloads[composer.READER_NAME] = bundle.reader_bytes
    payloads[composer.EXTENSION_NAME] = bundle.extension_bytes
    entry = ("PINS = " + repr(((composer.READER_NAME, *composer.HISTORICAL_READER_PIN),
                              (composer.EXTENSION_NAME, *composer.HISTORICAL_EXTENSION_PIN))) +
             "\nvalue = _n32_native.get('native32_observer_binding')\n" +
             "binding_path = 'ROOT-NATIVE32-PRODUCTION-BINDING01.json'\n" +
             "binding_read = 'ROOT-NATIVE32-PRODUCTION-BINDING01.json'\n").encode()
    queue = b"binding_path = 'ROOT-NATIVE32-PRODUCTION-BINDING01.json'\n"
    outer = ("from pathlib import Path\nimport hashlib\nimport sys\n" +
             "_C23_EXTERNAL_IMPORT_PINS = " + repr(original_pins) + "\n" +
             N37_EXTERNAL_GUARD_SOURCE + "\n").encode()
    return Native32CurrentSdkConsumerFixtureV1(entry, queue, outer, bundle, payloads)


@runtime_checkable
class ExternalGuardModuleV1(Protocol):
    def _check_c23_external_imports(self, root: Path, policy: dict[str, object]) -> None: ...


def external_guard_module_v1(raw: bytes) -> ExternalGuardModuleV1:
    module = types.ModuleType("native32_current_sdk_external_guard_fixture")
    module.__dict__["require"] = need
    exec(compile(raw, "<actual N37 external guard>", "exec"), module.__dict__)
    if not isinstance(module, ExternalGuardModuleV1):
        raise RuntimeError("actual external consumer required")
    return module


class CurrentSdkBindingTests(unittest.TestCase):
    root_identity: tuple[int, int]
    previous_modules: dict[str, types.ModuleType | None]
    api: RuntimeApiV1
    bundle: composer.Native32CurrentSdkBundleV1
    binding: JsonObject
    base: JsonObject
    anchor: JsonObject
    historical: JsonObject
    historical_pin: JsonObject

    @classmethod
    def write(cls, relative: str, raw: bytes) -> Path:
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return path

    @classmethod
    def document(cls, relative: str, value: object) -> JsonObject:
        return ref(cls.write(relative, encoded(value)))

    @classmethod
    def setUpClass(cls) -> None:
        global ROOT
        ROOT = configured_fixture_root_v1()
        if ROOT.exists():
            raise RuntimeError("exclusive fixture root must initially be absent")
        ROOT.mkdir()
        stat = ROOT.stat()
        cls.root_identity = stat.st_dev, stat.st_ino
        cls.previous_modules = {}
        try:
            cls.prepare()
        except BaseException:
            cls.tearDownClass()
            raise

    @classmethod
    def prepare(cls) -> None:
        old_root = ROOT / "source31"
        current_root = ROOT / "source32"
        old_root.mkdir()
        current_root.mkdir()
        unchanged = [row(f"xar_autoplayer/fixture_{i}.py", b"# same\n")
                     for i in range(1460)]
        old_rows = unchanged + [row(name, b"# parent\n") for name in DELTA if name not in NEW]
        new_rows = unchanged + [row(name, b"# current\n") for name in DELTA]
        for name in DELTA:
            cls.write("source32/" + name, b"# current\n")
        old_anchor_ref = cls.document("source31-anchor.json", {
            "schema": "xar.source31.canonical-git-anchor/v1",
            "status": "CANONICAL_REF_CREATED_NOT_DEPLOYED", "machine_id": MACHINE,
            "commit": OLD_COMMIT})
        old_base_ref = cls.document("source31-base.json", {
            "schema": "root.ck3.final-sdk-freeze/v1", "status": "FINAL_SOURCE_FROZEN",
            "machine_id": MACHINE, "runtime_admitted": False, "source_file_count": 1466,
            "source_root": str(old_root), "business_source_commit": OLD_COMMIT,
            "source31_canonical_anchor": old_anchor_ref, "files": old_rows})
        cls.anchor = {
            "schema": "xar.source32.canonical-git-anchor/v1",
            "status": "CANONICAL_REF_CREATED_NOT_DEPLOYED", "machine_id": MACHINE,
            "parent": OLD_COMMIT, "commit": NEW_COMMIT, "source_epoch_count": 43,
            "source_file_count": 1468, "source_bytes": sum(int(str(v["bytes"])) for v in new_rows),
            "output_pins": [v for v in new_rows if v["relative"] in DELTA],
            "canonical_patch_rows": [{
                "relative": "ck3_autonomous_player/src/" + name,
                "before_pin": None if name in NEW else {"bytes": 9, "sha256": sha(b"# parent\n")},
                "output_pin": {"bytes": 10, "sha256": sha(b"# current\n")},
                "public_input": None, "public_source_commit": "3" * 40}
                for name in DELTA]}
        anchor_ref = cls.document("source32-anchor.json", cls.anchor)
        cls.base = {
            "schema": "root.ck3.final-sdk-freeze/v1", "status": "FINAL_SOURCE_FROZEN",
            "machine_id": MACHINE, "runtime_admitted": False, "source_file_count": 1468,
            "source_bytes": cls.anchor["source_bytes"], "source_root": str(current_root),
            "business_source_commit": NEW_COMMIT, "source32_canonical_anchor": anchor_ref,
            "files": json_value(new_rows)}
        base_ref = cls.document("source32-base.json", cls.base)
        source_inputs: JsonObject = {
            "header": pin(ROOT / "header.hpp", size=4669,
                digest="e5534112bd49e9242f6d4ff6cbee7fcbbab38bb3628d006ffcd726c9baa6bf62"),
            "core": pin(ROOT / "core.cpp", size=16599,
                digest="5f8ee4ea50b3b2441978fea1e82a10792d5bcd59bd29fd39d7ff6229d57d0b5d")}
        plan_ref = cls.document("native-plan.json", {"machine_id": MACHINE,
                                                    "source_inputs": source_inputs})
        dll = cls.write("native.dll", b"synthetic DLL bytes; never loaded")
        dll_ref = ref(dll)
        output_pins = [pin(dll, raw=dll.read_bytes())] + [
            pin(ROOT / ("native." + suffix)) for suffix in ("map", "lib", "exp")]
        link_ref = cls.document("link.json", {"return_code": 0})
        names = ("XarCk3BridgeIdentity", "XarCk3BridgePrepareStartup", "XarCk3BridgeStart",
                 "XarCk3BridgeStartWithPipe", "XarCk3BridgeStop", "XarRefillCoreCarrier12004")
        production: JsonObject = {
            "schema": "xar.native32.offline-production-result/v1",
            "status": "OFFLINE_ARTIFACT_QUALIFIED_NOT_DEPLOYED", "machine_id": MACHINE,
            "original_807_overlay_preserved": True, "all_four_header_consumers_recompiled": True,
            "reused_inputs_before_after_stat_equal": True,
            "runtime_qualified": False, "drain_fence": False,
            "performance_goal_qualified": False, "old_commands_archive_member_extracted": False,
            "Game_calls": 0, "DLL_loads": 0, "deployment_changes": 0,
            "qualification_mode": "link_only_continuation_after_transient_leaf_cap",
            "original_production_attempt_failed": True,
            "partial_bytes_unreadable_after_overwrite": True, "recompiles_in_continuation": 0,
            "continuation_producer": pin(ROOT / "continuation.py"),
            "continuation_plan": pin(ROOT / "continuation.json"),
            "original_failure": pin(ROOT / "failed.json"),
            "partial_preimages": json_value(output_pins), "continuation_link_receipt":
                {**link_ref, "device": "1", "file_id": "2", "mtime_ns": "3"},
            "plan": {**plan_ref, "device": "1", "file_id": "2", "mtime_ns": "3"},
            "sources": source_inputs, "objects": [
                pin(ROOT / ("native32-" + name + ".obj"))
                for name in ("bridge", "commands", "core", "install")],
            "outputs": json_value(output_pins),
            "exports": [{"name": name, "rva": hex(i + 1),
                         "executable": i != 5, "forwarded": False}
                        for i, name in enumerate(names)],
            "core_link_proof": [{"function": name, "symbol": name, "bytes": 1,
                "normalized_sha256": "4" * 64, "linked_rva": "1",
                "verified_target_relocations": 1, "all_nonrelocation_bytes_equal": True}
                for name in ("ForwardExecute", "ForwardAppend", "Enter", "DiagnosticFrame")]}
        production_ref = cls.document("native-production.json", production)
        cls.historical = {
            "schema": "xar.native32.source31-production-observer-binding/v2",
            "machine_id": MACHINE, "status": "COLD_SOURCE_BOUND_NOT_RUNTIME_ADMITTED",
            "sdk_base_ref": old_base_ref, "sdk_anchor_ref": old_anchor_ref,
            "production_result_ref": production_ref, "production_input_manifest_ref": plan_ref,
            "dll": dll_ref, "sealed_parser_source": {"path": str(ROOT / "parser.py"),
                "bytes": 15948, "sha256":
                "97e1495f857f2562dc90dcbfea351362f6be9363372f1bc3ecd65e11ef22d6d6"}}
        cls.historical_pin = cls.document("historical-binding.json", cls.historical)
        frozen = REPO / "tools/g2_saved_campaign/candidates/native32_runtime_journal_adapter_20261021"
        cls.bundle = composer.compose_native32_current_sdk_binding_v1(
            (frozen / composer.READER_NAME).read_bytes(),
            (frozen / composer.EXTENSION_NAME).read_bytes(),
            historical_binding_ref=exact(cls.historical_pin),
            current_sdk_base_ref=exact(base_ref), current_sdk_anchor_ref=exact(anchor_ref),
            machine_id=MACHINE)
        cls.binding = json_object(parse_json(cls.bundle.current_binding_bytes))
        path = cls.write(composer.READER_NAME, cls.bundle.reader_bytes)
        spec = importlib.util.spec_from_file_location("native32_current_sdk_fixture_reader", path)
        if spec is None or spec.loader is None:
            raise RuntimeError("fixture loader")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        if not isinstance(module, RuntimeApiV1):
            raise RuntimeError("typed emitted runtime API")
        cls.api = module
        cls.install_sdk_modules()
        cls.assert_bounds()

    @classmethod
    def install_sdk_modules(cls) -> None:
        root = ROOT / "source32"
        names = ("xar_autoplayer", "xar_autoplayer.bridge",
                 "xar_autoplayer.bridge.player_heir_candidate_component_v1",
                 "xar_autoplayer.bridge.native_loaded_provider_custody_v1",
                 "xar_autoplayer.bridge.native_loaded_provider_origin_v1")
        for name in names:
            cls.previous_modules[name] = sys.modules.get(name)
            module = types.ModuleType(name)
            path = root / (name.replace(".", "/") + ".py")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"# explicit fake SDK model\n")
            module.__file__ = str(path)
            setattr(module, "__path__", [str(path.parent)])
            sys.modules[name] = module
        bridge = sys.modules["xar_autoplayer.bridge"]
        component = sys.modules[names[2]]
        custody = sys.modules[names[3]]
        origin = sys.modules[names[4]]
        setattr(sys.modules["xar_autoplayer"], "bridge", bridge)
        setattr(bridge, "player_heir_candidate_component_v1", component)
        setattr(component, "_LoadedNativeProviderV1", FixtureProvider)
        setattr(component, "_LOADED_NATIVE_SEAL", object())
        setattr(custody, "_PreloadCustodyV1", FixtureCustody)
        setattr(custody, "_RESOURCE_SEAL", object())
        setattr(origin, "_OriginSessionV1", FixtureOrigin)

    @classmethod
    def assert_bounds(cls) -> None:
        files = [p for p in ROOT.rglob("*") if p.is_file()]
        physical_upper = sum(((p.stat().st_size + 4095) // 4096) * 4096 for p in files)
        if physical_upper + 131072 >= 3145728:
            raise RuntimeError("fixture soft capacity exceeded")

    @classmethod
    def tearDownClass(cls) -> None:
        for name, previous in getattr(cls, "previous_modules", {}).items():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous
        sys.modules.pop("native32_current_sdk_fixture_reader", None)
        if ROOT.exists():
            actual = ROOT.resolve(strict=True)
            if actual != ROOT.absolute() or (ROOT.stat().st_dev, ROOT.stat().st_ino) != cls.root_identity:
                raise RuntimeError("fixture root identity drift")
            if any(bool(getattr(p.lstat(), "st_file_attributes", 0) & 0x400)
                   or p.is_symlink() for p in [ROOT, *ROOT.rglob("*")]):
                raise RuntimeError("fixture reparse drift; cleanup refused")
            shutil.rmtree(ROOT)
            if ROOT.exists():
                raise RuntimeError("fixture cleanup failed")

    def binding_for(self, base: JsonObject | None = None,
                    anchor: JsonObject | None = None) -> JsonObject:
        current = copy.deepcopy(self.base if base is None else base)
        qualification = copy.deepcopy(self.anchor if anchor is None else anchor)
        anchor_ref = self.document("case-anchor.json", qualification)
        current["source32_canonical_anchor"] = anchor_ref
        base_ref = self.document("case-base.json", current)
        wire = copy.deepcopy(self.binding)
        wire["current_sdk_base_ref"] = base_ref
        wire["current_sdk_anchor_ref"] = anchor_ref
        return wire

    def host(self) -> tuple[HostOwner, HostDriver, FixtureObject]:
        driver = HostDriver(HostState(), HostEndpoint("fixture-pipe", []), "fixture-pipe")
        owner = HostOwner(driver, MACHINE)
        driver._player_heir_candidate_owner_v1 = owner
        component = sys.modules["xar_autoplayer.bridge.player_heir_candidate_component_v1"]
        custody = sys.modules["xar_autoplayer.bridge.native_loaded_provider_custody_v1"]
        origin = sys.modules["xar_autoplayer.bridge.native_loaded_provider_origin_v1"]
        provider = FixtureProvider()
        for key, value in {"seal": getattr(component, "_LOADED_NATIVE_SEAL"), "owner": owner,
            "driver": driver, "machine_id": MACHINE, "native_dll_sha256": record(self.historical["dll"])["sha256"],
            "pipe_name": driver.pipe_name, "game_pid": 42, "game_creation_filetime": 134370291327133940,
            "connection_generation": 1}.items():
            setattr(provider, key, value)
        holder = FixtureCustody()
        session = FixtureOrigin()
        for key, value in {"seal": getattr(custody, "_RESOURCE_SEAL"), "closed": False,
                           "owner": owner, "_origin_session_v1": session}.items():
            setattr(holder, key, value)
        setattr(session, "holder", holder)
        setattr(session, "epoch", owner.epoch)
        owner._player_heir_loaded_provider_v1 = provider
        owner._player_heir_loaded_custody_v1 = holder
        return owner, driver, holder

    def test_historical_v2_unchanged_and_current_root_explicit(self) -> None:
        old = self.api._qualify_native32_historical_binding_v2(self.historical, machine_id=MACHINE)
        current = self.api.qualify_native32_binding_v1(self.binding, machine_id=MACHINE)
        self.assertEqual(getattr(old, "sdk_root"), ROOT / "source31")
        self.assertEqual(getattr(current, "sdk_root"), ROOT / "source32")
        self.assertEqual(getattr(getattr(current, "historical"), "wire"), self.historical)
        self.assertEqual(json_object(parse_json(self.bundle.current_binding_bytes)), self.binding)

    def test_real_reader_same_owner_single_fake_query_and_zero_credit(self) -> None:
        owner, driver, _ = self.host()
        result = self.api.read_native32_once_v1(owner, driver, binding_value=self.binding,
            machine_id=MACHINE, request_id="fixture.query", selection=self.api.AllNativeObservedHistoryV1())
        self.assertEqual(result["status"], "positive_observations_only")
        self.assertEqual(len(driver.endpoint.sent), 1)
        self.assertEqual(driver.endpoint.sent[0]["expected_revision"], 0)
        self.assertEqual(result["actual_native_requests"], 1)
        self.assertEqual(result["credit_days"], 0)
        self.assertIs(result["drain_fence"], False)
        self.assertIs(result["current_failed_request_completion_proven"], False)

    def test_real_emitted_extension_consumes_current_binding(self) -> None:
        owner, driver, _ = self.host()
        result = self.api.read_native32_once_v1(owner, driver, binding_value=self.binding,
            machine_id=MACHINE, request_id="fixture.query", selection=self.api.AllNativeObservedHistoryV1())
        path = self.write(composer.EXTENSION_NAME, self.bundle.extension_bytes)
        previous = sys.modules.get("observer_journal_runtime_v1")
        if not isinstance(self.api, types.ModuleType):
            raise RuntimeError("actual emitted module required")
        sys.modules["observer_journal_runtime_v1"] = self.api
        try:
            spec = importlib.util.spec_from_file_location("native32_current_sdk_fixture_extension", path)
            if spec is None or spec.loader is None:
                raise RuntimeError("extension loader")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if not isinstance(module, ExtensionApiV1):
                raise RuntimeError("typed emitted extension")
            envelope: dict[str, object] = {"meta": None, "content": [], "structured_content": result,
                        "is_error": False, "result_type": "complete"}
            accepted = module.validate_native32_mcp_result_v1(envelope,
                actual_game={"machine_id": MACHINE, "pid": 42,
                             "creation_filetime": 134370291327133940},
                binding_value=self.binding, machine_id=MACHINE)
            self.assertEqual(accepted, result)
        finally:
            if previous is None:
                sys.modules.pop("observer_journal_runtime_v1", None)
            else:
                sys.modules["observer_journal_runtime_v1"] = previous

    def test_old_wire_is_not_current_binding_alias(self) -> None:
        with self.assertRaises(ValueError):
            self.api.qualify_native32_binding_v1(self.historical, machine_id=MACHINE)

    def test_wrong_fields_types_generation_parent_and_machine(self) -> None:
        for key, value in (("source_file_count", True), ("source_file_count", 1466),
                           ("runtime_admitted", True), ("machine_id", "another")):
            with self.subTest(key=key, value=value):
                base = copy.deepcopy(self.base)
                base[key] = value
                with self.assertRaises(ValueError):
                    self.api.qualify_native32_binding_v1(self.binding_for(base), machine_id=MACHINE)
        for key, value in (("parent", "9" * 40), ("source_epoch_count", 42),
                           ("source_epoch_count", True), ("schema", "old")):
            anchor = copy.deepcopy(self.anchor)
            anchor[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.api.qualify_native32_binding_v1(self.binding_for(anchor=anchor), machine_id=MACHINE)
        for key in ("historical_binding_ref", "current_sdk_base_ref", "current_sdk_anchor_ref"):
            wire = copy.deepcopy(self.binding)
            del wire[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                self.api.qualify_native32_binding_v1(wire, machine_id=MACHINE)

        wire = copy.deepcopy(self.binding)
        base = copy.deepcopy(self.base)
        embedded = record(base["source32_canonical_anchor"])
        embedded["bytes"] = float(str(embedded["bytes"]))
        base["source32_canonical_anchor"] = json_object(embedded)
        wire["current_sdk_base_ref"] = self.document("float-anchor-base.json", base)
        with self.assertRaises(ValueError):
            self.api.qualify_native32_binding_v1(wire, machine_id=MACHINE)

    def test_unknown_delta_and_new_before_pin_rejected(self) -> None:
        base = copy.deepcopy(self.base)
        items = base["files"]
        if not isinstance(items, list):
            raise RuntimeError("fixture rows")
        first = record(items[0])
        first["sha256"] = "9" * 64
        items[0] = json_object(first)
        with self.assertRaises(ValueError):
            self.api.qualify_native32_binding_v1(self.binding_for(base), machine_id=MACHINE)
        anchor = copy.deepcopy(self.anchor)
        changes = anchor["canonical_patch_rows"]
        if not isinstance(changes, list):
            raise RuntimeError("fixture changes")
        for index, item in enumerate(changes):
            patch = record(item)
            if patch["before_pin"] is None:
                patch["before_pin"] = {"bytes": 1, "sha256": "0" * 64}
                changes[index] = json_object(patch)
                break
        with self.assertRaises(ValueError):
            self.api.qualify_native32_binding_v1(self.binding_for(anchor=anchor), machine_id=MACHINE)

    def test_dll_drift_and_foreign_current_module_rejected(self) -> None:
        old = copy.deepcopy(self.historical)
        record_dll = record(old["dll"])
        record_dll["sha256"] = "9" * 64
        old["dll"] = json_object(record_dll)
        wire = copy.deepcopy(self.binding)
        wire["historical_binding_ref"] = self.document("wrong-dll-history.json", old)
        with self.assertRaises(ValueError):
            self.api.qualify_native32_binding_v1(wire, machine_id=MACHINE)
        module = sys.modules["xar_autoplayer.bridge.native_loaded_provider_origin_v1"]
        before = module.__file__
        try:
            module.__file__ = str(self.write("foreign-origin.py", b"# foreign\n"))
            with self.assertRaises(ValueError):
                self.api.qualify_native32_binding_v1(self.binding, machine_id=MACHINE)
        finally:
            module.__file__ = before

    def test_missing_revoked_holder_and_connection_drift_do_not_send(self) -> None:
        owner, driver, holder = self.host()
        setattr(holder, "closed", True)
        with self.assertRaises(ValueError):
            self.api.read_native32_once_v1(owner, driver, binding_value=self.binding,
                machine_id=MACHINE, request_id="fixture.query", selection=self.api.AllNativeObservedHistoryV1())
        self.assertFalse(driver.endpoint.sent)
        owner, driver, _ = self.host()
        owner._player_heir_loaded_custody_v1 = None
        with self.assertRaises(ValueError):
            self.api.read_native32_once_v1(owner, driver, binding_value=self.binding,
                machine_id=MACHINE, request_id="fixture.query", selection=self.api.AllNativeObservedHistoryV1())
        self.assertFalse(driver.endpoint.sent)
        owner, driver, _ = self.host()
        driver.state.generation = 2
        result = self.api.read_native32_once_v1(owner, driver, binding_value=self.binding,
            machine_id=MACHINE, request_id="fixture.query", selection=self.api.AllNativeObservedHistoryV1())
        self.assertEqual(result["actual_native_requests"], 0)
        self.assertFalse(driver.endpoint.sent)


    def test_native_frame_identity_rejection_retains_original(self) -> None:
        owner, driver, _ = self.host()
        driver.state.birth = "134370291327133941"
        result = self.api.read_native32_once_v1(owner, driver, binding_value=self.binding,
            machine_id=MACHINE, request_id="fixture.query", selection=self.api.AllNativeObservedHistoryV1())
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["actual_native_requests"], 1)
        self.assertIsInstance(result["original_parsed_frame_json"], str)
        self.assertFalse(result["current_failed_request_completion_proven"])

    def test_frozen_historical_source_drift_rejected(self) -> None:
        frozen = REPO / "tools/g2_saved_campaign/candidates/native32_runtime_journal_adapter_20261021"
        with self.assertRaises(ValueError):
            composer.compose_native32_current_sdk_binding_v1(
                (frozen / composer.READER_NAME).read_bytes() + b"\n",
                (frozen / composer.EXTENSION_NAME).read_bytes(),
                historical_binding_ref=exact(self.historical_pin),
                current_sdk_base_ref=exact(self.binding["current_sdk_base_ref"]),
                current_sdk_anchor_ref=exact(self.binding["current_sdk_anchor_ref"]), machine_id=MACHINE)


    def test_three_consumers_preserve_24_pins_and_real_external_guard(self) -> None:
        fixture = portable_consumer_fixture_v1(self.bundle)
        result = composer.patch_native32_current_sdk_consumers_v1(
            fixture.entry_bytes, fixture.queue_bytes, fixture.outer_bytes, fixture.bundle)
        self.assertIsInstance(result, composer.Native32CurrentSdkConsumersV1)
        before_scope: dict[str, object] = {"require": need}
        after_scope: dict[str, object] = {"require": need}
        exec(compile(fixture.outer_bytes, "<before canonical consumer>", "exec"), before_scope)
        exec(compile(result.outer_bytes, "<after canonical consumer>", "exec"), after_scope)
        before = record(before_scope["_C23_EXTERNAL_IMPORT_PINS"])
        after = record(after_scope["_C23_EXTERNAL_IMPORT_PINS"])
        self.assertEqual(set(before), set(after))
        names = {"observer_journal_runtime_v1", "native32_mcp_extension_v1"}
        self.assertEqual({name for name in before if before[name] != after[name]}, names)
        self.assertEqual({name: before[name] for name in before if name not in names},
                         {name: after[name] for name in after if name not in names})
        self.assertEqual(after["observer_journal_runtime_v1"], (len(self.bundle.reader_bytes), sha(self.bundle.reader_bytes)))
        self.assertEqual(after["native32_mcp_extension_v1"], (len(self.bundle.extension_bytes), sha(self.bundle.extension_bytes)))
        paths = {name: self.write("consumer-gate/" + name, raw)
                 for name, raw in fixture.external_payloads.items()}
        policy: dict[str, object] = {
            "entry_source_pins": [[str(path), sha(fixture.external_payloads[name])] for name, path in paths.items()],
            "external_import_source_pins": {name[:-3]: {
                "path": str(path), "bytes": len(fixture.external_payloads[name]),
                "sha256": sha(fixture.external_payloads[name])} for name, path in paths.items()},
        }
        guard = external_guard_module_v1(result.outer_bytes)
        guard._check_c23_external_imports(ROOT / "consumer-gate", policy)
        with self.assertRaises(ValueError):
            external_guard_module_v1(fixture.outer_bytes)._check_c23_external_imports(ROOT / "consumer-gate", policy)
        self.assertIn(b"native32_current_sdk_binding", result.entry_bytes)
        self.assertNotIn(b"native32_observer_binding", result.entry_bytes)
        self.assertEqual(result.entry_bytes.count(composer.BINDING_NAME.encode()), 2)
        self.assertEqual(result.queue_bytes.count(composer.BINDING_NAME.encode()), 1)

    def test_consumer_mismatched_or_ambiguous_source_rejected(self) -> None:
        fixture = portable_consumer_fixture_v1(self.bundle)
        wrong = fixture.outer_bytes.replace(composer.HISTORICAL_READER_PIN[1].encode(), b"9" * 64)
        for outer in (wrong, fixture.outer_bytes + b"_C23_EXTERNAL_IMPORT_PINS = {}\n",
                      fixture.outer_bytes.replace(b"external_fixture_0", b"external_fixture_1"),
                      fixture.outer_bytes.replace(b"(14,", b"(True,", 1)):
            with self.subTest(outer_sha=sha(outer)), self.assertRaises(ValueError):
                composer.patch_native32_current_sdk_consumers_v1(
                    fixture.entry_bytes, fixture.queue_bytes, outer, fixture.bundle)
        for entry, queue in ((fixture.entry_bytes + b"# " + composer.HISTORICAL_BINDING_NAME.encode(),
                              fixture.queue_bytes),
                             (fixture.entry_bytes, fixture.queue_bytes.replace(
                                 composer.HISTORICAL_BINDING_NAME.encode(), b"wrong.json"))):
            with self.assertRaises(ValueError):
                composer.patch_native32_current_sdk_consumers_v1(entry, queue, fixture.outer_bytes, fixture.bundle)

    def test_outer_utf8_surroundings_and_original_guard_bytes_unchanged(self) -> None:
        fixture = portable_consumer_fixture_v1(self.bundle)
        prefix = "# source: \\u6d4b\\u8bd5\n".encode().decode("unicode_escape").encode("utf-8")
        suffix = b"\n# trailing consumer source stays byte-identical\n"
        result = composer.patch_native32_current_sdk_consumers_v1(
            fixture.entry_bytes, fixture.queue_bytes, prefix + fixture.outer_bytes + suffix, fixture.bundle)
        self.assertTrue(result.outer_bytes.startswith(prefix))
        self.assertTrue(result.outer_bytes.endswith(suffix))
        self.assertIn(N37_EXTERNAL_GUARD_SOURCE.encode(), result.outer_bytes)
        self.assertEqual(sha(N37_EXTERNAL_GUARD_SOURCE.encode()), N37_EXTERNAL_GUARD_SHA256)


if __name__ == "__main__":
    unittest.main()

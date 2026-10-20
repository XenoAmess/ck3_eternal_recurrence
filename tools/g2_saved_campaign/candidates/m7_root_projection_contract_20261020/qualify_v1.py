"""One synthetic Service/MCP qualification; never imports a live runtime."""
from pathlib import Path
import ast
import asyncio
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import datetime, timezone
import difflib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
BASE = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/sdk-v20261019-candidate/src20")
BUDGET = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/G2-PARALLEL-SOURCE-QUALIFICATION1MiB0630-ADMITTED01.json")
ARTIFACT = BUDGET.parent / "G2-PARALLEL-QUALIFICATION0630-01/m7"
MACHINE = "xenoamess-full-tower-eb9d2c1186"
SERVICE = BASE / "xar_autoplayer/bridge/service.py"


def now():
    return datetime.now(timezone.utc).isoformat()


def pin(path):
    raw = Path(path).read_bytes()
    return {"path": str(Path(path).resolve()), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def write_new(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    if len(raw) > 32768:
        raise ValueError("small proof bound exceeded")
    with Path(path).open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def allocation(root):
    import ctypes
    from ctypes import wintypes
    function = ctypes.WinDLL("kernel32", use_last_error=True).GetCompressedFileSizeW
    function.argtypes, function.restype = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD)], wintypes.DWORD
    total = 4096
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("qualification root must contain no links")
        if path.is_dir():
            total += 4096
        else:
            high = wintypes.DWORD()
            ctypes.set_last_error(0)
            low = function(str(path), ctypes.byref(high))
            if low == 0xFFFFFFFF and ctypes.get_last_error():
                raise ctypes.WinError(ctypes.get_last_error())
            total += (high.value << 32) | low
    return total


def load_leaf(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    began = now()
    budget = json.loads(BUDGET.read_bytes())
    lane = budget["lanes"]["m7"]
    if (budget["machine_id"] != MACHINE or lane["source_hard_bytes"] != 65536
            or lane["artifact_hard_bytes"] != 196608
            or Path(lane["artifact_root"]).resolve() != ARTIFACT.resolve()
            or datetime.now(timezone.utc) >= datetime.fromisoformat(budget["review_at_utc"])):
        raise ValueError("current finite m7 budget differs or expired")
    capacity = {volume: dict(zip(("total", "used", "free"), shutil.disk_usage(volume + ":/")))
                for volume in ("D", "Z")}
    if any(capacity[v]["free"] < budget["volumes"][v]["prior_allholds_floor"] + cap
           for v, cap in (("D", 196608), ("Z", 65536))):
        raise ValueError("current free bytes below retained floor and lane cap")
    if allocation(HERE) > 49152:
        raise ValueError("insufficient reserved source room for diff/proof")
    ARTIFACT.mkdir(parents=True, exist_ok=False)
    temporary = ARTIFACT / "tmp"
    temporary.mkdir()
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    tempfile.tempdir = str(temporary)
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(BASE), str(REPO / "ck3_autonomous_player/tests/unit"), str(HERE)]
    from xar_autoplayer.ck3_live_run_identity_v1 import current_machine_id
    if current_machine_id() != MACHINE:
        raise ValueError("actual machine differs")
    import transform_service_v1 as transform
    original_source = SERVICE.read_text(encoding="utf-8")
    modified_source = transform.transform_service_v1(original_source)
    before_method, _ = transform.method_source(original_source)
    after_method, node = transform.method_source(modified_source)
    helper_name = "xar_autoplayer.bridge.player_heir_projection_service_contract_v1"
    helper = load_leaf(helper_name, HERE / "player_heir_projection_service_contract_v1.py")
    import xar_autoplayer.bridge.service as service_module
    original = service_module.GameplayBridgeService.query_campaign_root_context_v1
    namespace = dict(service_module.__dict__)
    tree = ast.parse(modified_source)
    method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == transform.METHOD)
    exec(compile(ast.Module(body=[method], type_ignores=[]), "<m7-service-candidate-RAM>", "exec"), namespace)
    corrected = namespace[transform.METHOD]
    import test_campaign_root_context_v1_bridge as fixture
    import test_player_heir_candidate_component_v1 as native_fixture
    import test_player_heir_fixed_dynasty_projection_v1 as mapper_fixture
    from xar_autoplayer.bridge.driver import BridgeUnavailableError
    from xar_autoplayer.bridge.mcp_server import create_server, _ck3_query_campaign_root_context_v1
    from xar_autoplayer.bridge.version_identity import CK3_12004
    from xar_autoplayer.player_heir_fixed_dynasty_projection_v1 import project_fixed_dynasty_candidate_v1
    from mcp import Client
    key = helper.PROJECTION

    class Driver(fixture._ServiceDriver):
        def __init__(self, mutate=None, with_projection=True, positive=True):
            super().__init__()
            self.mutate, self.with_projection, self.positive = mutate, with_projection, positive

        def take_snapshot(self):
            value = super().take_snapshot()
            value["diagnostics"]["hello"].update(game_version=CK3_12004.game_version,
                expected_ck3_version=CK3_12004.game_version, expected_ck3_sha256=CK3_12004.executable_sha256)
            return value

        def execute_step(self, step, *, expected_revision=None):
            value = super().execute_step(step, expected_revision=expected_revision)
            root = native_fixture.native_result()["campaign_root_context"]
            value["campaign_root_context"] = root
            for field in set(value) & set(root):
                value[field] = deepcopy(root[field])
            value["backend_id"] = CK3_12004.backend_id("campaign-root-context-v1")
            if self.with_projection:
                if self.positive:
                    case = mapper_fixture.fixture()
                    core = case["current_core"]
                    core = replace(core, date_raw=root["date_raw"],
                                   played_character_id=root["player_character_id"])
                    observation = replace(case["captured"].observation,
                        actor_character_id=root["player_character_id"], before=core, after=core,
                        candidate_character_id=root[helper.COMPONENT]["observation"]["candidate_character_id"])
                    binding = replace(case["current"], date_raw=core.date_raw,
                                      actor_character_id=core.played_character_id)
                    case.update(current=binding, current_core=core,
                        captured=replace(case["captured"], binding=binding, observation=observation))
                    projection = asdict(project_fixed_dynasty_candidate_v1(**case))
                    projection.update(machine_id="synthetic-service-fixture",
                        game_identity={"pid":123,"creation_date":"synthetic-exact-birth","executable":"synthetic/ck3.exe"},
                        native_provider_sha256="a"*64, owner_source_epoch="b"*64,
                        query_id="synthetic-service-query", native_query_sequence=value["query_sequence"],
                        capture_epoch_basis="original_root_query_sequence",
                        **{field:value[field] for field in ("queried_snapshot_id","queried_revision","queried_native_revision")})
                else:
                    projection = native_fixture.leaf._unknown("trusted_loaded_Native_DLL_custody_unavailable")
                value[key] = projection
            if self.mutate is not None:
                self.mutate(value)
            return value

    class Focused(unittest.IsolatedAsyncioTestCase):
        async def test_original_Service_and_registered_MCP_optional_projection(self):
            with self.assertRaisesRegex(BridgeUnavailableError, "malformed result"):
                original(service_module.GameplayBridgeService(Driver()), expected_revision=fixture.PUBLIC_REVISION)
            with patch.object(service_module.GameplayBridgeService, transform.METHOD, corrected):
                # Exercise the original facade and registered official Client;
                # only the one candidate method is replaced in memory.
                unchanged = _ck3_query_campaign_root_context_v1(
                    service_module.GameplayBridgeService(Driver(with_projection=False)), fixture.PUBLIC_REVISION)
                self.assertNotIn(key, unchanged)
                for positive in (True, False):
                    async with Client(create_server(Driver(positive=positive))) as client:
                        result = await client.call_tool("ck3_query_campaign_root_context_v1",
                            {"expected_revision":fixture.PUBLIC_REVISION})
                    self.assertFalse(result.is_error)
                    value = result.structured_content[key]
                    self.assertEqual(value["status"], "positive_witness" if positive else "unknown")
                    self.assertIsNone(value["b"])
                    self.assertEqual(value["H_interval"], [70,100] if positive else [0,100])
                changes = {
                    "boolean k": lambda v:v[key].update(k=True),
                    "backup zero": lambda v:v[key].update(b=0),
                    "point score": lambda v:v[key].update(H_interval=[100,100]),
                    "partial provider": lambda v:v[key].pop("native_provider_sha256"),
                    "stale query": lambda v:v[key].update(queried_revision=999),
                    "missing native component": lambda v:v["campaign_root_context"].pop(helper.COMPONENT),
                    "synthetic native fixture": lambda v:v["campaign_root_context"][helper.COMPONENT]["observation"].update(source_fixture=True),
                    "foreign extra key": lambda v:v.update(foreign_extra=True),
                    "old mirror drift": lambda v:v.update(top_liege_character_id=999),
                }
                for label, mutate in changes.items():
                    with self.subTest(label=label):
                        with self.assertRaises(BridgeUnavailableError):
                            _ck3_query_campaign_root_context_v1(
                                service_module.GameplayBridgeService(Driver(mutate=mutate)), fixture.PUBLIC_REVISION)

    buffer = io.StringIO()
    started = time.perf_counter()
    result = unittest.TextTestRunner(stream=buffer, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Focused))
    proof = {"schema":"xar.m7.root-projection-Service-qualification/v1", "machine_id":MACHINE,
        "observed_at_utc":now(), "started_at_utc":began,
        "status":"PASS" if result.wasSuccessful() else "FAIL",
        "tests_run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),
        "elapsed_seconds":time.perf_counter()-started,"output":buffer.getvalue(),
        "original_failure_reproduced":"campaign-root backend returned a malformed result",
        "synthetic_cases":{"registered_MCP":2,"legacy_facade":1,"malformed_rejections":9},
        "budget":pin(BUDGET),"capacity_at_start":capacity,"source_Service":pin(SERVICE),
        "method_before_sha256":hashlib.sha256(before_method.encode()).hexdigest(),
        "method_after_sha256":hashlib.sha256(after_method.encode()).hexdigest(),
        "transformed_Service_sha256":hashlib.sha256(modified_source.encode()).hexdigest(),
        "production_helper_target":transform.HELPER_TARGET,
        "boundaries":{"all_Game_Native_provider_frames":"synthetic","actual_H":"NOTRUN",
            "M7":"in_progress","G2":"6/8","runtime_adoption":False,
            "Game_Native_MCP_external_desktop_Task_actions":0,"SDK_or_SAVE_writes":0},
        "retention":{"policy_version":"1.0.0","review_at_utc":"2026-10-27T06:30:00Z",
            "reason":"Current unadopted source candidate; consolidate after Root integration."}}
    if not result.wasSuccessful():
        proof["source_allocation"] = allocation(HERE)
        proof["artifact_allocation"] = allocation(ARTIFACT)
        write_new(ARTIFACT / "QUALIFICATION-FAILED.json", proof)
        print(json.dumps(proof, ensure_ascii=False))
        return 1
    diff = "".join(difflib.unified_diff(original_source.splitlines(keepends=True),
        modified_source.splitlines(keepends=True), fromfile="a/ck3_autonomous_player/src/xar_autoplayer/bridge/service.py",
        tofile="b/ck3_autonomous_player/src/xar_autoplayer/bridge/service.py"))
    with (HERE / "service.diff").open("xb") as stream:
        stream.write(diff.encode())
    proof["source_files"] = [pin(path) for path in sorted(HERE.iterdir()) if path.is_file()]
    proof["source_allocation_before_proof"] = allocation(HERE)
    proof["artifact_allocation_before_proof"] = allocation(ARTIFACT)
    # Reserve conservative clusters for both bounded proof copies before either.
    encoded = (json.dumps(proof,ensure_ascii=False,indent=2)+"\n").encode()
    clusters = ((len(encoded)+4095)//4096)*4096
    if allocation(HERE)+clusters>65536 or allocation(ARTIFACT)+clusters>196608:
        raise ValueError("proof would exceed exact lane highwater")
    write_new(ARTIFACT / "QUALIFICATION.json", proof)
    write_new(HERE / "SOURCE-READY.json", proof)
    print(json.dumps({"status":proof["status"],"machine_id":MACHINE,"proof":pin(ARTIFACT/"QUALIFICATION.json"),
        "source_ready":pin(HERE/"SOURCE-READY.json"),"source_allocation":allocation(HERE),
        "artifact_allocation":allocation(ARTIFACT),"temporary_entries":len(list(temporary.iterdir()))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

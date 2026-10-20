"""A13 cold fullscreen2560 migration; Root alone installs returned bytes."""
from __future__ import annotations
import ast
import copy
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from types import ModuleType
from typing import Callable, Protocol, TypedDict, cast

sys.dont_write_bytecode = True
MACHINE = "xenoamess-full-tower-eb9d2c1186"
ORIGINAL = Path("Z:/ck3_mod_rewrite/tools/g2_saved_campaign/prepare_c23_a10_environment_migration_v1.py")
ORIGINAL_PIN = (16083, "02e2a010f511734426404bc201e3384a9973f16a181e41d94afeea12f42699b6")
BASE28_PIN = (411438, "0d903bb46616b91e4947ee838c64662ddcf3be14c89999bd1a5272f01c48f585")
SOURCE_ENV = "666efa22b7d909257689cc20dc7b343cc7e48f4aae6fafb053c99142b21a1202"
ORIGINAL_ENV = "dbcb5ea688435677d945cef9fc9c73c31d01d229ec060c3a951e53701bf33b57"
SEED_PIN = (9054, "c2c672d520267e6f860dd968ce2ccf1c06faca10fd1cd0552d213929b9a8dac8")
MODULES = ("bridge.driver_state_wal_v1", "bridge.native_driver",
    "checkpoint_environment_rebinder", "ordinary_seed_rebinder",
    "cold_checkpoint_validator", "bridge.succession_transition_contract", "environment")
Doc = dict[str, object]

class ExactRef(TypedDict):
    path: str
    bytes: int
    sha256: str
class SdkInputs(TypedDict):
    sdk_root: str
    sdk_base: ExactRef
    sdk_files: dict[str, ExactRef]
    source28_anchor: ExactRef
class Plan(SdkInputs):
    schema: str
    machine_id: str
    execution_owner: str
    root_direct_execution_release: bool
    observed_at_utc: str
    source27_anchor: ExactRef
    closure_index: ExactRef
    quiescence: ExactRef
    source_base: ExactRef
    source_wal: ExactRef | None
    source_identity: dict[str, list[str]]
    original_seed: ExactRef
    source_derived_seed: ExactRef
    prior_migration: ExactRef
    source_manifest: ExactRef
    source_settings: ExactRef
    target_manifest: ExactRef
    target_settings: ExactRef
    source_save_identity: list[str]
    target_driver_path: str
    target_seed_path: str
    receipt_path: str
    source_manifest_archive_path: str
    source_settings_archive_path: str
class Composer(Protocol):
    def __call__(self, plan: Plan) -> tuple[bytes, bytes, Doc, Doc]: ...
class Replay(Protocol):
    def __call__(self, base_bytes: bytes, journal_bytes: bytes | None) -> tuple[Doc, str]: ...
class Settings(Protocol):
    def __call__(self, text: str, *, display_mode: str,
                 screen_edge_scroll_mode: str | None = None) -> Doc: ...

def need(value: object, reason: str) -> None:
    if not value: raise ValueError("A13 ENV: " + reason)
def obj(value: object) -> Doc:
    if not isinstance(value, dict): raise ValueError("A13 ENV: object")
    need(all(type(k) is str for k in value), "string object keys")
    return cast(Doc, value)
def text(value: object) -> str:
    need(type(value) is str and bool(value), "nonempty text")
    return cast(str, value)
def integer(value: object) -> int:
    need(type(value) is int and value >= 0, "exact nonnegative integer")
    return cast(int, value)
def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
def encode(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
def file_ref(value: object) -> ExactRef:
    d = obj(value)
    need(set(d) == {"path", "bytes", "sha256"}, "exact ref fields")
    path, size, digest = text(d["path"]), integer(d["bytes"]), text(d["sha256"])
    need(re.fullmatch("[0-9a-f]{64}", digest) is not None, "SHA256")
    return {"path": path, "bytes": size, "sha256": digest}
def future(path: str | Path, raw: bytes) -> ExactRef:
    return {"path": str(path), "bytes": len(raw), "sha256": sha(raw)}
def identity(path: Path) -> list[str]:
    st = path.stat()
    return [str(v) for v in (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)]
def read_exact(item: ExactRef, limit: int = 65536) -> bytes:
    p = Path(item["path"]).resolve(strict=True)
    before = identity(p)
    need(integer(item["bytes"]) <= limit and int(before[2]) == item["bytes"], "bounded input")
    with p.open("rb") as stream: raw = stream.read(limit + 1)
    need(len(raw) == item["bytes"] and sha(raw) == item["sha256"] and identity(p) == before,
         "input bytes/hash/identity changed")
    return raw
def checked(item: ExactRef, limit: int = 65536) -> Doc:
    value: object = json.loads(read_exact(item, limit))
    return obj(value)
def stamp(value: str) -> datetime:
    at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    need(at.tzinfo is not None, "aware UTC")
    return at
def fresh(value: str) -> None:
    need(-10 <= (datetime.now(timezone.utc) - stamp(value)).total_seconds() <= 600, "fresh UTC")
def _original() -> tuple[ModuleType, str]:
    raw = read_exact(future(ORIGINAL, ORIGINAL.read_bytes()), 32768)
    need((len(raw), sha(raw)) == ORIGINAL_PIN, "original migration producer")
    name = "_a13_original_env_" + ORIGINAL_PIN[1]
    spec = importlib.util.spec_from_file_location(name, ORIGINAL)
    need(spec is not None and spec.loader is not None, "original loader")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(raw, str(ORIGINAL), "exec"), vars(module))
    return module, raw.decode("utf-8-sig")
def parse_plan(value: object) -> Plan:
    d = obj(value)
    need(set(d) == set(Plan.__annotations__), "exact plan fields")
    refs = ("sdk_base", "source28_anchor", "source27_anchor", "closure_index", "quiescence",
        "source_base", "original_seed", "source_derived_seed", "prior_migration",
        "source_manifest", "source_settings", "target_manifest", "target_settings")
    for key in refs: file_ref(d[key])
    if d["source_wal"] is not None: file_ref(d["source_wal"])
    for key in ("schema", "machine_id", "execution_owner", "observed_at_utc", "sdk_root",
        "target_driver_path", "target_seed_path", "receipt_path",
        "source_manifest_archive_path", "source_settings_archive_path"): text(d[key])
    need(d["root_direct_execution_release"] is True, "Root release")
    files = obj(d["sdk_files"])
    need(set(files) == set(MODULES), "seven SDK modules")
    for item in files.values(): file_ref(item)
    identities = obj(d["source_identity"])
    need(set(identities) == {"base", "wal"}, "pair identity keys")
    for value2 in [*identities.values(), d["source_save_identity"]]:
        need(type(value2) is list and len(cast(list[object], value2)) in (0, 5), "identity list")
        for token in cast(list[object], value2):
            need(type(token) is str and re.fullmatch("0|[1-9][0-9]*", token) is not None,
                 "identity canonical decimal strings")
    need(len(cast(list[object], identities["base"])) == 5
         and len(cast(list[object], d["source_save_identity"])) == 5, "base/SAVE identities")
    return cast(Plan, d)
def load_sdk(plan: SdkInputs) -> tuple[dict[str, ModuleType], dict[str, ExactRef]]:
    root = Path(plan["sdk_root"]).resolve(strict=True)
    need((plan["sdk_base"]["bytes"], plan["sdk_base"]["sha256"]) == BASE28_PIN, "actual Source28 BASE")
    base = checked(plan["sdk_base"], 524288)
    need(base.get("machine_id") == MACHINE and base.get("status") == "FINAL_SOURCE_FROZEN"
         and base.get("source_root") == str(root)
         and base.get("source28_canonical_anchor") == plan["source28_anchor"], "Source28 provenance")
    checked(plan["source28_anchor"])
    rows = {text(obj(row)["relative"]): obj(row) for row in cast(list[object], base["files"])}
    sources: dict[str, ExactRef] = {}
    for name in MODULES:
        relative = "xar_autoplayer/" + name.replace(".", "/") + ".py"
        item = file_ref(plan["sdk_files"][name]); path = root / relative
        need(Path(item["path"]).resolve(strict=True) == path.resolve(strict=True)
             and (item["bytes"], item["sha256"]) == (rows[relative]["bytes"], rows[relative]["sha256"]),
             "exact SDK module")
        read_exact(item, 4194304); sources[name] = item
    before = list(sys.path); sys.path.insert(0, str(root))
    try:
        for name, module in tuple(sys.modules.items()):
            if name == "xar_autoplayer" or name.startswith("xar_autoplayer."):
                origin = getattr(module, "__file__", None)
                need(type(origin) is str and Path(origin).resolve().is_relative_to(root), "fresh Source28 process")
        modules = {name: importlib.import_module("xar_autoplayer." + name) for name in MODULES}
        for name, module in modules.items():
            need(Path(text(module.__file__)).resolve() == Path(sources[name]["path"]).resolve()
                 and module.__spec__ is not None and module.__spec__.origin == module.__file__, "SDK origin")
    finally: sys.path[:] = before
    return modules, sources

def change_mode(data: bytes) -> bytes:
    body = data.decode("utf-8-sig")
    pattern = r'("display_mode"\s*=\s*\{[^{}]*\bvalue\s*=\s*")windowed(")'
    changed, count = re.subn(pattern, r"\1fullscreen\2", body, flags=re.DOTALL)
    need(count == 1, "one active display mode")
    prefix = b"\xef\xbb\xbf" if data.startswith(b"\xef\xbb\xbf") else b""
    need(re.sub(pattern.replace("windowed", "fullscreen"), r"\1windowed\2",
                changed, count=1, flags=re.DOTALL) == body, "only active mode changed")
    return prefix + changed.encode()

def validate_source_graphics(plan: Plan, modules: dict[str, ModuleType], prior: Doc) -> None:
    manifest = checked(plan["source_manifest"], 32768)
    load = obj(manifest["load_profile"]); display = obj(manifest["display"])
    need(display.get("mode") == "windowed" and display.get("resolution") == [1280, 720]
         and load.get("enabled_mods") == [], "source vanilla/windowed1280")
    prepared = file_ref(prior["staged_target_settings"])
    need(prepared["sha256"] == load["pdx_settings_prepared_sha256"], "source prepared settings lineage")
    read_exact(prepared)
    source = read_exact(plan["source_settings"]); target = read_exact(plan["target_settings"])
    need(target == change_mode(source), "target settings may change only active mode")
    contract = cast(Settings, modules["environment"].settings_contract)
    need(contract(source.decode("utf-8-sig"), display_mode="windowed",
         screen_edge_scroll_mode="screen_edge_scroll_mode_disabled") == load["pdx_settings_contract"],
         "actual source settings contract")

def make_graphics_target(sdk: SdkInputs, source_manifest: ExactRef, source_settings: ExactRef,
                         source_prepared_settings: ExactRef, prepared_at: str) -> tuple[bytes, bytes, Doc]:
    fresh(prepared_at); modules, _ = load_sdk(sdk)
    environment = modules["environment"]
    manifest = checked(source_manifest, 32768)
    need(manifest.get("machine_id") == MACHINE and manifest.get("environment_sha256") == SOURCE_ENV,
         "source fullscreen migration basis")
    display = obj(manifest["display"]); load = obj(manifest["load_profile"])
    need(display.get("mode") == "windowed" and display.get("resolution") == [1280, 720]
         and load.get("enabled_mods") == [], "source actual vanilla/windowed1280")
    prepared = read_exact(source_prepared_settings)
    need(sha(prepared) == load["pdx_settings_prepared_sha256"], "historical prepared settings")
    data = read_exact(source_settings); body = data.decode("utf-8-sig")
    contract = cast(Settings, environment.settings_contract)
    need(contract(body, display_mode="windowed", screen_edge_scroll_mode="screen_edge_scroll_mode_disabled")
         == load["pdx_settings_contract"], "actual source settings semantics")
    target_settings = change_mode(data)
    changed = target_settings.decode("utf-8-sig")
    target_contract = contract(changed, display_mode="fullscreen",
        screen_edge_scroll_mode="screen_edge_scroll_mode_disabled")
    target = copy.deepcopy(manifest)
    obj(target["display"]).update(mode="fullscreen", resolution=[2560, 1440])
    target_load = obj(target["load_profile"])
    target_load.update(pdx_settings_prepared_sha256=sha(target_settings),
                       pdx_settings_contract=target_contract)
    target["prepared_at"] = prepared_at
    digest = cast(Callable[[Doc], str], environment._contract_digest)
    need(digest(manifest) == SOURCE_ENV, "source contract digest")
    target["environment_sha256"] = digest(target)
    return target_settings, encode(target) + b"\n", {
        "machine_id": MACHINE, "source_settings": source_settings,
        "source_prepared_settings": source_prepared_settings,
        "target_settings_sha256": sha(target_settings), "target_environment_sha256": target["environment_sha256"],
        "source_contract": load["pdx_settings_contract"], "target_contract": target_contract,
        "only_active_mode_changed": True, "inactive_windowed_resolution_preserved": True,
        "Game_Task_RPC_calls": 0}
def validate_closed(plan: Plan) -> None:
    fresh(plan["observed_at_utc"])
    index = checked(plan["closure_index"], 32768)
    q = checked(plan["quiescence"], 32768)
    need((plan["closure_index"]["bytes"], plan["closure_index"]["sha256"]) ==
         (5088, "5ad53086563d7c2d5dfa845760dd7b20f4db7511347d9d88c1b52c8a3c547d6d")
         and index.get("schema") == "xar.A12-actual-closure-index/v1"
         and index.get("owned_job_active_final") == 0 and index.get("SDK_status") == "SDK_NOT_STARTED"
         and index.get("NEXT") == 10538 and index.get("saved_cycles") == 4753
         and index.get("new_business_credit") == 0 and index.get("wall_clock_reset") is False,
         "actual closed A12 input authority")
    for fact in cast(list[object], index["closure_refs"]): checked(file_ref(fact), 65536)
    need(index.get("machine_id") == MACHINE and q.get("machine_id") == MACHINE
         and q.get("schema") == "xar.A13-native2560-quiescence/v1", "actual closed source machine")
    fresh(text(q.get("observed_at_utc")))
    need(q.get("game_processes") == q.get("sdk_processes") == q.get("obs_processes")
         == q.get("publisher_processes") == [] and q.get("supervisor_task_registered") is False,
         "closed Game/SDK/OBS/publisher/Task required")
    refs = cast(list[object], q.get("evidence_refs"))
    need(type(refs) is list and bool(refs) and plan["closure_index"] in refs, "closure in actual quiescence refs")
    for item in refs: checked(file_ref(item), 65536)
def read_pair(plan: Plan, modules: dict[str, ModuleType]) -> tuple[Doc, str, dict[str, list[str]]]:
    base = Path(plan["source_base"]["path"]).resolve(strict=True)
    journal = None if plan["source_wal"] is None else Path(plan["source_wal"]["path"]).resolve(strict=True)
    need(base.name == "driver-state.json" and (journal is None or
         (journal.parent == base.parent and journal.name == "driver-state.wal-v1.json")), "closed canonical pair")
    if journal is None: need(not (base.parent / "driver-state.wal-v1.json").exists(), "unbound WAL exists")
    before = {"base": identity(base), "wal": [] if journal is None else identity(journal)}
    need(before == plan["source_identity"], "pair prestat")
    raw = read_exact(plan["source_base"], 41943040)
    wal_raw = None if plan["source_wal"] is None else read_exact(plan["source_wal"], 8388608)
    replay = cast(Replay, modules["bridge.driver_state_wal_v1"].replay)
    payload, status = replay(raw, wal_raw)
    need(status in ("base_only", "already_consolidated", "replayed") and payload.get("format_version") == 2,
         "original full/replayed v2 required")
    need(before == {"base": identity(base), "wal": [] if journal is None else identity(journal)}, "pair changed")
    return payload, status, before
def _finite_original(source_seed: Doc, prior: Doc) -> Composer:
    o, original_text = _original()
    node = next(n for n in ast.parse(original_text).body
                if isinstance(n, ast.FunctionDef) and n.name == "compose_environment_migration")
    code = text(ast.get_source_segment(original_text, node))
    def swap(old: str, new: str, count: int = 1) -> None:
        nonlocal code
        assert code is not None
        need(code.count(old) == count, "finite original seam: " + old[:48])
        code = code.replace(old, new, count)
    swap("xar.C23-A10-environment-migration-input/v1", "xar.A13-native2560-environment-migration-input/v1")
    start = code.index('    index = checked(plan["closure_index"], 16384)\n')
    end = code.index('    checked(plan["source27_anchor"])\n', start)
    code = code[:start] + "    validate_closed(plan)\n" + code[end:]
    swap('    modules, sdk_sources = load_sdk(plan)\\n'.replace("\\n", "\n"),
         '    modules, sdk_sources = load_sdk(plan)\\n    validate_source_graphics(plan, modules, prior)\\n'.replace("\\n", "\n"))
    swap('"windowed"', '"fullscreen"', 3)
    swap("[1280, 720]", "[2560, 1440]", 2)
    start = code.index('    base = Path(plan["source_base"]["path"]).resolve(strict=True)\n')
    end = code.index('    old_binding = rebinder._checkpoint_binding(payload)\n', start)
    code = code[:start] + '''    payload, status, before = read_pair(plan, modules)
    wal = modules["bridge.driver_state_wal_v1"]
    rebinder = modules["checkpoint_environment_rebinder"]
    replace = modules["ordinary_seed_rebinder"]._replace_lifecycle_anchors
    consumer = modules["bridge.native_driver"].load_native_driver_state_for_resume_payload
    cold = modules["cold_checkpoint_validator"].validate_cold_start_checkpoint_payload_for_pipe
''' + code[end:]
    swap('payload["last_checkpoint"] == original["actual_saved_checkpoint"]',
         'payload["last_checkpoint"] == source_seed["actual_saved_checkpoint"]')
    swap('"xar.C23-A10-environment-migration/v1"', '"xar.C23-A13-environment-migration/v1"')
    swap('"xar.C23-A10-environment-migration-quote/v1"', '"xar.C23-A13-environment-migration-quote/v1"')
    swap('"actual_A09_closure"', '"actual_A12_closure"')
    swap('"original_checkpoint": payload["last_checkpoint"]',
         '"original_checkpoint": original["actual_saved_checkpoint"], "source_checkpoint": payload["last_checkpoint"]')
    swap('"source27_export"', '"sdk_export"')
    swap('"rollback_cycles": 7, "rollback_days": 1, "unknown10519_credit": 0',
         '"rollback_cycles": 5, "rollback_days": 0, "unknown10534_credit": 0')
    swap('"actual_next_sequence": 10521', '"actual_next_sequence": 10538')
    namespace = dict(vars(o))
    namespace.update(MigrationInput=Plan, OLD_ENV=SOURCE_ENV, load_sdk=load_sdk,
        validate_closed=validate_closed, read_pair=read_pair, source_seed=source_seed,
        validate_source_graphics=validate_source_graphics, prior=prior, identity=identity)
    exec(compile(code, "A13-finite-original-cold-migration", "exec"), namespace)
    function = namespace["compose_environment_migration"]; need(callable(function), "composed API")
    return cast(Composer, function)

def compose_environment_migration(value: object) -> tuple[bytes, bytes, Doc, Doc]:
    plan = parse_plan(value)
    need(plan["schema"] == "xar.A13-native2560-environment-migration-input/v1"
         and plan["machine_id"] == MACHINE and plan["execution_owner"] == "Root", "Root plan")
    prior = checked(plan["prior_migration"], 32768)
    original_raw = read_exact(plan["original_seed"], 16384)
    need((len(original_raw), sha(original_raw)) == SEED_PIN, "original SAVE10480 seed")
    original: object = json.loads(original_raw)
    original_doc = obj(original); source_seed = checked(plan["source_derived_seed"], 16384)
    need(prior.get("schema") == "xar.C23-A10-environment-migration/v1"
         and prior.get("machine_id") == MACHINE and prior.get("original_seed") == plan["original_seed"]
         and prior.get("derived_seed") == plan["source_derived_seed"]
         and prior.get("source27_anchor") == plan["source27_anchor"], "prior graphics migration lineage")
    original_cp = obj(original_doc["actual_saved_checkpoint"])
    expected = copy.deepcopy(original_doc)
    obj(obj(expected["actual_saved_checkpoint"])["succession_lifecycle"])["environment_sha256"] = SOURCE_ENV
    need(source_seed == expected and prior.get("target_checkpoint") == source_seed["actual_saved_checkpoint"],
         "source seed only original environment SHA differs")
    source_settings = read_exact(plan["source_settings"])
    source_manifest_raw = read_exact(plan["source_manifest"], 32768)
    for key in ("target_driver_path", "target_seed_path", "receipt_path",
                "source_manifest_archive_path", "source_settings_archive_path"):
        need(not Path(plan[key]).exists() and not Path(plan[key]).is_symlink(), "create-only output consumed")
    function = _finite_original(source_seed, prior)
    target_driver, target_seed, receipt, quote = function(plan)
    receipt.update(original_producer={"path": str(ORIGINAL), "bytes": ORIGINAL_PIN[0], "sha256": ORIGINAL_PIN[1]}, prior_migration=plan["prior_migration"],
        source_environment_sha256=SOURCE_ENV, target_environment_sha256=obj(receipt["target_lifecycle"])["environment_sha256"],
        source_derived_seed=plan["source_derived_seed"], target_derived_seed=quote["derived_seed"],
        source28_anchor=plan["source28_anchor"], source_settings=plan["source_settings"],
        source_prepared_settings=prior["staged_target_settings"],
        source_manifest_archive=future(plan["source_manifest_archive_path"], source_manifest_raw),
        source_settings_archive=future(plan["source_settings_archive_path"], source_settings),
        canonical_source_manifest=plan["source_manifest"], canonical_source_settings=plan["source_settings"],
        source_settings_identity=identity(Path(plan["source_settings"]["path"])),
        source_manifest_identity=identity(Path(plan["source_manifest"]["path"])),
        SAVE_body_validation_calls=2, SAVE_copied=False, canonical_cold_validator_unchanged=True,
        changed_graphics_mode="windowed1280_to_fullscreen2560", actual_target_Game_mod_absence_verified=False,
        history_or_actions_reconstructed=False, runtime_apply_calls=0)
    need(obj(original_cp["succession_lifecycle"])["environment_sha256"] == ORIGINAL_ENV, "original saved environment")
    need(len(encode(receipt)) + 1 <= 24576, "receipt cap")
    paths = [plan["source_manifest_archive_path"], plan["source_settings_archive_path"]]
    need(all(not Path(p).exists() and not Path(p).is_symlink() for p in paths), "new archives required")
    quote.update(receipt=future(plan["receipt_path"], encode(receipt)),
        source_manifest_archive=receipt["source_manifest_archive"], source_settings_archive=receipt["source_settings_archive"],
        SAVE_body_validation_calls=2, SAVE_bytes_copied=0, apply_calls=0)
    return target_driver, target_seed, receipt, quote

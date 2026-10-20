"""LF join candidate; no adoption."""
from __future__ import annotations
import ast, copy, difflib, json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
import prepare_candidate as base
from qualify_candidate import allocated, CARD, CARD_PIN, OUT, MACHINE, DEADLINE, SOURCE_NAMES

OLD = b'return b"".join(serialized_parts) + b"\\n"'
NEW = b'return b"".join((*serialized_parts, b"\\n"))'
FUNCTION = "NativeHeadlessGameplayDriver._encode_driver_state_locked"

def compose(raw):
    if base.pin(raw) != {"bytes": base.SIZE, "sha256": base.SHA256} or raw.count(OLD) != 1:
        raise ValueError("preimage")
    out = raw.replace(OLD, NEW, 1)
    if out.replace(NEW, OLD, 1) != raw: raise ValueError("inverse differs")
    a, b = base.function_nodes(raw), base.function_nodes(out)
    if {k for k in a.keys() | b.keys() if ast.dump(a[k]) != ast.dump(b[k])} != {FUNCTION}:
        raise ValueError("AST")
    return out

def module(name, raw):
    m = ModuleType(name); m.__package__ = name.rpartition(".")[0]
    sys.modules[name] = m
    exec(compile(raw, name, "exec", dont_inherit=True), m.__dict__)
    return m

class Lock:
    def __init__(self, name, events): self.name, self.events, self.depth = name, events, 0
    def __enter__(self): self.depth += 1; self.events.append(("enter", self.name))
    def __exit__(self, *args): self.events.append(("exit", self.name)); self.depth -= 1

def selected(raw, history):
    nodes = base.function_nodes(raw)
    owner = ast.ClassDef(name="Driver", bases=[], keywords=[], decorator_list=[], body=[
        nodes[FUNCTION], nodes["NativeHeadlessGameplayDriver._persist_driver_state"]])
    tree = ast.fix_missing_locations(ast.Module(body=[ast.ImportFrom(module="__future__",
        names=[ast.alias(name="annotations")], level=0), owner], type_ignores=[]))
    env = dict(__package__="lf_qualified", _NATIVE_DRIVER_STATE_VERSION=2,
        driver_state_json_parts=history.driver_state_json_parts, copy=copy, os=os, json=json,
        start_army_timing=lambda *a, **k: None, finish_army_timing=lambda *a, **k: None)
    exec(compile(tree, "selected", "exec"), env)
    return env["Driver"], env

def main():
    if datetime.now(timezone.utc) >= DEADLINE or base.pin(CARD.read_bytes()) != CARD_PIN:
        raise ValueError("budget expired or changed")
    own = base.OWN / Path(__file__).name
    sources = (*SOURCE_NAMES, own.name)
    source_alloc = sum(allocated(base.OWN / n) for n in sources)
    source_bound = source_alloc + 4096 * (len(sources) + 1)
    if source_bound > 65536: raise ValueError("source cap")
    proof_path = OUT / "ENCODE-LF-ONCE-QUALIFICATION.json"
    patch_path = OUT / "ENCODE-LF-ONCE.patch"; fixture = OUT / "lf-once-owned"
    if any(p.exists() for p in (proof_path, patch_path, fixture)):
        raise FileExistsError("create-only")
    original = base.read_input(); candidate = compose(original)
    patch = "".join(difflib.unified_diff(original.decode().splitlines(True), candidate.decode().splitlines(True),
        fromfile="Source25/native_driver.py", tofile="lf-once/native_driver.py", n=3)).encode()
    names = ("bridge/driver_state_wal_v1.py", "bridge/driver_state_history_json.py", "environment.py")
    raw = {n: subprocess.run(["git", "show", base.COMMIT + ":ck3_autonomous_player/src/xar_autoplayer/" + n],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout for n in names}
    package = ModuleType("lf_qualified"); package.__path__ = []; sys.modules[package.__name__] = package
    module("lf_qualified.driver_state_wal_v1", raw[names[0]])
    history = module("lf_qualified.history", raw[names[1]])
    node = next(n for n in ast.parse(raw[names[2]]).body if isinstance(n, ast.FunctionDef) and n.name == "write_bytes_atomic")
    atomic_env = {"Path": Path, "os": os}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "atomic", "exec"), atomic_env)
    fixture.mkdir(); results, failures, paths = [], [], []
    for mode in ("full", "concurrent_append", "write_failure"):
        variants = []
        for label, source in (("original", original), ("candidate", candidate)):
            cls, env = selected(source, history); d = cls(); events = []
            d._driver_state_lock, d._driver_state_write_lock = Lock("state", events), Lock("write", events)
            d.state_dir, d.pipe_name, d._session_bridge_pid = fixture, "synthetic-pipe", 182100
            d._episode_character_id, d._episode_run_id = 40526, "synthetic-episode"
            for n in ("last_checkpoint", "managed_restore_transaction", "succession_expectation", "succession_lifecycle", "campaign_goal"):
                setattr(d, "_" + n, None)
            d._rollback_war_failures, d._rollback_war_failures_migration_required = [], False
            d._command_history = [{"index": 1, "command": "query", "ok": True, "result": {"unicode": "罗贝尔"}}]
            d._driver_state_history_json = history.DriverStateHistoryJsonCache()
            d._driver_state_wal_barrier_required, d._driver_state_wal_barrier_generation = True, 0
            d._driver_state_dirty, d._driver_state_error, d.allow_driver_state_wal_v1 = True, None, False
            target = fixture / (mode + "-" + label + ".json"); paths.append(target)
            d._native_driver_state_path = lambda: target
            def writer(path, payload, **kw):
                assert d._driver_state_write_lock.depth == 1 and d._driver_state_lock.depth == 0
                assert type(payload) is bytes
                events.append(("atomic", base.pin(payload)))
                if mode == "write_failure": raise OSError("synthetic write failure")
                atomic_env["write_bytes_atomic"](path, payload, **kw)
                if mode == "concurrent_append":
                    with d._driver_state_lock:
                        d._command_history.append({"index": 2, "command": "readonly", "ok": True})
                        d._driver_state_dirty = True
            env["write_bytes_atomic"] = writer
            receipt = d._persist_driver_state(persistence_reason=mode)
            payload = target.read_bytes() if target.exists() else None
            if payload is not None: assert payload.endswith(b"\n") and json.loads(payload)["format_version"] == 2
            variants.append((payload, receipt, d._driver_state_dirty, d._driver_state_error, events))
        equal = variants[0] == variants[1]
        if not equal: failures.append(mode)
        results.append({"case": mode, "equal": equal,
            "bytes": len(variants[1][0]) if variants[1][0] is not None else None})
    fixture_alloc = sum(allocated(p) for p in paths if p.exists())
    if not failures:
        if fixture.resolve().parent != OUT.resolve(): raise ValueError("cleanup")
        for p in paths:
            p.unlink(missing_ok=True)
        fixture.rmdir()
    patch_path.write_bytes(patch)
    proof = dict(schema="xar.driver-full-state-lf-once-qualification/v1", machine_id=MACHINE,
        observed_at_utc=datetime.now(timezone.utc).isoformat(),
        status="SOURCE_QUALIFIED_NOT_ADOPTED" if not failures else "FAILED", commit=base.COMMIT,
        input=base.pin(original), output_RAM=base.pin(candidate), source=base.pin(own.read_bytes()),
        cases=results, failures=failures, function=FUNCTION, inverse_and_other_ASTs_equal=True,
        source_allocated=source_alloc, source_bound=source_bound, fixture_peak=fixture_alloc,
        patch=base.pin(patch), cleanup=not failures, runtime_credit=0)
    encoded = json.dumps(proof, ensure_ascii=False, separators=(",", ":")).encode()
    with proof_path.open("xb") as f: f.write(encoded)
    retained = [OUT / n for n in ("QUALIFICATION.json", "DIFF.patch", proof_path.name, patch_path.name)]
    highwater = sum(allocated(p) for p in retained) + fixture_alloc + 4096 * 17
    if highwater > 196608: raise ValueError("artifact cap")
    print(json.dumps(dict(proof={"path": str(proof_path), **base.pin(encoded)},
        artifact_highwater=highwater, qualification=proof), ensure_ascii=False))
    return int(bool(failures))

if __name__ == "__main__": raise SystemExit(main())

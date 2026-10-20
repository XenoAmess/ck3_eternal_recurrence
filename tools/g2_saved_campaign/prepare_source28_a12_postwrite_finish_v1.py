"""A12 exact postwrite verification. Returns the sole create-only receipt in RAM."""
import ast, hashlib, json, shutil, subprocess, sys, types
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from prepare_c23_a10_union_v1 import ExactRef

def prepare_finish(module: ModuleType, release_ref: ExactRef) -> tuple[Path, bytes]:
    p = module.prior
    need = module.require
    release = p.checked(release_ref, 32768)
    need(release["schema"] == "xar.storage.Source28-A12-source03-and-postwrite-finish-exact/v1"
        and release["machine_id"] == module.MACHINE and release["owner"] == "Root"
        and release["status"] == "ADMITTED" and release["Root_postwrite_finish_execution_release"] is True,
        "separate exact Root finish release")
    change = release["source_output"]
    verifier = {"path": change["path"], "bytes": change["after"]["bytes"], "sha256": change["after"]["sha256"]}
    need(p.ref(module.__file__) == verifier, "exact corrected verifier")
    machine = subprocess.check_output([sys.executable, "-B", str(module.OWN.parent / "ck3_live_run_id.py"), "machine"], text=True).strip()
    need(machine == module.MACHINE, "actual machine differs")
    original = release["original_adopt"]
    plan_ref, quote_ref, card_ref = original["plan"], original["quote"], original["card"]
    plan, quote, card = p.checked(plan_ref, 131072), p.checked(quote_ref, 262144), p.checked(card_ref)
    old = change["before"]
    archive = change["preserved_before"]
    need(plan["union_producer"] == quote["adopter"] == old and p.ref(archive["path"]) == archive
        and (old["bytes"], old["sha256"]) == (archive["bytes"], archive["sha256"]),
        "original producer provenance must remain exact")
    need(card["schema"] == "xar.C23-A12-runtime-prepare-admission/v1"
        and card["machine_id"] == module.MACHINE and card["owner"] == "Root"
        and card["status"] == "ADMITTED" and card["root_direct_execution_release"] is True
        and card["canonical_capacity_review_passed"] is True
        and card["plan"] == plan_ref and card["quote"] == quote_ref
        and card["full_storage_ref"] == plan["full_storage_ref"]
        and type(card["hard_bytes"]) is int and quote["prepare_peak_upper"] <= card["hard_bytes"],
        "original exact runtime release")
    runtime, taskroot = module.U12, module.O / "tasks/spec-supervisor-a12"
    intent, receipt = module.O / "A12-PREPARE-INTENT01.json", module.O / "A12-PREPARED01.json"
    need(p.ref(intent) == original["intent"] and not receipt.exists(), "consumed intent and absent receipt")
    claim = p.checked(original["intent"])
    need(claim["machine_id"] == module.MACHINE and claim["status"] == "ONE_SHOT_A12_PREPARE_INTENT"
        and claim["plan"] == plan_ref and claim["quote"] == quote_ref and claim["card"] == card_ref,
        "original one-shot intent differs")
    need(datetime.now(timezone.utc) < datetime.fromisoformat(quote["review_at_utc"])
        and datetime.now(timezone.utc) < datetime.fromisoformat(release["review_at_utc"])
        and shutil.disk_usage(module.O).free >= card["capacity"]["D_conservative_floor_bytes"],
        "fresh finite review and floor")
    need(not (runtime / "p37-queue").exists() and not (runtime / "STOP-OWNED-GAME-C23").exists(),
        "no started SDK or Game stop marker")
    rows = quote["files"]
    need(len(rows) == 140 and len({row["path"] for row in rows}) == 140, "original complete140")
    actual = []
    for row in rows:
        item = {key: row[key] for key in ("path", "bytes", "sha256")}
        need(p.ref(row["path"]) == item, "actual140 output differs")
        if row["mode"] == "hardlink":
            need(p.ref(row["source"]["path"]) == row["source"], "immutable source differs")
            a, b = Path(row["path"]).stat(), Path(row["source"]["path"]).stat()
            need((a.st_dev, a.st_ino) == (b.st_dev, b.st_ino), "immutable link identity differs")
        else:
            need(row["mode"] == "create-only", "unknown original output mode")
        actual.append(item)
    state, original = runtime / "state", module.T0 / "state"
    need(state.resolve(strict=True) == original.resolve(strict=True)
        and (state.stat().st_dev, state.stat().st_ino) == (original.stat().st_dev, original.stat().st_ino),
        "whole state same-FileID junction")
    module.campaign_score_guard(alias_required=True)
    path = module.OWN / "adopt_c23_a05_union_v1.py"
    need(p.ref(path) == quote["original_adopter_source"],
        "original adopter source exact")
    body = path.read_text(encoding="utf-8")
    node = next(n for n in ast.parse(body).body if isinstance(n, ast.FunctionDef) and n.name == "adopt")
    body = ast.get_source_segment(body, node).replace("A05", "A12").replace("a05", "a12")
    need(body.count("    freeze = union.checked(") == 1, "original postwrite boundary")
    tail = "    freeze = union.checked(" + body.split("    freeze = union.checked(", 1)[1]
    seam = "exec(compile(source, 'A12-actual-saved-basis', 'exec'), scope)"
    tail = p.swap(tail.encode(), seam, "source=metadata_source(source)\n    " + seam, 1).decode()
    seam = "_, basis_report = scope['saved_basis'](runtime_root=runtime)"
    tail = p.swap(tail.encode(), seam, "metadata_scope(scope,runtime)\n    " + seam, 1).decode()
    tail = p.swap(tail.encode(), "'intent': ref(intent), 'outputs': actual",
        "'intent': ref(intent), 'postwrite_recovery': recovery, 'outputs': actual", 1).decode()
    tail = p.swap(tail.encode(), "'state_same_FileID': True",
        "'state_same_FileID': True, 'campaign_score_same_FileID': True", 1).decode()
    adopter = p._module(path, "_a12_finish_original_adopter")
    captured = []
    def ram_once(target: Path, payload: bytes) -> ExactRef:
        need(Path(target) == receipt and not receipt.exists() and not captured, "sole prepared receipt")
        captured.append(payload)
        return {"path": str(receipt), "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    union = types.SimpleNamespace(MACHINE=module.MACHINE, T0=module.T0, checked=p.checked,
        ref=p.ref, raw=p.raw, _module=p._module)
    env = dict(vars(adopter), union=union, runtime=runtime, taskroot=taskroot, receipt=receipt,
        intent=intent, actual=actual, machine=module.MACHINE, plan=plan, plan_ref=plan_ref,
        quote_ref=quote_ref, card_ref=card_ref, once=ram_once, metadata_source=module.metadata_source,
        metadata_scope=module.metadata_scope, recovery={"release": release_ref,
        "original_producer": old, "preserved_original_producer": archive,
        "corrected_verifier_producer": verifier, "intent_replayed": False,
        "runtime_outputs_rewritten": 0, "original_postwrite_verifier_failed": "startup timing shape"})
    exec(compile("def verify_postwrite():\n" + tail, "A12-exact-postwrite-finish-RAM", "exec"), env)
    env["verify_postwrite"]()
    need(len(captured) == 1 and not receipt.exists(), "prepared receipt remains RAM-only")
    return receipt, captured[0]

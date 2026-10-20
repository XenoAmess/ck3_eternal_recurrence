"""Independent strict package-scope transform/qualification; old files unchanged."""
import ctypes as C
from ctypes import wintypes as W
from datetime import datetime, timezone
import difflib, hashlib, importlib.util, json, shutil, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
RELATIVE = "xar_autoplayer/war_strategic_reserve_v1.py"
BASE_SHA = "9c86a5f0fc82e292fc3baa553d128978b8b53f74ac7dae067bf86d8344b7a703"
IMPORT = "from .war_reinforcement_finance_v1 import observe_reinforcement_finance_v1\n"
OLD = '''    connected_wars = purposes | {row["war_id"] for row in _armies(snapshot.get("active_wars"))
        if row.get("player_is_primary_war_leader") is True and type(row.get("war_id")) is int}
'''
NEW = OLD + '''    # Additional links restrict the package; they never authorize a hire.
    connected_wars.update(row["war_id"] for row in _armies(snapshot.get("active_wars"))
        if nonleading_player_realm_siege_war_v1(snapshot, row))
    native = snapshot.get("native_revision")
    played, diag = snapshot.get("played_character", {}), snapshot.get("diagnostics", {})
    native_frame = (snapshot.get("source") == "injected-dll-named-pipe"
        and type(native) is int and native > 0 and snapshot.get("snapshot_id") == f"native:{native}"
        and type(snapshot.get("date_raw")) is int and snapshot.get("paused") is True
        and snapshot.get("map_ready") is True and snapshot.get("active_event") is None
        and snapshot.get("pending_character_interaction") is None
        and played.get("source") == "native" and played.get("alive") is True
        and diag.get("connected") is True and type(diag.get("bridge_pid")) is int and diag["bridge_pid"] > 0
        and type(diag.get("connection_generation")) is int and diag["connection_generation"] >= 0)
    active_native_nonleading = {row["war_id"] for row in _armies(snapshot.get("active_wars"))
        if native_frame and row.get("source") == "native" and row.get("player_side") == "defender"
        and row.get("player_is_primary_war_leader") is False
        and type(row.get("war_id")) is int and row["war_id"] > 0}
'''
HOLD = '''        records.append((row, selected, set(prior_purposes) | set(prior_scope)))
'''
HNEW = HOLD + '''        # Preserve prior strict contract costs while the same War remains active,
        # including after its siege scope disappears. Unknown history grants nothing.
        qualified_prior = {war["war_id"] for war in _armies(decision.get("war_spending_priority", {}).get("wars"))
            if war.get("primary_player_war") is False and war.get("player_side") == "defender"
            and type(war.get("war_id")) is int
            and isinstance(proof := war.get("nonleading_realm_siege_cash_protection_v1"), Mapping)
            and proof.get("qualified_current_scope") is True and proof.get("procurement_scope_extended") is True
            and proof.get("reasons") == ["qualified_nonleading_defence_stationary_hostile_siege_in_player_realm"]
            and "qualified_nonleading_defence_stationary_hostile_siege_in_player_realm" in war.get("protect_cash_reasons", [])}
        prior_native, prior_date = source.get("native_revision"), source.get("date_raw")
        frame_verified = (type(prior_native) is int and prior_native > 0
                and source.get("snapshot_id") == f"native:{prior_native}"
                and type(prior_date) is int and prior_date <= snapshot["date_raw"])
        active_prior = set(prior_purposes) & active_native_nonleading
        if active_prior and (not frame_verified or not active_prior.issubset(qualified_prior)):
            return {"status": "unavailable", "reason": "active_nonleading_prior_contract_scope_unqualified",
                    "remaining_package_gold_raw": None}
        connected_wars.update(active_prior)
'''
PAIRS = [(IMPORT, IMPORT + "from .nonleading_player_realm_siege_v1 import nonleading_player_realm_siege_war_v1\n"), (OLD, NEW), (HOLD, HNEW)]

def transform_package(raw, *, inverse=False):
    if not inverse and hashlib.sha256(raw).hexdigest() != BASE_SHA: raise ValueError("package preimage differs")
    text = raw.decode(); nl = "\r\n" if "\r\n" in text else "\n"
    for a, b in reversed(PAIRS) if inverse else PAIRS:
        a, b = (b, a) if inverse else (a, b)
        a, b = a.replace("\n", nl), b.replace("\n", nl)
        if text.count(a) != 1: raise ValueError("exact package hunk differs")
        text = text.replace(a, b, 1)
    result = text.encode()
    if inverse and hashlib.sha256(result).hexdigest() != BASE_SHA: raise ValueError("inverse differs")
    return result

def allocation(path):
    class Standard(C.Structure):
        _fields_ = [("allocation", C.c_longlong), ("end", C.c_longlong), ("links", W.DWORD), ("delete", C.c_byte), ("directory", C.c_byte)]
    k = C.WinDLL("kernel32", use_last_error=True)
    k.CreateFileW.argtypes = [W.LPCWSTR,W.DWORD,W.DWORD,C.c_void_p,W.DWORD,W.DWORD,W.HANDLE]; k.CreateFileW.restype = W.HANDLE
    k.GetFileInformationByHandleEx.argtypes = [W.HANDLE,C.c_int,C.c_void_p,W.DWORD]; k.CloseHandle.argtypes = [W.HANDLE]
    h = k.CreateFileW(str(path),0x80,7,None,3,0x02000000,None); info = Standard()
    if h == W.HANDLE(-1).value: raise C.WinError(C.get_last_error())
    try:
        if not k.GetFileInformationByHandleEx(h,1,C.byref(info),C.sizeof(info)): raise C.WinError(C.get_last_error())
    finally: k.CloseHandle(h)
    return info.allocation

def account(root):
    rows = [root,*root.rglob("*")]
    return {"FileStandardInfo_allocation":sum(map(allocation,rows)), "directory_floor":4096*sum(p.is_dir() for p in rows)}

if __name__ == "__main__":
    s = importlib.util.spec_from_file_location("qualified_decision_original",HERE/"qualify.py")
    q = importlib.util.module_from_spec(s); s.loader.exec_module(q)
    lane = q.OUT; out = lane/"package-followup01"
    card = json.loads(q.finite(q.CARD))
    if q.sha(q.finite(q.CARD)) != q.CARD_SHA or datetime.now(timezone.utc) >= datetime.fromisoformat(card["review_at_utc"]): raise ValueError("budget changed/expired")
    out.mkdir(); q.OUT = out
    raw = q.finite(q.SRC/RELATIVE)
    if q.finite(q.FROZEN/RELATIVE) != raw: raise ValueError("frozen base differs")
    transformed = transform_package(raw)
    if transform_package(transformed,inverse=True) != raw: raise ValueError("inverse differs")
    trade = q.module_from_ram(q.tx.transform(q.finite(q.SRC/q.tx.TRADEOFF),q.tx.TRADEOFF,stage="procurement"),q.tx.TRADEOFF)
    model = (trade,q.original_construction)
    with q.installed(model): module = q.module_from_ram(transformed,RELATIVE)
    facts = {}; error = None
    try:
        d = q.driver("scope"); a = d.snapshot["active_wars"][0]
        b = q.deepcopy(a); b["war_id"] += 1; b["player_relative_war_score"] = -10; b["enemy_armies"][0]["army_id"] += 1
        d.snapshot["active_wars"].append(b)
        with q.installed(model): first = module.assess_mercenary_reinforcement_v1(d.snapshot,q.context(d.snapshot),campaign_root=d.snapshot["campaign_root_context"])
        assert first["selected_candidate"]["purpose_war_ids"] == [a["war_id"]]
        ledger = {"pending":None,"observed":[{"status":"employment_observed","action_request_id":"strict-A","source_frame":q.cash.observed_frame(d.snapshot),"decision":first}]}
        for case in ("both_current","A_siege_gone","A_ended","prior_unknown"):
            snap, saved = q.deepcopy(d.snapshot),q.deepcopy(ledger)
            snap["active_wars"][0]["player_relative_war_score"] = -1; snap["active_wars"][1]["player_relative_war_score"] = -20
            if case != "both_current": snap["active_wars"][0]["enemy_armies"][0]["siege_province_in_player_subrealm"] = None
            if case == "A_ended": snap["active_wars"].pop(0)
            if case == "prior_unknown": saved["observed"][0]["decision"]["war_spending_priority"]["wars"][0][q.tx.FIELD]["qualified_current_scope"] = False
            old = q.strategic.observe_procurement_package_budget_v1(snap,saved,purpose_war_ids=[b["war_id"]])
            new = module.observe_procurement_package_budget_v1(snap,saved,purpose_war_ids=[b["war_id"]])
            assert old["status"] == "no_prior_package"
            if case in ("both_current","A_siege_gone"):
                assert new["committed_contract_quote_gold_raw"] == 15000000 and new["remaining_package_gold_raw"] == 5000000
                with q.installed(model): choice = module.assess_mercenary_reinforcement_v1(snap,q.context(snap),campaign_root=snap["campaign_root_context"],procurement_ledger=saved)
                assert choice["selected_company_id"] is None
            elif case == "prior_unknown": assert new["status"] == "unavailable"
            else: assert new["status"] == "no_prior_package"
            facts[case] = {"before":old,"after":new}
    except BaseException: error = traceback.format_exc()
    q.new(out/"package.patch","".join(difflib.unified_diff(raw.decode().splitlines(True),transformed.decode().splitlines(True),fromfile=RELATIVE,tofile="procurement-closed/"+RELATIVE)).encode())
    before = account(lane); fixtures = (out/"synthetic-fixtures").resolve()
    if fixtures != out.resolve()/"synthetic-fixtures": raise ValueError("cleanup target differs")
    if fixtures.exists(): shutil.rmtree(fixtures)
    source = account(HERE)
    proof = {"schema":"xar.nonleading-procurement-package-followup/v1","machine_id":q.MACHINE,"observed_at_utc":datetime.now(timezone.utc).isoformat(),"machine_source":"same lane; prior qualification tools/ck3_live_run_id.py machine",
        "status":"FAILED_PRESERVED" if error else "SOURCE_FOLLOWUP_QUALIFIED_NOT_DEPLOYED","subcases_completed":len(facts),"error":error,"preimage":q.reference(q.SRC/RELATIVE),"RAM_output":{"relative":RELATIVE,"bytes":len(transformed),"sha256":q.sha(transformed)},"patch":q.reference(out/"package.patch"),"facts":facts,
        "boundary":"Current strict helper admits budget connections. Prior qualified same-actor/episode native frame/date restricts the package while that native defender War stays active, even after its siege disappears. Native revision numbers are not ordered across reloads. Unknown prior scope makes budget unavailable, never fresh. No live, hire-authority or performance credit.",
        "source_allocation":source,"artifact_highwater":before,"FileStandardInfo_class":1,"source_proof_reserved":4096,"artifact_result_and_FS_reserved":32768,"temporary_owned_fixture_cleaned":not fixtures.exists(),"review_at_utc":card["review_at_utc"]}
    if sum(source.values())+4096 > 65536 or sum(before.values())+32768 > 196608: raise ValueError("allocation exceeds lane")
    q.new(out/"RESULT.json",(json.dumps(proof,ensure_ascii=False,indent=2)+"\n").encode())
    print(json.dumps({"status":proof["status"],"result":q.reference(out/"RESULT.json"),"RAM_output":proof["RAM_output"],"source":source,"artifacts":before}))
    raise SystemExit(1 if error else 0)

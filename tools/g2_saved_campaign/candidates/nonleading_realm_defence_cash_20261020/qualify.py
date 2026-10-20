"""One bounded offline qualification. No Game, native, MCP, Task or desktop IO.

Run with -B -X utf8. The two transformed modules are compiled in RAM. Closed
actual portable695 is used unchanged and in explicitly synthetic variants.
The existing synthetic WarDriver exercises genuine policy/ordinary consumers.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import ctypes
from datetime import datetime, timezone
import difflib
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SRC = REPO / "ck3_autonomous_player/src"
UNIT = REPO / "ck3_autonomous_player/tests/unit"
FROZEN = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/sdk-v20261019-candidate/src20")
CARD = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/G2-PARALLEL-SOURCE-QUALIFICATION1MiB0630-ADMITTED01.json")
CARD_SHA = "0d279e0bcc91159536b4e2c86a8079f24db195df9456a5c819d7a773ecdae1d4"
OUT = CARD.parent / "G2-PARALLEL-QUALIFICATION0630-01/decision"
MACHINE = "xenoamess-full-tower-eb9d2c1186"
FIXTURE = REPO / "ck3_autonomous_player/tests/fixtures/portable_actual_695.json.gz"
FIXTURE_SHA = "da619ee770f2a4c124e9e625a9acc6913b2af96b8b1ab2af90896a67bd5e2937"
HELPER = SRC / "xar_autoplayer/nonleading_player_realm_siege_v1.py"
HELPER_SHA = "3f5103e42c8d7d785aa7680d19be592407a55b8e3d6bb4fb55159817fbe925e6"
MAX_READ = 128 * 1024


def finite(path):
    if path.stat().st_size > MAX_READ:
        raise ValueError("finite source/artifact read bound exceeded")
    return path.read_bytes()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def reference(path):
    data = finite(path)
    return {"path": str(path), "bytes": len(data), "sha256": sha(data)}


def new(path, data):
    if not path.parent.resolve().is_relative_to(OUT.resolve()):
        raise ValueError("artifact output escaped assigned lane")
    if len(data) > 64 * 1024:
        raise ValueError("single output exceeds quote")
    with path.open("xb") as stream:
        stream.write(data)


def allocated(path):
    high = ctypes.c_uint32()
    get = ctypes.windll.kernel32.GetCompressedFileSizeW
    get.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_uint32)]
    get.restype = ctypes.c_uint32
    ctypes.set_last_error(0)
    low = get(str(path), ctypes.byref(high))
    if low == 0xFFFFFFFF and ctypes.get_last_error():
        raise ctypes.WinError(ctypes.get_last_error())
    return (high.value << 32) | low


def account(root):
    # Only this worker's explicitly assigned finite child is enumerated.
    files = sorted(p for p in root.rglob("*") if p.is_file())
    return {"file_count": len(files), "logical_bytes": sum(p.stat().st_size for p in files),
            "allocated_file_bytes": sum(allocated(p) for p in files),
            "directory_count": 1 + sum(p.is_dir() for p in root.rglob("*")),
            "files": [reference(p) for p in files]}


spec = importlib.util.spec_from_file_location("decision_candidate_transform", HERE / "transform.py")
tx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tx)
sys.path[:0] = [str(SRC), str(UNIT), str(REPO)]
from test_war_reinforcement_tradeoff_v1 import WarDriver, company, context
from xar_autoplayer import construction_formal_consumer as original_construction
from xar_autoplayer import war_mercenary_consumer_v1 as mercenary
from xar_autoplayer import war_reinforcement_tradeoff_v1 as original_tradeoff
from xar_autoplayer import war_strategic_reserve_v1 as strategic
from xar_autoplayer import wartime_construction_cash_v1 as cash
from xar_autoplayer.nonleading_player_realm_siege_v1 import nonleading_player_realm_siege_war_v1


def module_from_ram(raw, relative):
    name = relative.removesuffix(".py").replace("/", ".")
    module = types.ModuleType(name)
    module.__package__ = "xar_autoplayer"
    module.__file__ = str(SRC / relative)
    exec(compile(raw, module.__file__, "exec"), module.__dict__)
    return module


@contextmanager
def installed(model):
    tradeoff, construction = model
    import xar_autoplayer
    with (patch.dict(sys.modules, {
              tradeoff.__name__: tradeoff, construction.__name__: construction}),
          patch.object(xar_autoplayer, "war_reinforcement_tradeoff_v1", tradeoff),
          patch.object(xar_autoplayer, "construction_formal_consumer", construction),
          patch.object(mercenary, "observe_war_spending_priority_v1", tradeoff.observe_war_spending_priority_v1),
          patch.object(strategic, "observe_war_spending_priority_v1", tradeoff.observe_war_spending_priority_v1)):
        yield tradeoff, construction


def priority(model, snapshot):
    with installed(model):
        return model[0].observe_war_spending_priority_v1(snapshot,
            campaign_root=snapshot.get("campaign_root_context"))


def strip_new(value):
    value = deepcopy(value)
    value.pop("nonleading_realm_siege_construction_deferred_v1", None)
    for row in value["wars"]:
        row.pop(tx.FIELD, None)
    return value


def synthetic_actual(actual):
    value = deepcopy(actual["snapshot"])
    war = value["active_wars"][0]
    war["player_is_primary_war_leader"] = False
    for enemy in war["enemy_armies"]:
        enemy.update(siege_province_in_player_subrealm=True,
            move_target_province_id=None, route_province_ids=[], route_read_status="complete_empty")
    return value


def driver(name):
    directory = OUT / "synthetic-fixtures" / name
    directory.mkdir(parents=True, exist_ok=False)
    result = WarDriver(directory)
    value = result.snapshot
    # These native-shaped identity/realm facts are synthetic, not observations.
    value.update(source="injected-dll-named-pipe", snapshot_id=f"native:{value['native_revision']}",
        paused=True, map_ready=True, active_event=None, pending_character_interaction=None)
    value["played_character"].update(source="native", alive=True)
    value["played_character_gold"]["raw"] = 60000000
    value.setdefault("diagnostics", {}).update(connected=True, bridge_pid=4242, connection_generation=0)
    war = value["active_wars"][0]
    war.update(source="native", player_is_primary_war_leader=False, player_relative_war_score=-12,
        targeted_title_ids=[])
    enemy = war["enemy_armies"][0]
    enemy.update(source="native", owner_character_id=99999, army_state="sieging", army_state_code=3,
        siege_province_in_player_subrealm=True, move_target_province_id=None,
        route_province_ids=[], route_read_status="complete_empty")
    assert nonleading_player_realm_siege_war_v1(value, war)
    return result


class Qualification(unittest.TestCase):
    models = None
    actual = None
    test_cases = 0
    facts = {}

    def test_01_exact_transform_drift_and_primary_equivalence(self):
        for relative, raw in ORIGINALS.items():
            for stage in ("guard", "procurement"):
                candidate = tx.transform(raw, relative, stage=stage)
                self.assertEqual(tx.transform(candidate, relative, stage=stage, inverse=True), raw)
                with self.assertRaises(ValueError):
                    tx.transform(raw + b"\n", relative, stage=stage)
                with self.assertRaises(ValueError):
                    tx.transform(candidate + b"\n", relative, stage=stage, inverse=True)
        base = priority(MODELS["original"], ACTUAL["snapshot"])
        for stage in ("guard", "procurement"):
            self.assertEqual(strip_new(priority(MODELS[stage], ACTUAL["snapshot"])), base)

    def test_02_guard_has_real_construction_effect_with_ample_cash(self):
        d = driver("guard-ample")
        d.snapshot["played_character_gold"]["raw"] = 100000000
        value = d.snapshot
        root = value["campaign_root_context"]
        frame = cash.observed_frame(value)
        spending = {"status": "observed", "frame": {"actor_character_id": frame["played_character_id"],
            "native_revision": frame["native_revision"], "date_raw": frame["date_raw"],
            "snapshot_id": frame["snapshot_id"]}, "budget": {"active_war_count": 1, "reserved_raw": {"gold": 0}}}
        ample = cash.observe_wartime_construction_cash_v1(value, kind="new_building", construction_gold_raw=1,
            root=root, spending=spending, market=context(value), market_source_frame=frame,
            mercenary_ledger={"pending": None, "observed": []})
        self.assertTrue(ample["new_spend_allowed"])
        old = priority(MODELS["original"], value)
        guard = priority(MODELS["guard"], value)
        self.assertFalse(old["defer_new_economic_construction"])
        self.assertTrue(guard["defer_new_economic_construction"])
        self.assertEqual(guard["cash_protection_priority_war_ids"], [])
        planned = {"revision": value["revision"], "plan": {"selected_step": "life-advance"}}
        with installed(MODELS["guard"]):
            result = MODELS["guard"][1].plan_construction_private(d, planned, value, [], {"life-advance"})
        self.assertEqual(result["plan"]["selected_step"], "life-advance")
        self.assertIn("qualified nonleading defensive siege", result["plan"]["construction_spending_deferred_v1"]["reason"])
        self.assertEqual(d.requests, [])
        self.facts["guard"] = {"baseline_ample_cash_admission": ample,
            "baseline_priority_deferred": False, "guard_priority_deferred": True,
            "ordinary_construction_result": result, "native_requests": 0}

    def test_03_scope_negatives_and_no_input_mutation(self):
        changes = ("unknown_realm", "foreign_realm", "moving", "attacker", "terminal_score",
            "event", "disconnected", "wrong_snapshot", "detached_war", "bool_score")
        for change in changes:
            with self.subTest(change=change):
                value = synthetic_actual(ACTUAL)
                war = value["active_wars"][0]
                if change == "unknown_realm":
                    for row in war["enemy_armies"]: row["siege_province_in_player_subrealm"] = None
                elif change == "foreign_realm":
                    for row in war["enemy_armies"]: row["siege_province_in_player_subrealm"] = False
                elif change == "moving":
                    for row in war["enemy_armies"]: row.update(move_target_province_id=2623, route_province_ids=[2623])
                elif change == "attacker": war["player_side"] = "attacker"
                elif change == "terminal_score": war["player_relative_war_score"] = -100
                elif change == "event": value["active_event"] = {"instance_id": 44}
                elif change == "disconnected": value["diagnostics"]["connected"] = False
                elif change == "wrong_snapshot": value["snapshot_id"] = "native:old"
                elif change == "bool_score": war["player_relative_war_score"] = True
                else:
                    self.assertFalse(nonleading_player_realm_siege_war_v1(value, deepcopy(war)))
                    continue
                before = deepcopy(value)
                baseline = priority(MODELS["original"], value)
                for stage in ("guard", "procurement"):
                    result = priority(MODELS[stage], value)
                    self.assertFalse(result["nonleading_realm_siege_construction_deferred_v1"])
                    self.assertEqual(strip_new(result), baseline)
                self.assertEqual(value, before)

    def test_04_guard_does_not_open_procurement_but_explicit_stage_does(self):
        d = driver("scope")
        base = {"selected_step": "life-advance"}
        caps = {mercenary.QUERY_CAPABILITY, mercenary.HIRE_CAPABILITY, mercenary.ROOT_CAPABILITY}
        results = {}
        for stage in ("original", "guard", "procurement"):
            with installed(MODELS[stage]):
                results[stage] = mercenary.plan_war_mercenary_turn_v1(d, base, snapshot=d.snapshot,
                    history=[], bridge_capabilities=caps)
        self.assertEqual(results["original"]["selected_step"], "life-advance")
        self.assertEqual(results["guard"]["selected_step"], "life-advance")
        self.assertEqual(results["procurement"]["selected_step"], mercenary.QUERY_STEP)
        self.assertEqual(d.requests, [])
        self.assertEqual(d.hire_count, 0)
        self.facts["explicit_procurement_scope"] = results

    def test_05_actual_assessor_keeps_finance_legality_and_unknown_arrival(self):
        d = driver("assessor")
        root = d.snapshot["campaign_root_context"]
        market = context(d.snapshot)
        with installed(MODELS["procurement"]):
            selected = strategic.assess_mercenary_reinforcement_v1(d.snapshot, market, campaign_root=root)
            self.assertEqual(selected["selected_company_id"], 0)
            chosen = selected["selected_candidate"]
            self.assertEqual(chosen["purpose_war_ids"], [100663323])
            self.assertTrue(chosen["finance"]["retains_military_allocation"])
            self.assertIsNone(selected["arrival_eta_days"])
            self.assertIsNone(selected["battle_win_probability"])
            self.assertFalse(selected["postcondition_verified"])
            for bad in ("native_affordability", "maintenance_unknown", "treasury_short", "spawn_hostile"):
                with self.subTest(bad=bad):
                    s, c, r = deepcopy(d.snapshot), deepcopy(market), deepcopy(root)
                    if bad == "native_affordability": c["rows"][0]["final_terms"]["can_afford"] = False
                    elif bad == "maintenance_unknown": r["player_max_monthly_gold_maintenance_v1"]["status"] = "unavailable"
                    elif bad == "treasury_short": s["played_character_gold"]["raw"] = 1
                    else: c["rows"][0]["location"]["hire_auto_raise_province_id"] = s["active_wars"][0]["enemy_armies"][0]["current_province_id"]
                    rejected = strategic.assess_mercenary_reinforcement_v1(s, c, campaign_root=r)
                    self.assertIsNone(rejected["selected_company_id"])
        self.facts["representative_assessor"] = {key: selected[key] for key in
            ("selected_company_id", "selected_candidate", "arrival_eta_days", "battle_win_probability", "postcondition_verified")}

    def test_06_pending_and_concrete_orders_never_duplicate_or_retarget(self):
        d = driver("pending")
        with installed(MODELS["procurement"]):
            selected = strategic.assess_mercenary_reinforcement_v1(d.snapshot, context(d.snapshot),
                campaign_root=d.snapshot["campaign_root_context"])
            plan = {"war_mercenary_source_frame": cash.observed_frame(d.snapshot),
                "war_mercenary_decision_v1": selected, "war_mercenary_pre_capture_epoch": 1}
            d.hire_mercenary_v1 = lambda **kwargs: (_ for _ in ()).throw(TimeoutError("synthetic lost hire ACK"))
            with self.assertRaises(TimeoutError):
                mercenary.submit_war_mercenary_v1(d, plan=plan, expected_revision=d.snapshot["revision"])
            with self.assertRaisesRegex(ValueError, "never be resubmitted"):
                mercenary.submit_war_mercenary_v1(d, plan=plan, expected_revision=d.snapshot["revision"])
            for step in ("move-army-1-to-2629", "select-event-option-1", "query-war-termination-options-100663323"):
                with self.subTest(step=step):
                    result = mercenary.plan_war_mercenary_turn_v1(d, {"selected_step": step},
                        snapshot=d.snapshot, history=[], bridge_capabilities={mercenary.QUERY_CAPABILITY, mercenary.HIRE_CAPABILITY})
                    self.assertEqual(result["selected_step"], step)
        self.facts["pending_no_duplicate"] = {"lost_ack_retained": True, "second_submit_refused": True,
            "concrete_move_event_termination_steps_preserved": True}

    def test_07_same_purpose_package_cap_remains_cumulative(self):
        d = driver("package")
        with installed(MODELS["procurement"]):
            selected = strategic.assess_mercenary_reinforcement_v1(d.snapshot, context(d.snapshot),
                campaign_root=d.snapshot["campaign_root_context"])
            chosen = selected["selected_candidate"]
            record = {"status": "employment_observed", "action_request_id": "synthetic-prior-contract",
                "source_frame": cash.observed_frame(d.snapshot), "decision": selected}
            ledger = {"pending": None, "observed": [record]}
            budget = strategic.observe_procurement_package_budget_v1(d.snapshot, ledger, purpose_war_ids=[100663323])
            self.assertEqual(budget["status"], "available")
            self.assertEqual(budget["committed_contract_quote_gold_raw"], chosen["gold_cost_raw"])
            remaining = strategic.assess_mercenary_reinforcement_v1(d.snapshot, context(d.snapshot),
                campaign_root=d.snapshot["campaign_root_context"], procurement_ledger=ledger)
            self.assertIsNone(remaining["selected_company_id"])
            self.assertFalse(budget["payment_attribution_verified"])
        self.facts["cumulative_package"] = budget


if __name__ == "__main__":
    card_raw = finite(CARD)
    if sha(card_raw) != CARD_SHA:
        raise ValueError("storage card changed")
    card = json.loads(card_raw)
    now = datetime.now(timezone.utc)
    if now >= datetime.fromisoformat(card["review_at_utc"]):
        raise ValueError("manual budget review expired")
    machine = subprocess.run([sys.executable, "-B", "-X", "utf8", str(REPO / "tools/ck3_live_run_id.py"), "machine"],
        check=True, capture_output=True, text=True, encoding="utf-8")
    if MACHINE not in machine.stdout or card["machine_id"] != MACHINE:
        raise ValueError("execution machine mismatch")
    if OUT.exists():
        raise ValueError("unique qualification output already exists; no blind replay")
    OUT.mkdir(parents=True)
    (OUT / "synthetic-fixtures").mkdir()
    ORIGINALS = {relative: finite(SRC / relative) for relative in tx.BASE}
    for relative, raw in ORIGINALS.items():
        if sha(raw) != tx.BASE[relative] or finite(FROZEN / relative) != raw:
            raise ValueError("current and frozen Source25 target leaf differ")
    if sha(finite(HELPER)) != HELPER_SHA or finite(FROZEN / "xar_autoplayer/nonleading_player_realm_siege_v1.py") != finite(HELPER):
        raise ValueError("strict helper is not reviewed Source25 leaf")
    actual_raw = finite(FIXTURE)
    if sha(actual_raw) != FIXTURE_SHA:
        raise ValueError("portable actual fixture changed")
    ACTUAL = json.loads(gzip.decompress(actual_raw))
    MODELS = {"original": (original_tradeoff, original_construction)}
    diffs = {}
    previous = ORIGINALS
    for stage in ("guard", "procurement"):
        transformed = {relative: tx.transform(raw, relative, stage=stage) for relative, raw in ORIGINALS.items()}
        MODELS[stage] = tuple(module_from_ram(transformed[relative], relative) for relative in (tx.TRADEOFF, tx.CONSTRUCTION))
        diff = "".join("".join(difflib.unified_diff(previous[relative].decode().splitlines(True),
            transformed[relative].decode().splitlines(True), fromfile=f"{('original' if stage == 'guard' else 'guard')}/{relative}",
            tofile=f"{stage}/{relative}")) for relative in ORIGINALS)
        path = OUT / f"{stage}.patch"
        new(path, diff.encode("utf-8"))
        diffs[stage] = {"patch": reference(path), "outputs_RAM_only": {
            relative: {"bytes": len(raw), "sha256": sha(raw)} for relative, raw in transformed.items()}}
        previous = transformed
    buffer = io.StringIO()
    result = unittest.TextTestRunner(stream=buffer, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Qualification))
    new(OUT / "qualification.txt", buffer.getvalue().encode("utf-8"))
    fixtures = OUT / "synthetic-fixtures"
    fixture_account = account(fixtures)
    source_account = account(HERE)
    before_cleanup = account(OUT)
    # Owned synthetic child only; retained result/log/diff are never removed.
    if fixtures.resolve() != (OUT.resolve() / "synthetic-fixtures") or not fixtures.resolve().is_relative_to(OUT.resolve()):
        raise ValueError("owned fixture cleanup target mismatch")
    shutil.rmtree(fixtures)
    facts = Qualification.facts
    proof = {"schema": "xar.nonleading-realm-defence-cash-policy-qualification/v1",
        "machine_id": MACHINE, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "machine_source": "tools/ck3_live_run_id.py machine actual output",
        "status": "SOURCE_CANDIDATE_QUALIFIED_NOT_DEPLOYED" if result.wasSuccessful() else "FAILED_PRESERVED",
        "budget_card": reference(CARD), "source_parent_business_commit": "9b791aae9bb1314162aa5cab923e6cca2892e6d8",
        "target_preimages": {relative: reference(SRC / relative) for relative in tx.BASE},
        "strict_scope_helper": reference(HELPER), "stages": diffs,
        "fixture": {**reference(FIXTURE), "historical_machine_id": "unknown",
            "boundary": "Unmodified portable695 primary snapshot is actual; nonleading/stationary/realm and actionable WarDriver cases are explicitly synthetic."},
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "test_log": reference(OUT / "qualification.txt"), "facts": facts,
        "policy_boundary": [
            "guard stage defers optional construction for a current strictly qualified nonleading defensive siege even when the baseline ample-cash gate permits an outlay; procurement scope stays unchanged",
            "procurement stage explicitly adds that exact war to existing cash reasons and procurement focus; independent gameplay policy change, no performance credit",
            "all source targets compiled in RAM only; current Source25, SDK, Native and runtime untouched",
            "no new funding, refund, net income, legality, arrival, battle probability, movement or peace authority; original finance/pending/package/native-hire checks retained",
            "no Game/native/MCP/Task/desktop operation; no live adoption or land-retention credit"],
        "storage": {"source": source_account, "artifact_before_cleanup": before_cleanup,
            "owned_synthetic_fixture_peak": fixture_account, "synthetic_fixture_cleaned": not fixtures.exists(),
            "conservative_directory_and_result_overhead_reserved_bytes": 32768,
            "source_hard_bytes": 65536, "artifact_hard_bytes": 196608,
            "review_at_utc": card["review_at_utc"]}}
    encoded = (json.dumps(proof, ensure_ascii=False, indent=2) + "\n").encode()
    if source_account["allocated_file_bytes"] + source_account["directory_count"] * 4096 > 65536:
        raise ValueError("source allocated highwater exceeds lane")
    if before_cleanup["allocated_file_bytes"] + before_cleanup["directory_count"] * 4096 + len(encoded) + 32768 > 196608:
        raise ValueError("artifact highwater/result quote exceeds lane")
    new(OUT / "RESULT.json", encoded)
    print(json.dumps({"status": proof["status"], "tests_run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors),
        "result": reference(OUT / "RESULT.json"), "source": source_account,
        "artifacts_before_cleanup": before_cleanup}, ensure_ascii=False))
    raise SystemExit(0 if result.wasSuccessful() else 1)

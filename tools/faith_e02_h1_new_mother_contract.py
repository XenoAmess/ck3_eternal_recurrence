"""Explicit successor mother provenance and finite ordinary/promote case contract."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import sys
from typing import Literal

import faith_e02_h1_queue as Q
import faith_e02_demote_preparation_contract as D
# Select the adapter beside the selected demote contract, including an external
# source bundle. Do not require or extend the shared public host package path.
sys.path.insert(0, str(Path(D.__file__).resolve().parent / "ck3_mod_acceptance_cases"))
import faith_e02_demote_preparation_adapter as Preparation

MACHINE = D.MACHINE
SCHEMA = "faith-e02-h1-new-common-mother-case-v1"
MOTHER_SCHEMA = "faith-e02-h1-demoted-common-mother-v1"
ARM_SCHEMA = "faith-e02-h1-new-common-mother-arm-result-v1"
RESULT_SCHEMA: Literal["faith-e02-h1-new-common-mother-execution-result-v1"] = "faith-e02-h1-new-common-mother-execution-result-v1"
CASES: dict[Q.Arm, str] = {
    "ordinary": "faith-engine-e02-h1-new-mother-ordinary-v1",
    "promote": "faith-engine-e02-h1-new-mother-promote-h2-ghw-v1",
}
Stage = Literal["h1", "h2", "events", "h3", "done"]
MAX_CALLS = 128
GHW = "ck3_query_player_ghw_permissions_v1"
HOF_CONFIRM = "ck3_confirm_ingame_decision_outcome_v1"
EVENT_CONTEXT, EVENT_SELECT = "ck3_query_current_event_window_context_v1", "ck3_select_event_option"
READONLY = frozenset({Q.SITES, Q.RELIGION, Q.GOVERNANCE, Q.DETAIL, Q.COOLDOWN})
CULTURE = "same_immutable_mother_no_culture_mutator"


@dataclass(frozen=True)
class Mother:
    manifest: Q.Pin
    preparation: Q.Pin
    allocation: Q.Pin
    prepared: Q.Pin
    saved: D.SavedInput
    parent_saved: D.SavedInput
    parent_h2: Q.Pin
    ledger: Path
    disclosure: str
    membership: dict[str, bool]
    native_qualification: Q.Pin
    run_id: str


def preparation_source() -> Path:
    return Path(Preparation.__file__).resolve()


def field(value: Q.Obj, name: str) -> object:
    Q.require(name in value, "Missing required field: " + name)
    return value[name]


def exact_map(value: object) -> dict[str, bool]:
    source = Q.obj(value)
    result: dict[str, bool] = {}
    Q.require(0 < len(source) <= 64, "Complete bounded membership map required")
    for key, flag in source.items():
        Q.require(key.isascii() and key.isdecimal() and str(int(key)) == key and type(flag) is bool,
                  "Canonical site IDs and exact Boolean grades required")
        Q.integer(int(key))
        if not isinstance(flag, bool):
            raise ValueError("Grade is not Boolean")
        result[key] = flag
    return result


def saved_input(value: object, *, parent: bool = False) -> D.SavedInput:
    row = Q.obj(value)
    Q.require(set(row) == {"save", "bytes", "sha256", "player_id", "date_raw"}, "Explicit saved-input fields required")
    path = Path(Q.text(row["save"]))
    Q.require(path.is_absolute(), "Saved input must have an absolute path")
    sha = Q.text(row["sha256"])
    Q.require(len(sha) == 64 and all(c in "0123456789abcdef" for c in sha), "Canonical SHA-256 required")
    result: D.SavedInput = {"save": Q.text(row["save"]), "bytes": Q.integer(row["bytes"], 1, 2**53-1),
        "sha256": sha, "player_id": Q.integer(row["player_id"]),
        "date_raw": Q.integer(row["date_raw"], -(2**31), 2**31-1)}
    Q.require(result["player_id"] == D.ACTOR and result["date_raw"] == D.DATE, "Mother actor/date differs")
    if parent:
        Q.require(sha == Q.SAVE_SHA and result["bytes"] == 69030069, "Original de0f mother identity required")
    else:
        actual = Q.pin(path)
        Q.require(sha != Q.SAVE_SHA and actual["sha256"] == sha and actual["bytes"] == result["bytes"],
                  "Actual new saved file missing or changed")
    return result


def native_scene(value: object) -> Q.Scene:
    frame = Q.obj(value)
    actor = Q.obj(frame.get("played_character"))
    diagnostics = Q.obj(frame.get("diagnostics"))
    hello = Q.obj(diagnostics.get("hello"))
    executable_sha = Q.text(hello.get("expected_ck3_sha256"))
    Q.require(len(executable_sha) == 64 and all(c in "0123456789abcdefABCDEF" for c in executable_sha),
              "Exact hexadecimal executable identity required")
    Q.require(frame.get("source") == "injected-dll-named-pipe" and frame.get("backend_id") == "native-headless"
              and frame.get("episode_projection") == "native_campaign" and frame.get("paused") is True
              and frame.get("map_ready") is True and actor.get("alive") is True
              and hello.get("ck3_build_match") is True and hello.get("expected_ck3_version") == "1.20.0.4"
              and executable_sha.upper() == "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
              "Original paused Native frame and exact executable identity required")
    # The selected public opening_binding derives None for an absent optional
    # episode_run_id. Keep the original pinned raw frame unchanged.
    episode = frame.get("episode_run_id")
    Q.require(episode is None or type(episode) is str, "Episode identity must remain explicit")
    result: Q.Scene = {"played_character_id": Q.integer(actor.get("character_id")),
        "date_raw": Q.integer(frame.get("date_raw"), -(2**31), 2**31-1),
        "game_pid": Q.integer(hello.get("pid"), 1), "connection_generation": Q.integer(diagnostics.get("connection_generation"), 1, 2**53-1),
        "native_revision": Q.integer(frame.get("native_revision"), 1, 2**53-1),
        "episode_run_id": Q.text(episode) if episode is not None else None}
    Q.require(result["played_character_id"] == D.ACTOR and result["date_raw"] == D.DATE,
              "Original Native actor/date differs")
    return result


def same_scene(a: Q.Scene, b: Q.Scene) -> None:
    for key in ("played_character_id", "date_raw", "game_pid", "connection_generation", "episode_run_id"):
        Q.require(Q.encode(Q.obj(a)[key]) == Q.encode(Q.obj(b)[key]), "Source crossed the original preparation scene: " + key)


def intent(value: object, ledger: Path, run_id: str, action: D.Mutation) -> Q.Pin:
    ref = Q.checked_pin(value)
    Q.require(Path(ref["path"]).parent == ledger, "Preparation intent escaped original ledger")
    row = Q.read(Path(ref["path"]))
    scope: Q.Obj = {"machine_id": MACHINE, "saved_sha256": Q.SAVE_SHA, "played_character_id": D.ACTOR,
                   "action": action, "holy_site_id": 0}
    Q.require(row.get("schema") == "faith-e02-h1-preparation-once-intent-v1"
              and row.get("run_id") == run_id and row.get("unknown_must_never_replay") is True
              and Q.encode(row.get("scope")) == Q.encode(scope), "Original preparation intent identity differs")
    return ref


def load_mother(manifest_value: object, preparation_value: object) -> Mother:
    """Read actual preparation artifacts only; no missing/null or example fallback."""
    manifest_ref, preparation_ref = Q.checked_pin(manifest_value), Q.checked_pin(preparation_value)
    path, prep_path = Path(manifest_ref["path"]), Path(preparation_ref["path"])
    Q.require(path.name == "new-common-mother.json" and prep_path.name == "demote-preparation-result.json"
              and path.parent == prep_path.parent and path.parent.name == "case-output", "Use one actual public preparation output")
    m, p = Q.read(path), Q.read(prep_path)
    run_id = Q.text(m.get("run_id"))
    Q.require(m.get("schema") == MOTHER_SCHEMA and p.get("schema") == "faith-e02-h1-demote-preparation-result-v1"
              and m.get("machine_id") == p.get("machine_id") == MACHINE and p.get("run_id") == run_id
              and p.get("status") == "DEMOTED_AND_CHECKPOINT_MATERIALIZED"
              and Q.encode(Q.checked_pin(p.get("new_common_mother"))) == Q.encode(manifest_ref),
              "Actual completed preparation sidecar must bind the exact new manifest")
    for key, expected in (("demote_attempts", 1), ("save_attempts", 1), ("promote_submissions", 0), ("create_hof_submissions", 0)):
        Q.require(Q.integer(field(p, key)) == expected, "Preparation mutation count differs: " + key)
    Q.require(field(p, "demote_outcome_unknown") is False and field(p, "save_outcome_unknown") is False
              and field(m, "requires_two_new_independent_h1_restores") is True
              and field(m, "old_R16_not_a_comparison_arm") is True and field(m, "automatic_retry") is False
              and Q.integer(field(m, "hof_confirm_submissions")) == 0
              and field(m, "native_culture_observed") is False and field(m, "native_free_action_count_observed") is False,
              "Preparation remains unknown or lacks independent successor scope")
    saved, parent = saved_input(m.get("saved_input")), saved_input(m.get("parent_saved_input"), parent=True)
    Q.require(Path(saved["save"]).resolve() != Path(parent["save"]).resolve(), "New mother overwrote parent")
    parent_h2 = Q.checked_pin(m.get("parent_h2_case_contract"))
    old = Q.retained_h2(Q.read(Path(parent_h2["path"])))
    Q.require(Q.encode(old.get("saved_input")) == Q.encode(parent), "Parent H2 contract changed its original mother")
    ledger = Path(Q.text(m.get("once_ledger_root")))
    disclosure = Q.text(m.get("prior_setup_disclosure"))
    Q.require(ledger.is_absolute() and ledger.is_dir() and not ledger.is_symlink()
              and old.get("once_ledger_root") == str(ledger)
              and old.get("prior_setup_disclosure") == disclosure, "Original ledger/disclosure cannot change")
    identity = Q.obj(m.get("identity"))
    Q.require([Q.integer(identity.get(k)) for k in ("actor", "faith", "rite", "faith_main_rite")] == [D.ACTOR, D.FAITH, D.RITE, D.RITE]
              and field(identity, "head_holder") is None, "Actual known no-head identity required")
    membership = exact_map(m.get("faith_membership"))
    Q.require(sum(membership.values()) == Q.integer(m.get("main_membership_count")) == 2
              and membership.get("0") is False and membership.get("32") is False
              and field(m, "nadjaf32_eminent") is False, "Complete two-main-site ordinary-Nadjaf baseline required")
    demotion = Q.obj(m.get("demotion"))
    Q.require(Q.encode(demotion) == Q.encode(p.get("demotion"))
              and demotion.get("independent_demotion_observed") is True and demotion.get("payment_total_proven") is True,
              "Independent original demotion evidence required")
    before_map, after_map = exact_map(demotion.get("membership_before")), exact_map(demotion.get("membership_after"))
    D.membership_post(before_map, after_map)
    Q.require(after_map == membership, "Manifest disagrees with independent post-demotion grade")
    before, after = Q.obj(demotion.get("before")), Q.obj(demotion.get("after"))
    scene = native_scene(before)
    same_scene(scene, native_scene(after))
    from ck3_mod_acceptance_cases.faith_e02_h1_comparison_adapter import wallet, identity as heads
    cost = Q.vector(demotion.get("full10_quote"), promotion=True)
    Q.require(all(n == 0 for i, n in enumerate(cost) if i != 2) and cost[2] >= 0
              and Q.integer(demotion.get("actual_wallet_debit_raw"), 0, 2**63-1) == cost[2], "Actual piety-only demotion debit differs")
    old_wallet, new_wallet = wallet(before), wallet(after)
    Q.require(new_wallet == {**old_wallet, "piety": old_wallet["piety"] - cost[2]}, "Original demotion wallet readback differs")
    demote_ref = intent(demotion.get("intent"), ledger, run_id, "demote")
    save_ref = intent(m.get("save_intent"), ledger, run_id, "save-checkpoint")
    intent_refs = [Q.checked_pin(v) for v in Q.array(p.get("intents"))]
    Q.require(Q.encode(intent_refs) == Q.encode([demote_ref, save_ref]), "Preparation intents lost or reordered")
    allocation = Q.pin(path.parent.parent / "allocated-context.json")
    allocated = Q.read(Path(allocation["path"]))
    Q.require(allocated.get("schema") == "ck3-mod-acceptance-run-context-v1" and allocated.get("run_id") == run_id
              and allocated.get("case") == D.CASE and allocated.get("product") == "faith-engine"
              and Path(Q.text(allocated.get("run_dir"))).resolve() == path.parent.parent,
              "Materialized mother must come from its actual public preparation allocation")
    prepared_ref = Q.checked_pin(allocated.get("prepared_case"))
    prepared = Q.read(Path(prepared_ref["path"]))
    Q.require(prepared.get("case") == D.CASE, "Prepared allocation belongs to another case")
    preparation_contract = Q.read(Path(Q.checked_pin(prepared.get("contract"))["path"]))
    Q.require(preparation_contract.get("schema") == D.SCHEMA and preparation_contract.get("case") == D.CASE
              and Q.encode(preparation_contract.get("saved_input")) == Q.encode(parent)
              and Q.encode(preparation_contract.get("h2_case_contract")) == Q.encode(parent_h2)
              and preparation_contract.get("once_ledger_root") == str(ledger),
              "Actual prepared source must retain its original parent and once ledger")
    adapter_pin, selected_adapter = Q.checked_pin(prepared.get("adapter")), Q.pin(Path(Preparation.__file__))
    Q.require((adapter_pin["bytes"], adapter_pin["sha256"]) == (selected_adapter["bytes"], selected_adapter["sha256"]),
              "Mother preparation source differs from the selected exact demotion adapter")
    from ck3_mod_acceptance_cases.faith_e02_h1_comparison_adapter import cohort
    cohort(Q.read(Path(Q.checked_pin(prepared.get("runtime_manifest"))["path"])), m.get("native_qualification"))
    startup = Q.obj(prepared.get("startup"))
    save_dir = Path(Q.text(startup.get("state_dir"))) / "profile" / "save games"
    Q.require(Q.encode(D.materialized(m.get("save_receipt"), save_dir, Path(parent["save"]))) == Q.encode(saved),
              "New bytes do not match the original native materialized Save")
    rows: list[Q.Obj] = []
    for value_ref in Q.array(p.get("receipts")):
        ref = Q.checked_pin(value_ref)
        Q.require(Path(ref["path"]).parent == path.parent, "Foreign original preparation receipt")
        values = Q.array(Q.read(Path(ref["path"])).get("rows"))
        Q.require(len(values) == 1, "One original row per preparation receipt required")
        row = Q.obj(values[0])
        plan = Q.obj(row.get("plan"))
        tool = Q.text(plan.get("tool"))
        D.step(Q.text(row.get("id")), tool, Q.obj(plan.get("args")), consumed=tool in {D.CONFIRM, D.SAVE})
        Q.require(row.get("ok") is True and not row.get("error"), "Failed preparation row cannot qualify new mother")
        same_scene(scene, native_scene(row.get("after_snapshot")))
        rows.append(row)
    Q.require(1 <= len(rows) <= D.MAX_CALLS and Q.integer(p.get("public_calls"), 1) <= D.MAX_CALLS, "Preparation receipt/call cap differs")
    confirms = [i for i, r in enumerate(rows) if Q.obj(r["plan"]).get("tool") == D.CONFIRM]
    saves = [i for i, r in enumerate(rows) if Q.obj(r["plan"]).get("tool") == D.SAVE]
    Q.require(len(confirms) == len(saves) == 1 and confirms[0] < saves[0], "Exactly one original demote then Save required")
    Q.require(Q.encode(rows[confirms[0]].get("result")) == Q.encode(demotion.get("ack"))
              and Q.encode(rows[saves[0]].get("result")) == Q.encode(m.get("save_receipt")), "Original ACK or Save receipt changed")
    observed_sites: list[tuple[int, dict[str, bool]]] = []
    religions: list[Q.Obj] = []
    governances: list[Q.Obj] = []
    for i, row in enumerate(rows):
        tool, result = Q.text(Q.obj(row["plan"])["tool"]), Q.obj(row.get("result"))
        if tool == Q.SITES:
            observed_sites.append((i, Q.membership(result, D.FAITH)))
        elif tool == Q.RELIGION:
            religions.append(result)
        elif tool == Q.GOVERNANCE:
            governances.append(result)
    Q.require(any(i < confirms[0] and v == before_map for i, v in observed_sites)
              and any(confirms[0] < i < saves[0] and v == after_map for i, v in observed_sites)
              and any(i > saves[0] and v == after_map for i, v in observed_sites), "Original independent 3-to-2 and post-Save grade reads required")
    Q.require(bool(religions) and bool(governances)
              and Q.encode(heads(religions[0], governances[0])) == Q.encode(identity)
              and Q.encode(heads(religions[-1], governances[-1])) == Q.encode(identity), "Original independent identity/no-head reads differ")
    for governance in (governances[0], governances[-1]):
        Q.require(field(Q.obj(governance.get("heads")), "faith_religious_head_holder_character_id") is None,
                  "Original no-head cannot be an omitted/unknown holder field")
    precheck = Q.obj(m.get("promote32_readonly_precheck"))
    Q.require(precheck.get("action") == "promote" and Q.integer(precheck.get("site_id")) == 32
              and Q.encode(precheck) == Q.encode(p.get("promote32_readonly_precheck")), "Original readonly promotion precheck absent")
    Q.vector(precheck.get("native_resource_quote"), promotion=True)
    original_promote_details: list[Q.Obj] = []
    original_cooldowns: list[Q.Obj] = []
    for i, row in enumerate(rows):
        plan = Q.obj(row["plan"])
        args = Q.obj(plan.get("args"))
        if confirms[0] < i < saves[0] and args.get("action") == "promote":
            if plan.get("tool") == Q.DETAIL:
                original_promote_details.append(Q.obj(D.terms(row.get("result"), "promote", 32)))
            elif plan.get("tool") == Q.COOLDOWN:
                original_cooldowns.append(D.cooldown(row.get("result"), "promote"))
    Q.require(any(Q.encode(v) == Q.encode(precheck) for v in original_promote_details),
              "Promotion precheck must match an actual original Native detail row")
    D.cooldown(m.get("promote32_cooldown"), "promote")
    Q.require(Q.encode(m.get("promote32_cooldown")) == Q.encode(p.get("promote32_cooldown")), "Independent cooldown source differs")
    Q.require(any(Q.encode(v) == Q.encode(m.get("promote32_cooldown")) for v in original_cooldowns),
              "Inactive cooldown must match an actual independent original row")
    return Mother(manifest_ref, preparation_ref, allocation, prepared_ref, saved, parent, parent_h2,
                  ledger, disclosure, membership, Q.checked_pin(m.get("native_qualification")), run_id)


def required(branch: Q.Arm) -> frozenset[str]:
    basic = Q.READS | Q.PRESENT | Q.LIFECYCLE
    return frozenset(basic | ({Q.PROMOTE, HOF_CONFIRM, EVENT_CONTEXT, EVENT_SELECT, GHW} if branch == "promote" else set()))


def readonly(branch: Q.Arm) -> frozenset[str]:
    return READONLY | ({GHW} if branch == "promote" else set())


def action_scope(mother: Mother, action: Literal["promote", "create_hof"]) -> Q.Obj:
    return {"machine_id": MACHINE, "saved_sha256": mother.saved["sha256"], "played_character_id": D.ACTOR,
            "faith_id": D.FAITH, "action": action, "holy_site_id": 32 if action == "promote" else None}


def canonical_hof_key(mother: Mother) -> str:
    return hashlib.sha256((mother.saved["sha256"] + ":31254:103:" + Q.DECISION).encode("ascii")).hexdigest()


def reject_parent_hof_claim(mother: Mother) -> None:
    parent = hashlib.sha256((Q.SAVE_SHA + ":31254:103:" + Q.DECISION).encode("ascii")).hexdigest()
    Q.require(not (mother.ledger / (parent + ".claim.json")).exists()
              and not (mother.ledger / (parent + ".submit-once.json")).exists(),
              "Retained parent HoF claim requires reconciliation; new mother cannot bypass it")

"""Explicit major H1 -> one original H2 -> same-world read-only H3 product caller."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import importlib
from pathlib import Path
from typing import Literal, TypedDict

import faith_e02_h1_queue as Q
import faith_e02_hof_queue as HOF
import faith_e02_h1_h2_composite_queue as C
from ck3_mod_acceptance_cases import faith_e02_h1_comparison_adapter as H1
from ck3_mod_acceptance_cases.faith_e02_ghw_observation_contract import GhwObservation


class H2Outcome(TypedDict):
    status: Literal["not_submitted", "unknown", "observed"]
    confirm_dispatch_attempts: int
    original_claim: Q.Pin | None
    actual_confirm_row: Q.Obj | None
    quote_receipts: list[Q.Pin]
    full10_quote: Q.Obj | None
    wallet_before: C.Wallet | None
    wallet_delta_raw_after_minus_before: C.WalletDelta
    independent_post: C.H2Post | None
    head_creation_observed: bool
    wallet_observation_complete: bool
    gold_prestige_piety_observed: bool
    title_id: int | None
    holder_character_id: int | None
    holder_is_player: bool | None
    submission_outcome_unknown: bool
    quote_settlement_resource_index_join_verified: Literal[False]
    errors: dict[str, str]


class CompositeResult(TypedDict):
    schema: Literal["faith-e02-h1-h2-ghw-composite-result-v1"]
    machine_id: str
    run_id: str
    case: str
    status: str
    h1_arm_result: Q.Pin | None
    h2: H2Outcome | None
    event_policy: Q.Obj | None
    ghw_observation: GhwObservation | None
    h3_same_world_qualified: bool
    actual_public_calls: int
    hof_confirm_submissions: int
    ghw_launch_submissions: Literal[0]
    war_commands_submitted: Literal[0]
    business_pass: Literal[False]
    automatic_retry: Literal[False]
    error: str | None


def legacy_observation() -> C.LegacyObservation:
    value: object = importlib.import_module("ck3_mod_acceptance_cases.faith_e02_r19_ghw_adapter")
    if not isinstance(value, C.LegacyObservation):
        raise ValueError("Existing H2/H3 observation entry points unavailable")
    Q.require(Path(value.__file__).resolve().parent == Path(H1.__file__).resolve().parent,
        "H1 and H2/H3 must use the same selected public source")
    return value


def validate_contract(value: object) -> Q.Obj:
    context = Q.obj(value)
    c, spec = Q.obj(context.get("case_contract")), Q.obj(context.get("case_spec"))
    Q.require(c.get("schema") == C.SCHEMA and c.get("case") == context.get("case") == C.CASE
        and c.get("product") == context.get("product") == "faith-engine", "Explicit composite case identity required")
    original = Q.read(Path(Q.checked_pin(c.get("h1_phase_contract"))["path"]))
    Q.require(original.get("schema") == H1.SCHEMA and original.get("case") == H1.CASE
        and original.get("arm") == c.get("arm") == "promote", "Only original major H1 phase input is supported")
    for key in ("saved_input", "h2_case_contract", "once_ledger_root", "prior_setup_disclosure",
                "holy_site_id", "profile", "native_qualification", "native_culture_observed", "culture_control"):
        Q.require(Q.encode(c.get(key)) == Q.encode(original.get(key)), "Composite changed H1 phase input: " + key)
    saved = Q.obj(c.get("saved_input"))
    Q.require(set(saved) == {"save", "bytes", "sha256", "player_id", "date_raw"}
        and Q.integer(saved.get("bytes")) == 69030069 and saved.get("sha256") == Q.SAVE_SHA
        and Q.integer(saved.get("player_id")) == 31254 and Q.integer(saved.get("date_raw")) == 53144328
        and c.get("profile") == {"enabled_mods": [], "product_files": []}
        and c.get("machine_id") == "4-8e1c2f1861" and Q.integer(c.get("holy_site_id")) == 32
        and c.get("native_culture_observed") is False
        and c.get("culture_control") == "same_immutable_mother_no_culture_mutator", "Retained controlled H1 mother required")
    Q.require(Q.integer(c.get("max_public_calls")) == C.MAX_CALLS
        and Q.integer(original.get("max_public_calls")) == Q.MAX_CALLS
        and "create_hof_submissions" not in c
        and Q.integer(c.get("h1_hof_confirm_limit")) == 0 and Q.integer(c.get("h2_hof_confirm_limit")) == 1
        and c.get("confirm_once_when_ready") is True and Q.integer(c.get("max_confirm_submissions")) == 1
        and c.get("ghw_launch_confirmation_allowed") is False, "Finite once and observation limits differ")
    ledger = Path(Q.text(c.get("once_ledger_root")))
    h2 = Q.retained_h2(Q.read(Path(Q.checked_pin(c.get("h2_case_contract"))["path"])))
    Q.require(ledger.is_absolute() and ledger.is_dir() and not ledger.is_symlink()
        and str(ledger) == h2.get("once_ledger_root") == Q.obj(context.get("case_inputs")).get("once_ledger_root"),
        "Reuse the original retained H2 ledger; no new retry root")
    stage_caps = {stage: sorted(tools) for stage, tools in C.STAGE_TOOLS.items()}
    Q.require(Q.encode(c.get("stage_capabilities")) == Q.encode(stage_caps)
        and set(Q.text(x) for x in Q.array(spec.get("required_mcp_tools"))) == C.REQUIRED
        and set(Q.text(x) for x in Q.array(spec.get("opt_in_read_only_mcp_tools"))) == C.READONLY
        and all(spec.get(key) is False for key in H1.CLOSED), "Predeclare the exact stage union, with unrelated actions closed")
    plan = Q.read(Path(Q.text(spec.get("initial_plan"))))
    expected = {"steps": [Q.validate_step("h1-composite-initial-capabilities", "ck3_get_capabilities", {}, "promote", 32)]}
    Q.require(Q.encode(plan) == Q.encode(expected), "One declared capability read must be counted")
    old = legacy_observation()
    quoted = H1.selected_quotes()
    Q.require(Path(quoted.__file__).resolve() == Path(HOF.__file__).resolve(), "Shared HoF helper instance differs")
    needed = {Path(__file__).resolve(), Path(C.__file__).resolve(), Path(H1.__file__).resolve(),
        Path(Q.__file__).resolve(), Path(HOF.__file__).resolve(), Path(old.__file__).resolve()}
    Q.require(needed <= C.dependency_paths(c.get("dependencies")), "Pin the new caller and its actual reused source entry points")
    runtime = Q.read(Path(Q.checked_pin(context.get("runtime_manifest"))["path"]))
    H1.cohort(runtime, c.get("native_qualification"))
    return c


def prepare_case(value: object) -> Q.Obj:
    context = Q.obj(value)
    c = validate_contract(context)
    saved, inputs = Q.obj(c["saved_input"]), Q.obj(context["case_inputs"])
    Q.require(Q.encode(context.get("saved_campaign")) == Q.encode(saved), "Prepare selected another mother")
    path = Path(Q.text(saved["save"]))
    before = path.stat()
    actual = Q.pin(path)
    Q.require(actual["bytes"] == saved["bytes"] and actual["sha256"] == saved["sha256"]
        and path.stat().st_mtime_ns == before.st_mtime_ns, "Original immutable mother changed")
    grant = Q.read(Path(Q.checked_pin(inputs.get("storage_admission"))["path"]))
    expiry = datetime.fromisoformat(Q.text(grant.get("expires_at_utc")).replace("Z", "+00:00"))
    Q.require(grant.get("active") is True and grant.get("machine_id") == c["machine_id"]
        and expiry.tzinfo is not None and datetime.now(timezone.utc) < expiry, "Fresh scene admission required")
    module: object = importlib.import_module("ck3_mod_acceptance_prepare")
    if not isinstance(module, H1.Prepare):
        raise ValueError("Standard public preparation unavailable")
    profile = Q.obj(module.materialize_product_profile(context, None, inputs.get("configuration")))
    profile = Q.obj(module.finish_product_profile(context, profile, provenance={
        "machine_id": c["machine_id"], "kind": C.CASE, "saved_input": saved,
        "fresh_restore_observed": False, "preparation_mod_mounted": False,
        "h2_case_contract": c["h2_case_contract"], "h1_phase_contract": c["h1_phase_contract"],
        "prior_setup_disclosure": c["prior_setup_disclosure"], "native_culture_observed": False}))
    return {"startup": {"mode": "saved_campaign", "state_dir": profile["state_dir"],
        "saved_campaign": {**saved, "product_inventory": Q.obj(profile["product_inventory"])["path"]}},
        "profile": profile, "initial_plan": Q.obj(context["case_spec"])["initial_plan"],
        "runtime_status": "NOT_RUN", "business_pass": False}


class StageClient:
    """Count public calls and enforce stage scopes on the original public client."""
    def __init__(self, client: C.Client, context: Q.Obj) -> None:
        self.client, self.context = client, context
        self.operator_reviewer, self.manifest = client.operator_reviewer, client.manifest
        self.stage: C.Stage = "h1"
        self.calls, self.confirm_submissions = 1, 0
        self.h2_claim: Path | None = None
        self.selected_for_pair = False
        self.pair_queries = 0
        self.first_quote: Q.Obj | None = None
        self.quote_reviewed = False

    def enter(self, stage: C.Stage) -> None:
        allowed: dict[C.Stage, set[C.Stage]] = {"h1": {"h2", "done"}, "h2": {"events", "done"},
            "events": {"h3", "done"}, "h3": {"events", "done"}, "done": set()}
        Q.require(stage in allowed[self.stage], "Composite stage cannot rewind or retry")
        self.stage = stage

    def guard(self, reserve: float = 0) -> object:
        return self.client.guard(reserve)

    def budget(self, count: int) -> None:
        Q.require(self.calls + count <= C.MAX_CALLS, "Composite public-call cap reached")
        self.client.guard(120 + 300 + count * 20 + 20)

    def snapshot(self, *, require_event_free: bool = True) -> object:
        Q.require("ck3_take_snapshot" in C.STAGE_TOOLS[self.stage], "Snapshot is outside the current stage")
        self.budget(1)
        self.calls += 1
        return self.client.snapshot(require_event_free=require_event_free)

    def root_checkpoint(self, name: str, payload: Q.Obj, reserve: int = 120) -> object:
        result = Q.obj(self.client.root_checkpoint(name, payload, reserve=reserve))
        Q.require(result.get("run_id") == self.context["run_id"] and result.get("reviewer") == self.operator_reviewer
            and result.get("status") == "complete", "Actual current Root review not complete")
        return result

    def execute_plan(self, steps: list[Q.Obj], name: str, timeout: float | None = None,
                     reserve: int = 90) -> object:
        values = C.validate_steps(self.stage, steps)
        Q.require(type(reserve) is int and reserve == 90, "Use the actual public reserve90 boundary")
        self.budget(len(values))
        for row in values:
            tool, args = Q.text(row["tool"]), Q.obj(row["args"])
            if tool == HOF.CONFIRM:
                Q.require(self.confirm_submissions == 0 and self.h2_claim is not None,
                    "Original H2 claim required; unknown/used Confirm cannot replay")
                HOF.validate({"steps": values}, claim_path=self.h2_claim)
                self.confirm_submissions += 1  # Consume locally before the potentially unknown dispatch.
            if self.stage == "h1" and tool == HOF.QUERY and self.selected_for_pair and self.pair_queries == 1:
                Q.require(self.first_quote is not None and not self.quote_reviewed, "Unexpected extra selected quote")
                self.root_checkpoint("composite-major-hof-quote-review", {
                    "first_actual_quote": self.first_quote, "no_confirm_yet": True,
                    "next_step": "independent second quote; then original H2 once if still legal"})
                self.quote_reviewed = True
        self.calls += len(values)
        result = self.client.execute_plan(values, name, timeout=timeout, reserve=90)
        rows = Q.array(result)
        for step, raw in zip(values, rows):
            tool, args = Q.text(step["tool"]), Q.obj(step["args"])
            if self.stage == "h1" and tool == "ck3_select_ingame_decision_item_v1" and args.get("decision_key") == Q.DECISION:
                self.selected_for_pair, self.pair_queries = True, 0
            elif self.stage == "h1" and tool == HOF.QUERY and self.selected_for_pair:
                checked = Q.obj(raw)
                H1.hof_terms(checked)  # Real shared full10 / native legality consumer.
                self.pair_queries += 1
                if self.pair_queries == 1:
                    self.first_quote = checked
        return result


def wallet(frame: Q.Obj) -> C.Wallet:
    known = H1.wallet(frame)
    present = "played_character_treasury" in frame
    treasury = frame.get("played_character_treasury")
    raw: int | None = None
    if treasury is not None:
        coin = Q.obj(treasury)
        Q.require(Q.integer(coin.get("scale")) == Q.SCALE, "Treasury raw scale differs")
        raw = Q.integer(coin.get("raw"), -(2**63), 2**63-1)
    return {"gold": known["gold"], "prestige": known["prestige"], "piety": known["piety"],
        "treasury_field_present": present, "treasury_raw": raw}


def wallet_delta(before: C.Wallet | None, after: C.Wallet | None) -> C.WalletDelta:
    def difference(a: object, b: object) -> int | None:
        if type(a) is not int or type(b) is not int:
            return None
        delta = b - a
        return delta if -(2**63) <= delta <= 2**63-1 else None

    if before is None or after is None:
        return {"gold": None, "prestige": None, "piety": None, "treasury": None}
    return {"gold": difference(before["gold"], after["gold"]),
        "prestige": difference(before["prestige"], after["prestige"]),
        "piety": difference(before["piety"], after["piety"]),
        "treasury": difference(before["treasury_raw"], after["treasury_raw"])}


def one(client: StageClient, name: str, tool: str) -> Q.Obj:
    step: Q.Obj = {"id": name, "tool": tool, "args": {}, "fresh_revision": True, "continue_on_error": True}
    rows = Q.array(client.execute_plan([step], name, timeout=20, reserve=90))
    Q.require(len(rows) == 1, "One actual public result required")
    row = Q.obj(rows[0])
    Q.require(row.get("ok") is True and not row.get("error"), "Actual public observation failed: " + tool)
    return Q.obj(row.get("result"))


def major_h1(context: Q.Obj, c: Q.Obj, client: StageClient, opening: H1.Opening) -> tuple[H1.ArmRun, Q.Obj]:
    run = H1.ArmRun(context, client, c, opening)
    cohort = H1.cohort(client.manifest, c["native_qualification"])
    allocation = Q.pin(Path(Q.text(context["run_dir"])) / "allocated-context.json")
    allocated = Q.read(Path(allocation["path"]))
    Q.require(allocated.get("schema") == "ck3-mod-acceptance-run-context-v1"
        and allocated.get("case") == C.CASE and allocated.get("run_id") == run.run_id,
        "Use this actual composite allocation, never a forged H1 case alias")
    initial, heads = run.snapshot(), run.heads()
    sites = run.sites()
    Q.require(sites.get("32") is False, "Major arm must start at the same ordinary Nadjaf32")
    promotion = H1.promote_once(run, sites)
    quotes = run.quote_pair()  # Unchanged original producer; Root review is between its two query calls.
    Q.require(client.quote_reviewed and client.pair_queries == 2, "Exactly two reviewed independent major quotes required")
    final_sites = run.sites()
    expected = dict(sites)
    expected["32"] = True
    final_heads, final = run.heads(), run.snapshot()
    Q.require(final_sites == expected and H1.wallet(final) == H1.wallet(promotion["after"]),
        "H1 controls changed outside the one proven promotion")
    result: Q.Obj = {"schema": "faith-e02-h1-arm-result-v1", "machine_id": c["machine_id"],
        "run_id": run.run_id, "product_case": C.CASE, "phase": "h1", "arm": "promote", "holy_site_id": 32,
        "mother_sha256": Q.SAVE_SHA, "once_ledger_root": c["once_ledger_root"],
        "native_qualification": cohort["qualification"], "native_compile_source_commit": cohort["native_compile_source_commit"],
        "native_cohort": cohort, "native_culture_observed": False, "culture_control": c["culture_control"],
        "prior_setup_disclosure": c["prior_setup_disclosure"], "allocated_context": allocation,
        "identity_before": heads, "identity_after": final_heads, "scene": run.baseline,
        "membership_before": sites, "membership_final": final_sites, "wallet_initial": H1.wallet(initial),
        "promotion": promotion, "hof_quotes": quotes, "final_snapshot": final,
        "faith_membership_counts": {"ordinary": sum(not x for x in final_sites.values()), "eminent": sum(final_sites.values())},
        "counts_are_realm_controlled_qualifying_counts": False, "promotion_attempts": int(run.attempted),
        "promotion_outcome_unknown": run.unknown, "promotion_intent": run.intent,
        "public_calls": run.calls, "receipts": run.receipts, "hof_confirm_submissions": 0,
        "status": "QUOTED_NO_HOF_SUBMISSION", "business_pass": False}
    Q.write_once(run.output / "h1-arm-result.json", result)
    return run, result


def independent_post(client: StageClient, opening: H1.Opening, baseline: Q.Scene,
                     old: C.LegacyObservation) -> C.H2Post:
    post: C.H2Post = {"snapshot": None, "religion": None, "governance": None, "heads": None,
        "wallet": None, "errors": {}, "head_creation_observed": False}
    try:
        frame = Q.obj(client.snapshot(require_event_free=False))
        same_world(opening, baseline, frame)
        post["snapshot"], post["wallet"] = frame, wallet(frame)
    except Exception as error:
        post["errors"]["snapshot"] = type(error).__name__ + ": " + str(error)
    for field, tool in (("religion", Q.RELIGION), ("governance", Q.GOVERNANCE)):
        try:
            current = one(client, "composite-h2-" + field + "-after", tool)
            if field == "religion":
                post["religion"] = current
            else:
                post["governance"] = current
        except Exception as error:
            post["errors"][field] = type(error).__name__ + ": " + str(error)
    try:
        heads = Q.obj(old.require_identity(post["religion"] or {}, post["governance"] or {}, no_head=False))
        post["heads"] = heads
        Q.integer(heads.get("faith_religious_head_title_id"))
        Q.integer(heads.get("faith_religious_head_holder_character_id"))
        post["head_creation_observed"] = not post["errors"]
    except Exception as error:
        post["errors"]["heads"] = type(error).__name__ + ": " + str(error)
    return post


def same_world(opening: H1.Opening, baseline: Q.Scene, frame: object) -> None:
    current = Q.obj(opening.opening_binding(frame))
    original = Q.obj(baseline)
    for key in ("played_character_id", "date_raw", "game_pid", "connection_generation", "episode_run_id"):
        Q.require(Q.encode(current.get(key)) == Q.encode(original[key]), "Composite crossed the actual world: " + key)


def h2_once(context: Q.Obj, c: Q.Obj, client: StageClient, run: H1.ArmRun,
            arm: Q.Obj, old: C.LegacyObservation) -> H2Outcome:
    result: H2Outcome = {"status": "not_submitted", "confirm_dispatch_attempts": 0,
        "original_claim": None, "actual_confirm_row": None, "quote_receipts": [], "full10_quote": None,
        "wallet_before": None, "wallet_delta_raw_after_minus_before": wallet_delta(None, None),
        "independent_post": None, "head_creation_observed": False, "wallet_observation_complete": False,
        "gold_prestige_piety_observed": False, "title_id": None, "holder_character_id": None, "holder_is_player": None,
        "submission_outcome_unknown": False, "quote_settlement_resource_index_join_verified": False, "errors": {}}
    try:
        baseline = run.baseline
        if baseline is None:
            raise ValueError("Actual H1 scene absent")
        Q.require(run.branch == "promote" and arm.get("arm") == "promote"
            and arm.get("status") == "QUOTED_NO_HOF_SUBMISSION"
            and Q.integer(arm.get("hof_confirm_submissions")) == 0
            and Q.integer(arm.get("promotion_attempts")) == 1
            and not run.unknown and client.quote_reviewed, "Only resolved major H1 can enter H2")
        pre = Q.obj(client.snapshot())
        same_world(run.opening, baseline, pre)
        result["wallet_before"] = wallet(pre)
        Q.require(H1.wallet(pre) == H1.wallet(arm["final_snapshot"]), "Wallet changed after the major quote pair")
        religion = one(client, "composite-h2-religion-preconfirm", Q.RELIGION)
        governance = one(client, "composite-h2-governance-preconfirm", Q.GOVERNANCE)
        old.require_identity(religion, governance, no_head=True)
        quotes = Q.obj(arm["hof_quotes"])
        refs = [Q.checked_pin(x) for x in Q.array(quotes["quote_receipts"])]
        Q.require(len(refs) == 2, "Use only the major phase's two actual original quotes")
        result["quote_receipts"] = refs
        terms = [Q.obj(value) for value in Q.array(quotes.get("terms"))]
        Q.require(len(terms) == 2, "Actual two major terms required")
        result["full10_quote"] = Q.obj(terms[1].get("resource_quote"))
        Q.vector(result["full10_quote"])
        intent = hashlib.sha256((Q.SAVE_SHA + ":31254:103:" + Q.DECISION).encode("ascii")).hexdigest()
        claim: Q.Obj = {"schema": "faith-e02-R19-hof-once-claim-v1", "machine_id": c["machine_id"],
            "run_id": context["run_id"], "actor": 31254, "faith": 103, "date_raw": 53144328,
            "decision_key": Q.DECISION, "intent_key": intent, "once_ledger_root": c["once_ledger_root"],
            "quote_receipts": refs, "unknown_must_not_repeat": True}
        HOF.verify_quote_pair(claim)
        path = Path(Q.text(c["once_ledger_root"])) / (intent + ".claim.json")
        client.budget(4)  # Admit only with room for dispatch and the three independent post reads.
        Q.write_once(path, claim)  # Original stable root and original intent; no restore/run/PID retry scope.
        result["original_claim"] = Q.pin(path)
        step: Q.Obj = {"id": "composite-h2-confirm-once", "tool": HOF.CONFIRM,
            "args": {"decision_key": Q.DECISION, "expected_outcome": "decision_closed"},
            "fresh_revision": True, "continue_on_error": True}
        HOF.admit_confirm({"steps": [step]}, path)
        client.h2_claim = path
        result["confirm_dispatch_attempts"] = 1
        result["submission_outcome_unknown"] = True
        try:
            rows = Q.array(client.execute_plan([step], "composite-h2-confirm-once", timeout=20, reserve=90))
            Q.require(len(rows) == 1, "One original Confirm result required")
            result["actual_confirm_row"] = Q.obj(rows[0])
        except Exception as error:
            result["errors"]["dispatch"] = type(error).__name__ + ": " + str(error)
        post = independent_post(client, run.opening, baseline, old)
        result["independent_post"] = post
        result["head_creation_observed"] = post["head_creation_observed"]
        result["gold_prestige_piety_observed"] = post["wallet"] is not None
        delta = wallet_delta(result["wallet_before"], post["wallet"])
        result["wallet_delta_raw_after_minus_before"] = delta
        result["wallet_observation_complete"] = all(value is not None for value in delta.values())
        if post["head_creation_observed"] and post["heads"] is not None:
            result["title_id"] = Q.integer(post["heads"].get("faith_religious_head_title_id"))
            holder = Q.integer(post["heads"].get("faith_religious_head_holder_character_id"))
            result["holder_character_id"], result["holder_is_player"] = holder, holder == 31254
            result["submission_outcome_unknown"] = False
            result["status"] = "observed"
        else:
            result["status"] = "unknown"
    except Exception as error:
        result["errors"]["precondition"] = type(error).__name__ + ": " + str(error)
    Q.write_once(Path(Q.text(context["output"])) / "composite-h2-independent-poststate.json", result)
    return result


def run_case(value: object, client: C.Client) -> CompositeResult:
    context = Q.obj(value)
    c = validate_contract(context)
    opening, old = H1.selected_opening(context), legacy_observation()
    facade = StageClient(client, context)
    result: CompositeResult = {"schema": "faith-e02-h1-h2-ghw-composite-result-v1",
        "machine_id": Q.text(c["machine_id"]), "run_id": Q.text(context["run_id"]), "case": C.CASE,
        "status": "PARTIAL", "h1_arm_result": None, "h2": None, "event_policy": None,
        "ghw_observation": None, "h3_same_world_qualified": False, "actual_public_calls": 1,
        "hof_confirm_submissions": 0, "ghw_launch_submissions": 0, "war_commands_submitted": 0,
        "business_pass": False, "automatic_retry": False, "error": None}
    try:
        run, arm = major_h1(context, c, facade, opening)
        result["h1_arm_result"] = Q.pin(run.output / "h1-arm-result.json")
        baseline = run.baseline
        if baseline is None:
            raise ValueError("Actual H1 scene absent")
        facade.enter("h2")
        h2 = h2_once(context, c, facade, run, arm, old)
        result["h2"] = h2
        facade.enter("events")
        frame = Q.obj(facade.snapshot(require_event_free=False))
        same_world(opening, baseline, frame)

        def reader(current: object) -> Mapping[str, object]:
            return Q.obj(opening.opening_binding(current))

        binding = Q.obj(baseline)
        event = Q.obj(old.drain_current_events(context, facade, frame, binding, reader, phase="composite-h2-post"))
        result["event_policy"] = event
        Q.require(event.get("status") == "DRAINED", "Unresolved event preserves H2 evidence; no blind H3 continuation")
        facade.enter("h3")
        ghw = old.observe_ghw(context, facade, binding, reader)
        result["ghw_observation"] = ghw
        final = Q.obj(facade.snapshot(require_event_free=False))
        same_world(opening, baseline, final)
        Q.require(final.get("active_event") is None, "New actual event invalidates the paired H3 group")
        result["h3_same_world_qualified"] = ghw["current_group_qualified"]
        result["status"] = "H1_QUOTED_H2_" + h2["status"].upper()
    except Exception as error:
        result["error"] = type(error).__name__ + ": " + str(error)
    if facade.stage != "done":
        facade.enter("done")
    result["actual_public_calls"], result["hof_confirm_submissions"] = facade.calls, facade.confirm_submissions
    Q.write_once(Path(Q.text(context["output"])) / "h1-h2-ghw-composite-result.json", result)
    return result


def verify_case(value: object) -> Q.Obj:
    context = Q.obj(value)
    validate_contract(context)
    result = Q.read(Path(Q.text(context["output"])) / "h1-h2-ghw-composite-result.json")
    Q.require(result.get("case") == C.CASE and result.get("run_id") == context["run_id"], "Composite result identity differs")
    return {"business_pass": False, "whole_product_acceptance_credit": False,
        "h1_quoted": result.get("h1_arm_result") is not None,
        "h2_head_creation_observed": Q.obj(result.get("h2") or {}).get("head_creation_observed") is True,
        "h3_same_world_qualified": result.get("h3_same_world_qualified") is True,
        "automatic_retry": False}


def make_metadata(original_major_fragment: Path, output: Path) -> None:
    """Metadata-only CLI; no prepare, allocation, host or game calls."""
    original_spec = Q.read(original_major_fragment)
    previous = Q.obj(original_spec.get("adapter"))
    phase_path = Path(Q.text(previous.get("config")))
    original = Q.read(phase_path)
    Q.require(original.get("schema") == H1.SCHEMA and original.get("case") == H1.CASE
        and original.get("arm") == "promote", "Select a freshly produced original major H1 fragment")
    Q.require(not output.exists(), "New composite metadata directory required")
    old = legacy_observation()
    quoted = H1.selected_quotes()
    c: Q.Obj = {**original, "schema": C.SCHEMA, "case": C.CASE,
        "h1_phase_contract": Q.pin(phase_path), "max_public_calls": C.MAX_CALLS,
        "confirm_once_when_ready": True, "max_confirm_submissions": 1,
        "h1_hof_confirm_limit": 0, "h2_hof_confirm_limit": 1,
        "ghw_launch_confirmation_allowed": False,
        "stage_capabilities": {stage: sorted(tools) for stage, tools in C.STAGE_TOOLS.items()},
        "dependencies": [Q.pin(Path(path)) for path in (__file__, C.__file__, H1.__file__, Q.__file__,
                                                        quoted.__file__, old.__file__)]}
    c.pop("create_hof_submissions", None)  # The original zero belongs to the pinned H1 sub-contract only.
    output.mkdir(parents=True, exist_ok=False)
    config, plan = output / "case-contract.json", output / "initial-plan.json"
    Q.write_once(config, c)
    Q.write_once(plan, {"steps": [Q.validate_step("h1-composite-initial-capabilities", "ck3_get_capabilities", {}, "promote", 32)]})
    spec: Q.Obj = {**original_spec, "id": C.CASE,
        "adapter": {"module": "tools.ck3_mod_acceptance_cases.faith_e02_h1_h2_composite_adapter", "config": str(config)},
        "initial_plan": str(plan), "required_mcp_tools": sorted(C.REQUIRED),
        "opt_in_read_only_mcp_tools": sorted(C.READONLY), **{name: False for name in H1.CLOSED},
        "business_contract_applicable": False, "whole_product_acceptance_credit": False}
    Q.write_once(output / "case-fragment.json", spec)



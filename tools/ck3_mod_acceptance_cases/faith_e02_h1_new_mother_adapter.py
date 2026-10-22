"""Two fresh successor-mother arms; only promoted arm continues once to H2/H3."""
from __future__ import annotations
from ck3_mod_acceptance_saved_profile_v2 import materialize_saved_profile_v2

from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import importlib
from pathlib import Path
from typing import Literal, TypedDict

import faith_e02_h1_queue as Q
import faith_e02_hof_queue as HOF
import faith_e02_demote_preparation_contract as D
import faith_e02_h1_new_mother_contract as N
import faith_e02_h1_h2_composite_queue as C
from ck3_mod_acceptance_cases import faith_e02_h1_comparison_adapter as H
from ck3_mod_acceptance_cases import faith_e02_h1_h2_composite_adapter as G


State = Literal["PARTIAL", "H1_QUOTED", "H1_QUOTED_H2_OBSERVED", "H1_QUOTED_H2_UNKNOWN", "H1_QUOTED_H2_NOT_SUBMITTED"]


class Execution(TypedDict):
    schema: Literal["faith-e02-h1-new-common-mother-execution-result-v1"]
    machine_id: str
    run_id: str
    case: str
    arm: Q.Arm
    status: State
    h1_arm_result: Q.Pin | None
    h2: G.H2Outcome | None
    events: Q.Obj | None
    h3: Q.Obj | None
    actual_public_calls: int
    hof_confirm_submissions: int
    promotion_submissions: int
    promotion_outcome_unknown: bool
    promotion_intent: Q.Pin | None
    ghw_launch_submissions: int
    war_commands_submitted: int
    automatic_retry: bool
    business_pass: bool
    error: str | None


def source_paths() -> set[Path]:
    old = G.legacy_observation()
    return {Path(p).resolve() for p in (__file__, N.__file__, D.__file__, N.preparation_source(), Q.__file__, HOF.__file__,
                                       H.__file__, G.__file__, C.__file__, old.__file__)}


def known_identity(religion: object, governance: object) -> Q.Obj:
    heads = Q.obj(Q.obj(governance).get("heads"))
    Q.require(N.field(heads, "faith_religious_head_holder_character_id") is None,
              "Known no-head observation required; omitted is not null")
    return H.identity(religion, governance)


def known_heads(run: H.ArmRun) -> Q.Obj:
    return known_identity(run.result(Q.RELIGION), run.result(Q.GOVERNANCE))


def validate_contract(context_value: object) -> Q.Obj:
    context = Q.obj(context_value)
    c, spec = Q.obj(context.get("case_contract")), Q.obj(context.get("case_spec"))
    branch = Q.arm(c.get("arm"))
    Q.require(c.get("schema") == N.SCHEMA and c.get("case") == context.get("case") == N.CASES[branch]
              and c.get("product") == context.get("product") == "faith-engine" and c.get("machine_id") == N.MACHINE,
              "Explicit new-mother case identity required; old contracts cannot alias it")
    mother = N.load_mother(c.get("new_common_mother"), c.get("preparation_result"))
    Q.require(Q.encode(c.get("saved_input")) == Q.encode(mother.saved)
              and Q.encode(c.get("parent_h2_case_contract")) == Q.encode(mother.parent_h2)
              and c.get("once_ledger_root") == str(mother.ledger)
              and Q.obj(context.get("case_inputs")).get("once_ledger_root") == str(mother.ledger)
              and c.get("prior_setup_disclosure") == mother.disclosure,
              "New saved input, original parent, ledger and disclosure must remain explicit")
    Q.require(c.get("profile") == {"enabled_mods": [], "product_files": []}
              and Q.integer(c.get("holy_site_id")) == 32 and c.get("native_culture_observed") is False
              and c.get("culture_control") == N.CULTURE and Q.integer(c.get("max_public_calls")) == N.MAX_CALLS
              and Q.integer(c.get("h1_public_call_cap")) == Q.MAX_CALLS
              and Q.integer(c.get("promotion_limit")) == (1 if branch == "promote" else 0)
              and Q.integer(c.get("hof_confirm_limit")) == (1 if branch == "promote" else 0)
              and Q.integer(c.get("h3_readonly_limit")) == (2 if branch == "promote" else 0)
              and c.get("ghw_launch_confirmation_allowed") is False and Q.integer(c.get("war_command_limit")) == 0,
              "Finite vanilla branch limits differ")
    Q.require(set(Q.text(x) for x in Q.array(spec.get("required_mcp_tools"))) == N.required(branch)
              and set(Q.text(x) for x in Q.array(spec.get("opt_in_read_only_mcp_tools"))) == N.readonly(branch)
              and all(spec.get(flag) is False for flag in H.CLOSED), "Public tool union differs")
    initial = {"steps": [Q.validate_step("h1-new-mother-initial-capabilities", "ck3_get_capabilities", {}, branch, 32)]}
    Q.require(Q.encode(Q.read(Path(Q.text(spec.get("initial_plan"))))) == Q.encode(initial), "One declared capability call required")
    refs = {Path(Q.checked_pin(v)["path"]).resolve() for v in Q.array(c.get("dependencies"))}
    Q.require(source_paths() <= refs, "Pin all actual successor and reused source entry points")
    H.cohort(Q.read(Path(Q.checked_pin(context.get("runtime_manifest"))["path"])), c.get("native_qualification"))
    H.selected_quotes()
    return c


def prepare_case(context_value: object) -> Q.Obj:
    context = Q.obj(context_value)
    c = validate_contract(context)
    saved = Q.obj(c["saved_input"])
    Q.require(Q.encode(context.get("saved_campaign")) == Q.encode(saved), "Prepare selected a different successor mother")
    inputs = Q.obj(context["case_inputs"])
    grant = Q.read(Path(Q.checked_pin(inputs.get("storage_admission"))["path"]))
    expiry = datetime.fromisoformat(Q.text(grant.get("expires_at_utc")).replace("Z", "+00:00"))
    Q.require(grant.get("active") is True and grant.get("machine_id") == N.MACHINE
              and expiry.tzinfo is not None and datetime.now(timezone.utc) < expiry, "Fresh full scene admission required")
    module: object = importlib.import_module("ck3_mod_acceptance_prepare")
    if not isinstance(module, H.Prepare):
        raise ValueError("Actual public preparation entry points unavailable")
    profile = Q.obj(materialize_saved_profile_v2(context, None, inputs.get("configuration"), source_role=None))
    profile = Q.obj(module.finish_product_profile(context, profile, provenance={
        "machine_id": N.MACHINE, "kind": c["case"], "saved_input": saved,
        "new_common_mother": c["new_common_mother"], "preparation_result": c["preparation_result"],
        "parent_h2_case_contract": c["parent_h2_case_contract"], "prior_setup_disclosure": c["prior_setup_disclosure"],
        "fresh_restore_observed": False, "preparation_mod_mounted": False, "native_culture_observed": False}))
    return {"startup": {"mode": "saved_campaign", "state_dir": profile["state_dir"],
            "saved_campaign": {**saved, "product_inventory": Q.obj(profile["product_inventory"])["path"]}},
            "profile": profile, "initial_plan": Q.obj(context["case_spec"])["initial_plan"],
            "runtime_status": "NOT_RUN", "business_pass": False}


class StageClient:
    """Use the original public client; never create a host or rename its case."""
    def __init__(self, client: C.Client, context: Q.Obj, branch: Q.Arm) -> None:
        self.client, self.context, self.branch = client, context, branch
        self.operator_reviewer, self.manifest = client.operator_reviewer, client.manifest
        self.stage: N.Stage = "h1"
        self.calls, self.confirm_submissions, self.ghw_reads = 1, 0, 0
        self.h2_claim: Path | None = None
        self.promotion_claim: Path | None = None
        self.promotion_submissions = 0
        self.selected_for_pair, self.quote_reviewed = False, False
        self.pair_queries = 0
        self.first_quote: Q.Obj | None = None

    def enter(self, stage: N.Stage) -> None:
        allowed: dict[N.Stage, set[N.Stage]] = {"h1": {"h2", "done"}, "h2": {"events", "done"},
            "events": {"h3", "done"}, "h3": {"done"}, "done": set()}
        Q.require(stage in allowed[self.stage] and (self.branch == "promote" or stage == "done"), "Stage cannot rewind or cross ordinary arm")
        self.stage = stage

    def guard(self, reserve: float = 0) -> object:
        return self.client.guard(reserve)

    def budget(self, count: int) -> None:
        Q.require(self.calls + count <= N.MAX_CALLS, "Finite successor call cap exhausted")
        self.client.guard(120 + 300 + count * 20 + 20)

    def snapshot(self, *, require_event_free: bool = True) -> object:
        Q.require(self.stage != "done", "No reads after caller closure")
        self.budget(1)
        self.calls += 1
        return self.client.snapshot(require_event_free=require_event_free)

    def root_checkpoint(self, name: str, payload: Q.Obj, reserve: int = 120) -> object:
        value = Q.obj(self.client.root_checkpoint(name, payload, reserve=reserve))
        Q.require(value.get("run_id") == self.context["run_id"] and value.get("reviewer") == self.operator_reviewer
                  and value.get("status") == "complete", "Actual current Root review required")
        return value

    def execute_plan(self, steps: list[Q.Obj], name: str, timeout: float | None = None, reserve: int = 90) -> object:
        Q.require(len(steps) == 1 and reserve == 90 and self.stage != "done", "One finite public step required")
        step = Q.obj(steps[0])
        tool, args, sid = Q.text(step.get("tool")), Q.obj(step.get("args")), Q.text(step.get("id"))
        Q.require(step.get("fresh_revision") is True and step.get("continue_on_error") is True, "Fresh public step required")
        self.budget(1)
        if self.stage == "h1":
            Q.validate_step(sid, tool, args, self.branch, 32, claimed_promote=self.promotion_claim is not None)
            if tool == Q.PROMOTE:
                Q.require(self.promotion_claim is not None and self.promotion_submissions == 0,
                          "Original retained promotion claim required before one dispatch")
                if self.promotion_claim is None:
                    raise ValueError("Promotion claim absent")
                claim = Q.read(self.promotion_claim)
                c = Q.obj(self.context["case_contract"])
                scope = Q.obj(claim.get("scope"))
                Q.require(self.promotion_claim.parent == Path(Q.text(c["once_ledger_root"]))
                          and claim.get("schema") == "faith-e02-h1-new-mother-promote-intent-v1"
                          and claim.get("run_id") == self.context["run_id"] and claim.get("unknown_must_never_replay") is True
                          and scope.get("saved_sha256") == Q.obj(c["saved_input"])["sha256"]
                          and scope.get("action") == "promote" and Q.integer(scope.get("holy_site_id")) == 32,
                          "Actual promotion claim identity differs")
                self.promotion_submissions += 1
        elif self.stage == "h2":
            Q.require(tool in {Q.RELIGION, Q.GOVERNANCE, N.HOF_CONFIRM}, "H2 permits only actual heads and one original Confirm")
            if tool == N.HOF_CONFIRM:
                Q.require(self.confirm_submissions == 0 and self.h2_claim is not None, "Consumed or unknown H2 cannot replay")
                HOF.validate({"steps": steps}, claim_path=self.h2_claim)
                self.confirm_submissions += 1
            else:
                Q.require(not args, "H2 identity read has no extra arguments")
        elif self.stage == "events":
            Q.require(tool in {N.EVENT_CONTEXT, N.EVENT_SELECT}, "Only bounded original first-option event handling")
            Q.integer(args.get("event_instance_id"), 1)
            if tool == N.EVENT_SELECT:
                Q.integer(args.get("option_number"), 1, 64)
        else:
            Q.require(tool == N.GHW and not args and self.ghw_reads < 2, "H3 is exactly two readonly permissions calls")
            self.ghw_reads += 1
        if self.stage == "h1" and tool == Q.QUERY and self.selected_for_pair and self.pair_queries == 1:
            Q.require(self.first_quote is not None and not self.quote_reviewed, "Unexpected extra HoF quote")
            self.root_checkpoint("new-mother-hof-quote-review", {"first_actual_quote": self.first_quote,
                "no_confirm_yet": True, "new_common_mother": Q.obj(self.context["case_contract"])["new_common_mother"]})
            self.quote_reviewed = True
        self.calls += 1
        rows = Q.array(self.client.execute_plan(steps, name, timeout=timeout, reserve=90))
        Q.require(len(rows) == 1, "One original public result required")
        if self.stage == "h1" and tool == "ck3_select_ingame_decision_item_v1":
            self.selected_for_pair, self.pair_queries = True, 0
        elif self.stage == "h1" and tool == Q.QUERY and self.selected_for_pair:
            row = Q.obj(rows[0])
            H.hof_terms(row)
            self.pair_queries += 1
            if self.pair_queries == 1:
                self.first_quote = row
        return rows


def promote_once(run: H.ArmRun, mother: N.Mother, before_sites: dict[str, bool], client: StageClient) -> Q.Obj:
    H.ensure_promotion_site_window(run)
    target: Q.Obj = {"action": "promote", "holy_site_id": 32}
    run.result("ck3_open_holy_site_decision_v1", target)
    raw_first = run.result(Q.DETAIL, target)
    first, detailed = H.promotion_terms(raw_first, 32), D.terms(raw_first, "promote", 32)
    cooldown = D.cooldown(run.result(Q.COOLDOWN, {"action": "promote"}), "promote")
    digest = hashlib.sha256(Q.encode(first).encode()).hexdigest()
    review = Q.obj(run.client.root_checkpoint("new-mother-promote-original-five-fields-review", {
        "native_observation": first, "native_observation_sha256": digest,
        "approval_key": "promote_once_authorized", "prepare_original_image": True,
        "membership_before": before_sites, "cooldown": cooldown, "new_common_mother": mother.manifest}, reserve=120))
    Q.require(review.get("run_id") == run.run_id and review.get("reviewer") == run.client.operator_reviewer
              and review.get("status") == "complete" and review.get("original_image_directly_reviewed") is True
              and review.get("promote_once_authorized") is True and review.get("reviewed_native_observation_sha256") == digest,
              "Original PNG and exact five native fields must be reviewed")
    image = Q.checked_pin(review.get("original_image"))
    Q.require(Path(image["path"]).read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), "Actual original PNG required")
    before = run.snapshot()
    raw_second = run.result(Q.DETAIL, target)
    second = H.promotion_terms(raw_second, 32)
    D.stable_terms(detailed, D.terms(raw_second, "promote", 32))
    D.cooldown(run.result(Q.COOLDOWN, {"action": "promote"}), "promote")
    Q.require(Q.encode(first) == Q.encode(second) and run.sites() == before_sites == mother.membership,
              "Reviewed quote, selected token or two-main-site baseline changed")
    known_heads(run)
    Q.require(H.wallet(run.snapshot()) == H.wallet(before), "Wallet changed before the one promotion")
    N.reject_parent_hof_claim(mother)
    scope = N.action_scope(mother, "promote")
    root = mother.ledger
    path = root / (hashlib.sha256(Q.encode(scope).encode()).hexdigest() + ".new-h1-promote.intent.json")
    run.guard(8)
    run.unknown = True
    Q.reject_existing_promotion(root, scope)
    Q.write_once(path, {"schema": "faith-e02-h1-new-mother-promote-intent-v1", "scope": scope,
        "parent_saved_sha256": Q.SAVE_SHA, "new_common_mother": mother.manifest, "run_id": run.run_id,
        "scene": run.baseline, "review": review, "exact_native_five_fields": second,
        "exact_native_five_fields_sha256": digest, "unknown_must_never_replay": True})
    run.attempted, run.intent = True, Q.pin(path)
    client.promotion_claim = path
    ack = run.call(Q.PROMOTE, target, claimed=True)
    after_sites, after = run.sites(), run.snapshot()
    expected = dict(before_sites)
    expected["32"] = True
    old_wallet, new_wallet = H.wallet(before), H.wallet(after)
    debit = {key: old_wallet[key] - new_wallet[key] for key in ("gold", "prestige", "piety")}
    raw = Q.vector(second["native_resource_quote"], promotion=True)
    Q.require(after_sites == expected and sum(after_sites.values()) == 3
              and [debit[k] for k in ("gold", "prestige", "piety")] == raw[:3]
              and all(v == 0 for v in raw[3:]), "Independent exact 2-to-3 and wallet debit missing; never replay")
    run.unknown = False
    proof: Q.Obj = {"intent": Q.pin(path), "ack": ack, "before": before, "after": after,
        "membership_before": before_sites, "membership_after": after_sites,
        "full10_quote": second["native_resource_quote"], "actual_wallet_debit_raw": debit,
        "payment_total_proven": True, "independent_promotion_observed": True,
        "exact_native_five_fields_sha256": digest, "Root_review": review}
    Q.write_once(run.output / "new-mother-promotion-independent-post.json", proof)
    return proof


def one(client: StageClient, name: str, tool: str) -> Q.Obj:
    rows = Q.array(client.execute_plan([{"id": name, "tool": tool, "args": {},
        "fresh_revision": True, "continue_on_error": True}], name, timeout=20, reserve=90))
    row = Q.obj(rows[0])
    Q.require(row.get("ok") is True and not row.get("error"), "Actual independent read failed")
    return Q.obj(row.get("result"))


def independent_post(client: StageClient, run: H.ArmRun) -> C.H2Post:
    post: C.H2Post = {"snapshot": None, "religion": None, "governance": None, "heads": None, "wallet": None,
        "errors": {}, "head_creation_observed": False}
    baseline = run.baseline
    if baseline is None:
        raise ValueError("Actual scene absent")
    try:
        frame = Q.obj(client.snapshot(require_event_free=False))
        G.same_world(run.opening, baseline, frame)
        post["snapshot"], post["wallet"] = frame, G.wallet(frame)
    except Exception as error:
        post["errors"]["snapshot"] = type(error).__name__ + ": " + str(error)
    for key, tool in (("religion", Q.RELIGION), ("governance", Q.GOVERNANCE)):
        try:
            result = one(client, "new-mother-h2-" + key + "-after", tool)
            if key == "religion":
                post["religion"] = result
            else:
                post["governance"] = result
        except Exception as error:
            post["errors"][key] = type(error).__name__ + ": " + str(error)
    try:
        religion, governance = Q.obj(post["religion"]), Q.obj(post["governance"])
        heads = Q.obj(governance.get("heads"))
        Q.require(religion.get("available") is True and governance.get("frame_available") is True and heads.get("available") is True,
                  "Independent actual head components missing")
        for value, fields in ((religion, ("played_character_id", "faith_id", "rite_id", "faith_main_rite_id")),
                              (heads, ("played_character_id", "faith_id", "actor_rite_id", "faith_main_rite_id"))):
            Q.require([Q.integer(value.get(k)) for k in fields] == [D.ACTOR, D.FAITH, D.RITE, D.RITE], "Head recipient Faith/Rite changed")
        Q.integer(heads.get("faith_religious_head_title_id"), 1)
        Q.integer(heads.get("faith_religious_head_holder_character_id"), 1)
        post["heads"], post["head_creation_observed"] = heads, not post["errors"]
    except Exception as error:
        post["errors"]["heads"] = type(error).__name__ + ": " + str(error)
    return post


def h2_once(context: Q.Obj, client: StageClient, run: H.ArmRun, arm: Q.Obj, mother: N.Mother) -> G.H2Outcome:
    result: G.H2Outcome = {"status": "not_submitted", "confirm_dispatch_attempts": 0, "original_claim": None,
        "actual_confirm_row": None, "quote_receipts": [], "full10_quote": None, "wallet_before": None,
        "wallet_delta_raw_after_minus_before": G.wallet_delta(None, None), "independent_post": None,
        "head_creation_observed": False, "wallet_observation_complete": False, "gold_prestige_piety_observed": False,
        "title_id": None, "holder_character_id": None, "holder_is_player": None, "submission_outcome_unknown": False,
        "quote_settlement_resource_index_join_verified": False, "errors": {}}
    try:
        baseline = run.baseline
        if baseline is None:
            raise ValueError("Actual promoted scene absent")
        Q.require(run.attempted and not run.unknown and arm.get("status") == "QUOTED_NO_HOF_SUBMISSION"
                  and client.quote_reviewed and client.pair_queries == 2, "Resolved promoted H1 and exactly two reviewed quotes required")
        pre = Q.obj(client.snapshot())
        G.same_world(run.opening, baseline, pre)
        Q.require(H.wallet(pre) == H.wallet(arm["final_snapshot"]), "Wallet changed since original quote pair")
        result["wallet_before"] = G.wallet(pre)
        known_identity(one(client, "new-mother-h2-religion-before", Q.RELIGION),
                   one(client, "new-mother-h2-governance-before", Q.GOVERNANCE))
        pair = Q.obj(arm["hof_quotes"])
        refs = [Q.checked_pin(v) for v in Q.array(pair.get("quote_receipts"))]
        terms = [Q.obj(v) for v in Q.array(pair.get("terms"))]
        Q.require(len(refs) == len(terms) == 2, "Use actual same-world quote pair only")
        result["quote_receipts"], result["full10_quote"] = refs, Q.obj(terms[1]["resource_quote"])
        Q.vector(result["full10_quote"])
        N.reject_parent_hof_claim(mother)
        key = N.canonical_hof_key(mother)
        claim: Q.Obj = {"schema": "faith-e02-R19-hof-once-claim-v1", "machine_id": N.MACHINE,
            "run_id": run.run_id, "actor": D.ACTOR, "faith": D.FAITH, "date_raw": D.DATE,
            "decision_key": Q.DECISION, "intent_key": key, "once_ledger_root": str(mother.ledger),
            "new_common_mother": mother.manifest, "saved_sha256": mother.saved["sha256"],
            "parent_saved_sha256": Q.SAVE_SHA, "quote_receipts": refs, "unknown_must_not_repeat": True}
        HOF.verify_quote_pair(claim)
        path = mother.ledger / (key + ".claim.json")
        client.budget(4)
        Q.write_once(path, claim)
        result["original_claim"] = Q.pin(path)
        step: Q.Obj = {"id": "new-mother-h2-confirm-once", "tool": N.HOF_CONFIRM,
            "args": {"decision_key": Q.DECISION, "expected_outcome": "decision_closed"},
            "fresh_revision": True, "continue_on_error": True}
        HOF.admit_confirm({"steps": [step]}, path)
        client.h2_claim = path
        result["confirm_dispatch_attempts"], result["submission_outcome_unknown"] = 1, True
        try:
            rows = Q.array(client.execute_plan([step], "new-mother-h2-confirm-once", timeout=20, reserve=90))
            result["actual_confirm_row"] = Q.obj(rows[0])
        except Exception as error:
            result["errors"]["dispatch"] = type(error).__name__ + ": " + str(error)
        post = independent_post(client, run)
        result["independent_post"], result["head_creation_observed"] = post, post["head_creation_observed"]
        result["gold_prestige_piety_observed"] = post["wallet"] is not None
        delta = G.wallet_delta(result["wallet_before"], post["wallet"])
        result["wallet_delta_raw_after_minus_before"] = delta
        result["wallet_observation_complete"] = all(v is not None for v in delta.values())
        if post["head_creation_observed"] and post["heads"] is not None:
            result["title_id"] = Q.integer(post["heads"].get("faith_religious_head_title_id"), 1)
            holder = Q.integer(post["heads"].get("faith_religious_head_holder_character_id"), 1)
            result["holder_character_id"], result["holder_is_player"] = holder, holder == D.ACTOR
            result["status"], result["submission_outcome_unknown"] = "observed", False
        else:
            result["status"] = "unknown"
    except Exception as error:
        result["errors"]["precondition"] = type(error).__name__ + ": " + str(error)
    Q.write_once(run.output / "new-mother-h2-independent-post.json", result)
    return result


def h3_twice(client: StageClient, run: H.ArmRun) -> Q.Obj:
    result: Q.Obj = {"reads": [], "errors": {}, "current_group_qualified": False,
        "ghw_launch_submissions": 0, "war_commands_submitted": 0,
        "missing_variable_is_false": False, "no_ghw_is_world_peace": False, "automatic_retry": False}
    values: list[Q.Obj] = []
    errors: dict[str, str] = {}
    if run.baseline is None:
        raise ValueError("Actual world absent")
    for number in range(2):
        name = "new-mother-h3-readonly-" + str(number + 1)
        try:
            before = Q.obj(client.snapshot(require_event_free=False))
            G.same_world(run.opening, run.baseline, before)
            value = one(client, name, N.GHW)
            after = Q.obj(client.snapshot(require_event_free=False))
            G.same_world(run.opening, run.baseline, after)
            values.append({"receipt": Q.pin(run.output / (name + ".actual-results.json")), "value": value,
                           "before": before, "after": after})
        except Exception as error:
            errors[name] = type(error).__name__ + ": " + str(error)
    if len(values) == 2:
        a, b = Q.obj(values[0]["value"]), Q.obj(values[1]["value"])
        try:
            for value in (a, b):
                Q.require(value.get("available") is True and value.get("read_only") is True
                          and value.get("schema") == "ck3_12004_player_ghw_permissions_v1"
                          and Q.integer(value.get("played_character_id")) == D.ACTOR
                          and Q.integer(value.get("faith_id")) == D.FAITH
                          and Q.integer(value.get("date_raw"), -(2**31), 2**31-1) == D.DATE,
                          "Current GHW components unavailable; preserve unknown")
            Q.require(Q.integer(b.get("capture_epoch"), 1, 2**53-1) > Q.integer(a.get("capture_epoch"), 1, 2**53-1),
                      "Two independent GHW captures required")
            Q.require(all(N.field(Q.obj(v["after"]), "active_event") is None
                          and N.field(Q.obj(v["after"]), "pending_character_interaction") is None for v in values),
                      "New interruption leaves the H3 group unknown")
            result["current_group_qualified"] = not errors
        except Exception as error:
            errors["qualification"] = type(error).__name__ + ": " + str(error)
    result["reads"], result["errors"] = values, errors
    Q.write_once(run.output / "new-mother-h3-two-readonly.json", result)
    return result


def run_case(context_value: object, client: C.Client) -> Execution:
    context = Q.obj(context_value)
    c = validate_contract(context)
    mother = N.load_mother(c["new_common_mother"], c["preparation_result"])
    branch = Q.arm(c["arm"])
    opening = H.selected_opening(context)
    facade = StageClient(client, context, branch)
    run = H.ArmRun(context, facade, c, opening)
    result: Execution = {"schema": N.RESULT_SCHEMA, "machine_id": N.MACHINE, "run_id": run.run_id,
        "case": N.CASES[branch], "arm": branch, "status": "PARTIAL", "h1_arm_result": None,
        "h2": None, "events": None, "h3": None, "actual_public_calls": 1, "hof_confirm_submissions": 0,
        "promotion_submissions": 0, "promotion_outcome_unknown": False, "promotion_intent": None,
        "ghw_launch_submissions": 0, "war_commands_submitted": 0, "automatic_retry": False,
        "business_pass": False, "error": None}
    try:
        H.cohort(client.manifest, c["native_qualification"])
        allocated_ref = Q.pin(Path(Q.text(context["run_dir"])) / "allocated-context.json")
        allocated = Q.read(Path(allocated_ref["path"]))
        Q.require(allocated.get("schema") == "ck3-mod-acceptance-run-context-v1"
                  and allocated.get("case") == c["case"] and allocated.get("run_id") == run.run_id,
                  "Actual successor case allocation required; never forge an old case alias")
        initial, heads_before, sites = run.snapshot(), known_heads(run), run.sites()
        Q.require(sites == mother.membership and sum(sites.values()) == 2 and sites.get("32") is False,
                  "Fresh actual restore is not the materialized successor mother")
        promotion: Q.Obj | None = promote_once(run, mother, sites, facade) if branch == "promote" else None
        quotes = run.quote_pair()
        final_sites, heads_after, final = run.sites(), known_heads(run), run.snapshot()
        expected = dict(sites)
        if branch == "promote":
            expected["32"] = True
        Q.require(final_sites == expected and facade.pair_queries == 2 and facade.quote_reviewed,
                  "Only intended grade and two actual quotes may change")
        expected_wallet = H.wallet(Q.obj(promotion)["after"]) if promotion is not None else H.wallet(initial)
        Q.require(H.wallet(final) == expected_wallet, "H1 wallet changed outside the single promotion")
        arm: Q.Obj = {"schema": N.ARM_SCHEMA, "machine_id": N.MACHINE, "run_id": run.run_id,
            "case": c["case"], "arm": branch, "status": "QUOTED_NO_HOF_SUBMISSION", "holy_site_id": 32,
            "new_common_mother": mother.manifest, "preparation_result": mother.preparation,
            "mother_sha256": mother.saved["sha256"], "parent_saved_sha256": Q.SAVE_SHA,
            "once_ledger_root": str(mother.ledger), "prior_setup_disclosure": mother.disclosure,
            "allocated_context": allocated_ref, "scene": run.baseline,
            "native_cohort": H.cohort(client.manifest, c["native_qualification"]),
            "identity_before": heads_before, "identity_after": heads_after,
            "membership_before": sites, "membership_final": final_sites,
            "wallet_initial": H.wallet(initial), "final_snapshot": final, "promotion": promotion,
            "hof_quotes": quotes, "promotion_attempts": int(run.attempted), "promotion_outcome_unknown": run.unknown,
            "promotion_intent": run.intent, "public_calls": run.calls, "receipts": run.receipts,
            "native_culture_observed": False, "culture_control": N.CULTURE,
            "counts_are_realm_controlled_qualifying_counts": False, "hof_confirm_submissions": 0}
        Q.write_once(run.output / "new-mother-h1-arm-result.json", arm)
        result["h1_arm_result"] = Q.pin(run.output / "new-mother-h1-arm-result.json")
        result["status"] = "H1_QUOTED"
        if branch == "promote":
            facade.enter("h2")
            h2 = h2_once(context, facade, run, arm, mother)
            result["h2"] = h2
            facade.enter("events")
            frame = Q.obj(facade.snapshot(require_event_free=False))
            if run.baseline is None:
                raise ValueError("Actual H1 scene missing")
            G.same_world(opening, run.baseline, frame)
            def reader(value: object) -> Mapping[str, object]:
                return Q.obj(opening.opening_binding(value))
            events = Q.obj(G.legacy_observation().drain_current_events(context, facade, frame, Q.obj(run.baseline), reader,
                                                                      phase="new-mother-h2-post"))
            result["events"] = events
            Q.require(events.get("status") == "DRAINED", "Unknown event result preserved; no blind H3 continuation")
            facade.enter("h3")
            result["h3"] = h3_twice(facade, run)
            states: dict[Literal["not_submitted", "unknown", "observed"], State] = {
                "not_submitted": "H1_QUOTED_H2_NOT_SUBMITTED", "unknown": "H1_QUOTED_H2_UNKNOWN", "observed": "H1_QUOTED_H2_OBSERVED"}
            result["status"] = states[h2["status"]]
    except Exception as error:
        result["error"] = type(error).__name__ + ": " + str(error)
    if facade.stage != "done":
        facade.enter("done")
    result["actual_public_calls"], result["hof_confirm_submissions"] = facade.calls, facade.confirm_submissions
    result["promotion_submissions"], result["promotion_outcome_unknown"] = int(run.attempted), run.unknown
    result["promotion_intent"] = run.intent
    Q.write_once(run.output / "new-mother-execution-result.json", result)
    return result


def verify_case(context_value: object) -> Q.Obj:
    context = Q.obj(context_value)
    c = validate_contract(context)
    ref = Q.pin(Path(Q.text(context["output"])) / "new-mother-execution-result.json")
    value = Q.read(Path(ref["path"]))
    Q.require(value.get("schema") == N.RESULT_SCHEMA and value.get("run_id") == context["run_id"]
              and value.get("case") == c["case"] and value.get("machine_id") == N.MACHINE
              and value.get("h1_arm_result") is not None, "Completed original H1 phase required")
    return {"result": ref, "status": value["status"], "business_pass": False,
        "case_contract_qualified": False, "whole_product_acceptance_credit": False,
        "independent_two_arm_join_required": True, "automatic_retry": False}

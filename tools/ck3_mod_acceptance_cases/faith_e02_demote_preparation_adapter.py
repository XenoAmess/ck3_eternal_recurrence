"""One legal demotion and one materialized checkpoint; no HoF or promotion Confirm."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib
from pathlib import Path

import faith_e02_h1_queue as Q
import faith_e02_demote_preparation_contract as D
from ck3_mod_acceptance_cases import faith_e02_h1_comparison_adapter as H


def validate_contract(context_value: object) -> Q.Obj:
    context = Q.obj(context_value)
    c = Q.obj(context.get("case_contract"))
    Q.require(c.get("schema") == D.SCHEMA and c.get("case") == context.get("case") == D.CASE
              and c.get("product") == context.get("product") == "faith-engine"
              and c.get("machine_id") == D.MACHINE, "Independent preparation case identity differs")
    old = Q.retained_h2(Q.read(Path(Q.checked_pin(c.get("h2_case_contract"))["path"])))
    saved = Q.obj(c.get("saved_input"))
    Q.require(Q.encode(saved) == Q.encode(old.get("saved_input"))
              and set(saved) == {"save", "bytes", "sha256", "player_id", "date_raw"}
              and saved.get("sha256") == Q.SAVE_SHA
              and Q.integer(saved.get("bytes"), 1, 2**53-1) == 69030069
              and Q.integer(saved.get("player_id")) == D.ACTOR
              and Q.integer(saved.get("date_raw"), -(2**31), 2**31-1) == D.DATE,
              "Restore the original immutable adopted-Nadjaf mother")
    ledger = Path(Q.text(c.get("once_ledger_root")))
    Q.require(ledger.is_absolute() and ledger.is_dir() and not ledger.is_symlink()
              and old.get("once_ledger_root") == str(ledger)
              and Q.obj(context.get("case_inputs")).get("once_ledger_root") == str(ledger),
              "Retain the original H2 ledger; no unknown-result replay by changing roots")
    Q.require(c.get("profile") == {"enabled_mods": [], "product_files": []}
              and Q.integer(c.get("demote_site_id")) == D.DEMOTE_SITE
              and Q.integer(c.get("promote_precheck_site_id")) == D.PROMOTE_SITE
              and Q.integer(c.get("max_public_calls"), 1) == D.MAX_CALLS
              and Q.integer(c.get("max_demote_submissions")) == 1
              and Q.integer(c.get("max_save_submissions")) == 1
              and Q.integer(c.get("promote_submissions")) == 0
              and Q.integer(c.get("create_hof_submissions")) == 0,
              "Finite vanilla preparation scope differs")
    Q.require(c.get("prior_setup_disclosure") == old.get("prior_setup_disclosure"),
              "Original mechanism preparation disclosure must remain explicit")
    spec = Q.obj(context.get("case_spec"))
    Q.require(set(Q.text(x) for x in Q.array(spec.get("required_mcp_tools"))) == D.REQUIRED
              and set(Q.text(x) for x in Q.array(spec.get("opt_in_read_only_mcp_tools"))) == D.READONLY_OPT_IN
              and all(spec.get(k) is False for k in H.CLOSED), "Finite public tools/permissions differ")
    Q.require(Q.encode(Q.read(Path(Q.text(spec.get("initial_plan"))))) == Q.encode({"steps": [D.step(
        "h1-preparation-initial-capabilities", "ck3_get_capabilities", {})]}),
        "One declared capability read must be included in the call cap")
    sources = {Path(__file__).resolve(), Path(D.__file__).resolve(), Path(Q.__file__).resolve(),
               Path(H.__file__).resolve(), Path(H.selected_quotes().__file__).resolve()}
    dependencies = {Path(Q.checked_pin(x)["path"]).resolve() for x in Q.array(c.get("dependencies"))}
    Q.require(sources <= dependencies, "Pin the exact adapter and actual shared source dependencies")
    H.cohort(Q.read(Path(Q.checked_pin(context.get("runtime_manifest"))["path"])), c.get("native_qualification"))
    return c


def prepare_case(context_value: object) -> Q.Obj:
    context = Q.obj(context_value)
    c = validate_contract(context)
    saved = Q.obj(c["saved_input"])
    Q.require(Q.encode(context.get("saved_campaign")) == Q.encode(saved), "Prepare selected another mother")
    source = Path(Q.text(saved["save"]))
    actual = Q.pin(source)
    Q.require(actual["bytes"] == saved["bytes"] and actual["sha256"] == saved["sha256"], "Original mother changed")
    inputs = Q.obj(context["case_inputs"])
    grant = Q.read(Path(Q.checked_pin(inputs.get("storage_admission"))["path"]))
    expiry = datetime.fromisoformat(Q.text(grant.get("expires_at_utc")).replace("Z", "+00:00"))
    Q.require(grant.get("active") is True and grant.get("machine_id") == D.MACHINE
              and expiry.tzinfo is not None and datetime.now(timezone.utc) < expiry, "Fresh full scene admission required")
    module: object = importlib.import_module("ck3_mod_acceptance_prepare")
    if not isinstance(module, H.Prepare):
        raise ValueError("Actual public preparation functions unavailable")
    profile = Q.obj(module.materialize_product_profile(context, None, inputs.get("configuration")))
    profile = Q.obj(module.finish_product_profile(context, profile, provenance={
        "machine_id": D.MACHINE, "kind": D.CASE, "saved_input": saved,
        "h2_case_contract": c["h2_case_contract"], "prior_setup_disclosure": c["prior_setup_disclosure"],
        "fresh_restore_observed": False, "preparation_mod_mounted": False,
        "native_culture_observed": False, "new_common_mother_materialized": False}))
    return {"startup": {"mode": "saved_campaign", "state_dir": profile["state_dir"],
            "saved_campaign": {**saved, "product_inventory": Q.obj(profile["product_inventory"])["path"]}},
            "profile": profile, "initial_plan": Q.obj(context["case_spec"])["initial_plan"],
            "runtime_status": "NOT_RUN", "business_pass": False}


class Preparation:
    def __init__(self, context: Q.Obj, client: H.Client, contract: Q.Obj, opening: H.Opening) -> None:
        self.context, self.client, self.c, self.opening = context, client, contract, opening
        self.output = Path(Q.text(context.get("output")))
        self.run_id = Q.text(context.get("run_id"))
        self.calls, self.number = 1, 0
        self.baseline: Q.Scene | None = None
        self.last_revision = 0
        self.demote_attempted = self.save_attempted = False
        self.demote_unknown = self.save_unknown = False
        self.receipts: list[Q.Pin] = []
        self.intents: list[Q.Pin] = []

    def guard(self, count: int) -> None:
        Q.require(self.calls + count <= D.MAX_CALLS, "Finite preparation call cap exhausted")
        self.client.guard(120 + 300 + count * 20 + 20)

    def frame(self, value: object) -> Q.Obj:
        frame = Q.obj(value)
        current = H.scene(frame, self.opening)
        Q.require(current["played_character_id"] == D.ACTOR and current["date_raw"] == D.DATE,
                  "Actual restored actor/date differs")
        if self.baseline is None:
            self.baseline = current
        else:
            a, b = Q.obj(current), Q.obj(self.baseline)
            for key in ("played_character_id", "date_raw", "game_pid", "connection_generation", "episode_run_id"):
                Q.require(Q.encode(a[key]) == Q.encode(b[key]), "Preparation crossed same-owner scene: " + key)
        Q.require(current["native_revision"] >= self.last_revision, "Native revision regressed")
        self.last_revision = current["native_revision"]
        return frame

    def snapshot(self) -> Q.Obj:
        self.guard(1)
        self.calls += 1
        return self.frame(self.client.snapshot(require_event_free=False))

    def result(self, tool: str, args: Q.Obj | None = None, *, consumed: bool = False) -> Q.Obj:
        self.guard(1 if tool in D.READS else 2)
        if tool not in D.READS:
            self.snapshot()  # Actual public actions need not publish before_snapshot.
        self.number += 1
        name = "h1-preparation-" + str(self.number).zfill(3)
        request = D.step(name, tool, args or {}, consumed=consumed)
        self.calls += 1
        rows = Q.array(self.client.execute_plan([request], name, timeout=45 if tool == D.SAVE else 20, reserve=90))
        Q.require(len(rows) == 1, "One original public row required")
        row = Q.obj(rows[0])
        self.receipts.append(Q.pin(self.output / (name + ".actual-results.json")))
        if "before_snapshot" in row:
            self.frame(row["before_snapshot"])
        self.frame(row.get("after_snapshot"))
        Q.require(row.get("ok") is True and not row.get("error"), "Actual public call rejected: " + tool)
        value = Q.obj(row.get("result"))
        if "played_character_id" in value:
            Q.require(Q.integer(value["played_character_id"]) == D.ACTOR
                      and Q.integer(value.get("date_raw"), -(2**31), 2**31-1) == D.DATE,
                      "Native result crossed actual actor/date")
        return value

    def sites(self) -> dict[str, bool]:
        return Q.membership(self.result(Q.SITES, {"holy_site_id": D.DEMOTE_SITE}), D.FAITH)

    def heads(self) -> Q.Obj:
        religion, governance = self.result(Q.RELIGION), self.result(Q.GOVERNANCE)
        Q.require("faith_religious_head_holder_character_id" in Q.obj(governance.get("heads")),
                  "Typed no-HoF observation cannot be missing/unknown")
        return H.identity(religion, governance)

    def decision(self, action: D.Action, site: int) -> D.Terms:
        query: Q.Obj = {"window_kind": "holy_site"}
        window = self.result(D.WINDOW, query)
        if not H.selected_promotion_site_window(window, site):
            self.result(D.OPEN_WINDOW, {"holy_site_id": site})
            window = self.result(D.WINDOW, query)
        Q.require(H.selected_promotion_site_window(window, site), "Independent selected holy-site window unavailable")
        target: Q.Obj = {"action": action, "holy_site_id": site}
        self.result(D.OPEN_DECISION, target)
        return D.terms(self.result(Q.DETAIL, target), action, site)

    def consume(self, kind: D.Mutation, evidence: object) -> Q.Pin:
        self.guard(10)
        if kind == "demote":
            Q.require(not self.demote_attempted and not self.demote_unknown, "Demote already consumed or unknown")
            self.demote_unknown = True
        else:
            Q.require(not self.save_attempted and not self.save_unknown and not self.demote_unknown,
                      "Save already consumed or demotion outcome unknown")
            self.save_unknown = True
        ref = D.claim(Path(Q.text(self.c["once_ledger_root"])), self.run_id, kind, evidence)
        self.intents.append(ref)
        if kind == "demote":
            self.demote_attempted = True
        else:
            self.save_attempted = True
        return ref


def reviewed(run: Preparation, observation: Q.Obj) -> Q.Obj:
    review = Q.obj(run.client.root_checkpoint("h1-preparation-demote-review", {
        "native_observation": observation,
        "native_observation_sha256": hashlib.sha256(Q.encode(observation).encode()).hexdigest(),
        "approval_key": "demote_preparation_once_authorized", "prepare_original_image": True}, reserve=120))
    Q.require(review.get("run_id") == run.run_id and review.get("reviewer") == run.client.operator_reviewer
              and review.get("status") == "complete" and review.get("original_image_directly_reviewed") is True
              and review.get("demote_preparation_once_authorized") is True
              and review.get("reviewed_native_observation_sha256") == hashlib.sha256(Q.encode(observation).encode()).hexdigest(),
              "Actual Root review and explicit one-demotion authorization required")
    image = Q.checked_pin(review.get("original_image"))
    Q.require(Path(image["path"]).read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), "Original reviewed PNG required")
    return review


def run_case(context_value: object, client: H.Client) -> Q.Obj:
    context = Q.obj(context_value)
    c = validate_contract(context)
    H.cohort(client.manifest, c["native_qualification"])
    run = Preparation(context, client, c, H.selected_opening(context))
    result: Q.Obj = {"schema": "faith-e02-h1-demote-preparation-result-v1", "machine_id": D.MACHINE,
        "run_id": run.run_id, "status": "PARTIAL", "business_pass": False,
        "promote_submissions": 0, "create_hof_submissions": 0,
        "normal_exit_observed_by_case": False, "native_free_action_count_observed": False}
    try:
        initial = run.snapshot()
        result["scene"] = run.baseline
        result["identity_before"] = run.heads()
        before_sites = run.sites()
        Q.require(sum(before_sites.values()) == 3 and before_sites.get("0") is True
                  and before_sites.get("32") is False, "Original three-main-site Faith103 baseline required")
        first = run.decision("demote", D.DEMOTE_SITE)
        cooldown = D.cooldown(run.result(Q.COOLDOWN, {"action": "demote"}), "demote")
        observation: Q.Obj = {"site_id": D.DEMOTE_SITE, "terms": first, "cooldown": cooldown,
                             "membership_before": before_sites, "create_hof_submissions": 0}
        result["review_observation"] = observation
        review = reviewed(run, observation)
        result["Root_precommit_review"] = review
        before = run.snapshot()
        second = D.terms(run.result(Q.DETAIL, {"action": "demote", "holy_site_id": D.DEMOTE_SITE}),
                         "demote", D.DEMOTE_SITE)
        D.stable_terms(first, second)
        Q.require(run.sites() == before_sites and run.heads() == result["identity_before"]
                  and H.wallet(before) == H.wallet(initial), "Reviewed scene, identity or wallet changed")
        intent = run.consume("demote", {"terms": second, "review": review, "before": before})
        ack = run.result(D.CONFIRM, {"action": "demote", "holy_site_id": D.DEMOTE_SITE}, consumed=True)
        after_sites, after = run.sites(), run.snapshot()
        D.membership_post(before_sites, after_sites)
        old, new = H.wallet(before), H.wallet(after)
        cost = second["resource_vector_raw"][2]
        Q.require(new == {**old, "piety": old["piety"] - cost}, "Independent exact wallet debit not proven")
        run.demote_unknown = False
        result["demotion"] = {"intent": intent, "ack": ack, "before": before, "after": after,
            "membership_before": before_sites, "membership_after": after_sites,
            "full10_quote": second["native_resource_quote"], "actual_wallet_debit_raw": cost,
            "independent_demotion_observed": True, "payment_total_proven": True}
        precheck = run.decision("promote", D.PROMOTE_SITE)
        result["promote32_readonly_precheck"] = precheck
        promote_cooldown = D.cooldown(run.result(Q.COOLDOWN, {"action": "promote"}), "promote")
        result["promote32_cooldown"] = promote_cooldown
        result["free_action_text_before"] = second["requirements"]
        result["free_action_text_after"] = precheck["requirements"]
        Q.require(run.sites() == after_sites and run.heads() == result["identity_before"]
                  and H.wallet(run.snapshot()) == new, "Post-demotion controls changed before save")
        save_intent = run.consume("save-checkpoint", {"demotion": result["demotion"],
                                  "precheck": precheck, "promote_cooldown": promote_cooldown})
        save_result = run.result(D.SAVE, consumed=True)
        save_dir = Path(Q.text(context.get("state_dir"))) / "profile" / "save games"
        saved = D.materialized(save_result, save_dir, Path(Q.text(Q.obj(c["saved_input"])["save"])))
        Q.require(saved["sha256"] != Q.SAVE_SHA, "New demotion baseline cannot retain the original mother bytes")
        Q.require(run.sites() == after_sites and run.heads() == result["identity_before"]
                  and H.wallet(run.snapshot()) == new, "Independent post-save identity/grades/wallet changed")
        run.save_unknown = False
        mother: Q.Obj = {"schema": "faith-e02-h1-demoted-common-mother-v1", "machine_id": D.MACHINE,
            "run_id": run.run_id, "saved_input": saved, "parent_saved_input": c["saved_input"],
            "parent_h2_case_contract": c["h2_case_contract"], "once_ledger_root": c["once_ledger_root"],
            "prior_setup_disclosure": c["prior_setup_disclosure"], "identity": result["identity_before"],
            "faith_membership": after_sites, "main_membership_count": 2, "nadjaf32_eminent": False,
            "demotion": result["demotion"], "save_intent": save_intent, "save_receipt": save_result,
            "native_qualification": c["native_qualification"], "native_culture_observed": False,
            "native_free_action_count_observed": False, "free_action_text": precheck["requirements"],
            "promote32_readonly_precheck": precheck, "promote32_cooldown": promote_cooldown,
            "requires_two_new_independent_h1_restores": True, "old_R16_not_a_comparison_arm": True,
            "hof_confirm_submissions": 0, "automatic_retry": False}
        Q.write_once(run.output / "new-common-mother.json", mother)
        result["new_common_mother"] = Q.pin(run.output / "new-common-mother.json")
        result["status"] = "DEMOTED_AND_CHECKPOINT_MATERIALIZED"
    except Exception as error:
        result["error"] = type(error).__name__ + ": " + str(error)
    result.update(public_calls=run.calls, demote_attempts=int(run.demote_attempted),
                  save_attempts=int(run.save_attempted), demote_outcome_unknown=run.demote_unknown,
                  save_outcome_unknown=run.save_unknown, intents=run.intents, receipts=run.receipts)
    Q.write_once(run.output / "demote-preparation-result.json", result)
    return result


def verify_case(context_value: object) -> Q.Obj:
    context = Q.obj(context_value)
    validate_contract(context)
    ref = Q.pin(Path(Q.text(context.get("output"))) / "demote-preparation-result.json")
    result = Q.read(Path(ref["path"]))
    Q.require(result.get("status") == "DEMOTED_AND_CHECKPOINT_MATERIALIZED"
              and result.get("run_id") == context.get("run_id") and result.get("machine_id") == D.MACHINE
              and result.get("demote_outcome_unknown") is False and result.get("save_outcome_unknown") is False,
              "Only independently observed demotion and saved checkpoint qualify this preparation")
    mother_ref = Q.checked_pin(result.get("new_common_mother"))
    mother = Q.read(Path(mother_ref["path"]))
    saved = Q.obj(mother.get("saved_input"))
    actual = Q.pin(Path(Q.text(saved.get("save"))))
    Q.require(actual["bytes"] == Q.integer(saved.get("bytes"), 1, 2**53-1)
              and actual["sha256"] == saved.get("sha256"), "New mother no longer matches saved bytes")
    return {"status": result["status"], "preparation_completed": True, "new_common_mother": mother_ref,
            "business_pass": False, "business_contract_applicable": False, "case_contract_qualified": False,
            "gui_contract_qualified": False, "whole_product_acceptance_credit": False,
            "product_release_pass": False, "automatic_retry": False}

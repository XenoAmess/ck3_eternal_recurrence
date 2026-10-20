"""Join actual successor H1 arm receipts; zero or reversed quote deltas are valid."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import faith_e02_h1_queue as Q
import faith_e02_h1_new_mother_contract as N
from ck3_mod_acceptance_cases import faith_e02_h1_comparison_adapter as H


def checked_arm(ref_value: object, expected: Q.Arm) -> Q.Obj:
    ref = Q.checked_pin(ref_value)
    value = Q.read(Path(ref["path"]))
    Q.require(value.get("schema") == N.ARM_SCHEMA and value.get("arm") == expected
              and value.get("case") == N.CASES[expected] and value.get("machine_id") == N.MACHINE
              and value.get("status") == "QUOTED_NO_HOF_SUBMISSION"
              and value.get("promotion_outcome_unknown") is False
              and Q.integer(value.get("hof_confirm_submissions")) == 0
              and value.get("native_culture_observed") is False and value.get("culture_control") == N.CULTURE,
              "New-schema complete actual H1 arm required; no old R16/R21 or unknown aliases")
    mother = N.load_mother(value.get("new_common_mother"), value.get("preparation_result"))
    Q.require(value.get("mother_sha256") == mother.saved["sha256"] and value.get("parent_saved_sha256") == Q.SAVE_SHA
              and value.get("once_ledger_root") == str(mother.ledger)
              and value.get("prior_setup_disclosure") == mother.disclosure, "Actual successor provenance differs")
    allocation_path = Path(Q.checked_pin(value.get("allocated_context"))["path"])
    allocated = Q.read(allocation_path)
    Q.require(allocated.get("schema") == "ck3-mod-acceptance-run-context-v1"
              and allocated.get("case") == N.CASES[expected] and allocated.get("run_id") == value.get("run_id")
              and allocation_path.parent / "case-output" == Path(ref["path"]).parent,
              "Original public successor allocation/output required")
    cohort = Q.obj(value.get("native_cohort"))
    Q.require(Q.encode(Q.qualified_hof_cohort(cohort.get("qualification"))) == Q.encode(cohort), "Actual Native cohort differs")
    for key in ("identity_before", "identity_after"):
        identity = Q.obj(value.get(key))
        Q.require([Q.integer(identity.get(k)) for k in ("actor", "faith", "rite", "faith_main_rite")] == [31254, 103, 150, 150]
                  and N.field(identity, "head_holder") is None, "Known no-head actor/Faith/Rite controls required")
    scene = Q.obj(value.get("scene"))
    Q.require(Q.integer(scene.get("played_character_id")) == 31254
              and Q.integer(scene.get("date_raw"), -(2**31), 2**31-1) == 53144328,
              "Actual independently restored actor/date differs")
    Q.integer(scene.get("game_pid"), 1)
    Q.integer(scene.get("connection_generation"), 1, 2**53-1)
    pair = Q.obj(value.get("hof_quotes"))
    terms: list[Q.Obj] = []
    epochs: list[int] = []
    refs = [Q.checked_pin(v) for v in Q.array(pair.get("quote_receipts"))]
    Q.require(len(refs) == 2 and refs[0]["path"] != refs[1]["path"], "Two independent original quote receipts required")
    for quote in refs:
        Q.require(Path(quote["path"]).parent == Path(ref["path"]).parent, "Quote belongs to another actual arm")
        rows = Q.array(Q.read(Path(quote["path"])).get("rows"))
        Q.require(len(rows) == 1, "One original public query row required")
        row = Q.obj(rows[0])
        plan = Q.obj(row.get("plan"))
        Q.require(plan.get("tool") == Q.QUERY and Q.obj(plan.get("args")) == {"decision_key": Q.DECISION}, "Original quote tool differs")
        N.same_scene(N.native_scene(row.get("after_snapshot")), N.native_scene(value.get("final_snapshot")))
        terms.append(H.hof_terms(row))
        epochs.append(Q.integer(terms[-1].get("capture_epoch"), 1, 2**53-1))
    Q.require(epochs[1] > epochs[0] and Q.encode(epochs) == Q.encode(pair.get("capture_epochs"))
              and Q.encode(terms) == Q.encode(pair.get("terms")), "Original quote pair changed")
    for field in ("resource_quote", "requirements_description", "cost_description", "context_adapter", "named_parameter_count", "stock_default_parameter"):
        Q.require(Q.encode(terms[0].get(field)) == Q.encode(terms[1].get(field)), "Independent quote terms unstable")
    Q.require(Q.encode(Q.vector(terms[0]["resource_quote"])) == Q.encode(pair.get("resource_vector_raw")), "Stored full10 quote differs")
    Q.require(Q.integer(value.get("public_calls"), 1) <= Q.MAX_CALLS, "H1 phase exceeded original finite cap")
    Q.require(N.exact_map(value.get("membership_before")) == mother.membership, "Arm did not restore the new two-major mother")
    return value


def compare(ordinary_ref: object, promoted_ref: object) -> Q.Obj:
    a, b = checked_arm(ordinary_ref, "ordinary"), checked_arm(promoted_ref, "promote")
    Q.require(Q.text(a.get("run_id")) != Q.text(b.get("run_id")), "Two new independent managed restores required")
    Q.require(Q.integer(Q.obj(a["scene"])["game_pid"], 1) != Q.integer(Q.obj(b["scene"])["game_pid"], 1),
              "Independent original managed processes required")
    for key in ("new_common_mother", "preparation_result", "mother_sha256", "parent_saved_sha256", "once_ledger_root",
                "prior_setup_disclosure", "identity_before", "identity_after", "membership_before", "wallet_initial", "native_cohort", "culture_control"):
        Q.require(Q.encode(a.get(key)) == Q.encode(b.get(key)), "Controlled input differs: " + key)
    qa = {Q.checked_pin(v)["path"] for v in Q.array(Q.obj(a["hof_quotes"])["quote_receipts"])}
    qb = {Q.checked_pin(v)["path"] for v in Q.array(Q.obj(b["hof_quotes"])["quote_receipts"])}
    Q.require(qa.isdisjoint(qb), "Two arms cannot reuse original quote files")
    before = N.exact_map(a["membership_before"])
    expected = dict(before)
    expected["32"] = True
    Q.require(sum(before.values()) == 2 and before.get("32") is False
              and N.exact_map(a.get("membership_final")) == before
              and N.exact_map(b.get("membership_final")) == expected and sum(expected.values()) == 3
              and Q.integer(a.get("promotion_attempts")) == 0 and a.get("promotion") is None
              and Q.integer(b.get("promotion_attempts")) == 1, "Only the selected 32 grade may change")
    Q.require(H.wallet(a["final_snapshot"]) == a["wallet_initial"], "Ordinary arm changed its wallet")
    promotion = Q.obj(b.get("promotion"))
    ref = Q.checked_pin(promotion.get("intent"))
    intent = Q.read(Path(ref["path"]))
    mother = N.load_mother(b["new_common_mother"], b["preparation_result"])
    Q.require(intent.get("schema") == "faith-e02-h1-new-mother-promote-intent-v1"
              and intent.get("run_id") == b["run_id"]
              and Q.encode(intent.get("scope")) == Q.encode(N.action_scope(mother, "promote"))
              and Path(ref["path"]).parent == mother.ledger
              and promotion.get("independent_promotion_observed") is True and promotion.get("payment_total_proven") is True,
              "Original new-mother once promotion proof required")
    five = Q.obj(intent.get("exact_native_five_fields"))
    digest = hashlib.sha256(Q.encode(five).encode()).hexdigest()
    review = Q.obj(intent.get("review"))
    Q.require(len(five) == 5 and intent.get("exact_native_five_fields_sha256") == digest
              and review.get("reviewed_native_observation_sha256") == digest
              and review.get("original_image_directly_reviewed") is True and review.get("promote_once_authorized") is True,
              "Root review lost exact five-field binding")
    image = Q.checked_pin(review.get("original_image"))
    Q.require(Path(image["path"]).read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), "Original reviewed PNG missing")
    cost = Q.vector(promotion.get("full10_quote"), promotion=True)
    old, new = H.wallet(promotion.get("before")), H.wallet(promotion.get("after"))
    debit = {k: old[k] - new[k] for k in ("gold", "prestige", "piety")}
    Q.require([debit[k] for k in ("gold", "prestige", "piety")] == cost[:3] and all(v == 0 for v in cost[3:])
              and Q.encode(debit) == Q.encode(promotion.get("actual_wallet_debit_raw"))
              and N.exact_map(promotion.get("membership_before")) == before
              and N.exact_map(promotion.get("membership_after")) == expected
              and H.wallet(b["final_snapshot"]) == new, "Independent grade/wallet proof differs")
    va = Q.vector(Q.obj(Q.array(Q.obj(a["hof_quotes"])["terms"])[0])["resource_quote"])
    vb = Q.vector(Q.obj(Q.array(Q.obj(b["hof_quotes"])["terms"])[0])["resource_quote"])
    return {"schema": "faith-e02-h1-new-mother-actual-comparison-v1", "machine_id": N.MACHINE,
        "arm_results": [Q.checked_pin(ordinary_ref), Q.checked_pin(promoted_ref)], "new_common_mother": mother.manifest,
        "ordinary_hof_resource_vector_raw": va, "promoted_hof_resource_vector_raw": vb,
        "promoted_minus_ordinary_quote_raw": [y-x for x, y in zip(va, vb)], "raw_scale": Q.SCALE,
        "promotion_full10_quote_separate": promotion["full10_quote"], "promotion_actual_debit_separate": debit,
        "nonzero_or_negative_quote_difference_required": False, "selected_site_cost_attribution_observed": False,
        "cost_rule_reference": {"game_relative_path": "common/script_values/02_religion_values.txt",
            "sha256": "9e55618b00b463589af310bd17511b4f260fea4d3acb43e512e209cfc1517ded", "line_ranges": [[4094, 4188]],
            "qualification": "retained_exact_1_20_0_4_source_review_not_current_installation_or_state"},
        "cost_rule_scope": "Any player-controlled major holy-site county whose holder has the player's Faith; not selected32 alone.",
        "demotion_role": "Releases the Faith major-site cap; other qualifying major sites may keep both quotes equal.",
        "native_culture_observed": False, "culture_control": N.CULTURE,
        "counts_are_realm_controlled_qualifying_counts": False, "unknown_attribution_preserved": True,
        "H2_head_creation_credit": False, "whole_product_acceptance_credit": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ordinary", type=Path, required=True)
    parser.add_argument("--promoted", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    Q.write_once(args.output, compare(Q.pin(args.ordinary), Q.pin(args.promoted)))


if __name__ == "__main__":
    main()

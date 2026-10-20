"""Read two original H1 arm results; compare native ten-slot quotes, never submit."""
from __future__ import annotations

import argparse
from pathlib import Path
import faith_e02_h1_queue as Q
from ck3_mod_acceptance_cases.faith_e02_h1_comparison_adapter import hof_terms, wallet


def required_controls(value: Q.Obj) -> None:
    for name in ("identity_before", "identity_after"):
        identity = Q.obj(value.get(name))
        Q.require([Q.integer(identity.get(k)) for k in ("actor", "faith", "rite", "faith_main_rite")]
                  == [31254, 103, 150, 150] and "head_holder" in identity
                  and identity["head_holder"] is None and identity.get("native_culture_observed") is False
                  and identity.get("culture_control") == "same_immutable_mother_no_culture_mutator",
                  "Complete actual H1 actor/Faith/Rite controls required")
    initial = Q.obj(value.get("wallet_initial"))
    Q.require(set(initial) == {"gold", "prestige", "piety"}, "Three actual initial wallet balances required")
    for number in initial.values():
        Q.integer(number, -(2**63), 2**63-1)
    for name in ("membership_before", "membership_final"):
        membership = Q.obj(value.get(name))
        Q.require(bool(membership) and all(k.isdecimal() and type(v) is bool for k, v in membership.items()),
                  "Complete Boolean Faith membership map required")
    counts = Q.obj(value.get("faith_membership_counts"))
    Q.require(set(counts) == {"ordinary", "eminent"}, "Faith membership counts required")
    Q.integer(counts["ordinary"], 0, 64)
    Q.integer(counts["eminent"], 0, 64)
    Q.text(value.get("once_ledger_root"))
    Q.checked_pin(value.get("native_qualification"))


def checked_arm(ref_value: object, expected_arm: Q.Arm) -> Q.Obj:
    ref = Q.checked_pin(ref_value)
    value = Q.read(Path(ref["path"]))
    Q.require(value.get("schema") == "faith-e02-h1-arm-result-v1" and value.get("arm") == expected_arm
              and value.get("status") == "QUOTED_NO_HOF_SUBMISSION"
              and Q.integer(value.get("hof_confirm_submissions")) == 0
              and value.get("promotion_outcome_unknown") is False
              and value.get("mother_sha256") == Q.SAVE_SHA
              and value.get("native_culture_observed") is False
              and value.get("culture_control") == "same_immutable_mother_no_culture_mutator",
              "Complete actual arm without HoF/unknown required")
    required_controls(value)
    cohort = Q.qualified_hof_cohort(value.get("native_qualification"))
    Q.require(value.get("native_compile_source_commit") == cohort["native_compile_source_commit"]
              and Q.encode(value.get("native_cohort")) == Q.encode(cohort),
              "Arm must retain its actual selected Native cohort, not the semantic-origin commit")
    allocation_path = Path(Q.checked_pin(value.get("allocated_context"))["path"])
    allocated = Q.read(allocation_path)
    output = allocation_path.parent / "case-output"
    Q.require(Path(ref["path"]).resolve().parent == output.resolve(), "Use the actual standard CaseClient output")
    Q.require(allocated.get("run_id") == value.get("run_id"), "Arm lost its original actual allocation")
    quotes = Q.obj(value.get("hof_quotes"))
    refs = Q.array(quotes.get("quote_receipts"))
    Q.require(len(refs) == 2 and Q.obj(refs[0]).get("path") != Q.obj(refs[1]).get("path"), "Two original quote files")
    terms: list[Q.Obj] = []
    epochs: list[int] = []
    for original in refs:
        quote_path = Path(Q.checked_pin(original)["path"])
        Q.require(quote_path.resolve().parent == output.resolve(), "Quote belongs to another actual arm")
        packet = Q.read(quote_path)
        rows = Q.array(packet.get("rows"))
        Q.require(len(rows) == 1, "One actual original HoF query per receipt")
        terms.append(hof_terms(rows[0]))
        epochs.append(Q.integer(terms[-1].get("capture_epoch"), 1, 2**53-1))
    Q.require(epochs[1] > epochs[0] and Q.encode(epochs) == Q.encode(quotes.get("capture_epochs")),
              "Original quote captures are not independent/increasing")
    for key in ("resource_quote", "requirements_description", "cost_description", "context_adapter",
                "named_parameter_count", "stock_default_parameter"):
        Q.require(Q.encode(terms[0].get(key)) == Q.encode(terms[1].get(key)), "Original pair terms changed")
    Q.require(Q.encode(terms) == Q.encode(quotes.get("terms")), "Stored quote terms differ from original receipts")
    raw = Q.vector(terms[0].get("resource_quote"))
    Q.require(raw == Q.vector(terms[1].get("resource_quote"))
              and Q.encode(raw) == Q.encode(quotes.get("resource_vector_raw")), "Per-arm quotes changed")
    Q.require(Q.integer(value.get("public_calls"), 1) <= Q.MAX_CALLS, "Arm exceeded finite public cap")
    return value


def compare(ordinary_ref: object, promoted_ref: object) -> Q.Obj:
    a, b = checked_arm(ordinary_ref, "ordinary"), checked_arm(promoted_ref, "promote")
    Q.require(Q.text(a.get("run_id")) != Q.text(b.get("run_id")), "Independent restore/run IDs required")
    qa = {Q.text(Q.obj(r).get("path")) for r in Q.array(Q.obj(a["hof_quotes"])["quote_receipts"])}
    qb = {Q.text(Q.obj(r).get("path")) for r in Q.array(Q.obj(b["hof_quotes"])["quote_receipts"])}
    Q.require(qa.isdisjoint(qb), "Independent actual quote files required for the two arms")
    for key in ("machine_id", "holy_site_id", "mother_sha256", "once_ledger_root", "native_qualification", "native_cohort",
                "identity_before", "identity_after", "membership_before", "wallet_initial", "culture_control"):
        Q.require(Q.encode(a.get(key)) == Q.encode(b.get(key)), "Two arms differ in controlled input: " + key)
    for key in ("played_character_id", "date_raw"):
        x, y = Q.obj(a.get("scene")), Q.obj(b.get("scene"))
        Q.require(Q.integer(x.get(key), -(2**31), 2**32-2) ==
                  Q.integer(y.get(key), -(2**31), 2**32-2), "Arms crossed actor/date")
    site = str(Q.integer(a.get("holy_site_id")))
    before = Q.obj(a.get("membership_before"))
    expected: Q.Obj = dict(before)
    Q.require(before.get(site) is False, "Original selected association must be ordinary")
    expected[site] = True
    Q.require(Q.encode(a.get("membership_final")) == Q.encode(before)
              and Q.encode(b.get("membership_final")) == Q.encode(expected)
              and Q.integer(a.get("promotion_attempts")) == 0
              and Q.integer(b.get("promotion_attempts")) == 1, "Only intended ordinary-to-Eminent relation may change")
    promotion = Q.obj(b.get("promotion"))
    original_intent = Q.read(Path(Q.checked_pin(promotion.get("intent"))["path"]))
    Q.require(original_intent.get("run_id") == b["run_id"] and promotion.get("payment_total_proven") is True
              and promotion.get("independent_promotion_observed") is True, "Original promotion proof incomplete")
    cost = Q.vector(promotion.get("full10_quote"), promotion=True)
    old, new = wallet(promotion.get("before")), wallet(promotion.get("after"))
    debit = {k: old[k] - new[k] for k in old}
    Q.require(list(debit.values()) == cost[:3] and all(n == 0 for n in cost[3:])
              and Q.encode(debit) == Q.encode(promotion.get("actual_wallet_debit_raw")), "Actual debit is not the promotion quote")
    va = Q.vector(Q.obj(Q.array(Q.obj(a["hof_quotes"])["terms"])[0])["resource_quote"])
    vb = Q.vector(Q.obj(Q.array(Q.obj(b["hof_quotes"])["terms"])[0])["resource_quote"])
    return {"schema": "faith-e02-h1-actual-two-arm-comparison-v1", "machine_id": a["machine_id"],
        "arm_results": [Q.checked_pin(ordinary_ref), Q.checked_pin(promoted_ref)],
        "ordinary_hof_resource_vector_raw": va, "promoted_hof_resource_vector_raw": vb,
        "promoted_minus_ordinary_quote_raw": [y-x for x, y in zip(va, vb)], "raw_scale": Q.SCALE,
        "promotion_full10_quote_separate": promotion["full10_quote"], "promotion_actual_debit_separate": debit,
        "faith_membership_counts": [a["faith_membership_counts"], b["faith_membership_counts"]],
        "counts_are_realm_controlled_qualifying_counts": False,
        "native_culture_observed": False, "culture_control": a["culture_control"],
        "script_validity_control": "each_actual_native_CanConfirm_true_no_bypass",
        "nonzero_quote_difference_required": False, "hof_confirm_submissions": 0,
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

"""Thin H1 product-case producer. Writes metadata only, never prepare/allocate/run."""
from __future__ import annotations

import argparse
from pathlib import Path
import faith_e02_h1_queue as Q
from ck3_mod_acceptance_cases import faith_e02_h1_comparison_adapter as A


def make_contract(branch: Q.Arm, mother: Path, original_h2_contract: Path,
                  qualification: Path, dependencies: list[Q.Pin]) -> Q.Obj:
    old = Q.retained_h2(Q.read(original_h2_contract))
    saved = Q.obj(old.get("saved_input"))
    # Hashing/materialization belongs to ordinary public prepare; no 69 MB copy here.
    Q.require(mother.is_absolute() and Path(Q.text(saved.get("save"))).resolve() == mother.resolve(),
              "Use the original H2 mother path")
    ledger = Path(Q.text(old.get("once_ledger_root")))
    Q.require(ledger.is_absolute() and ledger.is_dir() and not ledger.is_symlink(), "Retained original H2 ledger required")
    return {"schema": A.SCHEMA, "product": "faith-engine", "case": A.CASE, "arm": branch,
            "machine_id": "4-8e1c2f1861", "saved_input": saved,
            "h2_case_contract": Q.pin(original_h2_contract), "once_ledger_root": str(ledger),
            "prior_setup_disclosure": Q.text(old.get("prior_setup_disclosure")),
            "holy_site_id": 32, "profile": {"enabled_mods": [], "product_files": []},
            "native_qualification": Q.pin(qualification), "dependencies": dependencies,
            "native_culture_observed": False, "culture_control": "same_immutable_mother_no_culture_mutator",
            "max_public_calls": Q.MAX_CALLS, "create_hof_submissions": 0}


def make_spec(contract: Q.Obj, contract_path: Path, initial_plan: Path, state_dir: Path) -> Q.Obj:
    branch = Q.arm(contract.get("arm"))
    tools = Q.READS | Q.PRESENT | Q.LIFECYCLE | ({Q.PROMOTE} if branch == "promote" else set())
    return {"id": A.CASE, "status": "ready", "adapter": {
                "module": "tools.ck3_mod_acceptance_cases.faith_e02_h1_comparison_adapter", "config": str(contract_path)},
            "initial_plan": str(initial_plan), "startup": {"mode": "saved_campaign",
                "state_dir": str(state_dir), "saved_campaign": contract["saved_input"]},
            "budgets": {"command_timeout": 300, "readiness_timeout": 1800, "timeout": 5400,
                        "hold_seconds": 1800, "poll_interval": 0.5},
            "required_mcp_tools": sorted(tools),
            "opt_in_read_only_mcp_tools": sorted({Q.SITES, Q.RELIGION, Q.GOVERNANCE, Q.DETAIL, Q.COOLDOWN}),
            **{name: False for name in A.CLOSED}, "whole_product_acceptance_credit": False,
            "business_contract_applicable": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=("ordinary", "promote"), required=True)
    parser.add_argument("--mother", type=Path, required=True)
    parser.add_argument("--h2-contract", type=Path, required=True)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--future-state-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    Q.require(not args.output.exists() and not args.future_state_dir.exists(), "Independent unused metadata and state paths required")
    quotes = A.selected_quotes()
    contract = make_contract(Q.arm(args.arm), args.mother, args.h2_contract, args.qualification,
                [Q.pin(Path(A.__file__)), Q.pin(Path(Q.__file__)), Q.pin(Path(quotes.__file__))])
    args.output.mkdir(parents=True, exist_ok=False)
    config, plan = args.output / "case-contract.json", args.output / "initial-plan.json"
    Q.write_once(config, contract)
    Q.write_once(plan, {"steps": [Q.validate_step("h1-initial-capabilities", "ck3_get_capabilities", {},
                                               Q.arm(args.arm), 32)]})
    Q.write_once(args.output / "case-fragment.json", make_spec(contract, config, plan, args.future_state_dir))


if __name__ == "__main__":
    main()

"""Produce one independent public demotion preparation case; metadata writes only."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import faith_e02_h1_queue as Q
import faith_e02_demote_preparation_contract as D
# The public loader accepts adapter.path. This metadata-only CLI imports that
# same external file without replacing the selected shared client/host package.
sys.path.insert(0, str(Path(__file__).resolve().parent / "ck3_mod_acceptance_cases"))
import faith_e02_demote_preparation_adapter as A
from ck3_mod_acceptance_cases import faith_e02_h1_comparison_adapter as H


def make_contract(original_h2: Path, qualification: Path) -> Q.Obj:
    old = Q.retained_h2(Q.read(original_h2))
    ledger = Path(Q.text(old.get("once_ledger_root")))
    Q.require(ledger.is_absolute() and ledger.is_dir() and not ledger.is_symlink(), "Retained H2 ledger required")
    quotes = H.selected_quotes()
    return {"schema": D.SCHEMA, "product": "faith-engine", "case": D.CASE, "machine_id": D.MACHINE,
            "saved_input": old["saved_input"], "h2_case_contract": Q.pin(original_h2),
            "once_ledger_root": str(ledger), "prior_setup_disclosure": Q.text(old.get("prior_setup_disclosure")),
            "profile": {"enabled_mods": [], "product_files": []}, "demote_site_id": D.DEMOTE_SITE,
            "promote_precheck_site_id": D.PROMOTE_SITE, "native_qualification": Q.pin(qualification),
            "max_public_calls": D.MAX_CALLS, "max_demote_submissions": 1, "max_save_submissions": 1,
            "promote_submissions": 0, "create_hof_submissions": 0,
            "native_culture_observed": False, "native_free_action_count_observed": False,
            "dependencies": [Q.pin(Path(Q.text(m.__file__))) for m in (A, D, Q, H, quotes)]}


def make_spec(contract: Q.Obj, config: Path, plan: Path, state: Path) -> Q.Obj:
    Q.require(state.is_absolute(), "Future isolated state path must be absolute")
    return {"id": D.CASE, "status": "ready", "adapter": {"path": str(Path(A.__file__).resolve()), "config": str(config)},
            "initial_plan": str(plan), "startup": {"mode": "saved_campaign", "state_dir": str(state),
                "saved_campaign": contract["saved_input"]},
            "budgets": {"command_timeout": 300, "readiness_timeout": 1800, "timeout": 5400,
                        "hold_seconds": 1800, "poll_interval": 0.5},
            "required_mcp_tools": sorted(D.REQUIRED), "opt_in_read_only_mcp_tools": sorted(D.READONLY_OPT_IN),
            **{key: False for key in H.CLOSED}, "business_contract_applicable": False,
            "whole_product_acceptance_credit": False}


def produce(template_path: Path, original_h2: Path, qualification: Path, state: Path, output: Path) -> Q.Obj:
    Q.require(output.is_absolute() and not output.exists() and not state.exists(),
              "Unused independent metadata/state paths required")
    contract = make_contract(original_h2, qualification)
    products = Q.read(template_path)
    Q.require(products.get("schema") == "ck3-mod-acceptance-products-v1", "Public product catalog template required")
    product = Q.obj(Q.obj(products.get("products")).get("faith-engine"))
    config, plan = output / "case-contract.json", output / "initial-plan.json"
    spec = make_spec(contract, config, plan, state)
    # Do not carry old H1 cases/adapter aliases into this single preparation catalog.
    catalog: Q.Obj = {"schema": products["schema"], "product_inventory": products["product_inventory"],
                      "products": {"faith-engine": {**product, "cases": [spec]}}}
    output.mkdir(parents=True, exist_ok=False)
    Q.write_once(config, contract)
    Q.write_once(plan, {"steps": [D.step("h1-preparation-initial-capabilities", "ck3_get_capabilities", {})]})
    Q.write_once(output / "products.json", catalog)
    Q.write_once(output / "case-fragment.json", spec)
    return {"machine_id": D.MACHINE, "status": "METADATA_ONLY_NOT_PREPARED",
            "products": Q.pin(output / "products.json"), "case_contract": Q.pin(config),
            "initial_plan": Q.pin(plan), "adapter": Q.pin(Path(A.__file__)),
            "required_tools": sorted(D.REQUIRED), "new_common_mother_exists": False,
            "game_started": False, "native_business_qualified": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--products-template", type=Path, required=True)
    parser.add_argument("--h2-contract", type=Path, required=True)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--future-state-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(Q.encode(produce(args.products_template, args.h2_contract, args.qualification,
                           args.future_state_dir, args.output)))


if __name__ == "__main__":
    main()
